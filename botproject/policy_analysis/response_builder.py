"""
Policy Analysis Response Builder
Assembles the final API response dictionary for the policy upload and analysis endpoint.
Contains helpers for extracting critical areas, recommendations, determining policy status,
and building the unified response model for the Flutter/Dart frontend.
"""
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def extract_critical_areas(extracted_data: dict) -> list:
    """
    Extract and normalize critical areas from extracted policy data.

    Args:
        extracted_data: Raw extracted data dict from AI/regex pipeline.

    Returns:
        List of structured critical area dicts with areaId, name, description, status, importance.
    """
    critical_areas_raw = extracted_data.get("criticalAreas") or []
    critical_areas = []
    for idx, area in enumerate(critical_areas_raw):
        if isinstance(area, dict):
            critical_areas.append({
                "areaId": f"critical_{str(idx + 1).zfill(3)}",
                "name": area.get("name", ""),
                "description": area.get("description", ""),
                "status": area.get("status", "review_required"),
                "importance": area.get("importance", "medium")
            })
        elif isinstance(area, str):
            # If it's just a string, create a simple structure
            critical_areas.append({
                "areaId": f"critical_{str(idx + 1).zfill(3)}",
                "name": area,
                "description": area,
                "status": "review_required",
                "importance": "medium"
            })
    return critical_areas


def extract_recommendations_from_gaps(formatted_gaps: list) -> list:
    """
    Extract recommendation entries from formatted gap analysis results.

    Args:
        formatted_gaps: List of gap dicts from gap analysis.

    Returns:
        List of structured recommendation dicts.
    """
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
    return recommendations


def calculate_policy_status(extracted_data: dict) -> str:
    """
    Determine policy status based on start and end dates.

    Args:
        extracted_data: Raw extracted data dict containing startDate and endDate.

    Returns:
        One of "active", "expired", or "upcoming".
    """
    policy_status = "active"  # Default
    start_date_str = extracted_data.get("startDate", "")
    end_date_str = extracted_data.get("endDate", "")

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
                logger.info(f"Policy status: upcoming (starts on {start_date_str})")
            elif current_date > end_date:
                policy_status = "expired"
                logger.info(f"Policy status: expired (ended on {end_date_str})")
            else:
                policy_status = "active"
                logger.info(f"Policy status: active (valid from {start_date_str} to {end_date_str})")
    except Exception as e:
        logger.warning(f"Could not parse policy dates for status calculation: {str(e)}")
        policy_status = "active"  # Default to active if parsing fails

    return policy_status


def build_data_validation_block(data_validation: dict) -> dict:
    """
    Build the dataValidation sub-block used in both policyDetails and MongoDB document.

    Args:
        data_validation: Result dict from validate_policy_data().

    Returns:
        Formatted dataValidation dict for API response.
    """
    return {
        "hasIssues": data_validation.get("totalIssues", 0) > 0,
        "hasWarnings": data_validation.get("hasWarnings", False),
        "hasErrors": data_validation.get("hasErrors", False),
        "totalIssues": data_validation.get("totalIssues", 0),
        "warningCount": len(data_validation.get("warnings", [])),
        "errorCount": len(data_validation.get("errors", [])),
        "warnings": data_validation.get("warnings", []),
        "errors": data_validation.get("errors", []),
        "recommendations": data_validation.get("recommendations", [])
    }


def build_redundant_addon_block(redundant_addon_analysis: dict) -> dict:
    """
    Build the redundantAddonAnalysis sub-block for the response.

    Args:
        redundant_addon_analysis: Result dict from detect_redundant_addons().

    Returns:
        Formatted redundantAddonAnalysis dict for API response.
    """
    return {
        "hasRedundantAddons": redundant_addon_analysis.get("hasRedundantAddons", False),
        "redundantAddons": redundant_addon_analysis.get("redundantAddons", []),
        "totalWastedPremium": redundant_addon_analysis.get("totalWastedPremium", 0),
        "totalWastedFormatted": redundant_addon_analysis.get("totalWastedFormatted", "₹0"),
        "redundantCount": len(redundant_addon_analysis.get("redundantAddons", [])),
        "potentialAnnualSavings": redundant_addon_analysis.get("totalWastedPremium", 0)
    }


