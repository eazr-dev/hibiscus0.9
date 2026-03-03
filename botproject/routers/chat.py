"""
Chat Router - Conversation and Chat Session Management
Extracted from app.py - Handles all chat-related endpoints

This router includes:
- Session Management (new-chat, load-chat, update-title, delete-chat, archive-chat)
- Conversation Endpoints (ask, chatbot-continue, chat-history, search-chat)
- Chat Analytics and Export (chat-analytics, conversation-context, export-conversation)
- User Chat Management (clear-user-chat-history, search-chats)
"""
import asyncio
import logging
import time
import secrets
import os
import hashlib
import json
import openai
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Form, File, UploadFile, Request
from fastapi.responses import JSONResponse, Response

# Rate limiting
from core.rate_limiter import limiter, RATE_LIMITS

# Core imports
from core.dependencies import (
    get_session,
    store_session,
    delete_session,
    cache_api_call,
    get_cached_api_call,
    MONGODB_AVAILABLE,
    MULTILINGUAL_AVAILABLE
)

# Session and user management
from session_security.session_manager import session_manager
from session_security.token_genrations import verify_jwt_token, create_jwt_token

# Authentication verification utilities
from utils.auth_verification import (
    verify_user_authentication,
    create_auth_error_response,
    should_verify_token
)

# Models
from models.chat import (
    LoadChatRequest,
    DeleteChatRequest,
    SearchChatsRequest,
    UpdateChatTitleRequest,
    QueryInput,
    ChatbotContinue,
    ChatHistoryRequest,
    SearchChatRequest,
    ClearUserChatRequest,
    RegenerateReportRequest,
    RegenerateSectionRequest
)

# MongoDB chat manager
try:
    from database_storage.mongodb_chat_manager import (
        mongodb_chat_manager,
        load_specific_chat,
        delete_chat_session_by_id,
        update_chat_session_title,
        search_user_chats,
        get_all_user_chats,
        add_user_message_to_mongodb,
        add_assistant_message_to_mongodb,
        get_contextual_prompt_from_mongodb,
        backup_and_clear_user_chat_history,
        store_policy_analysis_in_mongodb,
        get_user_latest_policy_analysis,
        get_policy_analysis_by_id,
        get_policy_application,
        update_policy_answer,
        complete_application
    )
except ImportError:
    mongodb_chat_manager = None
    logger = logging.getLogger(__name__)
    logger.warning("MongoDB chat manager not available")

# Chat memory system
from ai_chat_components.chat_memory import (
    chat_memory,
    get_conversation_context,
    get_chat_analytics,
    search_chat_history,
    clear_chat_history
)

# Conversation processing
from ai_chat_components.processor import (
    generate_casual_response_with_context,
    generate_casual_response_hindi_with_context,
    detect_conversation_continuity,
    get_last_user_question,
    generate_contextual_suggestions,
    detect_intent_with_context,
    generate_reference_response,
    extract_conversation_topics,
    should_use_context,
    generate_financial_education_response,
    generate_claim_guidance_response,
    generate_claim_aware_casual_response,
    generate_claim_suggestions,
    get_cached_intent,
    # Advanced Human-Like Conversation System
    AdvancedConversationContext,
    generate_human_like_response,
    build_advanced_context_for_ai,
    get_conversation_context_summary
)

# Enhanced chatbot handlers
from ai_chat_components.enhanced_chatbot_handlers import (
    route_enhanced_chatbot,
    handle_service_selection,
    continue_financial_assistance_application,
    continue_insurance_application,
    FINANCIAL_ASSISTANCE_TYPES,
    get_session_info,
    clear_session,
    chatbot_sessions,
    INSURANCE_TYPES,
    continue_wallet_setup,
    generate_fresh_start_response,
    show_financial_assistance_eligibility,
    show_policy_details_from_stored_data,
    accept_policy_and_start_application,
    continue_policy_application,
    show_insurance_eligibility,
    extract_actual_user_input
)

# Multilingual support
if MULTILINGUAL_AVAILABLE:
    from support_features.multilingual_support import (
        get_predefined_response,
        process_user_input_with_language_detection,
        translate_chatbot_response,
        set_user_language_preference,
        get_user_language_preference,
        detect_hindi_or_english,
        translate_response
    )

# LLM configuration
from ai_chat_components.llm_config import get_llm

# Insurance analysis
try:
    from financial_services.dynamic_insurance_analyzer import UniversalDynamicAnalyzer
except ImportError:
    UniversalDynamicAnalyzer = None

# S3 and audit report generation
from database_storage.s3_bucket import upload_pdf_to_s3, upload_image_to_s3
from financial_services.audit_report import generate_pdf_report
from financial_services.insurance_audit import analyzer
from financial_services.protection_score_ans import answer_protection_score_question

# Live event data
try:
    from support_features.live_info import get_live_event_data
except ImportError:
    get_live_event_data = None

# RAG setup (imported from app.py context)
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.agents import create_react_agent, AgentExecutor
from support_features.tool_reg import register_tools

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(tags=["Chat"])

# ============= INITIALIZE RAG COMPONENTS =============
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
llm = get_llm(use_case='general')

try:
    vectorstore = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)
    logger.info("✓ Loaded existing FAISS vectorstore")
except Exception as e:
    logger.warning(f"⚠ Could not load vectorstore: {e}")
    vectorstore = None

if vectorstore:
    retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 3})

    rag_prompt_template = """
Context from documents: {context}
Question: {question}

Provide a comprehensive answer based on the context. If the context doesn't contain enough information, supplement with general knowledge but clearly distinguish between document-based and general information.

Answer:
"""
    rag_prompt = PromptTemplate(template=rag_prompt_template, input_variables=["context", "question"])
    rag_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        chain_type_kwargs={"prompt": rag_prompt},
        return_source_documents=True
    )
else:
    rag_chain = None

# ============= GLOBAL CACHES =============
_agent_cache = {}
_agent_cache_ttl = {}
_session_cache = {}
_session_cache_ttl = {}
_intent_cache = {}
_intent_cache_ttl = {}
_conversation_cache = {}
_conversation_cache_ttl = {}
_response_cache = {}
_response_cache_ttl = {}

# ============= HELPER FUNCTIONS =============

def rag_handler(query: str) -> dict:
    """Handle RAG queries with optional caching"""
    try:
        logger.info(f"📚 Processing RAG query: {query[:50]}...")

        # Create cache key
        cache_key = f"rag:{hash(query)}"

        # Check cache first if available
        cached_result = get_cached_api_call(cache_key)
        if cached_result:
            logger.info("✓ Returning cached RAG result")
            return cached_result

        # Check if rag_chain is available
        if not rag_chain:
            logger.warning("⚠ RAG chain not available")
            return {
                "response": "Document retrieval system is currently unavailable. Please try again later.",
                "source_documents": []
            }

        # Process query
        result = rag_chain.invoke({"query": query})
        response_data = {
            "response": result["result"],
            "source_documents": [
                {"content": doc.page_content[:200], "metadata": doc.metadata}
                for doc in result.get("source_documents", [])[:2]
            ]
        }

        # Cache result for 30 minutes (extended for better performance)
        cache_api_call(cache_key, response_data, expire_seconds=1800)
        logger.info("✓ RAG query processed and cached")

        return response_data
    except Exception as e:
        logger.error(f"✗ RAG handler error: {str(e)}")
        return {
            "response": f"Error retrieving document information: {str(e)}",
            "source_documents": []
        }


def get_cached_session(session_id: str):
    """Get session with caching"""
    import time

    current_time = time.time()
    cache_key = f"session:{session_id}"

    # Check cache first (TTL: 5 minutes)
    if (cache_key in _session_cache and
        cache_key in _session_cache_ttl and
        current_time - _session_cache_ttl[cache_key] < 300):
        return _session_cache[cache_key]

    # Get from storage
    session_data = get_session(session_id)

    # Cache it
    _session_cache[cache_key] = session_data
    _session_cache_ttl[cache_key] = current_time

    # Clean old cache entries
    if len(_session_cache) > 100:
        oldest_key = min(_session_cache_ttl.keys(), key=_session_cache_ttl.get)
        del _session_cache[oldest_key]
        del _session_cache_ttl[oldest_key]

    return session_data


def get_or_create_agent(access_token: str, user_id: int):
    """Get cached agent or create new one with TTL"""
    import time

    cache_key = f"agent:{user_id}"
    current_time = time.time()

    # Check if we have a valid cached agent (TTL: 10 minutes)
    if (cache_key in _agent_cache and
        cache_key in _agent_cache_ttl and
        current_time - _agent_cache_ttl[cache_key] < 600):
        logger.info("✓ Using cached agent")
        return _agent_cache[cache_key]

    # Create new agent and cache it
    logger.info("🔨 Creating new agent")
    try:
        from langchain import hub
        prompt = hub.pull("hwchase17/react")
        enhanced_tools = register_tools(access_token, user_id)
        agent = create_react_agent(llm=llm, tools=enhanced_tools, prompt=prompt)
        agent_executor = AgentExecutor(
            agent=agent,
            tools=enhanced_tools,
            verbose=True,
            handle_parsing_errors=True
        )

        # Cache the agent
        _agent_cache[cache_key] = agent_executor
        _agent_cache_ttl[cache_key] = current_time

        # Clean old cache entries (keep only last 50)
        if len(_agent_cache) > 50:
            oldest_key = min(_agent_cache_ttl.keys(), key=_agent_cache_ttl.get)
            del _agent_cache[oldest_key]
            del _agent_cache_ttl[oldest_key]

        return agent_executor
    except Exception as e:
        logger.error(f"✗ Error creating agent: {e}")
        return None


def create_standardized_response(
    response_type: str,
    data: Dict,
    session_id: str,
    metadata: Dict = None
) -> Dict:
    """
    Create a standardized response with ALL keys present

    SESSION ID CONSISTENCY FIX:
    - session_id parameter is ALWAYS the chat_session_id (conversation thread ID)
    - Response includes BOTH 'session_id' and 'chat_session_id' at root level (same value)
    - Response includes 'chat_session_id' and 'user_session_id' in data field
    - Response includes both session IDs in metadata field
    - This ensures consistent session tracking across all API responses

    Args:
        response_type: Type of response (chat_message, error, selection_menu, etc.)
        data: Response data dictionary
        session_id: Chat session ID (conversation thread identifier)
        metadata: Optional metadata dictionary

    Returns:
        Standardized response dictionary with consistent session ID fields
    """

    # Initialize ALL data fields with null
    standardized_data = {
        "type": response_type,
        "response": None,
        "message": None,
        "title": None,
        "subtitle": None,
        "action": None,
        "show_service_options": False,
        "language": data.get("language", "en"),
        "suggestions": None,
        "options": None,
        "service_type": None,
        "editable_fields": None,
        "assistance_type": None,
        "insurance_type": None,
        "eligibility": None,
        "loan_details": None,
        "coverage_details": None,
        "features": None,
        "next_action": None,
        "back_action": None,
        "cancel_action":None,
        "context_used": False,
        "session_continuation": False,
        "session_regenerated": False,
        "original_session_id": None,
        # Session identifiers - ALWAYS include these
        "chat_session_id": None,
        "user_session_id": None,
        # File-related fields
        "file_action_needed": None,
        "report_url": None,
        "report_id": None,
        "mongodb_id": None,
        # Analysis-specific fields
        "protection_score": None,
        "protection_level": None,
        "recommendations": None,
        "category_scores": None,
        "policy_info": None,
        "analysis_results": None,
        # Application Data review
        "application_data":None,
        "review_data":None,
        #payment
        "order_id": None,
        "proposalNum": None,
        "payment_session_id":None,
        "order_amount":None,
        "show_payment_option":True,
        "policyNum":None,
        "policyStatus":None,
        "documentUrl": None,
        # Quick actions
        "quick_actions": None,
        # Error fields
        "error": None,
        "validation_error": None,
        # Question flow fields
        "question_number": None,
        "total_questions": None,
        "progress": None,
        "input_type": None,
        "regex":None,
        "input_hint": None,
        "input_examples": None,
        "required": None,
        "exit_option": None,
        # Application fields
        "application_id": None,
        "reference_number": None,
        "next_steps": None,
        "estimated_processing": None
    }

    # Update with actual data
    standardized_data.update({k: v for k, v in data.items() if k in standardized_data})

    # ALWAYS ensure chat_session_id is set in data (critical for consistency)
    if not standardized_data.get("chat_session_id"):
        standardized_data["chat_session_id"] = session_id

    # Ensure user_session_id is preserved if provided in data
    if data.get("user_session_id") and not standardized_data.get("user_session_id"):
        standardized_data["user_session_id"] = data.get("user_session_id")

    # Initialize metadata with all keys
    standardized_metadata = {
        "message_id": None,
        "original_query": None,
        "processed_query": None,
        "chat_session_id": session_id,  # Always include in metadata
        "user_session_id": data.get("user_session_id"),  # Include if available
        "active_sessions": 0,
        "conversation_length": 0,
        "session_continuation": False,
        "context_used": False,
        "topics_discussed": [],
        "last_user_question": None,
        "language_detected": "en",
        "language_confidence": 1.0,
        "intent": None,
        "file_processed": False
    }

    # Update with actual metadata
    if metadata:
        standardized_metadata.update(metadata)

    # Ensure metadata always has current session IDs (overwrite if needed for consistency)
    standardized_metadata["chat_session_id"] = session_id
    if data.get("user_session_id"):
        standardized_metadata["user_session_id"] = data.get("user_session_id")

    return {
        "status": "success",
        "timestamp": datetime.now().isoformat(),
        "session_id": session_id,  # Keep for backward compatibility
        "chat_session_id": session_id,  # Add explicit chat_session_id at root level
        "response_type": response_type,
        "data": standardized_data,
        "metadata": standardized_metadata
    }


def add_to_conversation_memory(session_id: str, role: str, content: str):
    """Add message to conversation memory"""
    try:
        chat_memory.add_message(session_id, role, content)
    except Exception as e:
        logger.error(f"Error adding to conversation memory: {e}")


def get_conversation_history(session_id: str, limit: int = 10) -> List[Dict]:
    """Get conversation history"""
    try:
        messages = chat_memory.get_conversation_history(session_id, limit)
        return [msg.to_dict() for msg in messages]
    except Exception as e:
        logger.error(f"Error getting conversation history: {e}")
        return []


def build_contextual_prompt(session_id: str, query: str) -> str:
    """
    Build a contextual prompt by combining the query with conversation history
    Fallback function when MongoDB is not available
    """
    try:
        # Get recent conversation history
        history = get_conversation_history(session_id, limit=4)

        if not history:
            return query

        # Build context from recent messages (limited to prevent bleeding)
        context_parts = []
        for msg in history[-2:]:  # Last 2 messages only
            role = msg.get('role', 'user')
            content = msg.get('content', '')
            if content:
                context_parts.append(f"{role.capitalize()}: {content}")

        if context_parts:
            context_str = "\n".join(context_parts)
            return f"Previous conversation:\n{context_str}\n\nCurrent query: {query}"

        return query
    except Exception as e:
        logger.error(f"Error building contextual prompt: {e}")
        return query


# ============= POLICY QUERY HANDLER =============
def fetch_user_policies_from_mongodb(user_id: str, policy_for: str = None) -> list:
    """
    Fetch user policies from MongoDB using the same logic as /api/user/policies endpoint.
    Uses user_id as integer and queries policy_analysis collection.

    Args:
        user_id: User ID
        policy_for: "self", "family", or None (for all policies)
                   - "self": Returns policies where policyFor is "self" OR policyFor is missing/null
                   - "family": Returns policies where policyFor is "family"
                   - None: Returns all policies
    """
    try:
        from database_storage.mongodb_chat_manager import mongodb_chat_manager

        if mongodb_chat_manager is None or mongodb_chat_manager.db is None:
            logger.error("MongoDB not available for policy fetch")
            return []

        # Convert to integer (same as /api/user/policies)
        try:
            user_id_int = int(user_id)
        except ValueError:
            logger.error(f"Invalid user_id: {user_id}")
            return []

        db = mongodb_chat_manager.db
        policy_analysis_collection = db['policy_analysis']

        # Build query - same as /api/user/policies
        query_filter = {
            "user_id": user_id_int,
            "$or": [
                {"isDeleted": {"$exists": False}},
                {"isDeleted": False}
            ]
        }

        # Filter by policyFor if specified
        if policy_for == "self":
            # For "self" - include policies without policyFor field (default to self)
            query_filter["$and"] = [
                query_filter.pop("$or"),  # Move existing $or to $and
                {
                    "$or": [
                        {"policyFor": "self"},
                        {"policyFor": {"$exists": False}},
                        {"policyFor": None},
                        {"policyFor": ""}
                    ]
                }
            ]
            query_filter["$or"] = query_filter["$and"][0]  # Restore $or for isDeleted
            del query_filter["$and"]
            # Simpler approach - just use $or for policyFor condition
            query_filter = {
                "user_id": user_id_int,
                "$and": [
                    {
                        "$or": [
                            {"isDeleted": {"$exists": False}},
                            {"isDeleted": False}
                        ]
                    },
                    {
                        "$or": [
                            {"policyFor": "self"},
                            {"policyFor": {"$exists": False}},
                            {"policyFor": None},
                            {"policyFor": ""}
                        ]
                    }
                ]
            }
        elif policy_for == "family":
            query_filter["policyFor"] = "family"
        # If policy_for is None, don't filter - return all policies

        # Fetch all policies
        policies_cursor = policy_analysis_collection.find(query_filter).sort("created_at", -1)
        policies = list(policies_cursor)

        logger.info(f"📋 fetch_user_policies_from_mongodb: Found {len(policies)} policies for user_id={user_id_int}, policy_for={policy_for}")

        # Convert ObjectId to string
        for policy in policies:
            if "_id" in policy:
                policy["_id"] = str(policy["_id"])
            if "created_at" in policy and hasattr(policy["created_at"], 'isoformat'):
                policy["created_at"] = policy["created_at"].isoformat()
            if "updated_at" in policy and hasattr(policy["updated_at"], 'isoformat'):
                policy["updated_at"] = policy["updated_at"].isoformat()

        return policies

    except Exception as e:
        logger.error(f"Error fetching policies from MongoDB: {e}")
        return []


def filter_policies_by_query(query: str, policies_data: list) -> tuple:
    """
    Filter policies based on user query to identify specific policy.

    Returns:
        tuple: (filtered_policies, filter_type)
        filter_type: "provider", "type", "policy_number", or "none"
    """
    query_lower = query.lower()

    # Common insurance provider names
    provider_keywords = {
        'hdfc': ['hdfc', 'hdfc ergo', 'hdfc life'],
        'icici': ['icici', 'icici lombard', 'icici prudential'],
        'lic': ['lic', 'life insurance corporation'],
        'sbi': ['sbi', 'sbi life', 'sbi general'],
        'max': ['max', 'max life', 'max bupa'],
        'bajaj': ['bajaj', 'bajaj allianz'],
        'tata': ['tata', 'tata aig', 'tata aia'],
        'star': ['star', 'star health'],
        'reliance': ['reliance', 'reliance general'],
        'kotak': ['kotak', 'kotak life'],
        'aditya birla': ['aditya birla', 'birla sun life'],
        'care': ['care', 'care health'],
        'niva bupa': ['niva', 'niva bupa', 'bupa']
    }

    # Policy type keywords
    type_keywords = {
        'health': ['health', 'medical', 'mediclaim', 'swasthya'],
        'life': ['life', 'term', 'jeevan', 'endowment'],
        'motor': ['motor', 'car', 'bike', 'vehicle', 'auto', 'two wheeler'],
        'home': ['home', 'house', 'property', 'ghar'],
        'travel': ['travel', 'yatra'],
        'critical': ['critical', 'illness', 'cancer', 'heart']
    }

    filtered = []
    filter_type = "none"

    # Check for provider match
    for _, keywords in provider_keywords.items():
        if any(kw in query_lower for kw in keywords):
            for policy in policies_data:
                extracted = policy.get('extractedData', {})
                provider = extracted.get('insuranceProvider', '').lower()
                if any(kw in provider for kw in keywords):
                    filtered.append(policy)
            if filtered:
                filter_type = "provider"
                return (filtered, filter_type)

    # Check for policy type match
    for _, keywords in type_keywords.items():
        if any(kw in query_lower for kw in keywords):
            for policy in policies_data:
                extracted = policy.get('extractedData', {})
                policy_type = extracted.get('policyType', '').lower()
                if any(kw in policy_type for kw in keywords):
                    filtered.append(policy)
            if filtered:
                filter_type = "type"
                return (filtered, filter_type)

    # Check for policy number mention
    for policy in policies_data:
        extracted = policy.get('extractedData', {})
        policy_number = extracted.get('policyNumber', '').lower()
        if policy_number and policy_number in query_lower:
            filtered.append(policy)
            filter_type = "policy_number"
            return (filtered, filter_type)

    return (policies_data, "none")


def is_specific_policy_query(query: str) -> bool:
    """
    Check if the query is asking about a specific policy detail
    that would need clarification when multiple policies exist.
    """
    query_lower = query.lower()

    # Keywords that indicate asking about specific policy details
    specific_keywords = [
        'benefits', 'benefit', 'key benefits',
        'exclusions', 'exclusion', 'not covered',
        'coverage amount', 'sum assured', 'sum insured',
        'premium', 'premium amount',
        'expiry', 'expire', 'end date', 'validity',
        'start date', 'policy date',
        'waiting period',
        'claim process', 'how to claim',
        'policy number', 'policy details',
        'this policy', 'that policy', 'the policy'
    ]

    # Keywords that indicate asking about all policies (no clarification needed)
    general_keywords = [
        'how many', 'total', 'all policies', 'all my',
        'coverage gaps', 'gaps', 'recommendations',
        'protection score', 'portfolio', 'overview'
    ]

    # If asking about general/all policies, no clarification needed
    if any(kw in query_lower for kw in general_keywords):
        return False

    # If asking about specific details, may need clarification
    if any(kw in query_lower for kw in specific_keywords):
        return True

    return False


def build_policy_list(policies_data: list, language: str = 'en') -> str:
    """Build a formatted list of policies for display"""
    lines = []

    for i, policy in enumerate(policies_data, 1):
        extracted = policy.get('extractedData', {})
        provider = extracted.get('insuranceProvider', 'Unknown')
        policy_type = extracted.get('policyType', 'Unknown')
        coverage = extracted.get('coverageAmount', 0) or extracted.get('sumAssured', 0)

        if language == 'en':
            lines.append(f"{i}. {provider} - {policy_type} (Coverage: ₹{coverage:,.0f})")
        else:
            lines.append(f"{i}. {provider} - {policy_type} (कवरेज: ₹{coverage:,.0f})")

    return "\n".join(lines)


def is_valid_policy(policy: dict) -> bool:
    """
    Check if a policy has valid/meaningful extracted data.
    Filters out ghost policies with no provider, no type, and no coverage.
    """
    extracted = policy.get('extractedData', {})
    if not extracted:
        return False

    provider = extracted.get('insuranceProvider', '')
    policy_type = extracted.get('policyType', '')
    coverage = extracted.get('coverageAmount', 0) or extracted.get('sumAssured', 0)

    # Policy is invalid if ALL key fields are missing/unknown/empty
    provider_valid = provider and provider.lower() not in ('unknown', '', 'n/a', 'na', 'none', 'null')
    type_valid = policy_type and policy_type.lower() not in ('unknown', '', 'n/a', 'na', 'none', 'null')
    coverage_valid = coverage and float(coverage) > 0

    # At least provider OR type must be valid for policy to be shown
    return provider_valid or type_valid or coverage_valid


def filter_valid_policies(policies: list) -> list:
    """Filter out invalid/empty policies that have no meaningful data."""
    if not policies:
        return []
    valid = [p for p in policies if is_valid_policy(p)]
    filtered_count = len(policies) - len(valid)
    if filtered_count > 0:
        logger.info(f"📋 Filtered out {filtered_count} invalid/empty policies")
    return valid


def get_policy_quick_list(policies_data: list) -> list:
    """Get a quick list of policies for API response"""
    policy_list = []

    for policy in policies_data:
        extracted = policy.get('extractedData', {})
        policy_list.append({
            "policyId": policy.get('analysisId', ''),
            "provider": extracted.get('insuranceProvider', 'Unknown'),
            "policyType": extracted.get('policyType', 'Unknown'),
            "coverage": extracted.get('coverageAmount', 0) or extracted.get('sumAssured', 0),
            "protectionScore": policy.get('protectionScore', 0)
        })

    return policy_list


def get_policy_selection_buttons(policies_data: list, language: str = 'en') -> list:
    """Generate quick action buttons for each policy"""
    buttons = []

    for policy in policies_data[:5]:  # Limit to 5 buttons
        extracted = policy.get('extractedData', {})
        provider = extracted.get('insuranceProvider', 'Unknown')
        policy_type = extracted.get('policyType', 'Unknown')

        # Shorten provider name if too long
        short_provider = provider[:15] + '...' if len(provider) > 15 else provider

        buttons.append({
            "title": f"{short_provider} ({policy_type})",
            "action": "select_policy",
            "policyId": policy.get('analysisId', ''),
            "policyType": policy_type
        })

    # Add "View All" button
    buttons.append({
        "title": "View All Policies" if language == 'en' else "सभी देखें",
        "action": "view_policies",
        "redirect": True,
        "redirect_page": "my_policies"
    })

    return buttons


def detect_policy_type_in_query(query: str) -> str:
    """
    Detect if user is asking about a specific policy type.

    Returns:
        str: Policy type name or None if not detected
    """
    query_lower = query.lower()

    type_patterns = {
        'health': ['health', 'medical', 'mediclaim', 'hospital', 'swasthya', 'sehat'],
        'life': ['life', 'term', 'jeevan', 'life insurance', 'term plan'],
        'motor': ['motor', 'car', 'bike', 'vehicle', 'auto', 'gaadi', 'gadi'],
        'travel': ['travel', 'yatra', 'safar'],
        'home': ['home', 'house', 'property', 'ghar', 'makan'],
        'critical_illness': ['critical', 'illness', 'cancer', 'heart', 'bimari'],
        'accident': ['accident', 'personal accident', 'pa', 'durghatna']
    }

    for policy_type, keywords in type_patterns.items():
        if any(kw in query_lower for kw in keywords):
            return policy_type

    return None


def detect_policy_id_in_query(query: str) -> Optional[str]:
    """
    Detect if user is asking about a specific policy by its analysisId.

    Matches patterns like:
    - ANL_282_7a0e7d8ac7a0
    - show details for policy ANL_123_abc
    - policy ANL_xxx

    Returns:
        str: Policy analysisId if detected, None otherwise
    """
    import re

    # Pattern for analysisId: ANL_number_alphanumeric
    # Examples: ANL_282_7a0e7d8ac7a0, ANL_123_abcdef
    pattern = r'ANL_\d+_[a-zA-Z0-9]+'

    match = re.search(pattern, query, re.IGNORECASE)
    if match:
        return match.group(0)

    return None


def find_policy_by_id(policies: list, policy_id: str) -> Optional[dict]:
    """
    Find a policy by its analysisId from a list of policies.

    Args:
        policies: List of policy documents
        policy_id: The analysisId to search for

    Returns:
        dict: Policy document if found, None otherwise
    """
    if not policies or not policy_id:
        return None

    for policy in policies:
        if policy.get('analysisId', '').lower() == policy_id.lower():
            return policy

    return None


def detect_provider_in_query(query: str) -> str:
    """
    Detect if user is asking about a specific insurance provider.

    Returns:
        str: Provider name or None if not detected
    """
    query_lower = query.lower()

    provider_patterns = {
        'hdfc': ['hdfc', 'hdfc ergo', 'hdfc life'],
        'icici': ['icici', 'icici lombard', 'icici prudential'],
        'lic': ['lic', 'life insurance corporation'],
        'sbi': ['sbi', 'sbi life', 'sbi general'],
        'max': ['max', 'max life', 'max bupa'],
        'bajaj': ['bajaj', 'bajaj allianz'],
        'tata': ['tata', 'tata aig', 'tata aia'],
        'star': ['star', 'star health'],
        'reliance': ['reliance', 'reliance general'],
        'new india': ['new india', 'niacl'],
        'aditya birla': ['aditya birla', 'abhi'],
        'kotak': ['kotak', 'kotak life', 'kotak mahindra'],
        'care': ['care', 'care health', 'religare'],
        'niva bupa': ['niva', 'bupa', 'niva bupa']
    }

    for provider, keywords in provider_patterns.items():
        if any(kw in query_lower for kw in keywords):
            return provider

    return None


def is_general_policy_question(query: str) -> bool:
    """
    Check if the query is a general/navigation question about policies that should
    trigger the Self/Family selection flow.

    Returns:
        bool: True if it's a navigation question (show list)
        bool: False if it's a specific question (needs AI answer)
    """
    query_lower = query.lower()

    # FIRST: Check if this is a SPECIFIC question that needs AI answer
    # These should NOT trigger list navigation, but should go to AI response
    specific_question_patterns = [
        # Gap-related questions
        'how many gap', 'what are my gap', 'what gap', 'coverage gap',
        'tell me about gap', 'show gap', 'list gap', 'kitne gap',
        # Recommendation questions
        'what recommend', 'recommendation', 'suggest', 'advice',
        # Benefit/exclusion questions
        'what benefit', 'key benefit', 'what exclusion', 'not covered',
        'what is covered', 'coverage detail', 'kya cover',
        # Premium/amount questions
        'how much premium', 'premium amount', 'kitna premium',
        'coverage amount', 'sum assured', 'sum insured',
        # Expiry questions
        'when expir', 'expiry date', 'end date', 'validity', 'kab expire',
        # Status/Active questions
        'is my policy active', 'are my policies active', 'are all my policies active',
        'policy active', 'policies active', 'still active', 'still valid',
        'policy status', 'is it active', 'are they active',
        'policy expired', 'lapsed', 'inactive',
        'kya active hai', 'active hai kya', 'expire ho gayi',
        # Score questions
        'what is my protection', 'protection score kya', 'score kitna',
        # Comparison questions
        'compare', 'difference between', 'which is better',
        # Analysis/Review questions (locker context)
        'analyze', 'analysis', 'review my', 'audit',
        'review my locker', 'check my locker', 'locker policy',
        # Insurance-specific detail questions
        'room rent', 'deductible', 'co-pay', 'copay', 'copayment',
        'waiting period', 'cooling period', 'no claim bonus', 'ncb',
        'cashless', 'network hospital', 'maturity', 'surrender',
        'sub limit', 'sublimit', 'does it have', 'is there',
        'claim settlement', 'claim ratio', 'claim process',
        'does my', 'is my', 'will it', 'will my', 'can i claim',
        # Advisory/decision questions (follow-ups)
        'should', 'what to do', 'what can i do', 'what am i supposed',
        'buy new', 'buy a new', 'renew', 'upgrade', 'switch',
        'add on', 'addon', 'add-on', 'or just', 'or should',
        'kya karu', 'karna chahiye',
    ]

    if any(pattern in query_lower for pattern in specific_question_patterns):
        return False  # Not a general question - needs AI answer

    # Patterns that indicate NAVIGATION questions (show list/selection)
    navigation_patterns = [
        'my polic', 'meri polic', 'show polic', 'view polic', 'see polic',
        'list polic', 'display polic',
        'apni policy', 'apna policy', 'dikhao', 'dekho',
        'i have', 'do i have', 'what do i have'
    ]

    # Check if it's a navigation question
    if any(pattern in query_lower for pattern in navigation_patterns):
        return True

    # If user just said something very short related to policies (navigation)
    short_patterns = ['policies', 'policy', 'पॉलिसी', 'पालिसी']
    if len(query_lower.split()) <= 3 and any(p in query_lower for p in short_patterns):
        return True

    return False


def is_specific_policy_question(query: str) -> bool:
    """
    Check if the query is asking a specific question about policy details
    that requires AI-generated answer using policy data.

    Returns:
        bool: True if it's a specific question needing AI answer
    """
    query_lower = query.lower()

    # ===== EXCLUDE NAVIGATION QUERIES =====
    # These should be handled by the flow logic, not AI response
    navigation_patterns = [
        'show policies for',
        'show policy for',
        'policies for',
        'policy for',
        'view policies for',
        'view policy for',
        'show me policies',
        'show my policies',
        'view my policies',
        'dikha', 'dikhao',  # Hindi: show
    ]

    # If it's a navigation query (e.g., "show policies for brother"), don't treat as specific question
    if any(pattern in query_lower for pattern in navigation_patterns):
        return False

    specific_patterns = [
        # Gap-related
        'gap', 'gaps', 'missing', 'lack',
        # Recommendations
        'recommend', 'suggestion', 'advice', 'should i',
        # Benefits/Exclusions
        'benefit', 'exclusion', 'not covered', 'covered', 'include',
        # Amounts
        'premium', 'amount', 'cost', 'price', 'sum assured', 'sum insured',
        # Dates
        'expir', 'validity', 'start date', 'end date', 'renew',
        # Status/Active queries
        'active', 'inactive', 'status', 'lapsed', 'still valid', 'still active',
        'is it active', 'are they active',
        # Score
        'score', 'rating', 'grade',
        # Details
        'detail', 'information', 'about my', 'tell me',
        # Comparison
        'compare', 'vs', 'versus', 'better',
        # Review/Check existing (locker context)
        'review', 'locker',
        # ===== INSURANCE-SPECIFIC TERMS =====
        # Room rent / Sub-limits
        'room rent', 'limit', 'sub limit', 'sublimit', 'sub-limit',
        'capping', 'cap on', 'maximum', 'minimum',
        # Co-pay / Deductible
        'deductible', 'co-pay', 'copay', 'co pay', 'copayment', 'co-payment',
        # Waiting period / Cooling period
        'waiting period', 'cooling period', 'lock-in', 'lockin', 'lock in',
        # No Claim Bonus / Cashless
        'no claim bonus', 'ncb', 'cashless', 'network hospital',
        # Maturity / Surrender
        'maturity', 'surrender', 'paid up', 'paid-up',
        # Claim related
        'claim settlement', 'claim ratio', 'claim process', 'how to claim',
        # Does it have / Is there type questions
        'does it have', 'does it cover', 'is there', 'do i have', 'can i get', 'can i claim',
        'does my', 'is my', 'will it', 'will my', 'it cover',
        # ===== PERSONAL INFORMATION QUERIES =====
        # Name queries
        'name', 'naam', 'who is', 'whose',
        # Family member queries (for questions like "who is covered by brother's policy")
        # NOTE: These are for QUESTIONS about family, not navigation
        # 'brother', 'sister', etc. are handled by flow logic when combined with navigation
        # Nominee queries
        'nominee', 'beneficiary', 'heir',
        # Contact/Address queries
        'phone', 'mobile', 'contact', 'email', 'address',
        # Age/DOB queries
        'age', 'old', 'date of birth', 'dob', 'birthday', 'umar',
        # Policyholder queries
        'holder', 'owner', 'insured', 'proposer',
        # Who is covered
        'who is covered', 'covered member', 'insured member',
        # Hindi personal queries
        'kitna', 'kitne', 'kya hai', 'kab', 'kaun', 'kiska', 'kiski',
        'kon hai', 'naam kya', 'naam batao',
        # ===== ADVISORY / DECISION QUESTIONS =====
        # Follow-up questions asking for guidance on what to do with a policy
        'should', 'what to do', 'what can i do', 'what am i supposed',
        'buy new', 'buy a new', 'get new', 'get a new',
        'renew it', 'renew the', 'renew my',
        'upgrade', 'switch to', 'change to', 'replace',
        'add on', 'addon', 'add-on', 'rider',
        'keep it', 'cancel it', 'continue with', 'stop it',
        'worth it', 'good enough', 'sufficient',
        'or just', 'or should', 'instead of',
        'what happens if', 'what if',
        # Hindi advisory
        'kya karu', 'kya karun', 'karna chahiye', 'kaisa karu',
    ]

    return any(pattern in query_lower for pattern in specific_patterns)


def filter_policies_by_type_or_provider(policies: list, policy_type: str = None, provider: str = None) -> list:
    """
    Filter policies by type and/or provider.

    Args:
        policies: List of policy documents
        policy_type: Policy type to filter by (e.g., 'health', 'life')
        provider: Provider name to filter by (e.g., 'hdfc', 'icici')

    Returns:
        list: Filtered policies
    """
    if not policies:
        return []

    if not policy_type and not provider:
        return []

    filtered = []

    for policy in policies:
        extracted = policy.get('extractedData', {})
        p_type = extracted.get('policyType', '').lower()
        p_provider = extracted.get('insuranceProvider', '').lower()

        type_match = True
        provider_match = True

        if policy_type:
            type_match = policy_type.lower() in p_type

        if provider:
            provider_match = provider.lower() in p_provider

        if type_match and provider_match:
            filtered.append(policy)

    return filtered


