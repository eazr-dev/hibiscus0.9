"""
Utilities Package
Common utility functions used across the application
"""

# Import all utilities for easy access
from .phone_utils import (
    normalize_phone_number,
    add_country_code,
    validate_phone_number,
    mask_phone_number
)

from .date_utils import (
    calculate_age,
    get_current_timestamp,
    format_datetime,
    days_between
)

from .validators import (
    validate_email,
    validate_otp,
    validate_user_id,
    validate_session_id,
    sanitize_input
)

from .file_utils import (
    get_file_extension,
    validate_file_type,
    generate_unique_filename,
    get_file_size_mb,
    is_image_file,
    is_document_file
)

from .response_utils import (
    create_success_response,
    create_error_response,
    paginate_response,
    format_api_response
)

from .session_utils import (
    generate_session_id,
    extract_user_from_session,
    is_session_expired,
    calculate_session_expiry,
    create_session_data
)

from .string_utils import (
    slugify,
    truncate_text,
    mask_sensitive_data,
    generate_random_string,
    capitalize_words,
    remove_extra_spaces
)

# Token utils - import from root level token_genrations.py
# from .token_utils import (
#     generate_user_id,
#     create_user_token,
#     verify_user_token,
#     create_admin_token,
#     verify_admin_token,
#     create_jwt_token,  # Legacy alias
#     verify_jwt_token   # Legacy alias
# )

# Authentication verification
from .auth_verification import (
    verify_user_authentication,
    create_auth_error_response,
    should_verify_token
)

__all__ = [
    # Phone utils
    'normalize_phone_number',
    'add_country_code',
    'validate_phone_number',
    'mask_phone_number',

    # Date utils
    'calculate_age',
    'get_current_timestamp',
    'format_datetime',
    'days_between',

    # Validators
    'validate_email',
    'validate_otp',
    'validate_user_id',
    'validate_session_id',
    'sanitize_input',

    # File utils
    'get_file_extension',
    'validate_file_type',
    'generate_unique_filename',
    'get_file_size_mb',
    'is_image_file',
    'is_document_file',

    # Response utils
    'create_success_response',
    'create_error_response',
    'paginate_response',
    'format_api_response',

    # Session utils
    'generate_session_id',
    'extract_user_from_session',
    'is_session_expired',
    'calculate_session_expiry',
    'create_session_data',

    # String utils
    'slugify',
    'truncate_text',
    'mask_sensitive_data',
    'generate_random_string',
    'capitalize_words',
    'remove_extra_spaces',

    # Token utils - commented out
    # 'generate_user_id',
    # 'create_user_token',
    # 'verify_user_token',
    # 'create_admin_token',
    # 'verify_admin_token',
    # 'create_jwt_token',  # Legacy alias
    # 'verify_jwt_token',  # Legacy alias

    # Authentication verification
    'verify_user_authentication',
    'create_auth_error_response',
    'should_verify_token',
]
