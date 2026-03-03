"""
Pydantic models for the Eazr Financial Assistant API
"""
from .auth import (
    SendOTPRequest,
    SendOTPResponse,
    VerifyOTPRequest,
    VerifyOTPResponse,
    CheckSessionRequest,
    AppVersionInfo
)

from .chat import (
    ServiceSelectionRequest,
    QueryInput,
    QuickActionRequest,
    ChatbotContinue,
    ChatHistoryRequest,
    SearchChatRequest,
    ClearChatRequest,
    UpdateChatTitleRequest,
    LoadChatRequest,
    DeleteChatRequest,
    SearchChatsRequest,
    ClearUserChatRequest
)

from .user import (
    UpdateUserProfileRequest,
    UserProfileUpdateRequest,
    UserProfileUpdateResponse,
    DeleteAccountRequest
)

from .mongodb_models import (
    MongoDBChatHistoryRequest,
    MongoDBSearchChatRequest,
    MongoDBClearChatRequest,
    MongoDBUpdateUserProfileRequest,
    MongoDBUserStatsRequest
)

from .app_version import (
    AppVersionCreate,
    AppVersionUpdate,
    VersionCheckRequest
)

from .insurance import (
    ClaimGuidanceRequest
)

from .contact_support import (
    EmailSupport,
    PhoneSupport,
    WhatsAppSupport,
    LiveChatSupport,
    SocialMediaItem,
    SocialMediaLinks,
    OfficeAddress,
    ContactSupportCreateRequest,
    ContactSupportHistoryRequest,
    ContactSupportData,
    ContactSupportResponse,
    ContactSupportHistoryItem,
    ContactSupportHistoryResponse
)

__all__ = [
    # Auth models
    "SendOTPRequest",
    "SendOTPResponse",
    "VerifyOTPRequest",
    "VerifyOTPResponse",
    "CheckSessionRequest",
    "AppVersionInfo",

    # Chat models
    "ServiceSelectionRequest",
    "QueryInput",
    "QuickActionRequest",
    "ChatbotContinue",
    "ChatHistoryRequest",
    "SearchChatRequest",
    "ClearChatRequest",
    "UpdateChatTitleRequest",
    "LoadChatRequest",
    "DeleteChatRequest",
    "SearchChatsRequest",
    "ClearUserChatRequest",

    # User models
    "UpdateUserProfileRequest",
    "UserProfileUpdateRequest",
    "UserProfileUpdateResponse",
    "DeleteAccountRequest",

    # MongoDB models
    "MongoDBChatHistoryRequest",
    "MongoDBSearchChatRequest",
    "MongoDBClearChatRequest",
    "MongoDBUpdateUserProfileRequest",
    "MongoDBUserStatsRequest",

    # App version models
    "AppVersionCreate",
    "AppVersionUpdate",
    "VersionCheckRequest",

    # Insurance models
    "ClaimGuidanceRequest",

    # Contact Support models
    "EmailSupport",
    "PhoneSupport",
    "WhatsAppSupport",
    "LiveChatSupport",
    "SocialMediaItem",
    "SocialMediaLinks",
    "OfficeAddress",
    "ContactSupportCreateRequest",
    "ContactSupportHistoryRequest",
    "ContactSupportData",
    "ContactSupportResponse",
    "ContactSupportHistoryItem",
    "ContactSupportHistoryResponse"
]