async def show_policy_details(policy: dict, query: str, language: str = 'en') -> dict:
    """
    Show detailed information about a specific policy.

    Args:
        policy: Policy document from MongoDB
        query: Original user query (to tailor response)
        language: 'en' or 'hi'

    Returns:
        dict: Response with policy details and structured data for frontend rendering
    """
    try:
        extracted = policy.get('extractedData', {})
        gap_analysis = policy.get('gapAnalysis', [])
        protection_score = policy.get('protectionScore', 0)
        summary = policy.get('summary', {})

        # Extract details
        provider = extracted.get('insuranceProvider', 'Unknown')
        policy_type = extracted.get('policyType', 'Unknown')
        policy_number = extracted.get('policyNumber', 'N/A')
        coverage = extracted.get('coverageAmount', 0) or extracted.get('sumAssured', 0)
        premium = extracted.get('premium', 0) or extracted.get('premiumAmount', 0)
        key_benefits = extracted.get('keyBenefits', [])
        exclusions = extracted.get('exclusions', [])
        start_date = extracted.get('policyStartDate', '') or extracted.get('startDate', 'N/A')
        end_date = extracted.get('policyEndDate', '') or extracted.get('endDate', 'N/A')

        # Count high severity gaps
        high_gaps = [g for g in gap_analysis if g.get('severity', '').lower() == 'high']

        # Build a clean text response (for display)
        if language == 'en':
            clean_msg = f"{provider} - {policy_type}"
        else:
            clean_msg = f"{provider} - {policy_type}"

        # Format coverage and premium for display
        formatted_coverage = f"₹{coverage:,.0f}" if coverage else "N/A"
        formatted_premium = f"₹{premium:,.0f}" if premium else "N/A"
        formatted_validity = f"{start_date} to {end_date}" if start_date and end_date else "N/A"

        return {
            "response": clean_msg,
            "action": "policy_query",
            "has_policies": True,
            "flow_step": "show_policy_details",
            "policy_id": policy.get('analysisId', ''),
            # Comprehensive structured data for frontend rendering
            "policy_data": {
                "provider": provider,
                "policyType": policy_type,
                "policyNumber": policy_number,
                "coverage": coverage,
                "formattedCoverage": formatted_coverage,
                "premium": premium,
                "formattedPremium": formatted_premium,
                "startDate": start_date,
                "endDate": end_date,
                "formattedValidity": formatted_validity,
                "protectionScore": protection_score,
                "keyBenefits": key_benefits[:5] if key_benefits else [],
                "exclusions": exclusions[:3] if exclusions else [],
                "gapCount": len(gap_analysis),
                "highGapCount": len(high_gaps),
                "analysisId": policy.get('analysisId', '')
            },
            "quick_actions": [
                {
                    "title": "View All Benefits" if language == 'en' else "सभी लाभ देखें",
                    "action": "view_benefits",
                    "policyId": policy.get('analysisId', '')
                },
                {
                    "title": "Coverage Gaps" if language == 'en' else "कवरेज गैप",
                    "action": "view_gaps",
                    "policyId": policy.get('analysisId', '')
                },
                {
                    "title": "Back to Policies" if language == 'en' else "पॉलिसी सूची",
                    "action": "policy_query",
                    "query": "show my policies"
                }
            ]
        }
    except Exception as e:
        logger.error(f"Error showing policy details: {e}")
        return {
            "response": "Error fetching policy details." if language == 'en' else "पॉलिसी विवरण प्राप्त करने में त्रुटि।",
            "action": "policy_query",
            "error": str(e)
        }


async def show_policy_benefits(policy: dict, query: str, language: str = 'en') -> dict:
    """
    Show all benefits for a specific policy.

    Args:
        policy: Policy document from MongoDB
        query: Original user query
        language: 'en' or 'hi'

    Returns:
        dict: Response with policy benefits and structured data for frontend rendering
    """
    try:
        extracted = policy.get('extractedData', {})
        provider = extracted.get('insuranceProvider', 'Unknown')
        policy_type = extracted.get('policyType', 'Unknown')
        key_benefits = extracted.get('keyBenefits', [])
        coverage = extracted.get('coverageAmount', 0) or extracted.get('sumAssured', 0)
        policy_id = policy.get('analysisId', '')

        # Format coverage for display
        formatted_coverage = f"₹{coverage:,.0f}" if coverage else "N/A"

        # Build clean text response with individual benefits included
        if language == 'en':
            clean_msg = f"Benefits for {provider} - {policy_type}"
            no_benefits_msg = "No specific benefits information available for this policy."
            if key_benefits:
                clean_msg += f"\n\n**{len(key_benefits)} Benefits:**\n"
                for i, benefit in enumerate(key_benefits, 1):
                    if isinstance(benefit, dict):
                        benefit_text = benefit.get('name', benefit.get('title', benefit.get('benefit', str(benefit))))
                        benefit_desc = benefit.get('description', '')
                        clean_msg += f"  {i}. **{benefit_text}**"
                        if benefit_desc:
                            clean_msg += f" — {benefit_desc}"
                        clean_msg += "\n"
                    else:
                        clean_msg += f"  {i}. {benefit}\n"
        else:
            clean_msg = f"{provider} - {policy_type} के लाभ"
            no_benefits_msg = "इस पॉलिसी के लिए कोई विशिष्ट लाभ जानकारी उपलब्ध नहीं है।"
            if key_benefits:
                clean_msg += f"\n\n**{len(key_benefits)} लाभ:**\n"
                for i, benefit in enumerate(key_benefits, 1):
                    if isinstance(benefit, dict):
                        benefit_text = benefit.get('name', benefit.get('title', benefit.get('benefit', str(benefit))))
                        benefit_desc = benefit.get('description', '')
                        clean_msg += f"  {i}. **{benefit_text}**"
                        if benefit_desc:
                            clean_msg += f" — {benefit_desc}"
                        clean_msg += "\n"
                    else:
                        clean_msg += f"  {i}. {benefit}\n"

        # Normalize benefits to string array for consistent frontend rendering
        normalized_benefits = []
        for benefit in key_benefits:
            if isinstance(benefit, dict):
                benefit_text = benefit.get('name', benefit.get('title', benefit.get('benefit', str(benefit))))
                benefit_desc = benefit.get('description', '')
                if benefit_desc:
                    normalized_benefits.append(f"{benefit_text}: {benefit_desc}")
                else:
                    normalized_benefits.append(benefit_text)
            else:
                normalized_benefits.append(str(benefit))

        return {
            "response": clean_msg,
            "action": "policy_query",
            "has_policies": True,
            "flow_step": "show_policy_benefits",
            "policy_id": policy_id,
            # Structured data for frontend rendering
            "benefits_data": {
                "provider": provider,
                "policyType": policy_type,
                "coverage": coverage,
                "formattedCoverage": formatted_coverage,
                "benefits": normalized_benefits,
                "benefitsCount": len(normalized_benefits),
                "noBenefitsMessage": no_benefits_msg if not normalized_benefits else None
            },
            "quick_actions": [
                {
                    "title": "Coverage Gaps" if language == 'en' else "कवरेज गैप",
                    "action": "view_gaps",
                    "policyId": policy_id
                },
                {
                    "title": "Policy Details" if language == 'en' else "पॉलिसी विवरण",
                    "action": "show_policy_details",
                    "policyId": policy_id
                },
                {
                    "title": "Back to Policies" if language == 'en' else "पॉलिसी सूची",
                    "action": "policy_query",
                    "query": "show my policies"
                }
            ]
        }
    except Exception as e:
        logger.error(f"Error showing policy benefits: {e}")
        return {
            "response": "Error fetching policy benefits." if language == 'en' else "पॉलिसी लाभ प्राप्त करने में त्रुटि।",
            "action": "policy_query",
            "error": str(e)
        }


async def show_policy_gaps(policy: dict, query: str, language: str = 'en') -> dict:
    """
    Show coverage gaps for a specific policy.

    Args:
        policy: Policy document from MongoDB
        query: Original user query
        language: 'en' or 'hi'

    Returns:
        dict: Response with policy gaps and structured data for frontend rendering
    """
    try:
        extracted = policy.get('extractedData', {})
        provider = extracted.get('insuranceProvider', 'Unknown')
        policy_type = extracted.get('policyType', 'Unknown')
        gap_analysis = policy.get('gapAnalysis', [])
        protection_score = policy.get('protectionScore', 0)
        policy_id = policy.get('analysisId', '')

        # Categorize gaps by severity with full details
        high_gaps = []
        medium_gaps = []
        low_gaps = []

        for gap in gap_analysis:
            severity = gap.get('severity', '').lower()
            gap_item = {
                "gap": gap.get('title', gap.get('gap', gap.get('name', 'Unknown gap'))),
                "title": gap.get('title', gap.get('gap', gap.get('name', 'Unknown gap'))),
                "description": gap.get('description', ''),
                "severity": severity,
                "recommendation": gap.get('recommendation', ''),
                "type": gap.get('type', 'warning'),
                "icon": gap.get('icon', '')
            }
            if severity == 'high':
                high_gaps.append(gap_item)
            elif severity == 'medium':
                medium_gaps.append(gap_item)
            else:
                low_gaps.append(gap_item)

        # Clean text response
        if language == 'en':
            clean_msg = f"Coverage Gaps for {provider} - {policy_type}"
            no_gaps_msg = "No coverage gaps identified for this policy!"
        else:
            clean_msg = f"{provider} - {policy_type} के कवरेज गैप"
            no_gaps_msg = "इस पॉलिसी के लिए कोई कवरेज गैप नहीं पाया गया!"

        return {
            "response": clean_msg,
            "action": "policy_query",
            "has_policies": True,
            "flow_step": "show_policy_gaps",
            "policy_id": policy_id,
            # Structured data for frontend rendering
            "gaps_data": {
                "provider": provider,
                "policyType": policy_type,
                "protectionScore": protection_score,
                "totalGaps": len(gap_analysis),
                "highGaps": high_gaps,
                "mediumGaps": medium_gaps,
                "lowGaps": low_gaps,
                "highGapsCount": len(high_gaps),
                "mediumGapsCount": len(medium_gaps),
                "lowGapsCount": len(low_gaps),
                "noGapsMessage": no_gaps_msg if not gap_analysis else None
            },
            "quick_actions": [
                {
                    "title": "View Benefits" if language == 'en' else "लाभ देखें",
                    "action": "view_benefits",
                    "policyId": policy_id
                },
                {
                    "title": "Get Recommendations" if language == 'en' else "सिफारिशें पाएं",
                    "action": "view_recommendations",
                    "policyId": policy_id
                },
                {
                    "title": "Back to Policies" if language == 'en' else "पॉलिसी सूची",
                    "action": "policy_query",
                    "query": "show my policies"
                }
            ]
        }
    except Exception as e:
        logger.error(f"Error showing policy gaps: {e}")
        return {
            "response": "Error fetching coverage gaps." if language == 'en' else "कवरेज गैप प्राप्त करने में त्रुटि।",
            "action": "policy_query",
            "error": str(e)
        }


async def show_policy_recommendations(policy: dict, query: str, language: str = 'en') -> dict:
    """
    Show recommendations for a specific policy.

    Args:
        policy: Policy document from MongoDB
        query: Original user query
        language: 'en' or 'hi'

    Returns:
        dict: Response with policy recommendations
    """
    try:
        extracted = policy.get('extractedData', {})
        provider = extracted.get('insuranceProvider', 'Unknown')
        policy_type = extracted.get('policyType', 'Unknown')
        recommendations = policy.get('recommendations', [])
        gap_analysis = policy.get('gapAnalysis', [])
        protection_score = policy.get('protectionScore', 0)
        policy_id = policy.get('analysisId', '')

        # Build recommendations message
        if language == 'en':
            rec_msg = f"💡 **Recommendations for {provider} - {policy_type}**\n\n**Current Protection Score:** {protection_score}/100\n\n"
            if recommendations:
                rec_msg += "**Recommended Actions:**\n"
                for i, rec in enumerate(recommendations, 1):
                    if isinstance(rec, dict):
                        rec_text = rec.get('recommendation', rec.get('text', str(rec)))
                    else:
                        rec_text = str(rec)
                    rec_msg += f"  {i}. {rec_text}\n"
            else:
                if gap_analysis:
                    rec_msg += "**Based on your coverage gaps, we recommend:**\n"
                    # Sort by severity: high > medium > low
                    severity_order = {'high': 0, 'medium': 1, 'low': 2}
                    sorted_gaps = sorted(gap_analysis, key=lambda g: severity_order.get(g.get('severity', '').lower(), 3))
                    for i, gap in enumerate(sorted_gaps[:5], 1):
                        gap_name = gap.get('title', gap.get('gap', gap.get('name', 'Coverage issue')))
                        gap_desc = gap.get('description', '')
                        severity = gap.get('severity', 'Medium')
                        rec_msg += f"  {i}. **{gap_name}** ({severity})"
                        if gap_desc:
                            rec_msg += f" — {gap_desc}"
                        rec_msg += "\n"
                else:
                    rec_msg += "✅ Your policy looks comprehensive! No immediate recommendations.\n"
        else:
            rec_msg = f"💡 **{provider} - {policy_type} के लिए सिफारिशें**\n\n**वर्तमान सुरक्षा स्कोर:** {protection_score}/100\n\n"
            if recommendations:
                rec_msg += "**अनुशंसित कार्य:**\n"
                for i, rec in enumerate(recommendations, 1):
                    if isinstance(rec, dict):
                        rec_text = rec.get('recommendation', rec.get('text', str(rec)))
                    else:
                        rec_text = str(rec)
                    rec_msg += f"  {i}. {rec_text}\n"
            else:
                if gap_analysis:
                    rec_msg += "**आपके कवरेज गैप के आधार पर, हम सुझाव देते हैं:**\n"
                    severity_order = {'high': 0, 'medium': 1, 'low': 2}
                    sorted_gaps = sorted(gap_analysis, key=lambda g: severity_order.get(g.get('severity', '').lower(), 3))
                    for i, gap in enumerate(sorted_gaps[:5], 1):
                        gap_name = gap.get('title', gap.get('gap', gap.get('name', 'कवरेज समस्या')))
                        gap_desc = gap.get('description', '')
                        severity = gap.get('severity', 'Medium')
                        rec_msg += f"  {i}. **{gap_name}** ({severity})"
                        if gap_desc:
                            rec_msg += f" — {gap_desc}"
                        rec_msg += "\n"
                else:
                    rec_msg += "✅ आपकी पॉलिसी व्यापक दिखती है! कोई तत्काल सिफारिश नहीं।\n"

        # Build structured recommendations data for frontend
        recommendations_list = []
        if recommendations:
            for rec in recommendations:
                if isinstance(rec, dict):
                    recommendations_list.append({
                        "text": rec.get('recommendation', rec.get('text', str(rec))),
                        "priority": rec.get('priority', 'medium'),
                        "category": rec.get('category', 'general'),
                        "description": rec.get('description', '')
                    })
                else:
                    recommendations_list.append({
                        "text": str(rec),
                        "priority": "medium",
                        "category": "general",
                        "description": ""
                    })
        else:
            # Generate recommendations from ALL gaps (sorted by severity)
            if gap_analysis:
                severity_order = {'high': 0, 'medium': 1, 'low': 2}
                sorted_gaps = sorted(gap_analysis, key=lambda g: severity_order.get(g.get('severity', '').lower(), 3))
                for gap in sorted_gaps[:5]:
                    gap_name = gap.get('title', gap.get('gap', gap.get('name', 'Coverage issue')))
                    gap_desc = gap.get('description', '')
                    gap_severity = gap.get('severity', 'medium').lower()
                    gap_type = gap.get('type', 'warning')

                    # Map severity to priority
                    priority = gap_severity if gap_severity in ('high', 'medium', 'low') else 'medium'

                    # Build descriptive recommendation text
                    if gap_desc:
                        rec_text = f"{gap_name}: {gap_desc}" if language == 'en' else f"{gap_name}: {gap_desc}"
                    else:
                        rec_text = f"Consider adding coverage for: {gap_name}" if language == 'en' else f"इसके लिए कवरेज जोड़ने पर विचार करें: {gap_name}"

                    recommendations_list.append({
                        "text": rec_text,
                        "priority": priority,
                        "category": "coverage_gap",
                        "description": gap_desc,
                        "related_gap": gap_name,
                        "gap_type": gap_type
                    })

        recommendations_data = {
            "policyId": policy_id,
            "provider": provider,
            "policyType": policy_type,
            "protectionScore": protection_score,
            "recommendationsCount": len(recommendations_list),
            "recommendations": recommendations_list,
            "hasRecommendations": len(recommendations_list) > 0,
            "noRecommendationsMessage": "Your policy looks comprehensive! No immediate recommendations." if language == 'en' else "आपकी पॉलिसी व्यापक दिखती है! कोई तत्काल सिफारिश नहीं।"
        }

        return {
            "response": rec_msg,
            "action": "policy_query",
            "has_policies": True,
            "flow_step": "show_policy_recommendations",
            "policy_id": policy_id,
            "recommendations_count": len(recommendations_list),
            "protection_score": protection_score,
            "recommendations_data": recommendations_data,
            "quick_actions": [
                {
                    "title": "View Benefits" if language == 'en' else "लाभ देखें",
                    "action": "view_benefits",
                    "policyId": policy_id
                },
                {
                    "title": "Coverage Gaps" if language == 'en' else "कवरेज गैप",
                    "action": "view_gaps",
                    "policyId": policy_id
                },
                {
                    "title": "Back to Policies" if language == 'en' else "पॉलिसी सूची",
                    "action": "policy_query",
                    "query": "show my policies"
                }
            ]
        }
    except Exception as e:
        logger.error(f"Error showing policy recommendations: {e}")
        return {
            "response": "Error fetching recommendations." if language == 'en' else "सिफारिशें प्राप्त करने में त्रुटि।",
            "action": "policy_query",
            "error": str(e)
        }


def build_policy_list_message(policies: list, category: str, language: str = 'en') -> str:
    """
    Build a formatted message listing policies.

    Args:
        policies: List of policy documents
        category: 'self', 'family', member name, or 'filtered'
        language: 'en' or 'hi'

    Returns:
        str: Formatted policy list message
    """
    if not policies:
        return "No policies found." if language == 'en' else "कोई पॉलिसी नहीं मिली।"

    # Header based on category
    if category == 'self':
        header = f"📋 **Your Policies ({len(policies)}):**\n\n" if language == 'en' else f"📋 **आपकी पॉलिसी ({len(policies)}):**\n\n"
    elif category == 'family':
        header = f"👨‍👩‍👧‍👦 **Family Policies ({len(policies)}):**\n\n" if language == 'en' else f"👨‍👩‍👧‍👦 **परिवार की पॉलिसी ({len(policies)}):**\n\n"
    elif category == 'filtered':
        header = f"🔍 **Matching Policies ({len(policies)}):**\n\n" if language == 'en' else f"🔍 **मिलती पॉलिसी ({len(policies)}):**\n\n"
    else:
        # Family member name
        header = f"📋 **{category.title()}'s Policies ({len(policies)}):**\n\n" if language == 'en' else f"📋 **{category} की पॉलिसी ({len(policies)}):**\n\n"

    # Build list
    lines = []
    for i, policy in enumerate(policies, 1):
        extracted = policy.get('extractedData', {})
        provider = extracted.get('insuranceProvider', 'Unknown')
        policy_type = extracted.get('policyType', 'Unknown')
        coverage = extracted.get('coverageAmount', 0) or extracted.get('sumAssured', 0)
        score = policy.get('protectionScore', 0)

        if language == 'en':
            lines.append(f"{i}. **{provider}** - {policy_type}\n   Coverage: ₹{coverage:,.0f} | Score: {score}/100")
        else:
            lines.append(f"{i}. **{provider}** - {policy_type}\n   कवरेज: ₹{coverage:,.0f} | स्कोर: {score}/100")

    footer = "\n\nSelect a policy to see details." if language == 'en' else "\n\nविवरण देखने के लिए पॉलिसी चुनें।"

    return header + "\n".join(lines) + footer


def group_policies_by_family_member(family_policies: list) -> dict:
    """
    Group family policies by relationship/member.

    Args:
        family_policies: List of family policy documents

    Returns:
        dict: {member_name: [policies]}
    """
    grouped = {}

    for policy in family_policies:
        relationship = get_policy_relationship(policy)
        member_name = policy.get('familyMemberName', '') or relationship

        # Use relationship as key
        key = relationship or 'Other'

        if key not in grouped:
            grouped[key] = []
        grouped[key].append(policy)

    return grouped


def build_family_members_list_message(family_members: dict, language: str = 'en') -> str:
    """
    Build a message listing family members with their policy counts.

    Args:
        family_members: dict from group_policies_by_family_member()
        language: 'en' or 'hi'

    Returns:
        str: Formatted family members list
    """
    if not family_members:
        return "No family policies found." if language == 'en' else "परिवार की कोई पॉलिसी नहीं मिली।"

    if language == 'en':
        header = "👨‍👩‍👧‍👦 **Family Members with Policies:**\n\n"
        footer = "\n\nSelect a family member to see their policies."
    else:
        header = "👨‍👩‍👧‍👦 **पॉलिसी वाले परिवार के सदस्य:**\n\n"
        footer = "\n\nउनकी पॉलिसी देखने के लिए परिवार के सदस्य को चुनें।"

    lines = []
    member_icons = {
        'spouse': '💑',
        'wife': '👩',
        'husband': '👨',
        'son': '👦',
        'daughter': '👧',
        'father': '👴',
        'mother': '👵',
        'brother': '👨',
        'sister': '👩',
        'friend': '👤',
        'relative': '👤',
        'other': '👤'
    }

    for i, (member, policies) in enumerate(family_members.items(), 1):
        icon = member_icons.get(member.lower(), '👤')
        count = len(policies)

        # Get total coverage for this member
        total_coverage = sum(
            p.get('extractedData', {}).get('coverageAmount', 0) or
            p.get('extractedData', {}).get('sumAssured', 0)
            for p in policies
        )

        if language == 'en':
            lines.append(f"{i}. {icon} **{member.title()}** - {count} policy(ies)\n   Total Coverage: ₹{total_coverage:,.0f}")
        else:
            lines.append(f"{i}. {icon} **{member.title()}** - {count} पॉलिसी\n   कुल कवरेज: ₹{total_coverage:,.0f}")

    return header + "\n".join(lines) + footer


def get_family_member_buttons(family_members: dict, language: str = 'en') -> list:
    """
    Generate quick action buttons for each family member.

    Args:
        family_members: dict from group_policies_by_family_member()
        language: 'en' or 'hi'

    Returns:
        list: Quick action buttons
    """
    buttons = []

    for member, policies in family_members.items():
        count = len(policies)
        buttons.append({
            "title": f"{member.title()} ({count})" if language == 'en' else f"{member.title()} ({count})",
            "action": "select_family_member",
            "member": member,
            "query": f"show {member} policies"
        })

    # Add back button
    buttons.append({
        "title": "Back" if language == 'en' else "वापस",
        "action": "policy_query",
        "query": "show my policies"
    })

    return buttons


def get_policy_relationship(policy: dict) -> str:
    """
    Get the relationship/member type from a policy document.
    Normalizes various field names and values to a standard set.

    Args:
        policy: Policy document from MongoDB

    Returns:
        str: Normalized relationship name (e.g., 'spouse', 'son', 'daughter')
    """
    # Standard relationship mapping for normalization
    RELATIONSHIP_ALIASES = {
        # Spouse variants
        'spouse': 'spouse', 'wife': 'spouse', 'husband': 'spouse',
        'pati': 'spouse', 'patni': 'spouse', 'biwi': 'spouse',
        # Son variants
        'son': 'son', 'beta': 'son', 'boy': 'son', 'male child': 'son',
        # Daughter variants
        'daughter': 'daughter', 'beti': 'daughter', 'girl': 'daughter', 'female child': 'daughter',
        # Father variants
        'father': 'father', 'papa': 'father', 'dad': 'father',
        'pita': 'father', 'pitaji': 'father', 'baap': 'father',
        # Mother variants
        'mother': 'mother', 'mummy': 'mother', 'mom': 'mother',
        'mata': 'mother', 'mataji': 'mother', 'maa': 'mother', 'ma': 'mother',
        # Brother variants
        'brother': 'brother', 'bhai': 'brother', 'bhaiya': 'brother',
        # Sister variants
        'sister': 'sister', 'behen': 'sister', 'behan': 'sister', 'didi': 'sister',
        # Parent-in-law
        'father-in-law': 'father-in-law', 'sasur': 'father-in-law',
        'mother-in-law': 'mother-in-law', 'saas': 'mother-in-law',
        # Friend / Relative / Other
        'friend': 'friend', 'dost': 'friend', 'mitra': 'friend',
        'relative': 'relative', 'rishtedar': 'relative',
        'other': 'other',
        # Self
        'self': 'self', 'myself': 'self', 'me': 'self', 'khud': 'self',
    }

    def normalize_relationship(value: str) -> str:
        """Normalize relationship value to standard form"""
        if not value:
            return ''
        value_lower = value.lower().strip()
        return RELATIONSHIP_ALIASES.get(value_lower, value.title())

    # Check various possible fields in order of priority
    fields_to_check = [
        # Root level fields
        ('relationship', policy),
        ('familyRelation', policy),
        ('memberRelation', policy),
        ('policyFor', policy),  # Sometimes 'self' or 'family' stored here
        ('familyMemberRelation', policy),
        # Nested in extractedData
        ('relationship', policy.get('extractedData', {})),
        ('insuredRelation', policy.get('extractedData', {})),
        ('nomineeRelation', policy.get('extractedData', {})),
        ('memberType', policy.get('extractedData', {})),
        # Nested in policyHolder
        ('relationship', policy.get('policyHolder', {})),
    ]

    for field_name, source in fields_to_check:
        value = source.get(field_name, '') if isinstance(source, dict) else ''
        if value and isinstance(value, str) and value.strip():
            normalized = normalize_relationship(value)
            if normalized and normalized.lower() != 'family':  # 'family' is not a specific relationship
                return normalized

    # Check familyMemberName as last resort
    member_name = policy.get('familyMemberName', '')
    if member_name and isinstance(member_name, str) and member_name.strip():
        # Try to extract relationship from member name if it contains known keywords
        member_lower = member_name.lower()
        for alias, standard in RELATIONSHIP_ALIASES.items():
            if alias in member_lower:
                return standard.title()
        return member_name.strip().title()

    return 'Other'


# ============= POLICY QUERY FLOW STATE MANAGEMENT =============

def get_policy_query_state(session_id: str) -> dict:
    """
    Get the current policy query flow state from Redis.

    Args:
        session_id: Chat session ID

    Returns:
        dict: Flow state with keys like 'flow_step', 'selected_for', 'selected_member'
    """
    try:
        state_key = f"policy_query_state:{session_id}"
        state_data = get_session(state_key)
        if state_data:
            return state_data
        return {}
    except Exception as e:
        logger.error(f"Error getting policy query state: {e}")
        return {}


def store_policy_query_state(session_id: str, state: dict, expire_seconds: int = 3600) -> bool:
    """
    Store policy query flow state in Redis.

    Args:
        session_id: Chat session ID
        state: Flow state dict
        expire_seconds: TTL for state (default 1 hour)

    Returns:
        bool: Success status
    """
    try:
        state_key = f"policy_query_state:{session_id}"
        state['updated_at'] = datetime.now().isoformat()
        store_session(state_key, state, expire_seconds=expire_seconds)
        logger.info(f"📋 Stored policy query state for {session_id}: {state.get('flow_step', 'unknown')}")
        return True
    except Exception as e:
        logger.error(f"Error storing policy query state: {e}")
        return False


def clear_policy_query_state(session_id: str) -> bool:
    """
    Clear policy query flow state from Redis.

    Args:
        session_id: Chat session ID

    Returns:
        bool: Success status
    """
    try:
        state_key = f"policy_query_state:{session_id}"
        delete_session(state_key)
        logger.info(f"🗑️ Cleared policy query state for {session_id}")
        return True
    except Exception as e:
        logger.error(f"Error clearing policy query state: {e}")
        return False

# ============= END POLICY QUERY FLOW STATE MANAGEMENT =============


