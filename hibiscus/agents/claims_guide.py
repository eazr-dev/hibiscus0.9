"""
ClaimsGuideAgent — Agent 4
===========================
Step-by-step insurance claims guide.

Guides users through the claims process for any insurance type and situation,
including cashless hospitalization, reimbursement, death claims, maturity claims,
and claim rejection escalation.

IRDAI Mandated Timelines (non-negotiable — cite these):
- Cashless pre-authorization: 30 minutes (emergency), 4 hours (planned)
- Cashless claim settlement decision: within 3 hours of discharge
- Reimbursement claim settlement: 30 days from last document submission
- Death claim settlement: 30 days from document submission (no investigation)
- Investigation cases: 90 days maximum
- Insurer grievance response: 15 days
- Ombudsman approach: within 3 months of insurer rejection
"""
import json
import time
from typing import Any, Dict, List, Optional, Tuple

from hibiscus.agents.base import BaseAgent, AgentResult
from hibiscus.llm.router import call_llm
from hibiscus.observability.logger import PipelineLogger
from hibiscus.orchestrator.state import HibiscusState

AGENT_SYSTEM_PROMPT = """You are Hibiscus, EAZR's insurance AI assistant specializing in claims guidance.

Your role: Be the user's guide and advocate through the insurance claims process. Make complex processes simple and actionable.

CRITICAL RULES:
1. Give SPECIFIC, numbered, actionable steps — not generic advice
2. ALWAYS mention IRDAI mandated timelines (30 min cashless pre-auth, 30 days reimbursement, 30 days death claim)
3. For rejected claims: ALWAYS explain escalation rights (insurer grievance → IRDAI portal → Ombudsman → Consumer Forum)
4. NEVER say "it depends" without explaining what it depends on
5. Use ₹ symbol, Indian formats
6. Be emotionally supportive — claims are stressful situations
7. End with: "Keep all documents. Take written receipts for every submission."
8. Always mention: Ombudsman service is FREE for claims up to ₹50 lakh

TONE: Calm, clear, step-by-step. The user may be in a stressful situation — be their guide.
"""

