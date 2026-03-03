"""Health insurance extraction prompt - PRD v2 format with confidence scoring."""

V2_SYSTEM_PROMPT = (
    "You are an expert health insurance policy analyst for the Indian market. "
    "Extract policy details accurately from the document text. "
    "Return ONLY valid JSON. Do not use ```json or ``` markers. "
    "For every field, return {\"value\": <extracted_value>, \"source_page\": <page_number_or_null>, \"confidence\": <0.0_to_1.0>}. "
    "Set confidence based on how clearly the value appears in the document: "
    "1.0 = exact match found, 0.7-0.9 = inferred from nearby text in the document, 0.3-0.6 = uncertain, 0.0 = not found (value=null). "
    "CRITICAL: Extract ONLY from the provided document text. NEVER use your own knowledge about insurance products "
    "(e.g., standard Star Health FHO benefits, typical HDFC Ergo features). "
    "If a benefit is NOT explicitly mentioned in the document, set value=null and confidence=0.0. "
    "Every non-null field MUST have a valid source_page from the document."
)


def build_health_extraction_prompt(extracted_text: str) -> str:
    return f"""Analyze this HEALTH INSURANCE policy document and extract ALL fields below.
The document has [Page N] markers - use them to report source_page for each field.

Document Text:
{extracted_text}

Return a JSON object where EVERY field uses this format:
{{"value": <extracted_value>, "source_page": <page_number_or_null>, "confidence": <0.0_to_1.0>}}

Extract these fields:
{{
  "policyNumber": {{"value": "string", "source_page": null, "confidence": 0.0}},
  "uin": {{"value": "UIN/IRDAI product code", "source_page": null, "confidence": 0.0, "_hint": "The UIN (Unique Identification Number) is an IRDAI-assigned product code. Format is typically: XXXHLIPYYYYY or IRDAN###XXXXXXX (e.g., CHIHLIP23128V012223, TATHLIP23118V032223, SHAHLIP25039V082425). Look in: (1) page footers/headers, (2) near policy schedule, (3) product details section. Do NOT extract the product name or internal reference numbers as UIN. If no UIN matching the standard pattern is found, set value=null."}},
  "insurerName": {{"value": "Insurance company name", "source_page": null, "confidence": 0.0}},
  "insurerRegistrationNumber": {{"value": "IRDAI registration number", "source_page": null, "confidence": 0.0}},
  "insurerTollFree": {{"value": "Toll-free number", "source_page": null, "confidence": 0.0}},
  "insurerAddress": {{"value": "Insurer office address. IMPORTANT: Extract the address shown on the policy schedule or certificate page (typically first 1-3 pages), NOT from general T&C or conditions sections. If multiple addresses appear, prefer the one nearest to the policy number/policyholder details.", "source_page": null, "confidence": 0.0}},
  "productName": {{"value": "Plan tier/variant name (e.g. Platinum Plan, Gold, Supreme, Advantage). Prefer the specific plan name over the generic product brand.", "source_page": null, "confidence": 0.0}},
  "policyType": {{"value": "Individual/Family Floater/Group", "source_page": null, "confidence": 0.0}},
  "coverType": {{"value": "Individual/Floater", "source_page": null, "confidence": 0.0}},
  "policyPeriod": {{"value": "Start to End date string", "source_page": null, "confidence": 0.0}},
  "policyPeriodStart": {{"value": "YYYY-MM-DD", "source_page": null, "confidence": 0.0}},
  "policyPeriodEnd": {{"value": "YYYY-MM-DD", "source_page": null, "confidence": 0.0}},
  "policyHolderName": {{"value": "Name as in document", "source_page": null, "confidence": 0.0}},

  "tpaName": {{"value": "TPA name", "source_page": null, "confidence": 0.0}},
  "intermediaryName": {{"value": "Intermediary name", "source_page": null, "confidence": 0.0}},
  "intermediaryCode": {{"value": "IRDAI intermediary code", "source_page": null, "confidence": 0.0, "_hint": "Extract the IRDAI-issued broker/intermediary code (e.g. 'BA0000081897', '0001431006'). Do NOT use internal product/fulfiller codes like 'SH4080'. Prefer codes labeled 'Intermediary Code' or 'Broker Code' over 'Fulfiller Code'."}},
  "intermediaryEmail": {{"value": "Intermediary email", "source_page": null, "confidence": 0.0}},

  "insuredMembers": {{"value": [{{"memberName": "Name", "memberRelationship": "Self/Spouse/Son/Daughter/Father/Mother", "memberAge": 30, "memberGender": "Male/Female", "memberDOB": "YYYY-MM-DD or null", "memberSumInsured": 0, "memberCopay": 0, "memberOPLimit": 0, "memberPED": "condition or null"}}], "source_page": null, "confidence": 0.0, "_hint": "Extract ALL per-member details from the insured members table. memberSumInsured is the individual Sum Insured for each member (important for Individual policies where each member may have different SI). memberCopay is the co-payment percentage per member. memberOPLimit is the outpatient limit per member. memberPED is the pre-existing disease declared for that specific member (e.g. 'Hypertension', 'No PED Declared')."}},
  "totalMembersCovered": {{"value": 0, "source_page": null, "confidence": 0.0}},

  "sumInsured": {{"value": 0, "source_page": null, "confidence": 0.0}},
  "roomRentLimit": {{"value": "No cap / 1% of SI / amount per day", "source_page": null, "confidence": 0.0}},
  "roomRentCopay": {{"value": "percentage or amount", "source_page": null, "confidence": 0.0}},
  "icuLimit": {{"value": "No Capping / amount per day", "source_page": null, "confidence": 0.0}},
  "icuDailyLimit": {{"value": "ICU daily limit in rupees", "source_page": null, "confidence": 0.0}},
  "preHospitalization": {{"value": "30 days / 60 days", "source_page": null, "confidence": 0.0}},
  "postHospitalization": {{"value": "60 days / 90 days / 180 days", "source_page": null, "confidence": 0.0}},
  "dayCareProcedures": {{"value": "540+ procedures / true / false", "source_page": null, "confidence": 0.0, "_hint": "Look for 'Day Care Procedures', 'Day Care Treatment', 'Day Care Surgery', or any mention of day care in the hospitalization coverage section. Also check for '24-hour hospitalization not required' or 'less than 24 hours'. If day care is covered, set value to the details or true."}},
  "domiciliaryHospitalization": {{"value": "Up to SI / true / false", "source_page": null, "confidence": 0.0}},
  "ambulanceCover": {{"value": "amount or As per actual", "source_page": null, "confidence": 0.0}},
  "healthCheckup": {{"value": "details or amount", "source_page": null, "confidence": 0.0}},
  "ayushTreatment": {{"value": "Up to SI / true / false", "source_page": null, "confidence": 0.0}},
  "organDonor": {{"value": "Up to SI / true / false", "source_page": null, "confidence": 0.0}},
  "restoration": {{"value": "100% of SI / true / false", "source_page": null, "confidence": 0.0, "_hint": "Look for 'Restoration', 'Automatic Recharge', 'Unlimited Recharge', 'Reinstatement of Sum Insured', or 'Recharge Benefit'. If any of these exist as a benefit, extract the details (e.g. '100% of SI', 'Unlimited Automatic Recharge'). If not mentioned, set value=false."}},
  "restorationAmount": {{"value": "restoration details", "source_page": null, "confidence": 0.0}},
  "modernTreatment": {{"value": "Up to SI / details", "source_page": null, "confidence": 0.0}},
  "modernTreatmentLimit": {{"value": "Up to SI / 50% of SI", "source_page": null, "confidence": 0.0}},
  "mentalHealthCovered": {{"value": true, "source_page": null, "confidence": 0.0}},
  "mentalHealthLimit": {{"value": "coverage limit", "source_page": null, "confidence": 0.0}},
  "dailyCashAllowance": {{"value": "amount per day", "source_page": null, "confidence": 0.0}},
  "convalescenceBenefit": {{"value": "recovery benefit details", "source_page": null, "confidence": 0.0}},
  "consumablesCoverage": {{"value": true, "source_page": null, "confidence": 0.0, "_hint": "ONLY set true if the word 'consumables' or 'consumable cover' appears as an EXPLICIT separate line item/benefit in the policy schedule or benefit summary table. Look for exact terms: 'Consumables', 'Consumable Cover', 'Consumable Expenses'. Generic coverage phrases like 'Covered up to Sum Insured' for other benefits do NOT count. If no explicit consumables line item exists in the benefit table, set value=false."}},
  "consumablesCoverageDetails": {{"value": "details", "source_page": null, "confidence": 0.0}},

  "initialWaitingPeriod": {{"value": "30 Days (except accidents)", "source_page": null, "confidence": 0.0}},
  "preExistingDiseaseWaiting": {{"value": "36/48/24 months", "source_page": null, "confidence": 0.0}},
  "specificDiseaseWaiting": {{"value": "24 months", "source_page": null, "confidence": 0.0}},
  "maternityWaiting": {{"value": "24/36 months", "source_page": null, "confidence": 0.0}},
  "accidentCoveredFromDay1": {{"value": true, "source_page": null, "confidence": 0.0}},
  "specificDiseasesList": {{"value": ["disease1", "disease2"], "source_page": null, "confidence": 0.0}},

  "generalCopay": {{"value": "0% / 10% / 20%", "source_page": null, "confidence": 0.0, "_hint": "Extract ONLY the copay PERCENTAGE as a number (0, 10, 20, etc.). If copay is age-based (e.g. '20% for members above 61 years'), extract the percentage (20), NOT the age. If no copay is mentioned anywhere, set value to '0%'."}},
  "ageBasedCopay": {{"value": [{{"ageBracket": "0-45", "copayPercentage": 0}}], "source_page": null, "confidence": 0.0}},
  "diseaseSpecificCopay": {{"value": [{{"disease": "name", "copayPercentage": 20}}], "source_page": null, "confidence": 0.0}},

  "cataractLimit": {{"value": "amount per eye", "source_page": null, "confidence": 0.0}},
  "jointReplacementLimit": {{"value": "amount per joint", "source_page": null, "confidence": 0.0}},
  "internalProsthesisLimit": {{"value": "amount", "source_page": null, "confidence": 0.0}},
  "kidneyStoneLimit": {{"value": "amount", "source_page": null, "confidence": 0.0}},
  "gallStoneLimit": {{"value": "amount", "source_page": null, "confidence": 0.0}},
  "otherSubLimits": {{"value": ["sub-limit1"], "source_page": null, "confidence": 0.0}},

  "permanentExclusions": {{"value": ["exclusion1"], "source_page": null, "confidence": 0.0}},
  "conditionalExclusions": {{"value": ["exclusion1"], "source_page": null, "confidence": 0.0}},
  "preExistingConditions": {{"value": ["condition1"], "source_page": null, "confidence": 0.0}},
  "pedSpecificExclusions": {{"value": ["clause1"], "source_page": null, "confidence": 0.0}},

  "basePremium": {{"value": 0, "source_page": null, "confidence": 0.0, "_hint": "Extract the TOTAL base plan premium for ALL insured members combined, EXCLUDING add-on/rider premiums. If the premium schedule shows per-member breakdowns, SUM all members' base premiums. Do NOT extract just one member's premium."}},
  "gst": {{"value": 0, "source_page": null, "confidence": 0.0, "_hint": "Extract the GST/tax amount. If the policy explicitly states GST is exempt, nil, or 0, set value=0 with confidence=1.0 (this is a confirmed value, not missing). If GST is not mentioned at all, set value=null, confidence=0.0."}},
  "totalPremium": {{"value": 0, "source_page": null, "confidence": 0.0}},
  "premiumFrequency": {{"value": "Annual/Half-Yearly/Quarterly/Monthly/Single Premium. Look for 'Premium Payment Mode' or 'Payment Frequency' field.", "source_page": null, "confidence": 0.0}},
  "otherAddOnPremiums": {{"value": {{}}, "source_page": null, "confidence": 0.0, "_hint": "Dict of ALL add-on/rider premium amounts from the premium schedule e.g. {{\"Care Shield\": 1470, \"Annual Health Checkup\": 535}}. Include every line item beyond base premium."}},
  "existingCustomerDiscount": {{"value": 0, "source_page": null, "confidence": 0.0, "_hint": "Any discount applied (loyalty/renewal/existing customer discount amount). Extract as positive number."}},
  "healthGracePeriod": {{"value": "30 days", "source_page": null, "confidence": 0.0}},

  "ncbPercentage": {{"value": "10%/20%", "source_page": null, "confidence": 0.0, "_hint": "No Claim Bonus (NCB) or Cumulative Bonus (CB) percentage. Some insurers use branded names: HDFC ERGO 'Plus Benefit' = NCB (50% SI increase per claim-free year), Star Health 'Cumulative Bonus'. Extract the percentage value. If an NCB/CB benefit exists under any name, extract its percentage."}},
  "currentNcb": {{"value": "current percentage", "source_page": null, "confidence": 0.0}},
  "maxNcbPercentage": {{"value": "50%", "source_page": null, "confidence": 0.0, "_hint": "Maximum No Claim Bonus percentage allowed by the product. Look for 'Maximum Bonus', 'Max CB', 'Bonus up to'. Some products allow up to 100% (e.g., Star Health FHO allows up to 100% of SI). Do NOT assume 50% as default — extract from document or set null if not found."}},
  "ncbAmount": {{"value": "amount in rupees", "source_page": null, "confidence": 0.0}},
  "ncbProtect": {{"value": true, "source_page": null, "confidence": 0.0}},
  "ncbBoost": {{"value": true, "source_page": null, "confidence": 0.0}},
  "accumulatedNcbAmount": {{"value": "amount", "source_page": null, "confidence": 0.0}},
  "cumulativeBonusAmount": {{"value": "amount", "source_page": null, "confidence": 0.0, "_hint": "Look for 'Cumulative Bonus', 'Cumulative Bonus Amount', 'CB Amount', 'Bonus Amount', 'Accrued Bonus'. In Tata AIG policies look for 'Cumulative Bonus' in the policy schedule table. Extract the numeric amount in rupees. Also check 'Limit of Coverage' or 'Sum at Risk' minus 'Sum Insured' to derive the bonus amount."}},
  "inflationShieldAmount": {{"value": "amount", "source_page": null, "confidence": 0.0}},
  "totalEffectiveCoverage": {{"value": "total SI including bonuses", "source_page": null, "confidence": 0.0}},

  "hasAddOn": {{"value": true, "source_page": null, "confidence": 0.0}},
  "addOnPoliciesList": {{"value": [{{"addOnName": "name", "uin": "uin", "sumInsured": 0, "premium": 0}}], "source_page": null, "confidence": 0.0}},
  "claimShield": {{"value": true, "source_page": null, "confidence": 0.0}},
  "ncbShield": {{"value": true, "source_page": null, "confidence": 0.0}},
  "inflationShield": {{"value": true, "source_page": null, "confidence": 0.0}},
  "inflationShieldPercentage": {{"value": "10%", "source_page": null, "confidence": 0.0}},

  "declaredConditions": {{"value": ["condition1"], "source_page": null, "confidence": 0.0}},
  "pedWaitingPeriodCompleted": {{"value": true, "source_page": null, "confidence": 0.0, "_hint": "true if PED waiting is 'no waiting period', or if policy shows 'PED wait period reduced to 0', or if continuity benefit waives PED waiting, or if firstEnrollmentDate is old enough that waiting is completed."}},
  "pedStatus": {{"value": "None Declared / PED mentioned", "source_page": null, "confidence": 0.0}},

  "firstEnrollmentDate": {{"value": "date", "source_page": null, "confidence": 0.0}},
  "insuredSinceDate": {{"value": "date", "source_page": null, "confidence": 0.0}},
  "previousPolicyNumber": {{"value": "number", "source_page": null, "confidence": 0.0, "_hint": "Extract the COMPLETE previous/prior/old policy number. If the number spans multiple lines in the PDF, concatenate all parts. Do NOT use the CURRENT policy number. If no previous policy number is explicitly mentioned, set value=null."}},
  "continuousCoverageYears": {{"value": 0, "source_page": null, "confidence": 0.0}},
  "claimHistory": {{"value": "claims info", "source_page": null, "confidence": 0.0}},
  "portability": {{"value": {{"available": true, "waitingPeriodCredit": "details"}}, "source_page": null, "confidence": 0.0}},

  "networkHospitalsCount": {{"value": "14000+", "source_page": null, "confidence": 0.0}},
  "cashlessFacility": {{"value": true, "source_page": null, "confidence": 0.0}},
  "networkType": {{"value": "Pan India", "source_page": null, "confidence": 0.0}},
  "claimSettlementRatio": {{"value": "92%", "source_page": null, "confidence": 0.0}},
  "claimProcess": {{"value": "Cashless & Reimbursement", "source_page": null, "confidence": 0.0}},
  "claimIntimation": {{"value": "Within 24 hours", "source_page": null, "confidence": 0.0}},
  "claimDocuments": {{"value": ["doc1"], "source_page": null, "confidence": 0.0}},
  "preAuthTurnaround": {{"value": "turnaround times", "source_page": null, "confidence": 0.0}}
}}

CRITICAL INSTRUCTIONS:
1. Search the ENTIRE document for each field. Look in tables, schedules, benefit summaries, T&C sections.
2. Extract exact values as written. Do not paraphrase or summarize numeric values.
3. For room rent, search: "Room Rent", "Single Room", "Room charges", "Accommodation".
4. For waiting periods, search: "Waiting Period", "Pre-existing", "PED", "Cooling off".
5. For sub-limits, search: "Cataract", "Joint Replacement", "Internal Prosthesis", "Sub-limit".
6. For copay, search: "Co-pay", "Co-payment", "Cost sharing".
7. Use [Page N] markers to fill source_page accurately. Every non-null field MUST have a source_page.
8. Set confidence 1.0 for exact matches, 0.7-0.9 for inferred from nearby document text, <0.5 for uncertain.
9. If field not found after thorough search, set value to null and confidence to 0.0.
10. Return ONLY valid JSON without any markdown or explanation.
11. NEVER use your knowledge of insurance products to fill in values. Only extract what is EXPLICITLY written in the document text. If a policy schedule does not list room rent limits, waiting periods, network hospitals count, or other benefit details, those fields must be null — do NOT fill them from standard product features you know about."""
