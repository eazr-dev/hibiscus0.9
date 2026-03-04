"""
Tax Rules Seed Data
====================
Indian income tax rules applicable to insurance premiums and proceeds.
Sources: Income Tax Act 1961 (as amended), Finance Act 2021, Finance Act 2023,
Finance Act 2024.

Contains 30+ entries covering: 80C, 80CCC, 80D, 80CCD, 80CCE, 80DDB, 80GG, 80U,
10(10D), 10(23AAB), 37(1), 24(b), 80CCE, GST, 194DA, new tax regime, surrender/
annuity taxation.

All deduction limits in INR. Tax rules as of Financial Year 2024-25.
Run via: python -m hibiscus.knowledge.graph.seed
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
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

    # ── Section 80D — Additional Scenarios ────────────────────────────────────

    {
        "section": "80D",
        "subsection": "health_insurance_senior_only",
        "title": "Section 80D — Senior Parents Only: ₹50,000 Deduction",
        "max_deduction": 75000,
        "max_deduction_formatted": "₹75,000 (₹25,000 self + ₹50,000 senior parents)",
        "applicable_to": ["individual"],
        "regime": "old_tax_regime_only",
        "tax_saving_at_30pct_bracket": 23400,
        "conditions": [
            "Self (and spouse/children) are below 60 years — limit ₹25,000",
            "Parents are 60 years or above — additional limit ₹50,000",
            "Both limits are separate and fully stackable",
            "Total possible deduction: ₹25,000 (self) + ₹50,000 (senior parents) = ₹75,000",
            "Parents need not be financially dependent on the taxpayer",
        ],
        "disqualification_conditions": [
            "Parents-in-law are not eligible — only own parents",
            "Cash payment for insurance premium disqualifies",
        ],
        "examples": [
            "Self (age 38), parents (age 62 and 65): self premium ₹20,000 + parents premium ₹42,000 = deduct ₹20,000 + ₹42,000 = ₹62,000",
            "Self premium ₹30,000 (capped at ₹25,000) + parents premium ₹55,000 (capped at ₹50,000) = ₹75,000 total",
        ],
        "key_traps": [
            "Many policyholders claim only ₹25,000 and miss the additional ₹50,000 for senior parents",
            "Even if parents have their own employer-provided insurance, you can still claim deduction for premiums you pay on a separate policy",
        ],
        "fy_applicable": "2024-25",
        "relevant_products": ["health_individual", "health_family_floater", "senior_citizen_health"],
    },
    {
        "section": "80D",
        "subsection": "preventive_health_checkup",
        "title": "Section 80D — Preventive Health Check-up Sub-limit ₹5,000",
        "max_deduction": 5000,
        "max_deduction_formatted": "₹5,000 (sub-limit WITHIN the overall 80D limit)",
        "applicable_to": ["individual", "HUF"],
        "regime": "old_tax_regime_only",
        "tax_saving_at_30pct_bracket": 1560,
        "conditions": [
            "₹5,000 sub-limit for preventive health check-up expenditure — part of, not in addition to, the 80D limit",
            "CASH payment is allowed for preventive health check-up (exception to the no-cash rule for premiums)",
            "Does not require an insurance policy — direct medical check-up expenditure qualifies",
            "Can be claimed for self, spouse, dependent children, or parents",
            "Comes out of the overall ₹25,000 (or ₹50,000 for senior) 80D limit",
        ],
        "disqualification_conditions": [
            "Amount exceeding ₹5,000 is not additionally deductible under this sub-limit",
            "Diagnostic tests for treatment of illness do not qualify — must be preventive",
        ],
        "examples": [
            "Health premium ₹22,000 + preventive check-up ₹4,000 = total ₹26,000, deductible ₹25,000 (cap)",
            "Health premium ₹18,000 + preventive check-up ₹5,000 = total ₹23,000, fully deductible (within ₹25,000 limit)",
            "No health insurance policy but spent ₹5,000 on full-body check-up — still eligible for ₹5,000 deduction",
        ],
        "key_traps": [
            "The ₹5,000 is NOT additive on top of ₹25,000/₹50,000 — it is within that limit",
            "Cash payment is explicitly allowed only for preventive check-up, not insurance premium",
        ],
        "fy_applicable": "2024-25",
        "relevant_products": ["health_individual", "health_family_floater"],
    },
    {
        "section": "80D",
        "subsection": "health_insurance_group",
        "title": "Section 80D — Group Health Insurance: Employee vs. Top-up Treatment",
        "max_deduction": 25000,
        "max_deduction_formatted": "₹25,000 (on employee-paid top-up only)",
        "applicable_to": ["individual"],
        "regime": "old_tax_regime_only",
        "tax_saving_at_30pct_bracket": 7800,
        "conditions": [
            "Group health insurance premium paid by employer: NOT deductible by employee under 80D",
            "Employer gets deduction of premium as business expense under Section 37(1)",
            "Employee pays additional top-up or super top-up premium separately: eligible under 80D",
            "If employee pays a portion of the group premium from salary: that portion is eligible under 80D",
        ],
        "disqualification_conditions": [
            "Premium paid entirely by employer with no employee contribution: zero 80D benefit for employee",
            "Cash payment by employee for top-up: disqualifies",
        ],
        "examples": [
            "Employer pays ₹15,000 group premium fully: employee gets ₹0 deduction under 80D",
            "Employee buys ₹20,000 top-up policy separately: deduct ₹20,000 under 80D",
            "Employer pays ₹12,000, employee contributes ₹8,000 from salary: employee can claim ₹8,000",
        ],
        "key_traps": [
            "Employees with group insurance often assume they have no 80D benefit — they can still buy a top-up and claim",
            "Group term life insurance premium paid by employer: also not deductible by employee under 80C",
        ],
        "fy_applicable": "2024-25",
        "relevant_products": ["health_individual", "health_family_floater", "super_top_up"],
    },

    # ── Section 80C — Variants and Competing Instruments ──────────────────────

    {
        "section": "80C",
        "subsection": "ppf_comparison",
        "title": "Section 80C — PPF vs. Life Insurance: Comparison within ₹1.5L Limit",
        "max_deduction": 150000,
        "max_deduction_formatted": "₹1,50,000 (shared limit)",
        "applicable_to": ["individual", "HUF"],
        "regime": "old_tax_regime_only",
        "tax_saving_at_30pct_bracket": 46800,
        "conditions": [
            "PPF contribution and life insurance premium share the same ₹1.5L Section 80C limit",
            "PPF interest (currently 7.1% p.a.) is fully tax-exempt under Section 10(11)",
            "PPF maturity proceeds are also fully exempt — EEE (Exempt-Exempt-Exempt) status",
            "Insurance provides risk cover; PPF does not — they serve different purposes",
        ],
        "disqualification_conditions": [
            "PPF + Insurance + ELSS + home loan principal + tuition fees all compete for the same ₹1.5L",
            "ULIP charges (allocation, fund management) reduce effective returns vs PPF",
        ],
        "examples": [
            "₹1.5L invested: PPF ₹1.5L at 7.1% EEE vs ULIP ₹1.5L with 2-3% charges — PPF gives better net return",
            "Saving ₹46,800 tax at 30% bracket on ₹1.5L in 80C regardless of instrument chosen",
        ],
        "key_traps": [
            "Agents selling ULIPs rarely mention PPF as a competing 80C instrument with better returns and EEE status",
            "ULIP charges eat 1.5-2.5% annually — over 20 years this is a large compounded loss vs PPF",
        ],
        "fy_applicable": "2024-25",
        "relevant_products": ["ulip", "life_endowment", "life_savings"],
    },
    {
        "section": "80C",
        "subsection": "children_education",
        "title": "Section 80C — Children's Tuition Fees Compete with Insurance Premium",
        "max_deduction": 150000,
        "max_deduction_formatted": "₹1,50,000 (shared limit — tuition fees + insurance + other 80C)",
        "applicable_to": ["individual"],
        "regime": "old_tax_regime_only",
        "tax_saving_at_30pct_bracket": 46800,
        "conditions": [
            "Tuition fees for up to 2 children at any Indian university/school are eligible under 80C",
            "Full-time courses only — part-time or correspondence not eligible",
            "Development fees, donation, and building fund are NOT eligible — only tuition fee",
            "Combined with insurance premium within the ₹1.5L ceiling — not separate",
        ],
        "disqualification_conditions": [
            "Tuition fees for more than 2 children — excess not eligible",
            "Fees paid to foreign institutions — not eligible",
            "Spouse's tuition fees are not eligible under this provision",
        ],
        "examples": [
            "Tuition fee ₹80,000 (2 children) + LIC premium ₹70,000 = ₹1,50,000 — fully utilised 80C",
            "Tuition fee ₹1,00,000 + LIC premium ₹80,000 = ₹1,80,000 but cap is ₹1,50,000",
        ],
        "key_traps": [
            "Families with 2 children in private schools often exhaust 80C entirely on tuition fees — insurance premium may give zero additional tax benefit",
            "Must plan 80C basket early in the year to avoid overpaying insurance premiums for no tax gain",
        ],
        "fy_applicable": "2024-25",
        "relevant_products": ["life_term", "life_endowment", "ulip"],
    },
    {
        "section": "80C",
        "subsection": "housing_loan_principal",
        "title": "Section 80C — Home Loan Principal Repayment Competes with Insurance",
        "max_deduction": 150000,
        "max_deduction_formatted": "₹1,50,000 (shared limit)",
        "applicable_to": ["individual", "HUF"],
        "regime": "old_tax_regime_only",
        "tax_saving_at_30pct_bracket": 46800,
        "conditions": [
            "Principal repayment of home loan on a residential house qualifies under 80C",
            "Stamp duty and registration fees for house purchase also count in 80C (in the year of payment)",
            "Most salaried individuals with a home loan exhaust the ₹1.5L 80C limit on principal alone",
            "Deduction reversal: if property is sold within 5 years of possession, entire 80C deduction claimed is reversed",
        ],
        "disqualification_conditions": [
            "Interest component of home loan — NOT under 80C; deductible separately under Section 24(b)",
            "Home loan for commercial property — not eligible under 80C",
            "Pre-construction interest — not under 80C",
        ],
        "examples": [
            "Home loan EMI ₹30,000/month: principal portion ₹12,000 × 12 = ₹1,44,000 — almost fills ₹1.5L 80C limit",
            "Salaried with home loan: often leaves only ₹6,000-10,000 room for insurance premium in 80C",
        ],
        "key_traps": [
            "Most home loan borrowers have no room for insurance premium in 80C — insurance agent may not reveal this",
            "Buying life insurance under 80C when 80C is already exhausted by home loan gives ZERO tax benefit",
        ],
        "fy_applicable": "2024-25",
        "relevant_products": ["life_term", "life_endowment", "life_savings", "ulip"],
    },

    # ── New Tax Regime Implications ────────────────────────────────────────────

    {
        "section": "new_tax_regime",
        "subsection": "insurance_deductions_not_available",
        "title": "New Tax Regime (115BAC) — 80C, 80D, 80CCC Not Available",
        "max_deduction": 0,
        "max_deduction_formatted": "₹0 — no deductions for insurance under new regime",
        "applicable_to": ["individual"],
        "regime": "new_regime_only",
        "tax_saving_at_30pct_bracket": 0,
        "conditions": [
            "New tax regime is the DEFAULT for salaried individuals from FY 2024-25",
            "Under Section 115BAC: Sections 80C, 80D, 80CCC, 80CCD(1B) are NOT available",
            "Standard deduction of ₹75,000 is available under new regime (from FY 2024-25)",
            "NPS employer contribution under 80CCD(2) IS available under new regime",
            "Taxpayer must opt OUT explicitly to use old regime and claim insurance deductions",
        ],
        "disqualification_conditions": [
            "Insurance premium paid by a new regime taxpayer gives NO tax deduction",
            "Preventive health check-up sub-limit also not available under new regime",
        ],
        "examples": [
            "Salaried person defaults to new regime FY 2024-25: ₹25,000 health premium paid — ₹0 deduction",
            "Same person opts out to old regime: ₹25,000 health premium — ₹25,000 deduction under 80D",
            "Person in 30% bracket: switching to old regime saves ₹7,800 in tax just from health insurance",
        ],
        "key_traps": [
            "Most salaried individuals are now defaulted to new regime by employers — insurance tax benefits are lost unless they explicitly opt out",
            "Insurance agents selling policies as 'tax-saving' must clarify this only applies under old regime",
            "Break-even analysis needed: new regime lower slab rates vs old regime deductions",
        ],
        "fy_applicable": "2024-25",
        "relevant_products": ["health_individual", "life_term", "life_endowment", "ulip", "annuity"],
    },
    {
        "section": "new_tax_regime",
        "subsection": "nps_deduction_80CCD2",
        "title": "Section 80CCD(2) — Only Insurance-Adjacent Deduction Available in New Regime",
        "max_deduction": None,
        "max_deduction_formatted": "14% of salary (govt employees) or 10% of salary (others)",
        "applicable_to": ["individual"],
        "regime": "both_regimes",
        "tax_saving_at_30pct_bracket": None,
        "conditions": [
            "Employer's contribution to NPS (Tier I) for the employee is deductible under 80CCD(2)",
            "This deduction IS available under new tax regime — unlike 80C/80D",
            "For government employees: up to 14% of (basic + DA)",
            "For non-government employees: up to 10% of (basic + DA)",
            "Deduction is from employer's contribution, not employee's own contribution",
        ],
        "disqualification_conditions": [
            "Employee's own NPS contribution (80CCD(1) and 80CCD(1B)): NOT available in new regime",
            "Tier II NPS contributions: not eligible under any section",
        ],
        "examples": [
            "Salary ₹10L basic + DA: employer contributes 10% = ₹1L to NPS — ₹1L deductible even under new regime",
            "Government employee salary ₹8L: employer 14% NPS = ₹1.12L — deductible under new regime",
        ],
        "key_traps": [
            "80CCD(2) requires employer to contribute to NPS — most private sector employers do not offer this",
            "NPS maturity: 40% must be annuitised and annuity is fully taxable income",
        ],
        "fy_applicable": "2024-25",
        "relevant_products": ["nps", "annuity"],
    },

    # ── Section 10 — Additional Exemptions ────────────────────────────────────

    {
        "section": "10(10D)",
        "subsection": "life_insurance_maturity_exemption_conditions",
        "title": "Section 10(10D) — Premium-to-Sum-Assured Ratio Determines Taxability",
        "max_deduction": None,
        "max_deduction_formatted": "Exempt — no upper limit if conditions met",
        "applicable_to": ["individual", "HUF"],
        "regime": "both_regimes",
        "tax_saving_at_30pct_bracket": None,
        "conditions": [
            "Pre-April 2012 policies: premium must be <= 20% of sum assured for maturity to be exempt",
            "Post-April 2012 policies: premium must be <= 10% of sum assured for maturity to be exempt",
            "Disability/critical illness policies (80U/80DDB): premium can be up to 15% of SA",
            "Death benefit is ALWAYS 100% exempt — no premium-to-SA ratio check applies",
            "Partial surrender proceeds: treated proportionately for exemption",
        ],
        "disqualification_conditions": [
            "If premium exceeds the applicable ratio (10% or 20%): ENTIRE maturity is taxable, not just excess",
            "Keyman insurance: maturity is always taxable regardless of premium-to-SA ratio",
            "High-premium endowment policies commonly sold by LIC agents may breach the 10% rule",
        ],
        "examples": [
            "Policy (2015): SA ₹10L, annual premium ₹90,000 (9% of SA) — EXEMPT on maturity",
            "Policy (2015): SA ₹10L, annual premium ₹1,10,000 (11% of SA) — TAXABLE; TDS at 5% on income portion",
            "Policy (2010, pre-2012): SA ₹5L, annual premium ₹80,000 (16% of SA) < 20% — EXEMPT",
        ],
        "key_traps": [
            "Agents selling high-premium endowment plans often do not explain that maturity may be fully taxable if premium exceeds 10% of SA",
            "TDS at 5% is deducted by insurer automatically on non-exempt maturity payments",
        ],
        "fy_applicable": "2024-25",
        "relevant_products": ["life_endowment", "life_money_back", "life_savings"],
    },
    {
        "section": "10(10D)",
        "subsection": "key_man_insurance",
        "title": "10(10D) — Key Man Insurance: Death Benefit to Company is Taxable Business Income",
        "max_deduction": None,
        "max_deduction_formatted": "NA — taxability rule, no deduction",
        "applicable_to": ["company", "LLP", "firm"],
        "regime": "both_regimes",
        "tax_saving_at_30pct_bracket": None,
        "conditions": [
            "Key Man Insurance: company insures a key employee's life, company is the proposer and beneficiary",
            "Premium paid by company: deductible as business expense under Section 37(1)",
            "Death/maturity proceeds received by COMPANY: taxable as business income (not exempt under 10(10D))",
            "Section 10(10D) individual exemption does NOT apply to company-owned policies",
            "If key man policy is subsequently assigned to employee: proceeds in employee's hands may be taxable",
        ],
        "disqualification_conditions": [
            "Company cannot claim 10(10D) exemption — it applies only to individuals",
            "Surrender value received by company is also taxable income",
        ],
        "examples": [
            "Company buys ₹2Cr term on CEO's life: premium ₹2L/year deducted as expense. CEO dies: ₹2Cr received — taxable as company's business income",
            "Company reassigns key man policy to employee on retirement: employee's maturity proceeds taxable",
        ],
        "key_traps": [
            "Companies sometimes expect key man insurance payout to be tax-free — it is not",
            "Premium deductibility (37(1)) must be weighed against taxability of proceeds at company's tax rate",
        ],
        "fy_applicable": "2024-25",
        "relevant_products": ["life_term", "life_endowment"],
    },
    {
        "section": "10(23AAB)",
        "subsection": "superannuation_fund",
        "title": "Section 10(23AAB) — Approved Superannuation Fund: Premium Fully Exempt",
        "max_deduction": None,
        "max_deduction_formatted": "Employer contribution up to ₹1,50,000 per employee per year exempt",
        "applicable_to": ["individual"],
        "regime": "both_regimes",
        "tax_saving_at_30pct_bracket": None,
        "conditions": [
            "Life insurance premium paid to an IRDA-approved and income-tax-approved superannuation fund",
            "Employer-funded superannuation: employer contribution exempt from perquisite tax up to ₹1.5L per year per employee",
            "Income earned by the fund is fully exempt under 10(23AAB)",
            "On retirement: up to 1/3rd of corpus can be commuted tax-free; balance annuity is taxable",
            "Different from 80CCC (which is individual contribution to pension plan of insurer)",
        ],
        "disqualification_conditions": [
            "Superannuation fund not approved by income tax authorities: income not exempt",
            "Employer contribution exceeding ₹1.5L/year becomes taxable perquisite for employee",
            "Premature withdrawal before retirement (other than death/disability): taxable",
        ],
        "examples": [
            "Employer contributes ₹1.2L to LIC superannuation fund per year: fully exempt — not a perquisite for employee",
            "Employer contributes ₹2L/year: ₹1.5L exempt, ₹50,000 is taxable perquisite",
        ],
        "key_traps": [
            "Superannuation fund is often confused with NPS — different rules apply",
            "Annuity received post-retirement from superannuation is taxable as salary",
        ],
        "fy_applicable": "2024-25",
        "relevant_products": ["pension", "annuity"],
    },

    # ── Section 80CCE — Aggregate Limit ───────────────────────────────────────

    {
        "section": "80CCE",
        "subsection": "aggregate_limit_80C_80CCC_80CCD1",
        "title": "Section 80CCE — Combined Ceiling: 80C + 80CCC + 80CCD(1) = ₹1,50,000",
        "max_deduction": 150000,
        "max_deduction_formatted": "₹1,50,000 (aggregate of 80C + 80CCC + 80CCD(1))",
        "applicable_to": ["individual"],
        "regime": "old_tax_regime_only",
        "tax_saving_at_30pct_bracket": 46800,
        "conditions": [
            "80CCE imposes a combined cap of ₹1.5L on the sum of deductions under 80C + 80CCC + 80CCD(1)",
            "These three sections cannot each give ₹1.5L — the TOTAL is ₹1.5L",
            "Section 80CCD(1B): additional ₹50,000 for own NPS contribution — this is OUTSIDE and ABOVE the ₹1.5L cap",
            "Section 80CCD(2): employer NPS contribution — also outside the ₹1.5L cap",
            "Maximum possible: ₹1.5L (80CCE bucket) + ₹50,000 (80CCD(1B)) = ₹2L in total NPS+insurance space",
        ],
        "disqualification_conditions": [
            "New tax regime: 80CCE and all its components are not available",
            "Investing ₹1.5L in each of 80C, 80CCC, 80CCD(1) separately still gives only ₹1.5L total deduction",
        ],
        "examples": [
            "80C: ₹1,00,000 (LIC premium) + 80CCC: ₹30,000 (pension plan) + 80CCD(1): ₹20,000 (NPS) = ₹1,50,000 total under 80CCE",
            "If you also contribute ₹50,000 to NPS under 80CCD(1B): total deduction = ₹2,00,000",
        ],
        "key_traps": [
            "Agents selling both pension plans (80CCC) and life insurance (80C) may not explain the combined cap — both products compete for the same ₹1.5L",
            "Tax brochures listing each section's ₹1.5L limit imply additive benefits — this is misleading",
        ],
        "fy_applicable": "2024-25",
        "relevant_products": ["life_term", "life_endowment", "life_savings", "ulip", "annuity", "pension", "nps"],
    },

    # ── GST on Insurance — Detailed Rates ─────────────────────────────────────

    {
        "section": "GST",
        "subsection": "health_insurance_premium_18pct",
        "title": "GST on Health Insurance Premium — 18% (Full Amount Deductible Under 80D)",
        "max_deduction": 50000,
        "max_deduction_formatted": "₹50,000 (senior citizen; ₹25,000 for others) — GST-inclusive",
        "applicable_to": ["individual"],
        "regime": "old_tax_regime_only",
        "tax_saving_at_30pct_bracket": 15600,
        "conditions": [
            "GST on health insurance premium: 18% on all health insurance premiums",
            "The total premium paid including GST is eligible for deduction under 80D",
            "Example: ₹10,000 base premium + ₹1,800 GST = ₹11,800 — entire ₹11,800 is within 80D limit",
            "IRDAI has clarified: GST component of health premium is included in the 80D deductible amount",
            "Motor insurance GST: 18% — but motor insurance premium is NOT deductible under 80D",
        ],
        "disqualification_conditions": [
            "GST itself is not separately 'deducted' — it is part of the premium amount that is deductible",
            "If premium exceeds the 80D limit (₹25,000 or ₹50,000): GST portion of excess is also not deductible",
        ],
        "examples": [
            "Self health premium: base ₹21,186 + 18% GST ₹3,814 = ₹25,000 total — deduct full ₹25,000 under 80D",
            "Senior citizen premium: base ₹42,373 + 18% GST ₹7,627 = ₹50,000 total — deduct full ₹50,000",
        ],
        "key_traps": [
            "Some advisors incorrectly say only the net-of-GST premium is deductible — the GST-inclusive total qualifies",
            "18% GST significantly increases the effective cost of health insurance — factor this in when comparing premiums",
        ],
        "fy_applicable": "2024-25",
        "relevant_products": ["health_individual", "health_family_floater", "senior_citizen_health", "super_top_up"],
    },
    {
        "section": "GST",
        "subsection": "life_insurance_premium_rates",
        "title": "GST on Life Insurance — Differentiated Rates by Policy Type",
        "max_deduction": None,
        "max_deduction_formatted": "NA — cost impact, not a deduction",
        "applicable_to": ["individual"],
        "regime": "both_regimes",
        "tax_saving_at_30pct_bracket": None,
        "conditions": [
            "Pure term life insurance (risk only): 18% GST on entire premium",
            "Endowment/money back/savings plans (traditional): 4.5% GST on first-year premium; 2.25% on renewal premiums",
            "LIC traditional plans (participating): same 4.5%/2.25% concessional rate",
            "ULIPs: 18% GST on all charges (mortality, fund management, policy admin) — not on fund value",
            "Single premium policies: 1.8% GST on first-year single premium for savings-linked plans",
        ],
        "disqualification_conditions": [],
        "examples": [
            "Term premium ₹12,000: add 18% GST = ₹14,160 total payment (GST = ₹2,160)",
            "LIC Jeevan Anand premium ₹30,000 (Year 1): 4.5% GST = ₹1,350 → ₹31,350 total",
            "LIC Jeevan Anand premium ₹30,000 (Year 2+): 2.25% GST = ₹675 → ₹30,675 total",
            "ULIP annual charges ₹8,000: 18% GST = ₹9,440 total charges",
        ],
        "key_traps": [
            "Agents quote term premium exclusive of GST — actual outgo is 18% higher",
            "Traditional policy GST jumps from 2.25% (renewal) to 4.5% if premium is paid via offset or restructuring",
        ],
        "fy_applicable": "2024-25",
        "relevant_products": ["life_term", "life_endowment", "life_money_back", "life_savings", "ulip"],
    },
    {
        "section": "GST",
        "subsection": "annuity_pension_premium",
        "title": "GST on Annuity/Pension Products — Exempt from GST",
        "max_deduction": None,
        "max_deduction_formatted": "NA — GST exemption on pension/annuity",
        "applicable_to": ["individual"],
        "regime": "both_regimes",
        "tax_saving_at_30pct_bracket": None,
        "conditions": [
            "Pure pension/annuity products with no life insurance cover component: GST exempt under Schedule II",
            "Immediate annuity plans (e.g., LIC Jeevan Akshay): no GST on purchase price",
            "Deferred annuity plans (pure pension): no GST",
            "If the plan has a life insurance component (return of purchase price on death): may attract GST on the insurance element",
        ],
        "disqualification_conditions": [
            "ULIP-based pension plans with insurance charges: the charge component attracts 18% GST",
            "Plans that combine term cover + annuity: GST applicable on the insurance premium portion",
        ],
        "examples": [
            "LIC Jeevan Akshay VI (immediate annuity): purchase price ₹10L — no GST",
            "HDFC Life annuity plan (pure): ₹5L purchase — no GST",
        ],
        "key_traps": [
            "Zero GST on annuity purchase makes pension products slightly more cost-efficient vs insurance",
            "But annuity payout is fully taxable income — the GST saving upfront is offset by taxes on payout",
        ],
        "fy_applicable": "2024-25",
        "relevant_products": ["annuity", "pension"],
    },

    # ── Business and Property Insurance Tax Rules ──────────────────────────────

    {
        "section": "37(1)",
        "subsection": "business_insurance_deductible_expense",
        "title": "Section 37(1) — Business Insurance Premiums: Deductible as Business Expense",
        "max_deduction": None,
        "max_deduction_formatted": "No limit — full premium deductible as business expense",
        "applicable_to": ["company", "LLP", "firm"],
        "regime": "both_regimes",
        "tax_saving_at_30pct_bracket": None,
        "conditions": [
            "All insurance premiums paid wholly and exclusively for business purposes are deductible under 37(1)",
            "Eligible policies: fire insurance, marine insurance, professional indemnity, employee group health, key man, product liability, D&O",
            "NOT subject to the 80C/80D limits — these are separate business expense deductions",
            "Employer's group health insurance for employees: deductible as salary expense (also business deduction)",
            "Motor insurance for business vehicles: deductible as vehicle operating expense",
        ],
        "disqualification_conditions": [
            "Insurance premium with personal benefit component: only business-use proportion deductible",
            "Life insurance where company is NOT the beneficiary: personal benefit — not deductible under 37(1)",
            "Penalty, fines, or insurance for illegal activities: not deductible",
        ],
        "examples": [
            "IT company pays ₹5L for professional indemnity (PI) insurance: ₹5L deductible as business expense",
            "Manufacturing company pays ₹2L for fire insurance on factory: fully deductible under 37(1)",
            "Startup pays ₹3L for D&O (directors and officers) insurance: deductible",
            "Employer pays ₹50L group health premium for 200 employees: fully deductible",
        ],
        "key_traps": [
            "Key man insurance premium IS deductible by company under 37(1), but death/maturity proceeds are taxable income — net tax position must be evaluated",
            "Motor insurance for a car used partly for business: only the business-use fraction is deductible",
        ],
        "fy_applicable": "2024-25",
        "relevant_products": ["group_health", "professional_indemnity", "marine", "fire", "motor"],
    },
    {
        "section": "24(b)",
        "subsection": "home_loan_insurance",
        "title": "Section 24(b) — Home Loan Protection Insurance: Deductibility Treatment",
        "max_deduction": 200000,
        "max_deduction_formatted": "₹2,00,000 (within 24(b) interest deduction limit — if bundled with loan)",
        "applicable_to": ["individual"],
        "regime": "old_tax_regime_only",
        "tax_saving_at_30pct_bracket": 62400,
        "conditions": [
            "Home loan protection insurance (HLPP/mortgage insurance): if premium is bundled into loan and paid as part of EMI — deductible under Section 24(b) along with interest, within ₹2L limit",
            "If HLPP premium is paid separately as a standalone insurance policy (life policy on borrower securing the loan): may qualify under 80C within ₹1.5L limit",
            "The ₹2L deduction under 24(b) is for interest on self-occupied property — bundled insurance premium forms part of this",
            "Let-out property: no limit on interest deduction under 24(b) (only adjusted against rental income)",
        ],
        "disqualification_conditions": [
            "New tax regime: 24(b) self-occupied property interest deduction is NOT available",
            "HLPP premium for investment/rental property: different treatment",
        ],
        "examples": [
            "Home loan: bank bundles HLPP premium into EMI. Annual interest ₹1,80,000 + HLPP ₹20,000 = ₹2,00,000 — deduct full ₹2L under 24(b)",
            "Borrower separately buys term insurance assigning it to bank: premium ₹15,000 eligible under 80C",
        ],
        "key_traps": [
            "Banks often force-sell single-premium HLPP — the premium can be significant but tax treatment depends on structuring",
            "Under new regime: 24(b) self-occupied interest deduction is gone — HLPP bundled in loan gives no tax benefit",
        ],
        "fy_applicable": "2024-25",
        "relevant_products": ["life_term", "home_loan_protection"],
    },

    # ── Section 80GG — Rent Deduction ─────────────────────────────────────────

    {
        "section": "80GG",
        "subsection": "rent_vs_insurance_priority",
        "title": "Section 80GG — Rent Deduction (No HRA): Planning Priority vs. 80D",
        "max_deduction": 60000,
        "max_deduction_formatted": "₹60,000/year (₹5,000/month maximum)",
        "applicable_to": ["individual"],
        "regime": "old_tax_regime_only",
        "tax_saving_at_30pct_bracket": 18720,
        "conditions": [
            "For individuals who do NOT receive House Rent Allowance (HRA) from employer",
            "Self-employed professionals and freelancers commonly use 80GG",
            "Deduction is lowest of: (a) rent paid minus 10% of total income, (b) 25% of total income, (c) ₹5,000/month",
            "Taxpayer (or spouse/minor child) must NOT own a house at the place of employment",
            "Form 10BA must be filed declaring that no other house is owned",
        ],
        "disqualification_conditions": [
            "If you own a house in the city where you work: not eligible for 80GG",
            "If employer provides HRA (even partially): 80GG not available",
            "New tax regime: 80GG is not available",
        ],
        "examples": [
            "Self-employed consultant pays ₹15,000/month rent, no HRA: 80GG = min(₹15,000-10% income cap, 25% income cap, ₹5,000) = ₹5,000/month = ₹60,000/year",
            "Total income ₹8L: 10% = ₹80,000; annual rent ₹1.8L; 1.8L - 0.8L = ₹1L; 25% of ₹8L = ₹2L; ₹60,000/year cap wins",
        ],
        "key_traps": [
            "80GG and 80D both available in old regime — self-employed individuals can claim both; combined tax saving significant",
            "The ₹5,000/month cap (₹60,000/year) has not been revised in years — in high-rent cities it provides limited relief",
        ],
        "fy_applicable": "2024-25",
        "relevant_products": ["health_individual", "health_family_floater"],
    },

    # ── Critical Illness, Disability, Medical Treatment ───────────────────────

    {
        "section": "80DDB",
        "subsection": "critical_illness_treatment_deduction",
        "title": "Section 80DDB — Critical Illness Medical Treatment Deduction",
        "max_deduction": 100000,
        "max_deduction_formatted": "₹1,00,000 (age 60+) or ₹40,000 (age below 60)",
        "applicable_to": ["individual", "HUF"],
        "regime": "old_tax_regime_only",
        "tax_saving_at_30pct_bracket": 31200,
        "conditions": [
            "Deduction for actual medical treatment expenditure for specified diseases",
            "Specified diseases: cancer, renal failure requiring dialysis, haematological disorders (thalassaemia, haemophilia), neurological diseases (dementia, dystonia, motor neuron, ataxia, chorea, Parkinson's, aphasia), AIDS",
            "For self or dependent family members (spouse, children, parents, siblings)",
            "If insurance claim covers the expense: deduction reduced by the insurance reimbursement received",
            "Age < 60: max ₹40,000; Age 60+: max ₹1,00,000",
            "Certificate from specialist doctor in government hospital required",
        ],
        "disqualification_conditions": [
            "New tax regime: 80DDB deduction not available",
            "General hospitalisation — only specified diseases qualify",
            "No certificate from specialist: claim disallowed",
        ],
        "examples": [
            "Policyholder age 55 with cancer treatment: actual expense ₹60,000, insurance paid ₹30,000 — deductible: min(₹40,000, ₹60,000 - ₹30,000) = ₹30,000",
            "Taxpayer's father (age 65) on dialysis: expense ₹1.2L, insurance paid ₹0 — deductible ₹1,00,000 (cap for senior)",
        ],
        "key_traps": [
            "80DDB deduction is reduced by insurance claim amount — having health insurance does NOT block this deduction if there is a shortfall",
            "This deduction and 80D insurance premium deduction can BOTH be claimed simultaneously — they are different sections",
            "Specialist doctor certificate from government hospital is mandatory — private hospital specialists do not qualify for the certificate requirement",
        ],
        "fy_applicable": "2024-25",
        "relevant_products": ["health_individual", "critical_illness", "cancer_insurance"],
    },
    {
        "section": "80U",
        "subsection": "disability_higher_sa_condition",
        "title": "Section 80U — Person with Disability: Higher Premium-to-SA Ratio for 80C",
        "max_deduction": 150000,
        "max_deduction_formatted": "₹1,50,000 (severe disability) or ₹75,000 (disability) — fixed amounts",
        "applicable_to": ["individual"],
        "regime": "old_tax_regime_only",
        "tax_saving_at_30pct_bracket": 46800,
        "conditions": [
            "Flat deduction for individual with disability: ₹75,000 (disability 40%+ certified) or ₹1,50,000 (severe disability 80%+)",
            "Disability must be certified by a specified medical authority",
            "Insurance premium for a person with disability (Section 80U/80DD conditions): under 80C, premium can be up to 15% of sum assured (vs 10% for non-disabled individuals)",
            "The 15% ratio makes policies for disabled persons with relatively higher premiums still eligible for 80C",
            "Section 80DD: separate deduction for expenditure on dependent with disability (up to ₹75,000 or ₹1,25,000 for severe)",
        ],
        "disqualification_conditions": [
            "New tax regime: 80U deduction not available",
            "Disability must be as per Section 2(i) of Persons with Disabilities Act or as specified",
        ],
        "examples": [
            "Person with severe disability (80%+): claims flat ₹1,50,000 under 80U (no expense proof needed)",
            "Insurance policy for disabled person: SA ₹10L, premium ₹1,40,000 (14% of SA) — eligible under 80C because of 15% relaxation for disability",
        ],
        "key_traps": [
            "80U is a FLAT deduction — not linked to any expenditure. Medical certificate is all that's needed",
            "80U (self disability) and 80DD (dependent disability) are separate — both can be claimed if eligible",
        ],
        "fy_applicable": "2024-25",
        "relevant_products": ["life_term", "life_endowment", "life_savings"],
    },

    # ── Surrender and Annuity Taxation ────────────────────────────────────────

    {
        "section": "income_from_other_sources",
        "subsection": "ulip_surrender_taxation",
        "title": "ULIP Surrender Before 5 Years: 80C Deduction Reversed + Proceeds Taxable",
        "max_deduction": None,
        "max_deduction_formatted": "NA — adverse tax consequence on surrender",
        "applicable_to": ["individual"],
        "regime": "both_regimes",
        "tax_saving_at_30pct_bracket": None,
        "conditions": [
            "ULIP surrendered before 5 years from inception: 80C deductions claimed in all previous years are REVERSED — added back as income in the year of surrender",
            "Surrender proceeds also become taxable as income from other sources in the year of receipt",
            "After 5 years: if annual premium <= ₹2.5L (post-Feb-2021 ULIP), maturity is exempt under 10(10D)",
            "After 5 years: if annual premium > ₹2.5L (post-Feb-2021 ULIP), gains taxed as equity LTCG at 10% above ₹1L exemption",
            "Pre-Feb-2021 ULIPs: after 5 years, maturity remains fully exempt regardless of premium amount",
        ],
        "disqualification_conditions": [
            "Lock-in: ULIP cannot be surrendered before 5 years (only partial withdrawal possible after 5th year in some plans)",
        ],
        "examples": [
            "ULIP started 2020 (pre-Feb-2021), surrendered at 4 years: 80C claimed for 4 years reversed + surrender value taxable",
            "ULIP started March 2022, premium ₹1.5L/year, surrendered after 5 years: annual premium ≤ ₹2.5L → exempt",
            "ULIP started March 2022, premium ₹3L/year, maturity at 10 years: gains taxed at 10% LTCG (equity treatment)",
        ],
        "key_traps": [
            "Many ULIP investors are unaware that early surrender triggers TWO tax hits: deduction reversal + taxable proceeds",
            "The 5-year ULIP lock-in is regulatory — agents sometimes suggest partial withdrawal after 5th year which has different implications",
        ],
        "fy_applicable": "2024-25",
        "relevant_products": ["ulip"],
    },
    {
        "section": "income_from_other_sources",
        "subsection": "annuity_payout_fully_taxable",
        "title": "Annuity Payouts are Fully Taxable — No Cost Basis Offset",
        "max_deduction": None,
        "max_deduction_formatted": "NA — taxability rule",
        "applicable_to": ["individual"],
        "regime": "both_regimes",
        "tax_saving_at_30pct_bracket": None,
        "conditions": [
            "All annuity payouts from pension plans, NPS annuity, LIC Jeevan Akshay, and deferred annuity plans are FULLY taxable as income from other sources",
            "The purchase price was deducted under 80CCC or 80CCD in earlier years — so there is no remaining cost basis on receipt",
            "Annuity is taxed at the recipient's applicable income tax slab in the year of receipt",
            "Monthly, quarterly, or annual annuity income: all taxable regardless of frequency",
            "Even if the annuity is a 'return of purchase price + interest' structure: the entire payout is taxable",
        ],
        "disqualification_conditions": [
            "Commutation of pension: up to 1/3rd of NPS corpus at maturity is exempt from tax; the mandatory 40% annuity portion's payout is taxable",
        ],
        "examples": [
            "LIC Jeevan Akshay: purchase price ₹10L, annual annuity ₹72,000 — all ₹72,000 is taxable income each year",
            "NPS annuity: ₹5L used to buy annuity (mandatory 40% of corpus), monthly annuity ₹3,500 = ₹42,000/year — fully taxable",
            "Deferred pension plan matures, policyholder receives ₹8,000/month annuity: ₹96,000/year added to income",
        ],
        "key_traps": [
            "Retirees often assume annuity income is tax-free because they 'already paid tax' — the deduction was taken earlier, so payout is taxed fully now",
            "Annuity income pushes some retirees into higher tax slabs — plan annuity size against expected retirement income",
            "If senior citizen has total income (including annuity) above ₹3L (old regime) or ₹3L (new regime basic exemption): income tax applies",
        ],
        "fy_applicable": "2024-25",
        "relevant_products": ["annuity", "pension", "nps"],
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
