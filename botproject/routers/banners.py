"""
Banner/Ads System Router
Complete banner management system for displaying promotional content,
coming soon features, announcements, and ads in the Flutter app.

Features:
- User Endpoints: Get active banners, track views/clicks
- Admin Endpoints: Full CRUD, image upload, analytics
- Targeting: New users, returning users, all users
- Scheduling: Start/end dates for campaigns
- Analytics: Track impressions, clicks, CTR

Rate Limiting Applied (Redis-backed):
- User banner fetch: 60/minute per IP
- User tracking: 30/minute per IP
- Admin read: 30/minute per IP
- Admin write: 10/minute per IP
- Admin delete: 3/minute per IP

MongoDB Collections:
- banners: Banner documents
- banner_views: View tracking (for showOnlyOnce)
- banner_analytics: Impression and click tracking
"""

import logging
import hashlib
import base64
from datetime import datetime
from typing import Optional, List, Dict, Any
from io import BytesIO
from bson import ObjectId
from fastapi import APIRouter, HTTPException, Request, Header, UploadFile, File, Form, Depends
from pydantic import BaseModel, Field

from core.rate_limiter import limiter, RATE_LIMITS
from models.banner import (
    BannerCreateRequest, BannerUpdateRequest, BannerResponse,
    BannerViewRequest, BannerClickRequest, MarkBannerSeenRequest,
    BannerType, BannerPosition, TargetAudience, CTAType,
    DEFAULT_BANNERS
)

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(tags=["Banners"])


# ==================== DATABASE INITIALIZATION ====================

def init_banner_collections():
    """
    Initialize banner collections and create indexes.
    This ensures collections exist even before first insert.
    """
    try:
        db = get_db()

        # Create collections if they don't exist
        existing_collections = db.list_collection_names()

        # Initialize 'banners' collection
        if 'banners' not in existing_collections:
            db.create_collection('banners')
            logger.info("✅ Created 'banners' collection")

        # Initialize 'banner_views' collection
        if 'banner_views' not in existing_collections:
            db.create_collection('banner_views')
            logger.info("✅ Created 'banner_views' collection")

        # Initialize 'banner_analytics' collection
        if 'banner_analytics' not in existing_collections:
            db.create_collection('banner_analytics')
            logger.info("✅ Created 'banner_analytics' collection")

        # Create indexes for better query performance
        banners_collection = db['banners']
        banner_views_collection = db['banner_views']
        analytics_collection = db['banner_analytics']

        # Banners indexes
        banners_collection.create_index([("isActive", 1), ("isDeleted", 1)])
        banners_collection.create_index([("position", 1)])
        banners_collection.create_index([("priority", -1)])
        banners_collection.create_index([("bannerType", 1)])
        banners_collection.create_index([("targetAudience", 1)])
        banners_collection.create_index([("startDate", 1), ("endDate", 1)])

        # Banner views indexes (for showOnlyOnce feature)
        banner_views_collection.create_index([("user_id", 1), ("banner_id", 1)], unique=True)

        # Analytics indexes
        analytics_collection.create_index([("banner_id", 1), ("timestamp", -1)])
        analytics_collection.create_index([("user_id", 1)])
        analytics_collection.create_index([("action", 1)])

        logger.info("✅ Banner collections initialized with indexes")
        return True

    except Exception as e:
        logger.error(f"❌ Error initializing banner collections: {str(e)}", exc_info=True)
        return False


# ==================== HELPER FUNCTIONS ====================

def get_db():
    """Get MongoDB database connection"""
    from database_storage.mongodb_chat_manager import mongodb_chat_manager
    return mongodb_chat_manager.db


def verify_admin_token(authorization: str = Header(None)) -> dict:
    """Verify admin JWT token"""
    import jwt
    import os

    if not authorization:
        raise HTTPException(
            status_code=401,
            detail={
                "success": False,
                "error_code": "AUTH_8020",
                "message": "Authorization header required"
            }
        )

    try:
        # Extract token from "Bearer <token>"
        if authorization.startswith("Bearer "):
            token = authorization[7:]
        else:
            token = authorization

        # Decode JWT
        ADMIN_SECRET_KEY = os.getenv("ADMIN_SECRET_KEY", "eazr_admin_secret_key_2024")
        payload = jwt.decode(token, ADMIN_SECRET_KEY, algorithms=["HS256"])

        if payload.get("role") != "admin":
            raise HTTPException(
                status_code=403,
                detail={
                    "success": False,
                    "error_code": "AUTH_8020",
                    "message": "Admin role required"
                }
            )

        return payload

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail={
                "success": False,
                "error_code": "AUTH_8021",
                "message": "Token expired"
            }
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail={
                "success": False,
                "error_code": "AUTH_8022",
                "message": "Invalid token"
            }
        )


def optional_admin_token(authorization: str = Header(None)) -> Optional[dict]:
    """Optional admin token verification - returns None if no token or invalid"""
    if not authorization:
        return None
    try:
        import jwt
        import os
        if authorization.startswith("Bearer "):
            token = authorization[7:]
        else:
            token = authorization
        ADMIN_SECRET_KEY = os.getenv("ADMIN_SECRET_KEY", "eazr_admin_secret_key_2024")
        payload = jwt.decode(token, ADMIN_SECRET_KEY, algorithms=["HS256"])
        if payload.get("role") == "admin":
            return payload
        return None
    except:
        return None


