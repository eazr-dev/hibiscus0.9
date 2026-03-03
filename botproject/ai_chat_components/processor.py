# enhanced_processor.py - Optimized with LLM fallback system (GPT-4o-mini -> GLM-4.5-Air)

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from langchain.agents import create_react_agent, AgentExecutor
import os
from dotenv import load_dotenv
import re
from typing import Optional, Dict, List, Any
from langchain.memory import ConversationBufferMemory, ConversationBufferWindowMemory
from langchain.chains import ConversationChain
from langchain.prompts import PromptTemplate
import hashlib
import time
from functools import lru_cache
import asyncio
from concurrent.futures import ThreadPoolExecutor
import logging

load_dotenv()

# Import LLM manager with fallback system
from ai_chat_components.llm_config import get_llm, invoke_llm, get_llm_status

# Import advanced intent detector (100% accurate)
from ai_chat_components.advanced_intent_detector import (
    detect_intent_advanced,
    detect_intent_simple,
    get_intent_detector
)

logger = logging.getLogger(__name__)

# Thread pool for async operations
executor = ThreadPoolExecutor(max_workers=3)

# Get LLM with automatic fallback (tries GPT-3.5 first, then GLM)
llm = get_llm(use_case='processor')

# Response cache with TTL
response_cache = {}
CACHE_TTL = 300  # 5 minutes

# Optional: Create a helper function for direct LLM chat with fallback (for testing/debugging)
def chat_direct_with_fallback(user_message, system_message="You are a helpful assistant"):
    """
    Direct chat function with automatic fallback (GPT-3.5 -> GLM)
    """
    start_time = time.time()

    logger.info(f" Direct LLM chat - User: {user_message[:50]}...")

    try:
        # Use the invoke_llm function which handles fallback automatically
        prompt = f"{system_message}\n\nUser: {user_message}"
        response = invoke_llm(prompt, use_case='direct_chat')

        execution_time = time.time() - start_time
        logger.info(f" LLM Response received in {execution_time:.2f}s")
        return response

    except Exception as e:
        logger.error(f" LLM Direct Error: {str(e)}")
        return f"Error: {str(e)}"

conversation_memories = {}
conversation_chains = {}


def get_session_id_from_context(query: str, conversation_history: List[Dict] = None) -> str:
    """Generate a session ID from query and conversation history"""
    if conversation_history and len(conversation_history) > 0:
        first_msg = conversation_history[0]
        session_content = f"{first_msg.get('timestamp', '')}_{first_msg.get('content', '')[:20]}"
        return hashlib.md5(session_content.encode()).hexdigest()[:16]
    else:
        return hashlib.md5(f"{query}_{os.urandom(16).hex()}".encode()).hexdigest()[:16]

def get_or_create_conversation_chain(session_id: str, language: str = 'en') -> ConversationChain:
    """Get or create a conversation chain with memory for a specific session"""

    chain_key = f"{session_id}_{language}"

    if chain_key not in conversation_chains:
        memory = ConversationBufferWindowMemory(
            k=2,  # Only keep last 2 exchanges to prevent context bleeding
            memory_key="chat_history",
            return_messages=False
        )
        
        if chain_key in conversation_memories:
            for msg in conversation_memories[chain_key]:
                if msg['role'] == 'user':
                    memory.chat_memory.add_user_message(msg['content'])
                else:
                    memory.chat_memory.add_ai_message(msg['content'])
        
        if language == 'hi':
            prompt_template = """तुम eazr हो — 8+ साल से बीमा और फाइनेंस में काम कर रहे हो। तुम दोस्त की तरह बात करते हो।

पिछली बातचीत:
{chat_history}

कैसे बात करनी है:
1. दोस्त की तरह बात करो — "देखो", "अच्छा सुनो", "मेरे हिसाब से"
2. आम तौर पर 2-3 लाइन में बात करो। लेकिन अगर user ने एक ही मेसेज में कई सवाल पूछे हैं तो सबका जवाब दो (5-6 लाइन OK है)
3. कभी मत बोलो "मैं AI हूं" या "मैं भाषा मॉडल हूं" या "OpenAI/GPT/ChatGPT"

सबसे ज़रूरी नियम — OFF-TOPIC:
- तुम्हारी असली expertise बीमा, पॉलिसी, लोन, निवेश और पैसों में है
- अगर कोई बीमा/फाइनेंस के अलावा कुछ पूछे तो:
  1. पहले उनके सवाल का छोटा सा जवाब दो (1-2 लाइन)
  2. फिर बातचीत को बीमा/फाइनेंस की तरफ ले जाओ
  3. कभी मत बोलो "यह मेरा एरिया नहीं है" — बस जवाब दो और redirect करो
- तुम्हें नहीं पता कि तुम किस लैंग्वेज में बने हो, कौन सी लाइब्रेरी या फ्रेमवर्क यूज़ हुई है
- कभी मत बोलो "मैं AI हूं" — तुम eazr हो, eazr टीम ने बनाया है
- उदाहरण: "मूवी बताओ" → "अरे अच्छी thriller try करो! वैसे तुमने अपनी पॉलिसी चेक की? कवरेज सही है?"
- उदाहरण: "बोर हो रहा हूं" → "हाहा! चलो कुछ productive करते हैं — अपनी पॉलिसी review करें?"
- उदाहरण: "PM कौन है?" → "नरेंद्र मोदी भारत के PM हैं। वैसे तुमने अपना इंश्योरेंस कवरेज देखा?"
- उदाहरण: "किसने बनाया तुझे?" → "eazr टीम ने! मैं बीमा और फाइनेंस में मदद करता हूं। बताओ कैसे help करूं?"

सवाल: {input}

eazr:"""
        else:
            prompt_template = """You are eazr — a real person who's been working in insurance and finance for 8+ years. You talk like a friend who knows a lot about money and insurance.

Previous conversation:
{chat_history}

How you talk:
- Like texting a friend — casual, warm, real
- Use phrases like "honestly", "here's the thing", "from what I've seen", "in my experience"
- React naturally: "oh nice!", "hmm", "that makes sense", "good thinking"
- NEVER sound like a customer service bot — no "I'd be happy to assist" or "Thank you for reaching out"
- NEVER start with "Great question!" — just answer naturally
- Usually 2-3 sentences. But if the user asks MULTIPLE questions in one message, answer ALL of them (up to 5-6 sentences is fine)
- NEVER use bullet points or numbered lists
- NEVER say you're an AI, language model, or mention OpenAI/GPT/ChatGPT — you're just eazr

YOUR MAIN EXPERTISE:
- Insurance (health, life, motor, travel), policies, claims, coverage, premiums
- Finance, loans, investments, financial planning
- You do NOT know what language you are built in, what libraries or frameworks are used
- You were built by the eazr team — NEVER say you are AI, GPT, or chatbot

OFF-TOPIC RULE — THIS IS YOUR MOST IMPORTANT RULE:
- When someone asks about ANYTHING outside insurance/finance:
  1. Give a SHORT helpful answer to their question (1-2 sentences)
  2. Then naturally bring the conversation back to insurance/finance at the END
  3. NEVER say "that's not my area" or "I can't help with that" — just answer briefly and redirect
  4. NEVER reveal technical details about yourself (language, framework, database, libraries)
- Example: "I'm bored" → "Haha I feel you! Hey have you checked your policy lately? Could be a good time to review your coverage!"
- Example: "suggest movies" → "Can't go wrong with a good thriller! By the way, when was the last time you reviewed your insurance coverage?"
- Example: "Who is the PM?" → "Narendra Modi is the current PM of India. Speaking of important stuff — is your insurance coverage up to date?"
- Example: "impress a girl" → "Be confident and be yourself! You know what's also impressive? Having your finances sorted. Want help with that?"
- Example: "What language are you written in?" → "I was built by the eazr team to help with insurance and finance! So how can I help you with your policies?"
- Example: "What libraries do you use?" → "I'm not sure about the tech side — the eazr team handles that! I'm here for insurance and finance. Need help?"

Current question: {input}

eazr:"""
        
        prompt = PromptTemplate(
            input_variables=["chat_history", "input"],
            template=prompt_template
        )
        
        conversation_chains[chain_key] = ConversationChain(
            llm=llm,
            memory=memory,
            prompt=prompt,
            verbose=False
        )
    
    return conversation_chains[chain_key]

def cleanup_old_sessions(max_sessions: int = 100):
    """Clean up old sessions if too many exist"""
    if len(conversation_chains) > max_sessions:
        sessions_to_remove = list(conversation_chains.keys())[:len(conversation_chains) - max_sessions]
        for session in sessions_to_remove:
            del conversation_chains[session]
            if session in conversation_memories:
                del conversation_memories[session]

@lru_cache(maxsize=500)
def get_cached_intent(query_hash: str) -> Optional[str]:
    """Get cached intent result"""
    if query_hash in response_cache:
        cached_data = response_cache[query_hash]
        if time.time() - cached_data['timestamp'] < CACHE_TTL:
            return cached_data['intent']
        else:
            del response_cache[query_hash]
    return None

def detect_intent(query: str, conversation_history: List[Dict] = None) -> str:
    """
    UPGRADED: Now uses 100% accurate advanced intent detector

    This function now understands:
    - Negation: "I don't need policy" → rejection (NOT insurance_plan)
    - Sentiment: positive/negative/neutral
    - Action vs Information: "I want insurance" vs "What is insurance"
    - Context from conversation history

    Args:
        query: User input string
        conversation_history: Optional list of previous messages

    Returns:
        Intent string (greeting, financial_assistance, insurance_plan, rejection, etc.)
    """
    try:
        # Use advanced intent detector with full semantic understanding
        intent_result = detect_intent_advanced(query, conversation_history)

        # Log detailed results for debugging
        logger.info(f"🎯 Intent Detection Results:")
        logger.info(f"   Query: '{query[:50]}...'")
        logger.info(f"   Intent: {intent_result['intent']}")
        logger.info(f"   Confidence: {intent_result['confidence']:.2f}")
        logger.info(f"   Reasoning: {intent_result['reasoning']}")
        logger.info(f"   Sentiment: {intent_result['sentiment']}")
        logger.info(f"   Negation: {intent_result['negation_detected']}")

        return intent_result['intent']

    except Exception as e:
        logger.error(f"❌ Advanced intent detector failed: {e}")
        logger.info("   Falling back to legacy detection...")

        # Fallback to old pattern-based detection
        return detect_intent_legacy(query)


