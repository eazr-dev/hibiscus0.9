"""
User Policies Router
API endpoints for fetching user's uploaded policies
"""
import logging
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Header, Query, Body
from pydantic import BaseModel
from datetime import datetime

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api", tags=["User Policies"])


# Pydantic model for remove policy request
class RemovePolicyRequest(BaseModel):
    policyId: str
    userId: str


@router.get("/user/policies")
async def get_user_policies(
    userId: str = Query(..., description="User ID"),
    access_token: Optional[str] = Header(None, description="Access token", alias="access-token"),
    authorization: Optional[str] = Header(None, description="Bearer token", alias="Authorization"),
    category: Optional[str] = Query(None, description="Filter by category: life, health, motor, general, agricultural, business, specialty, other"),
    status: Optional[str] = Query(None, description="Filter by status: active, expired, pending"),
    policyFor: Optional[str] = Query(None, description="Filter by owner: self, family")
):
    """
    Get All User Policies

    Returns all policies uploaded by the user with portfolio overview and breakdown.

    **Headers (Optional):**
    - access-token: {token}
    - Authorization: Bearer {token}

    **Query Parameters:**
    - userId: User ID (required)
    - category: Filter by policy type (optional)
    - status: Filter by policy status (optional)
    - policyFor: Filter by owner type (optional)

    **Returns:**
    - Portfolio overview (total policies, active count, total coverage)
    - Portfolio breakdown by category
    - List of all policies with details
    """
    try:
        # Authentication check
        has_access_token = bool(access_token)
        has_auth = bool(authorization and authorization.startswith("Bearer "))

        if has_access_token:
            logger.info(f"Request authenticated with access-token header")
        elif has_auth:
            logger.info(f"Request authenticated with Authorization Bearer token")
        else:
            logger.info(f"Request without authentication (testing mode)")

        # Convert userId to int
        try:
            user_id_int = int(userId)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail={
                    "success": False,
                    "error_code": "VAL_2001",
                    "message": "userId must be a valid number"
                }
            )

        # Import MongoDB service
        from services.policy_locker_service import policy_locker_service
        from database_storage.mongodb_chat_manager import mongodb_chat_manager

        if mongodb_chat_manager is None or mongodb_chat_manager.db is None:
            raise HTTPException(status_code=503, detail="Database not available")

        # Get all policies for user
        db = mongodb_chat_manager.db
        policy_analysis_collection = db['policy_analysis']

        # Build query
        query = {"user_id": user_id_int}

        # Exclude soft-deleted policies
        query["$or"] = [
            {"isDeleted": {"$exists": False}},
            {"isDeleted": False}
        ]

        # Add policyFor filter
        # Default to "self" if not specified
        if policyFor:
            query["policyFor"] = policyFor
        else:
            # Default: show only self policies
            query["policyFor"] = "self"

        # Fetch all policies
        policies_cursor = policy_analysis_collection.find(query).sort("created_at", -1)
        policies = list(policies_cursor)

        # Initialize counters
        total_policies = 0
        active_policies = 0
        total_coverage = 0

        # Category breakdown - All policy types
        category_breakdown = {
            "life": {"count": 0, "coverage": 0, "premium": 0},
            "health": {"count": 0, "coverage": 0, "premium": 0},
            "motor": {"count": 0, "coverage": 0, "premium": 0},
            "general": {"count": 0, "coverage": 0, "premium": 0},
            "agricultural": {"count": 0, "coverage": 0, "premium": 0},
            "business": {"count": 0, "coverage": 0, "premium": 0},
            "specialty": {"count": 0, "coverage": 0, "premium": 0},
            "other": {"count": 0, "coverage": 0, "premium": 0}
        }

        # Format policies
        formatted_policies = []

        for policy in policies:
            # Get extracted data
            extracted_data = policy.get("extractedData", {})

            # Determine policy category
            policy_type = extracted_data.get("policyType", "unknown").lower()

            # Map policy type to category
            if policy_type in ["health", "medical", "mediclaim"]:
                policy_category = "health"
                icon_color = "green"
            elif policy_type in ["life", "term", "endowment", "ulip", "whole life"]:
                policy_category = "life"
                icon_color = "blue"
            elif policy_type in ["motor", "car", "vehicle", "bike", "two-wheeler", "four-wheeler", "auto"]:
                policy_category = "motor"
                icon_color = "purple"
            elif policy_type in ["general", "home", "property", "fire", "burglary", "travel", "personal accident"]:
                policy_category = "general"
                icon_color = "orange"
            elif policy_type in ["agricultural", "crop", "livestock", "farm"]:
                policy_category = "agricultural"
                icon_color = "brown"
            elif policy_type in ["business", "commercial", "liability", "professional indemnity", "cyber"]:
                policy_category = "business"
                icon_color = "indigo"
            elif policy_type in ["specialty", "marine", "aviation", "engineering"]:
                policy_category = "specialty"
                icon_color = "teal"
            else:
                policy_category = "other"
                icon_color = "gray"

            # Apply category filter
            if category and policy_category != category:
                continue

            # Get coverage and premium
            coverage = extracted_data.get("coverageAmount", 0)
            premium = extracted_data.get("premium", 0)

            # Determine status based on start and end dates (matching /api/policy/upload logic)
            start_date_str = extracted_data.get("startDate", "")
            end_date_str = extracted_data.get("endDate", "")
            policy_status = "active"  # Default

            try:
                if start_date_str and end_date_str:
                    current_date = datetime.now().date()

                    # Parse dates (handle both YYYY-MM-DD and DD-MM-YYYY formats)
                    if "-" in start_date_str:
                        parts = start_date_str.split("-")
                        if len(parts[0]) == 4:  # YYYY-MM-DD
                            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
                        else:  # DD-MM-YYYY
                            start_date = datetime.strptime(start_date_str, "%d-%m-%Y").date()
                    else:
                        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()

                    if "-" in end_date_str:
                        parts = end_date_str.split("-")
                        if len(parts[0]) == 4:  # YYYY-MM-DD
                            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
                        else:  # DD-MM-YYYY
                            end_date = datetime.strptime(end_date_str, "%d-%m-%Y").date()
                    else:
                        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()

                    # Determine status
                    if current_date < start_date:
                        policy_status = "upcoming"
                    elif current_date > end_date:
                        policy_status = "expired"
                    else:
                        policy_status = "active"
            except Exception as e:
                logger.warning(f"Could not parse policy dates: {str(e)}")
                policy_status = "active"  # Default if parsing fails

            # Apply status filter
            if status and policy_status != status:
                continue

            # Get protection score from saved data (or calculate if not present)
            protection_score = policy.get("protectionScore")
            if protection_score is None:
                # Fallback: Calculate from gaps if not stored
                gaps = policy.get("gapAnalysis", [])
                total_gaps = len(gaps)
                if total_gaps == 0:
                    protection_score = 100
                elif total_gaps <= 2:
                    protection_score = 90
                elif total_gaps <= 4:
                    protection_score = 75
                else:
                    protection_score = 60

            # Get gap count
            gaps = policy.get("gapAnalysis", [])
            total_gaps = len(gaps)

            # Get policy holder info
            policy_holder = policy.get("policyHolder", {})
            policy_holder_name = extracted_data.get("policyHolderName") or policy_holder.get("name", "N/A")
            insured_name = extracted_data.get("insuredName", policy_holder_name)

            # Get relationship (from policyHolder or default to self)
            relationship = policy_holder.get("relationship", "self")

            # Format policy data
            policy_data = {
                "policyId": policy.get("analysisId", ""),
                "policyName": extracted_data.get("insuranceProvider", "Unknown Policy"),
                "policyType": policy_type.title(),
                "category": policy_category,
                "provider": extracted_data.get("insuranceProvider", "Unknown"),
                "policyNumber": extracted_data.get("policyNumber", "N/A"),
                "policyHolderName": policy_holder_name,
                "insuredName": insured_name,
                "coverage": coverage,
                "sumAssured": coverage,
                "premium": premium,
                "premiumFrequency": extracted_data.get("premiumFrequency", "annually"),
                "startDate": extracted_data.get("startDate", ""),
                "endDate": end_date_str,
                "status": policy_status,
                "relationship": relationship,  # Added relationship field
                "protectionScore": protection_score,
                "gaps": total_gaps,
                "iconColor": icon_color,
                "uploadedAt": policy.get("created_at", datetime.now()).isoformat() if isinstance(policy.get("created_at"), datetime) else str(policy.get("created_at", "")),
                "policyFor": policy.get("policyFor", "self")
            }

            formatted_policies.append(policy_data)

            # Update counters
            total_policies += 1
            if policy_status == "active":
                active_policies += 1
                total_coverage += coverage

            # Update category breakdown
            if policy_category in category_breakdown:
                category_breakdown[policy_category]["count"] += 1
                category_breakdown[policy_category]["coverage"] += coverage
                category_breakdown[policy_category]["premium"] += premium

        # Build response
        response = {
            "success": True,
            "userId": userId,
            "portfolioOverview": {
                "totalPolicies": total_policies,
                "activePolicies": active_policies,
                "totalCoverage": total_coverage,
                "totalCoverageFormatted": f"₹{total_coverage/10000000:.1f}Cr" if total_coverage >= 10000000 else f"₹{total_coverage/100000:.1f}L"
            },
            "portfolioBreakdown": {
                "life": {
                    "count": category_breakdown["life"]["count"],
                    "coverage": category_breakdown["life"]["coverage"],
                    "premium": category_breakdown["life"]["premium"],
                    "percentage": round((category_breakdown["life"]["coverage"] / total_coverage * 100) if total_coverage > 0 else 0, 1)
                },
                "health": {
                    "count": category_breakdown["health"]["count"],
                    "coverage": category_breakdown["health"]["coverage"],
                    "premium": category_breakdown["health"]["premium"],
                    "percentage": round((category_breakdown["health"]["coverage"] / total_coverage * 100) if total_coverage > 0 else 0, 1)
                },
                "motor": {
                    "count": category_breakdown["motor"]["count"],
                    "coverage": category_breakdown["motor"]["coverage"],
                    "premium": category_breakdown["motor"]["premium"],
                    "percentage": round((category_breakdown["motor"]["coverage"] / total_coverage * 100) if total_coverage > 0 else 0, 1)
                },
                "general": {
                    "count": category_breakdown["general"]["count"],
                    "coverage": category_breakdown["general"]["coverage"],
                    "premium": category_breakdown["general"]["premium"],
                    "percentage": round((category_breakdown["general"]["coverage"] / total_coverage * 100) if total_coverage > 0 else 0, 1)
                },
                "agricultural": {
                    "count": category_breakdown["agricultural"]["count"],
                    "coverage": category_breakdown["agricultural"]["coverage"],
                    "premium": category_breakdown["agricultural"]["premium"],
                    "percentage": round((category_breakdown["agricultural"]["coverage"] / total_coverage * 100) if total_coverage > 0 else 0, 1)
                },
                "business": {
                    "count": category_breakdown["business"]["count"],
                    "coverage": category_breakdown["business"]["coverage"],
                    "premium": category_breakdown["business"]["premium"],
                    "percentage": round((category_breakdown["business"]["coverage"] / total_coverage * 100) if total_coverage > 0 else 0, 1)
                },
                "specialty": {
                    "count": category_breakdown["specialty"]["count"],
                    "coverage": category_breakdown["specialty"]["coverage"],
                    "premium": category_breakdown["specialty"]["premium"],
                    "percentage": round((category_breakdown["specialty"]["coverage"] / total_coverage * 100) if total_coverage > 0 else 0, 1)
                },
                "other": {
                    "count": category_breakdown["other"]["count"],
                    "coverage": category_breakdown["other"]["coverage"],
                    "premium": category_breakdown["other"]["premium"],
                    "percentage": round((category_breakdown["other"]["coverage"] / total_coverage * 100) if total_coverage > 0 else 0, 1)
                }
            },
            "policies": formatted_policies
        }

        return response

    except HTTPException as he:
        raise he

    except Exception as e:
        logger.error(f"Error fetching user policies: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error_code": "SRV_5001",
                "message": "Failed to fetch policies"
            }
        )


