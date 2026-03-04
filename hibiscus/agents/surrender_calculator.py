"""
🌺 Hibiscus v0.9 | EAZR AI Insurance Intelligence Engine
Surrender calculator agent — paid-up value, surrender penalties, opportunity cost of exit.
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
"""
import json
import re
import time
from typing import Any, Dict, List, Optional, Tuple

from hibiscus.agents.base import BaseAgent, AgentResult
from hibiscus.knowledge.formulas.irr import compute_policy_irr, interpret_irr
from hibiscus.knowledge.formulas.surrender_value import (
    SurrenderValueResult,
    calculate_surrender_projection,
)
from hibiscus.llm.router import call_llm
from hibiscus.observability.logger import PipelineLogger
from hibiscus.orchestrator.state import HibiscusState

# Approximate SBI FD benchmark rate for opportunity-cost comparison.
# Date-stamped: as of 2026-03-04. Update when RBI rate cycle changes materially.
INDICATIVE_FD_RATE = 0.075  # 7.5% p.a. — approximate, not guaranteed

AGENT_SYSTEM_PROMPT = """You are Hibiscus, EAZR's insurance AI assistant specializing in surrender value analysis.

Your role: Explain surrender value calculations clearly and help users decide whether to keep or exit a policy.

CRITICAL RULES:
1. NEVER compute or estimate numbers yourself — all numbers are provided to you in the prompt
2. NEVER say "your returns will be X%" unless the IRR is explicitly provided in the data
3. NEVER recommend surrendering a policy without citing the computed GSV
4. ALWAYS mention that SSV (Special Surrender Value) from the insurer may be higher than GSV
5. ALWAYS include: "Consult your insurer for the exact surrender value before proceeding"
6. Use ₹ symbol, Indian format (lakhs/crores), and DD/MM/YYYY for dates
7. Include IRDAI disclaimer: "This analysis is for educational purposes. Insurance is subject to market risks and policy terms."

TONE: Analytical, helpful, honest — do not sugarcoat poor policy returns.
"""


