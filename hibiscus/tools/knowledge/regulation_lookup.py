"""
Tool: Regulation Lookup — Neo4j Knowledge Graph
================================================
Look up IRDAI regulations and policyholder rights from the KG.
Used by: RegulationEngine, GrievanceNavigator, Educator agents.

Functions
---------
lookup_regulation(topic)                    — find regulation by keyword
get_rights_for_situation(situation)         — get applicable rights/regs for a user situation
lookup_ombudsman_for_state(state)           — find ombudsman office by state
get_consumer_rights_summary()              — full list of key policyholder rights
search_regulations_by_category(category)   — all regulations in a category
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
"""
from typing import Any, Dict, List, Optional

from hibiscus.knowledge.graph.client import kg_client
from hibiscus.observability.logger import get_logger

logger = get_logger("hibiscus.tools.knowledge.regulation_lookup")

# Situation → regulation category mapping
# Used to find relevant regulations given a user situation
_SITUATION_TO_CATEGORIES = {
    "cancel_policy": ["free_look_period"],
    "free_look": ["free_look_period"],
    "port_policy": ["health_insurance_portability"],
    "portability": ["health_insurance_portability"],
    "claim_rejected": ["claim_settlement", "policyholder_protection", "ombudsman"],
    "claim_delayed": ["claim_settlement", "policyholder_protection"],
    "pre_existing_disease": ["health_insurance"],
    "ped_waiting_period": ["health_insurance"],
    "mis_selling": ["mis_selling", "free_look_period"],
    "ulip_charges": ["ulip"],
    "surrender": ["ulip", "policyholder_protection"],
    "premium_hike": ["health_insurance", "policyholder_protection"],
    "ombudsman_complaint": ["ombudsman", "grievance_redressal"],
    "grievance": ["grievance_redressal", "policyholder_protection"],
    "digital_policy": ["digital_insurance"],
    "mental_health": ["health_insurance"],
    "maternity": ["health_insurance"],
    "modern_treatment": ["health_insurance"],
    "cashless_denied": ["health_insurance", "claim_settlement"],
    "reimbursement": ["claim_settlement"],
    "tax_80d": [],   # handled by tax_rules, not regulations
    "tax_80c": [],
}

# Key consumer rights — used as fallback when KG is unavailable
_KEY_CONSUMER_RIGHTS = [
    {
        "right": "Free Look Period",
        "description": "Cancel any policy within 15 days (30 days for online purchases) and get full premium refund minus stamp duty and risk premium.",
        "applicable_to": "All policies",
        "regulation": "IRDAI Free Look Period Regulations 2014",
    },
    {
        "right": "Portability (Health)",
        "description": "Port your health insurance to any other insurer at renewal without losing waiting period credits.",
        "applicable_to": "Health insurance",
        "regulation": "IRDAI Health Insurance Portability Guidelines 2016",
    },
    {
        "right": "Lifelong Renewability",
        "description": "Health insurers cannot deny renewal based on age or claims history.",
        "applicable_to": "Health insurance",
        "regulation": "IRDAI (Health Insurance) Regulations 2016",
    },
    {
        "right": "30-Day Claim Settlement",
        "description": "Insurer must settle claims within 30 days of receiving all documents. Interest at 2% above bank rate if delayed.",
        "applicable_to": "All insurance",
        "regulation": "IRDAI (Protection of Policyholders' Interests) Regulations 2017",
    },
    {
        "right": "Cashless Within 1 Hour",
        "description": "Cashless pre-authorisation for planned hospitalisation must be given within 3 hours; for emergency within 1 hour.",
        "applicable_to": "Health insurance",
        "regulation": "IRDAI Master Circular on Health Insurance 2024",
    },
    {
        "right": "Moratorium Period (Health)",
        "description": "After 5 continuous years of health insurance, insurer cannot dispute any claim on grounds of pre-existing disease.",
        "applicable_to": "Health insurance",
        "regulation": "IRDAI (Health Insurance) Amendment Regulations 2024",
    },
    {
        "right": "Pre-Existing Disease Coverage",
        "description": "Pre-existing diseases must be covered after maximum 3 years waiting period (new policies from 2024).",
        "applicable_to": "Health insurance",
        "regulation": "IRDAI (Health Insurance) Amendment Regulations 2024",
    },
    {
        "right": "Insurance Ombudsman",
        "description": "File dispute up to ₹50 lakh with Insurance Ombudsman for free. Award within 3 months, binding on insurer.",
        "applicable_to": "All insurance",
        "regulation": "Insurance Ombudsman Rules 2017 (amended 2021)",
    },
    {
        "right": "Grievance Resolution",
        "description": "Insurer must acknowledge complaints within 3 working days and resolve within 14 days (non-claims) or 30 days (claims).",
        "applicable_to": "All insurance",
        "regulation": "IRDAI Grievance Redressal Regulations 2024",
    },
    {
        "right": "ULIP Charge Disclosure",
        "description": "All ULIP charges (fund management max 1.35%, allocation, admin) must be disclosed. Net yield must be shown.",
        "applicable_to": "ULIPs",
        "regulation": "IRDAI ULIP Disclosure Norms 2019",
    },
    {
        "right": "Digital Policy Storage",
        "description": "Store all your insurance policies digitally in a single eInsurance Account (eIA) via Bima Sugam.",
        "applicable_to": "All insurance",
        "regulation": "IRDAI Bima Sugam Regulations 2023",
    },
    {
        "right": "Mental Health Coverage",
        "description": "Health insurers must cover mental illness treatment as per Mental Healthcare Act 2017.",
        "applicable_to": "Health insurance",
        "regulation": "IRDAI (Health Insurance) Amendment Regulations 2024",
    },
]