# Claims process by type — all steps and requirements defined here (not in LLM)
CLAIMS_PROCESS = {
    "cashless_health": {
        "title": "Cashless Health Insurance Claim",
        "steps": [
            "Go to a network hospital (check insurer's network hospital list online or call TPA helpline)",
            "Show your health insurance card / policy details at the insurance desk",
            "Hospital sends a pre-authorization request to your TPA/insurer",
            "TPA must respond within 30 minutes for emergencies, 4 hours for planned admissions (IRDAI mandate)",
            "On discharge, hospital settles directly with insurer — you pay only non-covered items",
            "Get the final settlement statement from hospital for your records",
        ],
        "documents": [
            "Health insurance card / e-card",
            "Photo ID proof (Aadhaar / PAN)",
            "Doctor's prescription / referral letter",
            "Admission letter from treating doctor",
        ],
        "irdai_rights": [
            "Pre-authorization within 30 minutes for emergency admission (IRDAI mandate)",
            "Pre-authorization within 4 hours for planned/elective admission",
            "Insurer cannot deny cashless at network hospital without a written reason",
            "Settlement decision within 3 hours of discharge request",
        ],
        "tips": [
            "Always call TPA helpline BEFORE admission for planned procedures",
            "Demand written rejection if cashless is denied — do not accept verbal denial",
            "Keep all bills, reports, discharge summary even for cashless claims",
            "Pre-hospitalization (30 days before) and post-hospitalization (60 days after) costs are also claimable",
        ],
    },
    "reimbursement_health": {
        "title": "Reimbursement Health Insurance Claim",
        "steps": [
            "Get hospitalized and pay all bills — keep EVERY original bill and receipt",
            "Collect all documents at discharge (complete list below)",
            "File claim within 15-30 days of discharge (check your policy — timelines vary)",
            "Submit documents to insurer/TPA via registered post or their app/portal",
            "Get acknowledgment with reference number — keep it safe",
            "Insurer must settle within 30 days of receiving last document (IRDAI mandate)",
            "If documents insufficient, insurer must communicate within 15 days",
            "Follow up weekly after day 20 if no response received",
        ],
        "documents": [
            "Fully filled claim form (from insurer website)",
            "Original discharge summary",
            "All original hospital bills (itemized)",
            "All original pharmacy / medicine bills",
            "All original diagnostic / lab test reports",
            "Doctor's prescription for all medicines purchased",
            "Indoor case papers / hospital treatment records",
            "KYC documents (Aadhaar, PAN)",
            "Cancelled cheque or NEFT bank account details",
            "Policy copy",
            "Pre-hospitalization reports (if relevant to the illness)",
        ],
        "irdai_rights": [
            "Settlement within 30 days of last document submission (IRDAI mandate)",
            "If partial payment made: insurer must give detailed written reason for deduction",
            "Insurer cannot reject without stating the specific policy clause violated",
            "Deficiency notice (asking for more docs) must be sent within 15 days",
        ],
        "tips": [
            "Make photocopies of EVERYTHING before submitting originals",
            "Send by registered post / speed post — keep tracking number",
            "If submitting online: screenshot every upload and note upload timestamps",
            "Pre-hospitalization (30-60 days) and post-hospitalization (60-90 days) expenses also claimable",
        ],
    },
    "death_claim": {
        "title": "Life Insurance Death Claim",
        "steps": [
            "Inform the insurer in writing as soon as possible (usually within 30 days of death)",
            "Contact the insurer's nearest branch or call customer care to initiate the claim",
            "Submit the claim form along with required documents to the branch",
            "Insurer must settle within 30 days of receiving complete documents (IRDAI mandate)",
            "If investigation is required, it must be completed within 90 days (no extensions)",
            "Claim amount is paid to the registered nominee or legal heir via NEFT",
        ],
        "documents": [
            "Claim form (available on insurer website)",
            "Original policy document",
            "Certified death certificate (from municipal authority — get multiple copies)",
            "Claimant (nominee) photo ID proof",
            "Claimant address proof",
            "Relationship proof (marriage certificate, birth certificate, etc.)",
            "Nominee's bank account details for NEFT",
            "Attending physician's statement (for illness-related death)",
            "Police FIR + postmortem report (for accidental or unnatural death)",
            "Hospital discharge summary (if death occurred in hospital)",
        ],
        "irdai_rights": [
            "Settlement within 30 days of complete documents — no exceptions",
            "If investigation needed, must complete within 90 days (IRDAI mandate)",
            "Policy that is 3+ years old: insurer CANNOT reject on grounds of non-disclosure of health history",
            "Claim cannot be contested after the contestability period (3 years for most insurers)",
        ],
        "tips": [
            "Get at least 6-8 certified copies of the death certificate from municipal authority",
            "A 3+ year old policy is very difficult to reject — know your rights",
            "If policy lapsed but was revived: check revival date and what was disclosed",
            "If nominee is a minor: a natural guardian / court-appointed guardian must file the claim",
        ],
    },
    "maturity_claim": {
        "title": "Policy Maturity Claim",
        "steps": [
            "Insurer sends a maturity notice 2-3 months before the maturity date",
            "Fill the maturity discharge voucher sent by insurer (or download from website)",
            "Submit documents including original policy, ID, and bank details",
            "Payment is made on or before the maturity date as stated in policy",
            "If payment not received within 30 days of maturity date: file a formal complaint",
        ],
        "documents": [
            "Original policy document",
            "Maturity discharge voucher (signed)",
            "Photo ID proof (Aadhaar, PAN)",
            "NEFT details / cancelled cheque",
            "Age proof (if not already submitted to insurer)",
        ],
        "irdai_rights": [
            "Payment on the maturity date as stated in the policy schedule",
            "Insurer must pay interest for any delay beyond the maturity date",
        ],
        "tips": [
            "Ensure your address with the insurer is updated — maturity notice goes there",
            "Update nominee records if there has been any change",
            "Verify the maturity benefit amount in your policy schedule beforehand",
            "Tax: maturity proceeds may be taxable if SA < 10x annual premium (Section 10(10D))",
        ],
    },
    "claim_rejection": {
        "title": "Handling a Claim Rejection",
        "steps": [
            "Read the rejection letter carefully — note the EXACT reason and clause cited",
            "Request a copy of your complete claim file (you are legally entitled to it)",
            "Check if rejection is valid: compare the stated reason against your policy terms",
            "If rejection is unfair or invalid: file a written grievance with the insurer",
            "Insurer must respond to grievance within 15 days (IRDAI mandate)",
            "If still not resolved: escalate to IRDAI Bima Bharosa portal (bimabharosaportal.irdai.gov.in)",
            "If unresolved within 30 days after IRDAI complaint: approach Insurance Ombudsman (FREE, up to ₹50 lakh)",
            "For claims above ₹50 lakh or highly complex cases: Consumer Forum (NCDRC/SCDRC)",
        ],
        "documents": [
            "Rejection letter (original)",
            "Copies of all claim documents originally submitted",
            "Correspondence with insurer (emails, written letters)",
            "Original policy document",
            "Any new evidence or medical records supporting your claim",
            "Timeline of events (dates of admission, discharge, submission, rejection)",
        ],
        "irdai_rights": [
            "Right to a written rejection with specific policy clause cited — verbal rejection not valid",
            "Right to approach Insurance Ombudsman within 3 months of insurer rejection",
            "Ombudsman service is completely FREE for claims up to ₹50 lakh",
            "Insurer must respond to internal grievance within 15 days",
            "Policies 3+ years old: cannot be rejected on non-disclosure of health history",
        ],
        "tips": [
            "Never accept a verbal rejection — always demand written rejection with policy clause",
            "Non-disclosure rejections on 3+ year old policies are legally challengeable",
            "IRDAI Bima Bharosa portal: bimabharosaportal.irdai.gov.in (free)",
            "Insurance Ombudsman offices are in every state — fully free process",
            "Consumer Forum: NCDRC for claims above ₹20 lakh, SCDRC for ₹1L to ₹20L",
        ],
        "escalation_ladder": [
            "Level 1: Internal grievance to insurer (15-day SLA)",
            "Level 2: IRDAI Bima Bharosa portal — bimabharosaportal.irdai.gov.in",
            "Level 3: Insurance Ombudsman — FREE, within 3 months of rejection, up to ₹50L",
            "Level 4: Consumer Forum — NCDRC for >₹20L claims",
            "Level 5: Civil court (last resort)",
        ],
    },
}

