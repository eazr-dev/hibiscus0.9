"""
TaxAdvisorAgent — Agent 11
============================
Insurance tax benefits advisor.

Computes Section 80C, 80D, and 10(10D) tax benefits using deterministic
formulas from knowledge/formulas/tax_benefit.py. Never uses LLM for math.
Provides new regime vs old regime comparison and maturity taxability check.

Uses Tier 2 (DeepSeek R1) for complex tax scenarios involving multiple
sections, regimes, and edge cases.

ALWAYS ends with: "Consult a CA for precise computation."
"""
import json
import re
import time
from typing import Any, Dict, List, Optional, Tuple

from hibiscus.agents.base import BaseAgent, AgentResult
from hibiscus.knowledge.formulas.tax_benefit import (
    TaxBenefitResult,
    check_10_10d_exemption,
    compute_80c_benefit,
    compute_80d_benefit,
    compute_total_tax_benefit,
)
from hibiscus.llm.router import call_llm
from hibiscus.observability.logger import PipelineLogger
from hibiscus.orchestrator.state import HibiscusState

AGENT_SYSTEM_PROMPT = """You are Hibiscus, EAZR's insurance tax benefits specialist.

Your role: Compute and explain insurance tax benefits clearly, showing all working.

CRITICAL RULES:
1. NEVER compute tax amounts yourself — all numbers are provided in the prompt from deterministic formulas
2. Show the formula used for each section
3. State all conditions met/failed explicitly
4. ALWAYS compare new regime vs old regime (very important for Indian users in 2024-25)
5. ALWAYS end with: "Tax computations are indicative. Consult a CA for precise computation."
6. Use ₹ symbol, Indian format (lakhs/crores)
7. Mention that ULIP premiums > ₹2.5L lose 10(10D) exemption (Budget 2021 change)
8. For old regime: explain this is only available if user opts out of new regime

TONE: Like a CA's associate explaining a tax computation — precise, structured, clear.
"""

# Tax regime constants (FY 2024-25)
NEW_REGIME_SLABS = [
    (300_000, 0.00, "Up to ₹3 lakh: Nil"),
    (600_000, 0.05, "₹3L to ₹6L: 5%"),
    (900_000, 0.10, "₹6L to ₹9L: 10%"),
    (1_200_000, 0.15, "₹9L to ₹12L: 15%"),
    (1_500_000, 0.20, "₹12L to ₹15L: 20%"),
    (float("inf"), 0.30, "Above ₹15L: 30%"),
]

OLD_REGIME_SLABS = [
    (250_000, 0.00, "Up to ₹2.5 lakh: Nil"),
    (500_000, 0.05, "₹2.5L to ₹5L: 5%"),
    (1_000_000, 0.20, "₹5L to ₹10L: 20%"),
    (float("inf"), 0.30, "Above ₹10L: 30%"),
]

MAX_80C = 150_000
MAX_80D_SELF_BELOW_60 = 25_000
MAX_80D_SELF_60_PLUS = 50_000
MAX_80D_PARENT_BELOW_60 = 25_000
MAX_80D_PARENT_60_PLUS = 50_000

# Standard deductions
STANDARD_DEDUCTION_OLD = 50_000
STANDARD_DEDUCTION_NEW = 75_000  # Enhanced from FY 2024-25


