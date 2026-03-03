"""
PolicyAnalyzer — Agent 1 (THE MOST CRITICAL AGENT)
====================================================
Analyzes an uploaded insurance policy document.

This is the core value proposition of EAZR:
"I actually read your policy and can tell you exactly what you have."

FLOW:
1. Call extract_policy() → get structured data from EAZR's extraction engine
2. Call calculate_score() → get EAZR Protection Score
3. Call check_compliance() → get IRDAI compliance status
4. Synthesize: strengths, weaknesses, gaps, red flags, recommendations
5. Return with confidence scores per field and page references

GROUND TRUTH RULE:
Every number in the output comes from extraction or KG — NEVER from LLM imagination.
If a field wasn't extracted, say "I couldn't find X in your document."
"""
import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from hibiscus.agents.base import BaseAgent, AgentResult
from hibiscus.observability.logger import PipelineLogger
from hibiscus.orchestrator.state import HibiscusState


class PolicyAnalyzerAgent(BaseAgent):
    name = "policy_analyzer"
    description = "Policy document analyzer"
    default_tier = "deepseek_v3"
    prompt_file = "policy_analyzer.txt"

    async def execute(self, state: HibiscusState) -> AgentResult:
        plog = PipelineLogger(
            component=f"agent.{self.name}",
            request_id=state.get("request_id", "?"),
            session_id=state.get("session_id", "?"),
            user_id=state.get("user_id", "?"),
        )
        start = time.time()

        uploaded_files = state.get("uploaded_files", [])
        doc_context = state.get("document_context")
        message = state.get("message", "")

        # ── Step 1: Get or extract policy data ─────────────────────────────
        extraction_data = None
        extraction_confidence = 0.0
        sources = []

        if doc_context and doc_context.get("extraction"):
            # Cached extraction from document memory
            extraction_data = doc_context["extraction"]
            extraction_confidence = doc_context.get("extraction_confidence", 0.85)
            sources.append({
                "type": "document_extraction",
                "reference": f"Cached extraction: {doc_context.get('doc_id', 'unknown')}",
                "confidence": extraction_confidence,
            })
            plog.step_start("using_cached_extraction", doc_id=doc_context.get("doc_id", "?"))

        elif uploaded_files:
            # Fresh extraction from uploaded files
            doc_id = uploaded_files[0].get("doc_id") or uploaded_files[0].get("filename", "unknown")
            plog.tool_call("extract_policy", f"Extracting: {doc_id}")

            try:
                from hibiscus.tools.existing_api.client import EAZRClient, HibiscusToolError
                client = EAZRClient()
                # Call the existing EAZR extraction API
                file_info = uploaded_files[0]
                if "analysis_id" in file_info:
                    # Document already analyzed in botproject — fetch results
                    analysis_result = await client.get_analysis(
                        analysis_id=file_info["analysis_id"],
                        user_id=state.get("user_id", ""),
                    )
                    extraction_data = analysis_result.get("extracted_data", {})
                    extraction_confidence = 0.90
                    sources.append({
                        "type": "document_extraction",
                        "reference": f"Analysis ID: {file_info['analysis_id']}",
                        "confidence": extraction_confidence,
                        "tool": "extract_policy",
                    })
                    plog.tool_result("extract_policy", success=True, latency_ms=0)
                else:
                    # No pre-analyzed doc — signal that extraction is needed
                    plog.warning("no_analysis_id", files=len(uploaded_files))
                    extraction_data = None

            except Exception as e:
                plog.error("extraction_failed", error=str(e))
                extraction_data = None

        # ── Handle case where no extracted data is available ───────────────
        if not extraction_data and not doc_context:
            # Check if user is asking about a previously uploaded document
            if "what did i upload" in message.lower() or "my policy" in message.lower():
                return AgentResult(
                    response=(
                        "I don't have a policy document on file for your current session. "
                        "Please upload your insurance policy PDF and I'll analyze it for you. "
                        "You can upload it using the attachment button."
                    ),
                    confidence=0.95,
                    sources=[],
                )
            return AgentResult(
                response=(
                    "To analyze your policy, please upload your insurance policy document (PDF). "
                    "I'll extract all the details and give you a complete analysis including "
                    "your EAZR Protection Score, coverage gaps, and recommendations."
                ),
                confidence=0.95,
                sources=[],
            )

        # ── Step 2: Get EAZR Protection Score ─────────────────────────────
        eazr_score = None
        score_data = {}
        if extraction_data:
            try:
                from hibiscus.tools.existing_api.client import EAZRClient
                client = EAZRClient()

                if doc_context and doc_context.get("analysis_id"):
                    score_result = await client.get_protection_score(
                        analysis_id=doc_context["analysis_id"],
                        user_id=state.get("user_id", ""),
                    )
                    eazr_score = score_result.get("eazr_score")
                    score_data = score_result.get("score_breakdown", {})
                    plog.tool_result("calculate_score", success=True, latency_ms=0)

            except Exception as e:
                plog.warning("score_fetch_failed", error=str(e))

        # ── Step 3: Synthesize analysis with LLM ──────────────────────────
        plog.step_start("synthesizing_analysis")

        # Build prompt with ONLY extracted data (no invented numbers)
        synthesis_prompt = self._build_synthesis_prompt(
            extraction_data=extraction_data,
            eazr_score=eazr_score,
            score_data=score_data,
            message=message,
        )

        try:
            from hibiscus.llm.router import call_llm
            llm_response = await call_llm(
                messages=[
                    {"role": "system", "content": self._system_prompt + "\n\n" + self._agent_prompt},
                    {"role": "user", "content": synthesis_prompt},
                ],
                tier=self.default_tier,
                conversation_id=state.get("conversation_id", "?"),
                agent=self.name,
            )

            response_text = llm_response["content"]

            # Compute overall confidence
            overall_confidence = self._compute_confidence(
                extraction_data=extraction_data,
                extraction_confidence=extraction_confidence,
                eazr_score=eazr_score,
            )

            latency_ms = int((time.time() - start) * 1000)

            return AgentResult(
                response=response_text,
                confidence=overall_confidence,
                sources=sources,
                latency_ms=latency_ms,
                tokens_in=llm_response.get("tokens_in", 0),
                tokens_out=llm_response.get("tokens_out", 0),
                structured_data={
                    "extraction": extraction_data,
                    "eazr_score": eazr_score,
                    "score_breakdown": score_data,
                },
                follow_up_suggestions=self._follow_ups(extraction_data),
                eazr_products_relevant=self._check_ipf_svf_relevance(extraction_data),
            )

        except Exception as e:
            plog.error("synthesis_failed", error=str(e))
            # Fallback: return raw extraction without synthesis
            return self._fallback_response(extraction_data, eazr_score, sources)

    def _build_synthesis_prompt(
        self,
        extraction_data: Optional[Dict],
        eazr_score: Optional[int],
        score_data: Dict,
        message: str,
    ) -> str:
        """Build synthesis prompt using ONLY extracted data — no invented numbers."""
        if not extraction_data:
            return "No extraction data available. Ask user to upload their policy document."

        # Serialize extraction data
        extraction_text = json.dumps(extraction_data, indent=2, ensure_ascii=False)
        score_text = f"EAZR Protection Score: {eazr_score}/100" if eazr_score else "Score: Not yet calculated"

        if score_data:
            score_breakdown = json.dumps(score_data, indent=2, ensure_ascii=False)
            score_text += f"\nScore Breakdown:\n{score_breakdown}"

        return f"""Analyze this insurance policy based on the EXTRACTED DATA below.

USER'S QUESTION/REQUEST: {message}

{score_text}

EXTRACTED POLICY DATA (ground truth — cite page numbers when available):
{extraction_text}

INSTRUCTIONS:
1. Every number you cite must come from the extracted data above
2. If a field shows "not_found" or is missing → say "I couldn't find [field] in your document"
3. Do NOT invent copay %, sub-limits, premiums, or sum insured values
4. Use Indian format: ₹, lakhs/crores, DD/MM/YYYY dates
5. Structure your response per the Policy Analyzer prompt format
6. Include confidence indicators where appropriate
7. End with IRDAI disclaimer

CRITICAL: If user asked "what did I upload?" → summarize the policy in 2-3 sentences first."""

    def _compute_confidence(
        self,
        extraction_data: Optional[Dict],
        extraction_confidence: float,
        eazr_score: Optional[int],
    ) -> float:
        """Compute overall response confidence."""
        if not extraction_data:
            return 0.3

        # Start with extraction confidence
        confidence = extraction_confidence

        # Boost if EAZR score available (means extraction was thorough)
        if eazr_score:
            confidence = min(confidence + 0.05, 0.95)

        # Check extraction completeness
        key_fields = ["policy_type", "insurer", "sum_insured", "premium"]
        found = sum(1 for f in key_fields if extraction_data.get(f))
        completeness = found / len(key_fields)
        confidence = confidence * 0.7 + completeness * 0.3

        return round(confidence, 2)

    def _follow_ups(self, extraction_data: Optional[Dict]) -> List[str]:
        """Generate relevant follow-up suggestions."""
        base = [
            "Would you like me to compare this with similar policies in the market?",
            "Do you want an explanation of any specific clause or term?",
        ]
        if extraction_data:
            policy_type = extraction_data.get("policy_type", "").lower()
            if "life" in policy_type or "endowment" in policy_type or "ulip" in policy_type:
                base.append("Should I calculate the surrender value of this policy?")
            elif "health" in policy_type:
                base.append("Would you like guidance on how to file a cashless claim?")
        return base

    def _check_ipf_svf_relevance(self, extraction_data: Optional[Dict]) -> List[str]:
        """Check if IPF or SVF products are relevant."""
        if not extraction_data:
            return []
        products = []
        policy_type = extraction_data.get("policy_type", "").lower()
        if any(t in policy_type for t in ["life", "endowment", "ulip", "money back"]):
            products.append("SVF")  # Surrender Value Financing
        premium = extraction_data.get("annual_premium", 0)
        if isinstance(premium, (int, float)) and premium > 50000:
            products.append("IPF")  # Insurance Premium Financing
        return products

    def _fallback_response(
        self,
        extraction_data: Optional[Dict],
        eazr_score: Optional[int],
        sources: List,
    ) -> AgentResult:
        """Minimal response when synthesis fails."""
        if extraction_data:
            policy_type = extraction_data.get("policy_type", "insurance")
            insurer = extraction_data.get("insurer", "your insurer")
            sum_insured = extraction_data.get("sum_insured", "")
            si_text = f" with sum insured of {self._format_currency(float(sum_insured))}" if sum_insured else ""
            score_text = f" Your EAZR Protection Score is **{eazr_score}/100**." if eazr_score else ""

            return AgentResult(
                response=(
                    f"I've analyzed your {policy_type} policy from {insurer}{si_text}.{score_text}\n\n"
                    "I encountered an issue generating the full analysis. "
                    "Please ask me specific questions about your policy and I'll answer them directly."
                ),
                confidence=0.70,
                sources=sources,
            )
        return AgentResult(
            response="I need your policy document to analyze it. Please upload your insurance policy PDF.",
            confidence=0.90,
            sources=[],
        )


# ── Module-level run function (called by agent_dispatch) ──────────────────
_agent = PolicyAnalyzerAgent()


async def run(state: HibiscusState) -> Dict[str, Any]:
    """Entry point for agent_dispatch."""
    return await _agent(state)
