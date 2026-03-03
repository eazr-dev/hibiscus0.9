"""
Policy Locker Module - Pydantic Models
Comprehensive models for Policy Locker, Family Management, Claims, and Emergency Services
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# ==================== ENUMS ====================

class InsuranceCategory(str, Enum):
    HEALTH = "health"
    LIFE = "life"
    MOTOR = "motor"
    GENERAL = "general"
    AGRICULTURAL = "agricultural"
    BUSINESS = "business"
    SPECIALTY = "specialty"
    OTHER = "other"


class PolicyStatus(str, Enum):
    ACTIVE = "Active"
    EXPIRING_SOON = "Expiring Soon"
    EXPIRED = "Expired"
    INACTIVE = "Inactive"


class PremiumType(str, Enum):
    ANNUAL = "Annual"
    MONTHLY = "Monthly"
    SINGLE = "Single"
    QUARTERLY = "Quarterly"


class Gender(str, Enum):
    MALE = "Male"
    FEMALE = "Female"
    OTHER = "Other"


class GapSeverity(str, Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class GapType(str, Enum):
    WARNING = "warning"
    INFO = "info"
    RECOMMENDATION = "recommendation"
    POSITIVE = "positive"


class ClaimStatus(str, Enum):
    INITIATED = "initiated"
    PENDING = "pending"
    PROCESSING = "processing"
    APPROVED = "approved"
    REJECTED = "rejected"
    SETTLED = "settled"


class ShareMethod(str, Enum):
    EMAIL = "email"
    LINK = "link"
    PRINT = "print"


class ExportFormat(str, Enum):
    PDF = "pdf"
    XLSX = "xlsx"


# ==================== BASE REQUEST MODELS ====================

class BaseLockerRequest(BaseModel):
    """Base request with session authentication"""
    session_id: str
    user_id: int


class BaseLockerRequestWithToken(BaseLockerRequest):
    """Base request with access token"""
    access_token: Optional[str] = None


# ==================== POLICY MODELS ====================

class CategorySpecificData(BaseModel):
    """Category-specific policy details - varies by insurance type"""
    # Health Insurance
    roomRentLimit: Optional[str] = None
    coPayment: Optional[str] = None
    preDiseaseWaitingPeriod: Optional[str] = None
    preExistingWaitingPeriod: Optional[str] = None
    cumulativeBonus: Optional[str] = None
    maternityBenefit: Optional[bool] = None
    maternityCover: Optional[str] = None
    prePostHospitalization: Optional[bool] = None
    prePostDays: Optional[str] = None
    dayCareProcedures: Optional[bool] = None
    ambulanceCover: Optional[bool] = None
    ambulanceLimit: Optional[str] = None
    networkHospitals: Optional[List[str]] = None
    restoration: Optional[bool] = None
    restorationAmount: Optional[str] = None

    # Life Insurance
    sumAssured: Optional[str] = None
    maturityAmount: Optional[str] = None
    bonusAccumulated: Optional[str] = None
    riders: Optional[List[str]] = None
    policyTerm: Optional[str] = None
    premiumPayingTerm: Optional[str] = None
    surrenderValue: Optional[str] = None
    loanAvailable: Optional[str] = None
    nominees: Optional[List[str]] = None
    deathBenefit: Optional[str] = None

    # Motor Insurance
    vehicleRegistrationNumber: Optional[str] = None
    vehicleMake: Optional[str] = None
    vehicleModel: Optional[str] = None
    yearOfManufacture: Optional[str] = None
    engineNumber: Optional[str] = None
    chassisNumber: Optional[str] = None
    vehicleType: Optional[str] = None
    zeroDepreciation: Optional[bool] = None
    engineProtection: Optional[bool] = None
    returnToInvoice: Optional[bool] = None
    roadsideAssistance: Optional[bool] = None
    passengerCover: Optional[bool] = None
    ncbPercentage: Optional[str] = None
    ownDamage: Optional[bool] = None
    thirdPartyOnly: Optional[bool] = None
    geographicalCoverage: Optional[str] = None

    # Home Insurance
    propertyAddress: Optional[str] = None
    propertyType: Optional[str] = None
    buildingCover: Optional[str] = None
    contentsCover: Optional[str] = None
    earthquakeCover: Optional[bool] = None
    floodCover: Optional[bool] = None
    theftCover: Optional[bool] = None
    fireCover: Optional[bool] = None
    personalAccidentCover: Optional[bool] = None
    liabilityCover: Optional[str] = None
    valuables: Optional[List[str]] = None

    # Travel Insurance
    destination: Optional[str] = None
    travelStartDate: Optional[str] = None
    travelEndDate: Optional[str] = None
    tripType: Optional[str] = None
    medicalCover: Optional[str] = None
    flightDelayCover: Optional[bool] = None
    baggageLossCover: Optional[bool] = None
    passportLossCover: Optional[bool] = None
    tripCancellation: Optional[bool] = None
    emergencyEvacuation: Optional[str] = None
    coveredCountries: Optional[List[str]] = None

    # Personal Accident
    accidentalDeathBenefit: Optional[str] = None
    permanentDisabilityBenefit: Optional[str] = None
    temporaryDisabilityBenefit: Optional[str] = None
    medicalExpenseCover: Optional[str] = None
    educationBenefit: Optional[bool] = None
    childEducationAmount: Optional[str] = None
    hospitalCashBenefit: Optional[bool] = None
    dailyCashAmount: Optional[str] = None
    coveredActivities: Optional[List[str]] = None

    # Critical Illness
    coveredIllnesses: Optional[List[str]] = None
    lumpsumBenefit: Optional[str] = None
    waitingPeriod: Optional[str] = None
    survivalPeriod: Optional[str] = None
    multipleClaims: Optional[bool] = None
    maxClaimCount: Optional[int] = None
    incomeBenefit: Optional[bool] = None
    monthlyIncome: Optional[str] = None

    # Business Insurance
    businessName: Optional[str] = None
    businessType: Optional[str] = None
    propertyValue: Optional[str] = None
    liabilityLimit: Optional[str] = None
    employeeCover: Optional[bool] = None
    coveredEmployees: Optional[int] = None
    cyberLiability: Optional[bool] = None
    dataBreachCover: Optional[str] = None
    businessInterruption: Optional[bool] = None
    lossOfIncomeLimit: Optional[str] = None
    coveredRisks: Optional[List[str]] = None

    # Crop Insurance
    cropType: Optional[str] = None
    areaInAcres: Optional[str] = None
    seasonType: Optional[str] = None
    coveredPerils: Optional[List[str]] = None
    preventedSowing: Optional[bool] = None
    midSeasonAdversity: Optional[bool] = None
    postHarvestLoss: Optional[bool] = None
    claimSettlementLevel: Optional[str] = None

    class Config:
        extra = "allow"  # Allow additional fields


class PolicySummary(BaseModel):
    """Policy summary for list views"""
    id: str
    policyNumber: str
    provider: str
    category: InsuranceCategory
    subType: Optional[str] = None
    policyHolderName: str
    startDate: str
    expiryDate: str
    premium: str
    premiumType: PremiumType
    coverageAmount: str
    idv: Optional[str] = None
    status: PolicyStatus
    protectionScore: int = Field(ge=0, le=100)
    needsAction: bool = False
    actionMessage: Optional[str] = None
    insuredMembers: int = 1
    categorySpecificData: Optional[Dict[str, Any]] = None


class PolicyDetails(PolicySummary):
    """Full policy details"""
    keyBenefits: List[str] = []
    coverageGaps: List[str] = []
    exclusions: List[str] = []
    documents: List[str] = []
    insuredMemberNames: List[str] = []
    categorySpecificData: Optional[CategorySpecificData] = None


# ==================== LOCKER API MODELS ====================

class GetSelfPoliciesRequest(BaseLockerRequest):
    """Request to get user's own policies"""
    category: Optional[InsuranceCategory] = None
    status: Optional[PolicyStatus] = None
    page: int = 1
    limit: int = 20


