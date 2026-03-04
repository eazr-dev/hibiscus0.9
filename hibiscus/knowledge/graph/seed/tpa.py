"""
🌺 Hibiscus v0.9 | EAZR AI Insurance Intelligence Engine
TPA seed data — Third-Party Administrators for health insurance claims processing.
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.

Data sources:
- IRDAI list of registered TPAs (March 2026)
- Insurer websites and annual reports
- Network hospital aggregator data
"""
from typing import Any, Dict, List

from hibiscus.knowledge.graph.client import kg_client
from hibiscus.observability.logger import get_logger

logger = get_logger("hibiscus.kg.seed.tpa")

# ── TPA Master Data ──────────────────────────────────────────────────────────
# Major Indian TPAs with their insurer partnerships and service metrics.

TPA_DATA: List[Dict[str, Any]] = [
    {
        "name": "Medi Assist Healthcare Services",
        "type": "health_tpa",
        "headquarters": "Bengaluru",
        "network_size": 10500,
        "digital_score": 8.5,
        "avg_processing_days": 7,
        "cashless_approval_time_hours": 2,
        "website": "https://www.mediassist.in",
        "irdai_license": "TPA/2002/001",
        "insurer_partnerships": [
            "Star Health and Allied Insurance",
            "HDFC ERGO General Insurance",
            "Bajaj Allianz General Insurance",
            "ICICI Lombard General Insurance",
            "Niva Bupa Health Insurance",
            "ManipalCigna Health Insurance",
        ],
        "key_features": [
            "AI-powered claim adjudication",
            "Mobile app for cashless requests",
            "24x7 helpline",
            "E-claim submission",
        ],
    },
    {
        "name": "Paramount Health Services & Insurance TPA",
        "type": "health_tpa",
        "headquarters": "Mumbai",
        "network_size": 8200,
        "digital_score": 7.5,
        "avg_processing_days": 8,
        "cashless_approval_time_hours": 3,
        "website": "https://www.phsi.co.in",
        "irdai_license": "TPA/2002/002",
        "insurer_partnerships": [
            "Star Health and Allied Insurance",
            "The New India Assurance",
            "United India Insurance",
            "National Insurance Company",
            "Oriental Insurance Company",
        ],
        "key_features": [
            "Pan-India network",
            "Government insurer specialist",
            "PMJAY empaneled",
            "Multi-language support",
        ],
    },
    {
        "name": "Vidal Health Insurance TPA",
        "type": "health_tpa",
        "headquarters": "Mumbai",
        "network_size": 7800,
        "digital_score": 8.0,
        "avg_processing_days": 7,
        "cashless_approval_time_hours": 2,
        "website": "https://www.vidalhealth.com",
        "irdai_license": "TPA/2002/003",
        "insurer_partnerships": [
            "ICICI Lombard General Insurance",
            "Bajaj Allianz General Insurance",
            "TATA AIG General Insurance",
            "Cholamandalam MS General Insurance",
        ],
        "key_features": [
            "Digital-first claims platform",
            "WhatsApp claim tracking",
            "AI document verification",
            "Wellness programs",
        ],
    },
    {
        "name": "Health India Insurance TPA Services",
        "type": "health_tpa",
        "headquarters": "New Delhi",
        "network_size": 6500,
        "digital_score": 7.0,
        "avg_processing_days": 9,
        "cashless_approval_time_hours": 4,
        "website": "https://www.healthindiatpa.com",
        "irdai_license": "TPA/2002/004",
        "insurer_partnerships": [
            "The New India Assurance",
            "National Insurance Company",
            "United India Insurance",
            "Oriental Insurance Company",
            "IFFCO Tokio General Insurance",
        ],
        "key_features": [
            "Government scheme specialist",
            "Rural network coverage",
            "Ayushman Bharat empaneled",
            "Vernacular language support",
        ],
    },
    {
        "name": "MD India Health Insurance TPA",
        "type": "health_tpa",
        "headquarters": "Mumbai",
        "network_size": 9200,
        "digital_score": 7.8,
        "avg_processing_days": 8,
        "cashless_approval_time_hours": 3,
        "website": "https://www.maboraksha.com",
        "irdai_license": "TPA/2002/005",
        "insurer_partnerships": [
            "Star Health and Allied Insurance",
            "Bajaj Allianz General Insurance",
            "SBI General Insurance",
            "Aditya Birla Health Insurance",
        ],
        "key_features": [
            "Largest TPA by claim volume",
            "PMJAY largest processor",
            "AI fraud detection",
            "Real-time claim tracking",
        ],
    },
    {
        "name": "Heritage Health Insurance TPA",
        "type": "health_tpa",
        "headquarters": "Hyderabad",
        "network_size": 5500,
        "digital_score": 7.2,
        "avg_processing_days": 9,
        "cashless_approval_time_hours": 4,
        "website": "https://www.heritagehealthtpa.com",
        "irdai_license": "TPA/2003/006",
        "insurer_partnerships": [
            "The New India Assurance",
            "United India Insurance",
            "National Insurance Company",
            "IFFCO Tokio General Insurance",
        ],
        "key_features": [
            "South India specialist",
            "Telugu/Tamil/Kannada support",
            "Government scheme processing",
            "Hospital empanelment expertise",
        ],
    },
    {
        "name": "Family Health Plan Insurance TPA",
        "type": "health_tpa",
        "headquarters": "Hyderabad",
        "network_size": 6800,
        "digital_score": 7.0,
        "avg_processing_days": 10,
        "cashless_approval_time_hours": 4,
        "website": "https://www.fhpl.net",
        "irdai_license": "TPA/2002/007",
        "insurer_partnerships": [
            "United India Insurance",
            "National Insurance Company",
            "Oriental Insurance Company",
            "The New India Assurance",
        ],
        "key_features": [
            "PSU insurer specialist",
            "Government employee schemes",
            "Large rural network",
            "Offline claim support",
        ],
    },
    {
        "name": "Raksha Health Insurance TPA",
        "type": "health_tpa",
        "headquarters": "New Delhi",
        "network_size": 5000,
        "digital_score": 6.8,
        "avg_processing_days": 10,
        "cashless_approval_time_hours": 5,
        "website": "https://www.raboraksha.com",
        "irdai_license": "TPA/2003/008",
        "insurer_partnerships": [
            "National Insurance Company",
            "United India Insurance",
            "Oriental Insurance Company",
        ],
        "key_features": [
            "North India focus",
            "Hindi-medium support",
            "Government hospital network",
            "Tier-2/3 city coverage",
        ],
    },
    {
        "name": "Medsave Health Insurance TPA",
        "type": "health_tpa",
        "headquarters": "New Delhi",
        "network_size": 5800,
        "digital_score": 7.0,
        "avg_processing_days": 9,
        "cashless_approval_time_hours": 4,
        "website": "https://www.medsavesolutions.com",
        "irdai_license": "TPA/2002/009",
        "insurer_partnerships": [
            "The New India Assurance",
            "National Insurance Company",
            "SBI General Insurance",
        ],
        "key_features": [
            "Corporate group health specialist",
            "Employee wellness programs",
            "Pre-authorization automation",
            "Multi-city presence",
        ],
    },
    {
        "name": "Anant Health Care TPA",
        "type": "health_tpa",
        "headquarters": "Ahmedabad",
        "network_size": 4200,
        "digital_score": 6.5,
        "avg_processing_days": 11,
        "cashless_approval_time_hours": 5,
        "website": "https://www.ananthealthcare.com",
        "irdai_license": "TPA/2003/010",
        "insurer_partnerships": [
            "United India Insurance",
            "National Insurance Company",
            "Oriental Insurance Company",
        ],
        "key_features": [
            "Gujarat/Rajasthan focus",
            "Gujarati/Hindi support",
            "Small-town hospital network",
            "Personal claims assistance",
        ],
    },
    {
        "name": "Good Health Insurance TPA",
        "type": "health_tpa",
        "headquarters": "Chennai",
        "network_size": 4800,
        "digital_score": 7.0,
        "avg_processing_days": 9,
        "cashless_approval_time_hours": 4,
        "website": "https://www.goodhealthplan.com",
        "irdai_license": "TPA/2003/011",
        "insurer_partnerships": [
            "The New India Assurance",
            "United India Insurance",
            "Cholamandalam MS General Insurance",
        ],
        "key_features": [
            "Tamil Nadu/Kerala specialist",
            "Tamil language support",
            "Ayush treatment processing",
            "Senior citizen claim expertise",
        ],
    },
    {
        "name": "Park Mediclaim Insurance TPA",
        "type": "health_tpa",
        "headquarters": "Ahmedabad",
        "network_size": 4500,
        "digital_score": 6.8,
        "avg_processing_days": 10,
        "cashless_approval_time_hours": 4,
        "website": "https://www.parkmediclaim.com",
        "irdai_license": "TPA/2002/012",
        "insurer_partnerships": [
            "National Insurance Company",
            "Oriental Insurance Company",
            "United India Insurance",
        ],
        "key_features": [
            "Western India network",
            "SME group health specialist",
            "Quick reimbursement",
            "Dedicated relationship managers",
        ],
    },
]


