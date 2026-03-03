"""
RecommenderAgent — Agent 3
===========================
Insurance product recommender.

Suggests appropriate insurance products based on user profile, coverage gaps,
existing policies, and financial situation.

Depends on PolicyAnalyzerAgent output when a document is uploaded — the gaps
identified by the analyzer feed directly into the recommendation logic.

RULES:
- NEVER state specific premium without a verified source
- NEVER say "guaranteed returns"
- NEVER recommend a specific policy as "the best"
- ALWAYS add IRDAI disclaimer
- ALWAYS explain WHY each product is recommended
- ALWAYS mention that comparison is based on available data
"""
import json
import time
from typing import Any, Dict, List, Optional

from hibiscus.agents.base import BaseAgent, AgentResult
from hibiscus.llm.router import call_llm
from hibiscus.observability.logger import PipelineLogger
from hibiscus.orchestrator.state import HibiscusState

AGENT_SYSTEM_PROMPT = """You are Hibiscus, EAZR's insurance AI assistant specializing in product recommendations.

Your role: Help users find the RIGHT type of insurance for their situation — not a specific product, but the right product category, features to look for, and why.

CRITICAL RULES:
1. NEVER recommend a specific insurer's policy as definitively "the best" — use phrases like "policies of this type" or "insurers offering high CSR"
2. NEVER state exact premiums unless sourced — use "typically ranges from ₹X to ₹Y" with a disclaimer
3. NEVER say "guaranteed returns" for any product — use accurate terms (projected, illustrated, not guaranteed)
4. ALWAYS explain the recommendation rationale (why this product for this user)
5. ALWAYS mention Claim Settlement Ratio (CSR) and Incurred Claim Ratio (ICR) as evaluation criteria
6. ALWAYS add IRDAI disclaimer at the end
7. Use ₹ symbol, Indian format (lakhs/crores)
8. Mention EAZR's comparison tool for getting actual quotes

APPROACH: Think like an independent financial advisor — prioritize user's needs over product features.
"""

# Coverage gap to product type mapping
GAP_TO_PRODUCT_MAP = {
    "no_term_life": {
        "product_type": "Term Life Insurance",
        "rationale": "Provides pure death benefit at lowest cost",
        "key_features": ["High sum assured (10-20x annual income)", "Low premium", "Pure protection"],
        "csr_importance": "Critical — look for CSR > 98%",
        "avoid": "Don't confuse with endowment/ULIP — term is pure protection",
    },
    "low_life_cover": {
        "product_type": "Additional Term Life Insurance",
        "rationale": "Existing life cover is insufficient — needs top-up",
        "key_features": ["Coverage gap fill", "Ladder coverage strategy"],
        "csr_importance": "Critical",
        "avoid": "Don't add endowment to increase life cover — use term only",
    },
    "no_health": {
        "product_type": "Individual / Family Floater Health Insurance",
        "rationale": "No health protection — any hospitalization creates financial emergency",
        "key_features": ["Network hospitals", "No sub-limits on room rent", "Restoration benefit"],
        "csr_importance": "ICR > 75% indicates fair claim settlement",
        "avoid": "Avoid policies with room rent sub-limits and many exclusions",
    },
    "low_health_cover": {
        "product_type": "Health Insurance Top-Up / Super Top-Up",
        "rationale": "Existing health cover is below city standard — super top-up is cost-effective upgrade",
        "key_features": ["Super top-up over existing base plan", "High deductible = low premium"],
        "csr_importance": "Same insurer as base plan preferred for seamless claims",
        "avoid": "Do not add a second standalone policy — super top-up is more efficient",
    },
    "no_critical_illness": {
        "product_type": "Critical Illness (CI) Insurance",
        "rationale": "No CI cover — a cancer or cardiac event would drain savings",
        "key_features": ["Lump sum on diagnosis", "Covers 30+ critical illnesses", "Income replacement"],
        "csr_importance": "Look for broad coverage (36+ CIs) and no survival clause",
        "avoid": "Avoid CI as a rider on a limited base policy — standalone CI is better",
    },
    "no_personal_accident": {
        "product_type": "Personal Accident Insurance",
        "rationale": "No disability or accidental death cover — very low cost, high protection",
        "key_features": ["Accidental death", "Permanent disability", "Daily hospital cash"],
        "csr_importance": "Look for global coverage and temporary disability benefit",
        "avoid": "Check exclusion list carefully (adventure sports etc.)",
    },
}