def build_analysis_response(
    *,
    user_id: str,
    analysis_id: str,
    upload_id: str,
    extracted_data: dict,
    extracted_uin: str,
    policy_type: str,
    detected_policy_type: str,
    policy_status: str,
    relationship: str,
    original_document_url: str,
    complete_category_data: dict,
    unified_sections: list,
    data_validation: dict,
    redundant_addon_analysis: dict,
    light_analysis: dict,
    policy_details_ui: dict,
) -> dict:
    """
    Build the final unified API response dict for Flutter/Dart frontend.

    This is the UNIFIED RESPONSE MODEL containing:
      - Section 1: policyDetails (TAB 1)
      - Section 2: policyAnalyzer (light analysis)
      - Section 3: insuranceProviderInfo (populated later)

    All parameters are keyword-only to prevent positional argument mistakes.

    Returns:
        Complete response dict ready to be returned from the endpoint.
    """
    policy_holder_name = extracted_data.get("policyHolderName", "")
    insured_name = extracted_data.get("insuredName", policy_holder_name)

    response = {
        "success": True,
        "userId": user_id,
        "policyId": analysis_id,
        "policyNumber": extracted_data.get("policyNumber", ""),
        "message": "Policy uploaded and analyzed successfully",

        # ==================== SECTION 1: POLICY DETAILS (TAB 1) ====================
        # Based on EAZR Production Templates V1.0 - TAB 1 specifications
        # UNIFIED RESPONSE MODEL for Flutter/Dart frontend
        "policyDetails": {
            # -------- COMMON FIELDS (same for all policy types) --------
            "policyNumber": extracted_data.get("policyNumber", ""),
            "uin": extracted_data.get("uin") or extracted_uin,
            "insuranceProvider": extracted_data.get("insuranceProvider", ""),
            "policyType": policy_type or extracted_data.get("policyType", ""),
            "policyHolderName": policy_holder_name,
            "insuredName": insured_name,
            "coverageAmount": extracted_data.get("coverageAmount", 0),
            "sumAssured": extracted_data.get("coverageAmount", 0),
            "premium": extracted_data.get("premium", 0),
            "premiumFrequency": extracted_data.get("premiumFrequency", "annually"),
            "startDate": extracted_data.get("startDate", ""),
            "endDate": extracted_data.get("endDate", ""),
            "status": policy_status,  # active/expired/upcoming
            "relationship": relationship,
            "originalDocumentUrl": original_document_url,

            # -------- UNIFIED SECTIONS (consistent structure for Flutter) --------
            # Each section has: sectionId, sectionTitle, sectionType, displayOrder, fields/items
            # sectionType: "fields" (key-value pairs), "list" (array of items), "value" (single value)
            # This allows Flutter to render ANY policy type with a single model
            "sections": unified_sections,

            # -------- LEGACY: Category-specific data (raw structure) --------
            # Kept for backward compatibility - use "sections" for new implementations
            "categorySpecificData": complete_category_data,

            # -------- FLUTTER UI STRUCTURE (Policy Details Tab) --------
            # Organized according to EAZR Flutter app UI components
            "policyDetailsUI": policy_details_ui,

            # -------- DATA VALIDATION RESULTS --------
            # Validation warnings and recommendations from data quality checks
            "dataValidation": build_data_validation_block(data_validation),

            # -------- REDUNDANT ADD-ON ANALYSIS --------
            # Detection of wasteful add-on premiums
            "redundantAddonAnalysis": build_redundant_addon_block(redundant_addon_analysis)
        },

        # ==================== SECTION 2: POLICY ANALYZER (LIGHT ANALYSIS) ====================
        # Simplified analysis summary for quick understanding
        # Contains: insurerName, planName, protectionVerdict, protectionScore, numbersThatMatter,
        # keyConcerns, whatYouShouldDo, policyStrengths, reportUrl, lightAnalysisReport (MD content)
        "policyAnalyzer": light_analysis,

        # ==================== SECTION 3: INSURANCE PROVIDER INFO ====================
        "insuranceProviderInfo": None,  # Will be populated by caller

        "processedAt": datetime.utcnow().isoformat() + "Z",
        "_internal": {
            "uploadId": upload_id,
            "analysisId": analysis_id,
            "extractedUIN": extracted_uin
        }
    }

    return response