async def handle_policy_query(user_id: str, query: str, language: str = 'en', context: dict = None, session_id: str = None, conversation_history: list = None) -> dict:
    """
    Handle user questions about their uploaded policies with conversational flow.
    Uses Redis-based session state to maintain flow context across messages.

    Flow:
    1. First ask: Self or Family?
    2. If Self: Show self policies list
    3. If Family: Show family members list → then show that member's policies
    4. After policy selection: Show policy details

    Args:
        user_id: User ID
        query: User's question about their policies
        language: 'en' or 'hi'
        context: Conversation context (legacy - now uses Redis state)
        session_id: Chat session ID for Redis state persistence
        conversation_history: Recent conversation messages for context (helps identify which policy user is referring to)

    Returns:
        dict with response, policy data, and quick actions
    """
    try:
        logger.info(f"📋 POLICY QUERY: user_id={user_id}, query='{query}', session_id={session_id}")

        query_lower = query.lower().strip()

        # ===== LOAD FLOW STATE FROM REDIS =====
        flow_state = {}
        if session_id:
            flow_state = get_policy_query_state(session_id)
            logger.info(f"📋 Loaded flow state: {flow_state}")

        # Merge legacy context with flow state (flow state takes priority)
        if context:
            for key, value in context.items():
                if key not in flow_state:
                    flow_state[key] = value

        # ===== CHECK FOR FLOW RESET KEYWORDS =====
        # Reset flow state when user wants to go back to policy list or start fresh
        reset_keywords = ['start over', 'reset', 'back to start', 'main menu', 'नए सिरे से', 'वापस', 'back to policies', 'show my policies', 'view my policies', 'my policies']
        if any(kw in query_lower for kw in reset_keywords):
            if session_id:
                clear_policy_query_state(session_id)
            flow_state = {}
            logger.info("📋 Flow state reset by user request")

        # Fetch ALL policies (both self and family)
        self_policies = fetch_user_policies_from_mongodb(str(user_id), policy_for="self")
        family_policies = fetch_user_policies_from_mongodb(str(user_id), policy_for="family")

        # Filter out invalid/empty policies (no provider, no type, no coverage)
        self_policies = filter_valid_policies(self_policies or [])
        family_policies = filter_valid_policies(family_policies or [])

        total_self = len(self_policies)
        total_family = len(family_policies)
        total_policies = total_self + total_family

        logger.info(f"📋 POLICY QUERY: Found {total_self} self policies, {total_family} family policies")

        # Helper function to save state and return response
        def save_state_and_return(response_dict: dict, new_state: dict) -> dict:
            """Save flow state to Redis and return response"""
            if session_id:
                # Preserve important state across steps
                merged_state = {**flow_state, **new_state}
                store_policy_query_state(session_id, merged_state)
            return response_dict

        # ===== STEP 0: No policies at all =====
        if total_policies == 0:
            if session_id:
                clear_policy_query_state(session_id)

            no_policy_msg = (
                "You haven't uploaded any insurance policies yet. "
                "Would you like to add your first policy for analysis?"
            ) if language == 'en' else (
                "आपने अभी तक कोई बीमा पॉलिसी अपलोड नहीं की है। "
                "क्या आप विश्लेषण के लिए अपनी पहली पॉलिसी जोड़ना चाहेंगे?"
            )

            return {
                "response": no_policy_msg,
                "action": "policy_query",
                "has_policies": False,
                "policy_count": 0,
                "flow_step": "no_policies",
                "quick_actions": [
                    {
                        "title": "Add Policy" if language == 'en' else "पॉलिसी जोड़ें",
                        "action": "add_policy",
                        "redirect": True,
                        "redirect_page": "add_policy"
                    }
                ]
            }

        # ===== DETECT USER SELECTIONS FROM QUERY =====
        # Check if user selected "Self" or "Family"
        is_self_selected = any(kw in query_lower for kw in ['self', 'myself', 'my own', 'mine', 'apna', 'apni', 'mera', 'meri', 'khud'])
        is_family_selected = any(kw in query_lower for kw in ['family', 'parivar', 'member', 'child', 'parent', 'biwi', 'pati', 'beta', 'beti', 'papa', 'mummy', 'mata', 'pita'])

        # Check for specific family member keywords (more specific, excludes generic family keyword)
        family_member_keywords = {
            'spouse': ['spouse', 'wife', 'husband', 'pati', 'patni', 'biwi'],
            'son': ['son', 'beta', 'boy'],
            'daughter': ['daughter', 'beti', 'girl'],
            'father': ['father', 'papa', 'dad', 'pita', 'pitaji'],
            'mother': ['mother', 'mummy', 'mom', 'mata', 'mataji', 'maa'],
            'brother': ['brother', 'bhai'],
            'sister': ['sister', 'behen', 'behan'],
            'father-in-law': ['father-in-law', 'sasur'],
            'mother-in-law': ['mother-in-law', 'saas'],
            'friend': ['friend'],
            'relative': ['relative'],
            'other': ['other']
        }

        selected_member = None
        for member, keywords in family_member_keywords.items():
            if any(kw in query_lower for kw in keywords):
                selected_member = member
                is_family_selected = True  # Selecting a member implies family
                break

        # ===== USE FLOW STATE FOR CONTEXT =====
        # If we have a previous selection in flow state and user didn't override
        if not is_self_selected and not is_family_selected and not selected_member:
            if flow_state.get('selected_for') == 'self':
                is_self_selected = True
                logger.info("📋 Using saved state: selected_for=self")
            elif flow_state.get('selected_for') == 'family':
                is_family_selected = True
                logger.info("📋 Using saved state: selected_for=family")

            if flow_state.get('selected_member'):
                selected_member = flow_state.get('selected_member')
                is_family_selected = True
                logger.info(f"📋 Using saved state: selected_member={selected_member}")

        # Check if user selected a specific policy type/provider
        selected_policy_type = detect_policy_type_in_query(query_lower)
        selected_provider = detect_provider_in_query(query_lower)

        # ===== CHECK FOR SPECIFIC POLICY BY ID =====
        # Detect if user is asking about a specific policy by its analysisId
        # Examples: "Show details for policy ANL_282_7a0e7d8ac7a0"
        #           "show all benefits for policy ANL_282_xxx"
        #           "show coverage gaps for policy ANL_282_xxx"
        detected_policy_id = detect_policy_id_in_query(query)
        if detected_policy_id:
            logger.info(f"📋 FLOW: Detected policy ID in query: {detected_policy_id}")

            # Search for policy in all user's policies
            all_policies = (self_policies or []) + (family_policies or [])
            found_policy = find_policy_by_id(all_policies, detected_policy_id)

            if found_policy:
                # Determine what type of information user is asking for
                if 'benefit' in query_lower:
                    logger.info(f"📋 FLOW: Found policy by ID, showing benefits")
                    return await show_policy_benefits(found_policy, query, language)
                elif 'gap' in query_lower:
                    logger.info(f"📋 FLOW: Found policy by ID, showing gaps")
                    return await show_policy_gaps(found_policy, query, language)
                elif 'recommend' in query_lower:
                    logger.info(f"📋 FLOW: Found policy by ID, showing recommendations")
                    return await show_policy_recommendations(found_policy, query, language)
                else:
                    logger.info(f"📋 FLOW: Found policy by ID, showing details")
                    # Save state before showing policy details
                    if session_id:
                        store_policy_query_state(session_id, {
                            "flow_step": "show_policy_details",
                            "selected_policy_id": detected_policy_id
                        })
                    return await show_policy_details(found_policy, query, language)
            else:
                # Policy ID detected but not found in user's policies
                logger.warning(f"📋 FLOW: Policy ID {detected_policy_id} not found in user's policies")
                not_found_msg = (
                    f"I couldn't find a policy with ID '{detected_policy_id}' in your portfolio. "
                    "Please select a policy from your list below."
                ) if language == 'en' else (
                    f"मुझे आपके पोर्टफोलियो में ID '{detected_policy_id}' वाली पॉलिसी नहीं मिली। "
                    "कृपया नीचे दी गई सूची से एक पॉलिसी चुनें।"
                )

                # Build quick actions to show available policies
                quick_actions = []
                if total_self > 0:
                    quick_actions.append({"title": f"Self Policies ({total_self})", "action": "policy_query_self", "query": "show self policies"})
                if total_family > 0:
                    quick_actions.append({"title": f"Family Policies ({total_family})", "action": "policy_query_family", "query": "show family policies"})

                return save_state_and_return({
                    "response": not_found_msg,
                    "action": "policy_query",
                    "has_policies": True,
                    "policy_count": total_policies,
                    "flow_step": "policy_not_found",
                    "quick_actions": quick_actions
                }, {
                    "flow_step": "policy_not_found",
                    "attempted_policy_id": detected_policy_id
                })

        # ===== FLOW LOGIC =====
        logger.info(f"📋 FLOW DEBUG: total_self={total_self}, total_family={total_family}, is_self_selected={is_self_selected}, is_family_selected={is_family_selected}, selected_member={selected_member}")

        # ===== STEP 0: Check if this is a SPECIFIC QUESTION that needs AI answer =====
        # Questions like "how many gaps", "what are my benefits", "tell me about exclusions"
        # should be answered using AI with policy data, not navigation flow
        if is_specific_policy_question(query_lower) and total_policies > 0:
            logger.info(f"📋 FLOW: Detected SPECIFIC QUESTION - routing to AI response")

            # Get all policies for context
            all_policies = (self_policies or []) + (family_policies or [])
            policy_summary = build_policy_summary_for_ai(all_policies)
            ai_response = generate_policy_query_response(query, policy_summary, language, conversation_history=conversation_history)

            # Build quick actions
            quick_actions = []
            if total_self > 0:
                quick_actions.append({"title": "View Self Policies", "action": "policy_query_self", "query": "show self policies"})
            if total_family > 0:
                quick_actions.append({"title": "View Family Policies", "action": "policy_query_family", "query": "show family policies"})
            quick_actions.append({"title": "Add Policy", "action": "add_policy", "redirect": True, "redirect_page": "add_policy"})

            return save_state_and_return({
                "response": ai_response,
                "action": "policy_query",
                "has_policies": True,
                "policy_count": total_policies,
                "self_count": total_self,
                "family_count": total_family,
                "flow_step": "specific_question_answer",
                "portfolio_overview": build_portfolio_overview(all_policies),
                "quick_actions": quick_actions
            }, {
                "flow_step": "specific_question_answer",
                "last_question": query
            })

        # ===== STEP 0B: Conversation follow-up detection =====
        # If the previous interaction was a specific AI answer about policies (e.g., discussing
        # an expired policy) and user asks a follow-up question (not a navigation/list request),
        # continue with AI response for conversational continuity.
        # Example: User asked "my policy expired what to do?" → AI answered →
        #   User says "should I add add-ons or buy new?" → should get AI answer, not list navigation.
        ai_continuation_steps = {
            'specific_question_answer', 'show_policy_details',
            'show_policy_benefits', 'show_policy_gaps', 'show_policy_recommendations'
        }
        if (flow_state.get('flow_step') in ai_continuation_steps
                and not is_general_policy_question(query_lower)
                and total_policies > 0):
            logger.info(f"📋 FLOW: Detected follow-up to previous policy discussion (prev_step={flow_state.get('flow_step')}) - routing to AI response")

            all_policies = (self_policies or []) + (family_policies or [])
            policy_summary = build_policy_summary_for_ai(all_policies)
            ai_response = generate_policy_query_response(query, policy_summary, language, conversation_history=conversation_history)

            quick_actions = []
            if total_self > 0:
                quick_actions.append({"title": "View Self Policies", "action": "policy_query_self", "query": "show self policies"})
            if total_family > 0:
                quick_actions.append({"title": "View Family Policies", "action": "policy_query_family", "query": "show family policies"})
            quick_actions.append({"title": "Add Policy", "action": "add_policy", "redirect": True, "redirect_page": "add_policy"})

            return save_state_and_return({
                "response": ai_response,
                "action": "policy_query",
                "has_policies": True,
                "policy_count": total_policies,
                "self_count": total_self,
                "family_count": total_family,
                "flow_step": "specific_question_answer",
                "portfolio_overview": build_portfolio_overview(all_policies),
                "quick_actions": quick_actions
            }, {
                "flow_step": "specific_question_answer",
                "last_question": query
            })

        # STEP 1: Initial query - Ask Self or Family (if both exist)
        if total_self > 0 and total_family > 0 and not is_self_selected and not is_family_selected and not selected_member:
            # Check if user is asking a general question
            if is_general_policy_question(query_lower):
                logger.info("📋 FLOW: Triggering ask_self_or_family (both self and family exist)")
                ask_msg = (
                    f"You have {total_self} policy(ies) for yourself and {total_family} policy(ies) for family members.\n\n"
                    "Would you like to see policies for **yourself** or your **family members**?"
                ) if language == 'en' else (
                    f"आपके पास अपने लिए {total_self} पॉलिसी और परिवार के सदस्यों के लिए {total_family} पॉलिसी हैं।\n\n"
                    "आप **अपनी** पॉलिसी देखना चाहेंगे या **परिवार** की?"
                )

                return save_state_and_return({
                    "response": ask_msg,
                    "action": "policy_query",
                    "has_policies": True,
                    "policy_count": total_policies,
                    "self_count": total_self,
                    "family_count": total_family,
                    "flow_step": "ask_self_or_family",
                    "quick_actions": [
                        {
                            "title": f"Self ({total_self})" if language == 'en' else f"खुद ({total_self})",
                            "action": "policy_query_self",
                            "query": "show my self policies"
                        },
                        {
                            "title": f"Family ({total_family})" if language == 'en' else f"परिवार ({total_family})",
                            "action": "policy_query_family",
                            "query": "show my family policies"
                        }
                    ]
                }, {
                    "flow_step": "ask_self_or_family",
                    "total_self": total_self,
                    "total_family": total_family
                })

        # STEP 2A: User selected "Self" OR user only has self policies - Show self policies list
        if is_self_selected or (total_self > 0 and total_family == 0):
            logger.info(f"📋 FLOW: Triggering show_self_policies (is_self_selected={is_self_selected}, only_self={total_self > 0 and total_family == 0})")
            policies_to_show = self_policies

            if len(policies_to_show) == 0:
                quick_actions = [
                    {"title": "Add Policy", "action": "add_policy", "redirect": True, "redirect_page": "add_policy"}
                ]
                if total_family > 0:
                    quick_actions.append({"title": "View Family Policies", "action": "policy_query_family", "query": "show family policies"})

                return save_state_and_return({
                    "response": "You don't have any policies uploaded for yourself." if language == 'en' else "आपके पास अपने लिए कोई पॉलिसी अपलोड नहीं है।",
                    "action": "policy_query",
                    "flow_step": "no_self_policies",
                    "quick_actions": [a for a in quick_actions if a]
                }, {
                    "flow_step": "no_self_policies",
                    "selected_for": "self"
                })

            # Check if user is asking about a specific policy
            filtered_policies = filter_policies_by_type_or_provider(policies_to_show, selected_policy_type, selected_provider)

            if filtered_policies and len(filtered_policies) == 1:
                # Show details of the specific policy - save state first
                if session_id:
                    store_policy_query_state(session_id, {
                        "flow_step": "show_policy_details",
                        "selected_for": "self",
                        "selected_policy_id": filtered_policies[0].get('analysisId', '')
                    })
                return await show_policy_details(filtered_policies[0], query, language)

            if filtered_policies and len(filtered_policies) < len(policies_to_show):
                policies_to_show = filtered_policies

            # Show list of self policies
            policy_list_msg = build_policy_list_message(policies_to_show, "self", language)

            return save_state_and_return({
                "response": policy_list_msg,
                "action": "policy_query",
                "has_policies": True,
                "policy_count": len(policies_to_show),
                "flow_step": "show_self_policies",
                "policies": get_policy_quick_list(policies_to_show),
                "quick_actions": get_policy_selection_buttons(policies_to_show, language)
            }, {
                "flow_step": "show_self_policies",
                "selected_for": "self"
            })

        # STEP 2B: User selected "Family" OR user only has family policies - Show family members list
        # Only trigger if no specific member is selected (member selection is handled in STEP 3)
        if (is_family_selected or (total_family > 0 and total_self == 0)) and not selected_member:
            logger.info(f"📋 FLOW: Triggering show_family_members (is_family_selected={is_family_selected}, only_family={total_family > 0 and total_self == 0})")

            if total_family == 0:
                quick_actions = [
                    {"title": "Add Family Policy", "action": "add_policy", "redirect": True, "redirect_page": "add_policy"}
                ]
                if total_self > 0:
                    quick_actions.append({"title": "View Self Policies", "action": "policy_query_self", "query": "show self policies"})

                return save_state_and_return({
                    "response": "You don't have any policies uploaded for family members." if language == 'en' else "आपके पास परिवार के सदस्यों के लिए कोई पॉलिसी अपलोड नहीं है।",
                    "action": "policy_query",
                    "flow_step": "no_family_policies",
                    "quick_actions": [a for a in quick_actions if a]
                }, {
                    "flow_step": "no_family_policies",
                    "selected_for": "family"
                })

            # Group family policies by member (using normalized relationship)
            family_members = group_policies_by_family_member(family_policies)
            family_list_msg = build_family_members_list_message(family_members, language)

            return save_state_and_return({
                "response": family_list_msg,
                "action": "policy_query",
                "has_policies": True,
                "policy_count": total_family,
                "flow_step": "show_family_members",
                "family_members": list(family_members.keys()),  # Just the member names for API
                "quick_actions": get_family_member_buttons(family_members, language)
            }, {
                "flow_step": "show_family_members",
                "selected_for": "family",
                "available_members": list(family_members.keys())
            })

        # STEP 3: User selected a specific family member - Show that member's policies
        if selected_member and total_family > 0:
            # Use normalized comparison for matching
            member_policies = [p for p in family_policies if get_policy_relationship(p).lower() == selected_member.lower()]

            if not member_policies:
                # Try partial match with normalized relationship
                member_policies = [p for p in family_policies if selected_member.lower() in get_policy_relationship(p).lower()]

            if not member_policies:
                # Try matching against available members in flow state
                available_members = flow_state.get('available_members', [])
                for avail_member in available_members:
                    if selected_member.lower() in avail_member.lower() or avail_member.lower() in selected_member.lower():
                        member_policies = [p for p in family_policies if get_policy_relationship(p).lower() == avail_member.lower()]
                        if member_policies:
                            selected_member = avail_member
                            break

            if not member_policies:
                # Try matching actual grouped family member names against query text
                # This handles cases like "Show policies for Friend" where "friend" keyword
                # maps to "other" but the actual relationship stored is "Friend"
                family_members_grouped = group_policies_by_family_member(family_policies)
                for member_key, policies_list in family_members_grouped.items():
                    if member_key.lower() in query_lower:
                        member_policies = policies_list
                        selected_member = member_key
                        logger.info(f"📋 FLOW: Matched member '{member_key}' directly from query text")
                        break

            if not member_policies:
                family_members = group_policies_by_family_member(family_policies)
                return save_state_and_return({
                    "response": f"No policies found for {selected_member}. Please select from the available family members." if language == 'en' else f"{selected_member} के लिए कोई पॉलिसी नहीं मिली। कृपया उपलब्ध परिवार के सदस्यों में से चुनें।",
                    "action": "policy_query",
                    "flow_step": "no_member_policies",
                    "quick_actions": get_family_member_buttons(family_members, language)
                }, {
                    "flow_step": "no_member_policies",
                    "selected_for": "family",
                    "attempted_member": selected_member
                })

            # Check if user is asking about a specific policy
            filtered_policies = filter_policies_by_type_or_provider(member_policies, selected_policy_type, selected_provider)

            if filtered_policies and len(filtered_policies) == 1:
                # Save state before showing policy details
                if session_id:
                    store_policy_query_state(session_id, {
                        "flow_step": "show_policy_details",
                        "selected_for": "family",
                        "selected_member": selected_member,
                        "selected_policy_id": filtered_policies[0].get('analysisId', '')
                    })
                return await show_policy_details(filtered_policies[0], query, language)

            # Show member's policies list
            policy_list_msg = build_policy_list_message(member_policies, selected_member, language)

            return save_state_and_return({
                "response": policy_list_msg,
                "action": "policy_query",
                "has_policies": True,
                "policy_count": len(member_policies),
                "flow_step": "show_member_policies",
                "selected_member": selected_member,
                "policies": get_policy_quick_list(member_policies),
                "quick_actions": get_policy_selection_buttons(member_policies, language)
            }, {
                "flow_step": "show_member_policies",
                "selected_for": "family",
                "selected_member": selected_member
            })

        # STEP 4: User asking about specific policy (by type/provider) - Show details
        all_policies = (self_policies or []) + (family_policies or [])
        filtered_policies = filter_policies_by_type_or_provider(all_policies, selected_policy_type, selected_provider)

        if filtered_policies and len(filtered_policies) == 1:
            # Save state before showing policy details
            if session_id:
                store_policy_query_state(session_id, {
                    "flow_step": "show_policy_details",
                    "selected_policy_id": filtered_policies[0].get('analysisId', ''),
                    "filter_type": selected_policy_type,
                    "filter_provider": selected_provider
                })
            return await show_policy_details(filtered_policies[0], query, language)

        if filtered_policies and len(filtered_policies) > 1:
            # Multiple matches - show list
            policy_list_msg = build_policy_list_message(filtered_policies, "filtered", language)
            return save_state_and_return({
                "response": policy_list_msg,
                "action": "policy_query",
                "has_policies": True,
                "policy_count": len(filtered_policies),
                "flow_step": "show_filtered_policies",
                "policies": get_policy_quick_list(filtered_policies),
                "quick_actions": get_policy_selection_buttons(filtered_policies, language)
            }, {
                "flow_step": "show_filtered_policies",
                "filter_type": selected_policy_type,
                "filter_provider": selected_provider
            })

        # DEFAULT: Show summary of all policies with AI response
        # This case is triggered when:
        # 1. User has both self and family but didn't ask a general question
        # 2. No specific flow step matched
        logger.info(f"📋 FLOW: Triggering DEFAULT (general_response) - no specific flow matched")
        all_policies = (self_policies or []) + (family_policies or [])
        policy_summary = build_policy_summary_for_ai(all_policies)
        ai_response = generate_policy_query_response(query, policy_summary, language)

        # Build quick actions, filtering out None values
        quick_actions = []
        if total_self > 0:
            quick_actions.append({"title": "View Self Policies", "action": "policy_query_self", "query": "show self policies"})
        if total_family > 0:
            quick_actions.append({"title": "View Family Policies", "action": "policy_query_family", "query": "show family policies"})
        quick_actions.append({"title": "Add Policy", "action": "add_policy", "redirect": True, "redirect_page": "add_policy"})

        return save_state_and_return({
            "response": ai_response,
            "action": "policy_query",
            "has_policies": True,
            "policy_count": total_policies,
            "self_count": total_self,
            "family_count": total_family,
            "flow_step": "general_response",
            "portfolio_overview": build_portfolio_overview(all_policies),
            "quick_actions": quick_actions
        }, {
            "flow_step": "general_response",
            "total_self": total_self,
            "total_family": total_family
        })

    except Exception as e:
        logger.error(f"Error in handle_policy_query: {e}", exc_info=True)

        # Clear state on error
        if session_id:
            clear_policy_query_state(session_id)

        error_msg = (
            "I'm having trouble fetching your policy information. Please try again."
        ) if language == 'en' else (
            "आपकी पॉलिसी जानकारी प्राप्त करने में समस्या हो रही है। कृपया पुनः प्रयास करें।"
        )
        return {
            "response": error_msg,
            "action": "policy_query",
            "error": str(e),
            "flow_step": "error"
        }


def build_policy_summary_for_ai(policies_data: list, include_personal_info: bool = True) -> str:
    """
    Build a comprehensive summary of user's policies for AI context.
    Includes personal information, family members, nominees for answering specific questions.

    MongoDB policy_analysis structure:
    - extractedData: {policyNumber, insuranceProvider, policyType, coverageAmount, premium, keyBenefits, exclusions,
                      policyHolderName, nominees, insuredMembers, familyMembers, ...}
    - gapAnalysis: [{gapId, category, severity, description, recommendation, estimatedCost}, ...]
    - protectionScore: number (0-100)
    - protectionScoreLabel: string
    - summary: {totalGaps, highSeverityGaps, mediumSeverityGaps, lowSeverityGaps, recommendedAdditionalCoverage}
    - policyHolder: {name, age, gender, contact, ...}
    - familyMemberName, relationship, policyFor
    """
    try:
        summary_parts = []
        total_coverage = 0
        total_gaps = 0
        all_family_members = []
        all_nominees = []

        summary_parts.append(f"=== USER'S INSURANCE PORTFOLIO ===")
        summary_parts.append(f"Total Policies: {len(policies_data)}")

        for i, policy in enumerate(policies_data, 1):
            # Get extractedData (contains policy details)
            extracted_data = policy.get('extractedData', {})

            # Debug logging for policy structure
            logger.info(f"📋 POLICY {i} DEBUG: policyFor={policy.get('policyFor')}, familyMemberName={policy.get('familyMemberName')}, relationship={policy.get('relationship')}")
            logger.info(f"📋 POLICY {i} extractedData keys: {list(extracted_data.keys())[:15]}")

            # Get root level fields
            gap_analysis = policy.get('gapAnalysis', [])
            protection_score = policy.get('protectionScore', 0)
            protection_score_label = policy.get('protectionScoreLabel', '')
            summary = policy.get('summary', {})
            policy_holder = policy.get('policyHolder', {})
            policy_for = policy.get('policyFor', 'self')
            relationship = policy.get('relationship', '') or policy.get('familyRelation', '')
            family_member_name = policy.get('familyMemberName', '')

            # Extract policy details from extractedData
            provider = extracted_data.get('insuranceProvider', 'Unknown Provider')
            policy_type = extracted_data.get('policyType', 'Unknown Type')
            policy_number = extracted_data.get('policyNumber', '')
            coverage = extracted_data.get('coverageAmount', 0) or extracted_data.get('sumAssured', 0)
            premium = extracted_data.get('premium', 0)
            premium_frequency = extracted_data.get('premiumFrequency', 'annually')
            start_date = extracted_data.get('startDate', '')
            end_date = extracted_data.get('endDate', '')

            # ===== PERSONAL INFORMATION EXTRACTION =====
            # Policy holder info
            holder_name = (
                extracted_data.get('policyHolderName', '') or
                extracted_data.get('insuredName', '') or
                extracted_data.get('proposerName', '') or
                policy_holder.get('name', '') or
                policy.get('policyHolderName', '')
            )
            holder_age = extracted_data.get('age', '') or policy_holder.get('age', '')
            holder_gender = extracted_data.get('gender', '') or policy_holder.get('gender', '')
            holder_dob = extracted_data.get('dateOfBirth', '') or extracted_data.get('dob', '')
            holder_contact = extracted_data.get('contactNumber', '') or extracted_data.get('phone', '') or extracted_data.get('mobile', '')
            holder_email = extracted_data.get('email', '')
            holder_address = extracted_data.get('address', '')

            # Nominees
            nominees = extracted_data.get('nominees', []) or extracted_data.get('nominee', [])
            if isinstance(nominees, dict):
                nominees = [nominees]
            if isinstance(nominees, str) and nominees:
                nominees = [{'name': nominees}]

            # Insured members (for family floater policies)
            insured_members = extracted_data.get('insuredMembers', []) or extracted_data.get('coveredMembers', []) or extracted_data.get('familyMembers', [])
            if isinstance(insured_members, dict):
                insured_members = [insured_members]

            # Collect all family members and nominees for summary
            for nominee in nominees if isinstance(nominees, list) else []:
                if isinstance(nominee, dict):
                    nominee_info = {
                        'name': nominee.get('name', ''),
                        'relation': nominee.get('relation', '') or nominee.get('relationship', ''),
                        'percentage': nominee.get('percentage', '') or nominee.get('share', ''),
                        'policy': f"{provider} - {policy_type}"
                    }
                    if nominee_info['name']:
                        all_nominees.append(nominee_info)

            for member in insured_members if isinstance(insured_members, list) else []:
                if isinstance(member, dict):
                    member_info = {
                        'name': member.get('name', ''),
                        'relation': member.get('relation', '') or member.get('relationship', ''),
                        'age': member.get('age', ''),
                        'policy': f"{provider} - {policy_type}"
                    }
                    if member_info['name']:
                        all_family_members.append(member_info)

            # If policy is for family member, add to list
            if policy_for == 'family' and family_member_name:
                all_family_members.append({
                    'name': family_member_name,
                    'relation': relationship,
                    'policy': f"{provider} - {policy_type}"
                })

            # Also check for family member name in extractedData
            extracted_family_name = (
                extracted_data.get('familyMemberName', '') or
                extracted_data.get('insuredName', '') or
                extracted_data.get('insuredMemberName', '') or
                extracted_data.get('policyHolderName', '')
            )
            extracted_relation = (
                extracted_data.get('relationship', '') or
                extracted_data.get('relation', '') or
                extracted_data.get('familyRelation', '') or
                relationship
            )

            # If this is a family policy and we found a name in extractedData, add it
            if policy_for == 'family' and extracted_family_name and extracted_family_name != holder_name:
                already_exists = any(m.get('name', '').lower() == extracted_family_name.lower() for m in all_family_members)
                if not already_exists:
                    all_family_members.append({
                        'name': extracted_family_name,
                        'relation': extracted_relation or relationship or 'family member',
                        'policy': f"{provider} - {policy_type}"
                    })

            # Key benefits (array of strings)
            key_benefits = extracted_data.get('keyBenefits', [])
            if isinstance(key_benefits, list):
                benefit_list = key_benefits
            else:
                benefit_list = []

            # Exclusions (array of strings)
            exclusions = extracted_data.get('exclusions', [])
            if isinstance(exclusions, list):
                exclusion_list = exclusions
            else:
                exclusion_list = []

            # Waiting periods
            waiting_periods = extracted_data.get('waitingPeriods', [])

            # Gap analysis (array of gap objects)
            gap_count = len(gap_analysis) if isinstance(gap_analysis, list) else 0
            gap_descriptions = []
            gap_recommendations = []
            if isinstance(gap_analysis, list):
                for gap in gap_analysis[:5]:  # Top 5 gaps
                    if isinstance(gap, dict):
                        desc = gap.get('description', '')
                        if desc:
                            gap_descriptions.append(f"[{gap.get('severity', 'medium')}] {desc}")
                        rec = gap.get('recommendation', '')
                        if rec:
                            gap_recommendations.append(rec)

            # Summary stats
            high_gaps = summary.get('highSeverityGaps', 0)
            medium_gaps = summary.get('mediumSeverityGaps', 0)
            low_gaps = summary.get('lowSeverityGaps', 0)

            total_coverage += coverage if coverage else 0
            total_gaps += gap_count

            # Build comprehensive policy summary
            policy_summary = f"""
--- Policy {i}: {provider} - {policy_type} ---
Policy For: {policy_for.upper()}{f' ({relationship}: {family_member_name})' if policy_for == 'family' and family_member_name else ''}
Policy Number: {policy_number}
"""
            # Add personal information if available
            if include_personal_info:
                if holder_name:
                    policy_summary += f"Policy Holder Name: {holder_name}\n"
                if holder_age:
                    policy_summary += f"Age: {holder_age}\n"
                if holder_gender:
                    policy_summary += f"Gender: {holder_gender}\n"
                if holder_dob:
                    policy_summary += f"Date of Birth: {holder_dob}\n"
                if holder_contact:
                    policy_summary += f"Contact: {holder_contact}\n"
                if holder_email:
                    policy_summary += f"Email: {holder_email}\n"
                if holder_address:
                    policy_summary += f"Address: {holder_address}\n"

                # Nominees for this policy
                if nominees and isinstance(nominees, list):
                    nominee_strs = []
                    for n in nominees[:3]:
                        if isinstance(n, dict) and n.get('name'):
                            n_str = n.get('name', '')
                            if n.get('relation') or n.get('relationship'):
                                n_str += f" ({n.get('relation', '') or n.get('relationship', '')})"
                            if n.get('percentage') or n.get('share'):
                                n_str += f" - {n.get('percentage', '') or n.get('share', '')}%"
                            nominee_strs.append(n_str)
                    if nominee_strs:
                        policy_summary += f"Nominees: {'; '.join(nominee_strs)}\n"

                # Insured members for this policy
                if insured_members and isinstance(insured_members, list):
                    member_strs = []
                    for m in insured_members[:5]:
                        if isinstance(m, dict) and m.get('name'):
                            m_str = m.get('name', '')
                            if m.get('relation') or m.get('relationship'):
                                m_str += f" ({m.get('relation', '') or m.get('relationship', '')})"
                            if m.get('age'):
                                m_str += f", Age: {m.get('age')}"
                            member_strs.append(m_str)
                    if member_strs:
                        policy_summary += f"Covered Family Members: {'; '.join(member_strs)}\n"

            # Calculate policy status
            policy_status = "active"
            days_left_str = ""
            if end_date:
                try:
                    from routers.dashboard import parse_date
                    parsed_end = parse_date(end_date)
                    if parsed_end:
                        days_left = (parsed_end - datetime.now()).days
                        if days_left < 0:
                            policy_status = "EXPIRED"
                            days_left_str = f" (expired {abs(days_left)} days ago)"
                        elif days_left <= 60:
                            policy_status = "EXPIRING SOON"
                            days_left_str = f" ({days_left} days left)"
                        else:
                            policy_status = "ACTIVE"
                            days_left_str = f" ({days_left} days left)"
                except Exception:
                    pass

            policy_summary += f"""Coverage Amount: ₹{coverage:,.0f}
Premium: ₹{premium:,.0f} ({premium_frequency})
Start Date: {start_date}
End Date: {end_date}
Policy Status: {policy_status}{days_left_str}
Protection Score: {protection_score}/100 ({protection_score_label})
Total Coverage Gaps: {gap_count} (High: {high_gaps}, Medium: {medium_gaps}, Low: {low_gaps})
Gap Details: {'; '.join(gap_descriptions[:3]) if gap_descriptions else 'No gaps identified'}
Recommendations: {'; '.join(gap_recommendations[:3]) if gap_recommendations else 'No specific recommendations'}
Key Benefits: {'; '.join(benefit_list[:5]) if benefit_list else 'Not specified in policy'}
Exclusions: {'; '.join(exclusion_list[:5]) if exclusion_list else 'Not specified in policy'}
Waiting Periods: {'; '.join(str(w) for w in waiting_periods[:3]) if waiting_periods else 'Not specified'}
"""
            summary_parts.append(policy_summary)

        # ===== FAMILY MEMBERS SUMMARY =====
        if all_family_members:
            summary_parts.append("\n=== FAMILY MEMBERS COVERED IN POLICIES ===")
            unique_members = {}
            for m in all_family_members:
                name = m.get('name', '').strip()
                if name and name not in unique_members:
                    unique_members[name] = m
            for name, m in unique_members.items():
                member_line = f"- {name}"
                if m.get('relation'):
                    member_line += f" (Relation: {m['relation']})"
                if m.get('age'):
                    member_line += f", Age: {m['age']}"
                summary_parts.append(member_line)

        # ===== NOMINEES SUMMARY =====
        if all_nominees:
            summary_parts.append("\n=== NOMINEES IN POLICIES ===")
            unique_nominees = {}
            for n in all_nominees:
                name = n.get('name', '').strip()
                if name and name not in unique_nominees:
                    unique_nominees[name] = n
            for name, n in unique_nominees.items():
                nominee_line = f"- {name}"
                if n.get('relation'):
                    nominee_line += f" (Relation: {n['relation']})"
                if n.get('percentage'):
                    nominee_line += f", Share: {n['percentage']}%"
                if n.get('policy'):
                    nominee_line += f", Policy: {n['policy']}"
                summary_parts.append(nominee_line)

        summary_parts.append(f"\n=== PORTFOLIO SUMMARY ===")
        summary_parts.append(f"Total Coverage: ₹{total_coverage:,.0f}")
        summary_parts.append(f"Total Coverage Gaps Identified: {total_gaps}")
        summary_parts.append(f"Total Family Members Covered: {len(set(m.get('name', '') for m in all_family_members if m.get('name')))}")
        summary_parts.append(f"Total Nominees: {len(set(n.get('name', '') for n in all_nominees if n.get('name')))}")

        return "\n".join(summary_parts)

    except Exception as e:
        logger.error(f"Error building policy summary: {e}", exc_info=True)
        return "Policy data available but summary generation failed."


def build_portfolio_overview(policies_data: list) -> dict:
    """
    Build portfolio overview from policies data.

    Uses correct MongoDB structure:
    - extractedData: {coverageAmount, premium, policyType, ...}
    - gapAnalysis: array of gaps
    - protectionScore: number
    """
    try:
        total_coverage = 0
        total_premium = 0
        total_gaps = 0
        avg_score = 0
        categories = {}

        for policy in policies_data:
            # Use correct MongoDB fields
            extracted_data = policy.get('extractedData', {})
            gap_analysis = policy.get('gapAnalysis', [])

            coverage = extracted_data.get('coverageAmount', 0) or extracted_data.get('sumAssured', 0)
            premium = extracted_data.get('premium', 0)
            score = policy.get('protectionScore', 0)
            gap_count = len(gap_analysis) if isinstance(gap_analysis, list) else 0

            # Categorize by policy type
            policy_type = extracted_data.get('policyType', 'Other').lower()
            if 'health' in policy_type:
                cat_key = 'health'
            elif 'life' in policy_type or 'term' in policy_type:
                cat_key = 'life'
            elif 'motor' in policy_type or 'car' in policy_type or 'vehicle' in policy_type:
                cat_key = 'motor'
            else:
                cat_key = 'other'

            if cat_key not in categories:
                categories[cat_key] = {'count': 0, 'coverage': 0}
            categories[cat_key]['count'] += 1
            categories[cat_key]['coverage'] += coverage if coverage else 0

            total_coverage += coverage if coverage else 0
            total_premium += premium if premium else 0
            total_gaps += gap_count
            avg_score += score if score else 0

        if len(policies_data) > 0:
            avg_score = avg_score / len(policies_data)

        return {
            "totalPolicies": len(policies_data),
            "totalCoverage": total_coverage,
            "totalCoverageFormatted": format_currency(total_coverage),
            "totalPremium": total_premium,
            "totalPremiumFormatted": format_currency(total_premium),
            "averageProtectionScore": round(avg_score, 1),
            "totalCoverageGaps": total_gaps,
            "categoryBreakdown": categories
        }

    except Exception as e:
        logger.error(f"Error building portfolio overview: {e}")
        return {}


def format_currency(amount: float) -> str:
    """Format amount in Indian currency style"""
    if amount >= 10000000:  # 1 Crore
        return f"₹{amount/10000000:.1f}Cr"
    elif amount >= 100000:  # 1 Lakh
        return f"₹{amount/100000:.1f}L"
    elif amount >= 1000:
        return f"₹{amount/1000:.1f}K"
    else:
        return f"₹{amount:,.0f}"


def generate_policy_query_response(query: str, policy_summary: str, language: str = 'en', conversation_history: list = None) -> str:
    """
    Generate intelligent AI response for policy queries using LLM.
    Handles personal information, family member queries, gaps, benefits, etc.
    Uses conversation_history to understand which policy the user is referring to.
    """
    try:
        from ai_chat_components.llm_config import get_llm

        llm = get_llm(use_case='chat')

        # Only include conversation context if the current query uses pronouns (it, that, this, etc.)
        conv_context = ""
        pronoun_refs = ['it ', 'that ', 'this ', 'the policy', 'which one', 'isko', 'uska', 'uski', 'isme']
        query_lower_check = query.lower()
        needs_context = any(p in query_lower_check for p in pronoun_refs)
        if needs_context and conversation_history and len(conversation_history) > 0:
            recent = conversation_history[-2:]
            conv_lines = []
            for msg in recent:
                role = msg.get('role', 'unknown')
                content = msg.get('content', '')[:150]
                if role in ('user', 'assistant', 'bot'):
                    conv_lines.append(f"{'User' if role == 'user' else 'Assistant'}: {content}")
            if conv_lines:
                conv_context = "\n(Previous exchange for pronoun resolution):\n" + "\n".join(conv_lines) + "\n"

        today_str = datetime.now().strftime("%B %d, %Y")
        system_prompt = f"""You are eazr, an intelligent insurance assistant with access to the user's complete policy portfolio.
You can answer ANY question about their policies including personal details, family members, nominees, coverage, gaps, and recommendations.
Today's date is {today_str}. Use this to accurately determine if policies are expired, expiring soon, or active.

=== USER'S COMPLETE POLICY DATA ===
{policy_summary}
=== END OF POLICY DATA ===
{conv_context}
INSTRUCTIONS:
1. MOST CRITICAL RULE: Answer the user's CURRENT question below. Do NOT repeat or continue answering a previous question from conversation history. Each new message = new question to answer.
2. If the user asks MULTIPLE questions in ONE message, answer ALL parts. Never skip any question. Address each one in order. It is OK to give a longer response (up to 300 words) for compound questions.
3. CONTEXT AWARENESS: When the user says "this policy", "it", "that policy", or pronouns:
   - Look at the RECENT CONVERSATION CONTEXT to identify which policy was being discussed
   - But if the current question is clearly about a DIFFERENT topic, answer the current question — don't repeat previous answers
4. For personal information queries (names, family members, nominees):
   - Look in: "Policy Holder Name", "Covered Family Members", "Nominees", "FAMILY MEMBERS COVERED IN POLICIES", "NOMINEES IN POLICIES"
   - Each policy shows "Policy For: FAMILY (relationship: name)" - use this for family member names
5. For coverage gap queries: List specific gaps with severity levels [High/Medium/Low]
6. For premium/coverage queries: Provide exact amounts in Indian format (₹X lakhs/crores)
7. If the information is NOT in the policy data:
   - Say "I don't have that information in your uploaded policy data" rather than making things up
   - For general insurance knowledge questions (claim process, porting, cashless etc.): provide general guidance even if not in the policy data
8. For expiry/status queries:
   - Check "Policy Status" field — EXPIRED, EXPIRING SOON, or ACTIVE
   - If end date has PASSED today's date ({today_str}), say it HAS EXPIRED
9. Be conversational, helpful, and ACCURATE
10. Response language: {"English" if language == 'en' else "Hindi"}
11. Keep response concise but complete (max 300 words)

IMPORTANT: Never make up information. Only use data from the policy portfolio above. For general insurance concepts (claim process, porting, cashless, copay, deductible, riders), you can provide general knowledge."""

        from langchain_core.messages import HumanMessage, SystemMessage

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"ANSWER THIS QUESTION NOW: {query}")
        ]

        response = llm.invoke(messages)
        return response.content.strip()

    except Exception as e:
        logger.error(f"Error generating policy query response: {e}")
        # Retry once with a simpler prompt before falling back to generic
        try:
            from ai_chat_components.llm_config import get_llm
            retry_llm = get_llm(use_case='chat')
            from langchain_core.messages import HumanMessage as HM, SystemMessage as SM
            retry_prompt = f"You are eazr, an insurance expert. Answer this user question about their insurance policies in 2-4 sentences. Be helpful and conversational.\n\nPolicy data:\n{policy_summary[:2000]}\n\nQuestion: {query}"
            retry_response = retry_llm.invoke([SM(content=retry_prompt)])
            if retry_response and retry_response.content.strip():
                return retry_response.content.strip()
        except Exception:
            pass
        # Final fallback
        if language == 'en':
            return f"Hmm, I'm having trouble pulling up the details right now. Can you try asking one question at a time? Like 'When does my policy expire?' — I'll give you exact answers!"
        else:
            return f"अरे, अभी details निकालने में थोड़ी दिक्कत हो रही है। एक बार एक सवाल पूछ कर देखो — जैसे 'मेरी पॉलिसी कब expire होगी?' — मैं सही जवाब दूंगा!"
# ============= END POLICY QUERY HANDLER =============


async def handle_insurance_analysis_dynamic(files, user_id, session_id, metadata, was_regenerated, original_session_id):
    """Handle dynamic insurance analysis - supports multiple files"""
    try:
        if not UniversalDynamicAnalyzer:
            raise Exception("Universal analyzer not available")

        # Initialize analyzer
        universal_analyzer = UniversalDynamicAnalyzer(openai_api_key=OPENAI_API_KEY)

        # Ensure files is a list
        if not isinstance(files, list):
            files = [files]

        allowed_extensions = {'.pdf', '.png', '.jpg', '.jpeg', '.webp'}
        results = []

        for file in files:
            file_ext = os.path.splitext(file.filename.lower())[1]

            if file_ext not in allowed_extensions:
                results.append({
                    "filename": file.filename,
                    "success": False,
                    "error": f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}"
                })
                continue

            # Read file content
            file_content = await file.read()

            if len(file_content) == 0:
                results.append({
                    "filename": file.filename,
                    "success": False,
                    "error": "Empty file"
                })
                continue

            try:
                # Analyze the file - use correct method name (synchronous, not async)
                analysis_result = universal_analyzer.analyze_insurance_universal(
                    pdf_content=file_content,
                    filename=file.filename
                )

                # Convert dataclass to dict for serialization
                from dataclasses import asdict
                analysis_dict = asdict(analysis_result)

                # Generate PDF report
                pdf_buffer = generate_pdf_report(analysis_result)
                report_url = upload_pdf_to_s3(
                    pdf_buffer,
                    f"analysis_{user_id}_{int(time.time())}.pdf",
                    "raceabove-dev"
                )

                # Store in MongoDB if available
                mongodb_id = None
                if mongodb_chat_manager and user_id:
                    mongodb_id = store_policy_analysis_in_mongodb(
                        user_id=user_id,
                        session_id=session_id,
                        analysis_data=analysis_dict,
                        report_url=report_url.get('s3_url') if isinstance(report_url, dict) else report_url,
                        filename=file.filename
                    )

                results.append({
                    "filename": file.filename,
                    "success": True,
                    "analysis": analysis_dict,
                    "report_url": report_url.get('s3_url') if isinstance(report_url, dict) else report_url,
                    "mongodb_id": mongodb_id
                })

            except Exception as file_error:
                logger.error(f"Error analyzing {file.filename}: {str(file_error)}")
                results.append({
                    "filename": file.filename,
                    "success": False,
                    "error": str(file_error)
                })

        # Return aggregated results
        successful_analyses = [r for r in results if r.get("success")]
        failed_analyses = [r for r in results if not r.get("success")]

        if successful_analyses:
            # Return first successful analysis as primary
            primary = successful_analyses[0]
            return create_standardized_response(
                response_type="analysis_result",
                data={
                    "response": "Insurance document analyzed successfully",
                    "analysis_results": primary.get("analysis"),
                    "report_url": primary.get("report_url"),
                    "mongodb_id": primary.get("mongodb_id"),
                    "total_files": len(files),
                    "successful": len(successful_analyses),
                    "failed": len(failed_analyses),
                    "all_results": results,
                    "session_regenerated": was_regenerated,
                    "original_session_id": original_session_id
                },
                session_id=session_id,
                metadata={
                    **metadata,
                    "file_processed": True,
                    "files_count": len(files)
                }
            )
        else:
            # All analyses failed
            return create_standardized_response(
                response_type="error",
                data={
                    "error": "Failed to analyze documents",
                    "message": "Could not process any of the uploaded files",
                    "failed_files": failed_analyses
                },
                session_id=session_id,
                metadata=metadata
            )

    except Exception as e:
        logger.error(f"Error in insurance analysis: {str(e)}")
        return create_standardized_response(
            response_type="error",
            data={
                "error": str(e),
                "message": "Insurance analysis failed"
            },
            session_id=session_id,
            metadata=metadata
        )


# ============= SESSION MANAGEMENT ENDPOINTS =============

