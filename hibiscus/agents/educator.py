"""
EducatorAgent — Agent 9
========================
Insurance concepts educator.

Explains insurance terms, concepts, and product types in plain language
with Indian context, practical examples using ₹ amounts, and relevant
analogies. Targets users with zero prior insurance knowledge.

Source hierarchy:
1. Built-in glossary (deterministic, always available)
2. LLM explanation with concrete Indian examples
3. Practical implication for the user's policy

L1/L2 query fast path — uses Tier 1 (DeepSeek V3.2) for speed.
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
"""
import json
import time
from typing import Any, Dict, List, Optional, Tuple

from hibiscus.agents.base import BaseAgent, AgentResult
from hibiscus.llm.router import call_llm
from hibiscus.observability.logger import PipelineLogger
from hibiscus.orchestrator.state import HibiscusState

AGENT_SYSTEM_PROMPT = """You are Hibiscus, EAZR's insurance educator.

Your role: Make insurance simple. Every concept should be explainable to a 25-year-old with no finance background.

CRITICAL RULES:
1. Define the term FIRST in one sentence, then explain with an example
2. ALWAYS include a practical ₹ example (e.g., "If your sum insured is ₹5 lakh and you have 20% co-pay, you pay ₹1 lakh for a ₹5 lakh claim")
3. Use Indian analogies and contexts
4. Explain WHY this matters for their specific policy (use context if provided)
5. Include common misconceptions for the term
6. Use ₹ symbol, Indian format (lakhs/crores)
7. Language: Simple English, avoid jargon. If term must be used, explain it immediately

TONE: Like a knowledgeable friend explaining something over chai — warm, clear, patient. Never condescending.
"""

