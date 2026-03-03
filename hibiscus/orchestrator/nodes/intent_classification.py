"""
Intent Classification Node
==========================
Classifies user message into:
- category (health/life/motor/travel/pa/cross/general)
- intent (analyze/recommend/claim/calculate/surrender/...)
- complexity (L1/L2/L3/L4)
- emotional_state (neutral/curious/concerned/distressed/urgent/frustrated)
- agents_needed

Uses keyword rules for fast classification, DeepSeek V3.2 as fallback.
"""
import json
import re
import time
from pathlib import Path

from hibiscus.observability.logger import PipelineLogger
from hibiscus.orchestrator.state import HibiscusState

# ── Prompt loading ──────────────────────────────────────────────────────────
_PROMPT_DIR = Path(__file__).parent.parent.parent / "llm" / "prompts"
_INTENT_PROMPT = (_PROMPT_DIR / "orchestrator" / "intent_classifier.txt").read_text()
_SYSTEM_PROMPT = (_PROMPT_DIR / "system" / "hibiscus_core.txt").read_text()


# ── Fast keyword rules (no LLM needed for obvious cases) ───────────────────
_CATEGORY_KEYWORDS = {
    "health": ["health", "medical", "hospitalization", "hospital", "oph", "opd", "critical illness",
                "star health", "niva bupa", "hdfc ergo health", "aditya birla health"],
    "life": ["life", "lic", "term", "ulip", "endowment", "money back", "surrender", "maturity",
              "jeevan", "click2protect", "iprotect", "sanchay"],
    "motor": ["car", "vehicle", "bike", "motor", "auto", "two-wheeler", "third party", "own damage"],
    "travel": ["travel", "trip", "flight", "abroad", "international", "visa"],
    "pa": ["personal accident", "accidental", "disability"],
}

_INTENT_KEYWORDS = {
    "analyze": ["analyze", "analyse", "review", "check", "read", "what does my", "uploaded", "explain my policy"],
    "claim": ["claim", "settle", "rejection", "hospital bill", "cashless", "reimbursement"],
    "surrender": ["surrender", "should i continue", "should i keep", "policy loan", "paid-up"],
    "calculate": ["calculate", "how much", "maturity", "premium", "emi", "irr", "returns"],
    "recommend": ["recommend", "suggest", "best policy", "which policy", "compare"],
    "educate": ["what is", "explain", "how does", "meaning of", "define"],
    "regulate": ["irdai", "regulation", "rule", "circular", "right", "legal", "free look"],
    "grievance": ["complaint", "ombudsman", "consumer court", "escalate", "grievance"],
    "tax": ["80c", "80d", "tax", "deduction", "exemption", "10(10d)"],
    "portfolio": ["all my policies", "portfolio", "total coverage", "all policies"],
}

_EMOTIONAL_KEYWORDS = {
    "distressed": ["emergency", "critical", "icu", "dying", "rejected my claim", "can't afford",
                   "losing my home", "desperate"],
    "urgent": ["urgent", "immediately", "asap", "deadline", "today", "expiring"],
    "frustrated": ["useless", "wrong", "cheated", "fraud", "not working", "terrible", "worst"],
    "concerned": ["worried", "confused", "not sure", "scared", "help me understand"],
}


def _fast_classify(message: str, uploaded_files: list) -> dict:
    """Fast keyword-based classification. Returns partial result."""
    msg_lower = message.lower()

    # Category detection
    category = "general"
    for cat, keywords in _CATEGORY_KEYWORDS.items():
        if any(kw in msg_lower for kw in keywords):
            category = cat
            break

    # Intent detection
    intent = "general_chat"
    for intnt, keywords in _INTENT_KEYWORDS.items():
        if any(kw in msg_lower for kw in keywords):
            intent = intnt
            break

    # If files uploaded, likely analysis intent
    if uploaded_files and intent == "general_chat":
        intent = "analyze"

    # Emotional state
    emotional_state = "neutral"
    for state, keywords in _EMOTIONAL_KEYWORDS.items():
        if any(kw in msg_lower for kw in keywords):
            emotional_state = state
            break
    if "?" in message and emotional_state == "neutral":
        emotional_state = "curious"

    # Has document
    has_document = bool(uploaded_files) or any(
        kw in msg_lower for kw in ["my policy", "this policy", "the document", "uploaded"]
    )

    return {
        "category": category,
        "intent": intent,
        "emotional_state": emotional_state,
        "has_document": has_document,
    }


