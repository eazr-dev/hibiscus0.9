"""
🌺 Hibiscus v0.9 | EAZR AI Insurance Intelligence Engine
Calculator agent — EMI, IRR, inflation-adjusted returns, opportunity cost analysis.
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
"""
import re
import time
from typing import Any, Dict, List, Optional, Tuple

from hibiscus.agents.base import BaseAgent, AgentResult
from hibiscus.knowledge.formulas.irr import compute_policy_irr, interpret_irr
from hibiscus.llm.router import call_llm
from hibiscus.observability.logger import PipelineLogger
from hibiscus.orchestrator.state import HibiscusState



# Constants used in calculations
LIFE_COVER_MULTIPLIERS = {
    "minimum": 10,
    "recommended": 15,
    "ideal": 20,
}

HEALTH_COVER_BY_CITY = {
    "metro": {
        "minimum": 1_000_000,      # 10 lakhs
        "recommended": 2_500_000,  # 25 lakhs
        "cities": ["Mumbai", "Delhi", "NCR", "Bengaluru", "Chennai", "Hyderabad", "Pune", "Kolkata"],
    },
    "tier2": {
        "minimum": 500_000,       # 5 lakhs
        "recommended": 1_000_000, # 10 lakhs
        "cities": ["Other cities"],
    },
}

PREMIUM_BUDGET_GUIDELINES = {
    "minimum_pct": 0.05,   # 5% of income
    "maximum_pct": 0.10,   # 10% of income
    "life_pct": 0.02,      # 2% for term
    "health_pct": 0.03,    # 3% for health
}

HEALTH_INFLATION_RATE = 0.15   # 15% annual medical inflation India
FD_RATE = 0.075
PPF_RATE = 0.071
NIFTY_HISTORICAL_RATE = 0.125


