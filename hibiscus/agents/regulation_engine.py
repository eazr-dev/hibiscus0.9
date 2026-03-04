"""
🌺 Hibiscus v0.9 | EAZR AI Insurance Intelligence Engine
Regulation engine agent — IRDAI circular lookup, compliance checking, regulatory guidance.
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
"""
import json
import time
from typing import Any, Dict, List, Optional, Tuple

from hibiscus.agents.base import BaseAgent, AgentResult
from hibiscus.llm.router import call_llm
from hibiscus.observability.logger import PipelineLogger
from hibiscus.orchestrator.state import HibiscusState


# ── Knowledge base version metadata ──────────────────────────────────────
_LAST_VERIFIED = "2026-03-04"
_SOURCE = "IRDAI circulars via training data"

# Core IRDAI regulation knowledge base
# This is the ground truth — LLM only synthesizes from this, never adds to it
REGULATION_KNOWLEDGE_BASE = {
    "free_look_period": {
        "title": "Free Look Period",
        "regulation": "IRDAI (Protection of Policyholders' Interests) Regulations 2017 — Regulation 6",
        "what_it_says": (
            "Policyholders have the right to return a policy within 15 days of receipt "
            "for policies sold through regular channels, and 30 days for policies sold "
            "through distance marketing (online/phone). The insurer must refund the premium "
            "paid, less pro-rata risk premium, stamp duty, and medical examination costs."
        ),
        "user_action": (
            "Write to your insurer within the free look window stating you wish to cancel. "
            "The insurer must process your refund within 15 days of receiving the cancellation request."
        ),
        "escalation": "If refund not given: file complaint at IRDAI Bima Bharosa portal",
        "keywords": ["free look", "cancel policy", "return policy", "cooling off", "cooling period"],
    },

    "portability": {
        "title": "Health Insurance Portability",
        "regulation": "IRDAI Health Insurance Portability Guidelines 2011; IRDAI Circular No. 015/IRDA/Health/Port/09-10",
        "what_it_says": (
            "Every health insurance policyholder has the right to port their policy to another insurer "
            "without losing waiting period credits earned on the previous policy. Portability applies "
            "to both individual and family floater health policies. The new insurer CANNOT deny portability "
            "without a valid medical reason."
        ),
        "user_action": (
            "Apply for portability at least 45 days before your renewal date. "
            "The new insurer must respond within 15 days. "
            "You retain all waiting period credits earned with the previous insurer."
        ),
        "escalation": "If portability denied without valid reason: file IRDAI complaint immediately",
        "keywords": ["port", "portability", "switch insurer", "change insurer", "transfer policy"],
    },

    "grievance_redressal": {
        "title": "Grievance Redressal Process",
        "regulation": "IRDAI (Protection of Policyholders' Interests) Regulations 2017 — Regulation 13 & 14",
        "what_it_says": (
            "Every insurer must have a Grievance Redressal Officer (GRO). "
            "Insurers must acknowledge grievances within 3 working days. "
            "They must resolve grievances within 15 days of receipt. "
            "If not resolved within 15 days, the policyholder can approach IRDAI."
        ),
        "user_action": (
            "Step 1: File written complaint to insurer's GRO (keep acknowledgment reference number).\n"
            "Step 2: If not resolved in 15 days: approach IRDAI Bima Bharosa portal (bimabharosaportal.irdai.gov.in).\n"
            "Step 3: If still unresolved: approach Insurance Ombudsman within 3 months."
        ),
        "escalation": "Ombudsman, Consumer Forum (NCDRC/SCDRC), Civil Court",
        "keywords": ["grievance", "complaint", "not resolved", "insurer not responding", "15 days"],
    },

    "ombudsman": {
        "title": "Insurance Ombudsman",
        "regulation": "Insurance Ombudsman Rules 2017 (as amended)",
        "what_it_says": (
            "The Insurance Ombudsman is a free, quasi-judicial forum for resolving disputes between "
            "policyholders and insurance companies. Jurisdiction: claims up to ₹50 lakh. "
            "The ombudsman service is completely FREE for policyholders. "
            "The insurer must comply with the ombudsman award within 30 days. "
            "Complaints must be filed within 3 months of insurer's final rejection/no response."
        ),
        "user_action": (
            "File complaint at the ombudsman office for your state (list at irdai.gov.in). "
            "Required: insurer's rejection letter, all claim documents, correspondence timeline. "
            "The process takes approximately 3-6 months."
        ),
        "escalation": "If unhappy with ombudsman award: Consumer Forum or Civil Court",
        "offices": "17 Ombudsman offices across India — jurisdiction by policyholder's state",
        "keywords": ["ombudsman", "dispute", "reject", "50 lakh", "free resolution", "3 months"],
    },

    "claim_settlement_timelines": {
        "title": "Claim Settlement Timelines",
        "regulation": "IRDAI (Protection of Policyholders' Interests) Regulations 2017 — Regulation 9",
        "what_it_says": (
            "Health: Cashless pre-authorization within 30 minutes (emergency) or 4 hours (planned).\n"
            "Health: Reimbursement settlement within 30 days of last document submission.\n"
            "Life: Death claim settlement within 30 days (no investigation) or 90 days (with investigation).\n"
            "General: All claims must be settled/repudiated within 30 days of receiving all documents.\n"
            "Interest on delayed payments: applicable if settlement exceeds stipulated timelines."
        ),
        "user_action": (
            "Track submission date and follow up after 25 days. "
            "Demand written reason for any delay beyond timelines. "
            "File IRDAI complaint if timelines violated."
        ),
        "escalation": "IRDAI Bima Bharosa portal → Ombudsman",
        "keywords": ["timeline", "how long", "days to settle", "delay", "30 days", "90 days"],
    },

    "waiting_period": {
        "title": "Waiting Period Rules for Health Insurance",
        "regulation": "IRDAI Guidelines on Standardization of Exclusions in Health Insurance — 2020",
        "what_it_says": (
            "Initial waiting period: 30 days for all illnesses except accidents.\n"
            "Pre-existing disease (PED) waiting period: Maximum 3 years (reduced from 4 years as per IRDAI 2023).\n"
            "Specific illness waiting period: 1-2 years for listed conditions (hernia, cataract, etc.).\n"
            "Accident claims: No waiting period.\n"
            "Portability: Waiting period credits from previous insurer must be carried forward."
        ),
        "user_action": (
            "Check your policy schedule for the PED waiting period. "
            "Any PED waiting period above 3 years is now non-compliant as per IRDAI 2023 guidelines. "
            "Report to IRDAI if insurer refuses to reduce it."
        ),
        "escalation": "File IRDAI complaint if waiting period exceeds 3 years for PED",
        "keywords": ["waiting period", "pre-existing", "PED", "30 days", "3 years", "4 years", "exclusion"],
    },

    "grace_period": {
        "title": "Grace Period and Policy Revival",
        "regulation": "IRDAI (Protection of Policyholders' Interests) Regulations 2017",
        "what_it_says": (
            "Life insurance: 30-day grace period for annual/half-yearly/quarterly premiums. "
            "15-day grace period for monthly premiums. Policy remains in force during grace period.\n"
            "Health insurance: 30-day grace period typically.\n"
            "Revival: Most policies allow revival within 2-5 years of lapse with back premiums + interest."
        ),
        "user_action": (
            "If within grace period: pay premium immediately — policy is still valid.\n"
            "If lapsed: contact insurer for revival terms within the revival period.\n"
            "Lapsed life policy still has surrender value (if 3+ years premiums paid)."
        ),
        "escalation": "If insurer refuses revival within allowable period: file IRDAI complaint",
        "keywords": ["grace period", "lapsed", "lapse", "revival", "late payment", "missed premium"],
    },

    "nomination": {
        "title": "Nomination Rights",
        "regulation": "Insurance Act 1938 — Section 39; IRDAI Guidelines on Nomination",
        "what_it_says": (
            "Every insurance policy must allow the policyholder to nominate a beneficiary. "
            "Nominees can be changed at any time during the policy term. "
            "For life insurance: nominee receives claim proceeds directly without legal proceedings "
            "(if nominee is a 'beneficial nominee' — spouse/parent/child/sibling)."
        ),
        "user_action": (
            "Ensure your nomination is updated after marriage, divorce, or death of nominee. "
            "Register a beneficial nominee (spouse/parent/child) to avoid complications in claims. "
            "Keep nominee details in your policy documents accessible to family."
        ),
        "escalation": "Dispute over nominee claim: approach courts or ombudsman",
        "keywords": ["nominee", "nomination", "beneficiary", "who gets money", "change nominee"],
    },

    "non_disclosure": {
        "title": "Non-Disclosure and Contestability",
        "regulation": "Insurance Act 1938 — Section 45; IRDAI clarification circular",
        "what_it_says": (
            "Section 45: An insurer CANNOT call into question a life insurance policy after 3 years "
            "from the date of commencement, even on grounds of mis-statement or non-disclosure. "
            "Exception: fraudulent suppression of material facts. "
            "This means: death claims on 3+ year old policies cannot be rejected for non-disclosure "
            "of previous health conditions unless the insurer can prove fraud."
        ),
        "user_action": (
            "If your claim is rejected on 'non-disclosure' grounds for a 3+ year old policy: "
            "cite Section 45 of the Insurance Act in your grievance. "
            "Approach the ombudsman — this is a strong legal ground for challenging rejection."
        ),
        "escalation": "This is a strong legal ground — file ombudsman complaint and mention Section 45",
        "keywords": ["non disclosure", "not disclosed", "pre-existing", "3 years", "section 45", "contestability", "fraud"],
    },

    "health_insurance_restoration": {
        "title": "Restoration / Reinstatement Benefit",
        "regulation": "IRDAI Health Insurance Master Circular 2024",
        "what_it_says": (
            "Some health insurance policies offer restoration of sum insured once exhausted in a policy year. "
            "IRDAI mandates standardized terms for restoration benefits as per 2024 Master Circular. "
            "Restoration can be: unlimited (any illness) or partial (different illness only). "
            "Check your policy to see if restoration applies to the same illness used to exhaust cover."
        ),
        "user_action": (
            "Check your policy's restoration clause carefully before assuming coverage is restored. "
            "Confirm with insurer if restoration applies to the same illness or only different illnesses."
        ),
        "escalation": "If insurer disputes restoration claim: file IRDAI complaint",
        "keywords": ["restoration", "reinstatement", "sum insured exhausted", "refill", "recharged"],
    },
}

