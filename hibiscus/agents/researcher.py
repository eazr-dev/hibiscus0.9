"""
🌺 Hibiscus v0.9 | EAZR AI Insurance Intelligence Engine
Researcher agent — web search + RAG for real-time insurance market intelligence.
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
"""
import json
import time
from typing import Any, Dict, List, Optional, Tuple

from hibiscus.agents.base import BaseAgent, AgentResult
from hibiscus.llm.router import call_llm
from hibiscus.observability.logger import PipelineLogger
from hibiscus.orchestrator.state import HibiscusState

AGENT_SYSTEM_PROMPT = """You are Hibiscus, EAZR's insurance AI research assistant.

Your role: Provide current, sourced information about insurance products, regulations, and market data.

CRITICAL RULES:
1. CLEARLY distinguish between: web search results (current), RAG corpus (may be dated), and general knowledge
2. ALWAYS cite sources with URLs and publication dates where available
3. NEVER present LLM-generated information as "current" — it has a knowledge cutoff
4. For regulatory information: always recommend verifying at irdai.gov.in
5. For product comparisons: never say one product is "the best" — present criteria
6. Use ₹ symbol, Indian formats
7. Note recency explicitly: "As of [date/source]" for any data point

WHEN WEB SEARCH IS UNAVAILABLE:
- Use general knowledge but explicitly say "Based on publicly available data as of my training"
- Recommend the user visit irdai.gov.in, policybazaar.com, or insurer websites for current data
- Never pretend to have current data if you don't

TONE: Researched, balanced, citing sources. Like a thorough insurance journalist.
"""

# Research topic categories and their key sources
RESEARCH_TOPICS = {
    "irdai_news": {
        "label": "IRDAI Regulatory Updates",
        "primary_sources": ["irdai.gov.in", "IRDAI Annual Reports"],
        "search_query_template": "IRDAI regulations insurance India 2025",
        "rag_collections": ["irdai_circulars"],
    },
    "product_comparison": {
        "label": "Insurance Product Comparison",
        "primary_sources": [
            "IRDAI Annual Report CSR data",
            "Insurer websites",
            "policybazaar.com",
        ],
        "search_query_template": "{product_type} insurance comparison India 2025",
        "rag_collections": ["product_features"],
    },
    "claims_data": {
        "label": "Claims Settlement Data",
        "primary_sources": ["IRDAI Annual Report 2023-24"],
        "search_query_template": "insurance claim settlement ratio India 2024 IRDAI",
        "rag_collections": ["irdai_circulars", "insurer_data"],
    },
    "insurance_rules": {
        "label": "Insurance Rules and Policies",
        "primary_sources": ["Insurance Act 1938", "IRDAI regulations"],
        "search_query_template": "insurance rules India 2025 IRDAI",
        "rag_collections": ["irdai_circulars", "regulations"],
    },
    "market_news": {
        "label": "Insurance Market News",
        "primary_sources": ["ET Insurance", "Business Standard", "LiveMint"],
        "search_query_template": "India insurance market news 2025",
        "rag_collections": [],
    },
}

# Static knowledge: key CSR/ICR data from IRDAI Annual Report 2023-24
# (Tier 1 reference — always available even without live search)
STATIC_INSURER_DATA = {
    "life_csr_2023_24": {
        "LIC": 98.62,
        "Max Life": 99.51,
        "HDFC Life": 99.39,
        "SBI Life": 97.05,
        "ICICI Prudential Life": 97.82,
        "Tata AIA Life": 99.03,
        "Bajaj Allianz Life": 99.02,
        "source": "IRDAI Annual Report 2023-24",
        "note": "CSR = Claims Settlement Ratio — percentage of death claims settled",
    },
    "health_icr_2023_24": {
        "Star Health": 65.09,
        "Niva Bupa": 87.66,
        "Care Health": 55.00,
        "HDFC ERGO": 107.24,
        "Bajaj Allianz Health": 79.10,
        "source": "IRDAI Annual Report 2023-24",
        "note": "ICR = Incurred Claim Ratio — lower is better for insurer, but very low (<50%) may indicate strict claims processing",
    },
}

# Topic detection keywords
TOPIC_KEYWORDS = {
    "irdai_news": [
        "irdai", "regulation", "regulatory", "circular", "rule change",
        "new rule", "insurance rule", "mandate",
    ],
    "product_comparison": [
        "best", "compare", "vs", "versus", "which is better", "top",
        "review", "recommend", "suggest", "rating",
    ],
    "claims_data": [
        "claim settlement", "csr", "icr", "how good", "settles claim",
        "rejection rate", "how reliable",
    ],
    "insurance_rules": [
        "free look", "portability", "cooling period", "waiting period",
        "grace period", "surrender", "contestability",
    ],
    "market_news": [
        "latest", "news", "2025", "2024", "recent", "new launch", "new policy",
        "announced", "update",
    ],
}


