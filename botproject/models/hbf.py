"""
HBF (Hospital Bill Financing) Models
Pydantic models for bill financing eligibility, offers, and loan management.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
from datetime import datetime
from enum import Enum


# ============= Enums =============

class LoanType(str, Enum):
    HBF = "hbf"


class LoanStatus(str, Enum):
    PRE_QUALIFIED = "pre_qualified"
    OFFERS_GENERATED = "offers_generated"
    APPLIED = "applied"
    APPROVED = "approved"
    DISBURSED = "disbursed"
    REJECTED = "rejected"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


# ============= Request Models =============

class BaseHBFRequest(BaseModel):
    session_id: str
    user_id: int


class EligibilityCheckRequest(BaseHBFRequest):
    loan_type: LoanType
    amount: float
    audit_id: Optional[str] = None


class GetOffersRequest(BaseHBFRequest):
    loan_id: str


class ApplyLoanRequest(BaseHBFRequest):
    loan_id: str
    selected_offer_id: str


class CompleteLoanRequest(BaseHBFRequest):
    loan_id: str


# ============= Response Models =============

class EazrScoreBreakdown(BaseModel):
    total_score: int = 0
    factors: Dict[str, int] = Field(default_factory=dict)
    is_eligible: bool = False
    tier: str = ""
    message: str = ""


class LoanOffer(BaseModel):
    offer_id: str
    tenure_months: int
    interest_rate: float
    emi_amount: float
    total_payable: float
    processing_fee: float


class EligibilityResult(BaseModel):
    loan_id: str
    loan_type: LoanType
    is_eligible: bool
    eazr_score: EazrScoreBreakdown
    max_eligible_amount: float = 0.0
    indicative_rate_range: str = ""
    message: str = ""


class OffersResult(BaseModel):
    loan_id: str
    loan_type: LoanType
    amount: float
    offers: List[LoanOffer] = Field(default_factory=list)
    valid_until: Optional[datetime] = None


class LoanApplicationResult(BaseModel):
    loan_id: str
    status: LoanStatus
    selected_offer: Optional[LoanOffer] = None
    message: str = ""
    next_steps: List[str] = Field(default_factory=list)


class LoanStatusResult(BaseModel):
    loan_id: str
    loan_type: LoanType
    status: LoanStatus
    amount: float = 0.0
    tenure_months: int = 0
    interest_rate: float = 0.0
    emi_amount: float = 0.0
    total_payable: float = 0.0
    disbursement_date: Optional[datetime] = None
    next_emi_date: Optional[datetime] = None
    emis_paid: int = 0
    emis_remaining: int = 0
    outstanding_amount: float = 0.0