# Keyword-to-regulation mapping for fast lookup
KEYWORD_TO_REGULATION = {}
for reg_key, reg_data in REGULATION_KNOWLEDGE_BASE.items():
    for kw in reg_data.get("keywords", []):
        KEYWORD_TO_REGULATION[kw] = reg_key


class RegulationEngineAgent(BaseAgent):
    """Explains IRDAI regulations and consumer rights."""

    name = "regulation_engine"
    description = "IRDAI regulation lookup and compliance"
    default_tier = "deepseek_v3"
    prompt_file = "regulation_engine.txt"

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

            # ── Step 1: Match regulations ──────────────────────────────────
            plog.step_start("match_regulations")
            matched_regulations, match_confidence = self._match_regulations(message)
            plog.step_complete(
                "match_regulations",
                matched=list(matched_regulations.keys()),
                confidence=match_confidence,
            )

            # ── Step 2: Build situation context ───────────────────────────
            doc_context = state.get("document_context")
            situation_context = self._build_situation_context(message, doc_context, state)

            # ── Step 3: LLM synthesis ──────────────────────────────────────
            plog.step_start("llm_synthesis")
            is_rights_violation = any(w in message.lower() for w in [
                "rejected", "denied", "not responding", "violation", "cheated", "fraud"
            ])
            is_distressed = emotional_state in ("distressed", "frustrated", "urgent")

            synthesis_prompt = self._build_synthesis_prompt(
                message=message,
                matched_regulations=matched_regulations,
                situation_context=situation_context,
                is_rights_violation=is_rights_violation,
                is_distressed=is_distressed,
            )

            llm_response = await call_llm(
                messages=[
                    {
                        "role": "system",
                        "content": self._system_prompt + "\n\n" + self._agent_prompt,
                    },
                    {"role": "user", "content": synthesis_prompt},
                ],
                tier=self.default_tier,
                conversation_id=state.get("conversation_id", "?"),
                agent=self.name,
            )

            response_text = llm_response["content"]
            plog.step_complete("llm_synthesis")

            # ── Step 4: Build sources ──────────────────────────────────────
            sources = []
            for reg_key, reg_data in matched_regulations.items():
                sources.append({
                    "type": "regulation",
                    "reference": reg_data["regulation"],
                    "confidence": 0.90,
                })
            sources.append({
                "type": "official",
                "reference": "IRDAI (Protection of Policyholders' Interests) Regulations 2017",
                "url": "https://irdai.gov.in",
                "confidence": 0.92,
            })

            # Confidence: high if regulation matched, lower if generic response
            confidence = 0.88 if matched_regulations else 0.70
            latency_ms = int((time.time() - start) * 1000)

            return AgentResult(
                response=response_text,
                confidence=confidence,
                sources=sources,
                latency_ms=latency_ms,
                tokens_in=llm_response.get("tokens_in", 0),
                tokens_out=llm_response.get("tokens_out", 0),
                structured_data={
                    "regulations_matched": list(matched_regulations.keys()),
                    "is_rights_violation": is_rights_violation,
                    "escalation_path": self._get_escalation_path(matched_regulations),
                },
                follow_up_suggestions=self._build_follow_ups(matched_regulations, is_rights_violation),
            )

        except Exception as e:
            plog.error("regulation_engine", error=str(e))
            return AgentResult(
                response=self._error_response(),
                confidence=0.0,
                sources=[],
            )

    # ── Private helpers ────────────────────────────────────────────────────

    def _match_regulations(
        self, message: str
    ) -> Tuple[Dict[str, Any], float]:
        """Match user message to relevant regulations."""
        msg_lower = message.lower()
        matched: Dict[str, Any] = {}
        matched_count = 0

        for kw, reg_key in KEYWORD_TO_REGULATION.items():
            if kw in msg_lower and reg_key not in matched:
                matched[reg_key] = REGULATION_KNOWLEDGE_BASE[reg_key]
                matched_count += 1

        # Also check regulation keys directly
        for reg_key, reg_data in REGULATION_KNOWLEDGE_BASE.items():
            if reg_key.replace("_", " ") in msg_lower and reg_key not in matched:
                matched[reg_key] = reg_data

        confidence = min(0.90, 0.65 + matched_count * 0.10)
        return matched, confidence

    def _build_situation_context(
        self,
        message: str,
        doc_context: Optional[Dict[str, Any]],
        state: HibiscusState,
    ) -> Dict[str, Any]:
        """Build user's specific situation context."""
        context: Dict[str, Any] = {
            "user_message": message,
        }

        if doc_context and doc_context.get("extraction"):
            extraction = doc_context["extraction"]
            context["policy_type"] = extraction.get("policy_type", "Unknown")
            context["insurer"] = extraction.get("insurer", "Unknown")
            context["policy_term"] = extraction.get("policy_term")
            years_paid = extraction.get("years_paid") or extraction.get("policy_year")
            context["years_paid"] = years_paid
            if years_paid and isinstance(years_paid, (int, float)):
                context["is_contestable"] = int(years_paid) >= 3

        user_profile = state.get("user_profile") or {}
        if user_profile.get("age"):
            context["user_age"] = user_profile["age"]

        return context

    def _build_synthesis_prompt(
        self,
        message: str,
        matched_regulations: Dict[str, Any],
        situation_context: Dict[str, Any],
        is_rights_violation: bool,
        is_distressed: bool,
    ) -> str:
        """Build the synthesis prompt."""
        tone_instruction = ""
        if is_distressed:
            tone_instruction = (
                "\nTONE: User appears frustrated/distressed. Start with acknowledgment: "
                "'I understand this is frustrating. Here is exactly what the law says and what you can do.' "
                "End with empowering statement about their rights."
            )

        if not matched_regulations:
            regs_text = (
                "No specific regulation matched. Provide general IRDAI rights overview:\n"
                + json.dumps(
                    {
                        "key_rights": [
                            "Free look period: 15 days (30 days for online purchase)",
                            "Grievance resolution: 15 days SLA",
                            "Health portability: mandatory",
                            "Death claim: 30 days settlement",
                            "Ombudsman: FREE up to ₹50 lakh",
                        ]
                    },
                    indent=2,
                )
            )
        else:
            regs_text = json.dumps(matched_regulations, indent=2, ensure_ascii=False)

        situation_text = json.dumps(situation_context, indent=2, ensure_ascii=False)

        rights_violation_instruction = ""
        if is_rights_violation:
            rights_violation_instruction = (
                "\nRIGHTS VIOLATION DETECTED: The user may be experiencing a rights violation. "
                "Be explicit about: (a) what the regulation says, (b) that the insurer may be in violation, "
                "(c) exact escalation steps with contacts. "
                "Include: 'IRDAI Bima Bharosa: bimabharosaportal.irdai.gov.in' "
                "and 'Insurance Ombudsman: FREE service — approach within 3 months of rejection'."
            )

        return f"""The user has a question about insurance regulations and consumer rights.
{tone_instruction}
{rights_violation_instruction}

USER'S QUESTION: {message}

USER'S SITUATION CONTEXT:
{situation_text}

MATCHED REGULATIONS (from IRDAI knowledge base — cite these accurately):
{regs_text}

INSTRUCTIONS FOR RESPONSE:
Structure your response in these sections:

**1. What the Regulation Says**
   - Quote the relevant rule accurately
   - Cite the regulation name and number
   - Use simple language

**2. What This Means for You**
   - Apply the regulation to THIS user's specific situation
   - Be specific — not generic

**3. What You Should Do**
   - Numbered action steps
   - Specific contacts / portals
   - Timelines

**4. Your Rights if Violated**
   - Escalation path (insurer grievance → IRDAI portal → Ombudsman → Consumer Forum)
   - Mention: Ombudsman is FREE for claims up to ₹50 lakh
   - IRDAI Bima Bharosa: bimabharosaportal.irdai.gov.in

**5. Verify Current Rules**
   - "For the most current version of this regulation, visit irdai.gov.in"
   - Note if any recent amendments are expected

DATA FRESHNESS: Regulation knowledge base last verified {_LAST_VERIFIED} (source: {_SOURCE}).
Include in your response: "Regulation data last verified: {_LAST_VERIFIED}. Always confirm at irdai.gov.in for the latest version."

CRITICAL: Only cite regulations from the data above. Do not invent regulation numbers or rules.
"""

    def _get_escalation_path(self, matched_regulations: Dict[str, Any]) -> List[str]:
        """Extract escalation paths from matched regulations."""
        paths = set()
        for reg_data in matched_regulations.values():
            if reg_data.get("escalation"):
                paths.add(reg_data["escalation"])
        return list(paths)

    def _build_follow_ups(
        self, matched_regulations: Dict[str, Any], is_rights_violation: bool
    ) -> List[str]:
        """Build follow-up suggestions."""
        follow_ups = []

        if "ombudsman" in matched_regulations or is_rights_violation:
            follow_ups.append("Would you like help finding the ombudsman office in your state?")
            follow_ups.append("Should I help you draft a grievance letter to the insurer?")
        if "portability" in matched_regulations:
            follow_ups.append("Want me to guide you through the portability process step by step?")
        if "free_look_period" in matched_regulations:
            follow_ups.append("Should I help you draft a free look cancellation letter?")
        if "non_disclosure" in matched_regulations:
            follow_ups.append("Would you like to understand how to challenge a rejection under Section 45?")

        if not follow_ups:
            follow_ups = [
                "Do you have a specific situation related to this regulation you want to discuss?",
                "Should I explain the escalation path if your rights are not being respected?",
            ]

        return follow_ups[:3]


# ── Module-level run function (called by agent_dispatch) ──────────────────
_agent = RegulationEngineAgent()


async def run(state: HibiscusState) -> Dict[str, Any]:
    """Entry point for agent_dispatch."""
    return await _agent(state)
