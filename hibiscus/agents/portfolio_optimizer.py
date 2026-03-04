"""
🌺 Hibiscus v0.9 | EAZR AI Insurance Intelligence Engine
Portfolio optimizer agent — coverage gap detection, rebalancing, family-wide optimization.
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
"""
import json
import time
from typing import Any, Dict, List, Optional, Tuple

from hibiscus.agents.base import BaseAgent, AgentResult
from hibiscus.llm.router import call_llm
from hibiscus.observability.logger import PipelineLogger
from hibiscus.orchestrator.state import HibiscusState


# Scoring weights for portfolio score (0-100)
#
# Weight rationale (based on Indian insurance advisory best practices):
#   life_cover_adequacy  (30%) — Breadwinner protection: income replacement is the
#       single most catastrophic gap; losing an earner with no term cover can
#       devastate a family financially.
#   health_cover_adequacy (30%) — Medical inflation in India runs at ~15% p.a.;
#       an uninsured hospitalization (especially in metros) is a top cause of
#       household financial distress.
#   critical_illness     (15%) — CI events (cancer, cardiac) incur lump-sum costs
#       of ₹5L-₹50L+ that regular health policies may only partially cover.
#   personal_accident    (10%) — PA/disability cover is very low cost yet protects
#       against income loss from disability; lower weight because the premium
#       outlay is minimal and risk is narrower than life/health.
#   no_redundancy        (10%) — Overlapping policies waste premium without adding
#       meaningful coverage; consolidation improves cost efficiency.
#   premium_efficiency    (5%) — Spending within the 5-10% of income guideline
#       ensures sustainability; lowest weight because it is a soft guideline,
#       not a coverage gap.
PORTFOLIO_SCORING_WEIGHTS = {
    "life_cover_adequacy": 30,      # Breadwinner protection (10-15x income)
    "health_cover_adequacy": 30,    # Medical inflation hedge (city-based)
    "critical_illness": 15,         # Lump-sum CI event protection
    "personal_accident": 10,        # Low-cost disability / accidental death cover
    "no_redundancy": 10,            # Eliminate wasteful overlapping policies
    "premium_efficiency": 5,        # Keep spend within 5-10% of income
}

# Minimum health cover benchmarks
HEALTH_BENCHMARKS = {
    "metro": {"minimum": 1_000_000, "ideal": 2_500_000},
    "tier2": {"minimum": 500_000, "ideal": 1_000_000},
}

# Life cover multipliers
LIFE_MULTIPLIERS = {
    "minimum": 10,
    "recommended": 15,
}


