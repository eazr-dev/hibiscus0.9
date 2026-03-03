"""
User Profile Router
Handles user profile management, updates, and account deletion

Rate Limiting Applied (Redis-backed):
- User read: 30/minute per IP
- User write: 10/minute per IP
- User delete: 5/minute per IP
"""
import logging
import time
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, HTTPException, File, UploadFile, Form, Request
from models.user import (
    UserProfileUpdateRequest,
    UserProfileUpdateResponse,
    UpdateUserProfileRequest,
    DeleteAccountRequest
)
from core.dependencies import (
    get_session,
    store_session,
    MONGODB_AVAILABLE
)
from session_security.session_manager import session_manager
from services.user_service import user_service
from core.rate_limiter import limiter, RATE_LIMITS

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(tags=["User Profile"])


@router.get("/user-profile/{session_id}")
@limiter.limit(RATE_LIMITS["user_read"])
async def get_user_profile(request: Request, session_id: str):
    """
    Get user profile with automatic session regeneration and eazr.in data

    Returns complete user profile including:
    - MongoDB stored data
    - eazr.in API data
    - Profile completion score
    - Calculated age from DOB
    """
    try:
        current_timestamp = datetime.now().isoformat()
        original_session_id = session_id

        # Auto-validate and regenerate session if needed
        session_id, session_data, was_regenerated = session_manager.validate_and_regenerate_session(
            original_session_id,
            get_session,
            store_session
        )

        if was_regenerated:
            logger.info(f"Session regenerated for profile fetch: {original_session_id} -> {session_id}")

        if not MONGODB_AVAILABLE:
            return {
                "success": False,
                "error": "MongoDB service unavailable",
                "session_id": session_id,
                "session_regenerated": was_regenerated
            }

        # Get user_id from session data
        user_id = session_data.get('user_id')
        eazr_user_id = session_data.get('eazr_user_id')
        access_token = session_data.get('access_token')

        # Debug logging for session data
        logger.info(f"Session data keys: {list(session_data.keys())}")
        logger.info(f"User ID: {user_id}, Eazr User ID: {eazr_user_id}, Access Token: {'present' if access_token else 'missing'}")

        if not user_id:
            # Try to recover user_id from MongoDB if session was regenerated
            if was_regenerated:
                from database_storage.mongodb_chat_manager import mongodb_chat_manager
                phone = session_data.get('phone')
                if phone:
                    user_doc = mongodb_chat_manager.users_collection.find_one(
                        {"preferences.phone": phone}
                    )
                    if user_doc:
                        user_id = user_doc.get('user_id')
                        eazr_user_id = user_doc.get('eazr_user_id')
                        session_data['user_id'] = user_id
                        if eazr_user_id:
                            session_data['eazr_user_id'] = eazr_user_id
                        store_session(session_id, session_data, expire_seconds=1209600)

            if not user_id:
                return {
                    "success": False,
                    "error": "User ID not found in session",
                    "session_id": session_id,
                    "session_regenerated": was_regenerated
                }

        # Get user profile using service
        try:
            profile_data = await user_service.get_user_profile(
                user_id=user_id,
                session_id=session_id,
                access_token=access_token,
                eazr_user_id=eazr_user_id
            )

            return {
                "success": True,
                **profile_data,
                "session_id": session_id,
                "session_regenerated": was_regenerated,
                "original_session_id": original_session_id if was_regenerated else None,
                "timestamp": current_timestamp
            }

        except ValueError as e:
            logger.error(f"Error getting user profile: {e}")
            # Create basic profile if not found
            from database_storage.mongodb_chat_manager import mongodb_chat_manager
            if "not found" in str(e) and session_data.get('phone'):
                profile_data = {
                    "user_id": user_id,
                    "eazr_user_id": eazr_user_id,
                    "last_session_id": session_id,
                    "session_history": [session_id],
                    "preferences": {
                        "phone": session_data.get('phone'),
                        "user_name": session_data.get('user_name', 'User'),
                        "registration_date": current_timestamp,
                        "last_login": current_timestamp,
                        "login_count": 1,
                        "profile_completion_score": 20
                    },
                    "interests": [],
                    "language_preference": "en",
                    "interaction_patterns": {},
                    "created_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc)
                }

                mongodb_chat_manager.users_collection.insert_one(profile_data)
                logger.info(f"Created new profile for user {user_id} during session regeneration")

                # Retry getting profile
                profile_data = await user_service.get_user_profile(
                    user_id=user_id,
                    session_id=session_id,
                    access_token=access_token,
                    eazr_user_id=eazr_user_id
                )

                return {
                    "success": True,
                    **profile_data,
                    "session_id": session_id,
                    "session_regenerated": was_regenerated,
                    "timestamp": current_timestamp
                }
            else:
                raise HTTPException(status_code=404, detail=str(e))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user profile: {str(e)}")

        # Create recovery session
        recovery_session = f"recovery_profile_{int(time.time())}"
        return {
            "success": False,
            "error": str(e),
            "session_id": recovery_session,
            "session_regenerated": True,
            "recovery_mode": True
        }