def banner_doc_to_response(doc: dict, include_analytics: bool = False) -> dict:
    """Convert MongoDB document to API response format"""
    response = {
        "bannerId": str(doc.get("_id", "")),
        "title": doc.get("title", ""),
        "subtitle": doc.get("subtitle"),
        "description": doc.get("description"),
        "imageUrl": doc.get("imageUrl"),
        "backgroundImageUrl": doc.get("backgroundImageUrl"),
        "backgroundColor": doc.get("backgroundColor"),
        "textColor": doc.get("textColor"),
        "bannerType": doc.get("bannerType", "promotional"),
        "position": doc.get("position"),  # Can be None (shows on all screens)
        "ctaType": doc.get("ctaType", "none"),
        "ctaText": doc.get("ctaText"),
        "ctaValue": doc.get("ctaValue"),
        "targetAudience": doc.get("targetAudience", "all_users"),
        "priority": doc.get("priority", 0),
        "isActive": doc.get("isActive", True),
        "showOnlyOnce": doc.get("showOnlyOnce", False),
        "startDate": doc.get("startDate").isoformat() + "Z" if doc.get("startDate") else None,
        "endDate": doc.get("endDate").isoformat() + "Z" if doc.get("endDate") else None,
        "tags": doc.get("tags", []),
        "createdAt": doc.get("created_at").isoformat() + "Z" if doc.get("created_at") else None,
        "updatedAt": doc.get("updated_at").isoformat() + "Z" if doc.get("updated_at") else None,
        "createdBy": doc.get("created_by")
    }

    if include_analytics:
        response["impressions"] = doc.get("impressions", 0)
        response["clicks"] = doc.get("clicks", 0)
        impressions = doc.get("impressions", 0)
        clicks = doc.get("clicks", 0)
        response["ctr"] = round((clicks / impressions * 100), 2) if impressions > 0 else 0.0

    return response


def is_banner_visible(banner: dict, user_id: Optional[int], db) -> tuple:
    """
    Check if banner should be shown to user
    Returns: (should_show, reason)
    """
    now = datetime.utcnow()

    # Check if active
    if not banner.get("isActive", True):
        return False, "Banner is disabled"

    # Check if deleted
    if banner.get("isDeleted", False):
        return False, "Banner is deleted"

    # Check start date
    start_date = banner.get("startDate")
    if start_date and start_date > now:
        return False, "Banner campaign has not started"

    # Check end date
    end_date = banner.get("endDate")
    if end_date and end_date < now:
        return False, "Banner campaign has ended"

    # Check if user has already seen (for showOnlyOnce banners)
    if user_id and banner.get("showOnlyOnce", False):
        banner_views_collection = db['banner_views']
        existing_view = banner_views_collection.find_one({
            "user_id": int(user_id),
            "banner_id": str(banner.get("_id", ""))
        })
        if existing_view:
            return False, "User has already seen this banner"

    # Check target audience
    target_audience = banner.get("targetAudience", "all_users")
    if user_id and target_audience != "all_users":
        policy_count = db['policy_analysis'].count_documents({
            "user_id": int(user_id),
            "$or": [
                {"isDeleted": {"$exists": False}},
                {"isDeleted": False}
            ]
        })

        is_new_user = policy_count == 0

        if target_audience == "new_users" and not is_new_user:
            return False, "Banner is for new users only"
        elif target_audience == "returning_users" and is_new_user:
            return False, "Banner is for returning users only"
        elif target_audience == "premium_users" and policy_count < 3:
            return False, "Banner is for premium users only"

    return True, "OK"


# ==================== USER ENDPOINTS ====================

@router.get("/banners")
@limiter.limit("60/minute")
async def get_banners(
    request: Request,
    userId: Optional[int] = None,
    limit: int = 10
):
    """
    Get Active Banners for User

    Returns all active banners that should be displayed to the user,
    based on targeting rules (audience type).

    **Query Parameters:**
    - userId: User ID (optional, for personalized targeting based on user type)
    - limit: Max number of banners to return (default 10)

    **Target Audience Types:**
    - all_users: Show to everyone
    - new_users: Users with no policies
    - returning_users: Users with at least 1 policy
    - premium_users: Users with 3+ policies

    **Returns:**
    - List of banners sorted by priority (highest first)
    """
    try:
        db = get_db()
        banners_collection = db['banners']
        now = datetime.utcnow()

        # Build query for active banners
        query = {
            "isActive": True,
            "isDeleted": {"$ne": True},
            "$or": [
                {"startDate": {"$exists": False}},
                {"startDate": None},
                {"startDate": {"$lte": now}}
            ]
        }

        # Add end date filter
        query["$and"] = [
            {"$or": [
                {"endDate": {"$exists": False}},
                {"endDate": None},
                {"endDate": {"$gte": now}}
            ]}
        ]

        # Fetch banners sorted by priority (descending)
        banners = list(banners_collection.find(query).sort("priority", -1).limit(limit * 2))

        # If no banners exist, create default coming soon banners
        if len(banners) == 0:
            logger.info("No banners found. Creating default coming soon banners...")
            for default_banner in DEFAULT_BANNERS:
                banner_doc = {
                    **default_banner,
                    "impressions": 0,
                    "clicks": 0,
                    "isDeleted": False,
                    "created_at": now,
                    "updated_at": now,
                    "created_by": "system"
                }
                banners_collection.insert_one(banner_doc)

            # Re-fetch
            banners = list(banners_collection.find(query).sort("priority", -1).limit(limit * 2))

        # Filter banners based on visibility rules
        visible_banners = []
        for banner in banners:
            should_show, reason = is_banner_visible(banner, userId, db)
            if should_show:
                visible_banners.append(banner_doc_to_response(banner))
                if len(visible_banners) >= limit:
                    break

        logger.info(f"Returning {len(visible_banners)} banners for user {userId}")

        return {
            "success": True,
            "data": {
                "banners": visible_banners,
                "count": len(visible_banners)
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching banners: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error_code": "BAN_8001",
                "message": "Failed to fetch banners"
            }
        )


