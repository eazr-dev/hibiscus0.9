"""
Hospital Bill Audit Intelligence Models
Pydantic models for hospital bill audit, discrepancy detection, and savings calculation.
Based on EAZR India Hospital Bill Audit Spec v2.0 (No Government Rate Comparison)
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


# ============= Enums =============

class BillType(str, Enum):
    HOSPITAL = "hospital"


class HospitalType(str, Enum):
    GOVERNMENT = "government"
    MUNICIPAL = "municipal"
    TRUST = "trust"
    COOPERATIVE = "cooperative"
    PRIVATE_STANDALONE = "private_standalone"
    PRIVATE_CORPORATE_CHAIN = "private_corporate_chain"
    NURSING_HOME = "nursing_home"


class BillDocType(str, Enum):
    INTERIM = "interim"
    FINAL_DISCHARGE = "final_discharge"
    CASHLESS = "cashless"
    REIMBURSEMENT = "reimbursement"
    ESTIMATE = "estimate"
    PACKAGE = "package"
    DAYCARE = "daycare"


class AuditStatus(str, Enum):
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class CoverageStatus(str, Enum):
    COVERED = "covered"
    PARTIAL = "partial"
    NOT_COVERED = "not_covered"
    AT_RISK = "at_risk"


class DiscrepancyType(str, Enum):
    # Billing errors
    DUPLICATE_CHARGE = "DUPLICATE_CHARGE"
    CROSS_SECTION_DUPLICATE = "CROSS_SECTION_DUPLICATE"
    PHANTOM_CHARGE = "PHANTOM_CHARGE"
    CALCULATION_ERROR = "CALCULATION_ERROR"
    DATE_OUTSIDE_STAY = "DATE_OUTSIDE_STAY"
    # Overcharging
    PRICE_ABOVE_MRP = "PRICE_ABOVE_MRP"
    PACKAGE_VIOLATION = "PACKAGE_VIOLATION"
    INFLATED_QUANTITY = "INFLATED_QUANTITY"
    EXCESSIVE_QUANTITY = "EXCESSIVE_QUANTITY"
    # Unbundling & upcoding
    UNBUNDLED_PROCEDURE = "UNBUNDLED_PROCEDURE"
    UPCODED_PROCEDURE = "UPCODED_PROCEDURE"
    # Unnecessary services
    UNNECESSARY_TEST = "UNNECESSARY_TEST"
    REPEAT_TEST = "REPEAT_TEST"
    EXCESSIVE_CONSULTANT = "EXCESSIVE_CONSULTANT"
    # Compliance
    COMPLIMENTARY_CHARGED = "COMPLIMENTARY_CHARGED"
    NABH_VIOLATION = "NABH_VIOLATION"


class DiscrepancyCategory(str, Enum):
    BILLING_ERROR = "billing_error"
    OVERCHARGING = "overcharging"
    UNBUNDLING = "unbundling"
    UNNECESSARY = "unnecessary"
    COMPLIANCE = "compliance"
    INFORMATIONAL = "informational"


class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFORMATIONAL = "informational"


# ============= Data Models (Structured Extraction) =============

class BillLineItem(BaseModel):
    """Universal line item for any bill section."""
    voucher_or_serial_no: Optional[str] = None
    date: Optional[str] = None
    description: str = ""
    provider_or_doctor: Optional[str] = None
    patient_class: Optional[str] = None
    lab_no: Optional[str] = None
    quantity: float = 1.0
    unit_rate: float = 0.0
    amount: float = 0.0
    is_implant: Optional[bool] = None
    generic_name: Optional[str] = None


class BillSubsection(BaseModel):
    """A subsection within a bill section."""
    subsection_name: str = ""
    line_items: List[BillLineItem] = Field(default_factory=list)
    subsection_subtotal: float = 0.0
    calculated_subtotal: float = 0.0


class BillSection(BaseModel):
    """A section in the hospital bill (dynamic — matches bill's own headings)."""
    section_name: str = ""
    subsections: List[BillSubsection] = Field(default_factory=list)
    section_subtotal: float = 0.0
    calculated_section_total: float = 0.0


class HospitalContext(BaseModel):
    """Hospital identification and classification."""
    hospital_name: str = ""
    hospital_type: str = ""
    city: str = ""
    state: str = ""
    nabh_accredited: bool = False


class BillMetadata(BaseModel):
    """Bill document metadata."""
    hospital_name: str = ""
    hospital_address: str = ""
    hospital_city: str = ""
    hospital_state: str = ""
    hospital_pincode: str = ""
    hospital_type: str = ""
    registration_number: str = ""
    pan_number: str = ""
    gst_number: str = ""
    bill_number: str = ""
    bill_date: str = ""
    bill_type: str = ""


class PatientDetails(BaseModel):
    """Patient and admission details."""
    patient_name: str = ""
    uhid: str = ""
    ip_number: str = ""
    age: Optional[int] = None
    gender: str = ""
    admission_date: str = ""
    admission_time: str = ""
    discharge_date: str = ""
    discharge_time: str = ""
    los_days: int = 0
    primary_diagnosis: str = ""
    secondary_diagnosis: str = ""
    procedure_performed: str = ""
    surgery_grade: str = ""
    treating_doctor: str = ""
    surgeon_name: str = ""
    anaesthetist_name: str = ""
    admission_type: str = ""
    discharge_status: str = ""
    patient_class: str = ""
    bed_number: str = ""
    ward_name: str = ""
    company_payer: str = ""
    policy_number: str = ""
    deposit_paid: float = 0.0


class BillSummary(BaseModel):
    """Financial summary of the bill."""
    gross_amount: float = 0.0
    gst_amount: float = 0.0
    discount: float = 0.0
    tpa_approved: float = 0.0
    tpa_deductions: float = 0.0
    copay: float = 0.0
    non_payable_by_insurer: float = 0.0
    advance_deposit_paid: float = 0.0
    refund_due: float = 0.0
    patient_payable: float = 0.0
    total_outstanding: float = 0.0
    payment_mode: str = ""


class SubtotalCheck(BaseModel):
    """Validation check for a section subtotal."""
    section: str = ""
    calculated_sum: float = 0.0
    bill_subtotal: float = 0.0
    match: bool = True
    difference: float = 0.0


class GrandTotalCheck(BaseModel):
    """Validation check for grand total."""
    calculated_sum_of_sections: float = 0.0
    bill_grand_total: float = 0.0
    match: bool = True
    difference: float = 0.0


class ExtractionValidation(BaseModel):
    """Phase 3 extraction validation results."""
    subtotal_checks: List[SubtotalCheck] = Field(default_factory=list)
    grand_total_check: Optional[GrandTotalCheck] = None
    column_confusion_flags: List[str] = Field(default_factory=list)
    date_consistency: bool = True
    los_room_charge_match: bool = True
    extraction_confidence: str = "medium"
    confidence_reason: str = ""


class HospitalBillData(BaseModel):
    """Complete hospital bill data with dynamic sections."""
    hospital_context: HospitalContext = Field(default_factory=HospitalContext)
    metadata: BillMetadata = Field(default_factory=BillMetadata)
    patient_details: PatientDetails = Field(default_factory=PatientDetails)
    bill_sections: List[BillSection] = Field(default_factory=list)
    bill_summary: BillSummary = Field(default_factory=BillSummary)
    extraction_validation: ExtractionValidation = Field(default_factory=ExtractionValidation)


# ============= Coverage Matching Models =============

class CoverageLineItemResult(BaseModel):
    description: str
    billed_amount: float
    covered_amount: float
    excess_amount: float = 0.0
    status: CoverageStatus
    reason: str
    policy_clause: Optional[str] = None
    triggers_proportionate_deduction: bool = False


class CoverageMatchResult(BaseModel):
    total_bill_amount: float = 0.0
    total_covered: float = 0.0
    total_not_covered: float = 0.0
    copay_amount: float = 0.0
    deductible_amount: float = 0.0
    estimated_out_of_pocket: float = 0.0
    si_available: float = 0.0
    si_remaining_after: float = 0.0
    si_exhaustion_warning: bool = False
    coverage_percentage: float = 0.0
    proportionate_deduction_warning: bool = False
    line_items: List[CoverageLineItemResult] = Field(default_factory=list)


# ============= Discrepancy Models =============

class Discrepancy(BaseModel):
    id: str
    type: DiscrepancyType
    category: DiscrepancyCategory
    severity: Severity
    description: str
    item_name: str = ""
    section_found_in: str = ""
    line_items_involved: List[str] = Field(default_factory=list)
    billed_amount: float = 0.0
    benchmark_amount: Optional[float] = None
    benchmark_source: str = ""
    overcharged_amount: float = 0.0
    confidence: float = 0.0
    confidence_category: str = ""
    applicable_law: str = ""
    action: str = ""


# ============= Savings Models =============

class SavingsResult(BaseModel):
    total_discrepancy_amount: float = 0.0
    high_confidence_savings: float = 0.0
    medium_confidence_savings: float = 0.0
    low_confidence_savings: float = 0.0
    conservative_estimate: float = 0.0
    moderate_estimate: float = 0.0
    optimistic_estimate: float = 0.0
    breakdown_by_type: Dict[str, float] = Field(default_factory=dict)
    items_to_dispute: int = 0
    dispute_priority_order: List[str] = Field(default_factory=list)


# ============= Bill Health Score =============

class BillHealthScore(BaseModel):
    score: int = 0
    grade: str = ""
    interpretation: str = ""
    factors: Dict[str, int] = Field(default_factory=dict)


# ============= Full Audit Result =============

class BillAuditResult(BaseModel):
    audit_id: str
    audit_version: str = "2.0-india-no-govt-benchmark"
    bill_type: BillType = BillType.HOSPITAL
    status: AuditStatus
    hospital_context: Optional[HospitalContext] = None
    bill_data: Dict[str, Any] = Field(default_factory=dict)
    extraction_validation: Optional[ExtractionValidation] = None
    coverage_analysis: Optional[CoverageMatchResult] = None
    discrepancies: List[Discrepancy] = Field(default_factory=list)
    savings: Optional[SavingsResult] = None
    bill_health_score: Optional[BillHealthScore] = None
    limitations: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    report_url: Optional[str] = None
    dispute_letter_url: Optional[str] = None
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


# ============= Request Models =============

class BaseBillAuditRequest(BaseModel):
    session_id: str
    user_id: int


class GetAuditRequest(BaseBillAuditRequest):
    audit_id: str


class GenerateReportRequest(BaseBillAuditRequest):
    audit_id: str
    include_dispute_letter: bool = False
