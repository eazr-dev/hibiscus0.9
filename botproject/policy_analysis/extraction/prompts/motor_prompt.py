"""Motor insurance extraction prompt - PRD v2 format with confidence scoring."""

V2_SYSTEM_PROMPT = (
    "You are an expert motor insurance policy analyst for the Indian market. "
    "Extract policy details accurately from the document text. "
    "Return ONLY valid JSON. Do not use ```json or ``` markers. "
    "For every field, return {\"value\": <extracted_value>, \"source_page\": <page_number_or_null>, \"confidence\": <0.0_to_1.0>}. "
    "Set confidence based on how clearly the value appears in the document: "
    "1.0 = exact match found, 0.7-0.9 = inferred from context, 0.3-0.6 = uncertain, 0.0 = not found (value=null)."
)


def build_motor_extraction_prompt(extracted_text: str) -> str:
    return f"""Analyze this MOTOR INSURANCE policy document and extract ALL fields below.
The document has [Page N] markers - use them to report source_page for each field.

Document Text:
{extracted_text}

Return a JSON object where EVERY field uses this format:
{{"value": <extracted_value>, "source_page": <page_number_or_null>, "confidence": <0.0_to_1.0>}}

Extract these fields:
{{
  // ── Section 1: Policy Basics ──
  "policyNumber": {{"value": "string", "source_page": null, "confidence": 0.0}},
  "uin": {{"value": "UIN/IRDAI product code (e.g., IRDAN157RP0033V02201920)", "source_page": null, "confidence": 0.0}},
  "certificateNumber": {{"value": "Certificate number", "source_page": null, "confidence": 0.0}},
  "coverNoteNumber": {{"value": "Cover note number", "source_page": null, "confidence": 0.0}},
  "productType": {{"value": "Comprehensive/Third Party Only/Standalone OD", "source_page": null, "confidence": 0.0}},
  "insurerName": {{"value": "Insurance company name", "source_page": null, "confidence": 0.0}},
  "policyPeriodStart": {{"value": "YYYY-MM-DD", "source_page": null, "confidence": 0.0}},
  "policyPeriodEnd": {{"value": "YYYY-MM-DD", "source_page": null, "confidence": 0.0}},
  "policyTerm": {{"value": 1, "source_page": null, "confidence": 0.0}},
  "previousPolicyNumber": {{"value": "Previous policy number", "source_page": null, "confidence": 0.0}},
  "previousInsurer": {{"value": "Previous insurance company name", "source_page": null, "confidence": 0.0}},
  "insurerTollFree": {{"value": "Insurer toll-free helpline number", "source_page": null, "confidence": 0.0}},
  "claimEmail": {{"value": "Insurer CLAIMS-SPECIFIC email (look for 'Claims Registration', 'general.claims@', 'claims@', 'motor.claims@', NOT the generic 'customersupport@' or 'customer.care@' email)", "source_page": null, "confidence": 0.0}},
  "claimApp": {{"value": "Insurer claims app name or URL", "source_page": null, "confidence": 0.0}},

  // ── Section 2: Vehicle Details ──
  "registrationNumber": {{"value": "MH01AB1234", "source_page": null, "confidence": 0.0}},
  "vehicleClass": {{"value": "Private Car/Two Wheeler/Commercial", "source_page": null, "confidence": 0.0}},
  "vehicleCategory": {{"value": "private_car/two_wheeler/commercial/pcv/gcv", "source_page": null, "confidence": 0.0}},
  "vehicleMake": {{"value": "Maruti Suzuki/Honda/Hyundai", "source_page": null, "confidence": 0.0}},
  "vehicleModel": {{"value": "Swift VXi/City/Creta", "source_page": null, "confidence": 0.0}},
  "vehicleVariant": {{"value": "VXi/ZXi/SXi", "source_page": null, "confidence": 0.0}},
  "manufacturingYear": {{"value": 2020, "source_page": null, "confidence": 0.0}},
  "registrationDate": {{"value": "YYYY-MM-DD", "source_page": null, "confidence": 0.0}},
  "engineNumber": {{"value": "Engine number", "source_page": null, "confidence": 0.0}},
  "chassisNumber": {{"value": "Chassis number", "source_page": null, "confidence": 0.0}},
  "fuelType": {{"value": "Petrol/Diesel/CNG/LPG/Electric/Hybrid", "source_page": null, "confidence": 0.0}},
  "cubicCapacity": {{"value": "1197", "source_page": null, "confidence": 0.0}},
  "seatingCapacity": {{"value": 5, "source_page": null, "confidence": 0.0}},
  "vehicleColor": {{"value": "White/Black/Silver", "source_page": null, "confidence": 0.0}},
  "rtoLocation": {{"value": "Mumbai/Delhi", "source_page": null, "confidence": 0.0}},
  "hypothecation": {{"value": {{"isHypothecated": true, "financierName": "Bank name", "loanAccountNumber": "Loan account"}}, "source_page": null, "confidence": 0.0}},

  // ── Section 3: Owner / Policyholder Details ──
  "ownerName": {{"value": "Owner full name", "source_page": null, "confidence": 0.0}},
  "ownerType": {{"value": "individual/company/firm/trust", "source_page": null, "confidence": 0.0}},
  "ownerAddress": {{"value": "Full address", "source_page": null, "confidence": 0.0}},
  "ownerAddressCity": {{"value": "City", "source_page": null, "confidence": 0.0}},
  "ownerAddressState": {{"value": "State", "source_page": null, "confidence": 0.0}},
  "ownerAddressPincode": {{"value": "Pincode", "source_page": null, "confidence": 0.0}},
  "ownerContact": {{"value": "Phone number", "source_page": null, "confidence": 0.0}},
  "ownerEmail": {{"value": "POLICYHOLDER/OWNER email ONLY. Do NOT use intermediary/broker/agent email (look for 'Intermediary', 'Broker', 'Agent' labels near the email to exclude them).", "source_page": null, "confidence": 0.0}},
  "ownerPan": {{"value": "POLICYHOLDER/OWNER PAN ONLY. Indian PAN format: AAAPL1234C — the 4th letter indicates entity type: P=Person, C=Company, F=Firm. Only extract PAN where 4th letter is P (personal). Do NOT use the insurer/company PAN.", "source_page": null, "confidence": 0.0}},

  // ── Section 4: Coverage Details ──
  "idv": {{"value": 500000, "source_page": null, "confidence": 0.0}},
  "idvMinimum": {{"value": 0, "source_page": null, "confidence": 0.0}},
  "idvMaximum": {{"value": 0, "source_page": null, "confidence": 0.0}},
  "odPremium": {{"value": 5000, "source_page": null, "confidence": 0.0}},
  "tpPremium": {{"value": "Third-party LIABILITY premium ONLY (Act Liability / Basic TP). For Standalone OD policies, tpPremium MUST be 0. Do NOT put PA/CPA premium here.", "source_page": null, "confidence": 0.0}},
  "compulsoryDeductible": {{"value": 0, "source_page": null, "confidence": 0.0}},
  "voluntaryDeductible": {{"value": 0, "source_page": null, "confidence": 0.0}},
  "geographicScope": {{"value": "India", "source_page": null, "confidence": 0.0}},
  "paOwnerCover": {{"value": 1500000, "source_page": null, "confidence": 0.0}},
  "paUnnamedPassengers": {{"value": "TOTAL cover amount for all unnamed passengers combined (number_of_persons × per_person_limit). E.g. if 7 persons at Rs.40,000 each → 280000. Do NOT put just the person count here.", "source_page": null, "confidence": 0.0}},
  "paUnnamedPassengersPerPerson": {{"value": "Per-person PA limit for unnamed passengers. E.g. 40000 or 100000.", "source_page": null, "confidence": 0.0}},
  "paPaidDriver": {{"value": 200000, "source_page": null, "confidence": 0.0}},
  "llPaidDriver": {{"value": true, "source_page": null, "confidence": 0.0}},
  "llEmployees": {{"value": 0, "source_page": null, "confidence": 0.0}},
  "tppdCover": {{"value": 750000, "source_page": null, "confidence": 0.0}},

  // ── Section 5: NCB (No Claim Bonus) Details ──
  "ncbPercentage": {{"value": "0%/20%/25%/35%/45%/50%", "source_page": null, "confidence": 0.0}},
  "ncbProtection": {{"value": true, "source_page": null, "confidence": 0.0}},
  "ncbDeclaration": {{"value": "Declaration text", "source_page": null, "confidence": 0.0}},
  "claimFreeYears": {{"value": 0, "source_page": null, "confidence": 0.0}},

  // ── Section 6: Add-on Covers ──
  "zeroDepreciation": {{"value": true, "source_page": null, "confidence": 0.0}},
  "engineProtection": {{"value": true, "source_page": null, "confidence": 0.0}},
  "returnToInvoice": {{"value": false, "source_page": null, "confidence": 0.0}},
  "roadsideAssistance": {{"value": true, "source_page": null, "confidence": 0.0}},
  "consumables": {{"value": true, "source_page": null, "confidence": 0.0}},
  "tyreCover": {{"value": false, "source_page": null, "confidence": 0.0}},
  "keyCover": {{"value": false, "source_page": null, "confidence": 0.0}},
  "ncbProtect": {{"value": true, "source_page": null, "confidence": 0.0}},
  "emiBreakerCover": {{"value": false, "source_page": null, "confidence": 0.0}},
  "passengerCover": {{"value": true, "source_page": null, "confidence": 0.0}},
  "passengerCoverAmount": {{"value": 100000, "source_page": null, "confidence": 0.0}},
  "personalBaggage": {{"value": false, "source_page": null, "confidence": 0.0}},
  "outstationEmergency": {{"value": false, "source_page": null, "confidence": 0.0}},
  "dailyAllowance": {{"value": false, "source_page": null, "confidence": 0.0}},
  "windshieldCover": {{"value": false, "source_page": null, "confidence": 0.0}},
  "electricVehicleCover": {{"value": false, "source_page": null, "confidence": 0.0}},
  "batteryProtect": {{"value": false, "source_page": null, "confidence": 0.0}},
  "legalLiabilityPaidDriver": {{"value": true, "source_page": null, "confidence": 0.0}},
  "legalLiabilityEmployees": {{"value": false, "source_page": null, "confidence": 0.0}},
  "paNamedPersons": {{"value": false, "source_page": null, "confidence": 0.0}},

  // ── Section 7: Premium Breakdown ──
  "basicOdPremium": {{"value": 0, "source_page": null, "confidence": 0.0}},
  "ncbDiscount": {{"value": 0, "source_page": null, "confidence": 0.0}},
  "voluntaryDeductibleDiscount": {{"value": 0, "source_page": null, "confidence": 0.0}},
  "antiTheftDiscount": {{"value": 0, "source_page": null, "confidence": 0.0}},
  "aaiMembershipDiscount": {{"value": 0, "source_page": null, "confidence": 0.0}},
  "electricalAccessoriesPremium": {{"value": 0, "source_page": null, "confidence": 0.0}},
  "nonElectricalAccessoriesPremium": {{"value": 0, "source_page": null, "confidence": 0.0}},
  "cngLpgKitPremium": {{"value": 0, "source_page": null, "confidence": 0.0}},
  "addOnPremium": {{"value": 0, "source_page": null, "confidence": 0.0}},
  "loading": {{"value": 0, "source_page": null, "confidence": 0.0}},
  "netOdPremium": {{"value": 0, "source_page": null, "confidence": 0.0}},
  "basicTpPremium": {{"value": "Basic TP liability premium (NOT PA/CPA). For Standalone OD, set to 0.", "source_page": null, "confidence": 0.0}},
  "paOwnerDriverPremium": {{"value": "Compulsory PA Owner-Driver premium (CPA). This is NOT TP premium — it's a separate statutory PA cover.", "source_page": null, "confidence": 0.0}},
  "paPassengersPremium": {{"value": 0, "source_page": null, "confidence": 0.0}},
  "paPaidDriverPremium": {{"value": 0, "source_page": null, "confidence": 0.0}},
  "llPaidDriverPremium": {{"value": 0, "source_page": null, "confidence": 0.0}},
  "netTpPremium": {{"value": 0, "source_page": null, "confidence": 0.0}},
  "grossPremium": {{"value": 0, "source_page": null, "confidence": 0.0}},
  "gst": {{"value": 0, "source_page": null, "confidence": 0.0}},
  "totalPremium": {{"value": 0, "source_page": null, "confidence": 0.0}},

  // ── Section 8: Exclusions ──
  "electricalAccessoriesExclusion": {{"value": "Electrical accessories exclusion details", "source_page": null, "confidence": 0.0}},
  "nonElectricalAccessoriesExclusion": {{"value": "Non-electrical accessories exclusion details", "source_page": null, "confidence": 0.0}},
  "biofuelKitExclusion": {{"value": "Bi-fuel/CNG/LPG kit exclusion details", "source_page": null, "confidence": 0.0}},
  "otherExclusions": {{"value": ["exclusion1", "exclusion2"], "source_page": null, "confidence": 0.0}}
}}

CRITICAL INSTRUCTIONS:
1. Search the ENTIRE document for each field. Look in the policy schedule, certificate of insurance, premium breakup tables, endorsements, and terms & conditions sections.
2. Extract exact values as written. Do not paraphrase or summarize numeric values.
3. For IDV, search: "IDV", "Insured's Declared Value", "Insured Declared Value", "Sum Insured (Vehicle)".
4. For NCB, search: "NCB", "No Claim Bonus", "No Claims Bonus", "Claim Free", "NCB %", "NCB Discount".
5. For add-on covers, search: "Add-on", "Add On", "Addon", "Zero Dep", "Nil Depreciation", "Bumper to Bumper", "Engine Protect", "RSA", "Roadside", "Return to Invoice", "RTI", "Consumable", "Tyre", "Key Replacement", "EMI", "Passenger", "Baggage", "Windshield", "EV Cover", "Battery".
6. For Own Damage section, search: "OD", "Own Damage", "Section I", "OD Premium", "Basic OD".
7. For Third Party section, search: "TP", "Third Party", "Section II", "TP Premium", "Act Liability", "Third-Party".
8. For PA cover, search: "PA", "Personal Accident", "PA Owner", "PA Driver", "PA Passenger", "CPA", "Compulsory PA".
9. For deductible, search: "Deductible", "Compulsory Deductible", "Voluntary Deductible", "Excess".
10. For vehicle details, search: "Registration", "Reg. No", "Make", "Model", "Engine No", "Chassis No", "CC", "Cubic Capacity", "Fuel", "Seating", "RTO", "Hypothecation", "Financier".
11. For premium breakdown, search: "Premium Summary", "Premium Breakup", "Premium Details", "Net Premium", "Gross Premium", "GST", "IGST", "CGST", "SGST", "Loading", "Discount".
11a. For claimEmail, look specifically for "Claims Registration", "Register Claim", "claim email", "general.claims@", "claims@", "motor.claims@". Do NOT use generic support emails like "customersupport@" or "customer.care@". Indian insurers list claims email separately near the claims process section or at the bottom of the first page.
12. For product type, determine: "Comprehensive" (both OD + TP), "Third Party Only" (TP only, no OD), "Standalone OD" (OD only, no TP). Check if both OD and TP sections exist.
12a. CRITICAL — tpPremium vs paOwnerDriverPremium distinction:
  - tpPremium = Third-party LIABILITY premium (covers injury/death to others, property damage). Keywords: "Act Liability", "TP Premium", "Third Party", "Section II liability".
  - paOwnerDriverPremium = Compulsory Personal Accident cover for the owner-driver (CPA). Keywords: "PA Cover", "CPA", "Personal Accident", "PA Owner-Driver".
  - For "Standalone OD" policies: tpPremium MUST be 0 (no TP liability in standalone OD). Any CPA/PA premium (often ₹399-₹750) goes ONLY in paOwnerDriverPremium, NOT in tpPremium.
  - For "Comprehensive" policies: Both tpPremium and paOwnerDriverPremium may exist separately.
13. CRITICAL — PAN and Email entity disambiguation:
  - ownerPan: Indian PAN format is AAAPL1234C. The 4th character indicates entity type: P=Person, C=Company, F=Firm, H=HUF, A=AOP, T=Trust. ONLY extract a PAN with 4th letter 'P' as ownerPan. If you see a PAN like "AABCF0191R" (4th letter F=Firm), that belongs to the INSURER or COMPANY, not the policyholder. Set ownerPan to null if no personal PAN is found.
  - ownerEmail/ownerContact: Insurance documents contain multiple emails and phone numbers belonging to different entities (insurer, intermediary/broker/agent, policyholder). ONLY extract contact details that appear under "Insured"/"Policyholder"/"Owner" labels. Do NOT extract contacts appearing under "Intermediary"/"Broker"/"Agent"/"Consultant"/"Producer"/"Channel Partner" sections.
14. Use [Page N] markers to fill source_page accurately.
15. Set confidence 1.0 for exact matches, 0.7-0.9 for inferred values, <0.5 for uncertain.
16. If field not found after thorough search, set value to null and confidence to 0.0.
17. Return ONLY valid JSON without any markdown or explanation."""
