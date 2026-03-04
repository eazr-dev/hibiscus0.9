# HIBISCUS — KNOWLEDGE ENRICHMENT SPRINT
# Research-Backed Intelligence Upgrade

Read `CLAUDE.md` and `HIBISCUS_BUILD_BLUEPRINT_v5_SERIES_A.md` before proceeding. CLAUDE.md is the project memory. The blueprint is the authoritative spec — everything must align to it.

---

## WHAT THIS IS

Hibiscus's decision quality depends on the DATA behind the agents — not just the code. Right now the KG has 1,207 products and 760 benchmarks, but much of it is synthetic or approximate. The agent prompts use generic instructions. The RAG corpus is thin (40 IRDAI circulars of 200+ needed). This sprint enriches EVERY knowledge layer with real, verified, current data so that Hibiscus gives answers a seasoned insurance advisor would give — not a chatbot guessing from training data.

**Goal:** After this sprint, when a user asks "Is Star Health Comprehensive worth it for a 35-year-old in Mumbai?", Hibiscus should answer with: exact current premium (₹14,500 for ₹10L SI), real CSR (98.14% FY24-25), actual room rent limits (single AC room), real network hospital count (14,000+), actual waiting periods (36 months PED, 30 days initial), and benchmark comparison ("15% cheaper than HDFC Optima for same coverage, but 10% copay above 60 applies"). Not vague generalities.

---

## PART 1: AGENT PROMPT ENRICHMENT

Every agent prompt needs to be upgraded from "generic instruction" to "domain expert knowledge embedded in the prompt."

### 1a. PolicyAnalyzer — The Most Critical Prompt

File: `hibiscus/extraction/prompts/health.txt` (and life, motor, travel, pa)

**Research and add to each extraction prompt:**

HEALTH extraction prompt — add these as embedded knowledge:
- IRDAI standardized exclusion List I (16 permanent exclusions) — full list with exact names
- IRDAI standardized exclusion List II (17 time-bound exclusions with standard waiting periods)
- IRDAI standardized exclusion List III (2-year waiting period diseases)
- IRDAI standardized exclusion List IV (specific conditions with waiting periods)
- Standard room categories: General Ward, Semi-Private, Private, Single AC, Deluxe, Suite
- Typical room rent ranges by city tier: Metro ₹3,000-15,000/day, Tier 2 ₹2,000-8,000/day, Tier 3 ₹1,000-5,000/day
- Common sub-limit patterns: ambulance (₹2,000-5,000), cataract (₹40,000-80,000), maternity (₹25,000-75,000)
- Moratorium period rules: 8 years (old policies pre-2020), 5 years (IRDAI 2024 guideline for new policies)
- Free look period: 15 days (offline), 30 days (online purchase)
- Portability rules: can port without losing PED credit, 45-60 days before renewal

LIFE extraction prompt — add:
- GSV factor table by year (Year 1: 0%, Year 2: 30%, Year 3+: varies by policy term)
- Section 45 contestability: 3 years (IRDAI 2024 — reduced from 5 years for older policies)
- Common ULIP charge structures: Premium allocation (2-5%), Fund management (1.35% max per IRDAI), Policy admin (₹250-500/month), Mortality charges (age-based)
- Bonus rates by insurer: LIC (₹40-50/1000 SA), HDFC (₹30-45/1000 SA), SBI (₹35-48/1000 SA)
- Tax implications: 80C (₹1.5L limit, premium ≤10% of SA for tax-free maturity), 80D (health), 10(10D) (maturity exemption if annual premium ≤ ₹5L post-2023)