class PaginationInfo(BaseModel):
    """Pagination metadata"""
    currentPage: int
    totalPages: int
    totalCount: int


class GetPoliciesResponse(BaseModel):
    """Response for policy list"""
    success: bool
    data: Dict[str, Any]  # Contains policies and pagination


class LockerSummary(BaseModel):
    """Summary statistics for locker"""
    totalPolicies: int
    activePolicies: int
    expiringPolicies: int
    totalCoverage: str
    averageProtectionScore: int


class CategoryBreakdown(BaseModel):
    """Category-wise coverage breakdown"""
    category: str
    displayName: str
    policyCount: int
    totalCoverage: str
    coveragePercentage: float


class PortfolioStatistics(BaseModel):
    """Portfolio statistics response"""
    categoryBreakdown: List[CategoryBreakdown]
    totalCoverage: str


# ==================== FAMILY MEMBER MODELS ====================

class FamilyMemberSummary(BaseModel):
    """Family member with policy summary"""
    id: str
    name: str
    relation: str
    avatar: Optional[str] = None
    gender: Optional[Gender] = None
    dateOfBirth: Optional[str] = None
    policiesCount: int = 0
    totalCoverage: str = "0"
    protectionScore: int = 0


class FamilySummary(BaseModel):
    """Family overview summary"""
    totalMembers: int
    totalPolicies: int
    totalCoverage: str


