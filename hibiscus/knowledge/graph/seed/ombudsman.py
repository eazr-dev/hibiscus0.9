"""
🌺 Hibiscus v0.9 | EAZR AI Insurance Intelligence Engine
KG seed: ombudsman — 17 IRDAI ombudsman offices with jurisdiction mapping.
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
"""
from typing import Any, Dict, List

from hibiscus.knowledge.graph.client import Neo4jClient
from hibiscus.observability.logger import get_logger

logger = get_logger("hibiscus.kg.seed.ombudsman")


OMBUDSMAN_OFFICES: List[Dict[str, Any]] = [

    {
        "city": "Ahmedabad",
        "office_name": "Office of the Insurance Ombudsman, Ahmedabad",
        "jurisdiction_states": ["Gujarat", "Dadra and Nagar Haveli and Daman and Diu"],
        "address": (
            "Office of the Insurance Ombudsman, Jeevan Prakash Building, "
            "6th floor, Tilak Marg, Relief Road, Ahmedabad - 380 001"
        ),
        "phone": "079-25501201",
        "email": "bimalokpal.ahmedabad@cioins.co.in",
        "complaint_threshold_lakhs": 50,
        "time_limit_months": 12,
        "service_free": True,
        "award_timeline_months": 3,
    },
    {
        "city": "Bhopal",
        "office_name": "Office of the Insurance Ombudsman, Bhopal",
        "jurisdiction_states": ["Madhya Pradesh", "Chhattisgarh"],
        "address": (
            "Janak Vihar Complex, 2nd Floor, 6, Malviya Nagar, Opp. Airtel Office, "
            "Near New Market, Bhopal - 462 003"
        ),
        "phone": "0755-2769201/202",
        "email": "bimalokpal.bhopal@cioins.co.in",
        "complaint_threshold_lakhs": 50,
        "time_limit_months": 12,
        "service_free": True,
        "award_timeline_months": 3,
    },
    {
        "city": "Bhubaneswar",
        "office_name": "Office of the Insurance Ombudsman, Bhubaneswar",
        "jurisdiction_states": ["Odisha"],
        "address": (
            "62, Forest park, Bhubaneswar - 751 009"
        ),
        "phone": "0674-2596461/2596455",
        "email": "bimalokpal.bhubaneswar@cioins.co.in",
        "complaint_threshold_lakhs": 50,
        "time_limit_months": 12,
        "service_free": True,
        "award_timeline_months": 3,
    },
    {
        "city": "Chandigarh",
        "office_name": "Office of the Insurance Ombudsman, Chandigarh",
        "jurisdiction_states": ["Punjab", "Haryana", "Himachal Pradesh", "Jammu and Kashmir", "Chandigarh UT"],
        "address": (
            "S.C.O. No. 101, 102 & 103, 2nd Floor, Batra Building, Sector 17 – D, "
            "Chandigarh - 160 017"
        ),
        "phone": "0172-2706468/2705861",
        "email": "bimalokpal.chandigarh@cioins.co.in",
        "complaint_threshold_lakhs": 50,
        "time_limit_months": 12,
        "service_free": True,
        "award_timeline_months": 3,
    },
    {
        "city": "Chennai",
        "office_name": "Office of the Insurance Ombudsman, Chennai",
        "jurisdiction_states": ["Tamil Nadu", "Puducherry (except Yanam)"],
        "address": (
            "Fatima Akhtar Court, 4th Floor, 453 (old 312), Anna Salai, Teynampet, "
            "Chennai - 600 018"
        ),
        "phone": "044-24333668/24335284",
        "email": "bimalokpal.chennai@cioins.co.in",
        "complaint_threshold_lakhs": 50,
        "time_limit_months": 12,
        "service_free": True,
        "award_timeline_months": 3,
    },
    {
        "city": "Delhi",
        "office_name": "Office of the Insurance Ombudsman, Delhi",
        "jurisdiction_states": ["Delhi", "Rajasthan"],
        "address": (
            "2/2 A, Universal Insurance Building, Asaf Ali Road, New Delhi - 110 002"
        ),
        "phone": "011-23232481/23213504",
        "email": "bimalokpal.delhi@cioins.co.in",
        "complaint_threshold_lakhs": 50,
        "time_limit_months": 12,
        "service_free": True,
        "award_timeline_months": 3,
    },
    {
        "city": "Guwahati",
        "office_name": "Office of the Insurance Ombudsman, Guwahati",
        "jurisdiction_states": [
            "Assam", "Meghalaya", "Manipur", "Mizoram", "Arunachal Pradesh",
            "Nagaland", "Tripura",
        ],
        "address": (
            "Jeevan Nivesh, 5th Floor, Nr. Panbazar over bridge, S.S. Road, "
            "Guwahati - 781 001 (Assam)"
        ),
        "phone": "0361-2632204/2602205",
        "email": "bimalokpal.guwahati@cioins.co.in",
        "complaint_threshold_lakhs": 50,
        "time_limit_months": 12,
        "service_free": True,
        "award_timeline_months": 3,
    },
    {
        "city": "Hyderabad",
        "office_name": "Office of the Insurance Ombudsman, Hyderabad",
        "jurisdiction_states": ["Andhra Pradesh", "Telangana", "Yanam (Puducherry)"],
        "address": (
            "6-2-46, 1st floor, 'Moin Court', Lane Opp. Saleem Function Palace, "
            "A. C. Guards, Lakdi-Ka-Pool, Hyderabad - 500 004"
        ),
        "phone": "040-67504123/23312122",
        "email": "bimalokpal.hyderabad@cioins.co.in",
        "complaint_threshold_lakhs": 50,
        "time_limit_months": 12,
        "service_free": True,
        "award_timeline_months": 3,
    },
    {
        "city": "Jaipur",
        "office_name": "Office of the Insurance Ombudsman, Jaipur",
        "jurisdiction_states": ["Rajasthan (Jaipur region)"],
        "address": (
            "Jeevan Nidhi – II Bldg., Gr. Floor, Bhawani Singh Marg, Jaipur - 302 005"
        ),
        "phone": "0141-2740363",
        "email": "bimalokpal.jaipur@cioins.co.in",
        "complaint_threshold_lakhs": 50,
        "time_limit_months": 12,
        "service_free": True,
        "award_timeline_months": 3,
        "note": "Jaipur office has jurisdiction in parts of Rajasthan — check if Delhi office covers your district",
    },
    {
        "city": "Kochi",
        "office_name": "Office of the Insurance Ombudsman, Kochi",
        "jurisdiction_states": ["Kerala", "Lakshadweep", "Mahe (Puducherry)"],
        "address": (
            "2nd Floor, Pulinat Bldg., Opp. Cochin Shipyard, M.G. Road, "
            "Ernakulam, Kochi - 682 015"
        ),
        "phone": "0484-2358759/2359338",
        "email": "bimalokpal.ernakulam@cioins.co.in",
        "complaint_threshold_lakhs": 50,
        "time_limit_months": 12,
        "service_free": True,
        "award_timeline_months": 3,
    },
    {
        "city": "Kolkata",
        "office_name": "Office of the Insurance Ombudsman, Kolkata",
        "jurisdiction_states": ["West Bengal", "Sikkim", "Andaman and Nicobar Islands"],
        "address": (
            "Hindustan Bldg. Annexe, 4th Floor, 4, C.R. Avenue, Kolkata - 700 072"
        ),
        "phone": "033-22124339/22124340",
        "email": "bimalokpal.kolkata@cioins.co.in",
        "complaint_threshold_lakhs": 50,
        "time_limit_months": 12,
        "service_free": True,
        "award_timeline_months": 3,
    },
    {
        "city": "Lucknow",
        "office_name": "Office of the Insurance Ombudsman, Lucknow",
        "jurisdiction_states": ["Uttar Pradesh", "Uttarakhand"],
        "address": (
            "6th Floor, Jeevan Bhawan, Phase-II, Nawal Kishore Road, Hazratganj, "
            "Lucknow - 226 001"
        ),
        "phone": "0522-2231530/23231331",
        "email": "bimalokpal.lucknow@cioins.co.in",
        "complaint_threshold_lakhs": 50,
        "time_limit_months": 12,
        "service_free": True,
        "award_timeline_months": 3,
    },
    {
        "city": "Mumbai",
        "office_name": "Office of the Insurance Ombudsman, Mumbai",
        "jurisdiction_states": ["Maharashtra", "Goa (excluding Panaji and North Goa)"],
        "address": (
            "3rd Floor, Jeevan Seva Annexe, S.V. Road, Santacruz (W), Mumbai - 400 054"
        ),
        "phone": "022-69038821/23/24/25/26/27",
        "email": "bimalokpal.mumbai@cioins.co.in",
        "complaint_threshold_lakhs": 50,
        "time_limit_months": 12,
        "service_free": True,
        "award_timeline_months": 3,
    },
    {
        "city": "Noida",
        "office_name": "Office of the Insurance Ombudsman, Noida",
        "jurisdiction_states": ["Uttar Pradesh (NCR region)", "Uttarakhand (NCR region)"],
        "address": (
            "Bhagwan Sahai Palace 4th Floor, Main Road, Naya Bans, Sector 15, "
            "Distt: Gautam Buddh Nagar, U.P. - 201301"
        ),
        "phone": "0120-2514252/2514253",
        "email": "bimalokpal.noida@cioins.co.in",
        "complaint_threshold_lakhs": 50,
        "time_limit_months": 12,
        "service_free": True,
        "award_timeline_months": 3,
    },
    {
        "city": "Patna",
        "office_name": "Office of the Insurance Ombudsman, Patna",
        "jurisdiction_states": ["Bihar", "Jharkhand"],
        "address": (
            "1st Floor, Kalpana Arcade Building, Bazar Samiti Road, Bahadurpur, "
            "Patna - 800 006"
        ),
        "phone": "0612-2680952",
        "email": "bimalokpal.patna@cioins.co.in",
        "complaint_threshold_lakhs": 50,
        "time_limit_months": 12,
        "service_free": True,
        "award_timeline_months": 3,
    },
    {
        "city": "Pune",
        "office_name": "Office of the Insurance Ombudsman, Pune",
        "jurisdiction_states": ["Maharashtra (except areas under Mumbai jurisdiction)", "Goa (Panaji, North Goa)"],
        "address": (
            "Jeevan Darshan Bldg., 3rd Floor, C.T.S. No.s. 195 to 198, "
            "N.C. Kelkar Road, Narayan Peth, Pune - 411 030"
        ),
        "phone": "020-41312555",
        "email": "bimalokpal.pune@cioins.co.in",
        "complaint_threshold_lakhs": 50,
        "time_limit_months": 12,
        "service_free": True,
        "award_timeline_months": 3,
    },
    {
        "city": "Visakhapatnam",
        "office_name": "Office of the Insurance Ombudsman, Visakhapatnam",
        "jurisdiction_states": ["Andhra Pradesh (Northern districts)", "Odisha (parts)"],
        "address": (
            "Door No. 48-8-106, Muthyalammapalem, Visakhapatnam - 530 017"
        ),
        "phone": "0891-2706873",
        "email": "bimalokpal.visakhapatnam@cioins.co.in",
        "complaint_threshold_lakhs": 50,
        "time_limit_months": 12,
        "service_free": True,
        "award_timeline_months": 3,
    },
]