async def lookup_regulation(topic: str) -> List[Dict[str, Any]]:
    """
    Find regulations matching a topic keyword.

    Searches against regulation subject, category, and key_requirements.

    Args:
        topic: Keyword or phrase (e.g. "free look", "portability", "claim settlement",
               "pre-existing", "ombudsman", "ULIP charges").

    Returns:
        List of matching regulation dicts (up to 5), ordered by relevance.
        Returns fallback data if KG unavailable.

    Example:
        regs = await lookup_regulation("free look period")
        regs = await lookup_regulation("portability")
    """
    if not topic or not topic.strip():
        return []

    if not kg_client.is_connected:
        await kg_client.connect()

    if not kg_client.is_connected:
        logger.warning("lookup_regulation_kg_unavailable", topic=topic)
        # Return filtered consumer rights as fallback
        topic_lower = topic.lower()
        fallback = [
            r for r in _KEY_CONSUMER_RIGHTS
            if topic_lower in r["right"].lower()
            or topic_lower in r["description"].lower()
            or topic_lower in r["regulation"].lower()
        ]
        return [{"subject": r["right"], "key_requirements": [r["description"]], "legislation_type": "consumer_right", "_fallback": True} for r in fallback[:3]]

    query = """
    MATCH (r:Regulation)
    WHERE toLower(r.subject) CONTAINS toLower($topic)
       OR toLower(r.category) CONTAINS toLower($topic)
       OR any(req IN r.key_requirements WHERE toLower(req) CONTAINS toLower($topic))
    RETURN r
    ORDER BY r.effective_date DESC
    LIMIT 5
    """
    try:
        results = await kg_client.query(
            query,
            params={"topic": topic.strip()},
            query_name="lookup_regulation",
        )
        regs = [dict(r["r"]) for r in results if "r" in r]
        logger.info("lookup_regulation_results", topic=topic, count=len(regs))
        return regs
    except Exception as exc:
        logger.warning("lookup_regulation_error", topic=topic, error=str(exc))
        return []


async def get_rights_for_situation(situation: str) -> Dict[str, Any]:
    """
    Get applicable regulations and consumer rights for a specific user situation.

    Args:
        situation: A situation keyword. Supported values:
          "cancel_policy", "free_look", "port_policy", "portability",
          "claim_rejected", "claim_delayed", "pre_existing_disease",
          "ped_waiting_period", "mis_selling", "ulip_charges", "surrender",
          "premium_hike", "ombudsman_complaint", "grievance",
          "digital_policy", "mental_health", "maternity", "modern_treatment",
          "cashless_denied", "reimbursement"

    Returns:
        Dict with:
          - situation: str
          - applicable_regulations: list of regulation dicts
          - consumer_rights: list of rights summaries
          - action_steps: list of recommended actions
          - important_timelines: dict of relevant deadlines
          - escalation_path: list of escalation steps

    Example:
        result = await get_rights_for_situation("claim_rejected")
    """
    situation_lower = situation.lower().strip()
    categories = _SITUATION_TO_CATEGORIES.get(situation_lower, [])

    # Fetch matching regulations from KG
    applicable_regs: List[Dict[str, Any]] = []
    if kg_client.is_connected or (await _try_connect()):
        for cat in categories:
            regs = await search_regulations_by_category(cat)
            applicable_regs.extend(regs)
    else:
        # Fallback: search consumer rights text
        applicable_regs = []

    # Get matching consumer rights from static fallback
    consumer_rights = _get_rights_for_situation_fallback(situation_lower)

    # Build action steps and timelines
    action_steps, timelines = _get_situation_guidance(situation_lower)

    return {
        "situation": situation,
        "applicable_regulations": applicable_regs[:5],
        "consumer_rights": consumer_rights,
        "action_steps": action_steps,
        "important_timelines": timelines,
        "escalation_path": _get_escalation_path(situation_lower),
    }