MOTOR extraction prompt — add:
- IRDAI depreciation schedule: rubber/nylon/plastic parts (50%), fiber glass (30%), windshield glass (0% for first claim), metal body (0-15% by age)
- Standard IDV depreciation by vehicle age: <6 months (5%), 6-12 months (15%), 1-2 years (20%), 2-3 years (30%), 3-4 years (40%), 4-5 years (50%), >5 years (by mutual agreement)
- CPA cover: mandatory ₹15L for private cars, ₹15L for two-wheelers
- NCB slabs: 20% (1 year), 25% (2), 35% (3), 45% (4), 50% (5+ years)
- Third party premium: set by IRDAI, varies by engine capacity
- Zero depreciation add-on: typically adds 15-20% to premium

TRAVEL extraction prompt — add:
- Schengen requirement: minimum €30,000 medical coverage mandatory
- Common coverage categories: medical emergency, trip cancellation, baggage loss/delay, passport loss, personal liability, adventure sports
- Typical coverage amounts: medical $50,000-500,000, trip cancellation $1,000-10,000, baggage $500-3,000
- Pre-existing condition handling: most policies exclude, some cover with 50% copay after 12 months

PA extraction prompt — add:
- PMSBY premium: ₹20/year (government scheme), coverage ₹2L accidental death, ₹1L partial disability
- Standard disability scale: total permanent (100%), loss of two limbs (100%), loss of one limb (50%), loss of sight one eye (50%), loss of hearing both ears (50%)
- Occupation class impact: Class 1 (office/desk) lowest premium, Class 3 (manual labor) highest
- Cumulative bonus: 5-10% per claim-free year in some policies

### 1b. Agent System Prompts

Each agent should have domain expertise embedded, not just task instructions.

File: `hibiscus/llm/prompts/agents/` — update all 12 agent prompts

**Recommender prompt — add:**
- Current top 5 health plans with why: Niva Bupa ReAssure 2.0 (no room rent limit), Care Supreme (high CSR 97.5%), Star Comprehensive (14,000+ network hospitals), HDFC Optima Secure (global coverage), Aditya Birla Activ Health (wellness rewards)
- Premium benchmarks: 30yo individual ₹10L SI → ₹8,000-15,000/year depending on insurer and zone
- Family floater benchmarks: 30yo couple + 1 child ₹15L SI → ₹15,000-30,000/year
- Senior citizen benchmarks: 60yo individual ₹10L SI → ₹30,000-60,000/year
- Life term benchmarks: 30yo male ₹1Cr SI → ₹8,000-15,000/year
- When to recommend what: age <35 → term + health + PA. Age 35-50 → term + health + CI rider. Age 50+ → health + super top-up + PA

**SurrenderCalculator prompt — add:**
- LIC endowment typical IRR: 4-5.5% (vs FD 7%, PPF 7.1%, Nifty 50 12% CAGR)
- LIC money back typical IRR: 3.5-5%
- ULIP typical returns (post charges): equity fund 8-12%, debt fund 6-8%, balanced 7-10%
- When surrender makes sense: IRR < 6% AND policy less than 50% through term AND no critical illness coverage gap
- When keep makes sense: policy > 75% through term OR guaranteed returns > current FD rate OR has CI rider not available elsewhere
- SVF/IPF pitch point: "Instead of surrendering at a loss, use SVF to get liquidity while keeping the policy alive"

**ClaimsGuide prompt — add:**
- Standard claim timeline: intimation within 24 hours, documents within 15 days, insurer decision within 30 days (IRDAI mandate)
- Cashless claim process: pre-authorization form → hospital submits → insurer approves/rejects within 1 hour (planned) or 3 hours (emergency)
- Reimbursement process: pay hospital → submit documents within 15-30 days → insurer processes within 30 days
- Common rejection reasons: non-disclosure of PED (35%), waiting period not met (25%), excluded treatment (20%), document issues (15%), policy lapsed (5%)
- Escalation path: insurer helpline → grievance cell → IGMS portal → insurance ombudsman → consumer court → NCDRC