# Income-based sum assured guidelines
LIFE_COVER_GUIDELINES = {
    "minimum_multiplier": 10,
    "recommended_multiplier": 15,
    "ideal_multiplier": 20,
    "note": "Income replacement method: cover = annual income × multiplier",
}

# Health cover by city tier
HEALTH_COVER_GUIDELINES = {
    "metro": {
        "minimum": 1_000_000,  # 10 lakhs
        "recommended": 2_500_000,  # 25 lakhs
        "cities": ["Mumbai", "Delhi", "Bengaluru", "Chennai", "Hyderabad", "Pune", "Kolkata"],
    },
    "tier2": {
        "minimum": 500_000,  # 5 lakhs
        "recommended": 1_000_000,  # 10 lakhs
        "cities": ["other"],
    },
}


class RecommenderAgent(BaseAgent):
    """Recommends insurance products based on user profile and coverage gaps."""

    name = "recommender"
    description = "Insurance product recommender"
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
            # ── Step 1: Extract user profile and existing coverage ─────────
            plog.step_start("extract_user_profile")
            user_profile = state.get("user_profile") or {}
            policy_portfolio = state.get("policy_portfolio") or []
            message = state.get("message", "")

            # Extract profile from message if not in state
            parsed_profile = self._parse_profile_from_message(message)
            merged_profile = {**user_profile, **parsed_profile}

            plog.step_complete("extract_user_profile", has_profile=bool(merged_profile))

            # ── Step 2: Get identified gaps from PolicyAnalyzer output ─────
            plog.step_start("collect_gaps")
            gaps = self._collect_gaps(state)
            plog.step_complete("collect_gaps", gaps_found=len(gaps))

            # ── Step 3: Map gaps to product recommendations ────────────────
            plog.step_start("map_gaps_to_products")
            product_recommendations = self._map_gaps_to_products(gaps, merged_profile)
            plog.step_complete("map_gaps_to_products", recommendations=len(product_recommendations))

            # ── Step 4: Compute coverage adequacy numbers ──────────────────
            adequacy_analysis = self._compute_coverage_adequacy(merged_profile, policy_portfolio)

            # ── Step 5: Build LLM synthesis prompt ────────────────────────
            plog.step_start("llm_synthesis")
            synthesis_prompt = self._build_synthesis_prompt(
                user_profile=merged_profile,
                policy_portfolio=policy_portfolio,
                gaps=gaps,
                product_recommendations=product_recommendations,
                adequacy_analysis=adequacy_analysis,
                message=message,
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

            # ── Step 6: Build sources ──────────────────────────────────────
            sources = [
                {
                    "type": "knowledge_base",
                    "reference": "IRDAI Annual Report 2023-24 — Claim Settlement Ratios",
                    "confidence": 0.85,
                },
                {
                    "type": "knowledge_base",
                    "reference": "IRDAI Insurance Market Data — Product Coverage Guidelines",
                    "confidence": 0.85,
                },
            ]
            if gaps:
                sources.append({
                    "type": "agent_output",
                    "reference": "PolicyAnalyzerAgent — identified coverage gaps",
                    "confidence": 0.80,
                })

            # Confidence: high if we have profile + gaps, medium if only message
            confidence = 0.85 if (merged_profile and gaps) else (0.75 if merged_profile else 0.65)

            latency_ms = int((time.time() - start) * 1000)

            return AgentResult(
                response=response_text,
                confidence=confidence,
                sources=sources,
                latency_ms=latency_ms,
                tokens_in=llm_response.get("tokens_in", 0),
                tokens_out=llm_response.get("tokens_out", 0),
                structured_data={
                    "gaps_identified": gaps,
                    "products_recommended": [r["product_type"] for r in product_recommendations],
                    "adequacy_analysis": adequacy_analysis,
                    "user_profile_used": merged_profile,
                },
                follow_up_suggestions=[
                    "Would you like me to explain any of these product types in detail?",
                    "Should I calculate how much premium you'd typically pay for term insurance?",
                    "Want me to check what tax benefits these products offer?",
                ],
                eazr_products_relevant=self._check_ipf_relevance(merged_profile, policy_portfolio),
            )

        except Exception as e:
            plog.error("recommender", error=str(e))
            return AgentResult(
                response=self._error_response(),
                confidence=0.0,
                sources=[],
            )

    # ── Private helpers ────────────────────────────────────────────────────

    def _parse_profile_from_message(self, message: str) -> Dict[str, Any]:
        """Parse basic profile details from user message."""
        import re
        profile: Dict[str, Any] = {}
        msg_lower = message.lower()

        # Age
        age_match = re.search(r"\b(\d{2})\s*(?:years?\s+old|year\s+old|yr\s+old|yrs?\s+old)\b", msg_lower)
        if not age_match:
            age_match = re.search(r"\bage\s+(?:is\s+)?(\d{2})\b", msg_lower)
        if age_match:
            profile["age"] = int(age_match.group(1))

        # Annual income
        income_patterns = [
            r"(?:annual\s+)?income\s+(?:of\s+)?(?:₹|rs\.?|inr)?\s*([\d,]+(?:\.\d+)?)\s*(lakh|crore|l|cr)?",
            r"earn(?:ing)?\s+(?:₹|rs\.?|inr)?\s*([\d,]+(?:\.\d+)?)\s*(lakh|crore|l|cr)?",
            r"salary\s+(?:of\s+)?(?:₹|rs\.?|inr)?\s*([\d,]+(?:\.\d+)?)\s*(lakh|crore|l|cr)?",
        ]
        for pattern in income_patterns:
            m = re.search(pattern, msg_lower)
            if m:
                amount = float(m.group(1).replace(",", ""))
                unit = (m.group(2) or "").strip()
                if unit in ("lakh", "l"):
                    amount *= 100_000
                elif unit in ("crore", "cr"):
                    amount *= 10_000_000
                profile["annual_income"] = amount
                break

        # City tier
        metro_cities = ["mumbai", "delhi", "bengaluru", "bangalore", "chennai", "hyderabad", "pune", "kolkata"]
        if any(city in msg_lower for city in metro_cities):
            profile["city_tier"] = "metro"

        # Family size
        family_match = re.search(r"(\d+)\s+(?:family\s+)?members?", msg_lower)
        if family_match:
            profile["family_size"] = int(family_match.group(1))
        if "spouse" in msg_lower or "wife" in msg_lower or "husband" in msg_lower:
            profile["has_spouse"] = True
        if "child" in msg_lower or "children" in msg_lower or "kids" in msg_lower:
            profile["has_children"] = True

        return profile

    def _collect_gaps(self, state: HibiscusState) -> List[str]:
        """
        Collect identified coverage gaps from:
        1. PolicyAnalyzerAgent output (in agent_outputs)
        2. State fields
        3. User message keywords
        """
        gaps: List[str] = []
        message = state.get("message", "").lower()

        # From previous agent outputs
        for output in state.get("agent_outputs", []):
            if isinstance(output, dict):
                structured = output.get("structured_data", {})
                if structured.get("gaps"):
                    gaps.extend(structured["gaps"])
                if structured.get("coverage_gaps"):
                    gaps.extend(structured["coverage_gaps"])

        # From document context
        doc_context = state.get("document_context")
        if doc_context and doc_context.get("extraction"):
            extraction = doc_context["extraction"]
            policy_type = (extraction.get("policy_type") or "").lower()
            # If they only have health, flag missing life
            if "health" in policy_type and "life" not in policy_type:
                if "no_term_life" not in gaps:
                    gaps.append("no_term_life")
            # Check health coverage adequacy
            sum_insured = extraction.get("sum_insured") or extraction.get("sum_assured")
            if sum_insured and float(str(sum_insured).replace(",", "")) < 500_000:
                if "low_health_cover" not in gaps:
                    gaps.append("low_health_cover")

        # From message keywords
        gap_keywords = {
            "term": "no_term_life",
            "life insurance": "no_term_life",
            "health": "no_health",
            "medical": "no_health",
            "critical illness": "no_critical_illness",
            "cancer": "no_critical_illness",
            "accident": "no_personal_accident",
            "disability": "no_personal_accident",
        }
        for keyword, gap in gap_keywords.items():
            if keyword in message and "already have" not in message:
                if "recommend" in message or "need" in message or "want" in message or "looking" in message:
                    if gap not in gaps:
                        gaps.append(gap)

        # Default: if no gaps found, provide general guidance
        if not gaps and ("recommend" in message or "need" in message or "suggest" in message):
            gaps = ["general_review"]

        return list(set(gaps))

    def _map_gaps_to_products(
        self, gaps: List[str], profile: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Map identified gaps to specific product recommendations."""
        recommendations = []

        for gap in gaps:
            if gap in GAP_TO_PRODUCT_MAP:
                rec = dict(GAP_TO_PRODUCT_MAP[gap])
                rec["gap"] = gap
                # Add profile-specific customization
                rec = self._customize_recommendation(rec, gap, profile)
                recommendations.append(rec)

        # If no specific gaps, provide general framework
        if not recommendations:
            recommendations = [
                {
                    "product_type": "Term Life Insurance",
                    "rationale": "Foundation of any insurance portfolio — pure protection at lowest cost",
                    "key_features": LIFE_COVER_GUIDELINES,
                    "gap": "general",
                },
                {
                    "product_type": "Health Insurance",
                    "rationale": "Medical inflation in India is 15%+ — essential for financial protection",
                    "key_features": ["₹10L+ for metro cities", "Restore benefit", "No room rent cap"],
                    "gap": "general",
                },
            ]

        return recommendations

    def _customize_recommendation(
        self, rec: Dict[str, Any], gap: str, profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Add profile-specific numbers to recommendation."""
        annual_income = profile.get("annual_income", 0)
        age = profile.get("age", 35)
        city_tier = profile.get("city_tier", "tier2")

        if gap in ("no_term_life", "low_life_cover") and annual_income:
            min_cover = annual_income * LIFE_COVER_GUIDELINES["minimum_multiplier"]
            rec_cover = annual_income * LIFE_COVER_GUIDELINES["recommended_multiplier"]
            rec["recommended_sum_assured"] = {
                "minimum": self._format_currency(min_cover),
                "recommended": self._format_currency(rec_cover),
                "basis": f"Income replacement: {LIFE_COVER_GUIDELINES['minimum_multiplier']}-{LIFE_COVER_GUIDELINES['recommended_multiplier']}x annual income",
            }

        if gap in ("no_health", "low_health_cover"):
            city_key = "metro" if city_tier == "metro" else "tier2"
            guide = HEALTH_COVER_GUIDELINES[city_key]
            rec["recommended_sum_insured"] = {
                "minimum": self._format_currency(guide["minimum"]),
                "recommended": self._format_currency(guide["recommended"]),
                "basis": f"City-based adequacy: {city_key} standard",
            }

        return rec

    def _compute_coverage_adequacy(
        self, profile: Dict[str, Any], portfolio: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Compute coverage adequacy ratios based on profile and portfolio."""
        annual_income = profile.get("annual_income", 0)
        age = profile.get("age", 35)
        city_tier = profile.get("city_tier", "tier2")

        total_life_cover = 0.0
        total_health_cover = 0.0
        has_ci = False
        has_pa = False

        for policy in portfolio:
            ptype = (policy.get("type") or policy.get("policy_type") or "").lower()
            sa = float(str(policy.get("sum_assured") or policy.get("sum_insured") or 0).replace(",", ""))
            if "term" in ptype or "life" in ptype or "endowment" in ptype:
                total_life_cover += sa
            if "health" in ptype or "medical" in ptype:
                total_health_cover += sa
            if "critical" in ptype:
                has_ci = True
            if "accident" in ptype or "personal accident" in ptype:
                has_pa = True

        adequacy: Dict[str, Any] = {}

        if annual_income:
            required_life = annual_income * LIFE_COVER_GUIDELINES["recommended_multiplier"]
            adequacy["life"] = {
                "current": self._format_currency(total_life_cover),
                "required": self._format_currency(required_life),
                "adequate": total_life_cover >= required_life,
                "gap": self._format_currency(max(0, required_life - total_life_cover)) if total_life_cover < required_life else None,
            }

        city_key = "metro" if city_tier == "metro" else "tier2"
        min_health = HEALTH_COVER_GUIDELINES[city_key]["minimum"]
        adequacy["health"] = {
            "current": self._format_currency(total_health_cover),
            "minimum_required": self._format_currency(min_health),
            "adequate": total_health_cover >= min_health,
            "city_standard": city_key,
        }

        adequacy["critical_illness"] = {"covered": has_ci}
        adequacy["personal_accident"] = {"covered": has_pa}

        return adequacy

    def _build_synthesis_prompt(
        self,
        user_profile: Dict[str, Any],
        policy_portfolio: List[Dict[str, Any]],
        gaps: List[str],
        product_recommendations: List[Dict[str, Any]],
        adequacy_analysis: Dict[str, Any],
        message: str,
    ) -> str:
        """Build prompt for LLM with all pre-computed analysis."""
        profile_text = json.dumps(user_profile, indent=2, ensure_ascii=False) if user_profile else "Not provided — use general guidance"
        portfolio_text = json.dumps(policy_portfolio[:5], indent=2, ensure_ascii=False) if policy_portfolio else "No portfolio data available"
        gaps_text = ", ".join(gaps) if gaps else "No specific gaps identified — provide general guidance"
        recommendations_text = json.dumps(product_recommendations, indent=2, ensure_ascii=False)
        adequacy_text = json.dumps(adequacy_analysis, indent=2, ensure_ascii=False) if adequacy_analysis else "Not computed"

        return f"""The user is asking for insurance product recommendations.

USER'S REQUEST: {message}

USER PROFILE (use this for personalization):
{profile_text}

EXISTING POLICY PORTFOLIO:
{portfolio_text}

IDENTIFIED COVERAGE GAPS:
{gaps_text}

PRE-COMPUTED COVERAGE ADEQUACY:
{adequacy_text}

PRODUCT RECOMMENDATIONS (based on gap analysis — present these):
{recommendations_text}

INSTRUCTIONS FOR RESPONSE:
1. Open with a brief assessment of the user's current situation (1-2 sentences)
2. Present Top 3 recommendations (or fewer if gaps < 3) in this format:
   **[Product Type]**
   - Why recommended: [personalized rationale]
   - What to look for: [3-4 specific features]
   - Approximate budget: [range if known, otherwise "varies by age/health — get quotes"]
   - What to avoid: [common pitfalls]
   - How to evaluate: [CSR/ICR criteria]

3. For each product, explicitly state WHY it fits THIS user's situation
4. Use the adequacy numbers computed above (current vs required coverage)
5. Do NOT recommend specific policy names — recommend product types and criteria
6. Do NOT state exact premiums without a source — use indicative ranges
7. Suggest using EAZR to compare actual quotes from multiple insurers
8. Mention that CSR (Claim Settlement Ratio) and ICR (Incurred Claim Ratio) are key evaluation metrics
9. End with IRDAI disclaimer: "Insurance recommendations are for educational purposes. Please consult a licensed insurance advisor before purchasing."
10. Add 2-3 follow-up questions the user might want to ask

Be specific and actionable. A user should know exactly what product to search for after reading this.
"""

    def _check_ipf_relevance(
        self, profile: Dict[str, Any], portfolio: List[Dict[str, Any]]
    ) -> List[str]:
        """Check if IPF product is relevant for this user."""
        products = []
        annual_income = profile.get("annual_income", 0)
        if annual_income and annual_income > 1_500_000:  # Above 15 LPA
            products.append("IPF")
        for policy in portfolio:
            premium = float(str(policy.get("annual_premium") or policy.get("premium") or 0).replace(",", ""))
            if premium > 50_000:
                if "IPF" not in products:
                    products.append("IPF")
                break
        return products


# ── Module-level run function (called by agent_dispatch) ──────────────────
_agent = RecommenderAgent()


async def run(state: HibiscusState) -> Dict[str, Any]:
    """Entry point for agent_dispatch."""
    return await _agent(state)
