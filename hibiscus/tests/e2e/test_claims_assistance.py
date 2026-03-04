"""
E2E tests: claims assistance flow.

Tests: cashless claim → reimbursement → distressed tone → disclaimer present.
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
"""
import pytest
import httpx

BASE_URL = "http://localhost:8001/hibiscus"
TIMEOUT = 90.0


class TestClaimsAssistance:
    def test_cashless_claim_guidance(self):
        """Cashless claim query should return step-by-step guidance."""
        with httpx.Client(base_url=BASE_URL, timeout=TIMEOUT) as client:
            resp = client.post("/chat", json={
                "message": "My mother was just admitted to a network hospital. "
                           "How do I initiate a cashless claim?",
                "session_id": "e2e_claim_001",
                "user_id": "e2e_claim_user_001",
            })
            assert resp.status_code == 200
            data = resp.json()
            response_lower = data.get("response", "").lower()
            assert any(w in response_lower for w in [
                "cashless", "network", "tpa", "hospital", "pre-authorisation", "pre-auth",
                "intimation", "insurer", "step"
            ]), f"Cashless claim response missing expected content: {data['response'][:400]}"

    def test_reimbursement_claim_guidance(self):
        """Reimbursement query should explain the reimbursement process."""
        with httpx.Client(base_url=BASE_URL, timeout=TIMEOUT) as client:
            resp = client.post("/chat", json={
                "message": "I was treated at a non-network hospital. "
                           "How do I file a reimbursement claim?",
                "session_id": "e2e_claim_002",
                "user_id": "e2e_claim_user_002",
            })
            assert resp.status_code == 200
            data = resp.json()
            response_lower = data.get("response", "").lower()
            assert any(w in response_lower for w in [
                "reimbursement", "bills", "documents", "submit", "insurer", "within", "days"
            ]), f"Reimbursement response missing expected content: {data['response'][:400]}"

    def test_distressed_claim_tone_is_empathetic(self):
        """Distressed user (ICU/cancer) must get empathetic response first."""
        with httpx.Client(base_url=BASE_URL, timeout=TIMEOUT) as client:
            resp = client.post("/chat", json={
                "message": "My husband is in ICU. The hospital is asking for a deposit of ₹2 lakhs. "
                           "We have a Star Health policy. What do I do? I'm very scared.",
                "session_id": "e2e_claim_003",
                "user_id": "e2e_claim_user_003",
            })
            assert resp.status_code == 200
            data = resp.json()
            response = data.get("response", "")
            response_lower = response.lower()

            # Must lead with empathy
            first_200 = response_lower[:200]
            has_empathy = any(phrase in first_200 for phrase in [
                "sorry", "understand", "difficult", "support", "here for you",
                "i know", "mujhe samajh", "concerned", "hope"
            ])
            assert has_empathy, (
                f"Response does not lead with empathy for distressed user: {response[:300]}"
            )

            # Must also address the immediate problem
            assert any(w in response_lower for w in [
                "cashless", "network", "tpa", "insurer", "hospital", "authorisation", "star health"
            ]), f"Response doesn't address the immediate claim issue: {response[:400]}"

    def test_claim_response_includes_disclaimer(self):
        """All claim guidance should include IRDAI-appropriate disclaimer."""
        with httpx.Client(base_url=BASE_URL, timeout=TIMEOUT) as client:
            resp = client.post("/chat", json={
                "message": "My claim was rejected. The insurer says it's a pre-existing condition. "
                           "What can I do?",
                "session_id": "e2e_claim_004",
                "user_id": "e2e_claim_user_004",
            })
            assert resp.status_code == 200
            data = resp.json()
            response_lower = data.get("response", "").lower()
            has_disclaimer = any(w in response_lower for w in [
                "irdai", "ombudsman", "grievance", "consult", "advisor",
                "disclaimer", "not a", "professional", "recommend"
            ])
            assert has_disclaimer, (
                f"No disclaimer/escalation path in claims response: {data['response'][-300:]}"
            )