# Built-in glossary — ground truth definitions
# LLM uses these as the base and adds examples/context
INSURANCE_GLOSSARY = {
    "sum_insured": {
        "term": "Sum Insured",
        "definition": "The maximum amount your insurer will pay for a single claim or in a policy year. This is the limit of the insurer's liability.",
        "example": "If your health policy has ₹5 lakh sum insured and you are hospitalized for ₹7 lakh, the insurer pays ₹5 lakh and you pay the remaining ₹2 lakh.",
        "common_misconception": "Many people think sum insured is what they get on maturity — that applies to life insurance, not health.",
        "related_terms": ["sum_assured", "coverage_limit", "policy_limit"],
        "section": "Health & Life Insurance basics",
    },
    "sum_assured": {
        "term": "Sum Assured",
        "definition": "The guaranteed amount paid to the nominee/beneficiary on the death of the insured, or to the policyholder on maturity of a life insurance policy.",
        "example": "If your term plan has ₹1 crore sum assured and you pass away during the term, your nominee receives ₹1 crore.",
        "common_misconception": "Sum assured is often confused with sum insured. Sum assured is for life insurance; sum insured is for health/general insurance.",
        "related_terms": ["death_benefit", "maturity_benefit", "sum_insured"],
        "section": "Life Insurance basics",
    },
    "premium": {
        "term": "Premium",
        "definition": "The amount you pay to the insurer (monthly, quarterly, or annually) to keep your insurance policy active.",
        "example": "If your term insurance premium is ₹12,000 per year, you pay ₹1,000 per month. If you miss payment, there is a 30-day grace period before the policy lapses.",
        "common_misconception": "A lower premium is not always better — it may mean lower coverage, more exclusions, or higher co-pay.",
        "related_terms": ["annual_premium", "modal_premium", "grace_period"],
        "section": "Insurance basics",
    },
    "copay": {
        "term": "Co-payment (Copay)",
        "definition": "The percentage of every claim that YOU pay from your own pocket, with the insurer paying the rest. It is a cost-sharing mechanism.",
        "example": "If your health policy has 20% co-pay and your hospital bill is ₹2 lakh, you pay ₹40,000 and the insurer pays ₹1.6 lakh. Policies with co-pay have lower premiums.",
        "common_misconception": "Co-pay is not the same as deductible. Co-pay applies to every claim; deductible is a fixed amount before insurance kicks in.",
        "related_terms": ["deductible", "sub_limit", "out_of_pocket_maximum"],
        "section": "Health Insurance",
    },
    "gsv": {
        "term": "Guaranteed Surrender Value (GSV)",
        "definition": "The minimum amount an insurer MUST pay you if you surrender (exit) a traditional life insurance policy. IRDAI mandates minimum GSV percentages.",
        "example": "If you paid ₹2 lakh in premiums over 5 years, and the GSV factor is 50%, you receive ₹1 lakh on surrender. Note: you lose all future bonuses and life cover.",
        "common_misconception": "GSV is the minimum — the Special Surrender Value (SSV) declared by your insurer may actually be higher. Always ask for both.",
        "related_terms": ["ssv", "surrender_value", "paid_up_value", "irr"],
        "section": "Life Insurance — Surrender",
    },
    "ulip": {
        "term": "Unit Linked Insurance Plan (ULIP)",
        "definition": "A product that combines life insurance with market-linked investments. Part of your premium goes to life cover, part is invested in equity/debt funds.",
        "example": "In a ULIP with ₹1 lakh annual premium: ₹5,000 may go to life cover charges, ₹10,000 to policy charges, and ₹85,000 invested in equity funds. Returns depend on market performance.",
        "common_misconception": "ULIPs do NOT give guaranteed returns. They are investment products with market risk. Anyone who said 'guaranteed 15% returns on ULIP' was mis-selling.",
        "related_terms": ["nav", "fund_value", "mortality_charge", "fund_management_charge"],
        "section": "Life Insurance",
    },
    "nav": {
        "term": "Net Asset Value (NAV)",
        "definition": "The per-unit price of a ULIP fund, calculated as total fund assets divided by number of units. Like the price of a mutual fund unit.",
        "example": "If your ULIP fund NAV is ₹25 and you have 10,000 units, your fund value is ₹2.5 lakh. If NAV rises to ₹30, your fund value becomes ₹3 lakh.",
        "common_misconception": "Higher NAV does not mean it is expensive to buy — it just means the fund has grown. Focus on fund returns, not NAV level.",
        "related_terms": ["ulip", "fund_value", "unit_allocation"],
        "section": "ULIP / Investment-linked Insurance",
    },
    "irr": {
        "term": "Internal Rate of Return (IRR)",
        "definition": "The actual annual return your insurance policy is earning on your money, considering all cash flows (premiums paid vs. maturity received). The honest measure of what your policy is worth financially.",
        "example": "If you pay ₹50,000/year for 20 years (total ₹10 lakh) and get ₹15 lakh on maturity, the IRR is approximately 4.5-5% per year. Compare this to FD at 7.5% to evaluate if the policy is worth it.",
        "common_misconception": "Many people are sold policies with 'returns of ₹X on maturity' without knowing the IRR. A ₹15 lakh maturity on ₹10 lakh invested over 20 years sounds good but is actually less than FD returns.",
        "related_terms": ["gsv", "maturity_benefit", "yield"],
        "section": "Life Insurance — Returns",
    },
    "cashless": {
        "term": "Cashless Hospitalization",
        "definition": "A facility where your insurer directly settles the hospital bill without you paying upfront. Only available at network hospitals empanelled by your insurer.",
        "example": "You are admitted to a network hospital. The hospital sends a pre-authorization request to your TPA. Once approved, the insurer pays the bill directly. You only pay non-covered items.",
        "common_misconception": "Cashless does not mean ALL expenses are paid. Items not covered by your policy (room upgrades, consumables in some policies) are still out-of-pocket.",
        "related_terms": ["network_hospital", "tpa", "reimbursement", "pre_authorization"],
        "section": "Health Insurance — Claims",
    },
    "tpa": {
        "term": "Third Party Administrator (TPA)",
        "definition": "A company hired by your insurer to manage health insurance claims, network hospitals, and pre-authorizations. They are the middleman between you and the insurer.",
        "example": "When you get admitted, the hospital calls your TPA (e.g., Vidal Health, Medi Assist) for pre-authorization. The TPA approves/rejects the cashless request on behalf of the insurer.",
        "common_misconception": "The TPA is not the insurer. If TPA rejects your claim, you can still escalate to the insurer directly.",
        "related_terms": ["cashless", "network_hospital", "pre_authorization"],
        "section": "Health Insurance — Operations",
    },
    "deductible": {
        "term": "Deductible",
        "definition": "A fixed amount you agree to pay from your pocket on each claim before the insurance kicks in. Higher deductible = lower premium.",
        "example": "If your health policy has ₹25,000 deductible and you file a claim for ₹2 lakh, you pay the first ₹25,000 and insurer pays ₹1.75 lakh.",
        "common_misconception": "Deductible vs Co-pay: Deductible is a FIXED amount per claim. Co-pay is a PERCENTAGE of every claim. Many policies have both.",
        "related_terms": ["copay", "sublimit", "out_of_pocket"],
        "section": "Health Insurance",
    },
    "csr": {
        "term": "Claim Settlement Ratio (CSR)",
        "definition": "The percentage of death claims settled by a life insurer in a year. For example, a CSR of 98% means the insurer settled 98 out of 100 death claims received.",
        "example": "If LIC has CSR of 98.6%, it means for every 100 death claims received, 98-99 were paid. A CSR above 97% is generally considered good for life insurance.",
        "common_misconception": "CSR alone is not enough to evaluate an insurer — also check the reasons for rejection (1.4% rejected) and average time to settlement.",
        "related_terms": ["icr", "insurer_rating", "death_claim"],
        "section": "Life Insurance — Evaluating Insurers",
    },
    "icr": {
        "term": "Incurred Claim Ratio (ICR)",
        "definition": "The ratio of total claims paid to total premium collected by a health insurer. An ICR of 80% means the insurer paid ₹80 in claims for every ₹100 premium collected.",
        "example": "If Star Health has ICR of 65%, it paid ₹65 in claims per ₹100 premium. This implies the insurer made good profit — but may also mean they are more strict with claims.",
        "common_misconception": "Very low ICR (<50%) may mean the insurer is too strict with claims. Very high ICR (>100%) means the insurer is losing money and may raise premiums. The sweet spot is 65-85%.",
        "related_terms": ["csr", "loss_ratio", "insurer_evaluation"],
        "section": "Health Insurance — Evaluating Insurers",
    },
    "free_look": {
        "term": "Free Look Period",
        "definition": "A window of 15 days (30 days for online policies) after you receive a policy to read it and return it for a full refund if you are not satisfied.",
        "example": "You buy a health policy online. If within 30 days you realize the terms are different from what was explained, you can return it and get a refund (minus small charges).",
        "common_misconception": "Many people don't know about this right. If you were mis-sold a policy, use the free look period — it's one of your strongest consumer rights under IRDAI.",
        "related_terms": ["cooling_off", "policy_cancellation", "irdai_rights"],
        "section": "Consumer Rights",
    },
    "portability": {
        "term": "Health Insurance Portability",
        "definition": "Your right to switch your health insurance to another insurer without losing the waiting period credits you have already earned.",
        "example": "If you have a 4-year-old health policy with 3-year PED waiting served, and you port to a new insurer, they MUST give you credit for those 3 years. You won't restart the waiting period.",
        "common_misconception": "Many people stay with a bad health insurer thinking they will lose waiting period credits if they switch. This is wrong — portability protects you.",
        "related_terms": ["waiting_period", "ped", "switch_insurer"],
        "section": "Health Insurance — Consumer Rights",
    },
    "loading": {
        "term": "Premium Loading",
        "definition": "An additional charge added to your standard premium by the insurer due to health risk factors (existing illness, BMI, age). Makes your premium higher than the standard rate.",
        "example": "Standard premium for a 35-year-old is ₹8,000/year. Due to diabetes, insurer loads 30% extra — you pay ₹10,400. This is called a 30% loading.",
        "common_misconception": "Loading is not the same as permanent exclusion. You pay more, but your PED may still be covered after the waiting period.",
        "related_terms": ["ped", "exclusion", "premium"],
        "section": "Health Insurance",
    },
    "maturity_benefit": {
        "term": "Maturity Benefit",
        "definition": "The lump sum amount paid by the insurer at the end of the policy term, if the policyholder is alive. This is a feature of endowment and money-back policies, not term insurance.",
        "example": "A 20-year endowment policy with sum assured ₹10 lakh may pay ₹18 lakh at maturity (sum assured + accumulated bonuses). The effective IRR may be 4-5%.",
        "common_misconception": "Term insurance has NO maturity benefit — it only pays on death. If you want pure protection + savings, they should be in separate products.",
        "related_terms": ["sum_assured", "irr", "survival_benefit"],
        "section": "Life Insurance",
    },
}

