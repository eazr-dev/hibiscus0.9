        policy_type_context = ""
        if "health" in policy_type.lower() or "medical" in policy_type.lower():
            policy_type_context = """
HEALTH INSURANCE ANALYSIS FRAMEWORK:
- Sum Insured Adequacy: Check if SI >= Rs.10L (metro), Rs.5L (non-metro) per person
- Room Rent Limits: Sub-limits reduce claim payouts significantly (1% or 2% of SI limits are restrictive)
- Co-payment: Any mandatory co-pay (10-20%) reduces effective coverage
- Disease-wise Sub-limits: Cataract, joint replacement, AYUSH limits
- Waiting Periods: Initial (30 days), PED (2-4 years), specific diseases (2 years)
- No Claim Bonus: Check if NCB protection available
- Restoration Benefit: Full restoration vs partial
- Day Care Procedures: 500+ procedures covered?
- Pre/Post Hospitalization: 60/180 days is standard
- Network Hospitals: Access to quality hospitals
- Mental Health Coverage: Now mandatory by IRDAI
- Maternity Coverage: If applicable
- Critical Illness: Not covered in base health plan

COMMON HEALTH GAPS TO CHECK:
1. Room rent limit causing claim reduction
2. Co-payment reducing effective coverage
3. Sub-limits on specific diseases
4. Long waiting periods for PED
5. No NCB protection
6. Limited restoration benefit
7. Missing critical illness cover
8. No personal accident cover"""
        elif "motor" in policy_type.lower() or "car" in policy_type.lower() or "vehicle" in policy_type.lower():
            policy_type_context = """
MOTOR INSURANCE ANALYSIS FRAMEWORK:
- IDV (Insured Declared Value): Should reflect current market value
- Zero Depreciation: Critical for new cars (< 5 years), saves 20-40% on claims
- Engine & Gearbox Protection: Covers hydrostatic lock damage
- NCB Protection: Protects accumulated no-claim bonus
- Return to Invoice: Covers gap between IDV and invoice value
- Roadside Assistance: 24/7 breakdown support
- Consumables Cover: Covers oil, nuts, bolts, bearings
- Tyre Cover: Expensive to replace, often excluded
- Key Replacement: Covers lost/stolen key
- Personal Accident Cover: Rs.15L mandatory for owner-driver

COMMON MOTOR GAPS TO CHECK:
1. No zero depreciation (major claim reduction)
2. Missing engine protection (hydrostatic lock not covered)
3. No NCB protection (lose years of bonus on one claim)
4. No roadside assistance
5. Missing consumables cover
6. Low PA cover (only Rs.15L statutory)
7. No return to invoice (gap on total loss)
8. No key replacement cover"""
        elif "life" in policy_type.lower() or "term" in policy_type.lower():
            policy_type_context = """
LIFE INSURANCE ANALYSIS FRAMEWORK:
- Sum Assured Adequacy: Should be 10-15x annual income
- Premium Paying Term: Shorter PPT vs policy term
- Critical Illness Rider: Covers major illnesses
- Accidental Death Benefit: Additional cover for accidents
- Disability Rider: Income replacement on disability
- Waiver of Premium: Premiums waived on disability
- Terminal Illness Benefit: Early payout on terminal diagnosis
- Return of Premium: Gets premiums back on survival

COMMON LIFE GAPS TO CHECK:
1. Inadequate sum assured (< 10x income)
2. No critical illness rider
3. No accidental death benefit
4. Missing waiver of premium
5. No disability coverage
6. No terminal illness benefit
7. Policy term not aligned with liabilities
8. No inflation protection"""
        elif "accidental" in policy_type.lower() or "accident" in policy_type.lower() or "pa" in policy_type.lower():
            policy_type_context = """
PERSONAL ACCIDENT ANALYSIS FRAMEWORK:
- Sum Insured: Minimum 5-10x monthly income
- Accidental Death Benefit: 100% of SI
- Permanent Total Disability (PTD): 100% of SI
- Permanent Partial Disability (PPD): As per schedule
- Temporary Total Disability: Weekly benefit
- Medical Expenses: Post-accident medical costs
- Hospital Cash: Daily allowance during hospitalization

COMMON PA GAPS TO CHECK:
1. Low sum insured (should be 10x monthly income)
2. Limited PPD coverage (only high % disabilities)
3. No temporary disability benefit
4. No medical expense cover
5. No hospital cash benefit
6. Adventure sports exclusion
7. No worldwide coverage"""
        elif "travel" in policy_type.lower():
            policy_type_context = """
TRAVEL INSURANCE ANALYSIS FRAMEWORK:
- Medical Expenses Adequacy: USA needs $100K-$250K, Europe/Schengen needs min EUR 30,000 ($50K), Asia needs $50K
- Emergency Medical Evacuation: Should cover air ambulance ($50K-$100K in USA, $25K-$50K elsewhere)
- Trip Cancellation: Should cover at least non-refundable trip costs (flights, hotels, tours)
- Trip Interruption: Return travel + unused accommodation costs
- Baggage Loss/Delay: Typical $1,500-$3,000 for loss, $300-$500 for delay
- Personal Liability: Minimum $50,000 recommended for international travel
- Flight Delay Compensation: Reasonable daily allowance after 6-12 hour delay
- Adventure Sports: Skiing, scuba, trekking - often excluded without add-on
- Schengen Compliance: Min EUR 30,000 medical, valid for entire trip, covers all Schengen states
- Pre-existing Conditions: Most policies exclude - check if declared conditions covered
- Passport Loss: Emergency passport replacement and travel costs
- Accidental Death/Disability: Coverage during travel period
- Deductible per Claim: Higher deductible means more out-of-pocket per incident
- Coverage Currency: Check if amounts are in USD, EUR, or INR

COMMON TRAVEL GAPS TO CHECK:
1. Medical cover insufficient for destination (USA needs $250K, getting only $50K)
2. No emergency evacuation cover (air ambulance can cost $50K-$100K)
3. Adventure sports excluded (skiing/scuba injury = 100% out of pocket)
4. Pre-existing conditions not covered (heart attack abroad = denied claim)
5. Non-Schengen compliant (visa rejection risk or claim denial in Europe)
6. Low trip cancellation cover (doesn't cover full non-refundable costs)
7. No flight delay compensation (stuck at airport with no support)
8. High per-claim deductible (reduces effective coverage on small claims)"""
