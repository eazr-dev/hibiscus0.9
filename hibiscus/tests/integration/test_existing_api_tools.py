"""
🌺 Hibiscus v0.9 | EAZR AI Insurance Intelligence Engine
Integration tests: existing API tool wrappers — HTTP client, retries, circuit breaker.
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
"""
import asyncio
import time
from unittest.mock import AsyncMock, patch

import pytest

from hibiscus.tools.existing_api.client import (
    BACKOFF_BASE,
    CIRCUIT_BREAKER_THRESHOLD,
    MAX_RETRIES,
    CircuitBreakerState,
    ExistingAPIError,
    call_existing_api,
)
from hibiscus.tools.existing_api.extraction import extract_policy
from hibiscus.tools.existing_api.scoring import calculate_protection_score
from hibiscus.tools.existing_api.reporting import generate_report
from hibiscus.tools.existing_api.compliance import check_irdai_compliance
from hibiscus.tools.existing_api.billing import audit_bill


# ── Circuit Breaker Unit Tests ────────────────────────────────────────────────


class TestCircuitBreaker:
    def test_initial_state_is_closed(self):
        cb = CircuitBreakerState()
        assert cb.is_open is False
        assert cb.opened_at is None

    def test_opens_after_threshold_failures(self):
        cb = CircuitBreakerState()
        for _ in range(CIRCUIT_BREAKER_THRESHOLD):
            cb.record_failure()
        assert cb.is_open is True

    def test_stays_closed_below_threshold(self):
        cb = CircuitBreakerState()
        for _ in range(CIRCUIT_BREAKER_THRESHOLD - 1):
            cb.record_failure()
        assert cb.is_open is False

    def test_success_resets_failures(self):
        cb = CircuitBreakerState()
        for _ in range(CIRCUIT_BREAKER_THRESHOLD - 1):
            cb.record_failure()
        cb.record_success()
        assert len(cb.failures) == 0
        assert cb.is_open is False

    def test_success_closes_open_circuit(self):
        cb = CircuitBreakerState()
        for _ in range(CIRCUIT_BREAKER_THRESHOLD):
            cb.record_failure()
        assert cb.is_open is True
        cb.record_success()
        assert cb.is_open is False
        assert cb.opened_at is None


# ── HTTP Client Tests (mocked) ───────────────────────────────────────────────


class TestExistingAPIClient:
    @pytest.fixture(autouse=True)
    def reset_circuit_breaker(self):
        """Reset the module-level circuit breaker before each test."""
        import hibiscus.tools.existing_api.client as client_mod
        client_mod._circuit = CircuitBreakerState()
        yield

    @pytest.mark.asyncio
    async def test_successful_call(self):
        """Happy path — API returns 200 with valid JSON."""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True, "data": "test"}

        with patch("hibiscus.tools.existing_api.client.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.request.return_value = mock_response
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            result = await call_existing_api("POST", "/api/v1/test", operation="default")
            assert result["success"] is True
            assert result["data"] == "test"

    @pytest.mark.asyncio
    async def test_server_error_raises(self):
        """500 error should raise ExistingAPIError."""
        mock_response = AsyncMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"

        with patch("hibiscus.tools.existing_api.client.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.request.return_value = mock_response
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            with pytest.raises(ExistingAPIError) as exc_info:
                await call_existing_api("POST", "/api/v1/test")
            assert exc_info.value.status_code == 500

    @pytest.mark.asyncio
    async def test_circuit_breaker_rejects_when_open(self):
        """When circuit is open, calls should be rejected immediately."""
        import hibiscus.tools.existing_api.client as client_mod
        for _ in range(CIRCUIT_BREAKER_THRESHOLD):
            client_mod._circuit.record_failure()

        with pytest.raises(ExistingAPIError) as exc_info:
            await call_existing_api("GET", "/api/v1/test")
        assert "Circuit breaker" in str(exc_info.value)


# ── Tool Wrapper Tests (mocked) ──────────────────────────────────────────────


class TestExtractionTool:
    @pytest.mark.asyncio
    async def test_extract_policy_success(self):
        mock_result = {
            "success": True,
            "policy_type": "health",
            "extraction": {"insurer": "Star Health", "sum_insured": 1000000},
            "confidence": 0.92,
            "doc_id": "doc_001",
        }
        with patch("hibiscus.tools.existing_api.extraction.call_existing_api", return_value=mock_result):
            result = await extract_policy("/path/to/policy.pdf", doc_id="doc_001")
            assert result["success"] is True
            assert result["policy_type"] == "health"
            assert result["confidence"] == 0.92

    @pytest.mark.asyncio
    async def test_extract_policy_failure_returns_error(self):
        with patch(
            "hibiscus.tools.existing_api.extraction.call_existing_api",
            side_effect=ExistingAPIError("Service unavailable"),
        ):
            result = await extract_policy("/path/to/policy.pdf")
            assert result["success"] is False
            assert "error" in result
            assert "message" in result


class TestScoringTool:
    @pytest.mark.asyncio
    async def test_calculate_score_success(self):
        mock_result = {
            "success": True,
            "eazr_score": 7.8,
            "percentile": 72,
        }
        with patch("hibiscus.tools.existing_api.scoring.call_existing_api", return_value=mock_result):
            result = await calculate_protection_score({"insurer": "Star Health"})
            assert result["success"] is True
            assert result["eazr_score"] == 7.8

    @pytest.mark.asyncio
    async def test_calculate_score_failure_graceful(self):
        with patch(
            "hibiscus.tools.existing_api.scoring.call_existing_api",
            side_effect=ExistingAPIError("Timeout"),
        ):
            result = await calculate_protection_score({})
            assert result["success"] is False


class TestReportingTool:
    @pytest.mark.asyncio
    async def test_generate_report_success(self):
        mock_result = {
            "success": True,
            "report_type": "comprehensive",
            "report": {"summary": "Good policy"},
        }
        with patch("hibiscus.tools.existing_api.reporting.call_existing_api", return_value=mock_result):
            result = await generate_report({"extraction": {}}, report_type="comprehensive")
            assert result["success"] is True
            assert result["report_type"] == "comprehensive"


class TestComplianceTool:
    @pytest.mark.asyncio
    async def test_check_compliance_success(self):
        mock_result = {
            "success": True,
            "compliant": True,
            "violations": [],
            "warnings": [{"check": "claim_timeline", "detail": "Not explicitly stated"}],
            "score": 0.90,
        }
        with patch("hibiscus.tools.existing_api.compliance.call_existing_api", return_value=mock_result):
            result = await check_irdai_compliance({"policy_type": "health"})
            assert result["success"] is True
            assert result["compliant"] is True
            assert result["score"] == 0.90


class TestBillingTool:
    @pytest.mark.asyncio
    async def test_audit_bill_success(self):
        mock_result = {
            "success": True,
            "total_billed": 250000,
            "total_eligible": 225000,
            "savings_identified": 25000,
            "overcharged_items": [{"item": "Gloves", "billed": 500, "benchmark": 50}],
        }
        with patch("hibiscus.tools.existing_api.billing.call_existing_api", return_value=mock_result):
            result = await audit_bill({"total": 250000})
            assert result["success"] is True
            assert result["savings_identified"] == 25000
            assert len(result["overcharged_items"]) == 1
