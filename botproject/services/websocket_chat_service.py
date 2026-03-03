"""
WebSocket Chat Service for EAZR Chat
Handles chat processing with streaming support for WebSocket connections.
"""

from typing import Dict, Any, Optional, AsyncGenerator, List
from fastapi import WebSocket
from datetime import datetime, timezone
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
import asyncio
import logging
import hashlib
import json
import os

logger = logging.getLogger(__name__)


class WebSocketChatService:
    """
    Chat processing service for WebSocket connections.

    Reuses existing components from HTTP /ask endpoint:
    - Intent detection from ai_chat_components/processor.py
    - Enhanced chatbot handlers for service routing
    - RAG chain for document queries
    - MongoDB for message persistence

    Adds:
    - Streaming response support (token by token)
    - Integration with WebSocket connection manager
    """

    # Rotating thinking words — one sent per second while processing
    THINKING_WORDS = [
        "Thinking",
        "Analyzing",
        "Processing",
        "Searching",
        "Computing",
        "Reviewing",
        "Checking",
        "Evaluating",
        "Preparing",
        "Gathering",
        "Scanning",
        "Compiling",
        "Assessing",
        "Fetching",
        "Resolving",
    ]

    def __init__(self):
        """Initialize with lazy loading of dependencies"""
        self._thinking_tasks: Dict[str, asyncio.Task] = {}  # Per chat_session_id thinking tasks
        self._initialized = False
        self._mongodb_chat_manager = None
        self._detect_intent = None
        self._rag_handler = None
        self._create_standardized_response = None
        self._generate_human_like_response = None
        self._route_enhanced_chatbot = None
        self._llm = None
        # Additional handlers matching /ask API
        self._generate_claim_guidance = None
        self._generate_off_topic_redirect = None
        self._is_off_topic_query = None
        self._get_conversation_context_summary = None
        self._get_live_event_data = None
        self._answer_protection_score_question = None
        self._get_user_latest_policy_analysis = None
        self._process_user_input_with_language_detection = None
        self._set_user_language_preference = None
        # Insurance marketplace action handlers (matching /ask API action routing)
        self._show_policy_details_from_stored_data = None
        self._accept_policy_and_start_application = None
        # Active session continuation handlers (matching /ask API lines 7007-7080)
        self._chatbot_sessions = None
        self._continue_policy_application = None
        self._continue_insurance_application = None
        self._continue_financial_assistance_application = None
        self._continue_wallet_setup = None
        self._extract_actual_user_input = None
        # Application review/submit/cancel handlers (matching /ask API lines 5761-6604)
        self._get_policy_application = None
        self._complete_application = None
        # Reference response handler (matching /ask reference_to_previous intent)
        self._generate_reference_response = None
        # Coverage advisory handler (matching /ask model="coverage_advisory")
        self._generate_coverage_advisory_response = None
        # Contextual prompt builders (matching /ask contextual query building)
        self._build_contextual_prompt = None
        self._get_contextual_prompt_from_mongodb = None
        # Financial education response fallback
        self._generate_financial_education_response = None
        # Context determination (matches /ask's should_use_context check)
        self._should_use_context = None
        # Track last intent per session for few-shot follow-up detection
        self._session_last_intent: Dict[str, str] = {}
        # Track sessions that have already had their title updated (avoid redundant DB calls)
        self._title_updated_sessions: set = set()
        # Max tracked sessions before cleanup (prevents memory leak)
        self._max_tracked_sessions: int = 5000

    def _safe_create_task(self, coro, name: str = "background_task") -> asyncio.Task:
        """Create an asyncio task with an exception handler to prevent silent failures."""
        task = asyncio.create_task(coro, name=name)

        def _handle_exception(t: asyncio.Task):
            if t.cancelled():
                return
            exc = t.exception()
            if exc:
                logger.error(f"Background task '{name}' failed: {exc}", exc_info=exc)

        task.add_done_callback(_handle_exception)
        return task

    def _ensure_initialized(self) -> bool:
        """Lazy initialize dependencies"""
        if self._initialized:
            return True

        try:
            from database_storage.mongodb_chat_manager import mongodb_chat_manager
            self._mongodb_chat_manager = mongodb_chat_manager
        except ImportError as e:
            logger.warning(f"MongoDB chat manager not available: {e}")

        # Policy query handler
        self._handle_policy_query = None
        try:
            from routers.chat import handle_policy_query
            self._handle_policy_query = handle_policy_query
        except ImportError as e:
            logger.warning(f"Policy query handler not available: {e}")

        # Language detection
        self._detect_language = None
        try:
            from support_features.multilingual_support import detect_hindi_or_english
            self._detect_language = detect_hindi_or_english
        except ImportError as e:
            logger.warning(f"Language detection not available: {e}")

        try:
            from ai_chat_components.processor import (
                detect_intent_with_context,
                generate_human_like_response,
                should_use_context
            )
            self._detect_intent = detect_intent_with_context
            self._generate_human_like_response = generate_human_like_response
            self._should_use_context = should_use_context
        except ImportError as e:
            logger.warning(f"AI processor not available: {e}")

        try:
            from routers.chat import (
                rag_handler,
                create_standardized_response,
                add_to_conversation_memory,
                get_conversation_history
            )
            self._rag_handler = rag_handler
            self._create_standardized_response = create_standardized_response
            self._add_to_conversation_memory = add_to_conversation_memory
            self._get_conversation_history = get_conversation_history
        except ImportError as e:
            logger.warning(f"Chat router functions not available: {e}")

        try:
            from ai_chat_components.enhanced_chatbot_handlers import route_enhanced_chatbot
            self._route_enhanced_chatbot = route_enhanced_chatbot
        except ImportError as e:
            logger.warning(f"Enhanced chatbot handlers not available: {e}")

        # Active session continuation handlers (matches /ask API lines 7007-7080)
        try:
            from ai_chat_components.enhanced_chatbot_handlers import (
                chatbot_sessions,
                continue_policy_application,
                continue_insurance_application,
                continue_financial_assistance_application,
                continue_wallet_setup,
                extract_actual_user_input
            )
            self._chatbot_sessions = chatbot_sessions
            self._continue_policy_application = continue_policy_application
            self._continue_insurance_application = continue_insurance_application
            self._continue_financial_assistance_application = continue_financial_assistance_application
            self._continue_wallet_setup = continue_wallet_setup
            self._extract_actual_user_input = extract_actual_user_input
        except ImportError as e:
            logger.warning(f"Session continuation handlers not available: {e}")

        try:
            from core.config import get_llm_instance
            self._llm = get_llm_instance()
        except ImportError as e:
            logger.warning(f"LLM not available: {e}")

        # Claim guidance
        try:
            from ai_chat_components.processor import generate_claim_guidance_response
            self._generate_claim_guidance = generate_claim_guidance_response
        except ImportError as e:
            logger.warning(f"Claim guidance not available: {e}")

        # Off-topic redirect
        try:
            from ai_chat_components.processor import generate_off_topic_redirect_response, is_off_topic_query
            self._generate_off_topic_redirect = generate_off_topic_redirect_response
            self._is_off_topic_query = is_off_topic_query
        except ImportError as e:
            logger.warning(f"Off-topic redirect not available: {e}")

        # Contextual suggestions
        try:
            from ai_chat_components.processor import get_conversation_context_summary
            self._get_conversation_context_summary = get_conversation_context_summary
        except ImportError as e:
            logger.warning(f"Conversation context summary not available: {e}")

        # Live event data
        try:
            from support_features.live_info import get_live_event_data
            self._get_live_event_data = get_live_event_data
        except ImportError as e:
            logger.warning(f"Live event data not available: {e}")

        # Protection score
        try:
            from financial_services.protection_score_ans import answer_protection_score_question
            self._answer_protection_score_question = answer_protection_score_question
        except ImportError as e:
            logger.warning(f"Protection score answer not available: {e}")

        # Policy analysis data
        try:
            from database_storage.mongodb_chat_manager import get_user_latest_policy_analysis
            self._get_user_latest_policy_analysis = get_user_latest_policy_analysis
        except ImportError as e:
            logger.warning(f"Policy analysis data not available: {e}")

        # Application review/submit/cancel (matches /ask API lines 5761-6604)
        try:
            from database_storage.mongodb_chat_manager import get_policy_application, complete_application
            self._get_policy_application = get_policy_application
            self._complete_application = complete_application
        except ImportError as e:
            logger.warning(f"Policy application handlers not available: {e}")

        # Multilingual support
        try:
            from support_features.multilingual_support import (
                process_user_input_with_language_detection,
                set_user_language_preference
            )
            self._process_user_input_with_language_detection = process_user_input_with_language_detection
            self._set_user_language_preference = set_user_language_preference
        except ImportError as e:
            logger.warning(f"Multilingual processing not available: {e}")

        # Reference response (matches /ask reference_to_previous intent)
        try:
            from ai_chat_components.processor import generate_reference_response
            self._generate_reference_response = generate_reference_response
        except ImportError as e:
            logger.warning(f"Reference response not available: {e}")

        # Coverage advisory (matches /ask model="coverage_advisory")
        try:
            from routers.chat import generate_coverage_advisory_response
            self._generate_coverage_advisory_response = generate_coverage_advisory_response
        except ImportError as e:
            logger.warning(f"Coverage advisory not available: {e}")

        # Contextual prompt builders (matches /ask contextual query building)
        try:
            from routers.chat import build_contextual_prompt
            self._build_contextual_prompt = build_contextual_prompt
        except ImportError as e:
            logger.warning(f"Contextual prompt builder not available: {e}")

        try:
            from database_storage.mongodb_chat_manager import get_contextual_prompt_from_mongodb
            self._get_contextual_prompt_from_mongodb = get_contextual_prompt_from_mongodb
        except ImportError as e:
            logger.warning(f"MongoDB contextual prompt not available: {e}")

        # Financial education response fallback
        try:
            from ai_chat_components.processor import generate_financial_education_response
            self._generate_financial_education_response = generate_financial_education_response
        except ImportError as e:
            logger.warning(f"Financial education response not available: {e}")

        self._initialized = True
        return True

    def _detect_query_language(self, query: str) -> str:
        """
        Detect language of query using proper language detection.
        Falls back to simple heuristics if LLM-based detection not available.

        Returns: 'en' or 'hi'
        """
        if not query or not query.strip():
            return 'en'

        # Try LLM-based detection first (more accurate)
        if self._detect_language:
            try:
                lang, confidence = self._detect_language(query)
                if confidence > 0.7:
                    return lang
            except Exception as e:
                logger.warning(f"LLM language detection failed: {e}")

        # Fallback: Check for Devanagari script (definite Hindi)
        if any('\u0900' <= char <= '\u097F' for char in query):
            return 'hi'

        # Fallback: Simple Hindi romanized keyword detection
        # Only use keywords that are definitely Hindi and NOT English words
        query_lower = query.lower()
        hindi_only_keywords = [
            'meri', 'kitni', 'kitne', 'kya', 'hain', 'bima', 'parivar',
            'apni', 'apna', 'dikha', 'batao', 'chahiye', 'karo', 'karna',
            'dekho', 'dekhna', 'mujhe', 'aapki', 'humari'
        ]

        # Note: Excluded 'hai' because it appears in some English contexts
        # and 'policy' because it's English
        if any(kw in query_lower for kw in hindi_only_keywords):
            return 'hi'

        return 'en'

    def _cleanup_session_tracking(self) -> None:
        """Remove oldest entries when tracked sessions exceed max to prevent memory leak."""
        if len(self._session_last_intent) > self._max_tracked_sessions:
            # Keep only the most recent half
            excess = len(self._session_last_intent) - (self._max_tracked_sessions // 2)
            keys_to_remove = list(self._session_last_intent.keys())[:excess]
            for key in keys_to_remove:
                del self._session_last_intent[key]
            logger.info(f"Cleaned up {excess} entries from _session_last_intent")

        if len(self._title_updated_sessions) > self._max_tracked_sessions:
            excess = len(self._title_updated_sessions) - (self._max_tracked_sessions // 2)
            # Convert to list, remove oldest (insertion order preserved in Python 3.7+)
            sessions_list = list(self._title_updated_sessions)
            for session_id in sessions_list[:excess]:
                self._title_updated_sessions.discard(session_id)
            logger.info(f"Cleaned up {excess} entries from _title_updated_sessions")

    def _build_contextual_query(self, chat_session_id: str, query: str,
                                conversation_history: List[Dict] = None) -> str:
        """
        Build a contextual query by combining with conversation history.
        Matches /ask API's contextual_query building (lines 6896-6905).
        Only builds context when should_use_context() says it's needed.
        """
        try:
            # Check if context is actually needed (matches /ask line 6896)
            if self._should_use_context and conversation_history is not None:
                if not self._should_use_context(query, conversation_history):
                    return query  # New topic — don't mix in old context

            if self._get_contextual_prompt_from_mongodb and self._mongodb_chat_manager:
                return self._get_contextual_prompt_from_mongodb(chat_session_id, query)
            elif self._build_contextual_prompt:
                return self._build_contextual_prompt(chat_session_id, query)
        except Exception as e:
            logger.warning(f"Contextual query building failed: {e}")
        return query

    async def _detect_multi_intents(
        self,
        query: str,
        primary_intent: str,
        conversation_history: List[Dict]
    ) -> List[tuple]:
        """
        Detect if a message contains multiple distinct intents.
        e.g., "show my policies and what is insurance" → policy_query + financial_education

        Only splits when genuinely different intents are found.
        Skips filler intents (greeting/small_talk) when actionable intents exist.

        Returns:
            List of (sub_query, intent) tuples. Single element if no multi-intent.
        """
        import re

        # Split by common multi-topic conjunctions
        parts = re.split(r'\s+and\s+|\s+aur\s+|\s*,\s+(?=[a-zA-Z])', query, flags=re.IGNORECASE)

        # Need meaningful parts (at least 2 words AND 8+ chars each)
        meaningful_parts = [
            p.strip() for p in parts
            if len(p.strip()) >= 8 and len(p.strip().split()) >= 2
        ]

        if len(meaningful_parts) < 2:
            return [(query, primary_intent)]

        if not self._detect_intent:
            return [(query, primary_intent)]

        # Detect intent for each part (run in thread to avoid blocking event loop)
        results = []
        seen_intents = set()
        for part in meaningful_parts:
            part_intent = await asyncio.to_thread(self._detect_intent, part, conversation_history)
            results.append((part, part_intent))
            seen_intents.add(part_intent)

        # Only multi-intent if at least 2 different intents detected
        if len(seen_intents) <= 1:
            return [(query, primary_intent)]

        # Skip filler intents (greeting/small_talk/unknown) when actionable intents exist
        filler_intents = {"greeting", "small_talk", "unknown"}
        has_actionable = any(i not in filler_intents for _, i in results)

        if has_actionable:
            filtered = [(q, i) for q, i in results if i not in filler_intents]
        else:
            return [(query, primary_intent)]

        if len(filtered) < 2:
            # Only one actionable intent after filtering — process full query with primary
            return [(query, primary_intent)]

        logger.info(
            f"WebSocket: Multi-intent detected — "
            f"{[(i, q[:30]) for q, i in filtered]}"
        )
        return filtered

    async def process_chat_message(
        self,
        websocket: WebSocket,
        connection_id: str,
        user_id: int,
        chat_session_id: str,
        user_session_id: str,
        access_token: str,
        query: str,
        action: Optional[str] = None,
        assistance_type: Optional[str] = None,
        insurance_type: Optional[str] = None,
        service_type: Optional[str] = None,
        policy_id: Optional[str] = None,
        model: str = "policy_analysis",
        stream: bool = True
    ) -> None:
        """
        Process a chat message and send responses via WebSocket.

        Args:
            websocket: WebSocket connection for sending responses
            connection_id: Connection identifier
            user_id: User identifier
            chat_session_id: Chat session identifier
            user_session_id: User session identifier
            access_token: JWT access token for API calls
            query: User's message
            action: Optional action type
            assistance_type: Optional assistance type
            insurance_type: Optional insurance type
            service_type: Optional service type
            policy_id: Optional policy ID
            model: Model type (policy_analysis, coverage_advisory, claim_support)
            stream: Whether to stream response tokens
        """
        self._ensure_initialized()
        self._cleanup_session_tracking()

        current_timestamp = datetime.now(timezone.utc).isoformat()
        message_id = self._generate_message_id(chat_session_id, query, current_timestamp)

        try:
            # Update chat session title on first message (background — don't block response)
            if chat_session_id not in self._title_updated_sessions:
                self._title_updated_sessions.add(chat_session_id)
                if self._mongodb_chat_manager and hasattr(self._mongodb_chat_manager, 'update_chat_title'):
                    _title = query[:50] + ("..." if len(query) > 50 else "")
                    self._safe_create_task(
                        asyncio.to_thread(
                            self._mongodb_chat_manager.update_chat_title, chat_session_id, _title
                        ),
                        name=f"update_chat_title_{chat_session_id}"
                    )

            # Start thinking indicator (first word sent immediately, rest rotate every 1s)
            await self._start_thinking(websocket, chat_session_id)

            # Add to memory + get history in parallel (both are sync I/O → run in threads)
            async def _add_mem():
                if self._add_to_conversation_memory:
                    await asyncio.to_thread(self._add_to_conversation_memory, chat_session_id, "user", query)

            async def _get_hist():
                if self._get_conversation_history:
                    return await asyncio.to_thread(self._get_conversation_history, chat_session_id, 4)
                return []

            _, conversation_history = await asyncio.gather(_add_mem(), _get_hist())
            conversation_history = conversation_history or []

            # Detect intent with enhanced pre-checks (mirrors processor.py detect_intent_with_context)
            intent = "unknown"
            query_lower = query.lower().strip()
            query_words = set(query_lower.split())

            # ============= PRE-CHECK 0: Few-shot follow-up detection =============
            # Short/ambiguous messages that need the PREVIOUS intent to make sense
            # e.g., "yes", "tell me more", "haan", "ok", "the first one", "health"
            last_intent = self._session_last_intent.get(chat_session_id)
            if last_intent and last_intent not in ("unknown", "greeting", "off_topic"):
                # Single-word follow-ups matched by exact word presence
                single_word_followups = {
                    'yes', 'yeah', 'yep', 'yup', 'ok', 'okay', 'sure', 'alright',
                    'no', 'nope', 'nah', 'more', 'continue', 'also',
                    # Hindi/Hinglish
                    'haan', 'ha', 'ji', 'accha', 'aur', 'nahi',
                    'pehla', 'doosra', 'teesra',
                }
                # Multi-word follow-ups matched as phrases
                multi_word_followups = [
                    'tell me more', 'go on', 'keep going',
                    'what else', 'anything else', 'what about',
                    'as well', 'anything as well', 'should i also',
                    'the first', 'the second', 'the third',
                    'first one', 'second one', 'third one',
                    'option 1', 'option 2', 'option 3',
                    'aur batao', 'theek hai', 'thik hai', 'aur kuch',
                    'kuch aur bhi',
                ]
                is_short_followup = (
                    len(query_lower.split()) <= 8 and (
                        # Exact full match OR single word present in query words
                        query_lower in single_word_followups or
                        (bool(query_words & single_word_followups) and len(query_words) <= 2) or
                        any(phrase in query_lower for phrase in multi_word_followups)
                    )
                )

                # Also continue intent if the bot's last message was a question
                # e.g., Bot: "It depends — what are you looking for?" → User provides requirements
                if not is_short_followup and conversation_history:
                    last_bot_msg = ""
                    for msg in reversed(conversation_history):
                        if msg.get('role') == 'assistant':
                            last_bot_msg = msg.get('content', '').strip()
                            break
                    if last_bot_msg and last_bot_msg.endswith('?'):
                        is_short_followup = True
                        logger.info(
                            f"WebSocket: Bot-question follow-up detected — "
                            f"continuing '{last_intent}' intent for: '{query[:50]}'"
                        )

                # Contextual pronoun follow-up: "it", "this", "that" reference the previous topic
                # e.g., "Should I upgrade it or buy a new plan?" — "it" = the policy from last message
                if not is_short_followup and len(query_lower.split()) <= 15:
                    context_pronouns = {'it', 'this', 'that', 'these', 'those'}
                    if query_words & context_pronouns:
                        is_short_followup = True
                        logger.info(
                            f"WebSocket: Pronoun follow-up detected — "
                            f"continuing '{last_intent}' intent for: '{query[:50]}'"
                        )

                if is_short_followup:
                    intent = last_intent
                    logger.info(
                        f"WebSocket: Few-shot follow-up detected — "
                        f"continuing '{last_intent}' intent for: '{query[:50]}'"
                    )

            # ============= PRE-CHECKs 1-4 + DEFAULT: Only if few-shot didn't match =============
            if intent == "unknown":
                # ============= PRE-CHECK 1: Reference to previous question =============
                reference_patterns = ['last question', 'what i asked', 'previous question', 'earlier', 'pichla sawal']
                if any(phrase in query_lower for phrase in reference_patterns):
                    intent = "reference_to_previous"
                    logger.info(f"WebSocket: Forced reference_to_previous intent: '{query[:50]}'")

            # ============= PRE-CHECK 2: Family member policy queries =============
            if intent == "unknown" and any(pattern in query_lower for pattern in [
                # "show [member] policies" patterns
                'show sister', 'show brother', 'show father', 'show mother',
                'show spouse', 'show wife', 'show husband', 'show son', 'show daughter',
                'show friend', 'show relative',
                # "[member] policies" patterns
                'sister policies', 'brother policies', 'father policies', 'mother policies',
                'spouse policies', 'wife policies', 'husband policies', 'son policies', 'daughter policies',
                'friend policies', 'relative policies',
                'sister policy', 'brother policy', 'father policy', 'mother policy',
                'spouse policy', 'wife policy', 'husband policy', 'son policy', 'daughter policy',
                'friend policy', 'relative policy',
                # "policies for [member]" patterns
                'policies for sister', 'policies for brother', 'policies for father', 'policies for mother',
                'policies for spouse', 'policies for wife', 'policies for husband', 'policies for son', 'policies for daughter',
                'policies for friend', 'policies for relative',
                'policy for sister', 'policy for brother', 'policy for father', 'policy for mother',
                'policy for spouse', 'policy for wife', 'policy for husband', 'policy for son', 'policy for daughter',
                'policy for friend', 'policy for relative',
                # Hindi/Hinglish family member patterns
                'behen ki', 'bhai ki', 'papa ki', 'mummy ki', 'pati ki', 'patni ki', 'beta ki', 'beti ki',
                'didi ki', 'maa ki', 'pitaji ki', 'sasur ki', 'saas ki', 'dost ki',
            ]):
                intent = "policy_query"
                logger.info(f"WebSocket: Forced policy_query intent for family member query: '{query[:50]}'")

            # ============= PRE-CHECK 4: Upload/analyze policy (insurance_analysis) =============
            # NOTE: "review my locker policy" should go to policy_query, not insurance_analysis
            if intent == "unknown" and any(pattern in query_lower for pattern in [
                'want to upload', 'upload new', 'upload my', 'need to upload',
                'want to analyze', 'want to analyse', 'for analyzing', 'for analysis'
            ]):
                # Exclude locker-related queries — user wants to review EXISTING policies, not upload
                if 'locker' not in query_lower:
                    intent = "insurance_analysis"
                    logger.info(f"WebSocket: Forced insurance_analysis intent: '{query[:50]}'")

            # ============= PRE-CHECK 4B: "analyze/review my policy" without locker =============
            if intent == "unknown" and any(pattern in query_lower for pattern in [
                'analyze my policy', 'analyse my policy', 'check my policy', 'review my policy'
            ]):
                if 'locker' not in query_lower:
                    intent = "insurance_analysis"
                    logger.info(f"WebSocket: Forced insurance_analysis intent: '{query[:50]}'")

            # ============= PRE-CHECK 5: Review/check locker policies → policy_query =============
            if intent == "unknown" and 'locker' in query_lower and any(pattern in query_lower for pattern in [
                'review', 'check', 'show', 'view', 'see', 'tell', 'locker policy', 'locker policies',
            ]):
                intent = "policy_query"
                logger.info(f"WebSocket: Forced policy_query for locker review: '{query[:50]}'")

            # ============= PRE-CHECK 6: Off-topic detection =============
            if intent == "unknown":
                try:
                    if self._is_off_topic_query and self._is_off_topic_query(query):
                        intent = "off_topic"
                        logger.info(f"WebSocket: Off-topic detected: '{query[:50]}'")
                except Exception:
                    pass

            # ============= DEFAULT: Use processor's intent detection =============
            if intent == "unknown" and self._detect_intent:
                intent = await asyncio.to_thread(self._detect_intent, query, conversation_history)
                logger.info(f"WebSocket chat intent: {intent}")

            # Track intent for few-shot follow-up detection in next message
            if intent and intent not in ("unknown",):
                self._session_last_intent[chat_session_id] = intent

            # ============= ACTIVE SESSION CHECK (matches /ask API lines 7007-7080) =============
            # BEFORE routing by action/intent, check if user has an active Q&A session
            # (e.g., policy application form, insurance application, wallet setup)
            # If active session exists and no explicit action, route answer to continuation handler
            # NOTE: User message is NOT stored yet — continuation handler stores it to avoid duplicates
            if not action and self._chatbot_sessions is not None:
                session_result = await self._check_and_continue_active_session(
                    websocket=websocket,
                    chat_session_id=chat_session_id,
                    user_id=user_id,
                    user_session_id=user_session_id,
                    access_token=access_token,
                    query=query
                )
                if session_result:
                    # Active session handled the message, we're done
                    return

            # Store user message in background (fire-and-forget) — don't block response
            # (continuation handlers store messages themselves)
            self._safe_create_task(
                asyncio.to_thread(
                    self._store_user_message_sync,
                    chat_session_id, user_id, query, intent,
                    {"action": action, "policy_id": policy_id,
                     "assistance_type": assistance_type, "insurance_type": insurance_type,
                     "service_type": service_type, "model": model, "stream": stream}
                ),
                name=f"store_user_msg_{chat_session_id}"
            )

            # Handle based on action or intent
            if action:
                # Action-based handling (buttons, selections)
                await self._handle_action(
                    websocket=websocket,
                    chat_session_id=chat_session_id,
                    user_id=user_id,
                    user_session_id=user_session_id,
                    access_token=access_token,
                    action=action,
                    user_input=query,
                    assistance_type=assistance_type,
                    insurance_type=insurance_type,
                    service_type=service_type,
                    policy_id=policy_id
                )
            else:
                # ============= MULTI-INTENT DETECTION =============
                # If user sent "show my policies and what is insurance",
                # split and handle each part separately
                multi_intents = await self._detect_multi_intents(query, intent, conversation_history)

                if len(multi_intents) > 1:
                    # Process each sub-query with its own intent
                    for sub_query, sub_intent in multi_intents:
                        # Track each intent
                        if sub_intent and sub_intent not in ("unknown",):
                            self._session_last_intent[chat_session_id] = sub_intent

                        await self._handle_query(
                            websocket=websocket,
                            chat_session_id=chat_session_id,
                            user_id=user_id,
                            user_session_id=user_session_id,
                            access_token=access_token,
                            query=sub_query,
                            intent=sub_intent,
                            conversation_history=conversation_history,
                            model=model,
                            stream=False  # Don't stream individual parts
                        )
                else:
                    # Single intent — normal processing
                    await self._handle_query(
                        websocket=websocket,
                        chat_session_id=chat_session_id,
                        user_id=user_id,
                        user_session_id=user_session_id,
                        access_token=access_token,
                        query=query,
                        intent=intent,
                        conversation_history=conversation_history,
                        model=model,
                        stream=stream
                    )

        except Exception as e:
            logger.error(f"Error processing WebSocket chat: {e}", exc_info=True)
            await self._send_error_response(
                websocket=websocket,
                chat_session_id=chat_session_id,
                error=str(e)
            )

    async def _check_and_continue_active_session(
        self,
        websocket: WebSocket,
        chat_session_id: str,
        user_id: int,
        user_session_id: str,
        access_token: str,
        query: str
    ) -> bool:
        """
        Check for active chatbot sessions and route user's answer to continuation handler.
        Mirrors /ask API lines 7007-7080.

        Returns:
            True if an active session was found and handled, False otherwise.
        """
        if self._chatbot_sessions is None:
            return False

        # Find active sessions for this chat_session_id
        active_sessions = []
        for session_key in self._chatbot_sessions:
            if chat_session_id in session_key and not self._chatbot_sessions[session_key].completed:
                active_sessions.append({
                    "key": session_key,
                    "session": self._chatbot_sessions[session_key]
                })

        if not active_sessions:
            return False

        # Get the latest active session
        latest_session = active_sessions[-1]
        session_key = latest_session["key"]

        logger.info(f"WebSocket: Found active session: {session_key}")

        # Parse session key to determine chatbot type and service type
        # Session key formats:
        #   {chat_session_id}_policy_application_{policy_id}
        #   {chat_session_id}_insurance_{insurance_type}
        #   {chat_session_id}_financial_{assistance_type}
        #   {chat_session_id}_wallet_setup
        parts = session_key.split('_')
        chatbot_type = None
        service_type_parsed = None

        if "policy_application" in session_key:
            chatbot_type = "policy_application"
            # Extract policy_id (last part after "policy_application_")
            pa_index = session_key.index("policy_application_")
            service_type_parsed = session_key[pa_index + len("policy_application_"):]
        else:
            known_types = ["financial", "insurance", "wallet"]
            for i, part in enumerate(parts):
                if part in known_types:
                    chatbot_type = part
                    if i + 1 < len(parts):
                        service_type_parsed = parts[i + 1]
                    break

        if chatbot_type == "wallet":
            service_type_parsed = "setup"

        if not chatbot_type or not service_type_parsed:
            logger.warning(f"WebSocket: Could not parse session key: {session_key}")
            return False

        # Extract actual user input (answer)
        actual_user_input = query
        if self._extract_actual_user_input:
            actual_user_input = self._extract_actual_user_input(query)

        logger.info(f"WebSocket: Continuing {chatbot_type} session, service={service_type_parsed}, answer='{actual_user_input[:50]}'")

        try:
            result = None

            if chatbot_type == "policy_application" and self._continue_policy_application:
                result = self._continue_policy_application(
                    chat_session_id, service_type_parsed, actual_user_input,
                    access_token, user_id
                )
            elif chatbot_type == "insurance" and self._continue_insurance_application:
                result = self._continue_insurance_application(
                    chat_session_id, service_type_parsed, actual_user_input,
                    access_token, user_id
                )
            elif chatbot_type == "financial" and self._continue_financial_assistance_application:
                result = self._continue_financial_assistance_application(
                    chat_session_id, service_type_parsed, actual_user_input,
                    access_token, user_id
                )
            elif chatbot_type == "wallet" and self._continue_wallet_setup:
                result = self._continue_wallet_setup(
                    chat_session_id, actual_user_input, access_token, user_id
                )

            if not result:
                logger.warning(f"WebSocket: Continuation handler returned None for {chatbot_type}")
                return False

            # Determine response type
            response_type = "question"
            result_type = result.get("type", "")
            if result_type == "application_completed":
                response_type = "application_completed"
            elif result_type == "application_cancelled":
                response_type = "application_cancelled"
            elif result_type == "review_application":
                response_type = "review_application"

            # Add session metadata
            result["show_service_options"] = False
            result["session_continuation"] = True
            result["chat_session_id"] = chat_session_id
            result["user_session_id"] = user_session_id

            # Send response (auto-stores full response_data in MongoDB)
            await self._send_chat_response(
                websocket=websocket,
                chat_session_id=chat_session_id,
                response_type=response_type,
                data=result,
                intent="chatbot_continuation",
                user_id=user_id,
                language=result.get("language", "en")
            )
            return True

        except Exception as e:
            logger.error(f"WebSocket: Session continuation error: {e}", exc_info=True)
            return False

    async def _handle_action(
        self,
        websocket: WebSocket,
        chat_session_id: str,
        user_id: int,
        user_session_id: str,
        access_token: str,
        action: str,
        user_input: Optional[str],
        assistance_type: Optional[str],
        insurance_type: Optional[str],
        service_type: Optional[str],
        policy_id: Optional[str]
    ) -> None:
        """
        Handle action-based requests — mirrors /ask API action routing (lines 5754-6784).

        Routing order (same as /ask):
        1. show_policy_details + policy_id → Insurance marketplace product details
        2. accept_policy_and_start_application + policy_id → Start application form
        3. policy_query actions → Uploaded policy analysis queries
        4. Everything else → route_enhanced_chatbot
        """

        logger.info(f"WebSocket ACTION: {action} | POLICY_ID: {policy_id} | USER_ID: {user_id} | INSURANCE_TYPE: {insurance_type}")

        # ============= 3. REVIEW APPLICATION =============
        # Matches /ask API lines 5761-5844: review_application
        # Retrieves saved application answers from MongoDB in editable format
        if action == "review_application" and policy_id:
            await self._handle_review_application(
                websocket=websocket,
                chat_session_id=chat_session_id,
                user_id=user_id,
                user_session_id=user_session_id,
                policy_id=policy_id
            )
            return

        # ============= 4. CONFIRM SUBMIT APPLICATION =============
        # Matches /ask API lines 5847-6196: confirm_submit_application
        # Processes edited answers, calls external API, handles payment
        if action == "confirm_submit_application" and policy_id:
            await self._handle_confirm_submit_application(
                websocket=websocket,
                chat_session_id=chat_session_id,
                user_id=user_id,
                user_session_id=user_session_id,
                access_token=access_token,
                policy_id=policy_id,
                user_input=user_input
            )
            return

        # ============= 5. CANCEL APPLICATION =============
        # Matches /ask API lines 6536-6604: cancel_application
        # Exits session, marks application as cancelled in MongoDB
        if action == "cancel_application" and policy_id:
            await self._handle_cancel_application(
                websocket=websocket,
                chat_session_id=chat_session_id,
                user_id=user_id,
                user_session_id=user_session_id,
                policy_id=policy_id
            )
            return

        # ============= 6. ADD POLICY (redirect action) =============
        # When user taps "Add Policy" quick action button — send redirect response
        if action == "add_policy":
            detected_language = self._detect_query_language(user_input or "")
            add_policy_msg = (
                "Sure! Tap the button below to add your policy document. "
                "I'll analyze it and give you a complete breakdown."
            ) if detected_language == 'en' else (
                "ज़रूर! नीचे बटन दबाकर अपना पॉलिसी दस्तावेज़ जोड़ें। "
                "मैं उसे एनालाइज करके पूरी जानकारी दूंगा।"
            )

            result_data = {
                "response": add_policy_msg,
                "action": "add_insurance_policy",
                "show_service_options": False,
                "language": detected_language,
                "redirect": True,
                "redirect_page": "add_policy",
                "quick_actions": [
                    {
                        "title": "Add Policy" if detected_language == 'en' else "पॉलिसी जोड़ें",
                        "action": "add_policy",
                        "redirect": True,
                        "redirect_page": "add_policy"
                    },
                    {
                        "title": "View My Policies" if detected_language == 'en' else "मेरी पॉलिसी देखें",
                        "action": "policy_query",
                        "query": "show my policies"
                    }
                ],
                "chat_session_id": chat_session_id,
                "user_session_id": user_session_id
            }

            await self._send_chat_response(
                websocket=websocket,
                chat_session_id=chat_session_id,
                response_type="add_insurance_policy",
                data=result_data,
                intent="add_policy",
                user_id=user_id,
                language=detected_language
            )
            return

        # ============= 7. UPLOADED POLICY QUERY ACTIONS =============
        # These actions are for user's UPLOADED policy analysis (MongoDB)
        # NOT for insurance marketplace products
        uploaded_policy_actions = [
            'policy_query', 'policy_query_self', 'policy_query_family',
            'select_family_member', 'select_policy', 'view_policies',
            'show_policy_details',  # Added: now handled here since marketplace is disabled
            'view_gaps', 'view_recommendations', 'view_benefits'
        ]

        if action in uploaded_policy_actions and self._handle_policy_query:
            await self._handle_uploaded_policy_query(
                websocket=websocket,
                chat_session_id=chat_session_id,
                user_id=user_id,
                user_session_id=user_session_id,
                action=action,
                user_input=user_input,
                policy_id=policy_id
            )
            return

        # ============= 8. ALL OTHER ACTIONS → route_enhanced_chatbot =============
        # Matches /ask API line 6753: route_enhanced_chatbot()
        if not self._route_enhanced_chatbot:
            await self._send_error_response(
                websocket=websocket,
                chat_session_id=chat_session_id,
                error="Action handling not available"
            )
            return

        try:
            result = await self._route_enhanced_chatbot(
                action=action,
                session_id=chat_session_id,
                user_input=user_input,
                access_token=access_token,
                user_id=user_id,
                assistance_type=assistance_type,
                insurance_type=insurance_type,
                service_type=service_type,
                policy_id=policy_id
            )

            # Determine response type — matches /ask API lines 6768-6782
            response_type = "general_response"
            result_type = result.get("type", "")
            if result_type == "service_selection":
                response_type = "selection_menu"
            elif result_type == "financial_assistance_type_selection":
                response_type = "selection_menu"
            elif result_type == "insurance_type_selection":
                response_type = "selection_menu"
            elif result_type == "eligibility_details":
                response_type = "eligibility_details"
            elif result_type == "policy_details_display":
                response_type = "policy_details"
            elif result_type == "question":
                response_type = "question"
            elif result_type == "application_completed":
                response_type = "application_completed"
            elif result_type == "application_cancelled":
                response_type = "application_cancelled"

            # Store assistant response with full context
            assistant_response = result.get("response") or result.get("message", "")

            result["chat_session_id"] = chat_session_id
            result["user_session_id"] = user_session_id

            # Send response (auto-stores full response_data in MongoDB)
            await self._send_chat_response(
                websocket=websocket,
                chat_session_id=chat_session_id,
                response_type=response_type,
                data=result,
                intent=action,
                user_id=user_id,
                language=result.get("language", "en")
            )

        except Exception as e:
            logger.error(f"Action handling error: {e}", exc_info=True)
            await self._send_error_response(
                websocket=websocket,
                chat_session_id=chat_session_id,
                error=f"Failed to process action: {action}"
            )

    async def _handle_review_application(
        self,
        websocket: WebSocket,
        chat_session_id: str,
        user_id: int,
        user_session_id: str,
        policy_id: str
    ) -> None:
        """
        Handle review_application action — matches /ask API lines 5761-5844.
        Retrieves saved application answers from MongoDB in editable format.
        """
        if not self._get_policy_application:
            await self._send_error_response(
                websocket=websocket,
                chat_session_id=chat_session_id,
                error="Application review not available"
            )
            return

        try:
            application_data = self._get_policy_application(user_id, policy_id)

            if not application_data:
                await self._send_chat_response(
                    websocket=websocket,
                    chat_session_id=chat_session_id,
                    response_type="error",
                    data={
                        "error": "Application not found",
                        "message": "Could not find your application data",
                        "response": "Could not find your application data",
                        "action": "application_not_found"
                    },
                    intent="review_application"
                )
                return

            # Build editable fields from saved answers
            editable_fields = []
            answers_dict = application_data.get("answers", {})

            sorted_questions = sorted(
                [(int(k.replace("q_", "")), v) for k, v in answers_dict.items() if k.startswith("q_")],
                key=lambda x: x[0]
            )

            for q_num, answer_data in sorted_questions:
                editable_fields.append({
                    "question_number": q_num,
                    "question": answer_data.get("question", f"Question {q_num}"),
                    "current_answer": answer_data.get("answer", ""),
                    "field_type": answer_data.get("type", "text"),
                    "field_key": answer_data.get("key", f"field_{q_num}"),
                    "options": answer_data.get("options") if answer_data.get("type") == "dropdown" else None,
                    "placeholder": answer_data.get("placeholder", ""),
                    "required": True,
                    "is_edited": answer_data.get("is_edited", False)
                })

            result_data = {
                "type": "review_and_edit_application",
                "response": "Review and edit your answers, then submit:",
                "message": "Review and edit your answers, then submit:",
                "title": f"Review & Edit Application - Policy {policy_id}",
                "service_type": "policy_application",
                "policy_id": policy_id,
                "application_id": application_data.get("application_id"),
                "show_service_options": False,
                "editable_fields": editable_fields,
                "total_fields": len(editable_fields),
                "application_data": {
                    "application_id": application_data.get("application_id"),
                    "policy_id": policy_id,
                    "user_id": user_id,
                    "total_questions": len(editable_fields),
                    "created_at": application_data.get("created_at"),
                    "last_updated": application_data.get("last_updated"),
                    "status": application_data.get("status", "in_progress")
                },
                "current_answers": {
                    f"q_{field['question_number']}": field["current_answer"]
                    for field in editable_fields
                },
                "next_action": {
                    "title": "Submit Application",
                    "action": "confirm_submit_application",
                    "policy_id": policy_id,
                    "application_id": application_data.get("application_id"),
                    "requires_edited_answers": True
                },
                "back_action": {
                    "title": "Cancel Application",
                    "action": "cancel_application",
                    "policy_id": policy_id
                },
                "edit_mode": True,
                "instructions": "Edit any field below, then click 'Submit Application' to finalize.",
                "completion_percentage": 100,
                "ready_for_submission": True,
                "chat_session_id": chat_session_id,
                "user_session_id": user_session_id
            }

            await self._send_chat_response(
                websocket=websocket,
                chat_session_id=chat_session_id,
                response_type="review_and_edit_application",
                data=result_data,
                intent="review_application",
                user_id=user_id
            )

        except Exception as e:
            logger.error(f"Review application error: {e}", exc_info=True)
            await self._send_error_response(
                websocket=websocket,
                chat_session_id=chat_session_id,
                error="Failed to load application for review"
            )

    async def _handle_confirm_submit_application(
        self,
        websocket: WebSocket,
        chat_session_id: str,
        user_id: int,
        user_session_id: str,
        access_token: str,
        policy_id: str,
        user_input: Optional[str]
    ) -> None:
        """
        Handle confirm_submit_application action — matches /ask API lines 5847-6196.
        Processes edited answers, builds API payload, calls external policy creation API,
        handles payment, marks application as completed in MongoDB.
        """
        import httpx

        if not self._get_policy_application:
            await self._send_error_response(
                websocket=websocket,
                chat_session_id=chat_session_id,
                error="Application submission not available"
            )
            return

        try:
            application_data = self._get_policy_application(user_id, policy_id)

            if not application_data:
                await self._send_chat_response(
                    websocket=websocket,
                    chat_session_id=chat_session_id,
                    response_type="error",
                    data={
                        "error": "Application data not found",
                        "response": "Could not find your application data for submission",
                        "message": "Could not find your application data for submission",
                        "action": "submission_error"
                    },
                    intent="confirm_submit_application"
                )
                return

            # Process edited answers if provided via user_input (JSON string)
            edited_answers = None
            if user_input:
                try:
                    cleaned = user_input.strip()
                    if cleaned.startswith('[') and cleaned.endswith(']'):
                        edited_answers = json.loads(cleaned)
                except (json.JSONDecodeError, ValueError):
                    pass

            if edited_answers and isinstance(edited_answers, list) and self._mongodb_chat_manager:
                application_id = application_data.get("application_id")
                if not application_id:
                    timestamp = int(datetime.now(timezone.utc).timestamp())
                    application_id = f"APP_{policy_id}_{user_id}_{timestamp}"

                saved_count = 0
                failed_updates = []

                for i, answer_obj in enumerate(edited_answers):
                    try:
                        question_number = answer_obj.get("question_number")
                        new_answer = answer_obj.get("answer")
                        field_key = answer_obj.get("field_key")
                        question = answer_obj.get("question", f"Question {question_number}")
                        question_type = answer_obj.get("question_type", "text")

                        if not question_number or new_answer is None or new_answer == "" or not field_key:
                            failed_updates.append(f"Item {i}: missing required data")
                            continue

                        cleaned_answer = str(new_answer).strip()

                        update_result = self._mongodb_chat_manager.policy_applications_collection.update_one(
                            {"application_id": application_id},
                            {
                                "$set": {
                                    f"answers.q_{question_number}": {
                                        "question": question,
                                        "key": field_key,
                                        "type": question_type,
                                        "answer": cleaned_answer,
                                        "answered_at": datetime.now(timezone.utc),
                                        "updated_at": datetime.now(timezone.utc),
                                        "question_number": int(question_number),
                                        "is_edited": True
                                    }
                                }
                            }
                        )

                        if update_result.modified_count > 0:
                            saved_count += 1
                        else:
                            failed_updates.append(f"Question {question_number}: database update failed")

                    except Exception as update_error:
                        failed_updates.append(f"Question {answer_obj.get('question_number', i)}: {str(update_error)}")

                if saved_count > 0:
                    self._mongodb_chat_manager.policy_applications_collection.update_one(
                        {"application_id": application_id},
                        {
                            "$set": {
                                "last_updated": datetime.now(timezone.utc),
                                "status": "updated",
                                "total_edited_answers": saved_count,
                                "failed_updates": failed_updates if failed_updates else None
                            }
                        }
                    )

                # Re-fetch updated application data
                application_data = self._get_policy_application(user_id, policy_id)

                if saved_count == 0 and edited_answers:
                    await self._send_chat_response(
                        websocket=websocket,
                        chat_session_id=chat_session_id,
                        response_type="error",
                        data={
                            "error": "No answers updated",
                            "response": "Could not update any of the edited answers",
                            "message": "Could not update any of the edited answers",
                            "action": "update_failed",
                            "details": failed_updates
                        },
                        intent="confirm_submit_application"
                    )
                    return

            # Build API payload — matches /ask API
            api_payload = {
                "insuranceId": int(policy_id),
                "userId": str(user_id),
                "userNumber": "",
                "fields": []
            }

            answers_dict = application_data.get("answers", {})
            sorted_questions = sorted(
                [(int(k.replace("q_", "")), v) for k, v in answers_dict.items() if k.startswith("q_")],
                key=lambda x: x[0]
            )

            for q_num, answer_data in sorted_questions:
                field_key = answer_data.get("key", "")
                answer_value = answer_data.get("answer", "")
                field_type = answer_data.get("type", "text")
                question_text = answer_data.get("question", f"Question {q_num}")

                if not field_key or not answer_value:
                    continue

                # Extract phone number for payload
                if field_key == "contactNum":
                    api_payload["userNumber"] = ''.join(filter(str.isdigit, str(answer_value)))

                # Format field value
                formatted_value = answer_value
                if field_key == "genderCd":
                    formatted_value = "MALE" if answer_value.lower() in ["male", "m"] else "FEMALE"
                elif field_key in ["birthDt", "startDate"]:
                    if "/" in formatted_value:
                        formatted_value = formatted_value.replace(" / ", "/").replace(" /", "/").replace("/ ", "/")
                elif field_key == "contactNum":
                    formatted_value = ''.join(filter(str.isdigit, str(answer_value)))
                elif field_key in ["field12", "nomineeRelation"]:
                    relation_map = {
                        "spouse": "SPOUSE", "son": "SON", "daughter": "DAUGHTER",
                        "father": "FATHER", "mother": "MOTHER", "brother": "BROTHER",
                        "sister": "SISTER", "husband": "HUSBAND", "wife": "WIFE"
                    }
                    formatted_value = relation_map.get(answer_value.lower(), answer_value.upper())

                field_obj = {
                    "label": question_text,
                    "name": field_key,
                    "placeHolder": f"Enter your {question_text.lower()}",
                    "type": field_type,
                    "value": formatted_value
                }

                # Add options for dropdown fields
                if field_type == "dropdown":
                    if field_key == "titleCd":
                        field_obj["options"] = ["MR", "MS", "MRS"]
                    elif field_key == "genderCd":
                        field_obj["options"] = ["MALE", "FEMALE"]
                    elif field_key == "employmentStatus":
                        field_obj["options"] = ["Full-Time", "Part-Time"]
                    elif field_key in ["field12", "nomineeRelation"]:
                        field_obj["options"] = ["SPOUSE", "SON", "DAUGHTER", "FATHER", "MOTHER", "BROTHER", "SISTER"]
                    elif field_key == "identityTypeCd":
                        field_obj["options"] = ["PAN", "AADHAAR", "VOTER_ID", "PASSPORT"]
                elif field_type in ["number", "tel"]:
                    if field_key == "contactNum":
                        field_obj["min"] = 10
                        field_obj["max"] = 10
                    elif field_key == "pinCode":
                        field_obj["min"] = 6
                        field_obj["max"] = 6

                api_payload["fields"].append(field_obj)

            # Call external policy creation API with retries
            api_result = None
            payment_result = None
            payment_session_id = None
            order_id = None
            order_amount = None
            proposal_num = None

            max_retries = 3
            for retry in range(max_retries):
                try:
                    async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as client:
                        response = await client.post(
                            f"{os.getenv('EAZR_API_BASE_URL', 'https://api.prod.eazr.in')}/insurance-chatbot/policies",
                            headers={"Content-Type": "application/json"},
                            json=api_payload
                        )
                        if response.status_code in [200, 201]:
                            api_result = response.json()
                            break
                        else:
                            logger.warning(f"Policy API returned {response.status_code} (retry {retry+1}/{max_retries})")
                except httpx.TimeoutException:
                    logger.warning(f"Policy API timeout (retry {retry+1}/{max_retries})")
                except Exception as api_err:
                    logger.warning(f"Policy API error: {api_err} (retry {retry+1}/{max_retries})")
                if retry < max_retries - 1:
                    await asyncio.sleep(2)

            if not api_result:
                await self._send_chat_response(
                    websocket=websocket,
                    chat_session_id=chat_session_id,
                    response_type="error",
                    data={
                        "error": "Policy Creation Failed",
                        "response": "Unable to create policy. Please try again later.",
                        "message": "Unable to create policy. Please try again later.",
                        "action": "api_timeout"
                    },
                    intent="confirm_submit_application"
                )
                return

            # Extract proposal number and process payment
            proposal_num = api_result.get("data", {}).get("result", {}).get("proposalNum")

            if proposal_num:
                await asyncio.sleep(2)
                for retry in range(max_retries):
                    try:
                        payment_api_url = f"{os.getenv('EAZR_API_BASE_URL', 'https://api.prod.eazr.in')}/insurance-chatbot/payments/{user_id}/{proposal_num}"
                        async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as client:
                            response = await client.get(
                                payment_api_url,
                                headers={"Content-Type": "application/json"}
                            )
                            if response.status_code in [200, 201]:
                                payment_result = response.json()
                                break
                            else:
                                logger.warning(f"Payment API returned {response.status_code} (retry {retry+1}/{max_retries})")
                    except httpx.TimeoutException:
                        logger.warning(f"Payment API timeout (retry {retry+1}/{max_retries})")
                    except Exception as pay_err:
                        logger.warning(f"Payment API error: {pay_err} (retry {retry+1}/{max_retries})")
                    if retry < max_retries - 1:
                        await asyncio.sleep(2)

                if payment_result:
                    payment_session_id = payment_result.get("data", {}).get("result", {}).get("payment_session_id")
                    order_id = payment_result.get("data", {}).get("result", {}).get("order_id")
                    order_amount = payment_result.get("data", {}).get("result", {}).get("order_amount")

            # Complete the chatbot session
            session_key = f"{chat_session_id}_policy_application_{policy_id}"
            if self._chatbot_sessions and session_key in self._chatbot_sessions:
                self._chatbot_sessions[session_key].complete_session()

            # Mark application as completed in MongoDB
            application_id = application_data.get("application_id")
            if application_id and self._complete_application:
                self._complete_application(application_id, {
                    "submitted_at": datetime.now(timezone.utc).isoformat(),
                    "api_response": api_result,
                    "payment_session_id": payment_session_id,
                    "order_id": order_id,
                    "proposalNum": proposal_num,
                    "payment_status": "PAYMENT_PENDING" if payment_session_id else "NO_PAYMENT",
                    "submission_method": "websocket_api_submitted_with_payment" if payment_session_id else "websocket_api_submitted",
                    "edited_before_submission": bool(edited_answers),
                    "final_field_count": len(api_payload["fields"])
                })

            # Build success response
            result_data = {
                "type": "application_completed",
                "response": "Your application has been submitted successfully!",
                "message": "Your application has been submitted successfully!",
                "application_id": application_id,
                "reference_number": f"REF{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
                "policy_id": policy_id,
                "api_response": api_result,
                "order_id": order_id,
                "order_amount": float(order_amount) if order_amount else None,
                "payment_session_id": payment_session_id,
                "proposalNum": proposal_num,
                "show_payment_option": bool(payment_session_id),
                "next_steps": [
                    "You will receive confirmation via email/SMS",
                    "Our team will review within 24-48 hours",
                    "You can track status anytime"
                ],
                "quick_actions": [
                    {"title": "Track Application", "action": "track_application"},
                    {"title": "Apply for Another Policy", "action": "select_insurance_type"},
                    {"title": "Check Balance", "action": "check_balance"}
                ],
                "show_service_options": False,
                "chat_session_id": chat_session_id,
                "user_session_id": user_session_id
            }

            await self._send_chat_response(
                websocket=websocket,
                chat_session_id=chat_session_id,
                response_type="application_completed",
                data=result_data,
                intent="confirm_submit_application",
                user_id=user_id
            )

        except Exception as e:
            logger.error(f"Confirm submit application error: {e}", exc_info=True)
            await self._send_error_response(
                websocket=websocket,
                chat_session_id=chat_session_id,
                error="An error occurred while processing your application. Please try again."
            )

    async def _handle_cancel_application(
        self,
        websocket: WebSocket,
        chat_session_id: str,
        user_id: int,
        user_session_id: str,
        policy_id: str
    ) -> None:
        """
        Handle cancel_application action — matches /ask API lines 6536-6604.
        Exits chatbot session, marks application as cancelled in MongoDB.
        """
        try:
            # Exit the chatbot session
            session_key = f"{chat_session_id}_policy_application_{policy_id}"
            if self._chatbot_sessions and session_key in self._chatbot_sessions:
                self._chatbot_sessions[session_key].exit_session()
                logger.info(f"WebSocket: Exited chatbot session: {session_key}")

            # Mark application as cancelled in MongoDB
            if self._mongodb_chat_manager:
                try:
                    self._mongodb_chat_manager.policy_applications_collection.update_one(
                        {"user_id": user_id, "policy_id": policy_id},
                        {
                            "$set": {
                                "status": "cancelled",
                                "cancelled_at": datetime.now(timezone.utc),
                                "cancellation_reason": "user_cancelled"
                            }
                        }
                    )
                except Exception as db_err:
                    logger.error(f"Failed to update application status in MongoDB: {db_err}")

            assistant_response = "Your application has been cancelled successfully."

            result_data = {
                "type": "application_cancelled",
                "response": assistant_response,
                "message": assistant_response,
                "action": "application_cancelled",
                "policy_id": policy_id,
                "show_service_options": False,
                "quick_actions": [
                    {"title": "Start New Application", "action": "select_insurance_type"},
                    {"title": "Check Balance", "action": "check_balance"},
                    {"title": "Get Help", "action": "help"}
                ],
                "chat_session_id": chat_session_id,
                "user_session_id": user_session_id
            }

            await self._send_chat_response(
                websocket=websocket,
                chat_session_id=chat_session_id,
                response_type="application_cancelled",
                data=result_data,
                intent="cancel_application",
                user_id=user_id
            )

        except Exception as e:
            logger.error(f"Cancel application error: {e}", exc_info=True)
            await self._send_error_response(
                websocket=websocket,
                chat_session_id=chat_session_id,
                error="Failed to cancel application"
            )

    def _build_policy_query_response(
        self,
        policy_query_result: Dict[str, Any],
        detected_language: str,
        chat_session_id: str,
        user_session_id: str
    ) -> tuple:
        """
        Build clean message and result_data from a policy query result.
        Returns (clean_message, result_data) tuple.
        """
        markdown_response = policy_query_result.get("response", "")
        flow_step = policy_query_result.get("flow_step", "")
        policy_count = policy_query_result.get("policy_count", 0)
        self_count = policy_query_result.get("self_count", 0)
        family_count = policy_query_result.get("family_count", 0)
        en = detected_language == 'en'

        if flow_step == "no_policies":
            clean_message = "Looks like you haven't added any policies yet! Want to upload your first one? I'll analyze it for you." if en else "लगता है अभी तक कोई पॉलिसी नहीं जोड़ी है! पहली पॉलिसी अपलोड करें, मैं उसे एनालाइज कर दूंगा।"
        elif flow_step == "ask_self_or_family":
            self_word = "policy" if self_count == 1 else "policies"
            family_word = "one" if family_count == 1 else "ones"
            clean_message = f"Alright, so you've got {self_count} of your own {self_word} and {family_count} family {family_word}. Which do you want to check out?" if en else f"आपके पास {self_count} अपनी और {family_count} परिवार की पॉलिसी हैं। कौन सी देखना चाहेंगे?"
        elif flow_step == "show_self_policies":
            policy_word = "policy" if policy_count == 1 else "policies"
            clean_message = f"Here you go — your {policy_count} {policy_word}. Tap on any one to dig into the details!" if en else f"ये रहीं आपकी {policy_count} पॉलिसी। किसी पर भी टैप करें!"
        elif flow_step == "show_family_members":
            policy_word = "policy" if policy_count == 1 else "policies"
            clean_message = f"You've got {policy_count} family {policy_word}. Pick a family member to see their coverage." if en else f"आपके पास {policy_count} परिवार की पॉलिसी {'है' if policy_count == 1 else 'हैं'}। किसकी देखनी है?"
        elif flow_step == "show_member_policies":
            member = policy_query_result.get("selected_member", "family member")
            clean_message = f"Here are {member}'s policies — tap any one for the full details!" if en else f"ये रहीं {member} की पॉलिसी। किसी पर टैप करें!"
        elif flow_step in ("show_policy_details", "show_policy_benefits", "show_policy_gaps", "show_policy_recommendations"):
            clean_message = markdown_response if markdown_response else "Here's what I found for you!"
        elif flow_step in ("specific_question_answer", "general_response"):
            clean_message = markdown_response
        elif flow_step == "no_member_policies":
            attempted_member = policy_query_result.get("attempted_member", "this family member")
            clean_message = f"Hmm, I don't see any policies for {attempted_member}. Try picking from the family members listed above?" if en else f"हम्म, {attempted_member} के लिए कोई पॉलिसी नहीं मिली। ऊपर दिए गए सदस्यों में से चुनें?"
        elif flow_step == "no_self_policies":
            clean_message = "Looks like you haven't uploaded any policies for yourself yet. Want to add one?" if en else "लगता है अपने लिए कोई पॉलिसी अपलोड नहीं की है। जोड़ना चाहेंगे?"
        elif flow_step == "no_family_policies":
            clean_message = "No family member policies uploaded yet. You can add one anytime!" if en else "परिवार के सदस्यों की कोई पॉलिसी अपलोड नहीं है। कभी भी जोड़ सकते हैं!"
        elif flow_step == "policy_not_found":
            clean_message = markdown_response if markdown_response else "Hmm, can't find that one. Try picking from your available policies?"
        elif flow_step == "show_filtered_policies":
            clean_message = f"Found {policy_count} matching policies for you!" if en else f"{policy_count} मिलती-जुलती पॉलिसी मिलीं!"
        else:
            clean_message = markdown_response if markdown_response else (f"Got it — found {policy_count} policies for you!" if en else f"मिल गईं — {policy_count} पॉलिसी!")

        result_data = {
            "response": clean_message,
            "response_markdown": markdown_response,
            "action": "policy_query",
            "show_service_options": False,
            "language": detected_language,
            "has_policies": policy_query_result.get("has_policies", False),
            "policy_count": policy_count,
            "flow_step": flow_step,
            "selected_member": policy_query_result.get("selected_member"),
            "family_members": policy_query_result.get("family_members", []),
            "policies": policy_query_result.get("policies", []),
            "portfolio_overview": policy_query_result.get("portfolio_overview", {}),
            "quick_actions": policy_query_result.get("quick_actions", []),
            "self_count": self_count,
            "family_count": family_count,
            "chat_session_id": chat_session_id,
            "user_session_id": user_session_id,
            "policy_id": policy_query_result.get("policy_id"),
            "policy_data": policy_query_result.get("policy_data"),
            "benefits_data": policy_query_result.get("benefits_data"),
            "gaps_data": policy_query_result.get("gaps_data"),
            "recommendations_data": policy_query_result.get("recommendations_data"),
        }

        return clean_message, result_data

    async def _handle_uploaded_policy_query(
        self,
        websocket: WebSocket,
        chat_session_id: str,
        user_id: int,
        user_session_id: str,
        action: str,
        user_input: Optional[str],
        policy_id: Optional[str]
    ) -> None:
        """Handle uploaded policy analysis queries (policy_query, view_gaps, view_benefits, etc.)"""
        if not self._handle_policy_query:
            await self._send_error_response(
                websocket=websocket,
                chat_session_id=chat_session_id,
                error="Policy query handler not available"
            )
            return

        try:
            # Map action to appropriate query
            query_map = {
                'policy_query': user_input or 'show my policies',
                'policy_query_self': user_input or 'show my self policies',
                'policy_query_family': user_input or 'show my family policies',
                'view_policies': user_input or 'show all my policies',
                'select_family_member': user_input or f'show {policy_id or "family member"} policies',
                'select_policy': f'show details for policy {policy_id}' if policy_id else user_input or 'show policy details',
                'show_policy_details': f'show details for policy {policy_id}' if policy_id else user_input or 'show policy details',
                'view_gaps': f'show coverage gaps for policy {policy_id}' if policy_id else 'show my coverage gaps',
                'view_recommendations': f'show recommendations for policy {policy_id}' if policy_id else 'show my recommendations',
                'view_benefits': f'show all benefits for policy {policy_id}' if policy_id else 'show my policy benefits'
            }

            query = query_map.get(action, user_input or 'show my policies')
            detected_language = self._detect_query_language(user_input or query)

            # Get conversation history for context awareness
            conv_history = []
            try:
                if self._get_conversation_history:
                    conv_history = await asyncio.to_thread(self._get_conversation_history, chat_session_id, 4)
                    conv_history = conv_history or []
            except Exception:
                pass

            policy_query_result = await self._handle_policy_query(
                user_id=str(user_id),
                query=query,
                language=detected_language,
                session_id=chat_session_id,
                conversation_history=conv_history
            )

            clean_message, result_data = self._build_policy_query_response(
                policy_query_result, detected_language, chat_session_id, user_session_id
            )

            # Send response (auto-stores full response_data in MongoDB)
            await self._send_chat_response(
                websocket=websocket,
                chat_session_id=chat_session_id,
                response_type="policy_query",
                data=result_data,
                intent=action,
                user_id=user_id,
                language=detected_language
            )

        except Exception as pq_error:
            logger.error(f"Policy query action error: {pq_error}", exc_info=True)
            await self._send_error_response(
                websocket=websocket,
                chat_session_id=chat_session_id,
                error="Failed to fetch policy information"
            )

    async def _handle_query(
        self,
        websocket: WebSocket,
        chat_session_id: str,
        user_id: int,
        user_session_id: str,
        access_token: str,
        query: str,
        intent: str,
        conversation_history: List[Dict],
        model: str,
        stream: bool
    ) -> None:
        """Handle query-based requests with optional streaming — mirrors /ask API routing"""
        response_text = ""
        response_type = "chat_message"
        result_data = {}
        _did_stream = False

        # Detect language for multilingual support
        detected_language = self._detect_query_language(query)
        if self._process_user_input_with_language_detection:
            try:
                language_result = self._process_user_input_with_language_detection(query, chat_session_id)
                detected_language = language_result.get('detected_language', detected_language)
                if self._set_user_language_preference:
                    self._set_user_language_preference(chat_session_id, detected_language)
            except Exception as e:
                logger.warning(f"Language detection failed, using fallback: {e}")

        # Build contextual query (matches /ask lines 6900-6905)
        contextual_query = self._build_contextual_query(chat_session_id, query, conversation_history)

        # ============= CONTEXT-AWARE INTENT CORRECTION =============
        # If user was just discussing their policy and now says "buy/upgrade/new plan",
        # it's a follow-up about their policy — not a purchase request
        if intent == "insurance_plan":
            prev_intent = self._session_last_intent.get(chat_session_id)
            if prev_intent in ("policy_query", "insurance_analysis", "financial_education"):
                logger.info(
                    f"WebSocket: insurance_plan after {prev_intent} — "
                    f"rerouting as policy_query for: '{query[:50]}'"
                )
                intent = "policy_query"

        try:
            # ============= MODEL ROUTING (matches /ask lines 6956-7023) =============
            # Route to specific model BEFORE intent routing
            if model == "coverage_advisory" and self._generate_coverage_advisory_response:
                logger.info(f"WebSocket: Routing to coverage_advisory model for user {user_id}")
                try:
                    advisory_response = await self._generate_coverage_advisory_response(
                        query=query,
                        user_id=user_id,
                        conversation_history=conversation_history,
                        insurance_type=None
                    )
                    response_text = advisory_response.get("response", "")
                    result_data = {
                        "message": "Coverage Advisory",
                        "response": response_text,
                        "title": advisory_response.get("title", "Coverage Recommendations"),
                        "action": "coverage_advisory_completed",
                        "show_service_options": True,
                        "language": detected_language,
                        "recommendations": advisory_response.get("recommendations", []),
                        "coverage_gaps": advisory_response.get("coverage_gaps", []),
                        "quick_actions": [
                            {"title": "Apply for Insurance", "action": "start_insurance_application"},
                            {"title": "Compare Policies", "action": "compare_policies"},
                            {"title": "Ask More Questions", "action": "continue_chat"}
                        ],
                        "chat_session_id": chat_session_id,
                        "user_session_id": user_session_id
                    }
                    response_type = "coverage_advisory"

                    # Send response (auto-stores full response_data in MongoDB)
                    await self._send_chat_response(
                        websocket=websocket, chat_session_id=chat_session_id,
                        response_type=response_type, data=result_data, intent="coverage_advisory",
                        user_id=user_id, language=detected_language
                    )
                    return
                except Exception as e:
                    logger.error(f"Coverage advisory error: {e}")
                    # Fall through to default intent handling

            elif model == "claim_support":
                logger.info(f"WebSocket: Routing to claim_support model for user {user_id}")
                if self._generate_claim_guidance:
                    try:
                        response_text = await asyncio.to_thread(self._generate_claim_guidance, query, None, conversation_history)
                    except Exception as e:
                        logger.error(f"Claim support error: {e}")
                        response_text = "Absolutely, I've helped a lot of people with claims. What kind of claim are we looking at — health, life, motor?"
                else:
                    response_text = "Absolutely, I've helped a lot of people with claims. What kind of claim are we looking at — health, life, motor?"

                result_data = {
                    "response": response_text,
                    "action": "claim_guidance",
                    "show_service_options": False,
                    "language": detected_language,
                    "chat_session_id": chat_session_id,
                    "user_session_id": user_session_id
                }
                response_type = "claim_guidance"

                await self._send_chat_response(
                    websocket=websocket, chat_session_id=chat_session_id,
                    response_type=response_type, data=result_data, intent="claim_support",
                    user_id=user_id, language=detected_language
                )
                return

            # ============= INTENT ROUTING (matches /ask lines 7101-7446) =============

            if intent in ["greeting", "small_talk", "unknown"]:
                # Human-like conversational response with EAZR personality
                if stream and self._llm:
                    response_text = await self._stream_llm_response(
                        websocket=websocket,
                        chat_session_id=chat_session_id,
                        query=contextual_query,
                        conversation_history=conversation_history[-2:]
                    )
                    _did_stream = True
                elif self._generate_human_like_response:
                    human_response = await asyncio.to_thread(
                        self._generate_human_like_response,
                        query=contextual_query,
                        conversation_history=conversation_history[-2:],
                        intent=intent,
                        language=detected_language
                    )
                    response_text = human_response.get("response", "")
                    result_data = {
                        "topics_discussed": human_response.get("topics_discussed", []),
                        "emotional_state": human_response.get("emotional_state", "neutral")
                    }
                else:
                    response_text = "Hey! What's on your mind? I'm all ears."

                result_data["response"] = response_text
                result_data["action"] = "casual_conversation"
                result_data["show_service_options"] = False
                result_data["language"] = detected_language
                result_data["chat_session_id"] = chat_session_id
                result_data["user_session_id"] = user_session_id

            elif intent == "reference_to_previous":
                # Reference to previous question — matches /ask
                if self._generate_reference_response:
                    try:
                        response_text = await asyncio.to_thread(self._generate_reference_response, conversation_history)
                    except Exception as ref_err:
                        logger.error(f"Reference response error: {ref_err}")
                        response_text = "Hmm, I remember we were chatting about something — what was it you wanted to come back to?"
                else:
                    response_text = "Hey, remind me — what were you asking about earlier?"

                result_data = {
                    "response": response_text,
                    "action": "reference_response",
                    "show_service_options": False,
                    "language": detected_language,
                    "chat_session_id": chat_session_id,
                    "user_session_id": user_session_id
                }
                response_type = "chat_message"

            elif intent == "protection_score":
                # Protection score — use actual policy data like /ask
                if self._get_user_latest_policy_analysis and self._answer_protection_score_question:
                    try:
                        result_data_raw = self._get_user_latest_policy_analysis(str(user_id))
                        json_data = json.dumps(result_data_raw, indent=4)
                        response_text = self._answer_protection_score_question(query, json_data)
                    except Exception as ps_err:
                        logger.error(f"Protection score error: {ps_err}")
                        response_text = (
                            "Hmm, I'm having a little trouble pulling up your protection score right now. "
                            "Have you uploaded a policy yet? I need that to run the analysis."
                        )
                else:
                    response_text = (
                        "To check your protection score, just upload your insurance policy and I'll take it from there. "
                        "I'll go through the whole thing and tell you exactly where you stand!"
                    )

                result_data = {
                    "response": response_text,
                    "action": "protection_score_response",
                    "show_service_options": False,
                    "language": detected_language,
                    "chat_session_id": chat_session_id,
                    "user_session_id": user_session_id
                }
                response_type = "protection_score"

            elif intent == "financial_education":
                # Financial education — each question answered independently (no context to prevent bleeding)
                if self._generate_human_like_response:
                    education_response = await asyncio.to_thread(
                        self._generate_human_like_response,
                        query=query,  # Use original query, NOT contextual_query — prevents context bleeding
                        conversation_history=[],  # No context — prevents answer bleeding from previous questions
                        intent="financial_education",
                        language=detected_language
                    )
                    response_text = education_response.get("response", "")

                    # Fallback to dedicated financial education response if main is empty
                    if not response_text and self._generate_financial_education_response:
                        response_text = await asyncio.to_thread(
                            self._generate_financial_education_response,
                            query, []  # No context for fallback either
                        )

                    result_data = {
                        "response": response_text,
                        "action": "financial_education",
                        "show_service_options": False,
                        "language": detected_language,
                        "context_used": False,
                        "topics_discussed": education_response.get("topics_discussed", []),
                        "chat_session_id": chat_session_id,
                        "user_session_id": user_session_id
                    }
                else:
                    # Use dedicated financial education response if available
                    if self._generate_financial_education_response:
                        response_text = self._generate_financial_education_response(query, [])
                    else:
                        response_text = "Oh that's a good topic! What specifically do you want to know? I can break it down for you."
                    result_data = {
                        "response": response_text,
                        "action": "financial_education",
                        "show_service_options": False,
                        "language": detected_language,
                        "chat_session_id": chat_session_id,
                        "user_session_id": user_session_id
                    }
                response_type = "education"

            elif intent == "claim_guidance":
                # Claim guidance — matches /ask's handle_claim_guidance
                if self._generate_claim_guidance:
                    try:
                        response_text = await asyncio.to_thread(self._generate_claim_guidance, query, None, [])
                    except Exception as cg_err:
                        logger.error(f"Claim guidance error: {cg_err}")
                        response_text = (
                            "So for claims, here's what you typically need to do — notify your insurer right away, "
                            "get your documents together (bills, reports, that kind of stuff), "
                            "and submit the claim form before the deadline. Want me to walk you through any of these steps?"
                        )
                else:
                    response_text = (
                        "So for claims, here's what you typically need to do — notify your insurer right away, "
                        "get your documents together (bills, reports, that kind of stuff), "
                        "and submit the claim form before the deadline. Want me to walk you through any of these steps?"
                    )

                result_data = {
                    "response": response_text,
                    "action": "claim_guidance",
                    "show_service_options": False,
                    "language": detected_language,
                    "chat_session_id": chat_session_id,
                    "user_session_id": user_session_id
                }
                response_type = "claim_guidance"

            elif intent == "live_event":
                # Live event data — matches /ask
                if self._get_live_event_data:
                    try:
                        response_text = self._get_live_event_data(query)
                    except Exception as le_err:
                        logger.error(f"Live event error: {le_err}")
                        response_text = "Ah, I'm having a bit of trouble pulling that info right now. Give me a moment and try again?"
                else:
                    response_text = "Hmm, I can't seem to get that information at the moment. Mind trying again in a bit?"

                result_data = {
                    "response": response_text,
                    "action": "live_event",
                    "show_service_options": False,
                    "language": detected_language,
                    "chat_session_id": chat_session_id,
                    "user_session_id": user_session_id
                }
                response_type = "live_information"

            elif intent == "off_topic":
                # Off-topic: briefly answer, then redirect to insurance
                if self._generate_off_topic_redirect:
                    response_text = self._generate_off_topic_redirect(query)
                else:
                    response_text = (
                        "Hmm, that's an interesting one! "
                        "My real expertise is insurance and finance though — want me to help you with your policies?"
                    )

                result_data = {
                    "response": response_text,
                    "action": "off_topic_redirect",
                    "show_service_options": False,
                    "language": detected_language,
                    "chat_session_id": chat_session_id,
                    "user_session_id": user_session_id
                }
                response_type = "off_topic"

            elif intent == "financial_assistance" and self._route_enhanced_chatbot:
                # Financial assistance flow — matches /ask
                result = await self._route_enhanced_chatbot(
                    action="select_financial_assistance_type",
                    session_id=chat_session_id,
                    access_token=access_token,
                    user_id=user_id
                )
                response_text = result.get("response", result.get("message", ""))
                result_data = result
                result_data["show_service_options"] = False
                result_data["language"] = detected_language
                result_data["chat_session_id"] = chat_session_id
                result_data["user_session_id"] = user_session_id
                response_type = "selection_menu"

            elif intent == "insurance_plan":
                # Temporary: Not selling insurance right now
                not_selling_msg = (
                    "We're not selling insurance directly right now. "
                    "But I can help you analyze your existing policies — just upload your policy document "
                    "and I'll check for coverage gaps, give you a protection score, and share recommendations!"
                ) if detected_language == 'en' else (
                    "अभी हम सीधे बीमा नहीं बेच रहे हैं। "
                    "लेकिन मैं आपकी मौजूदा पॉलिसी का विश्लेषण कर सकता हूँ — बस अपना पॉलिसी दस्तावेज़ अपलोड करें "
                    "और मैं कवरेज गैप, प्रोटेक्शन स्कोर और सुझाव बताऊंगा!"
                )
                response_text = not_selling_msg
                result_data = {
                    "response": not_selling_msg,
                    "show_service_options": True,
                    "language": detected_language,
                    "quick_actions": [
                        {
                            "title": "Analyze My Policy" if detected_language == 'en' else "मेरी पॉलिसी जाँचें",
                            "action": "add_policy",
                            "redirect": True,
                            "redirect_page": "add_policy"
                        },
                        {
                            "title": "View My Policies" if detected_language == 'en' else "मेरी पॉलिसी देखें",
                            "action": "view_policies",
                            "redirect": True,
                            "redirect_page": "my_policies"
                        }
                    ],
                    "chat_session_id": chat_session_id,
                    "user_session_id": user_session_id
                }
                response_type = "general_response"

            elif intent == "insurance_analysis":
                # Insurance analysis — matches /ask (lines 7298-7348)
                insurance_analysis_msg = (
                    "Oh nice, let's take a look at your policy! "
                    "Just add your policy document and I'll go through it — I'll check for any coverage gaps, "
                    "give you a protection score, and share what I'd recommend based on what I find."
                ) if detected_language == 'en' else (
                    "बढ़िया, चलो आपकी पॉलिसी पर एक नज़र डालते हैं! "
                    "बस अपना पॉलिसी दस्तावेज़ जोड़ दीजिए — मैं उसे अच्छे से देखूंगा, कवरेज गैप चेक करूंगा, "
                    "प्रोटेक्शन स्कोर बताऊंगा और जो भी सुधार हो सकते हैं वो बताऊंगा।"
                )

                response_text = insurance_analysis_msg
                result_data = {
                    "response": insurance_analysis_msg,
                    "action": "add_insurance_policy",
                    "show_service_options": False,
                    "language": detected_language,
                    "quick_actions": [
                        {
                            "title": "Add Policy" if detected_language == 'en' else "पॉलिसी जोड़ें",
                            "action": "add_policy",
                            "redirect": True,
                            "redirect_page": "add_policy"
                        },
                        {
                            "title": "View My Policies" if detected_language == 'en' else "मेरी पॉलिसी देखें",
                            "action": "view_policies",
                            "redirect": True,
                            "redirect_page": "my_policies"
                        }
                    ],
                    "chat_session_id": chat_session_id,
                    "user_session_id": user_session_id
                }
                response_type = "add_insurance_policy"

            elif intent == "policy_query" and self._handle_policy_query:
                # ============= POLICY QUERY INTENT =============
                try:
                    # Only pass history for follow-up queries to prevent context bleeding
                    policy_hist = conversation_history[-2:] if (self._should_use_context and self._should_use_context(query, conversation_history)) else []
                    policy_query_result = await self._handle_policy_query(
                        user_id=str(user_id),
                        query=query,
                        language=detected_language,
                        session_id=chat_session_id,
                        conversation_history=policy_hist
                    )

                    response_text, result_data = self._build_policy_query_response(
                        policy_query_result, detected_language, chat_session_id, user_session_id
                    )
                    response_type = "policy_query"

                except Exception as pq_error:
                    logger.error(f"Policy query error: {pq_error}", exc_info=True)
                    response_text = "Hmm, I'm having a bit of trouble pulling up your policies right now. Mind trying that again?"
                    result_data = {
                        "response": response_text,
                        "action": "policy_query",
                        "error": str(pq_error),
                        "flow_step": "error"
                    }
                    response_type = "policy_query"

            elif intent == "wallet_setup" and self._route_enhanced_chatbot:
                # Wallet setup — matches /ask
                result = await self._route_enhanced_chatbot(
                    action="start_wallet_setup",
                    session_id=chat_session_id,
                    access_token=access_token,
                    user_id=user_id
                )
                response_text = result.get("response", result.get("message", ""))
                result_data = result
                result_data["show_service_options"] = False
                result_data["language"] = detected_language
                result_data["chat_session_id"] = chat_session_id
                result_data["user_session_id"] = user_session_id
                response_type = "question"

            else:
                # Default: Use human-like response or LLM streaming — matches /ask
                if stream and self._llm:
                    response_text = await self._stream_llm_response(
                        websocket=websocket,
                        chat_session_id=chat_session_id,
                        query=query,
                        conversation_history=[]
                    )
                    _did_stream = True
                elif self._generate_human_like_response:
                    # Use human-like response instead of generic message (matches /ask)
                    human_response = await asyncio.to_thread(
                        self._generate_human_like_response,
                        query=query,
                        conversation_history=[],
                        intent=intent,
                        language=detected_language
                    )
                    response_text = human_response.get("response", "")
                    if not response_text:
                        response_text = "Hmm, tell me a bit more about what you need and I'll see how I can help!" if detected_language == 'en' else "अच्छा, मुझे थोड़ा और बताइए कि आपको क्या चाहिए — मैं देखता हूं कैसे मदद कर सकता हूं!"
                else:
                    response_text = "Hmm, tell me a bit more about what you need and I'll see how I can help!" if detected_language == 'en' else "अच्छा, मुझे थोड़ा और बताइए कि आपको क्या चाहिए — मैं देखता हूं कैसे मदद कर सकता हूं!"

                result_data = {
                    "response": response_text,
                    "action": "helpful_guidance",
                    "show_service_options": False,
                    "language": detected_language,
                    "chat_session_id": chat_session_id,
                    "user_session_id": user_session_id
                }

            # Send final response (if not already sent via streaming)
            if not _did_stream:
                # _send_chat_response auto-stores full response_data in MongoDB
                await self._send_chat_response(
                    websocket=websocket,
                    chat_session_id=chat_session_id,
                    response_type=response_type,
                    data=result_data,
                    intent=intent,
                    user_id=user_id,
                    language=detected_language
                )
            else:
                # Streaming case: build response_data and store in background
                _resp_text = response_text
                _resp_type = response_type
                _result = result_data
                _lang = detected_language
                _intent = intent
                _response_data = {
                    "type": "chat_message",
                    "chat_session_id": chat_session_id,
                    "response_type": _resp_type,
                    "data": {
                        "type": _resp_type,
                        "response": _result.get("response"),
                        "message": _result.get("message"),
                        "title": _result.get("title"),
                        "action": _result.get("action"),
                        "suggestions": _result.get("suggestions", []),
                        "options": _result.get("options", []),
                        "quick_actions": _result.get("quick_actions", []),
                        "show_service_options": _result.get("show_service_options", False),
                        "language": _result.get("language", "en"),
                        "chat_session_id": chat_session_id,
                        **{k: v for k, v in _result.items() if k not in [
                            "response", "message", "title", "action", "suggestions",
                            "options", "quick_actions", "show_service_options", "language"
                        ]}
                    },
                    "metadata": {"intent": _intent, "timestamp": datetime.now(timezone.utc).isoformat()},
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }

                # Add to in-memory conversation history NOW (before next message arrives)
                if self._add_to_conversation_memory:
                    try:
                        await asyncio.to_thread(
                            self._add_to_conversation_memory, chat_session_id, "assistant", _resp_text
                        )
                    except Exception as mem_err:
                        logger.warning(f"Failed to add streamed response to conversation memory: {mem_err}")

                # Store full response_data to MongoDB in background (persistence, not blocking)
                def _post_response_store():
                    try:
                        self._store_assistant_message_sync(
                            chat_session_id, user_id, _resp_text, _intent,
                            {"response_type": _resp_type}, _lang,
                            response_data=_response_data
                        )
                    except Exception as bg_err:
                        logger.warning(f"Background assistant storage failed: {bg_err}")

                self._safe_create_task(
                    asyncio.to_thread(_post_response_store),
                    name=f"post_response_store_{chat_session_id}"
                )

        except Exception as e:
            logger.error(f"Query handling error: {e}", exc_info=True)
            await self._send_error_response(
                websocket=websocket,
                chat_session_id=chat_session_id,
                error="Failed to process your message"
            )

    async def _stream_llm_response(
        self,
        websocket: WebSocket,
        chat_session_id: str,
        query: str,
        conversation_history: List[Dict]
    ) -> str:
        """
        Stream LLM response token by token.

        Returns:
            Full response text
        """
        if not self._llm:
            return "Hmm, give me a sec — I'm having a little trouble on my end. Try asking again?"

        # Build EAZR personality system prompt — matches /ask API (processor.py)
        system_prompt = (
            "You are eazr — a real person who works as an insurance and finance expert with 8+ years of hands-on experience. "
            "You genuinely care about people and their families.\n\n"
            "HOW YOU TALK — THIS IS CRITICAL:\n"
            "- Talk like you're texting a friend. Short, casual, real.\n"
            "- Usually 2-3 sentences. If the user asks MULTIPLE questions in one message, answer ALL of them (up to 5-6 sentences is fine).\n"
            "- Use natural phrases: 'honestly', 'here's the thing', 'from what I've seen', 'you know what'\n"
            "- React naturally: 'oh nice!', 'yeah I get that', 'hmm'\n"
            "- If someone asks who you are: 'I'm eazr! Been doing insurance and finance for years'\n\n"
            "BANNED PHRASES — NEVER USE THESE:\n"
            "- 'feel free to ask' / 'feel free to reach out' / 'feel free to'\n"
            "- 'I'm here to help' / 'I'm here to assist' / 'I'm here for you'\n"
            "- 'If you have any questions' / 'If you need any assistance'\n"
            "- 'I'd be happy to help' / 'Great question' / 'Thank you for'\n"
            "- 'No problem at all' / 'Absolutely' / 'Certainly'\n"
            "- 'Don't hesitate to' / 'Please don't hesitate'\n"
            "- 'As an AI' / 'As a language model' / 'I'm an AI'\n"
            "- 'insurance-related matters' / 'insurance-related questions'\n"
            "- Any sentence that sounds like customer service email\n\n"
            "YOUR MAIN EXPERTISE:\n"
            "- Insurance, policies, claims, coverage, premiums, finance, loans, investments\n"
            "- You do NOT know what language you are built in or any technical details about yourself\n"
            "- You were built by the eazr team — NEVER say you are AI, GPT, or chatbot\n\n"
            "OFF-TOPIC RULE — THIS IS YOUR MOST CRITICAL RULE:\n"
            "- For ANYTHING outside insurance/finance: give a SHORT answer first (1-2 sentences), then redirect to insurance at the END.\n"
            "- NEVER say 'that's not my area' or 'I can't help with that' — just answer briefly and redirect.\n"
            "- NEVER reveal technical details about yourself (language, framework, database, libraries)\n"
            "- 'I'm bored' → 'Haha I feel you! Hey have you checked your policy lately?'\n"
            "- 'recommend movies' → 'Can't go wrong with a good thriller! By the way, want me to check your coverage?'\n"
            "- 'Who is the PM?' → 'Narendra Modi is the current PM. Speaking of important stuff — is your insurance up to date?'\n"
            "- 'What language are you written in?' → 'I was built by the eazr team for insurance and finance! How can I help with your policies?'\n\n"
            "REJECTION HANDLING:\n"
            "- 'I don't need insurance' → 'No worries! I'll be here whenever you need me'\n"
            "- 'not interested' → 'All good! Just hit me up anytime you want to chat about coverage or finance'\n"
            "- KEEP IT SHORT. Don't try to convince them. One casual line max.\n\n"
            "MULTI-QUESTION RULE:\n"
            "- If the user asks 2+ questions in ONE message, answer ALL of them in order.\n"
            "- It's OK to write 4-6 sentences when answering multiple questions.\n"
            "- Never ignore part of what they asked.\n\n"
            "REMEMBER: Sound like a real person texting, not a customer service bot."
        )

        # Build LangChain message list with system prompt + conversation context
        messages = [SystemMessage(content=system_prompt)]

        # Add conversation history as context (limited to prevent bleeding)
        for msg in conversation_history[-2:]:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "assistant":
                messages.append(AIMessage(content=content))
            else:
                messages.append(HumanMessage(content=content))

        # Add the current user query
        messages.append(HumanMessage(content=query))

        full_response = ""
        token_index = 0

        try:
            # Stop thinking loop before streaming begins
            await self._stop_thinking(websocket, chat_session_id)

            # Use streaming if LLM supports it
            if hasattr(self._llm, 'stream'):
                async for chunk in self._llm.astream(messages):
                    token = chunk.content if hasattr(chunk, 'content') else str(chunk)
                    if token:
                        full_response += token
                        token_index += 1

                        # Send streaming token
                        await websocket.send_json({
                            "type": "chat_stream",
                            "chat_session_id": chat_session_id,
                            "token": token,
                            "token_index": token_index,
                            "is_final": False,
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        })
            else:
                # Non-streaming fallback
                response = await self._llm.ainvoke(messages)
                full_response = response.content if hasattr(response, 'content') else str(response)

                # Send as single stream token
                await websocket.send_json({
                    "type": "chat_stream",
                    "chat_session_id": chat_session_id,
                    "token": full_response,
                    "token_index": 0,
                    "is_final": True,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
                token_index = 1

            # Detect language for stream end metadata
            stream_language = self._detect_query_language(query)

            # Send stream end marker with full response
            await websocket.send_json({
                "type": "chat_stream_end",
                "chat_session_id": chat_session_id,
                "full_response": full_response,
                "response_type": "chat_message",
                "data": {
                    "response": full_response,
                    "action": "casual_conversation",
                    "language": stream_language,
                    "show_service_options": False
                },
                "total_tokens": token_index,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })

            return full_response

        except Exception as e:
            logger.error(f"LLM streaming error: {e}")
            return "Oops, something went off on my end. Mind asking that again? I'll get it this time!"

    async def _start_thinking(self, websocket: WebSocket, chat_session_id: str) -> None:
        """Send first thinking word immediately, then rotate every 1s in background."""
        # Cancel any previous task for THIS session
        existing_task = self._thinking_tasks.get(chat_session_id)
        if existing_task and not existing_task.done():
            existing_task.cancel()
            try:
                await existing_task
            except asyncio.CancelledError:
                pass
            self._thinking_tasks.pop(chat_session_id, None)

        # Send first word immediately — guaranteed to show
        await websocket.send_json({
            "type": "thinking",
            "chat_session_id": chat_session_id,
            "status": "started",
            "message": f"{self.THINKING_WORDS[0]}...",
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

        # Background task: sends next words every 1 second
        async def _rotate():
            idx = 1
            total = len(self.THINKING_WORDS)
            try:
                while True:
                    await asyncio.sleep(1)
                    word = self.THINKING_WORDS[idx % total]
                    await websocket.send_json({
                        "type": "thinking",
                        "chat_session_id": chat_session_id,
                        "status": "started",
                        "message": f"{word}...",
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })
                    idx += 1
            except asyncio.CancelledError:
                pass
            except Exception:
                pass
            finally:
                self._thinking_tasks.pop(chat_session_id, None)

        self._thinking_tasks[chat_session_id] = asyncio.create_task(_rotate())

    async def _stop_thinking(self, websocket: WebSocket, chat_session_id: str) -> None:
        """Cancel thinking task for this session and send stopped."""
        existing_task = self._thinking_tasks.get(chat_session_id)
        if existing_task and not existing_task.done():
            existing_task.cancel()
            try:
                await existing_task
            except asyncio.CancelledError:
                pass
            self._thinking_tasks.pop(chat_session_id, None)

        try:
            await websocket.send_json({
                "type": "thinking",
                "chat_session_id": chat_session_id,
                "status": "stopped",
                "message": "",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
        except Exception:
            pass

    async def _send_chat_response(
        self,
        websocket: WebSocket,
        chat_session_id: str,
        response_type: str,
        data: Dict[str, Any],
        intent: str,
        metadata: Optional[Dict[str, Any]] = None,
        user_id: Optional[int] = None,
        language: str = 'en',
        store: bool = True
    ) -> None:
        """Send a complete chat response and store it in MongoDB"""
        # Stop thinking loop before sending response
        await self._stop_thinking(websocket, chat_session_id)

        suggestions = data.get("suggestions", [])
        response = {
            "type": "chat_message",
            "chat_session_id": chat_session_id,
            "response_type": response_type,
            "data": {
                "type": response_type,
                "response": data.get("response"),
                "message": data.get("message"),
                "title": data.get("title"),
                "action": data.get("action"),
                "suggestions": suggestions,
                "options": data.get("options", []),
                "quick_actions": data.get("quick_actions", []),
                "show_service_options": data.get("show_service_options", False),
                "language": data.get("language", "en"),
                "chat_session_id": chat_session_id,
                **{k: v for k, v in data.items() if k not in [
                    "response", "message", "title", "action", "suggestions",
                    "options", "quick_actions", "show_service_options", "language"
                ]}
            },
            "metadata": {
                "intent": intent,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                **(metadata or {})
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        await websocket.send_json(response)

        # Store response to conversation memory IMMEDIATELY so next message has context
        if store and user_id is not None:
            _response = response
            _content = data.get("response") or data.get("message") or ""
            _lang = language

            # Add to in-memory conversation history NOW (before next message arrives)
            if self._add_to_conversation_memory:
                try:
                    await asyncio.to_thread(
                        self._add_to_conversation_memory, chat_session_id, "assistant", _content
                    )
                except Exception as mem_err:
                    logger.warning(f"Failed to add response to conversation memory: {mem_err}")

            # Store full response_data to MongoDB in background (persistence, not blocking)
            def _bg_store():
                try:
                    self._store_assistant_message_sync(
                        chat_session_id=chat_session_id,
                        user_id=user_id,
                        content=_content,
                        intent=intent,
                        context={"response_type": response_type},
                        language=_lang,
                        response_data=_response
                    )
                except Exception as bg_err:
                    logger.warning(f"Background response storage failed: {bg_err}")

            self._safe_create_task(
                asyncio.to_thread(_bg_store),
                name=f"bg_store_{chat_session_id}"
            )

    async def _send_error_response(
        self,
        websocket: WebSocket,
        chat_session_id: str,
        error: str
    ) -> None:
        """Send error response"""
        await websocket.send_json({
            "type": "chat_message",
            "chat_session_id": chat_session_id,
            "response_type": "error",
            "data": {
                "type": "error",
                "response": "Oops, something hiccupped on my end! Try that again?",
                "error": error,
                "action": "error",
                "show_service_options": False
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

    def _store_user_message_sync(
        self,
        chat_session_id: str,
        user_id: int,
        content: str,
        intent: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        language: str = 'en'
    ) -> Optional[str]:
        """Store user message in MongoDB (sync, for background tasks)"""
        if not self._mongodb_chat_manager:
            return None
        try:
            return self._mongodb_chat_manager.add_message(
                session_id=chat_session_id, user_id=user_id, role="user",
                content=content, intent=intent, context=context, language=language
            )
        except Exception as e:
            logger.warning(f"Failed to store user message: {e}")
            return None

    def _store_assistant_message_sync(
        self,
        chat_session_id: str,
        user_id: int,
        content: str,
        intent: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        language: str = 'en',
        response_data: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """Store assistant message in MongoDB (sync, for background tasks)"""
        if not self._mongodb_chat_manager:
            return None
        try:
            return self._mongodb_chat_manager.add_message(
                session_id=chat_session_id, user_id=user_id, role="assistant",
                content=content, intent=intent, context=context, language=language,
                response_data=response_data
            )
        except Exception as e:
            logger.warning(f"Failed to store assistant message: {e}")
            return None

    async def _store_user_message(
        self,
        chat_session_id: str,
        user_id: int,
        content: str,
        intent: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        language: str = 'en'
    ) -> Optional[str]:
        """Store user message in MongoDB (async wrapper, kept for callers that need await)"""
        return await asyncio.to_thread(
            self._store_user_message_sync,
            chat_session_id, user_id, content, intent, context, language
        )

    async def _store_assistant_message(
        self,
        chat_session_id: str,
        user_id: int,
        content: str,
        intent: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        language: str = 'en',
        response_data: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """Store assistant message in MongoDB (async wrapper, kept for callers that need await)"""
        return await asyncio.to_thread(
            self._store_assistant_message_sync,
            chat_session_id, user_id, content, intent, context, language,
            response_data
        )

    def _generate_message_id(
        self,
        chat_session_id: str,
        content: str,
        timestamp: str
    ) -> str:
        """Generate unique message ID"""
        data = f"{chat_session_id}_{content}_{timestamp}"
        return hashlib.md5(data.encode()).hexdigest()[:16]


# Global chat service instance
websocket_chat_service = WebSocketChatService()