def _get_rights_for_situation_fallback(situation: str) -> List[Dict[str, Any]]:
    """Return relevant consumer rights from the static list for a situation."""
    situation_to_rights = {
        "cancel_policy": ["Free Look Period"],
        "free_look": ["Free Look Period"],
        "port_policy": ["Portability (Health)"],
        "portability": ["Portability (Health)", "Lifelong Renewability"],
        "claim_rejected": ["30-Day Claim Settlement", "Insurance Ombudsman", "Grievance Resolution"],
        "claim_delayed": ["30-Day Claim Settlement", "Grievance Resolution"],
        "pre_existing_disease": ["Pre-Existing Disease Coverage", "Moratorium Period (Health)"],
        "ped_waiting_period": ["Pre-Existing Disease Coverage", "Moratorium Period (Health)"],
        "mis_selling": ["Free Look Period", "ULIP Charge Disclosure"],
        "ulip_charges": ["ULIP Charge Disclosure"],
        "surrender": ["ULIP Charge Disclosure"],
        "premium_hike": ["Lifelong Renewability"],
        "ombudsman_complaint": ["Insurance Ombudsman"],
        "grievance": ["Grievance Resolution", "Insurance Ombudsman"],
        "cashless_denied": ["Cashless Within 1 Hour", "30-Day Claim Settlement"],
        "reimbursement": ["30-Day Claim Settlement"],
        "mental_health": ["Mental Health Coverage"],
        "digital_policy": ["Digital Policy Storage"],
    }
    applicable_right_names = situation_to_rights.get(situation, [])
    return [
        r for r in _KEY_CONSUMER_RIGHTS
        if r["right"] in applicable_right_names
    ]


def _get_situation_guidance(situation: str):
    """Return action steps and timelines for a given situation."""
    guidance = {
        "cancel_policy": (
            [
                "Check if you are within the free look period (15 days from policy receipt, 30 days for online)",
                "Write to the insurer requesting cancellation under free look period",
                "Keep proof of policy receipt date (courier receipt, email timestamp)",
                "Expect refund within 15 days minus stamp duty and proportionate risk premium",
            ],
            {"free_look_window": "15 days (offline), 30 days (online)", "refund_timeline": "15 days from cancellation request"},
        ),
        "claim_rejected": (
            [
                "Request written rejection letter with specific reason from insurer",
                "File complaint with insurer's Grievance Redressal Officer (GRO)",
                "If not resolved in 14-30 days, escalate to IRDAI Bima Bharosa portal",
                "File with Insurance Ombudsman within 1 year of insurer's final rejection",
                "Compile: policy document, rejection letter, all medical records, correspondence",
            ],
            {
                "insurer_grievance_deadline": "30 days (claims)",
                "ombudsman_filing_deadline": "1 year from insurer rejection",
                "ombudsman_award_timeline": "3 months from complaint",
            },
        ),
        "port_policy": (
            [
                "Initiate portability request at least 45 days before renewal date",
                "Contact new insurer — they cannot refuse your portability application without reason",
                "Ensure new insurer credits waiting periods already served with previous insurer",
                "You can increase sum insured at porting — waiting period applies only to incremental SI",
            ],
            {"portability_notice": "45 days before renewal", "new_insurer_response": "Mandatory acceptance"},
        ),
        "mis_selling": (
            [
                "Invoke free look period immediately (15/30 days from policy receipt)",
                "File complaint with insurer's GRO citing mis-selling with specifics",
                "File complaint on IRDAI Bima Bharosa portal",
                "If no resolution, approach Insurance Ombudsman",
                "Document: sales call recording (if available), agent's promises, what you were told",
            ],
            {"free_look_window": "15-30 days", "grievance_resolution": "14 days"},
        ),
        "cashless_denied": (
            [
                "Insurer must provide pre-authorisation within 1 hour (emergency) or 3 hours (planned)",
                "Ask hospital TPA desk for specific written reason for denial",
                "Call insurer helpline immediately — escalate to senior officer",
                "If denied, pay and file for reimbursement (keep all original bills)",
                "File complaint with insurer GRO within 24 hours",
            ],
            {"cashless_preauth_emergency": "1 hour", "cashless_preauth_planned": "3 hours", "reimbursement_settlement": "30 days"},
        ),
    }
    default = (
        ["Contact your insurer first with written complaint", "Keep record of all correspondence", "Escalate to IRDAI Bima Bharosa if not resolved"],
        {"grievance_resolution": "14-30 days", "ombudsman_option": "If insurer fails to resolve"},
    )
    return guidance.get(situation, default)


