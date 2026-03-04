"""
🌺 Hibiscus v0.9 | EAZR AI Insurance Intelligence Engine
Risk detector agent — identifies coverage gaps, under-insurance, and hidden exclusions.
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
"""
import json
import time
from typing import Any, Dict, List, Optional, Tuple

from hibiscus.agents.base import BaseAgent, AgentResult
from hibiscus.llm.router import call_llm
from hibiscus.observability.logger import PipelineLogger
from hibiscus.orchestrator.state import HibiscusState


# Mis-selling patterns and their detection logic
MIS_SELLING_PATTERNS = {
    "low_sa_ratio": {
        "flag": "Low Sum Assured to Premium Ratio",
        "severity": "HIGH",
        "description": "Sum assured is below type-specific minimum SA/Premium ratio",
        "implication": "Policy does not qualify for Section 80C tax benefit in full; not adequate as life cover",
        "irdai_reference": "Section 80C Income Tax Act — SA/Premium ratio requirement",
        # Type-specific thresholds: term policies naturally have high SA/premium
        # ratios (often 100x+), so 8x flags only truly broken products.
        # Endowment/ULIP/money-back have lower ratios by design; 10x is the
        # Section 80C floor for full tax benefit eligibility.
        "threshold": 10,  # default; overridden per-type in detection logic
        "threshold_by_type": {
            "term": 8,
            "endowment": 10,
            "ulip": 10,
            "money back": 10,
        },
        "metric": "sa_to_premium_ratio",
    },
    "ulip_high_charges": {
        "flag": "ULIP with High Charge Structure",
        "severity": "MEDIUM",
        "description": "ULIP policy with mortality charge + fund management charge > 2.5% of fund value",
        "implication": "Excessive charges reduce investment returns significantly — may perform worse than direct mutual funds",
        "irdai_reference": "IRDAI (Unit Linked Insurance Products) Regulations 2019 — charge limits",
        "metric": "total_charges",
    },
    "endowment_low_irr": {
        "flag": "Traditional Endowment with Likely Low IRR",
        "severity": "MEDIUM",
        "description": "Endowment/money back policy with high premium, low sum assured",
        "implication": "Traditional plans typically yield 4-6% IRR — below FD rates (7.5%). May not be efficient as investment",
        "irdai_reference": "General investment benchmark",
        "metric": "irr_estimate",
    },
    "guaranteed_returns_claim": {
        "flag": "Potential Mis-representation of Returns",
        "severity": "HIGH",
        "description": "Policy sold with promise of 'guaranteed' returns on market-linked products",
        "implication": "Market-linked products (ULIPs) cannot have guaranteed returns — this is a mis-selling indicator",
        "irdai_reference": "IRDAI (Protection of Policyholders' Interests) Regulations 2017",
        "metric": "policy_type_vs_return_claim",
    },
    "health_room_rent_subliimit": {
        "flag": "Health Policy with Room Rent Sub-limit",
        "severity": "MEDIUM",
        "description": "Health policy has room rent capped at 1% or 2% of sum insured per day",
        "implication": "In metro hospitals, room rent above sub-limit triggers proportional deduction on entire bill",
        "irdai_reference": "IRDAI Health Insurance Master Circular 2024 — sub-limit disclosure",
        "metric": "room_rent_sublimit",
    },
    "copay_high": {
        "flag": "High Co-payment Clause",
        "severity": "MEDIUM",
        "description": "Co-payment above 20% — user pays significant portion of each claim",
        "implication": "High co-pay drastically reduces effective coverage — check if premium savings justify it",
        "irdai_reference": "IRDAI Health Insurance Regulations",
        "metric": "copay_percentage",
    },
}

# Coverage gap definitions
COVERAGE_GAP_DEFINITIONS = {
    "no_term_life": {
        "description": "No term life insurance — income earner has no pure protection cover",
        "severity": "HIGH",
        "urgency": "Immediate",
        "rationale": "Without term cover, dependents have no income replacement if earner passes away",
    },
    "insufficient_life_cover": {
        "description": "Life cover below 10x annual income",
        "severity": "HIGH",
        "urgency": "Within 3 months",
        "rationale": "Standard income replacement guideline is 10-15x annual income",
    },
    "no_health_cover": {
        "description": "No health insurance — any hospitalization is a financial emergency",
        "severity": "HIGH",
        "urgency": "Immediate",
        "rationale": "Medical inflation in India is 15% annually — uninsured hospitalization can be devastating",
    },
    "low_health_cover": {
        "description": "Health cover below minimum city standard",
        "severity": "MEDIUM",
        "urgency": "Within 6 months",
        "rationale": "Metro: minimum ₹10L required; Tier 2: minimum ₹5L",
    },
    "no_critical_illness": {
        "description": "No critical illness cover — cancer/cardiac event not financially protected",
        "severity": "MEDIUM",
        "urgency": "Within 6 months",
        "rationale": "CI treatment costs ₹5L-₹50L+ in India; regular health insurance may have sub-limits",
    },
    "no_personal_accident": {
        "description": "No personal accident / disability cover",
        "severity": "LOW",
        "urgency": "Within 12 months",
        "rationale": "PA insurance is very low cost and covers income loss from disability",
    },
}


