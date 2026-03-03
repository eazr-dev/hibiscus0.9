"""
CEO Note Router
Dynamic CEO welcome note for first-time users, managed from admin panel.

Features:
- GET /ceo-note: Get active CEO note (checks if user has seen it)
- POST /admin/ceo-note: Create/update CEO note (admin only)
- GET /admin/ceo-note: Get current CEO note config (admin only)
- POST /ceo-note/mark-seen: Mark note as seen by user

Content Format:
- Supports Markdown format from rich text editor
- Admin panel can use editors like TipTap, Quill, or Editor.js that export MD

Rate Limiting Applied (Redis-backed):
- User read: 30/minute per IP
- Admin write: 10/minute per IP
"""
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Header, Request, Body
from pydantic import BaseModel, Field

from core.rate_limiter import limiter, RATE_LIMITS

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(tags=["CEO Note"])


# ==================== PYDANTIC MODELS ====================

class CEONoteContent(BaseModel):
    """CEO Note content model for admin input"""
    title: str = Field(..., min_length=1, max_length=100, description="Note title (e.g., 'Welcome to Eazr!')")
    content: str = Field(..., min_length=1, max_length=5000, description="Note content in Markdown format")
    ceoName: str = Field(default="Founder & CEO", max_length=100, description="CEO name to display")
    ceoDesignation: str = Field(default="Founder & CEO", max_length=100, description="CEO designation")
    ceoImageUrl: Optional[str] = Field(default=None, description="CEO profile image URL (optional)")
    isEnabled: bool = Field(default=True, description="Whether the note is active")
    showOnlyOnce: bool = Field(default=True, description="Show only once per user (recommended)")
    targetAudience: str = Field(default="new_users", description="Target: 'new_users', 'all_users', or 'returning_users'")


class MarkSeenRequest(BaseModel):
    """Request to mark CEO note as seen"""
    userId: int = Field(..., description="The user ID")
    noteId: str = Field(..., description="The CEO note ID that was seen")


# ==================== DEFAULT CEO NOTE ====================
# Fallback if no note is configured in database

DEFAULT_CEO_NOTE = {
    "noteId": "default_ceo_note_v1",
    "title": "Welcome to Eazr! 🎉",
    "content": """### Hi there! 👋

I'm thrilled to welcome you to **Eazr** – your personal insurance companion.

We built Eazr because we believe managing insurance shouldn't be complicated. Whether you're tracking your policies, understanding your coverage gaps, or just want peace of mind knowing everything is in one place – we've got you covered.

**Here's what you can do:**
- 📄 Upload and organize all your insurance policies
- 🔍 Get AI-powered analysis of your coverage
- 🎯 Identify gaps in your protection
- 🎁 Unlock rewards by adding more policies

If you ever have questions or feedback, I'd love to hear from you. Just reach out through the app.

Welcome aboard! 🚀

*– Team Eazr*
""",
    "ceoName": "Team Eazr",
    "ceoDesignation": "Founder & CEO",
    "ceoImageUrl": None,
    "isEnabled": True,
    "showOnlyOnce": True,
    "targetAudience": "all_users",  # Changed from "new_users" to show to ALL users
    "version": 1
}


# ==================== HELPER FUNCTIONS ====================

def get_db():
    """Get MongoDB database connection"""
    from database_storage.mongodb_chat_manager import mongodb_chat_manager
    if mongodb_chat_manager is None or mongodb_chat_manager.db is None:
        raise HTTPException(
            status_code=503,
            detail={
                "success": False,
                "error_code": "DB_5001",
                "message": "Database connection unavailable"
            }
        )
    return mongodb_chat_manager.db


async def get_user_id_from_token(authorization: Optional[str], access_token: Optional[str]) -> Optional[int]:
    """Extract user ID from authorization token"""
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization.replace("Bearer ", "")
    elif access_token:
        token = access_token

    if not token:
        return None

    try:
        from core.auth import decode_token
        payload = decode_token(token)
        return payload.get("user_id") or payload.get("sub")
    except Exception as e:
        logger.warning(f"Failed to decode token: {e}")
        return None


# ==================== USER ENDPOINTS ====================

