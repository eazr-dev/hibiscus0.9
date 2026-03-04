"""
PolicyAnalyzer — Agent 1 (THE MOST CRITICAL AGENT)
====================================================
Analyzes an uploaded insurance policy document using NATIVE extraction.

FLOW:
1. Get PDF data (from upload or cached)
2. Process PDF → text with page markers (native)
3. Classify policy type (native, 3-tier)
4. Extract structured data (native, DeepSeek V3.2)
5. Validate extraction (native, 5-check)
6. Score (native, using KG benchmarks)
7. Gap analysis (native)
8. Synthesize response with LLM

GROUND TRUTH RULE:
Every number in the output comes from extraction (with page ref) or KG — NEVER LLM imagination.
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
"""
import json
import time
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

        extraction_data = None
        extraction_confidence = 0.0
        sources: List[Dict] = []
        eazr_score = None
        score_data: Dict = {}
        gaps_data: List[Dict] = []
        validation_data: Dict = {}

        # ── Step 1: Use cached extraction if available ────────────────────
        if doc_context and doc_context.get("extraction"):
            extraction_data = doc_context["extraction"]
            extraction_confidence = doc_context.get("extraction_confidence", 0.85)
            eazr_score = doc_context.get("eazr_score")
            score_data = doc_context.get("score_breakdown", {})
            gaps_data = doc_context.get("gaps", [])
            sources.append({
                "type": "document_extraction",
                "reference": f"Cached extraction: {doc_context.get('doc_id', 'unknown')}",
                "confidence": extraction_confidence,
            })
            plog.step_start("using_cached_extraction", doc_id=doc_context.get("doc_id", "?"))

        # ── Step 2: Native extraction from uploaded PDF ───────────────────
        elif uploaded_files:
            file_info = uploaded_files[0]
            doc_id = file_info.get("doc_id") or file_info.get("filename", "unknown")
            plog.step_start("native_extraction", doc_id=doc_id)

            native_result = await self._native_extract(file_info, state, plog)

            if native_result:
                extraction_data = native_result["extraction"]
                extraction_confidence = native_result.get("confidence", 0.90)
                eazr_score = native_result.get("eazr_score")
                score_data = native_result.get("score_breakdown", {})
                gaps_data = native_result.get("gaps", [])
                validation_data = native_result.get("validation", {})
                sources.append({
                    "type": "native_extraction",
                    "reference": f"Native pipeline: {doc_id}",
                    "confidence": extraction_confidence,
                    "category": native_result.get("category", ""),
                })
            else:
                plog.warning("native_extraction_returned_none")

        # ── Handle no data ────────────────────────────────────────────────
        if not extraction_data and not doc_context:
            if "what did i upload" in message.lower() or "my policy" in message.lower():
                return AgentResult(
                    response=(
                        "I don't have a policy document on file for your current session. "
                        "Please upload your insurance policy PDF and I'll analyze it for you."
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

        # ── Step 3: Synthesize analysis ───────────────────────────────────
        plog.step_start("synthesizing_analysis")

        synthesis_prompt = self._build_synthesis_prompt(
            extraction_data=extraction_data,
            eazr_score=eazr_score,
            score_data=score_data,
            gaps_data=gaps_data,
            validation_data=validation_data,
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
            overall_confidence = self._compute_confidence(
                extraction_data, extraction_confidence, eazr_score,
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
                    "gaps": gaps_data,
                    "validation": validation_data,
                },
                follow_up_suggestions=self._follow_ups(extraction_data),
                products_relevant=self._check_ipf_svf_relevance(extraction_data),
            )

        except Exception as e:
            plog.error("synthesis_failed", error=str(e))
            return self._fallback_response(extraction_data, eazr_score, sources)

    # ── Native Extraction Pipeline ──────────────────────────────────────

    async def _native_extract(
        self, file_info: Dict, state: HibiscusState, plog: PipelineLogger
    ) -> Optional[Dict]:
        """
        Run the full native extraction pipeline:
        PDF → text → classify → extract → validate → score → gaps
        """
        try:
            from hibiscus.extraction.processor import document_processor
            from hibiscus.extraction.classifier import policy_classifier
            from hibiscus.extraction.validation import validation_engine
            from hibiscus.extraction.scoring import scoring_engine
            from hibiscus.extraction.gap_analysis import gap_analysis_engine

            # Get PDF data
            pdf_data = await self._get_pdf_data(file_info, state)
            if not pdf_data:
                plog.warning("no_pdf_data")
                return None

            # 1. Process PDF → text
            plog.step_start("pdf_processing")
            doc = await document_processor.process(
                pdf_data, filename=file_info.get("filename"),
            )
            if doc.char_count < 200:
                plog.warning("pdf_text_too_sparse", chars=doc.char_count)
                return None
            plog.step_complete("pdf_processing", pages=doc.total_pages, chars=doc.char_count)

            # 2. Classify policy type
            plog.step_start("classification")
            classification = await policy_classifier.classify(doc.first_pages_text)
            plog.step_complete(
                "classification",
                category=classification.category,
                sub_type=classification.sub_type,
                confidence=classification.confidence,
                tier=classification.tier_used,
            )

            # 3. Extract structured data (LLM call)
            plog.step_start("extraction")
            extractor = self._get_extractor(classification.category)
            extraction = await extractor.extract(doc, classification)
            if not extraction:
                plog.warning("extraction_empty")
                return None
            plog.step_complete("extraction", fields=len(extraction))

            # 4. Validate extraction
            plog.step_start("validation")
            validation = await validation_engine.validate(extraction, classification.category)
            plog.step_complete(
                "validation",
                score=validation.score,
                confidence=validation.confidence,
                errors=len(validation.errors),
            )

            # 5. Score
            plog.step_start("scoring")
            scoring = await scoring_engine.score(extraction, classification.category)
            plog.step_complete(
                "scoring",
                eazr_score=scoring.eazr_score,
                verdict=scoring.verdict,
            )

            # 6. Gap analysis
            plog.step_start("gap_analysis")
            gaps = await gap_analysis_engine.analyze(
                extraction, scoring, classification.category,
            )
            plog.step_complete("gap_analysis", total_gaps=gaps.total_gaps)

            # Build result
            return {
                "extraction": extraction,
                "category": classification.category,
                "sub_type": classification.sub_type,
                "confidence": validation.weighted_confidence,
                "eazr_score": scoring.eazr_score,
                "score_breakdown": {
                    "verdict": scoring.verdict,
                    "verdict_color": scoring.verdict_color,
                    "components": [
                        {"name": c.name, "score": c.score, "weight": c.weight}
                        for c in scoring.components
                    ],
                    "vfm_score": scoring.vfm_score,
                    "zone_classification": scoring.zone_classification,
                },
                "gaps": [
                    {
                        "type": g.gap_type,
                        "severity": g.severity,
                        "category": g.category,
                        "description": g.description,
                        "impact": g.impact,
                        "recommendation": g.recommendation,
                        "estimated_cost": g.estimated_cost,
                    }
                    for g in gaps.gaps
                ],
                "validation": {
                    "score": validation.score,
                    "confidence": validation.confidence,
                    "errors": len(validation.errors),
                    "warnings": len(validation.warnings),
                },
            }

        except Exception as e:
            plog.error("native_extraction_failed", error=str(e))
            return None

    async def _get_pdf_data(self, file_info: Dict, state: HibiscusState) -> Optional[bytes]:
        """Get PDF bytes from file_info."""
        # Check for direct bytes
        if "data" in file_info:
            return file_info["data"]
        if "content" in file_info:
            data = file_info["content"]
            if isinstance(data, bytes):
                return data
            if isinstance(data, str):
                import base64
                try:
                    return base64.b64decode(data)
                except Exception:
                    return data.encode()

        # Check for file path
        if "path" in file_info:
            try:
                with open(file_info["path"], "rb") as f:
                    return f.read()
            except Exception:
                pass

        # Check for S3/URL
        if "url" in file_info or "s3_key" in file_info:
            # TODO: Download from S3/URL
            pass

        return None

    def _get_extractor(self, category: str):
        """Get the appropriate extractor for the category."""
        from hibiscus.extraction.extractors.health import health_extractor
        from hibiscus.extraction.extractors.life import life_extractor
        from hibiscus.extraction.extractors.motor import motor_extractor
        from hibiscus.extraction.extractors.travel import travel_extractor
        from hibiscus.extraction.extractors.pa import pa_extractor

        extractors = {
            "health": health_extractor,
            "life": life_extractor,
            "motor": motor_extractor,
            "travel": travel_extractor,
            "pa": pa_extractor,
        }
        return extractors.get(category, health_extractor)

    # ── Synthesis ───────────────────────────────────────────────────────

    def _build_synthesis_prompt(
        self,
        extraction_data: Optional[Dict],
        eazr_score: Optional[int],
        score_data: Dict,
        gaps_data: List[Dict],
        validation_data: Dict,
        message: str,
    ) -> str:
        """Build synthesis prompt using ONLY extracted data."""
        if not extraction_data:
            return "No extraction data available. Ask user to upload their policy document."

        extraction_text = json.dumps(extraction_data, indent=2, ensure_ascii=False, default=str)
        score_text = f"EAZR Protection Score: {eazr_score}/100" if eazr_score else "Score: Not yet calculated"

        if score_data:
            score_text += f"\nScore Breakdown:\n{json.dumps(score_data, indent=2, ensure_ascii=False, default=str)}"

        gaps_text = ""
        if gaps_data:
            gaps_text = f"\n\nCOVERAGE GAPS IDENTIFIED ({len(gaps_data)} gaps):\n"
            for g in gaps_data:
                gaps_text += f"\n[{g.get('severity', '?')}] {g.get('category', '')}: {g.get('description', '')}"
                if g.get("recommendation"):
                    gaps_text += f"\n  → Recommendation: {g['recommendation']}"
                if g.get("estimated_cost"):
                    gaps_text += f" (est. ₹{g['estimated_cost']:,}/year)"

        validation_text = ""
        if validation_data:
            validation_text = f"\n\nVALIDATION: Score {validation_data.get('score', '?')}/100, Confidence: {validation_data.get('confidence', '?')}"

        return f"""Analyze this insurance policy based on the EXTRACTED DATA below.

USER'S QUESTION/REQUEST: {message}

{score_text}{validation_text}{gaps_text}

EXTRACTED POLICY DATA (ground truth — cite page numbers when available):
{extraction_text}

INSTRUCTIONS:
1. Every number you cite must come from the extracted data above
2. For fields with source_page — cite as "(page X)" in your response
3. If a field has confidence < 0.5 — caveat it: "This appears to be [value] but I'm not fully confident"
4. If a field is null/not found → say "I couldn't find [field] in your document"
5. Use Indian format: ₹, lakhs/crores, DD/MM/YYYY dates
6. Include the coverage gaps analysis with severity levels
7. End with IRDAI disclaimer

CRITICAL: If user asked "what did I upload?" → summarize the policy in 2-3 sentences first."""

    def _compute_confidence(
        self,
        extraction_data: Optional[Dict],
        extraction_confidence: float,
        eazr_score: Optional[int],
    ) -> float:
        if not extraction_data:
            return 0.3

        confidence = extraction_confidence
        if eazr_score:
            confidence = min(confidence + 0.05, 0.95)

        # Check extraction completeness
        key_fields = ["policyNumber", "insurerName", "sumInsured", "totalPremium",
                       "policy_type", "insurer", "sum_insured", "premium"]
        found = sum(
            1 for f in key_fields
            if extraction_data.get(f) and (
                not isinstance(extraction_data[f], dict) or extraction_data[f].get("value")
            )
        )
        completeness = found / max(len(key_fields), 1)
        confidence = confidence * 0.7 + completeness * 0.3

        return round(confidence, 2)

    def _follow_ups(self, extraction_data: Optional[Dict]) -> List[str]:
        base = [
            "Would you like me to compare this with similar policies in the market?",
            "Do you want an explanation of any specific clause or term?",
        ]
        if extraction_data:
            # Check policy type from either native or legacy format
            policy_type = ""
            pt_field = extraction_data.get("policyType") or extraction_data.get("policy_type")
            if isinstance(pt_field, dict):
                policy_type = str(pt_field.get("value", "")).lower()
            elif pt_field:
                policy_type = str(pt_field).lower()

            if any(t in policy_type for t in ["life", "endowment", "ulip", "money back"]):
                base.append("Should I calculate the surrender value of this policy?")
            elif "health" in policy_type:
                base.append("Would you like guidance on how to file a cashless claim?")
        return base

    def _check_ipf_svf_relevance(self, extraction_data: Optional[Dict]) -> List[str]:
        if not extraction_data:
            return []
        products = []

        policy_type = ""
        pt_field = extraction_data.get("policyType") or extraction_data.get("policy_type")
        if isinstance(pt_field, dict):
            policy_type = str(pt_field.get("value", "")).lower()
        elif pt_field:
            policy_type = str(pt_field).lower()

        if any(t in policy_type for t in ["life", "endowment", "ulip", "money back"]):
            products.append("SVF")

        premium_field = extraction_data.get("totalPremium") or extraction_data.get("premium")
        premium = 0
        if isinstance(premium_field, dict):
            try:
                premium = float(str(premium_field.get("value", 0)).replace(",", ""))
            except (ValueError, TypeError):
                pass
        elif premium_field:
            try:
                premium = float(str(premium_field).replace(",", ""))
            except (ValueError, TypeError):
                pass

        if premium > 50000:
            products.append("IPF")
        return products

    def _fallback_response(
        self, extraction_data: Optional[Dict], eazr_score: Optional[int], sources: List,
    ) -> AgentResult:
        if extraction_data:
            # Extract key info from either format
            insurer_field = extraction_data.get("insurerName") or extraction_data.get("insurer")
            insurer = ""
            if isinstance(insurer_field, dict):
                insurer = str(insurer_field.get("value", "your insurer"))
            elif insurer_field:
                insurer = str(insurer_field)

            score_text = f" Your EAZR Protection Score is **{eazr_score}/100**." if eazr_score else ""

            return AgentResult(
                response=(
                    f"I've analyzed your policy from {insurer}.{score_text}\n\n"
                    "I encountered an issue generating the full analysis. "
                    "Please ask me specific questions about your policy."
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