class RiskDetectorAgent(BaseAgent):
    """Identifies risks, mis-selling indicators, and coverage gaps in insurance portfolios."""

    name = "risk_detector"
    description = "Mis-selling and coverage gap detector"
    default_tier = "deepseek_v3"
    prompt_file = "risk_detector.txt"

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

            # ── Step 1: Extract policy data for analysis ───────────────────
            plog.step_start("extract_policy_data")
            policies_to_analyze = self._collect_policies(state)
            plog.step_complete(
                "extract_policy_data",
                policies_count=len(policies_to_analyze),
            )

            # ── Step 2: Run deterministic risk checks ──────────────────────
            plog.step_start("run_risk_checks")
            risk_flags = self._detect_mis_selling_flags(policies_to_analyze)
            gap_list = self._detect_coverage_gaps(policies_to_analyze, user_profile)
            over_insurance = self._detect_over_insurance(policies_to_analyze)
            urgency_level = self._compute_urgency(risk_flags, gap_list)

            # ── Step 2.5: Fraud/anomaly detection ────────────────────────
            fraud_alerts = []
            try:
                from hibiscus.services.fraud_alert import fraud_detector
                doc_context = state.get("document_context")
                if doc_context:
                    extraction = doc_context.get("extraction") or {}
                    if extraction:
                        fraud_alerts = fraud_detector.check_document(extraction, state)
                        # Behavioral checks
                        fraud_alerts.extend(
                            fraud_detector.check_behavioral(state.get("session_history", []))
                        )
                        if fraud_alerts:
                            # Merge fraud alerts into risk_flags
                            for alert in fraud_alerts:
                                risk_flags.append({
                                    "category": "fraud",
                                    "flag": alert.alert_type,
                                    "severity": alert.severity.value if hasattr(alert.severity, 'value') else alert.severity,
                                    "description": alert.evidence,
                                    "recommendation": alert.recommendation,
                                })
                            if any(a.severity.value in ("HIGH", "CRITICAL") for a in fraud_alerts):
                                urgency_level = "high"
            except Exception as e:
                plog.warning("fraud_detection_failed", error=str(e))

            plog.step_complete(
                "run_risk_checks",
                risk_flags=len(risk_flags),
                gaps=len(gap_list),
                urgency=urgency_level,
                fraud_alerts=len(fraud_alerts),
            )

            # ── Step 3: LLM synthesis ──────────────────────────────────────
            plog.step_start("llm_synthesis")
            synthesis_prompt = self._build_synthesis_prompt(
                message=message,
                policies=policies_to_analyze,
                risk_flags=risk_flags,
                gap_list=gap_list,
                over_insurance=over_insurance,
                urgency_level=urgency_level,
                user_profile=user_profile,
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
            sources = [
                {
                    "type": "formula",
                    "reference": "Section 80C Income Tax Act — 10x SA/Premium ratio",
                    "confidence": 0.95,
                },
                {
                    "type": "regulation",
                    "reference": "IRDAI (Protection of Policyholders' Interests) Regulations 2017",
                    "confidence": 0.92,
                },
            ]
            if policies_to_analyze:
                sources.append({
                    "type": "document_extraction",
                    "reference": f"Analysis of {len(policies_to_analyze)} policy/policies",
                    "confidence": 0.80,
                })

            # Confidence: high if we have actual policy data
            confidence = 0.85 if policies_to_analyze else 0.65
            latency_ms = int((time.time() - start) * 1000)

            return AgentResult(
                response=response_text,
                confidence=confidence,
                sources=sources,
                latency_ms=latency_ms,
                tokens_in=llm_response.get("tokens_in", 0),
                tokens_out=llm_response.get("tokens_out", 0),
                structured_data={
                    "risk_flags": risk_flags,
                    "gap_list": gap_list,
                    "mis_selling_flags": [f for f in risk_flags if f.get("category") == "mis_selling"],
                    "fraud_alerts": [a.to_dict() for a in fraud_alerts] if fraud_alerts else [],
                    "over_insurance": over_insurance,
                    "urgency_level": urgency_level,
                    "policies_analyzed": len(policies_to_analyze),
                },
                follow_up_suggestions=[
                    "Would you like me to explain any of these risk flags in detail?",
                    "Should I recommend products to fill the identified coverage gaps?",
                    "Want me to calculate the tax implications of restructuring your portfolio?",
                ],
                products_relevant=self._check_product_relevance(risk_flags, gap_list),
            )

        except Exception as e:
            plog.error("risk_detector", error=str(e))
            return AgentResult(
                response=self._error_response(),
                confidence=0.0,
                sources=[],
            )

    # ── Private helpers ────────────────────────────────────────────────────

    def _collect_policies(self, state: HibiscusState) -> List[Dict[str, Any]]:
        """Collect all policy data from state."""
        policies = []

        # From current document context
        doc_context = state.get("document_context")
        if doc_context and doc_context.get("extraction"):
            extraction = doc_context["extraction"]
            extraction["_source"] = "uploaded_document"
            policies.append(extraction)

        # From portfolio memory
        for policy in state.get("policy_portfolio") or []:
            if policy:
                policy = dict(policy)
                policy.setdefault("_source", "portfolio_memory")
                policies.append(policy)

        # From previous agent outputs (PolicyAnalyzer)
        for output in state.get("agent_outputs") or []:
            if isinstance(output, dict) and output.get("structured_data"):
                sd = output["structured_data"]
                if sd.get("extraction"):
                    sd["extraction"]["_source"] = "policy_analyzer_output"
                    policies.append(sd["extraction"])

        return policies

    def _detect_mis_selling_flags(
        self, policies: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Run deterministic mis-selling checks on each policy."""
        flags = []

        for policy in policies:
            policy_type = (policy.get("policy_type") or policy.get("type") or "").lower()
            annual_premium = self._safe_float(policy.get("annual_premium") or policy.get("premium"))
            sum_assured = self._safe_float(policy.get("sum_assured") or policy.get("sum_insured"))
            copay = self._safe_float(policy.get("copay") or policy.get("co_payment"))
            room_rent_limit = policy.get("room_rent_sublimit") or policy.get("room_rent_limit")

            # Check 1: SA/Premium ratio (life insurance) — type-specific thresholds
            if annual_premium and sum_assured and any(
                t in policy_type for t in ["life", "endowment", "ulip", "term", "money back"]
            ):
                ratio = sum_assured / annual_premium
                # Determine the applicable threshold for this policy type
                type_thresholds = MIS_SELLING_PATTERNS["low_sa_ratio"]["threshold_by_type"]
                applicable_threshold = MIS_SELLING_PATTERNS["low_sa_ratio"]["threshold"]
                for ptype_key, ptype_threshold in type_thresholds.items():
                    if ptype_key in policy_type:
                        applicable_threshold = ptype_threshold
                        break
                if ratio < applicable_threshold:
                    flags.append({
                        "flag": MIS_SELLING_PATTERNS["low_sa_ratio"]["flag"],
                        "category": "mis_selling",
                        "severity": MIS_SELLING_PATTERNS["low_sa_ratio"]["severity"],
                        "evidence": (
                            f"SA/Premium ratio = {ratio:.1f}x "
                            f"(minimum {applicable_threshold}x required for {policy_type} for full 80C benefit)"
                        ),
                        "implication": MIS_SELLING_PATTERNS["low_sa_ratio"]["implication"],
                        "reference": MIS_SELLING_PATTERNS["low_sa_ratio"]["irdai_reference"],
                        "policy_type": policy_type,
                    })

            # Check 2: High co-payment
            if copay and copay > 20:
                flags.append({
                    "flag": MIS_SELLING_PATTERNS["copay_high"]["flag"],
                    "category": "product_structure",
                    "severity": "MEDIUM",
                    "evidence": f"Co-payment clause: {copay:.0f}% — user pays this proportion of each claim",
                    "implication": MIS_SELLING_PATTERNS["copay_high"]["implication"],
                    "reference": MIS_SELLING_PATTERNS["copay_high"]["irdai_reference"],
                    "policy_type": policy_type,
                })

            # Check 3: Room rent sublimit (health)
            if room_rent_limit and "health" in policy_type:
                flags.append({
                    "flag": MIS_SELLING_PATTERNS["health_room_rent_subliimit"]["flag"],
                    "category": "product_structure",
                    "severity": "MEDIUM",
                    "evidence": f"Room rent capped at: {room_rent_limit}",
                    "implication": MIS_SELLING_PATTERNS["health_room_rent_subliimit"]["implication"],
                    "reference": MIS_SELLING_PATTERNS["health_room_rent_subliimit"]["irdai_reference"],
                    "policy_type": policy_type,
                })

            # Check 4: ULIP type check
            if "ulip" in policy_type:
                charges = self._safe_float(policy.get("total_charges") or policy.get("mortality_charge"))
                if charges and charges > 2.5:
                    flags.append({
                        "flag": MIS_SELLING_PATTERNS["ulip_high_charges"]["flag"],
                        "category": "mis_selling",
                        "severity": "MEDIUM",
                        "evidence": f"Total ULIP charges: {charges:.1f}% (threshold: 2.5%)",
                        "implication": MIS_SELLING_PATTERNS["ulip_high_charges"]["implication"],
                        "reference": MIS_SELLING_PATTERNS["ulip_high_charges"]["irdai_reference"],
                        "policy_type": policy_type,
                    })

        return flags

    def _detect_coverage_gaps(
        self,
        policies: List[Dict[str, Any]],
        user_profile: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Identify coverage gaps based on policies and profile."""
        gaps = []

        has_life = False
        has_term = False
        has_health = False
        has_ci = False
        has_pa = False
        total_life_cover = 0.0
        total_health_cover = 0.0

        for policy in policies:
            policy_type = (policy.get("policy_type") or policy.get("type") or "").lower()
            sa = self._safe_float(policy.get("sum_assured") or policy.get("sum_insured"))

            if any(t in policy_type for t in ["term", "life", "endowment", "ulip"]):
                has_life = True
                total_life_cover += sa
                if "term" in policy_type:
                    has_term = True
            if "health" in policy_type or "medical" in policy_type:
                has_health = True
                total_health_cover += sa
            if "critical" in policy_type:
                has_ci = True
            if "accident" in policy_type or "personal accident" in policy_type:
                has_pa = True

        annual_income = self._safe_float(user_profile.get("annual_income"))
        city_tier = user_profile.get("city_tier", "tier2")

        # Gap: no term life
        if not has_term and annual_income:
            required = annual_income * 10
            gaps.append({
                **COVERAGE_GAP_DEFINITIONS["no_term_life"],
                "gap_key": "no_term_life",
                "quantified": f"Need: {self._format_currency(required)} — Current term: ₹0",
            })
        elif has_life and annual_income:
            required = annual_income * 10
            if total_life_cover < required:
                gaps.append({
                    **COVERAGE_GAP_DEFINITIONS["insufficient_life_cover"],
                    "gap_key": "insufficient_life_cover",
                    "quantified": (
                        f"Current: {self._format_currency(total_life_cover)} — "
                        f"Required: {self._format_currency(required)}"
                    ),
                })

        # Gap: no health
        if not has_health:
            gaps.append({
                **COVERAGE_GAP_DEFINITIONS["no_health_cover"],
                "gap_key": "no_health_cover",
                "quantified": "Current health cover: ₹0",
            })
        else:
            min_cover = 1_000_000 if city_tier == "metro" else 500_000
            if total_health_cover < min_cover:
                gaps.append({
                    **COVERAGE_GAP_DEFINITIONS["low_health_cover"],
                    "gap_key": "low_health_cover",
                    "quantified": (
                        f"Current: {self._format_currency(total_health_cover)} — "
                        f"Minimum for {city_tier}: {self._format_currency(min_cover)}"
                    ),
                })

        # Gap: no CI (for income earners)
        if not has_ci and annual_income and annual_income > 500_000:
            gaps.append({
                **COVERAGE_GAP_DEFINITIONS["no_critical_illness"],
                "gap_key": "no_critical_illness",
                "quantified": "No critical illness cover found",
            })

        # Gap: no PA (advisory)
        if not has_pa:
            gaps.append({
                **COVERAGE_GAP_DEFINITIONS["no_personal_accident"],
                "gap_key": "no_personal_accident",
                "quantified": "No personal accident cover found",
            })

        return gaps

    def _detect_over_insurance(
        self, policies: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Detect redundant or over-insurance situations."""
        over_insurance = []

        # Check for duplicate health policies
        health_policies = [
            p for p in policies
            if "health" in (p.get("policy_type") or p.get("type") or "").lower()
        ]
        if len(health_policies) > 1:
            over_insurance.append({
                "flag": "Multiple standalone health policies",
                "severity": "LOW",
                "evidence": f"{len(health_policies)} standalone health policies found",
                "suggestion": "Consider consolidating — a super top-up may be more cost-effective than multiple base policies",
            })

        return over_insurance

    def _compute_urgency(
        self,
        risk_flags: List[Dict[str, Any]],
        gap_list: List[Dict[str, Any]],
    ) -> str:
        """Compute overall urgency level from all flags and gaps."""
        has_high = any(
            f.get("severity") == "HIGH"
            for f in risk_flags + gap_list
        )
        has_medium = any(
            f.get("severity") == "MEDIUM"
            for f in risk_flags + gap_list
        )

        if has_high:
            return "high"
        if has_medium:
            return "medium"
        return "low"

    def _safe_float(self, value: Any) -> float:
        """Safely convert a value to float."""
        if value is None:
            return 0.0
        try:
            if isinstance(value, str):
                value = value.replace(",", "").replace("₹", "").strip()
            return float(value)
        except (ValueError, TypeError):
            return 0.0

    def _build_synthesis_prompt(
        self,
        message: str,
        policies: List[Dict[str, Any]],
        risk_flags: List[Dict[str, Any]],
        gap_list: List[Dict[str, Any]],
        over_insurance: List[Dict[str, Any]],
        urgency_level: str,
        user_profile: Dict[str, Any],
    ) -> str:
        """Build synthesis prompt with pre-computed risk analysis."""
        policies_text = json.dumps(
            [{k: v for k, v in p.items() if not k.startswith("_")} for p in policies[:3]],
            indent=2, ensure_ascii=False,
        ) if policies else "No policy data available — analyzing from user description"

        flags_text = json.dumps(risk_flags, indent=2, ensure_ascii=False) if risk_flags else "None detected"
        gaps_text = json.dumps(gap_list, indent=2, ensure_ascii=False) if gap_list else "None detected"
        over_text = json.dumps(over_insurance, indent=2, ensure_ascii=False) if over_insurance else "None detected"

        return f"""Analyze this user's insurance for risks, gaps, and red flags.

USER'S REQUEST: {message}
OVERALL URGENCY: {urgency_level.upper()}

POLICY DATA ANALYZED:
{policies_text}

COMPUTED RISK FLAGS (evidence-based — present these):
{flags_text}

COVERAGE GAPS IDENTIFIED:
{gaps_text}

OVER-INSURANCE / REDUNDANCY:
{over_text}

USER PROFILE CONTEXT:
{json.dumps(user_profile, indent=2, ensure_ascii=False) if user_profile else "Not available"}

INSTRUCTIONS FOR RESPONSE:

1. Start with overall risk summary (1-2 sentences about urgency level)

2. RISK FLAGS section (only if risk_flags is not empty):
   For each flag:
   - Flag name with severity badge [HIGH/MEDIUM/LOW]
   - Evidence: exact metric that triggered it
   - What it means for the user
   - Regulatory reference

3. COVERAGE GAPS section:
   For each gap:
   - Gap name with urgency
   - Current vs required (use numbers provided)
   - Priority action

4. OVER-INSURANCE section (only if detected):
   - What's redundant and why

5. PRIORITY ACTIONS (top 3):
   - Numbered, ordered by severity
   - Specific and actionable

6. IMPORTANT DISCLAIMERS:
   - "These findings are based on available policy data and standard benchmarks"
   - "Consult a SEBI-registered investment advisor or IRDAI-licensed insurance advisor for major decisions"
   - IRDAI disclaimer

CRITICAL:
- Only cite flags from the computed data above — do not invent new ones
- Back every flag with the specific evidence provided
- Be honest about risk severity — do not downplay HIGH flags
"""

    def _check_product_relevance(
        self, risk_flags: List[Dict[str, Any]], gap_list: List[Dict[str, Any]]
    ) -> List[str]:
        """Check if EAZR SVF or IPF is relevant."""
        products = []
        # SVF relevant if there's a ULIP or endowment with red flags suggesting exit
        has_exit_candidate = any(
            f.get("severity") == "HIGH" and f.get("category") == "mis_selling"
            for f in risk_flags
        )
        if has_exit_candidate:
            products.append("SVF")
        return products


# ── Module-level run function (called by agent_dispatch) ──────────────────
_agent = RiskDetectorAgent()


async def run(state: HibiscusState) -> Dict[str, Any]:
    """Entry point for agent_dispatch."""
    return await _agent(state)
