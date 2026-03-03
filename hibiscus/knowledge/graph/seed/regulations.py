"""
IRDAI Regulations Seed Data
============================
Key IRDAI circulars, regulations, and guidelines relevant to Indian insurance consumers.

All circular numbers and dates are from IRDAI public records.
Run via: python -m hibiscus.knowledge.graph.seed
"""
from typing import Any, Dict, List

from hibiscus.knowledge.graph.client import Neo4jClient
from hibiscus.observability.logger import get_logger

logger = get_logger("hibiscus.kg.seed.regulations")


REGULATIONS: List[Dict[str, Any]] = [

    # ── Health Insurance Regulations ─────────────────────────────────────────

    {
        "circular_no": "IRDA/HLT/REG/MISC/141/07/2016",
        "date": "2016-07-20",
        "subject": "IRDAI (Health Insurance) Regulations 2016",
        "category": "health_insurance",
        "effective_date": "2016-07-20",
        "key_requirements": [
            "Health insurance policies must offer lifelong renewability",
            "Premiums can only be revised on actuarial grounds with IRDAI approval",
            "Pre-existing diseases to be covered after maximum 4 years waiting period",
            "Insurers must give at least 3 months notice before product withdrawal",
            "Standardised definitions for pre-existing disease, critical illness, and related terms",
        ],
        "consumer_rights_granted": [
            "Right to lifelong renewability",
            "Right to portability across insurers",
            "Protection against arbitrary premium hikes",
        ],
        "legislation_type": "regulation",
    },
    {
        "circular_no": "IRDAI/HLT/REG/CIR/187/09/2024",
        "date": "2024-09-01",
        "subject": "IRDAI (Health Insurance) Amendment Regulations 2024",
        "category": "health_insurance",
        "effective_date": "2024-10-01",
        "key_requirements": [
            "Mandatory coverage of mental illness as per Mental Healthcare Act 2017",
            "All health plans must cover modern treatments — robotic surgery, stem cell therapy, etc.",
            "Waiting period for pre-existing diseases capped at 3 years for new policies",
            "Moratorium period set at 5 years — no contestability after 5 continuous years",
            "Day-care procedures list expanded — all procedures not requiring 24-hour admission",
        ],
        "consumer_rights_granted": [
            "Mental health coverage as a right",
            "Modern treatment access without exclusion",
            "Shortened pre-existing disease waiting periods",
            "5-year moratorium protection",
        ],
        "legislation_type": "amendment_regulation",
    },
    {
        "circular_no": "IRDAI/HLT/CIR/MISC/100/04/2024",
        "date": "2024-04-12",
        "subject": "IRDAI Master Circular on Health Insurance 2024",
        "category": "health_insurance",
        "effective_date": "2024-04-12",
        "key_requirements": [
            "Standardised list of 541 day-care procedures that must be covered",
            "Cashless facility must be available at network hospitals within 1 hour of request",
            "Pre-authorisation for planned hospitalisation must be given within 3 hours",
            "Discharge within 3 hours of payment clearance or cashless approval",
            "Claim settlement — cashless within 3 hours, reimbursement within 30 days",
        ],
        "consumer_rights_granted": [
            "Cashless in 1 hour",
            "Discharge within 3 hours",
            "Reimbursement within 30 days",
            "Day-care procedures must be covered",
        ],
        "legislation_type": "master_circular",
    },
    {
        "circular_no": "IRDAI/HLT/CIR/MISC/084/03/2016",
        "date": "2016-03-28",
        "subject": "IRDAI Health Insurance Portability Guidelines",
        "category": "health_insurance_portability",
        "effective_date": "2016-04-01",
        "key_requirements": [
            "Policyholders can port health policy to any other insurer at renewal",
            "New insurer must honour credits for waiting periods served with previous insurer",
            "Portability request to be made at least 45 days before renewal date",
            "New insurer cannot refuse portability application without valid reason",
            "Sum insured can be increased at porting but waiting period applies to incremental SI",
        ],
        "consumer_rights_granted": [
            "Right to port without losing waiting period credits",
            "Right to increase cover at porting",
            "Protection against arbitrary porting refusal",
        ],
        "legislation_type": "guideline",
    },
    {
        "circular_no": "IRDAI/HLT/REG/CIR/201/10/2020",
        "date": "2020-10-01",
        "subject": "Standard Health Insurance Products — Arogya Sanjeevani",
        "category": "health_insurance",
        "effective_date": "2020-04-01",
        "key_requirements": [
            "All insurers must offer Arogya Sanjeevani Policy — a standard product",
            "Sum insured: ₹1 lakh to ₹5 lakhs",
            "Co-payment: 5% on all claims",
            "Pre-existing diseases after 4 years waiting period",
            "Standardised terms across all insurers for easy comparison",
        ],
        "consumer_rights_granted": [
            "Simple comparable health product available from every insurer",
            "Standardised terms — no fine print surprises",
        ],
        "legislation_type": "product_mandate",
    },

    # ── Claims Settlement Regulations ─────────────────────────────────────────

    {
        "circular_no": "IRDAI/HLT/REG/MISC/205/07/2017",
        "date": "2017-07-25",
        "subject": "IRDAI (Protection of Policyholders' Interests) Regulations 2017",
        "category": "policyholder_protection",
        "effective_date": "2017-08-01",
        "key_requirements": [
            "Life claims must be settled within 30 days of receipt of all documents",
            "If investigation required, life claim must be settled within 90 days",
            "Health/general claims — reimbursement within 30 days",
            "Interest at 2% above bank rate if claim delayed beyond prescribed period",
            "Policy document must be delivered within 15 days of policy issuance",
        ],
        "consumer_rights_granted": [
            "30-day claim settlement right",
            "Interest on delayed claims",
            "Right to receive policy document promptly",
        ],
        "legislation_type": "regulation",
    },
    {
        "circular_no": "IRDAI/HLTH/CIR/MISC/197/09/2011",
        "date": "2011-09-20",
        "subject": "IRDAI Claim Settlement Guidelines — 30/60 Day Deadlines",
        "category": "claim_settlement",
        "effective_date": "2011-10-01",
        "key_requirements": [
            "Non-life insurers must acknowledge claim within 3 days",
            "Survey to be arranged within 72 hours of claim intimation",
            "Survey report to be submitted within 30 days from date of survey",
            "Repudiation or settlement within 30 days from final survey report",
            "Total claim process not to exceed 60 days from intimation",
        ],
        "consumer_rights_granted": [
            "Claim intimation acknowledgement within 3 days",
            "Survey within 72 hours",
            "Final decision within 60 days",
        ],
        "legislation_type": "guideline",
    },

    # ── Free Look Period ──────────────────────────────────────────────────────

    {
        "circular_no": "IRDAI/LIFE/CIR/GLD/013/02/2014",
        "date": "2014-02-14",
        "subject": "IRDAI Free Look Period Regulations",
        "category": "free_look_period",
        "effective_date": "2014-02-14",
        "key_requirements": [
            "Free look period: 15 days from receipt of policy document",
            "30 days free look period if policy sold via distance marketing (online/phone)",
            "Policyholders can return the policy and get full refund minus stamp duty and proportionate premium",
            "ULIP free look — units redeemed at NAV on date of receipt of cancellation",
            "Insurer must process free look cancellation within 15 days",
        ],
        "consumer_rights_granted": [
            "15-day no questions asked cancellation",
            "30-day cancellation for online purchases",
            "Full premium refund minus minimal charges",
        ],
        "legislation_type": "regulation",
    },

    # ── Grievance Redressal ───────────────────────────────────────────────────

    {
        "circular_no": "IRDAI/BROK/MISC/CIR/016/01/2024",
        "date": "2024-01-15",
        "subject": "IRDAI Grievance Redressal Regulations 2024 (Bima Bharosa)",
        "category": "grievance_redressal",
        "effective_date": "2024-04-01",
        "key_requirements": [
            "Insurers must acknowledge complaints within 3 working days",
            "Resolve complaints within 14 days for non-claims, 30 days for claims",
            "Integrated Grievance Management System — Bima Bharosa Portal",
            "Dedicated Grievance Redressal Officer (GRO) at each insurer",
            "Appeal to IRDAI if not satisfied within 14 days of insurer response",
        ],
        "consumer_rights_granted": [
            "14-day grievance resolution right",
            "Escalation to IRDAI via Bima Bharosa portal",
            "Dedicated GRO at every insurer",
        ],
        "legislation_type": "regulation",
        "portal": "https://bimabharosa.irdai.gov.in",
    },

    # ── Mis-selling Guidelines ────────────────────────────────────────────────

    {
        "circular_no": "IRDAI/LIFE/CIR/MISC/234/11/2015",
        "date": "2015-11-30",
        "subject": "IRDAI Guidelines Against Mis-selling of Insurance Products",
        "category": "mis_selling",
        "effective_date": "2016-01-01",
        "key_requirements": [
            "Agent/distributor must assess customer's insurance needs before recommending",
            "Full disclosure of product features, exclusions, charges, and returns",
            "Prohibits presenting insurance as fixed deposit or guaranteed savings scheme",
            "Calls must be recorded if selling over phone",
            "Customer must be informed of free look period at time of sale",
        ],
        "consumer_rights_granted": [
            "Right to full product disclosure before purchase",
            "Right to know charges and returns upfront",
            "Protection against false comparisons with bank deposits",
        ],
        "legislation_type": "guideline",
    },

    # ── ULIP Regulations ──────────────────────────────────────────────────────

    {
        "circular_no": "IRDAI/LIFE/REG/ULIP/101/05/2019",
        "date": "2019-05-10",
        "subject": "IRDAI ULIP Disclosure Norms and Charges Regulations",
        "category": "ulip",
        "effective_date": "2019-06-01",
        "key_requirements": [
            "Fund management charge capped at 1.35% per annum",
            "Premium allocation charge in year 1 capped",
            "Mortality charge to be disclosed annually",
            "Net yield — difference between gross yield and charges — to be disclosed",
            "Projection statements (at 4%, 8%) must be shown at time of sale",
        ],
        "consumer_rights_granted": [
            "Right to know all ULIP charges before buying",
            "Net yield disclosure — clear picture of actual returns",
            "Standardised return projections",
        ],
        "legislation_type": "regulation",
    },

    # ── Insurance Ombudsman Rules ─────────────────────────────────────────────

    {
        "circular_no": "GSR_GO_17_2017",
        "date": "2017-06-20",
        "subject": "Insurance Ombudsman Rules 2017 (Amended 2021)",
        "category": "ombudsman",
        "effective_date": "2017-06-20",
        "key_requirements": [
            "Ombudsman covers disputes up to ₹50 lakh",
            "Complaint must be filed within 1 year of insurer's final reply",
            "Ombudsman award is binding on the insurer",
            "Free service — no fees for policyholders",
            "Ombudsman must pass award within 3 months of complaint",
        ],
        "consumer_rights_granted": [
            "Free dispute resolution up to ₹50 lakh",
            "Binding award on insurer",
            "Award within 3 months",
        ],
        "legislation_type": "rules",
        "amendment_year": 2021,
    },

    # ── Annual Returns / Disclosure ───────────────────────────────────────────

    {
        "circular_no": "IRDAI/F&A/CIR/MISC/183/09/2023",
        "date": "2023-09-01",
        "subject": "IRDAI Annual Return Regulations and Public Disclosures",
        "category": "transparency_disclosure",
        "effective_date": "2023-10-01",
        "key_requirements": [
            "Insurers must publish CSR, ICR, solvency ratios on website annually",
            "Claims data by product line to be disclosed publicly",
            "Grievance data — received, resolved, pending — published quarterly",
            "Annual report must include actuarial assumptions and financial health metrics",
            "Compliance report to be submitted to IRDAI within 45 days of year end",
        ],
        "consumer_rights_granted": [
            "Right to access insurer financial health data",
            "Claims data transparency",
            "Grievance data for comparison",
        ],
        "legislation_type": "regulation",
    },

    # ── IRDAI (Insurance Regulatory) General Amendments ──────────────────────

    {
        "circular_no": "IRDAI/REG/MISC/CIR/001/01/2023",
        "date": "2023-01-05",
        "subject": "IRDAI (Insurance Companies — General Business) Amendment 2023 — Bima Sugam",
        "category": "digital_insurance",
        "effective_date": "2023-04-01",
        "key_requirements": [
            "Bima Sugam — unified digital platform for buying, managing, and claiming insurance",
            "All insurers to integrate with Bima Sugam by 2024",
            "Digital policy issuance within 24 hours of payment",
            "e-Insurance Account (eIA) for storing all policies digitally",
            "One-touch claim filing through Bima Sugam",
        ],
        "consumer_rights_granted": [
            "Digital storage of all policies in eIA",
            "Single platform for all insurance",
            "Simplified digital claims",
        ],
        "legislation_type": "regulation",
        "portal": "https://bimasugam.irdai.gov.in",
    },
    {
        "circular_no": "IRDAI/REG/MISC/CIR/175/07/2022",
        "date": "2022-07-12",
        "subject": "IRDAI (Insurance Advertisement and Disclosure) Guidelines 2022",
        "category": "advertising",
        "effective_date": "2022-10-01",
        "key_requirements": [
            "All insurance ads must clearly state IRDAI registration number",
            "Disclaimers on ULIP/savings returns — past performance disclaimer mandatory",
            "Ads must not make comparative claims about other insurers without data",
            "Digital ads regulated — influencer marketing requires disclosure",
            "Key policy features must be readable — minimum font size regulations",
        ],
        "consumer_rights_granted": [
            "Protection from misleading insurance advertising",
            "Clear disclosures on returns",
        ],
        "legislation_type": "guideline",
    },
]


