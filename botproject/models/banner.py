"""
Banner/Ads System Models
Pydantic models for Banner and Advertisement management

Models:
- BannerCreateRequest: Admin creates new banner
- BannerUpdateRequest: Admin updates existing banner
- BannerResponse: Banner data returned to client
- AdCreateRequest: Admin creates new ad
- AdUpdateRequest: Admin updates existing ad
- AdResponse: Ad data returned to client
"""

from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# ==================== ENUMS ====================

class BannerType(str, Enum):
    """Types of banners"""
    PROMOTIONAL = "promotional"      # Promotions, offers
    INFORMATIONAL = "informational"  # General info
    COMING_SOON = "coming_soon"      # Coming soon features
    ANNOUNCEMENT = "announcement"    # Important announcements
    ALERT = "alert"                  # Urgent alerts


class BannerPosition(str, Enum):
    """Where banner appears in the app"""
    HOME_TOP = "home_top"            # Top of home screen
    HOME_BOTTOM = "home_bottom"      # Bottom of home screen
    DASHBOARD = "dashboard"          # Dashboard screen
    POLICY_LIST = "policy_list"      # Policy list screen
    PROFILE = "profile"              # Profile screen
    FULL_SCREEN = "full_screen"      # Full-screen modal/popup


class TargetAudience(str, Enum):
    """Target audience for the banner"""
    ALL_USERS = "all_users"
    NEW_USERS = "new_users"          # Users with no policies
    RETURNING_USERS = "returning_users"  # Users with policies
    PREMIUM_USERS = "premium_users"  # Users with 3+ policies


class CTAType(str, Enum):
    """Call-to-action button types"""
    NONE = "none"                    # No CTA
    LINK = "link"                    # External URL
    SCREEN = "screen"                # Navigate to app screen
    ACTION = "action"                # Trigger app action


# ==================== BANNER MODELS ====================

class BannerCreateRequest(BaseModel):
    """Request model to create a new banner"""

    title: str = Field(..., min_length=1, max_length=100, description="Banner title")
    subtitle: Optional[str] = Field(None, max_length=200, description="Banner subtitle")
    description: Optional[str] = Field(None, max_length=500, description="Banner description/content")

    # Visual elements
    imageUrl: Optional[str] = Field(None, description="Banner image URL (S3)")
    backgroundImageUrl: Optional[str] = Field(None, description="Background image URL")
    backgroundColor: Optional[str] = Field(None, description="Background color (hex)")
    textColor: Optional[str] = Field(None, description="Text color (hex)")

    # Banner configuration
    bannerType: BannerType = Field(default=BannerType.PROMOTIONAL, description="Type of banner")
    position: Optional[BannerPosition] = Field(default=None, description="Display position (optional - shows on all screens if not specified)")

    # Call-to-action
    ctaType: CTAType = Field(default=CTAType.NONE, description="CTA button type")
    ctaText: Optional[str] = Field(None, max_length=50, description="CTA button text")
    ctaValue: Optional[str] = Field(None, description="CTA value (URL, screen name, or action)")

    # Targeting
    targetAudience: TargetAudience = Field(default=TargetAudience.ALL_USERS, description="Target audience")

    # Display settings
    priority: int = Field(default=0, ge=0, le=100, description="Display priority (higher = first)")
    isActive: bool = Field(default=True, description="Whether banner is active")
    showOnlyOnce: bool = Field(default=False, description="Show only once per user")

    # Scheduling
    startDate: Optional[datetime] = Field(None, description="When to start showing")
    endDate: Optional[datetime] = Field(None, description="When to stop showing")

    # Additional metadata
    tags: Optional[List[str]] = Field(default=[], description="Tags for filtering")
    metadata: Optional[Dict[str, Any]] = Field(default={}, description="Additional custom data")


class BannerUpdateRequest(BaseModel):
    """Request model to update an existing banner"""

    title: Optional[str] = Field(None, min_length=1, max_length=100)
    subtitle: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = Field(None, max_length=500)

    imageUrl: Optional[str] = None
    backgroundImageUrl: Optional[str] = None
    backgroundColor: Optional[str] = None
    textColor: Optional[str] = None

    bannerType: Optional[BannerType] = None
    position: Optional[BannerPosition] = None

    ctaType: Optional[CTAType] = None
    ctaText: Optional[str] = Field(None, max_length=50)
    ctaValue: Optional[str] = None

    targetAudience: Optional[TargetAudience] = None

    priority: Optional[int] = Field(None, ge=0, le=100)
    isActive: Optional[bool] = None
    showOnlyOnce: Optional[bool] = None

    startDate: Optional[datetime] = None
    endDate: Optional[datetime] = None

    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