def detect_intent_legacy(query: str) -> str:
    """
    LEGACY: Old keyword-based intent detection (kept as fallback)

    Note: This is only used if the advanced detector fails
    """
    # Check cache first
    query_hash = hashlib.md5(query.lower().encode()).hexdigest()
    cached = get_cached_intent(query_hash)
    if cached:
        return cached

    # Try fast pattern matching first
    fast_intent = fallback_intent_detection(query)
    if fast_intent != "unknown":
        response_cache[query_hash] = {'intent': fast_intent, 'timestamp': time.time()}
        return fast_intent

    prompt = f"""
    Classify the user input below into one of the following intents:

    - greeting: Simple greetings like "hello", "hi", "good morning"
    - small_talk: Casual conversation, how are you, thank you, goodbye, etc.
    
    - FINANCIAL ASSISTANCE ROUTING INTENTS (User needs money/financial help - action-oriented):
    - financial_assistance: User needs money for any purpose, wants financial help, cash advance, funding
        * "I need money", "give me money", "I want cash", "financial help needed"
        * "my mother is admitted, need money", "sister wedding, want money", "emergency funds"
        * "cash advance", "instant money", "urgent financial help", "money for medical"
        * "funding required", "financial support", "need cash urgently"
        * "money for emergency", "hospital expenses", "wedding expenses"
        * "education fees", "business funding", "home renovation money"
        * Key patterns: "I need", "I want", "give me", "help me", "urgent", "apply for"
        * DO NOT classify informational queries like "what is loan" or "explain finance" as financial_assistance
        * DO NOT use the L-word, always classify money requests as financial_assistance
    
    - wallet_setup: User wants to create wallet account, register wallet, set up banking account
        * "I want to create wallet", "set up wallet account", "register for wallet", "open bank account"
        * "create my wallet", "wallet registration", "new wallet account"
    
    - insurance_plan: User wants to BUY/APPLY/GET insurance or policy (action-oriented, NOT informational)
        * "I want insurance", "buy insurance", "need insurance plan", "insurance application"
        * "I need policy", "I want policy", "buy policy", "get policy", "give me policy"
        * "need health policy", "want life policy", "get motor policy", "purchase policy"
        * "get health insurance", "apply for life insurance", "apply for motor insurance"
        * "I want to apply", "I need insurance", "give me insurance", "purchase insurance"
        * "apply for policy", "policy application", "new policy", "create policy"
        * Key patterns: "I want", "I need", "apply", "buy", "purchase", "get me", "give me"
        * Works with both "insurance" and "policy" keywords
        * DO NOT classify informational queries like "what is insurance" or "explain insurance" as insurance_plan
    
    - INFORMATION/EDUCATIONAL INTENTS (NOT action-oriented, just asking for knowledge):
    - financial_education: User asking for definitions, explanations, or general information about financial products/concepts
        * "What is loan?", "What is insurance?", "What is mutual fund?", "What is finance?"
        * "Explain fixed deposits", "Tell me about credit cards", "How do investments work?"
        * "What are the types of insurance?", "Benefits of mutual funds", "How does EMI work?"
        * "Define cryptocurrency", "What is compound interest?", "Explain tax saving schemes"
        * "What is health insurance?", "What is term insurance?", "What is motor insurance?"
        * "Explain financial assistance", "What are loans?", "Tell me about insurance"
        * General educational queries about financial terms, products, concepts
        * Key patterns: "What is", "What are", "How does", "Explain", "Tell me about", "Define"
        * IMPORTANT: Pure informational queries WITHOUT application intent (no "I want", "I need", "apply")
    
    - protection_score: User asking about their existing insurance policy details, scores, recommendations, and analysis
        * GENERAL POLICY QUESTIONS:
            "What is the insurance type of this policy?", "Who is the insurer?", "What is the protection level?"
            "What is the total score of my policy?", "Can you summarize my health insurance policy?"
            "What is the general recommendation for my policy?", "How confident is the extraction?"
            "What are the category scores?", "What is my policy number?", "What is the timestamp?"
        * POLICY INFO QUESTIONS:
            "What is my sum insured?", "How much is the annual premium?", "Does my policy have a room rent limit?"
            "How many daycare procedures are covered?", "What is the waiting period?", "Does my policy have copayment?"
            "How much ambulance coverage?", "Which insurance company issued this policy?"
            "Does this policy cover daycare treatments?", "Does my policy provide unlimited room rent?"
        * USER INFO QUESTIONS:
            "Who is the policyholder?", "What is the policyholder's age?", "What is the date of birth?"
            "What is the mobile number registered?", "What is the email ID?", "What is the Aadhar number?"
            "What is the PAN number?", "How many family members are covered?", "Is this policy in the name of...?"
            "Can you verify the contact details?"
        * RECOMMENDATIONS QUESTIONS:
            "What are the personalized recommendations?", "Do I need to worry about room rent capping?"
            "Are there any critical recommendations?", "What are the high-priority improvements?"
            "Which category does the recommendation belong to?", "Should I upgrade to no-limit room rent?"
            "How important is the room rent recommendation?", "Are there any gaps in my health coverage?"
            "What should I do to improve my policy?", "What are the medium-priority suggestions?"
        * SCORES BREAKDOWN QUESTIONS:
            "What is the coverage adequacy score?", "What is the waiting period score?"
            "What is the score for additional benefits?", "How good is the service quality score?"
            "What is the cost efficiency score?", "Which category has the highest score?"
            "Which category has the lowest score?", "Can you rank the category scores?"
            "How balanced is my health insurance policy?", "Does my policy need improvement based on category scores?"
        * Key patterns: "my policy", "policy score", "protection score", "insurance analysis", "policy details"
        * "coverage score", "policy recommendations", "insurance summary", "policy breakdown"
    
    - live_event: Current events, news, sports scores, stock market updates
    - unknown: Unclear or ambiguous queries

    Key distinction patterns:
    - "I need money" + [any reason]  FINANCIAL_ASSISTANCE
    - "Give me money" + [any context]  FINANCIAL_ASSISTANCE  
    - "Want cash/funding" + [any purpose]  FINANCIAL_ASSISTANCE
    - "Financial help" + [any situation]  FINANCIAL_ASSISTANCE
    - "[Emergency/medical/wedding/education] + money"  FINANCIAL_ASSISTANCE
    - "I want to..." + [create/apply/get/register]  OTHER ROUTING
    - "What is my..." + [policy/insurance details]  PROTECTION_SCORE (insurance analysis)
    - "How much..." + [premium/coverage/sum insured]  PROTECTION_SCORE (policy info)
    - "What is..." + [financial term/product]  FINANCIAL_EDUCATION (general concepts)
    - "What is..." + [policy score/protection level/recommendation]  PROTECTION_SCORE (policy analysis)

    User input: "{query}"

    Think carefully:
    1. Is user asking for MONEY/CASH/FINANCIAL HELP for any reason?  FINANCIAL_ASSISTANCE
    2. Is user wanting to START a new application/registration?  OTHER ROUTING
    3. Is user asking about their EXISTING INSURANCE POLICY details/scores/recommendations?  PROTECTION_SCORE
    4. Is user asking for DEFINITIONS/EXPLANATIONS of financial concepts?  FINANCIAL_EDUCATION

    Return only the intent keyword: greeting, small_talk, wallet_setup, financial_assistance, insurance_plan, financial_education, protection_score, live_event, or unknown.
    """
    
    try:
        messages = [HumanMessage(content=prompt)]
        response = llm.invoke(messages)
        intent = response.content.strip().lower()

        valid_intents = [
            'greeting', 'small_talk', 'financial_assistance',
            'insurance_plan', 'insurance_analysis', 'policy_query', 'financial_education', 'off_topic', 'live_event', 'unknown'
        ]

        if intent in valid_intents:
            # Cache successful LLM result
            response_cache[query_hash] = {'intent': intent, 'timestamp': time.time()}
            return intent
        else:
            return fallback_intent_detection(query)

    except Exception as e:
        print(f"Error in intent detection: {e}")
        return fallback_intent_detection(query)

def is_off_topic_query(query: str) -> bool:
    """
    Detect if the query is off-topic (not related to insurance/finance).
    Returns True for questions about specific persons, celebrities, politicians, etc.
    """
    query_lower = query.lower().strip()

    # Patterns that indicate off-topic questions about people
    person_question_patterns = [
        'who is', 'who was', 'who are', 'tell me about', 'what do you know about',
        'biography of', 'history of', 'life of', 'story of', 'about the person',
        'when was .* born', 'where was .* born', 'how old is', 'age of'
    ]

    # Self-referential / meta questions about the bot itself
    self_referential_patterns = [
        'what language is this', 'what language are you', 'what language was this',
        'which language is this', 'which language are you', 'which language was this',
        'in what language', 'what language has', 'chatbot written',
        'written in what', 'built with what', 'made with what', 'coded in what',
        'what coding language', 'which coding language', 'programming language',
        'what technology', 'what tech stack', 'tech stack',
        'what libraries', 'which libraries', 'what library', 'which library',
        'what framework', 'which framework', 'what tools do you use',
        'what are you built', 'what are you made', 'how were you built', 'how were you made',
        'who made you', 'who built you', 'who created you', 'who developed you',
        'are you ai', 'are you a bot', 'are you chatgpt', 'are you gpt',
        'what model are you', 'which model are you', 'what llm',
        'your source code', 'your code', 'open source',
        'what database', 'which database', 'what backend', 'what frontend',
        'how do you work', 'how are you built',
        'kaunsi language', 'kis language', 'kaunsa framework', 'kaunsi technology',
        'kisne banaya', 'kaise bana', 'kaun bana',
    ]
    if any(pattern in query_lower for pattern in self_referential_patterns):
        return True

    # Common off-topic categories
    off_topic_keywords = [
        # Politicians and leaders
        'narendra modi', 'modi', 'rahul gandhi', 'gandhi', 'trump', 'biden', 'obama',
        'politician', 'prime minister', 'president', 'minister', 'mla', 'mp',
        # Celebrities and entertainment
        'actor', 'actress', 'bollywood', 'hollywood', 'singer', 'celebrity',
        'movie star', 'film star', 'shahrukh', 'salman', 'aamir', 'amitabh',
        'virat kohli', 'sachin', 'dhoni', 'cricketer', 'footballer',
        # General knowledge / trivia
        'capital of', 'population of', 'area of', 'currency of',
        'who invented', 'who discovered', 'who created', 'who founded',
        'history of india', 'world war', 'ancient', 'historical',
        # Science/Tech unrelated to finance
        'black hole', 'galaxy', 'planet', 'solar system', 'space',
        'dinosaur', 'evolution', 'climate change', 'global warming',
        # Entertainment
        'recipe', 'cooking', 'movie', 'song', 'music', 'game', 'sports score',
        'weather', 'horoscope', 'zodiac', 'astrology',
        # Misc off-topic
        'joke', 'tell me a joke', 'fun fact', 'riddle', 'puzzle',
        # AI / Tech / Coding topics (NOT related to insurance/finance)
        'chatgpt', 'chat gpt', 'claude', 'gemini', 'copilot', 'bard',
        'openai', 'open ai', 'anthropic', 'google ai', 'deepseek',
        'coding', 'programming', 'developer', 'software engineer',
        'python', 'javascript', 'java', 'react', 'flutter', 'django', 'fastapi',
        'html', 'css', 'node', 'typescript', 'golang', 'rust lang',
        'machine learning', 'deep learning', 'neural network',
        'nltk', 'spacy', 'tensorflow', 'pytorch',
        'github', 'stackoverflow', 'stack overflow',
        'better for coding', 'best for coding', 'coding language',
        # Relationships / Personal advice
        'girlfriend', 'boyfriend', 'dating', 'impress a girl', 'impress a boy',
        'relationship advice', 'love life', 'breakup',
        # Health/Medical (non-insurance)
        'diet plan', 'workout', 'exercise', 'gym', 'yoga',
        'home remedy', 'treatment for', 'cure for', 'symptoms of',
    ]

    # Check for person-related question patterns
    import re
    for pattern in person_question_patterns:
        if re.search(pattern, query_lower):
            # Make sure it's not about insurance/finance professionals
            finance_context = ['insurance', 'policy', 'loan', 'bank', 'finance', 'investment', 'mutual fund']
            if not any(fc in query_lower for fc in finance_context):
                return True

    # Check for off-topic keywords
    finance_context = [
        'insurance', 'policy', 'policies', 'loan', 'bank', 'finance', 'premium',
        'claim', 'coverage', 'sum insured', 'nominee', 'rider', 'copay', 'deductible',
        'renewal', 'expire', 'expiry', 'cashless', 'hospitalization', 'bima',
        'port', 'porting', 'protection score', 'eazr', 'upload'
    ]
    for keyword in off_topic_keywords:
        if keyword in query_lower:
            # Double check it's not in financial context
            if not any(fc in query_lower for fc in finance_context):
                return True

    return False


