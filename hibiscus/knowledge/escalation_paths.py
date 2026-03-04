"""
Hibiscus v0.9 | EAZR AI Insurance Intelligence Engine
Shared escalation paths — single source of truth for claims_guide and grievance_navigator.
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
"""
from typing import Any, Dict, List

# Complete grievance escalation ladder — referenced by both ClaimsGuide and GrievanceNavigator.
ESCALATION_LADDER: List[Dict[str, Any]] = [
    {
        "level": 1,
        "name": "Internal Grievance — Insurer's GRO",
        "applicable_when": "First step — mandatory before approaching IRDAI or Ombudsman",
        "timeline": "Insurer must respond within 15 days (IRDAI mandate)",
        "cost": "Free",
        "how_to": [
            "Write a formal grievance letter to the insurer's Grievance Redressal Officer (GRO)",
            "Include: Policy number, nature of complaint, documents, expected resolution",
            "Send via: Registered post + email (keep tracking number and email timestamps)",
            "Also file through insurer's app/website grievance portal",
            "Get a written acknowledgment with reference number — this is your evidence",
        ],
        "contact": "Find GRO contact at insurer's website -> Customer Service -> Grievance Redressal",
        "escalation_trigger": "No response in 15 days OR unsatisfactory response",
        "irdai_reference": "IRDAI (Protection of Policyholders' Interests) Regulations 2017 — Regulation 13",
    },
    {
        "level": 2,
        "name": "IRDAI Bima Bharosa Portal",
        "applicable_when": "Insurer did not respond in 15 days, OR response is unsatisfactory",
        "timeline": "IRDAI forwards to insurer; insurer must resolve within 15 days",
        "cost": "Free",
        "how_to": [
            "Visit: bimabharosaportal.irdai.gov.in",
            "Register/login with your email or mobile",
            "Select 'Register Complaint' -> choose insurer -> fill complaint details",
            "Attach: Insurer's response (if any), your original documents, correspondence",
            "Note your complaint reference number",
            "IRDAI tracks resolution and intervenes if insurer does not respond",
        ],
        "contact": "bimabharosaportal.irdai.gov.in | IRDAI helpline: 155255 or 1800-4254-732",
        "escalation_trigger": "Not resolved within 30 days of IRDAI complaint",
        "irdai_reference": "IRDAI IGMS — Integrated Grievance Management System",
    },
    {
        "level": 3,
        "name": "Insurance Ombudsman",
        "applicable_when": [
            "Insurer rejected/ignored the complaint",
            "Within 3 months of insurer's final rejection letter",
            "Claim amount up to ₹50 lakh",
        ],
        "timeline": "Ombudsman must pass award within 3 months of receiving complete documents",
        "cost": "Completely FREE — no fees, no lawyers required",
        "how_to": [
            "Identify the Ombudsman office for your state (list at irdai.gov.in)",
            "Download the complaint form from irdai.gov.in/ombudsman",
            "Fill form and submit with all documents",
            "You can appear in person or submit written arguments",
            "Ombudsman holds hearings and passes a binding award",
            "Insurer must comply with award within 30 days",
        ],
        "contact": "17 offices across India — contact by state (see below)",
        "escalation_trigger": "Unhappy with ombudsman award, or claim above ₹50L",
        "irdai_reference": "Insurance Ombudsman Rules 2017",
        "important_note": "DO NOT exceed 3 months from insurer rejection — you lose the right to approach ombudsman",
    },
    {
        "level": 4,
        "name": "Consumer Forum",
        "applicable_when": "Claims above ₹50 lakh, or if ombudsman approach is not suitable",
        "timeline": "Variable — typically 6-18 months",
        "cost": "Small filing fee; lawyers recommended for complex cases",
        "how_to": [
            "DCDRC (District Consumer Disputes Redressal Commission): Claims up to ₹1 crore",
            "SCDRC (State Consumer Disputes Redressal Commission): Claims ₹1 crore to ₹10 crore",
            "NCDRC (National Consumer Disputes Redressal Commission): Claims above ₹10 crore",
            "Consumer complaint under Consumer Protection Act 2019",
            "Insurer can be held liable for deficiency in service",
        ],
        "contact": "consumerhelpline.gov.in | edaakhil.nic.in (online filing)",
        "escalation_trigger": "Dissatisfied with forum order",
        "irdai_reference": "Consumer Protection Act 2019",
    },
    {
        "level": 5,
        "name": "Civil Court",
        "applicable_when": "Last resort when all other remedies exhausted",
        "timeline": "2-10 years typically",
        "cost": "Filing fees + lawyer fees — significant",
        "how_to": [
            "Consult a lawyer with insurance litigation experience",
            "File civil suit in appropriate court",
        ],
        "contact": "Local civil court / High Court",
        "escalation_trigger": "Final option",
        "irdai_reference": "Code of Civil Procedure 1908",
    },
]

# Compact version used in claims_guide.py for claim_rejection process
CLAIM_REJECTION_ESCALATION_LADDER: List[str] = [
    f"Level {step['level']}: {step['name']} — {step['timeline']}"
    for step in ESCALATION_LADDER
]
