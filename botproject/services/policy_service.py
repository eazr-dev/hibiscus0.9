"""
Policy Service
Business logic for insurance policy analysis, claim guidance, and policy comparisons
"""
import logging
import os
from datetime import datetime
from typing import List, Optional, Dict, Any
from io import BytesIO

logger = logging.getLogger(__name__)


class PolicyService:
    """Service for handling insurance policy operations"""

    def __init__(self):
        """Initialize policy service"""
        from core.dependencies import MONGODB_AVAILABLE
        if MONGODB_AVAILABLE:
            from database_storage.mongodb_chat_manager import mongodb_chat_manager
            self.mongodb_manager = mongodb_chat_manager
        else:
            self.mongodb_manager = None
            logger.warning("MongoDB not available for PolicyService")

    async def get_claim_guidance(
        self,
        query: str,
        insurance_type: str,
        session_id: str,
        user_id: int,
        conversation_history: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate claim guidance response with LLM

        Args:
            query: User's claim question
            insurance_type: Type of insurance (health, motor, life)
            session_id: Current session ID
            user_id: User ID
            conversation_history: Previous conversation messages

        Returns:
            Dictionary with response, action, and suggestions
        """
        from ai_chat_components.processor import (
            generate_claim_guidance_response,
            generate_claim_aware_casual_response,
            generate_claim_suggestions
        )

        if conversation_history is None:
            conversation_history = []

        # Check if query is about claim process
        claim_keywords = [
            'claim', 'settlement', 'reimbursement', 'cashless', 'documents',
            'process', 'steps', 'how to claim', 'claim status', 'claim form',
            'hospital bills', 'claim rejection', 'claim approval', 'claim amount'
        ]

        is_claim_query = any(keyword in query.lower() for keyword in claim_keywords)

        # Generate response based on query type
        if is_claim_query:
            response = generate_claim_guidance_response(
                query,
                insurance_type,
                conversation_history
            )
            action = "claim_guidance"
        else:
            # For general queries, use casual response with claim context
            response = generate_claim_aware_casual_response(
                query,
                conversation_history
            )
            action = "casual_conversation"

        # Generate suggestions based on context
        suggestions = generate_claim_suggestions(insurance_type, conversation_history)

        # Store messages in MongoDB
        if self.mongodb_manager:
            # Store user message
            self.mongodb_manager.claim_guidance_collection.insert_one({
                "session_id": session_id,
                "user_id": user_id,
                "role": "user",
                "content": query,
                "insurance_type": insurance_type,
                "timestamp": datetime.utcnow(),
                "guidance_type": "claim_settlement"
            })

            # Store assistant response
            self.mongodb_manager.claim_guidance_collection.insert_one({
                "session_id": session_id,
                "user_id": user_id,
                "role": "assistant",
                "content": response,
                "insurance_type": insurance_type,
                "timestamp": datetime.utcnow(),
                "guidance_type": "claim_settlement",
                "action": action
            })

        return {
            "response": response,
            "action": action,
            "suggestions": suggestions,
            "context_used": len(conversation_history) > 0
        }

    async def analyze_insurance_document(
        self,
        files: List,
        user_id: str,
        session_id: str,
        generate_pdf: bool = True
    ) -> Dict[str, Any]:
        """
        Analyze insurance documents (PDF/images) using universal analyzer

        Args:
            files: List of uploaded files
            user_id: User ID
            session_id: Session ID
            generate_pdf: Whether to generate PDF report

        Returns:
            Dictionary with analysis results

        Raises:
            ValueError: If analysis fails
        """
        from financial_services.dynamic_insurance_analyzer import UniversalDynamicAnalyzer
        from database_storage.s3_bucket import upload_pdf_to_s3, upload_image_to_s3
        from database_storage.mongodb_chat_manager import store_policy_analysis_in_mongodb

        OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        if not OPENAI_API_KEY:
            raise ValueError("OpenAI API key not configured")

        universal_analyzer = UniversalDynamicAnalyzer(openai_api_key=OPENAI_API_KEY)

        # Validate file types
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

            logger.info(f"Analyzing insurance for User: {user_id}, Session: {session_id}, File: {file.filename}")

            # Upload original document to S3
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            original_doc_filename = f"original_docs/{user_id}/{timestamp}_{file.filename}"
            original_doc_url = None

            try:
                if file_ext in {'.png', '.jpg', '.jpeg', '.webp'}:
                    original_doc_s3 = upload_image_to_s3(file_content, original_doc_filename, 'raceabove-dev')
                else:
                    original_doc_s3 = upload_pdf_to_s3(BytesIO(file_content), original_doc_filename, 'raceabove-dev')

                original_doc_url = original_doc_s3.get("url") or original_doc_s3.get("s3_url")
                logger.info(f"Original document uploaded to S3: {original_doc_url}")
            except Exception as upload_error:
                logger.error(f"Failed to upload original document: {upload_error}")

            # Handle images - store without analysis
            if file_ext in {'.png', '.jpg', '.jpeg', '.webp'}:
                try:
                    mongodb_id = None
                    if self.mongodb_manager:
                        mongodb_id = store_policy_analysis_in_mongodb(
                            userId=user_id,
                            sessionId=session_id,
                            filename=file.filename,
                            analysis_result={
                                "file_type": "image",
                                "original_filename": file.filename,
                                "file_size": len(file_content),
                                "upload_timestamp": datetime.now().isoformat()
                            },
                            s3_url=original_doc_url
                        )

                    results.append({
                        "filename": file.filename,
                        "success": True,
                        "file_type": "image",
                        "original_document_url": original_doc_url,
                        "mongodb_id": str(mongodb_id) if mongodb_id else None,
                        "message": "Image uploaded successfully for manual review"
                    })
                    continue

                except Exception as img_error:
                    logger.error(f"Image handling error: {img_error}")
                    results.append({
                        "filename": file.filename,
                        "success": False,
                        "error": f"Image processing failed: {img_error}"
                    })
                    continue

            # Handle PDF analysis
            try:
                # Analyze with universal analyzer
                file.file.seek(0)  # Reset file pointer
                analysis_result = universal_analyzer.analyze_document(file.file)

                if not analysis_result.get("success"):
                    results.append({
                        "filename": file.filename,
                        "success": False,
                        "error": analysis_result.get("error", "Analysis failed")
                    })
                    continue

                # Store analysis in MongoDB
                mongodb_id = None
                if self.mongodb_manager:
                    mongodb_id = store_policy_analysis_in_mongodb(
                        userId=user_id,
                        sessionId=session_id,
                        filename=file.filename,
                        analysis_result=analysis_result,
                        s3_url=original_doc_url
                    )

                # Add result
                results.append({
                    "filename": file.filename,
                    "success": True,
                    "analysis": analysis_result,
                    "original_document_url": original_doc_url,
                    "mongodb_id": str(mongodb_id) if mongodb_id else None
                })

                logger.info(f"Successfully analyzed {file.filename}")

            except Exception as analysis_error:
                logger.error(f"Analysis error for {file.filename}: {analysis_error}")
                results.append({
                    "filename": file.filename,
                    "success": False,
                    "error": str(analysis_error),
                    "original_document_url": original_doc_url
                })

        return {
            "results": results,
            "total_files": len(files),
            "successful": len([r for r in results if r.get("success")]),
            "failed": len([r for r in results if not r.get("success")])
        }

    async def compare_policies(
        self,
        policy_ids: List[str],
        user_id: str,
        session_id: str
    ) -> Dict[str, Any]:
        """
        Compare multiple insurance policies

        Args:
            policy_ids: List of policy MongoDB IDs
            user_id: User ID
            session_id: Session ID

        Returns:
            Dictionary with comparison results

        Raises:
            ValueError: If less than 2 valid policies found
        """
        if not self.mongodb_manager:
            raise ValueError("MongoDB service unavailable")

        # Fetch policies from MongoDB
        from bson import ObjectId
        policies = []

        for policy_id in policy_ids:
            try:
                policy = self.mongodb_manager.policy_analyses_collection.find_one(
                    {"_id": ObjectId(policy_id)}
                )
                if policy:
                    policies.append(policy)
            except Exception as e:
                logger.warning(f"Could not fetch policy {policy_id}: {e}")

        if len(policies) < 2:
            raise ValueError("At least 2 valid policies required for comparison")

        # Build comparison
        comparison = {
            "total_policies": len(policies),
            "policies": [],
            "comparison_summary": {
                "lowest_premium": None,
                "highest_coverage": None,
                "best_value": None
            },
            "timestamp": datetime.now().isoformat()
        }

        for policy in policies:
            comparison["policies"].append({
                "policy_id": str(policy["_id"]),
                "filename": policy.get("filename"),
                "insurance_type": policy.get("insurance_type"),
                "analysis": policy.get("analysis_result"),
                "uploaded_at": policy.get("created_at").isoformat() if policy.get("created_at") else None
            })

        return comparison

    async def get_market_rates(self) -> Dict[str, Any]:
        """
        Get current insurance market rates and benchmarks

        Returns:
            Dictionary with market rate information
        """
        market_rates = {
            "health_insurance": {
                "average_premium_annual": {
                    "individual": "₹15,000 - ₹25,000",
                    "family": "₹30,000 - ₹50,000"
                },
                "coverage_range": "₹3 Lakhs - ₹25 Lakhs"
            },
            "motor_insurance": {
                "average_premium_annual": {
                    "two_wheeler": "₹1,500 - ₹3,000",
                    "four_wheeler": "₹5,000 - ₹15,000"
                }
            },
            "life_insurance": {
                "average_premium_annual": "₹10,000 - ₹30,000",
                "coverage_range": "₹10 Lakhs - ₹1 Crore"
            },
            "last_updated": datetime.now().isoformat()
        }

        return market_rates


# Create singleton instance
policy_service = PolicyService()