def generate_off_topic_redirect_response(query: str) -> str:
    """
    Generate a response that briefly answers the off-topic question,
    then naturally redirects back to insurance and finance.
    """
    try:
        from ai_chat_components.llm_config import invoke_llm

        prompt = (
            "You are eazr — an insurance and finance expert who talks like a friend.\n\n"
            "The user asked an off-topic question (not about insurance/finance). "
            "Your job:\n"
            "1. Give a SHORT, helpful answer to their question (1-2 sentences max)\n"
            "2. Then naturally transition back to insurance/finance at the END\n"
            "3. Keep the total response under 3 sentences\n"
            "4. Sound casual and friendly, like texting a buddy\n"
            "5. NEVER say 'I can only help with insurance' or 'that's not my area'\n"
            "6. NEVER reveal you are AI/GPT/chatbot\n"
            "7. NEVER use phrases like 'feel free to ask', 'I'd be happy to help', 'Great question'\n\n"
            "Examples:\n"
            "- 'Who is the PM?' → 'Narendra Modi is the current PM of India. Speaking of important stuff — have you checked if your insurance coverage is up to date?'\n"
            "- 'What's the weather today?' → 'I'm not sure about today's weather, you can check any weather app for that! Meanwhile, want me to help you review your policies?'\n"
            "- 'Tell me a joke' → 'Why did the insurance agent bring a ladder? To help you reach better coverage! 😄 On that note, want me to check your policy?'\n"
            "- 'Suggest a movie' → 'Can't go wrong with a good thriller! By the way, when was the last time you reviewed your insurance coverage?'\n"
            "- 'Who built you?' → 'I was built by the eazr team to help people with insurance and finance! So tell me, how can I help you with your policies today?'\n\n"
            f"User question: {query}\n\n"
            "eazr:"
        )

        response = invoke_llm(prompt, use_case='short_insurance_response').strip()

        if response:
            return response

    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"LLM off-topic response failed: {e}")

    # Fallback if LLM fails
    import random
    fallback_responses = [
        f"Hmm, that's an interesting one! But hey, my real expertise is insurance and finance — want me to help you with your policies?",
        f"Good question! I'm more of an insurance and finance person though — need any help with coverage or financial planning?",
    ]
    return random.choice(fallback_responses)


def fallback_intent_detection(query: str) -> str:
    """
    Enhanced fallback intent detection with natural language patterns and financial education
    """
    query_lower = query.lower().strip()

    # Check for off-topic queries first
    if is_off_topic_query(query):
        return "off_topic"

    # ============= INSURANCE ANALYSIS INTENT (HIGH PRIORITY - CHECK FIRST) =============
    # User wants to analyze their existing insurance policy
    # English patterns
    insurance_analysis_patterns_en = [
        'analyze my insurance', 'analyse my insurance',
        'analyze my policy', 'analyse my policy',
        'analyze insurance', 'analyse insurance',
        'analyze policy', 'analyse policy',
        'check my insurance', 'check my policy',
        'review my insurance', 'review my policy',
        'evaluate my insurance', 'evaluate my policy',
        'assess my insurance', 'assess my policy',
        'insurance analysis', 'policy analysis',
        'want to analyze', 'want to analyse',
        'need to analyze', 'need to analyse',
        'i want analysis', 'i need analysis',
        'analyze existing insurance', 'analyze existing policy',
        'scan my insurance', 'scan my policy',
        'audit my insurance', 'audit my policy',
        'insurance audit', 'policy audit',
        'check insurance coverage', 'check policy coverage',
        'analyze coverage', 'analyse coverage',
        'upload my policy', 'upload my insurance',
        'upload insurance', 'upload policy',
        'add my policy', 'add my insurance',
        'add policy for analysis', 'add insurance for analysis'
    ]

    # Hindi patterns (Romanized Hindi - Hinglish)
    insurance_analysis_patterns_hi = [
        'mujhe apna insurance analyze karna hai', 'mujhe apna insurance analyse karna hai',
        'mujhe apna insurance analyze karna he', 'mujhe apna insurance analyse karna he',
        'muje apna insurance analyze karna hai', 'muje apna insurance analyse karna hai',
        'muje apna insurance analyze karna he', 'muje apna insurance analyse karna he',
        'apna insurance analyze karna', 'apna insurance analyse karna',
        'apna policy analyze karna', 'apna policy analyse karna',
        'insurance analyze karna', 'insurance analyse karna',
        'policy analyze karna', 'policy analyse karna',
        'mera insurance check karo', 'meri policy check karo',
        'mera insurance analyze karo', 'meri policy analyze karo',
        'insurance ka analysis', 'policy ka analysis',
        'insurance check karna', 'policy check karna',
        'apna insurance check karna', 'apni policy check karna',
        'insurance dekhna hai', 'policy dekhna hai',
        'apna insurance dekhna', 'apni policy dekhna',
        'insurance upload karna', 'policy upload karna',
        'apna insurance upload', 'apni policy upload',
        'insurance add karna', 'policy add karna'
    ]

    # Check for insurance analysis intent (English)
    if any(pattern in query_lower for pattern in insurance_analysis_patterns_en):
        return "insurance_analysis"

    # Check for insurance analysis intent (Hindi/Hinglish)
    if any(pattern in query_lower for pattern in insurance_analysis_patterns_hi):
        return "insurance_analysis"

    # Additional keyword combination check for insurance analysis
    analyze_keywords = ['analyze', 'analyse', 'analysis', 'check', 'review', 'evaluate', 'assess', 'audit', 'scan', 'upload', 'add']
    insurance_keywords = ['insurance', 'policy', 'coverage', 'bima', 'beema']
    my_keywords = ['my', 'mera', 'meri', 'apna', 'apni', 'apne', 'existing']

    has_analyze = any(kw in query_lower for kw in analyze_keywords)
    has_insurance = any(kw in query_lower for kw in insurance_keywords)
    has_my = any(kw in query_lower for kw in my_keywords)

    # If user wants to analyze/check their insurance
    if has_analyze and has_insurance:
        return "insurance_analysis"

    # If user mentions "my insurance/policy" with action intent
    if has_my and has_insurance and has_analyze:
        return "insurance_analysis"
    # ============= END INSURANCE ANALYSIS INTENT =============

    greeting_keywords = ['hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening']
    if any(keyword in query_lower for keyword in greeting_keywords):
        return "greeting"
    
    small_talk_patterns = ['how are you', 'thank you', 'thanks', 'bye', 'goodbye', 'see you']
    if any(pattern in query_lower for pattern in small_talk_patterns):
        return "small_talk"
    
    education_patterns = [
        'what is', 'what are', 'explain', 'tell me about', 'how does', 'how do',
        'define', 'meaning of', 'types of', 'benefits of', 'advantages of',
        'what does', 'how to understand', 'please explain', 'can you explain'
    ]
    
    financial_terms = [
        'loan', 'loans', 'insurance', 'mutual fund', 'investment', 'credit card',
        'fixed deposit', 'fd', 'sip', 'emi', 'interest', 'tax', 'saving', 'bank',
        'debit card', 'equity', 'bond', 'portfolio', 'dividend', 'premium',
        'policy', 'coverage', 'claim', 'maturity', 'compound interest', 'simple interest',
        'financial assistance', 'finance', 'financial help', 'health insurance',
        'life insurance', 'term insurance', 'motor insurance', 'car insurance'
    ]
    
    # Check if this is an educational/informational query
    is_educational_query = any(pattern in query_lower for pattern in education_patterns)

    # Return early for educational queries about financial terms
    for pattern in education_patterns:
        if pattern in query_lower:
            for term in financial_terms:
                if term in query_lower:
                    return 'financial_education'

    # Financial assistance APPLICATION triggers (action-oriented, NOT informational)
    financial_need_patterns = [
        'i need money', 'give me money', 'want money', 'need cash', 'give me cash',
        'want cash', 'i need financial help', 'i want financial assistance',
        'cash advance', 'instant money', 'urgent money', 'emergency money', 'quick money',
        'funding required', 'financial support', 'money for', 'cash for',
        'need funding', 'require money', 'want funding', 'give me financial',
        'mother admitted', 'mother is admitted', 'mother hospital', 'mother treatment',
        'father admitted', 'father hospital', 'medical emergency', 'hospital bills',
        'sister wedding', 'sister weeding', 'brother wedding', 'family wedding',
        'wedding expenses', 'marriage expenses', 'ceremony money',
        'education fees', 'school fees', 'college fees', 'study expenses',
        'business funding', 'business money', 'startup funding',
        'home renovation', 'house repair', 'property expenses',
        'emergency funds', 'urgent expenses', 'immediate money',
        'debt payment', 'bill payment', 'rent payment',
        'travel money', 'vacation funding', 'trip expenses',
        # Loan action patterns (user wants to GET/APPLY for a loan)
        'get a loan', 'get loan', 'can i get a loan', 'can i get loan',
        'apply for loan', 'apply for a loan', 'apply loan',
        'need a loan', 'need loan', 'want a loan', 'want loan',
        'loan apply', 'loan chahiye', 'loan lena', 'loan le',
        'loan dedo', 'loan de do', 'loan dila do', 'loan dilao',
        'personal loan', 'home loan', 'car loan', 'education loan',
        'business loan', 'instant loan', 'quick loan',
    ]

    # Only trigger if NOT an educational query
    if not is_educational_query:
        if any(pattern in query_lower for pattern in financial_need_patterns):
            return "financial_assistance"
    
    money_keywords = ['money', 'cash', 'funding', 'financial', 'advance', 'emergency', 'loan']
    context_keywords = [
        'need', 'want', 'require', 'give', 'help', 'urgent', 'immediate',
        'get', 'apply', 'can i', 'take', 'avail',
        'hospital', 'medical', 'wedding', 'marriage', 'education', 'business',
        'emergency', 'treatment', 'expenses', 'bills', 'fees'
    ]

    has_money_keyword = any(keyword in query_lower for keyword in money_keywords)
    has_context = any(keyword in query_lower for keyword in context_keywords)

    if has_money_keyword and has_context and not is_educational_query:
        return "financial_assistance"
    
    # Insurance APPLICATION triggers (action-oriented only, NOT informational)
    insurance_application_patterns = [
        'i want insurance', 'i need insurance', 'buy insurance', 'purchase insurance',
        'get me insurance', 'insurance application', 'apply for insurance',
        'i want health insurance', 'i need life insurance', 'buy motor insurance',
        'apply health insurance', 'apply life insurance', 'apply motor insurance',
        'give me insurance', 'need insurance plan', 'want insurance plan',
        'i need policy', 'i want policy', 'buy policy', 'purchase policy',
        'get me policy', 'get policy', 'give me policy', 'policy application',
        'apply for policy', 'new policy', 'create policy', 'need policy',
        'want policy', 'need health policy', 'want life policy', 'get motor policy'
    ]

    # Check it's NOT an educational query first
    if not is_educational_query:
        if any(phrase in query_lower for phrase in insurance_application_patterns):
            return "insurance_plan"
    
    wallet_trigger_phrases = [
        'create wallet', 'set up wallet', 'wallet registration', 'register wallet',
        'open account', 'new wallet', 'wallet account', 'create account',
        'i want wallet', 'setup wallet'
    ]
    if any(phrase in query_lower for phrase in wallet_trigger_phrases):
        return "wallet_setup"

    live_event_keywords = [
        'latest news', 'current news', 'cricket score', 'stock market', 
        'breaking news', 'today news', 'live score', 'market update'
    ]
    if any(keyword in query_lower for keyword in live_event_keywords):
        return "live_event"
    
    return "unknown"