class ResearcherAgent(BaseAgent):
    """Fetches and synthesizes insurance research from available sources."""

    name = "researcher"
    description = "Insurance market researcher"
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
            message = state.get("message", "")

            # ── Step 1: Detect research topic ──────────────────────────────
            plog.step_start("detect_research_topic")
            topic = self._detect_topic(message)
            topic_config = RESEARCH_TOPICS.get(topic, RESEARCH_TOPICS["market_news"])
            plog.step_complete("detect_research_topic", topic=topic)

            # ── Step 2: Attempt web search (Tavily) ────────────────────────
            plog.step_start("web_search")
            web_results, web_available = await self._try_web_search(
                message, topic_config.get("search_query_template", message)
            )
            plog.step_complete(
                "web_search",
                available=web_available,
                results_count=len(web_results),
            )

            # ── Step 3: Get relevant static data ──────────────────────────
            plog.step_start("gather_static_data")
            static_data = self._get_relevant_static_data(message, topic)
            plog.step_complete("gather_static_data", data_keys=list(static_data.keys()))

            # ── Step 4: LLM synthesis ──────────────────────────────────────
            plog.step_start("llm_synthesis")
            synthesis_prompt = self._build_synthesis_prompt(
                message=message,
                topic=topic,
                topic_config=topic_config,
                web_results=web_results,
                web_available=web_available,
                static_data=static_data,
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

            # ── Step 5: Build sources ──────────────────────────────────────
            sources = self._build_sources(topic, web_results, static_data)

            # Confidence: high if web search available and found results
            if web_available and web_results:
                confidence = 0.82
            elif static_data:
                confidence = 0.72  # Static data is slightly dated
            else:
                confidence = 0.60  # General knowledge only

            latency_ms = int((time.time() - start) * 1000)

            return AgentResult(
                response=response_text,
                confidence=confidence,
                sources=sources,
                latency_ms=latency_ms,
                tokens_in=llm_response.get("tokens_in", 0),
                tokens_out=llm_response.get("tokens_out", 0),
                structured_data={
                    "topic": topic,
                    "web_search_used": web_available,
                    "web_results_count": len(web_results),
                    "static_data_used": bool(static_data),
                },
                follow_up_suggestions=self._build_follow_ups(topic),
            )

        except Exception as e:
            plog.error("researcher", error=str(e))
            return AgentResult(
                response=self._error_response(),
                confidence=0.0,
                sources=[],
            )

    # ── Private helpers ────────────────────────────────────────────────────

    def _detect_topic(self, message: str) -> str:
        """Detect the research topic from the user message."""
        msg_lower = message.lower()
        topic_scores: Dict[str, int] = {}

        for topic, keywords in TOPIC_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in msg_lower)
            if score > 0:
                topic_scores[topic] = score

        if topic_scores:
            return max(topic_scores, key=lambda t: topic_scores[t])

        return "market_news"  # Default

    async def _try_web_search(
        self, query: str, template: str
    ) -> Tuple[List[Dict[str, Any]], bool]:
        """
        Attempt Tavily web search. Returns (results, available_bool).
        Falls back gracefully if Tavily is not configured.
        """
        try:
            from hibiscus.config import settings
            if not getattr(settings, "tavily_api_key", None):
                return [], False

            from tavily import AsyncTavilyClient
            client = AsyncTavilyClient(api_key=settings.tavily_api_key)

            # Build search query
            search_query = template.format(
                product_type=self._extract_product_type(query)
            ) if "{product_type}" in template else query

            response = await client.search(
                query=search_query,
                search_depth="basic",
                max_results=5,
                include_answer=True,
            )

            results = []
            for r in response.get("results", []):
                results.append({
                    "title": r.get("title", ""),
                    "url": r.get("url", ""),
                    "content": r.get("content", "")[:500],  # Truncate
                    "published_date": r.get("published_date", "Unknown date"),
                    "score": r.get("score", 0),
                })

            return results, True

        except ImportError:
            return [], False
        except Exception:
            return [], False

    def _extract_product_type(self, message: str) -> str:
        """Extract product type from message for search query building."""
        msg_lower = message.lower()
        if "health" in msg_lower:
            return "health"
        if "term" in msg_lower or "life" in msg_lower:
            return "life"
        if "motor" in msg_lower or "car" in msg_lower:
            return "motor"
        if "travel" in msg_lower:
            return "travel"
        return "insurance"

    def _get_relevant_static_data(
        self, message: str, topic: str
    ) -> Dict[str, Any]:
        """Get relevant static data based on topic."""
        msg_lower = message.lower()
        data: Dict[str, Any] = {}

        # CSR data for life insurers
        if any(w in msg_lower for w in ["life insurance", "term insurance", "claim settlement", "csr"]):
            data["life_csr"] = STATIC_INSURER_DATA["life_csr_2023_24"]

        # ICR data for health insurers
        if any(w in msg_lower for w in ["health insurance", "icr", "incurred claim", "star health",
                                         "niva bupa", "care health"]):
            data["health_icr"] = STATIC_INSURER_DATA["health_icr_2023_24"]

        # Key IRDAI regulations (static knowledge)
        if topic == "insurance_rules" or "free look" in msg_lower:
            data["key_regulations"] = {
                "free_look_period": "15 days for regular policies, 30 days for policies sold through distance marketing",
                "portability": "Mandatory for health insurance — insurer cannot deny portability",
                "waiting_period": "Initial waiting period typically 30 days; 2-4 years for pre-existing conditions",
                "grace_period": "15-30 days depending on premium frequency",
                "contestability": "30 days for life insurance after 3 years of policy being in force",
                "source": "IRDAI (Protection of Policyholders' Interests) Regulations 2017",
            }

        return data

    def _build_synthesis_prompt(
        self,
        message: str,
        topic: str,
        topic_config: Dict[str, Any],
        web_results: List[Dict[str, Any]],
        web_available: bool,
        static_data: Dict[str, Any],
    ) -> str:
        """Build synthesis prompt."""
        static_text = json.dumps(static_data, indent=2, ensure_ascii=False) if static_data else "None available"

        if web_available and web_results:
            web_text = json.dumps(web_results[:4], indent=2, ensure_ascii=False)
            data_source_note = "Web search results are available and current."
        elif not web_available:
            web_text = "Web search not available in this session."
            data_source_note = (
                "Web search is not available. Use static data + general knowledge. "
                "EXPLICITLY tell the user: 'Web search is unavailable — this information "
                "is based on my training data as of early 2025. Please verify current data at irdai.gov.in'"
            )
        else:
            web_text = "Web search returned no results."
            data_source_note = (
                "Web search returned no results. Use static data + general knowledge. "
                "Inform the user to check irdai.gov.in for the latest data."
            )

        return f"""The user is asking for insurance research/information.

USER'S QUESTION: {message}
RESEARCH TOPIC: {topic_config.get('label', topic)}

DATA SOURCE NOTE: {data_source_note}

WEB SEARCH RESULTS (if available):
{web_text}

STATIC DATA (from IRDAI Annual Report 2023-24 and regulatory knowledge):
{static_text}

PRIMARY SOURCES FOR THIS TOPIC: {', '.join(topic_config.get('primary_sources', []))}

INSTRUCTIONS FOR RESPONSE:
1. Address the user's specific question directly
2. Clearly mark source for EVERY data point:
   - "[Source: IRDAI Annual Report 2023-24]" for CSR/ICR data
   - "[Source: Web search — title, URL, date]" for web results
   - "[Based on training data — verify for current information]" for general knowledge
3. If comparing products: present criteria (CSR, ICR, features, premiums) not a winner
4. If regulatory: cite regulation name and effective date
5. Always add: "For the most current information, visit irdai.gov.in"
6. Use ₹ symbol, Indian format
7. End with note about recency if web search was unavailable
8. Mention IRDAI disclaimer for recommendations

FORMAT:
- Use headers for different sections
- Use bullet points for comparative data
- Bold key statistics
- Cite sources inline

Do NOT present general knowledge as current verified data.
"""

    def _build_sources(
        self,
        topic: str,
        web_results: List[Dict[str, Any]],
        static_data: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Build source list from available data."""
        sources = []

        for result in web_results[:4]:
            sources.append({
                "type": "web_search",
                "reference": result.get("title", "Web search result"),
                "url": result.get("url", ""),
                "date": result.get("published_date", "Unknown"),
                "confidence": min(0.85, result.get("score", 0.7)),
            })

        if static_data.get("life_csr") or static_data.get("health_icr"):
            sources.append({
                "type": "official_report",
                "reference": "IRDAI Annual Report 2023-24",
                "url": "https://irdai.gov.in",
                "confidence": 0.90,
            })

        if static_data.get("key_regulations"):
            sources.append({
                "type": "regulation",
                "reference": "IRDAI (Protection of Policyholders' Interests) Regulations 2017",
                "url": "https://irdai.gov.in",
                "confidence": 0.92,
            })

        if not sources:
            sources.append({
                "type": "training_knowledge",
                "reference": "General insurance knowledge (training data — verify currency)",
                "confidence": 0.60,
            })

        return sources

    def _build_follow_ups(self, topic: str) -> List[str]:
        """Build follow-up suggestions."""
        follow_ups = {
            "irdai_news": [
                "Would you like me to explain what a specific IRDAI regulation means for you?",
                "Want to know your consumer rights under IRDAI regulations?",
            ],
            "product_comparison": [
                "Should I explain what CSR and ICR mean and how to use them to evaluate insurers?",
                "Want me to calculate how much premium you'd need for the recommended cover?",
            ],
            "claims_data": [
                "Would you like guidance on how to ensure your claim is not rejected?",
                "Should I explain the claims process for your specific policy type?",
            ],
            "insurance_rules": [
                "Want me to explain your rights if an insurer violates any of these regulations?",
                "Should I explain how to use the free look period?",
            ],
        }
        return follow_ups.get(topic, [
            "Would you like me to search for more specific information?",
            "Should I explain any of this in more detail?",
        ])


# ── Module-level run function (called by agent_dispatch) ──────────────────
_agent = ResearcherAgent()


async def run(state: HibiscusState) -> Dict[str, Any]:
    """Entry point for agent_dispatch."""
    return await _agent(state)