@router.post("/update-user-profile")
@limiter.limit(RATE_LIMITS["user_write"])
async def update_user_profile(request: Request, profile_request: UpdateUserProfileRequest):
    """
    Update user profile information

    Supports updating:
    - Basic info (name, phone, gender, DOB)
    - App version info
    - Language preference
    - Interests
    """
    try:
        session_id = profile_request.session_id

        # Validate session
        session_id, session_data, was_regenerated = session_manager.validate_and_regenerate_session(
            session_id,
            get_session,
            store_session
        )

        if not session_data or not session_data.get('active'):
            raise HTTPException(status_code=401, detail="Invalid or expired session")

        if not MONGODB_AVAILABLE:
            raise HTTPException(status_code=503, detail="MongoDB service unavailable")

        user_id = session_data.get('user_id')
        if not user_id:
            raise HTTPException(status_code=400, detail="User ID not found in session")

        # Update profile using service
        try:
            result = await user_service.update_user_profile(user_id, profile_request.profile_data)

            return {
                "success": True,
                "message": "Profile updated successfully",
                "session_id": session_id,
                "session_regenerated": was_regenerated
            }

        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user profile: {str(e)}")
        raise HTTPException(status_code=500, detail="Profile update failed")


@router.post("/update-user-profile-with-picture")
@limiter.limit(RATE_LIMITS["user_write"])
async def update_user_profile_with_picture(
    request: Request,
    full_name: Optional[str] = Form(None),
    gender: Optional[str] = Form(None),
    dob: Optional[str] = Form(None),
    age: Optional[str] = Form(None),  # Accept as string, will convert to int
    language_preference: Optional[str] = Form(None),
    interests: Optional[str] = Form(None),
    session_id: str = Form(...),
    user_id: int = Form(...),
    profile_pic: Optional[UploadFile] = File(None)
):
    """
    Update user profile with optional picture upload to S3

    Supports:
    - Profile picture upload to S3 bucket
    - All profile fields with validation
    - Comma-separated interests
    - Multiple date formats for DOB
    - Auto-calculated age from DOB
    - Gender normalization
    """
    try:
        current_timestamp = datetime.now().isoformat()

        # Validate session
        session_id, session_data, was_regenerated = session_manager.validate_and_regenerate_session(
            session_id,
            get_session,
            store_session
        )

        if not session_data or not session_data.get('active'):
            logger.warning(f"Session {session_id} not found or inactive, proceeding with user_id {user_id}")

        if not MONGODB_AVAILABLE:
            raise HTTPException(status_code=503, detail="MongoDB service unavailable")

        # Update profile using service with S3 upload support
        try:
            result = await user_service.update_profile_with_picture_enhanced(
                user_id=user_id,
                session_id=session_id,
                full_name=full_name,
                gender=gender,
                dob=dob,
                age=age,
                language_preference=language_preference,
                interests=interests,
                profile_picture=profile_pic,
                current_timestamp=current_timestamp
            )

            return {
                "success": True,
                "message": result["message"],
                "user_id": user_id,
                "session_id": session_id,
                "session_regenerated": was_regenerated,
                "updated_fields": result["updated_fields"],
                "profile": result["profile"],
                "timestamp": current_timestamp
            }

        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating profile with picture: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Profile update failed: {str(e)}")


