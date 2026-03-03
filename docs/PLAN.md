# Plan: Check 5 — PDF Text Verification

## Goal
Add an automated verification step that compares extracted field values against the raw PDF text to catch LLM hallucinations and extraction errors. Pure Python text matching — NO additional LLM calls.

## Files to Create/Modify

### 1. CREATE: `botproject/policy_analysis/validation/pdf_text_verifier.py`
New module with:
- **Normalization helpers**: numbers (Indian comma `5,00,000`, `₹`, Lakh/Crore), dates (8+ format variants), strings, policy numbers
- **Pre-extraction**: Scan PDF text once, extract all numbers into a sorted list for O(1)-per-field lookup
- **Per-type field maps**: Which fields to verify and how (exact_string / numeric / date / percentage / name_string) for each of the 5 policy types
- **Core function**: `verify_against_pdf_text(v2_raw_extraction, extracted_text, category)` → returns pass/fail + mismatches list

### 2. EDIT: `botproject/policy_analysis/validation/__init__.py` (line 1-4)
Add export for `verify_against_pdf_text`

### 3. EDIT: `botproject/routers/policy_upload.py` (4 edits)
- **Import** (line 66): Add `from policy_analysis.validation.pdf_text_verifier import verify_against_pdf_text`
- **Init** (line ~1131): Add `pdf_text_verification = {}`
- **Save pre-enrichment text** (line ~1093): Store `_original_pdf_text = extracted_text` before UIN enrichment appends web data
- **Call** (line ~1308): `pdf_text_verification = verify_against_pdf_text(v2_raw_extraction, _original_pdf_text, v2_category)`
- **MongoDB response** (line ~5499): Add `"pdfTextVerification": pdf_text_verification if pdf_text_verification else None,`
- **API response** (line ~6096): Add `"pdfTextVerification": pdf_text_verification if pdf_text_verification else None,`

## Verification Logic

### Verifiable Fields (per type)
| Field | Health | Motor | Life | PA | Travel | Match Type |
|-------|--------|-------|------|----|--------|------------|
| policyNumber | ✓ | ✓ | ✓ | ✓ | ✓ | exact_string |
| uin | ✓ | ✓ | ✓ | ✓ | ✓ | exact_string |
| insurerName | ✓ | ✓ | ✓ | ✓ | ✓ | name_string |
| sumInsured/idv/sumAssured | ✓ | ✓ | ✓ | ✓ | — | numeric |
| totalPremium | ✓ | ✓ | ✓ | ✓ | ✓ | numeric |
| policyPeriodStart/End | ✓ | ✓ | ✓ | ✓ | ✓ | date |
| ncbPercentage/copay | ✓ | ✓ | — | — | — | percentage |
| registrationNumber | — | ✓ | — | — | — | exact_string |
| engineNumber/chassisNumber | — | ✓ | — | — | — | exact_string |
| pre/postHospitalization | ✓ | — | — | — | — | exact_string |

### Skipped Fields (interpretive/computed)
keyBenefits, exclusions, claimSettlementRatio, networkHospitalsCount, all boolean addon flags, all computed scores/verdicts

### Normalization Rules
1. **Numbers**: Strip `₹ Rs. INR ,` → compare as float (0.5% tolerance). Also parse `5 Lakh` → 500000, `1 Crore` → 10000000
2. **Dates**: Parse to datetime, generate 8+ text representations (`DD/MM/YYYY`, `DD-Mon-YYYY`, `DD Month YYYY`, etc.)
3. **Strings**: Case-insensitive, collapse whitespace
4. **Policy numbers**: Strip all non-alphanumeric chars before compare
5. **Names**: Split into words, check all words exist individually in PDF text

## Output Structure
```json
{
  "passed": true,
  "fieldsVerified": 18,
  "fieldsMatched": 16,
  "fieldsMismatched": 2,
  "fieldsSkipped": 45,
  "mismatches": [
    {
      "field": "postHospitalization",
      "extractedValue": "120 days",
      "matchType": "exact_string",
      "severity": "important",
      "message": "Extracted '120 days' but not found in PDF text"
    }
  ],
  "verifiedFields": ["policyNumber", "sumInsured", "totalPremium", ...]
}
```

## Design Principles
- **No LLM calls** — pure Python regex/string matching, <100ms
- **Lean toward leniency** — better to miss a mismatch than flag a false positive
- **"passed" = no CRITICAL mismatches** — important/standard mismatches are warnings only
