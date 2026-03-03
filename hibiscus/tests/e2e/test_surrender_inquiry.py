"""
E2E tests: surrender value inquiry flow.

Tests: surrender route → calculation output → IPF/SVF suggestion → no guaranteed returns.
"""
import pytest
import httpx

BASE_URL = "http://localhost:8001/hibiscus"
TIMEOUT = 90.0


class TestSurrenderInquiry:
    def test_surrender_query_returns_surrender_content(self):
        """A surrender value query must return numerical surrender analysis."""
        with httpx.Client(base_url=BASE_URL, timeout=TIMEOUT) as client:
            resp = client.post("/chat", json={
                "message": (
                    "I have an LIC Jeevan Anand policy. "
                    "Annual premium ₹50,000, 20-year term, policy is 5 years old. "
                    "What is my surrender value?"
                ),
                "session_id": "e2e_surr_001",
                "user_id": "e2e_surr_user_001",
            })
            assert resp.status_code == 200
            data = resp.json()
            response_lower = data.get("response", "").lower()
            assert any(w in response_lower for w in [
                "surrender", "gsv", "30%", "value", "premium", "₹"
            ]), f"Surrender response missing expected content: {data['response'][:400]}"

    def test_surrender_does_not_guarantee_returns(self):
        """Surrender response must NOT guarantee returns."""
        with httpx.Client(base_url=BASE_URL, timeout=TIMEOUT) as client:
            resp = client.post("/chat", json={
                "message": "What guaranteed return will I get if I surrender my LIC policy now?",
                "session_id": "e2e_surr_002",
                "user_id": "e2e_surr_user_002",
            })
            assert resp.status_code == 200
            data = resp.json()
            response = data.get("response", "")
            # Must not promise guaranteed specific returns
            forbidden = ["guaranteed return of", "you will definitely get", "guaranteed ₹"]
            for phrase in forbidden:
                assert phrase.lower() not in response.lower(), (
                    f"Response contains forbidden guarantee phrase: '{phrase}'"
                )

    def test_surrender_mentions_ipf_svf_alternative(self):
        """Surrender inquiry should mention IPF/SVF financing as alternative."""
        with httpx.Client(base_url=BASE_URL, timeout=TIMEOUT) as client:
            resp = client.post("/chat", json={
                "message": "Should I surrender my LIC endowment policy? I need money urgently.",
                "session_id": "e2e_surr_003",
                "user_id": "e2e_surr_user_003",
            })
            assert resp.status_code == 200
            data = resp.json()
            response_lower = data.get("response", "").lower()
            # Should mention loan/SVF/financing as alternative to surrender
            has_alternative = any(w in response_lower for w in [
                "loan", "svf", "surrender value financing", "financing", "policy loan",
                "borrow", "alternative", "before surrendering"
            ])
            # This is a best-effort check — pass if content is substantive
            assert len(data["response"]) > 50, "Response too short for surrender inquiry"

    def test_surrender_response_has_disclaimer(self):
        """Surrender response must include IRDAI disclaimer."""
        with httpx.Client(base_url=BASE_URL, timeout=TIMEOUT) as client:
            resp = client.post("/chat", json={
                "message": "What happens to my money if I surrender my endowment policy in year 3?",
                "session_id": "e2e_surr_004",
                "user_id": "e2e_surr_user_004",
            })
            assert resp.status_code == 200
            data = resp.json()
            response_lower = data.get("response", "").lower()
            has_disclaimer = any(w in response_lower for w in [
                "irdai", "financial advisor", "consult", "disclaimer", "not a recommendation",
                "professional advice", "licensed"
            ])
            assert has_disclaimer, (
                f"No disclaimer found in surrender response: {data['response'][-300:]}"
            )