# ── How to File — Reference Data ──────────────────────────────────────────────

OMBUDSMAN_FILING_GUIDE = {
    "eligibility": [
        "Must have made a complaint to the insurer first",
        "Insurer rejected it OR did not respond within 30 days",
        "Complaint is within 1 year of insurer's final reply or 13 months from event",
        "Dispute amount must not exceed ₹50 lakh",
        "Not pending before another court, consumer forum, or arbitration",
    ],
    "documents_required": [
        "Complaint letter to the insurer (copy)",
        "Insurer's rejection letter or proof of no response",
        "Policy document",
        "Relevant medical/claim documents",
        "Government ID proof",
    ],
    "process": [
        "1. File complaint online at https://bimabharosa.irdai.gov.in or by post/in person",
        "2. Ombudsman acknowledges within 3 working days",
        "3. Mediation attempted between insurer and policyholder",
        "4. If no settlement, Ombudsman passes a final award within 3 months",
        "5. Award is binding on insurer — insurer must comply within 30 days",
        "6. If policyholder is unsatisfied with award, can reject within 30 days and approach consumer court",
    ],
    "irdai_bima_bharosa_portal": "https://bimabharosa.irdai.gov.in",
    "integrated_ombudsman_portal": "https://ecoi.co.in",
}


# ── Cypher ─────────────────────────────────────────────────────────────────────

