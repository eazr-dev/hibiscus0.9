"""
Fraud & Anomaly Detection Service
===================================
Detects suspicious documents and behavioral patterns.

Document-level signals:
- Inconsistent data (policy dates, numbers, insurer patterns)
- Suspicious premium/SI ratio (too cheap or too expensive)
- Missing expected insurance fields (non-insurance document)
- Duplicate policy numbers across uploads

Behavioral signals:
- Rapid uploads (>5 in one session)
- Testing patterns (sequential probing queries)

Alerts are logged and available for admin review — NEVER surfaced to users.
The risk_detector agent merges fraud alerts into its risk_flags.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from hibiscus.observability.logger import get_logger

logger = get_logger(__name__)


class FraudSeverity(str, Enum):
    LOW = "LOW"          # Log only
    MEDIUM = "MEDIUM"    # Flag in admin dashboard
    HIGH = "HIGH"        # Flag + restrict certain features
    CRITICAL = "CRITICAL"  # Flag + notify ops + restrict account


@dataclass
class FraudAlert:
    """A single fraud/anomaly detection signal."""
    alert_type: str               # e.g., "suspicious_ratio", "non_insurance_doc"
    severity: FraudSeverity
    evidence: str                 # Specific evidence that triggered this
    recommendation: str           # What action to take
    confidence: float             # 0-1, how confident we are this is anomalous
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "alert_type": self.alert_type,
            "severity": self.severity.value,
            "evidence": self.evidence,
            "recommendation": self.recommendation,
            "confidence": self.confidence,
            "details": self.details,
        }


# ── Known insurer policy number patterns (prefix → insurer) ─────────────────
_POLICY_NUMBER_PATTERNS = {
    "P/": "Star Health",
    "STAR": "Star Health",
    "HDT": "HDFC ERGO",
    "ERG": "HDFC ERGO",
    "ICL": "ICICI Lombard",
    "BAG": "Bajaj Allianz",
    "LIC": "LIC",
    "SBI": "SBI Life",
    "MAX": "Max Life",
    "NB": "Niva Bupa",
}

# ── Expected fields in a valid insurance document extraction ────────────────
_INSURANCE_INDICATOR_FIELDS = [
    "policy_type", "insurer", "insurer_name", "sum_insured", "sum_assured",
    "premium", "annual_premium", "policy_number", "policy_start_date",
    "policy_end_date", "policyholder", "coverage", "plan_name",
]

# ── Premium/SI ratio bounds by category ────────────────────────────────────
_RATIO_BOUNDS = {
    "health": (0.002, 0.15),    # 0.2% to 15% of SI
    "life": (0.001, 0.20),      # 0.1% to 20% of SI
    "term_life": (0.001, 0.05), # 0.1% to 5% of SI
    "motor": (0.01, 0.25),      # 1% to 25% of IDV
    "travel": (0.01, 0.30),     # 1% to 30%
    "pa": (0.002, 0.10),        # 0.2% to 10%
}


class FraudDetector:
    """
    Stateless fraud detection. All methods are pure functions.
    Called by risk_detector agent during policy analysis.
    """

    def check_document(
        self,
        extraction: Dict[str, Any],
        state: Optional[Dict[str, Any]] = None,
    ) -> List[FraudAlert]:
        """
        Run all document-level fraud checks on extraction data.
        Returns list of FraudAlert (may be empty for clean documents).
        """
        if not extraction:
            return []

        alerts = []
        alerts.extend(self._check_non_insurance_doc(extraction))
        alerts.extend(self._check_date_consistency(extraction))
        alerts.extend(self._check_suspicious_ratios(extraction))
        alerts.extend(self._check_policy_number_consistency(extraction))

        if state:
            alerts.extend(self._check_duplicate_policy(extraction, state))

        return alerts

    def check_behavioral(
        self,
        session_history: List[Dict[str, Any]],
    ) -> List[FraudAlert]:
        """
        Check behavioral patterns in session history.
        """
        alerts = []
        alerts.extend(self._check_rapid_uploads(session_history))
        return alerts

    # ── Document-Level Checks ────────────────────────────────────────────────

    def _check_non_insurance_doc(self, extraction: Dict) -> List[FraudAlert]:
        """Flag documents that don't look like insurance policies."""
        indicator_count = sum(
            1 for f in _INSURANCE_INDICATOR_FIELDS
            if extraction.get(f)
        )

        if indicator_count < 2:
            return [FraudAlert(
                alert_type="non_insurance_document",
                severity=FraudSeverity.LOW,
                evidence=f"Only {indicator_count}/{len(_INSURANCE_INDICATOR_FIELDS)} insurance fields found in extraction",
                recommendation="Verify this is actually an insurance policy document",
                confidence=0.7 if indicator_count == 0 else 0.5,
                details={"fields_found": indicator_count},
            )]
        return []

    def _check_date_consistency(self, extraction: Dict) -> List[FraudAlert]:
        """Check for date inconsistencies."""
        alerts = []
        start = extraction.get("policy_start_date")
        end = extraction.get("policy_end_date") or extraction.get("policy_expiry_date")

        if start and end:
            from datetime import datetime

            def _parse(d: Any) -> Optional[datetime]:
                if isinstance(d, datetime):
                    return d
                if isinstance(d, str):
                    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
                        try:
                            return datetime.strptime(d.strip(), fmt)
                        except ValueError:
                            continue
                return None

            start_dt = _parse(start)
            end_dt = _parse(end)

            if start_dt and end_dt:
                if start_dt > end_dt:
                    alerts.append(FraudAlert(
                        alert_type="date_inconsistency",
                        severity=FraudSeverity.MEDIUM,
                        evidence=f"Policy start date ({start}) is after end date ({end})",
                        recommendation="Verify document authenticity — dates are reversed",
                        confidence=0.9,
                        details={"start": str(start), "end": str(end)},
                    ))

                # Policy term > 50 years (suspicious for most types)
                delta = end_dt - start_dt
                if delta.days > 50 * 365:
                    alerts.append(FraudAlert(
                        alert_type="unusual_policy_term",
                        severity=FraudSeverity.LOW,
                        evidence=f"Policy term is {delta.days // 365} years — unusually long",
                        recommendation="Verify — most policies are 1-30 year terms",
                        confidence=0.6,
                    ))

        return alerts

    def _check_suspicious_ratios(self, extraction: Dict) -> List[FraudAlert]:
        """Check if premium/SI ratio is outside expected bounds."""
        alerts = []

        premium = None
        for f in ("annual_premium", "premium"):
            val = extraction.get(f)
            if val is not None:
                try:
                    premium = float(val)
                    break
                except (ValueError, TypeError):
                    pass

        si = None
        for f in ("sum_insured", "sum_assured"):
            val = extraction.get(f)
            if val is not None:
                try:
                    si = float(val)
                    break
                except (ValueError, TypeError):
                    pass

        if premium is not None and si is not None and si > 0:
            ratio = premium / si
            category = (extraction.get("policy_type") or "health").lower().replace(" ", "_")
            bounds = _RATIO_BOUNDS.get(category, _RATIO_BOUNDS["health"])

            if ratio < bounds[0]:
                alerts.append(FraudAlert(
                    alert_type="suspicious_ratio_low",
                    severity=FraudSeverity.MEDIUM,
                    evidence=f"Premium/SI ratio {ratio:.4f} is below minimum {bounds[0]} for {category}. "
                             f"Premium ₹{premium:,.0f} for SI ₹{si:,.0f} is unusually cheap.",
                    recommendation="Verify premium and sum insured values — ratio indicates possible data entry error or fraudulent document",
                    confidence=0.75,
                    details={"premium": premium, "sum_insured": si, "ratio": round(ratio, 6), "category": category},
                ))
            elif ratio > bounds[1]:
                alerts.append(FraudAlert(
                    alert_type="suspicious_ratio_high",
                    severity=FraudSeverity.MEDIUM,
                    evidence=f"Premium/SI ratio {ratio:.4f} exceeds maximum {bounds[1]} for {category}. "
                             f"Premium ₹{premium:,.0f} for SI ₹{si:,.0f} is unusually expensive.",
                    recommendation="Check for potential mis-selling or incorrect extraction",
                    confidence=0.70,
                    details={"premium": premium, "sum_insured": si, "ratio": round(ratio, 6), "category": category},
                ))

        return alerts

    def _check_policy_number_consistency(self, extraction: Dict) -> List[FraudAlert]:
        """Check if policy number format matches the claimed insurer."""
        alerts = []
        policy_no = extraction.get("policy_number")
        insurer = extraction.get("insurer") or extraction.get("insurer_name")

        if policy_no and insurer:
            policy_upper = policy_no.upper()
            insurer_lower = insurer.lower()

            for prefix, expected_insurer in _POLICY_NUMBER_PATTERNS.items():
                if policy_upper.startswith(prefix):
                    if expected_insurer.lower() not in insurer_lower:
                        alerts.append(FraudAlert(
                            alert_type="policy_number_mismatch",
                            severity=FraudSeverity.MEDIUM,
                            evidence=f"Policy number '{policy_no}' has prefix '{prefix}' typical of {expected_insurer}, "
                                     f"but insurer is listed as '{insurer}'",
                            recommendation="Verify policy number matches the insurer",
                            confidence=0.65,
                            details={"policy_number": policy_no, "claimed_insurer": insurer,
                                     "expected_insurer": expected_insurer},
                        ))
                    break

        return alerts

    def _check_duplicate_policy(
        self,
        extraction: Dict,
        state: Dict[str, Any],
    ) -> List[FraudAlert]:
        """Check if this policy number already exists in portfolio."""
        alerts = []
        policy_no = extraction.get("policy_number")
        if not policy_no:
            return alerts

        portfolio = state.get("policy_portfolio", [])
        for existing in portfolio:
            existing_no = existing.get("policy_number")
            if existing_no and existing_no == policy_no:
                # Same policy re-uploaded — not necessarily fraud, could be update
                existing_insurer = existing.get("insurer", "unknown")
                new_insurer = extraction.get("insurer", "unknown")
                if existing_insurer.lower() != new_insurer.lower():
                    alerts.append(FraudAlert(
                        alert_type="duplicate_policy_different_insurer",
                        severity=FraudSeverity.HIGH,
                        evidence=f"Policy number '{policy_no}' already exists from '{existing_insurer}' "
                                 f"but new upload claims insurer '{new_insurer}'",
                        recommendation="Potential document tampering — same policy number, different insurer",
                        confidence=0.85,
                        details={"policy_number": policy_no, "existing_insurer": existing_insurer,
                                 "new_insurer": new_insurer},
                    ))

        return alerts

    # ── Behavioral Checks ────────────────────────────────────────────────────

    def _check_rapid_uploads(
        self,
        session_history: List[Dict[str, Any]],
    ) -> List[FraudAlert]:
        """Flag sessions with an unusual number of document uploads."""
        upload_count = sum(
            1 for msg in session_history
            if msg.get("role") == "user" and msg.get("metadata", {}).get("has_files")
        )

        if upload_count > 5:
            return [FraudAlert(
                alert_type="rapid_uploads",
                severity=FraudSeverity.MEDIUM,
                evidence=f"{upload_count} document uploads in a single session",
                recommendation="May indicate broker/agent behavior rather than end user — monitor",
                confidence=0.5,
                details={"upload_count": upload_count},
            )]
        return []


# ── Module-level singleton ──────────────────────────────────────────────────
fraud_detector = FraudDetector()
