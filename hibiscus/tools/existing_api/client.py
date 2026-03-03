"""
Resilient HTTP Client — EAZR Existing API
==========================================
Every endpoint in discovery.py becomes a typed async tool function here.

Features:
- Per-category configurable timeouts
- Exponential backoff retry (3 attempts, 1s / 2s / 4s)
- Circuit breaker (5 failures in 60s → 30s cooldown)
- Structured logging of every call (endpoint, latency, status)
- Graceful degradation: returns HibiscusToolError with context
- Auth injection: session_id / JWT passed transparently
- File upload support (multipart/form-data)
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from collections import deque

import httpx

from .discovery import EXISTING_CONFIG, EndpointCategory

logger = logging.getLogger("hibiscus.tools.client")

# ── Timeouts by category (seconds) ───────────────────────────────────────────
CATEGORY_TIMEOUTS: Dict[str, float] = {
    EndpointCategory.POLICY_EXTRACTION:  90.0,   # PDF → full analysis (DeepSeek + report)
    EndpointCategory.POLICY_ANALYSIS:    60.0,   # Re-analysis
    EndpointCategory.REPORT_GENERATION:  30.0,   # PDF generation
    EndpointCategory.BILLING:            45.0,   # Bill audit (LLM)
    EndpointCategory.CHAT:               15.0,   # Chat responses
    EndpointCategory.SCORING:            10.0,   # Score calculation
    EndpointCategory.POLICY_CRUD:         5.0,   # CRUD ops
    EndpointCategory.USER:                5.0,
    EndpointCategory.AUTH:                8.0,
    EndpointCategory.HEALTH:              3.0,
    EndpointCategory.CARDS:               5.0,
    EndpointCategory.NOTIFICATION:        5.0,
    EndpointCategory.IPF_SVF:            10.0,
    EndpointCategory.REWARDS:             5.0,
    EndpointCategory.LEGAL:               3.0,
    EndpointCategory.WEBSOCKET:          60.0,
    "default":                           10.0,
}

# ── Circuit Breaker ───────────────────────────────────────────────────────────
CIRCUIT_FAILURE_THRESHOLD = 5      # failures before opening
CIRCUIT_WINDOW_SECONDS    = 60     # sliding window
CIRCUIT_COOLDOWN_SECONDS  = 30     # open → half-open cooldown


class HibiscusToolError(Exception):
    """Raised when an EAZR API call fails after all retries."""
    def __init__(self, endpoint: str, status_code: int, message: str, detail: Any = None):
        self.endpoint    = endpoint
        self.status_code = status_code
        self.message     = message
        self.detail      = detail
        super().__init__(f"[{endpoint}] {status_code}: {message}")


@dataclass
class CircuitBreaker:
    failures:   deque = field(default_factory=deque)
    opened_at:  Optional[float] = None

    def record_failure(self) -> None:
        now = time.monotonic()
        self.failures.append(now)
        # Drop old failures outside the window
        while self.failures and self.failures[0] < now - CIRCUIT_WINDOW_SECONDS:
            self.failures.popleft()
        if len(self.failures) >= CIRCUIT_FAILURE_THRESHOLD:
            self.opened_at = now
            logger.warning("Circuit breaker OPENED")

    def record_success(self) -> None:
        self.failures.clear()
        self.opened_at = None

    @property
    def is_open(self) -> bool:
        if self.opened_at is None:
            return False
        if time.monotonic() - self.opened_at > CIRCUIT_COOLDOWN_SECONDS:
            logger.info("Circuit breaker half-open — trying again")
            self.opened_at = None
            return False
        return True


class EAZRClient:
    """
    Typed async HTTP client for all EAZR existing API endpoints.

    Instantiate once per Hibiscus session and pass session credentials.

    Example:
        client = EAZRClient(base_url="http://localhost:8000", session_id="...", access_token="...")
        policies = await client.get_user_policies(user_id="123")
        detail   = await client.get_policy_detail(policy_id="abc", user_id="123")
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        session_id:   Optional[str] = None,
        access_token: Optional[str] = None,
        user_id:      Optional[str] = None,
        max_retries:  int = 3,
    ):
        if base_url is None:
            # Use settings so EAZR_API_BASE env var is respected (e.g. http://eazr-app:8000 in Docker)
            from hibiscus.config import settings
            base_url = settings.eazr_api_base
        self.base_url     = base_url.rstrip("/")
        self.session_id   = session_id
        self.access_token = access_token
        self.user_id      = user_id
        self.max_retries  = max_retries
        self._circuit     = CircuitBreaker()
        # NOTE: Don't create a persistent AsyncClient here — it causes connection
        # issues when used within FastAPI's uvicorn event loop. Use fresh clients
        # per request instead (see _request below).
        self._http        = None

    def _default_headers(self) -> Dict[str, str]:
        h: Dict[str, str] = {"Content-Type": "application/json"}
        if self.access_token:
            h["Authorization"] = f"Bearer {self.access_token}"
        return h

    def _timeout(self, category: EndpointCategory) -> float:
        return CATEGORY_TIMEOUTS.get(category, CATEGORY_TIMEOUTS["default"])

    async def _request(
        self,
        method:   str,
        path:     str,
        category: EndpointCategory,
        *,
        json:     Optional[Dict] = None,
        params:   Optional[Dict] = None,
        data:     Optional[Dict] = None,
        files:    Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        Core request method with retry + circuit breaker.
        Returns parsed JSON dict on success.
        Raises HibiscusToolError on failure.
        """
        if self._circuit.is_open:
            raise HibiscusToolError(path, 503, "Circuit breaker open — EAZR API temporarily unavailable")

        timeout  = self._timeout(category)
        last_err = None

        for attempt in range(self.max_retries):
            t0 = time.monotonic()
            try:
                async with httpx.AsyncClient(
                    base_url=self.base_url,
                    headers=self._default_headers(),
                    follow_redirects=True,
                ) as http:
                    resp = await http.request(
                        method, path,
                        json=json, params=params, data=data, files=files,
                        timeout=timeout,
                    )
                latency_ms = int((time.monotonic() - t0) * 1000)
                logger.info(
                    "EAZR API %s %s → %d  (%dms)",
                    method, path, resp.status_code, latency_ms,
                )
                if resp.status_code < 400:
                    self._circuit.record_success()
                    return resp.json()
                # 4xx — don't retry
                body = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
                raise HibiscusToolError(
                    path, resp.status_code,
                    body.get("message", body.get("detail", "API error")),
                    detail=body,
                )
            except HibiscusToolError:
                raise
            except (httpx.TimeoutException, httpx.NetworkError) as exc:
                last_err = exc
                self._circuit.record_failure()
                wait = 2 ** attempt  # 1s, 2s, 4s
                logger.warning("EAZR %s %s attempt %d failed (%s) — retry in %ds", method, path, attempt + 1, exc, wait)
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(wait)

        raise HibiscusToolError(path, 503, f"All {self.max_retries} retries failed", detail=str(last_err))

    async def close(self) -> None:
        pass  # No persistent client to close (uses per-request AsyncClient)

    # ── Context manager support ───────────────────────────────────────────────
    async def __aenter__(self):
        return self

    async def __aexit__(self, *_):
        await self.close()

    # ═════════════════════════════════════════════════════════════════════════
    # AUTH
    # ═════════════════════════════════════════════════════════════════════════

    async def send_otp(self, phone: str) -> Dict:
        return await self._request("POST", "/send-otp", EndpointCategory.AUTH, json={"phone": phone})

    async def verify_otp(self, phone: str, otp: str, **kwargs) -> Dict:
        return await self._request("POST", "/verify-otp", EndpointCategory.AUTH, json={"phone": phone, "otp": otp, **kwargs})

    async def check_session(self, session_id: str) -> Dict:
        return await self._request("POST", "/check-session", EndpointCategory.AUTH, json={"session_id": session_id})

    # ═════════════════════════════════════════════════════════════════════════
    # POLICY UPLOAD & EXTRACTION
    # ═════════════════════════════════════════════════════════════════════════

    async def upload_and_analyze_policy(
        self,
        pdf_bytes:    bytes,
        filename:     str,
        user_id:      str,
        session_id:   str,
        policy_for:   str = "self",
        name:         str = "",
        gender:       str = "male",
        relationship: str = "self",
        dob:          Optional[str] = None,
        generate_pdf: bool = True,
    ) -> Dict:
        """
        Core Hibiscus tool. Upload PDF → receive full 7-stage analysis.
        Latency: 30-90 seconds (DeepSeek extraction + scoring + report).
        """
        data = {
            "userId":      user_id,
            "sessionId":   session_id,
            "policyFor":   policy_for,
            "name":        name,
            "gender":      gender,
            "relationship": relationship,
            "uploadedAt":  time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "generate_pdf": str(generate_pdf).lower(),
        }
        if dob:
            data["dateOfBirth"] = dob
        files = {"policyDocument": (filename, pdf_bytes, "application/pdf")}
        return await self._request(
            "POST", "/api/policy/upload",
            EndpointCategory.POLICY_EXTRACTION,
            data=data, files=files,
        )

    # ═════════════════════════════════════════════════════════════════════════
    # USER POLICIES
    # ═════════════════════════════════════════════════════════════════════════

    async def get_user_policies(
        self,
        user_id:    str,
        category:   Optional[str] = None,
        status:     Optional[str] = None,
        policy_for: Optional[str] = None,
    ) -> Dict:
        params: Dict[str, str] = {"userId": user_id}
        if category:   params["category"]  = category
        if status:     params["status"]    = status
        if policy_for: params["policyFor"] = policy_for
        return await self._request("GET", "/api/user/policies", EndpointCategory.POLICY_CRUD, params=params)

    async def get_policy_detail(self, policy_id: str, user_id: str) -> Dict:
        return await self._request(
            "GET", f"/api/user/policies/{policy_id}",
            EndpointCategory.POLICY_CRUD,
            params={"userId": user_id},
        )

    async def get_analysis(self, analysis_id: str, user_id: str) -> Dict:
        """
        Fetch a previously completed policy analysis from botproject.
        Called by PolicyAnalyzer when uploaded_files contains analysis_id.
        Uses GET /api/user/policies/{analysis_id} which returns the policy details.
        """
        return await self._request(
            "GET", f"/api/user/policies/{analysis_id}",
            EndpointCategory.POLICY_CRUD,
            params={"userId": user_id},
        )

    async def remove_policy(self, policy_id: str, user_id: str) -> Dict:
        return await self._request(
            "POST", "/api/policy/remove",
            EndpointCategory.POLICY_CRUD,
            json={"policyId": policy_id, "userId": user_id},
        )

    # ═════════════════════════════════════════════════════════════════════════
    # POLICY LOCKER
    # ═════════════════════════════════════════════════════════════════════════

    async def get_locker_summary(self, session_id: str, user_id: str) -> Dict:
        return await self._request(
            "GET", "/api/v1/policy-locker/summary",
            EndpointCategory.POLICY_CRUD,
            params={"session_id": session_id, "user_id": user_id},
        )

    async def get_self_policies(self, session_id: str, user_id: str) -> Dict:
        return await self._request(
            "GET", "/api/v1/policy-locker/policies/self",
            EndpointCategory.POLICY_CRUD,
            params={"session_id": session_id, "user_id": user_id},
        )

    async def get_family_policies(self, session_id: str, user_id: str) -> Dict:
        return await self._request(
            "GET", "/api/v1/policy-locker/policies/family",
            EndpointCategory.POLICY_CRUD,
            params={"session_id": session_id, "user_id": user_id},
        )

    async def get_family_members_locker(self, session_id: str, user_id: str) -> Dict:
        return await self._request(
            "GET", "/api/v1/policy-locker/family-members",
            EndpointCategory.USER,
            params={"session_id": session_id, "user_id": user_id},
        )

    async def get_claim_details(self, claim_id: str, session_id: str, user_id: str) -> Dict:
        return await self._request(
            "GET", f"/api/v1/policy-locker/claims/{claim_id}",
            EndpointCategory.POLICY_CRUD,
            params={"session_id": session_id, "user_id": user_id},
        )

    async def get_emergency_services(self, session_id: str, user_id: str) -> Dict:
        return await self._request(
            "GET", "/api/v1/policy-locker/emergency-services",
            EndpointCategory.POLICY_CRUD,
            params={"session_id": session_id, "user_id": user_id},
        )

    # ═════════════════════════════════════════════════════════════════════════
    # CLAIM GUIDANCE
    # ═════════════════════════════════════════════════════════════════════════

    async def get_claim_guidance(
        self,
        query:          str,
        session_id:     str,
        access_token:   str,
        user_id:        str,
        insurance_type: Optional[str] = None,
    ) -> Dict:
        body: Dict[str, Any] = {
            "query":        query,
            "session_id":   session_id,
            "access_token": access_token,
            "user_id":      user_id,
        }
        if insurance_type:
            body["insurance_type"] = insurance_type
        return await self._request("POST", "/insurance-claim-guidance", EndpointCategory.POLICY_ANALYSIS, json=body)

    # ═════════════════════════════════════════════════════════════════════════
    # DASHBOARD & PORTFOLIO
    # ═════════════════════════════════════════════════════════════════════════

    async def get_protection_score(self, user_id: str, annual_income: Optional[int] = None) -> Dict:
        headers = {}
        if annual_income:
            headers["annualIncome"] = str(annual_income)
        return await self._request(
            "GET", f"/api/dashboard/protection-score/{user_id}",
            EndpointCategory.SCORING,
        )

    async def refresh_protection_score(self, annual_income: Optional[int] = None, reason: str = "") -> Dict:
        return await self._request(
            "POST", "/api/dashboard/refresh-score",
            EndpointCategory.SCORING,
            json={"annualIncome": annual_income, "reason": reason},
        )

    async def get_dashboard_insights(self, user_id: str) -> Dict:
        return await self._request(
            "GET", "/api/dashboard/insights",
            EndpointCategory.RECOMMENDATION,
            params={"user_id": user_id},
        )

    async def get_renewals(self, user_id: str) -> Dict:
        return await self._request(
            "GET", "/api/dashboard/renewals",
            EndpointCategory.POLICY_CRUD,
            params={"user_id": user_id},
        )

    async def get_portfolio_breakdown(self, user_id: str) -> Dict:
        return await self._request(
            "GET", "/api/portfolio/breakdown",
            EndpointCategory.SCORING,
            params={"userId": user_id},
        )

    # ═════════════════════════════════════════════════════════════════════════
    # FAMILY
    # ═════════════════════════════════════════════════════════════════════════

    async def get_family_coverage(self, user_id: str) -> Dict:
        return await self._request(
            "GET", "/api/family/members",
            EndpointCategory.USER,
            params={"userId": user_id},
        )

    # ═════════════════════════════════════════════════════════════════════════
    # BILL AUDIT
    # ═════════════════════════════════════════════════════════════════════════

    async def upload_bill(
        self,
        files:      List[tuple],   # [(filename, bytes, content_type), ...]
        session_id: str,
        user_id:    str,
        policy_id:  Optional[str] = None,
    ) -> Dict:
        data: Dict[str, str] = {"session_id": session_id, "user_id": user_id}
        if policy_id:
            data["policy_id"] = policy_id
        http_files = [("files", f) for f in files]
        return await self._request(
            "POST", "/api/v1/bill-audit/upload",
            EndpointCategory.BILLING,
            data=data, files=dict(enumerate(http_files)),
        )

    async def get_bill_audit_result(self, audit_id: str, session_id: str, user_id: str) -> Dict:
        return await self._request(
            "GET", f"/api/v1/bill-audit/{audit_id}",
            EndpointCategory.BILLING,
            params={"session_id": session_id, "user_id": user_id},
        )

    async def generate_bill_audit_report(self, audit_id: str, session_id: str, user_id: str) -> Dict:
        return await self._request(
            "POST", f"/api/v1/bill-audit/{audit_id}/report",
            EndpointCategory.REPORT_GENERATION,
            data={"session_id": session_id, "user_id": user_id},
        )

    async def generate_dispute_letter(
        self,
        audit_id:    str,
        session_id:  str,
        user_id:     str,
        include_pdf: bool = True,
    ) -> Dict:
        return await self._request(
            "POST", f"/api/v1/bill-audit/{audit_id}/dispute-letter",
            EndpointCategory.BILLING,
            data={"session_id": session_id, "user_id": user_id, "include_pdf": str(include_pdf).lower()},
        )

    # ═════════════════════════════════════════════════════════════════════════
    # HBF FINANCING
    # ═════════════════════════════════════════════════════════════════════════

    async def check_hbf_eligibility(self, session_id: str, user_id: str, amount: float, audit_id: Optional[str] = None) -> Dict:
        body: Dict[str, Any] = {"session_id": session_id, "user_id": user_id, "loan_type": "HBF", "amount": amount}
        if audit_id:
            body["audit_id"] = audit_id
        return await self._request("POST", "/api/v1/hbf/eligibility", EndpointCategory.IPF_SVF, json=body)

    async def get_hbf_offers(self, session_id: str, user_id: str, loan_id: str) -> Dict:
        return await self._request(
            "POST", "/api/v1/hbf/offers",
            EndpointCategory.IPF_SVF,
            json={"session_id": session_id, "user_id": user_id, "loan_id": loan_id},
        )

    # ═════════════════════════════════════════════════════════════════════════
    # CARDS
    # ═════════════════════════════════════════════════════════════════════════

    async def get_credit_cards(self, skip: int = 0, limit: int = 50) -> Dict:
        return await self._request("GET", "/cards/credit/cards", EndpointCategory.CARDS, params={"skip": skip, "limit": limit})

    async def search_credit_cards(self, query: str) -> Dict:
        return await self._request("GET", "/cards/credit/search", EndpointCategory.CARDS, params={"q": query})

    async def get_card_benefits(self, card_id: str) -> Dict:
        return await self._request("GET", f"/cards/benefits/{card_id}", EndpointCategory.CARDS)

    async def get_user_cards(self, user_id: str, card_for: Optional[str] = None) -> Dict:
        params: Dict[str, str] = {}
        if card_for:
            params["card_for"] = card_for
        return await self._request("GET", f"/cards/user/{user_id}", EndpointCategory.CARDS, params=params)

    # ═════════════════════════════════════════════════════════════════════════
    # USER PROFILE
    # ═════════════════════════════════════════════════════════════════════════

    async def get_user_profile(self, session_id: str) -> Dict:
        return await self._request("GET", f"/user-profile/{session_id}", EndpointCategory.USER)

    # ═════════════════════════════════════════════════════════════════════════
    # NOTIFICATIONS
    # ═════════════════════════════════════════════════════════════════════════

    async def register_device_token(self, user_id: str, fcm_token: str, device_type: str, **kwargs) -> Dict:
        return await self._request(
            "POST", "/notifications/register-device",
            EndpointCategory.NOTIFICATION,
            json={"user_id": user_id, "fcm_token": fcm_token, "device_type": device_type, **kwargs},
        )

    async def get_notification_history(self, user_id: str, limit: int = 20, unread_only: bool = False) -> Dict:
        return await self._request(
            "GET", "/notifications/history",
            EndpointCategory.NOTIFICATION,
            params={"user_id": user_id, "limit": limit, "unread_only": str(unread_only).lower()},
        )

    # ═════════════════════════════════════════════════════════════════════════
    # REWARDS
    # ═════════════════════════════════════════════════════════════════════════

    async def get_rewards_progress(self, user_id: Optional[str] = None) -> Dict:
        params = {"userId": user_id} if user_id else {}
        return await self._request("GET", "/rewards/progress", EndpointCategory.REWARDS, params=params)

    async def check_reward_eligibility(self, user_id: Optional[str] = None) -> Dict:
        params = {"userId": user_id} if user_id else {}
        return await self._request("GET", "/rewards/eligibility", EndpointCategory.REWARDS, params=params)

    # ═════════════════════════════════════════════════════════════════════════
    # LEGAL
    # ═════════════════════════════════════════════════════════════════════════

    async def get_privacy_policy(self) -> Dict:
        return await self._request("GET", "/api/privacy-policy", EndpointCategory.LEGAL)

    async def get_terms_and_conditions(self) -> Dict:
        return await self._request("GET", "/api/terms-and-conditions", EndpointCategory.LEGAL)

    # ═════════════════════════════════════════════════════════════════════════
    # SUPPORT
    # ═════════════════════════════════════════════════════════════════════════

    async def get_contact_support(self) -> Dict:
        return await self._request("GET", "/support/contact", EndpointCategory.HEALTH)

    # ═════════════════════════════════════════════════════════════════════════
    # HEALTH
    # ═════════════════════════════════════════════════════════════════════════

    async def health_check(self) -> Dict:
        return await self._request("GET", "/health", EndpointCategory.HEALTH)

    async def enhanced_health(self) -> Dict:
        return await self._request("GET", "/enhanced-health", EndpointCategory.HEALTH)


# ── Factory helper ────────────────────────────────────────────────────────────

def make_client(
    session_id:   Optional[str] = None,
    access_token: Optional[str] = None,
    user_id:      Optional[str] = None,
    base_url:     Optional[str] = None,
) -> EAZRClient:
    """
    Create an EAZRClient with credentials.
    Typical usage in a Hibiscus agent node:

        client = make_client(session_id=state["session_id"], access_token=state["token"], user_id=state["user_id"])
        policies = await client.get_user_policies(user_id=state["user_id"])
    """
    return EAZRClient(
        base_url=base_url or EXISTING_CONFIG.api_base_url,
        session_id=session_id,
        access_token=access_token,
        user_id=user_id,
    )