def _determine_complexity(intent: str, has_document: bool, agents_needed: list) -> str:
    """Determine complexity level."""
    if intent in ("general_chat", "educate") and not has_document:
        return "L1"
    if intent in ("analyze",) and has_document:
        return "L2"
    if intent in ("claim", "regulate", "recommend", "portfolio", "tax"):
        return "L3"
    if intent in ("surrender", "calculate") or len(agents_needed) > 2:
        return "L4"
    return "L2"


def _determine_agents(intent: str, category: str, has_document: bool) -> list:
    """Determine which agents are needed."""
    agent_map = {
        "analyze": ["policy_analyzer"],
        "recommend": ["recommender", "risk_detector"],
        "claim": ["claims_guide"],
        "calculate": ["calculator"],
        "surrender": ["surrender_calculator", "risk_detector"],
        "educate": [],  # Direct LLM for education (L1/L2)
        "regulate": ["regulation_engine"],
        "research": ["researcher"],
        "grievance": ["grievance_navigator"],
        "portfolio": ["portfolio_optimizer"],
        "tax": ["tax_advisor"],
        "general_chat": [],
    }
    agents = agent_map.get(intent, [])
    if has_document and "policy_analyzer" not in agents and intent not in ("educate", "general_chat"):
        agents = ["policy_analyzer"] + agents
    return agents


async def run(state: HibiscusState) -> dict:
    """Classify the user's intent."""
    plog = PipelineLogger(
        component="intent_classification",
        request_id=state.get("request_id", "?"),
        session_id=state.get("session_id", "?"),
        user_id=state.get("user_id", "?"),
    )
    start = time.time()
    plog.step_start("intent_classification")

    message = state.get("message", "")
    uploaded_files = state.get("uploaded_files", [])

    # ── Step 1: Fast keyword classification ──────────────────────────────
    fast_result = _fast_classify(message, uploaded_files)

    # ── Step 2: Try LLM classification for better accuracy ───────────────
    llm_result = {}
    try:
        from hibiscus.llm.router import call_llm
        session_context = ""
        if state.get("session_history"):
            last_turns = state["session_history"][-3:]
            session_context = "\n".join([
                f"{t.get('role', 'user')}: {t.get('content', '')[:100]}"
                for t in last_turns
            ])

        prompt = f"""Classify this insurance query:

MESSAGE: "{message}"
UPLOADED FILES: {[f.get('filename', '') for f in uploaded_files]}
RECENT CONTEXT: {session_context or 'None'}

{_INTENT_PROMPT}"""

        llm_response = await call_llm(
            messages=[
                {"role": "system", "content": "You are the Hibiscus intent classifier. Return JSON only."},
                {"role": "user", "content": prompt},
            ],
            tier="deepseek_v3",
            conversation_id=state.get("conversation_id", "?"),
            agent="intent_classifier",
        )

        content = llm_response["content"].strip()
        # Extract JSON from response
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            llm_result = json.loads(json_match.group())

    except Exception as e:
        plog.warning("intent_llm_fallback", error=str(e), using="keyword_rules")

    # ── Step 3: Merge results (LLM overrides keyword if available) ────────
    category = llm_result.get("category", fast_result["category"])
    intent = llm_result.get("intent", fast_result["intent"])
    emotional_state = llm_result.get("emotional_state", fast_result["emotional_state"])
    has_document = llm_result.get("has_document", fast_result["has_document"])
    document_type = llm_result.get("document_type", "unknown")
    requires_calculation = llm_result.get("requires_calculation", intent in ("calculate", "surrender"))
    agents_needed = llm_result.get("agents_needed", _determine_agents(intent, category, has_document))
    complexity = llm_result.get("complexity", _determine_complexity(intent, has_document, agents_needed))

    # ── Step 4: Model selection ──────────────────────────────────────────
    from hibiscus.llm.model_selector import select_tier
    tier = select_tier(
        task=f"l{complexity[1]}_response" if complexity.startswith("L") else "l1_response",
        emotional_state=emotional_state,
        complexity=complexity,
    )

    latency_ms = int((time.time() - start) * 1000)
    plog.step_complete(
        "intent_classification",
        latency_ms=latency_ms,
        category=category,
        intent=intent,
        complexity=complexity,
        emotional_state=emotional_state,
        agents_needed=agents_needed,
    )

    return {
        "category": category,
        "intent": intent,
        "complexity": complexity,
        "emotional_state": emotional_state,
        "has_document": has_document,
        "document_type": document_type,
        "agents_needed": agents_needed,
        "requires_calculation": requires_calculation,
        "primary_model": tier.value,
    }
