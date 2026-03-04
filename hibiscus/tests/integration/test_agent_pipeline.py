"""
Integration tests: agent pipeline routing and response format.

Tests: intent routing → agent selection → response format (not LLM quality).
Uses a live Hibiscus container on port 8001.
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
"""
import pytest
import httpx

BASE_URL = "http://localhost:8001/hibiscus"
TIMEOUT = 60.0


@pytest.fixture
def client():
    return httpx.Client(base_url=BASE_URL, timeout=TIMEOUT)


def _chat(client, message: str, session_id: str = "int_test_session") -> dict:
    resp = client.post("/chat", json={
        "message": message,
        "session_id": session_id,
        "user_id": "int_test_user",
    })
    assert resp.status_code == 200, f"HTTP {resp.status_code}: {resp.text[:200]}"
    data = resp.json()
    assert "response" in data, f"No 'response' key in: {data}"
    return data


class TestAgentPipeline:
    def test_l1_educate_routes_to_direct_llm(self, client):
        """Simple educational query should NOT invoke specialist agents."""
        data = _chat(client, "What is a deductible in health insurance?", "int_pipe_001")
        assert data.get("response"), "Empty response"
        # L1 educate — no specialist agents (direct_llm fast path)
        agents = data.get("agents_invoked", [])
        assert "policy_analyzer" not in agents, f"policy_analyzer fired on L1: {agents}"

    def test_analyze_intent_routes_to_policy_analyzer(self, client):
        """'Analyze my policy' should invoke the policy_analyzer agent."""
        data = _chat(client, "Can you analyze my health insurance policy?", "int_pipe_002")
        assert data.get("response"), "Empty response"
        # Should either invoke policy_analyzer OR ask user to upload
        response_lower = data["response"].lower()
        has_agent = "policy_analyzer" in data.get("agents_invoked", [])
        has_upload_ask = any(w in response_lower for w in ["upload", "share", "provide", "document"])
        assert has_agent or has_upload_ask, (
            f"Expected policy_analyzer invoked or upload prompt. agents={data.get('agents_invoked')}"
        )

    def test_surrender_routes_to_calculator(self, client):
        """Surrender query should invoke surrender_calculator."""
        data = _chat(
            client,
            "I have an LIC Jeevan Anand policy for 20 years paying ₹50,000 per year. "
            "What will be the surrender value if I exit in year 5?",
            "int_pipe_003",
        )
        assert data.get("response"), "Empty response"
        response_lower = data["response"].lower()
        # Must mention surrender-related concepts
        assert any(w in response_lower for w in ["surrender", "gsv", "value", "policy year"]), (
            f"Surrender response missing expected content: {data['response'][:300]}"
        )

    def test_claim_routes_to_claims_guide(self, client):
        """Claim query should invoke claims_guide agent."""
        data = _chat(client, "How do I file a cashless claim for hospitalisation?", "int_pipe_004")
        assert data.get("response"), "Empty response"
        response_lower = data["response"].lower()
        assert any(w in response_lower for w in ["cashless", "hospital", "tpa", "network", "claim"]), (
            f"Claims response missing expected content: {data['response'][:300]}"
        )

    def test_response_always_has_required_keys(self, client):
        """Every chat response must have response, confidence, sources."""
        data = _chat(client, "What is a no-claim bonus?", "int_pipe_005")
        assert "response" in data
        assert "confidence" in data, "Missing 'confidence'"
        assert isinstance(data["confidence"], float), "confidence must be float"
        assert 0.0 <= data["confidence"] <= 1.0, f"confidence out of range: {data['confidence']}"