@router.post("/delete-account")
@limiter.limit(RATE_LIMITS["user_delete"])
async def delete_account(request: Request, delete_request: DeleteAccountRequest):
    """
    Delete user account with proper cleanup

    Soft delete that:
    - Marks account as deleted
    - Backs up user data
    - Deactivates sessions
    - Preserves data for recovery (30 days)
    """
    try:
        # Validate session
        session_id, session_data, was_regenerated = session_manager.validate_and_regenerate_session(
            delete_request.session_id,
            get_session,
            store_session
        )

        if not session_data or not session_data.get('active'):
            raise HTTPException(status_code=401, detail="Invalid or expired session")

        if not delete_request.confirm:
            raise HTTPException(status_code=400, detail="Account deletion must be confirmed")

        if not MONGODB_AVAILABLE:
            raise HTTPException(status_code=503, detail="MongoDB service unavailable")

        user_id = delete_request.user_id

        # Verify user_id matches session
        if session_data.get('user_id') != user_id:
            raise HTTPException(status_code=403, detail="User ID mismatch")

        # Delete account using service
        try:
            result = await user_service.delete_user_account(
                user_id=user_id,
                session_id=session_id,
                reason=delete_request.reason
            )

            return {
                "success": True,
                "message": "Account deleted successfully",
                **result
            }

        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting account: {str(e)}")
        raise HTTPException(status_code=500, detail="Account deletion failed")


@router.patch("/user-profile/{session_id}", response_model=UserProfileUpdateResponse)
@limiter.limit(RATE_LIMITS["user_write"])
async def update_user_profile_patch(request: Request, session_id: str, update_request: UserProfileUpdateRequest):
    """
    Update user profile with PATCH method (allows partial updates including null values)

    This endpoint supports:
    - Partial updates (only send fields to update)
    - Null values to clear fields
    - Auto-calculated age from DOB
    - Gender validation and normalization
    - Profile completion score calculation
    - Session regeneration support
    """
    try:
        current_timestamp = datetime.now().isoformat()
        original_session_id = session_id

        # Auto-validate and regenerate session if needed
        session_id, session_data, was_regenerated = session_manager.validate_and_regenerate_session(
            original_session_id,
            get_session,
            store_session
        )

        if was_regenerated:
            logger.info(f"Session regenerated for profile update: {original_session_id} -> {session_id}")

        if not MONGODB_AVAILABLE:
            raise HTTPException(
                status_code=503,
                detail="MongoDB service unavailable",
                headers={"X-Session-Id": session_id, "X-Session-Regenerated": str(was_regenerated)}
            )

        # Get user_id from session
        user_id = session_data.get('user_id')
        if not user_id:
            # Try to recover user_id
            if was_regenerated:
                from database_storage.mongodb_chat_manager import mongodb_chat_manager
                phone = session_data.get('phone')
                if phone:
                    user_doc = mongodb_chat_manager.users_collection.find_one(
                        {"preferences.phone": phone}
                    )
                    if user_doc:
                        user_id = user_doc.get('user_id')
                        session_data['user_id'] = user_id
                        store_session(session_id, session_data, expire_seconds=1209600)

            if not user_id:
                raise HTTPException(
                    status_code=400,
                    detail="User ID not found in session",
                    headers={"X-Session-Id": session_id, "X-Session-Regenerated": str(was_regenerated)}
                )

        # Use service to update profile
        result = await user_service.update_user_profile_patch(
            user_id=user_id,
            update_request=update_request,
            session_id=session_id,
            current_timestamp=current_timestamp
        )

        # Add session info to response
        result['session_id'] = session_id
        result['session_regenerated'] = was_regenerated
        result['original_session_id'] = original_session_id if was_regenerated else None
        result['timestamp'] = current_timestamp

        return UserProfileUpdateResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user profile: {str(e)}")

        recovery_session = f"recovery_update_{int(time.time())}"
        raise HTTPException(
            status_code=500,
            detail=str(e),
            headers={
                "X-Session-Id": recovery_session,
                "X-Session-Regenerated": "true",
                "X-Recovery-Mode": "true"
            }
        )