async def seed_tpas() -> int:
    """
    Seed TPA nodes into Neo4j Knowledge Graph.

    Creates:
    - (:TPA) nodes with properties
    - (:Insurer)-[:USES_TPA]->(:TPA) relationships

    Returns:
        Number of TPA nodes created.
    """
    if not kg_client.is_connected:
        await kg_client.connect()
    if not kg_client.is_connected:
        logger.warning("tpa_seed_skipped", reason="Neo4j not connected")
        return 0

    created = 0

    for tpa in TPA_DATA:
        # Create TPA node
        partnerships = tpa.pop("insurer_partnerships", [])
        features = tpa.pop("key_features", [])

        try:
            await kg_client.execute_write(
                """
                MERGE (t:TPA {name: $name})
                SET t += $props,
                    t.key_features = $features,
                    t.updated_at = datetime()
                """,
                params={
                    "name": tpa["name"],
                    "props": {k: v for k, v in tpa.items() if k != "name"},
                    "features": features,
                },
                query_name="seed_tpa_node",
            )
            created += 1

            # Create USES_TPA relationships
            for insurer_name in partnerships:
                await kg_client.execute_write(
                    """
                    MATCH (i:Insurer)
                    WHERE toLower(i.name) CONTAINS toLower($insurer_partial)
                    WITH i LIMIT 1
                    MATCH (t:TPA {name: $tpa_name})
                    MERGE (i)-[:USES_TPA]->(t)
                    """,
                    params={
                        "insurer_partial": insurer_name.split(" ")[0],  # Match on first word
                        "tpa_name": tpa["name"],
                    },
                    query_name="seed_tpa_relationship",
                )

        except Exception as exc:
            logger.warning(
                "tpa_seed_error",
                tpa_name=tpa["name"],
                error=str(exc),
            )

    logger.info("tpa_seed_complete", tpas_created=created, total=len(TPA_DATA))
    return created