@router.get("/ceo-note")
@limiter.limit(RATE_LIMITS["user_read"])
async def get_ceo_note(
    request: Request,
    userId: Optional[int] = None,
    authorization: Optional[str] = Header(None, alias="Authorization"),
    access_token: Optional[str] = Header(None, alias="access-token")
):
    """
    Get CEO Note for Display

    Returns the active CEO note if:
    1. CEO note is enabled
    2. User hasn't seen it yet (if showOnlyOnce is true)
    3. User matches target audience

    **Query Parameters:**
    - userId: User ID (optional, can also be extracted from token)

    **Headers:**
    - Authorization: Bearer {token}
    - access-token: {token} (alternative)

    **Returns:**
    - shouldShow: Whether to display the note
    - note: CEO note content (if shouldShow is true)

    **Content Format:**
    - content field is in Markdown format
    - Use a Markdown renderer on the app side (e.g., react-native-markdown-display)
    """
    try:
        db = get_db()

        # Get user ID from token or query param
        user_id = userId
        if not user_id:
            user_id = await get_user_id_from_token(authorization, access_token)

        # Get active CEO note from database
        ceo_notes_collection = db['ceo_notes']
        active_note = ceo_notes_collection.find_one({
            "isEnabled": True,
            "isDeleted": {"$ne": True}
        }, sort=[("created_at", -1)])  # Get most recent active note

        # If no note exists, create default note in database (one-time setup)
        if not active_note:
            now = datetime.utcnow()
            default_note_doc = {
                "title": DEFAULT_CEO_NOTE["title"],
                "content": DEFAULT_CEO_NOTE["content"],
                "contentFormat": "markdown",
                "ceoName": DEFAULT_CEO_NOTE["ceoName"],
                "ceoDesignation": DEFAULT_CEO_NOTE["ceoDesignation"],
                "ceoImageUrl": DEFAULT_CEO_NOTE.get("ceoImageUrl"),
                "isEnabled": DEFAULT_CEO_NOTE["isEnabled"],
                "showOnlyOnce": DEFAULT_CEO_NOTE["showOnlyOnce"],
                "targetAudience": DEFAULT_CEO_NOTE["targetAudience"],
                "version": 1,
                "isDeleted": False,
                "created_at": now,
                "updated_at": now
            }
            result = ceo_notes_collection.insert_one(default_note_doc)
            logger.info(f"Auto-created default CEO note with ID: {result.inserted_id}")

            # Fetch the inserted note
            active_note = ceo_notes_collection.find_one({"_id": result.inserted_id})

        # Set noteId from MongoDB _id
        active_note["noteId"] = str(active_note.get("_id", ""))

        # Check if note is enabled
        if not active_note.get("isEnabled", True):
            return {
                "success": True,
                "data": {
                    "shouldShow": False,
                    "reason": "CEO note is disabled"
                }
            }

        # Check if user has already seen this note (if showOnlyOnce is true)
        should_show = True
        not_show_reason = None

        if user_id and active_note.get("showOnlyOnce", True):
            ceo_note_views_collection = db['ceo_note_views']
            existing_view = ceo_note_views_collection.find_one({
                "user_id": int(user_id),
                "note_id": active_note["noteId"]
            })

            if existing_view:
                should_show = False
                not_show_reason = "User has already seen this note"
                logger.info(f"User {user_id} has already seen CEO note {active_note['noteId']}")

        # Check target audience (only if still showing)
        if should_show:
            target_audience = active_note.get("targetAudience", "all_users")
            if user_id and target_audience != "all_users":
                # Check if user is new (no policies) or returning (has policies)
                policy_count = db['policy_analysis'].count_documents({
                    "user_id": int(user_id),
                    "$or": [
                        {"isDeleted": {"$exists": False}},
                        {"isDeleted": False}
                    ]
                })

                is_new_user = policy_count == 0

                if target_audience == "new_users" and not is_new_user:
                    should_show = False
                    not_show_reason = "Note is for new users only"
                elif target_audience == "returning_users" and is_new_user:
                    should_show = False
                    not_show_reason = "Note is for returning users only"

        # Build response
        if should_show:
            response_note = {
                "noteId": active_note["noteId"],
                "title": active_note.get("title", "Welcome!"),
                "content": active_note.get("content", ""),  # Markdown content
                "contentFormat": "markdown",  # Indicate format for app
                "ceoName": active_note.get("ceoName", "Team Eazr"),
                "ceoDesignation": active_note.get("ceoDesignation", "Founder & CEO"),
                "ceoImageUrl": active_note.get("ceoImageUrl"),
                "version": active_note.get("version", 1)
            }

            return {
                "success": True,
                "data": {
                    "shouldShow": True,
                    "note": response_note
                }
            }
        else:
            return {
                "success": True,
                "data": {
                    "shouldShow": False,
                    "reason": not_show_reason or ("Note not applicable" if not user_id else "Unknown reason")
                }
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting CEO note: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error_code": "SRV_5001",
                "message": "Failed to get CEO note"
            }
        )