**RegulationEngine prompt — add:**
- Key IRDAI circulars every Indian should know:
  - IRDAI/HLT/CIR/090/03/2024 — Master circular on health insurance (standardized exclusions, portability, moratorium)
  - IRDAI/LIFE/CIR/GDL/081/02/2024 — Guidelines on insurance products (revised surrender value norms)
  - Policyholder protection regulations 2024 — free look, claim settlement timelines, grievance
  - IRDAI (Insurance Advertisements and Disclosure) Regulations 2021 — mis-selling prevention
- Consumer rights: right to free look cancellation, right to port without losing PED credit, right to claim beyond policy period if intimated during policy period, right to interest on delayed claim settlement

**RiskDetector prompt — add:**
- Mis-selling red flags:
  - Endowment/ULIP sold to someone who needs term insurance (most common)
  - "Guaranteed returns" claim on market-linked products
  - Premium > 10% of annual income
  - Duplicate coverage (two health policies without knowing benefits stack)
  - Rider cost > 30% of base premium (over-loading)
  - Policy sold to person above product's target age
- Common coverage gaps by life stage:
  - Young single (22-30): usually no health insurance, no term
  - Young family (28-40): inadequate SI (<5x income), no child education cover
  - Mid-career (40-55): no critical illness, no top-up, outdated sum insured
  - Pre-retirement (55-65): no PA, health SI inadequate for metro hospitals

**TaxAdvisor prompt — add:**
- Section 80C (₹1.5L limit): life insurance premium (only if premium ≤10% of SA post-2012), PPF, ELSS, EPF, NPS Tier I, SCSS, NSC, home loan principal. Insurance competes with PPF/ELSS here.
- Section 80D: self/family ₹25,000, parents ₹25,000 (₹50,000 if senior), preventive health check ₹5,000 within 80D limit
- Section 80CCC: pension plan premium up to ₹1.5L (within 80C overall limit)
- Section 10(10D): maturity/death proceeds tax-free if annual premium ≤ ₹5L (post-2023 Budget). ULIP with premium > ₹2.5L taxed as capital gains.
- New vs Old regime: old regime benefits from 80C/80D deductions, new regime doesn't. If user is on new regime, 80C/80D deductions don't apply — insurance premium is pure cost.
- NPS vs insurance pension: NPS has 80CCD(1B) additional ₹50,000 deduction. NPS equity exposure is higher. NPS annuity is taxable, insurance pension annuity also taxable.

**Educator prompt — add:**
- Top 20 insurance terms every Indian gets wrong:
  - Copay: YOUR share, not insurer's
  - Sub-limit: ceiling on specific expense even if within SI
  - Room rent limit: affects EVERYTHING proportionally, not just room cost
  - Moratorium: after this period, insurer can't reject claims for non-disclosure (except fraud)
  - Free look: cancellation window, not "free trial"
  - NCB: No Claim Bonus — SI increase for claim-free years, not premium discount
  - Restoration: SI refills once per year if exhausted (not for same illness)
  - Floater: shared SI for family — one big claim exhausts everyone's coverage
  - Waiting period: for PED (36 months), for specific diseases (24 months), initial (30 days)
  - Surrender value: what you get back if you quit — NOT the premium you paid

---

## PART 2: KNOWLEDGE GRAPH ENRICHMENT

### 2a. Insurer Data — Upgrade to FY 2024-25

File: `hibiscus/knowledge/graph/seed/insurers.py` and `insurers_expanded.py`

For ALL 62 insurers in KG, verify and update with FY 2024-25 data:

**Search for and update:**
- Claim Settlement Ratio (CSR): Life insurers from IRDAI Annual Report 2024-25 (97.82% industry average)
- Incurred Claim Ratio (ICR): Health/General insurers (85.34% industry average, standalone health 68.06%)
- Solvency Ratio: from IRDAI Statement 11/12
- Complaint ratio: from IGMS portal data
- Network hospital count: from insurer websites (Star Health 14,000+, HDFC ERGO 13,000+, etc.)
- Average claim settlement time: from insurer public disclosures
- Premium income: from IRDAI annual report

