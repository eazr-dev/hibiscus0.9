# 🌺 Hibiscus v0.9 | EAZR AI Insurance Intelligence Engine
# Insurance formula modules — depreciation, premium, life cover, health SI, tax

from hibiscus.knowledge.formulas.depreciation import (
    IDV_DEPRECIATION_BY_AGE,
    PART_DEPRECIATION,
    NCB_SLABS,
    compute_idv,
    compute_claim_depreciation,
    compute_ncb_discount,
    estimate_salvage_value,
    ClaimDepreciationBreakdown,
)