@router.get("/banners/{banner_id}")
@limiter.limit("60/minute")
async def get_banner_by_id(
    request: Request,
    banner_id: str,
    userId: Optional[int] = None
):
    """
    Get Single Banner by ID

    **Path Parameters:**
    - banner_id: The banner ID

    **Query Parameters:**
    - userId: User ID (optional, for visibility check)

    **Returns:**
    - Banner details if visible to user
    """
    try:
        db = get_db()
        banners_collection = db['banners']

        # Find banner
        try:
            banner = banners_collection.find_one({"_id": ObjectId(banner_id)})
        except:
            banner = banners_collection.find_one({"bannerId": banner_id})

        if not banner:
            raise HTTPException(
                status_code=404,
                detail={
                    "success": False,
                    "error_code": "BAN_8002",
                    "message": "Banner not found"
                }
            )

        # Check visibility
        should_show, reason = is_banner_visible(banner, userId, db)

        if not should_show:
            return {
                "success": True,
                "data": {
                    "shouldShow": False,
                    "reason": reason
                }
            }

        return {
            "success": True,
            "data": {
                "shouldShow": True,
                "banner": banner_doc_to_response(banner)
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching banner {banner_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error_code": "BAN_8001",
                "message": "Failed to fetch banner"
            }
        )


@router.post("/banners/track-view")
@limiter.limit(RATE_LIMITS["user_write"])
async def track_banner_view(
    request: Request,
    body: BannerViewRequest
):
    """
    Track Banner Impression/View

    Call this when a banner is displayed to the user.

    **Request Body (JSON):**
    ```json
    {
        "userId": 343,
        "bannerId": "678abc123def456..."
    }
    ```

    **Returns:**
    - success: Whether the view was tracked
    """
    try:
        db = get_db()
        banners_collection = db['banners']
        analytics_collection = db['banner_analytics']

        # Increment impression count
        result = banners_collection.update_one(
            {"_id": ObjectId(body.bannerId)},
            {"$inc": {"impressions": 1}}
        )

        # Log detailed analytics
        analytics_collection.insert_one({
            "banner_id": body.bannerId,
            "user_id": body.userId,
            "action": "view",
            "timestamp": datetime.utcnow(),
            "ip_address": request.client.host if request.client else None
        })

        logger.info(f"Banner view tracked: {body.bannerId} by user {body.userId}")

        return {
            "success": True,
            "message": "View tracked successfully"
        }

    except Exception as e:
        logger.error(f"Error tracking banner view: {str(e)}", exc_info=True)
        # Don't fail the request for tracking errors
        return {
            "success": True,
            "message": "View tracked"
        }


@router.post("/banners/track-click")
@limiter.limit(RATE_LIMITS["user_write"])
async def track_banner_click(
    request: Request,
    body: BannerClickRequest
):
    """
    Track Banner Click

    Call this when a user clicks/taps on a banner.

    **Request Body (JSON):**
    ```json
    {
        "userId": 343,
        "bannerId": "678abc123def456..."
    }
    ```

    **Returns:**
    - success: Whether the click was tracked
    """
    try:
        db = get_db()
        banners_collection = db['banners']
        analytics_collection = db['banner_analytics']

        # Increment click count
        banners_collection.update_one(
            {"_id": ObjectId(body.bannerId)},
            {"$inc": {"clicks": 1}}
        )

        # Log detailed analytics
        analytics_collection.insert_one({
            "banner_id": body.bannerId,
            "user_id": body.userId,
            "action": "click",
            "timestamp": datetime.utcnow(),
            "ip_address": request.client.host if request.client else None
        })

        logger.info(f"Banner click tracked: {body.bannerId} by user {body.userId}")

        return {
            "success": True,
            "message": "Click tracked successfully"
        }

    except Exception as e:
        logger.error(f"Error tracking banner click: {str(e)}", exc_info=True)
        return {
            "success": True,
            "message": "Click tracked"
        }


@router.post("/banners/mark-seen")
@limiter.limit(RATE_LIMITS["user_write"])
async def mark_banner_seen(
    request: Request,
    body: MarkBannerSeenRequest
):
    """
    Mark Banner as Seen

    Call this when user dismisses/closes a banner that has showOnlyOnce=true.
    This ensures the banner won't be shown again to this user.

    **Request Body (JSON):**
    ```json
    {
        "userId": 343,
        "bannerId": "678abc123def456..."
    }
    ```

    **Returns:**
    - success: Whether the banner was marked as seen
    """
    try:
        db = get_db()
        banner_views_collection = db['banner_views']

        # Upsert to avoid duplicates
        result = banner_views_collection.update_one(
            {
                "user_id": int(body.userId),
                "banner_id": body.bannerId
            },
            {
                "$set": {
                    "user_id": int(body.userId),
                    "banner_id": body.bannerId,
                    "seen_at": datetime.utcnow()
                }
            },
            upsert=True
        )

        logger.info(f"Banner {body.bannerId} marked as seen by user {body.userId}")

        return {
            "success": True,
            "message": "Banner marked as seen"
        }

    except Exception as e:
        logger.error(f"Error marking banner as seen: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error_code": "BAN_8003",
                "message": "Failed to mark banner as seen"
            }
        )


# ==================== ADMIN ENDPOINTS ====================

