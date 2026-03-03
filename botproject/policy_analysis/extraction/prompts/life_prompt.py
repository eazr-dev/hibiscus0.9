"""Life insurance extraction prompt - PRD v2 format with confidence scoring."""

V2_SYSTEM_PROMPT = (
    "You are an expert life insurance policy analyst for the Indian market. "
    "Extract policy details accurately from the document text. "
    "Return ONLY valid JSON. Do not use ```json or ``` markers. "
    "For every field, return {\"value\": <extracted_value>, \"source_page\": <page_number_or_null>, \"confidence\": <0.0_to_1.0>}. "
    "Set confidence based on how clearly the value appears in the document: "
    "1.0 = exact match found, 0.7-0.9 = inferred from context, 0.3-0.6 = uncertain, 0.0 = not found (value=null)."
)


def build_life_extraction_prompt(extracted_text: str) -> str:
    return f"""Analyze this LIFE INSURANCE policy document and extract ALL fields below.
The document has [Page N] markers - use them to report source_page for each field.

Document Text:
{extracted_text}

Return a JSON object where EVERY field uses this format:
{{"value": <extracted_value>, "source_page": <page_number_or_null>, "confidence": <0.0_to_1.0>}}

Extract these fields:
{{
  "policyNumber": {{"value": "string", "source_page": null, "confidence": 0.0}},
  "uin": {{"value": "UIN/IRDAI product code", "source_page": null, "confidence": 0.0}},
  "insurerName": {{"value": "Insurance company name", "source_page": null, "confidence": 0.0}},
  "productName": {{"value": "Product/Plan name", "source_page": null, "confidence": 0.0}},
  "policyType": {{"value": "Term/Endowment/ULIP/Whole Life/Money Back", "source_page": null, "confidence": 0.0, "_hint": "Classify based on plan characteristics: 'Whole Life' = coverage until age 99/100 or maturity 50+ years away (e.g. Jeevan Umang, Jeevan Anand with whole life cover, Whole Life plans). 'Endowment' = fixed term with maturity payout (e.g. Jeevan Lakshya, Jeevan Labh). 'Term' = pure death cover, no maturity benefit. 'ULIP' = market-linked with fund/NAV. 'Money Back' = periodic survival payouts during term. Look for keywords: 'Whole Life', 'Sampurna', 'lifetime', 'age 100' in plan description."}},
  "policyIssueDate": {{"value": "YYYY-MM-DD", "source_page": null, "confidence": 0.0}},
  "policyStatus": {{"value": "Active/Lapsed/Paid-Up/Surrendered", "source_page": null, "confidence": 0.0}},
  "policyPeriodStart": {{"value": "YYYY-MM-DD", "source_page": null, "confidence": 0.0, "_hint": "Date of Commencement of Policy (NOT Date of Commencement of Risk, which may differ)."}},
  "policyPeriodEnd": {{"value": "YYYY-MM-DD", "source_page": null, "confidence": 0.0, "_hint": "IMPORTANT: This is the POLICY maturity date (Date of Maturity), NOT the rider expiry date. The rider table may show a different (earlier) expiry. Always use the main policy 'Date of Maturity' from the schedule, which is the latest end date."}},

  "policyholderName": {{"value": "Name as in document", "source_page": null, "confidence": 0.0}},
  "policyholderDob": {{"value": "YYYY-MM-DD", "source_page": null, "confidence": 0.0, "_hint": "Date of birth of proposer/policyholder. If the policyholder IS the life assured (Self), use the same DOB as lifeAssuredDob. Search for 'Date of birth of the Life Assured' or 'Proposer DOB'."}},
  "policyholderAge": {{"value": 0, "source_page": null, "confidence": 0.0, "_hint": "Age of proposer/policyholder. If the policyholder IS the life assured (Self), use the same age as lifeAssuredAge."}},
  "policyholderGender": {{"value": "Male/Female", "source_page": null, "confidence": 0.0}},
  "lifeAssuredName": {{"value": "Name of life assured", "source_page": null, "confidence": 0.0}},
  "lifeAssuredDob": {{"value": "YYYY-MM-DD", "source_page": null, "confidence": 0.0}},
  "lifeAssuredAge": {{"value": 0, "source_page": null, "confidence": 0.0}},
  "relationshipWithPolicyholder": {{"value": "Self/Spouse/Child/Parent", "source_page": null, "confidence": 0.0}},

  "sumAssured": {{"value": 0, "source_page": null, "confidence": 0.0}},
  "coverType": {{"value": "Level/Increasing/Decreasing", "source_page": null, "confidence": 0.0}},
  "policyTerm": {{"value": "number of years", "source_page": null, "confidence": 0.0, "_hint": "The POLICY term in years. Look for 'Policy Term' or 'Plan & Policy Term' in the schedule table. This is the number of years from commencement to maturity of the BASE POLICY (NOT the rider term). For Whole Life plans this may be 50-100 years. Do NOT compute from rider expiry date."}},
  "premiumPayingTerm": {{"value": "number of years", "source_page": null, "confidence": 0.0}},
  "maturityDate": {{"value": "YYYY-MM-DD", "source_page": null, "confidence": 0.0, "_hint": "IMPORTANT: Use the 'Date of Maturity' from the main policy schedule. Do NOT confuse with rider expiry date which may be much earlier. The maturity date is when the policy ends and maturity benefit is paid."}},
  "deathBenefit": {{"value": "death benefit amount or description", "source_page": null, "confidence": 0.0}},

  "premiumAmount": {{"value": 0, "source_page": null, "confidence": 0.0}},
  "premiumFrequency": {{"value": "Annual/Half-Yearly/Quarterly/Monthly", "source_page": null, "confidence": 0.0}},
  "premiumDueDate": {{"value": "YYYY-MM-DD or day of month", "source_page": null, "confidence": 0.0}},
  "gracePeriod": {{"value": "30 days / 15 days", "source_page": null, "confidence": 0.0}},
  "modalPremiumBreakdown": {{"value": {{"base": 0, "gst": 0, "rider": 0}}, "source_page": null, "confidence": 0.0, "_hint": "CRITICAL: 'base' = Instalment Premium for Base Policy. 'rider' = SUM of all rider premiums from the rider table. 'gst' = GST/tax amount ONLY if explicitly shown as 'GST' or 'Tax'. If total = base + rider premiums (no separate GST line), set gst=0. Do NOT assign rider premium to gst."}},
  "basePremium": {{"value": 0, "source_page": null, "confidence": 0.0, "_hint": "Instalment Premium for Base Policy ONLY (excluding rider premiums and GST)."}},
  "gst": {{"value": 0, "source_page": null, "confidence": 0.0, "_hint": "GST/tax amount ONLY if explicitly labeled as 'GST', 'Service Tax', or 'Tax' in the document. If no explicit GST line item exists, set to 0. Do NOT confuse rider premium with GST."}},
  "totalPremium": {{"value": 0, "source_page": null, "confidence": 0.0, "_hint": "Total Instalment Premium (including base + rider + GST if any). This is the total amount payable per instalment."}},

  "riders": {{"value": [{{"riderName": "Rider name", "riderSumAssured": 0, "riderPremium": 0, "riderTerm": "number of years"}}], "source_page": null, "confidence": 0.0, "_hint": "Extract ALL riders from the rider table. riderPremium = 'Premium Instalment for Rider' column value (NOT 0). riderTerm = years from commencement to rider expiry. Each rider should have its premium from the rider details table."}},

  "bonusType": {{"value": "Simple Reversionary/Compound Reversionary/Terminal/Loyalty", "source_page": null, "confidence": 0.0}},
  "declaredBonusRate": {{"value": "rate per 1000 SA or percentage", "source_page": null, "confidence": 0.0}},
  "accruedBonus": {{"value": 0, "source_page": null, "confidence": 0.0}},
  "surrenderValue": {{"value": 0, "source_page": null, "confidence": 0.0}},
  "paidUpValue": {{"value": 0, "source_page": null, "confidence": 0.0}},
  "loanValue": {{"value": 0, "source_page": null, "confidence": 0.0}},

  "fundOptions": {{"value": [{{"fundName": "Fund name", "allocation": "percentage"}}], "source_page": null, "confidence": 0.0}},
  "currentNav": {{"value": 0.0, "source_page": null, "confidence": 0.0}},
  "unitsHeld": {{"value": 0.0, "source_page": null, "confidence": 0.0}},
  "fundValue": {{"value": 0, "source_page": null, "confidence": 0.0}},
  "switchOptions": {{"value": "number of free switches per year", "source_page": null, "confidence": 0.0}},
  "partialWithdrawal": {{"value": "allowed after N years / conditions", "source_page": null, "confidence": 0.0}},

  "nominees": {{"value": [{{"nomineeName": "Name", "nomineeRelationship": "Spouse/Child/Parent", "nomineeShare": "percentage", "nomineeAge": 0}}], "source_page": null, "confidence": 0.0}},
  "appointeeName": {{"value": "Appointee name (if nominee is minor)", "source_page": null, "confidence": 0.0}},
  "appointeeRelationship": {{"value": "Relationship with nominee", "source_page": null, "confidence": 0.0}},

  "revivalPeriod": {{"value": "number of years", "source_page": null, "confidence": 0.0}},
  "freelookPeriod": {{"value": "15 days / 30 days", "source_page": null, "confidence": 0.0}},
  "policyLoanInterestRate": {{"value": "percentage per annum", "source_page": null, "confidence": 0.0}},
  "autoPayMode": {{"value": "Auto Premium Loan / details", "source_page": null, "confidence": 0.0}},

  "suicideClause": {{"value": "exclusion clause details", "source_page": null, "confidence": 0.0}},
  "otherExclusions": {{"value": ["exclusion1", "exclusion2"], "source_page": null, "confidence": 0.0}},

  "claimSettlementRatio": {{"value": "percentage", "source_page": null, "confidence": 0.0}},
  "claimProcess": {{"value": "claim process description", "source_page": null, "confidence": 0.0}},
  "insurerTollFree": {{"value": "Toll-free number", "source_page": null, "confidence": 0.0}},
  "claimEmail": {{"value": "claims email address", "source_page": null, "confidence": 0.0}}
}}

CRITICAL INSTRUCTIONS:
1. Search the ENTIRE document for each field. Look in tables, schedules, benefit summaries, T&C sections.
2. Extract exact values as written. Do not paraphrase or summarize numeric values.
3. For sum assured, search: "Sum Assured", "Basic Sum Assured", "Total Sum Assured", "Cover Amount", "SA".
4. For death benefit, search: "Death Benefit", "Sum on Death", "Benefit on Death", "Death Claim".
5. For maturity, search: "Maturity Benefit", "Maturity Date", "Sum on Maturity", "Maturity Value".
6. For bonus, search: "Bonus", "Reversionary Bonus", "Terminal Bonus", "Loyalty Addition", "Accrued Bonus".
7. For riders, search: "Rider", "Add-on", "Accidental Death", "Waiver of Premium", "Critical Illness Rider".
8. For nominees, search: "Nominee", "Nomination", "Appointee", "Beneficiary", "Nominee Share".
9. For surrender value, search: "Surrender Value", "Guaranteed Surrender Value", "Special Surrender Value", "Paid-Up Value".
10. For ULIP details, search: "NAV", "Fund Value", "Units", "Fund Option", "Switch", "Partial Withdrawal".
11. For premiums, search: "Premium", "Modal Premium", "Base Premium", "GST", "Rider Premium", "Due Date".
12. Use [Page N] markers to fill source_page accurately.
13. Set confidence 1.0 for exact matches, 0.7-0.9 for inferred values, <0.5 for uncertain.
14. If field not found after thorough search, set value to null and confidence to 0.0.
15. MATURITY vs RIDER: The schedule may list BOTH a 'Date of Maturity' for the base policy AND a 'Date of expiry of rider'. These are DIFFERENT. policyPeriodEnd/maturityDate/policyTerm MUST use the base policy maturity, NOT the rider expiry. The rider expiry goes into riders[].riderTerm only.
16. PREMIUM SPLIT: Total Premium often = Base Premium + Rider Premiums. Do NOT assume the difference is GST unless 'GST' or 'Tax' is explicitly printed. Check the rider table for each rider's premium amount.
17. Return ONLY valid JSON without any markdown or explanation."""