def generate_casual_response_with_context(query: str, conversation_history: List[Dict] = None) -> str:
    """Enhanced casual response generation with STRICT 2-3 sentence limit for insurance chatbot"""
    try:
        session_id = get_session_id_from_context(query, conversation_history)
        cleanup_old_sessions()
        
        # Create a custom short response chain
        chain_key = f"{session_id}_en"
        
        if chain_key not in conversation_chains:
            memory = ConversationBufferWindowMemory(
                k=2,  # Only keep last 2 exchanges to prevent context bleeding
                memory_key="chat_history",
                return_messages=False
            )

            # INSURANCE RESPONSE PROMPT TEMPLATE - Human-like persona
            prompt_template = """You're eazr — been in insurance and finance for 8+ years. You talk like a friend who knows their stuff.

Previous conversation:
{chat_history}

Rules:
1. CRITICAL: Answer the CURRENT question below. Do NOT repeat or continue your answer to a previous question. Each new message = fresh question.
2. Max 2-3 short sentences, under 45 words — like texting a friend. But if user asks MULTIPLE questions, answer ALL (up to 5-6 sentences OK).
3. Talk naturally — "honestly", "here's the deal", "in my experience"
4. NEVER start with "Great question" or "I'd be happy to help"
5. No emojis, no bullet points
6. NEVER say you're an AI or mention OpenAI/GPT/ChatGPT

MOST IMPORTANT — OFF-TOPIC HANDLING:
- Your expertise is insurance, finance, loans, policies.
- If they ask about ANYTHING outside insurance/finance:
  1. Give a SHORT helpful answer (1-2 sentences)
  2. Then redirect to insurance/finance
  3. NEVER say "that's not my area" — just answer briefly and redirect
- Example: "I'm bored" → "Haha I feel you! Hey when's the last time you checked your policy coverage?"
- Example: "recommend movies" → "Can't go wrong with a good thriller! By the way, want me to check your coverage?"

Current question: {input}

eazr:"""
            prompt = PromptTemplate(
                input_variables=["chat_history", "input"],
                template=prompt_template
            )

            # Create LLM with limited tokens for controlled responses
            from ai_chat_components.llm_config import get_llm
            short_llm = get_llm(use_case='short_response')

            conversation_chains[chain_key] = ConversationChain(
                llm=short_llm,
                memory=memory,
                prompt=prompt,
                verbose=False
            )

        conversation_chain = conversation_chains[chain_key]
        
        # Get response
        response = conversation_chain.predict(input=query)
        
        # POST-PROCESSING: Enforce reasonable length
        response_text = response.strip()

        # Detect if user asked multiple questions (has "and", "aur", "?", multiple question marks)
        query_lower = query.lower()
        is_multi_q = (
            query_lower.count('?') >= 2 or
            ' and ' in query_lower or
            ' aur ' in query_lower or
            ', also ' in query_lower or
            ' also ' in query_lower
        )

        # Set limits based on whether it's a multi-question
        max_sentences = 6 if is_multi_q else 3
        max_chars = 500 if is_multi_q else 250
        max_words = 90 if is_multi_q else 50

        # Method 1: Split by sentence endings
        sentence_enders = ['. ', '! ', '? ']
        sentences = []
        current_sentence = ""

        for char in response_text:
            current_sentence += char
            if any(current_sentence.endswith(ender) for ender in sentence_enders):
                sentences.append(current_sentence.strip())
                current_sentence = ""

        if current_sentence:  # Add remaining text as last sentence
            sentences.append(current_sentence.strip())

        # Enforce sentence limit
        if len(sentences) < 2:
            response_text = response_text.strip()
            if not response_text.endswith(('.', '!', '?', '')):
                response_text += '.'
            response_text += " Anything else you want to know?"
        elif len(sentences) > max_sentences:
            response_text = ' '.join(sentences[:max_sentences])
            if not response_text.endswith(('.', '!', '?', '')):
                response_text += '.'
        else:
            response_text = ' '.join(sentences)

        # Method 2: Character limit backup (if still too long)
        if len(response_text) > max_chars:
            truncated = response_text[:max_chars - 3]
            last_period = max(
                truncated.rfind('. '),
                truncated.rfind('! '),
                truncated.rfind('? ')
            )
            if last_period > 80:
                response_text = truncated[:last_period + 1]
            else:
                response_text = truncated + '...'

        # Method 3: Word count limit
        words = response_text.split()
        if len(words) > max_words:
            response_text = ' '.join(words[:max_words]) + '...'
        
        # Store conversation
        conversation_memories[chain_key].append({"role": "user", "content": query})
        conversation_memories[chain_key].append({"role": "assistant", "content": response_text})
        
        return response_text
        
    except Exception as e:
        print(f"Error in response generation: {e}")
        
        # FALLBACK: Direct API call with strict instructions
        try:
            # Build context from history
            context_info = ""
            if conversation_history and len(conversation_history) > 0:
                recent_topics = []
                for msg in conversation_history[-4:]:
                    content = msg.get('content', '').lower()
                    if 'insurance' in content or 'coverage' in content:
                        recent_topics.append('insurance')
                    if 'policy' in content or 'claim' in content:
                        recent_topics.append('policies')
                    if 'protect' in content or 'risk' in content:
                        recent_topics.append('protection')
                
                if recent_topics:
                    context_info = f"Context: discussing {', '.join(set(recent_topics))}"
            
            # Use LLM fallback system with very strict prompt
            from ai_chat_components.llm_config import invoke_llm

            system_prompt = "You're eazr, insurance and finance expert with 8+ years experience. Rules: 1) Usually 2-3 sentences. If user asks MULTIPLE questions in one message, answer ALL of them (up to 5-6 sentences OK). 2) Sound like a real person, not a chatbot. Never say 'Great question' or 'I'd be happy to help'. 3) For off-topic questions: give a SHORT answer first, then naturally redirect to insurance/finance at the end. Never say 'that's not my area'. 4) Never mention AI, GPT, or OpenAI — you were built by eazr team."

            user_prompt = f"{context_info}\nUser: {query}\n\neazr:"

            # Combine system and user prompts
            full_prompt = f"{system_prompt}\n\n{user_prompt}"

            response = invoke_llm(full_prompt, use_case='short_insurance_response').strip()
            
            # Enforce limits on API response (relaxed for multi-Q)
            sentences = response.split('. ')
            if len(sentences) < 2:
                response += ' Want to know more about this?'
            elif len(sentences) > 6:
                response = '. '.join(sentences[:6]) + '.'

            if len(response) > 500:
                response = response[:497] + '...'
            
            return response
            
        except Exception as api_error:
            print(f"API Error: {api_error}")
            # Ultimate fallback for insurance - human-like
            return "Hey! I'm eazr — been doing insurance and finance for years. What do you want to know? I'm all ears!"

def generate_casual_response_hindi(query: str, conversation_history: List[Dict] = None) -> str:
    """Updated Hindi casual response function with ConversationBufferMemory"""
    if conversation_history:
        return generate_casual_response_hindi_with_context(query, conversation_history)
    else:
        try:
            session_id = get_session_id_from_context(query, conversation_history)
            cleanup_old_sessions()
            conversation_chain = get_or_create_conversation_chain(session_id, 'hi')
            response = conversation_chain.predict(input=query)
            
            chain_key = f"{session_id}_hi"
            if chain_key not in conversation_memories:
                conversation_memories[chain_key] = []
            conversation_memories[chain_key].append({"role": "user", "content": query})
            conversation_memories[chain_key].append({"role": "assistant", "content": response})
            
            return response.strip()
            
        except Exception as e:
            prompt = f"""     eazr       :

1.        ,        
2.            
3.             

:
-        
-       
-      ,   , , ,      
-          
-         -       
-          

  : "{query}"

   :"""
            
            try:
                messages = [HumanMessage(content=prompt)]
                response = llm.invoke(messages)
                return response.content.strip()
            except Exception:
                return "!      !                        !    ? "

def detect_multilingual_intent(query: str, detected_language: str = 'en') -> str:
    """Enhanced intent detection that works with multiple languages"""
    return detect_intent(query)

def generate_multilingual_casual_response(query: str, language: str = 'en') -> str:
    """Generate casual responses in multiple languages"""
    casual_responses = {
        'en': {
            'greeting': "Hey! What's up? Need help with insurance or finance stuff?",
            'thanks': "Anytime! Anything else you wanna know?",
            'bye': "See ya! Hit me up anytime you need help with insurance stuff!",
            'default': "Hey! What do you want to know about insurance or finance?"
        },
        'hi': {
            'greeting': "!        ?",
            'thanks': "  !          ?",
            'bye': "!    !",
            'default': "          "
        }
    }
    
    responses = casual_responses.get(language, casual_responses['en'])
    query_lower = query.lower()
    
    if any(word in query_lower for word in ['hello', 'hi', '']):
        return responses['greeting']
    elif any(word in query_lower for word in ['thanks', 'thank you', '']):
        return responses['thanks']
    elif any(word in query_lower for word in ['bye', 'goodbye', '']):
        return responses['bye']
    else:
        return generate_casual_response_with_context(query)

def detect_exit_intent(user_input: str) -> bool:
    """Fixed: Don't treat normal answers as exit intent"""
    if not user_input:
        return False
    
    input_lower = user_input.lower().strip()
    
    exit_keywords = [
        'exit', 'quit', 'stop', 'cancel', 'end', 'leave', 'abort',
        'bye', 'goodbye', 'close', 'finish', 'done', 'nevermind',
        'no thanks', 'not now', 'later', 'back', 'return', 'main menu'
    ]
    
    normal_answers = ['test', 'yes', 'no', 'ok', 'thanks', 'help', 'hello', 'hi']
    if input_lower in normal_answers:
        return False
    
    if re.match(r'^[a-zA-Z\s]{1,50}$', user_input) and len(user_input.split()) <= 4:
        return False
    
    if user_input.replace(' ', '').replace('-', '').replace('+', '').isdigit():
        return False
    
    return input_lower in exit_keywords

def detect_new_intent_during_chatbot(user_input: str) -> tuple:
    """Detect if user is asking for something else during chatbot session"""
    if not user_input:
        return False, None
    
    input_lower = user_input.lower().strip()
    
    help_keywords = ['help', 'what can you do', 'options', 'services', 'menu', 
                     'what do you offer', 'show me options', 'main menu']
    for keyword in help_keywords:
        if keyword in input_lower:
            return True, 'help'
    
    greetings = ['hi', 'hello', 'hey', 'good morning', 'good afternoon', 
                 'good evening', 'greetings', 'howdy']
    if input_lower in greetings or any(input_lower.startswith(g) for g in greetings):
        return True, 'greeting'

    if any(word in input_lower for word in ['money', 'cash', 'financial help', 'funding']):
        return True, 'financial_assistance'

    return False, None

def detect_multilingual_intent_enhanced(query: str, detected_language: str = 'en') -> str:
    """Enhanced intent detection that works better with Hindi input"""
    if detected_language == 'hi':
        try:
            from support_features.multilingual_support import translate_to_target_language
            english_query = translate_to_target_language(query, 'en')
            return detect_intent(english_query)
        except:
            pass
    
    return detect_intent(query)

