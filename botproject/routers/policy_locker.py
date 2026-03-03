"""
Policy Locker Router
API endpoints for Policy Locker, Family Management, Claims, and Emergency Services

All endpoints follow the specification in policy_locker_api_specification.md

Rate Limiting Applied (Redis-backed):
- File uploads: 5/minute
- Policy analysis: 10/minute
- Policy read: 30/minute
- Policy modify/delete: 5-10/minute
- Claims: 10/minute
- Family members: 10/minute
"""
import logging
from typing import Optional, List
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Query, Path, Request

from core.dependencies import get_session, store_session, MONGODB_AVAILABLE
from core.rate_limiter import limiter, RATE_LIMITS
from session_security.session_manager import session_manager
from services.policy_locker_service import policy_locker_service
from models.policy_locker import (
    # Request models
    BaseLockerRequest,
    GetSelfPoliciesRequest,
    AddFamilyMemberRequest,
    UpdateFamilyMemberRequest,
    AnalyzePolicyRequest,
    ConfirmPolicyRequest,
    InitiateClaimRequest,
    RenewPolicyRequest,
    SharePolicyRequest,
    # Flow request models
    StartAddPolicyFlowRequest,
    SelectOwnerRequest,
    SelectRelationshipRequest,
    EnterMemberDetailsRequest,
    SelectInsuranceTypeRequest,
    ReviewAnalysisRequest,
    # Enums
    InsuranceCategory,
    PolicyStatus,
    Gender,
    ShareMethod,
    ExportFormat,
    PolicyOwnerType,
    AddPolicyFlowStep
)
from pydantic import BaseModel
from typing import Dict, Any


# ==================== ADDITIONAL REQUEST MODELS ====================

class AddPolicyRequest(BaseLockerRequest):
    """Request to add a policy manually"""
    policyNumber: str
    provider: str
    category: str
    subType: Optional[str] = None
    policyHolderName: str
    startDate: str
    expiryDate: str
    premium: str
    premiumType: str = "Annual"
    coverageAmount: str
    idv: Optional[str] = None
    insuredMembers: int = 1
    keyBenefits: List[str] = []
    coverageGaps: List[str] = []
    exclusions: List[str] = []
    documents: List[str] = []
    insuredMemberNames: List[str] = []
    categorySpecificData: Optional[Dict[str, Any]] = None
    memberId: Optional[str] = None
    isForSelf: bool = True


class DeletePolicyRequest(BaseLockerRequest):
    """Request to delete a policy"""
    policyId: str


class DeleteFamilyMemberRequest(BaseLockerRequest):
    """Request to delete a family member"""
    memberId: str


class GetClaimStatusRequest(BaseLockerRequest):
    """Request to get claim status"""
    claimId: str

logger = logging.getLogger(__name__)

# Create router with prefix
router = APIRouter(prefix="/api/v1", tags=["Policy Locker"])


# ==================== HELPER FUNCTIONS ====================

def validate_session(session_id: str, user_id: int):
    """Validate session and return session data"""
    try:
        session_id, session_data, was_regenerated = session_manager.validate_and_regenerate_session(
            session_id,
            get_session,
            store_session
        )

        if not session_data or not session_data.get('active'):
            raise HTTPException(status_code=401, detail="Invalid or expired session")

        # Verify user_id matches
        session_user_id = session_data.get('user_id')
        if session_user_id and session_user_id != user_id:
            raise HTTPException(status_code=403, detail="User ID mismatch")

        return session_id, session_data, was_regenerated

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Session validation error: {e}")
        raise HTTPException(status_code=401, detail="Session validation failed")


# ==================== TEST ENDPOINT ====================

@router.get("/locker/test")
@limiter.limit(RATE_LIMITS["relaxed"])
async def test_policy_locker(request: Request):
    """Simple test endpoint to verify router is loaded"""
    return {"success": True, "message": "Policy Locker router is working!"}


# ==================== LOCKER APIs ====================

