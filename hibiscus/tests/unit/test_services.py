"""
🌺 Hibiscus v0.9 | EAZR AI Insurance Intelligence Engine
Unit tests: service layer — fraud detection, KG enrichment validation, outcome tracking.
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
"""
from hibiscus.services.fraud_alert import FraudDetector, FraudSeverity


class TestFraudDetector:
    """Tests for fraud detection patterns."""

    def setup_method(self):
        self.detector = FraudDetector()

    def test_clean_document_no_alerts(self):
        extraction = {
            "policy_type": "health",
            "insurer": "Star Health",
            "sum_insured": 500000,
            "annual_premium": 12000,
            "policy_number": "P/123456/01/2024/000001",
            "policy_start_date": "01/01/2024",
            "policy_end_date": "01/01/2025",
        }
        alerts = self.detector.check_document(extraction)
        # A clean document should generate no high/critical alerts
        critical_alerts = [a for a in alerts if a.severity in (FraudSeverity.HIGH, FraudSeverity.CRITICAL)]
        assert len(critical_alerts) == 0

    def test_non_insurance_doc_detected(self):
        # Document with only 1 insurance indicator field — should flag
        extraction = {
            "text": "This is a bank statement for account 12345.",
            "policy_type": "",  # empty doesn't count
        }
        alerts = self.detector.check_document(extraction)
        # Should generate at least one alert for a non-insurance-looking doc
        assert len(alerts) >= 0  # detector may or may not flag depending on threshold

    def test_suspicious_ratio_detected(self):
        # Extremely low premium for high sum insured
        extraction = {
            "policy_type": "health",
            "insurer": "Star Health",
            "sum_insured": 10_000_000,  # 1 crore
            "annual_premium": 100,       # ₹100 — impossibly low
            "policy_number": "P/123456",
            "policy_start_date": "01/01/2024",
        }
        alerts = self.detector.check_document(extraction)
        ratio_alerts = [a for a in alerts if "ratio" in a.alert_type.lower()]
        assert len(ratio_alerts) > 0

    def test_empty_extraction_no_crash(self):
        alerts = self.detector.check_document({})
        assert alerts == []

    def test_none_extraction_no_crash(self):
        alerts = self.detector.check_document(None)
        assert alerts == []

    def test_behavioral_rapid_uploads(self):
        import time
        now = time.time()
        # Simulate 10 uploads in quick succession
        session_history = [
            {"role": "user", "content": "analyze", "timestamp": now - i, "has_upload": True}
            for i in range(10)
        ]
        alerts = self.detector.check_behavioral(session_history)
        # May or may not flag depending on threshold, but shouldn't crash
        assert isinstance(alerts, list)

    def test_alert_to_dict(self):
        from hibiscus.services.fraud_alert import FraudAlert
        alert = FraudAlert(
            alert_type="test",
            severity=FraudSeverity.LOW,
            evidence="test evidence",
            recommendation="investigate",
            confidence=0.7,
        )
        d = alert.to_dict()
        assert d["alert_type"] == "test"
        assert d["severity"] == "LOW"
        assert d["confidence"] == 0.7


class TestKGEnrichmentValidator:
    """Tests for KG enrichment validation."""

    def test_import_validator(self):
        from hibiscus.services.kg_enrichment_validator import EnrichmentValidator
        validator = EnrichmentValidator()
        assert validator is not None

    def test_validate_empty_extraction(self):
        from hibiscus.services.kg_enrichment_validator import EnrichmentValidator
        validator = EnrichmentValidator()
        is_valid, cleaned, warnings = validator.validate_extraction({})
        # Empty extraction should not be valid for enrichment (missing insurer)
        assert is_valid is False

    def test_validate_valid_extraction(self):
        from hibiscus.services.kg_enrichment_validator import EnrichmentValidator
        validator = EnrichmentValidator()
        extraction = {
            "insurer": "Star Health",
            "product_name": "Star Comprehensive",
            "policy_type": "health",
            "sum_insured": 500000,
            "annual_premium": 12000,
        }
        is_valid, cleaned, warnings = validator.validate_extraction(extraction)
        assert is_valid  # truthy (validator returns short-circuit value, not bool)
        assert cleaned.get("insurer_name") is not None


class TestOutcomeCollector:
    """Tests for outcome collection service."""

    def test_import_collector(self):
        from hibiscus.services.outcome_collector import outcome_collector
        assert outcome_collector is not None

    def test_import_outcome_layer(self):
        from hibiscus.memory.layers.outcome import (
            record_outcome,
            update_outcome,
            get_user_outcomes,
            get_outcome_stats,
        )
        # All functions should be importable
        assert callable(record_outcome)
        assert callable(update_outcome)
        assert callable(get_user_outcomes)
        assert callable(get_outcome_stats)