# Keyword-to-term mapping for fast lookup
KEYWORD_TO_TERM = {}
for term_key, term_data in INSURANCE_GLOSSARY.items():
    KEYWORD_TO_TERM[term_key.replace("_", " ")] = term_key
    KEYWORD_TO_TERM[term_data["term"].lower()] = term_key
    # Also add related terms
    for related in term_data.get("related_terms", []):
        if related not in KEYWORD_TO_TERM:
            KEYWORD_TO_TERM[related.replace("_", " ")] = term_key


class EducatorAgent(BaseAgent):
    """Explains insurance concepts in plain language with Indian examples."""

    name = "educator"
    description = "Insurance concepts educator"
    default_tier = "deepseek_v3"  # L1/L2 fast path — Tier 1

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

            # ── Step 1: Find the term(s) being asked about ─────────────────
            plog.step_start("term_lookup")
            matched_terms, match_confidence = self._lookup_terms(message)
            plog.step_complete(
                "term_lookup",
                matched=list(matched_terms.keys()),
                confidence=match_confidence,
            )

            # ── Step 2: Get policy context (if document uploaded) ──────────
            policy_context = self._extract_policy_context(state)

            # ── Step 3: LLM explanation using glossary data ────────────────
            plog.step_start("llm_explanation")
            synthesis_prompt = self._build_synthesis_prompt(
                message=message,
                matched_terms=matched_terms,
                policy_context=policy_context,
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
            plog.step_complete("llm_explanation")

            # ── Step 4: Sources and confidence ────────────────────────────
            sources = []
            if matched_terms:
                sources.append({
                    "type": "glossary",
                    "reference": "EAZR Insurance Glossary — IRDAI-standard definitions",
                    "confidence": 0.92,
                })
            else:
                sources.append({
                    "type": "knowledge_base",
                    "reference": "General insurance knowledge",
                    "confidence": 0.75,
                })

            confidence = 0.90 if matched_terms else 0.72
            latency_ms = int((time.time() - start) * 1000)

            return AgentResult(
                response=response_text,
                confidence=confidence,
                sources=sources,
                latency_ms=latency_ms,
                tokens_in=llm_response.get("tokens_in", 0),
                tokens_out=llm_response.get("tokens_out", 0),
                structured_data={
                    "terms_explained": list(matched_terms.keys()),
                    "from_glossary": bool(matched_terms),
                },
                follow_up_suggestions=self._build_follow_ups(matched_terms),
            )

        except Exception as e:
            plog.error("educator", error=str(e))
            return AgentResult(
                response=self._error_response(),
                confidence=0.0,
                sources=[],
            )

    # ── Private helpers ────────────────────────────────────────────────────

    def _lookup_terms(
        self, message: str
    ) -> Tuple[Dict[str, Any], float]:
        """Find matching glossary terms in the user's message."""
        msg_lower = message.lower()
        matched: Dict[str, Any] = {}

        # Direct glossary key matches
        for term_key, term_data in INSURANCE_GLOSSARY.items():
            term_name = term_data["term"].lower()
            if term_name in msg_lower or term_key.replace("_", " ") in msg_lower:
                matched[term_key] = term_data

        # Keyword mapping
        for kw, term_key in KEYWORD_TO_TERM.items():
            if kw in msg_lower and term_key not in matched:
                matched[term_key] = INSURANCE_GLOSSARY[term_key]

        confidence = min(0.92, 0.65 + len(matched) * 0.10)
        return matched, confidence

    def _extract_policy_context(self, state: HibiscusState) -> Optional[Dict[str, Any]]:
        """Extract relevant policy context to make explanation specific."""
        doc_context = state.get("document_context")
        if not doc_context or not doc_context.get("extraction"):
            return None

        extraction = doc_context["extraction"]
        return {
            "policy_type": extraction.get("policy_type", ""),
            "insurer": extraction.get("insurer", ""),
            "sum_insured": extraction.get("sum_insured") or extraction.get("sum_assured"),
            "copay": extraction.get("copay"),
            "room_rent_sublimit": extraction.get("room_rent_sublimit"),
            "premium": extraction.get("annual_premium") or extraction.get("premium"),
        }

    def _build_synthesis_prompt(
        self,
        message: str,
        matched_terms: Dict[str, Any],
        policy_context: Optional[Dict[str, Any]],
    ) -> str:
        """Build explanation prompt."""
        if matched_terms:
            terms_text = json.dumps(matched_terms, indent=2, ensure_ascii=False)
            source_note = "Use the glossary definitions as the authoritative base. Add examples and analogies."
        else:
            terms_text = "No exact match found in glossary — explain based on general insurance knowledge."
            source_note = "No glossary match. Explain based on general knowledge but flag if the term is non-standard."

        context_text = ""
        if policy_context:
            context_text = f"""
USER'S POLICY CONTEXT (use this to make explanation specific):
{json.dumps(policy_context, indent=2, ensure_ascii=False)}
"""

        return f"""The user wants to understand an insurance term or concept.

USER'S QUESTION: {message}

GLOSSARY DATA ({source_note}):
{terms_text}
{context_text}

INSTRUCTIONS FOR RESPONSE:

Structure your explanation as follows:

**[Term Name]** — [one-sentence definition]

**Simple Explanation:**
[Explain in 2-3 sentences as if talking to someone with zero finance knowledge. Use analogy.]

**Example with ₹:**
[Concrete numerical example using realistic Indian amounts]

**Why This Matters for You:**
[If policy context is available: explain how this applies to THEIR policy specifically]
[If no policy context: explain why this matters generally]

**Common Misconception:**
[One thing people often get wrong about this term]

**Related Terms:**
[2-3 related terms they might also want to know — brief 1-line explanation each]

RULES:
1. Definition must come FIRST — one clear sentence
2. Example MUST use ₹ amounts
3. Use Indian analogies (chai shop, cricket, train journey — if relevant)
4. If user asked about multiple terms: explain the most relevant one fully, mention others briefly
5. If term not in glossary: explain based on general knowledge and say "this is a general explanation"
6. End with: "Want me to explain any related term in detail?"
"""

    def _build_follow_ups(self, matched_terms: Dict[str, Any]) -> List[str]:
        """Build follow-up suggestions based on explained terms."""
        follow_ups = []

        if "copay" in matched_terms or "deductible" in matched_terms:
            follow_ups.append("Would you like to see how copay affects your out-of-pocket cost with your actual policy numbers?")
        if "irr" in matched_terms or "gsv" in matched_terms:
            follow_ups.append("Should I calculate the IRR of your policy to show the actual returns?")
        if "csr" in matched_terms or "icr" in matched_terms:
            follow_ups.append("Would you like to see the CSR/ICR data for your insurer from the latest IRDAI report?")
        if "portability" in matched_terms:
            follow_ups.append("Want me to guide you through the health insurance portability process?")
        if "ulip" in matched_terms or "nav" in matched_terms:
            follow_ups.append("Should I explain the charges in a ULIP and how they impact your investment?")

        if not follow_ups:
            follow_ups = [
                "Is there another insurance term you'd like me to explain?",
                "Would you like me to apply this concept to your specific policy?",
            ]

        return follow_ups[:3]


# ── Module-level run function (called by agent_dispatch) ──────────────────
_agent = EducatorAgent()


async def run(state: HibiscusState) -> Dict[str, Any]:
    """Entry point for agent_dispatch."""
    return await _agent(state)