**Key CSR data points to verify (FY 2024-25):**
- LIC: 98.64%
- HDFC Life: 99.07%
- ICICI Prudential: 99.17%
- SBI Life: 98.54%
- Max Life (Axis Max): 99.70%
- Tata AIA: 99.41%
- Bajaj Allianz Life: 98.09%
- Star Health: ~82.3% (health CSR, not death claim)
- Niva Bupa: ~97.5% (health)
- Care Health: ~97.0% (health)

### 2b. Product Data — Add Real Premiums

File: `hibiscus/knowledge/graph/seed/products_expanded.py`

For top 50 products (10 per category), add REAL premium data points:

**Health — add concrete premium examples:**
```
Star Health Comprehensive:
  - 25yo individual, ₹5L SI, Zone 1: ₹5,500/year
  - 30yo individual, ₹10L SI, Zone 1: ₹9,800/year
  - 35yo couple floater, ₹15L SI, Zone 1: ₹18,500/year
  - 45yo family (2A+2C), ₹20L SI, Zone 1: ₹28,000/year
  - 60yo individual, ₹10L SI, Zone 1: ₹35,000/year

HDFC Ergo Optima Secure:
  - 25yo individual, ₹10L SI, Zone 1: ₹7,200/year
  - 30yo individual, ₹10L SI, Zone 1: ₹8,500/year
  ... (similar age/SI matrix)

Niva Bupa ReAssure 2.0:
  ... (similar)

Care Supreme:
  ... (similar)
```

**Life Term — add concrete premium examples:**
```
HDFC Click2Protect Life:
  - 30yo male, non-smoker, ₹1Cr SA, 30yr term: ₹9,800/year
  - 35yo male, non-smoker, ₹1Cr SA, 25yr term: ₹13,200/year
  - 30yo female, non-smoker, ₹1Cr SA, 30yr term: ₹7,500/year

ICICI iProtect Smart:
  ... (similar)

Max Life Smart Secure Plus:
  ... (similar)
```

**Motor — add current TP premium rates (IRDAI fixed):**
```
Private car TP (by engine capacity):
  - ≤1000cc: ₹2,094
  - 1000-1500cc: ₹3,416
  - >1500cc: ₹7,897

Two-wheeler TP (by engine capacity):
  - ≤75cc: ₹538
  - 75-150cc: ₹714
  - 150-350cc: ₹1,366
  - >350cc: ₹2,804
```

### 2c. Benchmark Data — Make It Real

File: `hibiscus/knowledge/graph/seed/benchmarks_expanded.py`

Current 760 benchmarks are approximate. Replace with real data:

**Health premium benchmarks (verified from insurer websites):**
```
For EACH age band (18-25, 26-35, 36-45, 46-55, 56-65, 66+):
  For EACH SI level (₹3L, ₹5L, ₹10L, ₹15L, ₹25L, ₹50L, ₹1Cr):
    For EACH zone (Metro/Tier1, Tier2, Tier3):
      Average premium across top 5 insurers
      Min premium (cheapest plan)
      Max premium (most expensive plan)
```

**Life term premium benchmarks:**
```
For EACH age (25, 30, 35, 40, 45, 50):
  For EACH SA (₹50L, ₹1Cr, ₹2Cr):
    For EACH term (20yr, 25yr, 30yr):
      Average premium male/female non-smoker
```

**Average hospital costs by city tier (for gap analysis):**
```
Metro (Mumbai, Delhi, Bangalore, Chennai, Hyderabad, Kolkata):
  - Average ICU cost: ₹25,000-50,000/day
  - Average room rent (single AC): ₹8,000-15,000/day
  - Average heart surgery: ₹3-8L
  - Average knee replacement: ₹2.5-5L
  - Average cancer treatment: ₹5-20L
  - Average normal delivery: ₹50,000-1.5L
  - Average C-section: ₹1-3L

Tier 2 (Pune, Ahmedabad, Jaipur, Lucknow, Kochi):
  - Average ICU cost: ₹15,000-30,000/day
  ... (similar but lower)

Tier 3 and rural:
  ... (similar but lowest)
```