class CalculatorAgent(BaseAgent):
    """Financial calculations for insurance planning."""

    name = "calculator"
    description = "Financial calculations and projections"
    default_tier = "deepseek_r1"  # Complex math — use Tier 2
    prompt_file = "calculator.txt"

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

            # ── Step 1: Detect calculation type and extract inputs ─────────
            plog.step_start("detect_calculation_type")
            calc_type = self._detect_calculation_type(message)
            inputs = self._extract_inputs(message, user_profile, state)
            plog.step_complete(
                "detect_calculation_type",
                calc_type=calc_type,
                inputs_found=list(inputs.keys()),
            )

            # ── Step 2: Check for missing inputs ──────────────────────────
            missing = self._check_missing_inputs(calc_type, inputs)
            if missing:
                plog.warning("missing_inputs", calc_type=calc_type, missing=missing)
                return AgentResult(
                    response=self._ask_for_missing_inputs(calc_type, missing, inputs),
                    confidence=0.6,
                    sources=[],
                )

            # ── Step 3: Run deterministic calculations ────────────────────
            plog.step_start("run_calculations")
            calc_results = self._run_calculations(calc_type, inputs)
            plog.step_complete("run_calculations", calc_type=calc_type)

            # ── Step 4: LLM synthesis with computed numbers ────────────────
            plog.step_start("llm_synthesis")
            synthesis_prompt = self._build_synthesis_prompt(
                message=message,
                calc_type=calc_type,
                inputs=inputs,
                results=calc_results,
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

            # ── Step 5: Sources and confidence ────────────────────────────
            sources = self._build_sources(calc_type, inputs)
            confidence = 0.90 if not missing else 0.75
            latency_ms = int((time.time() - start) * 1000)

            return AgentResult(
                response=response_text,
                confidence=confidence,
                sources=sources,
                latency_ms=latency_ms,
                tokens_in=llm_response.get("tokens_in", 0),
                tokens_out=llm_response.get("tokens_out", 0),
                structured_data={
                    "calculation_type": calc_type,
                    "inputs": inputs,
                    "results": calc_results,
                },
                follow_up_suggestions=self._build_follow_ups(calc_type),
                products_relevant=self._check_product_relevance(calc_type, inputs, calc_results),
            )

        except Exception as e:
            plog.error("calculator", error=str(e))
            return AgentResult(
                response=self._error_response(),
                confidence=0.0,
                sources=[],
            )

    # ── Detection and extraction ───────────────────────────────────────────

    def _detect_calculation_type(self, message: str) -> str:
        """Detect what calculation the user wants."""
        msg_lower = message.lower()

        if any(w in msg_lower for w in ["how much life", "life insurance need", "life cover need", "term insurance amount"]):
            return "life_need"
        if any(w in msg_lower for w in ["health cover", "how much health", "health insurance need", "medical cover"]):
            return "health_need"
        if any(w in msg_lower for w in ["premium afford", "can i afford", "budget for insurance", "how much premium"]):
            return "premium_affordability"
        if any(w in msg_lower for w in ["emi", "monthly payment", "ipf", "premium financing"]):
            return "emi_calculation"
        if any(w in msg_lower for w in ["irr", "return", "yield", "maturity", "how much will i get"]):
            return "policy_irr"
        if any(w in msg_lower for w in ["inflation", "cover enough", "sum insured adequate", "10 years"]):
            return "inflation_adequacy"

        # Default: life need (most common calculation query)
        return "life_need"

    def _extract_inputs(
        self,
        message: str,
        user_profile: Dict[str, Any],
        state: HibiscusState,
    ) -> Dict[str, Any]:
        """Extract numerical inputs from message + state."""
        inputs: Dict[str, Any] = {}
        msg_lower = message.lower()

        # From user profile
        if user_profile.get("annual_income"):
            inputs["annual_income"] = float(user_profile["annual_income"])
        if user_profile.get("age"):
            inputs["age"] = int(user_profile["age"])
        if user_profile.get("city_tier"):
            inputs["city_tier"] = user_profile["city_tier"]

        # Annual income from message
        income_patterns = [
            r"(?:annual\s+)?income\s+(?:of\s+)?(?:₹|rs\.?|inr)?\s*([\d,]+(?:\.\d+)?)\s*(lakh|crore|l|cr)?",
            r"earn(?:ing)?\s+(?:₹|rs\.?|inr)?\s*([\d,]+(?:\.\d+)?)\s*(lakh|crore|l|cr)?",
            r"salary\s+(?:of\s+)?(?:₹|rs\.?|inr)?\s*([\d,]+(?:\.\d+)?)\s*(lakh|crore|l|cr)?",
            r"(?:₹|rs\.?|inr)\s*([\d,]+(?:\.\d+)?)\s*(lakh|crore|l|cr)?\s+(?:per\s+year|annual|p\.a\.)",
        ]
        if "annual_income" not in inputs:
            for pattern in income_patterns:
                m = re.search(pattern, msg_lower)
                if m:
                    inputs["annual_income"] = self._parse_amount(m.group(1), m.group(2))
                    break

        # Age
        if "age" not in inputs:
            age_m = re.search(r"\b(\d{2})\s*(?:years?\s*old|yr\s*old|yrs?\s*old)\b", msg_lower)
            if not age_m:
                age_m = re.search(r"\bage\s+(?:is\s+)?(\d{2})\b", msg_lower)
            if age_m:
                inputs["age"] = int(age_m.group(1))

        # City tier
        if "city_tier" not in inputs:
            metro_cities = ["mumbai", "delhi", "ncr", "bengaluru", "bangalore", "chennai",
                            "hyderabad", "pune", "kolkata"]
            if any(city in msg_lower for city in metro_cities):
                inputs["city_tier"] = "metro"
            else:
                inputs["city_tier"] = "tier2"  # Default

        # Dependents
        dep_m = re.search(r"(\d+)\s+(?:dependents?|family\s+members?|children)", msg_lower)
        if dep_m:
            inputs["dependents"] = int(dep_m.group(1))

        # Existing liabilities (loans)
        loan_patterns = [
            r"(?:home\s+)?loan\s+(?:of\s+)?(?:₹|rs\.?|inr)?\s*([\d,]+(?:\.\d+)?)\s*(lakh|crore|l|cr)?",
            r"liabilit(?:y|ies)\s+(?:of\s+)?(?:₹|rs\.?|inr)?\s*([\d,]+(?:\.\d+)?)\s*(lakh|crore|l|cr)?",
        ]
        for pattern in loan_patterns:
            m = re.search(pattern, msg_lower)
            if m:
                inputs["existing_liabilities"] = self._parse_amount(m.group(1), m.group(2))
                break

        # For IRR calculation
        premium_m = re.search(
            r"(?:annual\s+)?premium\s+(?:of\s+)?(?:₹|rs\.?|inr)?\s*([\d,]+(?:\.\d+)?)\s*(lakh|crore|l|cr)?",
            msg_lower,
        )
        if premium_m:
            inputs["annual_premium"] = self._parse_amount(premium_m.group(1), premium_m.group(2))

        # Policy term for IRR
        term_m = re.search(r"(\d+)\s*[- ]?year\s+policy|policy\s+term\s+(?:of\s+)?(\d+)", msg_lower)
        if term_m:
            inputs["policy_term"] = int(term_m.group(1) or term_m.group(2))

        # Maturity amount
        maturity_patterns = [
            r"maturity\s+(?:of\s+)?(?:₹|rs\.?|inr)?\s*([\d,]+(?:\.\d+)?)\s*(lakh|crore|l|cr)?",
            r"(?:get|receive)\s+(?:₹|rs\.?|inr)?\s*([\d,]+(?:\.\d+)?)\s*(lakh|crore|l|cr)?\s+(?:on\s+)?maturity",
        ]
        for pattern in maturity_patterns:
            m = re.search(pattern, msg_lower)
            if m:
                inputs["maturity_amount"] = self._parse_amount(m.group(1), m.group(2))
                break

        # Sum insured (for adequacy check)
        si_patterns = [
            r"(?:sum\s+insured|sum\s+assured|cover)\s+(?:of\s+)?(?:₹|rs\.?|inr)?\s*([\d,]+(?:\.\d+)?)\s*(lakh|crore|l|cr)?",
        ]
        for pattern in si_patterns:
            m = re.search(pattern, msg_lower)
            if m:
                inputs["current_sum_insured"] = self._parse_amount(m.group(1), m.group(2))
                break

        # Years for inflation projection
        years_m = re.search(r"(?:in|after)\s+(\d+)\s+years?", msg_lower)
        if years_m:
            inputs["projection_years"] = int(years_m.group(1))

        # Loan amount for EMI
        loan_amount_m = re.search(
            r"(?:loan|finance)\s+(?:of\s+)?(?:₹|rs\.?|inr)?\s*([\d,]+(?:\.\d+)?)\s*(lakh|crore|l|cr)?",
            msg_lower,
        )
        if loan_amount_m:
            inputs["loan_amount"] = self._parse_amount(loan_amount_m.group(1), loan_amount_m.group(2))

        return inputs

    def _parse_amount(self, number_str: str, unit: Optional[str]) -> float:
        """Parse amount string with unit (lakh/crore) into absolute float."""
        amount = float(number_str.replace(",", ""))
        unit = (unit or "").strip().lower()
        if unit in ("lakh", "l"):
            return amount * 100_000
        elif unit in ("crore", "cr"):
            return amount * 10_000_000
        return amount

    def _check_missing_inputs(
        self, calc_type: str, inputs: Dict[str, Any]
    ) -> List[str]:
        """Return list of missing required inputs for this calculation."""
        requirements = {
            "life_need": ["annual_income"],
            "health_need": [],  # city_tier has default
            "premium_affordability": ["annual_income"],
            "emi_calculation": ["loan_amount"],
            "policy_irr": ["annual_premium", "policy_term", "maturity_amount"],
            "inflation_adequacy": ["current_sum_insured"],
        }
        required = requirements.get(calc_type, [])
        return [f for f in required if not inputs.get(f)]

    def _ask_for_missing_inputs(
        self, calc_type: str, missing: List[str], partial: Dict[str, Any]
    ) -> str:
        """Return a targeted question for missing inputs."""
        field_labels = {
            "annual_income": "your annual income (e.g., ₹12 lakh per year)",
            "loan_amount": "the loan/financing amount (e.g., ₹2 lakh)",
            "annual_premium": "the annual premium amount (e.g., ₹50,000 per year)",
            "policy_term": "the total policy term in years (e.g., 20 years)",
            "maturity_amount": "the maturity benefit amount mentioned in your policy",
            "current_sum_insured": "your current health/life cover amount",
        }
        calc_labels = {
            "life_need": "life insurance need",
            "health_need": "health insurance adequacy",
            "premium_affordability": "premium affordability",
            "emi_calculation": "EMI calculation",
            "policy_irr": "policy return (IRR)",
            "inflation_adequacy": "inflation adequacy check",
        }
        calc_label = calc_labels.get(calc_type, "calculation")
        missing_labels = [field_labels.get(f, f) for f in missing]

        if len(missing_labels) == 1:
            return (
                f"To calculate your {calc_label}, I need one detail: **{missing_labels[0]}**.\n\n"
                "Please share this and I'll calculate it immediately."
            )
        items = "\n".join(f"  - {label}" for label in missing_labels)
        return (
            f"To calculate your {calc_label}, I need:\n{items}\n\n"
            "Please share these details and I'll run the calculation."
        )

    # ── Calculation functions ──────────────────────────────────────────────

    def _run_calculations(
        self, calc_type: str, inputs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Dispatch to the appropriate calculation function."""
        dispatch = {
            "life_need": self._calc_life_need,
            "health_need": self._calc_health_need,
            "premium_affordability": self._calc_premium_affordability,
            "emi_calculation": self._calc_emi,
            "policy_irr": self._calc_policy_irr,
            "inflation_adequacy": self._calc_inflation_adequacy,
        }
        calc_fn = dispatch.get(calc_type, self._calc_life_need)
        return calc_fn(inputs)

    def _calc_life_need(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Income replacement life insurance need calculation."""
        annual_income = inputs["annual_income"]
        age = inputs.get("age", 35)
        dependents = inputs.get("dependents", 2)
        existing_liabilities = inputs.get("existing_liabilities", 0)

        # Income replacement method
        minimum_cover = annual_income * LIFE_COVER_MULTIPLIERS["minimum"]
        recommended_cover = annual_income * LIFE_COVER_MULTIPLIERS["recommended"]
        ideal_cover = annual_income * LIFE_COVER_MULTIPLIERS["ideal"]

        # Add liabilities to cover
        minimum_with_liabilities = minimum_cover + existing_liabilities
        recommended_with_liabilities = recommended_cover + existing_liabilities

        # Years of coverage remaining (retire at 60)
        years_to_retire = max(0, 60 - age)

        return {
            "method": "Income Replacement Method",
            "formula": "Cover = Annual Income × Multiplier + Outstanding Liabilities",
            "inputs_used": {
                "annual_income": annual_income,
                "age": age,
                "dependents": dependents,
                "existing_liabilities": existing_liabilities,
                "years_to_retire": years_to_retire,
            },
            "results": {
                "minimum_cover": minimum_cover,
                "recommended_cover": recommended_cover,
                "ideal_cover": ideal_cover,
                "minimum_with_liabilities": minimum_with_liabilities,
                "recommended_with_liabilities": recommended_with_liabilities,
                "multipliers_used": LIFE_COVER_MULTIPLIERS,
            },
            "note": (
                "This is an estimate using the income replacement method. "
                "Actual need depends on expenses, goals, and family situation."
            ),
        }

    def _calc_health_need(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """City-based health insurance adequacy."""
        city_tier = inputs.get("city_tier", "tier2")
        guide = HEALTH_COVER_BY_CITY.get(city_tier, HEALTH_COVER_BY_CITY["tier2"])
        family_size = inputs.get("dependents", 1) + 1  # Include self

        # Individual vs family floater
        individual_cover = guide["recommended"]
        family_cover = guide["recommended"] * min(1.5, 1 + (family_size - 1) * 0.3)

        # Inflation-adjusted need in 10 years
        years = 10
        future_need = guide["recommended"] * ((1 + HEALTH_INFLATION_RATE) ** years)

        return {
            "method": "City-Based Adequacy Standard",
            "inputs_used": {
                "city_tier": city_tier,
                "family_size": family_size,
                "health_inflation_rate": f"{HEALTH_INFLATION_RATE:.0%} p.a.",
            },
            "results": {
                "minimum_cover": guide["minimum"],
                "recommended_cover": guide["recommended"],
                "individual_recommended": individual_cover,
                "family_floater_recommended": round(family_cover, -5),
                "future_need_10yr": round(future_need, -5),
                "city_standard": city_tier,
                "cities": guide["cities"],
            },
            "note": (
                f"Health insurance adequacy in {city_tier} cities. "
                f"Medical inflation in India averages {HEALTH_INFLATION_RATE:.0%} annually — "
                f"₹10L cover today will effectively be ₹{self._format_currency(future_need)} in 10 years."
            ),
        }

    def _calc_premium_affordability(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Premium budget based on income guidelines."""
        annual_income = inputs["annual_income"]

        min_budget = annual_income * PREMIUM_BUDGET_GUIDELINES["minimum_pct"]
        max_budget = annual_income * PREMIUM_BUDGET_GUIDELINES["maximum_pct"]
        life_budget = annual_income * PREMIUM_BUDGET_GUIDELINES["life_pct"]
        health_budget = annual_income * PREMIUM_BUDGET_GUIDELINES["health_pct"]

        monthly_min = min_budget / 12
        monthly_max = max_budget / 12

        return {
            "method": "Income-Based Premium Budget (5-10% rule)",
            "formula": "Budget = Annual Income × 5% to 10%",
            "inputs_used": {"annual_income": annual_income},
            "results": {
                "annual_budget_min": min_budget,
                "annual_budget_max": max_budget,
                "monthly_budget_min": round(monthly_min, 2),
                "monthly_budget_max": round(monthly_max, 2),
                "suggested_split": {
                    "term_life": life_budget,
                    "health_insurance": health_budget,
                    "other_insurance": max_budget - life_budget - health_budget,
                },
            },
            "note": (
                "5-10% of annual income is the standard insurance budget guideline. "
                "Term insurance should be prioritized first (2% budget), "
                "then health (3%), then supplementary covers."
            ),
        }

    def _calc_emi(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """EMI calculation for insurance premium financing."""
        loan_amount = inputs["loan_amount"]
        annual_rate = inputs.get("interest_rate", 0.12)  # 12% default IPF rate
        tenure_months = inputs.get("tenure_months", 12)

        monthly_rate = annual_rate / 12
        # EMI formula: P × r × (1+r)^n / ((1+r)^n - 1)
        if monthly_rate > 0:
            emi = loan_amount * monthly_rate * ((1 + monthly_rate) ** tenure_months) / \
                  (((1 + monthly_rate) ** tenure_months) - 1)
        else:
            emi = loan_amount / tenure_months

        total_payment = emi * tenure_months
        total_interest = total_payment - loan_amount

        return {
            "method": "Standard EMI Formula",
            "formula": "EMI = P × r × (1+r)^n / ((1+r)^n - 1)",
            "inputs_used": {
                "loan_amount": loan_amount,
                "annual_interest_rate": f"{annual_rate:.0%}",
                "tenure_months": tenure_months,
            },
            "results": {
                "monthly_emi": round(emi, 2),
                "total_payment": round(total_payment, 2),
                "total_interest": round(total_interest, 2),
                "effective_cost_of_financing": f"{(total_interest / loan_amount * 100):.2f}%",
            },
            "note": (
                f"Based on {annual_rate:.0%} annual interest rate. "
                "Actual IPF rates from EAZR vary by policy and tenure. "
                "Contact EAZR for current rates."
            ),
        }

    def _calc_policy_irr(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Compute policy IRR using deterministic formula."""
        annual_premium = inputs["annual_premium"]
        policy_term = inputs["policy_term"]
        maturity_amount = inputs["maturity_amount"]
        premium_term = inputs.get("premium_term", policy_term)
        annual_bonus = inputs.get("annual_bonus", 0)

        irr_value = compute_policy_irr(
            annual_premium=annual_premium,
            premium_term=premium_term,
            maturity_amount=maturity_amount,
            policy_term=policy_term,
            annual_bonus=annual_bonus,
        )
        interpretation = interpret_irr(irr_value)

        total_premiums = annual_premium * premium_term
        total_maturity = maturity_amount + (annual_bonus * policy_term)

        return {
            "method": "Newton-Raphson IRR",
            "inputs_used": {
                "annual_premium": annual_premium,
                "premium_term": premium_term,
                "policy_term": policy_term,
                "maturity_amount": maturity_amount,
                "annual_bonus": annual_bonus,
            },
            "results": {
                "irr_pct": interpretation.get("irr_pct"),
                "irr_verdict": interpretation.get("verdict"),
                "irr_context": interpretation.get("context"),
                "comparisons": interpretation.get("comparisons", {}),
                "total_premiums_paid": total_premiums,
                "total_maturity_value": total_maturity,
                "absolute_gain": total_maturity - total_premiums,
            },
        }

    def _calc_inflation_adequacy(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Check if current sum insured is adequate after inflation."""
        current_si = inputs["current_sum_insured"]
        years = inputs.get("projection_years", 10)
        inflation_rate = HEALTH_INFLATION_RATE

        future_value_needed = current_si * ((1 + inflation_rate) ** years)
        shortfall = future_value_needed - current_si

        # Year-by-year progression
        yearly = {}
        for y in [5, 10, 15, 20]:
            if y <= years + 5:
                yearly[f"year_{y}"] = round(current_si * ((1 + inflation_rate) ** y), -3)

        return {
            "method": "Medical Inflation Adjustment",
            "formula": f"Future Need = Current Cover × (1 + {inflation_rate:.0%})^years",
            "inputs_used": {
                "current_sum_insured": current_si,
                "projection_years": years,
                "health_inflation_rate": f"{inflation_rate:.0%} p.a.",
            },
            "results": {
                "current_cover": current_si,
                "cover_needed_after_n_years": round(future_value_needed, -3),
                "shortfall": round(shortfall, -3),
                "yearly_projections": yearly,
            },
            "note": (
                f"India's medical inflation averages {inflation_rate:.0%} annually (industry estimate). "
                "Your current cover of ₹{:,.0f} will effectively have the purchasing power of "
                "₹{:,.0f} in {} years.".format(
                    current_si,
                    round(current_si / ((1 + inflation_rate) ** years), -3),
                    years,
                )
            ),
        }

    def _build_synthesis_prompt(
        self,
        message: str,
        calc_type: str,
        inputs: Dict[str, Any],
        results: Dict[str, Any],
    ) -> str:
        """Build synthesis prompt with all pre-computed results."""
        import json
        results_text = json.dumps(results, indent=2, ensure_ascii=False)
        inputs_text = json.dumps(inputs, indent=2, ensure_ascii=False)

        calc_labels = {
            "life_need": "Life Insurance Need Calculation",
            "health_need": "Health Insurance Adequacy Check",
            "premium_affordability": "Premium Budget Calculation",
            "emi_calculation": "EMI Calculation (Insurance Premium Financing)",
            "policy_irr": "Policy Return (IRR) Calculation",
            "inflation_adequacy": "Cover Adequacy After Inflation",
        }

        return f"""The user wants a financial calculation related to insurance.

USER'S REQUEST: {message}
CALCULATION TYPE: {calc_labels.get(calc_type, calc_type)}

INPUTS USED:
{inputs_text}

COMPUTED RESULTS (all numbers are deterministic — present exactly):
{results_text}

INSTRUCTIONS FOR RESPONSE:
1. State the calculation method and formula clearly at the start
2. Show the inputs used (so user can verify)
3. Present the key result prominently (bold or highlight)
4. Provide context: is this result good/adequate/concerning?
5. Show the formula: {results.get('formula', 'See method above')}
6. Use Indian format: ₹, lakhs/crores throughout
7. If IRR calculation: compare explicitly against FD (7.5%), PPF (7.1%), and Nifty 50 (12.5%)
8. State all assumptions (inflation rate used, multipliers used, etc.)
9. Add appropriate caveats (e.g., "actual need may vary based on lifestyle")
10. End with IRDAI disclaimer for recommendations
11. Suggest 2 follow-up calculations the user might find useful

DO NOT recompute or alter any numbers. Present what is calculated above.
"""

    def _build_sources(
        self, calc_type: str, inputs: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Build source citations based on calculation type."""
        sources = [
            {
                "type": "formula",
                "reference": "Standard actuarial/financial formulas",
                "confidence": 0.95,
            },
        ]
        if calc_type == "life_need":
            sources.append({
                "type": "guideline",
                "reference": "IRDAI Consumer Education — Life Insurance Need Assessment",
                "confidence": 0.85,
            })
        if calc_type == "health_need":
            sources.append({
                "type": "guideline",
                "reference": "IRDAI Annual Report 2023-24 — Health Insurance Market Data",
                "confidence": 0.85,
            })
        if calc_type == "policy_irr":
            sources.append({
                "type": "formula",
                "reference": "Newton-Raphson IRR — standard financial mathematics",
                "confidence": 0.95,
            })
        return sources

    def _build_follow_ups(self, calc_type: str) -> List[str]:
        """Build follow-up suggestions based on calculation type."""
        follow_ups = {
            "life_need": [
                "Should I calculate the approximate term insurance premium for this cover amount?",
                "Want me to check the tax benefit you'd get on the term insurance premium?",
            ],
            "health_need": [
                "Want me to check if your current health cover is adequate?",
                "Should I calculate how medical inflation will impact your cover in 10 years?",
            ],
            "premium_affordability": [
                "Should I suggest how to split this budget across life and health insurance?",
                "Want me to calculate what cover you can get within this budget?",
            ],
            "policy_irr": [
                "Should I compare this IRR against keeping the policy vs surrendering?",
                "Want me to calculate what the same money invested in ELSS would yield?",
            ],
            "inflation_adequacy": [
                "Should I suggest how much additional cover you need to stay adequate?",
                "Want me to check what a top-up plan would cost?",
            ],
        }
        return follow_ups.get(calc_type, [
            "Would you like me to explain the calculation methodology?",
            "Should I calculate something else related to your insurance?",
        ])

    def _check_product_relevance(
        self, calc_type: str, inputs: Dict[str, Any], results: Dict[str, Any]
    ) -> List[str]:
        """Check if EAZR's IPF or SVF products are relevant."""
        products = []
        if calc_type == "emi_calculation":
            products.append("IPF")
        annual_income = inputs.get("annual_income", 0)
        if annual_income > 1_200_000:  # Above 12 LPA
            products.append("IPF")
        return list(set(products))


# ── Module-level run function (called by agent_dispatch) ──────────────────
_agent = CalculatorAgent()


async def run(state: HibiscusState) -> Dict[str, Any]:
    """Entry point for agent_dispatch."""
    return await _agent(state)