@router.get("/admin/banners")
@limiter.limit(RATE_LIMITS["admin_read"])
async def admin_list_banners(
    request: Request,
    skip: int = 0,
    limit: int = 20,
    isActive: Optional[bool] = None,
    bannerType: Optional[str] = None,
    position: Optional[str] = None,
    admin_user: Optional[dict] = Depends(optional_admin_token)
):
    """
    [ADMIN] List All Banners

    Get all banners with optional filters. Includes analytics data.

    **Headers:**
    - Authorization: Bearer {admin_token} (Optional for local development)

    **Query Parameters:**
    - skip: Number of records to skip (pagination)
    - limit: Max records to return (default 20)
    - isActive: Filter by active status
    - bannerType: Filter by banner type
    - position: Filter by display position

    **Returns:**
    - List of all banners with analytics
    """
    try:
        db = get_db()
        banners_collection = db['banners']

        # Build query
        query = {"isDeleted": {"$ne": True}}

        if isActive is not None:
            query["isActive"] = isActive

        if bannerType:
            query["bannerType"] = bannerType

        if position:
            query["position"] = position

        # Get total count
        total = banners_collection.count_documents(query)

        # Fetch banners
        banners = list(
            banners_collection.find(query)
            .sort([("priority", -1), ("created_at", -1)])
            .skip(skip)
            .limit(limit)
        )

        banner_list = [banner_doc_to_response(b, include_analytics=True) for b in banners]

        return {
            "success": True,
            "data": {
                "banners": banner_list,
                "total": total,
                "skip": skip,
                "limit": limit,
                "count": len(banner_list),
                "hasMore": (skip + len(banner_list)) < total
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing banners: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error_code": "BAN_8001",
                "message": "Failed to list banners"
            }
        )


