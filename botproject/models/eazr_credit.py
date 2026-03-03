"""
Eazr Credit Waitlist - Pydantic Models
Models for managing user waitlist for Eazr Credit feature
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# ==================== REQUEST MODELS ====================

class JoinWaitlistRequest(BaseModel):
    """Request to join the Eazr Credit waitlist"""
    user_id: int = Field(..., description="User's unique ID from session")

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": 12345
            }
        }


# ==================== RESPONSE DATA MODELS ====================

class WaitlistData(BaseModel):
    """Waitlist entry data structure"""
    user_id: int = Field(..., description="User's unique ID")
    is_waitlisted: bool = Field(..., description="True if user is on waitlist")
    waitlist_id: Optional[str] = Field(None, description="Unique waitlist entry ID (null if not waitlisted)")
    position: Optional[int] = Field(None, description="User's position in waitlist (null if not waitlisted)")
    joined_at: Optional[str] = Field(None, description="ISO 8601 timestamp when user joined (null if not waitlisted)")

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": 12345,
                "is_waitlisted": True,
                "waitlist_id": "WL-2024-001234",
                "position": 10542,
                "joined_at": "2024-12-18T10:30:00Z"
            }
        }


# ==================== RESPONSE MODELS ====================

class WaitlistResponse(BaseModel):
    """Standard waitlist API response"""
    success: bool = Field(..., description="API call success status")
    message: str = Field(..., description="Human readable message")
    data: Optional[WaitlistData] = Field(None, description="Waitlist data object")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Successfully joined the waitlist",
                "data": {
                    "user_id": 12345,
                    "is_waitlisted": True,
                    "waitlist_id": "WL-2024-001234",
                    "position": 10542,
                    "joined_at": "2024-12-18T10:30:00Z"
                }
            }
        }


class WaitlistStatusResponse(BaseModel):
    """Response for checking waitlist status"""
    success: bool = Field(..., description="API call success status")
    message: str = Field(..., description="Human readable message")
    data: WaitlistData = Field(..., description="Waitlist status data")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "User waitlist status retrieved",
                "data": {
                    "user_id": 12345,
                    "is_waitlisted": True,
                    "waitlist_id": "WL-2024-001234",
                    "position": 10542,
                    "joined_at": "2024-12-15T08:20:00Z"
                }
            }
        }


class WaitlistErrorResponse(BaseModel):
    """Error response for waitlist API"""
    success: bool = Field(False, description="Always False for errors")
    message: str = Field(..., description="Error message")
    data: Optional[WaitlistData] = Field(None, description="May contain existing waitlist data for 409 conflict")

    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "message": "You are already on the waitlist",
                "data": {
                    "user_id": 12345,
                    "is_waitlisted": True,
                    "waitlist_id": "WL-2024-001234",
                    "position": 10542,
                    "joined_at": "2024-12-15T08:20:00Z"
                }
            }
        }