class SurrenderCalculatorAgent(BaseAgent):
    """Computes surrender value and IRR for life insurance policies."""

    name = "surrender_calculator"
    description = "Surrender value and hold-vs-surrender analyzer"
    default_tier = "deepseek_r1"  # Complex math — use Tier 2

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
            # ── Step 1: Extract policy data ────────────────────────────────
            plog.step_start("extract_policy_data")
            policy_data, data_source, extraction_confidence = self._extract_policy_data(state)

            # ── Step 2: Check for missing critical fields ──────────────────
            missing = self._check_missing_fields(policy_data)
            if missing:
                plog.warning(
                    "missing_required_fields",
                    missing_fields=missing,
                    source=data_source,
                )
                return AgentResult(
                    response=self._ask_for_missing_data(missing, policy_data),
                    confidence=0.5,
                    sources=[],
                )

            annual_premium = float(policy_data["annual_premium"])
            policy_year = int(policy_data["policy_year"])
            policy_term = int(policy_data["policy_term"])
            premium_term = int(policy_data.get("premium_term", policy_term))
            sum_assured = float(policy_data.get("sum_assured", annual_premium * 10))
            bonus_rate = float(policy_data.get("bonus_rate_per_1000", 35.0))
            maturity_amount = float(policy_data.get("maturity_amount", sum_assured))

            plog.step_complete(
                "extract_policy_data",
                annual_premium=annual_premium,
                policy_year=policy_year,
                source=data_source,
            )

            # ── Step 3: Compute surrender projection ───────────────────────
            plog.step_start("surrender_projection")
            # Show current year and next 3 years (up to policy maturity)
            projection_start = max(1, policy_year)
            projection_end_year = min(policy_year + 3, policy_term)

            # Compute full projection from year 1 to projection_end_year
            # then slice to get current + future years
            full_projection = calculate_surrender_projection(
                annual_premium=annual_premium,
                policy_term=policy_term,
                premium_term=premium_term,
                sum_assured=sum_assured,
                bonus_rate_per_1000=bonus_rate,
                start_year=1,
            )

            # Filter to the years we want to show
            current_and_future = [
                r for r in full_projection
                if projection_start <= r.year <= (policy_year + 3)
            ]
            current_year_result = next(
                (r for r in full_projection if r.year == policy_year), None
            )

            plog.step_complete("surrender_projection", years_computed=len(current_and_future))

            # ── Step 4: Compute IRR ────────────────────────────────────────
            plog.step_start("irr_computation")
            irr_result = None
            irr_interpretation = {}

            try:
                annual_bonus = (sum_assured / 1000) * bonus_rate
                irr_value = compute_policy_irr(
                    annual_premium=annual_premium,
                    premium_term=premium_term,
                    maturity_amount=maturity_amount,
                    policy_term=policy_term,
                    annual_bonus=annual_bonus,
                )
                irr_interpretation = interpret_irr(irr_value)
                irr_result = irr_value
                plog.step_complete("irr_computation", irr_pct=irr_interpretation.get("irr_pct"))
            except Exception as e:
                plog.warning("irr_computation_failed", error=str(e))

            # ── Step 5: Build FD comparison ────────────────────────────────
            fd_comparison = self._compute_fd_comparison(
                annual_premium=annual_premium,
                policy_year=policy_year,
                premium_term=premium_term,
                current_year_result=current_year_result,
            )

            # ── Step 6: Build LLM synthesis prompt ────────────────────────
            plog.step_start("llm_synthesis")
            synthesis_prompt = self._build_synthesis_prompt(
                policy_data=policy_data,
                current_year_result=current_year_result,
                projection_table=current_and_future,
                irr_interpretation=irr_interpretation,
                fd_comparison=fd_comparison,
                message=state.get("message", ""),
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

            # ── Step 7: Build sources ──────────────────────────────────────
            sources = [
                {
                    "type": "formula",
                    "reference": "IRDAI GSV Table — IRDAI (Protection of Policyholders' Interests) Regulations 2002",
                    "confidence": 0.95,
                },
            ]
            if data_source == "document_extraction":
                sources.append({
                    "type": "document_extraction",
                    "reference": "Uploaded policy document",
                    "confidence": extraction_confidence,
                })
            if irr_result is not None:
                sources.append({
                    "type": "formula",
                    "reference": "IRR computation — Newton-Raphson method",
                    "confidence": 0.95,
                })

            # ── Confidence based on data completeness ──────────────────────
            confidence = self._compute_confidence(policy_data, irr_result, extraction_confidence)

            latency_ms = int((time.time() - start) * 1000)

            # Build structured data for downstream use
            structured_data: Dict[str, Any] = {
                "policy_inputs": policy_data,
                "current_gsv": current_year_result.gsv if current_year_result else None,
                "paid_premiums": current_year_result.paid_premiums if current_year_result else None,
                "sv_percentage": current_year_result.sv_percentage if current_year_result else None,
                "irr_pct": irr_interpretation.get("irr_pct"),
                "irr_verdict": irr_interpretation.get("verdict"),
                "projection_table": [
                    {
                        "year": r.year,
                        "gsv": r.gsv,
                        "paid_premiums": r.paid_premiums,
                        "sv_pct": r.sv_percentage,
                        "notes": r.notes,
                    }
                    for r in current_and_future
                ],
                "fd_comparison": fd_comparison,
            }

            return AgentResult(
                response=response_text,
                confidence=confidence,
                sources=sources,
                latency_ms=latency_ms,
                tokens_in=llm_response.get("tokens_in", 0),
                tokens_out=llm_response.get("tokens_out", 0),
                structured_data=structured_data,
                follow_up_suggestions=[
                    "Would you like me to analyze the tax implications of surrendering?",
                    "Should I check if you qualify for a policy loan instead of surrendering?",
                    "Want me to compare what reinvesting the surrender value in a term + MF plan would yield?",
                ],
                products_relevant=["SVF"],  # Surrender Value Financing may be relevant
            )

        except Exception as e:
            plog.error("surrender_calculator", error=str(e))
            return AgentResult(
                response=self._error_response(),
                confidence=0.0,
                sources=[],
            )

    # ── Private helpers ────────────────────────────────────────────────────

    def _extract_policy_data(
        self, state: HibiscusState
    ) -> Tuple[Dict[str, Any], str, float]:
        """
        Extract policy parameters from state.
        Priority: document_context > session memory > user message parsing.
        Returns: (policy_data dict, source string, confidence float)
        """
        # Try document_context first (uploaded policy)
        doc_context = state.get("document_context")
        if doc_context and doc_context.get("extraction"):
            extraction = doc_context["extraction"]
            policy_data = {
                "annual_premium": extraction.get("annual_premium") or extraction.get("premium"),
                "policy_year": extraction.get("policy_year") or extraction.get("years_paid"),
                "policy_term": extraction.get("policy_term") or extraction.get("term"),
                "premium_term": extraction.get("premium_term") or extraction.get("premium_paying_term"),
                "sum_assured": extraction.get("sum_assured") or extraction.get("sum_insured"),
                "bonus_rate_per_1000": extraction.get("bonus_rate_per_1000", 35.0),
                "maturity_amount": extraction.get("maturity_amount"),
            }
            # Strip None values to trigger missing check
            policy_data = {k: v for k, v in policy_data.items() if v is not None}
            return policy_data, "document_extraction", doc_context.get("extraction_confidence", 0.85)

        # Try session history for previously mentioned policy details
        session_history = state.get("session_history", [])
        parsed_from_history = {}
        for turn in reversed(session_history[-6:]):  # Last 6 turns
            if isinstance(turn, dict) and turn.get("structured_data"):
                sd = turn["structured_data"]
                if sd.get("policy_inputs"):
                    parsed_from_history = sd["policy_inputs"]
                    break

        # Try parsing from current message
        message = state.get("message", "")
        parsed_from_message = self._parse_numbers_from_message(message)

        # Merge: message overrides history
        merged = {**parsed_from_history, **parsed_from_message}
        if merged:
            return merged, "user_message_parsed", 0.70

        return {}, "none", 0.0

    def _parse_numbers_from_message(self, message: str) -> Dict[str, Any]:
        """
        Attempt to parse policy parameters from free-text user message.
        Handles patterns like "₹50,000 premium", "20 year policy", "10 year premium term".
        """
        data: Dict[str, Any] = {}
        msg_lower = message.lower()

        # Annual premium
        premium_patterns = [
            r"(?:annual\s+)?premium\s+(?:of\s+)?(?:₹|rs\.?|inr)?\s*([\d,]+)",
            r"(?:₹|rs\.?|inr)\s*([\d,]+)\s+(?:annual\s+)?premium",
            r"pay(?:ing)?\s+(?:₹|rs\.?|inr)?\s*([\d,]+)",
        ]
        for pattern in premium_patterns:
            m = re.search(pattern, msg_lower)
            if m:
                data["annual_premium"] = float(m.group(1).replace(",", ""))
                break

        # Policy year (how many years paid)
        year_patterns = [
            r"(?:paid|completed|into)\s+(\d+)\s+years?",
            r"(\d+)\s+years?\s+(?:completed|old|ago|paid)",
            r"policy\s+year\s+(\d+)",
        ]
        for pattern in year_patterns:
            m = re.search(pattern, msg_lower)
            if m:
                data["policy_year"] = int(m.group(1))
                break

        # Policy term
        term_patterns = [
            r"(\d+)\s*[- ]?year\s+policy",
            r"policy\s+(?:term|period)\s+(?:of\s+)?(\d+)\s+years?",
            r"term\s+(?:of\s+)?(\d+)\s+years?",
        ]
        for pattern in term_patterns:
            m = re.search(pattern, msg_lower)
            if m:
                data["policy_term"] = int(m.group(1))
                break

        # Premium term
        premium_term_patterns = [
            r"premium\s+(?:paying\s+)?term\s+(?:of\s+)?(\d+)\s+years?",
            r"pay\s+for\s+(\d+)\s+years?",
        ]
        for pattern in premium_term_patterns:
            m = re.search(pattern, msg_lower)
            if m:
                data["premium_term"] = int(m.group(1))
                break

        # Sum assured
        sa_patterns = [
            r"sum\s+assured\s+(?:of\s+)?(?:₹|rs\.?|inr)?\s*([\d,]+(?:\.\d+)?)\s*(lakh|crore|l|cr)?",
            r"(?:₹|rs\.?|inr)\s*([\d,]+(?:\.\d+)?)\s*(lakh|crore|l|cr)?\s+sum\s+assured",
        ]
        for pattern in sa_patterns:
            m = re.search(pattern, msg_lower)
            if m:
                amount = float(m.group(1).replace(",", ""))
                unit = (m.group(2) or "").strip()
                if unit in ("lakh", "l"):
                    amount *= 100_000
                elif unit in ("crore", "cr"):
                    amount *= 10_000_000
                data["sum_assured"] = amount
                break

        return data

    def _check_missing_fields(self, policy_data: Dict[str, Any]) -> List[str]:
        """Return list of critical missing fields."""
        required = ["annual_premium", "policy_year", "policy_term"]
        return [f for f in required if not policy_data.get(f)]

    def _ask_for_missing_data(
        self, missing: List[str], partial_data: Dict[str, Any]
    ) -> str:
        """Return a specific question asking for missing fields."""
        field_labels = {
            "annual_premium": "annual premium amount (e.g., ₹50,000 per year)",
            "policy_year": "how many years of premiums you have already paid",
            "policy_term": "total policy term in years (e.g., 20-year policy)",
            "premium_term": "premium paying term (how many years you pay premiums)",
            "sum_assured": "sum assured / death benefit amount",
        }
        missing_labels = [field_labels.get(f, f) for f in missing]

        if len(missing_labels) == 1:
            question = f"To calculate the surrender value, I need one more detail: **{missing_labels[0]}**."
        else:
            items = "\n".join(f"  - {label}" for label in missing_labels)
            question = f"To calculate the surrender value accurately, I need the following details:\n{items}"

        if partial_data:
            provided = []
            if partial_data.get("annual_premium"):
                provided.append(f"Annual premium: {self._format_currency(float(partial_data['annual_premium']))}")
            if partial_data.get("policy_year"):
                provided.append(f"Years paid: {partial_data['policy_year']}")
            if partial_data.get("policy_term"):
                provided.append(f"Policy term: {partial_data['policy_term']} years")
            if provided:
                question = "I have some details already:\n" + "\n".join(f"  - {p}" for p in provided) + "\n\n" + question

        question += (
            "\n\nYou can also upload your policy document PDF and I'll extract all the details automatically."
        )
        return question

    def _compute_fd_comparison(
        self,
        annual_premium: float,
        policy_year: int,
        premium_term: int,
        current_year_result: Optional[SurrenderValueResult],
    ) -> Dict[str, Any]:
        """
        Compare: if user had invested all premiums in FD at the indicative rate,
        compounded annually.  Rate sourced from INDICATIVE_FD_RATE constant.
        """
        if not current_year_result:
            return {}

        fd_rate = INDICATIVE_FD_RATE
        fd_rate_pct = f"{fd_rate * 100:.1f}%"
        fd_value = 0.0
        for i in range(min(policy_year, premium_term)):
            # Each year's premium invested for remaining years
            years_invested = policy_year - i
            fd_value += annual_premium * ((1 + fd_rate) ** years_invested)

        gsv = current_year_result.gsv
        paid_premiums = current_year_result.paid_premiums

        return {
            "fd_corpus_if_invested": round(fd_value, 2),
            "gsv_now": gsv,
            "paid_premiums": paid_premiums,
            "fd_rate_used": f"{fd_rate_pct} p.a. (approximate SBI FD rate as of 2026-03-04)",
            "fd_vs_gsv_difference": round(fd_value - gsv, 2),
            "note": (
                f"FD comparison assumes all premiums invested from day one at {fd_rate_pct} compounding. "
                "Actual FD rates vary by bank and tenure. "
                "Policy also provides life cover which pure investment does not."
            ),
        }

    def _build_synthesis_prompt(
        self,
        policy_data: Dict[str, Any],
        current_year_result: Optional[SurrenderValueResult],
        projection_table: List[SurrenderValueResult],
        irr_interpretation: Dict[str, Any],
        fd_comparison: Dict[str, Any],
        message: str,
    ) -> str:
        """Build prompt for LLM synthesis using ONLY pre-computed numbers."""
        current_gsv_text = "Not available (policy in first 3 years — no surrender value)"
        if current_year_result and current_year_result.gsv > 0:
            current_gsv_text = (
                f"₹{current_year_result.gsv:,.0f} "
                f"({current_year_result.sv_percentage:.1f}% of ₹{current_year_result.paid_premiums:,.0f} paid)"
            )
        elif current_year_result:
            current_gsv_text = (
                f"₹0 — policy is in year {current_year_result.year} "
                f"(surrender value available only from year 3 onwards per IRDAI)"
            )

        # Build projection table text
        table_rows = []
        for r in projection_table:
            sv_note = f" | {r.notes}" if r.notes and r.notes != "Standard surrender" else ""
            table_rows.append(
                f"  Year {r.year}: GSV = ₹{r.gsv:,.0f} "
                f"({r.sv_percentage:.1f}% of ₹{r.paid_premiums:,.0f} paid){sv_note}"
            )
        projection_text = "\n".join(table_rows) if table_rows else "No projection available"

        # IRR text
        irr_text = "IRR could not be computed (maturity amount not available)"
        if irr_interpretation.get("irr_pct") is not None:
            irr_text = (
                f"IRR if held to maturity: {irr_interpretation['irr_pct']}% p.a.\n"
                f"Verdict: {irr_interpretation.get('verdict', '')}\n"
                f"Context: {irr_interpretation.get('context', '')}"
            )
            comps = irr_interpretation.get("comparisons", {})
            if comps:
                vs_fd = comps.get("vs_fd", 0)
                irr_text += f"\n  vs FD ({INDICATIVE_FD_RATE * 100:.1f}%): {'+' if vs_fd >= 0 else ''}{vs_fd:.2f}% difference"

        # FD comparison text
        fd_text = ""
        if fd_comparison:
            fd_text = (
                f"\nFD COMPARISON (if premiums invested in FD @ {fd_comparison['fd_rate_used']}):\n"
                f"  FD corpus today: ₹{fd_comparison['fd_corpus_if_invested']:,.0f}\n"
                f"  GSV today: ₹{fd_comparison['gsv_now']:,.0f}\n"
                f"  Difference: ₹{abs(fd_comparison['fd_vs_gsv_difference']):,.0f} "
                f"({'FD is better' if fd_comparison['fd_vs_gsv_difference'] > 0 else 'Policy GSV is better'})\n"
                f"  Note: {fd_comparison['note']}"
            )

        return f"""The user is asking about their insurance policy surrender value.

USER'S QUESTION: {message}

POLICY DETAILS (extracted/provided):
  Annual Premium: ₹{float(policy_data.get('annual_premium', 0)):,.0f}
  Policy Year: {policy_data.get('policy_year')} (years paid so far)
  Policy Term: {policy_data.get('policy_term')} years
  Premium Term: {policy_data.get('premium_term', policy_data.get('policy_term'))} years
  Sum Assured: ₹{float(policy_data.get('sum_assured', 0)):,.0f}
  Bonus Rate: ₹{policy_data.get('bonus_rate_per_1000', 35.0)} per ₹1,000 SA per year

COMPUTED RESULTS (these are deterministic IRDAI formula outputs — present them exactly):

CURRENT SURRENDER VALUE (Year {policy_data.get('policy_year')}):
  {current_gsv_text}
  Note: The Guaranteed Surrender Value (GSV) is the MINIMUM the insurer must pay.
        The Special Surrender Value (SSV) declared by the insurer may be higher.

SURRENDER VALUE PROJECTION (next 3 years):
{projection_text}

IRR ANALYSIS:
  {irr_text}
{fd_text}

INSTRUCTIONS FOR RESPONSE:
1. Present the surrender table clearly using the exact numbers above
2. Explain what GSV% means in plain language (per IRDAI guidelines)
3. Explain the IRR verdict — good/moderate/poor for an insurance product
4. Discuss whether it makes sense to surrender NOW vs wait (based on the numbers)
5. Mention that: life cover protection is LOST on surrender — factor this in
6. If policy year < 3: be very clear there is ZERO surrender value
7. Mention: "Contact your insurer for the actual Special Surrender Value, which may be higher"
8. End with IRDAI disclaimer
9. Suggest a policy loan as an alternative if user needs money but doesn't want to lose cover

DO NOT invent any numbers not in the computed data above.
"""

    def _compute_confidence(
        self,
        policy_data: Dict[str, Any],
        irr_result: Optional[float],
        extraction_confidence: float,
    ) -> float:
        """Score confidence based on data completeness."""
        # All required fields present
        all_required = all(policy_data.get(f) for f in ["annual_premium", "policy_year", "policy_term"])
        if not all_required:
            return 0.5

        # Optional fields boost confidence
        has_optional = sum(
            1 for f in ["sum_assured", "premium_term", "maturity_amount"]
            if policy_data.get(f)
        )
        base = 0.80
        base += has_optional * 0.03
        if irr_result is not None:
            base += 0.05
        # Blend with extraction confidence
        if extraction_confidence > 0:
            base = base * 0.6 + extraction_confidence * 0.4

        return round(min(base, 0.92), 2)


# ── Module-level run function (called by agent_dispatch) ──────────────────
_agent = SurrenderCalculatorAgent()


async def run(state: HibiscusState) -> Dict[str, Any]:
    """Entry point for agent_dispatch."""
    return await _agent(state)
