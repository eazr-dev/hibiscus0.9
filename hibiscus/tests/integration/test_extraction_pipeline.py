"""
Integration test for the native extraction pipeline.

Tests the full flow: ProcessedDocument → classify → validate → score → gap analyze.
Extraction step is mocked (requires LLM), but all other steps run for real.
"""
import pytest

from hibiscus.extraction.processor import ProcessedDocument, PageContent
from hibiscus.extraction.classifier import PolicyClassifier, ClassificationResult
from hibiscus.extraction.extractors.base import BaseExtractor
from hibiscus.extraction.validation import ValidationEngine
from hibiscus.extraction.scoring import ScoringEngine
from hibiscus.extraction.gap_analysis import GapAnalysisEngine


def _cf(value, source_page=1, confidence=0.95):
    return {"value": value, "source_page": source_page, "confidence": confidence}


def _build_health_document() -> ProcessedDocument:
    """Build a realistic health policy ProcessedDocument."""
    page1 = PageContent(
        page_num=1,
        text=(
            "Star Health and Allied Insurance Company Limited\n"
            "Family Health Optima Insurance Policy\n"
            "Policy Number: P/123/2024/012345\n"
            "UIN: 567NHLIP00234\n"
            "Policy Type: Family Floater\n"
            "Sum Insured: ₹10,00,000\n"
            "Premium: ₹18,500 + GST ₹3,330 = ₹21,830\n"
            "Policy Period: 01/04/2025 to 31/03/2026\n"
            "Insured Members: Self (35M), Spouse (32F), Child (5M)\n"
        ),
    )
    page2 = PageContent(
        page_num=2,
        text=(
            "Room Rent: No Capping (All categories allowed)\n"
            "ICU Charges: No Capping\n"
            "Co-payment: Nil\n"
            "Restoration Benefit: 100% of Sum Insured\n"
            "Pre-existing Disease Waiting Period: 36 months\n"
            "Specific Disease Waiting: 24 months\n"
            "No Claim Bonus: 25% (Cumulative)\n"
            "Network Hospitals: 14,000+\n"
            "Cashless Facility: Available\n"
            "Day Care Procedures: Covered (580+ procedures)\n"
            "Ambulance Cover: ₹5,000 per hospitalization\n"
            "AYUSH Treatment: Covered\n"
            "Modern Treatment: Covered up to SI\n"
            "Consumables: Covered\n"
        ),
    )
    page3 = PageContent(
        page_num=3,
        text=(
            "Pre-hospitalization: 60 days\n"
            "Post-hospitalization: 90 days\n"
            "Domiciliary Hospitalization: Covered\n"
            "Health Checkup: Annual after 2 claim-free years\n"
            "Maternity: Available after 36 months waiting\n"
            "Bariatric Surgery: Not Covered\n"
            "Genetic Disorders: Not Covered\n"
        ),
    )
    return ProcessedDocument(
        pages=[page1, page2, page3],
        total_pages=3,
        extraction_method="digital",
    )


def _build_motor_document() -> ProcessedDocument:
    """Build a realistic motor policy ProcessedDocument."""
    page1 = PageContent(
        page_num=1,
        text=(
            "ICICI Lombard General Insurance Company\n"
            "Motor Comprehensive Insurance Policy\n"
            "Policy Number: 1234/OG/2025/1234567\n"
            "Registration Number: MH02AB1234\n"
            "Engine Number: K10B1234567\n"
            "Chassis Number: MABCD12345EF67890\n"
            "Vehicle Make: Maruti Suzuki\n"
            "Vehicle Model: Swift VXI\n"
            "Year of Manufacture: 2022\n"
            "IDV: ₹5,50,000\n"
            "Total Premium: ₹18,450 (incl. GST)\n"
        ),
    )
    return ProcessedDocument(
        pages=[page1],
        total_pages=1,
        extraction_method="digital",
    )


# ── Classification Tests ──────────────────────────────────────────────