class AddFamilyMemberRequest(BaseLockerRequest):
    """Request to add a family member"""
    name: str
    relationship: str
    dateOfBirth: Optional[str] = None
    gender: Optional[Gender] = None


class UpdateFamilyMemberRequest(BaseLockerRequest):
    """Request to update a family member"""
    member_id: str
    name: Optional[str] = None
    relationship: Optional[str] = None
    dateOfBirth: Optional[str] = None
    gender: Optional[Gender] = None


class RelationshipType(BaseModel):
    """Relationship type option"""
    id: str
    label: str
    icon: Optional[str] = None


# ==================== UPLOAD & ANALYSIS MODELS ====================

class UploadPolicyRequest(BaseLockerRequest):
    """Request metadata for policy upload"""
    memberId: Optional[str] = None
    isForSelf: bool = True


class UploadPolicyResponse(BaseModel):
    """Response after uploading policy document"""
    success: bool
    data: Dict[str, Any]


class AnalyzePolicyRequest(BaseLockerRequest):
    """Request to analyze uploaded policy"""
    uploadId: str
    memberId: Optional[str] = None
    memberName: Optional[str] = None
    memberDOB: Optional[str] = None
    memberGender: Optional[Gender] = None
    relationship: Optional[str] = None


class GapAnalysisItem(BaseModel):
    """Individual gap analysis item"""
    type: GapType
    title: str
    description: str
    severity: GapSeverity
    icon: Optional[str] = None


class AnalysisGapItem(BaseModel):
    """Gap item in analysis result"""
    title: str
    status: str  # "Missing", "Limited", "Covered"
    severity: GapSeverity
    recommendation: Optional[str] = None


class AnalysisResult(BaseModel):
    """Policy analysis result"""
    status: str  # "completed", "processing", "failed"
    extractedData: Optional[Dict[str, Any]] = None
    protectionScore: Optional[int] = None
    gapAnalysis: List[AnalysisGapItem] = []
    keyFeatures: List[str] = []
    confidence: Optional[float] = None


class ConfirmPolicyRequest(BaseLockerRequest):
    """Request to confirm and save analyzed policy"""
    analysisId: str
    memberId: Optional[str] = None
    corrections: Optional[Dict[str, str]] = None


# ==================== GAP ANALYSIS & RECOMMENDATIONS ====================

class PolicyGapAnalysis(BaseModel):
    """Complete gap analysis for a policy"""
    gaps: List[GapAnalysisItem]
    overallScore: int
    recommendations: List[str]


class RecommendationItem(BaseModel):
    """Policy recommendation"""
    id: str
    title: str
    description: str
    type: str  # "upgrade", "addon", "new_policy"
    priority: GapSeverity
    estimatedCost: Optional[str] = None


