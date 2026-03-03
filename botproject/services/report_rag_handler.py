"""
Report RAG Handler
Handles RAG queries for user's insurance gap analysis reports
"""
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)


class ReportRAGHandler:
    """Handle RAG queries for user's insurance reports with improved accuracy"""

    def __init__(self):
        self.report_context_window = 24  # hours
        self.min_similarity_threshold = 0.3

        # Keywords that indicate report queries
        self.report_query_patterns = {
            'score': ['protection score', 'my score', 'score'],
            'gaps': ['gap', 'gaps', 'missing', 'lacking', 'not covered'],
            'coverage': ['my coverage', 'current coverage', 'coverage amount', 'sum insured'],
            'recommendations': ['recommend', 'suggestion', 'should i', 'what to do', 'improve'],
            'premium': ['premium', 'cost', 'price', 'how much'],
            'report': ['my report', 'my analysis', 'analysis', 'report']
        }

    def detect_report_query(
        self,
        query: str,
        conversation_history: List = None,
        metadata: Dict = None
    ) -> bool:
        """
        Enhanced detection for report-related queries

        Returns True if:
        1. Query contains report-specific keywords
        2. Recent conversation included gap_analysis or insurance_analysis
        3. Metadata indicates file was processed recently
        """
        query_lower = query.lower()

        # Check 1: Direct keyword match
        for category, keywords in self.report_query_patterns.items():
            if any(keyword in query_lower for keyword in keywords):
                logger.info(f"Report query detected: {category} - '{query}'")
                return True

        # Check 2: Recent report generation in conversation
        if conversation_history:
            recent_messages = conversation_history[-5:]  # Last 5 messages
            for msg in recent_messages:
                msg_metadata = msg.get('metadata', {})
                intent = msg_metadata.get('intent', '')

                if intent in ['gap_analysis', 'insurance_analysis', 'file_processed']:
                    logger.info(f"Report query detected from conversation context: {intent}")
                    return True

        # Check 3: Metadata indicates recent file processing
        if metadata:
            if metadata.get('file_processed') or metadata.get('intent') == 'gap_analysis':
                logger.info("Report query detected from metadata")
                return True

        return False

    def get_user_report_context(self, user_id: int, chat_session_id: str = None) -> Optional[Dict]:
        """
        Get user's most recent insurance report with all relevant data

        Checks:
        1. MongoDB insurance_reports collection (if available)
        2. Chat history metadata for report data
        3. Session storage
        """
        from database_storage.mongodb_chat_manager import mongodb_chat_manager

        # Try MongoDB first
        try:
            if hasattr(mongodb_chat_manager, 'get_latest_insurance_report'):
                report = mongodb_chat_manager.get_latest_insurance_report(
                    user_id=user_id,
                    hours=self.report_context_window
                )

                if report:
                    logger.info(f"Found report in MongoDB for user {user_id}")
                    # MongoDB document has structured data at root level
                    # The 'data' field contains the full backup
                    return self._format_report_context(report)
        except Exception as e:
            logger.warning(f"MongoDB report lookup failed: {e}")

        # Fallback: Check chat history
        if chat_session_id:
            try:
                from routers.chat import get_conversation_history

                history = get_conversation_history(chat_session_id, limit=20)

                # Look for insurance_analysis response in history
                for msg in reversed(history):
                    metadata = msg.get('metadata', {})
                    if metadata.get('intent') in ['gap_analysis', 'insurance_analysis']:
                        # Extract report data from the message
                        content = msg.get('content', '')

                        # Try to parse as JSON
                        try:
                            data = json.loads(content)
                            if 'data' in data:
                                logger.info(f"Found report data in chat history for user {user_id}")
                                return self._format_report_context(data['data'])
                        except:
                            pass

            except Exception as e:
                logger.warning(f"Chat history lookup failed: {e}")

        logger.warning(f"No report found for user {user_id}")
        return None

    def _format_report_context(self, report_data: Dict) -> Dict:
        """Format report data into structured context"""
        return {
            "report_url": report_data.get('report_url'),
            "protection_score": report_data.get('protection_score'),
            "coverage_gaps": report_data.get('coverage_gaps', []),
            "recommendations": report_data.get('recommendations', []),
            "current_coverage": report_data.get('current_coverage') or report_data.get('coverage_details', {}).get('current_coverage'),
            "recommended_coverage": report_data.get('recommended_coverage') or report_data.get('coverage_details', {}).get('recommended_coverage'),
            "premium_estimates": report_data.get('premium_estimates', {}),
            "policy_details": report_data.get('policy_details', {}),
            "policy_info": report_data.get('policy_info', {}),
            "analysis_results": report_data.get('analysis_results', ''),
            "category_scores": report_data.get('category_scores', {})
        }

    def create_context_for_llm(self, report_context: Dict, query: str) -> str:
        """
        Create a focused context string for LLM based on query type
        This improves accuracy by only including relevant sections
        """
        query_lower = query.lower()
        context_parts = []

        # Header
        context_parts.append("=== USER'S INSURANCE GAP ANALYSIS REPORT ===\n")

        # Include protection score if available
        if report_context.get('protection_score') is not None:
            context_parts.append(f"PROTECTION SCORE: {report_context['protection_score']}/100")

        # Include coverage info if query is about coverage/amount/sum
        if any(word in query_lower for word in ['coverage', 'amount', 'sum', 'insured', 'cover']):
            if report_context.get('current_coverage'):
                context_parts.append(f"CURRENT COVERAGE: ₹{report_context['current_coverage']:,}")
            if report_context.get('recommended_coverage'):
                context_parts.append(f"RECOMMENDED COVERAGE: ₹{report_context['recommended_coverage']:,}")

        # Include gaps if query is about gaps/missing/lacking
        if any(word in query_lower for word in ['gap', 'missing', 'lack', 'not covered', 'problem']):
            if report_context.get('coverage_gaps'):
                context_parts.append("\nCOVERAGE GAPS:")
                for i, gap in enumerate(report_context['coverage_gaps'], 1):
                    context_parts.append(f"  {i}. {gap}")

        # Include recommendations if query is about what to do/suggest/recommend
        if any(word in query_lower for word in ['recommend', 'suggest', 'should', 'what to do', 'improve', 'fix']):
            if report_context.get('recommendations'):
                context_parts.append("\nRECOMMENDATIONS:")
                for i, rec in enumerate(report_context['recommendations'], 1):
                    context_parts.append(f"  {i}. {rec}")

        # Include premium if query is about cost/price/premium
        if any(word in query_lower for word in ['premium', 'cost', 'price', 'pay', 'expensive', 'cheap']):
            estimates = report_context.get('premium_estimates', {})
            if estimates:
                context_parts.append("\nPREMIUM ESTIMATES:")
                if estimates.get('current'):
                    context_parts.append(f"  Current: {estimates['current']}")
                if estimates.get('recommended'):
                    context_parts.append(f"  Recommended: {estimates['recommended']}")
                if estimates.get('additional'):
                    context_parts.append(f"  Additional Cost: {estimates['additional']}")

        # If no specific match or limited structured data, use full analysis text
        if len(context_parts) <= 2:  # Only header + maybe score
            # Use the full analysis_results text if available
            full_text = report_context.get('analysis_results', '')

            if full_text:
                # Use first 2500 characters of the full report
                context_parts = [
                    "=== USER'S INSURANCE GAP ANALYSIS REPORT ===\n",
                    full_text[:2500]
                ]
            else:
                # Fallback to structured data (even if limited)
                context_parts = ["=== USER'S INSURANCE GAP ANALYSIS REPORT ==="]

                if report_context.get('protection_score') is not None:
                    context_parts.append(f"\nProtection Score: {report_context['protection_score']}/100")

                if report_context.get('current_coverage'):
                    context_parts.append(f"Current Coverage: ₹{report_context['current_coverage']:,}")

                if report_context.get('recommended_coverage'):
                    context_parts.append(f"Recommended Coverage: ₹{report_context['recommended_coverage']:,}")

                if report_context.get('coverage_gaps'):
                    context_parts.append("\nCoverage Gaps:")
                    for gap in report_context['coverage_gaps']:
                        context_parts.append(f"  - {gap}")

                if report_context.get('recommendations'):
                    context_parts.append("\nRecommendations:")
                    for rec in report_context['recommendations']:
                        context_parts.append(f"  - {rec}")

        return "\n".join(context_parts)

    async def answer_report_query(
        self,
        query: str,
        user_id: int,
        chat_session_id: str,
        conversation_history: List = None
    ) -> Dict:
        """
        Answer user's question about their insurance report using RAG

        Improved approach:
        1. Get report context
        2. Create focused context based on query
        3. Use simple pattern matching for common questions
        4. Fall back to LLM for complex questions
        """
        logger.info(f"RAG: Answering report query for user {user_id}: '{query}'")

        # Get report context
        report_context = self.get_user_report_context(user_id, chat_session_id)

        if not report_context:
            logger.warning(f"RAG: No report found for user {user_id}")
            return {
                "response": "I don't have a recent insurance analysis report for you. "
                           "Please upload your insurance policy document to get a gap analysis.",
                "action": "no_report_found",
                "show_service_options": True,
                "file_action_needed": "analyze_pdf",
                "language": "en"
            }

        logger.info(f"RAG: Report found with keys: {list(report_context.keys())}")
        logger.info(f"RAG: Protection score: {report_context.get('protection_score')}")
        logger.info(f"RAG: Report URL: {report_context.get('report_url')}")

        # Try simple pattern matching first for better accuracy
        simple_answer = self._try_simple_answer(query, report_context)
        if simple_answer:
            logger.info(f"RAG: Pattern matching succeeded")
            return {
                "response": simple_answer,
                "action": "report_query_answered",
                "show_service_options": False,
                "source": "user_report",
                "report_url": report_context.get('report_url'),
                "language": "en"
            }

        # Fall back to LLM for complex queries
        logger.info(f"RAG: Pattern matching failed, using LLM")
        return await self._llm_answer(query, report_context, conversation_history, chat_session_id)

    def _try_simple_answer(self, query: str, report_context: Dict) -> Optional[str]:
        """
        Try to answer simple queries with pattern matching
        This is more reliable than LLM for straightforward questions
        """
        query_lower = query.lower()

        # Protection score questions
        if any(word in query_lower for word in ['protection score', 'my score', 'score']):
            score = report_context.get('protection_score')
            if score is not None:
                level = "excellent" if score >= 80 else "good" if score >= 60 else "needs improvement"
                return (f"Your protection score is {score} out of 100, which is {level}. "
                       f"This score is based on analyzing your current insurance coverage against recommended standards.")

        # Coverage amount questions
        if any(word in query_lower for word in ['current coverage', 'coverage amount', 'how much coverage', 'sum insured']):
            current = report_context.get('current_coverage')
            recommended = report_context.get('recommended_coverage')
            if current:
                response = f"Your current insurance coverage is ₹{current:,}."
                if recommended:
                    gap = recommended - current
                    if gap > 0:
                        response += f" However, we recommend ₹{recommended:,} for adequate protection (a gap of ₹{gap:,})."
                return response

        # Gap questions
        if any(word in query_lower for word in ['what gaps', 'gaps did you find', 'what\'s missing', 'coverage gaps']):
            gaps = report_context.get('coverage_gaps', [])
            if gaps:
                response = f"I found {len(gaps)} coverage gap(s) in your insurance:\n\n"
                for i, gap in enumerate(gaps, 1):
                    response += f"{i}. {gap}\n"
                return response.strip()

        # Recommendation questions
        if any(word in query_lower for word in ['what do you recommend', 'what should i do', 'recommendations', 'suggestions']):
            recs = report_context.get('recommendations', [])
            if recs:
                response = "Based on your gap analysis, here are my recommendations:\n\n"
                for i, rec in enumerate(recs, 1):
                    response += f"{i}. {rec}\n"
                return response.strip()

        # Premium questions
        if any(word in query_lower for word in ['premium', 'cost', 'how much', 'price']):
            estimates = report_context.get('premium_estimates', {})
            if estimates:
                response = "Premium estimates:\n"
                if estimates.get('current'):
                    response += f"Current: {estimates['current']}\n"
                if estimates.get('recommended'):
                    response += f"Recommended: {estimates['recommended']}\n"
                if estimates.get('additional'):
                    response += f"Additional cost: {estimates['additional']}\n"
                return response.strip()

        return None

    async def _llm_answer(
        self,
        query: str,
        report_context: Dict,
        conversation_history: List,
        chat_session_id: str
    ) -> Dict:
        """Use LLM for complex queries"""
        try:
            import openai
            import os

            # Get API key from environment
            openai.api_key = os.getenv('OPENAI_API_KEY')

            if not openai.api_key:
                raise ValueError("OPENAI_API_KEY environment variable not set")

            # Create focused context
            context_str = self.create_context_for_llm(report_context, query)

            logger.info(f"LLM context created with {len(context_str)} characters")
            logger.debug(f"Context preview: {context_str[:200]}...")

            # Build system prompt
            system_prompt = f"""You are an insurance advisor assistant helping a user understand their insurance gap analysis report.

{context_str}

Instructions:
1. Answer ONLY based on the report data provided above
2. Be specific and reference exact numbers from the report
3. Keep answers concise (2-3 sentences max)
4. If the information is not in the report, say so
5. Use Indian Rupee format (₹) for amounts
6. Be helpful and explain in simple terms"""

            # Get recent conversation for context
            history_messages = []
            if conversation_history:
                for msg in conversation_history[-3:]:
                    role = msg.get('role', 'user')
                    content = msg.get('content', '')
                    if role and content:
                        history_messages.append({"role": role, "content": content})

            # Add current query
            history_messages.append({"role": "user", "content": query})

            logger.info(f"Calling OpenAI with {len(history_messages)} messages")

            # Call OpenAI
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt}
                ] + history_messages,
                temperature=0.3,  # Lower temperature for more factual answers
                max_tokens=300
            )

            answer = response.choices[0].message.content.strip()
            logger.info(f"LLM answer received: {len(answer)} characters")

            # Store in conversation memory
            from routers.chat import add_to_conversation_memory
            add_to_conversation_memory(chat_session_id, "assistant", answer)

            return {
                "response": answer,
                "action": "report_query_answered",
                "show_service_options": False,
                "source": "user_report_llm",
                "report_url": report_context.get('report_url'),
                "language": "en"
            }

        except Exception as e:
            import traceback
            logger.error(f"LLM answer failed: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            logger.error(f"Report context keys: {list(report_context.keys()) if report_context else 'None'}")

            # Fallback to showing report URL
            return {
                "response": f"I'm having trouble accessing the details right now, but you can view your complete gap analysis report here: {report_context.get('report_url')}",
                "action": "error_with_fallback",
                "show_service_options": False,
                "report_url": report_context.get('report_url'),
                "language": "en"
            }


# Create singleton
report_rag_handler = ReportRAGHandler()
