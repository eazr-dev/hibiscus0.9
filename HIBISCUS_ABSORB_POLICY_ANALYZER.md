# HIBISCUS — ABSORB POLICY ANALYSIS ENGINE

Read `CLAUDE.md` and `HIBISCUS_BUILD_BLUEPRINT_v5_SERIES_A.md` before proceeding.

---

## WHAT THIS IS

PolicyAnalyzer currently calls botproject via HTTP for extraction, scoring, and analysis. This makes Hibiscus dependent on botproject for its most critical function. We're absorbing the entire policy analysis pipeline into Hibiscus so it owns the intelligence end-to-end.

**Before:** User uploads PDF → Hibiscus → HTTP call to botproject → extraction → HTTP call to botproject → scoring → HTTP response → Hibiscus synthesizes

**After:** User uploads PDF → Hibiscus → native extraction (DeepSeek) → native scoring → native validation → native gap analysis → grounded response. Zero HTTP dependency for analysis.

botproject still handles: auth, KYC, payments, IPF/SVF loan lifecycle, CRUD, document storage (S3). Hibiscus now handles: ALL intelligence — extraction, scoring, validation, analysis, reporting.

---

## STEP 1: READ THE EXISTING BOTPROJECT EXTRACTION CODE

Before writing any new code, understand what exists. Read these files completely:

```bash
# Find all extraction-related files
find botproject/ -type f -name "*.py" | xargs grep -l "extract" | head -20
find botproject/ -type f -name "*.py" | xargs grep -l "score\|scoring\|protection" | head -20
find botproject/ -type f -name "*.py" | xargs grep -l "report\|generate_report" | head -20
find botproject/ -type f -name "*.py" | xargs grep -l "validate\|validation" | head -20
find botproject/ -type f -name "*.py" | xargs grep -l "zone\|classification\|classify" | head -20

# Find extraction prompts
find botproject/ -type f \( -name "*.txt" -o -name "*.md" -o -name "*.py" \) | xargs grep -l "system.*prompt\|SYSTEM_PROMPT\|extraction_prompt" | head -20

# Find JSON schemas for extraction output
find botproject/ -type f -name "*.py" | xargs grep -l "json_schema\|extraction_schema\|BaseModel" | head -20
```

Read every file found above. Understand:
1. How does botproject receive a PDF? (upload endpoint, S3 storage, OCR pipeline)
2. What LLM does it call for extraction? (model, prompt, JSON schema)
3. How does it validate extracted data? (5-check validation)
4. How does it calculate protection scores? (scoring algorithm, 141K lines reference)
5. How does it classify policy types? (zone classification)
6. How does it generate reports? (template engine, per-category logic)
7. What are the per-category extraction schemas? (health, life, motor, travel, PA)

---

## STEP 1b: AUDIT BOTPROJECT DATA vs HIBISCUS KG

After reading botproject's code, identify ALL reference data it uses for extraction, validation, scoring, and analysis. Then compare with what Hibiscus already has in Neo4j KG, Qdrant RAG, and formula files.

```bash
# Find all hardcoded data, lookup tables, reference datasets in botproject
grep -rn "BENCHMARK\|benchmark\|GSV\|gsv_factor\|depreciation\|exclusion\|zone\|city_tier" botproject/ --include="*.py" | head -50
grep -rn "INSURER\|insurer_data\|product_data\|PRODUCT" botproject/ --include="*.py" | head -50
grep -rn "room_rent\|copay_range\|premium_range\|sum_insured_range" botproject/ --include="*.py" | head -50

# Find JSON/CSV data files
find botproject/ -type f \( -name "*.json" -o -name "*.csv" -o -name "*.yaml" \) | head -20

# Find MongoDB collection references
grep -rn "collection\|find_one\|find_many\|aggregate" botproject/ --include="*.py" | head -30
```

For each data source found, check if it exists in Hibiscus:

| Data | In botproject | In Hibiscus KG/RAG | Action |
|---|---|---|---|
| Insurer profiles | MongoDB `insurers` collection? | Neo4j 52 Insurer nodes | Compare field coverage. If botproject has fields KG doesn't, add to KG seed. |
| Product database | MongoDB `products` collection? | Neo4j 200 Product nodes | Same — compare and fill gaps. |
| Benchmarks | Hardcoded or MongoDB? | Neo4j 776 Benchmark nodes | Verify ranges match. |
| GSV tables | Hardcoded in scoring? | `knowledge/formulas/surrender_value.py` | Verify tables are identical. |
| IRDAI exclusion lists | In prompts or data files? | RAG corpus | Verify all 4 IRDAI exclusion lists are in RAG. If not, add. |
| Depreciation tables (motor) | Hardcoded? | Check `knowledge/formulas/` | If missing, create `hibiscus/knowledge/formulas/depreciation.py`. |
| Room rent benchmarks | In analysis logic? | Check KG benchmarks | If missing, add room rent benchmarks by city tier to KG. |
| Zone/city tier mapping | In classification service? | Check KG or utils | If missing, create `hibiscus/utils/city_tiers.py`. |

**Action for each gap:** Create the data in Hibiscus. Either:
- Add to Neo4j KG seed files (if it's entity/relationship data)
- Add to Qdrant RAG corpus (if it's regulatory/reference text)
- Add to `knowledge/formulas/` (if it's calculation tables)
- Add to `utils/` (if it's classification/mapping logic)

**Do NOT leave any data dependency on botproject.** After this step, Hibiscus must have ALL reference data needed for extraction, validation, scoring, and gap analysis — independent of botproject.

---

## STEP 2: READ THE v7.0 EXTRACTION SPECIFICATIONS

These are the production-grade extraction specs that define what Hibiscus should extract per policy type. They exist in the repository or were previously generated. Check:

```bash
find . -name "*v7*" -o -name "*extraction*spec*" -o -name "*master_framework*" | head -20
find . -name "*canon*" | head -20
```

If the v7.0 specs are not in the repo, the specifications define:

**Per policy category (Health, Life, Motor, Travel, PA):**
- System prompt for the LLM extraction call
- Complete JSON extraction schema with all fields
- Validation rules and confidence scoring
- Source mapping (page/clause references for every extracted field)
- Analysis engine rules (gap detection, adequacy assessment, worst-case scenarios)
- 4 extraction tiers: INSTANT (<2s), STANDARD (<8s), DEEP (<15s), EXPERT (<30s)

**Key extraction rules that MUST be preserved:**
1. Every extracted value includes source reference (page/clause)
2. Missing fields marked `[NOT FOUND IN DOCUMENT]` — never hallucinated
3. Ambiguous values flag confidence level
4. Currency in Indian format (₹, lakhs/crores)
5. Dates in DD-MMM-YYYY format

---

## STEP 3: BUILD THE NATIVE EXTRACTION PIPELINE

Create these files inside `hibiscus/`:

### 3a. Document Processor

`hibiscus/extraction/__init__.py`
`hibiscus/extraction/processor.py`

```python
"""
Document Processor — handles PDF intake, OCR, text extraction.

Input: PDF file (bytes or S3 path)
Output: Extracted text with page markers

Pipeline:
1. PDF → text extraction (PyPDF2 / pdfplumber for digital PDFs)
2. If text extraction fails or is sparse → OCR fallback (Tesseract or cloud OCR)
3. Page boundary markers preserved: [PAGE 1], [PAGE 2], etc.
4. Clean extracted text (remove headers/footers, fix encoding issues)
5. Return: {pages: [{page_num, text}], total_pages, extraction_method: "digital"|"ocr"}
"""
```

### 3b. Policy Classifier

`hibiscus/extraction/classifier.py`

```python
"""
Policy Type Classifier — determines category before extraction.

Input: First 2-3 pages of extracted text
Output: {category: "health"|"life"|"motor"|"travel"|"pa", confidence: 0.0-1.0, signals: [...]}

Method:
1. Keyword-based classification first (fast, deterministic):
   - health: "mediclaim", "hospitalization", "sum insured", "copay", "room rent"
   - life: "sum assured", "maturity benefit", "death benefit", "nominee", "surrender"
   - motor: "IDV", "insured vehicle", "own damage", "third party", "NCB"
   - travel: "passport", "destination", "trip", "evacuation", "visa"
   - pa: "accidental death", "permanent disability", "temporary disability"

2. If ambiguous (confidence < 0.8) → LLM classification (DeepSeek V3.2, 100 tokens max)

3. Sub-type classification:
   - health: individual | floater | senior | critical_illness | top_up
   - life: term | endowment | ulip | whole_life | money_back | pension
   - motor: car_comprehensive | car_tp | two_wheeler | commercial
   - travel: single_trip | multi_trip | student
   - pa: individual | group
"""
```

### 3c. Per-Category Extractors

`hibiscus/extraction/extractors/__init__.py`
`hibiscus/extraction/extractors/health.py`
`hibiscus/extraction/extractors/life.py`
`hibiscus/extraction/extractors/motor.py`
`hibiscus/extraction/extractors/travel.py`
`hibiscus/extraction/extractors/pa.py`

Each extractor follows the same pattern:

```python
"""
Category-specific extraction using LLM.

Input: Full document text with page markers + sub-type classification
Output: Structured JSON matching the v7.0 schema for this category

Implementation:
1. Load category-specific system prompt from hibiscus/extraction/prompts/{category}.txt
2. Construct extraction prompt with document text
3. Call DeepSeek V3.2 with JSON mode
4. Parse response into Pydantic model
5. Run category-specific validation
6. Calculate confidence per field
7. Return structured extraction with source_map (page references)

The system prompt defines:
- What fields to extract (complete JSON schema)
- How to handle missing fields
- How to calculate derived fields
- Category-specific rules (e.g., room rent calculations for health, GSV tables for life)
"""
```

### 3d. Extraction Prompts

`hibiscus/extraction/prompts/health.txt`
`hibiscus/extraction/prompts/life.txt`
`hibiscus/extraction/prompts/motor.txt`
`hibiscus/extraction/prompts/travel.txt`
`hibiscus/extraction/prompts/pa.txt`

These are the system prompts for each category's LLM extraction call. They should be derived from:
1. The existing botproject extraction prompts (read from `botproject/prompts/`)
2. The v7.0 extraction specifications (comprehensive field schemas)

Each prompt must include:
- Role definition ("You are EAZR's {Category} Insurance Policy Extraction Engine")
- Critical rules (extract only what's stated, never hallucinate, page references required)
- Complete JSON schema for output
- Extraction examples
- Error handling instructions

### 3e. Extraction Schemas (Pydantic)

`hibiscus/extraction/schemas/__init__.py`
`hibiscus/extraction/schemas/health.py`
`hibiscus/extraction/schemas/life.py`
`hibiscus/extraction/schemas/motor.py`
`hibiscus/extraction/schemas/travel.py`
`hibiscus/extraction/schemas/pa.py`
`hibiscus/extraction/schemas/common.py`

Pydantic models matching the v7.0 JSON schemas. Every field has:
```python
class ExtractedField(BaseModel):
    value: Any
    confidence: float  # 0.0-1.0
    source_page: Optional[int]
    source_clause: Optional[str]
    extraction_note: Optional[str]
```

### 3f. Validation Engine

`hibiscus/extraction/validation.py`

```python
"""
5-Check Validation (from existing botproject logic):

1. Completeness: Are all critical fields extracted?
   - health critical: insurer, policy_number, sum_insured, premium, copay, room_rent_limit
   - life critical: insurer, policy_number, sum_assured, premium, policy_type, maturity_date
   - motor critical: insurer, vehicle_number, IDV, premium, NCB, policy_type
   - etc.

2. Consistency: Do extracted values make logical sense?
   - start_date < end_date
   - premium proportional to sum insured (within category benchmarks from KG)
   - age within product eligibility range
   - copay percentage between 0-100%

3. Format: Are values in correct format?
   - Currency with ₹ symbol
   - Dates in DD-MMM-YYYY
   - Percentages as numbers 0-100

4. Range: Are values within reasonable ranges?
   - Health premium: ₹3,000 - ₹5,00,000 per year
   - Health sum insured: ₹1,00,000 - ₹5,00,00,000
   - Life premium: ₹1,000 - ₹50,00,000 per year
   - Motor IDV: ₹10,000 - ₹1,00,00,000
   (Use KG benchmarks for category-specific ranges)

5. Cross-reference: Do values match KG data?
   - Insurer name exists in KG (fuzzy match)
   - Product name matches known products (if identifiable)
   - Premium range matches KG benchmarks for this category/age/sum insured

Output: {
    valid: bool,
    score: 0-100,
    confidence: HIGH|MEDIUM|LOW,
    errors: [...],
    warnings: [...],
    field_scores: {field_name: {score, issues}}
}
"""
```

### 3g. Scoring Engine

`hibiscus/extraction/scoring.py`

```python
"""
EAZR Protection Score Calculator.

Absorbs the scoring logic from botproject (the 141K line reference).

Input: Validated extraction data + user profile (if available)
Output: EAZR Score 0-100 with component breakdown

Components (weighted by category):

HEALTH:
- Coverage adequacy (30%): sum_insured vs metro benchmark for age/family
- Sub-limit quality (25%): room rent, copay, disease-wise limits
- Insurer quality (20%): CSR, solvency, claim settlement time (from KG)
- Feature richness (15%): restoration, no-claim bonus, day care, domiciliary
- Value for money (10%): premium vs benchmark for equivalent coverage

LIFE:
- Coverage adequacy (35%): sum_assured vs 10-15x income
- Policy value (25%): IRR, surrender value trajectory, bonus rates
- Insurer quality (20%): CSR, solvency, complaint ratio (from KG)
- Rider coverage (10%): ADB, CI, WOP presence
- Flexibility (10%): premium payment options, partial withdrawal, loan

MOTOR:
- IDV adequacy (30%): current IDV vs market value
- Coverage completeness (25%): add-ons, zero depreciation, RSA
- Insurer quality (20%): CSR, cashless garage network
- Premium value (15%): premium vs benchmark for vehicle type/age
- Claims process (10%): cashless ratio, avg settlement time

Use KG benchmarks for all comparisons. If KG doesn't have the data, score that component as "insufficient data" rather than guessing.
"""
```

### 3h. Gap Analysis Engine

`hibiscus/extraction/gap_analysis.py`

```python
"""
Coverage Gap Detection.

Input: Extraction data + scoring data + user profile + KG benchmarks
Output: Identified gaps with severity and recommendations

Gap Types:
- COVERAGE_GAP: Sum insured inadequate for profile
- SUB_LIMIT_TRAP: Room rent or disease limits that reduce effective coverage
- MISSING_COVERAGE: No health/term/PA when needed
- OVERLAP: Duplicate coverage across policies
- INFLATION_EROSION: Fixed sum insured losing value over time
- RIDER_GAP: Missing critical riders (CI, ADB, WOP)
- PREMIUM_BURDEN: Premium too high relative to income

Each gap includes:
- severity: LOW | MEDIUM | HIGH | CRITICAL
- description: plain language explanation
- impact: quantified financial impact where possible
- recommendation: specific action (with EAZR product tie-in where relevant)
- source: KG benchmark or formula that identified the gap
"""
```

---

## STEP 4: REWIRE POLICYANALYZER AGENT

Update `hibiscus/agents/policy_analyzer.py`:

**Before:** Calls `extract_policy()` HTTP tool → gets data → calls `calculate_score()` HTTP tool → synthesizes

**After:**
```python
async def execute(self, state):
    # 1. Get document (from upload or S3)
    document = await get_document(state)
    
    # 2. Process PDF → text with page markers (native)
    processed = await document_processor.process(document)
    
    # 3. Classify policy type (native)
    classification = await policy_classifier.classify(processed)
    
    # 4. Extract structured data (native LLM call to DeepSeek)
    extraction = await get_extractor(classification.category).extract(processed, classification)
    
    # 5. Validate extraction (native)
    validation = await validation_engine.validate(extraction, classification.category)
    
    # 6. Score (native, using KG benchmarks)
    score = await scoring_engine.score(extraction, classification.category, state.get("user_profile"))
    
    # 7. Gap analysis (native, using KG benchmarks)
    gaps = await gap_analysis_engine.analyze(extraction, score, state.get("user_profile"))
    
    # 8. Synthesize response using all native data
    # Now the agent has FULL control over every data point
    # Every number traces to extraction (with page ref) or KG (with source)
    # Confidence scoring is granular per field, not a single HTTP response confidence
```

---

## STEP 5: UPDATE TOOLS AND DEPENDENCIES

### 5a. Keep botproject HTTP tools as FALLBACK

Don't remove the existing HTTP tool wrappers. Keep them as fallback:
```python
# If native extraction fails (e.g., PDF processing error), fall back to botproject
try:
    extraction = await native_extract(document)
except ExtractionError:
    logger.warning("Native extraction failed, falling back to botproject")
    extraction = await eazr_client.extract_policy(document)
```

### 5b. Update document memory storage

After native extraction, store the full extraction result in document memory (MongoDB):
```python
await document_memory.store({
    "user_id": state["user_id"],
    "session_id": state["session_id"],
    "extraction": extraction.dict(),
    "classification": classification.dict(),
    "score": score.dict(),
    "gaps": gaps,
    "validation": validation.dict(),
    "timestamp": datetime.utcnow()
})
```

### 5c. Update auto-KG enrichment

The Phase 4 KG enrichment service should now read from native extraction output (higher quality, more fields) rather than botproject's HTTP response.

---

## STEP 6: ADD PDF PROCESSING DEPENDENCIES

Update `hibiscus/pyproject.toml`:
```toml
# PDF processing
pdfplumber = ">=0.10.0"
PyPDF2 = ">=3.0.0"
pytesseract = ">=0.3.10"  # OCR fallback
Pillow = ">=10.0.0"       # Image processing for OCR
```

Update `hibiscus/Dockerfile`:
```dockerfile
# Add Tesseract for OCR fallback
RUN apt-get update && apt-get install -y tesseract-ocr && rm -rf /var/lib/apt/lists/*
```

---

## STEP 7: TEST THE NATIVE PIPELINE

### Unit Tests

`hibiscus/tests/unit/test_classifier.py` — policy type classification accuracy
`hibiscus/tests/unit/test_extraction_health.py` — health extraction schema compliance
`hibiscus/tests/unit/test_extraction_life.py` — life extraction schema compliance
`hibiscus/tests/unit/test_validation.py` — validation catches bad data
`hibiscus/tests/unit/test_scoring.py` — score calculation correctness

### Integration Test

```
1. Take a real health policy PDF
2. Process through native pipeline: processor → classifier → extractor → validator → scorer → gap analyzer
3. Compare output with botproject's extraction for the same document
4. Verify: field completeness >= botproject, validation stricter, scoring includes KG benchmarks
5. Verify: every extracted number has page reference
6. Verify: zero hallucinated values
```

### Regression Test

```
1. Run HibiscusBench (120 cases) with native extraction
2. DQ must be >= 0.84 (no regression from Phase 3/4)
3. PolicyAnalyzer-specific cases must improve (more grounded, more detailed)
```

---

## RULES

- **DO NOT modify botproject.** Read its code to understand logic, but build fresh in hibiscus/extraction/.
- **Keep botproject HTTP tools as fallback** — graceful degradation if native extraction fails.
- **Every extracted value must have a page reference.** This is non-negotiable.
- **Never hallucinate numbers.** If extraction doesn't find copay, say "not found" — don't invent 10%.
- **Use DeepSeek V3.2 for extraction.** It's the primary model. JSON mode for structured output.
- **Use KG benchmarks in scoring and validation.** This is what makes native scoring better than botproject's — it has access to the full Knowledge Graph.
- **Test with real PDFs.** Not synthetic test data. Real Star Health, HDFC Ergo, LIC documents.

---

## VERIFICATION

After building, confirm:

```
- [ ] PDF processed natively (no HTTP call to botproject for extraction)
- [ ] Classification correct for health, life, motor, travel, PA documents
- [ ] Extraction output matches or exceeds botproject quality
- [ ] Every number has page reference
- [ ] Validation catches: missing fields, impossible values, format errors
- [ ] EAZR Score calculated using KG benchmarks
- [ ] Gap analysis identifies real gaps with severity and recommendations
- [ ] Fallback to botproject works if native extraction fails
- [ ] Document memory stores full extraction result
- [ ] HibiscusBench DQ >= 0.84
- [ ] "What did I upload?" returns data from native extraction
- [ ] Follow-up "What's not covered?" references actual extracted exclusions
```
