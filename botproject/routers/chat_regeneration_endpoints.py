"""
Report Regeneration API Endpoints
Handles full report and section-specific regeneration
"""
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from bson import ObjectId
from io import BytesIO
from utils.pdf_report_generator import create_gap_analysis_pdf

logger = logging.getLogger(__name__)


async def regenerate_full_report(
    report_id: str,
    user_id: int,
    mongodb_chat_manager,
    chat_session_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Regenerate the entire insurance gap analysis report using DeepSeek API

    Args:
        report_id: Report ID (format: report_{user_id}_{timestamp}_{random_hex})
        user_id: User ID for validation
        mongodb_chat_manager: MongoDB manager instance
        chat_session_id: Optional chat session ID

    Returns:
        Dict with regenerated report data
    """
    try:
        logger.info(f"Starting full report regeneration for report_id: {report_id}")

        # Fetch original report from MongoDB using report_id
        # Exclude soft-deleted policies
        original_report = mongodb_chat_manager.policy_analysis_collection.find_one({
            "report_id": report_id,
            "user_id": user_id,
            "$or": [
                {"isDeleted": {"$exists": False}},
                {"isDeleted": False}
            ]
        })

        if not original_report:
            return {
                "success": False,
                "error": "Report not found or access denied",
                "message": f"No report found with ID {report_id} for user {user_id}"
            }

        logger.info(f"Found original report: {original_report.get('filename')}")

        # Extract original data
        original_analysis = original_report.get('analysis_text', '')
        uin = original_report.get('uin')
        policy_type = original_report.get('policy_type')
        filename = original_report.get('filename')

        # Create regeneration prompt using the SAME format as original analysis
        regeneration_prompt = f"""
You are an expert insurance analyst for the Indian market. Regenerate a comprehensive gap analysis report based on the original analysis data.

CRITICAL INSTRUCTIONS:
- Maintain the EXACT SAME STRUCTURE as the original report
- Keep each section BRIEF and focused
- Extract information from the original analysis
- Use the SAME formatting rules

🚨 MOST IMPORTANT RULES:
1. In Policy Summary and Coverage Details sections:
   - NEVER write "[Not found]", "[Not mentioned]", "Not mentioned in document", or any placeholder
   - If data is not available, simply DO NOT include that bullet point at all
   - Skip the entire line/field if data is missing
   - The number of bullet points will vary based on available data

2. Formatting Standards:
   - ALL monetary amounts MUST use ₹ symbol with comma separators
   - Correct: ₹3,00,000 or ₹14,593.00
   - Wrong: ■3,00,000 or 3,00,000 or 14593

3. Priority Actions Section:
   - Use bullet points (●) NOT numbered lists
   - Wrong: 1. Add coverage, 2. Increase limit
   - Correct: - Add coverage, - Increase limit

**Original Policy Information:**
- Policy UIN: {uin}
- Policy Type: {policy_type}
- Document: {filename}

**Original Analysis Data:**
{original_analysis}

Regenerate the report in this EXACT structure:

## 1. Policy Summary
⚠️ CRITICAL INSTRUCTIONS - FOLLOW EXACTLY:
1. Write a bullet point ONLY when you find ACTUAL data for that field
2. NEVER write "[Not found]", "[Not mentioned]", or any placeholder
3. If data is missing, DO NOT create a bullet point for that field at all
4. Simply skip/omit the entire line if you don't find the data
5. Total bullet points will vary - this is expected and correct

Extract from original analysis and format properly:
- UIN (Unique Identification Number): {uin or '(extract if found)'}
- Policy Number: (add line only if found in original)
- Insurance Company: (add line only if found)
- Policy Type: {policy_type or '(extract if found)'}
- Policyholder Name: (add line only if found)
- Sum Assured/Coverage Amount: (Format: ₹5,00,000 or ₹5 Lakhs - always use ₹ and commas)
- Premium Amount: (Format: ₹15,000 annually - always use ₹ and commas)
- Policy Start Date: (add line only if found)
- Policy End Date/Maturity Date: (add line only if found)
- Policy Term: (add line only if found)
- Premium Payment Term: (add line only if found)

CRITICAL: ALL monetary amounts MUST use ₹ symbol and comma separators

## 2. Coverage Details
⚠️ CRITICAL: Only add bullet points for items with REAL data. Never write "[Not found]" or placeholders.

Extract and add lines only for items you find in original:
- Base Coverage: (Format: ₹5,00,000 - always use ₹ symbol and commas)
- Key Riders/Add-ons: (add line only if found)
- Key Benefits Covered: (add line only if found)
- Major Exclusions: (add line only if found)

FORMAT RULE: All amounts must use ₹ symbol with comma separators

## 3. Gap Analysis (Based on Indian Insurance Market Standards)

IMPORTANT: Identify 5-8 CRITICAL gaps based on the original analysis. For each gap, provide:
- Gap Name (in bold)
- DETAILED explanation (2-4 sentences) covering:
  * What is missing or inadequate
  * Why it matters for this policyholder
  * Potential financial impact
  * Real-world scenario where this gap could cause problems

Format:
**Gap 1: [Gap Name]**
Detailed explanation of the gap, why it's critical, what risks it poses, and how it could financially impact the policyholder. Include specific amounts (with ₹ symbol and commas like ₹1,00,000) or percentages if relevant. Explain with a real-world scenario.

**Gap 2: [Gap Name]**
[Detailed explanation...]

Maintain the same gap analysis depth as the original report.

## 4. Risk Assessment
Evaluate financial risks due to identified gaps in Indian context (Keep concise - 2-3 sentences per category):
- High Risk Areas: [Brief description based on original]
- Medium Risk Areas: [Brief description based on original]
- IRDAI Compliance: [Brief note]

## 5. Recommendations (India-Specific)
Provide 4-6 specific, actionable recommendations in one line each:
- [Recommendation 1 in one line]
- [Recommendation 2 in one line]
- [Recommendation 3 in one line]
- [Recommendation 4 in one line]

## 6. Priority Actions
Top 3-5 immediate actions (use bullet points, NOT numbered list):
- [Most critical action]
- [Second priority action]
- [Third priority action]
- [Fourth priority action if applicable]

IMPORTANT: Use bullet points (●) NOT numbered lists (1. 2. 3.) in this section

Generate the complete regenerated report now with the EXACT SAME structure and detail level as the original:
"""

        # Call DeepSeek API to regenerate report
        from openai import OpenAI
        import os

        # Configure DeepSeek client
        DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
        deepseek_client = OpenAI(
            api_key=DEEPSEEK_API_KEY,
            base_url="https://api.deepseek.com"
        )

        logger.info("Calling DeepSeek API for report regeneration...")

        try:
            response = deepseek_client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert insurance analyst providing detailed gap analysis reports. CRITICAL: Extract ONLY actual data, format ALL amounts with ₹ symbol and comma separators, use bullet points (NOT numbered lists) in Priority Actions."
                    },
                    {
                        "role": "user",
                        "content": regeneration_prompt
                    }
                ],
                temperature=0.1,
                max_tokens=4000
            )

            regenerated_text = response.choices[0].message.content.strip()

            # Log token usage
            if response.usage:
                logger.info(f"========== TOKEN USAGE (REGENERATION) ==========")
                logger.info(f"Input Tokens:  {response.usage.prompt_tokens}")
                logger.info(f"Output Tokens: {response.usage.completion_tokens}")
                logger.info(f"Total Tokens:  {response.usage.total_tokens}")
                logger.info(f"================================================")

            logger.info(f"DeepSeek response length: {len(regenerated_text)} characters")

        except Exception as e:
            logger.error(f"Error calling DeepSeek API for regeneration: {str(e)}")
            return {
                "success": False,
                "error": "Failed to regenerate report",
                "message": f"DeepSeek API error: {str(e)}"
            }

        # Generate new PDF using shared generator for consistent styling
        pdf_buffer = create_gap_analysis_pdf(
            report_text=regenerated_text,
            filename=filename,
            is_regenerated=True,
            uin=uin,
            policy_type=policy_type
        )

        # Upload to S3
        from database_storage.s3_bucket import upload_pdf_to_s3
        import secrets

        timestamp = int(datetime.now().timestamp())
        random_suffix = secrets.token_hex(4)
        new_report_filename = f"gap_analysis_{user_id}_{timestamp}_regenerated.pdf"
        new_report_id = f"report_{user_id}_{timestamp}_{random_suffix}"

        logger.info(f"Uploading regenerated report to S3: {new_report_filename}")
        s3_result = upload_pdf_to_s3(pdf_buffer, new_report_filename, "raceabove-dev")

        # Extract S3 URL
        report_url = None
        if isinstance(s3_result, dict) and s3_result.get('success'):
            report_url = s3_result.get('s3_url')
        elif s3_result:
            report_url = str(s3_result)

        if not report_url:
            logger.error("Failed to upload regenerated report to S3")
            return {
                "success": False,
                "error": "Failed to upload regenerated report",
                "message": "Could not upload PDF to storage"
            }

        # Store regenerated report in MongoDB
        regenerated_record = {
            "report_id": new_report_id,
            "original_report_id": report_id,
            "user_id": user_id,
            "session_id": chat_session_id or original_report.get('session_id'),
            "filename": filename,
            "report_url": report_url,
            "report_filename": new_report_filename,
            "uin": uin,
            "policy_type": policy_type,
            "analysis_text": regenerated_text,
            "regenerated": True,
            "regeneration_timestamp": datetime.now(),
            "created_at": datetime.now()
        }

        new_mongodb_id = mongodb_chat_manager.policy_analysis_collection.insert_one(
            regenerated_record
        ).inserted_id

        logger.info(f"Stored regenerated report in MongoDB with ID: {new_mongodb_id}")

        return {
            "success": True,
            "report_id": new_report_id,
            "original_report_id": report_id,
            "report_url": report_url,
            "mongodb_id": str(new_mongodb_id),
            "message": "Report regenerated successfully",
            "regenerated_at": datetime.now().isoformat(),
            "analysis_summary": regenerated_text[:500] + "..." if len(regenerated_text) > 500 else regenerated_text
        }

    except Exception as e:
        logger.error(f"Error regenerating full report: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to regenerate report"
        }


async def regenerate_report_section(
    report_id: str,
    section_name: str,
    user_id: int,
    mongodb_chat_manager,
    llm,
    additional_instructions: Optional[str] = None,
    chat_session_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Regenerate a specific section of the insurance gap analysis report

    Args:
        report_id: Report ID
        section_name: Section to regenerate (e.g., "gap_analysis", "recommendations")
        user_id: User ID for validation
        mongodb_chat_manager: MongoDB manager instance
        llm: LLM instance
        additional_instructions: Optional custom instructions
        chat_session_id: Optional chat session ID

    Returns:
        Dict with regenerated section data
    """
    try:
        logger.info(f"Starting section regeneration for report_id: {report_id}, section: {section_name}")

        # Fetch original report
        # Exclude soft-deleted policies
        original_report = mongodb_chat_manager.policy_analysis_collection.find_one({
            "report_id": report_id,
            "user_id": user_id,
            "$or": [
                {"isDeleted": {"$exists": False}},
                {"isDeleted": False}
            ]
        })

        if not original_report:
            return {
                "success": False,
                "error": "Report not found or access denied"
            }

        # Extract data
        original_analysis = original_report.get('analysis_text', '')
        uin = original_report.get('uin')
        policy_type = original_report.get('policy_type')
        filename = original_report.get('filename')

        # Section-specific prompts
        section_prompts = {
            "executive_summary": "Create a concise executive summary of the insurance coverage status",
            "gap_analysis": "Provide a detailed gap analysis identifying all coverage gaps and missing protections",
            "recommendations": "Generate specific, actionable recommendations for improving insurance coverage",
            "risk_assessment": "Analyze and describe the risks that are currently not covered or under-covered",
            "next_steps": "Outline clear next steps the policyholder should take to address coverage gaps",
            "policy_overview": "Provide a comprehensive overview of the existing policy coverage and benefits"
        }

        section_prompt = section_prompts.get(section_name, f"Regenerate the {section_name} section")

        # Create regeneration prompt
        regeneration_prompt = f"""
You are an expert insurance analyst. Please regenerate ONLY the **{section_name.replace('_', ' ').title()}** section of this insurance gap analysis report.

**Policy Information:**
- Policy UIN: {uin}
- Policy Type: {policy_type}
- Document: {filename}

**Original Complete Analysis:**
{original_analysis}

**Task:**
{section_prompt}

{f"**Additional Instructions:** {additional_instructions}" if additional_instructions else ""}

**Important:**
- Focus ONLY on the {section_name.replace('_', ' ')} section
- Provide fresh insights while maintaining accuracy
- Use Markdown formatting with proper heading (## {section_name.replace('_', ' ').title()})
- Be specific and actionable
- Keep the tone professional yet accessible

Generate the {section_name.replace('_', ' ')} section now:
"""

        # Call LLM
        from langchain_core.messages import HumanMessage, SystemMessage

        messages = [
            SystemMessage(content="You are an expert insurance analyst providing detailed, section-specific analysis."),
            HumanMessage(content=regeneration_prompt)
        ]

        logger.info(f"Calling LLM for section regeneration: {section_name}")
        response = llm.invoke(messages)
        regenerated_section = response.content.strip()

        # Store section update in MongoDB
        section_update = {
            "report_id": report_id,
            "user_id": user_id,
            "section_name": section_name,
            "regenerated_content": regenerated_section,
            "regenerated_at": datetime.now(),
            "additional_instructions": additional_instructions
        }

        # Create a new version or update existing
        mongodb_chat_manager.policy_analysis_collection.update_one(
            {"report_id": report_id, "user_id": user_id},
            {
                "$set": {
                    f"sections.{section_name}": regenerated_section,
                    f"sections.{section_name}_updated_at": datetime.now()
                },
                "$push": {
                    "section_history": section_update
                }
            }
        )

        logger.info(f"Section {section_name} regenerated and stored successfully")

        return {
            "success": True,
            "report_id": report_id,
            "section_name": section_name,
            "regenerated_content": regenerated_section,
            "message": f"Section '{section_name.replace('_', ' ').title()}' regenerated successfully",
            "regenerated_at": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error regenerating section: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to regenerate section '{section_name}'"
        }