@router.get("/user-profile/{session_id}/completion-status")
@limiter.limit(RATE_LIMITS["user_read"])
async def get_profile_completion_status(request: Request, session_id: str):
    """
    Get detailed profile completion status

    Returns:
    - Completion percentage
    - Missing fields
    - Suggestions for completion
    """
    try:
        # Validate session
        session_id, session_data, was_regenerated = session_manager.validate_and_regenerate_session(
            session_id,
            get_session,
            store_session
        )

        if not session_data or not session_data.get('active'):
            raise HTTPException(status_code=401, detail="Invalid or expired session")

        if not MONGODB_AVAILABLE:
            raise HTTPException(status_code=503, detail="MongoDB service unavailable")

        user_id = session_data.get('user_id')
        if not user_id:
            raise HTTPException(status_code=400, detail="User ID not found in session")

        # Get completion status using service
        try:
            status = await user_service.get_profile_completion_status(user_id)

            return {
                "success": True,
                **status,
                "session_id": session_id,
                "session_regenerated": was_regenerated
            }

        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting completion status: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get completion status")


@router.get("/user-documents/{userId}")
@limiter.limit(RATE_LIMITS["user_read"])
async def get_user_uploaded_documents(
    request: Request,
    userId: str,
    limit: Optional[int] = 50,
    skip: Optional[int] = 0,
    file_type: Optional[str] = None,
    insurance_type: Optional[str] = None
):
    """
    Get all uploaded documents for a specific user with original and analysis report URLs

    Parameters:
    - userId: User ID
    - limit: Number of documents to return (default: 50)
    - skip: Number of documents to skip for pagination (default: 0)
    - file_type: Filter by file type (pdf, image)
    - insurance_type: Filter by insurance type (health, auto, life)

    Returns:
    - List of documents with original_document_url and analysis_report_url
    """
    try:
        # Try to get database connection
        from database_storage.mongodb_chat_manager import mongodb_chat_manager

        if mongodb_chat_manager is None:
            raise HTTPException(status_code=503, detail="Database connection not available")

        # Build query - use user_id (not userId) and convert to int
        try:
            user_id_int = int(userId)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid user ID format")

        query = {"user_id": user_id_int}

        if file_type:
            query["file_type"] = file_type

        if insurance_type:
            query["policy_type"] = insurance_type

        # Get policy collection - use the correct collection name
        policy_collection = mongodb_chat_manager.policy_analysis_collection

        # Log query for debugging
        logger.info(f"Querying policy_analysis_collection with: {query}")

        # Count total documents
        total_count = policy_collection.count_documents(query)
        logger.info(f"Found {total_count} documents for user {userId}")

        # Fetch documents with pagination
        cursor = policy_collection.find(query).sort("created_at", -1).skip(skip).limit(limit)

        documents = []
        reports = []

        for doc in cursor:
            # Log document ID for debugging
            logger.info(f"Processing document: {doc.get('_id')}, filename: {doc.get('filename')}")

            # Extract filename - use 'filename' field (not 'uploaded_filename')
            original_filename = doc.get("filename")

            # Get original file URL from 'original_file_url' field
            original_file_url = doc.get("original_file_url")

            # For the report URL, we use 'report_url' field (not 'analysis_report_url')
            report_url = doc.get("report_url")

            # Get report filename from 'report_filename' field
            report_filename = doc.get("report_filename")

            # Create document entry (original uploaded file)
            document_entry = {
                "id": str(doc.get("_id")),
                "report_id": doc.get("report_id"),
                "name": original_filename,
                "url": original_file_url,  # S3 URL for original uploaded PDF
                "file_type": "pdf",  # All uploaded insurance documents are PDFs
                "uploaded_at": doc.get("created_at").isoformat() if doc.get("created_at") else None,
                "uin": doc.get("uin"),
                "policy_type": doc.get("policy_type"),
                "session_id": doc.get("session_id")
            }
            documents.append(document_entry)

            # Create report entry (analysis report) - only if analysis was done
            if report_url:
                report_entry = {
                    "id": str(doc.get("_id")),
                    "report_id": doc.get("report_id"),
                    "name": report_filename,
                    "url": report_url,
                    "original_document_id": str(doc.get("_id")),
                    "original_document_name": original_filename,

                    # Analysis summary
                    "uin": doc.get("uin"),
                    "policy_type": doc.get("policy_type"),
                    "session_id": doc.get("session_id"),

                    "created_at": doc.get("created_at").isoformat() if doc.get("created_at") else None
                }
                reports.append(report_entry)
        data = {
            "success": True,
            "userId": userId,
            "total_documents": total_count,
            "returned_count": len(documents),
            "skip": skip,
            "limit": limit,
            "documents": documents,
            "reports": reports
        }

        print('ssssssss',data)

        return {
            "success": True,
            "userId": userId,
            "total_documents": total_count,
            "returned_count": len(documents),
            "skip": skip,
            "limit": limit,
            "documents": documents,
            "reports": reports
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving documents for user {userId}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving documents: {str(e)}")


@router.get("/user-documents/{userId}/summary")
@limiter.limit(RATE_LIMITS["user_read"])
async def get_user_documents_summary(request: Request, userId: str):
    """
    Get summary of user's uploaded documents

    Parameters:
    - userId: User ID

    Returns:
    - Summary statistics and document counts
    """
    try:
        # Try to get database connection
        from database_storage.mongodb_chat_manager import insurance_db

        if insurance_db is None:
            raise HTTPException(status_code=503, detail="Database connection not available")

        policy_collection = insurance_db['policy_analyses']

        # Get total count
        total_documents = policy_collection.count_documents({"userId": userId})

        # Count by file type
        pdf_count = policy_collection.count_documents({"userId": userId, "file_type": "pdf"})
        image_count = policy_collection.count_documents({"userId": userId, "file_type": "image"})

        # Count by insurance type
        health_count = policy_collection.count_documents({"userId": userId, "insurance_type": "health"})
        auto_count = policy_collection.count_documents({"userId": userId, "insurance_type": "auto"})
        life_count = policy_collection.count_documents({"userId": userId, "insurance_type": "life"})

        # Get latest document
        latest_doc = policy_collection.find_one(
            {"userId": userId},
            sort=[("created_at", -1)]
        )

        return {
            "success": True,
            "userId": userId,
            "summary": {
                "total_documents": total_documents,
                "by_file_type": {
                    "pdf": pdf_count,
                    "image": image_count
                },
                "by_insurance_type": {
                    "health": health_count,
                    "auto": auto_count,
                    "life": life_count
                },
                "latest_upload": {
                    "filename": latest_doc.get("uploaded_filename") if latest_doc else None,
                    "uploaded_at": latest_doc.get("created_at").isoformat() if latest_doc and latest_doc.get("created_at") else None,
                    "insurance_type": latest_doc.get("insurance_type") if latest_doc else None
                } if latest_doc else None
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving summary for user {userId}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving summary: {str(e)}")
