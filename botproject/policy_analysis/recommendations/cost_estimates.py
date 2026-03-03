"""
Static cost estimate database for policy upgrade recommendations.

Provides approximate annual cost estimates for common insurance add-ons,
upgrades, and improvements across all 5 insurance types.

Values are indicative ranges based on Indian insurance market (2024-25).
Actual costs vary by insurer, age, location, vehicle, and other factors.
"""

# ==================== HEALTH INSURANCE COST ESTIMATES ====================

HEALTH_COSTS = {
    # Feature ID → {title, annual cost range, description}
    "room_rent": {
        "title": "Upgrade to No Room Rent Cap",
        "annualCostLow": 2000,
        "annualCostHigh": 5000,
        "description": "Switch to a plan with no room rent capping to avoid proportional deductions during claims.",
    },
    "copay": {
        "title": "Reduce/Remove Co-payment",
        "annualCostLow": 1500,
        "annualCostHigh": 4000,
        "description": "Choose a plan variant with 0% co-pay to get 100% claim coverage.",
    },
    "sum_insured": {
        "title": "Increase Sum Insured",
        "annualCostLow": 3000,
        "annualCostHigh": 8000,
        "description": "Increase SI to ₹10-25 lakhs. Alternatively, add a super top-up for cost-effective coverage boost.",
    },
    "restoration": {
        "title": "Add Restoration Benefit",
        "annualCostLow": 1000,
        "annualCostHigh": 3000,
        "description": "Get a plan with restoration benefit so your SI is restored after a claim in the same year.",
    },
    "pec_waiting": {
        "title": "Choose Shorter PEC Waiting",
        "annualCostLow": 2000,
        "annualCostHigh": 6000,
        "description": "Some plans offer 24-month PEC waiting vs standard 36-48 months. Premium may be slightly higher.",
    },
    "ncb": {
        "title": "Switch to Higher NCB Plan",
        "annualCostLow": 0,
        "annualCostHigh": 1000,
        "description": "Choose a plan offering 50%+ NCB to accumulate higher coverage over claim-free years.",
    },
    "day_care": {
        "title": "Ensure Day Care Coverage",
        "annualCostLow": 500,
        "annualCostHigh": 1500,
        "description": "Switch to a plan covering day care procedures (cataract, dialysis, chemotherapy, etc.).",
    },
    "pre_post_hosp": {
        "title": "Add Pre/Post Hospitalization",
        "annualCostLow": 500,
        "annualCostHigh": 2000,
        "description": "Ensure both pre (30-60 days) and post (60-180 days) hospitalization expenses are covered.",
    },
    "ayush": {
        "title": "Add AYUSH Coverage",
        "annualCostLow": 300,
        "annualCostHigh": 1000,
        "description": "Most modern plans include AYUSH. Switch if your current plan doesn't cover it.",
    },
    "ambulance": {
        "title": "Add Ambulance Cover",
        "annualCostLow": 200,
        "annualCostHigh": 500,
        "description": "Ensure ambulance expenses are covered in your plan.",
    },
    "network_hospitals": {
        "title": "Switch to Larger Network Insurer",
        "annualCostLow": 0,
        "annualCostHigh": 2000,
        "description": "Consider an insurer with 10,000+ network hospitals for easier cashless access.",
    },
    "modern_treatments": {
        "title": "Ensure Modern Treatment Coverage",
        "annualCostLow": 500,
        "annualCostHigh": 2000,
        "description": "Switch to a plan covering modern treatments (robotic surgery, stem cell therapy, etc.).",
    },
    "mental_health": {
        "title": "Add Mental Health Coverage",
        "annualCostLow": 300,
        "annualCostHigh": 1500,
        "description": "IRDAI mandates mental health coverage. Ensure your plan includes it.",
    },
}

# ==================== MOTOR INSURANCE COST ESTIMATES ====================