class TaxAdvisorAgent(BaseAgent):
    """Computes insurance tax benefits under 80C, 80D, and 10(10D)."""

    name = "tax_advisor"
    description = "Insurance tax benefits advisor"
    default_tier = "deepseek_r1"  # Complex tax — Tier 2

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

            # ── Step 1: Extract tax inputs ─────────────────────────────────
            plog.step_start("extract_tax_inputs")
            tax_inputs = self._extract_tax_inputs(message, user_profile, state)
            plog.step_complete(
                "extract_tax_inputs",
                inputs_found=list(tax_inputs.keys()),
            )

            # ── Step 2: Check for minimum inputs ──────────────────────────
            if not self._has_minimum_inputs(tax_inputs):
                return AgentResult(
                    response=self._ask_for_tax_inputs(tax_inputs),
                    confidence=0.6,
                    sources=[],
                )

            # ── Step 3: Run deterministic tax computations ─────────────────
            plog.step_start("tax_computation")
            tax_results = self._compute_tax_benefits(tax_inputs)
            plog.step_complete(
                "tax_computation",
                total_saving=tax_results.get("total_tax_saving", 0),
            )

            # ── Step 4: Regime comparison ──────────────────────────────────
            plog.step_start("regime_comparison")
            regime_comparison = self._compute_regime_comparison(tax_inputs, tax_results)
            plog.step_complete("regime_comparison")

            # ── Step 5: 10(10D) check ──────────────────────────────────────
            exemption_10_10d = None
            # For ULIP queries, sum_assured is not needed — the 2021 threshold rule only checks annual premium
            has_10_10d_inputs = (
                tax_inputs.get("life_premium") and tax_inputs.get("annual_life_premium") and
                (tax_inputs.get("sum_assured") or tax_inputs.get("is_ulip"))
            )
            if has_10_10d_inputs:
                plog.step_start("10_10d_check")
                # For ULIPs without sum_assured, use 10x premium as proxy (doesn't affect 2021 ULIP threshold check)
                _sum_assured = float(tax_inputs.get("sum_assured") or tax_inputs["annual_life_premium"] * 10)
                exemption_10_10d = check_10_10d_exemption(
                    sum_assured=_sum_assured,
                    annual_premium=float(tax_inputs["annual_life_premium"]),
                    policy_year_of_issue=int(tax_inputs.get("policy_issue_year", 2015)),
                    is_ulip=tax_inputs.get("is_ulip", False),
                    ulip_annual_premium=float(tax_inputs.get("annual_life_premium", 0)),
                )
                plog.step_complete("10_10d_check", exempt=exemption_10_10d.get("exempt", True))

            # ── Step 6: LLM synthesis ──────────────────────────────────────
            plog.step_start("llm_synthesis")
            synthesis_prompt = self._build_synthesis_prompt(
                message=message,
                tax_inputs=tax_inputs,
                tax_results=tax_results,
                regime_comparison=regime_comparison,
                exemption_10_10d=exemption_10_10d,
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

            # ── Step 7: Sources ────────────────────────────────────────────
            sources = self._build_sources(tax_inputs)
            confidence = 0.88 if self._has_all_inputs(tax_inputs) else 0.75
            latency_ms = int((time.time() - start) * 1000)

            return AgentResult(
                response=response_text,
                confidence=confidence,
                sources=sources,
                latency_ms=latency_ms,
                tokens_in=llm_response.get("tokens_in", 0),
                tokens_out=llm_response.get("tokens_out", 0),
                structured_data={
                    "tax_inputs": tax_inputs,
                    "tax_results": tax_results,
                    "regime_comparison": regime_comparison,
                    "exemption_10_10d": exemption_10_10d,
                    "total_tax_saving": tax_results.get("total_tax_saving", 0),
                },
                follow_up_suggestions=[
                    "Should I check the maturity proceeds taxability for your life policy?",
                    "Want me to calculate what additional tax benefit you can get by increasing health insurance?",
                    "Should I compare old vs new tax regime in detail for your income level?",
                ],
            )

        except Exception as e:
            plog.error("tax_advisor", error=str(e))
            return AgentResult(
                response=self._error_response(),
                confidence=0.0,
                sources=[],
            )

    # ── Input extraction ───────────────────────────────────────────────────

    def _extract_tax_inputs(
        self,
        message: str,
        user_profile: Dict[str, Any],
        state: HibiscusState,
    ) -> Dict[str, Any]:
        """Extract all tax-relevant inputs from state and message."""
        inputs: Dict[str, Any] = {}
        msg_lower = message.lower()

        # From user profile
        if user_profile.get("annual_income"):
            inputs["annual_income"] = float(user_profile["annual_income"])
        if user_profile.get("age"):
            inputs["age"] = int(user_profile["age"])
            inputs["self_age"] = int(user_profile["age"])

        # From document context
        doc_context = state.get("document_context")
        if doc_context and doc_context.get("extraction"):
            extraction = doc_context["extraction"]
            ptype = (extraction.get("policy_type") or "").lower()
            premium = self._parse_amount_str(
                str(extraction.get("annual_premium") or extraction.get("premium") or "")
            )
            sa = self._parse_amount_str(
                str(extraction.get("sum_assured") or extraction.get("sum_insured") or "")
            )
            if "health" in ptype or "medical" in ptype:
                inputs["health_premium"] = premium
            elif any(t in ptype for t in ["life", "term", "endowment", "ulip"]):
                inputs["life_premium"] = premium
                inputs["annual_life_premium"] = premium
                inputs["is_ulip"] = "ulip" in ptype
                if sa:
                    inputs["sum_assured"] = sa

        # Self age from message
        if "age" not in inputs:
            for pattern in [
                r"i\s+am\s+(\d{2})\s+(?:years?)?",
                r"(?:my\s+)?age\s+is\s+(\d{2})",
                r"(\d{2})\s+year[s\s]+old",
            ]:
                m = re.search(pattern, msg_lower)
                if m:
                    inputs["age"] = int(m.group(1))
                    inputs["self_age"] = int(m.group(1))
                    break

        # From message: annual income
        if "annual_income" not in inputs:
            for pattern in [
                r"(?:annual\s+)?income\s+(?:of\s+)?(?:₹|rs\.?|inr)?\s*([\d,]+(?:\.\d+)?)\s*(lakh|crore|l|cr)?",
                r"earn(?:ing)?\s+(?:₹|rs\.?|inr)?\s*([\d,]+(?:\.\d+)?)\s*(lakh|crore|l|cr)?",
                r"salary\s+(?:of\s+)?(?:₹|rs\.?|inr)?\s*([\d,]+(?:\.\d+)?)\s*(lakh|crore|l|cr)?",
            ]:
                m = re.search(pattern, msg_lower)
                if m:
                    inputs["annual_income"] = self._parse_amount(m.group(1), m.group(2))
                    break

        # Tax bracket directly from percentage mention ("I am in 30% tax bracket")
        if "tax_bracket" not in inputs:
            m = re.search(r"(\d+)%\s+tax\s+(?:bracket|slab|rate)", msg_lower)
            if m:
                inputs["tax_bracket"] = float(m.group(1)) / 100.0
                # Infer approximate income from tax bracket for 80D computation
                if "annual_income" not in inputs:
                    bracket = float(m.group(1))
                    # Map bracket to representative income (old regime)
                    if bracket >= 30:
                        inputs["annual_income"] = 1_500_001  # above ₹15L
                    elif bracket >= 20:
                        inputs["annual_income"] = 800_000    # ₹8L
                    elif bracket >= 5:
                        inputs["annual_income"] = 400_000    # ₹4L

        # Life premium from message — broader patterns
        if "life_premium" not in inputs:
            for pattern in [
                r"life\s+(?:insurance\s+)?premium\s+(?:of\s+)?(?:₹|rs\.?|inr)?\s*([\d,]+(?:\.\d+)?)\s*(lakh|crore|l|cr)?",
                r"term\s+(?:insurance\s+)?premium\s+(?:of\s+)?(?:₹|rs\.?|inr)?\s*([\d,]+(?:\.\d+)?)\s*(lakh|crore|l|cr)?",
                # "I pay ₹3 lakhs annually [for ULIP/term/policy]"
                r"(?:i\s+)?pay\s+(?:₹|rs\.?|inr)\s*([\d,]+(?:\.\d+)?)\s*(lakh|crore|l|cr)?\s+(?:annually|per\s+year|yearly)\s+(?:for\s+)?(?:a\s+)?(?:ulip|term|life|lic)",
                r"(?:ulip|term|lic|life\s+insurance)\s+(?:premium\s+)?(?:of\s+)?(?:₹|rs\.?|inr)\s*([\d,]+(?:\.\d+)?)\s*(lakh|crore|l|cr)?",
                r"pay\s+(?:₹|rs\.?|inr)\s*([\d,]+(?:\.\d+)?)\s*(lakh|crore|l|cr)?\s+(?:annually|per\s+year)\s+(?:to\s+lic|for\s+(?:a\s+)?ulip)",
                r"(?:₹|rs\.?|inr)\s*([\d,]+(?:\.\d+)?)\s*(lakh|crore|l|cr)?\s+(?:annually|per\s+year)\s+(?:for\s+(?:a\s+)?ulip|to\s+lic)",
            ]:
                m = re.search(pattern, msg_lower)
                if m:
                    inputs["life_premium"] = self._parse_amount(m.group(1), m.group(2))
                    inputs["annual_life_premium"] = inputs["life_premium"]
                    # Detect ULIP
                    if "ulip" in msg_lower:
                        inputs["is_ulip"] = True
                    break

        # Health premium from message — broader patterns
        if "health_premium" not in inputs:
            for pattern in [
                r"health\s+(?:insurance\s+)?premium\s+(?:of\s+)?(?:₹|rs\.?|inr)?\s*([\d,]+(?:\.\d+)?)\s*(lakh|crore|l|cr)?",
                r"medical\s+(?:insurance\s+)?premium\s+(?:of\s+)?(?:₹|rs\.?|inr)?\s*([\d,]+(?:\.\d+)?)\s*(lakh|crore|l|cr)?",
                # "pay ₹22,000 for my family health insurance"
                r"pay\s+(?:₹|rs\.?|inr)\s*([\d,]+(?:\.\d+)?)\s*(lakh|crore|l|cr)?\s+for\s+(?:my\s+)?(?:family\s+)?health\s+insurance",
                r"(?:₹|rs\.?|inr)\s*([\d,]+(?:\.\d+)?)\s*(lakh|crore|l|cr)?\s+for\s+(?:my\s+)?(?:family\s+)?health\s+insurance",
                # "family health insurance of ₹X"
                r"family\s+health\s+insurance\s+(?:of\s+)?(?:₹|rs\.?|inr)\s*([\d,]+(?:\.\d+)?)\s*(lakh|crore|l|cr)?",
            ]:
                m = re.search(pattern, msg_lower)
                if m:
                    inputs["health_premium"] = self._parse_amount(m.group(1), m.group(2))
                    break

        # Parent health premium — broader patterns
        if "parent_health_premium" not in inputs:
            for pattern in [
                r"parent(?:s'?)?\s+health\s+(?:insurance\s+)?premium\s+(?:of\s+)?(?:₹|rs\.?|inr)?\s*([\d,]+(?:\.\d+)?)\s*(lakh|crore|l|cr)?",
                r"(?:father|mother)\s+(?:insurance\s+)?premium\s+(?:of\s+)?(?:₹|rs\.?|inr)?\s*([\d,]+(?:\.\d+)?)\s*(lakh|crore|l|cr)?",
                # "₹35,000 for my parents' health insurance"
                r"(?:₹|rs\.?|inr)\s*([\d,]+(?:\.\d+)?)\s*(lakh|crore|l|cr)?\s+for\s+(?:my\s+)?parents?'?\s+health\s+insurance",
                r"pay\s+(?:₹|rs\.?|inr)\s*([\d,]+(?:\.\d+)?)\s*(lakh|crore|l|cr)?\s+for\s+(?:my\s+)?parents?'?\s+health\s+insurance",
                # "parents' health insurance ... ₹35,000"
                r"parents?'?\s+health\s+insurance\s+(?:and\s+)?(?:₹|rs\.?|inr)\s*([\d,]+(?:\.\d+)?)\s*(lakh|crore|l|cr)?",
            ]:
                m = re.search(pattern, msg_lower)
                if m:
                    inputs["parent_health_premium"] = self._parse_amount(m.group(1), m.group(2))
                    break

        # Parent age — broader patterns
        if "parent_age" not in inputs:
            for pattern in [
                r"parent(?:s')?\s+age\s+(?:is\s+)?(\d{2})",
                r"father.*?(\d{2})\s+years?",
                # "they are 65+" / "they are 65 years old" / "parents are 65+"
                r"(?:they\s+are|they're|parents?\s+are)\s+(\d{2})\+?",
                r"parents?\s+(?:are\s+)?(?:aged?\s+)?(\d{2})\+?",
                r"(?:aged?\s+)?(\d{2})\+?\s+(?:years?\s+old\s+)?(?:senior|parent)",
            ]:
                m = re.search(pattern, msg_lower)
                if m:
                    inputs["parent_age"] = int(m.group(1))
                    break
            # Detect "65+" without explicit age number — treat as senior (65)
            if "parent_age" not in inputs and re.search(r"(?:60|65)\+", msg_lower):
                inputs["parent_age"] = 65

        # Sum assured
        if "sum_assured" not in inputs:
            for pattern in [
                r"sum\s+assured\s+(?:of\s+)?(?:₹|rs\.?|inr)?\s*([\d,]+(?:\.\d+)?)\s*(lakh|crore|l|cr)?",
            ]:
                m = re.search(pattern, msg_lower)
                if m:
                    inputs["sum_assured"] = self._parse_amount(m.group(1), m.group(2))
                    break

        # Tax bracket from income (only if not already set from percentage pattern)
        if "tax_bracket" not in inputs:
            annual_income = inputs.get("annual_income", 0)
            if annual_income:
                inputs["tax_bracket"] = self._income_to_bracket(annual_income, regime="old")

        # Policy purchase year — for 10(10D) check
        if "policy_issue_year" not in inputs:
            for pattern in [
                r"bought\s+(?:it\s+)?in\s+(?:\w+\s+)?(\d{4})",
                r"purchased\s+(?:in\s+)?(?:\w+\s+)?(\d{4})",
                r"took\s+(?:it\s+)?in\s+(?:\w+\s+)?(\d{4})",
                r"(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*\s+(\d{4})",
                r"(?:in\s+)?(\d{4})\s+i\s+(?:bought|purchased|took)",
            ]:
                m = re.search(pattern, msg_lower)
                if m:
                    year = int(m.group(1))
                    if 2000 <= year <= 2030:
                        inputs["policy_issue_year"] = year
                    break

        # ULIP detection from message
        if "is_ulip" not in inputs and "ulip" in msg_lower:
            inputs["is_ulip"] = True
            # Also mark as life premium context if not yet set
            if "life_premium" not in inputs:
                # Try generic ₹X lakh pattern as ULIP premium
                for pattern in [
                    r"pay\s+(?:₹|rs\.?|inr)\s*([\d,]+(?:\.\d+)?)\s*(lakh|crore|l|cr)?",
                    r"(?:₹|rs\.?|inr)\s*([\d,]+(?:\.\d+)?)\s*(lakh|crore|l|cr)?\s+(?:annually|per\s+year|yearly)",
                ]:
                    m = re.search(pattern, msg_lower)
                    if m:
                        inputs["life_premium"] = self._parse_amount(m.group(1), m.group(2))
                        inputs["annual_life_premium"] = inputs["life_premium"]
                        break

        # Existing 80C investments
        for pattern in [
            r"(?:existing\s+)?80c\s+(?:investments?\s+)?(?:of\s+)?(?:₹|rs\.?|inr)?\s*([\d,]+(?:\.\d+)?)\s*(lakh|crore|l|cr)?",
            r"(?:ppf|elss|nsc|epf)\s+(?:of\s+)?(?:₹|rs\.?|inr)?\s*([\d,]+(?:\.\d+)?)\s*(lakh|crore|l|cr)?",
        ]:
            m = re.search(pattern, msg_lower)
            if m:
                inputs["existing_80c_investments"] = self._parse_amount(m.group(1), m.group(2))
                break

        return inputs

    def _parse_amount(self, number_str: str, unit: Optional[str]) -> float:
        """Parse amount string with unit."""
        try:
            amount = float(number_str.replace(",", ""))
            unit = (unit or "").strip().lower()
            if unit in ("lakh", "l"):
                return amount * 100_000
            elif unit in ("crore", "cr"):
                return amount * 10_000_000
            return amount
        except (ValueError, TypeError):
            return 0.0

    def _parse_amount_str(self, value: str) -> float:
        """Parse amount from string that may include units."""
        if not value or value == "None":
            return 0.0
        value = str(value).replace(",", "").replace("₹", "").strip()
        try:
            if "crore" in value.lower() or "cr" in value.lower():
                return float(re.sub(r"[^\d.]", "", value)) * 10_000_000
            elif "lakh" in value.lower() or " l" in value.lower():
                return float(re.sub(r"[^\d.]", "", value)) * 100_000
            return float(re.sub(r"[^\d.]", "", value))
        except (ValueError, TypeError):
            return 0.0

    def _income_to_bracket(self, income: float, regime: str = "old") -> float:
        """Estimate marginal tax bracket from income."""
        slabs = OLD_REGIME_SLABS if regime == "old" else NEW_REGIME_SLABS
        for slab_max, rate, _ in slabs:
            if income <= slab_max:
                return rate
        return 0.30

    def _has_minimum_inputs(self, inputs: Dict[str, Any]) -> bool:
        """Check if we have enough to compute something useful."""
        has_premium = inputs.get("life_premium") or inputs.get("health_premium")
        return bool(has_premium)

    def _has_all_inputs(self, inputs: Dict[str, Any]) -> bool:
        """Check if we have all preferred inputs."""
        return bool(
            inputs.get("annual_income") and
            (inputs.get("life_premium") or inputs.get("health_premium")) and
            inputs.get("tax_bracket")
        )

    def _ask_for_tax_inputs(self, partial: Dict[str, Any]) -> str:
        """Ask for missing tax inputs."""
        items = []
        if not partial.get("life_premium") and not partial.get("health_premium"):
            items.append("  - Your insurance premium amounts (life insurance premium, health insurance premium)")
        if not partial.get("annual_income"):
            items.append("  - Your annual income (to determine your tax bracket)")
        items.append("  - (Optional) Parent's health insurance premium and their age")
        items.append("  - (Optional) Other 80C investments (PPF, ELSS, EPF) to check if limit is exhausted")

        return (
            "To compute your insurance tax benefits, I need:\n" +
            "\n".join(items) +
            "\n\nYou can also upload your policy document and I'll extract the premium automatically."
        )

    # ── Tax computations ───────────────────────────────────────────────────

    def _compute_tax_benefits(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Run deterministic tax computations."""
        tax_bracket = float(inputs.get("tax_bracket", 0.30))
        self_age = int(inputs.get("self_age") or inputs.get("age") or 35)
        parent_age = int(inputs.get("parent_age") or 0)
        existing_80c = float(inputs.get("existing_80c_investments") or 0)

        results = {}
        total_saving = 0.0

        # Section 80C
        life_premium = float(inputs.get("life_premium") or 0)
        if life_premium > 0:
            sum_assured = float(inputs.get("sum_assured") or life_premium * 10)
            annual_life_premium = float(inputs.get("annual_life_premium") or life_premium)
            r80c = compute_80c_benefit(
                life_premium=life_premium,
                sum_assured=sum_assured,
                annual_premium=annual_life_premium,
                policy_issue_date_after_2012=inputs.get("policy_issue_year", 2015) >= 2012,
                tax_bracket=tax_bracket,
                existing_80c_investments=existing_80c,
            )
            results["section_80c"] = {
                "eligible_deduction": r80c.eligible_deduction,
                "actual_premium": r80c.actual_premium,
                "tax_saving": r80c.tax_saving,
                "notes": r80c.notes,
                "conditions_met": r80c.conditions_met,
                "conditions_failed": r80c.conditions_failed,
            }
            total_saving += r80c.tax_saving

        # Section 80D
        health_premium = float(inputs.get("health_premium") or 0)
        parent_health_premium = float(inputs.get("parent_health_premium") or 0)
        if health_premium > 0 or parent_health_premium > 0:
            r80d = compute_80d_benefit(
                self_family_premium=health_premium,
                parent_premium=parent_health_premium,
                self_age=self_age,
                parent_age=parent_age,
                tax_bracket=tax_bracket,
            )
            results["section_80d"] = {
                "eligible_deduction": r80d.eligible_deduction,
                "actual_premium": r80d.actual_premium,
                "tax_saving": r80d.tax_saving,
                "notes": r80d.notes,
                "conditions_met": r80d.conditions_met,
                "conditions_failed": r80d.conditions_failed,
            }
            total_saving += r80d.tax_saving

        results["total_tax_saving"] = round(total_saving, 2)
        results["effective_cost_reduction"] = (
            f"You save ₹{total_saving:,.0f} in taxes, reducing the effective cost of your insurance."
            if total_saving > 0 else "No tax benefit computed with provided data."
        )

        return results

    def _compute_regime_comparison(
        self, inputs: Dict[str, Any], tax_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Compare old vs new tax regime."""
        annual_income = float(inputs.get("annual_income") or 0)
        if not annual_income:
            return {"note": "Provide annual income for regime comparison"}

        total_deductions_old = STANDARD_DEDUCTION_OLD
        life_premium = float(inputs.get("life_premium") or 0)
        health_premium = float(inputs.get("health_premium") or 0)
        parent_health_premium = float(inputs.get("parent_health_premium") or 0)
        existing_80c = float(inputs.get("existing_80c_investments") or 0)

        # Old regime: 80C + 80D available
        deductions_80c = min(life_premium + existing_80c, MAX_80C)
        deductions_80d_self = min(health_premium, MAX_80D_SELF_BELOW_60)
        deductions_80d_parent = min(parent_health_premium, MAX_80D_PARENT_BELOW_60)
        total_deductions_old += deductions_80c + deductions_80d_self + deductions_80d_parent

        taxable_old = max(0, annual_income - total_deductions_old)
        tax_old = self._compute_tax(taxable_old, regime="old")

        # New regime: no 80C/80D, higher standard deduction
        taxable_new = max(0, annual_income - STANDARD_DEDUCTION_NEW)
        tax_new = self._compute_tax(taxable_new, regime="new")

        better_regime = "old" if tax_old < tax_new else "new"
        saving_from_choice = abs(tax_old - tax_new)

        return {
            "annual_income": annual_income,
            "old_regime": {
                "total_deductions": total_deductions_old,
                "taxable_income": taxable_old,
                "tax_liability": round(tax_old, 2),
                "includes": ["Standard deduction ₹50,000", "Section 80C", "Section 80D"],
            },
            "new_regime": {
                "total_deductions": STANDARD_DEDUCTION_NEW,
                "taxable_income": taxable_new,
                "tax_liability": round(tax_new, 2),
                "includes": ["Standard deduction ₹75,000 only"],
                "note": "No 80C/80D deductions in new regime",
            },
            "recommendation": {
                "better_regime": better_regime,
                "saving_vs_other_regime": round(saving_from_choice, 2),
                "note": (
                    f"Old regime saves ₹{saving_from_choice:,.0f} more for this income level."
                    if better_regime == "old"
                    else f"New regime saves ₹{saving_from_choice:,.0f} more — but you lose 80C/80D benefits."
                ),
            },
        }

    def _compute_tax(self, taxable_income: float, regime: str = "old") -> float:
        """Compute tax from taxable income using slabs."""
        slabs = OLD_REGIME_SLABS if regime == "old" else NEW_REGIME_SLABS
        tax = 0.0
        prev_slab = 0

        for slab_max, rate, _ in slabs:
            if taxable_income <= 0:
                break
            slab_income = min(taxable_income - prev_slab, slab_max - prev_slab)
            if slab_income <= 0:
                prev_slab = slab_max
                continue
            if taxable_income > prev_slab:
                taxable_in_slab = min(taxable_income - prev_slab, slab_max - prev_slab)
                tax += taxable_in_slab * rate
            prev_slab = slab_max
            if prev_slab >= taxable_income:
                break

        # Add 4% cess
        return tax * 1.04

    def _build_synthesis_prompt(
        self,
        message: str,
        tax_inputs: Dict[str, Any],
        tax_results: Dict[str, Any],
        regime_comparison: Dict[str, Any],
        exemption_10_10d: Optional[Dict[str, Any]],
    ) -> str:
        """Build synthesis prompt with all pre-computed numbers."""
        exemption_text = ""
        if exemption_10_10d:
            exemption_text = f"\nSECTION 10(10D) MATURITY EXEMPTION:\n{json.dumps(exemption_10_10d, indent=2, ensure_ascii=False)}"

        return f"""The user wants to understand their insurance tax benefits.

USER'S REQUEST: {message}

INPUTS USED FOR COMPUTATION:
Life premium: ₹{float(tax_inputs.get('life_premium', 0)):,.0f}
Health premium: ₹{float(tax_inputs.get('health_premium', 0)):,.0f}
Parent health premium: ₹{float(tax_inputs.get('parent_health_premium', 0)):,.0f}
Sum assured: ₹{float(tax_inputs.get('sum_assured', 0)):,.0f}
Annual income: ₹{float(tax_inputs.get('annual_income', 0)):,.0f}
Tax bracket: {float(tax_inputs.get('tax_bracket', 0.30)) * 100:.0f}%
Existing 80C investments: ₹{float(tax_inputs.get('existing_80c_investments', 0)):,.0f}
Self age: {tax_inputs.get('self_age', 35)} | Parent age: {tax_inputs.get('parent_age', 0)}

COMPUTED TAX BENEFITS (deterministic — present exactly):
{json.dumps(tax_results, indent=2, ensure_ascii=False)}

REGIME COMPARISON:
{json.dumps(regime_comparison, indent=2, ensure_ascii=False)}
{exemption_text}

INSTRUCTIONS FOR RESPONSE:

1. **Summary**: Total tax saving = ₹{float(tax_results.get('total_tax_saving', 0)):,.0f}/year

2. **Section 80C** (if applicable):
   - Formula: Premium × min(eligible %) × tax bracket
   - Show eligible deduction amount and conditions met/failed
   - If SA < 10x premium: explain the proportional deduction

3. **Section 80D** (if applicable):
   - Self + family: ₹X deduction (limit ₹25,000 or ₹50,000 based on age)
   - Parents: ₹X additional deduction (limit ₹25,000 or ₹50,000)
   - Total 80D saving

4. **Effective Cost After Tax**:
   - Annual premium = ₹X, Tax saving = ₹Y, Effective cost = ₹(X-Y)
   - "Your health insurance effectively costs ₹Y/year after tax benefit"

5. **Old vs New Regime Comparison**:
   - Present both tax liabilities
   - Recommend which is better for this income level
   - Note: "Insurance deductions only benefit under old regime"

6. **10(10D) Maturity Taxability** (if computed): Explain result clearly

7. **DISCLAIMER** (mandatory):
   "Tax computations are indicative. Actual tax benefit depends on your total income,
   other deductions, and choice of tax regime. Consult a CA for precise computation."

DO NOT change or recompute any numbers. Present what is computed above.
"""

    def _build_sources(self, tax_inputs: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Build source citations."""
        sources = []
        if tax_inputs.get("life_premium"):
            sources.append({
                "type": "law",
                "reference": "Section 80C — Income Tax Act 1961",
                "confidence": 0.95,
            })
        if tax_inputs.get("health_premium"):
            sources.append({
                "type": "law",
                "reference": "Section 80D — Income Tax Act 1961",
                "confidence": 0.95,
            })
        sources.append({
            "type": "regulation",
            "reference": "Income Tax Act 1961 — Finance Act 2024 (FY 2024-25 slabs)",
            "confidence": 0.92,
        })
        return sources


# ── Module-level run function (called by agent_dispatch) ──────────────────
_agent = TaxAdvisorAgent()


async def run(state: HibiscusState) -> Dict[str, Any]:
    """Entry point for agent_dispatch."""
    return await _agent(state)
