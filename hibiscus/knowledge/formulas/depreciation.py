"""
🌺 Hibiscus v0.9 | EAZR AI Insurance Intelligence Engine
Motor insurance depreciation formulas — IDV computation, part-wise depreciation, salvage value.
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
"""
from dataclasses import dataclass
from typing import Optional


# ── IRDAI IDV Depreciation Schedule ────────────────────────────────────────────
# VERIFY: approximate schedule — needs verification against current IRDAI motor circular

IDV_DEPRECIATION_BY_AGE = {
    # vehicle_age_months_max: depreciation_percentage
    6: 5,       # Less than 6 months: 5%
    12: 15,     # 6-12 months: 15%
    24: 20,     # 1-2 years: 20%
    36: 30,     # 2-3 years: 30%
    48: 40,     # 3-4 years: 40%
    60: 50,     # 4-5 years: 50%
}
# Beyond 5 years: IDV by mutual agreement (typically 55-70% depreciation)


# ── Part-wise Depreciation (for non-zero-dep claims) ──────────────────────────
# VERIFY: approximate — needs verification against IRDAI depreciation schedule

PART_DEPRECIATION = {
    "rubber_nylon_plastic": 50,     # Rubber, nylon, plastic parts: 50%
    "tyres_tubes": 50,              # Tyres and tubes: 50%
    "batteries": 50,                # Batteries: 50%
    "air_bags": 50,                 # Air bags: 50%
    "fiberglass": 30,               # Fiberglass components: 30%
    "windshield_glass": 0,          # Windshield glass: 0% (first claim)
    "metal_body_new": 0,            # Metal body (new vehicle <1yr): 0%
    "metal_body_1_5yr": 5,          # Metal body (1-5 years): 5%
    "metal_body_5_10yr": 10,        # Metal body (5-10 years): 10%
    "metal_body_10yr_plus": 15,     # Metal body (10+ years): 15%
}


def compute_idv(
    ex_showroom_price: float,
    vehicle_age_months: int,
    accessories_value: float = 0,
) -> float:
    """
    Compute Insured Declared Value (IDV) for a vehicle.

    IDV = (Ex-Showroom Price - Depreciation) + Accessories Value (depreciated)

    Args:
        ex_showroom_price: Original ex-showroom price in INR
        vehicle_age_months: Vehicle age in months from registration
        accessories_value: Value of non-factory-fitted accessories

    Returns:
        IDV in INR
    """
    if ex_showroom_price <= 0:
        raise ValueError("ex_showroom_price must be > 0")
    if vehicle_age_months < 0:
        raise ValueError("vehicle_age_months must be >= 0")

    # Find applicable depreciation rate
    depreciation_pct = 0
    if vehicle_age_months > 60:
        # Beyond 5 years: mutual agreement, estimate 55%
        depreciation_pct = 55
    else:
        for age_limit, pct in sorted(IDV_DEPRECIATION_BY_AGE.items()):
            if vehicle_age_months <= age_limit:
                depreciation_pct = pct
                break

    vehicle_idv = ex_showroom_price * (1 - depreciation_pct / 100)
    accessories_idv = accessories_value * (1 - depreciation_pct / 100)

    return round(vehicle_idv + accessories_idv)


def compute_claim_depreciation(
    part_type: str,
    replacement_cost: float,
) -> dict:
    """
    Compute depreciation deduction on a vehicle part for a non-zero-dep claim.

    Args:
        part_type: Key from PART_DEPRECIATION dict
        replacement_cost: Cost of replacing the part in INR

    Returns:
        Dict with depreciation_pct, deduction, and net_payable
    """
    if part_type not in PART_DEPRECIATION:
        raise ValueError(f"Unknown part type: {part_type}. Valid: {list(PART_DEPRECIATION.keys())}")

    dep_pct = PART_DEPRECIATION[part_type]
    deduction = replacement_cost * dep_pct / 100
    net_payable = replacement_cost - deduction

    return {
        "part_type": part_type,
        "replacement_cost": round(replacement_cost),
        "depreciation_pct": dep_pct,
        "depreciation_deduction": round(deduction),
        "net_payable_by_insurer": round(net_payable),
    }


