"""Travel insurance extraction prompt - PRD v2 format with confidence scoring."""

V2_SYSTEM_PROMPT = (
    "You are an expert travel insurance policy analyst for the Indian market. "
    "Extract policy details accurately from the document text. "
    "Return ONLY valid JSON. Do not use ```json or ``` markers. "
    "For every field, return {\"value\": <extracted_value>, \"source_page\": <page_number_or_null>, \"confidence\": <0.0_to_1.0>}. "
    "Set confidence based on how clearly the value appears in the document: "
    "1.0 = exact match found, 0.7-0.9 = inferred from context, 0.3-0.6 = uncertain, 0.0 = not found (value=null)."
)


def build_travel_extraction_prompt(extracted_text: str) -> str:
    return f"""Analyze this TRAVEL INSURANCE policy document and extract ALL fields below.
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
  "policyIssueDate": {{"value": "YYYY-MM-DD", "source_page": null, "confidence": 0.0}},
  "policyStatus": {{"value": "Active/Expired/Cancelled", "source_page": null, "confidence": 0.0}},
  "tripType": {{"value": "Single Trip/Annual Multi-Trip/Student/Business/Senior Citizen", "source_page": null, "confidence": 0.0}},
  "travelType": {{"value": "International/Domestic/Both", "source_page": null, "confidence": 0.0}},
  "geographicCoverage": {{"value": "worldwide/worldwide_excl_usa_canada/schengen/asia/specific_countries/domestic", "source_page": null, "confidence": 0.0}},
  "policyPeriodStart": {{"value": "YYYY-MM-DD", "source_page": null, "confidence": 0.0, "_hint": "For travel insurance, this is the trip start date / 'Travel Dates: From' / coverage start date. Use the same date as tripStartDate."}},
  "policyPeriodEnd": {{"value": "YYYY-MM-DD", "source_page": null, "confidence": 0.0, "_hint": "For travel insurance, this is the trip end date / 'Travel Dates: To' / coverage end date. Use the same date as tripEndDate."}},

  "tripStartDate": {{"value": "YYYY-MM-DD", "source_page": null, "confidence": 0.0}},
  "tripEndDate": {{"value": "YYYY-MM-DD", "source_page": null, "confidence": 0.0}},
  "tripDuration": {{"value": "number of days", "source_page": null, "confidence": 0.0}},
  "destinationCountries": {{"value": ["country1", "country2"], "source_page": null, "confidence": 0.0}},
  "originCountry": {{"value": "country name", "source_page": null, "confidence": 0.0}},
  "purposeOfTravel": {{"value": "Leisure/Business/Education/Employment/Pilgrimage", "source_page": null, "confidence": 0.0}},

  "travellers": {{"value": [{{"name": "Name", "age": 0, "dateOfBirth": "YYYY-MM-DD", "relationship": "Self/Spouse/Child/Parent", "passportNumber": "string", "preExistingConditionsDeclared": true}}], "source_page": null, "confidence": 0.0, "_hint": "IMPORTANT: Always compute 'age' from dateOfBirth and policyIssueDate if DOB is available. age = floor(policyIssueDate - dateOfBirth in years). Do NOT leave age as 0 if DOB is known."}},
  "policyHolderName": {{"value": "Name as in document", "source_page": null, "confidence": 0.0}},

  "medicalExpenses": {{"value": 0, "source_page": null, "confidence": 0.0}},
  "medicalDeductible": {{"value": 0, "source_page": null, "confidence": 0.0}},
  "coverageIncludes": {{"value": ["Hospitalization", "OPD", "Dental Emergency", "Physiotherapy"], "source_page": null, "confidence": 0.0}},
  "emergencyMedicalEvacuation": {{"value": 0, "source_page": null, "confidence": 0.0, "_hint": "IMPORTANT: If the benefit table says 'INCLUDED' or 'INCLUDED*' (meaning included under the overall medical limit), set value to the medicalExpenses amount (e.g. 200000 if medical is $200,000). Do NOT set to null or 0 for INCLUDED benefits. 'INCLUDED' means it IS covered. Extract the numeric limit, or the medical expenses amount if no separate limit is given."}},
  "repatriationOfRemains": {{"value": 0, "source_page": null, "confidence": 0.0, "_hint": "IMPORTANT: If the benefit table says 'INCLUDED' or 'INCLUDED*' (meaning included under overall medical limit), set value to the medicalExpenses amount. 'INCLUDED' means it IS covered - do NOT return null or 0."}},
  "covidTreatmentCovered": {{"value": true, "source_page": null, "confidence": 0.0}},
  "covidQuarantineCovered": {{"value": true, "source_page": null, "confidence": 0.0}},
  "covidQuarantineLimit": {{"value": 0, "source_page": null, "confidence": 0.0}},
  "cashlessNetworkAvailable": {{"value": true, "source_page": null, "confidence": 0.0}},
  "cashlessNetworkName": {{"value": "Network provider name", "source_page": null, "confidence": 0.0}},
  "cashlessHospitalsCount": {{"value": "number of hospitals", "source_page": null, "confidence": 0.0}},
  "assistanceHelplineForCashless": {{"value": "helpline number", "source_page": null, "confidence": 0.0}},
  "preExistingCovered": {{"value": true, "source_page": null, "confidence": 0.0}},
  "preExistingConditions": {{"value": ["condition1"], "source_page": null, "confidence": 0.0}},
  "preExistingLimit": {{"value": 0, "source_page": null, "confidence": 0.0}},
  "preExistingAgeRestriction": {{"value": "age limit for PED coverage", "source_page": null, "confidence": 0.0}},
  "maternityCovered": {{"value": true, "source_page": null, "confidence": 0.0}},

  "tripCancellation": {{"value": 0, "source_page": null, "confidence": 0.0}},
  "tripCancellationCoveredReasons": {{"value": ["reason1", "reason2"], "source_page": null, "confidence": 0.0}},
  "tripCancellationNotCoveredReasons": {{"value": ["reason1", "reason2"], "source_page": null, "confidence": 0.0}},
  "tripInterruption": {{"value": 0, "source_page": null, "confidence": 0.0}},
  "tripCurtailmentCovered": {{"value": true, "source_page": null, "confidence": 0.0}},
  "tripCurtailmentLimit": {{"value": 0, "source_page": null, "confidence": 0.0}},
  "tripCurtailmentBenefitType": {{"value": "Reimbursement/Lump Sum/Pro-rata", "source_page": null, "confidence": 0.0}},
  "flightDelay": {{"value": 0, "source_page": null, "confidence": 0.0}},
  "tripDelayTriggerHours": {{"value": 0, "source_page": null, "confidence": 0.0}},
  "tripDelayCoveredExpenses": {{"value": ["Meals", "Accommodation", "Transport"], "source_page": null, "confidence": 0.0}},
  "missedConnectionCovered": {{"value": true, "source_page": null, "confidence": 0.0}},
  "missedConnectionTriggerHours": {{"value": 0, "source_page": null, "confidence": 0.0}},
  "missedConnectionBenefitAmount": {{"value": 0, "source_page": null, "confidence": 0.0}},
  "hijackDistress": {{"value": 0, "source_page": null, "confidence": 0.0}},

  "baggageLoss": {{"value": 0, "source_page": null, "confidence": 0.0}},
  "baggagePerItemLimit": {{"value": 0, "source_page": null, "confidence": 0.0}},
  "baggageValuablesLimit": {{"value": 0, "source_page": null, "confidence": 0.0}},
  "baggageDocumentationRequired": {{"value": ["PIR from airline", "Purchase receipts", "Police report"], "source_page": null, "confidence": 0.0}},
  "baggageDelay": {{"value": 0, "source_page": null, "confidence": 0.0}},
  "passportLoss": {{"value": 0, "source_page": null, "confidence": 0.0}},

  "personalLiability": {{"value": 0, "source_page": null, "confidence": 0.0}},
  "accidentalDeath": {{"value": 0, "source_page": null, "confidence": 0.0}},
  "permanentDisability": {{"value": 0, "source_page": null, "confidence": 0.0}},
  "homeburglary": {{"value": 0, "source_page": null, "confidence": 0.0}},

  "adventureSportsExclusion": {{"value": true, "source_page": null, "confidence": 0.0}},
  "sportsCoveredList": {{"value": ["sport1", "sport2"], "source_page": null, "confidence": 0.0}},
  "sportsExcludedList": {{"value": ["sport1", "sport2"], "source_page": null, "confidence": 0.0}},
  "adventureAdditionalPremium": {{"value": 0, "source_page": null, "confidence": 0.0}},

  "travelBasePremium": {{"value": 0, "source_page": null, "confidence": 0.0}},
  "travelGst": {{"value": 0, "source_page": null, "confidence": 0.0}},
  "travelTotalPremium": {{"value": 0, "source_page": null, "confidence": 0.0}},
  "premiumPerDay": {{"value": 0, "source_page": null, "confidence": 0.0}},
  "premiumAgeBand": {{"value": "age band used for premium calculation", "source_page": null, "confidence": 0.0}},
  "premiumDestinationZone": {{"value": "zone used for premium calculation", "source_page": null, "confidence": 0.0}},
  "premiumCoverageLevel": {{"value": "Silver/Gold/Platinum/Comprehensive", "source_page": null, "confidence": 0.0}},
  "coverageCurrency": {{"value": "USD/EUR/INR", "source_page": null, "confidence": 0.0}},
  "deductiblePerClaim": {{"value": 0, "source_page": null, "confidence": 0.0, "_hint": "Primary deductible amount per claim. Use the medicalDeductible value if a separate per-claim deductible is not stated. This is the amount the insured pays before the insurer pays."}},
  "schengenCompliant": {{"value": true, "source_page": null, "confidence": 0.0}},

  "emergencyHelpline24x7": {{"value": "24x7 helpline number", "source_page": null, "confidence": 0.0}},
  "claimsEmail": {{"value": "claims email address", "source_page": null, "confidence": 0.0}},
  "insurerAddress": {{"value": "Insurer office address", "source_page": null, "confidence": 0.0}},
  "primaryContactName": {{"value": "primary contact person name", "source_page": null, "confidence": 0.0}},
  "primaryContactPhone": {{"value": "primary contact phone", "source_page": null, "confidence": 0.0}},
  "primaryContactEmail": {{"value": "primary contact email", "source_page": null, "confidence": 0.0}},
  "emergencyContactIndiaName": {{"value": "emergency contact in India name", "source_page": null, "confidence": 0.0}},
  "emergencyContactIndiaRelationship": {{"value": "relationship with traveller", "source_page": null, "confidence": 0.0}},
  "emergencyContactIndiaPhone": {{"value": "emergency contact phone in India", "source_page": null, "confidence": 0.0}}
}}

CRITICAL INSTRUCTIONS:
1. Search the ENTIRE document for each field. Look in tables, schedules, benefit summaries, coverage schedules, T&C sections.
2. Extract exact values as written. Do not paraphrase or summarize numeric values.
3. For sum insured / medical cover, search: "Sum Insured", "Medical Expenses", "Medical Cover", "Coverage Amount", "Aggregate Limit".
4. For trip cancellation, search: "Trip Cancellation", "Cancellation Charges", "Cancellation Cover", "Trip Interruption".
5. For baggage, search: "Baggage", "Checked-in Baggage", "Baggage Loss", "Baggage Delay", "Personal Effects".
6. For flight delay, search: "Flight Delay", "Trip Delay", "Delay of Flight", "Missed Connection", "Travel Delay".
7. For evacuation, search: "Medical Evacuation", "Emergency Evacuation", "Repatriation", "Repatriation of Mortal Remains".
8. For Schengen compliance, search: "Schengen", "Schengen Visa", "EU Regulation", "Minimum Cover EUR 30000".
9. For coverage schedule, search: "Coverage Schedule", "Schedule of Benefits", "Benefit Table", "Sum Insured Schedule".
10. For adventure sports, search: "Adventure Sports", "Hazardous Activities", "Winter Sports", "Extreme Sports", "Excluded Sports".
11. For geographic coverage, search: "Geographic Scope", "Territory", "Worldwide", "Destination", "Zone", "Applicable Countries".
12. For COVID coverage, search: "Covid", "COVID-19", "Pandemic", "Quarantine", "Coronavirus".
13. Use [Page N] markers to fill source_page accurately.
14. Set confidence 1.0 for exact matches, 0.7-0.9 for inferred values, <0.5 for uncertain.
15. If field not found after thorough search, set value to null and confidence to 0.0.
16. INCLUDED BENEFITS: Many travel policies show benefits as 'INCLUDED' or 'INCLUDED*' meaning they are covered under the overall medical limit. For emergencyMedicalEvacuation and repatriationOfRemains, if the benefit says 'INCLUDED', set the value to the medicalExpenses amount. Do NOT treat 'INCLUDED' as null/0 — it means the benefit IS covered.
17. POLICY PERIOD: For travel insurance, policyPeriodStart = tripStartDate and policyPeriodEnd = tripEndDate. Always extract both.
18. DEDUCTIBLE: If deductiblePerClaim is not separately stated, use the medicalDeductible amount. These are the same concept in most travel policies.
19. Return ONLY valid JSON without any markdown or explanation."""
