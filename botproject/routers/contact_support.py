"""
Contact Support API Router
Handles contact support endpoints for mobile app and admin dashboard

Rate Limiting Applied (Redis-backed):
- Public endpoints: 60/minute per IP
- Admin endpoints: 10/minute per IP
"""
from fastapi import APIRouter, HTTPException, Header, Query, Request
from typing import Optional
import logging
from datetime import datetime

from models.contact_support import (
    ContactSupportCreateRequest,
    ContactSupportResponse,
    ContactSupportHistoryResponse,
    ContactSupportData
)
from services.contact_support_service import get_contact_support_service
from core.rate_limiter import limiter, RATE_LIMITS

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Contact Support"])


# ============= Mobile App Endpoint =============

@router.get(
    "/support/contact",
    response_model=ContactSupportResponse,
    summary="Get Contact Support Details (Mobile App)",
    description="Fetches the contact support details to be displayed in the app's Contact Support screen."
)
@limiter.limit(RATE_LIMITS["public"])
async def get_contact_support(
    request: Request,
    authorization: Optional[str] = Header(None, description="Bearer token for authentication")
):
    """
    Get contact support details for mobile app

    Returns contact information including:
    - Email support details
    - Phone support details
    - WhatsApp support (if enabled)
    - Live chat (if enabled)
    - Social media links
    - Office address (if enabled)
    """
    try:
        # Note: Authorization validation can be added here if needed
        # For now, we're allowing access to contact support without strict auth
        # as it's a public information endpoint

        service = get_contact_support_service()
        data = service.get_contact_support()

        if not data:
            raise HTTPException(
                status_code=404,
                detail={
                    "success": False,
                    "message": "Contact support details not configured",
                    "error": "No contact details found"
                }
            )

        return {
            "success": True,
            "message": "Contact support details fetched successfully",
            "data": data
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching contact support: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "message": "Failed to fetch contact support details",
                "error": "Internal server error"
            }
        )


# ============= Admin Dashboard Endpoints =============

@router.post(
    "/admin/support/contact",
    response_model=ContactSupportResponse,
    summary="Create/Update Contact Support Details (Admin)",
    description="Creates or updates the contact support details from admin dashboard/panel."
)
@limiter.limit(RATE_LIMITS["admin_write"])
async def create_or_update_contact_support(
    request: Request,
    support_request: ContactSupportCreateRequest,
    authorization: Optional[str] = Header(None, description="Bearer token with admin privileges"),
    x_admin_id: Optional[str] = Header(None, alias="X-Admin-Id", description="Admin user ID for audit trail"),
    x_admin_email: Optional[str] = Header(None, alias="X-Admin-Email", description="Admin email for audit"),
    x_admin_name: Optional[str] = Header(None, alias="X-Admin-Name", description="Admin name for audit")
):
    """
    Create or update contact support details

    Requires admin authentication. All changes are logged for audit trail.
    """
    try:
        # Validate admin ID is provided
        if not x_admin_id:
            raise HTTPException(
                status_code=400,
                detail={
                    "success": False,
                    "message": "Admin ID required",
                    "error": "X-Admin-Id header is required"
                }
            )

        # TODO: Add proper admin authentication validation here
        # For now, we just require the admin ID header

        service = get_contact_support_service()

        # Convert Pydantic model to dict, excluding None values for nested optionals
        data = support_request.model_dump(exclude_none=False)

        # Handle optional nested models
        if support_request.whatsapp:
            data['whatsapp'] = support_request.whatsapp.model_dump()
        if support_request.live_chat:
            data['live_chat'] = support_request.live_chat.model_dump()
        if support_request.social_media:
            data['social_media'] = support_request.social_media.model_dump()
        if support_request.office_address:
            data['office_address'] = support_request.office_address.model_dump()

        result = service.create_or_update_contact_support(
            data=data,
            admin_id=x_admin_id,
            admin_email=x_admin_email,
            admin_name=x_admin_name
        )

        return {
            "success": True,
            "message": "Contact support details updated successfully",
            "data": result
        }

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "message": "Validation failed",
                "error": str(e)
            }
        )
    except Exception as e:
        logger.error(f"Error updating contact support: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "message": "Failed to update contact support details",
                "error": "Internal server error"
            }
        )