@router.post("/ceo-note/mark-seen")
@limiter.limit(RATE_LIMITS["user_write"])
async def mark_ceo_note_seen(
    request: Request,
    body: MarkSeenRequest
):
    """
    Mark CEO Note as Seen

    Call this endpoint after the user dismisses/closes the CEO note.
    This ensures the note won't be shown again (if showOnlyOnce is enabled).

    **Request Body (JSON):**
    ```json
    {
        "userId": 343,
        "noteId": "678abc123def456..."
    }
    ```

    **Returns:**
    - success: Whether the operation succeeded
    """
    try:
        db = get_db()

        # Get user ID from request body
        user_id = body.userId

        # Record the view
        ceo_note_views_collection = db['ceo_note_views']

        # Upsert to avoid duplicates
        result = ceo_note_views_collection.update_one(
            {
                "user_id": int(user_id),
                "note_id": body.noteId
            },
            {
                "$set": {
                    "user_id": int(user_id),
                    "note_id": body.noteId,
                    "seen_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                },
                "$setOnInsert": {
                    "created_at": datetime.utcnow()
                }
            },
            upsert=True
        )

        logger.info(f"CEO note {body.noteId} marked as seen by user {user_id}")

        return {
            "success": True,
            "message": "CEO note marked as seen"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking CEO note as seen: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error_code": "SRV_5001",
                "message": "Failed to mark CEO note as seen"
            }
        )


# ==================== ADMIN ENDPOINTS ====================

