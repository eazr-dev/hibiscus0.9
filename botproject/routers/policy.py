"""
Insurance Policy Router
Handles insurance policy analysis, claim guidance, and policy comparisons
"""
import logging
import hashlib
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, HTTPException, File, UploadFile, Form
from models.insurance import ClaimGuidanceRequest
from core.dependencies import (
    get_session,
    store_session,
    MONGODB_AVAILABLE
)
from session_security.session_manager import session_manager
from services.policy_service import policy_service

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(tags=["Insurance & Policy"])


@router.post("/insurance-claim-guidance")
async def claim_guidance(request: ClaimGuidanceRequest):
    """
    Guide users through insurance claim settlement process

    Features:
    - Step-by-step claim guidance
    - Document requirements
    - Process explanation
    - Session regeneration support
    - Conversation history tracking
    """
    try:
        query = request.query.strip()
        original_session_id = request.session_id
        access_token = request.access_token
        user_id = request.user_id
        insurance_type = request.insurance_type

        current_timestamp = datetime.now().isoformat()

        logger.info(f"Processing claim guidance query: '{query}' for session: {original_session_id}")

        # Auto-validate and regenerate session if needed
        session_id, session_data, was_regenerated = session_manager.validate_and_regenerate_session(
            original_session_id,
            get_session,
            store_session,
            user_data={
                'user_id': user_id,
                'access_token': access_token
            }
        )

        if was_regenerated:
            logger.info(f"Session auto-regenerated for claim guidance: {original_session_id} -> {session_id}")
            if not session_data.get('access_token'):
                session_data['access_token'] = access_token
            if not session_data.get('user_id'):
                session_data['user_id'] = user_id
            store_session(session_id, session_data, expire_seconds=1209600)

        # Update session activity
        session_data['last_activity'] = current_timestamp
        store_session(session_id, session_data, expire_seconds=1209600)

        # Get conversation history from MongoDB
        conversation_history = []
        if MONGODB_AVAILABLE:
            from database_storage.mongodb_chat_manager import mongodb_chat_manager

            claim_history = mongodb_chat_manager.claim_guidance_collection.find(
                {
                    "$or": [
                        {"session_id": session_id},
                        {"session_id": original_session_id}
                    ]
                }
            ).sort("timestamp", -1).limit(10)

            for msg in claim_history:
                conversation_history.append({
                    'role': msg.get('role', 'user'),
                    'content': msg.get('content', ''),
                    'timestamp': msg.get('timestamp', datetime.now()).isoformat()
                })

        # Get claim guidance using service
        try:
            guidance_result = await policy_service.get_claim_guidance(
                query=query,
                insurance_type=insurance_type,
                session_id=session_id,
                user_id=user_id,
                conversation_history=conversation_history
            )

            # Build response
            result = {
                **guidance_result,
                "show_service_options": False,
                "language": "en",
                "session_id": session_id,
                "session_regenerated": was_regenerated,
                "conversation_metadata": {
                    "message_id": hashlib.md5(f"{session_id}_{query}_{current_timestamp}".encode()).hexdigest()[:16],
                    "language_detected": "en",
                    "intent": "claim_guidance" if guidance_result["action"] == "claim_guidance" else "general_query",
                    "insurance_type": insurance_type,
                    "conversation_length": len(conversation_history) + 2,
                    "timestamp": current_timestamp,
                    "session_regenerated": was_regenerated,
                    "current_session_id": session_id,
                    "original_session_id": original_session_id if was_regenerated else None
                }
            }

            if was_regenerated:
                result["original_session_id"] = original_session_id
                result["session_message"] = "Session regenerated successfully"
                logger.info(f"Claim guidance processed with regenerated session: {original_session_id} -> {session_id}")

            return result

        except Exception as e:
            logger.error(f"Error processing claim guidance: {e}")
            raise HTTPException(status_code=500, detail="Failed to process claim guidance")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing claim guidance: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process claim guidance")


@router.post("/analyze-insurance-dynamic", tags=["Analysis"])
async def analyze_insurance(
    files: List[UploadFile] = File(...),
    userId: str = Form(...),
    sessionId: str = Form(...),
    generate_pdf: bool = Form(default=True)
):
    """
    Universal Insurance Analysis API

    Supports:
    - Multiple PDFs and images
    - Auto, Health, or Life Insurance detection
    - Market price comparison
    - Value for money assessment
    - Recommendations
    - Better alternatives with savings

    Returns analysis results for each uploaded file.
    """
    try:
        # Analyze documents using service
        result = await policy_service.analyze_insurance_document(
            files=files,
            user_id=userId,
            session_id=sessionId,
            generate_pdf=generate_pdf
        )

        return {
            "success": result["successful"] > 0,
            **result
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in insurance analysis: {str(e)}")
        raise HTTPException(status_code=500, detail="Insurance analysis failed")


@router.get("/insurance-market-rates", tags=["Analysis"])
async def get_market_rates():
    """
    Get current insurance market rates and benchmarks

    Returns:
    - Average premiums by insurance type
    - Market trends
    - Coverage benchmarks
    """
    try:
        market_rates = await policy_service.get_market_rates()

        return {
            "success": True,
            "market_rates": market_rates
        }

    except Exception as e:
        logger.error(f"Error fetching market rates: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch market rates")


@router.post("/compare-insurance-policies", tags=["Analysis"])
async def compare_policies(
    policy_ids: List[str] = Form(...),
    userId: str = Form(...),
    sessionId: str = Form(...)
):
    """
    Compare multiple insurance policies

    Features:
    - Side-by-side comparison
    - Coverage analysis
    - Premium comparison
    - Recommendations

    Returns detailed comparison report.
    """
    try:
        if not MONGODB_AVAILABLE:
            raise HTTPException(status_code=503, detail="MongoDB service unavailable")

        # Compare policies using service
        comparison = await policy_service.compare_policies(
            policy_ids=policy_ids,
            user_id=userId,
            session_id=sessionId
        )

        return {
            "success": True,
            "comparison": comparison
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error comparing policies: {str(e)}")
        raise HTTPException(status_code=500, detail="Policy comparison failed")
