"""Personal Accident insurance extraction prompt - PRD v2 format with confidence scoring."""

V2_SYSTEM_PROMPT = (
    "You are an expert personal accident insurance policy analyst for the Indian market. "
    "Extract policy details accurately from the document text. "
    "Return ONLY valid JSON. Do not use ```json or ``` markers. "
    "For every field, return {\"value\": <extracted_value>, \"source_page\": <page_number_or_null>, \"confidence\": <0.0_to_1.0>}. "
    "Set confidence based on how clearly the value appears in the document: "
    "1.0 = exact match found, 0.7-0.9 = inferred from context, 0.3-0.6 = uncertain, 0.0 = not found (value=null)."
)


def build_pa_extraction_prompt(extracted_text: str) -> str:
    return f"""Analyze this PERSONAL ACCIDENT INSURANCE policy document and extract ALL fields below.
The document has [Page N] markers - use them to report source_page for each field.

Document Text:
{extracted_text}

Return a JSON object where EVERY field uses this format:
{{"value": <extracted_value>, "source_page": <page_number_or_null>, "confidence": <0.0_to_1.0>}}

Extract these fields:
{{
  "policyNumber": {{"value": "string", "source_page": null, "confidence": 0.0}},
  "uin": {{"value": "UIN/IRDAI product code", "source_page": null, "confidence": 0.0, "_hint": "Format: XXXHLIPYYYYY or IRDAN###XXXXXXX. Look in page footers/headers. Do NOT extract product name or internal references as UIN. If not found, set value=null."}},
  "insurerName": {{"value": "Insurance company name", "source_page": null, "confidence": 0.0}},
  "productName": {{"value": "Product/Plan name", "source_page": null, "confidence": 0.0}},
  "policyPeriodStart": {{"value": "YYYY-MM-DD", "source_page": null, "confidence": 0.0}},
  "policyPeriodEnd": {{"value": "YYYY-MM-DD", "source_page": null, "confidence": 0.0}},
  "policyHolderName": {{"value": "Name as in document", "source_page": null, "confidence": 0.0}},
  "paInsuranceType": {{"value": "Individual/Family/Group", "source_page": null, "confidence": 0.0}},
  "paPolicySubType": {{"value": "Standard PA / Janata PA / Gramin PA / Named Perils / Other", "source_page": null, "confidence": 0.0}},
  "paCertificateNumber": {{"value": "Certificate number for group policies", "source_page": null, "confidence": 0.0}},
  "groupPolicyholderName": {{"value": "Group policyholder/employer name", "source_page": null, "confidence": 0.0}},
  "groupPolicyNumber": {{"value": "Master/group policy number", "source_page": null, "confidence": 0.0}},

  "paSumInsured": {{"value": 0, "source_page": null, "confidence": 0.0}},
  "accidentalDeathBenefitPercentage": {{"value": "100% of SI", "source_page": null, "confidence": 0.0}},
  "accidentalDeathBenefitAmount": {{"value": 0, "source_page": null, "confidence": 0.0}},
  "doubleIndemnityApplicable": {{"value": false, "source_page": null, "confidence": 0.0}},
  "doubleIndemnityConditions": {{"value": "Conditions under which double benefit is payable (e.g., public transport accident)", "source_page": null, "confidence": 0.0}},

  "permanentTotalDisabilityCovered": {{"value": true, "source_page": null, "confidence": 0.0}},
  "permanentTotalDisabilityPercentage": {{"value": "100% of SI", "source_page": null, "confidence": 0.0}},
  "permanentTotalDisabilityAmount": {{"value": 0, "source_page": null, "confidence": 0.0}},
  "ptdConditions": {{"value": ["Loss of both eyes", "Loss of two limbs", "Total and irrecoverable loss of sight and loss of limb"], "source_page": null, "confidence": 0.0}},

  "permanentPartialDisabilityCovered": {{"value": true, "source_page": null, "confidence": 0.0}},
  "ppdSchedule": {{"value": [{{"disability": "Loss of one hand", "percentage": "50%"}}, {{"disability": "Loss of one eye", "percentage": "50%"}}, {{"disability": "Loss of thumb", "percentage": "25%"}}], "source_page": null, "confidence": 0.0}},

  "temporaryTotalDisabilityCovered": {{"value": true, "source_page": null, "confidence": 0.0}},
  "ttdBenefitType": {{"value": "Weekly/Monthly/Lump Sum", "source_page": null, "confidence": 0.0}},
  "ttdBenefitPercentage": {{"value": "1% of SI per week", "source_page": null, "confidence": 0.0}},
  "ttdBenefitAmount": {{"value": 0, "source_page": null, "confidence": 0.0}},
  "ttdMaximumWeeks": {{"value": 0, "source_page": null, "confidence": 0.0}},
  "ttdWaitingPeriodDays": {{"value": 0, "source_page": null, "confidence": 0.0}},

  "medicalExpensesCovered": {{"value": true, "source_page": null, "confidence": 0.0}},
  "medicalExpensesLimitType": {{"value": "Percentage of SI / Fixed Amount / Up to SI", "source_page": null, "confidence": 0.0}},
  "medicalExpensesLimitPercentage": {{"value": "percentage of SI", "source_page": null, "confidence": 0.0}},
  "medicalExpensesLimitAmount": {{"value": 0, "source_page": null, "confidence": 0.0}},
  "medicalExpensesPerAccidentOrAnnual": {{"value": "Per Accident / Per Annum / Aggregate", "source_page": null, "confidence": 0.0}},

  "educationBenefitCovered": {{"value": false, "source_page": null, "confidence": 0.0}},
  "educationBenefitAmount": {{"value": 0, "source_page": null, "confidence": 0.0}},
  "educationBenefitType": {{"value": "Lump Sum / Annual / Per Child", "source_page": null, "confidence": 0.0}},
  "loanEmiCoverCovered": {{"value": false, "source_page": null, "confidence": 0.0}},
  "loanEmiCoverMaxMonths": {{"value": 0, "source_page": null, "confidence": 0.0}},
  "loanEmiCoverMaxAmountPerMonth": {{"value": 0, "source_page": null, "confidence": 0.0}},
  "ambulanceChargesCovered": {{"value": false, "source_page": null, "confidence": 0.0}},
  "ambulanceChargesLimit": {{"value": 0, "source_page": null, "confidence": 0.0}},
  "transportMortalRemainsCovered": {{"value": false, "source_page": null, "confidence": 0.0}},
  "transportMortalRemainsLimit": {{"value": 0, "source_page": null, "confidence": 0.0}},
  "funeralExpensesCovered": {{"value": false, "source_page": null, "confidence": 0.0}},
  "funeralExpensesLimit": {{"value": 0, "source_page": null, "confidence": 0.0}},
  "homeModificationCovered": {{"value": false, "source_page": null, "confidence": 0.0}},
  "homeModificationLimit": {{"value": 0, "source_page": null, "confidence": 0.0}},
  "vehicleModificationCovered": {{"value": false, "source_page": null, "confidence": 0.0}},
  "vehicleModificationLimit": {{"value": 0, "source_page": null, "confidence": 0.0}},
  "carriageOfAttendantCovered": {{"value": false, "source_page": null, "confidence": 0.0}},
  "carriageOfAttendantLimit": {{"value": 0, "source_page": null, "confidence": 0.0}},

  "paStandardExclusions": {{"value": ["exclusion1"], "source_page": null, "confidence": 0.0}},
  "paOccupationRestrictions": {{"value": ["restriction1"], "source_page": null, "confidence": 0.0}},
  "paAgeMinimum": {{"value": 0, "source_page": null, "confidence": 0.0}},
  "paAgeMaximum": {{"value": 0, "source_page": null, "confidence": 0.0}},
  "paMaxRenewalAge": {{"value": 0, "source_page": null, "confidence": 0.0}},
  "ttdEliminationPeriod": {{"value": "number of days before TTD benefit starts", "source_page": null, "confidence": 0.0}},

  "paPremiumFrequency": {{"value": "Annual/Half-Yearly/Quarterly/Monthly", "source_page": null, "confidence": 0.0}},
  "paOccupationClass": {{"value": "Class I / Class II / Class III / Hazardous", "source_page": null, "confidence": 0.0}},
  "paAgeBand": {{"value": "Age band for premium calculation", "source_page": null, "confidence": 0.0}},
  "basePremium": {{"value": 0, "source_page": null, "confidence": 0.0}},
  "gst": {{"value": 0, "source_page": null, "confidence": 0.0}},
  "totalPremium": {{"value": 0, "source_page": null, "confidence": 0.0}},

  "paInsuredMembers": {{"value": [{{"memberName": "Name", "memberRelationship": "Self/Spouse/Son/Daughter", "memberAge": 0, "memberGender": "Male/Female", "memberSumInsured": 0}}], "source_page": null, "confidence": 0.0}}
}}

CRITICAL INSTRUCTIONS:
1. Search the ENTIRE document for each field. Look in tables, schedules, benefit summaries, T&C sections, and certificate of insurance.
2. Extract exact values as written. Do not paraphrase or summarize numeric values.
3. For accidental death benefit, search: "Accidental Death", "AD Benefit", "Death Benefit", "Death due to Accident", "Capital Sum Insured".
4. For permanent total disability, search: "Permanent Total Disability", "PTD", "Total and Permanent Disability", "Loss of Limbs", "Loss of Sight".
5. For permanent partial disability, search: "Permanent Partial Disability", "PPD", "Benefit Schedule", "Disability Schedule", "Percentage of Compensation", "Scale of Benefits".
6. For temporary total disability, search: "Temporary Total Disability", "TTD", "Weekly Benefit", "Weekly Compensation", "Loss of Income", "Temporary Disablement".
7. For sum insured, search: "Sum Insured", "Capital Sum Insured", "CSI", "Sum Assured", "Coverage Amount".
8. For exclusions, search: "Exclusions", "Not Covered", "Excluded Perils", "Self-inflicted", "Suicide", "War", "Nuclear", "Intoxication", "Adventure Sports", "Hazardous Activities".
9. For occupation class, search: "Occupation Class", "Risk Category", "Occupation Group", "Hazardous Occupation".
10. For additional benefits, search: "Education Benefit", "Loan EMI", "Ambulance", "Transportation of Mortal Remains", "Funeral Expenses", "Home Modification", "Vehicle Modification", "Carriage of Attendant".
11. Use [Page N] markers to fill source_page accurately.
12. Set confidence 1.0 for exact matches, 0.7-0.9 for inferred values, <0.5 for uncertain.
13. If field not found after thorough search, set value to null and confidence to 0.0.
14. Return ONLY valid JSON without any markdown or explanation."""