class BannerResponse(BaseModel):
    """Banner data returned to client"""

    bannerId: str
    title: str
    subtitle: Optional[str] = None
    description: Optional[str] = None

    imageUrl: Optional[str] = None
    backgroundImageUrl: Optional[str] = None
    backgroundColor: Optional[str] = None
    textColor: Optional[str] = None

    bannerType: str
    position: str

    ctaType: str
    ctaText: Optional[str] = None
    ctaValue: Optional[str] = None

    targetAudience: str
    priority: int
    isActive: bool
    showOnlyOnce: bool

    startDate: Optional[str] = None
    endDate: Optional[str] = None

    # Analytics (optional, for admin)
    impressions: Optional[int] = None
    clicks: Optional[int] = None
    ctr: Optional[float] = None  # Click-through rate

    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None
    createdBy: Optional[str] = None


# ==================== BANNER VIEW TRACKING ====================

class BannerViewRequest(BaseModel):
    """Request to track banner view/impression"""
    userId: Optional[int] = Field(None, description="User ID (optional for anonymous)")
    bannerId: str = Field(..., description="Banner ID that was viewed")


class BannerClickRequest(BaseModel):
    """Request to track banner click"""
    userId: Optional[int] = Field(None, description="User ID (optional for anonymous)")
    bannerId: str = Field(..., description="Banner ID that was clicked")


class MarkBannerSeenRequest(BaseModel):
    """Request to mark banner as seen (for showOnlyOnce banners)"""
    userId: int = Field(..., description="User ID")
    bannerId: str = Field(..., description="Banner ID that was seen")


# ==================== IMAGE UPLOAD ====================

class BannerImageUploadResponse(BaseModel):
    """Response after uploading banner image"""
    success: bool
    imageUrl: str
    filename: str
    message: str


# ==================== ANALYTICS ====================

class BannerAnalytics(BaseModel):
    """Banner analytics data"""
    bannerId: str
    title: str
    impressions: int
    clicks: int
    ctr: float  # Click-through rate percentage
    uniqueViews: int
    startDate: Optional[str] = None
    endDate: Optional[str] = None
    isActive: bool


# ==================== ADMIN LIST RESPONSE ====================

class BannerListResponse(BaseModel):
    """Response for listing banners (admin)"""
    success: bool
    banners: List[BannerResponse]
    total: int
    skip: int
    limit: int
    hasMore: bool


# ==================== DEFAULT BANNERS ====================

# Default "Coming Soon" banners that can be auto-created
DEFAULT_BANNERS = [
    {
        "title": "AI Policy Assistant - Coming Soon!",
        "subtitle": "Your personal insurance advisor",
        "description": "Get instant answers about your policies, coverage gaps, and personalized recommendations powered by AI.",
        "bannerType": "coming_soon",
        "position": "home_top",
        "backgroundColor": "#4F46E5",
        "textColor": "#FFFFFF",
        "ctaType": "none",
        "targetAudience": "all_users",
        "priority": 100,
        "isActive": True,
        "showOnlyOnce": False,
        "tags": ["coming_soon", "ai", "feature"]
    },
    {
        "title": "Family Coverage - Coming Soon!",
        "subtitle": "Protect your loved ones",
        "description": "Track and manage insurance for your entire family in one place. Add family members and get comprehensive coverage insights.",
        "bannerType": "coming_soon",
        "position": "dashboard",
        "backgroundColor": "#059669",
        "textColor": "#FFFFFF",
        "ctaType": "none",
        "targetAudience": "returning_users",
        "priority": 90,
        "isActive": True,
        "showOnlyOnce": False,
        "tags": ["coming_soon", "family", "feature"]
    },
    {
        "title": "Claim Assistance - Coming Soon!",
        "subtitle": "Hassle-free claims",
        "description": "File and track insurance claims directly from the app. Get step-by-step guidance and real-time status updates.",
        "bannerType": "coming_soon",
        "position": "policy_list",
        "backgroundColor": "#DC2626",
        "textColor": "#FFFFFF",
        "ctaType": "none",
        "targetAudience": "all_users",
        "priority": 80,
        "isActive": True,
        "showOnlyOnce": False,
        "tags": ["coming_soon", "claims", "feature"]
    }
]