MOTOR_COSTS = {
    "zero_dep": {
        "title": "Add Zero Depreciation Cover",
        "annualCostLow": 1500,
        "annualCostHigh": 4000,
        "description": "Most valuable motor add-on. Get full claim without depreciation deduction on parts.",
    },
    "engine_protection": {
        "title": "Add Engine Protection Cover",
        "annualCostLow": 800,
        "annualCostHigh": 2500,
        "description": "Covers engine damage from water ingression, oil leakage. Essential in flood-prone areas.",
    },
    "ncb_protection": {
        "title": "Add NCB Protection",
        "annualCostLow": 500,
        "annualCostHigh": 1500,
        "description": "Protect your accumulated NCB discount even after making a claim.",
    },
    "rsa": {
        "title": "Add Roadside Assistance",
        "annualCostLow": 300,
        "annualCostHigh": 800,
        "description": "24/7 roadside assistance for towing, flat tyre, battery issues, fuel delivery.",
    },
    "consumables": {
        "title": "Add Consumables Cover",
        "annualCostLow": 400,
        "annualCostHigh": 1200,
        "description": "Covers nut, bolt, screw, oil, grease, AC gas charges during repairs.",
    },
    "pa_cover": {
        "title": "Increase PA Cover to ₹15L",
        "annualCostLow": 200,
        "annualCostHigh": 750,
        "description": "IRDAI mandates ₹15 lakhs PA cover for owner-driver. Mandatory compliance.",
    },
    "product_type": {
        "title": "Upgrade to Comprehensive Cover",
        "annualCostLow": 5000,
        "annualCostHigh": 15000,
        "description": "Add OD cover to your TP-only policy for complete vehicle protection.",
    },
    "deductible": {
        "title": "Reduce Voluntary Deductible",
        "annualCostLow": 500,
        "annualCostHigh": 2000,
        "description": "Lower your deductible to reduce out-of-pocket expenses during claims.",
    },
    "rti": {
        "title": "Add Return to Invoice Cover",
        "annualCostLow": 600,
        "annualCostHigh": 2000,
        "description": "Get invoice value (not depreciated IDV) in case of total loss or theft.",
    },
    "tyre_cover": {
        "title": "Add Tyre Damage Cover",
        "annualCostLow": 300,
        "annualCostHigh": 1000,
        "description": "Covers tyre damage from cuts, bursts, and accidental damage.",
    },
    "idv": {
        "title": "Increase IDV to Market Value",
        "annualCostLow": 1000,
        "annualCostHigh": 3000,
        "description": "Request IDV increase to match current market value for adequate total loss compensation.",
    },
}

# ==================== LIFE INSURANCE COST ESTIMATES ====================

LIFE_COSTS = {
    "sum_assured": {
        "title": "Increase Sum Assured",
        "annualCostLow": 3000,
        "annualCostHigh": 12000,
        "description": "Increase life cover to at least 10-15x annual income. Term plans offer the best rates.",
    },
    "policy_term": {
        "title": "Extend Policy Term",
        "annualCostLow": 1000,
        "annualCostHigh": 5000,
        "description": "Extend coverage until retirement age (60-65) for continuous protection.",
    },
    "riders": {
        "title": "Add Critical Illness / Accidental Death Rider",
        "annualCostLow": 1500,
        "annualCostHigh": 5000,
        "description": "Add riders for critical illness, accidental death, and waiver of premium.",
    },
    "nominees": {
        "title": "Designate a Nominee",
        "annualCostLow": 0,
        "annualCostHigh": 0,
        "description": "Designate a nominee immediately. No cost, just a form submission to your insurer.",
    },
    "csr": {
        "title": "Consider Insurer with Higher CSR",
        "annualCostLow": 0,
        "annualCostHigh": 3000,
        "description": "At next renewal, consider an insurer with CSR above 98% for life insurance.",
    },
    "death_benefit": {
        "title": "Ensure Adequate Death Benefit",
        "annualCostLow": 1000,
        "annualCostHigh": 5000,
        "description": "Ensure death benefit equals or exceeds Sum Assured for adequate family protection.",
    },
    "surrender_value": {
        "title": "Check Surrender Value Terms",
        "annualCostLow": 0,
        "annualCostHigh": 0,
        "description": "Review surrender value terms. No additional cost — contact insurer for current value.",
    },
}

# ==================== PA INSURANCE COST ESTIMATES ====================