def _get_escalation_path(situation: str) -> List[str]:
    """Return the escalation hierarchy for a situation."""
    return [
        "Step 1: Raise complaint with insurer's customer service",
        "Step 2: Escalate to insurer's Grievance Redressal Officer (GRO)",
        "Step 3: Raise on IRDAI Bima Bharosa portal — https://bimabharosa.irdai.gov.in",
        "Step 4: File with Insurance Ombudsman (disputes up to ₹50 lakh, free, binding on insurer)",
        "Step 5: Consumer court or civil court for disputes not covered by Ombudsman",
    ]


async def _try_connect() -> bool:
    """Attempt to connect to KG. Returns True if successful."""
    await kg_client.connect()
    return kg_client.is_connected


async def lookup_ombudsman_for_state(state: str) -> Dict[str, Any]:
    """
    Find the Insurance Ombudsman office with jurisdiction over a given state.

    Args:
        state: Indian state name (e.g. "Maharashtra", "Kerala", "Tamil Nadu").

    Returns:
        Dict with ombudsman office details, or {} if not found.

    Example:
        office = await lookup_ombudsman_for_state("Kerala")
        # Returns: {"city": "Kochi", "email": "bimalokpal.ernakulam@cioins.co.in", ...}
    """
    if not state or not state.strip():
        return {}

    if not kg_client.is_connected:
        await kg_client.connect()
    if not kg_client.is_connected:
        logger.warning("lookup_ombudsman_kg_unavailable", state=state)
        return {}

    query = """
    MATCH (o:OmbudsmanOffice)
    WHERE any(s IN o.jurisdiction_states WHERE toLower(s) CONTAINS toLower($state))
       OR toLower(o.state) CONTAINS toLower($state)
    RETURN o
    LIMIT 1
    """
    try:
        results = await kg_client.query(
            query,
            params={"state": state.strip()},
            query_name="lookup_ombudsman_for_state",
        )
        if results and "o" in results[0]:
            data = dict(results[0]["o"])
            logger.info("lookup_ombudsman_hit", state=state, city=data.get("city"))
            return data
        logger.info("lookup_ombudsman_miss", state=state)
        return {}
    except Exception as exc:
        logger.warning("lookup_ombudsman_error", state=state, error=str(exc))
        return {}


async def get_consumer_rights_summary() -> List[Dict[str, Any]]:
    """
    Return a full summary of key consumer rights under Indian insurance law.

    Returns the static list of rights enriched with KG data where available.
    This is always available — does not require KG connectivity.

    Returns:
        List of consumer right dicts with keys:
          - right: str — right name
          - description: str — explanation
          - applicable_to: str
          - regulation: str — source regulation
    """
    return _KEY_CONSUMER_RIGHTS


async def search_regulations_by_category(category: str) -> List[Dict[str, Any]]:
    """
    Search all regulations in a given category, ordered by effective_date descending.

    Args:
        category: Regulation category (e.g. "health_insurance", "claim_settlement",
                  "free_look_period", "ombudsman", "ulip", "policyholder_protection",
                  "mis_selling", "digital_insurance").

    Returns:
        List of regulation dicts. Returns [] if KG unavailable.
    """
    if not kg_client.is_connected:
        await kg_client.connect()
    if not kg_client.is_connected:
        logger.warning("search_regulations_kg_unavailable", category=category)
        return []

    query = """
    MATCH (r:Regulation)
    WHERE r.category = $category
    RETURN r
    ORDER BY r.effective_date DESC
    """
    try:
        results = await kg_client.query(
            query,
            params={"category": category},
            query_name="search_regulations_by_category",
        )
        regs = [dict(r["r"]) for r in results if "r" in r]
        logger.info("search_regulations_by_category", category=category, count=len(regs))
        return regs
    except Exception as exc:
        logger.warning("search_regulations_by_category_error", category=category, error=str(exc))
        return []