class AnalysisReportInsight(BaseModel):
    """Insight in analysis report"""
    type: str  # "positive", "warning", "info"
    title: str
    description: str


class AnalysisReportRecommendation(BaseModel):
    """Recommendation in analysis report"""
    action: str
    priority: GapSeverity
    potential_benefit: str


class AnalysisReport(BaseModel):
    """Comprehensive analysis report"""
    generatedAt: str
    coverageAmount: str
    protectionScore: int
    insights: List[AnalysisReportInsight]
    recommendations: List[AnalysisReportRecommendation]


# ==================== EMERGENCY SERVICES MODELS ====================

class EmergencyCategory(BaseModel):
    """Emergency service category"""
    id: str
    title: str
    description: str
    icon: Optional[str] = None


class EmergencyContact(BaseModel):
    """Emergency contact"""
    id: str
    name: str
    number: str
    description: Optional[str] = None
    isEmergency: bool = True


# ==================== CLAIMS MODELS ====================

class ClaimType(BaseModel):
    """Claim type option"""
    id: str
    title: str
    description: Optional[str] = None
    icon: Optional[str] = None


class RequiredDocument(BaseModel):
    """Required document for claim"""
    id: str
    name: str
    description: Optional[str] = None
    isMandatory: bool = True


class InitiateClaimRequest(BaseLockerRequest):
    """Request to initiate a claim"""
    policyId: str
    claimType: str
    description: str
    documents: List[str] = []  # List of uploadIds


class ClaimResponse(BaseModel):
    """Claim initiation response"""
    claimId: str
    claimNumber: str
    status: ClaimStatus
    nextSteps: List[str] = []


# ==================== RENEWAL MODELS ====================

class RenewalDiscount(BaseModel):
    """Renewal discount"""
    type: str  # "NCB", "Loyalty", "Early"
    amount: str
    description: str


class RenewalBenefit(BaseModel):
    """Renewal benefit"""
    title: str
    description: str


class RenewalQuote(BaseModel):
    """Renewal quote details"""
    policyId: str
    currentPremium: str
    renewalPremium: str
    basePremium: str
    taxes: str
    totalPremium: str
    expiryDate: str
    renewalBenefits: List[RenewalBenefit] = []
    discounts: List[RenewalDiscount] = []


class RenewPolicyRequest(BaseLockerRequest):
    """Request to renew policy"""
    policyId: str
    paymentMethod: str
    modifications: Optional[Dict[str, Any]] = None


# ==================== EXPORT & SHARE MODELS ====================

class SharePolicyRequest(BaseLockerRequest):
    """Request to share policy"""
    policyId: str
    method: ShareMethod
    email: Optional[str] = None
    expiryHours: int = 24


class SharePolicyResponse(BaseModel):
    """Share policy response"""
    shareUrl: Optional[str] = None
    emailSent: bool = False
    expiresAt: str


class ExportPolicyResponse(BaseModel):
    """Export policy response"""
    downloadUrl: str
    expiresAt: str


# ==================== DOCUMENT MODELS ====================

class PolicyDocument(BaseModel):
    """Policy document"""
    id: str
    name: str
    type: str  # "pdf", "jpg", "png"
    size: str
    uploadedAt: str
    downloadUrl: str


# ==================== CONFIG MODELS ====================

class InsuranceSubType(BaseModel):
    """Insurance sub-type"""
    id: str
    name: str


class InsuranceCategoryConfig(BaseModel):
    """Insurance category configuration"""
    id: str
    displayName: str
    subTypes: List[InsuranceSubType]


class UploadConfig(BaseModel):
    """Upload configuration"""
    supportedFormats: List[str]
    maxFileSizeMB: int
    supportedPolicyTypes: List[str]


# ==================== ADD POLICY FLOW ENUMS ====================

class PolicyOwnerType(str, Enum):
    """Who is the policy for"""
    SELF = "self"
    FAMILY = "family"
    FRIEND = "friend"