@router.post("/new-chat")
async def create_new_chat_conversation(
    user_session_id: str = Form(...),
    user_id: int = Form(...),
    access_token: str = Form(...),
    title: str = Form("New Chat")
):
    """
    Create NEW chat session - WITH AUTO-REPAIR for user_id mismatch
    """
    try:
        # Validate user session
        user_session_data = get_session(user_session_id)
        if not user_session_data or not user_session_data.get('active'):
            raise HTTPException(status_code=401, detail="Invalid user session")

        # Get user_id from session
        session_user_id = user_session_data.get('user_id')

        # Convert to int for comparison
        try:
            session_user_id_int = int(session_user_id) if session_user_id else None
            request_user_id_int = int(user_id) if user_id else None
        except (ValueError, TypeError) as e:
            logger.error(f"Invalid user_id format - session: {session_user_id}, request: {user_id}")
            raise HTTPException(status_code=400, detail=f"Invalid user ID format: {str(e)}")

        # Check if user_ids match
        if session_user_id_int != request_user_id_int:
            logger.warning(f"⚠ User ID mismatch - session: {session_user_id_int}, request: {request_user_id_int}")

            # ATTEMPT AUTO-REPAIR: Verify which one is correct using access_token
            token_verification = verify_jwt_token(access_token)

            if token_verification.get('valid'):
                token_user_id = int(token_verification['payload'].get('id'))
                logger.info(f"JWT token user_id: {token_user_id}")

                # Determine correct user_id based on JWT token
                if token_user_id == session_user_id_int:
                    # Session is correct, request is wrong
                    logger.error(f"✗ Request has wrong user_id. JWT confirms session user_id {session_user_id_int} is correct")
                    raise HTTPException(
                        status_code=403,
                        detail=f"User ID mismatch: Your session belongs to user {session_user_id_int}, but you sent {request_user_id_int}. Please logout and login again."
                    )

                elif token_user_id == request_user_id_int:
                    # Request is correct, session needs repair
                    logger.warning(f"🔧 Session has wrong user_id. JWT confirms request user_id {request_user_id_int} is correct. Auto-repairing session...")

                    # Update session with correct user_id
                    user_session_data['user_id'] = request_user_id_int
                    store_session(user_session_id, user_session_data, expire_seconds=1296000)

                    # Update MongoDB session
                    if mongodb_chat_manager:
                        mongodb_chat_manager.sessions_collection.update_one(
                            {"session_id": user_session_id},
                            {"$set": {"user_id": request_user_id_int}}
                        )

                    session_user_id_int = request_user_id_int
                    logger.info(f"✓ Session repaired with correct user_id: {request_user_id_int}")

                else:
                    # Neither matches JWT - critical error
                    logger.error(f"✗ CRITICAL: JWT user_id {token_user_id} doesn't match session {session_user_id_int} or request {request_user_id_int}")
                    raise HTTPException(
                        status_code=401,
                        detail="Authentication mismatch. Please logout and login again."
                    )
            else:
                # JWT invalid - can't auto-repair
                logger.error(f"✗ Cannot auto-repair: JWT token invalid - {token_verification.get('error')}")
                raise HTTPException(
                    status_code=403,
                    detail=f"User ID mismatch: session has {session_user_id_int}, but request has {request_user_id_int}. Token verification failed. Please logout and login again."
                )

        # Use the verified user_id
        verified_user_id = session_user_id_int

        current_timestamp = datetime.now()

        # Create NEW chat session
        chat_session_id = f"chat_{verified_user_id}_{int(time.time())}_{secrets.token_hex(4)}"

        chat_session_data = {
            'user_id': verified_user_id,
            'session_type': 'chat_session',
            'created_at': current_timestamp.isoformat(),
            'last_activity': current_timestamp.isoformat(),
            'title': title,
            'active': True,
            'message_count': 0,
            'user_session_id': user_session_id
        }

        # Store in Redis/Memory
        store_session(chat_session_id, chat_session_data, expire_seconds=86400)

        # Store in MongoDB
        if mongodb_chat_manager:
            result = mongodb_chat_manager.create_new_chat_session(
                user_id=verified_user_id,
                session_id=chat_session_id,
                title=title
            )

            if not result.get("success"):
                raise HTTPException(status_code=500, detail="Failed to create chat session in MongoDB")

            # Update user profile
            mongodb_chat_manager.users_collection.update_one(
                {"user_id": verified_user_id},
                {
                    "$addToSet": {"chat_session_history": chat_session_id},
                    "$set": {
                        "last_chat_session_id": chat_session_id,
                        "updated_at": datetime.utcnow()
                    }
                }
            )

        logger.info(f"✓ Created new chat {chat_session_id} for user {verified_user_id}")

        return {
            "success": True,
            "message": "New chat created successfully",
            "chat_session_id": chat_session_id,
            "user_session_id": user_session_id,
            "user_id": verified_user_id,  # Return verified user_id
            "title": title,
            "created_at": current_timestamp.isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"✗ Error creating new chat: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user/{user_id}/chat-sessions")
async def get_user_chat_sessions_endpoint(
    user_id: int,
    limit: int = 50,
    include_archived: bool = False
):
    """
    Get all chat sessions for a user - FIXED VERSION
    """
    try:
        if not MONGODB_AVAILABLE:
            raise HTTPException(status_code=503, detail="MongoDB service unavailable")

        from database_storage.mongodb_chat_manager import get_all_user_chats, mongodb_chat_manager

        # Convert user_id to int to ensure consistency
        try:
            user_id_int = int(user_id)
        except (ValueError, TypeError):
            raise HTTPException(status_code=400, detail="Invalid user ID")

        # Also try to find sessions where user_id might be stored as string
        chats = get_all_user_chats(user_id_int, limit, include_archived)

        # If no chats found, try with string user_id as fallback
        if not chats:
            logger.info(f"No chats found for user_id {user_id_int}, trying string format")
            # Query directly with both formats
            from database_storage.mongodb_chat_manager import mongodb_chat_manager
            query = {
                "$or": [
                    {"user_id": user_id_int},
                    {"user_id": str(user_id_int)}
                ],
                "deleted": False
            }
            if not include_archived:
                query["is_archived"] = False

            sessions = list(mongodb_chat_manager.sessions_collection.find(query).sort("last_activity", -1).limit(limit))

            # Fix user_id format in found sessions
            for session in sessions:
                if session.get("user_id") != user_id_int:
                    mongodb_chat_manager.sessions_collection.update_one(
                        {"_id": session["_id"]},
                        {"$set": {"user_id": user_id_int}}
                    )
                    logger.info(f"Fixed user_id format for session {session.get('session_id')}")

            # Retry getting chats
            chats = get_all_user_chats(user_id_int, limit, include_archived)

        # Filter out empty placeholder sessions (no messages + default title)
        default_titles = {"New Chat", "WebSocket Chat", "Chat Session", "Auto Chat"}
        chats = [chat for chat in chats if not (chat.get("title") in default_titles and chat.get("message_count", 0) == 0)]

        # Organize by date
        today = datetime.now().date()
        yesterday = today - timedelta(days=1)
        last_7_days = today - timedelta(days=7)
        last_30_days = today - timedelta(days=30)

        organized_chats = {
            "today": [],
            "yesterday": [],
            "last_7_days": [],
            "last_30_days": [],
            "older": []
        }

        for chat in chats:
            try:
                last_activity_date = datetime.fromisoformat(chat["last_activity"]).date()

                if last_activity_date == today:
                    organized_chats["today"].append(chat)
                elif last_activity_date == yesterday:
                    organized_chats["yesterday"].append(chat)
                elif last_activity_date > last_7_days:
                    organized_chats["last_7_days"].append(chat)
                elif last_activity_date > last_30_days:
                    organized_chats["last_30_days"].append(chat)
                else:
                    organized_chats["older"].append(chat)
            except:
                organized_chats["older"].append(chat)

        return {
            "success": True,
            "user_id": user_id_int,
            "total_chats": len(chats),
            "chats": chats,
            "organized_chats": organized_chats,
            "timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user chats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/load-chat-session")