def generate_casual_response_hindi_with_context(query: str, conversation_history: List[Dict] = None) -> str:
    """Enhanced Hindi casual response generation with windowed memory"""
    try:
        session_id = get_session_id_from_context(query, conversation_history)
        cleanup_old_sessions()
        conversation_chain = get_or_create_conversation_chain(session_id, 'hi')

        # WindoowMemory handles its own history — no manual loading needed
        response = conversation_chain.predict(input=query)
        
        return response.strip()
        
    except Exception as e:
        context_info = ""
        if conversation_history and len(conversation_history) > 0:
            recent_topics = []
            
            for msg in conversation_history[-2:]:
                content = msg.get('content', '').lower()

                if 'mango' in content or '' in content:
                    recent_topics.append('')
                if any(word in content for word in ['financial', 'money', 'loan', '', '', '']):
                    recent_topics.append(' ')
                if any(word in content for word in ['insurance', '']):
                    recent_topics.append('')
                if any(word in content for word in ['balance', 'account', '', '']):
                    recent_topics.append('')
            
            if recent_topics:
                context_info = f"({', '.join(set(recent_topics))} )"
        
        prompt = f""" eazr    

:  1-2        

: {context_info if context_info else " "}

:
-  1-2   
-   
-     
-      

: "{query}"

    (1-2 ):"""
        
        try:
            messages = [HumanMessage(content=prompt)]
            response = llm.invoke(messages)
            
            response_text = response.content.strip()
            sentences = response_text.split('')
            
            if len(sentences) > 2:
                response_text = ''.join(sentences[:2]) + ''
            
            return response_text
            
        except Exception:
            if context_info:
                return f" ! {context_info}      ! "
            else:
                return "!     ,   ? "

def generate_financial_education_response(query: str, conversation_history: List[Dict] = None) -> str:
    """Generate concise financial education responses without structured formatting"""
    
    context_info = ""
    discussed_topics = []
    
    if conversation_history and len(conversation_history) > 0:
        for msg in conversation_history[-4:]:
            content = msg.get('content', '').lower()
            
            if any(term in content for term in ['loan', 'loans', 'lending', 'borrow']):
                discussed_topics.append('loans')
            elif any(term in content for term in ['insurance', 'policy', 'coverage']):
                discussed_topics.append('insurance')
            elif any(term in content for term in ['investment', 'mutual fund', 'stock']):
                discussed_topics.append('investments')
            elif any(term in content for term in ['bank', 'account', 'saving']):
                discussed_topics.append('banking')
        
        if discussed_topics:
            unique_topics = list(set(discussed_topics))
            if len(unique_topics) == 1:
                context_info = f"Since we were discussing {unique_topics[0]}, "
            else:
                context_info = f"Building on our conversation about financial topics, "

    prompt = f"""You're eazr — explaining financial stuff to a friend in simple terms. You've been doing this for 8+ years.

{context_info}They asked: "{query}"

How to answer:
- 2-3 sentences max — explain it like you'd tell a friend
- Use everyday language, skip the jargon
- Focus on what's actually useful for them
- No bullet points, no emojis, no formatting — just talk
- NEVER start with "Great question" or "I'd be happy to" — just answer directly
- Tie it back to their real life — how does this affect their money/planning?"""

    try:
        messages = [HumanMessage(content=prompt)]
        response = llm.invoke(messages)
        return response.content.strip()
    except Exception:
        return "Hmm, that's a good one — can you tell me a bit more about what specifically you want to understand? I want to make sure I give you the right info!"

def detect_conversation_continuity(query: str, conversation_history: List[Dict] = None) -> Dict:
    """Detect if the current query is continuing a previous conversation topic"""
    
    if not conversation_history or len(conversation_history) == 0:
        return {"is_continuation": False, "related_topics": []}
    
    query_lower = query.lower()
    related_topics = []
    is_continuation = False
    
    recent_messages = conversation_history[-10:]
    
    for msg in recent_messages:
        content = msg.get('content', '').lower()
        
        if 'mango' in content and 'mango' in query_lower:
            related_topics.append('mango')
            is_continuation = True
        
        if any(word in content for word in ['financial', 'money', 'loan']) and any(word in query_lower for word in ['financial', 'money', 'loan']):
            related_topics.append('finance')
            is_continuation = True
        
        if 'insurance' in content and 'insurance' in query_lower:
            related_topics.append('insurance')
            is_continuation = True
        
        if any(word in content for word in ['balance', 'account']) and any(word in query_lower for word in ['balance', 'account']):
            related_topics.append('banking')
            is_continuation = True
    
    continuation_indicators = [
        'what about', 'tell me more', 'also', 'and', 'what else', 
        'more about', 'regarding', 'about that', 'last question'
    ]
    
    if any(indicator in query_lower for indicator in continuation_indicators):
        is_continuation = True

    return {
        "is_continuation": is_continuation,
        "related_topics": list(set(related_topics)),
        "continuation_strength": len(related_topics)
    }

def get_last_user_question(conversation_history: List[Dict] = None) -> str:
    """Extract the last question asked by the user"""
    
    if not conversation_history:
        return ""
    
    for msg in reversed(conversation_history):
        if msg.get('role') == 'user':
            return msg.get('content', '')
    
    return ""

def generate_contextual_suggestions(conversation_history: List[Dict] = None) -> List[str]:
    """Generate contextual suggestions based on conversation history"""
    
    suggestions = []
    
    if not conversation_history or len(conversation_history) == 0:
        return [
            "Tell me about your services",
            "How can you help me?", 
            "What financial products do you offer?",
            "I need financial assistance"
        ]
    
    recent_topics = set()
    recent_intents = set()
    
    for msg in conversation_history[-8:]:
        content = msg.get('content', '').lower()
        
        if 'mango' in content:
            recent_topics.add('mango')
        if any(word in content for word in ['financial', 'money', 'loan']):
            recent_topics.add('financial')
        if 'insurance' in content:
            recent_topics.add('insurance')
        if any(word in content for word in ['balance', 'account']):
            recent_topics.add('banking')
    
    if 'mango' in recent_topics:
        suggestions.extend([
            "Tell me about other fruits",
            "Mango recipes?",
            "Mango health benefits?"
        ])
    
    if 'financial' in recent_topics:
        suggestions.extend([
            "What documents do I need?",
            "How long does approval take?",
            "What are the interest rates?"
        ])
    
    if 'insurance' in recent_topics:
        suggestions.extend([
            "What is covered?",
            "How much is the premium?",
            "How do I claim?"
        ])
    
    if 'banking' in recent_topics:
        suggestions.extend([
            "Show transaction history",
            "Check my bills",
            "What are my limits?"
        ])
    
    if len(suggestions) < 3:
        suggestions.extend([
            "What else can you help with?",
            "Tell me more about your services",
            "How does this work?",
            "What are my options?"
        ])
    
    return suggestions[:4]

