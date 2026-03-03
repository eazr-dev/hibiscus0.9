"""
Tax Rules Seed Data
====================
Indian income tax rules applicable to insurance premiums and proceeds.
Sources: Income Tax Act 1961 (as amended), Finance Act 2021, Finance Act 2023.

All deduction limits in INR. Tax rules as of Financial Year 2024-25.
Run via: python -m hibiscus.knowledge.graph.seed
"""
from typing import Any, Dict, List

from hibiscus.knowledge.graph.client import Neo4jClient
from hibiscus.observability.logger import get_logger

logger = get_logger("hibiscus.kg.seed.tax_rules")


TAX_RULES: List[Dict[str, Any]] = [

    # ── Section 80C — Life Insurance Premium Deduction ────────────────────────

    {
        "section": "80C",
        "subsection": "life_insurance_premium",
        "title": "Section 80C — Life Insurance Premium Deduction",
        "max_deduction": 150000,
        "max_deduction_formatted": "₹1,50,000",
        "applicable_to": ["individual", "HUF"],
        "regime": "old_tax_regime_only",
        "tax_saving_at_30pct_bracket": 46800,
        "conditions": [
            "Policy issued before 1 April 2012: premium must be <= 20% of sum assured",
            "Policy issued on or after 1 April 2012: premium must be <= 10% of sum assured",
            "Policy issued for person with disability (Section 80U) or critical illness: premium <= 15% of sum assured",
            "Deduction available for own life, spouse, and children only",
            "Deduction is within the combined ₹1.5 lakh limit of Section 80C/80CCC/80CCD(1)",
        ],
        "disqualification_conditions": [
            "Policy terminated before 2 years from inception — deduction claimed is reversed",
            "ULIP surrendered before 5 years — deduction reversed",
        ],
        "examples": [
            "Premium ₹12,000/year for ₹1 lakh SA (12% of SA) — NOT eligible for policy after Apr 2012",
            "Premium ₹10,000/year for ₹1 lakh SA (10% of SA) — eligible",
            "Premium ₹50,000/year for ₹10 lakh SA (5% of SA) — eligible",
        ],
        "key_traps": [
            "LIC endowment plans with high premium-to-SA ratio may not fully qualify",
            "Only old tax regime benefit — new regime (default from FY 2024-25) has no 80C",
        ],
        "fy_applicable": "2024-25",
        "relevant_products": ["life_term", "life_endowment", "life_money_back", "life_savings", "ulip"],
    },

    # ── Section 80CCC — Pension Fund Contribution ─────────────────────────────

    {
        "section": "80CCC",
        "subsection": "pension_fund_contribution",
        "title": "Section 80CCC — Contribution to Pension Fund by LIC/Insurers",
        "max_deduction": 150000,
        "max_deduction_formatted": "₹1,50,000 (part of 80C combined limit)",
        "applicable_to": ["individual"],
        "regime": "old_tax_regime_only",
        "tax_saving_at_30pct_bracket": 46800,
        "conditions": [
            "Premium paid to LIC or any other insurer for annuity/pension plan",
            "Amount must be for a plan that provides pension after specified period",
            "Combined limit with 80C and 80CCD(1) is ₹1.5 lakh — not additive",
        ],
        "disqualification_conditions": [
            "Surrender of policy — entire amount received is taxable in the year of receipt",
            "Amount received on maturity of annuity is taxable as income",
        ],
        "examples": [
            "Contribution of ₹1,00,000 to LIC Jeevan Akshay pension plan — eligible up to ₹1.5L combined",
        ],
        "key_traps": [
            "Annuity payouts are fully taxable — no exemption on receipt",
            "This is often misunderstood as fully tax-free",
        ],
        "fy_applicable": "2024-25",
        "relevant_products": ["annuity", "pension"],
    },

    # ── Section 80D — Health Insurance Premium Deduction ─────────────────────

    {
        "section": "80D",
        "subsection": "self_and_family",
        "title": "Section 80D — Health Insurance Premium — Self, Spouse, Children",
        "max_deduction": 25000,
        "max_deduction_formatted": "₹25,000",
        "applicable_to": ["individual", "HUF"],
        "regime": "old_tax_regime_only",
        "tax_saving_at_30pct_bracket": 7800,
        "conditions": [
            "Premium paid for health insurance of self, spouse, dependent children",
            "Premium must be paid in any mode other than cash",
            "Preventive health check-up: sub-limit ₹5,000 within the ₹25,000 limit",
            "If any insured is senior citizen (age 60+), limit increases to ₹50,000",
        ],
        "disqualification_conditions": [
            "Premium paid in cash is not eligible",
            "Group health policy premium paid by employer is not eligible for deduction by employee",
        ],
        "examples": [
            "Individual age 35, health premium ₹12,000 — deduct ₹12,000",
            "Individual age 35, health premium ₹30,000 — deduct max ₹25,000",
            "Individual age 35, spouse is 60+, health premium ₹30,000 — deduct ₹30,000 (senior citizen limit ₹50,000)",
        ],
        "key_traps": [
            "Many people miss the preventive check-up sub-limit of ₹5,000",
            "Only old tax regime benefit",
        ],
        "fy_applicable": "2024-25",
        "relevant_products": ["health_individual", "health_family_floater"],
    },
    {
        "section": "80D",
        "subsection": "parents",
        "title": "Section 80D — Additional Deduction for Parents' Health Insurance",
        "max_deduction": 25000,
        "max_deduction_formatted": "₹25,000 (₹50,000 if parent is senior citizen)",
        "applicable_to": ["individual"],
        "regime": "old_tax_regime_only",
        "tax_saving_at_30pct_bracket": 15600,
        "conditions": [
            "Additional ₹25,000 deduction for health insurance premium paid for parents",
            "If either parent is aged 60 or above: limit increases to ₹50,000",
            "Parents need NOT be financially dependent on the taxpayer",
            "Payment must not be in cash",
        ],
        "disqualification_conditions": [
            "Parents-in-law are NOT eligible — only own parents",
            "Cash payment disqualifies",
        ],
        "examples": [
            "Parents age 58 and 60: premium ₹20,000 for parent health — deduct ₹20,000",
            "Parents age 62 and 65: premium ₹45,000 — deduct max ₹50,000",
            "Both policyholder (35) and parents (62+) are insured: total deduction up to ₹25,000 + ₹50,000 = ₹75,000",
        ],
        "max_combined_deduction": 75000,
        "max_combined_deduction_formatted": "₹75,000 (self ₹25K + parents ₹50K, if parents senior)",
        "key_traps": [
            "Many policyholders are unaware of the additional ₹50,000 for senior parents",
        ],
        "fy_applicable": "2024-25",
        "relevant_products": ["health_individual", "health_family_floater", "senior_citizen_health"],
    },
    {
        "section": "80D",
        "subsection": "both_senior_citizens",
        "title": "Section 80D — Maximum Deduction When Both Policyholder and Parents are Senior Citizens",
        "max_deduction": 100000,
        "max_deduction_formatted": "₹1,00,000",
        "applicable_to": ["individual"],
        "regime": "old_tax_regime_only",
        "tax_saving_at_30pct_bracket": 31200,
        "conditions": [
            "Policyholder AND/OR spouse is 60+ years: limit is ₹50,000 for self+family",
            "Parents are 60+ years: additional ₹50,000",
            "Total maximum ₹1,00,000 if both policyholder (or spouse) and parents are senior citizens",
        ],
        "disqualification_conditions": [
            "New tax regime — no 80D benefit",
            "Cash payments",
        ],
        "examples": [
            "Policyholder 62, parents 65+: premium ₹45,000 self + ₹48,000 parents = deduct ₹50,000 + ₹48,000 = ₹98,000",
        ],
        "fy_applicable": "2024-25",
        "relevant_products": ["health_individual", "senior_citizen_health"],
    },

    # ── Section 10(10D) — Life Insurance Maturity Proceeds Exemption ──────────

    {
        "section": "10(10D)",
        "subsection": "general_exemption",
        "title": "Section 10(10D) — Maturity Proceeds of Life Insurance Tax Exempt",
        "max_deduction": None,
        "max_deduction_formatted": "No upper limit (subject to conditions)",
        "applicable_to": ["individual", "HUF"],
        "regime": "both_regimes",
        "tax_saving_at_30pct_bracket": None,
        "conditions": [
            "Policy issued on or after 1 April 2003 but before 1 April 2012: premium must be <= 20% of sum assured",
            "Policy issued on or after 1 April 2012: premium must be <= 10% of sum assured for exemption",
            "Death benefit is ALWAYS exempt — no restriction",
            "Maturity + bonus exempt if premium condition is satisfied",
            "ULIP policies with premium <= ₹2.5 lakh per year: maturity exempt",
        ],
        "disqualification_conditions": [
            "ULIP issued on or after 1 Feb 2021 with annual premium > ₹2.5 lakh: gains taxable at 10% LTCG",
            "Life policy with premium > 10% of sum insured: maturity amount is taxable",
            "Keyman insurance policies: maturity is fully taxable",
        ],
        "examples": [
            "LIC policy (issued 2018), premium ₹1L, SA ₹10L (10%), maturity ₹15L — EXEMPT",
            "LIC policy (issued 2018), premium ₹2L, SA ₹10L (20%), maturity ₹15L — TAXABLE (TDS at 5%)",
            "ULIP started 2022, annual premium ₹5L > ₹2.5L threshold — gains taxable at 10% LTCG",
        ],
        "tds_provision": "TDS at 5% on maturity proceeds if NOT exempt under 10(10D)",
        "key_traps": [
            "High-premium LIC policies bought by misled investors may not be 10(10D) exempt",
            "ULIP buyers who invested > ₹2.5L/year after Feb 2021 will face capital gains tax",
            "Always check premium-to-SA ratio before buying for tax purposes",
        ],
        "fy_applicable": "2024-25",
        "relevant_products": ["life_endowment", "life_money_back", "life_savings", "ulip", "life_term"],
    },

    # ── ULIP Special Tax Rule (Finance Act 2021) ──────────────────────────────

    {
        "section": "10(10D)",
        "subsection": "ulip_high_premium_taxation",
        "title": "ULIP Taxation — Annual Premium Above ₹2.5 Lakh (Finance Act 2021)",
        "max_deduction": None,
        "max_deduction_formatted": "NA — this is a taxability rule, not a deduction",
        "applicable_to": ["individual"],
        "regime": "both_regimes",
        "tax_saving_at_30pct_bracket": None,
        "conditions": [
            "Applies to ULIP policies issued on or after 1 February 2021",
            "If aggregate annual premium across all ULIPs > ₹2.5 lakh: NOT exempt under 10(10D)",
            "Maturity gains from such ULIPs are treated as capital gains",
            "Holding > 12 months from redemption: taxed at 10% LTCG (no indexation)",
            "Death benefit remains exempt regardless of premium amount",
        ],
        "disqualification_conditions": [
            "ULIPs issued before 1 Feb 2021 are NOT affected",
            "ULIPs where aggregate premium <= ₹2.5L across all policies remain exempt",
        ],
        "examples": [
            "ULIP issued March 2021, premium ₹3L/year: maturity ₹40L, cost base ₹15L — LTCG = ₹25L taxable at 10%",
            "Two ULIPs, ₹1.5L premium each = ₹3L aggregate > ₹2.5L — both taxable",
        ],
        "tax_implication_example": "₹25L gain on ULIP → ₹2.5L LTCG tax (10%). Vs ELSS mutual fund: also 10% LTCG — similar treatment",
        "key_traps": [
            "Aggregate across ALL ULIPs — even if each individual policy is below ₹2.5L",
            "Mis-sold ULIPs post Feb 2021 as 'tax-free' are incorrect claims",
        ],
        "fy_applicable": "2024-25",
        "relevant_products": ["ulip"],
    },

    # ── GST on Insurance Premiums ─────────────────────────────────────────────

    {
        "section": "GST",
        "subsection": "insurance_premium_gst",
        "title": "GST on Insurance Premiums",
        "max_deduction": None,
        "max_deduction_formatted": "NA — this is a cost, not a deduction",
        "applicable_to": ["individual", "corporate"],
        "regime": "both_regimes",
        "tax_saving_at_30pct_bracket": None,
        "conditions": [
            "Term life insurance: 18% GST on premium",
            "Health insurance premium: 18% GST",
            "ULIP: 18% GST on charges (fund management, allocation, etc.)",
            "Endowment/savings plans: 18% GST on first-year premium; 9% GST from second year",
            "Motor insurance: 18% GST",
            "Travel insurance: 18% GST",
        ],
        "disqualification_conditions": [],
        "examples": [
            "Health premium ₹10,000 + 18% GST = ₹11,800 total payment",
            "Term premium ₹12,000 + 18% GST = ₹14,160 total",
            "LIC endowment premium ₹30,000 (Year 1): 4.5% GST = ₹31,350 (LIC has concessional rate of 4.5% for traditional)",
        ],
        "special_note": "LIC traditional (endowment/money back) policies: 4.5% GST in Year 1, 2.25% from Year 2 onwards — lower than private insurers",
        "key_traps": [
            "GST is included in premium quote from most insurers — verify if inclusive or exclusive",
            "80D deduction is on the total premium paid including GST",
            "GST on health premium is part of the deductible amount under 80D",
        ],
        "fy_applicable": "2024-25",
        "relevant_products": ["health_individual", "life_term", "motor", "travel", "ulip", "life_endowment"],
    },

    # ── NPS / Section 80CCD ───────────────────────────────────────────────────

    {
        "section": "80CCD",
        "subsection": "80CCD_1B_additional_nps",
        "title": "Section 80CCD(1B) — Additional NPS Deduction ₹50,000",
        "max_deduction": 50000,
        "max_deduction_formatted": "₹50,000 (OVER AND ABOVE 80C limit)",
        "applicable_to": ["individual"],
        "regime": "old_tax_regime_only",
        "tax_saving_at_30pct_bracket": 15600,
        "conditions": [
            "Additional ₹50,000 deduction for NPS contribution (Tier I account)",
            "This is SEPARATE from the ₹1.5L limit of 80C — total can be ₹2L",
            "Available only for own contribution (not employer contribution which is 80CCD(2))",
        ],
        "disqualification_conditions": [
            "New tax regime — not applicable",
            "Tier II NPS account — not eligible",
        ],
        "examples": [
            "80C used ₹1.5L (LIC + PPF) + 80CCD(1B) ₹50,000 NPS = total ₹2L deduction",
            "Tax saving at 30%: (₹1.5L + ₹50K) × 30% = ₹60,000 saved",
        ],
        "key_traps": [
            "NPS has 60% lump sum on maturity (40% mandatory annuity which is taxable)",
            "NPS is less liquid than mutual funds — lock-in till retirement",
        ],
        "fy_applicable": "2024-25",
        "relevant_products": ["nps", "annuity"],
    },

    # ── TDS on Insurance Maturity / Claim Payments ────────────────────────────

    {
        "section": "194DA",
        "subsection": "tds_on_insurance_maturity",
        "title": "Section 194DA — TDS on Life Insurance Policy Maturity Payments",
        "max_deduction": None,
        "max_deduction_formatted": "NA — TDS provision",
        "applicable_to": ["individual"],
        "regime": "both_regimes",
        "tax_saving_at_30pct_bracket": None,
        "conditions": [
            "TDS at 5% on maturity payment if policy is NOT exempt under Section 10(10D)",
            "Applies when maturity amount > ₹1 lakh",
            "TDS is on the 'income' portion (maturity - premiums paid) for policies after FY 2019-20",
            "If policy IS exempt under 10(10D), NO TDS",
        ],
        "disqualification_conditions": [
            "10(10D) exempt policies — TDS does not apply",
            "Death claims — TDS does not apply (always exempt)",
        ],
        "examples": [
            "LIC maturity ₹15L, premiums paid ₹10L, income = ₹5L, NOT 10(10D) exempt: TDS = 5% × ₹5L = ₹25,000",
            "HDFC Term policy death claim ₹1Cr — no TDS",
        ],
        "key_traps": [
            "Many policyholders are surprised by TDS on LIC maturity if premium-to-SA ratio is high",
        ],
        "fy_applicable": "2024-25",
        "relevant_products": ["life_endowment", "life_money_back", "life_savings"],
    },
]