@router.get("/admin/banners/{banner_id}")
@limiter.limit(RATE_LIMITS["admin_read"])
async def admin_get_banner(
    request: Request,
    banner_id: str,
    admin_user: Optional[dict] = Depends(optional_admin_token)
):
    """
    [ADMIN] Get Banner Details

    Get detailed banner information including analytics.

    **Headers:**
    - Authorization: Bearer {admin_token}

    **Path Parameters:**
    - banner_id: The banner ID

    **Returns:**
    - Full banner details with analytics
    """
    try:
        db = get_db()
        banners_collection = db['banners']

        # Find banner
        try:
            banner = banners_collection.find_one({"_id": ObjectId(banner_id)})
        except:
            banner = None

        if not banner:
            raise HTTPException(
                status_code=404,
                detail={
                    "success": False,
                    "error_code": "BAN_8002",
                    "message": "Banner not found"
                }
            )

        return {
            "success": True,
            "data": {
                "banner": banner_doc_to_response(banner, include_analytics=True)
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting banner {banner_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error_code": "BAN_8001",
                "message": "Failed to get banner"
            }
        )


@router.post("/admin/banners")
@limiter.limit(RATE_LIMITS["admin_write"])
async def admin_create_banner(
    request: Request,
    body: BannerCreateRequest,
    admin_user: Optional[dict] = Depends(optional_admin_token)
):
    """
    [ADMIN] Create New Banner

    Create a new banner/ad to display in the app.

    **Headers:**
    - Authorization: Bearer {admin_token} (Optional for local development)

    **Request Body (JSON):**
    ```json
    {
        "title": "Special Offer!",
        "subtitle": "Limited time only",
        "description": "Get 20% off on all health insurance plans",
        "imageUrl": "https://...",
        "bannerType": "promotional",
        "position": "home_top",
        "ctaType": "link",
        "ctaText": "Learn More",
        "ctaValue": "https://...",
        "targetAudience": "all_users",
        "priority": 100,
        "isActive": true,
        "showOnlyOnce": false,
        "startDate": "2024-01-01T00:00:00Z",
        "endDate": "2024-12-31T23:59:59Z"
    }
    ```

    **Banner Types:**
    - promotional: Promotions, offers
    - informational: General info
    - coming_soon: Coming soon features
    - announcement: Important announcements
    - alert: Urgent alerts

    **Positions:**
    - home_top, home_bottom, dashboard, policy_list, profile, full_screen

    **Target Audience:**
    - all_users, new_users, returning_users, premium_users

    **Returns:**
    - Created banner with ID
    """
    try:
        db = get_db()
        banners_collection = db['banners']
        now = datetime.utcnow()

        # Build banner document
        banner_doc = {
            "title": body.title,
            "subtitle": body.subtitle,
            "description": body.description,
            "imageUrl": body.imageUrl,
            "backgroundImageUrl": body.backgroundImageUrl,
            "backgroundColor": body.backgroundColor,
            "textColor": body.textColor,
            "bannerType": body.bannerType.value if body.bannerType else "promotional",
            "position": body.position.value if body.position else None,  # None means show on all screens
            "ctaType": body.ctaType.value if body.ctaType else "none",
            "ctaText": body.ctaText,
            "ctaValue": body.ctaValue,
            "targetAudience": body.targetAudience.value if body.targetAudience else "all_users",
            "priority": body.priority,
            "isActive": body.isActive,
            "showOnlyOnce": body.showOnlyOnce,
            "startDate": body.startDate,
            "endDate": body.endDate,
            "tags": body.tags or [],
            "metadata": body.metadata or {},
            "impressions": 0,
            "clicks": 0,
            "isDeleted": False,
            "created_at": now,
            "updated_at": now,
            "created_by": admin_user.get("username", "anonymous") if admin_user else "anonymous"
        }

        # Insert
        result = banners_collection.insert_one(banner_doc)
        banner_doc["_id"] = result.inserted_id

        creator = admin_user.get('username') if admin_user else 'anonymous'
        logger.info(f"Banner created: {result.inserted_id} by {creator}")

        return {
            "success": True,
            "message": "Banner created successfully",
            "data": {
                "banner": banner_doc_to_response(banner_doc, include_analytics=True)
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating banner: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error_code": "BAN_8004",
                "message": "Failed to create banner"
            }
        )


@router.put("/admin/banners/{banner_id}")
@limiter.limit(RATE_LIMITS["admin_write"])
async def admin_update_banner(
    request: Request,
    banner_id: str,
    body: BannerUpdateRequest,
    admin_user: Optional[dict] = Depends(optional_admin_token)
):
    """
    [ADMIN] Update Banner

    Update an existing banner's properties.

    **Headers:**
    - Authorization: Bearer {admin_token}

    **Path Parameters:**
    - banner_id: The banner ID to update

    **Request Body (JSON):**
    Only include fields you want to update.
    ```json
    {
        "title": "Updated Title",
        "isActive": false,
        "priority": 50
    }
    ```

    **Returns:**
    - Updated banner
    """
    try:
        db = get_db()
        banners_collection = db['banners']

        # Check if banner exists
        try:
            existing = banners_collection.find_one({"_id": ObjectId(banner_id)})
        except:
            existing = None

        if not existing:
            raise HTTPException(
                status_code=404,
                detail={
                    "success": False,
                    "error_code": "BAN_8002",
                    "message": "Banner not found"
                }
            )

        # Build update document
        update_data = {"updated_at": datetime.utcnow()}

        # Only update provided fields
        update_fields = body.dict(exclude_unset=True)
        for field, value in update_fields.items():
            if value is not None:
                # Handle enum values
                if hasattr(value, 'value'):
                    update_data[field] = value.value
                else:
                    update_data[field] = value

        # Update
        result = banners_collection.update_one(
            {"_id": ObjectId(banner_id)},
            {"$set": update_data}
        )

        # Fetch updated banner
        updated_banner = banners_collection.find_one({"_id": ObjectId(banner_id)})

        updater = admin_user.get('username') if admin_user else 'anonymous'
        logger.info(f"Banner updated: {banner_id} by {updater}")

        return {
            "success": True,
            "message": "Banner updated successfully",
            "data": {
                "banner": banner_doc_to_response(updated_banner, include_analytics=True)
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating banner {banner_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error_code": "BAN_8005",
                "message": "Failed to update banner"
            }
        )


@router.delete("/admin/banners/{banner_id}")
@limiter.limit(RATE_LIMITS["admin_delete"])
async def admin_delete_banner(
    request: Request,
    banner_id: str,
    permanent: bool = False,
    admin_user: Optional[dict] = Depends(optional_admin_token)
):
    """
    [ADMIN] Delete Banner

    Soft delete (default) or permanently delete a banner.

    **Headers:**
    - Authorization: Bearer {admin_token}

    **Path Parameters:**
    - banner_id: The banner ID to delete

    **Query Parameters:**
    - permanent: Set to true for permanent deletion (default: false)

    **Returns:**
    - Deletion confirmation
    """
    try:
        db = get_db()
        banners_collection = db['banners']

        # Check if banner exists
        try:
            existing = banners_collection.find_one({"_id": ObjectId(banner_id)})
        except:
            existing = None

        if not existing:
            raise HTTPException(
                status_code=404,
                detail={
                    "success": False,
                    "error_code": "BAN_8002",
                    "message": "Banner not found"
                }
            )

        if permanent:
            # Permanent delete
            result = banners_collection.delete_one({"_id": ObjectId(banner_id)})
            message = "Banner permanently deleted"
        else:
            # Soft delete
            deleter = admin_user.get("username", "anonymous") if admin_user else "anonymous"
            result = banners_collection.update_one(
                {"_id": ObjectId(banner_id)},
                {
                    "$set": {
                        "isDeleted": True,
                        "isActive": False,
                        "deleted_at": datetime.utcnow(),
                        "deleted_by": deleter
                    }
                }
            )
            message = "Banner deleted (soft delete)"

        deleter = admin_user.get('username') if admin_user else 'anonymous'
        logger.info(f"Banner deleted: {banner_id} by {deleter} (permanent={permanent})")

        return {
            "success": True,
            "message": message,
            "data": {
                "bannerId": banner_id,
                "permanent": permanent
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting banner {banner_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error_code": "BAN_8006",
                "message": "Failed to delete banner"
            }
        )


@router.post("/admin/banners/upload-image")
@limiter.limit(RATE_LIMITS["admin_write"])
async def admin_upload_banner_image(
    request: Request,
    file: UploadFile = File(...),
    admin_user: Optional[dict] = Depends(optional_admin_token)
):
    """
    [ADMIN] Upload Banner Image

    Upload an image for use in banners. Supports JPG, PNG, WebP, GIF.
    Max file size: 5MB.

    **Headers:**
    - Authorization: Bearer {admin_token} (Optional)

    **Form Data:**
    - file: The image file to upload

    **Returns:**
    - S3 URL of the uploaded image
    """
    try:
        # Content type mapping
        CONTENT_TYPE_MAP = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.webp': 'image/webp',
        }

        # Validate file type
        allowed_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.gif']
        file_ext = '.' + file.filename.split('.')[-1].lower() if '.' in file.filename else ''

        logger.info(f"Banner image upload started: filename={file.filename}, extension={file_ext}")

        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail={
                    "success": False,
                    "error_code": "BAN_8007",
                    "message": f"Invalid file type '{file_ext}'. Allowed: {', '.join(allowed_extensions)}"
                }
            )

        # Read file content
        content = await file.read()
        file_size = len(content)
        logger.info(f"Banner image read: size={file_size} bytes")

        # Validate file size (5MB max)
        if file_size > 5 * 1024 * 1024:
            raise HTTPException(
                status_code=400,
                detail={
                    "success": False,
                    "error_code": "BAN_8008",
                    "message": f"File too large ({file_size / 1024 / 1024:.2f}MB). Maximum size: 5MB"
                }
            )

        # Validate file is not empty
        if file_size == 0:
            raise HTTPException(
                status_code=400,
                detail={
                    "success": False,
                    "error_code": "BAN_8007",
                    "message": "Empty file uploaded"
                }
            )

        # Generate unique filename
        file_hash = hashlib.md5(content).hexdigest()[:8]
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        filename = f"banner_{timestamp}_{file_hash}{file_ext}"

        # Get content type
        content_type = CONTENT_TYPE_MAP.get(file_ext, 'image/jpeg')

        logger.info(f"Uploading to S3: filename={filename}, content_type={content_type}")

        # Upload to S3
        from database_storage.s3_bucket import upload_image_to_s3

        result = upload_image_to_s3(
            image_buffer=BytesIO(content),
            filename=filename,
            bucket_name="raceabove-dev",
            content_type=content_type
        )

        if not result.get("success"):
            error_msg = result.get("error", result.get("message", "Unknown S3 error"))
            logger.error(f"S3 upload failed: {error_msg}")
            raise HTTPException(
                status_code=500,
                detail={
                    "success": False,
                    "error_code": "BAN_8009",
                    "message": f"Failed to upload image to S3: {error_msg}"
                }
            )

        uploader = admin_user.get('username') if admin_user else 'anonymous'
        logger.info(f"Banner image uploaded successfully: {filename} -> {result.get('s3_url')} by {uploader}")

        return {
            "success": True,
            "message": "Image uploaded successfully",
            "data": {
                "imageUrl": result.get("s3_url"),
                "filename": filename
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading banner image: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error_code": "BAN_8009",
                "message": "Failed to upload image"
            }
        )


@router.get("/admin/banners/{banner_id}/analytics")
@limiter.limit(RATE_LIMITS["admin_read"])
async def admin_get_banner_analytics(
    request: Request,
    banner_id: str,
    days: int = 30,
    admin_user: Optional[dict] = Depends(optional_admin_token)
):
    """
    [ADMIN] Get Banner Analytics

    Get detailed analytics for a specific banner.

    **Headers:**
    - Authorization: Bearer {admin_token}

    **Path Parameters:**
    - banner_id: The banner ID

    **Query Parameters:**
    - days: Number of days of analytics (default 30)

    **Returns:**
    - Impressions, clicks, CTR, daily breakdown
    """
    try:
        db = get_db()
        banners_collection = db['banners']
        analytics_collection = db['banner_analytics']

        # Get banner
        try:
            banner = banners_collection.find_one({"_id": ObjectId(banner_id)})
        except:
            banner = None

        if not banner:
            raise HTTPException(
                status_code=404,
                detail={
                    "success": False,
                    "error_code": "BAN_8002",
                    "message": "Banner not found"
                }
            )

        # Calculate date range
        from datetime import timedelta
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        # Get daily breakdown
        pipeline = [
            {
                "$match": {
                    "banner_id": banner_id,
                    "timestamp": {"$gte": start_date, "$lte": end_date}
                }
            },
            {
                "$group": {
                    "_id": {
                        "date": {"$dateToString": {"format": "%Y-%m-%d", "date": "$timestamp"}},
                        "action": "$action"
                    },
                    "count": {"$sum": 1}
                }
            },
            {
                "$sort": {"_id.date": 1}
            }
        ]

        daily_stats = list(analytics_collection.aggregate(pipeline))

        # Process daily stats
        daily_breakdown = {}
        for stat in daily_stats:
            date = stat["_id"]["date"]
            action = stat["_id"]["action"]
            if date not in daily_breakdown:
                daily_breakdown[date] = {"date": date, "views": 0, "clicks": 0}
            if action == "view":
                daily_breakdown[date]["views"] = stat["count"]
            elif action == "click":
                daily_breakdown[date]["clicks"] = stat["count"]

        # Convert to list
        daily_list = list(daily_breakdown.values())

        # Calculate totals
        total_impressions = banner.get("impressions", 0)
        total_clicks = banner.get("clicks", 0)
        ctr = round((total_clicks / total_impressions * 100), 2) if total_impressions > 0 else 0.0

        # Get unique viewers
        unique_viewers = analytics_collection.distinct(
            "user_id",
            {"banner_id": banner_id, "action": "view", "user_id": {"$ne": None}}
        )

        return {
            "success": True,
            "data": {
                "bannerId": banner_id,
                "title": banner.get("title"),
                "totalImpressions": total_impressions,
                "totalClicks": total_clicks,
                "ctr": ctr,
                "uniqueViewers": len(unique_viewers),
                "dateRange": {
                    "start": start_date.isoformat() + "Z",
                    "end": end_date.isoformat() + "Z",
                    "days": days
                },
                "dailyBreakdown": daily_list
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting banner analytics: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error_code": "BAN_8010",
                "message": "Failed to get analytics"
            }
        )


@router.post("/admin/banners/bulk-update")
@limiter.limit(RATE_LIMITS["admin_write"])
async def admin_bulk_update_banners(
    request: Request,
    body: dict,
    admin_user: Optional[dict] = Depends(optional_admin_token)
):
    """
    [ADMIN] Bulk Update Banners

    Update multiple banners at once (e.g., deactivate all, update priorities).

    **Headers:**
    - Authorization: Bearer {admin_token}

    **Request Body (JSON):**
    ```json
    {
        "bannerIds": ["id1", "id2", "id3"],
        "update": {
            "isActive": false
        }
    }
    ```

    **Returns:**
    - Number of banners updated
    """
    try:
        db = get_db()
        banners_collection = db['banners']

        banner_ids = body.get("bannerIds", [])
        update_data = body.get("update", {})

        if not banner_ids or not update_data:
            raise HTTPException(
                status_code=400,
                detail={
                    "success": False,
                    "error_code": "BAN_8011",
                    "message": "bannerIds and update fields are required"
                }
            )

        # Add updated_at
        update_data["updated_at"] = datetime.utcnow()

        # Convert IDs to ObjectId
        object_ids = [ObjectId(bid) for bid in banner_ids]

        # Update
        result = banners_collection.update_many(
            {"_id": {"$in": object_ids}},
            {"$set": update_data}
        )

        updater = admin_user.get('username') if admin_user else 'anonymous'
        logger.info(f"Bulk update: {result.modified_count} banners by {updater}")

        return {
            "success": True,
            "message": f"Updated {result.modified_count} banners",
            "data": {
                "modifiedCount": result.modified_count,
                "matchedCount": result.matched_count
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error bulk updating banners: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error_code": "BAN_8012",
                "message": "Failed to bulk update banners"
            }
        )


@router.get("/admin/banners/analytics/summary")
@limiter.limit(RATE_LIMITS["admin_read"])
async def admin_get_analytics_summary(
    request: Request,
    days: int = 30,
    admin_user: Optional[dict] = Depends(optional_admin_token)
):
    """
    [ADMIN] Get Overall Banner Analytics Summary

    Get summary analytics across all banners.

    **Headers:**
    - Authorization: Bearer {admin_token} (Optional for local development)

    **Query Parameters:**
    - days: Number of days to analyze (default 30)

    **Returns:**
    - Total impressions, clicks, top performing banners
    """
    try:
        db = get_db()
        banners_collection = db['banners']
        analytics_collection = db['banner_analytics']

        from datetime import timedelta
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        # Get all active banners
        active_banners = list(banners_collection.find(
            {"isDeleted": {"$ne": True}},
            {"_id": 1, "title": 1, "impressions": 1, "clicks": 1, "bannerType": 1, "position": 1}
        ))

        # Calculate totals
        total_impressions = sum(b.get("impressions", 0) for b in active_banners)
        total_clicks = sum(b.get("clicks", 0) for b in active_banners)
        overall_ctr = round((total_clicks / total_impressions * 100), 2) if total_impressions > 0 else 0.0

        # Top performing banners (by CTR)
        top_banners = []
        for b in active_banners:
            impressions = b.get("impressions", 0)
            clicks = b.get("clicks", 0)
            ctr = round((clicks / impressions * 100), 2) if impressions > 0 else 0.0
            top_banners.append({
                "bannerId": str(b["_id"]),
                "title": b.get("title", ""),
                "impressions": impressions,
                "clicks": clicks,
                "ctr": ctr
            })

        # Sort by CTR (descending)
        top_banners.sort(key=lambda x: x["ctr"], reverse=True)

        # Get stats by type
        type_stats = {}
        for b in active_banners:
            btype = b.get("bannerType", "unknown")
            if btype not in type_stats:
                type_stats[btype] = {"count": 0, "impressions": 0, "clicks": 0}
            type_stats[btype]["count"] += 1
            type_stats[btype]["impressions"] += b.get("impressions", 0)
            type_stats[btype]["clicks"] += b.get("clicks", 0)

        # Get stats by position
        position_stats = {}
        for b in active_banners:
            pos = b.get("position", "unknown")
            if pos not in position_stats:
                position_stats[pos] = {"count": 0, "impressions": 0, "clicks": 0}
            position_stats[pos]["count"] += 1
            position_stats[pos]["impressions"] += b.get("impressions", 0)
            position_stats[pos]["clicks"] += b.get("clicks", 0)

        return {
            "success": True,
            "data": {
                "summary": {
                    "totalBanners": len(active_banners),
                    "totalImpressions": total_impressions,
                    "totalClicks": total_clicks,
                    "overallCTR": overall_ctr
                },
                "topPerforming": top_banners[:5],
                "byType": type_stats,
                "byPosition": position_stats,
                "dateRange": {
                    "start": start_date.isoformat() + "Z",
                    "end": end_date.isoformat() + "Z",
                    "days": days
                }
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting analytics summary: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error_code": "BAN_8013",
                "message": "Failed to get analytics summary"
            }
        )


# ==================== UTILITY ENDPOINTS ====================

@router.get("/admin/banners/init-collections")
@limiter.limit(RATE_LIMITS["admin_write"])
async def admin_init_banner_collections(
    request: Request,
    admin_user: Optional[dict] = Depends(optional_admin_token)
):
    """
    [ADMIN] Initialize Banner Collections

    Manually initialize banner collections and create indexes.
    Use this if collections are not appearing in MongoDB.

    **Headers:**
    - Authorization: Bearer {admin_token}

    **Returns:**
    - Status of collection initialization
    """
    try:
        db = get_db()

        # Get existing collections
        existing_collections = db.list_collection_names()

        results = {
            "collections_before": existing_collections,
            "created": [],
            "indexes_created": []
        }

        # Create collections if they don't exist
        if 'banners' not in existing_collections:
            db.create_collection('banners')
            results["created"].append("banners")
            logger.info("Created 'banners' collection")

        if 'banner_views' not in existing_collections:
            db.create_collection('banner_views')
            results["created"].append("banner_views")
            logger.info("Created 'banner_views' collection")

        if 'banner_analytics' not in existing_collections:
            db.create_collection('banner_analytics')
            results["created"].append("banner_analytics")
            logger.info("Created 'banner_analytics' collection")

        # Create indexes
        banners_collection = db['banners']
        banner_views_collection = db['banner_views']
        analytics_collection = db['banner_analytics']

        # Banners indexes
        banners_collection.create_index([("isActive", 1), ("isDeleted", 1)])
        banners_collection.create_index([("position", 1)])
        banners_collection.create_index([("priority", -1)])
        results["indexes_created"].append("banners indexes")

        # Banner views indexes
        banner_views_collection.create_index([("user_id", 1), ("banner_id", 1)], unique=True)
        results["indexes_created"].append("banner_views indexes")

        # Analytics indexes
        analytics_collection.create_index([("banner_id", 1), ("timestamp", -1)])
        analytics_collection.create_index([("user_id", 1)])
        results["indexes_created"].append("banner_analytics indexes")

        # Get updated collection list
        results["collections_after"] = db.list_collection_names()

        initializer = admin_user.get('username') if admin_user else 'anonymous'
        logger.info(f"Banner collections initialized by {initializer}")

        return {
            "success": True,
            "message": "Banner collections initialized successfully",
            "data": results
        }

    except Exception as e:
        logger.error(f"Error initializing collections: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error_code": "BAN_8014",
                "message": f"Failed to initialize collections: {str(e)}"
            }
        )