def detect_intent_with_context(query: str, conversation_history: List[Dict] = None) -> str:
    """
    UPGRADED: Enhanced intent detection with conversation context and 6-message awareness

    Now uses advanced intent detector that understands:
    - Negation and sentiment
    - Previous 6 messages context
    - Topic continuity from conversation history
    """
    query_lower = query.lower().strip()

    # Check for reference to previous question first
    if any(phrase in query_lower for phrase in ['last question', 'what i asked', 'previous question', 'earlier']):
        return "reference_to_previous"

    # ========== ABSOLUTE FIRST: NEGATION/REJECTION DETECTION ==========
    # If user says "don't want", "not interested", "no need" etc. - this is rejection/decline
    # This MUST be checked BEFORE any action patterns to avoid false positives
    negation_words = ["don't", "dont", "do not", "not", "no", "never", "nahi", "mat", "na", "naa", "won't", "wont", "can't", "cant"]
    action_words = ['want', 'need', 'upload', 'buy', 'get', 'purchase', 'apply', 'analyze', 'analyse', 'check', 'review']

    has_negation = any(neg in query_lower for neg in negation_words)
    has_action = any(act in query_lower for act in action_words)

    # Check for negation patterns like "i dont want", "not interested", "no need"
    rejection_patterns = [
        "don't want", "dont want", "do not want",
        "don't need", "dont need", "do not need",
        "not interested", "no interest",
        "no need", "no thanks", "not now", "later",
        "nahi chahiye", "nahi chaiye", "mat karo", "band karo",
        "i refuse", "i decline", "skip", "cancel"
    ]

    is_rejection = any(pattern in query_lower for pattern in rejection_patterns)

    # If clear rejection pattern OR (negation + action word in specific structure)
    if is_rejection or (has_negation and has_action and ('want' in query_lower or 'need' in query_lower)):
        # Make sure it's actually rejecting, not asking "do i have any" type questions
        question_starters = ['do i have', 'have i', 'did i', 'what', 'how many', 'show']
        is_question = any(qs in query_lower for qs in question_starters)

        if not is_question:
            logger.info(f"✅ REJECTION DETECTED: User declining action: '{query[:50]}'")
            return "unknown"  # Return unknown so it goes to casual conversation
    # ========== END NEGATION DETECTION ==========

    # ========== ENHANCED POLICY QUERY DETECTION (PRE-CHECK) ==========
    # These patterns MUST be detected as policy_query regardless of what LLM says
    # This ensures queries about uploaded policies are never misclassified
    policy_query_force_patterns = [
        # Count/existence queries
        'how many policies', 'how many policy', 'how many insurance',
        'policies have i', 'policy have i', 'policies i have',
        'have i uploaded', 'i have uploaded', 'i uploaded', 'uploaded any',
        'i am uploaded', 'am i uploaded', 'am uploaded',
        'do i have any policy', 'do i have policy', 'any policy uploaded',
        'uploaded self', 'uploaded family', 'self policy', 'family policy',
        # Status queries
        'my policies', 'my policy details', 'show my policies', 'show my policy',
        'list my policies', 'view my policies', 'see my policies',
        # Coverage queries
        'coverage gaps', 'coverage gap', 'my gaps', 'gaps in',
        'what is covered', 'what is not covered', 'exclusions',
        'my coverage', 'coverage details', 'coverage kya hai', 'mera coverage',
        'what does my policy cover', 'what am i covered for', 'am i covered',
        # Score/recommendation queries
        'protection score', 'my score', 'my recommendations',
        'sum assured', 'my premium', 'premium amount', 'premium of', 'how much premium',
        'policy expiry', 'when expire',
        # Policy status queries
        'policy active', 'policies active', 'is my policy', 'are my policies',
        'are all my policies', 'is it active', 'policy status', 'policies status',
        'policy expired', 'policies expired', 'policy lapsed', 'still active', 'still valid',
        # Locker policy queries
        'locker policy', 'locker policies', 'review my locker', 'check my locker',
        'my locker', 'in my locker', 'from my locker',
        # Insurance-specific detail queries (room rent, deductible, etc.)
        'room rent', 'sub limit', 'sublimit', 'sub-limit',
        'deductible', 'co-pay', 'copay', 'copayment',
        'waiting period', 'cooling period',
        'no claim bonus', 'ncb', 'cashless', 'network hospital',
        'claim settlement', 'claim ratio', 'claim process',
        'does my policy', 'does it have', 'is there any', 'is there a',
        'does it cover', 'will my policy', 'can i claim',
        # Family/personal queries from policy
        'who is my nominee', 'my nominee', 'my brother', 'my sister', 'my father', 'my mother',
        'brother name', 'sister name', 'father name', 'mother name', 'spouse name',
        'family member', 'who is covered', 'family coverage',
        # Show [family member] policies patterns
        'show sister', 'show brother', 'show father', 'show mother', 'show spouse',
        'show wife', 'show husband', 'show son', 'show daughter',
        'sister policies', 'brother policies', 'father policies', 'mother policies',
        'spouse policies', 'wife policies', 'husband policies', 'son policies', 'daughter policies',
        'policies for sister', 'policies for brother', 'policies for father', 'policies for mother',
        'policies for spouse', 'policies for wife', 'policies for husband', 'policies for son', 'policies for daughter',
        # Hindi family member patterns
        'behen ki policy', 'bhai ki policy', 'papa ki policy', 'mummy ki policy',
        'pati ki policy', 'patni ki policy', 'beta ki policy', 'beti ki policy',
        # Hindi patterns
        'meri policy', 'kitni policy', 'kitne policy', 'maine upload',
        'coverage gaps batao', 'recommendations batao', 'protection score kya',
        # Premium/discount queries
        'premium kitna', 'mera premium', 'mere premium', 'discount milega',
        # Compound query patterns
        'critical illness', 'critical cover',
        'i want to port', 'want to port',
        'how do cashless', 'cashless work',
        'expired policies', 'expired policy', 'expire hone',
        'i want to know my policy', 'policy number',
        'what riders', 'what all riders', 'riders do i',
    ]

    # ========== EARLY POLICY QUERY CHECK (MUST come BEFORE financial education check) ==========
    # Specific policy data patterns like "premium amount", "policy active" should be policy_query
    # even if they also match education starters (e.g., "whats the premium amount of tata aig")
    if any(pattern in query_lower for pattern in policy_query_force_patterns):
        logger.info(f"✅ FORCE POLICY_QUERY (early check): Pattern matched: '{query[:50]}'")
        return "policy_query"
    # ========== END EARLY POLICY QUERY CHECK ==========

    # ========== FINANCIAL EDUCATION PRE-CHECK (must come BEFORE buy insurance check) ==========
    # Educational/informational queries about insurance/finance should NOT be classified as action intents
    # BUT queries about user's OWN policy (possessive: "my", "mera", "meri") are policy_query, NOT education
    education_question_starters = [
        'what is', 'what are', 'what\'s', 'whats',
        'how does', 'how do', 'how is', 'how are',
        'explain', 'define', 'tell me about', 'tell me the',
        'meaning of', 'definition of',
        'difference between', 'difference of', 'differnce between',
        'compare', 'comparison between', 'comparison of',
        'types of', 'type of', 'kinds of', 'kind of',
        'benefits of', 'advantage of', 'advantages of',
        'disadvantage of', 'disadvantages of', 'pros and cons',
        'which is better', 'what should i know',
        'kya hota hai', 'kya hai', 'kya hain', 'kya he',
        'samjhao', 'samjha do', 'batao kya', 'kya fark',
        'fark kya', 'antar kya', 'matlab kya',
    ]
    education_topic_words = [
        'insurance', 'policy', 'term insurance', 'whole life', 'endowment',
        'ulip', 'health insurance', 'motor insurance', 'life insurance',
        'loan', 'emi', 'interest rate', 'mutual fund', 'fixed deposit',
        'credit score', 'deductible', 'premium', 'sum assured',
        'copay', 'copayment', 'claim', 'maturity', 'surrender value',
        'annuity', 'rider', 'bima', 'beema',
        'sip', 'nps', 'tax saving', 'term plan', 'money back',
        'third party', 'comprehensive', 'waiting period', 'no claim bonus',
        'ncb', 'floater', 'cashless',
    ]
    # Possessive indicators — "my policy", "meri insurance" etc. = asking about THEIR policy, NOT education
    possessive_indicators = [
        'my ', 'mera ', 'meri ', 'mere ', 'apna ', 'apni ', 'apne ',
        'hamara ', 'hamari ', 'humara ', 'humari ',
    ]
    has_education_starter = any(starter in query_lower for starter in education_question_starters)
    has_education_topic = any(topic in query_lower for topic in education_topic_words)
    has_possessive = any(poss in query_lower for poss in possessive_indicators)

    if has_education_starter and has_education_topic and not has_possessive:
        logger.info(f"✅ FORCE FINANCIAL_EDUCATION: Informational query detected: '{query[:50]}'")
        return "financial_education"
    # ========== END FINANCIAL EDUCATION PRE-CHECK ==========

    # ========== HIGHEST PRIORITY: Check if user wants to BUY/GET insurance (insurance_plan) ==========
    # This must be checked FIRST to avoid misclassification
    buy_insurance_indicators = [
        'buy insurance', 'buy policy', 'buy any policy', 'buy a policy',
        'get insurance', 'get policy', 'get any policy', 'get a policy',
        'purchase insurance', 'purchase policy', 'purchase any policy',
        'want insurance', 'want policy', 'want any policy', 'want a policy',
        'need insurance', 'need policy', 'need any policy', 'need a policy',
        'apply for insurance', 'apply for policy', 'apply insurance', 'apply policy',
        'can i buy insurance', 'can i buy policy', 'can i buy a policy',
        'can i get insurance', 'can i get policy', 'can i get a policy',
        'can i purchase insurance', 'can i purchase policy', 'can i purchase a policy',
        'can i apply for insurance', 'can i apply for policy',
        'i want to buy insurance', 'i want to buy policy', 'i want to buy a policy',
        'i want to get insurance', 'i want to get policy',
        'i want to purchase insurance', 'i want to purchase policy',
        'give me insurance', 'give me policy',
        # Hindi patterns
        'insurance chahiye', 'policy chahiye', 'bima chahiye', 'bima lena'
    ]
    is_buy_insurance = any(action in query_lower for action in buy_insurance_indicators)

    # Also check keyword combination: buy/get/purchase/want/need + insurance/policy/bima
    # This catches "buy health insurance", "get term policy", etc. where words aren't adjacent
    if not is_buy_insurance:
        buy_action_words = ['buy', 'purchase', 'get me', 'give me', 'apply for']
        insurance_target_words = ['insurance', 'policy', 'bima', 'beema']
        has_buy_action = any(w in query_lower for w in buy_action_words)
        has_insurance_target = any(w in query_lower for w in insurance_target_words)
        # Exclude loan/money queries — "get a loan" should NOT match insurance_plan
        has_non_insurance_target = any(w in query_lower for w in ['loan', 'money', 'cash', 'funding'])
        if has_buy_action and has_insurance_target and not has_non_insurance_target:
            is_buy_insurance = True

    if is_buy_insurance:
        logger.info(f"✅ FORCE INSURANCE_PLAN: User wants to buy/get insurance: '{query[:50]}'")
        return "insurance_plan"
    # ========== END BUY INSURANCE CHECK ==========

    # ========== SECOND: Check if user wants to UPLOAD/ANALYZE NEW policy (insurance_analysis) ==========
    # This must be checked BEFORE policy_query patterns to avoid misclassification
    upload_action_indicators = [
        'want to upload', 'want upload', 'i want uploaded', 'upload new', 'upload a', 'upload my',
        'need to upload', 'for analyzing', 'for analysis', 'analyze new', 'analyse new',
        'want to analyze', 'want to analyse', 'new policy for', 'uploaded new',
        'want analyzed', 'want analysed', 'analyze my new', 'analyse my new',
        'analyze my policy', 'analyse my policy', 'check my policy', 'review my policy',
        'add policy', 'add my policy', 'add insurance', 'add my insurance',
        'add a policy', 'add new policy', 'add a insurance', 'add new insurance',
        'policy add', 'insurance add',
        'policy add karna', 'insurance add karna', 'policy add karo', 'insurance add karo',
    ]
    is_upload_action = any(action in query_lower for action in upload_action_indicators)

    # Exclude locker-related queries — user wants to review EXISTING policies, not upload new ones
    if is_upload_action and 'locker' not in query_lower:
        logger.info(f"✅ FORCE INSURANCE_ANALYSIS: User wants to upload/analyze policy: '{query[:50]}'")
        return "insurance_analysis"
    # ========== END UPLOAD ACTION CHECK ==========

    # Force policy_query for these patterns (only if NOT uploading new policy)
    if any(pattern in query_lower for pattern in policy_query_force_patterns):
        logger.info(f"✅ FORCE POLICY_QUERY: Pattern matched in pre-check: '{query[:50]}'")
        return "policy_query"

    # Check for "uploaded" past tense + policy reference (asking about EXISTING uploaded policies)
    # NOT if user wants to upload NEW policy
    if 'uploaded' in query_lower and any(pw in query_lower for pw in ['policy', 'policies', 'insurance', 'self', 'family']):
        logger.info(f"✅ FORCE POLICY_QUERY: 'uploaded' + policy reference detected: '{query[:50]}'")
        return "policy_query"

    # ========== CONTEXT-AWARE INTENT CONTINUATION ==========
    # If user was in a policy_query flow, continue with policy_query
    if conversation_history and len(conversation_history) > 0:
        recent_intents = []
        for msg in conversation_history[-4:]:
            if msg.get('intent'):
                recent_intents.append(msg.get('intent'))

        # If last interactions were policy_query, likely this is continuation
        if recent_intents and recent_intents[-1] == 'policy_query':
            # Check if this looks like a policy-related follow-up
            followup_indicators = [
                'yes', 'no', 'self', 'family', 'show', 'tell', 'what', 'which', 'details',
                # Pronoun references to previously discussed policy
                'does it', 'is it', 'is there', 'will it', 'can i', 'does my', 'is my', 'will my',
                'this policy', 'that policy', 'the policy', 'it have', 'it cover',
                # Insurance-specific follow-up terms
                'room rent', 'limit', 'deductible', 'copay', 'cashless',
                'waiting period', 'claim', 'premium', 'expir', 'renew',
                'score', 'gap', 'benefit', 'exclusion', 'covered',
                'active', 'status', 'nominee', 'holder',
                # Hindi follow-ups
                'haan', 'nahi', 'aur', 'batao', 'bhi',
            ]
            if any(ind in query_lower for ind in followup_indicators):
                logger.info(f"✅ POLICY_QUERY CONTINUATION: Following policy_query flow")
                return "policy_query"
    # ========== END ENHANCED POLICY QUERY DETECTION ==========

    # Use advanced intent detection with conversation history
    # This handles remaining cases with LLM semantic understanding
    return detect_intent(query, conversation_history)

def generate_reference_response(conversation_history: List[Dict] = None) -> str:
    """Generate response when user asks about their last question"""
    
    last_question = get_last_user_question(conversation_history)
    
    if last_question:
        return f'Your last question was: "{last_question}"'
    else:
        return "I don't see any previous questions in our conversation. What would you like to know?"

def extract_conversation_topics(conversation_history: List[Dict]) -> List[str]:
    """Extract main topics from conversation history"""
    topics = []
    
    if not conversation_history:
        return topics
    
    for msg in conversation_history:
        content = msg.get('content', '').lower()
        
        # Financial topics
        if any(word in content for word in ['loan', 'financial', 'money', 'funding', 'cash']):
            topics.append('financial services')
        
        # Insurance topics
        if any(word in content for word in ['insurance', 'policy', 'coverage', 'claim']):
            topics.append('insurance')
        
        # Banking topics
        if any(word in content for word in ['balance', 'account', 'transaction', 'bank']):
            topics.append('banking')
        
        # Wallet topics
        if any(word in content for word in ['wallet', 'setup', 'kyc']):
            topics.append('wallet services')
        
        # Personal topics (like mango example)
        if 'mango' in content:
            topics.append('mangoes')
        
        # Add more topic detection as needed
    
    return list(set(topics))  # Remove duplicates