class AddPolicyFlowStep(str, Enum):
    """Steps in Add Policy Flow"""
    SELECT_OWNER = "select_owner"           # Step 1: My Self or For Family/Friend
    SELECT_RELATIONSHIP = "select_relationship"  # Step 2 (Family): Select relationship
    ENTER_MEMBER_DETAILS = "enter_member_details"  # Step 3 (Family): Name, Gender, DOB
    SELECT_INSURANCE_TYPE = "select_insurance_type"  # Step 4: Select insurance category
    UPLOAD_DOCUMENT = "upload_document"     # Step 5: Upload insurance document
    ANALYZING = "analyzing"                 # Step 6: AI analyzing document
    REVIEW_ANALYSIS = "review_analysis"     # Step 7: Review extracted data
    CONFIRM_POLICY = "confirm_policy"       # Step 8: Confirm and save
    COMPLETED = "completed"                 # Final: Policy added


# ==================== ADD POLICY FLOW REQUEST MODELS ====================

class StartAddPolicyFlowRequest(BaseLockerRequest):
    """Start the Add Policy flow"""
    pass


class SelectOwnerRequest(BaseLockerRequest):
    """Step 1: Select policy owner (self or family/friend)"""
    flowId: str
    ownerType: PolicyOwnerType  # "self" or "family" or "friend"


class SelectRelationshipRequest(BaseLockerRequest):
    """Step 2 (Family): Select relationship"""
    flowId: str
    relationship: str  # spouse, son, daughter, father, mother, etc.


class EnterMemberDetailsRequest(BaseLockerRequest):
    """Step 3 (Family): Enter member details"""
    flowId: str
    name: str
    gender: Gender
    dateOfBirth: str  # Format: YYYY-MM-DD


class SelectInsuranceTypeRequest(BaseLockerRequest):
    """Step 4: Select insurance type/category"""
    flowId: str
    category: InsuranceCategory
    subType: Optional[str] = None


class UploadPolicyDocumentRequest(BaseLockerRequest):
    """Step 5: Upload policy document (metadata, file sent separately)"""
    flowId: str
    # File is sent as multipart form data


class GetAnalysisStatusRequest(BaseLockerRequest):
    """Step 6: Check analysis status"""
    flowId: str


class ReviewAnalysisRequest(BaseLockerRequest):
    """Step 7: Review and optionally correct extracted data"""
    flowId: str
    corrections: Optional[Dict[str, Any]] = None  # User corrections to extracted data


class ConfirmPolicyRequest(BaseLockerRequest):
    """Step 8: Confirm and save policy"""
    analysisId: str
    memberId: Optional[str] = None
    corrections: Optional[Dict[str, str]] = None


# ==================== ADD POLICY FLOW RESPONSE MODELS ====================

class FlowStateResponse(BaseModel):
    """Response with current flow state"""
    flowId: str
    currentStep: AddPolicyFlowStep
    ownerType: Optional[PolicyOwnerType] = None
    memberId: Optional[str] = None
    memberName: Optional[str] = None
    relationship: Optional[str] = None
    category: Optional[str] = None
    subType: Optional[str] = None
    uploadId: Optional[str] = None
    analysisId: Optional[str] = None
    analysisStatus: Optional[str] = None
    nextStep: Optional[AddPolicyFlowStep] = None
    message: str


class AnalysisResultResponse(BaseModel):
    """Analysis result response"""
    flowId: str
    analysisId: str
    status: str  # "processing", "completed", "failed"
    extractedData: Optional[Dict[str, Any]] = None
    protectionScore: Optional[int] = None
    gapAnalysis: List[Dict[str, Any]] = []
    keyFeatures: List[str] = []
    confidence: Optional[float] = None
    nextStep: Optional[AddPolicyFlowStep] = None


class PolicyAddedResponse(BaseModel):
    """Response when policy is successfully added"""
    policyId: str
    policyNumber: Optional[str] = None
    message: str
    flowCompleted: bool = True


# ==================== ERROR MODELS ====================

class ErrorDetail(BaseModel):
    """Error detail"""
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseModel):
    """Standard error response"""
    success: bool = False
    error: ErrorDetail
