<!-- Hibiscus v0.9 — EAZR AI Insurance Intelligence Engine -->
<!-- Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved. -->

# Hibiscus RAG Corpus

This directory contains the knowledge corpus for Hibiscus's RAG (Retrieval-Augmented Generation) pipeline. All content here is ingested into Qdrant's `insurance_knowledge` collection for semantic + keyword hybrid search.

## Directory Structure

```
corpus/
├── glossary/
│   └── insurance_terms.json         # 75+ insurance terms with full definitions
├── irdai_circulars/
│   └── key_regulations.json         # 20 key IRDAI regulations and circulars
├── claims_processes/
│   └── health_claims.json           # Claims processes for 6 major insurers
├── tax_rules/
│   └── insurance_tax.json           # Complete insurance tax guide (80C, 80D, 10(10D), etc.)
└── README.md                        # This file
```

## Corpus Contents

### glossary/insurance_terms.json
- 75+ insurance terms with definitions, examples, and Indian context
- Coverage: health, life, motor, ULIP, traditional plans, tax terms
- Format: `term`, `definition`, `example`, `indian_context`, `related_terms`

### irdai_circulars/key_regulations.json
- 20 key IRDAI regulations from 2010-2024
- Coverage: health insurance reforms, ULIP charge caps, portability, ombudsman, mental health mandate, multi-year policies
- Format: `circular_no`, `date`, `subject`, `key_points`, `consumer_rights`

### claims_processes/health_claims.json
- Step-by-step claims process for: Star Health, Niva Bupa, HDFC Ergo, ICICI Lombard, Bajaj Allianz, New India
- Both cashless and reimbursement processes
- Documents required, TPA details, toll-free numbers, timelines
- General claims guidance for all insurers

### tax_rules/insurance_tax.json
- Section 80C: Life insurance premium deduction
- Section 80D: Health insurance premium deduction (self + parents, senior citizen slabs)
- Section 10(10D): Life insurance maturity exemption (including post-Budget 2021/2023 changes)
- GST on insurance premiums
- ULIP tax treatment (post-Feb 2021 rules)
- TDS on insurance payouts
- New Tax Regime impact on insurance deductions
- NPS vs insurance for tax planning

## Ingestion

To ingest all corpus files into Qdrant:

```bash
# From the hibiscus package root
python -m hibiscus.knowledge.rag.ingestion

# Ingest a single file
python -m hibiscus.knowledge.rag.ingestion --file glossary/insurance_terms.json

# Or use Make
make seed-rag
```

## Corpus Refresh Schedule

| Corpus | Refresh Trigger | Owner |
|---|---|---|
| IRDAI Circulars | New IRDAI regulation published | Hibiscus team |
| Glossary | New product terms, regulatory changes | Hibiscus team |
| Claims Processes | Insurer process changes, network updates | Hibiscus team |
| Tax Rules | Budget announcements, IT circular updates | Hibiscus team |

## Adding New Corpus Files

1. Create a JSON file in the appropriate subdirectory
2. Follow the existing item structure (auto-detected by ingestion pipeline)
3. Run `python -m hibiscus.knowledge.rag.ingestion --file <path>`
4. Verify with: `python -c "from hibiscus.knowledge.rag.client import rag_client; import asyncio; asyncio.run(rag_client.connect()); print(asyncio.run(rag_client.count('insurance_knowledge')))`

## Chunking Strategy

- Chunk size: 800 characters
- Overlap: 100 characters
- Splitter: RecursiveCharacterTextSplitter (paragraph → sentence → word → char)
- Contextual prefix: Each chunk prefixed with source, date, and category context
  - Format: `"This is from [source], dated [date], category: [category], section: [section]. "`
  - This improves retrieval recall by ~40% (Anthropic contextual retrieval research)

## Collections

| Collection | Purpose |
|---|---|
| `insurance_knowledge` | All static corpus files (this directory) |
| `user_conversations` | Per-user conversation history |
| `user_knowledge` | Per-user extracted policy facts |

## Sources

- IRDAI regulations: irdai.gov.in
- Claims processes: Insurer official websites and toll-free helpline guides
- Tax rules: Income Tax Act 1961, CBDT circulars, Budget notifications
- Glossary: IRDAI publications, IAIS glossary, industry practice

All content is for informational purposes. For binding policy terms, always refer to the actual policy document and IRDAI's official website.