async def load_chat_session_endpoint(request: LoadChatRequest):
    """
    Load a specific chat session with all messages - FIXED VERSION

    Used when user clicks on a chat from sidebar
    """
    try:
        if not MONGODB_AVAILABLE:
            raise HTTPException(status_code=503, detail="MongoDB service unavailable")

        from database_storage.mongodb_chat_manager import load_specific_chat, mongodb_chat_manager

        # Load chat data
        chat_data = load_specific_chat(request.session_id, request.message_limit)

        if not chat_data.get("success"):
            raise HTTPException(status_code=404, detail="Chat session not found")

        # Get session info
        session_info = chat_data.get("session", {})
        session_user_id = session_info.get("user_id")

        # Convert both to same type for comparison (handle string/int mismatch)
        try:
            session_user_id_int = int(session_user_id) if session_user_id else None
            request_user_id_int = int(request.user_id) if request.user_id else None
        except (ValueError, TypeError):
            logger.error(f"Invalid user_id format - session: {session_user_id}, request: {request.user_id}")
            raise HTTPException(status_code=400, detail="Invalid user ID format")

        # Verify ownership with type-safe comparison
        if session_user_id_int != request_user_id_int:
            # Try to verify via messages as fallback
            messages = chat_data.get("messages", [])
            if messages and len(messages) > 0:
                # Check if any message belongs to this user
                message_user_ids = set()
                for msg in messages:
                    try:
                        msg_user_id = int(msg.get("user_id", 0))
                        message_user_ids.add(msg_user_id)
                    except (ValueError, TypeError):
                        continue

                if request_user_id_int not in message_user_ids:
                    logger.warning(f"Access denied: user {request_user_id_int} tried to access session {request.session_id} belonging to user {session_user_id_int}")
                    raise HTTPException(status_code=403, detail="Access denied to this chat")
                else:
                    # User has messages in this chat, update session owner
                    logger.info(f"Fixing session ownership for {request.session_id}: updating to user {request_user_id_int}")
                    mongodb_chat_manager.sessions_collection.update_one(
                        {"session_id": request.session_id},
                        {"$set": {"user_id": request_user_id_int}}
                    )
                    session_info["user_id"] = request_user_id_int
            else:
                logger.warning(f"Access denied: user {request_user_id_int} tried to access session {request.session_id} belonging to user {session_user_id_int}")
                raise HTTPException(status_code=403, detail="Access denied to this chat")

        return {
            "success": True,
            "session_id": request.session_id,
            "session_info": session_info,
            "messages": chat_data.get("messages", []),
            "total_messages": chat_data.get("total_messages", 0),
            "loaded_at": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error loading chat session: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/update-chat-title")
async def update_chat_title_endpoint(request: UpdateChatTitleRequest):
    """
    Update chat session title (rename chat)
    """
    try:
        if not MONGODB_AVAILABLE:
            raise HTTPException(status_code=503, detail="MongoDB service unavailable")

        from database_storage.mongodb_chat_manager import update_chat_session_title, mongodb_chat_manager

        # Verify ownership
        session = mongodb_chat_manager.sessions_collection.find_one({"session_id": request.session_id})
        if not session or session.get("user_id") != request.user_id:
            raise HTTPException(status_code=403, detail="Access denied")

        success = update_chat_session_title(request.session_id, request.new_title)

        if success:
            return {
                "success": True,
                "message": "Chat title updated successfully",
                "session_id": request.session_id,
                "new_title": request.new_title
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to update chat title")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating chat title: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/delete-chat-session")
async def delete_chat_session_endpoint(request: DeleteChatRequest):
    """
    Delete a chat session

    - soft delete (default): Marks as deleted but keeps data
    - hard delete: Permanently removes all data
    """
    try:
        if not MONGODB_AVAILABLE:
            raise HTTPException(status_code=503, detail="MongoDB service unavailable")

        from database_storage.mongodb_chat_manager import delete_chat_session_by_id, mongodb_chat_manager

        # Verify ownership
        session = mongodb_chat_manager.sessions_collection.find_one({"session_id": request.session_id})
        if not session or session.get("user_id") != request.user_id:
            raise HTTPException(status_code=403, detail="Access denied")

        success = delete_chat_session_by_id(request.session_id, request.hard_delete)

        if success:
            # Clear from memory/redis
            delete_session(request.session_id)

            return {
                "success": True,
                "message": "Chat deleted successfully",
                "session_id": request.session_id,
                "hard_delete": request.hard_delete
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to delete chat")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search-chats")
async def search_chats_endpoint(request: SearchChatsRequest):
    """
    Search through user's chat history

    Searches both chat titles and message content
    """
    try:
        if not MONGODB_AVAILABLE:
            raise HTTPException(status_code=503, detail="MongoDB service unavailable")

        from database_storage.mongodb_chat_manager import search_user_chats

        results = search_user_chats(
            user_id=request.user_id,
            search_query=request.search_query,
            limit=request.limit
        )

        return {
            "success": True,
            "search_query": request.search_query,
            "total_results": len(results),
            "results": results,
            "timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching chats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/archive-chat")
async def archive_chat_endpoint(session_id: str, user_id: int):
    """Archive a chat session"""
    try:
        if not MONGODB_AVAILABLE:
            raise HTTPException(status_code=503, detail="MongoDB service unavailable")

        from database_storage.mongodb_chat_manager import mongodb_chat_manager

        # Verify ownership
        session = mongodb_chat_manager.sessions_collection.find_one({"session_id": session_id})
        if not session or session.get("user_id") != user_id:
            raise HTTPException(status_code=403, detail="Access denied")

        success = mongodb_chat_manager.archive_chat_session(session_id)

        if success:
            return {
                "success": True,
                "message": "Chat archived successfully",
                "session_id": session_id
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to archive chat")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error archiving chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============= CONVERSATION ENDPOINTS =============

# ============= IMPORTANT NOTE ABOUT /ask ENDPOINT =============
# The /ask endpoint (2,439 lines spanning app.py lines 6802-9240) is a massive unified
# chat endpoint that handles:
# - Guest vs authenticated user differentiation
# - File uploads and insurance analysis
# - RAG queries and intent detection
# - Service selection (loans, insurance, wallet)
# - Application workflows
# - Multilingual support
# - Context-aware responses
#
# Due to its enormous size and complexity, it requires manual extraction.
# For now, the endpoint remains in app.py. Future refactoring should consider:
# 1. Breaking it into smaller, focused endpoints
# 2. Extracting business logic into separate service modules
# 3. Creating middleware for authentication checks
# 4. Separating file handling logic
#
# To use this router module while keeping /ask in app.py:
# - Include this router in your app: app.include_router(chat_router, prefix="", tags=["Chat"])
# - Comment out duplicate endpoints in app.py (all except /ask)
# - Eventually extract and refactor the /ask endpoint
# ============= END NOTE =============


@router.post("/chatbot-continue")
async def continue_chatbot(request: ChatbotContinue):
    """Legacy chatbot continuation support (ASYNC)"""
    try:
        logger.info(f"🔄 Legacy chatbot continuation for {request.chatbot_type}")

        # Route to enhanced chatbot system
        if request.chatbot_type == "wallet_setup":
            result = await route_enhanced_chatbot(
                action="start_wallet_setup",
                session_id=request.session_id,
                user_input=request.user_input,
                access_token=request.access_token,
                user_id=request.user_id
            )
        elif request.chatbot_type == "personal_loan":
            result = await route_enhanced_chatbot(
                action="start_loan_application",
                session_id=request.session_id,
                user_input=request.user_input,
                access_token=request.access_token,
                user_id=request.user_id,
                loan_type="personal"
            )
        elif request.chatbot_type == "insurance_plan":
            result = await route_enhanced_chatbot(
                action="start_insurance_application",
                session_id=request.session_id,
                user_input=request.user_input,
                access_token=request.access_token,
                user_id=request.user_id,
                insurance_type=request.sub_type or "health"
            )
        else:
            result = {"error": f"Unknown legacy chatbot type: {request.chatbot_type}"}

        return result

    except Exception as e:
        logger.error(f"✗ Error in legacy chatbot continuation: {e}")
        return {"error": str(e)}


@router.post("/chat-history")
async def get_chat_history(request: ChatHistoryRequest):
    """Get conversation history for a session"""
    try:
        messages = chat_memory.get_conversation_history(request.session_id, request.limit)

        return {
            "success": True,
            "session_id": request.session_id,
            "messages": [msg.to_dict() for msg in messages],
            "total_messages": len(messages),
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error getting chat history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search-chat")
async def search_chat(request: SearchChatRequest):
    """Search through conversation history"""
    try:
        results = search_chat_history(request.session_id, request.query, request.limit)

        return {
            "success": True,
            "session_id": request.session_id,
            "search_query": request.query,
            "results": results,
            "total_results": len(results),
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error searching chat history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat-analytics")
async def get_chat_analytics_endpoint(request: ChatHistoryRequest):
    """Get analytics about the conversation"""
    try:
        analytics = get_chat_analytics(request.session_id)

        return {
            "success": True,
            "session_id": request.session_id,
            "analytics": analytics,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error getting chat analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/clear-user-chat-history")
async def clear_user_chat_history_endpoint(request: ClearUserChatRequest):
    """Backup and clear ALL conversation history for a user across all sessions"""
    try:
        # Validate session with regeneration
        session_id, session_data, was_regenerated = session_manager.validate_and_regenerate_session(
            request.session_id,
            get_session,
            store_session
        )

        if not session_data or not session_data.get('active'):
            raise HTTPException(status_code=401, detail="Invalid or expired session")

        # Verify user_id matches session
        if session_data.get('user_id') != request.user_id:
            raise HTTPException(status_code=403, detail="User ID mismatch with session")

        if not MONGODB_AVAILABLE:
            raise HTTPException(status_code=503, detail="MongoDB service unavailable")

        if not request.confirm:
            return {
                "success": False,
                "message": "Please confirm chat history backup and deletion by setting confirm=true",
                "user_id": request.user_id,
                "session_id": session_id,
                "session_regenerated": was_regenerated,
                "warning": "This will BACKUP your conversation history and then CLEAR it from active storage",
                "info": "Your chat history will be safely stored in backup collections and can be restored if needed",
                "confirmation_required": True,
                "timestamp": datetime.now().isoformat()
            }

        # Backup and clear user chat history
        result = backup_and_clear_user_chat_history(
            request.user_id,
            backup_reason="user_requested_clear"
        )

        if result["success"]:
            # Log the activity
            if mongodb_chat_manager:
                mongodb_chat_manager.log_user_activity(
                    user_id=request.user_id,
                    session_id=session_id,
                    activity_type="chat_history_backed_up_and_cleared",
                    metadata={
                        "backup_id": result.get("backup_id"),
                        "backup_stats": result.get("backup_stats"),
                        "cleared_stats": result.get("cleared_stats")
                    }
                )

        return {
            "success": result["success"],
            "message": result["message"],
            "user_id": request.user_id,
            "session_id": session_id,
            "session_regenerated": was_regenerated,
            "backup_details": {
                "backup_id": result.get("backup_id"),
                "backup_timestamp": result.get("backup_timestamp"),
                "backup_stats": result.get("backup_stats"),
                "cleared_stats": result.get("cleared_stats")
            } if result["success"] else None,
            "error": result.get("error") if not result["success"] else None,
            "operation": "backup_and_clear",
            "timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in backup and clear endpoint for user {request.user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversation-context/{session_id}")
async def get_conversation_context_endpoint(session_id: str):
    """Get conversation context for debugging/admin purposes"""
    try:
        context = get_conversation_context(session_id)

        return {
            "success": True,
            "session_id": session_id,
            "context": context,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error getting conversation context: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export-conversation/{session_id}")
async def export_conversation(session_id: str, format: str = "json"):
    """Export conversation data"""
    try:
        messages = chat_memory.get_conversation_history(session_id)
        analytics = get_chat_analytics(session_id)
        context = get_conversation_context(session_id)

        export_data = {
            "session_id": session_id,
            "export_timestamp": datetime.now().isoformat(),
            "format_version": "1.0",
            "messages": [msg.to_dict() for msg in messages],
            "analytics": analytics,
            "user_context": context.get("user_context", {}),
            "conversation_summary": context.get("summary", {})
        }

        if format.lower() == "json":
            return JSONResponse(
                content=export_data,
                headers={"Content-Disposition": f"attachment; filename=conversation_{session_id}.json"}
            )
        else:
            # Convert to CSV format
            import csv
            import io

            output = io.StringIO()
            writer = csv.writer(output)

            # Write headers
            writer.writerow(["Timestamp", "Role", "Content", "Intent", "Message_ID"])

            # Write messages
            for msg in messages:
                writer.writerow([
                    msg.timestamp.isoformat(),
                    msg.role,
                    msg.content[:200],  # Truncate long messages
                    msg.intent or "",
                    msg.message_id
                ])

            csv_content = output.getvalue()

            return Response(
                content=csv_content,
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename=conversation_{session_id}.csv"}
            )

    except Exception as e:
        logger.error(f"Error exporting conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============= HELPER FUNCTIONS FOR /ASK ENDPOINT =============

async def handle_insurance_policy_selection(query: str, chat_session_id: str, user_id: int, metadata: dict, access_token: str):
    """
    Handle insurance policy selection intent
    Shows insurance type selection menu to user

    Note: User query is already saved to MongoDB at line 5034 before this function is called,
    so we don't need to save it again here to avoid duplicates.
    """
    try:
        # Show insurance type selection menu
        result = await route_enhanced_chatbot(
            action="select_insurance_type",
            session_id=chat_session_id,
            access_token=access_token,
            user_id=user_id
        )
        response_type = "selection_menu"
        action = "select_insurance_type"

        # Extract assistant response for MongoDB
        assistant_response = (
            result.get("response") or
            result.get("message") or
            result.get("title") or
            "Here are your insurance options"
        )

        # Save assistant response to MongoDB
        if mongodb_chat_manager:
            try:
                add_assistant_message_to_mongodb(
                    chat_session_id,
                    user_id,
                    assistant_response,
                    intent="insurance_plan",
                    context={
                        "action": action,
                        "response_type": response_type,
                        "has_options": bool(result.get("options"))
                    }
                )
                logger.info(f"✓ Saved assistant insurance response to MongoDB: {assistant_response[:50]}...")
            except Exception as e:
                logger.error(f"Error saving assistant insurance response to MongoDB: {e}")

        # Add required fields
        result["show_service_options"] = False
        result["chat_session_id"] = chat_session_id
        result["user_session_id"] = chat_session_id

        # Build standardized response
        return create_standardized_response(
            response_type="policy_selection",
            data=result,
            session_id=chat_session_id,
            metadata=metadata
        )

    except Exception as e:
        logger.error(f"Error in handle_insurance_policy_selection: {e}")
        error_result = {
            "response": f"Error processing insurance policy selection: {str(e)}",
            "action": "error",
            "show_service_options": True,
            "chat_session_id": chat_session_id,
            "user_session_id": chat_session_id
        }
        return create_standardized_response(
            response_type="error",
            data=error_result,
            session_id=chat_session_id,
            metadata=metadata
        )


async def handle_claim_guidance(
    query: str,
    insurance_type: str,
    chat_session_id: str,
    user_id: int,
    metadata: dict,
    was_regenerated: bool = False,
    original_user_session_id: str = None
):
    """
    Handle insurance claim guidance queries
    Provides step-by-step claim filing assistance
    """
    try:
        # Generate claim guidance response with insurance type
        guidance_response = generate_claim_guidance_response(query, insurance_type, [])

        result = {
            "response": guidance_response,
            "action": "claim_guidance",
            "show_service_options": False,
            "chat_session_id": chat_session_id,
            "user_session_id": chat_session_id,
            "insurance_type": insurance_type,
            "session_regenerated": was_regenerated,
            "suggestions": [
                "What documents do I need for a claim?",
                "How long does claim processing take?",
                "Track my claim status"
            ]
        }

        # Add original session ID if regenerated
        if was_regenerated and original_user_session_id:
            result["original_session_id"] = original_user_session_id

        return create_standardized_response(
            response_type="claim_guidance",
            data=result,
            session_id=chat_session_id,
            metadata=metadata
        )

    except Exception as e:
        logger.error(f"Error in handle_claim_guidance: {e}")
        error_result = {
            "response": f"Error providing claim guidance: {str(e)}",
            "action": "error",
            "show_service_options": True,
            "chat_session_id": chat_session_id,
            "user_session_id": chat_session_id
        }
        return create_standardized_response(
            response_type="error",
            data=error_result,
            session_id=chat_session_id,
            metadata=metadata
        )


# ==================== DEEPSEEK API CONFIGURATION ====================
# DeepSeek API Key - Use environment variable or fallback
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

# Configure OpenAI client to use DeepSeek endpoint (OpenAI v1.0+)
from openai import OpenAI
deepseek_client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com"
)


# ==================== DEEPSEEK HELPER FUNCTIONS ====================

def extract_uin_from_text_deepseek(text: str) -> str:
    """Extract UIN (Unique Identification Number) from insurance document text using DeepSeek AI"""
    try:
        # Search entire document for UIN (use complete text)
        text_sample = text

        prompt = f"""
Extract the UIN (Unique Identification Number) from this Indian insurance document.

CRITICAL INSTRUCTIONS:
1. UIN is a mandatory alphanumeric code that identifies insurance products in India
2. Common UIN formats:
   - IRDAN157RP0033V02201920 (IRDAI format with prefix)
   - HDFHLIP21016V012122 (longer format with company prefix)
   - 117N097V02 (shorter format)
   - IRDA/NL-HLT/BAGI/P-H/V.I/320/13-14 (IRDA format with slashes)
3. Look for these labels ANYWHERE in the document:
   - "UIN:" or "UIN :"
   - "UIN Number" or "UIN No"
   - "Unique Identification Number"
   - "Product UIN"
   - "IRDAI UIN" or "IRDA UIN"
   - Near bottom of pages (footer area)
   - Near company registration details
4. SEARCH THE ENTIRE DOCUMENT - UIN can appear:
   - At the top (policy header)
   - In the middle (policy details)
   - At the bottom (footer/disclaimer section)
   - On add-on/rider details pages
   - Near IRDAI registration information

RESPONSE FORMAT:
- Return ONLY the UIN code (alphanumeric string with slashes if present)
- DO NOT include labels like "UIN:", "Product:", etc.
- If multiple UINs found, prefer the PRODUCT UIN (usually the longest one with IRDAN/IRDA prefix)
- If no UIN found, return exactly: NOT_FOUND

EXAMPLES:
Document: "UIN : IRDAN157RP0033V02201920"
Correct Response: IRDAN157RP0033V02201920

Document: "Product: Stand-Alone Own Damage Private Car Policy UIN : IRDAN157RP0033V02201920"
Correct Response: IRDAN157RP0033V02201920

Document: "UIN: HDFHLIP21016V012122"
Correct Response: HDFHLIP21016V012122

Document Text (Search the ENTIRE text below):
---
{text_sample}
---

Extract the UIN and return ONLY the UIN code (with slashes if present):"""

        response = deepseek_client.chat.completions.create(
            model="deepseek-reasoner",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert at extracting UIN from Indian insurance documents. Search the ENTIRE document including headers, body, footers, and add-on sections. Product UIN (with IRDAN/IRDA prefix) is the most important. Return ONLY the UIN alphanumeric code. Be extremely thorough. If you cannot find a UIN after searching everywhere, return 'NOT_FOUND'."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.0,
            max_tokens=300
        )

        uin_raw = response.choices[0].message.content.strip()
        logger.info(f"DeepSeek Raw response for UIN: {uin_raw}")

        # Clean up the response - remove common prefixes and labels
        uin = uin_raw.replace("UIN:", "").replace("UIN", "").replace(":", "").strip()
        uin = uin.replace("Number", "").replace("number", "").replace(" ", "").strip()

        # Remove quotes if present
        uin = uin.replace('"', '').replace("'", "")

        # Validate UIN format
        if uin == "NOT_FOUND" or uin == "NOTFOUND" or not uin:
            logger.warning("UIN not found in document using DeepSeek extraction")
            return None

        # Check minimum length (UINs are typically 10+ characters)
        if len(uin) < 8:
            logger.warning(f"Extracted UIN '{uin}' is too short (less than 8 characters). Likely invalid.")
            return None

        # Check if it contains alphanumeric characters (allow slashes for IRDA format)
        uin_cleaned = uin.replace("/", "").replace("-", "")
        if not any(c.isalpha() for c in uin_cleaned) or not any(c.isdigit() for c in uin_cleaned):
            logger.warning(f"Extracted UIN '{uin}' doesn't contain both letters and numbers. Likely invalid.")
            return None

        logger.info(f"✓ Successfully extracted UIN: {uin}")
        return uin

    except Exception as e:
        logger.error(f"Error extracting UIN using DeepSeek: {str(e)}")
        return None


def _extract_uin_regex(text: str) -> str:
    """
    Deterministic regex-based UIN extraction from insurance document text.
    Covers all common IRDAI UIN formats across health, motor, life, PA, travel.
    Used as a fallback when AI/DeepSeek extraction fails.
    """
    import re as _re_uin
    if not text:
        return None

    # Pattern 1: Explicit "UIN:" / "UIN Number:" / "UIN No:" label with separator
    # Handles: "UIN: ACKHLIP25035V022425", "UIN : IRDAN157RP0033V02201920"
    label_matches = _re_uin.findall(
        r'\bUIN\s*(?:Number|No\.?)?\s*[:\-]\s*([A-Z0-9][A-Z0-9/\-]{7,29})',
        text, _re_uin.IGNORECASE
    )
    for m in label_matches:
        m = m.strip().rstrip('.')
        if any(c.isalpha() for c in m) and any(c.isdigit() for c in m):
            return m.upper()

    # Pattern 2: IRDAN-prefixed format (e.g., IRDAN157RP0033V02201920)
    irdan_matches = _re_uin.findall(r'\b(IRDAN[A-Z0-9]{8,25})\b', text)
    if irdan_matches:
        return irdan_matches[0].upper()

    # Pattern 3: IRDA slash format (e.g., IRDA/NL-HLT/BAGI/P-H/V.I/320/13-14)
    irda_slash = _re_uin.findall(r'\b(IRDA/[A-Z]{2,4}-[A-Z]{2,4}/[A-Z0-9/\-\.]{4,30})\b', text)
    if irda_slash:
        return irda_slash[0].upper()

    # Pattern 4: "Unique Identification No." / "Unique Identification Number" — separator optional
    # Handles: "Unique Identification No. SHAHLIP25039V082425" (space only, no colon)
    #           "Unique Identification Number: HDFHLIP21016V012122"
    uid_matches = _re_uin.findall(
        r'Unique\s+Identification\s+(?:Number|No\.?)\s*[:\-]?\s+([A-Z0-9][A-Z0-9/\-]{7,29})',
        text, _re_uin.IGNORECASE
    )
    for m in uid_matches:
        m = m.strip().rstrip('.')
        if any(c.isalpha() for c in m) and any(c.isdigit() for c in m):
            return m.upper()

    # Pattern 5: "UIN No." / "UIN Number" with space only (no colon)
    # Handles: "UIN No. ACKHLIP25035V022425", "UIN Number HDFHLIP21016V012122"
    uin_nocolon = _re_uin.findall(
        r'\bUIN\s+(?:Number|No\.?)\s+([A-Z0-9][A-Z0-9/\-]{7,29})',
        text, _re_uin.IGNORECASE
    )
    for m in uin_nocolon:
        m = m.strip().rstrip('.')
        if any(c.isalpha() for c in m) and any(c.isdigit() for c in m):
            return m.upper()

    return None


def identify_policy_type_deepseek(text: str) -> str:
    """Identify policy type from document content using weighted keyword scoring.

    Uses a 2-phase approach:
      Phase 1 – Definitive keyword check: terms that ONLY appear in a specific
                policy type (e.g. "chassis no" is exclusively motor). A single
                match short-circuits to that type.
      Phase 2 – Weighted scoring across all types. Every keyword carries a
                weight (1-3). All types are scored simultaneously and the
                highest total wins. No early-return bias.

    Designed for the Indian insurance market – covers all major insurers
    (ICICI Lombard, HDFC ERGO, Bajaj Allianz, Tata AIG, New India, SBI General,
    Acko, Digit, Kotak, Iffco Tokio, Reliance, Royal Sundaram, Cholamandalam,
    National, Oriental, United India, etc.), policy structures, and IRDAI
    regulatory terminology.

    Handles cross-sell contamination (motor PDFs often include health/life ads).

    Supported types: health, motor, life, travel, home, pa, unknown
    """
    import logging as _log
    import re as _re
    _logger = _log.getLogger(__name__)
    text_lower = text.lower()
    # Normalize: collapse multiple whitespace, remove soft hyphens / zero-width
    # chars that break keyword matching for OCR-extracted text
    text_lower = _re.sub(r'[\u00ad\u200b\u200c\u200d\ufeff]', '', text_lower)
    text_lower = _re.sub(r'\s+', ' ', text_lower)

    _logger.info(">>> V2 WEIGHTED TYPE DETECTION RUNNING (not old priority-based) <<<")

    # ================================================================
    # PHASE 1 – DEFINITIVE KEYWORDS (single match → immediate return)
    # These terms exist ONLY in one policy type, never in cross-sell ads.
    # ================================================================

    # --- Motor definitive: terms exclusive to motor insurance ---
    motor_definitive = [
        # Policy structure sections
        'own damage premium', 'own damage policy period',
        'basic od premium', 'total own damage premium',
        'third party premium', 'total liability premium',
        'liability policy period',
        'section - i own damage', 'section - ii liability',
        'section i own damage', 'section ii liability',
        'section­i own damage', 'section­ii liability',
        # Vehicle identification
        'insured declared value', 'idv of vehicle', 'total idv',
        'chassis no', 'engine no',
        # Regulatory / Certificate of Insurance
        'motor vehicle act', 'motor vehicles act',
        'central motor vehicle rules', 'central motor vehicle',
        'form 51 of the central motor',
        'certificate of insurance and policy schedule',
        # Motor-only clauses
        'drivers clause', 'limitations as to use',
        'pa cover for owner driver', 'pa cover to owner driver',
        'compulsory pa cover for owner driver',
        'pa cover to unnamed passengers',
        'legal liability to paid driver',
        # Motor product names (Indian market)
        'auto secure', 'motor package policy',
        'private car package', 'two wheeler package',
        'commercial vehicle package',
        'standalone own damage', 'standalone od',
        # IMT endorsements (motor-only IRDAI endorsements)
        'imt 16', 'imt 22', 'imt 28', 'imt 07',
        'imt endorsement',
        # Motor add-on identifiers
        'engine secure', 'tyre secure', 'tyre protect',
        'return to invoice', 'depreciation reimbursement',
        'consumables expenses', 'consumable cover',
        'key replacement', 'key protect',
        'rim protect', 'windshield cover',
        'ncb protect', 'ncb protector',
        # Vehicle details table headers
        'cc/kw', 'mfg. year', 'mfg year',
        'rto location', 'rto code',
    ]
    motor_matches = [kw for kw in motor_definitive if kw in text_lower]
    if motor_matches:
        _logger.info(f">>> MOTOR DETECTED via Phase 1 definitive keywords: {motor_matches[:5]} <<<")
        return "motor"

    # --- Travel definitive: MUST be checked BEFORE health ---
    # Travel policies (especially from health insurers like Care Health) contain
    # many health keywords (hospitalization, cashless, pre-existing) that would
    # trigger health detection. Travel-exclusive terms must short-circuit first.
    travel_definitive = [
        # Product names (Indian market travel products)
        'explore asia', 'explore europe', 'explore worldwide',
        'travel guard', 'travel companion',
        'asia guard', 'asia guard gold', 'asiaguard',
        'travel protect', 'travel shield', 'travel secure',
        'travel infinity', 'travel elite', 'travel easy',
        'travel smart', 'star travel protect',
        'optima secure travel', 'travel max',
        # Travel-exclusive coverage terms
        'repatriation of mortal remains', 'loss of passport',
        'loss of checked-in baggage', 'checked-in baggage',
        'trip cancellation', 'trip interruption', 'trip delay',
        'trip curtailment',
        'baggage delay', 'baggage loss',
        'flight delay', 'hijack cover', 'hijack distress',
        'personal liability overseas', 'overseas medical',
        'country of travel', 'destination country',
        'schengen',
        'overseas mediclaim', 'overseas travel insurance',
        'loss of travel documents',
        'compassionate visit', 'sponsor protection',
        # Passport / travel document references
        'passport number', 'passport no',
        # Medical evacuation with repatriation (travel-exclusive combo)
        'medical evacuation and repatriation',
        # NOTE: 'geographical scope' and 'emergency medical evacuation' removed
        # from definitive — they appear in health policies as "Not Applicable"
        # fields. Kept in Phase 2 weighted scoring instead.
        # Currency-based sum insured (travel policies use foreign currency)
        'sum insured in usd', 'sum insured (usd)', 'sum insured (in usd)',
        'sum insured in eur', 'sum insured (eur)',
    ]
    travel_matches = [kw for kw in travel_definitive if kw in text_lower]
    if travel_matches:
        # Anti-pattern: health policies with travel add-ons (e.g. "Overseas Travel
        # Secure" in HDFC ERGO Optima) contain travel keywords but are fundamentally
        # health policies.  If MULTIPLE strong health indicators are present,
        # do NOT classify as travel — fall through to health check.
        health_anti_for_travel = [
            'family floater', 'cashless hospitalization', 'cashless treatment',
            'pre-hospitalization', 'post-hospitalization',
            'domiciliary hospitalization', 'day care procedure',
            'hospitalization expenses', 'room rent', 'icu charges',
            'mediclaim', 'medicare', 'sum insured restoration',
            'restore benefit', 'cumulative bonus', 'network hospital',
            'cashless facility',
        ]
        health_anti_travel_matches = [kw for kw in health_anti_for_travel if kw in text_lower]
        if len(health_anti_travel_matches) >= 3:
            _logger.info(
                f">>> Travel keywords found ({travel_matches[:5]}) but SKIPPED — "
                f"strong health signal ({len(health_anti_travel_matches)} anti-patterns): "
                f"{health_anti_travel_matches[:5]}. Falling through to health check. <<<"
            )
        else:
            _logger.info(f">>> TRAVEL DETECTED via Phase 1 definitive keywords: {travel_matches[:5]} <<<")
            return "travel"

    # --- PA (Personal Accident) definitive: checked BEFORE health ---
    # PA/Guard plans from health insurers contain health keywords but are
    # fundamentally accident-only products with different scoring needs.
    pa_definitive = [
        'personal accident', 'personal accident cover',
        'personal guard', 'global personal guard',
        'accidental death benefit', 'accidental death and disablement',
        'accidental death',  # shorter form – PDF may say "Accidental Death 100% of SI"
        'permanent total disablement', 'permanent partial disablement',
        'permanent total disability benefit',
        'permanent partial disability benefit',
        'permanent total disability', 'permanent partial disability',
        'temporary total disablement', 'temporary total disability',
        'pa owner driver', 'group personal accident',
        'group care 360',  # EAZR company PA product
        'capital sum insured',  # PA-specific term for sum insured
    ]
    pa_matches = [kw for kw in pa_definitive if kw in text_lower]
    if len(pa_matches) >= 2:
        # PA-only keywords: if ANY of these match, it's definitely a PA policy
        # regardless of any health keywords (e.g. "cashless facility" in PA certs).
        pa_only_keywords = [
            'group care 360', 'personal guard', 'global personal guard',
            'group personal accident', 'pa owner driver',
        ]
        has_pa_only = any(kw in text_lower for kw in pa_only_keywords)

        if has_pa_only:
            _logger.info(f">>> PA DETECTED via PA-only keyword + definitive: {pa_matches[:5]} <<<")
            return "pa"

        # Anti-pattern: health policies with accident riders also match PA keywords.
        # If MULTIPLE strong health indicators are present, do NOT classify as PA.
        # Require >= 3 health anti-pattern matches to override PA (single matches
        # like "cashless facility" can appear in PA certificates too).
        health_anti_patterns = [
            'family floater', 'cashless hospitalization', 'cashless treatment',
            'pre-hospitalization', 'post-hospitalization',
            'domiciliary hospitalization', 'day care procedure',
            'hospitalization expenses', 'room rent', 'icu charges',
            'mediclaim', 'medicare', 'sum insured restoration',
            'restore benefit', 'cumulative bonus', 'network hospital',
        ]
        health_anti_matches = [kw for kw in health_anti_patterns if kw in text_lower]
        if len(health_anti_matches) >= 3:
            _logger.info(
                f">>> PA keywords found ({pa_matches[:5]}) but SKIPPED — "
                f"strong health signal ({len(health_anti_matches)} anti-patterns): "
                f"{health_anti_matches[:5]}. Falling through to health check. <<<"
            )
        else:
            _logger.info(f">>> PA DETECTED via Phase 1 definitive keywords: {pa_matches[:5]} <<<")
            return "pa"

    # --- Health definitive: terms exclusive to health insurance ---
    health_definitive = [
        'cashless hospitalization', 'cashless treatment',
        'cashless facility', 'network hospital',
        'pre-hospitalization', 'post-hospitalization',
        'domiciliary hospitalization', 'day care procedure',
        'family floater', 'sum insured restoration',
        'restore benefit', 'room rent limit',
        'icu charges', 'cumulative bonus',
        'mediclaim',
    ]
    if any(kw in text_lower for kw in health_definitive):
        return "health"

    # --- Life definitive ---
    life_definitive = [
        'sum assured', 'life assured', 'death benefit',
        'maturity benefit', 'surrender value',
        'mortality charge', 'fund value',
    ]
    if any(kw in text_lower for kw in life_definitive):
        return "life"

    # ================================================================
    # PHASE 2 – WEIGHTED SCORING (all types scored, highest wins)
    # Weight 3 = strong indicator, 2 = moderate, 1 = weak / shared term
    # ================================================================

    def _calc(kw_weights: dict, txt: str) -> int:
        return sum(w for kw, w in kw_weights.items() if kw in txt)

    # --- Motor keywords (comprehensive Indian market) ---
    motor_kw = {
        # Core motor terms
        'idv': 3, 'own damage': 3, 'third party liability': 3,
        'zero depreciation': 3, 'nil depreciation': 3,
        'vehicle insurance': 3, 'motor insurance': 3,
        'car insurance': 3, 'bike insurance': 3,
        'package policy': 2, 'comprehensive policy': 2,
        'third party only': 3, 'tp only': 3,
        'motor vehicle': 2,
        # Vehicle identification
        'chassis number': 3, 'engine number': 3,
        'registration number': 2, 'registration no': 2,
        'vehicle make': 2, 'vehicle model': 2,
        'make/model': 2, 'body type': 2, 'fuel type': 2,
        'cubic capacity': 2, 'manufacturing year': 2,
        'seating capacity': 2, 'geographical area': 2,
        'hypothecation': 2, 'hire purchase': 2,
        # Motor-specific add-ons
        'roadside assistance': 1, 'road side assistance': 1,
        'personal accident cover for owner': 2,
        'unnamed passengers': 2,
        'electrical accessories': 1, 'non-electrical accessories': 1,
        'bi-fuel': 1, 'cng kit': 1, 'lpg kit': 1,
        'loss of personal belongings': 1,
        'emergency transport': 1, 'hotel expenses': 1,
        # Premium structure
        'od premium': 2, 'tp premium': 2,
        'voluntary deductible': 2, 'compulsory deductible': 2,
        'imposed excess': 2,
        'no claim bonus': 1,  # shared with health, lower weight
        # Vehicle types
        'private car': 2, 'two wheeler': 2, 'four wheeler': 2,
        'commercial vehicle': 2, 'goods carrying': 2,
        'passenger carrying': 2, 'three wheeler': 2,
        'electric vehicle': 1,
        # Regulatory
        'certificate of insurance': 2,
    }

    # --- Health keywords (refined – removed motor-ambiguous terms) ---
    health_kw = {
        'hospitalization': 3,
        'room rent': 3, 'sub-limit': 2,
        'pre-existing disease': 3, 'waiting period': 2,
        'copay': 2, 'co-pay': 2,
        'daycare': 2, 'ambulance cover': 2,
        'health checkup': 2, 'ayush': 2,
        'organ donor': 2, 'maternity benefit': 2,
        'floater': 2,
        'health insurer': 2,
        # Lower weight – appear in motor cross-sell ads
        'medical expenses': 1,
        'health insurance': 1,
        # 'deductible' REMOVED – appears in motor policies too
    }

    # --- Life keywords ---
    life_kw = {
        'life insurance': 3, 'term insurance': 3, 'endowment': 3,
        'whole life': 3, 'life cover': 3,
        'ulip': 3, 'term plan': 3,
        'money back': 2, 'annuity': 2, 'pension plan': 2,
    }

    # --- Travel keywords (expanded for Indian travel insurance market) ---
    travel_kw = {
        'travel insurance': 3, 'trip insurance': 3,
        'overseas travel': 3, 'international travel': 3,
        'flight delay': 3, 'baggage loss': 3,
        'trip cancellation': 3, 'medical evacuation': 3,
        'passport loss': 2, 'loss of passport': 3,
        'repatriation': 3, 'baggage delay': 3,
        'trip delay': 3, 'trip interruption': 3,
        'trip curtailment': 3,
        'country of travel': 3, 'destination country': 3,
        'geographical scope': 2, 'schengen': 3,
        'checked-in baggage': 3, 'hijack': 2,
        'overseas medical': 2, 'personal liability overseas': 3,
        'explore asia': 3, 'explore europe': 3,
        'asia guard': 3, 'travel guard': 3,
        'compassionate visit': 3, 'loss of travel documents': 3,
        'sponsor protection': 2,
    }

    # --- PA (Personal Accident) keywords ---
    pa_kw = {
        'personal accident': 3, 'personal accident cover': 3,
        'accidental death': 3, 'accidental death benefit': 3,
        'permanent total disability': 3, 'permanent partial disability': 3,
        'permanent total disablement': 3, 'permanent partial disablement': 3,
        'temporary total disability': 3, 'temporary total disablement': 3,
        'capital sum insured': 2,
        'group personal accident': 3,
        'accidental death and disablement': 3,
        'personal guard': 3, 'global personal guard': 3,
        'pa cover': 2, 'pa insurance': 2,
        'disability schedule': 2, 'disablement schedule': 2,
        'scale of compensation': 2,
        'loss of limbs': 2, 'loss of sight': 2,
        'weekly benefit': 1, 'weekly compensation': 1,
    }

    # --- Home keywords ---
    home_kw = {
        'home insurance': 3, 'fire insurance': 3,
        'property insurance': 3, 'householder': 3,
        'building insurance': 3, 'contents insurance': 3,
        'burglary': 3, 'natural calamity': 2,
    }

    scores = {
        'motor': _calc(motor_kw, text_lower),
        'health': _calc(health_kw, text_lower),
        'life': _calc(life_kw, text_lower),
        'travel': _calc(travel_kw, text_lower),
        'home': _calc(home_kw, text_lower),
        'pa': _calc(pa_kw, text_lower),
    }

    max_type = max(scores, key=scores.get)
    if scores[max_type] == 0:
        return "unknown"

    return max_type


def fetch_policy_from_db_deepseek(uin: str, policy_type: str):
    """Fetch policy data and document_link from database based on UIN and policy type"""
    try:
        import psycopg2
        from psycopg2.extras import RealDictCursor

        # PostgreSQL Database Configuration
        DB_CONFIG = {
            "host": os.getenv("TYPEORM_HOST", "eazr.ca3p8fstvky1.ap-south-1.rds.amazonaws.com"),
            "user": os.getenv("TYPEORM_USERNAME", "postgres"),
            "password": os.getenv("TYPEORM_PASSWORD", "xpt7Wt9layPaEEfxinwU"),
            "database": os.getenv("TYPEORM_DATABASE", "insurance_data"),
            "port": int(os.getenv("TYPEORM_PORT", "5432"))
        }

        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Determine table name based on policy type
        table_map = {
            "health": "health_ins_masterdata",
            "life": "life_ins_masterdata",
            "non_life": "non_life_ins_masterdata"
        }

        table_name = table_map.get(policy_type)
        if not table_name:
            logger.warning(f"Unknown policy type: {policy_type}")
            return None

        # Query to fetch policy data including document_link (using exact column name "UIN")
        query = f'SELECT * FROM {table_name} WHERE "UIN" = %s LIMIT 1'
        cursor.execute(query, (uin,))
        result = cursor.fetchone()

        cursor.close()
        conn.close()

        if result:
            logger.info(f"Found policy in {table_name} with UIN: {uin}")
            result_dict = dict(result)

            # Check if document_link exists
            if 'document_link' in result_dict and result_dict['document_link']:
                logger.info(f"Document link found: {result_dict['document_link']}")
            else:
                logger.warning("No document_link found in database record")

            return result_dict
        else:
            logger.warning(f"No policy found in {table_name} with UIN: {uin}")
            return None

    except Exception as e:
        logger.error(f"Error fetching policy from database: {str(e)}")
        return None


def download_pdf_from_url_deepseek(url: str):
    """Download PDF from given URL and return as BytesIO"""
    try:
        import requests
        from io import BytesIO

        logger.info(f"Downloading PDF from URL: {url}")
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        pdf_buffer = BytesIO(response.content)
        logger.info(f"Successfully downloaded PDF from URL")
        return pdf_buffer
    except Exception as e:
        logger.error(f"Error downloading PDF from URL: {str(e)}")
        return None


def extract_text_from_pdf_buffer_deepseek(pdf_buffer) -> str:
    """Extract text from PDF buffer"""
    try:
        import PyPDF2
        import pdfplumber
        from io import BytesIO

        extracted_text = ""

        # Try PyPDF2 first
        pdf_reader = PyPDF2.PdfReader(pdf_buffer)
        for page in pdf_reader.pages:
            extracted_text += page.extract_text() + "\n"

        # If PyPDF2 fails, try pdfplumber
        if not extracted_text.strip():
            pdf_buffer.seek(0)
            with pdfplumber.open(pdf_buffer) as pdf:
                for page in pdf.pages:
                    extracted_text += page.extract_text() + "\n"

        logger.info(f"Extracted {len(extracted_text)} characters from PDF")
        return extracted_text
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {str(e)}")
        return ""


async def handle_insurance_pdf_analysis(
    files,
    user_id: int,
    chat_session_id: str,
    metadata: dict,
    was_regenerated: bool = False,
    original_session_id: str = None,
    vehicle_market_value: int = 500000,
    annual_income: int = 600000
):
    """
    Handle insurance PDF document analysis with gap analysis
    NEW: Uses AI-powered gap analysis with UIN extraction and T&C comparison

    Args:
        files: Uploaded file(s)
        user_id: User ID
        chat_session_id: Current session ID
        metadata: Request metadata
        was_regenerated: Whether session was regenerated
        original_session_id: Original session ID if regenerated
        vehicle_market_value: Vehicle market value (default: 500000)
        annual_income: Annual income (default: 600000)
    """
    try:
        import PyPDF2
        import pdfplumber
        import psycopg2
        from psycopg2.extras import RealDictCursor
        import requests
        from utils.pdf_report_generator import create_gap_analysis_pdf
        from io import BytesIO
        from datetime import datetime

        # Ensure files is a list
        if not isinstance(files, list):
            files = [files]

        # Process first file only
        file = files[0]
        file_content = await file.read()

        # Extract text from PDF
        extracted_text = ""
        try:
            pdf_file = BytesIO(file_content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)

            for page in pdf_reader.pages:
                extracted_text += page.extract_text() + "\n"

            # Fallback to pdfplumber if PyPDF2 fails
            if not extracted_text.strip():
                pdf_file.seek(0)
                with pdfplumber.open(pdf_file) as pdf:
                    for page in pdf.pages:
                        extracted_text += page.extract_text() + "\n"
        except Exception as e:
            logger.error(f"Error extracting PDF text: {e}")
            raise ValueError(f"Failed to extract text from PDF: {str(e)}")

        if not extracted_text.strip():
            raise ValueError("No text content found in the uploaded file")

        # Upload original PDF to S3
        from database_storage.s3_bucket import upload_pdf_to_s3
        import secrets
        timestamp = int(datetime.now().timestamp())
        original_pdf_filename = f"original_{user_id}_{timestamp}_{file.filename}"

        logger.info(f"Uploading original PDF to S3: {original_pdf_filename}")
        original_pdf_buffer = BytesIO(file_content)
        original_s3_result = upload_pdf_to_s3(original_pdf_buffer, original_pdf_filename, "raceabove-dev")

        original_file_url = None
        if isinstance(original_s3_result, dict) and original_s3_result.get('success'):
            original_file_url = original_s3_result.get('s3_url')
            logger.info(f"Original PDF uploaded successfully: {original_file_url}")
        else:
            logger.warning(f"Failed to upload original PDF to S3: {original_s3_result.get('error') if isinstance(original_s3_result, dict) else original_s3_result}")

        # Extract UIN from the document using DeepSeek
        extracted_uin = extract_uin_from_text_deepseek(extracted_text)
        logger.info(f"Extracted UIN from document: {extracted_uin}")

        # Identify policy type — Hibiscus 3-tier classifier
        from policy_analysis.classification import classify_policy as _hibiscus_classify
        from policy_analysis.classification import match_product_from_db, get_product_by_uin
        _cls_result = _hibiscus_classify(extracted_text, "", "", extracted_uin or "")
        policy_type = _cls_result.get_legacy_type()
        logger.info(
            f"Hibiscus classification: {policy_type} "
            f"(detail={_cls_result.policy_type.value}, "
            f"conf={_cls_result.confidence:.3f}, tier={_cls_result.tier_used})"
        )

        # Match against insurance_india PostgreSQL database
        db_match_result = await asyncio.to_thread(match_product_from_db, _cls_result)
        db_product_by_uin = None
        if extracted_uin:
            db_product_by_uin = await asyncio.to_thread(get_product_by_uin, extracted_uin)
        if db_match_result.get("matched"):
            logger.info(f"DB match: category_id={db_match_result['validation'].get('category_id')}, "
                        f"products={len(db_match_result.get('products', []))}")
        if db_product_by_uin:
            logger.info(f"DB UIN match: {db_product_by_uin.get('product_name', 'N/A')}")

        # Fetch policy data from database if UIN is found
        db_policy_data = None
        terms_and_conditions_text = ""

        if extracted_uin and policy_type != "unknown":
            db_policy_data = fetch_policy_from_db_deepseek(extracted_uin, policy_type)
            if db_policy_data:
                logger.info(f"Successfully fetched policy data from database for UIN: {extracted_uin}")

                # Download and extract terms & conditions PDF
                if 'document_link' in db_policy_data and db_policy_data['document_link']:
                    document_link = db_policy_data['document_link']
                    logger.info(f"Downloading terms & conditions PDF from: {document_link}")

                    terms_pdf_buffer = download_pdf_from_url_deepseek(document_link)
                    if terms_pdf_buffer:
                        terms_and_conditions_text = extract_text_from_pdf_buffer_deepseek(terms_pdf_buffer)
                        logger.info(f"Successfully extracted {len(terms_and_conditions_text)} characters from terms & conditions PDF")
                    else:
                        logger.warning("Failed to download terms & conditions PDF")
                else:
                    logger.warning("No document_link found in database record")
            else:
                logger.warning(f"Policy not found in database for UIN: {extracted_uin}")

        # ==================== UIN WEB ENRICHMENT ====================
        # If no T&C from database and PDF data is sparse, enrich via web search
        if not terms_and_conditions_text and extracted_uin:
            try:
                from services.uin_web_enrichment_service import is_data_insufficient, enrich_policy_via_uin, format_enrichment_for_prompt

                insufficient, insufficiency_reason = is_data_insufficient(extracted_text, policy_type=policy_type)
                if insufficient:
                    logger.info(f"UIN enrichment (chat): Data insufficient ({insufficiency_reason}), enriching via web for UIN {extracted_uin}")
                    enrichment_data = await enrich_policy_via_uin(
                        extracted_uin, policy_type,
                        extracted_text_snippet=(extracted_text or "")[:4000]
                    )
                    if enrichment_data:
                        enrichment_text = format_enrichment_for_prompt(enrichment_data)
                        # Use enriched T&C as the terms_and_conditions_text
                        # so the comparison prompt path is taken (richer analysis)
                        terms_and_conditions_text = enrichment_text
                        logger.info(f"UIN enrichment (chat): Populated T&C with {len(enrichment_text)} chars of web-enriched data")
                    else:
                        logger.info("UIN enrichment (chat): No enrichment data found, continuing with PDF data only")
            except Exception as e:
                logger.warning(f"UIN enrichment (chat): Failed ({e}), continuing with PDF data only")

        # Prepare prompt for DeepSeek
        if terms_and_conditions_text:
            # Enhanced comparison prompt with terminology awareness and accuracy checks
            prompt = f"""
You are an expert insurance analyst for the Indian market with deep IRDAI regulatory knowledge.

🚨 CRITICAL ACCURACY RULE:
Before identifying ANY gap, you must FIRST read the COMPLETE premium schedule/breakup section to see what coverages the policyholder ACTUALLY has. A "missing" coverage that's actually present is a SERIOUS ERROR.

MOST IMPORTANT RULES:
1. In Policy Summary and Coverage Details:
   - NEVER write "[Not found]", "[Not mentioned]", or any placeholder
   - If you cannot find data for a field, simply DO NOT include that bullet point
   - Skip the entire line if no data exists
   - The number of bullet points will vary — this is correct

2. Formatting Standards:
   - ALL monetary amounts MUST use ₹ with comma separators
   - Correct: ₹3,00,000 or ₹14,593.00
   - Wrong: ■3,00,000 or 3,00,000 or Rs 300000

3. Priority Actions Section:
   - Use bullet points (●), NOT numbered lists

4. **TERMINOLOGY AWARENESS (CRITICAL):**
   Insurance companies use DIFFERENT NAMES for the SAME coverage. Before declaring anything "missing":

   **Motor Insurance:**
   - Zero Depreciation = Depreciation Reimbursement = Nil Depreciation = Bumper to Bumper
   - NCB Protection = Bonus Protection = NCB Guard = Bonus Saver
   - Engine Protection = Engine Secure = Hydrostatic Lock Cover = Engine Guard
   - Return to Invoice = Invoice Protection = Total Loss Cover = IDV Protection
   - Roadside Assistance may appear as separate line item AFTER policy premium

   **Health Insurance:**
   - Room Rent Waiver = No Room Limit = Room Capping Waiver
   - Restoration = Sum Insured Reinstatement = Reload Benefit
   - Copay Waiver = Zero Copayment = No Copay

   **Life Insurance:**
   - Accidental Death = ADB Rider = Accidental Death Benefit
   - Critical Illness = CI Rider = Dread Disease Cover
   - Waiver of Premium = WOP Rider = Premium Exemption

5. **CALCULATION CHECKS:**
   - If receipt shows separate items AFTER total premium (e.g., "Roadside Assistance ₹136"), these are ADDITIONAL SERVICES properly itemized, NOT errors
   - Allow ±₹50-100 for rounding differences
   - Only flag calculation errors if >₹200 unexplained difference

6. **REGULATORY COMPLIANCE:**
   - Third-party property ₹7.5L for cars = MEETS REGULATORY MINIMUM (not inadequate)
   - Owner PA ₹15L = MEETS REGULATORY MINIMUM (not inadequate)
   - If limit MEETS regulatory standard, it's COMPLIANT (can suggest higher as optional enhancement, but NOT a gap)

---

## 1. Policy Summary

Extract ONLY actual data found. Skip fields with no data.

- UIN (Unique Identification Number): {extracted_uin or '(search document)'}
- Policy Number: (only if found)
- Insurance Company: (only if found)
- Policy Type: (only if found)
- Policyholder Name: (only if found)
- Sum Assured/Coverage Amount: (Format: ₹3,00,000 - use ₹ and commas)
- Premium Amount: (Format: ₹14,593 annually - use ₹ and commas)
- Policy Start Date: (only if found)
- Policy End Date/Maturity Date: (only if found)
- Policy Term: (only if found)
- Premium Payment Term: (only if found)

---

## 2. Coverage Details

Include only if found:

- Base Coverage: (Format: ₹10,00,000 - use ₹ and commas)
- Active Riders/Add-ons: (list ALL you find in premium schedule/breakup - e.g., "Depreciation Reimbursement, Engine Secure, Return to Invoice")
- Key Benefits Covered: (only if found)
- Exclusions: (only if found)

---

## 3. Gap Analysis (Based on THIS Specific T&C Document)

**IMPORTANT: Before identifying gaps, FIRST do this:**
1. Read the COMPLETE "Premium Schedule" or "Schedule of Premium" or "Premium Breakup" section
2. List ALL coverages/add-ons/riders you find (with their codes like TA XX, IMT XX)
3. Check if each potential gap exists under a DIFFERENT NAME using the terminology list above
4. Only report a gap if it's GENUINELY missing after checking all alternative names

Identify 5-8 REAL, VERIFIED gaps by comparing the two documents.

For EACH gap:

**Gap 1: [Exact Coverage Name from T&C]**

WHAT'S IN T&C: [Cite specific section/clause from T&C where this coverage is offered]

WHAT POLICYHOLDER HAS: [State exactly what their current policy shows - be specific. Say "Has [coverage name] with ₹X premium" if present, or "Does not have this coverage" if genuinely missing]

THE GAP: [One clear sentence explaining what's missing or inadequate]

WHY IT MATTERS: [Financial impact and real-world Indian scenario]

EXAMPLE COST: [₹ formatted amount - e.g., ₹50,000 to ₹2,00,000]

---

**Gap 2-8:** [Same detailed format]

**CRITICAL REMINDERS:**
- If policy has "Depreciation Reimbursement" → they HAVE zero depreciation (just maybe limited)
- If policy has "Engine Secure" → they HAVE engine protection
- If policy has "Return to Invoice" → they HAVE invoice protection
- If receipt shows separate "Roadside Assistance" → it's properly itemized, NOT missing
- Third-party ₹7.5L = regulatory compliant (can suggest higher as enhancement, not gap)

---

## 4. Risk Assessment

Based on verified gaps from T&C comparison:
- High Risk Areas: [Based on actual missing coverages from T&C]
- Medium Risk Areas: [Based on actual gaps]
- IRDAI Compliance: [Any compliance notes from T&C]

---

## 5. Recommendations (Specific to This Policy)

Based on verified gaps:
- [Add specific rider/coverage that EXISTS in T&C but MISSING in policy]
- [Increase specific coverage that is LOWER than T&C allows]
- [Consider specific optional benefits available in T&C]

---

## 6. Priority Actions

Use bullet points (●), NOT numbers

- [Most urgent action based on verified gap]
- [Second priority action]
- [Third priority action]

---

**POLICYHOLDER'S ACTUAL POLICY DOCUMENT (COMPLETE):**
---
{extracted_text}
---

**THIS POLICY'S OFFICIAL TERMS & CONDITIONS (COMPLETE):**
---
{terms_and_conditions_text}
---

**FINAL ACCURACY CHECKS:**
1. Did I read the complete premium schedule before identifying gaps? ✓
2. Did I check for alternative coverage names using the terminology list? ✓
3. Did I verify that separate line items are properly itemized, not errors? ✓
4. Did I recognize regulatory minimums as compliant, not inadequate? ✓
5. Are all amounts formatted with ₹ symbol? ✓

REMEMBER: Only report gaps that are REAL, SPECIFIC, and VERIFIABLE from these documents. Better to miss a minor gap than report a FALSE one.
"""
        else:
            # Enhanced standard analysis prompt with terminology awareness
            prompt = f"""
You are an expert insurance analyst for the Indian market with deep IRDAI regulatory knowledge.

🚨 CRITICAL ACCURACY RULE:
Before identifying ANY gap, you must FIRST read the COMPLETE premium schedule/breakup section to see what coverages the policyholder ACTUALLY has. A "missing" coverage that's actually present is a SERIOUS ERROR.

MOST IMPORTANT RULES:
1. In Policy Summary and Coverage Details:
   - NEVER write "[Not found]", "[Not mentioned]", or any placeholder
   - If you cannot find data for a field, simply DO NOT include that bullet point at all
   - Skip the entire line/field if data is missing
   - The number of bullet points will vary - this is correct

2. Formatting Standards:
   - ALL monetary amounts MUST use ₹ symbol with comma separators
   - Correct: ₹3,00,000 or ₹14,593.00
   - Wrong: ■3,00,000 or 3,00,000 or 14593

3. Priority Actions Section:
   - Use bullet points (●) NOT numbered lists
   - Wrong: 1. Add coverage, 2. Increase limit
   - Correct: - Add coverage, - Increase limit

4. **TERMINOLOGY AWARENESS (CRITICAL):**
   Insurance companies use DIFFERENT NAMES for the SAME coverage. Check these equivalents:

   **Motor:**
   - Zero Depreciation = Depreciation Reimbursement = Nil Depreciation = Bumper to Bumper
   - NCB Protection = Bonus Protection = NCB Guard = Bonus Saver
   - Engine Protection = Engine Secure = Hydrostatic Lock = Engine Guard
   - Return to Invoice = Invoice Protection = Total Loss Cover

   **Health:**
   - Room Rent Waiver = No Room Limit = Room Capping Waiver
   - Restoration = SI Reinstatement = Reload Benefit
   - Copay Waiver = Zero Copayment

   **Life:**
   - Accidental Death = ADB Rider = AD Benefit
   - Critical Illness = CI Rider = Dread Disease
   - Waiver of Premium = WOP = Premium Exemption

5. **REGULATORY COMPLIANCE:**
   - Motor: TP Property ₹7.5L = COMPLIANT | Owner PA ₹15L = COMPLIANT
   - Health: PED waiting 2-4 years = STANDARD
   - Life: Suicide clause 1 year = STANDARD

---

## 1. Policy Summary

Extract ONLY actual data. Skip if missing.

- UIN: {extracted_uin or '(extract if found)'}
- Policy Number: (only if found)
- Insurance Company: (only if found)
- Policy Type: (only if found)
- Policyholder Name: (only if found)
- Sum Assured/Coverage: (₹5,00,000 format)
- Premium: (₹15,000 annually format)
- Policy Start Date: (only if found)
- Policy End Date: (only if found)
- Policy Term: (only if found)

---

## 2. Coverage Details

Only bullets for items found:

- Base Coverage: (₹5,00,000 format)
- Active Riders/Add-ons: (list ALL from premium schedule)
- Key Benefits: (only if found)
- Major Exclusions: (only if found)

---

## 3. Gap Analysis (Based on Indian Market Standards)

**BEFORE identifying gaps:**
1. Read complete "Premium Schedule" / "Premium Breakup" section
2. List ALL coverages/add-ons with codes (TA XX, IMT XX, etc.)
3. Check alternative names for each potential gap
4. Only report if GENUINELY missing after thorough check

Identify 5-8 VERIFIED, HIGH-IMPACT gaps:

**Gap 1: [Gap Name]**

Detailed explanation of the gap (2-4 sentences): what is missing or inadequate, why it matters for this policyholder, potential financial impact with specific amounts (₹1,00,000), and real-world scenario where this gap could cause problems.

**Gap 2: [Gap Name]**

[Same detailed format...]

**Continue for 5-8 gaps**

**CRITICAL CHECKS:**
- "Depreciation Reimbursement" in policy → they HAVE zero dep coverage
- "Engine Secure" in policy → they HAVE engine protection
- "Return to Invoice" in policy → they HAVE invoice cover
- Separate "Roadside Assistance" line → properly itemized, not missing
- TP ₹7.5L = compliant (can suggest higher, but not a gap)

---

## 4. Risk Assessment

- High Risk Areas: [Verified gaps with claim-blocking potential]
- Medium Risk Areas: [Verified gaps with significant impact]
- IRDAI Compliance: [Status]

---

## 5. Recommendations (India-Specific)

- [Specific action for verified gap]
- [Specific action for verified gap]
- [Specific action for verified gap]

---

## 6. Priority Actions

- [Most urgent verified action]
- [Second priority verified action]
- [Third priority verified action]

---

**POLICY DOCUMENT (COMPLETE):**
---
{extracted_text}
---

**ACCURACY CHECKS:**
1. Read complete premium schedule? ✓
2. Checked alternative coverage names? ✓
3. Verified separate line items? ✓
4. Recognized regulatory minimums? ✓
5. All amounts with ₹ symbol? ✓

REMEMBER: Only high-impact gaps (₹5,000+ or claim-blocking). Accuracy > Quantity.
"""

        # Call DeepSeek API
        try:
            # Adjust system message and max_tokens based on whether we have terms & conditions
            if terms_and_conditions_text:
                system_message = "You are an expert Indian insurance analyst with IRDAI knowledge. CRITICAL RULES: 1) Extract ACTUAL data from documents - NEVER use placeholders 2) ONLY include fields where you find real data 3) DO NOT write 'Not mentioned' - instead SKIP/OMIT that field entirely 4) Make the response DYNAMIC - if only 5 fields have data, show only those 5 5) Format ALL amounts with ₹ symbol and comma separators (₹3,00,000 NOT ■3,00,000 or 3,00,000) 6) Use bullet points in Priority Actions section, NOT numbered lists 7) Compare actual documents and cite specific sections."
                max_tokens = 6000
            else:
                system_message = "Expert Indian insurance analyst with IRDAI knowledge. CRITICAL: 1) Extract ONLY actual data you find 2) DO NOT include fields with 'Not mentioned' - SKIP them entirely 3) Make the summary DYNAMIC - only show fields with real values 4) Format ALL amounts with ₹ symbol and comma separators (₹5,00,000 NOT ■5,00,000) 5) Use bullet points (●) in Priority Actions, NOT numbered lists (1. 2. 3.) 6) NEVER use placeholders or templates. Your job: Show ONLY the data that exists with proper formatting."
                max_tokens = 4000

            # Use lower temperature for better instruction following
            temperature = 0.0 if terms_and_conditions_text else 0.1

            response = deepseek_client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {
                        "role": "system",
                        "content": system_message
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )

            analysis_report = response.choices[0].message.content

            # Log token usage
            input_tokens = response.usage.prompt_tokens if response.usage else 0
            output_tokens = response.usage.completion_tokens if response.usage else 0
            total_tokens = response.usage.total_tokens if response.usage else 0

            logger.info(f"========== TOKEN USAGE ==========")
            logger.info(f"Input Tokens:  {input_tokens}")
            logger.info(f"Output Tokens: {output_tokens}")
            logger.info(f"Total Tokens:  {total_tokens}")
            logger.info(f"=================================")

            # Log database policy information
            if db_policy_data:
                logger.info(f"========== DATABASE POLICY INFO ==========")
                logger.info(f"UIN: {extracted_uin}")
                logger.info(f"Policy Type: {policy_type}")
                logger.info(f"Table: {policy_type}_ins_masterdata")
                logger.info(f"Database Record Found: Yes")
                logger.info(f"Terms & Conditions Found: {'Yes' if terms_and_conditions_text else 'No'}")
                logger.info(f"Terms & Conditions Length: {len(terms_and_conditions_text)} chars")
                logger.info(f"Comparison Mode: {'ENABLED - Comparing with T&C' if terms_and_conditions_text else 'DISABLED - Standard analysis'}")
                logger.info(f"==========================================")
            else:
                logger.info(f"========== DATABASE POLICY INFO ==========")
                logger.info(f"UIN: {extracted_uin or 'Not found'}")
                logger.info(f"Policy Type: {policy_type}")
                logger.info(f"Database Record Found: No")
                logger.info(f"Comparison Mode: DISABLED - Standard analysis")
                logger.info(f"==========================================")

        except Exception as e:
            logger.error(f"Error calling DeepSeek API: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to generate analysis: {str(e)}")

        # Generate PDF report using shared generator for consistent styling
        pdf_buffer = create_gap_analysis_pdf(
            report_text=analysis_report,
            filename=file.filename,
            is_regenerated=False,
            uin=extracted_uin,
            policy_type=policy_type
        )

        # Upload to S3
        from database_storage.s3_bucket import upload_pdf_to_s3
        timestamp = int(datetime.now().timestamp())
        random_suffix = secrets.token_hex(4)  # Generate 8-character hex string
        report_filename = f"gap_analysis_{user_id}_{timestamp}.pdf"
        report_id = f"report_{user_id}_{timestamp}_{random_suffix}"  # Proper report ID format

        logger.info(f"Uploading gap analysis PDF to S3: {report_filename}")
        logger.info(f"Generated report_id: {report_id}")
        s3_result = upload_pdf_to_s3(pdf_buffer, report_filename, "raceabove-dev")
        logger.info(f"S3 upload result: {s3_result}")

        # Extract S3 URL from result
        report_url = None
        if isinstance(s3_result, dict):
            if s3_result.get('success'):
                report_url = s3_result.get('s3_url')
                logger.info(f"S3 upload successful: {report_url}")
            else:
                logger.error(f"S3 upload failed: {s3_result.get('error')}")
                report_url = None
        else:
            report_url = str(s3_result) if s3_result else None
            logger.warning(f"S3 result is not a dict: {type(s3_result)}")

        if not report_url:
            logger.error("Failed to get S3 URL for gap analysis report")

        # Store in MongoDB if available
        mongodb_id = None
        if mongodb_chat_manager:
            try:
                mongodb_id = mongodb_chat_manager.policy_analysis_collection.insert_one({
                    "report_id": report_id,  # Store the proper report_id
                    "user_id": user_id,
                    "session_id": chat_session_id,
                    "filename": file.filename,
                    "original_file_url": original_file_url,  # S3 URL for original uploaded PDF
                    "report_url": report_url,
                    "report_filename": report_filename,  # Store the S3 filename
                    "uin": extracted_uin,
                    "policy_type": policy_type,
                    "analysis_text": analysis_report,
                    "created_at": datetime.now(),
                    "metadata": metadata
                }).inserted_id
                logger.info(f"Stored analysis in MongoDB: {mongodb_id} with report_id: {report_id}")
            except Exception as e:
                logger.warning(f"Could not store in MongoDB: {e}")

        # Store structured report for RAG queries
        if mongodb_chat_manager and hasattr(mongodb_chat_manager, 'store_insurance_report'):
            try:
                # Parse the LLM-generated report to extract structured data
                def parse_gap_analysis_report(analysis_report: str) -> Dict[str, Any]:
                    """Extract structured data from gap analysis report text"""
                    import re

                    data = {
                        "protection_score": None,
                        "coverage_gaps": [],
                        "recommendations": []
                    }

                    # Extract protection score (look for patterns like "75/100", "Score: 75")
                    score_patterns = [
                        r'(?:score|rating)[:\s]+(\d+)(?:/100)?',
                        r'(\d+)/100',
                        r'(\d+)\s*%'
                    ]
                    for pattern in score_patterns:
                        match = re.search(pattern, analysis_report, re.IGNORECASE)
                        if match:
                            data["protection_score"] = int(match.group(1))
                            break

                    # Extract coverage gaps (look for Gap Analysis section)
                    gap_section_match = re.search(
                        r'##\s*\d*\.?\s*Gap Analysis.*?(?=##|\Z)',
                        analysis_report,
                        re.IGNORECASE | re.DOTALL
                    )
                    if gap_section_match:
                        gap_text = gap_section_match.group(0)
                        # Extract bullet points or numbered items
                        gap_items = re.findall(
                            r'[-*●]\s*\*\*(.*?)\*\*[:\s]*(.*?)(?=[-*●]|\n\n|\Z)',
                            gap_text,
                            re.DOTALL
                        )
                        for title, desc in gap_items[:8]:  # Limit to 8 gaps
                            gap_text = f"{title.strip()}: {desc.strip()[:200]}"
                            data["coverage_gaps"].append(gap_text)

                    # Extract recommendations (look for Recommendations section)
                    rec_section_match = re.search(
                        r'##\s*\d*\.?\s*Recommendations?.*?(?=##|\Z)',
                        analysis_report,
                        re.IGNORECASE | re.DOTALL
                    )
                    if rec_section_match:
                        rec_text = rec_section_match.group(0)
                        # Extract bullet points or numbered items
                        rec_items = re.findall(r'[-*●]\s*(.*?)(?=[-*●]|\n\n|\Z)', rec_text, re.DOTALL)
                        for rec in rec_items[:8]:  # Limit to 8 recommendations
                            clean_rec = rec.strip().replace('**', '')[:200]
                            if clean_rec:
                                data["recommendations"].append(clean_rec)

                    return data

                # Parse the report
                parsed_data = parse_gap_analysis_report(analysis_report)

                # Build complete report data for RAG
                report_data = {
                    "report_id": report_id,  # Include the proper report_id
                    "report_url": report_url,
                    "report_type": "gap_analysis",
                    "protection_score": parsed_data.get("protection_score"),
                    "coverage_gaps": parsed_data.get("coverage_gaps", []),
                    "recommendations": parsed_data.get("recommendations", []),
                    "policy_info": {
                        "filename": file.filename,
                        "uin": extracted_uin,
                        "policy_type": policy_type
                    },
                    "analysis_results": analysis_report,
                    "created_at": datetime.now().isoformat()
                }

                # Store in insurance_reports collection for RAG
                rag_report_id = mongodb_chat_manager.store_insurance_report(
                    user_id=user_id,
                    session_id=chat_session_id,
                    report_data=report_data
                )
                logger.info(f"✓ Stored insurance report for RAG: {rag_report_id}")

            except Exception as e:
                logger.warning(f"Could not store report for RAG: {e}")

        # Return standardized response
        logger.info(f"Preparing response with report_url: {report_url}")
        logger.info(f"Using report_id: {report_id}")

        # Flatten the analysis data to top level so create_standardized_response can pick it up
        response_data = {
            "response": "Insurance gap analysis completed successfully",
            "action": "insurance_analysis",
            "report_url": report_url,  # Place at top level for standardized response
            "report_id": report_id,  # Proper report ID format: report_{user_id}_{timestamp}_{random_hex}
            "mongodb_id": str(mongodb_id) if mongodb_id else None,
            "show_service_options": False,
            "chat_session_id": chat_session_id,
            "user_session_id": chat_session_id,
            # Also include nested analysis object for backward compatibility
            "analysis": {
                "filename": file.filename,
                "uin": extracted_uin,
                "policy_type": policy_type,
                "report_url": report_url,
                "report_id": report_id,
                "mongodb_id": str(mongodb_id) if mongodb_id else None,
                "has_terms_comparison": bool(terms_and_conditions_text),
                "analysis_summary": analysis_report[:500] + "..." if len(analysis_report) > 500 else analysis_report
            },
            "dbMatch": {
                "matched": db_match_result.get("matched", False),
                "categoryId": db_match_result.get("validation", {}).get("category_id"),
                "subcategoryId": db_match_result.get("validation", {}).get("subcategory_id"),
                "dbFields": db_match_result.get("db_fields"),
                "topProducts": db_match_result.get("products", [])[:3],
                "productByUin": db_product_by_uin,
            } if db_match_result.get("matched") else None
        }

        logger.info(f"Response data with report_url at top level: {report_url}")
        logger.info(f"Response data analysis section: {response_data['analysis']}")

        return create_standardized_response(
            response_type="insurance_analysis",
            data=response_data,
            session_id=chat_session_id,
            metadata={**metadata, "intent": "gap_analysis", "file_processed": True}
        )

    except Exception as e:
        logger.error(f"Error in handle_insurance_pdf_analysis: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")

        error_result = {
            "response": f"Error analyzing insurance document: {str(e)}",
            "action": "error",
            "show_service_options": True,
            "chat_session_id": chat_session_id,
            "user_session_id": chat_session_id
        }
        return create_standardized_response(
            response_type="error",
            data=error_result,
            session_id=chat_session_id,
            metadata=metadata
        )


async def handle_policy_analysis_conversation(query: str, chat_session_id: str, user_id: int, conversation_history: list):
    """
    Handle conversation about existing policy analysis
    Answers follow-up questions about analyzed policies
    """
    try:
        # Get latest policy analysis for user
        policy_analysis = get_user_latest_policy_analysis(user_id)

        if not policy_analysis:
            result = {
                "response": "I don't have any policy analysis on record. Would you like to upload a policy document for analysis?",
                "action": "no_policy_found",
                "show_service_options": True,
                "chat_session_id": chat_session_id
            }
        else:
            # Generate response based on policy analysis data
            policy_summary = policy_analysis.get("summary", "Your policy analysis is available.")

            # Simple response based on policy data
            contextual_response = f"Based on your policy analysis: {policy_summary}\n\nIs there anything specific you'd like to know about your policy?"

            result = {
                "response": contextual_response,
                "action": "policy_conversation",
                "show_service_options": False,
                "chat_session_id": chat_session_id,
                "policy_id": policy_analysis.get("policy_id")
            }

        return create_standardized_response(
            response_type="policy_conversation",
            data=result,
            session_id=chat_session_id,
            metadata=None
        )

    except Exception as e:
        logger.error(f"Error in handle_policy_analysis_conversation: {e}")
        error_result = {
            "response": f"Error handling policy conversation: {str(e)}",
            "action": "error",
            "show_service_options": True,
            "chat_session_id": chat_session_id,
            "user_session_id": chat_session_id
        }
        return create_standardized_response(
            response_type="error",
            data=error_result,
            session_id=chat_session_id,
            metadata=None
        )


def task_handler(task_type: str, **kwargs):
    """
    Generic task handler for various background tasks
    Routes tasks to appropriate handlers
    """
    try:
        if task_type == "insurance_policy_selection":
            return handle_insurance_policy_selection(**kwargs)
        elif task_type == "claim_guidance":
            return handle_claim_guidance(**kwargs)
        elif task_type == "policy_analysis":
            return handle_policy_analysis_conversation(**kwargs)
        else:
            logger.warning(f"Unknown task type: {task_type}")
            return {
                "status": "error",
                "message": f"Unknown task type: {task_type}"
            }
    except Exception as e:
        logger.error(f"Error in task_handler: {e}")
        return {
            "status": "error",
            "message": str(e)
        }


# ============= MAIN /ASK ENDPOINT =============

@router.post("/ask")
@limiter.limit(RATE_LIMITS["ask"])
async def ask_agent_unified(
    request: Request,  # Required for rate limiter
    # Form data parameters
    query: Optional[str] = Form(None),
    user_session_id: Optional[str] = Form(None),  # For authentication
    chat_session_id: Optional[str] = Form(None),  # For conversation thread
    session_id: Optional[str] = Form(None),  # Backward compatibility
    access_token: Optional[str] = Form(None),
    user_id: Optional[int] = Form(None),
    user_phone: Optional[str] = Form(None),
    email: Optional[str] = Form(None),  # Support OAuth users with email
    action: Optional[str] = Form(None),
    user_input: Optional[str] = Form(None),
    assistance_type: Optional[str] = Form(None),
    insurance_type: Optional[str] = Form(None),
    service_type: Optional[str] = Form(None),
    file_action: Optional[str] = Form(None),
    vehicle_market_value: Optional[float] = Form(None),
    annual_income: Optional[float] = Form(None),
    policy_id: Optional[str] = Form(None),
    application_id: Optional[str] = Form(None),
    edited_answers: Optional[str] = Form(None),
    model: Optional[str] = Form("policy_analysis"),  # Model type: policy_analysis, coverage_advisory, claim_support
    files: Optional[List[UploadFile]] = File(None),
    file: Optional[UploadFile] = File(None),  # Backward compatibility
):
    """
    Complete unified chat endpoint with STRICT guest user blocking

    RATE LIMITED: 30 requests per minute per user
    This prevents abuse of expensive LLM API calls.

    GUEST USERS CAN ONLY:
    - Send text messages (casual conversation)
    - Ask general questions
    - Get information about services

    AUTHENTICATED USERS CAN:
    - Upload and analyze files
    - Apply for loans/insurance
    - Access account services
    - Complete applications
    - All features

    MODEL TYPES:
    - policy_analysis (default): Standard policy analysis and general queries
    - coverage_advisory: Coverage recommendations and advisory
    - claim_support: Insurance claim guidance and support
    """
    try:
        current_timestamp = datetime.now().isoformat()
        
        # Import mongodb_chat_manager
        try:
            from database_storage.mongodb_chat_manager import mongodb_chat_manager
        except ImportError:
            mongodb_chat_manager = None
        
        # ============= STEP 1: DETERMINE USER AUTHENTICATION STATUS =============
        # Handle backward compatibility
        if not user_session_id and session_id:
            user_session_id = session_id
        
        is_guest = True
        was_regenerated = False
        original_user_session_id = None
        
        # Check if user has valid authentication
        if user_session_id:
            user_session_data = get_cached_session(user_session_id)
            
            if user_session_data and user_session_data.get('active'):
                # Valid session found
                if not user_id:
                    user_id = user_session_data.get('user_id')
                if not access_token:
                    access_token = user_session_data.get('access_token')
                if not user_phone:
                    user_phone = user_session_data.get('phone')
                if not email:
                    email = user_session_data.get('email')

                # Check if we have valid user_id and access_token
                if user_id and user_id > 0 and access_token:
                    is_guest = False
                    logger.info(f"Authenticated user detected - user_id: {user_id}")
                
                # Update session activity
                user_session_data['last_activity'] = current_timestamp
                store_session(user_session_id, user_session_data, expire_seconds=1296000)
                
            elif user_session_data:
                # Try regeneration
                original_user_session_id = user_session_id
                user_session_id, user_session_data, was_regenerated = session_manager.validate_and_regenerate_session(
                    user_session_id,
                    get_session,
                    store_session,
                    user_data={'user_id': user_id, 'access_token': access_token}
                )
                
                if was_regenerated and user_session_data:
                    user_id = user_session_data.get('user_id')
                    access_token = user_session_data.get('access_token')
                    user_phone = user_session_data.get('phone')
                    email = user_session_data.get('email')

                    if user_id and user_id > 0 and access_token:
                        is_guest = False
        
        # Additional check: if user_id and access_token provided directly
        if user_id and user_id > 0 and access_token and is_guest:
            is_guest = False
            logger.info(f"User authenticated via direct credentials - user_id: {user_id}")

        logger.info(f"=== USER STATUS: {'GUEST' if is_guest else 'AUTHENTICATED'} | user_id: {user_id} | has_token: {bool(access_token)} ===")

        # ============= STEP 1.5: SECURITY VERIFICATION FOR AUTHENTICATED USERS =============
        # If user is attempting to authenticate (has credentials), verify the access token
        new_access_token = None  # Track if we refreshed the token

        if not is_guest and should_verify_token(user_session_id, access_token, user_id):
            logger.info("Performing security verification for authenticated user")

            # Verify access token, user_id, phone/email match
            is_valid, error_message, token_payload = verify_user_authentication(
                access_token=access_token,
                user_id=user_id,
                user_phone=user_phone,
                email=email
            )

            if not is_valid:
                # Check if token expired but session is still valid - attempt token refresh
                if "expired" in error_message.lower() or "session has expired" in error_message.lower():
                    logger.info(f"Token expired for user_id: {user_id}, attempting token refresh...")

                    # Get session data to verify session is still valid
                    session_data_for_refresh = get_cached_session(user_session_id) if user_session_id else None

                    if session_data_for_refresh and session_data_for_refresh.get('active'):
                        # Session is still valid - refresh the token
                        try:
                            # Get user info from session or provided parameters
                            refresh_user_id = user_id or session_data_for_refresh.get('user_id')
                            refresh_phone = user_phone or session_data_for_refresh.get('phone', '')
                            refresh_name = session_data_for_refresh.get('user_name', 'User')
                            refresh_email = email or session_data_for_refresh.get('email')

                            if refresh_user_id:
                                # Create new JWT token
                                new_access_token = create_jwt_token(
                                    user_id=int(refresh_user_id),
                                    phone=refresh_phone,
                                    name=refresh_name
                                )

                                # Update access_token for this request
                                access_token = new_access_token

                                # Update session with new token
                                session_data_for_refresh['access_token'] = new_access_token
                                session_data_for_refresh['token_refreshed_at'] = current_timestamp
                                session_data_for_refresh['last_activity'] = current_timestamp
                                store_session(user_session_id, session_data_for_refresh, expire_seconds=1296000)

                                # Update user_id and phone if not set
                                if not user_id:
                                    user_id = refresh_user_id
                                if not user_phone:
                                    user_phone = refresh_phone
                                if not email:
                                    email = refresh_email

                                logger.info(f"✓ Token refreshed successfully for user_id: {refresh_user_id}")

                                # Mark as authenticated since we just refreshed the token
                                is_valid = True
                                error_message = None

                        except Exception as refresh_error:
                            logger.error(f"Token refresh failed: {refresh_error}")
                            # Continue to return auth error

                # If still not valid after refresh attempt, return error
                if not is_valid:
                    logger.warning(f"Authentication verification failed: {error_message}")

                    # Use chat_session_id if available, otherwise create temp session
                    error_session_id = chat_session_id if chat_session_id else f"error_{int(time.time())}"

                    return create_auth_error_response(
                        error_message=error_message,
                        session_id=error_session_id
                    )

            # Authentication successful - update user info from verified token
            logger.info(f"✓ Authentication verified successfully for user_id: {user_id}")

            # Update user_id, phone, and email from verified token payload (if not already set)
            if token_payload:
                if not user_id:
                    user_id = token_payload.get("id")
                if not user_phone:
                    user_phone = token_payload.get("contactNumber")
                if not email:
                    email = token_payload.get("email")

        # ============= STEP 2: HANDLE GUEST USERS WITH STRICT BLOCKING =============
        if is_guest:
            logger.warning(f"GUEST USER ACCESS ATTEMPT - Checking restrictions")
            
            # Create or use guest chat session
            if not chat_session_id:
                chat_session_id = f"guest_{int(time.time())}_{secrets.token_hex(4)}"
            
            guest_session_data = {
                'session_id': chat_session_id,
                'user_id': 0,
                'is_guest': True,
                'created_at': current_timestamp,
                'last_activity': current_timestamp,
                'active': True,
                'guest_mode': True
            }
            
            store_session(chat_session_id, guest_session_data, expire_seconds=3600)
            
            # ===== BLOCK 1: FILE UPLOADS (STRICTLY FORBIDDEN FOR GUESTS) =====
            if file or files:
                logger.warning("BLOCKED: Guest user attempted file upload")
                return create_standardized_response(
                    response_type="error",
                    data={
                        "error": "Authentication required",
                        "message": "Please login to upload and analyze insurance documents. Create a free account to unlock all features!",
                        "action": "auth_required",
                        "show_service_options": False,
                        "quick_actions": [
                            {"title": "Sign Up", "action": "signup"},
                            {"title": "Login", "action": "login"},
                            {"title": "Learn More", "action": "learn_more"}
                        ]
                    },
                    session_id=chat_session_id,
                    metadata={"is_guest": True, "intent": "guest_file_upload"}
                )
            
            # ===== BLOCK 2: RESTRICTED ACTIONS (FORBIDDEN FOR GUESTS) =====
            restricted_actions = [
                # Financial assistance
                "select_financial_assistance_type",
                "show_financial_assistance_eligibility",
                "start_financial_assistance_application",
                "start_loan_application",
                
                # Insurance
                "select_insurance_type",
                "show_insurance_eligibility",
                "start_insurance_application",
                "show_policy_details",
                "accept_policy_and_start_application",
                "review_application",
                "confirm_submit_application",
                "check_policy_status",
                "download_policy",

                # Wallet
                "start_wallet_setup",
                "wallet_setup",
                
                # Account services
                "check_balance",
                "view_transactions",
                "view_bills",
                "view_financial_assistance",
                "view_insurance",
                
                # Applications
                "continue_application",
                "submit_application",
                "cancel_application",
                "view_my_applications"
            ]
            
            if action and action in restricted_actions:
                logger.warning(f"BLOCKED: Guest user attempted restricted action: {action}")
                return create_standardized_response(
                    response_type="info",
                    data={
                        "response": "To access this feature, please create a free account. It only takes a minute!",
                        "message": "Authentication Required",
                        "action": "auth_required",
                        "show_service_options": False,
                        "quick_actions": [
                            {"title": "Sign Up Now", "action": "signup"},
                            {"title": "Login", "action": "login"},
                            {"title": "Learn More", "action": "learn_more"},
                            {"title": "Continue as Guest", "action": "continue_guest"}
                        ]
                    },
                    session_id=chat_session_id,
                    metadata={"is_guest": True, "intent": "guest_limitation", "blocked_action": action}
                )
            
            # ===== ALLOWED: TEXT QUERIES ONLY =====
            if query:
                # Add to guest conversation memory
                add_to_conversation_memory(chat_session_id, "user", query)
                conversation_history = get_conversation_history(chat_session_id, limit=4)
                combined_history = [
                    {'role': msg.get('role', 'user'), 'content': msg.get('content', ''),
                     'timestamp': msg.get('timestamp', current_timestamp)}
                    for msg in conversation_history
                ]
                
                # Detect intent
                intent = detect_intent_with_context(query, combined_history)
                logger.info(f"Guest Intent: {intent}")
                
                result = None
                
                # Block financial/insurance/wallet intents - require authentication
                if intent in ["financial_assistance", "insurance_plan", "wallet_setup", "task"]:
                    result = {
                        "response": "I'd be happy to help you with that! To access loans, insurance, account services, or wallet features, you'll need to create a free account first. It only takes a minute to sign up!",
                        "action": "auth_required",
                        "show_service_options": False,
                        "language": "en",
                        "quick_actions": [
                            {"title": "Sign Up Now", "action": "signup"},
                            {"title": "Login", "action": "login"},
                            {"title": "Learn More", "action": "learn_more"}
                        ],
                        "suggestions": [
                            "What types of loans do you offer?",
                            "Tell me about insurance options",
                            "How does the application process work?",
                            "What documents do I need?"
                        ]
                    }
                
                # Allow RAG queries (information about services)
                elif intent == "rag_query":
                    response = rag_handler(query)
                    result = {
                        "response": response.get("response", ""),
                        "action": "information_retrieved",
                        "source_documents": response.get("source_documents", []),
                        "show_service_options": False,
                        "language": "en",
                        "is_guest": True,
                        "suggestions": [
                            "What services are available?",
                            "How do I create an account?",
                            "Tell me about loan requirements",
                            "What insurance types do you offer?"
                        ]
                    }
                
                # Allow casual conversation - Use Advanced Human-Like System for guests too
                else:
                    # Generate human-like response with 6-message context
                    human_response = generate_human_like_response(
                        query=query,
                        conversation_history=combined_history[-6:],  # Last 6 messages
                        intent=intent,
                        language="en"
                    )

                    result = {
                        "response": human_response.get("response", ""),
                        "action": "casual_conversation",
                        "show_service_options": False,
                        "language": "en",
                        "is_guest": True,
                        "context_used": human_response.get("context_used", False),
                        "topics_discussed": human_response.get("topics_discussed", []),
                        "emotional_state": human_response.get("emotional_state", "neutral"),
                        "suggestions": human_response.get("suggestions", [
                            "What can you help me with?",
                            "How do I apply for a loan?",
                            "Tell me about insurance options",
                            "How do I create an account?"
                        ])
                    }
                
                # Add assistant response to memory
                if result:
                    add_to_conversation_memory(chat_session_id, "assistant", result.get("response", ""))
                    result["is_guest"] = True
                    result["guest_session_id"] = chat_session_id
                
                return create_standardized_response(
                    response_type="chat_message",
                    data=result,
                    session_id=chat_session_id,
                    metadata={"is_guest": True, "intent": intent, "original_query": query}
                )
            
            # Default guest greeting
            return create_standardized_response(
                response_type="guest_message",
                data={
                    "response": "Welcome! To access full features including chat history, loans, insurance, and personalized assistance, please create a free account.",
                    "action": "guest_greeting",
                    "show_service_options": False,
                    "language": "en",
                    "is_guest": True,
                    "quick_actions": [
                        {"title": "Sign Up Now", "action": "signup"},
                        {"title": "Login", "action": "login"},
                        {"title": "Learn More", "action": "learn_more"}
                    ],
                    "suggestions": [
                        "What services do you offer?",
                        "How do I create an account?",
                        "Tell me about loan requirements",
                        "What insurance types are available?"
                    ]
                },
                session_id=chat_session_id,
                metadata={"is_guest": True, "intent": "guest_greeting"}
            )
        
        # ============= AUTHENTICATED USER - FULL ACCESS =============
        logger.info(f"Processing AUTHENTICATED user - user_id: {user_id}")
        
        # Update user session activity
        if user_session_id:
            user_session_data = get_cached_session(user_session_id)
            if user_session_data:
                user_session_data['last_activity'] = current_timestamp
                store_session(user_session_id, user_session_data, expire_seconds=1296000)
        
        # ============= HANDLE CHAT SESSION =============
        chat_session_created = False
        chat_was_regenerated = False
        original_chat_session_id = None
        
        if chat_session_id:
            chat_session_data = get_cached_session(chat_session_id)

            if not chat_session_data or not chat_session_data.get('active'):
                # DO NOT regenerate chat_session_id - preserve the incoming one!
                # This ensures request chat_session_id matches response chat_session_id
                chat_session_created = True

                chat_session_data = {
                    'user_id': user_id,
                    'session_type': 'chat_session',
                    'created_at': current_timestamp,
                    'last_activity': current_timestamp,
                    'title': 'Chat Session',
                    'active': True,
                    'message_count': 0,
                    'user_session_id': user_session_id
                }

                # Store with the SAME chat_session_id from request
                store_session(chat_session_id, chat_session_data, expire_seconds=86400)

                if mongodb_chat_manager:
                    mongodb_chat_manager.create_new_chat_session(
                        user_id=user_id,
                        session_id=chat_session_id,  # Use same session_id
                        title="Chat Session"
                    )

                logger.info(f"Chat session created/restored: {chat_session_id}")
            else:
                # Session exists and is active - just update activity
                chat_session_data['last_activity'] = current_timestamp
                chat_session_data['message_count'] = chat_session_data.get('message_count', 0) + 1
                store_session(chat_session_id, chat_session_data, expire_seconds=86400)
                logger.info(f"Chat session continued: {chat_session_id}")
        
        elif user_id and (query or action or file):
            chat_session_id = f"chat_{user_id}_{int(time.time())}_{secrets.token_hex(4)}"
            chat_session_created = True
            
            chat_session_data = {
                'user_id': user_id,
                'session_type': 'chat_session',
                'created_at': current_timestamp,
                'last_activity': current_timestamp,
                'title': 'Auto Chat',
                'active': True,
                'message_count': 0,
                'user_session_id': user_session_id
            }
            
            store_session(chat_session_id, chat_session_data, expire_seconds=86400)
            
            if mongodb_chat_manager:
                result = mongodb_chat_manager.create_new_chat_session(
                    user_id=user_id,
                    session_id=chat_session_id,
                    title="Auto Chat"
                )
                if result.get("success"):
                    logger.info(f"Auto-created chat session: {chat_session_id}")
        
        # Initialize metadata
        metadata = {
            "message_id": hashlib.md5(f"{chat_session_id}_{query}_{current_timestamp}".encode()).hexdigest()[:16] if query else None,
            "original_query": query,
            "processed_query": query,
            "user_session_id": user_session_id,
            "chat_session_id": chat_session_id,
            "chat_session_created": chat_session_created,
            "chat_session_regenerated": False,  # Never regenerate - always preserve incoming ID
            "is_guest": False,
            "active_sessions": len([s for s in chatbot_sessions.values() if not s.completed]),
            "conversation_length": 0,
            "session_continuation": False,
            "context_used": False,
            "topics_discussed": [],
            "last_user_question": None,
            "language_detected": "en",
            "language_confidence": 1.0,
            "intent": None,
            "file_processed": False,
            "user_session_regenerated": was_regenerated,
            "original_user_session_id": original_user_session_id if was_regenerated else None,
            "original_chat_session_id": None,  # No longer regenerating chat sessions
            "timestamp": current_timestamp,
            "token_refreshed": new_access_token is not None,  # Indicates if token was refreshed
            "new_access_token": new_access_token  # New token if refreshed, None otherwise
        }
        
        # ============= HANDLE FILE UPLOADS (AUTHENTICATED ONLY) =============
        # Support both 'files' (new) and 'file' (backward compatibility)
        files_to_process = files if files else ([file] if file else None)

        if files_to_process:
            # Ensure it's a list
            files_list = files_to_process if isinstance(files_to_process, list) else [files_to_process]
            logger.info(f"File upload by authenticated user - user_id: {user_id}, files: {len(files_list)}")

            # Validate file types
            allowed_extensions = {'.pdf', '.png', '.jpg', '.jpeg', '.webp'}
            for f in files_list:
                file_ext = os.path.splitext(f.filename.lower())[1]
                if file_ext not in allowed_extensions:
                    return create_standardized_response(
                        response_type="error",
                        data={
                            "error": "Invalid file type",
                            "message": f"File '{f.filename}' has unsupported type. Allowed: PDF, PNG, JPG, JPEG, WEBP",
                            "action": "file_error",
                            "show_service_options": False
                        },
                        session_id=chat_session_id,
                        metadata={**metadata, "intent": "file_upload_error"}
                    )

            metadata["file_processed"] = True


            if file_action == "analyze_insurance_dynamic":
                # Store user message (file upload action)
                if mongodb_chat_manager:
                    user_message_content = f"Uploaded insurance policy file: {files_list[0].filename}"
                    add_user_message_to_mongodb(
                        chat_session_id,
                        user_id,
                        user_message_content,
                        intent="file_upload_dynamic_analysis",
                        context={
                            "filename": files_list[0].filename,
                            "file_action": file_action
                        }
                    )
                    logger.info(f"✓ Saved user file upload to MongoDB: {user_message_content}")

                # Process the dynamic analysis
                analysis_response = await handle_insurance_analysis_dynamic(
                    files_list, user_id, chat_session_id, metadata, was_regenerated, original_user_session_id
                )

                # Store assistant message with report_url
                if mongodb_chat_manager and analysis_response.get("status") == "success":
                    response_data = analysis_response.get("data", {})
                    report_url = response_data.get("report_url")
                    report_id = response_data.get("report_id")

                    assistant_message = (
                        f"I've completed your insurance analysis. "
                        f"Your protection score report is ready."
                    )
                    if report_url:
                        assistant_message += f" View your report: {report_url}"

                    add_assistant_message_to_mongodb(
                        chat_session_id,
                        user_id,
                        assistant_message,
                        intent="dynamic_analysis_complete",
                        context={
                            "action": "insurance_analysis_dynamic",
                            "report_url": report_url,
                            "report_id": report_id,
                            "mongodb_id": response_data.get("mongodb_id"),
                            "filename": files_list[0].filename,
                            "file_action": file_action
                        }
                    )
                    logger.info(f"✓ Saved assistant analysis response to MongoDB with report_url: {report_url}")

                return analysis_response

            elif file_action == "analyze_pdf" or (query and query.lower() in ['protection score', 'quote_ka_court']):
                # Store user message (file upload action)
                if mongodb_chat_manager:
                    user_message_content = f"Uploaded insurance policy file: {files_list[0].filename}"
                    add_user_message_to_mongodb(
                        chat_session_id,
                        user_id,
                        user_message_content,
                        intent="file_upload_pdf_analysis",
                        context={
                            "filename": files_list[0].filename,
                            "file_action": file_action,
                            "vehicle_market_value": vehicle_market_value or 500000,
                            "annual_income": annual_income or 600000
                        }
                    )
                    logger.info(f"✓ Saved user file upload to MongoDB: {user_message_content}")

                # Process the PDF analysis
                analysis_response = await handle_insurance_pdf_analysis(
                    files_list, user_id, chat_session_id, metadata, was_regenerated, original_user_session_id,
                    vehicle_market_value or 500000,
                    annual_income or 600000
                )

                # Store assistant message with report_url
                if mongodb_chat_manager and analysis_response.get("status") == "success":
                    response_data = analysis_response.get("data", {})
                    report_url = response_data.get("report_url")
                    report_id = response_data.get("report_id")
                    analysis_data = response_data.get("analysis", {})

                    assistant_message = (
                        f"I've completed your insurance gap analysis. "
                        f"Your protection score report is ready."
                    )
                    if report_url:
                        assistant_message += f" View your report: {report_url}"

                    add_assistant_message_to_mongodb(
                        chat_session_id,
                        user_id,
                        assistant_message,
                        intent="gap_analysis_complete",
                        context={
                            "action": "insurance_analysis",
                            "report_url": report_url,
                            "report_id": report_id,
                            "mongodb_id": response_data.get("mongodb_id"),
                            "filename": analysis_data.get("filename"),
                            "policy_type": analysis_data.get("policy_type"),
                            "uin": analysis_data.get("uin"),
                            "file_action": file_action,
                            "vehicle_market_value": vehicle_market_value or 500000,
                            "annual_income": annual_income or 600000
                        }
                    )
                    logger.info(f"✓ Saved assistant analysis response to MongoDB with report_url: {report_url}")

                return analysis_response

            else:
                # Store user message (file upload action)
                if mongodb_chat_manager:
                    user_message_content = f"Uploaded insurance policy file: {files_list[0].filename}"
                    add_user_message_to_mongodb(
                        chat_session_id,
                        user_id,
                        user_message_content,
                        intent="file_upload_pdf_analysis",
                        context={
                            "filename": files_list[0].filename,
                            "file_action": "analyze_pdf",
                            "vehicle_market_value": vehicle_market_value or 500000,
                            "annual_income": annual_income or 600000
                        }
                    )
                    logger.info(f"✓ Saved user file upload to MongoDB: {user_message_content}")

                # Process the PDF analysis (default handler)
                analysis_response = await handle_insurance_pdf_analysis(
                    files_list, user_id, chat_session_id, metadata, was_regenerated, original_user_session_id,
                    vehicle_market_value or 500000,
                    annual_income or 600000
                )

                # Store assistant message with report_url
                if mongodb_chat_manager and analysis_response.get("status") == "success":
                    response_data = analysis_response.get("data", {})
                    report_url = response_data.get("report_url")
                    report_id = response_data.get("report_id")
                    analysis_data = response_data.get("analysis", {})

                    assistant_message = (
                        f"I've completed your insurance gap analysis. "
                        f"Your protection score report is ready."
                    )
                    if report_url:
                        assistant_message += f" View your report: {report_url}"

                    add_assistant_message_to_mongodb(
                        chat_session_id,
                        user_id,
                        assistant_message,
                        intent="gap_analysis_complete",
                        context={
                            "action": "insurance_analysis",
                            "report_url": report_url,
                            "report_id": report_id,
                            "mongodb_id": response_data.get("mongodb_id"),
                            "filename": analysis_data.get("filename"),
                            "policy_type": analysis_data.get("policy_type"),
                            "uin": analysis_data.get("uin"),
                            "file_action": "analyze_pdf",
                            "vehicle_market_value": vehicle_market_value or 500000,
                            "annual_income": annual_income or 600000
                        }
                    )
                    logger.info(f"✓ Saved assistant analysis response to MongoDB with report_url: {report_url}")

                return analysis_response
        
        # ============= HANDLE PROTECTION SCORE QUERIES =============
        if query and query.lower().strip() in ['quote_ka_court', 'protection score'] and not file:
            file_action_needed = "analyze_insurance_dynamic" if query.lower() == 'quote_ka_court' else "analyze_pdf"
            response_msg = ("Let's unlock your insurance insights! Upload your policy document in PDF format, and I'll analyze it." 
                          if query.lower() == 'quote_ka_court' 
                          else "Don't wait! Upload your insurance file and score to complete your audit quickly and easily.")
            
            return create_standardized_response(
                response_type="file_upload_request",
                data={
                    "message": "Please upload your insurance policy PDF for analysis",
                    "response": response_msg,
                    "action": "request_insurance_file_upload",
                    "file_action_needed": file_action_needed,
                    "show_service_options": False,
                    "language": "en"
                },
                session_id=chat_session_id,
                metadata={**metadata, "intent": "protection_score_request"}
            )
        
        # ============= HANDLE CLAIM GUIDANCE =============
        if query:
            claim_keywords = [
                'claim', 'settlement', 'reimbursement', 'cashless', 'claim process',
                'claim status', 'claim form', 'hospital bills', 'claim rejection',
                'claim approval', 'claim amount', 'insurance claim', 'how to claim'
            ]
            
            if any(keyword in query.lower() for keyword in claim_keywords):
                return await handle_claim_guidance(
                    query, insurance_type, chat_session_id, user_id, metadata, was_regenerated, original_user_session_id
                )
        
        # ============= HANDLE ACTIONS =============
        if action:
            actual_user_input = extract_actual_user_input(user_input) if user_input else None
            
            logger.info(f"ACTION: {action} | POLICY_ID: {policy_id} | USER_ID: {user_id}")
            
            # Review application
            if action == "review_application" and policy_id:
                from database_storage.mongodb_chat_manager import get_policy_application
                application_data = get_policy_application(user_id, policy_id)
                
                if not application_data:
                    return create_standardized_response(
                        response_type="error",
                        data={
                            "error": "Application not found",
                            "message": "Could not find your application data",
                            "action": "application_not_found"
                        },
                        session_id=chat_session_id,
                        metadata=metadata
                    )
                
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
                
                return create_standardized_response(
                    response_type="review_and_edit_application",
                    data={
                        "type": "review_and_edit_application",
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
                    },
                    session_id=chat_session_id,
                    metadata={**metadata, "intent": "review_and_edit_application"}
                )
            
            # Confirm submit with payment
            elif action == "confirm_submit_application" and policy_id:
                from database_storage.mongodb_chat_manager import get_policy_application, mongodb_chat_manager, complete_application
                application_data = get_policy_application(user_id, policy_id)
                
                if not application_data:
                    return create_standardized_response(
                        response_type="error",
                        data={
                            "error": "Application data not found",
                            "message": "Could not find your application data for submission",
                            "action": "submission_error"
                        },
                        session_id=chat_session_id,
                        metadata=metadata
                    )
                
                # Process edited answers if provided
                if edited_answers:
                    try:
                        if isinstance(edited_answers, str):
                            cleaned_json = edited_answers.strip()
                            if not (cleaned_json.startswith('[') and cleaned_json.endswith(']')):
                                raise ValueError("edited_answers must be a valid JSON array")
                            edited_data = json.loads(cleaned_json)
                        else:
                            edited_data = edited_answers
                        
                        if not isinstance(edited_data, list):
                            raise ValueError("edited_answers must be a list of answer objects")
                        
                        application_id = application_data.get("application_id")
                        if not application_id:
                            timestamp = int(datetime.now().timestamp())
                            application_id = f"APP_{policy_id}_{user_id}_{timestamp}"
                        
                        saved_count = 0
                        failed_updates = []
                        
                        for i, answer_obj in enumerate(edited_data):
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
                                
                                update_result = mongodb_chat_manager.policy_applications_collection.update_one(
                                    {"application_id": application_id},
                                    {
                                        "$set": {
                                            f"answers.q_{question_number}": {
                                                "question": question,
                                                "key": field_key,
                                                "type": question_type,
                                                "answer": cleaned_answer,
                                                "answered_at": datetime.now(),
                                                "updated_at": datetime.now(),
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
                                failed_updates.append(f"Question {question_number}: {str(update_error)}")
                        
                        if saved_count > 0:
                            mongodb_chat_manager.policy_applications_collection.update_one(
                                {"application_id": application_id},
                                {
                                    "$set": {
                                        "last_updated": datetime.now(),
                                        "status": "updated",
                                        "total_edited_answers": saved_count,
                                        "failed_updates": failed_updates if failed_updates else None
                                    }
                                }
                            )
                        
                        application_data = get_policy_application(user_id, policy_id)
                        
                        if saved_count == 0:
                            return create_standardized_response(
                                response_type="error",
                                data={
                                    "error": "No answers updated",
                                    "message": "Could not update any of the edited answers",
                                    "action": "update_failed",
                                    "details": failed_updates
                                },
                                session_id=chat_session_id,
                                metadata=metadata
                            )
                        
                    except Exception as parse_error:
                        return create_standardized_response(
                            response_type="error",
                            data={
                                "error": "Processing failed",
                                "message": f"Could not process the edited answers: {str(parse_error)}",
                                "action": "processing_error"
                            },
                            session_id=chat_session_id,
                            metadata=metadata
                        )
                
                # Build API payload
                api_payload = {
                    "insuranceId": int(policy_id),
                    "userId": str(user_id),
                    "userNumber": user_phone,
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
                
                import httpx
                import asyncio
                
                api_result = None
                payment_result = None
                payment_session_id = None
                order_id = None
                order_amount = None
                proposal_num = None
                
                async def create_policy_async():
                    max_retries = 3
                    retry_count = 0
                    
                    while retry_count < max_retries:
                        try:
                            async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as client:
                                response = await client.post(
                                    "https://api.prod.eazr.in/insurance-chatbot/policies",
                                    headers={"Content-Type": "application/json"},
                                    json=api_payload
                                )
                                
                                if response.status_code in [200, 201]:
                                    return response.json()
                                else:
                                    retry_count += 1
                                    if retry_count < max_retries:
                                        await asyncio.sleep(2)
                                    continue
                                        
                        except httpx.TimeoutException:
                            retry_count += 1
                            if retry_count < max_retries:
                                await asyncio.sleep(2)
                        except Exception as e:
                            retry_count += 1
                            if retry_count < max_retries:
                                await asyncio.sleep(2)
                    
                    return None
                
                async def process_payment_async(user_id, proposal_num):
                    max_retries = 3
                    retry_count = 0
                    
                    while retry_count < max_retries:
                        try:
                            payment_api_url = f"https://api.prod.eazr.in/insurance-chatbot/payments/{user_id}/{proposal_num}"
                            
                            async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as client:
                                response = await client.get(
                                    payment_api_url,
                                    headers={"Content-Type": "application/json"}
                                )
                                
                                if response.status_code in [200, 201]:
                                    return response.json()
                                else:
                                    retry_count += 1
                                    if retry_count < max_retries:
                                        await asyncio.sleep(2)
                                    continue
                                        
                        except httpx.TimeoutException:
                            retry_count += 1
                            if retry_count < max_retries:
                                await asyncio.sleep(2)
                        except Exception as e:
                            retry_count += 1
                            if retry_count < max_retries:
                                await asyncio.sleep(2)
                    
                    return None
                
                try:
                    api_result = await create_policy_async()
                    
                    if not api_result:
                        return create_standardized_response(
                            response_type="error",
                            data={
                                "error": "Policy Creation Failed",
                                "message": "Unable to create policy. Please try again later.",
                                "action": "api_timeout"
                            },
                            session_id=chat_session_id,
                            metadata=metadata
                        )
                    
                    proposal_num = api_result.get("data", {}).get("result", {}).get("proposalNum")
                    
                    if proposal_num:
                        await asyncio.sleep(2)
                        payment_result = await process_payment_async(user_id, proposal_num)
                        
                        if payment_result:
                            payment_session_id = payment_result.get("data", {}).get("result", {}).get("payment_session_id")
                            order_id = payment_result.get("data", {}).get("result", {}).get("order_id")
                            order_amount = payment_result.get("data", {}).get("result", {}).get("order_amount")
                    
                    session_key = f"{chat_session_id}_policy_application_{policy_id}"
                    if session_key in chatbot_sessions:
                        chatbot_sessions[session_key].complete_session()
                    
                    application_id = application_data.get("application_id")
                    if application_id and mongodb_chat_manager:
                        complete_application(application_id, {
                            "submitted_at": datetime.now().isoformat(),
                            "api_response": api_result,
                            "payment_session_id": payment_session_id,
                            "order_id": order_id,
                            "proposalNum": proposal_num,
                            "payment_status": "PAYMENT_PENDING" if payment_session_id else "NO_PAYMENT",
                            "submission_method": "api_submitted_with_payment" if payment_session_id else "api_submitted",
                            "edited_before_submission": bool(edited_answers),
                            "final_field_count": len(api_payload["fields"])
                        })
                    
                    return create_standardized_response(
                        response_type="application_completed",
                        data={
                            "type": "application_completed",
                            "message": "Your application has been submitted successfully!",
                            "application_id": application_id,
                            "reference_number": f"REF{datetime.now().strftime('%Y%m%d%H%M%S')}",
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
                        },
                        session_id=chat_session_id,
                        metadata={**metadata, "intent": "application_submitted"}
                    )
                    
                except Exception as api_error:
                    return create_standardized_response(
                        response_type="error",
                        data={
                            "error": "Processing Error",
                            "message": "An error occurred while processing your application. Please try again.",
                            "action": "processing_error",
                            "details": str(api_error)
                        },
                        session_id=chat_session_id,
                        metadata=metadata
                    )

            # Check policy status
            elif action == "check_policy_status":
                from database_storage.mongodb_chat_manager import mongodb_chat_manager

                # Fetch proposalNum from MongoDB policy_applications collection
                proposal_num = None
                application_data = None

                if policy_id:
                    # Get the application by policy_id and user_id
                    application_data = mongodb_chat_manager.policy_applications_collection.find_one(
                        {"user_id": user_id, "policy_id": policy_id},
                        sort=[("created_at", -1)]
                    )
                else:
                    # Get the most recent completed application
                    application_data = mongodb_chat_manager.policy_applications_collection.find_one(
                        {"user_id": user_id, "status": "completed"},
                        sort=[("completed_at", -1)]
                    )

                if application_data:
                    proposal_num = application_data.get("submission_details", {}).get("proposalNum")

                if not proposal_num:
                    return create_standardized_response(
                        response_type="error",
                        data={
                            "error": "Missing Proposal Number",
                            "message": "Proposal number is required to check policy status",
                            "action": "missing_proposal_num"
                        },
                        session_id=chat_session_id,
                        metadata=metadata
                    )

                import httpx

                async def check_status_async():
                    try:
                        status_url = f"https://api.prod.eazr.in/insurance-chatbot/policies/{user_id}/{proposal_num}/status"
                        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
                            response = await client.get(
                                status_url,
                                headers={"Content-Type": "application/json"}
                            )

                            if response.status_code in [200, 201]:
                                return response.json()
                            else:
                                return None
                    except Exception as e:
                        return None

                try:
                    status_result = await check_status_async()

                    if not status_result:
                        return create_standardized_response(
                            response_type="error",
                            data={
                                "error": "Status Check Failed",
                                "message": "Unable to retrieve policy status. Please try again later.",
                                "action": "status_check_failed"
                            },
                            session_id=chat_session_id,
                            metadata=metadata
                        )

                    policy_num = status_result.get("data", {}).get("policyNum")
                    policy_status = status_result.get("data", {}).get("result", {}).get("status", "PENDING")

                    # Update MongoDB with policyNum and policyStatus
                    if application_data:
                        application_id = application_data.get("application_id")
                        if application_id:
                            # Always update with latest status information
                            update_fields = {
                                "submission_details.policyStatus": policy_status,
                                "last_updated": datetime.now()
                            }
                            # Only update policyNum if we got it from API
                            if policy_num:
                                update_fields["submission_details.policyNum"] = policy_num

                            update_result = mongodb_chat_manager.policy_applications_collection.update_one(
                                {"application_id": application_id},
                                {"$set": update_fields}
                            )
                            logger.info(f"Updated policy application {application_id} with policyNum: {policy_num}, policyStatus: {policy_status}, matched: {update_result.matched_count}, modified: {update_result.modified_count}")

                    quick_actions = [
                        {"title": "Check Balance", "action": "check_balance"},
                        {"title": "Apply for Another Policy", "action": "select_insurance_type"}
                    ]

                    if policy_num:
                        quick_actions.insert(0, {
                            "title": "Download Policy",
                            "action": "download_policy",
                            "policyNum": policy_num,
                            "proposalNum": proposal_num
                        })

                    return create_standardized_response(
                        response_type="policy_status",
                        data={
                            "type": "policy_status",
                            "message": f"Policy status checked successfully",
                            "proposalNum": proposal_num,
                            "policyNum": policy_num,
                            "policyStatus": policy_status,
                            "status_details": status_result.get("data", {}).get("result", {}),
                            "quick_actions": quick_actions,
                            "show_service_options": False,
                            "chat_session_id": chat_session_id,
                            "user_session_id": user_session_id
                        },
                        session_id=chat_session_id,
                        metadata={**metadata, "intent": "policy_status_checked"}
                    )

                except Exception as status_error:
                    return create_standardized_response(
                        response_type="error",
                        data={
                            "error": "Processing Error",
                            "message": "An error occurred while checking policy status.",
                            "action": "processing_error",
                            "details": str(status_error)
                        },
                        session_id=chat_session_id,
                        metadata=metadata
                    )

            # Download policy
            elif action == "download_policy":
                import httpx
                from database_storage.mongodb_chat_manager import mongodb_chat_manager

                # Step 1: Fetch proposal_num from MongoDB
                proposal_num = None
                application_data = None

                if policy_id:
                    # Get the application by policy_id and user_id
                    application_data = mongodb_chat_manager.policy_applications_collection.find_one(
                        {"user_id": user_id, "policy_id": policy_id},
                        sort=[("created_at", -1)]
                    )
                else:
                    # Get the most recent completed application
                    application_data = mongodb_chat_manager.policy_applications_collection.find_one(
                        {"user_id": user_id, "status": "completed"},
                        sort=[("completed_at", -1)]
                    )

                if application_data:
                    submission_details = application_data.get("submission_details", {})
                    proposal_num = submission_details.get("proposalNum")

                if not proposal_num:
                    return create_standardized_response(
                        response_type="error",
                        data={
                            "error": "Proposal Number Not Found",
                            "message": "No proposal number found in your applications. Please complete a policy application first.",
                            "action": "proposal_not_found",
                            "quick_actions": [
                                {"title": "Apply for Insurance", "action": "select_insurance_type"},
                                {"title": "Check Balance", "action": "check_balance"}
                            ]
                        },
                        session_id=chat_session_id,
                        metadata=metadata
                    )

                # Step 2: Call status API to get policy_num using proposal_num
                async def get_policy_num_from_status_api():
                    try:
                        status_url = f"https://api.prod.eazr.in/policies/{user_id}/{proposal_num}/status"
                        logger.info(f"Fetching policyNum from status API: {status_url}")
                        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
                            response = await client.get(
                                status_url,
                                headers={"Content-Type": "application/json"}
                            )

                            logger.info(f"Status API response code: {response.status_code}")
                            if response.status_code in [200, 201]:
                                result = response.json()
                                logger.info(f"Status API response: {result}")
                                policy_num = result.get("data", {}).get("result", {}).get("policyNum")
                                logger.info(f"Extracted policyNum: {policy_num}")
                                return policy_num
                            else:
                                logger.error(f"Status API failed with status {response.status_code}: {response.text}")
                                return None
                    except Exception as e:
                        logger.error(f"Error fetching policyNum from status API: {str(e)}")
                        return None

                try:
                    # Fetch policy_num from status API
                    policy_num = await get_policy_num_from_status_api()

                    if not policy_num:
                        return create_standardized_response(
                            response_type="error",
                            data={
                                "error": "Policy Not Issued",
                                "message": "Your policy has not been issued yet. Please check back later or contact support.",
                                "action": "policy_not_issued",
                                "proposalNum": proposal_num,
                                "quick_actions": [
                                    {"title": "Check Policy Status", "action": "check_policy_status"},
                                    {"title": "Check Balance", "action": "check_balance"}
                                ]
                            },
                            session_id=chat_session_id,
                            metadata=metadata
                        )

                except Exception as e:
                    logger.error(f"Error in get_policy_num_from_status_api: {str(e)}")
                    return create_standardized_response(
                        response_type="error",
                        data={
                            "error": "Error Retrieving Policy",
                            "message": f"An error occurred while retrieving policy information: {str(e)}",
                            "action": "retrieval_error"
                        },
                        session_id=chat_session_id,
                        metadata=metadata
                    )

                # Now download the policy document
                async def download_policy_async():
                    try:
                        download_url = f"https://api.prod.eazr.in/insurance-chatbot/documents/{user_id}/{policy_num}"
                        logger.info(f"Downloading policy from URL: {download_url}")
                        async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as client:
                            response = await client.get(
                                download_url,
                                headers={"Content-Type": "application/json"}
                            )

                            logger.info(f"Download API response status: {response.status_code}")
                            if response.status_code in [200, 201]:
                                result = response.json()
                                logger.info(f"Download API response: {result}")
                                return result
                            else:
                                logger.error(f"Download API failed with status {response.status_code}: {response.text}")
                                return None
                    except Exception as e:
                        logger.error(f"Download policy error: {str(e)}")
                        return None

                try:
                    download_result = await download_policy_async()

                    if not download_result:
                        return create_standardized_response(
                            response_type="error",
                            data={
                                "error": "Download Failed",
                                "message": "Unable to download policy document. Please try again later.",
                                "action": "download_failed"
                            },
                            session_id=chat_session_id,
                            metadata=metadata
                        )

                    # Extract document URL from various possible response structures
                    result_data = download_result.get("data", {})
                    document_url = None
                    
                    if isinstance(result_data, dict):
                        result_obj = result_data.get("result", {})
                        document_url = (
                            result_obj.get("documentResponse") or
                            result_obj.get("documentUrl") or
                            result_obj.get("url") or
                            result_data.get("documentUrl") or
                            result_data.get("url")
                        )

                    logger.info(f"Extracted document URL: {document_url}")

                    if not document_url:
                        return create_standardized_response(
                            response_type="error",
                            data={
                                "error": "Document URL Not Found",
                                "message": "Policy document URL not found in response.",
                                "action": "url_not_found",
                                "response_data": download_result
                            },
                            session_id=chat_session_id,
                            metadata=metadata
                        )

                    return create_standardized_response(
                        response_type="policy_download",
                        data={
                            "type": "policy_download",
                            "message": "Your policy document is ready for download.",
                            "policyNum": policy_num,
                            "documentUrl": document_url,
                            "quick_actions": [
                                {"title": "Check Policy Status", "action": "check_policy_status", "proposalNum": proposal_num},
                                {"title": "Check Balance", "action": "check_balance"},
                                {"title": "Apply for Another Policy", "action": "select_insurance_type"}
                            ],
                            "show_service_options": False,
                            "chat_session_id": chat_session_id,
                            "user_session_id": user_session_id
                        },
                        session_id=chat_session_id,
                        metadata={**metadata, "intent": "policy_downloaded"}
                    )

                except Exception as download_error:
                    logger.error(f"Processing error in download_policy_async: {str(download_error)}")
                    return create_standardized_response(
                        response_type="error",
                        data={
                            "error": "Processing Error",
                            "message": "An error occurred while downloading policy document.",
                            "action": "processing_error",
                            "details": str(download_error)
                        },
                        session_id=chat_session_id,
                        metadata=metadata
                    )

            # Cancel application
            elif action == "cancel_application" and policy_id:
                # Save user action to MongoDB
                if mongodb_chat_manager:
                    try:
                        user_message_content = f"User cancelled application for policy {policy_id}"
                        add_user_message_to_mongodb(
                            chat_session_id,
                            user_id,
                            user_message_content,
                            intent="cancel_application"
                        )
                        logger.info(f"💾 Saved user action to MongoDB: {user_message_content[:50]}...")
                    except Exception as e:
                        logger.error(f"Error saving user action to MongoDB: {e}")

                session_key = f"{chat_session_id}_policy_application_{policy_id}"
                if session_key in chatbot_sessions:
                    chatbot_sessions[session_key].exit_session()

                if mongodb_chat_manager:
                    mongodb_chat_manager.policy_applications_collection.update_one(
                        {"user_id": user_id, "policy_id": policy_id},
                        {
                            "$set": {
                                "status": "cancelled",
                                "cancelled_at": datetime.now(),
                                "cancellation_reason": "user_cancelled"
                            }
                        }
                    )

                # Save assistant response to MongoDB
                assistant_response = "Your application has been cancelled successfully."
                if mongodb_chat_manager:
                    try:
                        add_assistant_message_to_mongodb(
                            chat_session_id,
                            user_id,
                            assistant_response,
                            intent="cancel_application",
                            context={
                                "action": "cancel_application",
                                "policy_id": policy_id,
                                "response_type": "application_cancelled"
                            }
                        )
                        logger.info(f"✓ Saved assistant response to MongoDB: {assistant_response[:50]}...")
                    except Exception as e:
                        logger.error(f"Error saving assistant response to MongoDB: {e}")

                return create_standardized_response(
                    response_type="application_cancelled",
                    data={
                        "type": "application_cancelled",
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
                    },
                    session_id=chat_session_id,
                    metadata={**metadata, "intent": "application_cancelled"}
                )
            
            # Show policy details
            elif action == "show_policy_details" and policy_id:
                # Save user action to MongoDB
                if mongodb_chat_manager:
                    try:
                        user_message_content = f"User requested policy details for policy ID: {policy_id}"
                        add_user_message_to_mongodb(
                            chat_session_id,
                            user_id,
                            user_message_content,
                            intent="show_policy_details"
                        )
                        logger.info(f"💾 Saved user action to MongoDB: {user_message_content[:50]}...")
                    except Exception as e:
                        logger.error(f"Error saving user action to MongoDB: {e}")

                result = await show_policy_details_from_stored_data(
                    policy_id,
                    chat_session_id,
                    access_token,
                    user_id
                )

                # Extract assistant response for MongoDB
                assistant_response = (
                    result.get("message") or
                    result.get("response") or
                    result.get("title") or
                    f"Here are the details for policy {policy_id}"
                )

                # Save assistant response to MongoDB
                if mongodb_chat_manager:
                    try:
                        add_assistant_message_to_mongodb(
                            chat_session_id,
                            user_id,
                            assistant_response,
                            intent="show_policy_details",
                            context={
                                "action": "show_policy_details",
                                "policy_id": policy_id,
                                "response_type": "policy_details"
                            }
                        )
                        logger.info(f"✓ Saved assistant response to MongoDB: {assistant_response[:50]}...")
                    except Exception as e:
                        logger.error(f"Error saving assistant response to MongoDB: {e}")

                result["chat_session_id"] = chat_session_id
                result["user_session_id"] = user_session_id

                return create_standardized_response(
                    response_type="policy_details",
                    data=result,
                    session_id=chat_session_id,
                    metadata={**metadata, "intent": "show_policy_details"}
                )
            
            # Start policy application
            elif action == "accept_policy_and_start_application" and policy_id:
                # Save user action to MongoDB
                if mongodb_chat_manager:
                    try:
                        user_message_content = f"User accepted policy {policy_id} and started application"
                        add_user_message_to_mongodb(
                            chat_session_id,
                            user_id,
                            user_message_content,
                            intent="start_policy_application"
                        )
                        logger.info(f"💾 Saved user action to MongoDB: {user_message_content[:50]}...")
                    except Exception as e:
                        logger.error(f"Error saving user action to MongoDB: {e}")

                result = await accept_policy_and_start_application(
                    chat_session_id,
                    policy_id,
                    access_token,
                    user_id
                )

                # NOTE: Do NOT save assistant response here!
                # The accept_policy_and_start_application() function already saves
                # the first question to MongoDB (enhanced_chatbot_handlers.py:2791)
                # Saving again here would create a duplicate message

                result["chat_session_id"] = chat_session_id
                result["user_session_id"] = user_session_id
                metadata={**metadata, "intent": "start_policy_application"}

                return create_standardized_response(
                    response_type="question",
                    data=result,
                    session_id=chat_session_id,
                    metadata={**metadata, "intent": "start_policy_application","chat_session_regenerated":False,"active_sessions":0,"original_chat_session_id":None}
                )
            
            # Check for active chatbot sessions
            if actual_user_input and action in ["start_financial_assistance_application", "start_insurance_application"]:
                assistance_type = assistance_type or "personal"
                insurance_type = insurance_type or "health"
                
                session_keys_to_check = []
                if action == "start_financial_assistance_application":
                    session_keys_to_check = [f"{chat_session_id}_financial_{assistance_type}"]
                elif action == "start_insurance_application":
                    session_keys_to_check = [f"{chat_session_id}_insurance_{insurance_type}"]
                
                for session_key in session_keys_to_check:
                    if session_key in chatbot_sessions and not chatbot_sessions[session_key].completed:
                        metadata["session_continuation"] = True
                        
                        try:
                            if action == "start_financial_assistance_application":
                                result = continue_financial_assistance_application(
                                    chat_session_id, assistance_type, actual_user_input, 
                                    access_token, user_id
                                )
                            else:
                                result = continue_insurance_application(
                                    chat_session_id, insurance_type, actual_user_input,
                                    access_token, user_id
                                )
                            
                            if result:
                                result["chat_session_id"] = chat_session_id
                                result["user_session_id"] = user_session_id
                                
                                response_type = "question"
                                if result.get("type") == "application_completed":
                                    response_type = "application_completed"
                                elif result.get("type") == "application_cancelled":
                                    response_type = "application_cancelled"
                                
                                return create_standardized_response(
                                    response_type=response_type,
                                    data=result,
                                    session_id=chat_session_id,
                                    metadata=metadata
                                )
                                
                        except Exception as continuation_error:
                            logger.error(f"Error in continuation: {continuation_error}")
            
            # Route other actions
            try:
                result = await route_enhanced_chatbot(
                    action=action,
                    session_id=chat_session_id,
                    user_input=actual_user_input,
                    access_token=access_token,
                    user_id=user_id,
                    assistance_type=assistance_type,
                    insurance_type=insurance_type,
                    service_type=service_type,
                    policy_id=policy_id
                )
                
                result["chat_session_id"] = chat_session_id
                result["user_session_id"] = user_session_id
                
                response_type = "general_response"
                if result.get("type") == "service_selection":
                    response_type = "selection_menu"
                elif result.get("type") == "financial_assistance_type_selection":
                    response_type = "selection_menu"
                elif result.get("type") == "insurance_type_selection":
                    response_type = "selection_menu"
                elif result.get("type") == "insurance_policy_selection":
                    response_type = "policy_selection"
                elif result.get("type") == "eligibility_details":
                    response_type = "eligibility_details"
                elif result.get("type") == "question":
                    response_type = "question"
                elif result.get("type") == "application_completed":
                    response_type = "application_completed"
                
                metadata["intent"] = action
                
                if MULTILINGUAL_AVAILABLE and result.get("response"):
                    result["response"] = translate_response(result["response"], chat_session_id)
                
                if actual_user_input:
                    add_to_conversation_memory(chat_session_id, "user", actual_user_input)
                if result.get("response"):
                    add_to_conversation_memory(chat_session_id, "assistant", result["response"])
                
                # Save to MongoDB - Enhanced to save ALL insurance/loan flow interactions
                if mongodb_chat_manager:
                    # Save user input/action - even if just action click
                    if actual_user_input:
                        user_message_content = actual_user_input
                    else:
                        # Create descriptive message for action-only clicks
                        action_descriptions = {
                            'select_insurance_type': 'User selected: I need insurance',
                            'show_insurance_eligibility': 'User requested insurance eligibility details',
                            'start_insurance_application': 'User started insurance application',
                            'select_financial_assistance_type': 'User selected: I need financial assistance',
                            'start_loan_application': 'User started loan application',
                            'start_wallet_setup': 'User initiated wallet setup',
                            'check_balance': 'User checked wallet balance',
                            'view_transactions': 'User viewed transactions',
                            'review_application': 'User reviewed application',
                            'confirm_submit_application': 'User confirmed application submission'
                        }
                        user_message_content = action_descriptions.get(action, f'User action: {action}')

                    add_user_message_to_mongodb(
                        chat_session_id,
                        user_id,
                        user_message_content,
                        intent=action
                    )
                    logger.info(f"✓ Saved user action to MongoDB: action={action}, message={user_message_content[:50]}...")

                    # Extract response text from result
                    response_text = (
                        result.get("response") or
                        result.get("message") or
                        result.get("title") or
                        f"Action performed: {action}"
                    )

                    # Build context with additional data
                    mongo_context = {
                        'action': action,
                        'response_type': result.get('type'),
                        'insurance_type': result.get('insurance_type') or insurance_type,
                        'assistance_type': result.get('assistance_type') or assistance_type,
                        'policy_id': result.get('policy_id') or policy_id,
                        'application_id': result.get('application_id'),
                        'has_options': bool(result.get('options'))
                    }

                    # Save assistant response with context
                    add_assistant_message_to_mongodb(
                        chat_session_id,
                        user_id,
                        response_text,
                        intent=action,
                        context=mongo_context
                    )
                    logger.info(f"✓ Saved assistant response to MongoDB: action={action}, response={response_text[:50] if response_text else 'None'}...")
                
                return create_standardized_response(
                    response_type=response_type,
                    data=result,
                    session_id=chat_session_id,
                    metadata=metadata
                )
                
            except Exception as routing_error:
                logger.error(f"Error in routing: {routing_error}")
                raise routing_error
        
        # ============= HANDLE TEXT QUERIES =============
        if query:
            add_to_conversation_memory(chat_session_id, "user", query)

            conversation_history = get_conversation_history(chat_session_id, limit=4)
            combined_history = [
                {
                    'role': msg.get('role', 'user'),
                    'content': msg.get('content', ''),
                    'timestamp': msg.get('timestamp', current_timestamp)
                } for msg in conversation_history
            ]
            
            use_context = should_use_context(query, combined_history)
            metadata["context_used"] = use_context
            metadata["conversation_length"] = len(combined_history)
            
            if use_context and mongodb_chat_manager:
                contextual_query = get_contextual_prompt_from_mongodb(chat_session_id, query)
            elif use_context:
                contextual_query = build_contextual_prompt(chat_session_id, query)
            else:
                contextual_query = query
            
            detected_language = "en"
            processing_query = query
            
            if MULTILINGUAL_AVAILABLE:
                language_result = process_user_input_with_language_detection(query, chat_session_id)
                detected_language = language_result['detected_language']
                english_query = language_result['english_query']
                set_user_language_preference(chat_session_id, detected_language)
                processing_query = english_query

                metadata["language_detected"] = detected_language
                metadata["language_confidence"] = language_result.get('confidence', 1.0)
                metadata["processed_query"] = processing_query

            # Check if there's an active Q&A session BEFORE saving user message
            # If there is, the Q&A handler will save the user answer itself
            has_active_qa_session = False
            for session_key in chatbot_sessions:
                if chat_session_id in session_key and not chatbot_sessions[session_key].completed:
                    has_active_qa_session = True
                    break

            # Only save user message if NOT in an active Q&A session
            # Q&A sessions save user answers inside their handlers (enhanced_chatbot_handlers.py:1675, 3038)
            if mongodb_chat_manager and not has_active_qa_session:
                user_message_id = add_user_message_to_mongodb(
                    chat_session_id, user_id, query, language=detected_language
                )
                metadata["message_id"] = user_message_id
            elif has_active_qa_session:
                logger.info(f"⏭️ Skipping user message save - active Q&A session will handle it")

            # Try to get cached intent first
            # Create a hash combining query and history for caching
            query_history_key = hashlib.md5(f"{processing_query}_{str(combined_history)}".encode()).hexdigest()
            intent = get_cached_intent(query_history_key)

            if intent is None:
                intent = detect_intent_with_context(processing_query, combined_history)
                logger.info(f"🎯 Detected Intent (new): {intent}")
            else:
                logger.info(f" Detected Intent (cached): {intent}")

            metadata["intent"] = intent
            metadata["model"] = model if model else "policy_analysis"

            result = None
            response_type = "chat_message"

            # ============= MODEL ROUTING =============
            # Route to specific model based on model parameter
            if model == "coverage_advisory":
                # Use coverage advisory model
                logger.info(f"Routing to coverage_advisory model for user {user_id}")
                try:
                    advisory_response = await generate_coverage_advisory_response(
                        query=processing_query,
                        user_id=user_id,
                        conversation_history=combined_history,
                        insurance_type=insurance_type
                    )

                    # Add to conversation memory
                    add_to_conversation_memory(chat_session_id, "assistant", advisory_response.get("response", ""))

                    # Store in MongoDB if available
                    if mongodb_chat_manager:
                        add_assistant_message_to_mongodb(
                            chat_session_id,
                            user_id,
                            advisory_response.get("response", ""),
                            intent="coverage_advisory",
                            language=detected_language
                        )

                    return create_standardized_response(
                        response_type="coverage_advisory",
                        data={
                            "message": "Coverage Advisory",
                            "response": advisory_response.get("response", ""),
                            "title": advisory_response.get("title", "Coverage Recommendations"),
                            "action": "coverage_advisory_completed",
                            "show_service_options": True,
                            "recommendations": advisory_response.get("recommendations", []),
                            "coverage_gaps": advisory_response.get("coverage_gaps", []),
                            "quick_actions": [
                                {"title": "Apply for Insurance", "action": "start_insurance_application"},
                                {"title": "Compare Policies", "action": "compare_policies"},
                                {"title": "Ask More Questions", "action": "continue_chat"}
                            ]
                        },
                        session_id=chat_session_id,
                        metadata={**metadata, "model": "coverage_advisory"}
                    )
                except Exception as e:
                    logger.error(f"Coverage advisory error: {str(e)}")
                    # Fall through to default handling

            elif model == "claim_support":
                # Use claim support model
                logger.info(f"Routing to claim_support model for user {user_id}")
                try:
                    claim_response = await handle_claim_guidance(
                        query=processing_query,
                        insurance_type=insurance_type,
                        chat_session_id=chat_session_id,
                        user_id=user_id,
                        metadata=metadata,
                        was_regenerated=was_regenerated,
                        original_session_id=original_user_session_id
                    )

                    return claim_response
                except Exception as e:
                    logger.error(f"Claim support error: {str(e)}")
                    # Fall through to default handling

            # Default: policy_analysis model (existing flow)
            # Continue with existing logic below

            # Check for active chatbot sessions
            print('###############',chatbot_sessions)
            active_sessions = []
            for session_key in chatbot_sessions:
                if chat_session_id in session_key and not chatbot_sessions[session_key].completed:
                    active_sessions.append({
                        "key": session_key,
                        "session": chatbot_sessions[session_key]
                    })
            
            if active_sessions:
                latest_session = active_sessions[-1]
                session_key = latest_session["key"]
                
                parts = session_key.split('_')
                chatbot_type = None
                service_type = None
                
                if "policy_application" in session_key:
                    chatbot_type = "policy_application"
                    service_type = parts[-1] if len(parts) >= 4 else None
                else:
                    known_types = ["financial", "insurance", "wallet"]
                    for i, part in enumerate(parts):
                        if part in known_types:
                            chatbot_type = part
                            if i + 1 < len(parts):
                                service_type = parts[i + 1]
                            break
                
                if chatbot_type == "wallet":
                    service_type = "setup"
                
                if chatbot_type and service_type:
                    try:
                        actual_user_input = extract_actual_user_input(processing_query) if processing_query else None
                        
                        if chatbot_type == "policy_application":
                            result = continue_policy_application(
                                chat_session_id, service_type, actual_user_input, access_token, user_id
                            )
                        elif chatbot_type == "financial":
                            result = continue_financial_assistance_application(
                                chat_session_id, service_type, actual_user_input, access_token, user_id
                            )
                        elif chatbot_type == "insurance":
                            result = continue_insurance_application(
                                chat_session_id, service_type, actual_user_input, access_token, user_id
                            )
                        elif chatbot_type == "wallet":
                            result = continue_wallet_setup(
                                chat_session_id, actual_user_input, access_token, user_id
                            )
                        
                        if result:
                            intent = result.get("action", "chatbot_continuation")
                            response_type = "question"
                            if result.get("type") == "application_completed":
                                response_type = "application_completed"
                            elif result.get("type") == "application_cancelled":
                                response_type = "application_cancelled"
                            elif result.get("type") == "review_application":
                                response_type = "review_application"
                            
                            result["show_service_options"] = False
                            result["language"] = detected_language
                            result["session_continuation"] = True
                            result["chat_session_id"] = chat_session_id
                            result["user_session_id"] = user_session_id
                            metadata["session_continuation"] = True
                            
                    except Exception as continuation_error:
                        logger.error(f"Error in continuation: {continuation_error}")
            
            if not result:
                if intent in ["greeting", "small_talk", "unknown"]:
                    # Use Advanced Human-Like Response System with 6-message context
                    logger.info(f"🤖 Using Advanced Human-Like Response System (context: {len(combined_history)} messages)")

                    human_response = generate_human_like_response(
                        query=contextual_query,
                        conversation_history=combined_history[-6:],  # Use last 6 messages
                        intent=intent,
                        language=detected_language
                    )

                    result = {
                        "response": human_response.get("response", ""),
                        "action": "casual_conversation",
                        "show_service_options": False,
                        "language": detected_language,
                        "context_used": human_response.get("context_used", use_context),
                        "suggestions": human_response.get("suggestions", generate_contextual_suggestions(combined_history)),
                        "topics_discussed": human_response.get("topics_discussed", []),
                        "emotional_state": human_response.get("emotional_state", "neutral"),
                        "chat_session_id": chat_session_id,
                        "user_session_id": user_session_id
                    }
                    response_type = "chat_message"
                
                elif intent == "protection_score":
                    result_data = get_user_latest_policy_analysis(str(user_id))
                    json_data = json.dumps(result_data, indent=4)
                    data = answer_protection_score_question(contextual_query, json_data)
                    
                    result = {
                        "response": data,
                        "action": "protection_score_response",
                        "show_service_options": False,
                        "language": detected_language,
                        "context_used": use_context,
                        "suggestions": generate_contextual_suggestions(combined_history),
                        "chat_session_id": chat_session_id,
                        "user_session_id": user_session_id
                    }
                    response_type = "protection_score"
                
                elif intent == "task":
                    if mongodb_chat_manager:
                        contextual_task_query = get_contextual_prompt_from_mongodb(chat_session_id, query)
                    else:
                        contextual_task_query = contextual_query
                    
                    task_response = task_handler(contextual_task_query, access_token, user_id)
                    
                    result = {
                        "response": task_response.get("response", ""),
                        "action": "task_completed",
                        "quick_actions": [
                            {"title": "Get Financial Help", "action": "select_financial_assistance_type"},
                            {"title": "Get Insurance", "action": "select_insurance_type"},
                            {"title": "Check Balance", "action": "check_balance"}
                        ],
                        "show_service_options": False,
                        "language": detected_language,
                        "chat_session_id": chat_session_id,
                        "user_session_id": user_session_id
                    }
                    response_type = "task_result"
                
                elif intent == "rag_query":
                    response = rag_handler(contextual_query)
                    
                    result = {
                        "response": response.get("response", ""),
                        "action": "information_retrieved",
                        "source_documents": response.get("source_documents", []),
                        "show_service_options": False,
                        "language": detected_language,
                        "chat_session_id": chat_session_id,
                        "user_session_id": user_session_id
                    }
                    response_type = "information"
                
                elif intent == "financial_education":
                    # Use Advanced Human-Like Response for financial education too
                    logger.info(f"📚 Financial Education with context awareness (context: {len(combined_history)} messages)")

                    # Get conversation context summary for better understanding
                    context_summary = get_conversation_context_summary(combined_history[-6:])

                    # Generate education response with context
                    education_response = generate_human_like_response(
                        query=contextual_query,
                        conversation_history=combined_history[-6:],
                        intent="financial_education",
                        language=detected_language
                    )

                    result = {
                        "response": education_response.get("response", generate_financial_education_response(contextual_query, combined_history)),
                        "action": "financial_education",
                        "show_service_options": False,
                        "language": detected_language,
                        "context_used": True,
                        "topics_discussed": context_summary.get("topics", []),
                        "suggestions": education_response.get("suggestions", generate_contextual_suggestions(combined_history)),
                        "chat_session_id": chat_session_id,
                        "user_session_id": user_session_id
                    }
                    response_type = "education"
                
                elif intent == "live_event":
                    try:
                        live_response = get_live_event_data(query)
                        result = {
                            "response": live_response,
                            "action": "live_event",
                            "show_service_options": False,
                            "language": detected_language,
                            "chat_session_id": chat_session_id,
                            "user_session_id": user_session_id
                        }
                        response_type = "live_information"
                    except Exception as e:
                        result = {
                            "response": "Sorry, I couldn't fetch live information right now.",
                            "action": "live_event_error",
                            "show_service_options": False,
                            "language": detected_language,
                            "chat_session_id": chat_session_id,
                            "user_session_id": user_session_id
                        }
                        response_type = "error"
                
                elif intent == "off_topic":
                    # Handle off-topic: briefly answer, then redirect to insurance
                    from ai_chat_components.processor import generate_off_topic_redirect_response
                    off_topic_response = generate_off_topic_redirect_response(contextual_query)

                    result = {
                        "response": off_topic_response,
                        "action": "off_topic_redirect",
                        "show_service_options": False,
                        "language": detected_language,
                        "suggestions": [
                            "Tell me about health insurance",
                            "How can I get a loan?",
                            "What insurance do I need?",
                            "Help me with financial planning"
                        ],
                        "chat_session_id": chat_session_id,
                        "user_session_id": user_session_id
                    }
                    response_type = "off_topic"

                elif intent == "financial_assistance":
                    # Show financial assistance type selection menu
                    result = await route_enhanced_chatbot(
                        action="select_financial_assistance_type",
                        session_id=chat_session_id,
                        access_token=access_token,
                        user_id=user_id
                    )
                    response_type = "selection_menu"

                    result["show_service_options"] = False
                    result["language"] = detected_language
                    result["chat_session_id"] = chat_session_id
                    result["user_session_id"] = user_session_id
                
                elif intent == "insurance_plan":
                    return await handle_insurance_policy_selection(
                        query, chat_session_id, user_id, metadata, access_token
                    )
                    # ============= INSURANCE NOT AVAILABLE - TEMPORARY =============
                    # TODO: Uncomment below code when insurance products are ready to sell
                    # return await handle_insurance_policy_selection(
                    #     query, chat_session_id, user_id, metadata, access_token
                    # )

                    # Currently not selling insurance - inform user
                    # insurance_not_available_msg = (
                    #     "Currently, we are not selling any insurance policies. "
                    #     "We are working on bringing you great insurance products in the near future. Stay tuned!"
                    # ) if detected_language == 'en' else (
                    #     "वर्तमान में, हम कोई बीमा पॉलिसी नहीं बेच रहे हैं। "
                    #     "हम भविष्य में आपके लिए बेहतरीन बीमा उत्पाद लाने पर काम कर रहे हैं। जुड़े रहें!"
                    # )

                    # result = {
                    #     "response": insurance_not_available_msg,
                    #     "action": "insurance_not_available",
                    #     "show_service_options": False,
                    #     "language": detected_language,
                    #     "quick_actions": [
                    #         {"title": "Get Financial Help", "action": "select_financial_assistance_type"},
                    #         {"title": "Check Balance", "action": "check_balance"},
                    #         {"title": "Talk to Support", "action": "help"}
                    #     ],
                    #     "suggestions": [
                    #         "What financial services do you offer?",
                    #         "I need a loan",
                    #         "Help me with my finances"
                    #     ],
                    #     "chat_session_id": chat_session_id,
                    #     "user_session_id": user_session_id
                    # }
                    # response_type = "chat_message"

                    # # Save to MongoDB
                    # if mongodb_chat_manager:
                    #     add_assistant_message_to_mongodb(
                    #         chat_session_id,
                    #         user_id,
                    #         insurance_not_available_msg,
                    #         intent="insurance_plan",
                    #         context={"action": "insurance_not_available", "language": detected_language}
                    #     )
                    # # ============= END INSURANCE NOT AVAILABLE =============

                elif intent == "insurance_analysis":
                    # ============= INSURANCE ANALYSIS INTENT =============
                    # User wants to analyze their existing insurance policy
                    # Show response with "Add Policy" button to redirect to frontend page

                    insurance_analysis_msg = (
                        "Great! I can help you analyze your insurance policy. "
                        "Please add your policy document and I'll provide a detailed analysis including coverage gaps, "
                        "protection score, and personalized recommendations."
                    ) if detected_language == 'en' else (
                        "बहुत अच्छा! मैं आपकी बीमा पॉलिसी का विश्लेषण करने में आपकी मदद कर सकता हूं। "
                        "कृपया अपना पॉलिसी दस्तावेज़ जोड़ें और मैं आपको कवरेज गैप, प्रोटेक्शन स्कोर, "
                        "और व्यक्तिगत सिफारिशों सहित विस्तृत विश्लेषण प्रदान करूंगा।"
                    )

                    result = {
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
                        "suggestions": [
                            "What is protection score?",
                            "How does policy analysis work?",
                            "What documents do I need?"
                        ] if detected_language == 'en' else [
                            "प्रोटेक्शन स्कोर क्या है?",
                            "पॉलिसी विश्लेषण कैसे काम करता है?",
                            "मुझे कौन से दस्तावेज़ चाहिए?"
                        ],
                        "chat_session_id": chat_session_id,
                        "user_session_id": user_session_id
                    }
                    response_type = "add_insurance_policy"

                    # NOTE: MongoDB save removed - generic save at end of function handles it
                    # This prevents duplicate assistant messages in chat history
                    # ============= END INSURANCE ANALYSIS INTENT =============

                elif intent == "policy_query":
                    # ============= POLICY QUERY INTENT =============
                    # User asking questions about their uploaded policies
                    # (coverage gaps, recommendations, policy count, details, etc.)
                    # Uses Redis-based flow state for multi-step conversation persistence

                    policy_query_result = await handle_policy_query(
                        user_id=str(user_id),
                        query=contextual_query,
                        language=detected_language,
                        session_id=chat_session_id,  # Pass session_id for flow state persistence
                        conversation_history=combined_history  # Pass conversation context for policy reference resolution
                    )

                    result = {
                        "response": policy_query_result.get("response", ""),
                        "action": "policy_query",
                        "show_service_options": False,
                        "language": detected_language,
                        "has_policies": policy_query_result.get("has_policies", False),
                        "policy_count": policy_query_result.get("policy_count", 0),
                        "self_count": policy_query_result.get("self_count", 0),
                        "family_count": policy_query_result.get("family_count", 0),
                        "flow_step": policy_query_result.get("flow_step", ""),  # Include flow step in response
                        "selected_member": policy_query_result.get("selected_member"),  # Include selected member if any
                        "family_members": policy_query_result.get("family_members", []),  # Include family members list
                        "policies": policy_query_result.get("policies", []),  # Include policies list
                        "portfolio_overview": policy_query_result.get("portfolio_overview", {}),
                        "quick_actions": policy_query_result.get("quick_actions", []),
                        # Include structured data for policy details, benefits, and gaps
                        "policy_id": policy_query_result.get("policy_id"),
                        "policy_data": policy_query_result.get("policy_data"),
                        "benefits_data": policy_query_result.get("benefits_data"),
                        "gaps_data": policy_query_result.get("gaps_data"),
                        "suggestions": [
                            "What are my coverage gaps?",
                            "Show my recommendations",
                            "What is my protection score?"
                        ] if detected_language == 'en' else [
                            "मेरी कवरेज गैप क्या हैं?",
                            "मेरी सिफारिशें दिखाएं",
                            "मेरा प्रोटेक्शन स्कोर क्या है?"
                        ],
                        "chat_session_id": chat_session_id,
                        "user_session_id": user_session_id
                    }
                    response_type = "policy_query"

                    # NOTE: MongoDB save removed - generic save at end of function handles it
                    # This prevents duplicate assistant messages in chat history
                    # ============= END POLICY QUERY INTENT =============

                elif intent == "wallet_setup":
                    result = await route_enhanced_chatbot(
                        action="start_wallet_setup",
                        session_id=chat_session_id,
                        access_token=access_token,
                        user_id=user_id
                    )
                    response_type = "question"
                    result["show_service_options"] = False
                    result["language"] = detected_language
                    result["chat_session_id"] = chat_session_id
                    result["user_session_id"] = user_session_id
                
                else:
                    helpful_msg = "I'd be happy to help you!" if detected_language == 'en' else "      "
                    
                    result = {
                        "response": helpful_msg,
                        "action": "helpful_guidance",
                        "show_service_options": False,
                        "language": detected_language,
                        "suggestions": generate_contextual_suggestions(combined_history),
                        "chat_session_id": chat_session_id,
                        "user_session_id": user_session_id
                    }
                    response_type = "chat_message"
            
            if not result:
                error_msg = "I'm sorry, I couldn't understand your request." if detected_language == 'en' else "  ,       "
                result = {
                    "response": error_msg,
                    "action": "error",
                    "show_service_options": False,
                    "language": detected_language,
                    "chat_session_id": chat_session_id,
                    "user_session_id": user_session_id
                }
                response_type = "error"
                intent = "error"
            
            # Extract assistant response - ensure it's never empty
            assistant_response = (
                result.get("response") or
                result.get("message") or
                result.get("title") or
                "Response generated"
            )

            # Validate response is not empty before saving
            if not assistant_response or not str(assistant_response).strip():
                logger.warning(f"Empty assistant response detected for intent: {intent}")
                assistant_response = f"I understand you're asking about: {query}"

            add_to_conversation_memory(chat_session_id, "assistant", assistant_response)

            # Save to MongoDB only if NOT a session continuation
            # Session continuations (Q&A flows) already save messages in their handlers
            is_session_continuation = result.get("session_continuation", False) or metadata.get("session_continuation", False)

            if mongodb_chat_manager and not is_session_continuation:
                logger.info(f"💾 Saving assistant message to MongoDB: intent={intent}, response_length={len(assistant_response)}")
                add_assistant_message_to_mongodb(
                    chat_session_id,
                    user_id,
                    assistant_response,
                    intent=intent,
                    context={
                        "action": result.get("action"),
                        "language": detected_language,
                        "original_query": query,
                        "user_session_regenerated": was_regenerated,
                        "original_user_session_id": original_user_session_id if was_regenerated else None,
                        "chat_session_regenerated": False,
                        "original_chat_session_id": None,
                        "response_type": response_type
                    },
                    language=detected_language
                )
                logger.info(f"✓ Assistant message saved to MongoDB successfully")
            elif is_session_continuation:
                logger.info(f"⏭️ Skipping MongoDB save for session continuation (already saved by handler)")

            if chat_session_id:
                chat_session_data = get_session(chat_session_id)
                if chat_session_data:
                    chat_session_data['last_activity'] = current_timestamp
                    chat_session_data['message_count'] = chat_session_data.get('message_count', 0) + 1
                    store_session(chat_session_id, chat_session_data, expire_seconds=86400)
            
            return create_standardized_response(
                response_type=response_type,
                data=result,
                session_id=chat_session_id,
                metadata=metadata
            )
        
        # Default response
        return create_standardized_response(
            response_type="chat_message",
            data={
                "response": "Welcome! How can I assist you today?",
                "action": "greeting",
                "show_service_options": True,
                "language": "en",
                "suggestions": generate_contextual_suggestions([]),
                "chat_session_id": chat_session_id,
                "user_session_id": user_session_id
            },
            session_id=chat_session_id,
            metadata=metadata
        )
        
    except Exception as e:
        logger.error(f"Error in ask endpoint: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        emergency_session = f"recovery_{int(time.time())}"
        if 'user_id' in locals() and user_id:
            emergency_session += f"_{user_id}"
        
        return create_standardized_response(
            response_type="error",
            data={
                "error": str(e),
                "message": "An error occurred while processing your request. Please try again.",
                "action": "error",
                "show_service_options": False,
                "language": "en"
            },
            session_id=emergency_session,
            metadata={
                "intent": "error",
                "original_query": query if 'query' in locals() else None,
                "error_details": str(e),
                "recovery_mode": True,
                "is_guest": is_guest if 'is_guest' in locals() else True
            }
        )


# ============= REFACTORED /ask ENDPOINT (Version 2 - Modular Architecture) =============

@router.post("/ask/v2")
@limiter.limit(RATE_LIMITS["ask"])
async def ask_agent_unified_v2(
    request: Request,  # Required for rate limiter
    # Form data parameters
    query: Optional[str] = Form(None),
    user_session_id: Optional[str] = Form(None),
    chat_session_id: Optional[str] = Form(None),
    session_id: Optional[str] = Form(None),
    access_token: Optional[str] = Form(None),
    user_id: Optional[int] = Form(None),
    user_phone: Optional[str] = Form(None),
    email: Optional[str] = Form(None),  # Support OAuth users with email
    action: Optional[str] = Form(None),
    user_input: Optional[str] = Form(None),
    assistance_type: Optional[str] = Form(None),
    insurance_type: Optional[str] = Form(None),
    service_type: Optional[str] = Form(None),
    file_action: Optional[str] = Form(None),
    vehicle_market_value: Optional[float] = Form(None),
    annual_income: Optional[float] = Form(None),
    policy_id: Optional[str] = Form(None),
    application_id: Optional[str] = Form(None),
    edited_answers: Optional[str] = Form(None),
    model: Optional[str] = Form("policy_analysis"),
    files: Optional[List[UploadFile]] = File(None),
    file: Optional[UploadFile] = File(None),
):
    """
    Refactored unified chat endpoint with modular architecture

    RATE LIMITED: 30 requests per minute per user
    This prevents abuse of expensive LLM API calls.

    This endpoint uses the new service layer pattern for better:
    - Maintainability (90% reduction in endpoint size)
    - Testability (independent handler modules)
    - Type safety (Pydantic validation)
    - Code reusability (centralized utilities)

    See REFACTORING_IMPLEMENTATION_GUIDE.md for details.
    """
    try:
        from datetime import datetime
        from models.chat_request import AskRequest, ChatContext
        from services.chat_handler_service import chat_handler_service
        from services.guest_chat_handler import guest_chat_handler
        from services.authenticated_chat_handler import authenticated_chat_handler

        # Create request model (Pydantic validation)
        request = AskRequest(
            query=query,
            user_session_id=user_session_id,
            chat_session_id=chat_session_id,
            session_id=session_id,
            access_token=access_token,
            user_id=user_id,
            user_phone=user_phone,
            action=action,
            user_input=user_input,
            assistance_type=assistance_type,
            insurance_type=insurance_type,
            service_type=service_type,
            file_action=file_action,
            vehicle_market_value=vehicle_market_value,
            annual_income=annual_income,
            policy_id=policy_id,
            application_id=application_id,
            edited_answers=edited_answers,
            model=model
        )

        # Step 1: Determine authentication
        is_guest, user_id, access_token, user_phone, was_regenerated, original_session_id = \
            chat_handler_service.determine_user_authentication(request)

        # Step 1.5: SECURITY VERIFICATION FOR AUTHENTICATED USERS
        # If user is attempting to authenticate (has credentials), verify the access token
        if not is_guest and should_verify_token(request.user_session_id, access_token, user_id):
            logger.info("Performing security verification for authenticated user (v2)")

            # Verify access token, user_id, phone/email match
            is_valid, error_message, token_payload = verify_user_authentication(
                access_token=access_token,
                user_id=user_id,
                user_phone=user_phone,
                email=email
            )

            if not is_valid:
                # Authentication failed - return error response
                logger.warning(f"Authentication verification failed (v2): {error_message}")

                # Use chat_session_id if available, otherwise create temp session
                error_session_id = request.chat_session_id if request.chat_session_id else f"error_{int(time.time())}"

                return create_auth_error_response(
                    error_message=error_message,
                    session_id=error_session_id
                )

            # Authentication successful - update user info from verified token
            logger.info(f"✓ Authentication verified successfully (v2) for user_id: {user_id}")

            # Update user_id, phone, and email from verified token payload (if not already set)
            if token_payload:
                if not user_id:
                    user_id = token_payload.get("id")
                if not user_phone:
                    user_phone = token_payload.get("contactNumber")
                if not email:
                    email = token_payload.get("email")

        # Step 2: Handle guest users
        if is_guest:
            context = chat_handler_service.create_guest_context(request.chat_session_id)
            return guest_chat_handler.handle_guest_request(
                request,
                context,
                has_files=bool(file or files)
            )

        # Step 3: Handle/create chat session
        chat_session_id, chat_session_created = chat_handler_service.handle_or_create_chat_session(
            user_id,
            request.chat_session_id,
            request.user_session_id or request.session_id,
            has_content=bool(request.query or request.action or file or files)
        )

        # Step 4: Create context
        context = ChatContext(
            user_id=user_id,
            user_session_id=request.user_session_id or request.session_id,
            chat_session_id=chat_session_id,
            is_guest=False,
            access_token=access_token,
            user_phone=user_phone,
            timestamp=datetime.now().isoformat(),
            was_regenerated=was_regenerated,
            original_user_session_id=original_session_id
        )

        # Step 5: Create metadata
        metadata = chat_handler_service.create_metadata(
            request.query,
            chat_session_id,
            request.user_session_id or request.session_id,
            chat_session_created,
            False,
            was_regenerated,
            original_session_id
        )

        # Step 5.5: Check for active chatbot sessions (CRITICAL for Q&A flow)
        # This must happen BEFORE routing to authenticated handler
        if not request.action and (request.query or request.user_input):
            from ai_chat_components.enhanced_chatbot_handlers import (
                chatbot_sessions,
                continue_policy_application,
                continue_financial_assistance_application,
                continue_insurance_application,
                continue_wallet_setup,
                extract_actual_user_input
            )

            # Find active sessions for this chat_session_id
            active_sessions = []
            for session_key in chatbot_sessions:
                if chat_session_id in session_key and not chatbot_sessions[session_key].completed:
                    active_sessions.append({
                        "key": session_key,
                        "session": chatbot_sessions[session_key]
                    })

            if active_sessions:
                # Continue the active chatbot session
                latest_session = active_sessions[-1]
                session_key = latest_session["key"]

                # Determine chatbot type from session key
                parts = session_key.split('_')
                chatbot_type = None
                service_type = None

                if "policy_application" in session_key:
                    chatbot_type = "policy_application"
                    service_type = parts[-1] if len(parts) >= 4 else None
                else:
                    known_types = ["financial", "insurance", "wallet"]
                    for i, part in enumerate(parts):
                        if part in known_types:
                            chatbot_type = part
                            if i + 1 < len(parts):
                                service_type = parts[i + 1]
                            break

                if chatbot_type == "wallet":
                    service_type = "setup"

                if chatbot_type and service_type:
                    try:
                        processing_query = request.query or request.user_input
                        actual_user_input = extract_actual_user_input(processing_query) if processing_query else None

                        # Route to appropriate continuation handler
                        result = None
                        if chatbot_type == "policy_application":
                            result = continue_policy_application(
                                chat_session_id, service_type, actual_user_input, access_token, user_id
                            )
                        elif chatbot_type == "financial":
                            result = continue_financial_assistance_application(
                                chat_session_id, service_type, actual_user_input, access_token, user_id
                            )
                        elif chatbot_type == "insurance":
                            result = continue_insurance_application(
                                chat_session_id, service_type, actual_user_input, access_token, user_id
                            )
                        elif chatbot_type == "wallet":
                            result = continue_wallet_setup(
                                chat_session_id, actual_user_input, access_token, user_id
                            )

                        if result:
                            # Determine response type
                            intent = result.get("action", "chatbot_continuation")
                            response_type = "question"
                            if result.get("type") == "application_completed":
                                response_type = "application_completed"
                            elif result.get("type") == "application_cancelled":
                                response_type = "application_cancelled"
                            elif result.get("type") == "review_application":
                                response_type = "review_application"

                            result["chat_session_id"] = chat_session_id
                            result["user_session_id"] = context.user_session_id

                            return create_standardized_response(
                                response_type=response_type,
                                data=result,
                                session_id=chat_session_id,
                                metadata={**metadata.dict(), "intent": intent}
                            )
                    except Exception as chatbot_error:
                        logger.error(f"Error continuing chatbot session: {chatbot_error}")
                        # Fall through to normal handler

        # Step 6: Handle authenticated request
        files_list = files if files else ([file] if file else None)
        return await authenticated_chat_handler.handle_authenticated_request(
            request,
            context,
            metadata,
            files_list
        )

    except Exception as e:
        logger.error(f"Error in /ask/v2 endpoint: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")

        # Emergency fallback response
        emergency_session = f"error_{int(time.time())}_{secrets.token_hex(4)}"
        return create_standardized_response(
            response_type="error",
            data={
                "error": "Internal server error",
                "message": "An unexpected error occurred. Please try again.",
                "action": "error",
                "show_service_options": True,
                "language": "en"
            },
            session_id=emergency_session,
            metadata={
                "intent": "error",
                "error_details": str(e),
                "endpoint": "/ask/v2"
            }
        )


# ============= HELPER FUNCTION: Coverage Advisory Response Generator =============

async def handle_policy_analysis_conversation(
    query: str,
    user_id: int,
    chat_session_id: str,
    metadata: Dict,
    was_regenerated: bool,
    original_user_session_id: str
) -> Dict:
    """
    Handle conversational queries about policy analysis using GLM LLM
    Similar to generate_casual_response_with_context but specialized for policy analysis
    """
    try:
        # Store user message in memory
        add_to_conversation_memory(chat_session_id, "user", query)
        
        # Get conversation history
        conversation_history = get_conversation_history(chat_session_id, limit=10)
        
        # Store in MongoDB if available
        if mongodb_chat_manager:
            add_user_message_to_mongodb(chat_session_id, user_id, query)
        
        # Build context from conversation history
        context_messages = []
        for msg in conversation_history[-6:]:  # Last 3 exchanges
            role = "User" if msg.get('role') == 'user' else "Assistant"
            content = msg.get('content', '')[:200]  # Limit length
            context_messages.append(f"{role}: {content}")
        
        context_str = "\n".join(context_messages) if context_messages else "New conversation about policy analysis"
        
        # Detect if user wants to upload
        upload_keywords = ['upload', 'analyze my policy', 'check my policy', 'pdf', 'document', 'file']
        wants_upload = any(keyword in query.lower() for keyword in upload_keywords)
        
        if wants_upload:
            # Guide them to upload
            response_text = "I'd be happy to analyze your insurance policy! Please upload your policy PDF document, and I'll provide you with a detailed protection score analysis including coverage adequacy, recommendations, and a comprehensive report. Just use the file upload option to get started. "
        else:
            # Use GLM LLM for conversational response
            prompt = f"""You are an expert insurance policy analyst assistant. You help users understand insurance policy analysis, protection scores, and coverage evaluation.

Previous conversation context:
{context_str}

Current user question: "{query}"

Provide a helpful, clear, and professional response that:
- Explains policy analysis concepts in simple, understandable terms
- Discusses protection scores, coverage adequacy, and policy evaluation when relevant
- Gives practical, actionable advice about what to look for in insurance policies
- Mentions that they can upload their policy PDF for detailed analysis if appropriate
- Keeps response concise and focused (3-4 sentences maximum)
- Uses professional but friendly tone
- Avoids excessive emojis (max 1)

If explaining technical terms, provide clear definitions. If discussing scores or metrics, explain what they mean for the policyholder.

Response:"""

            # Use GLM LLM (same configuration as in processor.py)
            from langchain_openai import ChatOpenAI
            from langchain_core.messages import HumanMessage
            
            # Use llm_config for proper GPT-3.5/GLM fallback
            from ai_chat_components.llm_config import get_llm
            policy_analysis_llm = get_llm(use_case='policy_analysis')
            
            messages = [HumanMessage(content=prompt)]
            response = policy_analysis_llm.invoke(messages)
            response_text = response.content.strip()
            
            # Post-process: ensure 3-4 sentences max
            sentences = [s.strip() for s in response_text.split('. ') if s.strip()]
            if len(sentences) > 4:
                response_text = '. '.join(sentences[:4])
                if not response_text.endswith('.'):
                    response_text += '.'
        
        # Store assistant response
        add_to_conversation_memory(chat_session_id, "assistant", response_text)
        
        if mongodb_chat_manager:
            add_assistant_message_to_mongodb(
                chat_session_id,
                user_id,
                response_text,
                intent="policy_analysis_conversation"
            )
        
        # Generate contextual suggestions
        # suggestions = generate_policy_analysis_suggestions(query, conversation_history)
        
        return create_standardized_response(
            response_type="policy_analysis_conversation",
            data={
                "response": response_text,
                "message": "Policy Analysis Information",
                "action": "policy_analysis_conversation",
                "model": "policy_analysis",
                "show_service_options": False,
                "language": "en",
                # "suggestions": suggestions,
                "quick_actions": [
                    {"title": "Upload Policy for Analysis", "action": "request_policy_upload"},
                    {"title": "Protection Score Info", "query": "What is protection score?", "model": "policy_analysis"},
                    {"title": "Coverage Tips", "query": "What makes good coverage?", "model": "policy_analysis"}
                ],
                "file_upload_available": True,
                "upload_hint": " Upload your policy PDF anytime for detailed analysis"
            },
            session_id=chat_session_id,
            metadata={**metadata, "intent": "policy_analysis_conversation"}
        )
        
    except Exception as e:
        logger.error(f"Error in policy analysis conversation: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        return create_standardized_response(
            response_type="error",
            data={
                "error": str(e),
                "message": "I encountered an issue processing your question. Would you like to upload your policy PDF for analysis, or try asking another question?",
                "action": "conversation_error",
                "model": "policy_analysis",
                "quick_actions": [
                    {"title": "Upload Policy", "action": "request_policy_upload"},
                    {"title": "Try Again", "action": "retry_question"}
                ]
            },
            session_id=chat_session_id,
            metadata={**metadata, "intent": "conversation_error"}
        )


async def generate_coverage_advisory_response(
    query: str,
    user_id: int,
    conversation_history: List[Dict] = None,
    insurance_type: Optional[str] = None
) -> Dict:
    """
    Generate comprehensive coverage advisory response using GLM LLM
    """
    try:
        # Import necessary classes
        from langchain_openai import ChatOpenAI
        from langchain_core.messages import HumanMessage
        
        # Build context from conversation history
        context_info = ""
        context_messages = []
        
        if conversation_history and len(conversation_history) > 0:
            recent_topics = []
            
            # Extract conversation context
            for msg in conversation_history[-6:]:
                content = msg.get('content', '')
                role = "User" if msg.get('role') == 'user' else "Assistant"
                
                # Build context messages for the prompt
                context_messages.append(f"{role}: {content[:150]}")
                
                # Track topics
                content_lower = content.lower()
                if 'health' in content_lower:
                    recent_topics.append('health insurance')
                if 'life' in content_lower:
                    recent_topics.append('life insurance')
                if 'motor' in content_lower or 'vehicle' in content_lower:
                    recent_topics.append('motor insurance')
                if 'term' in content_lower:
                    recent_topics.append('term insurance')
            
            if recent_topics:
                context_info = f"Continuing our discussion about {', '.join(set(recent_topics))}, "
        
        # Build context string for prompt
        context_str = "\n".join(context_messages) if context_messages else "New conversation about insurance coverage"
        
        # Create detailed advisory prompt for GLM
        prompt = f"""You are an expert insurance coverage advisor providing personalized recommendations and guidance.

Previous conversation context:
{context_str}

Insurance type focus: {insurance_type if insurance_type else 'General insurance coverage'}

Current user question: "{query}"

{context_info}provide comprehensive coverage advisory that:

 Is specific and actionable with clear recommendations
 Considers typical life stages and individual needs
 Explains coverage amounts and types in simple terms
 Compares different options when relevant
 Uses everyday language, avoiding jargon
 Provides practical, real-world examples
 Includes 2-3 key recommendations
 Keeps response focused and concise (4-5 sentences maximum)
 Helps users make informed decisions about their insurance needs

If discussing coverage amounts:
- For health insurance: Consider age, family size, medical history
- For life insurance: Use income multiplier method (10-15x annual income)
- For motor insurance: Consider vehicle value, usage, and add-ons

Provide clear, professional, and helpful guidance that empowers the user to make smart insurance decisions.

Response:"""
        
        # Initialize LLM for coverage advisory with proper fallback
        from ai_chat_components.llm_config import get_llm
        coverage_advisory_llm = get_llm(use_case='coverage_advisory')
        
        # Generate response using GLM
        messages = [HumanMessage(content=prompt)]
        response = coverage_advisory_llm.invoke(messages)
        advisory_text = response.content.strip()
        
        # Post-process response: ensure 4-5 sentences
        sentences = [s.strip() for s in advisory_text.split('. ') if s.strip()]
        if len(sentences) > 5:
            advisory_text = '. '.join(sentences[:5])
            if not advisory_text.endswith('.'):
                advisory_text += '.'
        
        # Generate contextual suggestions based on query
        suggestions = generate_coverage_suggestions(query, insurance_type)
        
        # Generate recommendations based on query type
        recommendations = []
        query_lower = query.lower()
        
        if 'health' in query_lower:
            recommendations = [
                "Consider a family floater if you have dependents",
                "Ensure adequate room rent and ICU coverage",
                "Look for plans with no claim bonus benefits"
            ]
        
        elif 'life' in query_lower or 'term' in query_lower:
            recommendations = [
                "Coverage should be 10-15x your annual income",
                "Term insurance offers maximum coverage at lowest cost",
                "Add critical illness rider for comprehensive protection"
            ]
        
        elif 'motor' in query_lower or 'vehicle' in query_lower or 'car' in query_lower:
            recommendations = [
                "Comprehensive coverage recommended for new vehicles",
                "Consider zero depreciation add-on for first 3 years",
                "Add personal accident cover for driver protection"
            ]
        
        elif 'home' in query_lower or 'property' in query_lower:
            recommendations = [
                "Cover structure value plus contents adequately",
                "Include natural calamity coverage for your region",
                "Consider liability coverage for visitor injuries"
            ]
        
        elif 'travel' in query_lower:
            recommendations = [
                "Get coverage equal to medical costs in destination country",
                "Include trip cancellation and baggage loss coverage",
                "Check for COVID-19 coverage if traveling internationally"
            ]
        
        else:
            # Generic recommendations
            recommendations = [
                "Assess your current financial obligations and dependents",
                "Compare policies from at least 3-4 insurers",
                "Review and update coverage annually or after major life events"
            ]
        
        # Generate coverage options if user is comparing
        coverage_options = []
        if 'compare' in query_lower or 'option' in query_lower or 'plan' in query_lower:
            coverage_options = [
                {
                    "option": "Basic Coverage",
                    "description": "Essential protection at affordable premiums",
                    "suitable_for": "Budget-conscious individuals with basic needs",
                    "pros": ["Lower premiums", "Core coverage included"],
                    "cons": ["Limited benefits", "Higher out-of-pocket costs"]
                },
                {
                    "option": "Comprehensive Coverage",
                    "description": "Extended protection with additional benefits",
                    "suitable_for": "Those seeking complete peace of mind",
                    "pros": ["Broader coverage", "More add-ons", "Better claim settlement"],
                    "cons": ["Higher premiums", "May include unnecessary features"]
                },
                {
                    "option": "Premium Coverage",
                    "description": "Maximum coverage with all add-ons and minimal exclusions",
                    "suitable_for": "High-value assets or comprehensive protection needs",
                    "pros": ["Complete protection", "Minimal exclusions", "Premium service"],
                    "cons": ["Highest premiums", "May be overkill for some needs"]
                }
            ]
        
        # Next steps for the user
        next_steps = [
            "Review your current coverage gaps and financial obligations",
            "Compare quotes from 3-4 reputable insurers",
            "Check policy exclusions and waiting periods carefully",
            "Read customer reviews and claim settlement ratios",
            "Consult with an advisor for personalized guidance if needed"
        ]
        
        return {
            "response": advisory_text,
            "suggestions": suggestions,
            "recommendations": recommendations,
            "coverage_options": coverage_options,
            "next_steps": next_steps,
            "insurance_type": insurance_type
        }
        
    except Exception as e:
        logger.error(f"Error generating coverage advisory with GLM: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        # Fallback response
        return {
            "response": "I can help you understand your insurance coverage needs. Could you provide more details about what type of coverage you're interested in or what specific questions you have?",
            "suggestions": [
                "What health insurance do I need?",
                "How much life cover is enough?",
                "What motor insurance coverage should I get?",
                "Compare different insurance options"
            ],
            "recommendations": [],
            "coverage_options": [],
            "next_steps": [
                "Identify your insurance needs",
                "Research available options",
                "Compare different plans",
                "Consult with an expert"
            ]
        }


def generate_coverage_suggestions(query: str, insurance_type: Optional[str] = None) -> List[str]:
    """Generate contextual suggestions for coverage advisory conversations"""
    
    query_lower = query.lower()
    
    # Health insurance suggestions
    if 'health' in query_lower or insurance_type == 'health':
        if 'family' in query_lower:
            return [
                "Individual vs family floater comparison",
                "What's the right sum insured for family?",
                "Should children have separate policies?",
                "Family health insurance tax benefits"
            ]
        elif 'amount' in query_lower or 'sum' in query_lower:
            return [
                "How to calculate adequate health cover?",
                "Factors affecting sum insured decision",
                "Should I increase coverage with age?",
                "Top-up vs super top-up plans"
            ]
        else:
            return [
                "Compare individual vs family floater",
                "What's a good sum insured amount?",
                "Should I get critical illness cover?",
                "How much maternity coverage do I need?"
            ]
    
    # Life insurance suggestions
    elif 'life' in query_lower or 'term' in query_lower or insurance_type == 'life':
        if 'amount' in query_lower or 'cover' in query_lower:
            return [
                "How to calculate life cover needed?",
                "Income replacement method explained",
                "DIME method for life insurance",
                "When to increase life cover?"
            ]
        elif 'rider' in query_lower:
            return [
                "Which riders should I add?",
                "Critical illness rider vs separate policy",
                "Accidental death benefit worth it?",
                "Waiver of premium rider explained"
            ]
        else:
            return [
                "Term vs whole life insurance",
                "How much life cover do I need?",
                "Should I add riders to my policy?",
                "When is the best time to buy?"
            ]
    
    # Motor insurance suggestions
    elif any(word in query_lower for word in ['motor', 'car', 'vehicle', 'auto']) or insurance_type == 'motor':
        if 'add-on' in query_lower or 'addon' in query_lower:
            return [
                "Essential vs optional add-ons",
                "Is zero depreciation worth it?",
                "Engine protection add-on explained",
                "Return to invoice cover benefits"
            ]
        elif 'idv' in query_lower or 'value' in query_lower:
            return [
                "What is IDV and why it matters?",
                "How is IDV calculated?",
                "Should I declare higher IDV?",
                "IDV vs market value difference"
            ]
        else:
            return [
                "Third party vs comprehensive coverage",
                "What add-ons should I get?",
                "How to reduce motor insurance premium?",
                "Should I get zero depreciation cover?"
            ]
    
    # Home insurance suggestions
    elif 'home' in query_lower or 'property' in query_lower or insurance_type == 'home':
        return [
            "Structure vs contents coverage",
            "Natural calamity coverage options",
            "Home insurance for renters",
            "Liability coverage importance"
        ]
    
    # Travel insurance suggestions
    elif 'travel' in query_lower or insurance_type == 'travel':
        return [
            "Medical coverage for international travel",
            "Trip cancellation insurance worth it?",
            "Coverage for adventure activities",
            "Annual vs single trip policy"
        ]
    
    # Generic coverage questions
    elif 'compare' in query_lower:
        return [
            "How to compare insurance policies?",
            "What factors to consider when comparing?",
            "Understanding policy terms and conditions",
            "Claim settlement ratio importance"
        ]
    
    elif 'premium' in query_lower or 'cost' in query_lower:
        return [
            "What factors affect insurance premium?",
            "How to reduce insurance costs?",
            "Is higher premium always better?",
            "Premium vs coverage balance"
        ]
    
    # Default suggestions
    return [
        "What's the ideal coverage amount?",
        "How do I choose between different plans?",
        "What factors affect insurance premium?",
        "When should I review my coverage?"
    ]
    

def debug_session_key_parsing(session_key: str):
    """Debug function to test session key parsing"""
    print(f" Debugging session key: {session_key}")
    
    parts = session_key.split('_')
    print(f" Split parts: {parts}")
    
    # Find the chatbot type and service type from the parts
    chatbot_type = None
    service_type = None
    
    # Look for known chatbot types in the parts
    known_types = ["financial", "insurance", "wallet"]
    for i, part in enumerate(parts):
        if part in known_types:
            chatbot_type = part
            # The next part should be the service type
            if i + 1 < len(parts):
                service_type = parts[i + 1]
            break
    
    # Special handling for wallet (no service type)
    if chatbot_type == "wallet":
        service_type = "setup"



# -------------------- Chat Memory API Endpoints --------------------


# ==================== REPORT REGENERATION API ENDPOINTS ====================

@router.post("/regenerate-report")
async def regenerate_full_report_endpoint(request: RegenerateReportRequest):
    """
    Regenerate entire insurance gap analysis report
    
    Request Body:
    {
        "report_id": "report_413_1763630701_d3454f8a",
        "user_id": 413,
        "access_token": "user_access_token",
        "chat_session_id": "optional_chat_session_id"
    }
    
    Response:
    {
        "success": true,
        "report_id": "report_413_1763631234_e4565g9b",
        "original_report_id": "report_413_1763630701_d3454f8a",
        "report_url": "https://s3.../gap_analysis_413_1763631234_regenerated.pdf",
        "mongodb_id": "...",
        "message": "Report regenerated successfully",
        "regenerated_at": "2025-11-20T15:30:00"
    }
    """
    try:
        logger.info(f"Full report regeneration requested for report_id: {request.report_id}")
        
        # Verify authentication
        is_valid, error_message, token_payload = verify_user_authentication(
            access_token=request.access_token,
            user_id=request.user_id
        )
        
        if not is_valid:
            raise HTTPException(status_code=401, detail=error_message)
        
        # Check MongoDB availability
        if not mongodb_chat_manager:
            raise HTTPException(status_code=503, detail="Database service not available")
        
        # Get LLM instance
        from core.config import get_llm_instance
        llm = get_llm_instance()
        
        # Import regeneration function
        from routers.chat_regeneration_endpoints import regenerate_full_report
        
        # Regenerate report using DeepSeek
        result = await regenerate_full_report(
            report_id=request.report_id,
            user_id=request.user_id,
            mongodb_chat_manager=mongodb_chat_manager,
            chat_session_id=request.chat_session_id
        )
        
        if not result.get('success'):
            raise HTTPException(
                status_code=404 if 'not found' in result.get('error', '').lower() else 500,
                detail=result.get('error', 'Failed to regenerate report')
            )
        
        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "data": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in regenerate_full_report_endpoint: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/regenerate-report-section")
async def regenerate_section_endpoint(request: RegenerateSectionRequest):
    """
    Regenerate a specific section of insurance gap analysis report
    
    Request Body:
    {
        "report_id": "report_413_1763630701_d3454f8a",
        "section_name": "recommendations",
        "user_id": 413,
        "access_token": "user_access_token",
        "chat_session_id": "optional_chat_session_id",
        "additional_instructions": "Focus on affordable options"
    }
    
    Available sections:
    - executive_summary
    - gap_analysis
    - recommendations
    - risk_assessment
    - next_steps
    - policy_overview
    
    Response:
    {
        "success": true,
        "report_id": "report_413_1763630701_d3454f8a",
        "section_name": "recommendations",
        "regenerated_content": "## Recommendations\n\n...",
        "message": "Section 'Recommendations' regenerated successfully",
        "regenerated_at": "2025-11-20T15:30:00"
    }
    """
    try:
        logger.info(f"Section regeneration requested - report_id: {request.report_id}, section: {request.section_name}")
        
        # Verify authentication
        is_valid, error_message, token_payload = verify_user_authentication(
            access_token=request.access_token,
            user_id=request.user_id
        )
        
        if not is_valid:
            raise HTTPException(status_code=401, detail=error_message)
        
        # Validate section name
        valid_sections = [
            "executive_summary", "gap_analysis", "recommendations",
            "risk_assessment", "next_steps", "policy_overview"
        ]
        
        if request.section_name not in valid_sections:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid section name. Must be one of: {', '.join(valid_sections)}"
            )
        
        # Check MongoDB availability
        if not mongodb_chat_manager:
            raise HTTPException(status_code=503, detail="Database service not available")
        
        # Get LLM instance
        from core.config import get_llm_instance
        llm = get_llm_instance()
        
        # Import regeneration function
        from routers.chat_regeneration_endpoints import regenerate_report_section
        
        # Regenerate section
        result = await regenerate_report_section(
            report_id=request.report_id,
            section_name=request.section_name,
            user_id=request.user_id,
            mongodb_chat_manager=mongodb_chat_manager,
            llm=llm,
            additional_instructions=request.additional_instructions,
            chat_session_id=request.chat_session_id
        )
        
        if not result.get('success'):
            raise HTTPException(
                status_code=404 if 'not found' in result.get('error', '').lower() else 500,
                detail=result.get('error', 'Failed to regenerate section')
            )
        
        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "data": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in regenerate_section_endpoint: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== END REPORT REGENERATION ENDPOINTS ====================


# ==================== ONBOARDING CONTENT ENDPOINT ====================

DEFAULT_ONBOARDING = {
    "title": "Policy Samjhega India.",
    "highlight_word": "India.",
    "description": (
        "Your policy has clauses that can deny your claim. "
        "Limits that cut your payout in half. "
        "Gaps that leave your family unprotected. "
        "Eazr shows you everything your agent didn't. "
        "Let's get started!"
    ),
    "footer_text": "Secure. Private. Built for you.",
}


@router.get("/api/v1/onboarding")
@limiter.limit(RATE_LIMITS.get("user_read", "30/minute"))
async def get_onboarding_content(request: Request):
    """
    Get onboarding screen content (title, description, footer).

    Returns admin-configured content from MongoDB, or defaults if not configured.
    """
    try:
        from database_storage.mongodb_chat_manager import mongodb_chat_manager

        if mongodb_chat_manager and mongodb_chat_manager.db:
            collection = mongodb_chat_manager.db["onboarding_config"]
            config = collection.find_one(
                {"is_active": True},
                sort=[("updated_at", -1)]
            )

            if config:
                return {
                    "success": True,
                    "data": {
                        "title": config.get("title", DEFAULT_ONBOARDING["title"]),
                        "highlight_word": config.get("highlight_word", DEFAULT_ONBOARDING["highlight_word"]),
                        "description": config.get("description", DEFAULT_ONBOARDING["description"]),
                        "footer_text": config.get("footer_text", DEFAULT_ONBOARDING["footer_text"]),
                    }
                }

        # Fallback to defaults
        return {
            "success": True,
            "data": DEFAULT_ONBOARDING
        }

    except Exception as e:
        logger.warning(f"Error fetching onboarding config, using defaults: {e}")
        return {
            "success": True,
            "data": DEFAULT_ONBOARDING
        }