class PortfolioOptimizerAgent(BaseAgent):
    """Reviews and optimizes the user's insurance portfolio."""

    name = "portfolio_optimizer"
    description = "Insurance portfolio optimizer"
    default_tier = "deepseek_r1"  # Multi-step analysis — Tier 2
    prompt_file = "portfolio_optimizer.txt"

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
            user_profile = state.get("user_profile") or {}
            portfolio = state.get("policy_portfolio") or []

            # Include current document in portfolio if not already there
            doc_context = state.get("document_context")
            if doc_context and doc_context.get("extraction"):
                doc_policy = dict(doc_context["extraction"])
                doc_policy["_source"] = "uploaded_document"
                # Deduplicate by insurer + type
                existing_types = {
                    (p.get("policy_type") or p.get("type"), p.get("insurer"))
                    for p in portfolio
                }
                doc_key = (
                    doc_policy.get("policy_type") or doc_policy.get("type"),
                    doc_policy.get("insurer"),
                )
                if doc_key not in existing_types:
                    portfolio = [doc_policy] + list(portfolio)

            # ── Step 1: Analyze portfolio ──────────────────────────────────
            plog.step_start("portfolio_analysis")

            if not portfolio and not user_profile:
                return AgentResult(
                    response=(
                        "To optimize your insurance portfolio, I need either:\n"
                        "1. Upload your policy documents (I'll extract details automatically), or\n"
                        "2. Tell me about your policies: type (term/health/ULIP), insurer, sum assured, and annual premium\n\n"
                        "Also helpful: your annual income and city — to check coverage adequacy."
                    ),
                    confidence=0.7,
                    sources=[],
                )

            coverage_analysis = self._analyze_coverage(portfolio, user_profile)
            redundancy_analysis = self._analyze_redundancy(portfolio)
            efficiency_analysis = self._analyze_premium_efficiency(portfolio, user_profile)
            portfolio_score = self._compute_portfolio_score(
                coverage_analysis, redundancy_analysis, efficiency_analysis
            )
            priority_actions = self._build_priority_actions(
                coverage_analysis, redundancy_analysis, efficiency_analysis
            )
            estimated_savings = self._estimate_savings(redundancy_analysis, efficiency_analysis)

            plog.step_complete(
                "portfolio_analysis",
                portfolio_score=portfolio_score,
                policies_analyzed=len(portfolio),
                gaps=len(coverage_analysis.get("gaps", [])),
            )

            # ── Step 2: LLM synthesis ──────────────────────────────────────
            plog.step_start("llm_synthesis")
            synthesis_prompt = self._build_synthesis_prompt(
                message=message,
                portfolio=portfolio,
                user_profile=user_profile,
                coverage_analysis=coverage_analysis,
                redundancy_analysis=redundancy_analysis,
                efficiency_analysis=efficiency_analysis,
                portfolio_score=portfolio_score,
                priority_actions=priority_actions,
                estimated_savings=estimated_savings,
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

            # ── Step 3: Sources ────────────────────────────────────────────
            sources = [
                {
                    "type": "guideline",
                    "reference": "IRDAI Consumer Education — Insurance Portfolio Best Practices",
                    "confidence": 0.85,
                },
                {
                    "type": "guideline",
                    "reference": "Standard income replacement and health cover adequacy benchmarks",
                    "confidence": 0.85,
                },
            ]
            if portfolio:
                sources.append({
                    "type": "document",
                    "reference": f"Analysis of {len(portfolio)} policy/policies",
                    "confidence": 0.80,
                })

            confidence = 0.82 if portfolio else 0.65
            latency_ms = int((time.time() - start) * 1000)

            return AgentResult(
                response=response_text,
                confidence=confidence,
                sources=sources,
                latency_ms=latency_ms,
                tokens_in=llm_response.get("tokens_in", 0),
                tokens_out=llm_response.get("tokens_out", 0),
                structured_data={
                    "portfolio_score": portfolio_score,
                    "coverage_analysis": coverage_analysis,
                    "redundancy_analysis": redundancy_analysis,
                    "priority_actions": priority_actions,
                    "estimated_annual_savings": estimated_savings,
                    "policies_analyzed": len(portfolio),
                },
                follow_up_suggestions=[
                    "Would you like me to explain how I calculated the portfolio score?",
                    "Should I calculate the tax benefits across your entire portfolio?",
                    "Want me to recommend specific products to fill the identified gaps?",
                ],
                products_relevant=self._check_product_relevance(portfolio, user_profile),
            )

        except Exception as e:
            plog.error("portfolio_optimizer", error=str(e))
            return AgentResult(
                response=self._error_response(),
                confidence=0.0,
                sources=[],
            )

    # ── Analysis functions ─────────────────────────────────────────────────

    def _analyze_coverage(
        self, portfolio: List[Dict[str, Any]], user_profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze coverage adequacy across the portfolio."""
        annual_income = self._safe_float(user_profile.get("annual_income"))
        city_tier = user_profile.get("city_tier", "tier2")
        family_size = user_profile.get("family_size", 2)

        # Aggregate by category
        total_life = 0.0
        total_health = 0.0
        has_term = False
        has_health = False
        has_ci = False
        has_pa = False
        has_motor = False

        for policy in portfolio:
            ptype = (policy.get("policy_type") or policy.get("type") or "").lower()
            sa = self._safe_float(policy.get("sum_assured") or policy.get("sum_insured"))

            if "term" in ptype:
                has_term = True
                total_life += sa
            elif any(t in ptype for t in ["endowment", "ulip", "money back", "life"]):
                total_life += sa
            if "health" in ptype or "medical" in ptype:
                has_health = True
                total_health += sa
            if "critical" in ptype:
                has_ci = True
            if "accident" in ptype or "personal accident" in ptype:
                has_pa = True
            if "motor" in ptype or "car" in ptype or "vehicle" in ptype:
                has_motor = True

        # Benchmarks
        life_required = annual_income * LIFE_MULTIPLIERS["recommended"] if annual_income else 0
        health_benchmark = HEALTH_BENCHMARKS.get(city_tier, HEALTH_BENCHMARKS["tier2"])
        health_required = health_benchmark["ideal"] * max(1, family_size / 2)

        gaps = []
        strengths = []

        # Life cover check
        if not has_term and annual_income:
            gaps.append({
                "type": "no_term_life",
                "severity": "HIGH",
                "description": "No term life insurance",
                "quantified": f"Required: {self._format_currency(life_required)} | Current: ₹0",
                "score_impact": -25,
            })
        elif total_life > 0:
            if annual_income and total_life < life_required:
                gap_amount = life_required - total_life
                gaps.append({
                    "type": "insufficient_life_cover",
                    "severity": "HIGH",
                    "description": f"Life cover below recommended {LIFE_MULTIPLIERS['recommended']}x income",
                    "quantified": f"Current: {self._format_currency(total_life)} | Gap: {self._format_currency(gap_amount)}",
                    "score_impact": -15,
                })
            else:
                strengths.append(f"Life cover: {self._format_currency(total_life)} (adequate)")

        # Health cover check
        if not has_health:
            gaps.append({
                "type": "no_health_cover",
                "severity": "HIGH",
                "description": "No health insurance — any hospitalization is unprotected",
                "quantified": f"Minimum needed: {self._format_currency(health_benchmark['minimum'])}",
                "score_impact": -25,
            })
        elif total_health < health_benchmark["minimum"]:
            gaps.append({
                "type": "low_health_cover",
                "severity": "MEDIUM",
                "description": f"Health cover below {city_tier} standard",
                "quantified": (
                    f"Current: {self._format_currency(total_health)} | "
                    f"Minimum: {self._format_currency(health_benchmark['minimum'])}"
                ),
                "score_impact": -15,
            })
        else:
            strengths.append(f"Health cover: {self._format_currency(total_health)} (adequate)")

        if not has_ci and annual_income and annual_income > 600_000:
            gaps.append({
                "type": "no_critical_illness",
                "severity": "MEDIUM",
                "description": "No critical illness cover",
                "quantified": "CI treatment costs ₹5L-₹50L+ — consider ₹25L CI cover",
                "score_impact": -10,
            })
        else:
            if has_ci:
                strengths.append("Critical illness cover: present")

        if not has_pa:
            gaps.append({
                "type": "no_personal_accident",
                "severity": "LOW",
                "description": "No personal accident / disability cover",
                "quantified": "PA insurance is very affordable — ~₹2,000-₹5,000/year for ₹25L cover",
                "score_impact": -5,
            })

        return {
            "total_life_cover": total_life,
            "total_health_cover": total_health,
            "has_term": has_term,
            "has_health": has_health,
            "has_ci": has_ci,
            "has_pa": has_pa,
            "gaps": gaps,
            "strengths": strengths,
            "life_required": life_required,
            "health_required": health_required,
        }

    def _analyze_redundancy(
        self, portfolio: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Identify redundant or overlapping policies."""
        redundancies = []

        # Group by category
        health_policies = [
            p for p in portfolio
            if "health" in (p.get("policy_type") or p.get("type") or "").lower()
        ]
        life_policies = [
            p for p in portfolio
            if any(t in (p.get("policy_type") or p.get("type") or "").lower()
                   for t in ["endowment", "money back", "whole life"])
        ]

        if len(health_policies) > 2:
            redundancies.append({
                "type": "multiple_health_policies",
                "severity": "LOW",
                "count": len(health_policies),
                "suggestion": "Consider consolidating to 1 base policy + 1 super top-up for better value",
                "potential_saving": "Could save ₹5,000-₹15,000/year in premiums",
            })

        if len(life_policies) > 1:
            redundancies.append({
                "type": "multiple_endowments",
                "severity": "MEDIUM",
                "count": len(life_policies),
                "suggestion": (
                    "Multiple traditional policies: Check if combined IRR justifies the premium. "
                    "Term insurance gives same/better life cover at much lower cost."
                ),
                "potential_saving": "May save ₹20,000-₹50,000/year by replacing with term",
            })

        return {
            "redundancies": redundancies,
            "redundancy_count": len(redundancies),
        }

    def _analyze_premium_efficiency(
        self,
        portfolio: List[Dict[str, Any]],
        user_profile: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Check if premium budget is within 5-10% of income."""
        annual_income = self._safe_float(user_profile.get("annual_income"))
        if not annual_income:
            return {"efficiency": "unknown", "reason": "Income not provided"}

        total_annual_premium = sum(
            self._safe_float(p.get("annual_premium") or p.get("premium"))
            for p in portfolio
        )

        pct_of_income = (total_annual_premium / annual_income * 100) if annual_income else 0
        min_budget_pct = 5.0
        max_budget_pct = 10.0

        if pct_of_income < min_budget_pct:
            efficiency = "under_insured_by_spend"
            message = f"Spending only {pct_of_income:.1f}% of income on insurance — below the recommended 5-10%"
        elif pct_of_income <= max_budget_pct:
            efficiency = "optimal"
            message = f"Premium at {pct_of_income:.1f}% of income — within the 5-10% guideline"
        else:
            efficiency = "over_spending"
            message = f"Premium at {pct_of_income:.1f}% of income — above the 10% guideline. Check for redundant policies."

        return {
            "total_annual_premium": total_annual_premium,
            "premium_pct_of_income": round(pct_of_income, 1),
            "efficiency": efficiency,
            "efficiency_message": message,
            "optimal_min": annual_income * 0.05,
            "optimal_max": annual_income * 0.10,
        }

    def _compute_portfolio_score(
        self,
        coverage: Dict[str, Any],
        redundancy: Dict[str, Any],
        efficiency: Dict[str, Any],
    ) -> int:
        """Compute 0-100 portfolio score."""
        score = 100

        # Deduct for gaps
        for gap in coverage.get("gaps", []):
            score += gap.get("score_impact", 0)

        # Deduct for redundancy
        for r in redundancy.get("redundancies", []):
            if r.get("severity") == "MEDIUM":
                score -= 5
            elif r.get("severity") == "LOW":
                score -= 2

        # Deduct for premium inefficiency
        eff = efficiency.get("efficiency", "unknown")
        if eff == "over_spending":
            score -= 5

        return max(0, min(100, score))

    def _build_priority_actions(
        self,
        coverage: Dict[str, Any],
        redundancy: Dict[str, Any],
        efficiency: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Build ordered list of priority actions."""
        actions = []

        # HIGH severity gaps first
        for gap in coverage.get("gaps", []):
            if gap["severity"] == "HIGH":
                actions.append({
                    "priority": 1,
                    "action": f"Address: {gap['description']}",
                    "why": gap["quantified"],
                    "urgency": "Immediate (within 30 days)",
                })

        # MEDIUM gaps
        for gap in coverage.get("gaps", []):
            if gap["severity"] == "MEDIUM":
                actions.append({
                    "priority": 2,
                    "action": f"Fill gap: {gap['description']}",
                    "why": gap["quantified"],
                    "urgency": "Within 3-6 months",
                })

        # Redundancy fixes
        for r in redundancy.get("redundancies", []):
            actions.append({
                "priority": 3,
                "action": f"Review: {r['suggestion']}",
                "why": r.get("potential_saving", ""),
                "urgency": "At next renewal",
            })

        return actions[:5]  # Top 5 actions

    def _estimate_savings(
        self,
        redundancy: Dict[str, Any],
        efficiency: Dict[str, Any],
    ) -> Optional[str]:
        """Estimate potential annual savings from optimization."""
        savings_texts = []

        for r in redundancy.get("redundancies", []):
            if r.get("potential_saving"):
                savings_texts.append(r["potential_saving"])

        if efficiency.get("efficiency") == "over_spending":
            total = efficiency.get("total_annual_premium", 0)
            max_ok = efficiency.get("optimal_max", 0)
            if total > max_ok:
                saving = total - max_ok
                savings_texts.append(
                    f"Up to {self._format_currency(saving)}/year by right-sizing premium spend"
                )

        if savings_texts:
            return "; ".join(savings_texts)
        return None

    def _build_synthesis_prompt(
        self,
        message: str,
        portfolio: List[Dict[str, Any]],
        user_profile: Dict[str, Any],
        coverage_analysis: Dict[str, Any],
        redundancy_analysis: Dict[str, Any],
        efficiency_analysis: Dict[str, Any],
        portfolio_score: int,
        priority_actions: List[Dict[str, Any]],
        estimated_savings: Optional[str],
    ) -> str:
        """Build the synthesis prompt with all pre-computed analysis."""
        # Strip internal fields before sending to LLM
        clean_portfolio = [
            {k: v for k, v in p.items() if not k.startswith("_")}
            for p in portfolio[:5]
        ]

        return f"""The user wants a comprehensive review of their insurance portfolio.

USER'S REQUEST: {message}

USER PROFILE:
{json.dumps(user_profile, indent=2, ensure_ascii=False) if user_profile else "Not provided"}

PORTFOLIO OVERVIEW ({len(portfolio)} policies):
{json.dumps(clean_portfolio, indent=2, ensure_ascii=False)}

PORTFOLIO SCORE: {portfolio_score}/100
(Higher is better. 80-100: Well-protected. 60-79: Adequate with gaps. Below 60: Significant risks.)

COVERAGE ANALYSIS:
Total life cover: {self._format_currency(coverage_analysis.get('total_life_cover', 0))}
Total health cover: {self._format_currency(coverage_analysis.get('total_health_cover', 0))}
Has term: {coverage_analysis.get('has_term', False)} | Has health: {coverage_analysis.get('has_health', False)}
Has CI: {coverage_analysis.get('has_ci', False)} | Has PA: {coverage_analysis.get('has_pa', False)}

Strengths: {json.dumps(coverage_analysis.get('strengths', []), ensure_ascii=False)}
Gaps: {json.dumps(coverage_analysis.get('gaps', []), indent=2, ensure_ascii=False)}

REDUNDANCY ANALYSIS:
{json.dumps(redundancy_analysis, indent=2, ensure_ascii=False)}

PREMIUM EFFICIENCY:
{json.dumps(efficiency_analysis, indent=2, ensure_ascii=False)}

PRIORITY ACTIONS (pre-computed, present in order):
{json.dumps(priority_actions, indent=2, ensure_ascii=False)}

ESTIMATED SAVINGS: {estimated_savings or "Not computed (need more data)"}

INSTRUCTIONS FOR RESPONSE:
1. Start with: "Portfolio Score: {portfolio_score}/100" with a brief interpretation
2. STRENGTHS section: what's working well (from strengths list)
3. GAPS section: what's missing or inadequate (from gaps list, ordered by severity)
4. REDUNDANCY section: overlapping policies (if any)
5. PREMIUM EFFICIENCY: are they spending the right amount?
6. PRIORITY ACTIONS: numbered, ordered, actionable (5 max)
7. If estimated_savings: "Potential savings: {estimated_savings}"
8. IPF mention if relevant: "If any of your high-premium policies are at risk of lapsing, EAZR's IPF can help maintain them"
9. DISCLAIMER: "Consult a SEBI-registered investment advisor for major portfolio restructuring"
10. IRDAI disclaimer

Use the numbers provided — do not invent or estimate figures not in the analysis above.
"""

    def _safe_float(self, value: Any) -> float:
        """Safely convert to float."""
        if value is None:
            return 0.0
        try:
            if isinstance(value, str):
                value = value.replace(",", "").replace("₹", "").strip()
                for unit in ["crore", "cr"]:
                    if unit in value.lower():
                        return float(value.lower().replace(unit, "").strip()) * 10_000_000
                for unit in ["lakh", "l"]:
                    if unit in value.lower():
                        return float(value.lower().replace(unit, "").strip()) * 100_000
            return float(value)
        except (ValueError, TypeError):
            return 0.0

    def _check_product_relevance(
        self, portfolio: List[Dict[str, Any]], user_profile: Dict[str, Any]
    ) -> List[str]:
        """Check if IPF or SVF is relevant."""
        products = []
        annual_income = self._safe_float(user_profile.get("annual_income"))
        if annual_income > 1_200_000:
            products.append("IPF")
        for policy in portfolio:
            premium = self._safe_float(policy.get("annual_premium") or policy.get("premium"))
            if premium > 50_000:
                if "IPF" not in products:
                    products.append("IPF")
                break
        return products


# ── Module-level run function (called by agent_dispatch) ──────────────────
_agent = PortfolioOptimizerAgent()


async def run(state: HibiscusState) -> Dict[str, Any]:
    """Entry point for agent_dispatch."""
    return await _agent(state)
