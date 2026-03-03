"""
Extraction Prompt Templates for Policy Analysis

Contains the main DeepSeek extraction prompt that extracts comprehensive
policy data from insurance document text. Supports all 5 policy types:
Health, Life, Motor, Personal Accident, and Travel.

EAZR Production Templates V1.0 - TAB 1 (Policy Details) comprehensive extraction.
"""
import logging

logger = logging.getLogger(__name__)


# System prompt used for the extraction LLM call
EXTRACTION_SYSTEM_PROMPT = (
    "You are an expert insurance policy analyst. Extract policy details accurately "
    "and return ONLY valid JSON without any explanation or markdown code blocks. "
    "Do not use ```json or ``` markers."
)


def build_extraction_prompt(extracted_text: str) -> str:
    """
    Build the comprehensive extraction prompt for DeepSeek.

    This prompt instructs the LLM to extract ALL fields from the insurance
    policy document text and return a structured JSON object covering
    Health, Motor, Life, Personal Accident, and Travel insurance types.

    Args:
        extracted_text: The raw text extracted from the policy PDF/images.

    Returns:
        The fully-formed prompt string ready for the LLM.
    """
    extraction_prompt = f"""
Analyze this insurance policy document and extract ALL information in JSON format.
Read the ENTIRE document thoroughly to extract all details accurately.

Document Text:
{extracted_text}

IMPORTANT: You MUST extract ALL the fields below. Search the entire document carefully for each field.

Return a JSON object with these fields:

{{
  "policyNumber": "Policy number/certificate number",
  "insuranceProvider": "Insurance company name",
  "policyType": "health/life/motor/travel/business/agriculture",
  "coverageAmount": 0,
  "premium": 0,
  "premiumFrequency": "annual/monthly/quarterly/half-yearly",
  "startDate": "YYYY-MM-DD",
  "endDate": "YYYY-MM-DD",
  "policyHolderName": "Name exactly as written in document",
  "uin": "UIN/IRDAI product code (format: XXXHLIPYYYYY e.g. CHIHLIP23128V012223, TATHLIP23118V032223). Look in page footers, headers, and product details. Do NOT use product name or internal reference numbers.",
  "productName": "Product/Plan name",
  "keyBenefits": ["benefit1", "benefit2", ...],
  "exclusions": ["exclusion1", "exclusion2", ...],
  "waitingPeriods": ["waiting period 1", "waiting period 2", ...],
  "criticalAreas": ["critical area 1", "critical area 2", ...],

  "categorySpecificData": {{
    // FOR HEALTH INSURANCE - Extract ALL these fields (Eazr Health Policy Structure):
    "uin": "UIN/IRDAI product code from footer or document (e.g., ACKHLIP25035V022425, IRDAN157RP0033V02201920)",
    "policyType": "Individual/Family Floater/Group",
    "tpaName": "TPA name",
    "policyPeriod": "Start to End date string",
    "insurerRegistrationNumber": "IRDAI Registration number (e.g., 108 for Star Health)",
    "insurerAddress": "Insurer office address",
    "insurerTollFree": "Toll free number (e.g., 18004250005)",
    "intermediaryName": "Insurance intermediary name (e.g., Eazr Finserv Pvt Ltd)",
    "intermediaryCode": "Intermediary IRDAI registration code",
    "intermediaryEmail": "Intermediary email address",
    "policyPeriodStart": "Policy start date (YYYY-MM-DD)",
    "policyPeriodEnd": "Policy end date (YYYY-MM-DD)",
    "insuredMembers": [
      {{"memberName": "Name", "memberRelationship": "Self/Spouse/Son/Daughter", "memberAge": 30, "memberGender": "Male/Female"}}
    ],
    "sumInsured": 500000,
    "coverType": "Individual/Floater",
    "roomRentLimit": "1% of SI (Max ₹10,000 per day) or ₹5,000/day or Single Private Room or No Limit",
    "roomRentCopay": "Room rent copay percentage or amount if applicable",
    "icuLimit": "No Capping (Actuals) or As per actual or ₹10,000/day",
    "icuDailyLimit": "ICU daily limit in rupees",
    "preHospitalization": "30 days or 60 days",
    "postHospitalization": "90 days or 180 days or 15% of SI (Max ₹15,00,000)",
    "dayCareProcedures": "540+ procedures or true/false",
    "domiciliaryHospitalization": "Up to SI or true/false",
    "ambulanceCover": "Up to ₹3,000 or ₹2,000 or As per actual",
    "healthCheckup": "Once per policy year or ₹5,000 or covered",
    "ayushTreatment": "Up to SI or true/false",
    "organDonor": "Up to SI or true/false",
    "restoration": "100% of SI or true/false",
    "restorationAmount": "100% of SI (Once per policy year) or restoration details",
    "modernTreatment": "Up to SI or modern treatment details",
    "dailyCashAllowance": "Daily cash amount (e.g., ₹500/day)",
    "convalescenceBenefit": "Convalescence/recovery benefit details",
    "initialWaitingPeriod": "30 Days (except accidents) or specific period",
    "preExistingDiseaseWaiting": "36 months or 48 months or 24 months",
    "specificDiseaseWaiting": "24 months for specific conditions",
    "maternityWaiting": "24 months or 36 months",
    "accidentCoveredFromDay1": true or false,
    "specificDiseasesList": ["Osteoarthritis", "Hernia", "Hydrocele", "Fistula in Ano", "Piles", "Sinusitis", "Tonsillitis", "Gall Stone", "Kidney Stone", "Joint Replacement"],
    "cataractLimit": "₹40,000 per eye (with lens implant) or ₹50,000 per eye",
    "jointReplacementLimit": "₹2,00,000 per joint or ₹1,50,000",
    "internalProsthesisLimit": "₹1,00,000 or actual cost whichever is less",
    "kidneyStoneLimit": "₹50,000 or specific limit",
    "gallStoneLimit": "₹50,000 or specific limit",
    "modernTreatmentLimit": "Up to Sum Insured or 50% of SI",
    "otherSubLimits": ["sub-limit 1", "sub-limit 2"],
    "permanentExclusions": ["Self-inflicted injury", "Cosmetic procedures", "Dental treatment"],
    "conditionalExclusions": ["conditional exclusion 1"],
    "preExistingConditions": ["PED condition 1", "PED condition 2"],

    // PREMIUM BREAKDOWN (Eazr Health Specific)
    "basePremium": 10000,
    "gst": 1800,
    "totalPremium": 11800,
    "premiumFrequency": "Annual or Half-Yearly or Quarterly",
    "basicPremium": 13630 or basic premium amount,
    "careShieldPremium": 3500 or Care Shield premium amount,
    "internationalCoveragePremium": 850 or International Coverage premium amount,
    "universalShieldPremium": 2000 or Universal Shield premium amount,
    "covidCarePremium": 700 or Covid Care premium amount,
    "otherAddOnPremiums": {{"addOnName": "premium amount"}},

    // NO CLAIM BONUS (NCB) - Detailed
    "ncbPercentage": "10% or 20%",
    "currentNcb": "Current NCB percentage",
    "accumulatedNcbPercentage": "Accumulated NCB percentage over years",
    "maxNcbPercentage": "50% or Maximum NCB percentage",
    "ncbAmount": "Accumulated NCB amount in rupees (e.g., ₹12,50,000)",
    "ncbProtect": true or false,
    "ncbBoost": true or false,
    "accumulatedNcbAmount": "Accumulated NCB amount in rupees (e.g., ₹12,50,000)",
    "cumulativeBonusAmount": "Cumulative bonus amount if mentioned",
    "inflationShieldAmount": "Inflation Shield accumulated amount (e.g., ₹4,16,500)",
    "totalEffectiveCoverage": "Total effective sum insured including all bonuses",
    "pedWaitingPeriodCompleted": true or false,
    "pedStatus": "PED status (e.g., 'None Declared' or 'PED mentioned')",

    // ADD-ON POLICIES (Eazr Health Specific)
    "hasAddOn": true or false,
    "addOnPoliciesList": [
      {{"addOnName": "Care Shield", "uin": "UIN number", "sumInsured": 10000000, "premium": 3500}},
      {{"addOnName": "International Coverage", "uin": "UIN number", "sumInsured": 10000000, "premium": 850}},
      {{"addOnName": "Universal Shield", "uin": "UIN number", "sumInsured": 10000000, "premium": 2000}},
      {{"addOnName": "Covid Care", "uin": "UIN number", "sumInsured": 10000000, "premium": 700}}
    ],
    "careShieldUIN": "Care Shield UIN number",
    "careShieldSumInsured": 10000000 or Care Shield sum insured,
    "careShieldPremium": 3500 or Care Shield premium amount,
    "internationalUIN": "International Coverage UIN",
    "internationalSumInsured": 10000000 or International Coverage sum insured,
    "internationalPremium": 850 or International Coverage premium amount,
    "internationalCountries": ["USA", "Canada", "UK", "Europe", "Singapore", "Thailand", "Malaysia", "UAE"],
    "universalShieldUIN": "Universal Shield UIN",
    "universalShieldSumInsured": 10000000 or Universal Shield sum insured,
    "universalShieldPremium": 2000 or Universal Shield premium amount,
    "covidCareUIN": "Covid Care UIN",
    "covidCareSumInsured": 10000000 or Covid Care sum insured,
    "covidCarePremium": 700 or Covid Care premium amount,
    "claimShield": true or false,
    "ncbShield": true or false,
    "inflationShield": true or false,
    "inflationShieldPercentage": "10% or percentage per year",

    // BENEFITS (Eazr Health Specific)
    "restoration": {{"available": true, "type": "100% of SI (Once per policy year)"}},
    "noClaimBonus": {{"available": true, "percentage": "10% per claim-free year", "accumulatedAmount": "₹12,50,000", "maxPercentage": "50%"}},
    "ayushCovered": true or false,
    "ayushLimit": "Up to SI or specific limit",
    "mentalHealthCovered": true or false,
    "mentalHealthLimit": "Coverage limit for mental illness",
    "dayCareCovered": true or false,
    "dayCareCoverageType": "540+ Procedures or Limited",

    // POLICY HISTORY (for renewals) - CRITICAL for waiting period calculations
    "firstEnrollmentDate": "First enrollment date (e.g., 20-Jun-2014) - look for 'First Enrollment Date' or 'Insured with Company since'",
    "insuredSinceDate": "Date insured with company since - VERY IMPORTANT for waiting period status",
    "previousPolicyNumber": "Previous policy number",
    "continuousCoverageYears": "Number of years of continuous coverage",
    "renewalDate": "Renewal date",
    "claimHistory": "Any claims made in previous year",
    "portability": {{"available": true, "waitingPeriodCredit": "Available for porting"}},

    // NETWORK HOSPITAL INFORMATION
    "networkHospitalsCount": "14,000+ Hospitals or 16000+",
    "ambulanceCoverLimit": "Up to ₹3,000 or amount",
    "cashlessFacility": true or false,
    "networkType": "Pan India or specific",

    // CLAIM INFORMATION
    "claimSettlementRatio": "92% or claim settlement ratio",
    "claimProcess": "Cashless & Reimbursement or specific process",
    "claimIntimation": "Within 24 hours of admission",
    "claimDocuments": ["Claim Form", "Medical Reports", "Discharge Summary", "Bills & Receipts"],

    // CO-PAYMENT DETAILS (CRITICAL for health policy analysis)
    "ageBasedCopay": [
      {{"ageBracket": "0-45", "copayPercentage": 0}},
      {{"ageBracket": "46-55", "copayPercentage": 10}},
      {{"ageBracket": "56-65", "copayPercentage": 20}}
    ],
    "diseaseSpecificCopay": [{{"disease": "disease name", "copayPercentage": 20}}],
    "generalCopay": "0% or 10% or 20% - general copay applicable to all claims",

    // NETWORK & CLAIMS TURNAROUND
    "preAuthTurnaround": "4 hours planned, 1 hour emergency - or specific turnaround times from policy",

    // PED-SPECIFIC EXCLUSIONS
    "pedSpecificExclusions": ["Any PED-specific exclusion clause"],

    // GRACE PERIOD (for premium payment)
    "healthGracePeriod": "30 days or specific grace period mentioned in policy",

    // CONSUMABLES COVERAGE
    "consumablesCoverage": true,
    "consumablesCoverageDetails": "Covered under add-on or included in base plan or not covered",

    // COVERED MEMBERS (for floater policies)
    "totalMembersCovered": 2,
    "membersList": ["Member 1 Name - Relationship", "Member 2 Name - Relationship"],

    "declaredConditions": ["condition1", "condition2"],

    // FOR MOTOR INSURANCE - Extract ALL these fields (EAZR_03 Motor Insurance Spec):
    // Section 1: Policy Basics
    "uin": "UIN/IRDAI product code from document footer (e.g., IRDAN157RP0033V02201920)",
    "certificateNumber": "Certificate number",
    "coverNoteNumber": "Cover note number",
    "productType": "Comprehensive/Third Party Only/Standalone OD",
    "policyPeriodStart": "YYYY-MM-DD policy start date",
    "policyPeriodEnd": "YYYY-MM-DD policy end date",
    "policyTerm": 1,
    "previousPolicyNumber": "Previous policy number",
    "previousInsurer": "Previous insurance company name",
    "insurerTollFree": "Insurer toll-free helpline number",
    "claimEmail": "Insurer claims email address",
    "claimApp": "Insurer claims app name or URL",

    // Section 2: Vehicle Details
    "registrationNumber": "MH01AB1234",
    "vehicleClass": "Private Car/Two Wheeler/Commercial",
    "vehicleCategory": "private_car/two_wheeler/commercial/pcv/gcv",
    "vehicleMake": "Maruti Suzuki/Honda/Hyundai",
    "vehicleModel": "Swift VXi/City/Creta",
    "vehicleVariant": "VXi/ZXi/SXi",
    "manufacturingYear": 2020,
    "registrationDate": "YYYY-MM-DD",
    "engineNumber": "Engine number",
    "chassisNumber": "Chassis number",
    "fuelType": "Petrol/Diesel/CNG/LPG/Electric/Hybrid",
    "cubicCapacity": "1197",
    "seatingCapacity": 5,
    "vehicleColor": "White/Black/Silver",
    "rtoLocation": "Mumbai/Delhi",
    "hypothecation": {{"isHypothecated": true, "financierName": "Bank name", "loanAccountNumber": "Loan account"}},

    // Section 3: Owner/Policyholder Details
    "ownerName": "Owner full name",
    "ownerType": "individual/company/firm/trust",
    "ownerAddress": "Full address",
    "ownerAddressCity": "City",
    "ownerAddressState": "State",
    "ownerAddressPincode": "Pincode",
    "ownerContact": "Phone number",
    "ownerEmail": "Email",
    "ownerPan": "PAN number",

    // Section 4: Coverage Details
    "idv": 500000,
    "idvMinimum": 0,
    "idvMaximum": 0,
    "odPremium": 5000,
    "tpPremium": 2000,
    "compulsoryDeductible": 0,
    "voluntaryDeductible": 0,
    "geographicScope": "India",
    "paOwnerCover": 1500000,
    "paUnnamedPassengers": 0,
    "paUnnamedPassengersPerPerson": 0,
    "paPaidDriver": 200000,
    "llPaidDriver": true,
    "llEmployees": 0,
    "tppdCover": 750000,

    // Section 5: NCB Details
    "ncbPercentage": "0%/20%/25%/35%/45%/50%",
    "ncbProtection": true,
    "ncbDeclaration": "Declaration text",
    "claimFreeYears": 0,

    // Section 6: Add-on Covers (15 types)
    "zeroDepreciation": true,
    "engineProtection": true,
    "returnToInvoice": false,
    "roadsideAssistance": true,
    "consumables": true,
    "tyreCover": false,
    "keyCover": false,
    "ncbProtect": true,
    "emiBreakerCover": false,
    "passengerCover": true,
    "passengerCoverAmount": 100000,
    "personalBaggage": false,
    "outstationEmergency": false,
    "dailyAllowance": false,
    "windshieldCover": false,
    "electricVehicleCover": false,
    "batteryProtect": false,

    // Section 7: Premium Breakdown (detailed)
    "basicOdPremium": 5000,
    "ncbDiscount": 1000,
    "voluntaryDeductibleDiscount": 0,
    "antiTheftDiscount": 0,
    "aaiMembershipDiscount": 0,
    "electricalAccessoriesPremium": 0,
    "nonElectricalAccessoriesPremium": 0,
    "cngLpgKitPremium": 0,
    "addOnPremium": 500,
    "loading": 0,
    "netOdPremium": 0,
    "basicTpPremium": 0,
    "paOwnerDriverPremium": 0,
    "paPassengersPremium": 0,
    "paPaidDriverPremium": 0,
    "llPaidDriverPremium": 0,
    "netTpPremium": 0,
    "grossPremium": 0,
    "gst": 0,
    "totalPremium": 0,

    "otherExclusions": ["exclusion1", "exclusion2"],

    // FOR LIFE INSURANCE - Extract ALL these fields:
    "uin": "UIN/IRDAI product code from document footer (e.g., 117N097V02, HDFHLIP21016V012122)",
    "policyType": "Term/Endowment/ULIP/Whole Life",
    "policyIssueDate": "YYYY-MM-DD",
    "policyStatus": "Active/Lapsed",
    "policyholderName": "Name",
    "policyholderDob": "YYYY-MM-DD",
    "policyholderAge": 35,
    "policyholderGender": "Male/Female",
    "lifeAssuredName": "Name if different",
    "lifeAssuredDob": "YYYY-MM-DD",
    "lifeAssuredAge": 35,
    "relationshipWithPolicyholder": "Self/Spouse",
    "sumAssured": 5000000,
    "coverType": "Level/Increasing/Decreasing",
    "policyTerm": "20 years",
    "premiumPayingTerm": "15 years",
    "maturityDate": "YYYY-MM-DD",
    "deathBenefit": "Sum Assured + Bonuses",
    "premiumAmount": 50000,
    "premiumDueDate": "YYYY-MM-DD",
    "gracePeriod": "30 days",
    "modalPremiumBreakdown": {{"base": 45000, "gst": 4500, "rider": 500}},
    "riders": [
      {{"riderName": "Accidental Death", "riderSumAssured": 1000000, "riderPremium": 500, "riderTerm": "20 years"}}
    ],
    "bonusType": "Simple Reversionary/Compound",
    "declaredBonusRate": "₹48 per ₹1,000 SA",
    "accruedBonus": 100000,
    "surrenderValue": 50000,
    "paidUpValue": 100000,
    "loanValue": 75000,
    "fundOptions": ["Equity Fund", "Debt Fund"],
    "currentNav": {{"Equity": 50.25, "Debt": 25.50}},
    "unitsHeld": 1000,
    "fundValue": 50000,
    "switchOptions": "4 free switches",
    "partialWithdrawal": "After 5 years",
    "nominees": [
      {{"nomineeName": "Name", "nomineeRelationship": "Spouse", "nomineeShare": 100, "nomineeAge": 30}}
    ],
    "appointeeName": "Appointee name",
    "appointeeRelationship": "Father",
    "revivalPeriod": "5 years",
    "freelookPeriod": "15 days",
    "policyLoanInterestRate": "9%",
    "autoPayMode": true,
    "suicideClause": "Not covered in first year",
    "otherExclusions": ["exclusion1"],

    // FOR PERSONAL ACCIDENT INSURANCE - Extract ALL these fields (EAZR_04 PA Spec):
    // Section 1: Policy Basics
    "paInsuranceType": "Individual/Family/Group",
    "paPolicySubType": "IND_PA/FAM_PA/GRP_PA/PA_MED/STU_PA",
    "paCertificateNumber": "Certificate number if group policy",
    "groupPolicyholderName": "Group policyholder name if group policy",
    "groupPolicyNumber": "Group policy number if applicable",

    // Section 2: Coverage Details (PA-specific 5 benefit types)
    "paSumInsured": 0,
    "accidentalDeathBenefitPercentage": 100,
    "accidentalDeathBenefitAmount": 0,
    "doubleIndemnityApplicable": false,
    "doubleIndemnityConditions": "Public transport accident",
    "permanentTotalDisabilityCovered": true,
    "permanentTotalDisabilityPercentage": 100,
    "permanentTotalDisabilityAmount": 0,
    "ptdConditions": ["Loss of both eyes", "Loss of both hands or feet", "Loss of one hand and one foot", "Total and permanent paralysis", "Complete and incurable insanity"],
    "permanentPartialDisabilityCovered": true,
    "ppdSchedule": [
        {{"disability": "Loss of both hands or both feet", "percentage": 100}},
        {{"disability": "Loss of one hand and one foot", "percentage": 100}},
        {{"disability": "Total loss of sight of both eyes", "percentage": 100}},
        {{"disability": "Loss of arm at shoulder", "percentage": 70}},
        {{"disability": "Loss of arm between elbow and shoulder", "percentage": 65}},
        {{"disability": "Loss of arm at or below elbow", "percentage": 60}},
        {{"disability": "Loss of hand", "percentage": 55}},
        {{"disability": "Loss of leg at or above knee", "percentage": 60}},
        {{"disability": "Loss of leg below knee", "percentage": 50}},
        {{"disability": "Loss of foot", "percentage": 45}},
        {{"disability": "Total loss of sight of one eye", "percentage": 50}},
        {{"disability": "Loss of thumb", "percentage": 25}},
        {{"disability": "Loss of index finger", "percentage": 10}},
        {{"disability": "Loss of any other finger", "percentage": 5}},
        {{"disability": "Loss of big toe", "percentage": 5}},
        {{"disability": "Loss of any other toe", "percentage": 2}},
        {{"disability": "Total deafness of both ears", "percentage": 50}},
        {{"disability": "Total deafness of one ear", "percentage": 15}},
        {{"disability": "Loss of speech", "percentage": 50}}
    ],
    "temporaryTotalDisabilityCovered": true,
    "ttdBenefitType": "weekly/monthly",
    "ttdBenefitPercentage": 1,
    "ttdBenefitAmount": 0,
    "ttdMaximumWeeks": 52,
    "ttdWaitingPeriodDays": 7,
    "medicalExpensesCovered": true,
    "medicalExpensesLimitType": "percentage_of_si/fixed_amount/actual",
    "medicalExpensesLimitPercentage": 10,
    "medicalExpensesLimitAmount": 0,
    "medicalExpensesPerAccidentOrAnnual": "per_accident/annual_aggregate",

    // Section 3: Additional Benefits
    "educationBenefitCovered": false,
    "educationBenefitAmount": 0,
    "educationBenefitType": "lump_sum/annual/per_child",
    "loanEmiCoverCovered": false,
    "loanEmiCoverMaxMonths": 0,
    "loanEmiCoverMaxAmountPerMonth": 0,
    "ambulanceChargesCovered": false,
    "ambulanceChargesLimit": 0,
    "transportMortalRemainsCovered": false,
    "transportMortalRemainsLimit": 0,
    "funeralExpensesCovered": false,
    "funeralExpensesLimit": 0,
    "homeModificationCovered": false,
    "homeModificationLimit": 0,
    "vehicleModificationCovered": false,
    "vehicleModificationLimit": 0,
    "carriageOfAttendantCovered": false,
    "carriageOfAttendantLimit": 0,

    // Section 4: Exclusions
    "paStandardExclusions": ["Suicide or self-inflicted injury", "War, invasion, act of foreign enemy", "Nuclear reaction, radiation", "Participation in criminal activity", "While under influence of alcohol/drugs", "Mental disorder or insanity", "Childbirth or pregnancy", "Pre-existing physical defect or infirmity", "Aviation other than as fare-paying passenger", "Hazardous sports (unless covered)", "Venereal diseases or HIV/AIDS"],
    "paOccupationRestrictions": ["Excluded occupations list"],
    "paAgeMinimum": 18,
    "paAgeMaximum": 65,
    "paMaxRenewalAge": 70,
    "ttdEliminationPeriod": 7,

    // Section 5: Premium Details
    "paPremiumFrequency": "annual/single",
    "paOccupationClass": "Class I/II/III",
    "paAgeBand": "18-35/36-45/46-55/56-65",

    // Section 6: Insured Members (for Family PA)
    "paInsuredMembers": [
        {{"name": "Name", "relationship": "self/spouse/child/parent", "dateOfBirth": "YYYY-MM-DD", "gender": "male/female/other", "occupation": "Occupation", "individualSI": 0}}
    ],

    // FOR TRAVEL INSURANCE - Extract ALL these fields (EAZR_05 Travel Insurance Full Spec):
    // Section 1: Policy Identification
    "uin": "UIN/IRDAI product code from document footer (e.g., IRDAN157RP0033V02201920)",
    "tripType": "Single Trip/Annual Multi-Trip/Student/Business/Senior Citizen",
    "travelType": "International/Domestic/Both",
    "insurerName": "Insurance company name",
    "policyIssueDate": "YYYY-MM-DD",
    "geographicCoverage": "worldwide/worldwide_excl_usa_canada/schengen/asia/specific_countries/domestic",
    "policyStatus": "active/upcoming/expired/claimed",

    // Section 2: Trip Details
    "tripStartDate": "YYYY-MM-DD",
    "tripEndDate": "YYYY-MM-DD",
    "tripDuration": "Number of days (e.g., 15)",
    "destinationCountries": ["Country1", "Country2"],
    "originCountry": "India",
    "purposeOfTravel": "Leisure/Business/Education/Medical/Pilgrimage",

    // Section 3: Traveller Details (enhanced - extract ALL traveller info)
    "travellers": [
      {{"name": "Traveller Name", "age": 30, "dateOfBirth": "YYYY-MM-DD", "relationship": "Self/Spouse/Child/Parent", "passportNumber": "Passport number if available", "preExistingConditionsDeclared": ["Condition1", "Condition2"]}}
    ],

    // Section 4: Medical Emergency Coverage (extract exact limits - amounts may be in USD, EUR, or INR)
    "medicalExpenses": "Coverage limit for medical expenses (e.g., $50,000 or ₹25,00,000)",
    "medicalDeductible": "Deductible amount per medical claim (e.g., $50, $100, or 0)",
    "coverageIncludes": ["Hospitalization", "Doctor consultation", "Prescribed medicines", "Diagnostic tests", "Emergency dental", "Ambulance"],
    "emergencyMedicalEvacuation": "Coverage limit for emergency evacuation (e.g., $25,000)",
    "repatriationOfRemains": "Coverage limit for repatriation (e.g., $25,000)",
    "covidTreatmentCovered": true or false,
    "covidQuarantineCovered": true or false,
    "covidQuarantineLimit": "Quarantine hotel/expenses limit if covered (e.g., $500)",
    "cashlessNetworkAvailable": true or false,
    "cashlessNetworkName": "Network provider name if available",
    "cashlessHospitalsCount": 0,
    "assistanceHelplineForCashless": "24x7 helpline for cashless facility",
    "preExistingCovered": true or false,
    "preExistingConditions": "Detailed PED terms (e.g., Emergency exacerbation only, Covered with sublimit)",
    "preExistingLimit": "PED coverage limit if covered (e.g., $10,000)",
    "preExistingAgeRestriction": "Age restriction for PED coverage (e.g., 60)",
    "maternityCovered": true or false,

    // Section 5: Trip Protection Coverage
    "tripCancellation": "Coverage limit for trip cancellation (e.g., $5,000 or ₹1,50,000)",
    "tripCancellationCoveredReasons": ["Death or serious illness of insured/family", "Natural disaster", "Visa rejection", "Job loss", "Court summons", "Terrorist incident"],
    "tripCancellationNotCoveredReasons": ["Change of mind", "Work commitments", "Known pre-existing conditions"],
    "tripInterruption": "Coverage limit for trip interruption (e.g., $5,000)",
    "tripCurtailmentCovered": true or false,
    "tripCurtailmentLimit": "Trip curtailment coverage limit",
    "tripCurtailmentBenefitType": "unused_expenses/additional_return_cost/both",
    "flightDelay": "Compensation for flight delay (e.g., $500 after 6 hours)",
    "tripDelayTriggerHours": 0,
    "tripDelayCoveredExpenses": ["Hotel", "Meals", "Communication"],
    "missedConnectionCovered": true or false,
    "missedConnectionTriggerHours": 0,
    "missedConnectionBenefitAmount": "Benefit amount for missed connection",
    "hijackDistress": "Hijack distress allowance (e.g., $1,000)",

    // Section 6: Baggage & Personal Belongings Coverage
    "baggageLoss": "Total coverage limit for baggage loss (e.g., $2,000)",
    "baggagePerItemLimit": "Per-item limit for baggage loss (e.g., $250 or ₹10,000)",
    "baggageValuablesLimit": "Valuables sub-limit (e.g., $500)",
    "baggageDocumentationRequired": ["PIR from airline", "Receipts", "Police report"],
    "baggageDelay": "Compensation for baggage delay (e.g., $500 after 12 hours)",
    "passportLoss": "Coverage for passport loss expenses (e.g., $500)",

    // Section 7: Personal Liability & Accident
    "personalLiability": "Personal liability coverage limit (e.g., $50,000)",
    "accidentalDeath": "Accidental death benefit during travel (e.g., $50,000)",
    "permanentDisability": "Permanent disability benefit (e.g., $50,000)",
    "homeburglary": "Home burglary cover during travel (e.g., $5,000 or 0 if not covered)",

    // Section 8: Adventure Sports & Activities
    "adventureSportsExclusion": "Excluded/Covered with add-on/Covered (list specific sports if mentioned)",
    "sportsCoveredList": ["Trekking below 4000m", "Snorkeling", "Jet skiing", "Parasailing"],
    "sportsExcludedList": ["Scuba diving beyond 30m", "Sky diving", "Bungee jumping", "Motor racing"],
    "adventureAdditionalPremium": true or false,

    // Section 9: Exclusions & Conditions
    "preExistingConditionExclusion": "Excluded/Covered up to X/Covered after waiting period",
    "schengenCompliant": true or false,
    "coverageCurrency": "USD/INR/EUR - primary currency of coverage amounts",
    "deductiblePerClaim": "Deductible amount per claim (e.g., $50 or $100)",

    // Section 10: Premium Breakdown
    "travelBasePremium": 0,
    "travelGst": 0,
    "travelTotalPremium": 0,
    "premiumPerDay": 0,
    "premiumAgeBand": "18-35/36-45/46-55/56-65/66+",
    "premiumDestinationZone": "Zone name or region",
    "premiumCoverageLevel": "Basic/Standard/Premium/Platinum",

    // Section 11: Emergency Contacts & Assistance
    "emergencyHelpline24x7": "24x7 emergency helpline number from policy",
    "claimsEmail": "Claims email address",
    "insurerAddress": "Insurer office address",
    "cashlessHospitals": "Network hospitals or cashless facility details",
    "primaryContactName": "Primary insured person's name",
    "primaryContactPhone": "Primary contact phone",
    "primaryContactEmail": "Primary contact email",
    "emergencyContactIndiaName": "Emergency contact in India name",
    "emergencyContactIndiaRelationship": "Relationship to insured",
    "emergencyContactIndiaPhone": "Emergency contact India phone"
  }}
}}

CRITICAL INSTRUCTIONS:
1. Search the ENTIRE document for each field
2. Look for values in tables, schedules, policy wording sections
3. Extract exact values as written in the document
4. For room rent, look for "Room Rent", "Single Room", "ICU Charges" etc.
5. For waiting periods, look for "Waiting Period", "Pre-existing", "PED" etc.
6. For sub-limits, look for specific procedure limits like cataract, joint replacement
7. For travel insurance, look for "Sum Insured", "Coverage", "Benefit Schedule", "Destination", "Trip Type"
8. If a field is truly not found after thorough search, use null
9. Return ONLY valid JSON without any markdown or explanation"""

    return extraction_prompt