@router.put(
    "/admin/support/contact",
    response_model=ContactSupportResponse,
    summary="Update Contact Support Details (Admin)",
    description="Updates the contact support details from admin dashboard/panel (same as POST)."
)
@limiter.limit(RATE_LIMITS["admin_write"])
async def update_contact_support(
    request: Request,
    support_request: ContactSupportCreateRequest,
    authorization: Optional[str] = Header(None, description="Bearer token with admin privileges"),
    x_admin_id: Optional[str] = Header(None, alias="X-Admin-Id", description="Admin user ID for audit trail"),
    x_admin_email: Optional[str] = Header(None, alias="X-Admin-Email", description="Admin email for audit"),
    x_admin_name: Optional[str] = Header(None, alias="X-Admin-Name", description="Admin name for audit")
):
    """
    Update contact support details (alias for POST)
    """
    return await create_or_update_contact_support(
        request=request,
        support_request=support_request,
        authorization=authorization,
        x_admin_id=x_admin_id,
        x_admin_email=x_admin_email,
        x_admin_name=x_admin_name
    )


@router.get(
    "/admin/support/contact/history",
    response_model=ContactSupportHistoryResponse,
    summary="Get Contact Support History (Admin)",
    description="Fetches the audit history of contact support detail changes."
)
@limiter.limit(RATE_LIMITS["admin_read"])
async def get_contact_support_history(
    request: Request,
    authorization: Optional[str] = Header(None, description="Bearer token with admin privileges"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Records per page")
):
    """
    Get contact support change history

    Returns paginated list of all changes made to contact support details,
    including who made the change and what was changed.
    """
    try:
        # TODO: Add proper admin authentication validation here

        service = get_contact_support_service()
        result = service.get_contact_support_history(page=page, limit=limit)

        return {
            "success": True,
            "message": "History fetched successfully",
            "data": result
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching contact support history: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "message": "Failed to fetch history",
                "error": "Internal server error"
            }
        )


# ============= Additional Utility Endpoints =============

@router.delete(
    "/admin/support/contact",
    summary="Delete Contact Support Details (Admin)",
    description="Deletes all contact support details. Use with caution."
)
@limiter.limit(RATE_LIMITS["admin_delete"])
async def delete_contact_support(
    request: Request,
    authorization: Optional[str] = Header(None, description="Bearer token with admin privileges"),
    x_admin_id: Optional[str] = Header(None, alias="X-Admin-Id", description="Admin user ID for audit trail"),
    confirm: bool = Query(False, description="Confirmation flag - must be true to delete")
):
    """
    Delete contact support details

    This will remove all contact support configuration.
    Requires explicit confirmation.
    """
    try:
        if not x_admin_id:
            raise HTTPException(
                status_code=400,
                detail={
                    "success": False,
                    "message": "Admin ID required",
                    "error": "X-Admin-Id header is required"
                }
            )

        if not confirm:
            raise HTTPException(
                status_code=400,
                detail={
                    "success": False,
                    "message": "Deletion requires confirmation",
                    "error": "Set confirm=true to proceed with deletion"
                }
            )

        service = get_contact_support_service()

        if not service.mongodb_manager:
            raise HTTPException(
                status_code=503,
                detail={
                    "success": False,
                    "message": "Service unavailable",
                    "error": "MongoDB not available"
                }
            )

        # Delete the contact support document
        result = service.mongodb_manager.contact_support_collection.delete_many({})

        logger.info(f"Contact support deleted by admin: {x_admin_id}, deleted_count: {result.deleted_count}")

        return {
            "success": True,
            "message": "Contact support details deleted successfully",
            "deleted_count": result.deleted_count
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting contact support: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "message": "Failed to delete contact support details",
                "error": "Internal server error"
            }
        )