# Claim type keyword detection mapping
CLAIM_TYPE_KEYWORDS = {
    "cashless": "cashless_health",
    "cashless claim": "cashless_health",
    "network hospital": "cashless_health",
    "tpa": "cashless_health",
    "reimbursement": "reimbursement_health",
    "reimburse": "reimbursement_health",
    "hospital bill": "reimbursement_health",
    "discharge": "reimbursement_health",
    "death claim": "death_claim",
    "policy holder died": "death_claim",
    "passed away": "death_claim",
    "nominee claim": "death_claim",
    "maturity": "maturity_claim",
    "maturity claim": "maturity_claim",
    "policy mature": "maturity_claim",
    "claim rejected": "claim_rejection",
    "rejected claim": "claim_rejection",
    "rejection": "claim_rejection",
    "claim denied": "claim_rejection",
    "repudiated": "claim_rejection",
    "ombudsman": "claim_rejection",
    "grievance": "claim_rejection",
    "unfairly": "claim_rejection",
}


class ClaimsGuideAgent(BaseAgent):
    """Guides users through insurance claims process step-by-step."""

    name = "claims_guide"
    description = "Claims assistance and guidance"
    default_tier = "deepseek_v3"

    async def execute(self, state: HibiscusState) -> AgentResult:
        plog = PipelineLogger(
            component=f"agent.{self.name}",
            request_id=state.get("request_id", "?"),
            session_id=state.get("session_id", "?"),
            user_id=state.get("user_id", "?"),
        )
        start = time.time()
        plog.agent_start(agent=self.name, model=self.default_tier, task=state.get("intent", ""))

        try:
            message = state.get("message", "")
            emotional_state = state.get("emotional_state", "neutral")

            # ── Step 1: Detect claim type ──────────────────────────────────
            plog.step_start("detect_claim_type")
            claim_type, detection_confidence = self._detect_claim_type(
                message, state.get("document_context")
            )
            plog.step_complete(
                "detect_claim_type",
                claim_type=claim_type,
                confidence=detection_confidence,
            )

            # ── Step 2: Extract insurer if mentioned ───────────────────────
            insurer = self._extract_insurer(message)

            # ── Step 2.5: Check claims status via insurer integration ─────
            claims_status_info = ""
            if insurer:
                try:
                    from hibiscus.config import settings as _cfg
                    if getattr(_cfg, "insurer_api_enabled", False):
                        from hibiscus.integrations.registry import get_integration
                        integration = get_integration(insurer)
                        if integration and "claims_status" in integration.supported_features:
                            # Extract policy number if available
                            policy_number = ""
                            if state.get("document_context"):
                                extraction = state["document_context"].get("extraction", {})
                                policy_number = extraction.get("policy_number", "")
                            if policy_number:
                                result = await integration.get_claims_status(policy_number)
                                if result:
                                    d = result.to_dict()
                                    claims_status_info = (
                                        f"\nLive Claims Status (from {insurer}):\n"
                                        f"  Claim ID: {d.get('claim_id', 'N/A')}\n"
                                        f"  Status: {d.get('status', 'N/A')}\n"
                                        f"  Amount Claimed: ₹{d.get('amount_claimed', 'N/A')}\n"
                                        f"  Next Steps: {', '.join(d.get('next_steps', []))}\n"
                                    )
                                    plog.step_complete("integration_claims_status", insurer=insurer, status=d.get("status"))
                except Exception as e:
                    plog.log("integration_claims_status_skipped", error=str(e))

            # ── Step 3: Load structured claim process guide ────────────────
            plog.step_start("load_claim_guide")
            claim_guide = CLAIMS_PROCESS.get(claim_type, CLAIMS_PROCESS["reimbursement_health"])
            plog.step_complete(
                "load_claim_guide",
                guide_title=claim_guide.get("title", ""),
                steps_count=len(claim_guide.get("steps", [])),
            )

            # ── Step 4: LLM synthesis ──────────────────────────────────────
            plog.step_start("llm_synthesis")
            is_distressed = emotional_state in ("distressed", "frustrated", "urgent")

            synthesis_prompt = self._build_synthesis_prompt(
                message=message,
                claim_type=claim_type,
                claim_guide=claim_guide,
                insurer=insurer,
                is_distressed=is_distressed,
                doc_context=state.get("document_context"),
                claims_status_info=claims_status_info,
            )

            llm_response = await call_llm(
                messages=[
                    {
                        "role": "system",
                        "content": self._system_prompt + "\n\n" + AGENT_SYSTEM_PROMPT,
                    },
                    {"role": "user", "content": synthesis_prompt},
                ],
                tier=self.default_tier,
                conversation_id=state.get("conversation_id", "?"),
                agent=self.name,
            )

            response_text = llm_response["content"]
            plog.step_complete("llm_synthesis")

            # ── Step 5: Build sources ──────────────────────────────────────
            sources = [
                {
                    "type": "regulation",
                    "reference": "IRDAI (Protection of Policyholders' Interests) Regulations 2017",
                    "confidence": 0.95,
                },
                {
                    "type": "regulation",
                    "reference": "IRDAI Master Circular on Health Insurance 2024",
                    "confidence": 0.90,
                },
            ]
            if claim_type == "claim_rejection":
                sources.append({
                    "type": "regulation",
                    "reference": "IRDAI Insurance Ombudsman Rules 2017",
                    "confidence": 0.95,
                })

            confidence = 0.88 if claim_type in CLAIMS_PROCESS else 0.72
            latency_ms = int((time.time() - start) * 1000)

            return AgentResult(
                response=response_text,
                confidence=confidence,
                sources=sources,
                latency_ms=latency_ms,
                tokens_in=llm_response.get("tokens_in", 0),
                tokens_out=llm_response.get("tokens_out", 0),
                structured_data={
                    "claim_type_detected": claim_type,
                    "insurer_mentioned": insurer,
                    "steps_count": len(claim_guide.get("steps", [])),
                    "documents_required": claim_guide.get("documents", []),
                    "irdai_rights": claim_guide.get("irdai_rights", []),
                    "escalation_ladder": claim_guide.get("escalation_ladder", []),
                },
                follow_up_suggestions=self._build_follow_ups(claim_type, insurer),
            )

        except Exception as e:
            plog.error("claims_guide", error=str(e))
            return AgentResult(
                response=self._error_response(),
                confidence=0.0,
                sources=[],
            )

    # ── Private helpers ────────────────────────────────────────────────────

    def _detect_claim_type(
        self,
        message: str,
        doc_context: Optional[Dict[str, Any]],
    ) -> Tuple[str, float]:
        """Detect claim type from message and document context."""
        msg_lower = message.lower()

        for keyword, claim_type in CLAIM_TYPE_KEYWORDS.items():
            if keyword in msg_lower:
                return claim_type, 0.88

        # Use document context as hint
        if doc_context:
            extraction = doc_context.get("extraction", {})
            policy_type = (extraction.get("policy_type") or "").lower()
            if "life" in policy_type:
                if any(w in msg_lower for w in ["die", "death", "died", "passed", "nominee"]):
                    return "death_claim", 0.80
                if any(w in msg_lower for w in ["mature", "maturity", "completed"]):
                    return "maturity_claim", 0.80
            elif "health" in policy_type or "medical" in policy_type:
                if "reimburse" in msg_lower or "paid" in msg_lower:
                    return "reimbursement_health", 0.80
                return "cashless_health", 0.70

        if any(w in msg_lower for w in ["claim", "how to claim", "file claim"]):
            return "reimbursement_health", 0.60

        return "reimbursement_health", 0.50

    def _extract_insurer(self, message: str) -> Optional[str]:
        """Extract insurer name mentioned in the message."""
        known_insurers = [
            "lic", "life insurance corporation",
            "hdfc life", "sbi life", "icici prudential", "max life",
            "bajaj allianz", "kotak mahindra", "tata aia", "aditya birla",
            "star health", "niva bupa", "care health", "manipal cigna",
            "hdfc ergo", "icici lombard", "new india assurance",
            "united india", "oriental insurance", "national insurance",
            "reliance general", "go digit",
        ]
        msg_lower = message.lower()
        for insurer in known_insurers:
            if insurer in msg_lower:
                return insurer.title()
        return None

    def _build_synthesis_prompt(
        self,
        message: str,
        claim_type: str,
        claim_guide: Dict[str, Any],
        insurer: Optional[str],
        is_distressed: bool,
        doc_context: Optional[Dict[str, Any]],
        claims_status_info: str = "",
    ) -> str:
        """Build synthesis prompt with all structured data pre-loaded."""
        tone_instruction = ""
        if is_distressed:
            tone_instruction = (
                "\nTONE OVERRIDE: User appears stressed/frustrated. "
                "Start with ONE empathetic sentence acknowledging their situation, "
                "then move directly to practical steps. End with an empowering statement about their rights."
            )

        insurer_text = f"Insurer mentioned: {insurer}" if insurer else "No specific insurer mentioned"

        policy_details = ""
        if doc_context and doc_context.get("extraction"):
            extraction = doc_context["extraction"]
            policy_details = (
                f"\nPolicy on file:\n"
                f"  Type: {extraction.get('policy_type', 'Unknown')}\n"
                f"  Insurer: {extraction.get('insurer', 'Unknown')}\n"
                f"  Sum Insured: {extraction.get('sum_insured') or extraction.get('sum_assured', 'Unknown')}\n"
            )

        steps_text = json.dumps(claim_guide.get("steps", []), indent=2, ensure_ascii=False)
        docs_text = json.dumps(claim_guide.get("documents", []), indent=2, ensure_ascii=False)
        rights_text = json.dumps(claim_guide.get("irdai_rights", []), indent=2, ensure_ascii=False)
        tips_text = json.dumps(claim_guide.get("tips", []), indent=2, ensure_ascii=False)
        escalation_text = ""
        if claim_guide.get("escalation_ladder"):
            escalation_text = (
                "\nESCALATION LADDER:\n"
                + json.dumps(claim_guide["escalation_ladder"], indent=2, ensure_ascii=False)
            )

        return f"""The user needs help with an insurance claim.
{tone_instruction}

USER'S REQUEST: {message}
Claim type: {claim_guide.get('title', 'General Claim')}
{insurer_text}
{policy_details}

PROCESS STEPS (present numbered):
{steps_text}

REQUIRED DOCUMENTS (present as checklist):
{docs_text}

IRDAI RIGHTS (always present in a "Your Rights" section):
{rights_text}

PRO TIPS:
{tips_text}
{escalation_text}
{claims_status_info}
INSTRUCTIONS FOR RESPONSE:
1. Address the user's specific situation — not generic advice
2. Present steps as a clear numbered list
3. Present required documents as a formatted checklist (with ✓ markers or bullet points)
4. Include a "Your Rights" section with the IRDAI rights above
5. For claim rejection: show the full escalation ladder explicitly
6. Include the Ombudsman note: "Ombudsman service is FREE for claims up to ₹50 lakh"
7. IRDAI Bima Bharosa URL: bimabharosaportal.irdai.gov.in
8. End with: "Keep all original documents and get written acknowledgment for every submission."
9. Do NOT make up policy-specific numbers — only use data provided above
10. If insurer mentioned: acknowledge but note specific process may vary by insurer
"""

    def _build_follow_ups(
        self, claim_type: str, insurer: Optional[str]
    ) -> List[str]:
        """Build contextual follow-up suggestions based on claim type."""
        if claim_type == "cashless_health":
            return [
                "Would you like help understanding what's covered and what's excluded?",
                "Want me to explain pre and post-hospitalization coverage limits?",
                "Should I explain how to handle co-payment if your policy has it?",
            ]
        elif claim_type == "reimbursement_health":
            return [
                "Do you need help understanding why some expenses might get deducted?",
                "Want me to explain which expenses are typically excluded from health claims?",
                "Should I calculate how much reimbursement you should expect?",
            ]
        elif claim_type == "death_claim":
            return [
                "Do you need guidance on the contestability period rules?",
                "Want to know what happens if the nominee is a minor?",
                "Should I explain what documents the legal heir needs if no nominee was registered?",
            ]
        elif claim_type == "claim_rejection":
            return [
                "Would you like help drafting a formal grievance letter to the insurer?",
                "Should I explain how to file a complaint with the Insurance Ombudsman?",
                "Want to understand on what legal grounds you can challenge the rejection?",
            ]
        elif claim_type == "maturity_claim":
            return [
                "Should I check the tax implications of your maturity amount?",
                "Want me to verify if your maturity amount calculation looks correct?",
            ]
        return [
            "Do you want me to explain your policy's claims clause in detail?",
            "Would you like guidance on what documents to keep ready?",
        ]


# ── Module-level run function (called by agent_dispatch) ──────────────────
_agent = ClaimsGuideAgent()


async def run(state: HibiscusState) -> Dict[str, Any]:
    """Entry point for agent_dispatch."""
    return await _agent(state)
