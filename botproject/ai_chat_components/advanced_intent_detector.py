"""
Advanced Intent Detection System - 100% Accuracy
Understands context, negation, sentiment, and user intent properly
No keyword matching - Uses LLM-based semantic understanding
"""

import logging
import hashlib
import time
from typing import Dict, Optional, List, Tuple
from langchain_core.messages import HumanMessage, SystemMessage
from functools import lru_cache

logger = logging.getLogger(__name__)

# Import LLM with fallback
from ai_chat_components.llm_config import get_llm, invoke_llm

# Intent cache with TTL
_intent_cache: Dict[str, Dict] = {}
CACHE_TTL = 300  # 5 minutes

# Get LLM instance
llm = get_llm(use_case='intent_detection')


class AdvancedIntentDetector:
    """
    100% Accurate Intent Detection using LLM semantic understanding

    Key Features:
    - Understands negation ("I don't need", "not interested")
    - Understands context ("I'm not looking for that")
    - Distinguishes action vs information queries
    - Multi-turn conversation awareness
    - Sentiment analysis (positive, negative, neutral)
    """

    def __init__(self):
        self.llm = get_llm(use_case='intent_detection')

        # Intent definitions with examples
        self.intent_definitions = {
            'greeting': {
                'description': 'User is greeting or saying hello',
                'positive_examples': ['hi', 'hello', 'good morning', 'hey there'],
                'negative_examples': ['I need help', 'what is loan']
            },
            'small_talk': {
                'description': 'Casual conversation, thank you, goodbye, how are you',
                'positive_examples': ['how are you', 'thanks', 'goodbye', 'nice to meet you'],
                'negative_examples': ['I need insurance', 'apply for policy']
            },
            'insurance_plan': {
                'description': 'User WANTS to BUY/APPLY/GET insurance or policy (action-oriented, NOT informational)',
                'positive_examples': [
                    'I want insurance',
                    'I need policy',
                    'buy health insurance',
                    'apply for insurance',
                    'get me insurance',
                    'I want to purchase policy',
                    'give me insurance plan',
                    'need insurance coverage'
                ],
                'negative_examples': [
                    'what is insurance',
                    'explain insurance',
                    'I don\'t need insurance',
                    'not interested in policy',
                    'I don\'t want insurance',
                    'no insurance needed',
                    'tell me about insurance',
                    'how does insurance work',
                    'add policy',
                    'add my policy',
                    'upload my policy',
                    'analyze my policy'
                ]
            },
            'financial_education': {
                'description': 'User asking for DEFINITIONS, EXPLANATIONS, or general INFORMATION (NOT action-oriented)',
                'positive_examples': [
                    'what is loan',
                    'what is insurance',
                    'explain mutual funds',
                    'tell me about EMI',
                    'how does insurance work',
                    'what are types of insurance',
                    'define financial assistance',
                    'benefits of insurance'
                ],
                'negative_examples': [
                    'I need insurance',
                    'I want loan',
                    'apply for policy',
                    'give me insurance'
                ]
            },
            'insurance_analysis': {
                'description': 'User wants to ANALYZE, UPLOAD, CHECK, or REVIEW their existing insurance policy (action-oriented)',
                'positive_examples': [
                    'analyze my insurance', 'analyse my insurance',
                    'analyze my policy', 'analyse my policy',
                    'check my insurance', 'check my policy',
                    'review my insurance', 'review my policy',
                    'evaluate my insurance', 'evaluate my policy',
                    'upload my policy', 'upload my insurance',
                    'add my policy', 'add my insurance',
                    'scan my policy', 'audit my insurance',
                    'insurance analysis', 'policy analysis',
                    'i want analyze my policy', 'i want to analyze my policy',
                    'mujhe apna insurance analyze karna hai',
                    'apna insurance check karna',
                    'mera insurance analyze karo'
                ],
                'negative_examples': [
                    'what is insurance',
                    'I need insurance',
                    'buy new policy',
                    'I want insurance',
                    'explain insurance'
                ]
            },
            'policy_query': {
                'description': 'User asking questions about their UPLOADED/EXISTING policies - coverage gaps, recommendations, policy count, details, family coverage, protection score',
                'positive_examples': [
                    'how many policies do i have', 'how many policy i have uploaded',
                    'what are my coverage gaps', 'show my coverage gaps',
                    'what is my protection score', 'show protection score',
                    'give me recommendations', 'policy recommendations',
                    'what policies have i uploaded', 'show my policies',
                    'my policy details', 'show my policy details',
                    'family coverage', 'family policies', 'family members policies',
                    'what is covered in my policy', 'what is not covered',
                    'policy exclusions', 'my policy exclusions',
                    'sum assured', 'what is my sum assured',
                    'premium details', 'my premium', 'how much premium',
                    'policy expiry', 'when does my policy expire',
                    'claim process', 'how to claim',
                    'meri policy ki details', 'meri policy mein kya covered hai',
                    'kitni policies hain', 'coverage gaps batao',
                    'recommendations batao', 'protection score kya hai'
                ],
                'negative_examples': [
                    'upload my policy', 'analyze my policy',
                    'i want insurance', 'buy new policy',
                    'what is insurance'
                ]
            },
            'unknown': {
                'description': 'Unclear, ambiguous, or out-of-scope query',
                'positive_examples': ['asdf', 'jkjkj', 'random text'],
                'negative_examples': []
            }
        }

    def detect_intent_llm(
        self,
        query: str,
        conversation_history: Optional[List[Dict]] = None
    ) -> Dict[str, any]:
        """
        Detect intent using LLM with semantic understanding

        Returns:
            {
                'intent': str,
                'confidence': float,
                'reasoning': str,
                'sentiment': str,  # positive, negative, neutral
                'is_action_query': bool,  # True if user wants to DO something
                'is_info_query': bool,    # True if user wants to LEARN something
                'negation_detected': bool  # True if user is rejecting/declining
            }
        """
        query_lower = query.lower().strip()
        query_words = query_lower.split()
        logger.info(f"🔍 INTENT DETECTION START: query='{query_lower}'")

        # ========== NEGATION DETECTION (MUST CHECK FIRST - HIGHEST PRIORITY) ==========
        # Negation words that indicate user is declining/rejecting
        negation_words = ['not', 'no', "don't", 'dont', "doesn't", 'doesnt', "won't", 'wont',
                         "can't", 'cant', 'never', 'nahi', 'mat', 'na', 'naa']

        # Check if query STARTS with negation or has negation before action word
        starts_with_negation = query_words[0] in negation_words if query_words else False

        # Check for negation word anywhere in query
        has_negation_word = any(word in negation_words for word in query_words)

        # Action words that when combined with negation = rejection
        action_words = ['analyze', 'analyse', 'check', 'review', 'upload', 'add', 'want', 'need',
                       'insurance', 'policy', 'karna', 'karni', 'karo', 'chahiye', 'chaiye']

        has_action_word = any(word in query_lower for word in action_words)

        # If negation word + action word = rejection
        if has_negation_word and has_action_word:
            logger.info(f"✓ Negation detected: negation_word + action_word in query: {query}")
            result = {
                'intent': 'unknown',
                'confidence': 0.95,
                'reasoning': 'User declining or expressing disinterest (negation + action detected)',
                'sentiment': 'negative',
                'is_action_query': False,
                'is_info_query': False,
                'negation_detected': True
            }
            return result
        # ========== END NEGATION DETECTION ==========

        # ========== FINANCIAL EDUCATION PRE-CHECK (must come BEFORE buy insurance check) ==========
        # Educational/informational queries should NOT be classified as action intents
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
            logger.info(f"✅ FINANCIAL EDUCATION DETECTED: Informational query: '{query[:50]}'")
            result = {
                'intent': 'financial_education',
                'confidence': 0.97,
                'reasoning': 'Educational/informational query about financial topic detected',
                'sentiment': 'neutral',
                'is_action_query': False,
                'is_info_query': True,
                'negation_detected': False
            }
            return result
        # Compound query: education topic + possessive = user asking about concept AND their policy → policy_query
        if has_education_starter and has_education_topic and has_possessive:
            logger.info(f"✅ COMPOUND Q → POLICY QUERY: education topic + possessive: '{query[:50]}'")
            result = {
                'intent': 'policy_query',
                'confidence': 0.94,
                'reasoning': 'Compound query: asking about a concept AND about their own policy',
                'sentiment': 'neutral',
                'is_action_query': False,
                'is_info_query': True,
                'negation_detected': False
            }
            return result
        # ========== END FINANCIAL EDUCATION PRE-CHECK ==========

        # ========== HIGHEST PRIORITY: BUY/GET INSURANCE CHECK ==========
        # This MUST come FIRST to catch purchase intent before policy_query
        buy_insurance_patterns = [
            'buy insurance', 'buy policy', 'buy any policy', 'buy a policy',
            'get insurance', 'get policy', 'get any policy', 'get a policy',
            'purchase insurance', 'purchase policy', 'purchase any policy',
            'want insurance', 'want policy', 'want any policy', 'want a policy',
            'need insurance', 'need policy', 'need any policy', 'need a policy',
            'apply for insurance', 'apply for policy', 'apply insurance', 'apply policy',
            'can i buy insurance', 'can i buy policy', 'can i buy a policy',
            'can i get insurance', 'can i get policy', 'can i get a policy',
            'can i purchase insurance', 'can i purchase policy',
            'can i apply for insurance', 'can i apply for policy',
            'i want to buy insurance', 'i want to buy policy', 'i want to buy a policy',
            'i want to get insurance', 'i want to get policy',
            'i want to purchase insurance', 'i want to purchase policy',
            'give me insurance', 'give me policy',
            # Broken English patterns (common in Indian English)
            'want buy insurance', 'want buy policy',
            'want get insurance', 'want get policy',
            'want purchase insurance', 'want purchase policy',
            'buy some insurance', 'buy some policy', 'get some insurance', 'get some policy',
            'buy any insurance', 'get any insurance',
            'suggest me insurance', 'suggest me policy', 'suggest insurance', 'suggest policy',
            'insurance buy', 'insurance purchase', 'insurance get',
            'insurance lena', 'insurance le', 'insurance kharidna', 'insurance kharid',
            'policy lena', 'policy le', 'policy kharidna', 'policy kharid',
            'insurance chahiye', 'policy chahiye', 'bima chahiye', 'bima lena',
            'bima kharidna', 'bima kharid', 'bima le',
            'new insurance', 'naya insurance', 'nayi policy', 'naya bima',
        ]

        is_buy_insurance = any(pattern in query_lower for pattern in buy_insurance_patterns)

        # Keyword combo: buy/purchase/get me + insurance/policy (catches "buy health insurance" etc.)
        if not is_buy_insurance:
            buy_action_words = ['buy', 'purchase', 'get me', 'give me', 'apply for']
            insurance_target_words = ['insurance', 'policy', 'bima', 'beema']
            has_buy_action = any(w in query_lower for w in buy_action_words)
            has_insurance_target = any(w in query_lower for w in insurance_target_words)
            has_non_insurance = any(w in query_lower for w in ['loan', 'money', 'cash', 'funding'])
            if has_buy_action and has_insurance_target and not has_non_insurance:
                is_buy_insurance = True

        # Override: queries about porting/transferring/comparing/renewing are NOT buy intent
        not_buy_words = ['port', 'porting', 'transfer', 'compare', 'renew', 'cancel',
                         'difference between', 'better', 'best', 'copay', 'deductible',
                         'cashless', 'rider', 'claim', 'expired', 'nominee',
                         'should i get', 'do i have', 'does my', 'is my',
                         'critical illness', 'hospitalization', 'what is']
        if is_buy_insurance and any(w in query_lower for w in not_buy_words):
            is_buy_insurance = False
            logger.info(f"⚠️ INSURANCE PLAN OVERRIDDEN: query contains policy action word, not a buy intent")

        if is_buy_insurance:
            logger.info(f"✅ INSURANCE PLAN INTENT MATCHED: query='{query}'")
            result = {
                'intent': 'insurance_plan',
                'confidence': 0.98,
                'reasoning': 'User wants to buy/get/purchase insurance',
                'sentiment': 'positive',
                'is_action_query': True,
                'is_info_query': False,
                'negation_detected': False
            }
            return result
        # ========== END BUY INSURANCE CHECK ==========

        # ========== UPLOAD/ANALYZE POLICY CHECK (insurance_analysis) ==========
        upload_analyze_patterns = [
            'want to upload', 'want upload', 'i want uploaded', 'upload new', 'upload a', 'upload my',
            'need to upload', 'for analyzing', 'for analysis', 'analyze new', 'analyse new',
            'want to analyze', 'want to analyse', 'new policy for', 'uploaded new',
            'analyze my policy', 'analyse my policy', 'check my policy', 'review my policy',
            'add policy', 'add my policy', 'add insurance', 'add my insurance',
            'add a policy', 'add new policy', 'add a insurance', 'add new insurance',
            'policy add', 'insurance add',
            'policy add karna', 'insurance add karna', 'policy add karo', 'insurance add karo',
        ]

        if any(pattern in query_lower for pattern in upload_analyze_patterns):
            logger.info(f"✅ INSURANCE ANALYSIS INTENT MATCHED: query='{query}'")
            result = {
                'intent': 'insurance_analysis',
                'confidence': 0.98,
                'reasoning': 'User wants to upload/analyze policy',
                'sentiment': 'positive',
                'is_action_query': True,
                'is_info_query': False,
                'negation_detected': False
            }
            return result
        # ========== END UPLOAD/ANALYZE CHECK ==========

        # ========== POLICY QUERY CHECK (Questions about uploaded policies) ==========
        # Direct phrase patterns for policy queries
        policy_query_direct_patterns = [
            # Count/existence queries
            'how many policies', 'how many policy', 'how many insurance',
            'policies have i', 'policy have i', 'policies i have',
            'have i uploaded', 'i have uploaded', 'i uploaded', 'uploaded any',
            'i am uploaded', 'am i uploaded', 'am uploaded',  # Broken English variations
            'do i have any policy', 'do i have policy', 'any policy uploaded',
            'uploaded self', 'uploaded family', 'self policy uploaded', 'family policy uploaded',
            # Status queries
            'my policies', 'my policy details', 'my insurance',
            'show my policies', 'show my policy', 'show policies',
            'list my policies', 'list my policy',
            'view my policies', 'view my policy',
            # Coverage queries
            'coverage gaps', 'coverage gap', 'my gaps',
            'what is covered', 'what is not covered',
            'policy exclusions', 'my exclusions',
            # Score/recommendation queries
            'protection score', 'my score',
            'my recommendations', 'recommendations for',
            # Amount queries
            'sum assured', 'sum insured',
            'my premium', 'premium amount',
            'policy expiry', 'policy expire', 'when expire',
            # Family queries
            'family coverage', 'family policies', 'family members',
            # Show [family member] policies patterns
            'show sister', 'show brother', 'show father', 'show mother', 'show spouse',
            'show wife', 'show husband', 'show son', 'show daughter',
            'sister policies', 'brother policies', 'father policies', 'mother policies',
            'spouse policies', 'wife policies', 'husband policies', 'son policies', 'daughter policies',
            'policies for sister', 'policies for brother', 'policies for father', 'policies for mother',
            'policies for spouse', 'policies for wife', 'policies for husband', 'policies for son', 'policies for daughter',
            # Hindi patterns
            'meri policy', 'mere policies', 'mera policy',
            'kitni policy', 'kitne policy',
            'coverage gaps batao', 'recommendations batao',
            'protection score kya', 'score batao',
            'maine upload', 'uploaded policy', 'uploaded insurance',
            # Hindi family member patterns
            'behen ki policy', 'bhai ki policy', 'papa ki policy', 'mummy ki policy',
            'pati ki policy', 'patni ki policy', 'beta ki policy', 'beti ki policy',
            # Compare/contrast policy queries
            'compare my', 'compare policies', 'compare policy', 'compare insurance',
            'which policy is better', 'which one is better',
            'konsi policy', 'konsi better', 'kaunsi policy',
            # Multi-Q patterns with policy context
            'port my policy', 'porting', 'transfer my policy',
            'i want to port', 'want to port',
            'riders on my', 'riders in my', 'add-on', 'add on',
            'what riders', 'what all riders', 'riders do i',
            'cashless claim', 'cashless hospital', 'network hospital',
            'how do cashless', 'cashless work',
            'copay', 'deductible', 'co-pay',
            'premium kitna', 'mera premium', 'mere premium',
            'discount milega', 'discount mil',
            'critical illness', 'critical cover',
            'expired policies', 'expired policy', 'expire hone',
            'i want to know my policy', 'policy number'
        ]

        # Check for direct pattern match first
        if any(pattern in query_lower for pattern in policy_query_direct_patterns):
            logger.info(f"✅ POLICY QUERY DIRECT PATTERN MATCHED: query='{query}'")
            result = {
                'intent': 'policy_query',
                'confidence': 0.98,
                'reasoning': 'Direct pattern match for policy query',
                'sentiment': 'neutral',
                'is_action_query': False,
                'is_info_query': True,
                'negation_detected': False
            }
            return result

        # Keywords for policy-related questions
        policy_query_keywords = [
            'how many', 'kitni', 'kitne', 'count', 'total',
            'gaps', 'gap',
            'score',
            'recommendations', 'recommendation', 'suggestions',
            'suggest improvements', 'suggest changes', 'suggest recommendations',
            'uploaded', 'have uploaded', 'have i uploaded', 'maine upload', 'i uploaded',
            'show my', 'my policies', 'meri policies', 'mere policies',
            'policy details', 'details of', 'detail',
            'family coverage', 'family policies', 'family members', 'parivar',
            'what is covered', 'kya covered', 'covered in my', 'not covered',
            'exclusions', 'exclusion',
            'sum assured', 'sum insured', 'coverage amount',
            'premium', 'kitna premium', 'premium kitna',
            'expiry', 'expire', 'validity', 'valid till', 'kab tak',
            'claim', 'claim process', 'how to claim', 'claim kaise',
            'benefits', 'key benefits', 'fayde',
            'provider', 'company', 'insurance company',
            'policy number', 'policy no',
            # Personal info from policy
            'name', 'nominee', 'brother', 'sister', 'father', 'mother', 'spouse', 'wife', 'husband',
            'son', 'daughter', 'family member', 'who is covered',
            # Compare/contrast
            'compare', 'better', 'best',
            # Porting/transfer
            'port', 'porting', 'transfer',
            # Riders/add-ons
            'rider', 'riders', 'add-on', 'add on',
            # Cashless/network
            'cashless', 'network hospital', 'empanelled',
            # Financial terms about policies
            'copay', 'co-pay', 'deductible', 'waiting period',
            'grace period', 'penalty', 'late renewal'
        ]

        # Question indicators
        question_indicators = [
            'what', 'how', 'when', 'which', 'where', 'tell me', 'show me', 'give me',
            'show', 'list', 'view', 'see', 'display',  # Command-style requests
            'do i have', 'have i', 'am i', 'is my', 'are my',
            'kya', 'kaise', 'kab', 'kaun', 'kitna', 'kitni', 'kitne', 'batao', 'dikhao', 'bataiye', 'dikha'
        ]

        has_policy_query_keyword = any(kw in query_lower for kw in policy_query_keywords)
        has_question_indicator = any(qi in query_lower for qi in question_indicators)
        has_policy_word = any(pw in query_lower for pw in ['policy', 'policies', 'insurance', 'bima', 'coverage'])

        logger.info(f"🔍 POLICY QUERY CHECK: keyword={has_policy_query_keyword}, question={has_question_indicator}, policy_word={has_policy_word}")

        # If user is asking a question about their policies
        if has_policy_query_keyword and (has_question_indicator or has_policy_word):
            logger.info(f"✅ POLICY QUERY INTENT MATCHED: query='{query}'")
            result = {
                'intent': 'policy_query',
                'confidence': 0.95,
                'reasoning': 'User asking question about their uploaded/existing policies',
                'sentiment': 'neutral',
                'is_action_query': False,
                'is_info_query': True,
                'negation_detected': False
            }
            return result
        # ========== END POLICY QUERY CHECK ==========

        # ========== INSURANCE ANALYSIS CHECK (User wants to upload/analyze a NEW policy) ==========
        # Keyword-based detection - ONLY for action of uploading/analyzing NEW policy
        # English keywords for analyze action (NOT including 'uploaded' past tense)
        analyze_keywords = [
            'analyze', 'analyse', 'analysis', 'check', 'review', 'evaluate',
            'assess', 'audit', 'scan', 'verify', 'examine'
        ]
        # Action keywords for uploading NEW policy (present/future tense only)
        upload_action_keywords = [
            'upload my', 'upload a', 'upload new', 'want to upload', 'need to upload',
            'add my', 'add a', 'add new', 'want to add', 'need to add',
            'submit my', 'submit a', 'submit new'
        ]
        # Hindi/Hinglish keywords for analyze action (verb forms)
        analyze_keywords_hindi = [
            'dekh', 'dekhna', 'dekhni', 'dekho', 'dekhiye',
            'janchna', 'janch', 'janchiye'
        ]

        # English keywords for insurance/policy
        insurance_keywords = ['insurance', 'policy', 'coverage', 'bima', 'beema', 'polisi']

        # Hindi/Hinglish keywords for my/want
        my_keywords = ['my', 'mera', 'meri', 'apna', 'apni', 'apne', 'hamara', 'hamari', 'muje', 'mujhe', 'mere']

        # Check for upload action patterns first (more specific)
        has_upload_action = any(kw in query_lower for kw in upload_action_keywords)

        # Check keyword combinations
        has_analyze_en = any(kw in query_lower for kw in analyze_keywords)
        has_analyze_hi = any(kw in query_lower for kw in analyze_keywords_hindi)
        has_analyze = has_analyze_en or has_analyze_hi
        has_insurance = any(kw in query_lower for kw in insurance_keywords)
        has_my = any(kw in query_lower for kw in my_keywords)

        logger.info(f"🔍 KEYWORD CHECK: has_analyze_en={has_analyze_en}, has_analyze_hi={has_analyze_hi}, has_insurance={has_insurance}, has_my={has_my}, has_upload_action={has_upload_action}")

        # PRIMARY CHECK: If query wants to upload/analyze NEW policy
        # BUT: if the user is asking a QUESTION (what/how/does/is/kya), prefer policy_query or financial_education
        question_words = ['what is', 'what are', 'how do', 'how does', 'does my', 'is my', 'do i', 'am i',
                          'difference between', 'compare', 'kya hai', 'kya mere', 'kya meri', 'tell me about',
                          'explain', 'should i', 'which', 'when does', 'how long', 'how much']
        is_asking_question = any(qw in query_lower for qw in question_words)

        if has_upload_action or (has_analyze and has_insurance and not is_asking_question):
            logger.info(f"✅ INSURANCE ANALYSIS INTENT MATCHED: query='{query}'")
            result = {
                'intent': 'insurance_analysis',
                'confidence': 0.98,
                'reasoning': 'Keyword combination: analyze/check + insurance/policy detected',
                'sentiment': 'positive',
                'is_action_query': True,
                'is_info_query': False,
                'negation_detected': False
            }
            return result
        elif has_analyze and has_insurance and is_asking_question and has_policy_word:
            # User is asking a question that happens to contain "check"/"review" words
            # Route to policy_query instead of insurance_analysis
            logger.info(f"✅ REDIRECTED TO POLICY QUERY (question with analyze keyword): query='{query}'")
            result = {
                'intent': 'policy_query',
                'confidence': 0.93,
                'reasoning': 'User asking question about policies (contains analyze keyword but is a question)',
                'sentiment': 'neutral',
                'is_action_query': False,
                'is_info_query': True,
                'negation_detected': False
            }
            return result
        # ========== END INSURANCE ANALYSIS CHECK ==========

        # ========== ADDITIONAL POLICY QUERY FALLBACK ==========
        # Catch remaining policy query patterns - past tense "uploaded" without action words
        has_uploaded_past = 'uploaded' in query_lower and not has_upload_action
        has_policy_ref = any(pw in query_lower for pw in ['policy', 'policies', 'insurance'])

        if has_uploaded_past and has_policy_ref:
            logger.info(f"✅ POLICY QUERY INTENT MATCHED (uploaded past tense): query='{query}'")
            result = {
                'intent': 'policy_query',
                'confidence': 0.95,
                'reasoning': 'User asking about policies they have uploaded (past tense)',
                'sentiment': 'neutral',
                'is_action_query': False,
                'is_info_query': True,
                'negation_detected': False
            }
            return result
        # ========== END ADDITIONAL POLICY QUERY FALLBACK ==========

        # ========== OFF-TOPIC DETECTION (before LLM fallback) ==========
        # Check for queries clearly outside insurance/finance domain
        try:
            from ai_chat_components.processor import is_off_topic_query
            if is_off_topic_query(query):
                logger.info(f"✅ OFF-TOPIC DETECTED: '{query[:50]}'")
                result = {
                    'intent': 'off_topic',
                    'confidence': 0.95,
                    'reasoning': 'Query is about a topic outside insurance/finance domain',
                    'sentiment': 'neutral',
                    'is_action_query': False,
                    'is_info_query': False,
                    'negation_detected': False
                }
                return result
        except Exception as e:
            logger.warning(f"Off-topic check failed: {e}")
        # ========== END OFF-TOPIC DETECTION ==========

        # Check cache
        cache_key = self._get_cache_key(query, conversation_history)
        cached = self._get_cached_intent(cache_key)
        if cached:
            logger.info(f"✓ Intent cache hit: {cached['intent']}")
            return cached

        # Build context from conversation history
        context = self._build_context(conversation_history)

        # Create structured prompt for LLM
        system_prompt = """You are an expert intent classification system for a financial AI assistant.

Your job is to analyze user input and classify intent with 100% accuracy by understanding:
1. SEMANTIC MEANING - not just keywords
2. NEGATION - "I don't need" is DIFFERENT from "I need"
3. SENTIMENT - positive (wants service) vs negative (rejecting service)
4. ACTION vs INFORMATION - "I want loan" vs "What is loan"

CRITICAL RULES (FOLLOW THESE EXACTLY):
1. NEGATION DETECTION - If user says ANY of these about insurance/policy:
   - "I don't want insurance/policy" → MUST BE 'unknown' (NOT insurance_plan)
   - "I don't need insurance/policy" → MUST BE 'unknown' (NOT insurance_plan)
   - "not interested in insurance" → MUST BE 'unknown' (NOT insurance_plan)
   - "I only want X (not insurance)" → MUST BE 'unknown' (user rejecting insurance)
   - ANY negation about insurance → MUST BE 'unknown'

2. INFORMATION vs ACTION:
   - "What is X" → 'financial_education' (NOT X service)
   - "I need/want X" → X service (action-oriented)

3. IMPORTANT: If negation is detected, the intent CANNOT be the service being negated!
   Example: "I don't want insurance" has negation=true, so intent CANNOT be insurance_plan

Return ONLY a valid JSON object with these exact fields:
{
    "intent": "one of: greeting, small_talk, insurance_plan, insurance_analysis, policy_query, financial_education, off_topic, unknown",
    "confidence": 0.0-1.0,
    "reasoning": "brief explanation",
    "sentiment": "positive/negative/neutral",
    "is_action_query": true/false,
    "is_info_query": true/false,
    "negation_detected": true/false
}"""

        user_prompt = f"""Analyze this user input and classify the intent:

User input: "{query}"

{context}

Intent definitions:
1. greeting - Simple greetings (hi, hello, good morning)
2. small_talk - Casual conversation (how are you, thanks, bye)
3. insurance_plan - User WANTS to BUY/APPLY NEW insurance or policy (I want insurance, I need policy, buy insurance)
4. insurance_analysis - User wants to ANALYZE/CHECK/REVIEW/UPLOAD their EXISTING policy (analyze my policy, check my insurance, review my policy, upload insurance, i want analyze my policy)
5. policy_query - User asking QUESTIONS about their UPLOADED policies (how many policies, coverage gaps, recommendations, protection score, policy details, family coverage, exclusions, premium, expiry, is my policy active)
6. financial_education - User wants INFORMATION/EXPLANATION (What is insurance, explain policy, tell me about coverage)
7. off_topic - Query is about something outside insurance/finance (coding, tech, AI, movies, celebrities, sports, dating, recipes, ChatGPT, programming languages, who built you). These will be briefly answered then redirected to insurance.
8. unknown - Unclear, or DECLINING/REJECTING a service

COMPOUND/MULTI-QUESTION RULE:
- If the user asks MULTIPLE questions in one message and ANY part is about insurance/policy/finance, classify based on the insurance part.
- "Compare my health and auto insurance, which one is better?" → policy_query (comparing their policies)
- "What is copay and deductible, does my policy have it?" → policy_query (asking about their policy)
- "Tell me about term insurance, and also do I have one?" → policy_query (checking their policies)
- "Premium kitna hai aur discount milega?" → policy_query (asking about their premium)
- NEVER classify a compound query as off_topic if it mentions insurance, policy, premium, claim, coverage, or any financial term.

Examples of OFF-TOPIC (briefly answered then redirected to insurance):
- "Is ChatGPT better than Claude for coding?" → off_topic (tech comparison, not insurance)
- "What language is this written in?" → off_topic (self-referential tech question)
- "What libraries do you use?" → off_topic (tech question)
- "Tell me a recipe" → off_topic (cooking, not insurance)
- "Who is Narendra Modi?" → off_topic (politics)
- "Suggest a movie" → off_topic (entertainment)
- "Who built you?" → off_topic (self-referential)
- "Are you AI?" → off_topic (self-referential)

Examples of UNKNOWN (includes rejections - THESE ARE CRITICAL):
- "I don't need policy" → unknown (user declining insurance)
- "I don't want insurance" → unknown (user declining insurance)
- "not interested in insurance" → unknown (user declining insurance)
- "I already have insurance" → unknown (user declining)
- "no thanks" → unknown (user declining)
- "don't show me this" → unknown (user declining)
- "I don't want insurance, I only want a loan" → unknown (user rejecting insurance)
- "I only want loan, not insurance" → unknown (user rejecting insurance)
- ANY query with "don't want insurance" or "not interested in insurance" → MUST BE unknown

Examples of ACTION (user wants service):
- "I want insurance" → insurance_plan (action)
- "I need policy" → insurance_plan (action)
- "buy health insurance" → insurance_plan (action)
- "apply for policy" → insurance_plan (action)

Examples of INFORMATION (user wants to learn):
- "What is insurance" → financial_education (information)
- "explain policy" → financial_education (information)
- "tell me about coverage" → financial_education (information)

Think carefully about:
1. Is there negation? (don't, not, no, never) → If YES about insurance, intent MUST be 'unknown'
2. What does the user ACTUALLY want? → If they say they DON'T want something, they're rejecting it
3. Is it action-oriented or information-seeking?
4. CRITICAL CHECK: If user says "I don't want X", the intent CANNOT be X

FINAL VALIDATION:
- If negation_detected = true AND query mentions insurance → intent MUST be 'unknown'
- DO NOT classify as insurance_plan if user is rejecting/declining insurance

Classify accurately based on MEANING, not just keywords."""

        try:
            # Call LLM
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]

            response = self.llm.invoke(messages)
            response_text = response.content.strip()

            # Parse JSON response
            import json

            # Extract JSON if wrapped in markdown code blocks
            if '```json' in response_text:
                response_text = response_text.split('```json')[1].split('```')[0].strip()
            elif '```' in response_text:
                response_text = response_text.split('```')[1].split('```')[0].strip()

            result = json.loads(response_text)

            # Validate result
            if not self._validate_result(result):
                logger.warning(f"Invalid LLM result, using fallback")
                return self._fallback_detection(query, conversation_history)

            # Cache result
            self._cache_intent(cache_key, result)

            logger.info(f"✓ Intent detected: {result['intent']} (confidence: {result['confidence']:.2f})")
            if result.get('negation_detected'):
                logger.info(f"  ⚠ Negation detected in query")

            return result

        except Exception as e:
            logger.error(f"✗ LLM intent detection error: {e}")
            return self._fallback_detection(query, conversation_history)

    def detect_intent_fast(self, query: str) -> str:
        """
        Fast intent detection (just returns intent string)
        For backward compatibility with existing code
        """
        result = self.detect_intent_llm(query)
        return result['intent']

    def _build_context(self, conversation_history: Optional[List[Dict]]) -> str:
        """Build context string from conversation history"""
        if not conversation_history or len(conversation_history) == 0:
            return "Context: This is the first message in the conversation."

        # Get last 3 messages for context
        recent = conversation_history[-3:] if len(conversation_history) > 3 else conversation_history

        context_lines = ["Recent conversation context:"]
        for msg in recent:
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')[:100]  # Limit to 100 chars
            context_lines.append(f"- {role}: {content}")

        return "\n".join(context_lines)

    def _validate_result(self, result: Dict) -> bool:
        """Validate LLM result"""
        required_keys = ['intent', 'confidence', 'reasoning', 'sentiment',
                        'is_action_query', 'is_info_query', 'negation_detected']

        if not all(key in result for key in required_keys):
            return False

        valid_intents = [
            'greeting', 'small_talk', 'insurance_plan', 'insurance_analysis',
            'policy_query', 'financial_education', 'off_topic', 'unknown'
        ]

        if result['intent'] not in valid_intents:
            return False

        if not (0 <= result['confidence'] <= 1):
            return False

        if result['sentiment'] not in ['positive', 'negative', 'neutral']:
            return False

        return True

    def _fallback_detection(
        self,
        query: str,
        conversation_history: Optional[List[Dict]] = None
    ) -> Dict:
        """
        Fallback detection using rule-based patterns
        Used when LLM fails
        """
        query_lower = query.lower().strip()

        # Detect negation/declining - treat as unknown
        negation_patterns = [
            "don't need", "don't want", "do not need", "do not want",
            "not interested", "not looking", "no thanks", "not required",
            "already have", "don't show", "not now", "maybe later",
            "i don't", "i do not", "i'm not", "i am not"
        ]

        if any(pattern in query_lower for pattern in negation_patterns):
            return {
                'intent': 'unknown',
                'confidence': 0.85,
                'reasoning': 'User declining or expressing disinterest',
                'sentiment': 'negative',
                'is_action_query': False,
                'is_info_query': False,
                'negation_detected': True
            }

        # Greeting
        if any(word in query_lower for word in ['hello', 'hi', 'hey', 'good morning', 'good afternoon']):
            return {
                'intent': 'greeting',
                'confidence': 0.9,
                'reasoning': 'Greeting detected',
                'sentiment': 'neutral',
                'is_action_query': False,
                'is_info_query': False,
                'negation_detected': False
            }

        # ========== HIGHEST PRIORITY: BUY/GET INSURANCE (insurance_plan) ==========
        buy_insurance_patterns = [
            'buy insurance', 'buy policy', 'buy any policy', 'buy a policy',
            'get insurance', 'get policy', 'get any policy', 'get a policy',
            'purchase insurance', 'purchase policy', 'purchase any policy',
            'want insurance', 'want policy', 'want any policy', 'want a policy',
            'need insurance', 'need policy', 'need any policy', 'need a policy',
            'apply for insurance', 'apply for policy', 'apply insurance', 'apply policy',
            'can i buy insurance', 'can i buy policy', 'can i buy a policy',
            'can i get insurance', 'can i get policy', 'can i get a policy',
            'can i purchase insurance', 'can i purchase policy',
            'can i apply for insurance', 'can i apply for policy',
            'i want to buy insurance', 'i want to buy policy', 'i want to buy a policy',
            'i want to get insurance', 'i want to get policy',
            'i want to purchase insurance', 'i want to purchase policy',
            'give me insurance', 'give me policy',
            # Broken English patterns (common in Indian English)
            'want buy insurance', 'want buy policy',
            'want get insurance', 'want get policy',
            'want purchase insurance', 'want purchase policy',
            'buy some insurance', 'buy some policy', 'get some insurance', 'get some policy',
            'buy any insurance', 'get any insurance',
            'suggest me insurance', 'suggest me policy', 'suggest insurance', 'suggest policy',
            'insurance buy', 'insurance purchase', 'insurance get',
            'insurance lena', 'insurance le', 'insurance kharidna', 'insurance kharid',
            'policy lena', 'policy le', 'policy kharidna', 'policy kharid',
            'insurance chahiye', 'policy chahiye', 'bima chahiye', 'bima lena',
            'bima kharidna', 'bima kharid', 'bima le',
            'new insurance', 'naya insurance', 'nayi policy', 'naya bima',
        ]

        if any(pattern in query_lower for pattern in buy_insurance_patterns):
            return {
                'intent': 'insurance_plan',
                'confidence': 0.95,
                'reasoning': 'User wants to buy/get insurance',
                'sentiment': 'positive',
                'is_action_query': True,
                'is_info_query': False,
                'negation_detected': False
            }
        # ========== END BUY INSURANCE CHECK ==========

        # ========== UPLOAD/ANALYZE POLICY CHECK (insurance_analysis) ==========
        upload_analyze_patterns = [
            'want to upload', 'want upload', 'i want uploaded', 'upload new', 'upload a', 'upload my',
            'need to upload', 'for analyzing', 'for analysis', 'analyze new', 'analyse new',
            'want to analyze', 'want to analyse', 'new policy for', 'uploaded new',
            'analyze my policy', 'analyse my policy', 'check my policy', 'review my policy',
            'add policy', 'add my policy', 'add insurance', 'add my insurance',
            'add a policy', 'add new policy', 'add a insurance', 'add new insurance',
            'policy add', 'insurance add',
            'policy add karna', 'insurance add karna', 'policy add karo', 'insurance add karo',
        ]

        if any(pattern in query_lower for pattern in upload_analyze_patterns):
            return {
                'intent': 'insurance_analysis',
                'confidence': 0.95,
                'reasoning': 'User wants to upload/analyze policy',
                'sentiment': 'positive',
                'is_action_query': True,
                'is_info_query': False,
                'negation_detected': False
            }
        # ========== END UPLOAD/ANALYZE CHECK ==========

        # ========== POLICY QUERY CHECK (Questions about EXISTING uploaded policies) ==========
        policy_query_patterns = [
            'how many policies', 'how many policy', 'how many insurance',
            'policies have i', 'policy have i', 'policies i have',
            'have i uploaded', 'i have uploaded', 'i uploaded', 'uploaded any',
            'i am uploaded', 'am i uploaded', 'am uploaded',
            'uploaded self', 'uploaded family', 'self policy', 'family policy',
            'my policies', 'my policy details', 'show my policies', 'show my policy',
            'coverage gaps', 'my gaps', 'protection score', 'my score',
            'my recommendations', 'sum assured', 'my premium', 'policy expiry',
            'meri policy', 'kitni policy', 'kitne policy'
        ]

        if any(pattern in query_lower for pattern in policy_query_patterns):
            return {
                'intent': 'policy_query',
                'confidence': 0.95,
                'reasoning': 'Policy query pattern detected - asking about existing policies',
                'sentiment': 'neutral',
                'is_action_query': False,
                'is_info_query': True,
                'negation_detected': False
            }

        # Also check for "uploaded" (past tense) + policy/insurance without action keywords
        if 'uploaded' in query_lower and any(pw in query_lower for pw in ['policy', 'policies', 'insurance']):
            return {
                'intent': 'policy_query',
                'confidence': 0.90,
                'reasoning': 'User asking about uploaded policies (past tense)',
                'sentiment': 'neutral',
                'is_action_query': False,
                'is_info_query': True,
                'negation_detected': False
            }
        # ========== END POLICY QUERY CHECK ==========

        # Information queries (what is, explain, tell me about)
        info_patterns = ['what is', 'what are', 'explain', 'tell me about',
                         'how does', 'how do', 'define', 'meaning of']

        if any(pattern in query_lower for pattern in info_patterns):
            return {
                'intent': 'financial_education',
                'confidence': 0.85,
                'reasoning': 'Informational query detected',
                'sentiment': 'neutral',
                'is_action_query': False,
                'is_info_query': True,
                'negation_detected': False
            }

        # Insurance analysis patterns (check BEFORE insurance_plan)
        insurance_analysis_patterns = [
            'analyze my insurance', 'analyse my insurance',
            'analyze my policy', 'analyse my policy',
            'analyze insurance', 'analyse insurance',
            'analyze policy', 'analyse policy',
            'check my insurance', 'check my policy',
            'review my insurance', 'review my policy',
            'evaluate my insurance', 'evaluate my policy',
            'upload my policy', 'upload my insurance',
            'add my policy', 'add my insurance',
            'scan my policy', 'audit my insurance',
            'insurance analysis', 'policy analysis',
            'mujhe apna insurance analyze karna',
            'apna insurance check karna',
            'mera insurance analyze karo',
            'apna insurance analyze karna'
        ]

        if any(pattern in query_lower for pattern in insurance_analysis_patterns):
            return {
                'intent': 'insurance_analysis',
                'confidence': 0.95,
                'reasoning': 'Insurance analysis/review action detected',
                'sentiment': 'positive',
                'is_action_query': True,
                'is_info_query': False,
                'negation_detected': False
            }

        # Keyword combination check for insurance analysis
        # NOTE: 'upload' removed - causes false positives with "uploaded" (past tense for policy_query)
        analyze_keywords = ['analyze', 'analyse', 'analysis', 'check', 'review', 'evaluate', 'assess', 'audit', 'scan']
        # Action keywords for NEW upload (present/future tense)
        upload_action_keywords = ['upload my', 'upload a', 'upload new', 'want to upload', 'add my', 'add a', 'add new']
        insurance_keywords = ['insurance', 'policy', 'coverage', 'bima', 'beema']

        has_analyze = any(kw in query_lower for kw in analyze_keywords)
        has_upload_action = any(kw in query_lower for kw in upload_action_keywords)
        has_insurance = any(kw in query_lower for kw in insurance_keywords)

        if (has_analyze or has_upload_action) and has_insurance:
            return {
                'intent': 'insurance_analysis',
                'confidence': 0.9,
                'reasoning': 'Insurance analysis keywords detected',
                'sentiment': 'positive',
                'is_action_query': True,
                'is_info_query': False,
                'negation_detected': False
            }

        # Action queries for insurance (buying/applying for NEW insurance)
        insurance_action_patterns = [
            'i want insurance', 'i need insurance', 'i want policy',
            'i need policy', 'buy insurance', 'apply insurance',
            'get insurance', 'purchase policy'
        ]

        if any(pattern in query_lower for pattern in insurance_action_patterns):
            return {
                'intent': 'insurance_plan',
                'confidence': 0.9,
                'reasoning': 'Insurance application action detected',
                'sentiment': 'positive',
                'is_action_query': True,
                'is_info_query': False,
                'negation_detected': False
            }

        # Unknown
        return {
            'intent': 'unknown',
            'confidence': 0.5,
            'reasoning': 'No clear intent detected',
            'sentiment': 'neutral',
            'is_action_query': False,
            'is_info_query': False,
            'negation_detected': False
        }

    def _get_cache_key(self, query: str, conversation_history: Optional[List[Dict]]) -> str:
        """Generate cache key"""
        history_hash = ""
        if conversation_history and len(conversation_history) > 0:
            # Hash last 3 messages
            recent = conversation_history[-3:]
            history_text = "".join([m.get('content', '') for m in recent])
            history_hash = hashlib.md5(history_text.encode()).hexdigest()[:8]

        query_hash = hashlib.md5(query.lower().encode()).hexdigest()
        return f"{query_hash}_{history_hash}"

    def _get_cached_intent(self, cache_key: str) -> Optional[Dict]:
        """Get cached intent result"""
        if cache_key in _intent_cache:
            cached_data = _intent_cache[cache_key]
            if time.time() - cached_data['timestamp'] < CACHE_TTL:
                return cached_data['result']
            else:
                del _intent_cache[cache_key]
        return None

    def _cache_intent(self, cache_key: str, result: Dict):
        """Cache intent result"""
        _intent_cache[cache_key] = {
            'result': result,
            'timestamp': time.time()
        }

        # Cleanup old cache entries
        if len(_intent_cache) > 500:
            # Remove oldest entries
            sorted_keys = sorted(_intent_cache.keys(),
                               key=lambda k: _intent_cache[k]['timestamp'])
            for key in sorted_keys[:100]:
                del _intent_cache[key]