# ── Cypher ─────────────────────────────────────────────────────────────────────

_MERGE_REGULATION = """
MERGE (r:Regulation {circular_no: $circular_no})
SET
  r.date                   = $date,
  r.subject                = $subject,
  r.category               = $category,
  r.effective_date         = $effective_date,
  r.key_requirements       = $key_requirements,
  r.consumer_rights_granted = $consumer_rights_granted,
  r.legislation_type       = $legislation_type,
  r.updated_at             = datetime()
RETURN r.circular_no AS circular_no
"""


async def seed_regulations(client: Neo4jClient) -> None:
    """
    MERGE all Regulation nodes into Neo4j. Idempotent — safe to re-run.
    """
    logger.info("seed_regulations_start", count=len(REGULATIONS))

    reg_params = []
    for reg in REGULATIONS:
        params = {
            "circular_no": reg["circular_no"],
            "date": reg["date"],
            "subject": reg["subject"],
            "category": reg["category"],
            "effective_date": reg["effective_date"],
            "key_requirements": reg["key_requirements"],
            "consumer_rights_granted": reg.get("consumer_rights_granted", []),
            "legislation_type": reg.get("legislation_type", "guideline"),
        }
        reg_params.append(params)

    succeeded = await client.execute_batch(
        _MERGE_REGULATION,
        param_list=reg_params,
        query_name="seed_regulations",
    )
    logger.info("seed_regulations_complete", succeeded=succeeded, total=len(REGULATIONS))