class TestClassificationIntegration:
    @pytest.mark.asyncio
    async def test_health_document_classification(self):
        doc = _build_health_document()
        classifier = PolicyClassifier()
        result = await classifier.classify(doc.first_pages_text)
        assert result.category == "health"
        assert result.confidence >= 0.85
        assert result.tier_used == 1  # UIN hit

    @pytest.mark.asyncio
    async def test_motor_document_classification(self):
        doc = _build_motor_document()
        classifier = PolicyClassifier()
        result = await classifier.classify(doc.first_pages_text)
        assert result.category == "motor"
        assert result.confidence >= 0.85


# ── Full Pipeline (with mocked extraction) ────────────────────────────


class TestFullPipeline:
    """Full pipeline: classify → (mock) extract → validate → score → gap."""

    @pytest.mark.asyncio
    async def test_health_full_pipeline(self):
        doc = _build_health_document()

        # Step 1: Classify
        classifier = PolicyClassifier()
        classification = await classifier.classify(doc.first_pages_text)
        assert classification.category == "health"

        # Step 2: Mock extraction (simulates what LLM would return)
        extraction = {
            "insurerName": _cf("Star Health", 1),
            "policyNumber": _cf("P/123/2024/012345", 1),
            "uin": _cf("567NHLIP00234", 1),
            "policyType": _cf("Family Floater", 1),
            "sumInsured": _cf(1000000, 1),
            "basePremium": _cf(18500, 1),
            "gst": _cf(3330, 1),
            "totalPremium": _cf(21830, 1),
            "policyPeriodStart": _cf("2025-04-01", 1),
            "policyPeriodEnd": _cf("2026-03-31", 1),
            "totalMembersCovered": _cf(3, 1),
            "coverType": _cf("Family Floater", 1),
            "roomRentLimit": _cf("No Capping", 2),
            "icuLimit": _cf("No Capping", 2),
            "generalCopay": _cf(0, 2),
            "restoration": _cf("100%", 2),
            "preExistingDiseaseWaiting": _cf("36 months", 2),
            "specificDiseaseWaiting": _cf("24 months", 2),
            "ncbPercentage": _cf(25, 2),
            "networkHospitalsCount": _cf(14000, 2),
            "cashlessFacility": _cf(True, 2),
            "dayCareProcedures": _cf("580+ procedures", 2),
            "ambulanceCover": _cf("₹5,000", 2),
            "ayushTreatment": _cf("Covered", 2),
            "modernTreatment": _cf("Covered", 2),
            "consumablesCoverage": _cf(True, 2),
            "preHospitalization": _cf("60 days", 3),
            "postHospitalization": _cf("90 days", 3),
            "domiciliaryHospitalization": _cf("Covered", 3),
            "healthCheckup": _cf("Annual", 3),
            "maternityWaiting": _cf("36 months", 3),
        }

        # Step 3: Validate
        validator = ValidationEngine()
        validation = await validator.validate(extraction, "health")
        assert validation.score >= 60
        assert validation.weighted_confidence >= 0.6

        # Step 4: Score
        scorer = ScoringEngine()
        score_result = await scorer.score(extraction, "health")
        assert score_result.eazr_score > 0
        assert len(score_result.components) == 4
        assert score_result.verdict != ""
        assert score_result.zone_classification["roomRent"] == "green"
        assert score_result.zone_classification["copay"] == "green"

        # Step 5: Gap analysis
        gap_engine = GapAnalysisEngine()
        gaps = await gap_engine.analyze(extraction, score_result, "health")
        assert gaps.total_gaps >= 0
        # This policy has 36mo PED waiting → should flag
        ped_gaps = [g for g in gaps.gaps if g.category == "PED Waiting"]
        # 36 months is not flagged (only 48 months is flagged)
        assert len(ped_gaps) == 0

    @pytest.mark.asyncio
    async def test_motor_full_pipeline(self):
        doc = _build_motor_document()

        # Classify
        classifier = PolicyClassifier()
        classification = await classifier.classify(doc.first_pages_text)
        assert classification.category == "motor"

        # Mock extraction
        extraction = {
            "insurerName": _cf("ICICI Lombard", 1),
            "policyNumber": _cf("1234/OG/2025/1234567", 1),
            "registrationNumber": _cf("MH02AB1234", 1),
            "engineNumber": _cf("K10B1234567", 1),
            "chassisNumber": _cf("MABCD12345EF67890", 1),
            "vehicleMake": _cf("Maruti Suzuki", 1),
            "vehicleModel": _cf("Swift VXI", 1),
            "yearOfManufacture": _cf(2022, 1),
            "idv": _cf(550000, 1),
            "totalPremium": _cf(18450, 1),
            "productType": _cf("Comprehensive", 1),
            "ncbPercentage": _cf(25),
        }

        # Validate
        validator = ValidationEngine()
        validation = await validator.validate(extraction, "motor")
        assert validation.score >= 50

        # Score
        scorer = ScoringEngine()
        score_result = await scorer.score(extraction, "motor")
        assert score_result.eazr_score > 0
        assert len(score_result.components) == 5

        # Gaps
        gap_engine = GapAnalysisEngine()
        gaps = await gap_engine.analyze(extraction, score_result, "motor")
        # No zero dep → at least one gap
        zd_gaps = [g for g in gaps.gaps if g.category == "Zero Depreciation"]
        assert len(zd_gaps) == 1


