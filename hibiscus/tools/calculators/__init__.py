"""Insurance financial formula tools."""
from hibiscus.knowledge.formulas.surrender_value import calculate_gsv, calculate_surrender_projection
from hibiscus.knowledge.formulas.irr import compute_irr, compute_policy_irr, interpret_irr
from hibiscus.knowledge.formulas.tax_benefit import (
    compute_80c_benefit,
    compute_80d_benefit,
    check_10_10d_exemption,
    compute_total_tax_benefit,
)

__all__ = [
    "calculate_gsv",
    "calculate_surrender_projection",
    "compute_irr",
    "compute_policy_irr",
    "interpret_irr",
    "compute_80c_benefit",
    "compute_80d_benefit",
    "check_10_10d_exemption",
    "compute_total_tax_benefit",
]
