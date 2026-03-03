"""
Hospital Bill Audit Service
Orchestration service for hospital bill audit analysis, reports, and dispute letters.
"""

import asyncio
import logging
import uuid
import os
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple
from io import BytesIO

logger = logging.getLogger(__name__)


def get_ist_now():
    ist_timezone = timezone(timedelta(hours=5, minutes=30))
    return datetime.now(ist_timezone).replace(tzinfo=None)


class BillAuditService:
    """
    Service for Bill Audit Intelligence operations.

    Handles:
    - Bill upload and text extraction
    - Bill analysis orchestration
    - Audit result storage/retrieval
    - Report generation
    - Dispute letter generation
    """

    def __init__(self):
        from core.dependencies import MONGODB_AVAILABLE

        self.mongodb_available = MONGODB_AVAILABLE
        self.mongodb_manager = None
        self.bill_audits_collection = None
        self._analyzer = None

        if MONGODB_AVAILABLE:
            from database_storage.mongodb_chat_manager import mongodb_chat_manager
            self.mongodb_manager = mongodb_chat_manager
            self._ensure_collections()
        else:
            logger.warning("MongoDB not available for BillAuditService")

    @property
    def analyzer(self):
        if self._analyzer is None:
            try:
                from financial_services.bill_audit_analyzer import BillAuditAnalyzer
                self._analyzer = BillAuditAnalyzer()
            except Exception as e:
                logger.error(f"Failed to initialize BillAuditAnalyzer: {e}")
        return self._analyzer

    def _try_reconnect_mongodb(self):
        if self.bill_audits_collection is not None:
            return True

        try:
            from database_storage.mongodb_chat_manager import mongodb_chat_manager
            if mongodb_chat_manager and mongodb_chat_manager.db is not None:
                self.mongodb_manager = mongodb_chat_manager
                self.mongodb_available = True
                self._ensure_collections()
                logger.info("MongoDB reconnected for BillAuditService")
                return self.bill_audits_collection is not None
        except Exception as e:
            logger.error(f"MongoDB reconnection failed: {e}")

        return False

    def _ensure_collections(self):
        if not self.mongodb_manager:
            return

        try:
            db = self.mongodb_manager.db
            self.bill_audits_collection = db['bill_audits']

            self._safe_create_index(self.bill_audits_collection, [("user_id", 1), ("status", 1)])
            self._safe_create_index(self.bill_audits_collection, [("audit_id", 1)], unique=True)
            self._safe_create_index(self.bill_audits_collection, [("created_at", -1)])

            logger.info("Bill audit collections initialized")
        except Exception as e:
            logger.error(f"Error initializing bill audit collections: {e}")

    def _safe_create_index(self, collection, keys, **kwargs):
        try:
            collection.create_index(keys, **kwargs)
        except Exception as e:
            error_str = str(e)
            if "11000" in error_str or "IndexKeySpecsConflict" in error_str or "86" in error_str:
                logger.debug(f"Index already exists, skipping: {keys}")
            else:
                logger.warning(f"Index creation warning for {keys}: {e}")

    def _serialize_doc(self, doc: Dict) -> Dict:
        if doc is None:
            return None
        doc = dict(doc)
        if '_id' in doc:
            doc['_id'] = str(doc['_id'])
        return doc

    async def process_bill_upload(
        self,
        user_id: int,
        files: List[Any],
        policy_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Process uploaded bill files: extract text, analyze, detect discrepancies.

        Args:
            user_id: User ID
            files: List of UploadFile objects (images/PDFs)
            policy_id: Optional policy ID for coverage matching

        Returns:
            Complete audit result dict
        """
        audit_id = f"AUDIT-{uuid.uuid4().hex[:12].upper()}"

        # Save initial record
        audit_doc = {
            "audit_id": audit_id,
            "user_id": user_id,
            "status": "processing",
            "uploaded_files": [],
            "matched_policy_id": policy_id,
            "created_at": get_ist_now(),
            "updated_at": get_ist_now(),
        }

        if self.bill_audits_collection is not None:
            try:
                self.bill_audits_collection.insert_one(audit_doc)
            except Exception as e:
                logger.error(f"Failed to save initial audit record: {e}")

        try:
            # Step 1: Upload raw files to S3 and collect file data
            uploaded_file_urls = []
            image_contents = []
            image_filenames = []
            pdf_contents = []

            for file in files:
                file_content = await file.read()
                filename = file.filename or "unknown"
                content_type = file.content_type or ""

                # Upload to S3
                s3_url = await self._upload_to_s3(file_content, filename, user_id, audit_id, content_type)
                if s3_url:
                    uploaded_file_urls.append(s3_url)

                # Categorize by file type
                if content_type.startswith("image/") or filename.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                    image_contents.append(file_content)
                    image_filenames.append(filename)
                elif content_type == "application/pdf" or filename.lower().endswith('.pdf'):
                    pdf_contents.append(file_content)
                else:
                    logger.warning(f"Unsupported file type: {content_type} for {filename}")

            # Step 2: Extract text from all files
            all_text = ""
            logger.info(f"[{audit_id}] Files: {len(image_contents)} images, {len(pdf_contents)} PDFs")

            if image_contents:
                extracted = await asyncio.to_thread(
                    self.analyzer.extract_text_from_images,
                    image_contents, image_filenames
                )
                all_text += extracted + "\n\n"
                logger.info(f"[{audit_id}] Image text extraction: {len(extracted)} chars")

            for i, pdf_content in enumerate(pdf_contents):
                try:
                    extracted = await asyncio.to_thread(
                        self.analyzer.extract_text_from_pdf,
                        pdf_content
                    )
                    all_text += extracted + "\n\n"
                    logger.info(f"[{audit_id}] PDF {i+1} text extraction: {len(extracted)} chars")
                except Exception as e:
                    logger.error(f"[{audit_id}] PDF {i+1} extraction failed: {e}")

            if not all_text.strip():
                await self._update_audit_status(audit_id, "failed", error="No text could be extracted from uploaded files")
                return {"audit_id": audit_id, "status": "failed", "error": "Text extraction failed"}

            logger.info(f"[{audit_id}] Total extracted text: {len(all_text)} chars")

            # Step 3: Extract structured data
            # PDF → DeepSeek, Images → GPT-4o
            source_type = "pdf" if pdf_contents and not image_contents else "image"
            logger.info(f"[{audit_id}] Structured extraction: source_type={source_type}")
            bill_data = await asyncio.to_thread(
                self.analyzer.extract_structured_data, all_text, source_type
            )
            bill_data_dict = bill_data.model_dump() if hasattr(bill_data, 'model_dump') else bill_data

            # Step 4: Validate extraction
            validation = await asyncio.to_thread(
                self.analyzer.validate_extraction, bill_data_dict
            )
            bill_data_dict["extraction_validation"] = validation

            # Step 5: Policy matching (optional)
            coverage_analysis = None
            if policy_id:
                policy_data = await self._get_policy_data(user_id, policy_id)
                if policy_data:
                    coverage_result = await asyncio.to_thread(
                        self.analyzer.match_bill_against_policy,
                        bill_data_dict, policy_data, "hospital"
                    )
                    coverage_analysis = coverage_result.model_dump() if hasattr(coverage_result, 'model_dump') else coverage_result

            # Step 6: Detect discrepancies (v2: provable errors only, no govt rate comparison)
            discrepancies_result = await asyncio.to_thread(
                self.analyzer.detect_discrepancies,
                bill_data_dict, "hospital"
            )
            discrepancies_list = [d.model_dump() if hasattr(d, 'model_dump') else d for d in discrepancies_result]

            # Step 7: Calculate savings
            savings_result = await asyncio.to_thread(
                self.analyzer.calculate_savings,
                discrepancies_result
            )
            savings_dict = savings_result.model_dump() if hasattr(savings_result, 'model_dump') else savings_result

            # Step 8: Bill health score
            bill_health_score = await asyncio.to_thread(
                self.analyzer.calculate_bill_health_score,
                bill_data_dict, discrepancies_result, validation
            )

            # Step 9: Generate limitations
            limitations = await asyncio.to_thread(
                self.analyzer._generate_limitations,
                bill_data_dict, validation
            )

            # Step 10: Generate recommendations
            recommendations = await asyncio.to_thread(
                self.analyzer._generate_recommendations,
                discrepancies_result, savings_dict, bill_data_dict
            )

            # Build complete result
            result = {
                "audit_id": audit_id,
                "audit_version": "2.0-india-no-govt-benchmark",
                "bill_type": "hospital",
                "status": "completed",
                "uploaded_files": uploaded_file_urls,
                "hospital_context": bill_data_dict.get("hospital_context"),
                "bill_data": bill_data_dict,
                "extraction_validation": validation,
                "coverage_analysis": coverage_analysis,
                "discrepancies": discrepancies_list,
                "savings": savings_dict,
                "bill_health_score": bill_health_score,
                "limitations": limitations,
                "recommendations": recommendations,
                "created_at": audit_doc["created_at"],
                "completed_at": get_ist_now(),
            }

            # Save to MongoDB
            if self.bill_audits_collection is not None:
                try:
                    self.bill_audits_collection.update_one(
                        {"audit_id": audit_id},
                        {"$set": {
                            **result,
                            "extracted_text": all_text[:10000],
                            "updated_at": get_ist_now(),
                        }}
                    )
                except Exception as e:
                    logger.error(f"Failed to save audit result: {e}")

            return result

        except Exception as e:
            logger.error(f"Bill audit processing failed: {e}", exc_info=True)
            await self._update_audit_status(audit_id, "failed", error=str(e))
            return {"audit_id": audit_id, "status": "failed", "error": str(e)}

    async def get_audit_result(self, user_id: int, audit_id: str) -> Optional[Dict[str, Any]]:
        if self.bill_audits_collection is None:
            if not self._try_reconnect_mongodb():
                return None

        try:
            doc = self.bill_audits_collection.find_one(
                {"audit_id": audit_id, "user_id": user_id}
            )
            return self._serialize_doc(doc)
        except Exception as e:
            logger.error(f"Failed to get audit result: {e}")
            return None

    async def get_audit_history(
        self, user_id: int, limit: int = 20, offset: int = 0
    ) -> Tuple[List[Dict[str, Any]], int]:
        if self.bill_audits_collection is None:
            if not self._try_reconnect_mongodb():
                return [], 0

        try:
            query = {"user_id": user_id}
            total = self.bill_audits_collection.count_documents(query)

            cursor = (
                self.bill_audits_collection
                .find(query, {
                    "audit_id": 1, "bill_type": 1, "status": 1,
                    "created_at": 1, "savings": 1, "uploaded_files": 1,
                })
                .sort("created_at", -1)
                .skip(offset)
                .limit(limit)
            )

            audits = [self._serialize_doc(doc) for doc in cursor]
            return audits, total
        except Exception as e:
            logger.error(f"Failed to get audit history: {e}")
            return [], 0

    async def generate_report(self, user_id: int, audit_id: str) -> Optional[str]:
        """Generate PDF report and upload to S3. Returns report URL."""
        audit = await self.get_audit_result(user_id, audit_id)
        if not audit:
            return None

        try:
            from financial_services.bill_audit_report_generator import generate_bill_audit_report
            pdf_buffer = await asyncio.to_thread(generate_bill_audit_report, audit)

            # Upload to S3
            from database_storage.s3_bucket import upload_pdf_to_s3
            filename = f"bill_audit_{audit_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.pdf"
            bucket = os.getenv("S3_BUCKET_NAME", "raceabove-dev")
            result = upload_pdf_to_s3(pdf_buffer, filename, bucket)

            if result.get("success"):
                report_url = result["s3_url"]

                # Save URL to audit record
                if self.bill_audits_collection is not None:
                    self.bill_audits_collection.update_one(
                        {"audit_id": audit_id},
                        {"$set": {"report_url": report_url, "updated_at": get_ist_now()}}
                    )

                return report_url
            else:
                logger.error(f"S3 upload failed: {result.get('error')}")
                return None

        except Exception as e:
            logger.error(f"Report generation failed: {e}", exc_info=True)
            return None

    async def generate_dispute_letter(
        self, user_id: int, audit_id: str, as_pdf: bool = True
    ) -> Optional[Dict[str, Any]]:
        """Generate dispute letter. Returns text and optional PDF URL."""
        audit = await self.get_audit_result(user_id, audit_id)
        if not audit:
            return None

        try:
            from financial_services.dispute_letter_generator import (
                generate_dispute_letter_text,
                generate_dispute_letter_pdf,
            )

            letter_text = generate_dispute_letter_text(audit)
            result = {"text": letter_text, "pdf_url": None}

            if as_pdf:
                pdf_buffer = await asyncio.to_thread(generate_dispute_letter_pdf, audit)

                from database_storage.s3_bucket import upload_pdf_to_s3
                filename = f"dispute_letter_{audit_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.pdf"
                bucket = os.getenv("S3_BUCKET_NAME", "raceabove-dev")
                s3_result = upload_pdf_to_s3(pdf_buffer, filename, bucket)

                if s3_result.get("success"):
                    result["pdf_url"] = s3_result["s3_url"]

                    if self.bill_audits_collection is not None:
                        self.bill_audits_collection.update_one(
                            {"audit_id": audit_id},
                            {"$set": {"dispute_letter_url": s3_result["s3_url"], "updated_at": get_ist_now()}}
                        )

            return result

        except Exception as e:
            logger.error(f"Dispute letter generation failed: {e}", exc_info=True)
            return None

    async def _upload_to_s3(
        self, file_content: bytes, filename: str, user_id: int, audit_id: str, content_type: str
    ) -> Optional[str]:
        try:
            from database_storage.s3_bucket import upload_image_to_s3
            from io import BytesIO

            buffer = BytesIO(file_content)
            s3_filename = f"bill_audits/{user_id}/{audit_id}/{filename}"
            bucket = os.getenv("S3_BUCKET_NAME", "raceabove-dev")

            result = upload_image_to_s3(buffer, s3_filename, bucket, content_type=content_type)
            if result and result.get("success"):
                return result.get("s3_url", result.get("url"))
        except Exception as e:
            logger.warning(f"S3 upload failed for {filename}: {e}")

        return None

    async def _get_policy_data(self, user_id: int, policy_id: str) -> Optional[Dict[str, Any]]:
        try:
            from services.policy_locker_service import policy_locker_service
            if policy_locker_service.policy_locker_collection:
                doc = policy_locker_service.policy_locker_collection.find_one({
                    "user_id": user_id,
                    "$or": [
                        {"_id": policy_id},
                        {"policy_id": policy_id},
                    ]
                })
                if doc:
                    return self._serialize_doc(doc)
        except Exception as e:
            logger.warning(f"Failed to fetch policy data: {e}")

        return None

    async def _update_audit_status(self, audit_id: str, status: str, error: str = None):
        if self.bill_audits_collection is not None:
            try:
                update = {"status": status, "updated_at": get_ist_now()}
                if error:
                    update["error"] = error
                self.bill_audits_collection.update_one(
                    {"audit_id": audit_id},
                    {"$set": update}
                )
            except Exception as e:
                logger.error(f"Failed to update audit status: {e}")


# Global singleton instance
bill_audit_service = BillAuditService()