@router.get("/locker/policies/self")
@limiter.limit(RATE_LIMITS["policy_read"])
async def get_self_policies(
    request: Request,
    session_id: str = Query(..., description="User session ID"),
    user_id: int = Query(..., description="User ID"),
    category: Optional[str] = Query(None, description="Filter by category"),
    status: Optional[str] = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page")
):
    """
    Get all policies owned by the authenticated user

    Returns paginated list of policies with summary information.
    """
    try:
        session_id, session_data, was_regenerated = validate_session(session_id, user_id)

        result = await policy_locker_service.get_self_policies(
            user_id=user_id,
            category=category,
            status=status,
            page=page,
            limit=limit
        )

        return {
            "success": True,
            "data": result,
            "session_id": session_id,
            "session_regenerated": was_regenerated
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting self policies: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get policies: {str(e)}")


@router.get("/locker/summary/self")
@limiter.limit(RATE_LIMITS["policy_read"])
async def get_self_summary(
    request: Request,
    session_id: str = Query(..., description="User session ID"),
    user_id: int = Query(..., description="User ID")
):
    """
    Get aggregated summary for user's own policies

    Returns total policies count, coverage, and protection score.
    """
    try:
        session_id, session_data, was_regenerated = validate_session(session_id, user_id)

        result = await policy_locker_service.get_self_summary(user_id)

        return {
            "success": True,
            "data": result,
            "session_id": session_id,
            "session_regenerated": was_regenerated
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting self summary: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get summary: {str(e)}")


@router.get("/locker/portfolio-statistics")
@limiter.limit(RATE_LIMITS["policy_read"])
async def get_portfolio_statistics(
    request: Request,
    session_id: str = Query(..., description="User session ID"),
    user_id: int = Query(..., description="User ID")
):
    """
    Get category-wise breakdown of coverage

    Returns portfolio breakdown by insurance category with percentages.
    """
    try:
        session_id, session_data, was_regenerated = validate_session(session_id, user_id)

        result = await policy_locker_service.get_portfolio_statistics(user_id)

        return {
            "success": True,
            "data": result,
            "session_id": session_id,
            "session_regenerated": was_regenerated
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting portfolio statistics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")


# ==================== FAMILY APIs ====================

@router.get("/locker/family-members")
@limiter.limit(RATE_LIMITS["user_read"])
async def get_family_members(
    request: Request,
    session_id: str = Query(..., description="User session ID"),
    user_id: int = Query(..., description="User ID")
):
    """
    Fetch all family members with their policy summary

    Returns list of family members with their coverage details.
    """
    try:
        session_id, session_data, was_regenerated = validate_session(session_id, user_id)

        result = await policy_locker_service.get_family_members(user_id)

        return {
            "success": True,
            "data": result,
            "session_id": session_id,
            "session_regenerated": was_regenerated
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting family members: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get family members: {str(e)}")


@router.get("/locker/summary/family")
@limiter.limit(RATE_LIMITS["user_read"])
async def get_family_summary(
    request: Request,
    session_id: str = Query(..., description="User session ID"),
    user_id: int = Query(..., description="User ID")
):
    """
    Get aggregated summary for family policies

    Returns total family members, policies, and coverage.
    """
    try:
        session_id, session_data, was_regenerated = validate_session(session_id, user_id)

        result = await policy_locker_service.get_family_summary(user_id)

        return {
            "success": True,
            "data": result,
            "session_id": session_id,
            "session_regenerated": was_regenerated
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting family summary: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get family summary: {str(e)}")


@router.get("/locker/policies/family/{memberId}")
@limiter.limit(RATE_LIMITS["policy_read"])
async def get_family_member_policies(
    request: Request,
    memberId: str = Path(..., description="Family member ID"),
    session_id: str = Query(..., description="User session ID"),
    user_id: int = Query(..., description="User ID"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100)
):
    """
    Fetch all policies for a specific family member

    Returns paginated list of policies for the specified family member.
    """
    try:
        session_id, session_data, was_regenerated = validate_session(session_id, user_id)

        result = await policy_locker_service.get_family_member_policies(
            user_id=user_id,
            member_id=memberId,
            page=page,
            limit=limit
        )

        return {
            "success": True,
            "data": result,
            "session_id": session_id,
            "session_regenerated": was_regenerated
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting family member policies: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get policies: {str(e)}")


# ==================== MEMBER MANAGEMENT APIs ====================

@router.post("/members")
@limiter.limit(RATE_LIMITS["family_member"])
async def add_family_member(request: Request, member_request: AddFamilyMemberRequest):
    """
    Add a new family member

    Creates a new family member record for policy management.
    """
    try:
        session_id, session_data, was_regenerated = validate_session(
            member_request.session_id, member_request.user_id
        )

        result = await policy_locker_service.add_family_member(
            user_id=member_request.user_id,
            name=member_request.name,
            relationship=member_request.relationship,
            date_of_birth=member_request.dateOfBirth,
            gender=member_request.gender.value if member_request.gender else None
        )

        return {
            "success": True,
            "data": result,
            "session_id": session_id,
            "session_regenerated": was_regenerated
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding family member: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to add member: {str(e)}")


@router.get("/members/{memberId}")
@limiter.limit(RATE_LIMITS["user_read"])
async def get_member_details(
    request: Request,
    memberId: str = Path(..., description="Member ID"),
    session_id: str = Query(..., description="User session ID"),
    user_id: int = Query(..., description="User ID")
):
    """
    Fetch details of a specific family member

    Returns complete member profile with policy summary.
    """
    try:
        session_id, session_data, was_regenerated = validate_session(session_id, user_id)

        result = await policy_locker_service.get_member_details(user_id, memberId)

        return {
            "success": True,
            "data": result,
            "session_id": session_id,
            "session_regenerated": was_regenerated
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting member details: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get member: {str(e)}")


@router.put("/members/{memberId}")
@limiter.limit(RATE_LIMITS["user_write"])
async def update_family_member(
    request: Request,
    memberId: str = Path(..., description="Member ID"),
    update_request: UpdateFamilyMemberRequest = None
):
    """
    Update a family member's details

    Updates the specified fields for the family member.
    """
    try:
        if not update_request:
            raise HTTPException(status_code=400, detail="Request body required")

        session_id, session_data, was_regenerated = validate_session(
            update_request.session_id, update_request.user_id
        )

        result = await policy_locker_service.update_family_member(
            user_id=update_request.user_id,
            member_id=memberId,
            name=update_request.name,
            relationship=update_request.relationship,
            date_of_birth=update_request.dateOfBirth,
            gender=update_request.gender.value if update_request.gender else None
        )

        return {
            "success": True,
            "data": result,
            "session_id": session_id,
            "session_regenerated": was_regenerated
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating family member: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update member: {str(e)}")


@router.delete("/members/{memberId}")
@limiter.limit(RATE_LIMITS["user_delete"])
async def delete_family_member(
    request: Request,
    memberId: str = Path(..., description="Member ID"),
    session_id: str = Query(..., description="User session ID"),
    user_id: int = Query(..., description="User ID")
):
    """
    Delete a family member

    Permanently removes the family member and their associated policies.
    """
    try:
        session_id, session_data, was_regenerated = validate_session(session_id, user_id)

        result = await policy_locker_service.delete_family_member(user_id, memberId)

        return {
            "success": True,
            "data": result,
            "session_id": session_id,
            "session_regenerated": was_regenerated
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting family member: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete member: {str(e)}")


@router.get("/members/relationships")
@limiter.limit(RATE_LIMITS["public"])
async def get_relationships(request: Request):
    """
    Fetch available relationship types for family members

    Returns list of supported relationships.
    """
    try:
        result = await policy_locker_service.get_relationships()
        return {"success": True, "data": result}

    except Exception as e:
        logger.error(f"Error getting relationships: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get relationships: {str(e)}")


# ==================== POLICY CRUD APIs ====================

@router.post("/policies")
@limiter.limit(RATE_LIMITS["policy_modify"])
async def add_policy(request: Request, policy_request: AddPolicyRequest):
    """
    Add a new policy manually to the locker

    Creates a new policy record with the provided details.
    """
    try:
        session_id, session_data, was_regenerated = validate_session(
            policy_request.session_id, policy_request.user_id
        )

        policy_data = {
            "policyNumber": policy_request.policyNumber,
            "provider": policy_request.provider,
            "category": policy_request.category,
            "subType": policy_request.subType,
            "policyHolderName": policy_request.policyHolderName,
            "startDate": policy_request.startDate,
            "expiryDate": policy_request.expiryDate,
            "premium": policy_request.premium,
            "premiumType": policy_request.premiumType,
            "coverageAmount": policy_request.coverageAmount,
            "idv": policy_request.idv,
            "insuredMembers": policy_request.insuredMembers,
            "keyBenefits": policy_request.keyBenefits,
            "coverageGaps": policy_request.coverageGaps,
            "exclusions": policy_request.exclusions,
            "documents": policy_request.documents,
            "insuredMemberNames": policy_request.insuredMemberNames,
            "categorySpecificData": policy_request.categorySpecificData
        }

        result = await policy_locker_service.add_policy(
            user_id=policy_request.user_id,
            policy_data=policy_data,
            member_id=policy_request.memberId,
            is_for_self=policy_request.isForSelf
        )

        return {
            "success": True,
            "data": result,
            "session_id": session_id,
            "session_regenerated": was_regenerated
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding policy: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to add policy: {str(e)}")


@router.delete("/policies/{policyId}")
@limiter.limit(RATE_LIMITS["policy_delete"])
async def delete_policy(
    request: Request,
    policyId: str = Path(..., description="Policy ID"),
    session_id: str = Query(..., description="User session ID"),
    user_id: int = Query(..., description="User ID")
):
    """
    Delete a policy from the locker

    Permanently removes the policy record.
    """
    try:
        session_id, session_data, was_regenerated = validate_session(session_id, user_id)

        result = await policy_locker_service.delete_policy(user_id, policyId)

        return {
            "success": True,
            "data": result,
            "session_id": session_id,
            "session_regenerated": was_regenerated
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting policy: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete policy: {str(e)}")


# ==================== POLICY DETAILS APIs ====================

@router.get("/policies/{policyId}")
@limiter.limit(RATE_LIMITS["policy_read"])
async def get_policy_details(
    request: Request,
    policyId: str = Path(..., description="Policy ID"),
    session_id: str = Query(..., description="User session ID"),
    user_id: int = Query(..., description="User ID")
):
    """
    Get complete details of a specific policy

    Returns full policy information including category-specific data.
    """
    try:
        session_id, session_data, was_regenerated = validate_session(session_id, user_id)

        result = await policy_locker_service.get_policy_details(user_id, policyId)

        return {
            "success": True,
            "data": result,
            "session_id": session_id,
            "session_regenerated": was_regenerated
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting policy details: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get policy: {str(e)}")


@router.get("/policies/{policyId}/gap-analysis")
@limiter.limit(RATE_LIMITS["ai_processing"])
async def get_policy_gap_analysis(
    request: Request,
    policyId: str = Path(..., description="Policy ID"),
    session_id: str = Query(..., description="User session ID"),
    user_id: int = Query(..., description="User ID")
):
    """
    Fetch AI-generated gap analysis for a policy

    Returns coverage gaps, recommendations, and overall score.
    """
    try:
        session_id, session_data, was_regenerated = validate_session(session_id, user_id)

        result = await policy_locker_service.get_policy_gap_analysis(user_id, policyId)

        return {
            "success": True,
            "data": result,
            "session_id": session_id,
            "session_regenerated": was_regenerated
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting gap analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get analysis: {str(e)}")


@router.get("/policies/{policyId}/documents")
@limiter.limit(RATE_LIMITS["policy_read"])
async def get_policy_documents(
    request: Request,
    policyId: str = Path(..., description="Policy ID"),
    session_id: str = Query(..., description="User session ID"),
    user_id: int = Query(..., description="User ID")
):
    """
    Fetch list of documents associated with a policy

    Returns list of uploaded documents with download URLs.
    """
    try:
        session_id, session_data, was_regenerated = validate_session(session_id, user_id)

        result = await policy_locker_service.get_policy_documents(user_id, policyId)

        return {
            "success": True,
            "data": result,
            "session_id": session_id,
            "session_regenerated": was_regenerated
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting policy documents: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get documents: {str(e)}")


# ==================== UPLOAD & OCR APIs ====================

@router.post("/policies/upload")
@limiter.limit(RATE_LIMITS["file_upload"])
async def upload_policy_document(
    request: Request,
    file: UploadFile = File(..., description="Policy document (PDF, max 10MB)"),
    session_id: str = Form(..., description="User session ID"),
    user_id: int = Form(..., description="User ID"),
    memberId: Optional[str] = Form(None, description="Family member ID"),
    isForSelf: bool = Form(True, description="Whether policy is for self")
):
    """
    Upload policy document for OCR processing

    Accepts PDF documents up to 10MB for AI analysis.
    """
    try:
        session_id, session_data, was_regenerated = validate_session(session_id, user_id)

        # Validate file
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=415, detail="Only PDF files are supported")

        content = await file.read()
        if len(content) > 10 * 1024 * 1024:  # 10MB
            raise HTTPException(status_code=413, detail="File too large. Maximum size is 10MB")

        result = await policy_locker_service.upload_policy_document(
            user_id=user_id,
            file_content=content,
            filename=file.filename,
            member_id=memberId,
            is_for_self=isForSelf
        )

        return {
            "success": True,
            "data": result,
            "session_id": session_id,
            "session_regenerated": was_regenerated
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading document: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to upload: {str(e)}")


@router.post("/policies/analyze")
@limiter.limit(RATE_LIMITS["ai_processing"])
async def analyze_policy_document(request: Request, analyze_request: AnalyzePolicyRequest):
    """
    Trigger AI analysis on uploaded document

    Initiates OCR and AI analysis on the uploaded policy document.
    """
    try:
        session_id, session_data, was_regenerated = validate_session(
            analyze_request.session_id, analyze_request.user_id
        )

        result = await policy_locker_service.analyze_policy_document(
            user_id=analyze_request.user_id,
            upload_id=analyze_request.uploadId,
            member_id=analyze_request.memberId,
            member_name=analyze_request.memberName,
            member_dob=analyze_request.memberDOB,
            member_gender=analyze_request.memberGender.value if analyze_request.memberGender else None,
            relationship=analyze_request.relationship
        )

        return {
            "success": True,
            "data": result,
            "session_id": session_id,
            "session_regenerated": was_regenerated
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing document: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to analyze: {str(e)}")


@router.get("/policies/{analysisId}/analysis")
@limiter.limit(RATE_LIMITS["policy_read"])
async def get_analysis_result(
    request: Request,
    analysisId: str = Path(..., description="Analysis ID"),
    session_id: str = Query(..., description="User session ID"),
    user_id: int = Query(..., description="User ID")
):
    """
    Fetch AI analysis results

    Returns extracted policy data, protection score, and gap analysis.
    """
    try:
        session_id, session_data, was_regenerated = validate_session(session_id, user_id)

        result = await policy_locker_service.get_analysis_result(user_id, analysisId)

        return {
            "success": True,
            "data": result,
            "session_id": session_id,
            "session_regenerated": was_regenerated
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting analysis result: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get result: {str(e)}")


@router.post("/policies/{analysisId}/confirm")
@limiter.limit(RATE_LIMITS["policy_modify"])
async def confirm_policy_addition(
    request: Request,
    analysisId: str = Path(..., description="Analysis ID"),
    confirm_request: ConfirmPolicyRequest = None
):
    """
    Confirm and save analyzed policy to locker

    Saves the analyzed policy after user confirmation.
    """
    try:
        if confirm_request:
            session_id, session_data, was_regenerated = validate_session(
                confirm_request.session_id, confirm_request.user_id
            )
            user_id = confirm_request.user_id
            member_id = confirm_request.memberId
            corrections = confirm_request.corrections
        else:
            raise HTTPException(status_code=400, detail="Request body required")

        result = await policy_locker_service.confirm_policy_addition(
            user_id=user_id,
            analysis_id=analysisId,
            member_id=member_id,
            corrections=corrections
        )

        return {
            "success": True,
            "data": result,
            "session_id": session_id,
            "session_regenerated": was_regenerated
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error confirming policy: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to confirm: {str(e)}")


# ==================== ANALYSIS & RECOMMENDATIONS APIs ====================

@router.get("/policies/{policyId}/analysis-report")
@limiter.limit(RATE_LIMITS["ai_processing"])
async def get_analysis_report(
    request: Request,
    policyId: str = Path(..., description="Policy ID"),
    session_id: str = Query(..., description="User session ID"),
    user_id: int = Query(..., description="User ID")
):
    """
    Fetch comprehensive AI-powered analysis report

    Returns detailed insights and recommendations.
    """
    try:
        session_id, session_data, was_regenerated = validate_session(session_id, user_id)

        result = await policy_locker_service.get_analysis_report(user_id, policyId)

        return {
            "success": True,
            "data": result,
            "session_id": session_id,
            "session_regenerated": was_regenerated
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting analysis report: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get report: {str(e)}")


@router.get("/policies/{policyId}/recommendations")
@limiter.limit(RATE_LIMITS["ai_processing"])
async def get_policy_recommendations(
    request: Request,
    policyId: str = Path(..., description="Policy ID"),
    session_id: str = Query(..., description="User session ID"),
    user_id: int = Query(..., description="User ID")
):
    """
    Get personalized recommendations for policy enhancement

    Returns actionable recommendations to improve coverage.
    """
    try:
        session_id, session_data, was_regenerated = validate_session(session_id, user_id)

        result = await policy_locker_service.get_policy_recommendations(user_id, policyId)

        return {
            "success": True,
            "data": result,
            "session_id": session_id,
            "session_regenerated": was_regenerated
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting recommendations: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get recommendations: {str(e)}")


# ==================== EMERGENCY SERVICES APIs ====================

@router.get("/emergency/categories")
@limiter.limit(RATE_LIMITS["public"])
async def get_emergency_categories(request: Request):
    """
    Fetch available emergency service categories

    Returns list of emergency categories (medical, vehicle, other).
    """
    try:
        result = await policy_locker_service.get_emergency_categories()
        return {"success": True, "data": result}

    except Exception as e:
        logger.error(f"Error getting emergency categories: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get categories: {str(e)}")


@router.get("/emergency/contacts/{category}")
@limiter.limit(RATE_LIMITS["public"])
async def get_emergency_contacts(
    request: Request,
    category: str = Path(..., description="Emergency category (medical, vehicle, other)")
):
    """
    Fetch emergency contact numbers by category

    Returns list of emergency contacts for the specified category.
    """
    try:
        if category not in ["medical", "vehicle", "other"]:
            raise HTTPException(status_code=400, detail="Invalid category")

        result = await policy_locker_service.get_emergency_contacts(category)
        return {"success": True, "data": result}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting emergency contacts: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get contacts: {str(e)}")


# ==================== CLAIMS APIs ====================

@router.get("/claims/types")
@limiter.limit(RATE_LIMITS["policy_read"])
async def get_claim_types(
    request: Request,
    policyId: str = Query(..., description="Policy ID"),
    session_id: str = Query(..., description="User session ID"),
    user_id: int = Query(..., description="User ID")
):
    """
    Fetch available claim types based on policy category

    Returns list of claim types applicable for the policy.
    """
    try:
        session_id, session_data, was_regenerated = validate_session(session_id, user_id)

        result = await policy_locker_service.get_claim_types(policyId)

        return {
            "success": True,
            "data": result,
            "session_id": session_id,
            "session_regenerated": was_regenerated
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting claim types: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get claim types: {str(e)}")


@router.get("/claims/required-documents")
@limiter.limit(RATE_LIMITS["policy_read"])
async def get_required_documents(
    request: Request,
    policyId: str = Query(..., description="Policy ID"),
    claimType: str = Query(..., description="Type of claim"),
    session_id: str = Query(..., description="User session ID"),
    user_id: int = Query(..., description="User ID")
):
    """
    Fetch required documents for claim filing

    Returns list of documents needed to file a claim.
    """
    try:
        session_id, session_data, was_regenerated = validate_session(session_id, user_id)

        result = await policy_locker_service.get_required_documents(policyId, claimType)

        return {
            "success": True,
            "data": result,
            "session_id": session_id,
            "session_regenerated": was_regenerated
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting required documents: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get documents: {str(e)}")


@router.post("/claims/initiate")
@limiter.limit(RATE_LIMITS["policy_modify"])
async def initiate_claim(request: Request, claim_request: InitiateClaimRequest):
    """
    Start a new claim request

    Initiates a claim and returns claim number and next steps.
    """
    try:
        session_id, session_data, was_regenerated = validate_session(
            claim_request.session_id, claim_request.user_id
        )

        result = await policy_locker_service.initiate_claim(
            user_id=claim_request.user_id,
            policy_id=claim_request.policyId,
            claim_type=claim_request.claimType,
            description=claim_request.description,
            documents=claim_request.documents
        )

        return {
            "success": True,
            "data": result,
            "session_id": session_id,
            "session_regenerated": was_regenerated
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error initiating claim: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to initiate claim: {str(e)}")


@router.get("/claims/{claimId}/status")
@limiter.limit(RATE_LIMITS["policy_read"])
async def get_claim_status(
    request: Request,
    claimId: str = Path(..., description="Claim ID"),
    session_id: str = Query(..., description="User session ID"),
    user_id: int = Query(..., description="User ID")
):
    """
    Get status of a specific claim

    Returns current status and details of the claim.
    """
    try:
        session_id, session_data, was_regenerated = validate_session(session_id, user_id)

        result = await policy_locker_service.get_claim_status(user_id, claimId)

        return {
            "success": True,
            "data": result,
            "session_id": session_id,
            "session_regenerated": was_regenerated
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting claim status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get claim status: {str(e)}")


@router.get("/claims")
@limiter.limit(RATE_LIMITS["policy_read"])
async def get_user_claims(
    request: Request,
    session_id: str = Query(..., description="User session ID"),
    user_id: int = Query(..., description="User ID"),
    status: Optional[str] = Query(None, description="Filter by status")
):
    """
    Get all claims for the user

    Returns list of all claims with optional status filter.
    """
    try:
        session_id, session_data, was_regenerated = validate_session(session_id, user_id)

        result = await policy_locker_service.get_user_claims(user_id, status)

        return {
            "success": True,
            "data": result,
            "session_id": session_id,
            "session_regenerated": was_regenerated
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user claims: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get claims: {str(e)}")


# ==================== RENEWAL APIs ====================

@router.get("/policies/{policyId}/renewal-quote")
@limiter.limit(RATE_LIMITS["policy_read"])
async def get_renewal_quote(
    request: Request,
    policyId: str = Path(..., description="Policy ID"),
    session_id: str = Query(..., description="User session ID"),
    user_id: int = Query(..., description="User ID")
):
    """
    Fetch renewal quote with benefits and premium breakdown

    Returns detailed renewal quote with discounts and benefits.
    """
    try:
        session_id, session_data, was_regenerated = validate_session(session_id, user_id)

        result = await policy_locker_service.get_renewal_quote(user_id, policyId)

        return {
            "success": True,
            "data": result,
            "session_id": session_id,
            "session_regenerated": was_regenerated
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting renewal quote: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get quote: {str(e)}")


@router.post("/policies/{policyId}/renew")
@limiter.limit(RATE_LIMITS["policy_modify"])
async def renew_policy(
    request: Request,
    policyId: str = Path(..., description="Policy ID"),
    renew_request: RenewPolicyRequest = None
):
    """
    Initiate policy renewal

    Returns payment URL for completing renewal.
    """
    try:
        if renew_request:
            session_id, session_data, was_regenerated = validate_session(
                renew_request.session_id, renew_request.user_id
            )
            user_id = renew_request.user_id
            payment_method = renew_request.paymentMethod
            modifications = renew_request.modifications
        else:
            raise HTTPException(status_code=400, detail="Request body required")

        result = await policy_locker_service.renew_policy(
            user_id=user_id,
            policy_id=policyId,
            payment_method=payment_method,
            modifications=modifications
        )

        return {
            "success": True,
            "data": result,
            "session_id": session_id,
            "session_regenerated": was_regenerated
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error renewing policy: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to renew: {str(e)}")


# ==================== EXPORT & SHARE APIs ====================

@router.get("/policies/{policyId}/export/{format}")
@limiter.limit(RATE_LIMITS["policy_export"])
async def export_policy(
    request: Request,
    policyId: str = Path(..., description="Policy ID"),
    format: str = Path(..., description="Export format (pdf or xlsx)"),
    session_id: str = Query(..., description="User session ID"),
    user_id: int = Query(..., description="User ID")
):
    """
    Export policy report in specified format

    Returns download URL for the exported file.
    """
    try:
        if format not in ["pdf", "xlsx"]:
            raise HTTPException(status_code=400, detail="Invalid format. Use 'pdf' or 'xlsx'")

        session_id, session_data, was_regenerated = validate_session(session_id, user_id)

        result = await policy_locker_service.export_policy(user_id, policyId, format)

        return {
            "success": True,
            "data": result,
            "session_id": session_id,
            "session_regenerated": was_regenerated
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting policy: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to export: {str(e)}")


@router.post("/policies/{policyId}/share")
@limiter.limit(RATE_LIMITS["policy_modify"])
async def share_policy(
    request: Request,
    policyId: str = Path(..., description="Policy ID"),
    share_request: SharePolicyRequest = None
):
    """
    Generate shareable link or send via email

    Returns share URL or email confirmation.
    """
    try:
        if share_request:
            session_id, session_data, was_regenerated = validate_session(
                share_request.session_id, share_request.user_id
            )
            user_id = share_request.user_id
            method = share_request.method.value
            email = share_request.email
            expiry_hours = share_request.expiryHours
        else:
            raise HTTPException(status_code=400, detail="Request body required")

        result = await policy_locker_service.share_policy(
            user_id=user_id,
            policy_id=policyId,
            method=method,
            email=email,
            expiry_hours=expiry_hours
        )

        return {
            "success": True,
            "data": result,
            "session_id": session_id,
            "session_regenerated": was_regenerated
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sharing policy: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to share: {str(e)}")


# ==================== CONFIG & META APIs ====================

@router.get("/config/insurance-categories")
@limiter.limit(RATE_LIMITS["public"])
async def get_insurance_categories(request: Request):
    """
    Fetch all supported insurance categories and sub-types

    Returns list of categories with their sub-types.
    """
    try:
        result = await policy_locker_service.get_insurance_categories()
        return {"success": True, "data": result}

    except Exception as e:
        logger.error(f"Error getting insurance categories: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get categories: {str(e)}")


@router.get("/config/upload-config")
@limiter.limit(RATE_LIMITS["public"])
async def get_upload_config(request: Request):
    """
    Fetch upload constraints and supported formats

    Returns file upload configuration.
    """
    try:
        result = await policy_locker_service.get_upload_config()
        return {"success": True, "data": result}

    except Exception as e:
        logger.error(f"Error getting upload config: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get config: {str(e)}")


# ==================== ADD POLICY FLOW APIs ====================
# Flow Steps:
# For Self: SELECT_OWNER -> SELECT_INSURANCE_TYPE -> UPLOAD_DOCUMENT -> ANALYZING -> REVIEW_ANALYSIS -> CONFIRM_POLICY -> COMPLETED
# For Family: SELECT_OWNER -> SELECT_RELATIONSHIP -> ENTER_MEMBER_DETAILS -> SELECT_INSURANCE_TYPE -> UPLOAD_DOCUMENT -> ANALYZING -> REVIEW_ANALYSIS -> CONFIRM_POLICY -> COMPLETED

@router.post("/flow/add-policy/start")
@limiter.limit(RATE_LIMITS["policy_modify"])
async def start_add_policy_flow(request: Request, flow_request: StartAddPolicyFlowRequest):
    """
    Start a new Add Policy flow

    Initiates a guided flow for adding a new policy to the locker.
    Returns a flow ID to track the session.
    """
    try:
        session_id, session_data, was_regenerated = validate_session(
            flow_request.session_id, flow_request.user_id
        )

        result = await policy_locker_service.start_add_policy_flow(flow_request.user_id)

        return {
            "success": True,
            "data": result,
            "session_id": session_id,
            "session_regenerated": was_regenerated
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting add policy flow: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start flow: {str(e)}")


@router.post("/flow/add-policy/select-owner")
@limiter.limit(RATE_LIMITS["policy_modify"])
async def flow_select_owner(request: Request, owner_request: SelectOwnerRequest):
    """
    Step 1: Select policy owner type

    Select whether the policy is for self or for a family member/friend.
    """
    try:
        session_id, session_data, was_regenerated = validate_session(
            owner_request.session_id, owner_request.user_id
        )

        result = await policy_locker_service.select_owner_type(
            user_id=owner_request.user_id,
            flow_id=owner_request.flowId,
            owner_type=owner_request.ownerType.value
        )

        return {
            "success": True,
            "data": result,
            "session_id": session_id,
            "session_regenerated": was_regenerated
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error selecting owner type: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to select owner: {str(e)}")


@router.post("/flow/add-policy/select-relationship")
@limiter.limit(RATE_LIMITS["policy_modify"])
async def flow_select_relationship(request: Request, relationship_request: SelectRelationshipRequest):
    """
    Step 2 (Family): Select relationship type

    Select the relationship of the family member (spouse, son, daughter, etc.).
    Only applicable when owner type is 'family' or 'friend'.
    """
    try:
        session_id, session_data, was_regenerated = validate_session(
            relationship_request.session_id, relationship_request.user_id
        )

        result = await policy_locker_service.select_relationship(
            user_id=relationship_request.user_id,
            flow_id=relationship_request.flowId,
            relationship=relationship_request.relationship
        )

        return {
            "success": True,
            "data": result,
            "session_id": session_id,
            "session_regenerated": was_regenerated
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error selecting relationship: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to select relationship: {str(e)}")


@router.post("/flow/add-policy/enter-member-details")
@limiter.limit(RATE_LIMITS["policy_modify"])
async def flow_enter_member_details(request: Request, member_details_request: EnterMemberDetailsRequest):
    """
    Step 3 (Family): Enter member details

    Enter the family member's name, gender, and date of birth.
    Creates a new family member record if one doesn't exist.
    """
    try:
        session_id, session_data, was_regenerated = validate_session(
            member_details_request.session_id, member_details_request.user_id
        )

        result = await policy_locker_service.enter_member_details(
            user_id=member_details_request.user_id,
            flow_id=member_details_request.flowId,
            name=member_details_request.name,
            gender=member_details_request.gender.value,
            date_of_birth=member_details_request.dateOfBirth
        )

        return {
            "success": True,
            "data": result,
            "session_id": session_id,
            "session_regenerated": was_regenerated
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error entering member details: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to enter details: {str(e)}")


@router.post("/flow/add-policy/select-insurance-type")
@limiter.limit(RATE_LIMITS["policy_modify"])
async def flow_select_insurance_type(request: Request, insurance_type_request: SelectInsuranceTypeRequest):
    """
    Step 4: Select insurance type/category

    Select the insurance category (health, life, motor, etc.) and optionally sub-type.
    """
    try:
        session_id, session_data, was_regenerated = validate_session(
            insurance_type_request.session_id, insurance_type_request.user_id
        )

        result = await policy_locker_service.select_insurance_type(
            user_id=insurance_type_request.user_id,
            flow_id=insurance_type_request.flowId,
            category=insurance_type_request.category.value,
            sub_type=insurance_type_request.subType
        )

        return {
            "success": True,
            "data": result,
            "session_id": session_id,
            "session_regenerated": was_regenerated
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error selecting insurance type: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to select type: {str(e)}")


@router.post("/flow/add-policy/upload")
@limiter.limit(RATE_LIMITS["file_upload"])
async def flow_upload_document(
    request: Request,
    file: UploadFile = File(..., description="Policy document (PDF, max 10MB)"),
    session_id: str = Form(..., description="User session ID"),
    user_id: int = Form(..., description="User ID"),
    flowId: str = Form(..., description="Flow session ID")
):
    """
    Step 5: Upload policy document

    Upload the insurance policy document (PDF) for AI analysis.
    Automatically triggers OCR and policy extraction.
    """
    try:
        session_id, session_data, was_regenerated = validate_session(session_id, user_id)

        # Validate file
        if not file.filename.lower().endswith(('.pdf', '.jpg', '.jpeg', '.png')):
            raise HTTPException(status_code=415, detail="Only PDF and image files are supported")

        content = await file.read()
        if len(content) > 10 * 1024 * 1024:  # 10MB
            raise HTTPException(status_code=413, detail="File too large. Maximum size is 10MB")

        result = await policy_locker_service.flow_upload_document(
            user_id=user_id,
            flow_id=flowId,
            file_content=content,
            filename=file.filename
        )

        return {
            "success": True,
            "data": result,
            "session_id": session_id,
            "session_regenerated": was_regenerated
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading document in flow: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to upload: {str(e)}")


@router.get("/flow/add-policy/{flowId}/analysis-status")
@limiter.limit(RATE_LIMITS["policy_read"])
async def flow_get_analysis_status(
    request: Request,
    flowId: str = Path(..., description="Flow session ID"),
    session_id: str = Query(..., description="User session ID"),
    user_id: int = Query(..., description="User ID")
):
    """
    Step 6: Check analysis status

    Poll this endpoint to check if the AI analysis is complete.
    Returns extracted policy data when analysis is done.
    """
    try:
        session_id, session_data, was_regenerated = validate_session(session_id, user_id)

        result = await policy_locker_service.get_flow_analysis_status(user_id, flowId)

        return {
            "success": True,
            "data": result,
            "session_id": session_id,
            "session_regenerated": was_regenerated
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting analysis status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")


@router.post("/flow/add-policy/confirm")
@limiter.limit(RATE_LIMITS["policy_modify"])
async def flow_confirm_policy(request: Request, review_request: ReviewAnalysisRequest):
    """
    Step 7 & 8: Review and confirm policy addition

    Review the extracted policy data, optionally provide corrections,
    and confirm to add the policy to the locker.
    """
    try:
        session_id, session_data, was_regenerated = validate_session(
            review_request.session_id, review_request.user_id
        )

        result = await policy_locker_service.review_and_confirm_policy(
            user_id=review_request.user_id,
            flow_id=review_request.flowId,
            corrections=review_request.corrections
        )

        return {
            "success": True,
            "data": result,
            "session_id": session_id,
            "session_regenerated": was_regenerated
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error confirming policy: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to confirm: {str(e)}")


@router.get("/flow/add-policy/{flowId}")
@limiter.limit(RATE_LIMITS["policy_read"])
async def flow_get_state(
    request: Request,
    flowId: str = Path(..., description="Flow session ID"),
    session_id: str = Query(..., description="User session ID"),
    user_id: int = Query(..., description="User ID")
):
    """
    Get current flow state

    Returns the current state of an Add Policy flow session.
    Useful for resuming an interrupted flow.
    """
    try:
        session_id, session_data, was_regenerated = validate_session(session_id, user_id)

        result = await policy_locker_service.get_flow_state(user_id, flowId)

        return {
            "success": True,
            "data": result,
            "session_id": session_id,
            "session_regenerated": was_regenerated
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting flow state: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get flow: {str(e)}")


@router.delete("/flow/add-policy/{flowId}")
@limiter.limit(RATE_LIMITS["policy_delete"])
async def flow_cancel(
    request: Request,
    flowId: str = Path(..., description="Flow session ID"),
    session_id: str = Query(..., description="User session ID"),
    user_id: int = Query(..., description="User ID")
):
    """
    Cancel flow

    Cancel an in-progress Add Policy flow session.
    """
    try:
        session_id, session_data, was_regenerated = validate_session(session_id, user_id)

        result = await policy_locker_service.cancel_flow(user_id, flowId)

        return {
            "success": True,
            "data": result,
            "session_id": session_id,
            "session_regenerated": was_regenerated
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling flow: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to cancel: {str(e)}")