@router.get("/admin/banners/debug-db")
@limiter.limit(RATE_LIMITS["admin_read"])
async def admin_debug_database(
    request: Request,
    admin_user: Optional[dict] = Depends(optional_admin_token)
):
    """
    [ADMIN] Debug Database Connection

    Shows database connection info and existing collections.
    Useful for troubleshooting.

    **Headers:**
    - Authorization: Bearer {admin_token}

    **Returns:**
    - Database name, collections, and banner count
    """
    try:
        db = get_db()

        # Get database info
        db_name = db.name
        collections = db.list_collection_names()

        # Get banner counts
        banner_count = 0
        banner_views_count = 0
        banner_analytics_count = 0

        if 'banners' in collections:
            banner_count = db['banners'].count_documents({})

        if 'banner_views' in collections:
            banner_views_count = db['banner_views'].count_documents({})

        if 'banner_analytics' in collections:
            banner_analytics_count = db['banner_analytics'].count_documents({})

        return {
            "success": True,
            "data": {
                "database_name": db_name,
                "collections": collections,
                "banner_collections": {
                    "banners": {
                        "exists": "banners" in collections,
                        "document_count": banner_count
                    },
                    "banner_views": {
                        "exists": "banner_views" in collections,
                        "document_count": banner_views_count
                    },
                    "banner_analytics": {
                        "exists": "banner_analytics" in collections,
                        "document_count": banner_analytics_count
                    }
                }
            }
        }

    except Exception as e:
        logger.error(f"Error debugging database: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error_code": "BAN_8015",
                "message": f"Failed to debug database: {str(e)}"
            }
        )