@router.get("/user/policies/{policyId}")
async def get_policy_details(
    policyId: str,
    userId: str = Query(..., description="User ID"),
    access_token: Optional[str] = Header(None, alias="access-token"),
    authorization: Optional[str] = Header(None, alias="Authorization")
):
    """
    Get Detailed Policy Information

    Returns complete details for a specific policy including gap analysis.

    **Headers (Optional):**
    - access-token: {token}
    - Authorization: Bearer {token}

    **Returns:**
    - Complete policy details
    - Coverage information
    - Gap analysis with recommendations
    """
    try:
        # Convert userId to int
        user_id_int = int(userId)

        # Import MongoDB
        from database_storage.mongodb_chat_manager import mongodb_chat_manager

        if mongodb_chat_manager is None or mongodb_chat_manager.db is None:
            raise HTTPException(status_code=503, detail="Database not available")

        db = mongodb_chat_manager.db
        policy_analysis_collection = db['policy_analysis']

        # Fetch policy (exclude soft-deleted)
        # Try multiple query approaches to find the policy
        policy = None

        # Approach 1: Try with analysisId field
        policy = policy_analysis_collection.find_one({
            "analysisId": policyId,
            "user_id": user_id_int,
            "$or": [
                {"isDeleted": {"$exists": False}},
                {"isDeleted": False}
            ]
        })

        # Approach 2: If not found, try with _id field (some policies might use _id)
        if not policy:
            policy = policy_analysis_collection.find_one({
                "_id": policyId,
                "user_id": user_id_int,
                "$or": [
                    {"isDeleted": {"$exists": False}},
                    {"isDeleted": False}
                ]
            })

        # Approach 3: If still not found, search without user_id to see if policy exists
        if not policy:
            logger.warning(f"Policy {policyId} not found for user {user_id_int}, checking if it exists for other users...")
            any_policy = policy_analysis_collection.find_one({"analysisId": policyId})
            if any_policy:
                logger.error(f"Policy {policyId} exists but belongs to user {any_policy.get('user_id')}, not {user_id_int}")
                raise HTTPException(
                    status_code=403,
                    detail={
                        "success": False,
                        "error_code": "AUTH_1005",
                        "message": "Policy not found or does not belong to this user"
                    }
                )

        if not policy:
            # Check if ANY policies exist for this user
            user_policy_count = policy_analysis_collection.count_documents({"user_id": user_id_int})
            logger.error(f"Policy {policyId} not found. User {user_id_int} has {user_policy_count} total policies.")

            raise HTTPException(
                status_code=404,
                detail={
                    "success": False,
                    "error_code": "RES_3001",
                    "message": "Policy not found"
                }
            )

        # Get extracted data
        extracted_data = policy.get("extractedData", {})
        gaps = policy.get("gapAnalysis", [])
        summary = policy.get("summary", {})
        protection_score = policy.get("protectionScore", 100)

        # Format gaps
        formatted_gaps = []
        high_count = 0
        medium_count = 0
        low_count = 0
        total_cost = 0

        for idx, gap in enumerate(gaps):
            estimated_cost_raw = gap.get("estimatedCost", 0)

            # Convert to number
            try:
                if isinstance(estimated_cost_raw, str):
                    estimated_cost_raw = estimated_cost_raw.replace('₹', '').replace('$', '').replace(',', '').strip()
                    estimated_cost = float(estimated_cost_raw) if '.' in estimated_cost_raw else int(estimated_cost_raw)
                else:
                    estimated_cost = estimated_cost_raw
            except:
                estimated_cost = 0

            severity = gap.get("severity", "medium").lower()

            formatted_gaps.append({
                "gapId": f"gap_{str(idx + 1).zfill(3)}",
                "category": gap.get("category", "Coverage Gap"),
                "severity": severity,
                "description": gap.get("description", ""),
                "recommendation": gap.get("recommendation", ""),
                "estimatedCost": estimated_cost
            })

            # Count severities
            if severity == "high":
                high_count += 1
            elif severity == "medium":
                medium_count += 1
            else:
                low_count += 1

            total_cost += estimated_cost

        # Determine status based on start and end dates (matching /api/policy/upload logic)
        start_date_str = extracted_data.get("startDate", "")
        end_date_str = extracted_data.get("endDate", "")
        policy_status = "active"  # Default

        try:
            if start_date_str and end_date_str:
                current_date = datetime.now().date()

                # Parse dates (handle both YYYY-MM-DD and DD-MM-YYYY formats)
                if "-" in start_date_str:
                    parts = start_date_str.split("-")
                    if len(parts[0]) == 4:  # YYYY-MM-DD
                        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
                    else:  # DD-MM-YYYY
                        start_date = datetime.strptime(start_date_str, "%d-%m-%Y").date()
                else:
                    start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()

                if "-" in end_date_str:
                    parts = end_date_str.split("-")
                    if len(parts[0]) == 4:  # YYYY-MM-DD
                        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
                    else:  # DD-MM-YYYY
                        end_date = datetime.strptime(end_date_str, "%d-%m-%Y").date()
                else:
                    end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()

                # Determine status
                if current_date < start_date:
                    policy_status = "upcoming"
                elif current_date > end_date:
                    policy_status = "expired"
                else:
                    policy_status = "active"
        except Exception as e:
            logger.warning(f"Could not parse policy dates: {str(e)}")
            policy_status = "active"  # Default if parsing fails

        # Calculate protection score label
        if protection_score >= 90:
            protection_score_label = "Excellent Coverage"
        elif protection_score >= 75:
            protection_score_label = "Good Coverage"
        elif protection_score >= 60:
            protection_score_label = "Fair Coverage"
        else:
            protection_score_label = "Needs Improvement"

        # Extract key benefits for prominent display
        key_benefits = extracted_data.get("keyBenefits") or []

        # Extract critical areas from policy
        critical_areas_raw = extracted_data.get("criticalAreas") or []
        critical_areas = []
        for idx, area in enumerate(critical_areas_raw):
            if isinstance(area, str):
                critical_areas.append({
                    "areaId": f"critical_{str(idx + 1).zfill(3)}",
                    "name": area,
                    "description": area,
                    "status": "review_required",
                    "importance": "medium"
                })
            elif isinstance(area, dict):
                critical_areas.append({
                    "areaId": area.get("areaId", f"critical_{str(idx + 1).zfill(3)}"),
                    "name": area.get("name", "Critical area"),
                    "description": area.get("description", area.get("name", "Critical area")),
                    "status": area.get("status", "review_required"),
                    "importance": area.get("importance", "medium")
                })

        # Extract recommendations from gaps
        recommendations = []
        for idx, gap in enumerate(formatted_gaps):
            recommendation_text = gap.get("recommendation", "")
            if recommendation_text:
                recommendations.append({
                    "recommendationId": f"rec_{str(idx + 1).zfill(3)}",
                    "category": gap.get("category", "Coverage Enhancement"),
                    "priority": gap.get("severity", "medium"),
                    "suggestion": recommendation_text,
                    "estimatedCost": gap.get("estimatedCost", 0),
                    "relatedGapId": gap.get("gapId", "")
                })

        # Get policy exclusions
        exclusions_raw = extracted_data.get("exclusions") or []

        # Get policy holder and insured information
        policy_holder = policy.get("policyHolder", {})
        policy_holder_name = extracted_data.get("policyHolderName") or policy_holder.get("name", "N/A")
        insured_name = extracted_data.get("insuredName", policy_holder_name)
        relationship = policy_holder.get("relationship", "self")

        # Get original document URL from upload data
        upload_id = policy.get("uploadId", "")
        original_document_url = None
        if upload_id:
            try:
                policy_uploads_collection = db['policy_uploads']
                upload_doc = policy_uploads_collection.find_one({"upload_id": upload_id})
                if upload_doc:
                    original_document_url = upload_doc.get("document_url")
            except Exception as e:
                logger.warning(f"Could not fetch original document URL: {str(e)}")

        # Get report URL from policy document
        report_url = policy.get("reportUrl", None)

        # Get insurance provider info
        provider_name = extracted_data.get("insuranceProvider", "")
        insurance_provider_info = None
        try:
            from services.insurance_provider_info import get_insurance_provider_info
            provider_info = get_insurance_provider_info(provider_name)
            if provider_info:
                insurance_provider_info = {
                    "providerName": provider_name,
                    "fullName": provider_info.get("fullName"),
                    "type": provider_info.get("type"),
                    "founded": provider_info.get("founded"),
                    "headquarters": provider_info.get("headquarters"),
                    "about": provider_info.get("about"),
                    "claimSettlementRatio": provider_info.get("claimSettlementRatio"),
                    "claimSettlementYear": provider_info.get("claimSettlementYear"),
                    "customerSupport": provider_info.get("customerSupport"),
                    "specialties": provider_info.get("specialties"),
                    "networkSize": provider_info.get("networkSize")
                }
        except Exception as e:
            logger.warning(f"Could not fetch provider info: {str(e)}")

        # Get saved computed fields from MongoDB
        saved_data_validation = policy.get("dataValidation", {})
        if not saved_data_validation:
            saved_data_validation = {
                "hasIssues": False, "hasWarnings": False, "hasErrors": False,
                "totalIssues": 0, "warningCount": 0, "errorCount": 0,
                "warnings": [], "errors": [], "recommendations": []
            }

        # Extract PRD v2 fields from MongoDB (stored as top-level document fields)
        saved_universal_scores = policy.get("universalScores", None)
        saved_zone_classification = policy.get("zoneClassification", None)
        saved_verdict = policy.get("verdict", None)
        saved_irdai_compliance = policy.get("irdaiCompliance", None)
        saved_zone_recommendations = policy.get("zoneRecommendations", None)

        # Fallback: extract PRD v2 fields from lightAnalysis if not stored at top level (old policies)
        saved_light_analysis = policy.get("lightAnalysis", {})
        if not saved_universal_scores and isinstance(saved_light_analysis, dict):
            saved_universal_scores = saved_light_analysis.get("universalScores", None)
        if not saved_zone_classification and isinstance(saved_light_analysis, dict):
            saved_zone_classification = saved_light_analysis.get("zoneClassification", None)
        if not saved_verdict and isinstance(saved_light_analysis, dict):
            saved_verdict = saved_light_analysis.get("verdict", None)

        # Get extraction V2 data and filter out null-value fields
        saved_extraction_v2 = extracted_data.get("extractionV2", None)
        if isinstance(saved_extraction_v2, dict):
            saved_extraction_v2 = {
                key: (
                    {k: v for k, v in val.items() if not (isinstance(v, dict) and v.get("value") is None)}
                    if isinstance(val, dict) and key != "metadata" and key != "extraction_metadata"
                    else val
                )
                for key, val in saved_extraction_v2.items()
            }

        # Get four check validation from data validation
        saved_four_checks = saved_data_validation.get("fourCheckValidation", None)

        # Build response matching new flat structure
        response = {
            "success": True,
            "policyId": policyId,
            "message": "Policy details retrieved successfully",

            # ==================== POLICY INFO ====================
            "policy": {
                "policyNumber": extracted_data.get("policyNumber", ""),
                "uin": extracted_data.get("uin") or policy.get("extractedUIN", ""),
                "insuranceProvider": provider_name,
                "policyType": extracted_data.get("policyType", ""),
                "policyHolderName": policy_holder_name,
                "insuredName": insured_name,
                "coverageAmount": extracted_data.get("coverageAmount", 0),
                "sumAssured": extracted_data.get("coverageAmount", 0),
                "premium": extracted_data.get("premium", 0),
                "premiumFrequency": extracted_data.get("premiumFrequency", "annually"),
                "startDate": start_date_str,
                "endDate": end_date_str,
                "status": policy_status,
                "relationship": relationship,
                "originalDocumentUrl": original_document_url,
            },

            # ==================== PRD v2 EXTRACTION ====================
            "extraction": saved_extraction_v2,

            # ==================== VALIDATION ====================
            "validation": {
                "dataQuality": {
                    "hasIssues": saved_data_validation.get("hasIssues", False),
                    "hasWarnings": saved_data_validation.get("hasWarnings", False),
                    "hasErrors": saved_data_validation.get("hasErrors", False),
                    "totalIssues": saved_data_validation.get("totalIssues", 0),
                    "warningCount": saved_data_validation.get("warningCount", 0),
                    "errorCount": saved_data_validation.get("errorCount", 0),
                    "warnings": saved_data_validation.get("warnings", []),
                    "errors": saved_data_validation.get("errors", []),
                    "recommendations": saved_data_validation.get("recommendations", []),
                },
                "fourChecks": saved_four_checks,
            },

            # ==================== UNIVERSAL SCORES ====================
            "scores": saved_universal_scores,

            # ==================== ZONE CLASSIFICATION ====================
            "zones": saved_zone_classification,

            # ==================== VERDICT ====================
            "verdict": saved_verdict,

            # ==================== IRDAI COMPLIANCE ====================
            "compliance": saved_irdai_compliance,

            # ==================== RECOMMENDATIONS ====================
            "recommendations": saved_zone_recommendations,

            # ==================== PROVIDER INFO ====================
            "provider": insurance_provider_info,

            # ==================== REPORT ====================
            "report": {
                "url": report_url,
                "fileName": None,
                "error": None,
            },

            "processedAt": (policy.get("created_at", datetime.utcnow()).isoformat() + "Z") if isinstance(policy.get("created_at"), datetime) else (str(policy.get("created_at", "")) + "Z" if policy.get("created_at") else datetime.utcnow().isoformat() + "Z"),
        }

        # Strip all None values from response recursively
        def _strip_nulls(obj):
            if isinstance(obj, dict):
                return {k: _strip_nulls(v) for k, v in obj.items() if v is not None}
            elif isinstance(obj, list):
                return [_strip_nulls(item) for item in obj]
            return obj

        response = _strip_nulls(response)
        return response

    except HTTPException as he:
        raise he

    except Exception as e:
        logger.error(f"Error fetching policy details: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error_code": "SRV_5001",
                "message": "Failed to fetch policy details"
            }
        )