PA_COSTS = {
    "sum_insured": {
        "title": "Increase PA Sum Insured",
        "annualCostLow": 500,
        "annualCostHigh": 3000,
        "description": "Increase PA cover to at least ₹25-50 lakhs for adequate accident protection.",
    },
    "ptd": {
        "title": "Add Permanent Total Disability Cover",
        "annualCostLow": 300,
        "annualCostHigh": 1500,
        "description": "PTD coverage is essential — ensures financial support for permanent disabilities.",
    },
    "ppd": {
        "title": "Add Permanent Partial Disability Cover",
        "annualCostLow": 200,
        "annualCostHigh": 1000,
        "description": "PPD coverage compensates for partial disabilities based on a defined schedule.",
    },
    "ttd": {
        "title": "Add Temporary Total Disability Cover",
        "annualCostLow": 200,
        "annualCostHigh": 800,
        "description": "TTD provides weekly/monthly income replacement during temporary disability recovery.",
    },
    "medical_expenses": {
        "title": "Add Medical Expenses Coverage",
        "annualCostLow": 300,
        "annualCostHigh": 1200,
        "description": "Covers accident-related medical expenses separately from health insurance.",
    },
    "ad_benefit": {
        "title": "Upgrade to 100% AD Benefit",
        "annualCostLow": 200,
        "annualCostHigh": 800,
        "description": "Ensure accidental death benefit is 100% of Sum Insured.",
    },
    "education_benefit": {
        "title": "Add Education Benefit",
        "annualCostLow": 200,
        "annualCostHigh": 1000,
        "description": "Covers children's education expenses in case of accidental death/disability.",
    },
    "loan_emi": {
        "title": "Add Loan EMI Cover",
        "annualCostLow": 200,
        "annualCostHigh": 800,
        "description": "Ensures ongoing loan EMIs are protected in case of accidental death/disability.",
    },
    "occupation_restrictions": {
        "title": "Review Occupation Restrictions",
        "annualCostLow": 0,
        "annualCostHigh": 500,
        "description": "Check if your occupation is covered. Some plans have fewer restrictions.",
    },
}

# ==================== TRAVEL INSURANCE COST ESTIMATES ====================

TRAVEL_COSTS = {
    "medical_cover": {
        "title": "Increase Medical Cover",
        "annualCostLow": 500,
        "annualCostHigh": 3000,
        "description": "Increase medical cover to at least ₹50 lakhs / $50,000 for international travel.",
    },
    "ped": {
        "title": "Add Pre-Existing Disease Coverage",
        "annualCostLow": 500,
        "annualCostHigh": 2000,
        "description": "Choose a plan covering pre-existing conditions for travel emergencies.",
    },
    "trip_cancellation": {
        "title": "Add Trip Cancellation Cover",
        "annualCostLow": 300,
        "annualCostHigh": 1500,
        "description": "Protects non-refundable flight/hotel costs if you need to cancel.",
    },
    "evacuation": {
        "title": "Add Emergency Evacuation",
        "annualCostLow": 200,
        "annualCostHigh": 1000,
        "description": "Critical for remote destinations — evacuation costs can exceed ₹50 lakhs.",
    },
    "baggage": {
        "title": "Add Baggage Protection",
        "annualCostLow": 100,
        "annualCostHigh": 500,
        "description": "Covers baggage loss and delay compensation.",
    },
    "personal_liability": {
        "title": "Add Personal Liability Cover",
        "annualCostLow": 200,
        "annualCostHigh": 800,
        "description": "Protection against third-party injury/damage claims abroad.",
    },
    "adventure_sports": {
        "title": "Add Adventure Sports Coverage",
        "annualCostLow": 300,
        "annualCostHigh": 1500,
        "description": "If planning adventure activities, ensure they're covered.",
    },
    "deductible": {
        "title": "Reduce Per-Claim Deductible",
        "annualCostLow": 200,
        "annualCostHigh": 800,
        "description": "Choose a plan with lower or no deductible per claim.",
    },
    "trip_interruption": {
        "title": "Add Trip Interruption Cover",
        "annualCostLow": 200,
        "annualCostHigh": 800,
        "description": "Covers additional expenses if your trip is interrupted and you need to return early.",
    },
    "flight_delay": {
        "title": "Add Flight Delay Cover",
        "annualCostLow": 100,
        "annualCostHigh": 400,
        "description": "Covers expenses during extended flight delays (meals, accommodation).",
    },
    "cashless_network": {
        "title": "Choose Plan with Cashless Network",
        "annualCostLow": 200,
        "annualCostHigh": 1000,
        "description": "Select a plan with cashless hospital network abroad for hassle-free treatment.",
    },
}

# ==================== ROUTER ====================

COST_DB = {
    "health": HEALTH_COSTS,
    "motor": MOTOR_COSTS,
    "life": LIFE_COSTS,
    "pa": PA_COSTS,
    "travel": TRAVEL_COSTS,
}


def get_cost_estimate(category: str, feature_id: str) -> dict | None:
    """Look up cost estimate for a feature upgrade."""
    type_costs = COST_DB.get(category, {})
    return type_costs.get(feature_id)