@router.get("/banners/health")
async def banner_health_check(request: Request):
    """
    Banner System Health Check

    Quick check to verify banner system is working and collections exist.
    No authentication required.

    **Returns:**
    - Database connection status
    - Collection existence status
    """
    try:
        db = get_db()
        collections = db.list_collection_names()

        # Check if banner collections exist
        banners_exists = 'banners' in collections
        views_exists = 'banner_views' in collections
        analytics_exists = 'banner_analytics' in collections

        # If collections don't exist, create them
        if not banners_exists or not views_exists or not analytics_exists:
            logger.info("Banner collections missing, initializing...")
            init_banner_collections()
            collections = db.list_collection_names()
            banners_exists = 'banners' in collections
            views_exists = 'banner_views' in collections
            analytics_exists = 'banner_analytics' in collections

        banner_count = db['banners'].count_documents({}) if banners_exists else 0

        return {
            "success": True,
            "data": {
                "status": "healthy",
                "database": db.name,
                "collections": {
                    "banners": banners_exists,
                    "banner_views": views_exists,
                    "banner_analytics": analytics_exists
                },
                "banner_count": banner_count,
                "message": "Banner system is operational"
            }
        }

    except Exception as e:
        logger.error(f"Banner health check failed: {str(e)}", exc_info=True)
        return {
            "success": False,
            "data": {
                "status": "unhealthy",
                "error": str(e),
                "message": "Banner system has issues"
            }
        }