---

## PART 3: RAG CORPUS ENRICHMENT

### 3a. IRDAI Circulars — Priority 50

Add the 50 most important IRDAI circulars to `hibiscus/knowledge/rag/corpus/irdai_circulars/`:

**Must have (these are what users actually ask about):**

1. Master Circular on Health Insurance Products (2024) — standardized exclusions, sub-limits, portability
2. Policyholder Protection Regulations (2024) — claim settlement timeline, free look, grievance
3. Health Insurance Portability Guidelines — how to port, PED credit transfer
4. Standardized Health Insurance Exclusion Lists I-IV — exact text
5. Claim Settlement Guidelines — 30-day mandate, interest on delays
6. Free Look Period Regulations — 15/30 day rules
7. Insurance Ombudsman Rules 2017 (as amended) — jurisdiction, process, timelines
8. ULIP Disclosure Regulations — charge disclosure, NAV reporting
9. Surrender Value Regulations (revised 2024) — new GSV/SSV norms
10. Mis-selling Prevention Guidelines — what constitutes mis-selling, remedies
11. Insurance Advertisements Regulations 2021 — what insurers can/cannot claim
12. Motor Insurance Guidelines — TP premium, IDV computation, NCB transfer
13. Travel Insurance Guidelines — minimum coverage, standard benefits
14. Group Insurance Regulations — employer group health, master policy holder rights
15. Micro Insurance Regulations — for low-income segments
16. Pre-existing Disease Definition Circular — what counts as PED, moratorium rules
17. Standard Product Guidelines (Arogya Sanjeevani, Saral Jeevan Bima) — mandatory standard products
18. IRDAI (Insurance Surveyor and Loss Assessor) Regulations — for motor claims
19. KYC/AML Guidelines for Insurance — verification requirements
20. Digital Insurance Regulations — e-policy, electronic issuance
21-50: Additional circulars by category (health 15, life 10, motor 5, general 20)

For each circular, create a JSON entry:
```json
{
  "circular_no": "IRDAI/HLT/CIR/090/03/2024",
  "date": "2024-03-15",
  "subject": "Master Circular on Health Insurance Products",
  "category": "health",
  "key_points": ["standardized exclusions", "moratorium 5 years", "portability within 45 days"],
  "full_text_summary": "500-word comprehensive summary of the circular's provisions",
  "consumer_impact": "What this means for policyholders in plain language",
  "source_url": "https://irdai.gov.in/..."
}
```

### 3b. Glossary — Expand to 500

File: `hibiscus/knowledge/rag/corpus/glossary/`

Current: 202 terms. Target: 500.

Add the 298 most common insurance terms Indian consumers search for. For each term:
```json
{
  "term": "Room Rent Sub-Limit",
  "definition": "A cap on the daily room charges your insurer will cover. If your room costs more than the limit, ALL other expenses are reduced proportionally — not just the room charge.",
  "example": "Your policy has a ₹5,000/day room rent limit. You stay in a ₹10,000/day room. The insurer doesn't just deduct ₹5,000 — they reduce your ENTIRE claim by 50% (the ratio of limit to actual). A ₹3L surgery bill becomes ₹1.5L reimbursement.",
  "common_misconception": "Most people think only the room charge difference comes from their pocket. In reality, the proportional deduction applies to everything — surgery, medicines, doctor fees.",
  "eazr_tip": "Always check if your policy has 'no room rent limit' or if the limit matches single AC room rates in your city (₹8,000-15,000/day in metros).",
  "related_terms": ["Sub-limit", "Proportional Deduction", "Copay", "Single AC Room"],
  "category": "health"
}
```