@router.get("/admin/ceo-note")
@limiter.limit(RATE_LIMITS["admin_read"])
async def get_ceo_note_admin(
    request: Request,
    authorization: Optional[str] = Header(None, alias="Authorization"),
    access_token: Optional[str] = Header(None, alias="access-token")
):
    """
    Get CEO Note Configuration (Admin)

    Returns the current CEO note configuration for admin panel editing.

    **Headers:**
    - Authorization: Bearer {token} (admin token required)

    **Returns:**
    - Current CEO note configuration
    - Statistics (views, unique users)
    """
    try:
        db = get_db()

        # TODO: Add admin authentication check
        # For now, allow access (implement proper admin check later)

        # Get active CEO note
        ceo_notes_collection = db['ceo_notes']
        active_note = ceo_notes_collection.find_one({
            "isDeleted": {"$ne": True}
        }, sort=[("created_at", -1)])

        # Get statistics
        stats = {
            "totalViews": 0,
            "uniqueUsers": 0
        }

        if active_note:
            note_id = str(active_note.get("_id", ""))
            ceo_note_views_collection = db['ceo_note_views']

            stats["totalViews"] = ceo_note_views_collection.count_documents({
                "note_id": note_id
            })
            stats["uniqueUsers"] = len(ceo_note_views_collection.distinct("user_id", {
                "note_id": note_id
            }))

        # Use default if none configured - also insert it into DB for easier management
        if not active_note:
            # Insert default note into database
            now = datetime.utcnow()
            default_note_doc = {
                "title": DEFAULT_CEO_NOTE["title"],
                "content": DEFAULT_CEO_NOTE["content"],
                "contentFormat": "markdown",
                "ceoName": DEFAULT_CEO_NOTE["ceoName"],
                "ceoDesignation": DEFAULT_CEO_NOTE["ceoDesignation"],
                "ceoImageUrl": DEFAULT_CEO_NOTE.get("ceoImageUrl"),
                "isEnabled": DEFAULT_CEO_NOTE["isEnabled"],
                "showOnlyOnce": DEFAULT_CEO_NOTE["showOnlyOnce"],
                "targetAudience": DEFAULT_CEO_NOTE["targetAudience"],
                "version": 1,
                "isDeleted": False,
                "created_at": now,
                "updated_at": now
            }
            result = ceo_notes_collection.insert_one(default_note_doc)
            logger.info(f"Created default CEO note with ID: {result.inserted_id}")

            note_config = {
                "noteId": str(result.inserted_id),
                "title": DEFAULT_CEO_NOTE["title"],
                "content": DEFAULT_CEO_NOTE["content"],
                "contentFormat": "markdown",
                "ceoName": DEFAULT_CEO_NOTE["ceoName"],
                "ceoDesignation": DEFAULT_CEO_NOTE["ceoDesignation"],
                "ceoImageUrl": DEFAULT_CEO_NOTE.get("ceoImageUrl"),
                "isEnabled": DEFAULT_CEO_NOTE["isEnabled"],
                "showOnlyOnce": DEFAULT_CEO_NOTE["showOnlyOnce"],
                "targetAudience": DEFAULT_CEO_NOTE["targetAudience"],
                "version": 1,
                "isDefault": True,
                "createdAt": now.isoformat() + "Z",
                "updatedAt": now.isoformat() + "Z"
            }
        else:
            note_config = {
                "noteId": str(active_note.get("_id", "")),
                "title": active_note.get("title", ""),
                "content": active_note.get("content", ""),
                "contentFormat": "markdown",
                "ceoName": active_note.get("ceoName", ""),
                "ceoDesignation": active_note.get("ceoDesignation", ""),
                "ceoImageUrl": active_note.get("ceoImageUrl"),
                "isEnabled": active_note.get("isEnabled", True),
                "showOnlyOnce": active_note.get("showOnlyOnce", True),
                "targetAudience": active_note.get("targetAudience", "new_users"),
                "version": active_note.get("version", 1),
                "isDefault": False,
                "createdAt": active_note.get("created_at").isoformat() + "Z" if active_note.get("created_at") else None,
                "updatedAt": active_note.get("updated_at").isoformat() + "Z" if active_note.get("updated_at") else None
            }

        return {
            "success": True,
            "data": {
                "note": note_config,
                "statistics": stats,
                "supportedFormats": ["markdown"],
                "editorRecommendation": "Use TipTap, Quill, or Editor.js with Markdown export"
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting CEO note config: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error_code": "SRV_5001",
                "message": "Failed to get CEO note configuration"
            }
        )


@router.post("/admin/ceo-note")
@limiter.limit(RATE_LIMITS["admin_write"])
async def create_or_update_ceo_note(
    request: Request,
    note: CEONoteContent,
    authorization: Optional[str] = Header(None, alias="Authorization"),
    access_token: Optional[str] = Header(None, alias="access-token")
):
    """
    Create or Update CEO Note (Admin)

    Creates a new CEO note or updates the existing one.
    Previous notes are soft-deleted (kept for history).

    **Request Body (JSON):**
    ```json
    {
        "title": "Welcome to Eazr! 🎉",
        "content": "### Hi there!\\n\\nWelcome message in **Markdown** format...",
        "ceoName": "John Doe",
        "ceoDesignation": "Founder & CEO",
        "ceoImageUrl": "https://example.com/ceo.jpg",
        "isEnabled": true,
        "showOnlyOnce": true,
        "targetAudience": "new_users"
    }
    ```

    **Content Format:**
    - Use Markdown syntax for formatting
    - Supports: headers, bold, italic, lists, links, etc.
    - Rich text editors like TipTap/Quill can export to Markdown

    **Target Audience Options:**
    - "new_users": Only users with no uploaded policies
    - "returning_users": Only users with at least one policy
    - "all_users": All users regardless of policy count

    **Headers:**
    - Authorization: Bearer {token} (admin token required)

    **Returns:**
    - Created/updated CEO note with noteId
    """
    try:
        db = get_db()

        # TODO: Add admin authentication check
        # For now, allow access (implement proper admin check later)

        ceo_notes_collection = db['ceo_notes']

        # Soft-delete existing active notes
        ceo_notes_collection.update_many(
            {"isDeleted": {"$ne": True}},
            {
                "$set": {
                    "isDeleted": True,
                    "deleted_at": datetime.utcnow()
                }
            }
        )

        # Get current version number
        last_note = ceo_notes_collection.find_one(
            sort=[("version", -1)]
        )
        new_version = (last_note.get("version", 0) + 1) if last_note else 1

        # Create new note
        now = datetime.utcnow()
        new_note = {
            "title": note.title,
            "content": note.content,
            "contentFormat": "markdown",
            "ceoName": note.ceoName,
            "ceoDesignation": note.ceoDesignation,
            "ceoImageUrl": note.ceoImageUrl,
            "isEnabled": note.isEnabled,
            "showOnlyOnce": note.showOnlyOnce,
            "targetAudience": note.targetAudience,
            "version": new_version,
            "isDeleted": False,
            "created_at": now,
            "updated_at": now
        }

        result = ceo_notes_collection.insert_one(new_note)
        note_id = str(result.inserted_id)

        logger.info(f"CEO note created/updated: {note_id}, version: {new_version}")

        return {
            "success": True,
            "data": {
                "noteId": note_id,
                "title": note.title,
                "content": note.content,
                "contentFormat": "markdown",
                "ceoName": note.ceoName,
                "ceoDesignation": note.ceoDesignation,
                "ceoImageUrl": note.ceoImageUrl,
                "isEnabled": note.isEnabled,
                "showOnlyOnce": note.showOnlyOnce,
                "targetAudience": note.targetAudience,
                "version": new_version,
                "createdAt": now.isoformat() + "Z"
            },
            "message": "CEO note saved successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating CEO note: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error_code": "SRV_5001",
                "message": "Failed to save CEO note"
            }
        )


