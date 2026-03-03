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
from hibiscus.observability.metrics import record_conversation as _metric_conversation
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
    # ── Most specific intents first — prevents generic keywords from short-circuiting ──
    # Domain-precise: unique keywords that rarely appear in other contexts
    "portfolio":  ["all my policies", "portfolio", "total coverage", "all policies", "multiple policies"],
    "tax":        ["80c", "80d", "tax benefit", "tax deduction", "tax saving", "deduction", "exemption", "10(10d)"],
    "surrender":  ["surrender", "should i continue", "should i keep", "policy loan", "paid-up"],
    "regulate":   ["irdai", "regulation", "circular", "free look", "legal right", "consumer right",
                   "ombudsman rule", "revive", "revival", "lapsed policy", "grace period",
                   "portability", "port my", "i want to port", "porting", "to port",
                   "do i port", "how do i port", "want to port", "switch insurer",
                   "moratorium", "continuous renewal", "continuous coverage", "5-year rule",
                   "5 year rule", "moratorium period"],
    "grievance":  ["ombudsman", "consumer court", "escalate", "grievance", "complaint", "unfairly rejected"],
    # ── Moderate specificity ──
    "claim":      ["claim", "settle", "hospital bill", "cashless", "reimbursement", "rejection"],
    "recommend":  ["recommend", "suggest", "best policy", "which policy", "compare",
                   "should i buy", "should i invest", "is it better", "better than", "worth buying",
                   "mis-selling", "mis selling", "agent is pushing", "guaranteed return",
                   "ulip vs", "vs mutual fund", "vs term",
                   "is there overlap", "policy overlap", "insurance overlap"],
    # NOTE: "returns" and "premium" deliberately removed — too broad, mis-routes comparison/mis-selling queries
    "calculate":  ["calculate", "how much cover", "how much life insurance", "maturity amount",
                   "emi calculation", "policy irr", "irr of", "how much will i get"],
    "analyze":    ["analyze", "analyse", "review my policy", "check my policy", "what does my policy",
                   "uploaded", "explain my policy",
                   # Policy-detail queries ("my X" about their specific policy)
                   "what is my sum insured", "what is my coverage", "what is my premium",
                   "what are my benefits", "what are the gaps", "gap in my", "gaps in my",
                   "room rent restriction", "room rent limit", "room rent cap",
                   "my room rent", "my icu limit", "my co-pay", "my copay",
                   "am i covered for", "will my policy cover", "does my policy cover",
                   "what does my", "tell me about my policy", "explain my coverage",
                   "my policy cover", "which members are covered", "who is covered",
                   "my waiting period", "my pre-existing", "my deductible"],
    # ── Most general — must come last ──
    "educate":    ["what is", "explain", "how does", "meaning of", "define", "difference between",
                   "how to", "what happens", "lapsed"],
    "research":   ["latest news", "market trend", "compare insurer", "best insurer"],
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


def _should_skip_llm(fast_result: dict, message: str, uploaded_files: list) -> bool:
    """
    Return True if keyword classification is confident enough to skip LLM.

    Skips LLM (saves ~10-15s) when:
    - Both intent AND category were matched by keywords (unambiguous)
    - Or short message where intent was clearly matched
    Never skips when files are uploaded (needs content-based classification).
    """
    # Always classify with LLM when files are uploaded
    if uploaded_files:
        return False

    intent_matched = fast_result["intent"] != "general_chat"
    category_matched = fast_result["category"] != "general"

    # Both keyword signals fired — very high confidence
    if intent_matched and category_matched:
        return True

    # Intent matched on a short unambiguous message
    if intent_matched and len(message.split()) < 20:
        return True

    # Distressed/urgent emotional state — always use LLM for better empathy routing
    if fast_result["emotional_state"] in ("distressed", "urgent"):
        return False

    return False


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
    # analyze without a document → use direct_llm for general guidance
    # Prevents policy_analyzer from asking for upload on "does my health insurance cover X?" queries
    if intent == "analyze" and not has_document:
        return []
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
    # Skip LLM when keyword classification is already highly confident.
    # This saves 10-15s for ~70% of L1/L2 queries.
    llm_result = {}
    if _should_skip_llm(fast_result, message, uploaded_files):
        plog.step_start("intent_llm_skipped", reason="high_confidence_keywords",
                        intent=fast_result["intent"], category=fast_result["category"])
    else:
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
                # Short limits: classification JSON is small and time-critical
                extra_kwargs={"max_tokens": 256, "timeout": 8},
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
    # Ground truth: if no files were uploaded, has_document MUST be False.
    # Prevents LLM from hallucinating has_document=True for "my health insurance" queries
    # which causes policy_analyzer to run and ask for document upload.
    if not uploaded_files:
        has_document = False
    document_type = llm_result.get("document_type", "unknown")
    requires_calculation = llm_result.get("requires_calculation", intent in ("calculate", "surrender"))
    # Always use our deterministic agent mapping — LLM agents_needed is unreliable
    # (LLM tends to default to policy_analyzer for everything)
    agents_needed = _determine_agents(intent, category, has_document)
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

    # Prometheus: record conversation start with complexity + category
    _metric_conversation(complexity=complexity, category=category)

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