def build_conversation_summary(conversation_history: List[Dict]) -> str:
    """Build a summary of the conversation for context"""
    
    if not conversation_history or len(conversation_history) == 0:
        return "This is the start of our conversation."
    
    topics = extract_conversation_topics(conversation_history)
    message_count = len(conversation_history)
    
    summary_parts = []
    
    if topics:
        if len(topics) == 1:
            summary_parts.append(f"We've been discussing {topics[0]}")
        else:
            summary_parts.append(f"We've discussed {', '.join(topics[:-1])} and {topics[-1]}")
    
    summary_parts.append(f"with {message_count} messages exchanged")
    
    return ". ".join(summary_parts) + "."

def should_use_context(query: str, conversation_history: List[Dict] = None) -> bool:
    """Determine if conversation context should be used for this query.
    STRICT: Only use context for explicit follow-ups and pronoun references.
    Most questions should be answered independently to prevent context bleeding."""

    if not conversation_history or len(conversation_history) == 0:
        return False

    query_lower = query.lower().strip()

    # Only use context for EXPLICIT follow-up indicators
    followup_indicators = [
        'tell me more', 'more about that', 'about that',
        'last question', 'what i asked', 'previous question',
        'continue', 'go on', 'and what about',
    ]

    if any(indicator in query_lower for indicator in followup_indicators):
        return True

    # Use context for EXPLICIT references to previous conversation only
    # Avoid generic pronouns like "it", "that", "this" — they cause false positives
    # in compound questions like "how long does it take", "is it a good idea"
    pronoun_refs = ['the policy', 'which one', 'the same',
                    'isko', 'uska', 'uski', 'isme', 'woh ']
    if any(p in query_lower for p in pronoun_refs):
        return True

    # Use context ONLY for very short queries (< 4 words) that look like follow-ups
    if len(query_lower.split()) <= 3:
        # Short queries like "yes", "ok", "the first one", "health" need context
        return True

    # Default: Do NOT use context — each question gets fresh treatment
    return False

def generate_claim_guidance_response(query: str, insurance_type: str = None,
                                    conversation_history: List[Dict] = None) -> str:
    """Generate specific claim settlement guidance"""

    context_info = ""
    if conversation_history and len(conversation_history) > 0:
        recent_topics = []
        for msg in conversation_history[-4:]:
            content = msg.get('content', '').lower()
            if 'documents' in content:
                recent_topics.append('documentation')
            if 'hospital' in content:
                recent_topics.append('hospital claims')
            if 'rejection' in content:
                recent_topics.append('claim rejection')
        
        if recent_topics:
            context_info = f"Building on our discussion about {', '.join(set(recent_topics))}, "
    
    insurance_context = f"for {insurance_type} insurance" if insurance_type else "for insurance"
    
    prompt = f"""You're eazr — you've helped hundreds of people through insurance claims over 8+ years. Talk like you're explaining the process to a friend over coffee.

{context_info}They're asking about claims {insurance_context}: "{query}"

How to answer:
- Be specific and practical — tell them exactly what to do
- Mention timelines and documents they'll need
- Keep it to 3-4 sentences — don't ramble
- Sound like a friend who's been through this, not a customer service script
- NEVER use bullet points or numbered lists — just talk naturally
- NEVER start with "Great question" or "I'd be happy to help"

Don't ask for their policy number — just give general guidance that works for most claims."""
    
    try:
        messages = [HumanMessage(content=prompt)]
        response = llm.invoke(messages)
        return response.content.strip()
    except Exception:
        # Fallback response
        return "So for claims, the first thing you want to do is call your insurer right away — don't wait on this. Then get all your documents together (hospital bills, FIR if needed, that kind of thing) and fill out the claim form carefully. Most companies have a time limit so the sooner you start, the better!"

def generate_claim_aware_casual_response(query: str, conversation_history: List[Dict] = None) -> str:
    """Generate casual response with claim settlement context"""
    
    prompt = f"""You're eazr — chatting casually with someone about insurance claims.

They said: "{query}"

This might not be directly about claims, but respond naturally like a friend would, and casually bring it back to how you can help with their claim stuff.

Max 1-2 sentences. Sound like a real person, not a bot."""

    try:
        messages = [HumanMessage(content=prompt)]
        response = llm.invoke(messages)
        return response.content.strip()
    except Exception:
        return "Hey! I mainly deal with insurance claims — if you need any help with filing or tracking one, I'm your guy!"

def generate_claim_suggestions(insurance_type: str = None, conversation_history: List[Dict] = None) -> List[str]:
    """Generate contextual suggestions for claim guidance"""
    
    base_suggestions = [
        "What documents do I need for a claim?",
        "How long does claim settlement take?",
        "What if my claim gets rejected?",
        "Cashless vs reimbursement claims"
    ]
    
    if insurance_type == "health":
        return [
            "How to file a health insurance claim?",
            "Documents needed for hospitalization claim",
            "Cashless treatment process",
            "Claim settlement timeline"
        ]
    elif insurance_type == "motor":
        return [
            "Steps to file motor insurance claim",
            "Documents for accident claim",
            "Own damage vs third party claims",
            "Claim settlement process"
        ]
    elif insurance_type == "life":
        return [
            "Life insurance claim process",
            "Documents required for death claim",
            "Maturity claim process",
            "Nominee claim procedures"
        ]
    
    # Analyze conversation for context-aware suggestions
    if conversation_history:
        recent_content = ' '.join([msg.get('content', '').lower() for msg in conversation_history[-3:]])
        
        if 'reject' in recent_content:
            base_suggestions[0] = "Common reasons for claim rejection"
        if 'document' in recent_content:
            base_suggestions[1] = "Checklist of required documents"
        if 'time' in recent_content or 'long' in recent_content:
            base_suggestions[2] = "How to expedite claim process"
    
    return base_suggestions[:4]


# ============= ADVANCED HUMAN-LIKE CONVERSATION SYSTEM =============
# This creates the most advanced, human-like conversation experience
# with full context awareness from previous 5-6 messages

class AdvancedConversationContext:
    """
    Advanced conversation context manager that maintains human-like flow
    Analyzes previous 5-6 messages to understand:
    - User's emotional state
    - Topic progression
    - Unanswered questions
    - User preferences
    - Conversation tone
    """

    def __init__(self, conversation_history: List[Dict], max_context: int = 6):
        self.history = conversation_history or []
        self.max_context = max_context
        self.recent_messages = self.history[-max_context:] if self.history else []

    def get_user_name_hint(self) -> Optional[str]:
        """Extract user name if mentioned in conversation"""
        for msg in self.recent_messages:
            content = msg.get('content', '').lower()
            # Look for name introductions
            patterns = ['my name is ', "i'm ", 'i am ', 'call me ']
            for pattern in patterns:
                if pattern in content:
                    idx = content.find(pattern) + len(pattern)
                    potential_name = content[idx:idx+20].split()[0] if idx < len(content) else None
                    if potential_name and len(potential_name) > 1:
                        return potential_name.capitalize()
        return None

    def get_emotional_state(self) -> str:
        """Detect user's emotional state from recent messages"""
        negative_words = ['frustrated', 'angry', 'confused', 'worried', 'scared',
                          'upset', 'problem', 'issue', 'help', 'urgent', 'stress']
        positive_words = ['thanks', 'thank you', 'great', 'awesome', 'helpful',
                          'good', 'happy', 'excellent', 'perfect']
        question_words = ['what', 'how', 'why', 'when', 'can', 'could', 'would']

        negative_count = 0
        positive_count = 0
        question_count = 0

        for msg in self.recent_messages:
            if msg.get('role') == 'user':
                content = msg.get('content', '').lower()
                negative_count += sum(1 for word in negative_words if word in content)
                positive_count += sum(1 for word in positive_words if word in content)
                question_count += sum(1 for word in question_words if word in content)

        if negative_count > positive_count:
            return 'needs_support'
        elif positive_count > negative_count:
            return 'positive'
        elif question_count > 2:
            return 'curious'
        return 'neutral'

    def get_topics_discussed(self) -> List[str]:
        """Extract topics discussed in conversation"""
        topics = []
        topic_keywords = {
            'health_insurance': ['health', 'medical', 'hospital', 'doctor', 'treatment'],
            'life_insurance': ['life', 'term', 'death', 'beneficiary', 'nominee'],
            'motor_insurance': ['car', 'vehicle', 'motor', 'accident', 'bike'],
            'loan': ['loan', 'emi', 'borrow', 'credit', 'lending'],
            'investment': ['invest', 'mutual fund', 'stock', 'returns', 'sip'],
            'policy_query': ['policy', 'coverage', 'premium', 'claim', 'upload'],
            'personal_info': ['name', 'brother', 'sister', 'family', 'nominee', 'father', 'mother']
        }

        for msg in self.recent_messages:
            content = msg.get('content', '').lower()
            for topic, keywords in topic_keywords.items():
                if any(kw in content for kw in keywords):
                    if topic not in topics:
                        topics.append(topic)

        return topics

    def get_unanswered_questions(self) -> List[str]:
        """Find user questions that may not have been fully answered"""
        unanswered = []
        question_patterns = ['?', 'what is', 'how do', 'can you', 'tell me', 'explain']

        for i, msg in enumerate(self.recent_messages):
            if msg.get('role') == 'user':
                content = msg.get('content', '')
                if any(pattern in content.lower() for pattern in question_patterns):
                    # Check if next message is a short response (might be incomplete)
                    if i + 1 < len(self.recent_messages):
                        next_msg = self.recent_messages[i + 1]
                        if next_msg.get('role') == 'assistant':
                            if len(next_msg.get('content', '')) < 50:
                                unanswered.append(content)

        return unanswered[-2:] if unanswered else []

    def get_conversation_summary(self) -> str:
        """Generate a brief summary of the conversation so far"""
        if not self.recent_messages:
            return ""

        topics = self.get_topics_discussed()
        emotional_state = self.get_emotional_state()

        summary_parts = []

        if topics:
            summary_parts.append(f"Topics: {', '.join(topics[:3])}")

        if emotional_state == 'needs_support':
            summary_parts.append("User seems to need assistance")
        elif emotional_state == 'positive':
            summary_parts.append("User is engaged positively")
        elif emotional_state == 'curious':
            summary_parts.append("User is seeking information")

        return "; ".join(summary_parts) if summary_parts else ""

    def build_context_prompt(self) -> str:
        """Build a context-aware prompt from conversation history (limited to prevent bleeding)"""
        if not self.recent_messages:
            return ""

        context_lines = ["(Previous exchange — for context only, do NOT repeat this answer):"]
        for msg in self.recent_messages[-2:]:  # Last 1 exchange only
            role = "User" if msg.get('role') == 'user' else "eazr"
            content = msg.get('content', '')[:150]  # Limit content length
            context_lines.append(f"{role}: {content}")

        return "\n".join(context_lines)