# ── Cypher ─────────────────────────────────────────────────────────────────────

_MERGE_TAX_RULE = """
MERGE (t:TaxRule {section: $section, subsection: $subsection})
SET
  t.title                      = $title,
  t.max_deduction              = $max_deduction,
  t.max_deduction_formatted    = $max_deduction_formatted,
  t.applicable_to              = $applicable_to,
  t.regime                     = $regime,
  t.conditions                 = $conditions,
  t.disqualification_conditions = $disqualification_conditions,
  t.examples                   = $examples,
  t.key_traps                  = $key_traps,
  t.fy_applicable              = $fy_applicable,
  t.relevant_products          = $relevant_products,
  t.updated_at                 = datetime()
RETURN t.section AS section, t.subsection AS subsection
"""


async def seed_tax_rules(client: Neo4jClient) -> None:
    """
    MERGE all TaxRule nodes into Neo4j. Idempotent — safe to re-run.
    """
    logger.info("seed_tax_rules_start", count=len(TAX_RULES))

    tax_params = []
    for rule in TAX_RULES:
        params = {
            "section": rule["section"],
            "subsection": rule["subsection"],
            "title": rule["title"],
            "max_deduction": rule.get("max_deduction"),
            "max_deduction_formatted": rule.get("max_deduction_formatted", ""),
            "applicable_to": rule.get("applicable_to", []),
            "regime": rule.get("regime", "old_tax_regime_only"),
            "conditions": rule.get("conditions", []),
            "disqualification_conditions": rule.get("disqualification_conditions", []),
            "examples": rule.get("examples", []),
            "key_traps": rule.get("key_traps", []),
            "fy_applicable": rule.get("fy_applicable", "2024-25"),
            "relevant_products": rule.get("relevant_products", []),
        }
        tax_params.append(params)

    succeeded = await client.execute_batch(
        _MERGE_TAX_RULE,
        param_list=tax_params,
        query_name="seed_tax_rules",
    )
    logger.info("seed_tax_rules_complete", succeeded=succeeded, total=len(TAX_RULES))
