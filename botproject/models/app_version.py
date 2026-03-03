"""
App version management Pydantic models
"""
from pydantic import BaseModel, validator
from typing import Optional, List


class AppVersionCreate(BaseModel):
    platform: str
    version_number: str
    version_name: Optional[str] = None
    build_number: Optional[str] = None
    release_notes: Optional[str] = None
    download_url: Optional[str] = None
    features: Optional[List[str]] = None
    bug_fixes: Optional[List[str]] = None
    minimum_supported: bool = True
    force_update: bool = False

    @validator('platform')
    def validate_platform(cls, v):
        if v.lower() not in ['ios', 'android']:
            raise ValueError('Platform must be either "ios" or "android"')
        return v.lower()


class AppVersionUpdate(BaseModel):
    version_name: Optional[str] = None
    build_number: Optional[str] = None
    release_notes: Optional[str] = None
    download_url: Optional[str] = None
    features: Optional[List[str]] = None
    bug_fixes: Optional[List[str]] = None
    minimum_supported: Optional[bool] = None
    force_update: Optional[bool] = None
    status: Optional[str] = None

    @validator('status')
    def validate_status(cls, v):
        if v and v not in ['active', 'deprecated', 'discontinued']:
            raise ValueError('Status must be "active", "deprecated", or "discontinued"')
        return v


class VersionCheckRequest(BaseModel):
    platform: str
    version_number: str

    @validator('platform')
    def validate_platform(cls, v):
        if v.lower() not in ['ios', 'android']:
            raise ValueError('Platform must be either "ios" or "android"')
        return v.lower()