Priority terms to add (grouped by what users actually search):
- Claim-related (30): TPA, cashless, reimbursement, pre-authorization, claim intimation, NEFT settlement, ...
- Policy-related (30): premium holiday, grace period, revival, paid-up value, reduced paid-up, lapse, ...
- Health-specific (50): day care, OPD, domiciliary, consumables, implant cover, organ donor, alternative treatment, ...
- Life-specific (40): bonus, reversionary bonus, terminal bonus, vested bonus, survival benefit, maturity benefit, ...
- Motor-specific (30): IDV, NCB, zero depreciation, RSA, engine protect, consumables cover, return to invoice, ...
- Tax-specific (20): 80C, 80D, 80CCC, 80CCD, 10(10D), new regime, old regime, ...
- Regulatory (30): IRDAI, IGMS, ombudsman, moratorium, contestability, Section 45, UIN, ...
- Financial (30): IRR, XIRR, CAGR, inflation-adjusted return, opportunity cost, break-even, ...
- EAZR-specific (20): EAZR Score, IPF, SVF, protection gap, premium financing, surrender value financing, ...

### 3c. Claims Processes — Expand to 100

File: `hibiscus/knowledge/rag/corpus/claims_processes/`

Current: 31. Target: 100.

Add detailed claim filing processes for:
- Top 10 health insurers (cashless + reimbursement flow, documents needed, timelines, escalation)
- Top 10 life insurers (death claim + maturity claim + survival benefit flow)
- Top 5 motor insurers (own damage + third party + total loss flow)
- General processes: how to file IGMS complaint, how to approach ombudsman, how to file consumer court case
- Specific claim types: cashless hospitalization, planned surgery pre-auth, emergency hospitalization, OPD claim, day care claim, domiciliary claim, maternity claim, critical illness claim

### 3d. Case Law — Expand to 100

File: `hibiscus/knowledge/rag/corpus/case_law/`

Current: 40. Target: 100.

Add landmark insurance case law that helps users understand their rights:
- Supreme Court rulings on claim rejections
- Consumer court orders on mis-selling
- Ombudsman decisions on PED disputes
- NCDRC orders on delayed claim settlement
- High court rulings on policy interpretation

For each case:
```json
{
  "case_name": "United India Insurance v. Manmohan Devi (2012)",
  "court": "Supreme Court of India",
  "category": "health",
  "issue": "Insurer rejected claim citing non-disclosure of PED",
  "ruling": "Court ruled in favor of policyholder — insurer had not conducted pre-policy medical examination",
  "consumer_impact": "If insurer doesn't do medical tests before issuing policy, they cannot later reject claims citing non-disclosure of pre-existing conditions",
  "citation": "2012 SCC OnLine SC 1234"
}
```

---

## PART 4: FORMULA ENRICHMENT

### 4a. Missing Formula Files

Create these files with real, verified formulas:

`hibiscus/knowledge/formulas/premium_adequacy.py`:
- Income multiple method: recommended SI = 10-15x annual income (life), 10x for health
- HLV (Human Life Value): present value of future earnings discounted at 8%
- Expense method: total family expenses × years until youngest child independent

`hibiscus/knowledge/formulas/inflation.py`:
- Medical inflation rate: 12-15% per year in India (vs general CPI 5-6%)
- Future hospital cost: current_cost × (1 + medical_inflation)^years
- SI adequacy with inflation: SI needed today × (1 + inflation)^policy_term

`hibiscus/knowledge/formulas/emi.py`:
- IPF EMI: standard reducing balance EMI formula
- SVF calculation: surrender_value × LTV_ratio (60-80%), interest 12-18% per annum
- Break-even analysis: months where EMI total < premium saved by not surrendering

`hibiscus/knowledge/formulas/opportunity_cost.py`:
- Compare: premium invested in Nifty 50 (12% CAGR) vs policy maturity value
- Compare: premium invested in PPF (7.1%) vs endowment maturity
- Compare: term + mutual fund vs endowment/ULIP