# ── ProcessedDocument Tests ───────────────────────────────────────────


class TestProcessedDocument:
    def test_full_text_has_page_markers(self):
        doc = _build_health_document()
        assert "[PAGE 1]" in doc.full_text
        assert "[PAGE 2]" in doc.full_text
        assert "[PAGE 3]" in doc.full_text

    def test_first_pages_text_limited(self):
        doc = _build_health_document()
        text = doc.first_pages_text
        assert "[PAGE 1]" in text
        assert "[PAGE 3]" in text  # Exactly 3 pages

    def test_char_count(self):
        doc = _build_health_document()
        assert doc.char_count > 100


# ── Base Extractor JSON Recovery ──────────────────────────────────────


class TestJsonRecovery:
    def test_clean_json(self):
        extractor = BaseExtractor()
        content = '{"insurerName": {"value": "Star", "confidence": 0.9}}'
        result = extractor._parse_response(content)
        assert result["insurerName"]["value"] == "Star"

    def test_markdown_wrapped_json(self):
        extractor = BaseExtractor()
        content = '```json\n{"key": "value"}\n```'
        result = extractor._parse_response(content)
        assert result["key"] == "value"

    def test_trailing_comma_repair(self):
        extractor = BaseExtractor()
        content = '{"key": "value",}'
        result = extractor._parse_response(content)
        assert result["key"] == "value"

    def test_unmatched_brace_repair(self):
        extractor = BaseExtractor()
        content = '{"key": {"nested": "value"}'
        result = extractor._parse_response(content)
        assert result["key"]["nested"] == "value"

    def test_empty_on_garbage(self):
        extractor = BaseExtractor()
        content = "this is not json at all"
        result = extractor._parse_response(content)
        assert result == {}


# ── Normalize Fields ──────────────────────────────────────────────────


class TestNormalizeFields:
    def test_cf_format_preserved(self):
        extractor = BaseExtractor()
        data = {"field1": {"value": "test", "source_page": 1, "confidence": 0.9}}
        result = extractor._normalize_fields(data)
        assert result["field1"]["value"] == "test"
        assert result["field1"]["source_page"] == 1
        assert result["field1"]["confidence"] == 0.9

    def test_bare_value_wrapped(self):
        extractor = BaseExtractor()
        data = {"field1": "bare_value"}
        result = extractor._normalize_fields(data)
        assert result["field1"]["value"] == "bare_value"
        assert result["field1"]["source_page"] is None
        assert result["field1"]["confidence"] == 0.5

    def test_mixed_fields(self):
        extractor = BaseExtractor()
        data = {
            "cf_field": {"value": 100, "source_page": 2, "confidence": 0.95},
            "bare_field": 200,
        }
        result = extractor._normalize_fields(data)
        assert result["cf_field"]["confidence"] == 0.95
        assert result["bare_field"]["value"] == 200
        assert result["bare_field"]["confidence"] == 0.5