_MERGE_OMBUDSMAN = """
MERGE (o:OmbudsmanOffice {city: $city})
SET
  o.office_name                  = $office_name,
  o.jurisdiction                 = $jurisdiction,
  o.address                      = $address,
  o.phone                        = $phone,
  o.email                        = $email,
  o.complaint_threshold_lakhs    = $complaint_threshold_lakhs,
  o.time_limit_months            = $time_limit_months,
  o.service_free                 = $service_free,
  o.award_timeline_months        = $award_timeline_months,
  o.updated_at                   = datetime()
RETURN o.city AS city
"""


async def seed_ombudsman(client: Neo4jClient) -> None:
    """
    MERGE all OmbudsmanOffice nodes into Neo4j. Idempotent — safe to re-run.
    """
    logger.info("seed_ombudsman_start", count=len(OMBUDSMAN_OFFICES))

    ombudsman_params = []
    for office in OMBUDSMAN_OFFICES:
        params = {
            "city": office["city"],
            "office_name": office["office_name"],
            # Store jurisdiction states as a pipe-separated string for Neo4j native storage
            "jurisdiction": " | ".join(office["jurisdiction_states"]),
            "address": office["address"],
            "phone": office["phone"],
            "email": office["email"],
            "complaint_threshold_lakhs": office["complaint_threshold_lakhs"],
            "time_limit_months": office["time_limit_months"],
            "service_free": office["service_free"],
            "award_timeline_months": office["award_timeline_months"],
        }
        ombudsman_params.append(params)

    succeeded = await client.execute_batch(
        _MERGE_OMBUDSMAN,
        param_list=ombudsman_params,
        query_name="seed_ombudsman",
    )
    logger.info("seed_ombudsman_complete", succeeded=succeeded, total=len(OMBUDSMAN_OFFICES))