`hibiscus/knowledge/formulas/eazr_score.py`:
- Complete EAZR Protection Score algorithm with weights per category
- Component formulas: coverage_adequacy, insurer_quality, feature_richness, value_for_money, risk_exposure
- Score normalization to 0-100 scale

`hibiscus/knowledge/formulas/depreciation.py`:
- Motor IDV depreciation table by vehicle age (from IRDAI schedule)
- Part-wise depreciation: rubber/nylon 50%, fiberglass 30%, plastic 50%, metal body by age
- Salvage value estimation

`hibiscus/knowledge/formulas/compound_growth.py`:
- CAGR calculator
- Inflation-adjusted returns
- Rule of 72 for doubling time
- Present value / future value

---

## VERIFICATION

After enrichment, run these checks:

```bash
# 1. Seed updated KG
make seed-kg
# Verify: insurer CSR values are FY 2024-25
# Verify: products have real premium data points
# Verify: benchmarks match published data

# 2. Re-ingest RAG corpus
make seed-rag
# Verify: "IRDAI portability circular" returns real circular with number
# Verify: "room rent sub-limit" returns detailed glossary entry with example
# Verify: "claim rejected PED" returns relevant case law
# Verify: point count significantly higher than current 794

# 3. Run HibiscusBench
make eval
# DQ must be >= 0.84 (should IMPROVE with richer data)
# Accuracy score (0.522) should improve significantly — this is the keyword coverage that benefits most from richer prompts

# 4. Spot check specific queries:
# "Best health plan for 30yo in Mumbai ₹15L budget" → should cite specific premiums and CSR
# "Should I surrender my LIC Jeevan Anand?" → should give IRR comparison with real numbers
# "How to file cashless claim with Star Health?" → should give exact step-by-step with documents and timelines
# "What is room rent sub-limit?" → should explain proportional deduction with example
# "IRDAI rule on pre-existing disease waiting period" → should cite exact circular number and provisions
```

---

## RESEARCH METHODOLOGY

For data that requires verification:

1. **IRDAI data (CSR, solvency, ICR):** Use IRDAI Annual Report 2024-25. Available at irdai.gov.in and lifeinscouncil.org.
2. **Premium data:** Use insurer websites directly (star1.in, hdfcergo.com, nivabupa.com, careinsurance.com). Get quotes for standard profiles.
3. **Benchmark data:** Cross-reference Ditto (joinditto.in), Beshak (beshak.org), and PolicyBazaar for comparative premium data.
4. **IRDAI circulars:** Download from irdai.gov.in/circulars. Use exact circular numbers and dates.
5. **Case law:** Use Indian Kanoon (indiankanoon.org), SCC Online, or legal databases. Use exact citations.
6. **Hospital costs:** Use NHA (National Health Authority) data, NATHEALTH reports, and hospital chain published rate cards.

**Where web search is not available in Claude Code, use the embedded knowledge from training data. Mark any data point that cannot be verified as "approximate — verify before production."**

---

## RULES

- **Every number must have a source.** If from IRDAI annual report, note "Source: IRDAI AR 2024-25". If from insurer website, note "Source: {insurer}.com, accessed March 2026". If from training data and unverifiable, note "Approximate — verify".
- **Don't fabricate precise numbers.** If you don't know Star Health's exact CSR for FY25, use the closest verified number and mark it.
- **Premium data gets stale fast.** Mark all premium data with "as of Q1 FY26" or similar date stamp.
- **Indian context only.** No US/UK insurance concepts mixed in. Room rent in ₹, not $. Copay as Indian insurers define it (not US deductible model).
- **Update CLAUDE.md** after enrichment with summary of what was added. CLAUDE.md is the ONLY project memory file — there is no MEMORY.md.

Commit and push when complete.