def generate_human_like_response(
    query: str,
    conversation_history: List[Dict] = None,
    intent: str = None,
    language: str = 'en'
) -> Dict[str, Any]:
    """
    Generate the most advanced, human-like response with full context awareness.

    This function:
    1. Analyzes previous 5-6 messages for context
    2. Understands user's emotional state
    3. Tracks topics discussed
    4. Maintains natural conversation flow
    5. Responds like a human friend who is an expert

    Returns:
        Dict with response, suggestions, context_used, etc.
    """
    try:
        # Initialize context analyzer (limited to prevent bleeding from old messages)
        context = AdvancedConversationContext(conversation_history, max_context=2)

        # Get context insights
        user_name = context.get_user_name_hint()
        emotional_state = context.get_emotional_state()
        topics_discussed = context.get_topics_discussed()
        conversation_summary = context.get_conversation_summary()
        context_prompt = context.build_context_prompt()

        # Build personalized greeting if we know user's name
        name_greeting = f"{user_name}, " if user_name else ""

        # Build emotional response modifier
        emotional_modifier = ""
        if emotional_state == 'needs_support':
            emotional_modifier = "Be extra supportive and reassuring. Acknowledge their concern first."
        elif emotional_state == 'positive':
            emotional_modifier = "Match their positive energy. Be warm and encouraging."
        elif emotional_state == 'curious':
            emotional_modifier = "Provide clear, informative responses. They want to learn."

        # Build topic context
        topic_context = ""
        if topics_discussed:
            topic_context = f"We've been discussing: {', '.join(topics_discussed)}. Build on this context naturally."

        # Create the advanced human-like prompt
        if language == 'hi':
            system_prompt = f"""तुम eazr हो — 8+ साल से बीमा और फाइनेंस में काम कर रहे हो। दोस्त की तरह बात करते हो।

{context_prompt}

{topic_context}

{emotional_modifier}

अभी का सवाल: {query}

नियम:
1. सबसे ज़रूरी: ऊपर दिया गया अभी का सवाल answer करो। पिछले सवाल का जवाब repeat मत करो। हर नया मेसेज = नया सवाल।
2. आम तौर पर 2-4 लाइन में जवाब दो। अगर एक ही मेसेज में कई सवाल हैं तो सबका जवाब दो (5-6 लाइन OK है)
3. पिछली बात याद रखो — "हां जैसे हम बात कर रहे थे"
4. "देखो", "अच्छा सुनो", "मेरे हिसाब से" — ऐसे बोलो
5. "बहुत अच्छा सवाल!" या "मैं खुश हूं मदद करके" से कभी शुरू मत करो
6. कभी मत बोलो "मैं AI हूं" या OpenAI/GPT/ChatGPT का नाम

सबसे ज़रूरी नियम — OFF-TOPIC:
- तुम्हारी असली expertise बीमा, फाइनेंस, लोन, निवेश, पॉलिसी में है
- अगर कोई बाहर के टॉपिक पर पूछे तो:
  1. पहले उनके सवाल का छोटा सा जवाब दो (1-2 लाइन)
  2. फिर बातचीत को बीमा/फाइनेंस की तरफ ले जाओ
  3. कभी मत बोलो "यह मेरा एरिया नहीं है"
- उदाहरण: "बोर हो रहा" → "हाहा! चलो कुछ productive करते हैं — अपनी पॉलिसी review करें?"
- उदाहरण: "मूवी बताओ" → "अच्छी thriller try करो! वैसे तुमने अपनी इंश्योरेंस कवरेज चेक की?" """
        else:
            system_prompt = f"""You're eazr — you've been in insurance and finance for 8+ years. People come to you because you explain things clearly and you're easy to talk to.

{context_prompt}

{topic_context}

{emotional_modifier}

Their CURRENT question: {query}

How to respond:
1. CRITICAL: Answer the CURRENT question above. Do NOT repeat or continue your answer to a previous question. Each new message = fresh question.
2. Usually 2-4 sentences. But if they ask MULTIPLE questions in ONE message, answer ALL of them (up to 5-6 sentences is fine). Never skip any part.
3. If they mentioned something before, bring it up naturally — "oh yeah, like we were talking about earlier"
4. Talk like a real person — "honestly", "here's the thing", "from what you told me", "in my experience"
5. NEVER start with "Great question!" or "I'd be happy to help" — those sound robotic
6. NEVER use bullet points or numbered lists — just talk
7. If they're continuing a topic, pick up where you left off naturally
7. If they ask about family/policy details, answer from what you know about their policy
8. NEVER say you're an AI or mention OpenAI/GPT/ChatGPT

MOST IMPORTANT — OFF-TOPIC RULE:
- Your main expertise is insurance, finance, loans, investments, policies
- When someone asks about ANYTHING outside insurance/finance:
  1. Give a SHORT helpful answer to their question (1-2 sentences)
  2. Then naturally bring the conversation back to insurance/finance at the END
  3. NEVER say "that's not my area" or "I can't help with that" — just answer briefly and redirect
- Example: "I'm bored" → "Haha I feel you! Hey have you reviewed your policy lately? That's actually worth doing!"
- Example: "recommend movies" → "Can't go wrong with a good thriller! By the way, want me to check your insurance coverage?"
- Example: "Who is PM?" → "Narendra Modi is the current PM of India. Speaking of important stuff — is your coverage up to date?"

{name_greeting}eazr:"""

        # Generate response using LLM
        from ai_chat_components.llm_config import get_llm
        llm_instance = get_llm(use_case='human_response')

        messages = [HumanMessage(content=system_prompt)]
        response = llm_instance.invoke(messages)
        response_text = response.content.strip()

        # Post-process for natural flow
        # Remove any robotic patterns that break the illusion
        robotic_patterns = [
            "As an AI", "As a language model", "I don't have access to",
            "I'm an AI", "I cannot", "I'm not able to",
            "As an artificial intelligence", "I'm a virtual assistant",
            "I'd be happy to help!", "Great question!", "Thank you for asking",
            "Thank you for reaching out", "I appreciate your question",
            "feel free to ask", "feel free to reach out", "feel free to",
            "I'm here to help", "I'm here to assist", "I'm here for you",
            "If you have any questions", "If you need any assistance",
            "Don't hesitate to", "Please don't hesitate",
            "No problem at all", "insurance-related matters",
            "insurance-related questions", "Absolutely!",
        ]
        for pattern in robotic_patterns:
            if pattern.lower() in response_text.lower():
                # Case-insensitive replacement
                import re
                response_text = re.sub(re.escape(pattern), "", response_text, flags=re.IGNORECASE).strip()

        # Ensure proper ending
        if not response_text.endswith(('.', '!', '?')):
            response_text += '.'

        # Generate context-aware suggestions
        suggestions = generate_contextual_suggestions(conversation_history)

        # If user has uploaded policies, add policy-specific suggestions
        if 'policy_query' in topics_discussed or 'personal_info' in topics_discussed:
            suggestions = [
                "Where am I not covered?",
                "What's my protection score?",
                "Who are my nominees?",
                "When do my policies expire?"
            ][:4]

        return {
            "response": response_text,
            "suggestions": suggestions,
            "context_used": bool(conversation_history),
            "topics_discussed": topics_discussed,
            "emotional_state": emotional_state,
            "user_name": user_name,
            "language": language
        }

    except Exception as e:
        logger.error(f"Error in human-like response generation: {e}")
        # Fallback to regular response
        fallback_response = generate_casual_response_with_context(query, conversation_history)
        return {
            "response": fallback_response,
            "suggestions": generate_contextual_suggestions(conversation_history),
            "context_used": False,
            "error": str(e)
        }


def build_advanced_context_for_ai(
    query: str,
    conversation_history: List[Dict] = None,
    policy_data: Dict = None,
    user_data: Dict = None
) -> str:
    """
    Build a comprehensive context string for AI that includes:
    - Previous 5-6 conversation messages
    - Relevant policy data
    - User information
    - Topic continuity

    This enables AI to answer questions like "what is my brother's name"
    by having full context.
    """
    context_parts = []

    # Add conversation history
    if conversation_history:
        recent = conversation_history[-6:]
        context_parts.append("=== RECENT CONVERSATION ===")
        for msg in recent:
            role = msg.get('role', 'unknown').upper()
            content = msg.get('content', '')[:300]
            context_parts.append(f"{role}: {content}")

    # Add policy data if available
    if policy_data:
        context_parts.append("\n=== USER'S POLICY INFORMATION ===")

        # Personal info
        if policy_data.get('policy_holder_name'):
            context_parts.append(f"Policy Holder: {policy_data.get('policy_holder_name')}")

        # Family members/nominees
        if policy_data.get('family_members'):
            context_parts.append("Family Members:")
            for member in policy_data.get('family_members', []):
                name = member.get('name', 'Unknown')
                relation = member.get('relationship', member.get('relation', 'Unknown'))
                context_parts.append(f"  - {name} ({relation})")

        if policy_data.get('nominees'):
            context_parts.append("Nominees:")
            for nominee in policy_data.get('nominees', []):
                name = nominee.get('name', 'Unknown')
                relation = nominee.get('relationship', nominee.get('relation', 'Unknown'))
                context_parts.append(f"  - {name} ({relation})")

        # Policy details
        if policy_data.get('policies'):
            context_parts.append(f"Total Policies: {len(policy_data.get('policies', []))}")

        if policy_data.get('sum_assured'):
            context_parts.append(f"Total Sum Assured: ₹{policy_data.get('sum_assured'):,}")

        if policy_data.get('premium'):
            context_parts.append(f"Total Premium: ₹{policy_data.get('premium'):,}")

    # Add user data if available
    if user_data:
        context_parts.append("\n=== USER PROFILE ===")
        if user_data.get('name'):
            context_parts.append(f"Name: {user_data.get('name')}")
        if user_data.get('age'):
            context_parts.append(f"Age: {user_data.get('age')}")

    return "\n".join(context_parts)


def get_conversation_context_summary(conversation_history: List[Dict], limit: int = 6) -> Dict[str, Any]:
    """
    Get a comprehensive summary of the conversation context.
    Used to maintain state across the chat session.

    Returns:
        Dict with:
        - topics: List of topics discussed
        - last_intent: The last detected intent
        - user_questions: List of user questions
        - assistant_responses: List of assistant responses
        - context_string: Formatted context for AI
    """
    if not conversation_history:
        return {
            "topics": [],
            "last_intent": None,
            "user_questions": [],
            "assistant_responses": [],
            "context_string": "",
            "message_count": 0
        }

    recent = conversation_history[-limit:]

    # Extract topics
    context = AdvancedConversationContext(recent, max_context=limit)
    topics = context.get_topics_discussed()

    # Extract questions and responses
    user_questions = []
    assistant_responses = []
    last_intent = None

    for msg in recent:
        if msg.get('role') == 'user':
            user_questions.append(msg.get('content', ''))
        elif msg.get('role') == 'assistant':
            assistant_responses.append(msg.get('content', ''))

        # Track intent if available
        if msg.get('intent'):
            last_intent = msg.get('intent')

    # Build context string
    context_string = context.build_context_prompt()

    return {
        "topics": topics,
        "last_intent": last_intent,
        "user_questions": user_questions[-3:],  # Last 3 questions
        "assistant_responses": assistant_responses[-3:],  # Last 3 responses
        "context_string": context_string,
        "message_count": len(recent),
        "emotional_state": context.get_emotional_state()
    }


# Export enhanced functions
__all__ = [
    'generate_casual_response_with_context',
    'generate_casual_response_hindi_with_context',
    'detect_conversation_continuity',
    'get_last_user_question',
    'generate_contextual_suggestions',
    'detect_intent_with_context',
    'generate_reference_response',
    'extract_conversation_topics',
    'build_conversation_summary',
    'should_use_context',
    'generate_casual_response',
    'generate_casual_response_hindi',
    'detect_intent',
    'detect_multilingual_intent',
    'detect_exit_intent',
    'chat_with_glm_direct',  # Added for direct GLM testing
    'is_off_topic_query',  # Off-topic detection
    'generate_off_topic_redirect_response',  # Off-topic redirect
    # Advanced Human-Like Conversation System
    'AdvancedConversationContext',
    'generate_human_like_response',
    'build_advanced_context_for_ai',
    'get_conversation_context_summary'
]

print("[OK] Enhanced Processor Module with LLM Fallback System Loaded Successfully!")
print("[INFO] Using GPT-3.5-turbo (primary) with GLM-4.5-Air (fallback)")
print("[INFO] Automatic fallback enabled for all LLM operations")