@dataclass
class ClaimDepreciationBreakdown:
    """Full depreciation breakdown for a motor insurance claim."""

    parts: list
    total_replacement_cost: float = 0
    total_depreciation: float = 0
    total_payable: float = 0
    compulsory_deductible: float = 0  # ₹1,000 for private cars
    voluntary_deductible: float = 0
    net_claim_amount: float = 0

    def add_part(self, part_type: str, cost: float) -> None:
        """Add a damaged part to the claim breakdown."""
        result = compute_claim_depreciation(part_type, cost)
        self.parts.append(result)
        self.total_replacement_cost += result["replacement_cost"]
        self.total_depreciation += result["depreciation_deduction"]
        self.total_payable += result["net_payable_by_insurer"]

    def finalize(
        self, compulsory_deductible: float = 1000, voluntary_deductible: float = 0
    ) -> dict:
        """Compute final claim amount after deductibles."""
        self.compulsory_deductible = compulsory_deductible
        self.voluntary_deductible = voluntary_deductible
        self.net_claim_amount = max(
            0, self.total_payable - compulsory_deductible - voluntary_deductible
        )
        return {
            "parts": self.parts,
            "total_replacement_cost": round(self.total_replacement_cost),
            "total_depreciation": round(self.total_depreciation),
            "amount_after_depreciation": round(self.total_payable),
            "compulsory_deductible": round(self.compulsory_deductible),
            "voluntary_deductible": round(self.voluntary_deductible),
            "net_claim_amount": round(self.net_claim_amount),
        }


def estimate_salvage_value(
    idv: float,
    damage_percentage: float,
) -> dict:
    """
    Estimate salvage value for a total loss / constructive total loss claim.

    A vehicle is typically declared total loss when repair cost > 75% of IDV.

    Args:
        idv: Insured Declared Value
        damage_percentage: Estimated damage as percentage of IDV (0-100)

    Returns:
        Dict with total_loss flag, salvage estimate, and claim amount
    """
    is_total_loss = damage_percentage >= 75
    # Salvage is typically 3-8% of IDV for total loss
    salvage_pct = 5 if is_total_loss else 0
    salvage_value = idv * salvage_pct / 100
    claim_amount = idv - salvage_value if is_total_loss else idv * damage_percentage / 100

    return {
        "idv": round(idv),
        "damage_percentage": damage_percentage,
        "is_total_loss": is_total_loss,
        "salvage_value": round(salvage_value),
        "claim_amount": round(claim_amount),
        "note": (
            "Total loss: insurer pays IDV minus salvage"
            if is_total_loss
            else "Partial damage: insurer pays repair cost minus depreciation and deductible"
        ),
    }


# ── NCB (No Claim Bonus) Computation ─────────────────────────────────────────

NCB_SLABS = {
    0: 0,    # No claim-free year: 0%
    1: 20,   # 1 claim-free year: 20%
    2: 25,   # 2 years: 25%
    3: 35,   # 3 years: 35%
    4: 45,   # 4 years: 45%
    5: 50,   # 5+ years: 50% (max)
}


def compute_ncb_discount(
    od_premium: float,
    claim_free_years: int,
) -> dict:
    """
    Compute NCB discount on OD premium.

    Args:
        od_premium: Own Damage premium before NCB
        claim_free_years: Number of consecutive claim-free years

    Returns:
        Dict with NCB percentage, discount amount, and net OD premium
    """
    years = min(claim_free_years, 5)  # Cap at 5 (50% max)
    ncb_pct = NCB_SLABS.get(years, 0)
    discount = od_premium * ncb_pct / 100

    return {
        "od_premium_before_ncb": round(od_premium),
        "claim_free_years": claim_free_years,
        "ncb_percentage": ncb_pct,
        "ncb_discount": round(discount),
        "od_premium_after_ncb": round(od_premium - discount),
    }