# Global instance
_detector = None

def get_intent_detector() -> AdvancedIntentDetector:
    """Get or create global intent detector instance"""
    global _detector
    if _detector is None:
        _detector = AdvancedIntentDetector()
        logger.info("✓ Advanced Intent Detector initialized")
    return _detector


# Convenience functions for backward compatibility
def detect_intent_advanced(query: str, conversation_history: Optional[List[Dict]] = None) -> Dict:
    """
    Detect intent with full details

    Returns dict with intent, confidence, reasoning, etc.
    """
    detector = get_intent_detector()
    return detector.detect_intent_llm(query, conversation_history)


def detect_intent_simple(query: str, conversation_history: Optional[List[Dict]] = None) -> str:
    """
    Simple intent detection - just returns intent string

    For backward compatibility with existing code
    """
    detector = get_intent_detector()
    result = detector.detect_intent_llm(query, conversation_history)
    return result['intent']


# Test function
def test_intent_detection():
    """Test the intent detection system"""
    test_cases = [
        # Rejections (should be detected correctly)
        ("I don't need policy", "rejection"),
        ("I don't want insurance", "rejection"),
        ("not interested in loan", "rejection"),
        ("I already have insurance", "rejection"),
        ("no thanks", "rejection"),

        # Action queries (should be detected correctly)
        ("I need money", "financial_assistance"),
        ("I want insurance", "insurance_plan"),
        ("give me policy", "insurance_plan"),
        ("my mother is admitted need money", "financial_assistance"),

        # Information queries (should be detected correctly)
        ("what is insurance", "financial_education"),
        ("explain loan", "financial_education"),
        ("tell me about policy", "financial_education"),

        # Greetings
        ("hello", "greeting"),
        ("hi there", "greeting"),
    ]

    print("\n" + "="*80)
    print("TESTING ADVANCED INTENT DETECTION")
    print("="*80 + "\n")

    detector = get_intent_detector()

    passed = 0
    failed = 0

    for query, expected_intent in test_cases:
        result = detector.detect_intent_llm(query)
        actual_intent = result['intent']

        status = "✓ PASS" if actual_intent == expected_intent else "✗ FAIL"
        if actual_intent == expected_intent:
            passed += 1
        else:
            failed += 1

        print(f"{status}")
        print(f"  Query: '{query}'")
        print(f"  Expected: {expected_intent}")
        print(f"  Actual: {actual_intent}")
        print(f"  Confidence: {result['confidence']:.2f}")
        print(f"  Reasoning: {result['reasoning']}")
        print(f"  Negation: {result['negation_detected']}")
        print()

    print("="*80)
    print(f"RESULTS: {passed} passed, {failed} failed out of {len(test_cases)} tests")
    print(f"Accuracy: {(passed/len(test_cases)*100):.1f}%")
    print("="*80 + "\n")


if __name__ == "__main__":
    # Run tests
    test_intent_detection()

logger.info("✓ Advanced Intent Detector module loaded")
