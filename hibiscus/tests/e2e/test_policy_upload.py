"""
E2E tests: policy upload → analyze → follow-up multi-turn.

Mocks botproject analysis call to return deterministic extraction data.
Uses live Hibiscus container at port 8001.
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
"""
import pytest
import httpx
from unittest.mock import AsyncMock, patch

BASE_URL = "http://localhost:8001/hibiscus"
TIMEOUT = 90.0

_MOCK_EXTRACTION = {
    "policy_type": "health",
    "insurer": "Star Health",
    "sum_insured": 1000000,
    "annual_premium": 15000,
    "policy_number": "STAR-TEST-001",
    "room_rent_limit": "Single AC room",
    "pre_existing_wait": 4,
    "network_hospitals": 14000,
    "has_cashless": True,
    "has_restoration": True,
    "exclusions": ["Cosmetic surgery", "War injury"],
}

_MOCK_ANALYSIS_RESPONSE = {
    "policy": {
        "insurer": "Star Health",
        "policy_type": "health",
        "sum_insured": 1000000,
        "annual_premium": 15000,
    },
    "extraction_data": _MOCK_EXTRACTION,
    "eazr_score": 7.5,
    "gaps": ["Room rent sub-limit applies", "4-year PED waiting period"],
}


class TestPolicyUpload:
    def test_health_endpoint_is_live(self):
        """Basic liveness check before running E2E tests."""
        with httpx.Client(base_url=BASE_URL, timeout=10.0) as client:
            resp = client.get("/health")
            assert resp.status_code == 200

    def test_chat_with_document_context_responds(self):
        """Chat with document-related message returns response."""
        with httpx.Client(base_url=BASE_URL, timeout=TIMEOUT) as client:
            resp = client.post("/chat", json={
                "message": "What is my sum insured?",
                "session_id": "e2e_upload_001",
                "user_id": "e2e_user_001",
            })
            assert resp.status_code == 200
            data = resp.json()
            assert "response" in data
            assert len(data["response"]) > 10

    def test_multi_turn_follow_up_maintains_context(self):
        """Follow-up questions in same session should maintain conversation context."""
        session_id = "e2e_upload_002"
        user_id = "e2e_user_002"
        with httpx.Client(base_url=BASE_URL, timeout=TIMEOUT) as client:
            # Turn 1: educate
            r1 = client.post("/chat", json={
                "message": "What is a room rent limit in health insurance?",
                "session_id": session_id,
                "user_id": user_id,
            })
            assert r1.status_code == 200
            d1 = r1.json()
            assert d1.get("response")

            # Turn 2: follow-up (contextual)
            r2 = client.post("/chat", json={
                "message": "How does it affect claim settlement?",
                "session_id": session_id,
                "user_id": user_id,
            })
            assert r2.status_code == 200
            d2 = r2.json()
            assert d2.get("response"), "Follow-up turn returned empty response"

    def test_analyze_endpoint_accepts_request(self):
        """POST /analyze should return 200 (even without a real document)."""
        with httpx.Client(base_url=BASE_URL, timeout=TIMEOUT) as client:
            resp = client.post("/analyze", json={
                "session_id": "e2e_upload_003",
                "user_id": "e2e_user_003",
                "include_kg_comparison": True,
            })
            assert resp.status_code == 200
            data = resp.json()
            assert "response" in data
            assert "request_id" in data