@router.get("/banners/positions")
async def get_banner_positions(request: Request):
    """
    Get Available Banner Positions

    Returns list of available banner positions for the app.
    Useful for admin panel dropdown.
    Position is optional - if not set, banner shows on all screens.
    """
    return {
        "success": True,
        "data": {
            "positions": [
                {"value": "", "label": "All Screens (No specific position)", "description": "Shows on all screens"},
                {"value": "home_top", "label": "Home - Top", "description": "Top of home screen"},
                {"value": "home_bottom", "label": "Home - Bottom", "description": "Bottom of home screen"},
                {"value": "dashboard", "label": "Dashboard", "description": "Dashboard screen"},
                {"value": "policy_list", "label": "Policy List", "description": "Policy list screen"},
                {"value": "profile", "label": "Profile", "description": "Profile screen"},
                {"value": "full_screen", "label": "Full Screen", "description": "Full-screen modal/popup"}
            ]
        }
    }


@router.get("/banners/types")
async def get_banner_types(request: Request):
    """
    Get Available Banner Types

    Returns list of available banner types.
    Useful for admin panel dropdown.
    """
    return {
        "success": True,
        "data": {
            "types": [
                {"value": "promotional", "label": "Promotional", "description": "Promotions and offers"},
                {"value": "informational", "label": "Informational", "description": "General information"},
                {"value": "coming_soon", "label": "Coming Soon", "description": "Upcoming features"},
                {"value": "announcement", "label": "Announcement", "description": "Important announcements"},
                {"value": "alert", "label": "Alert", "description": "Urgent alerts"}
            ]
        }
    }


@router.get("/banners/audiences")
async def get_target_audiences(request: Request):
    """
    Get Available Target Audiences

    Returns list of available target audiences.
    Useful for admin panel dropdown.
    """
    return {
        "success": True,
        "data": {
            "audiences": [
                {"value": "all_users", "label": "All Users", "description": "Show to everyone"},
                {"value": "new_users", "label": "New Users", "description": "Users with no policies"},
                {"value": "returning_users", "label": "Returning Users", "description": "Users with policies"},
                {"value": "premium_users", "label": "Premium Users", "description": "Users with 3+ policies"}
            ]
        }
    }