@router.patch("/admin/ceo-note/toggle")
@limiter.limit(RATE_LIMITS["admin_write"])
async def toggle_ceo_note(
    request: Request,
    isEnabled: bool = Body(..., embed=True),
    authorization: Optional[str] = Header(None, alias="Authorization"),
    access_token: Optional[str] = Header(None, alias="access-token")
):
    """
    Toggle CEO Note Enabled/Disabled (Admin)

    Quick toggle to enable or disable the CEO note without editing content.

    **Request Body:**
    ```json
    {
        "isEnabled": true
    }
    ```

    **Headers:**
    - Authorization: Bearer {token} (admin token required)

    **Returns:**
    - Updated enabled status
    """
    try:
        db = get_db()

        # TODO: Add admin authentication check

        ceo_notes_collection = db['ceo_notes']

        # Update the active note
        result = ceo_notes_collection.update_one(
            {"isDeleted": {"$ne": True}},
            {
                "$set": {
                    "isEnabled": isEnabled,
                    "updated_at": datetime.utcnow()
                }
            }
        )

        if result.modified_count == 0:
            # No note exists, create default with the enabled status
            return {
                "success": True,
                "data": {
                    "isEnabled": isEnabled,
                    "message": "No CEO note configured. Create one first."
                }
            }

        logger.info(f"CEO note toggled: isEnabled={isEnabled}")

        return {
            "success": True,
            "data": {
                "isEnabled": isEnabled
            },
            "message": f"CEO note {'enabled' if isEnabled else 'disabled'} successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error toggling CEO note: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error_code": "SRV_5001",
                "message": "Failed to toggle CEO note"
            }
        )


@router.delete("/admin/ceo-note/views")
@limiter.limit(RATE_LIMITS["admin_write"])
async def reset_ceo_note_views(
    request: Request,
    authorization: Optional[str] = Header(None, alias="Authorization"),
    access_token: Optional[str] = Header(None, alias="access-token")
):
    """
    Reset CEO Note Views (Admin)

    Clears all view records so the note will be shown to all users again.
    Useful when publishing a new important message.

    **Headers:**
    - Authorization: Bearer {token} (admin token required)

    **Returns:**
    - Number of view records deleted
    """
    try:
        db = get_db()

        # TODO: Add admin authentication check

        ceo_note_views_collection = db['ceo_note_views']

        result = ceo_note_views_collection.delete_many({})

        logger.info(f"CEO note views reset: {result.deleted_count} records deleted")

        return {
            "success": True,
            "data": {
                "deletedCount": result.deleted_count
            },
            "message": f"Cleared {result.deleted_count} view records. Note will be shown to all users again."
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resetting CEO note views: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error_code": "SRV_5001",
                "message": "Failed to reset CEO note views"
            }
        )
