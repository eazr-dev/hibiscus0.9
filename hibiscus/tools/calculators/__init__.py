"""
Insurance financial formula tools.
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
"""
from hibiscus.knowledge.formulas.surrender_value import calculate_gsv, calculate_surrender_projection
from hibiscus.knowledge.formulas.irr import compute_irr, compute_policy_irr, interpret_irr
from hibiscus.knowledge.formulas.tax_benefit import (
    compute_80c_benefit,
    compute_80d_benefit,
    check_10_10d_exemption,
    compute_total_tax_benefit,
)
from hibiscus.knowledge.formulas.inflation import inflate, real_coverage_needed, deflate, inflation_gap
from hibiscus.knowledge.formulas.compound_growth import fv_lumpsum, fv_annuity, pv, emi, cagr, doubling_years
from hibiscus.knowledge.formulas.premium_adequacy import (
    hlv_method,
    income_multiple_method,
    health_cover_needed,
    AdequacyResult,
)
from hibiscus.knowledge.formulas.emi import ipf_emi, svf_emi, EMIResult
from hibiscus.knowledge.formulas.opportunity_cost import endowment_vs_term_mf, OpportunityCostResult
from hibiscus.knowledge.formulas.eazr_score import calculate_eazr_score, EAZRScoreResult

__all__ = [
    # Surrender value
    "calculate_gsv",
    "calculate_surrender_projection",
    # IRR
    "compute_irr",
    "compute_policy_irr",
    "interpret_irr",
    # Tax benefit
    "compute_80c_benefit",
    "compute_80d_benefit",
    "check_10_10d_exemption",
    "compute_total_tax_benefit",
    # Inflation
    "inflate",
    "real_coverage_needed",
    "deflate",
    "inflation_gap",
    # Compound growth
    "fv_lumpsum",
    "fv_annuity",
    "pv",
    "emi",
    "cagr",
    "doubling_years",
    # Premium adequacy
    "hlv_method",
    "income_multiple_method",
    "health_cover_needed",
    "AdequacyResult",
    # EMI (IPF/SVF)
    "ipf_emi",
    "svf_emi",
    "EMIResult",
    # Opportunity cost
    "endowment_vs_term_mf",
    "OpportunityCostResult",
    # EAZR Score
    "calculate_eazr_score",
    "EAZRScoreResult",
]
