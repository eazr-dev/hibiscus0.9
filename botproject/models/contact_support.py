"""
Pydantic models for Contact Support API
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
import re


# ============= Nested Models =============

class EmailSupport(BaseModel):
    """Email support configuration"""
    address: str = Field(..., description="Support email address")
    subject_prefix: Optional[str] = Field(None, max_length=100, description="Email subject prefix")
    response_time: Optional[str] = Field(None, max_length=100, description="Expected response time")

    @field_validator('address')
    @classmethod
    def validate_email(cls, v):
        """Validate email address format"""
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, v):
            raise ValueError('Invalid email address format')
        return v


class PhoneSupport(BaseModel):
    """Phone support configuration"""
    number: str = Field(..., description="Phone number in E.164 format")
    display_number: Optional[str] = Field(None, max_length=30, description="Formatted display number")
    availability: Optional[str] = Field(None, max_length=100, description="Availability hours")

    @field_validator('number')
    @classmethod
    def validate_phone_number(cls, v):
        """Validate E.164 phone number format"""
        if not re.match(r'^\+[1-9]\d{6,14}$', v):
            raise ValueError('Phone number must be in E.164 format (e.g., +919876543210)')
        return v


class WhatsAppSupport(BaseModel):
    """WhatsApp support configuration"""
    enabled: bool = False
    number: Optional[str] = Field(None, description="WhatsApp number in E.164 format")
    display_number: Optional[str] = Field(None, max_length=30, description="Formatted display number")
    message_template: Optional[str] = Field(None, max_length=255, description="Pre-filled message template")

    @field_validator('number')
    @classmethod
    def validate_whatsapp_number(cls, v):
        """Validate E.164 phone number format if provided"""
        if v and not re.match(r'^\+[1-9]\d{6,14}$', v):
            raise ValueError('WhatsApp number must be in E.164 format')
        return v


class LiveChatSupport(BaseModel):
    """Live chat support configuration"""
    enabled: bool = False
    url: Optional[str] = Field(None, max_length=500, description="Live chat widget URL")


class SocialMediaItem(BaseModel):
    """Individual social media platform configuration"""
    enabled: bool = False
    url: Optional[str] = Field(None, max_length=255, description="Profile URL")
    handle: Optional[str] = Field(None, max_length=100, description="Social media handle")


class SocialMediaLinks(BaseModel):
    """Social media links configuration"""
    twitter: Optional[SocialMediaItem] = None
    instagram: Optional[SocialMediaItem] = None
    linkedin: Optional[SocialMediaItem] = None


class OfficeAddress(BaseModel):
    """Office address configuration"""
    enabled: bool = False
    address_line_1: Optional[str] = Field(None, max_length=255)
    address_line_2: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    pincode: Optional[str] = Field(None, max_length=10)
    country: Optional[str] = Field(None, max_length=100)


# ============= Request Models =============

class ContactSupportCreateRequest(BaseModel):
    """Request model for creating/updating contact support details (Admin)"""
    email: EmailSupport
    phone: PhoneSupport
    whatsapp: Optional[WhatsAppSupport] = None
    live_chat: Optional[LiveChatSupport] = None
    social_media: Optional[SocialMediaLinks] = None
    additional_info: Optional[str] = Field(None, max_length=500, description="Additional info text")
    office_address: Optional[OfficeAddress] = None

    class Config:
        json_schema_extra = {
            "example": {
                "email": {
                    "address": "support@eazr.in",
                    "subject_prefix": "Support Request - Eazr App",
                    "response_time": "Get a response within 24 hours"
                },
                "phone": {
                    "number": "+919876543210",
                    "display_number": "+91 98765 43210",
                    "availability": "Mon - Sat, 9:00 AM - 6:00 PM"
                },
                "whatsapp": {
                    "enabled": True,
                    "number": "+919876543210",
                    "display_number": "+91 98765 43210",
                    "message_template": "Hi, I need help with Eazr App"
                }
            }
        }


class ContactSupportHistoryRequest(BaseModel):
    """Request model for fetching contact support history"""
    page: int = Field(1, ge=1, description="Page number")
    limit: int = Field(10, ge=1, le=100, description="Records per page")


# ============= Response Models =============

class ContactSupportData(BaseModel):
    """Contact support data model"""
    id: str
    email: EmailSupport
    phone: PhoneSupport
    whatsapp: Optional[WhatsAppSupport] = None
    live_chat: Optional[LiveChatSupport] = None
    social_media: Optional[SocialMediaLinks] = None
    additional_info: Optional[str] = None
    office_address: Optional[OfficeAddress] = None
    updated_at: Optional[datetime] = None
    updated_by: Optional[str] = None


class ContactSupportResponse(BaseModel):
    """Response model for contact support GET endpoint"""
    success: bool
    message: str
    data: Optional[ContactSupportData] = None


class UpdatedByInfo(BaseModel):
    """Information about who made the update"""
    id: str
    email: Optional[str] = None
    name: Optional[str] = None


class ContactSupportHistoryItem(BaseModel):
    """Single history item for contact support changes"""
    id: str
    action: str  # CREATE, UPDATE
    changed_fields: List[str]
    old_values: Optional[Dict[str, Any]] = None
    new_values: Optional[Dict[str, Any]] = None
    updated_by: Optional[UpdatedByInfo] = None
    updated_at: datetime


class PaginationInfo(BaseModel):
    """Pagination information"""
    current_page: int
    total_pages: int
    total_records: int
    per_page: int


class ContactSupportHistoryData(BaseModel):
    """History data with pagination"""
    history: List[ContactSupportHistoryItem]
    pagination: PaginationInfo


class ContactSupportHistoryResponse(BaseModel):
    """Response model for contact support history endpoint"""
    success: bool
    message: str
    data: Optional[ContactSupportHistoryData] = None


class ValidationErrorItem(BaseModel):
    """Single validation error"""
    field: str
    message: str


class ContactSupportErrorResponse(BaseModel):
    """Error response model"""
    success: bool = False
    message: str
    error: Optional[str] = None
    errors: Optional[List[ValidationErrorItem]] = None