@router.post("/policy/remove")
async def remove_policy(
    request: RemovePolicyRequest = Body(...),
    access_token: Optional[str] = Header(None, description="Access token", alias="access-token"),
    authorization: Optional[str] = Header(None, description="Bearer token", alias="Authorization")
):
    """
    Remove Policy (Soft Delete)

    Soft deletes a policy by marking it as deleted instead of removing it from the database.
    This allows for data recovery and audit trails.

    **Method:** POST

    **Headers (Optional):**
    - access-token: {token}
    - Authorization: Bearer {token}

    **Request Body (JSON):**
    ```json
    {
        "policyId": "ANL_282_824fc6eda278",
        "userId": "282"
    }
    ```

    **Returns:**
    - success: true/false
    - message: Success or error message
    - policyId: ID of the removed policy
    - deletedAt: Timestamp of deletion
    """
    try:
        # Extract from request body
        policyId = request.policyId
        userId = request.userId

        # Authentication check
        has_access_token = bool(access_token)
        has_auth = bool(authorization and authorization.startswith("Bearer "))

        if has_access_token:
            logger.info(f"Request with access-token for policy {policyId}")
        elif has_auth:
            logger.info(f"Request with Authorization Bearer token for policy {policyId}")
        else:
            logger.info(f"Request without authentication for policy {policyId}")

        # Validate userId
        try:
            user_id_int = int(userId)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail={
                    "success": False,
                    "error_code": "VAL_2001",
                    "message": "userId must be a valid number"
                }
            )

        # Get MongoDB connection
        from database_storage.mongodb_chat_manager import mongodb_chat_manager

        if mongodb_chat_manager is None or mongodb_chat_manager.db is None:
            raise HTTPException(
                status_code=503,
                detail={
                    "success": False,
                    "error_code": "SRV_5002",
                    "message": "Database connection is not available"
                }
            )

        db = mongodb_chat_manager.db
        policy_analysis_collection = db['policy_analysis']

        # Check if policy exists and belongs to user
        policy = policy_analysis_collection.find_one({
            "analysisId": policyId,
            "user_id": user_id_int
        })

        if not policy:
            raise HTTPException(
                status_code=404,
                detail={
                    "success": False,
                    "error_code": "RES_3001",
                    "message": "Policy not found or does not belong to this user"
                }
            )

        # Check if already deleted
        if policy.get("isDeleted") == True:
            raise HTTPException(
                status_code=400,
                detail={
                    "success": False,
                    "error_code": "BIZ_7001",
                    "message": "This policy has already been deleted"
                }
            )

        # Soft delete: Update policy with deletion flag
        deletion_timestamp = datetime.now()
        update_result = policy_analysis_collection.update_one(
            {
                "analysisId": policyId,
                "user_id": user_id_int
            },
            {
                "$set": {
                    "isDeleted": True,
                    "deletedAt": deletion_timestamp,
                    "deletedBy": user_id_int,
                    "updated_at": deletion_timestamp
                }
            }
        )

        if update_result.modified_count == 0:
            raise HTTPException(
                status_code=500,
                detail={
                    "success": False,
                    "error_code": "SRV_5001",
                    "message": "Failed to delete policy"
                }
            )

        logger.info(f"✅ Policy {policyId} soft deleted for user {userId}")

        # Return success response
        return {
            "success": True,
            "message": "Policy removed successfully",
            "policyId": policyId,
            "userId": userId,
            "deletedAt": deletion_timestamp.isoformat()
        }

    except HTTPException as he:
        raise he

    except Exception as e:
        logger.error(f"Error removing policy: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error_code": "SRV_5001",
                "message": "Failed to remove policy"
            }
        )
