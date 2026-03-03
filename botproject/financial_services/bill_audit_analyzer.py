"""
Hospital Bill Audit Analyzer — EAZR India v2.0 (No Government Rate Comparison)
6-phase pipeline based on EAZR India Hospital Bill Audit Spec v2.0.
Phases: Detection → Extraction → Validation → Discrepancy → Savings → Score
Focuses on PROVABLE billing errors only: duplicates, calculation errors, MRP violations,
unbundling, phantom charges, date errors, repeat tests, package violations.
Does NOT compare against CGHS/ECHS/PMJAY or any government rate scheme.
"""

import os
import re
import json
import base64
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict

logger = logging.getLogger(__name__)


class BillAuditAnalyzer:
    """Hospital bill audit engine — extraction, benchmarking, discrepancy detection."""

    def __init__(self, openai_api_key: str = None):
        # OpenAI client (GPT-4o — used for image extraction)
        try:
            from openai import OpenAI
            api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
            if api_key:
                self.client = OpenAI(api_key=api_key)
                self.ai_enabled = True
                logger.info("BillAuditAnalyzer: OpenAI client initialized (GPT-4o for images)")
            else:
                self.ai_enabled = False
                logger.warning("BillAuditAnalyzer: No OpenAI API key — AI extraction disabled")
        except Exception as e:
            self.ai_enabled = False
            logger.error(f"BillAuditAnalyzer: OpenAI init failed: {e}")

        # DeepSeek client (used for PDF structured data extraction)
        self.deepseek_client = None
        self.deepseek_enabled = False
        try:
            from openai import OpenAI as OpenAIClient
            deepseek_key = os.getenv("DEEPSEEK_API_KEY")
            if deepseek_key:
                self.deepseek_client = OpenAIClient(
                    api_key=deepseek_key,
                    base_url="https://api.deepseek.com"
                )
                self.deepseek_enabled = True
                logger.info("BillAuditAnalyzer: DeepSeek client initialized (for PDF extraction)")
            else:
                logger.warning("BillAuditAnalyzer: No DEEPSEEK_API_KEY — PDF extraction will fall back to GPT-4o")
        except Exception as e:
            logger.error(f"BillAuditAnalyzer: DeepSeek init failed: {e}")

        # Unbundling patterns — procedure → items that should be included
        self.unbundling_patterns = {
            "angioplasty": ["angiography", "cath lab", "guide wire", "balloon", "stent deployment", "cardiac monitoring"],
            "cabg": ["heart-lung machine", "cardioplegia", "icu monitoring", "chest tube"],
            "appendectomy": ["laparoscopy port", "suture", "drain"],
            "c-section": ["ot charges", "anaesthesia", "newborn care", "suture", "nicu observation"],
            "caesarean": ["ot charges", "anaesthesia", "newborn care", "suture"],
            "cholecystectomy": ["laparoscopy port", "suture", "drain"],
            "hernia repair": ["mesh", "fixation device"],
            "hernioplasty": ["mesh", "fixation device"],
            "knee replacement": ["bone cement", "surgical tools", "physiotherapy"],
            "tkr": ["bone cement", "surgical tools", "physiotherapy"],
            "hip replacement": ["bone cement", "surgical tools", "physiotherapy"],
            "thr": ["bone cement", "surgical tools", "physiotherapy"],
            "cataract": ["iol", "viscoelastic", "topical anesthesia"],
            "phaco": ["iol", "viscoelastic", "topical anesthesia"],
            "tonsillectomy": ["ot consumables", "anaesthesia"],
            "septoplasty": ["nasal pack", "ot consumables"],
            "hysterectomy": ["ot charges", "anaesthesia", "suture", "drain"],
        }

        # Complimentary items that should not be charged (included in room rent/nursing)
        self.complimentary_items = [
            "drinking water", "water bottle", "water",
            "bed pan", "urinal", "urine pot",
            "patient gown", "hospital dress", "gown", "apron",
            "bed sheet", "bed linen", "pillow cover", "linen", "mattress cover",
            "soap", "tissue", "towel", "toiletries", "tissue paper", "tissue roll",
            "admission kit", "welcome kit", "patient kit",
            "basic nursing", "nursing care",
            "gloves", "mask", "cap", "shoe cover",
            "bio waste", "housekeeping", "biomedical waste",
            "sterilization", "sterilisation", "disinfection",
            "oxygen mask", "nasal prong",  # basic oxygen delivery devices
            "cotton", "gauze pad", "gauge pad", "cotton ball",
            "spirit swab", "betadine swab",
            "id band", "identity band", "wrist band",
        ]

        # Items that look complimentary but are legitimate in surgery/OT context
        self.complimentary_exceptions_in_ot = {
            "gloves", "mask", "cap", "shoe cover", "gown", "apron",
            "cotton", "gauze", "betadine", "spirit",
        }

        # Standard pre-op tests (do NOT flag for surgical patients)
        self.standard_preop_tests = {
            "cbc", "complete blood count", "hemogram",
            "blood sugar", "glucose", "fasting sugar",
            "serum creatinine", "creatinine",
            "blood urea", "bun", "urea",
            "serum electrolytes", "electrolytes",
            "lft", "liver function test",
            "pt inr", "pt", "prothrombin time", "inr",
            "ecg", "electrocardiogram",
            "x-ray", "xray", "x ray", "chest x-ray", "cxr",
            "blood group", "blood group and rh typing",
            "cross match", "compatibility",
            "hiv", "hiv i ii",
            "hbsag", "hepatitis b",
            "hcv", "hepatitis c",
            "urine routine", "urine re", "urine rm",
        }

        # Diagnosis → unnecessary tests mapping (MD Phase 4.6)
        self.unnecessary_tests_by_diagnosis = {
            "appendicitis": ["mri", "pet ct", "pet-ct", "pet scan", "bone scan", "echo", "echocardiography"],
            "appendectomy": ["mri", "pet ct", "pet-ct", "pet scan", "bone scan", "echo", "echocardiography"],
            "normal delivery": ["ct scan", "mri", "angiography", "pet ct", "pet-ct"],
            "c-section": ["ct scan", "mri", "angiography", "pet ct", "pet-ct"],
            "caesarean": ["ct scan", "mri", "angiography", "pet ct", "pet-ct"],
            "fracture": ["echo", "echocardiography", "endoscopy", "colonoscopy", "mri brain"],
            "dengue": ["mri", "ct scan", "pet ct", "pet-ct", "angiography"],
            "viral fever": ["mri", "ct scan", "pet ct", "pet-ct", "angiography"],
            "cataract": ["ct scan", "mri", "stress test", "tmt"],
            "hernia": ["pet ct", "pet-ct", "mri brain", "echo", "colonoscopy"],
            "tonsillectomy": ["ct scan", "mri", "echo", "colonoscopy"],
            "turp": ["mri brain", "echo", "pet ct", "pet-ct"],
            "kidney stone": ["mri brain", "echo", "pet ct", "pet-ct"],
            "gastroenteritis": ["mri", "pet ct", "pet-ct", "angiography"],
        }

        # ICU-exception tests (frequent repeats are normal in critical care)
        self.icu_frequent_tests = {
            "blood gas", "abg", "arterial blood gas",
            "electrolytes", "serum electrolytes",
            "blood sugar", "glucose", "random sugar", "grbs",
            "cbc", "complete blood count",
            "creatinine", "serum creatinine",
            "lactate", "serum lactate",
            "pt", "inr", "pt/inr", "prothrombin",
            "blood urea", "bun", "urea",
            "bilirubin", "serum bilirubin", "total bilirubin",
            "platelet count", "platelet",
            "sodium", "potassium", "magnesium", "calcium",
            "troponin", "bnp", "nt-probnp",
            "d-dimer",
        }

    # ================================================================
    # TEXT EXTRACTION
    # ================================================================

    def extract_text_from_images(self, image_contents: list, image_filenames: list) -> str:
        """Extract text from hospital bill images using GPT-4o Vision."""
        if not self.ai_enabled:
            raise Exception("OpenAI API not available for image extraction")

        try:
            MIME_TYPE_MAP = {
                '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
                '.png': 'image/png', '.webp': 'image/webp',
                '.gif': 'image/gif', '.bmp': 'image/bmp',
            }

            content_parts = [
                {
                    "type": "text",
                    "text": """You are an expert OCR system specialized in extracting text from INDIAN HOSPITAL BILLS.

TASK: Extract ALL text from the provided hospital bill images with 100% accuracy. Do NOT skip ANY text.

CRITICAL RULES FOR INDIAN HOSPITAL BILLS:
1. The AMOUNT column is ALWAYS the RIGHTMOST monetary column — this is the only column with ₹ values.
2. NEVER confuse these with amounts:
   - Vch No. / Voucher Number (3-5 digit codes in first/left column)
   - Lab No. (7-digit numbers in middle columns)
   - IP No / UHID / Bill No (identifiers in header)
   - Bed No (room/bed identifier)
3. Quantity column has small values (1.00, 2.00, 0.15) — NOT amounts.
4. Indian lakh format: ₹1,52,699 = One lakh fifty-two thousand six hundred ninety-nine.
5. Section subtotals must match sum of line items in that section.

=== HEADER / LETTERHEAD (TOP OF PAGE 1) — EXTRACT COMPLETELY ===
The top portion of an Indian hospital bill contains critical information. Extract EVERY field:
- HOSPITAL NAME: Usually the LARGEST text at the very top, often in bold/colored. This is the most important field.
  Common suffixes: Hospital, Medical Centre, Nursing Home, Healthcare, Institute, Foundation, Trust
  Examples: "Apollo Hospitals", "Fortis Memorial Research Institute", "Lilavati Hospital"
- HOSPITAL ADDRESS: City, State, Pin code — usually right below the hospital name
- Registration No / NABH No / ROHINI ID — hospital identifiers
- PAN Number (10 chars like AAAAA1234A)
- GSTIN / GST No (15 chars like 27AAAAA1234A1Z5) — the first 2 digits identify the STATE
- Phone/Fax/Email/Website

=== PATIENT & ADMISSION DETAILS — EXTRACT ALL ===
- Patient Name, Age, Gender
- UHID / MRN / Hospital ID Number
- IP Number / IPD Number / Admission Number
- Admission Date AND Time (format: DD/MM/YYYY or DD-Mon-YYYY)
- Discharge Date AND Time
- Treating Doctor / Consultant name
- Surgeon name, Anaesthetist name
- Primary/Provisional/Final Diagnosis — SEARCH CAREFULLY, may appear as:
  "Diagnosis:", "Provisional Diagnosis:", "Final Diagnosis:", "Clinical Diagnosis:",
  "Reason for Admission:", "Chief Complaint:", "Admitted for:", "Condition on Admission:"
- Procedure / Surgery performed
- Ward/Room Type: ICU, NICU, PICU, ICCU, HDU, Semi-Private, General Ward, Deluxe, Suite
- Bed Number, Ward Name
- Bill Type: Interim/Provisional, Final Discharge, Cashless, Estimate
- Company/TPA/Insurance payer name, Policy number

=== BILLING SECTIONS & LINE ITEMS ===
- Extract ALL section headings (STAY CHARGES, DIAGNOSTIC, PHARMACY, DOCTORS FEES, NURSING, OT/PROCEDURE, IMPLANTS, CONSUMABLES, etc.)
- For EACH line item: serial/voucher no | date | description | quantity | rate | AMOUNT
- SubTotal for EACH section
- Look for subsection headings within sections

=== BILL SUMMARY (USUALLY ON LAST PAGE) ===
- Gross Amount / Total Bill Amount / Grand Total — this is the MAIN total, NEVER ₹0
- GST Amount
- Discount
- TPA/Insurance Approved Amount
- TPA Deductions / Non-payable amounts
- Co-pay
- Advance/Deposit Paid
- Refund Due
- Net Patient Payable / Balance Outstanding
- Payment mode (Cash/Card/UPI/NEFT)

=== FORMATTING RULES ===
- Format tables with clear column separation using pipes |
- Preserve all numerical values EXACTLY as shown
- If multiple images, combine them in order (multi-page bill)
- Preserve document structure (headings, sections, sub-sections)
- Do NOT summarize or skip any text — extract EVERYTHING

OUTPUT: Return ONLY the extracted text, no commentary."""
                }
            ]

            for img_content, filename in zip(image_contents, image_filenames):
                ext = os.path.splitext(filename.lower())[1]
                mime_type = MIME_TYPE_MAP.get(ext, 'image/jpeg')
                base64_image = base64.b64encode(img_content).decode('utf-8')

                content_parts.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{mime_type};base64,{base64_image}"
                    }
                })

            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": content_parts}],
                max_tokens=16000,
                temperature=0.0
            )

            extracted_text = response.choices[0].message.content.strip()
            logger.info(f"Extracted text from {len(image_contents)} bill image(s), {len(extracted_text)} chars")
            return extracted_text

        except Exception as e:
            logger.error(f"Image text extraction failed: {e}")
            raise Exception(f"Failed to extract text from bill images: {str(e)}")

    def extract_text_from_pdf(self, pdf_content: bytes) -> str:
        """
        Extract text from PDF. Three-tier approach:
        1. PyPDF2 (fast, text-based PDFs)
        2. pdfplumber (better table extraction)
        3. PyMuPDF → GPT-4o Vision (image-based/scanned PDFs)
        """
        all_text = ""

        # Tier 1: PyPDF2
        try:
            import PyPDF2
            import io
            reader = PyPDF2.PdfReader(io.BytesIO(pdf_content))
            for page in reader.pages:
                page_text = page.extract_text() or ""
                all_text += page_text + "\n"
        except Exception as e:
            logger.warning(f"PyPDF2 extraction failed: {e}")

        # Tier 2: pdfplumber (if PyPDF2 gave poor results)
        if len(all_text.strip()) < 50:
            try:
                import pdfplumber
                import io
                with pdfplumber.open(io.BytesIO(pdf_content)) as pdf:
                    for page in pdf.pages:
                        text = page.extract_text() or ""
                        all_text += text + "\n"
                        tables = page.extract_tables()
                        for table in tables:
                            for row in table:
                                if row:
                                    all_text += " | ".join([str(c or "") for c in row]) + "\n"
            except Exception as e:
                logger.error(f"pdfplumber extraction also failed: {e}")

        # Check text quality — if too short or garbled, it's likely a scanned/image PDF
        text_quality = self._assess_text_quality(all_text)

        if text_quality == "good":
            logger.info(f"PDF text extraction: {len(all_text)} chars (text-based PDF)")
            return all_text

        # Tier 3: Convert PDF → images → GPT-4o Vision OCR
        logger.info(f"PDF text quality: {text_quality} ({len(all_text.strip())} chars). Converting to images for GPT-4o Vision OCR.")
        try:
            image_contents, image_filenames = self._convert_pdf_to_images(pdf_content)
            if image_contents:
                vision_text = self.extract_text_from_images(image_contents, image_filenames)
                if len(vision_text.strip()) > len(all_text.strip()):
                    logger.info(f"GPT-4o Vision OCR extracted {len(vision_text)} chars from {len(image_contents)} PDF pages")
                    return vision_text
                else:
                    logger.info("GPT-4o Vision gave less text than text extraction — using text extraction")
                    return all_text if all_text.strip() else vision_text
        except Exception as e:
            logger.error(f"PDF-to-image Vision OCR failed: {e}")

        if not all_text.strip():
            raise Exception("No text extracted from PDF. Text extraction, pdfplumber, and Vision OCR all failed.")

        return all_text

    def _convert_pdf_to_images(self, pdf_content: bytes) -> tuple:
        """Convert PDF pages to images using PyMuPDF for GPT-4o Vision processing."""
        image_contents = []
        image_filenames = []

        try:
            import pymupdf
            import io

            doc = pymupdf.open(stream=pdf_content, filetype="pdf")
            page_count = min(len(doc), 15)  # Limit to 15 pages to avoid token overflow

            for page_num in range(page_count):
                page = doc[page_num]
                # Render at 200 DPI for good OCR quality without excessive size
                mat = pymupdf.Matrix(200 / 72, 200 / 72)
                pix = page.get_pixmap(matrix=mat)
                img_bytes = pix.tobytes("png")
                image_contents.append(img_bytes)
                image_filenames.append(f"pdf_page_{page_num + 1}.png")

            doc.close()
            logger.info(f"Converted {page_count} PDF pages to images")

        except ImportError:
            logger.error("PyMuPDF not installed — cannot convert PDF to images. Install with: pip install PyMuPDF")
        except Exception as e:
            logger.error(f"PDF-to-image conversion failed: {e}")

        return image_contents, image_filenames

    def _assess_text_quality(self, text: str) -> str:
        """
        Assess quality of extracted PDF text.
        Returns: 'good', 'poor', or 'empty'
        """
        stripped = text.strip()
        if not stripped:
            return "empty"

        # Too short for a hospital bill
        if len(stripped) < 200:
            return "poor"

        # Count meaningful content indicators
        has_numbers = len(re.findall(r'\d+', stripped)) >= 5
        has_amounts = bool(re.search(r'(?:Rs\.?|INR|₹|Total|Amount|Charges)\s*', stripped, re.IGNORECASE))
        has_structure = bool(re.search(r'(?:Date|Patient|Hospital|Bill|Admission|Ward|Room|Doctor)', stripped, re.IGNORECASE))

        # High ratio of special chars / non-printable = garbled OCR
        printable_ratio = sum(1 for c in stripped if c.isprintable()) / max(len(stripped), 1)
        if printable_ratio < 0.8:
            return "poor"

        if has_numbers and (has_amounts or has_structure):
            return "good"

        return "poor"

    # ================================================================
    # STRUCTURED DATA EXTRACTION (GPT-4o)
    # ================================================================

    def extract_structured_data(self, text: str, source_type: str = "image") -> Dict[str, Any]:
        """
        Extract structured hospital bill data using AI.

        Args:
            text: Raw extracted text from bill
            source_type: "pdf" to use DeepSeek, "image" to use GPT-4o
        """
        # Choose AI client based on source type
        use_deepseek = (source_type == "pdf" and self.deepseek_enabled)

        if use_deepseek:
            client = self.deepseek_client
            model = "deepseek-chat"
            label = "DeepSeek"
        elif self.ai_enabled:
            client = self.client
            model = "gpt-4o"
            label = "GPT-4o"
        else:
            logger.warning("No AI client available — using regex fallback")
            return self._regex_extract_hospital(text)

        logger.info(f"Structured extraction: using {label} ({model}), text length: {len(text)} chars, source: {source_type}")

        try:
            prompt = f"""You are EAZR Bill Audit Intelligence — an expert Indian hospital bill auditor.

Analyze this hospital bill text and return a COMPLETE structured JSON extraction.

BILL TEXT:
{text[:30000]}

CRITICAL EXTRACTION RULES:
1. Amount = RIGHTMOST monetary column. NEVER confuse Vch No/Lab No/Serial No with amounts.
2. Indian number format: ₹1,52,699 = 152699. Read lakh/crore notation correctly.
3. Extract EVERY section dynamically using the bill's OWN section headings.
4. The bill total (gross_amount) can NEVER be 0 — find it on the last page.
5. All service dates must fall within admission_date to discharge_date (±1 day).
6. Fractional surgery fee quantities (1.35, 0.15, 0.90) are NORMAL (fee splitting).

HOSPITAL NAME — MUST EXTRACT (never leave empty):
- Usually the FIRST or LARGEST text on the bill (letterhead)
- Also appears near: Registration No, GST No, PAN, CIN
- Common patterns: "ABC Hospital", "XYZ Medical Centre", "PQR Healthcare Pvt Ltd"
- If unclear, use the name associated with the GST/PAN/registration number

DIAGNOSIS — SEARCH EVERYWHERE:
- May appear as: "Provisional Diagnosis", "Final Diagnosis", "Clinical Diagnosis", "Diagnosis", "Primary Diagnosis", "Admitting Diagnosis"
- May also be near: "Reason for Admission", "Chief Complaint", "Admitted for"
- For NICU: look for "Preterm", "Low Birth Weight", "Neonatal Jaundice", "RDS", "Sepsis"
- For maternity: "Full Term Pregnancy", "Labour Natural", "LSCS"
- If found anywhere in the bill text, EXTRACT IT

WARD/ROOM TYPE:
- Look for: "Ward", "Bed Type", "Room Category", "Class", "Patient Category"
- Common: "ICU", "NICU", "PICU", "HDU", "ICCU", "General Ward", "Semi-Private", "Private", "Deluxe"

BILL TYPE DETECTION:
- "Interim Bill" / "Provisional Bill" / "Running Bill" → "interim"
- "Final Bill" / "Discharge Summary Bill" / "Settlement Bill" → "final_discharge"
- "Cashless" / "TPA" / "Pre-Auth" in header → "cashless"
- "Estimate" / "Estimated Cost" → "estimate"
- "Package" / "Package Bill" → "package"
- "Daycare" / "Day Care" → "daycare"

LOS CALCULATION:
- If discharge_date and admission_date are both found, calculate LOS = discharge_date - admission_date (in days)
- If only admission_date exists (interim bill), set los_days = 0

Return this exact JSON structure:
{{
  "hospital_context": {{
    "hospital_name": "<MUST extract — full legal name from letterhead/header>",
    "hospital_type": "<government|municipal|trust|cooperative|private_standalone|private_corporate_chain|nursing_home>",
    "city": "<city from address or header>",
    "state": "<state — derive from address, pincode, or GST state code>",
    "nabh_accredited": false
  }},
  "metadata": {{
    "hospital_name": "<same as above>",
    "hospital_address": "<full address>",
    "hospital_city": "<city>",
    "hospital_state": "<state>",
    "hospital_pincode": "<6-digit pincode or empty>",
    "hospital_type": "<type>",
    "registration_number": "<registration no or empty>",
    "pan_number": "<PAN (AAAAA0000A format) or empty>",
    "gst_number": "<GST (15-char like 27AABCR1234A1Z5) or empty>",
    "bill_number": "<MUST extract — bill/invoice number>",
    "bill_date": "<DD/MM/YYYY>",
    "bill_type": "<interim|final_discharge|cashless|reimbursement|estimate|package|daycare>"
  }},
  "patient_details": {{
    "patient_name": "<full name — for babies: 'Baby of [Mother Name]'>",
    "uhid": "<UHID/CR No/MR No>",
    "ip_number": "<IP No/Admission No/Reg No>",
    "age": null,
    "gender": "<M|F or empty>",
    "admission_date": "<DD/MM/YYYY>",
    "admission_time": "<HH:MM or empty>",
    "discharge_date": "<DD/MM/YYYY or empty if interim>",
    "discharge_time": "<HH:MM or empty>",
    "los_days": 0,
    "primary_diagnosis": "<MUST search entire bill for diagnosis>",
    "secondary_diagnosis": "",
    "procedure_performed": "<procedure/surgery if any>",
    "surgery_grade": "",
    "treating_doctor": "<doctor name>",
    "surgeon_name": "",
    "anaesthetist_name": "",
    "admission_type": "<emergency|elective|planned|daycare|maternity>",
    "discharge_status": "<Normal|LAMA|Expired|Transferred or empty>",
    "patient_class": "<General Ward|Semi-Private|Private|ICU|NICU|PICU|HDU|etc>",
    "bed_number": "",
    "ward_name": "",
    "company_payer": "<Self|TPA name|Insurance company|CGHS|etc>",
    "policy_number": "",
    "deposit_paid": 0
  }},
  "bill_sections": [
    {{
      "section_name": "<EXACT heading from bill>",
      "subsections": [
        {{
          "subsection_name": "<sub-heading or empty>",
          "line_items": [
            {{
              "voucher_or_serial_no": "<identifier, NOT amount>",
              "date": "<DD-MM-YYYY service date>",
              "description": "<full description>",
              "provider_or_doctor": "<doctor/lab name if shown>",
              "patient_class": "<ward class if shown>",
              "lab_no": "<identifier, NOT amount>",
              "quantity": 1.0,
              "unit_rate": 0.0,
              "amount": 0.0
            }}
          ],
          "subsection_subtotal": 0.0
        }}
      ],
      "section_subtotal": 0.0
    }}
  ],
  "bill_summary": {{
    "gross_amount": 0.0,
    "gst_amount": 0.0,
    "discount": 0.0,
    "tpa_approved": 0.0,
    "tpa_deductions": 0.0,
    "copay": 0.0,
    "non_payable_by_insurer": 0.0,
    "advance_deposit_paid": 0.0,
    "refund_due": 0.0,
    "patient_payable": 0.0,
    "total_outstanding": 0.0,
    "payment_mode": ""
  }},
  "extraction_validation": {{
    "extraction_confidence": "<high|medium|low>",
    "confidence_reason": "<explanation>"
  }}
}}

IMPORTANT:
- hospital_name and gross_amount can NEVER be empty/0 — search the entire text
- primary_diagnosis: search the ENTIRE bill text, not just the header
- Extract ALL line items visible in the bill — miss nothing
- Use 0 for missing numeric values, empty string for missing text
- Dynamic sections: Read the bill's OWN section names. Different hospitals use different names.
- Return ONLY valid JSON, no commentary or markdown"""

            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=16000,
                temperature=0.1,
            )

            result_text = response.choices[0].message.content.strip()
            logger.info(f"{label} response received: {len(result_text)} chars")

            # Clean markdown wrapping
            if result_text.startswith("```"):
                result_text = re.sub(r'^```(?:json)?\s*', '', result_text)
                result_text = re.sub(r'\s*```$', '', result_text)

            data = json.loads(result_text)
            logger.info(f"Hospital bill data extracted via {label} (source: {source_type})")
            data = self._normalize_extracted_data(data)
            return self._enrich_extracted_data(data, text)

        except json.JSONDecodeError as e:
            logger.error(f"{label} returned invalid JSON: {e}. First 500 chars: {result_text[:500] if 'result_text' in dir() else 'N/A'}")
            # Try DeepSeek→GPT-4o fallback or vice versa
            return self._fallback_structured_extraction(text, label)
        except Exception as e:
            logger.error(f"{label} extraction failed: {type(e).__name__}: {e}")
            return self._fallback_structured_extraction(text, label)

    def _fallback_structured_extraction(self, text: str, failed_label: str) -> Dict:
        """Try the other AI model, then regex as last resort."""
        # If DeepSeek failed, try GPT-4o
        if failed_label == "DeepSeek" and self.ai_enabled:
            logger.info("Falling back from DeepSeek to GPT-4o for structured extraction")
            try:
                return self.extract_structured_data(text, source_type="image")  # forces GPT-4o
            except Exception as e:
                logger.error(f"GPT-4o fallback also failed: {e}")

        # If GPT-4o failed, try DeepSeek
        if failed_label == "GPT-4o" and self.deepseek_enabled:
            logger.info("Falling back from GPT-4o to DeepSeek for structured extraction")
            try:
                # Call DeepSeek directly to avoid recursion
                response = self.deepseek_client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[{"role": "user", "content": f"Extract structured JSON from this hospital bill:\n{text[:30000]}"}],
                    max_tokens=16000,
                    temperature=0.1,
                )
                result_text = response.choices[0].message.content.strip()
                if result_text.startswith("```"):
                    result_text = re.sub(r'^```(?:json)?\s*', '', result_text)
                    result_text = re.sub(r'\s*```$', '', result_text)
                data = json.loads(result_text)
                logger.info("DeepSeek fallback succeeded")
                data = self._normalize_extracted_data(data)
                return self._enrich_extracted_data(data, text)
            except Exception as e:
                logger.error(f"DeepSeek fallback also failed: {e}")

        logger.warning("All AI extraction failed — using regex fallback")
        return self._regex_extract_hospital(text)

    def _normalize_extracted_data(self, data: Dict) -> Dict:
        """Normalize all numeric fields in extracted data."""
        # Normalize bill_summary
        summary = data.get("bill_summary", {})
        for key in ["gross_amount", "gst_amount", "discount", "tpa_approved", "tpa_deductions",
                     "copay", "non_payable_by_insurer", "advance_deposit_paid", "refund_due",
                     "patient_payable", "total_outstanding"]:
            summary[key] = self._safe_float(summary.get(key))
        data["bill_summary"] = summary

        # Normalize patient_details numerics
        pd = data.get("patient_details", {})
        pd["los_days"] = int(self._safe_float(pd.get("los_days", 0)))
        pd["deposit_paid"] = self._safe_float(pd.get("deposit_paid", 0))
        if pd.get("age") is not None:
            pd["age"] = int(self._safe_float(pd.get("age", 0))) or None
        data["patient_details"] = pd

        # Normalize bill_sections
        for section in data.get("bill_sections", []):
            section["section_subtotal"] = self._safe_float(section.get("section_subtotal"))
            section["calculated_section_total"] = 0.0
            for subsection in section.get("subsections", []):
                subsection["subsection_subtotal"] = self._safe_float(subsection.get("subsection_subtotal"))
                subsection["calculated_subtotal"] = 0.0
                for item in subsection.get("line_items", []):
                    item["quantity"] = self._safe_float(item.get("quantity", 1))
                    item["unit_rate"] = self._safe_float(item.get("unit_rate"))
                    item["amount"] = self._safe_float(item.get("amount"))
                    subsection["calculated_subtotal"] += item["amount"]
                section["calculated_section_total"] += subsection["calculated_subtotal"]

        return data

    # GST state codes → state names (first 2 digits of GSTIN)
    GST_STATE_CODES = {
        "01": "Jammu & Kashmir", "02": "Himachal Pradesh", "03": "Punjab",
        "04": "Chandigarh", "05": "Uttarakhand", "06": "Haryana",
        "07": "Delhi", "08": "Rajasthan", "09": "Uttar Pradesh",
        "10": "Bihar", "11": "Sikkim", "12": "Arunachal Pradesh",
        "13": "Nagaland", "14": "Manipur", "15": "Mizoram",
        "16": "Tripura", "17": "Meghalaya", "18": "Assam",
        "19": "West Bengal", "20": "Jharkhand", "21": "Odisha",
        "22": "Chhattisgarh", "23": "Madhya Pradesh", "24": "Gujarat",
        "26": "Dadra & Nagar Haveli", "27": "Maharashtra", "29": "Karnataka",
        "30": "Goa", "31": "Lakshadweep", "32": "Kerala",
        "33": "Tamil Nadu", "34": "Puducherry", "35": "Andaman & Nicobar",
        "36": "Telangana", "37": "Andhra Pradesh",
    }

    def _enrich_extracted_data(self, data: Dict, raw_text: str) -> Dict:
        """
        Post-extraction enrichment — fill gaps that AI missed using regex on raw text.
        This catches hospital name, diagnosis, LOS, state from GST, etc.
        """
        hospital_ctx = data.get("hospital_context", {})
        metadata = data.get("metadata", {})
        patient = data.get("patient_details", {})
        enriched_fields = []

        # 1. Hospital name — try regex if AI left it empty
        hospital_name = (hospital_ctx.get("hospital_name") or metadata.get("hospital_name", "")).strip()
        if not hospital_name:
            hospital_name = self._regex_find_hospital_name(raw_text)
            if hospital_name:
                hospital_ctx["hospital_name"] = hospital_name
                metadata["hospital_name"] = hospital_name
                enriched_fields.append("hospital_name")

        # 2. State from GST number (first 2 digits = state code)
        gst = (metadata.get("gst_number") or "").strip()
        if gst and len(gst) >= 2:
            state_code = gst[:2]
            gst_state = self.GST_STATE_CODES.get(state_code, "")
            if gst_state:
                if not hospital_ctx.get("state"):
                    hospital_ctx["state"] = gst_state
                    enriched_fields.append("state_from_gst")
                if not metadata.get("hospital_state"):
                    metadata["hospital_state"] = gst_state

        # 3. Diagnosis — search raw text with regex if AI missed it
        if not patient.get("primary_diagnosis"):
            diagnosis = self._regex_find_diagnosis(raw_text)
            if diagnosis:
                patient["primary_diagnosis"] = diagnosis
                enriched_fields.append("diagnosis")

        # 4. LOS auto-calculation from dates
        if patient.get("admission_date") and patient.get("discharge_date") and patient.get("los_days", 0) == 0:
            adm = self._parse_date(patient["admission_date"])
            dis = self._parse_date(patient["discharge_date"])
            if adm and dis:
                los = (dis - adm).days
                if los >= 0:
                    patient["los_days"] = los
                    enriched_fields.append("los_calculated")

        # 5. Patient class from raw text (ICU/NICU/ward type)
        if not patient.get("patient_class"):
            ward = self._regex_find_ward_type(raw_text)
            if ward:
                patient["patient_class"] = ward
                enriched_fields.append("patient_class")

        # 6. Sync hospital_context and metadata
        if hospital_ctx.get("hospital_name") and not metadata.get("hospital_name"):
            metadata["hospital_name"] = hospital_ctx["hospital_name"]
        if metadata.get("hospital_name") and not hospital_ctx.get("hospital_name"):
            hospital_ctx["hospital_name"] = metadata["hospital_name"]
        if hospital_ctx.get("city") and not metadata.get("hospital_city"):
            metadata["hospital_city"] = hospital_ctx["city"]
        if metadata.get("hospital_city") and not hospital_ctx.get("city"):
            hospital_ctx["city"] = metadata["hospital_city"]

        # 7. Gross amount — MUST never be 0; fallback to regex from raw text
        summary = data.get("bill_summary", {})
        if self._safe_float(summary.get("gross_amount")) == 0:
            gross = self._regex_find_gross_amount(raw_text)
            if gross > 0:
                summary["gross_amount"] = gross
                enriched_fields.append("gross_amount")
            # Also try summing section subtotals
            elif data.get("bill_sections"):
                section_sum = sum(
                    self._safe_float(s.get("section_subtotal"))
                    for s in data["bill_sections"]
                )
                if section_sum > 0:
                    summary["gross_amount"] = section_sum
                    enriched_fields.append("gross_amount_from_sections")
            data["bill_summary"] = summary

        # 8. Patient payable fallback — check raw text
        if self._safe_float(summary.get("patient_payable")) == 0:
            payable = self._regex_find_patient_payable(raw_text)
            if payable > 0:
                summary["patient_payable"] = payable
                enriched_fields.append("patient_payable")
            data["bill_summary"] = summary

        data["hospital_context"] = hospital_ctx
        data["metadata"] = metadata
        data["patient_details"] = patient

        if enriched_fields:
            logger.info(f"Post-extraction enrichment filled: {', '.join(enriched_fields)}")

        return data

    def _regex_find_hospital_name(self, text: str) -> str:
        """Try to find hospital name from raw bill text using common patterns."""
        # Pattern 1: Explicit "Hospital Name:" label
        patterns = [
            r'(?:Hospital|Nursing Home|Medical Centre|Healthcare|Clinic)\s*(?:Name)?\s*[:\-]\s*(.+?)(?:\n|$)',
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                if len(name) > 3:
                    return name

        # Pattern 2: First few non-empty lines often contain hospital name
        # Look for lines with "hospital", "medical", "nursing", "healthcare", "clinic"
        hospital_keywords = ["hospital", "medical", "nursing", "healthcare", "clinic",
                             "institute", "centre", "center", "foundation", "trust"]
        for line in text.split("\n")[:20]:  # First 20 lines
            line = line.strip()
            if not line or len(line) < 5:
                continue
            line_lower = line.lower()
            if any(kw in line_lower for kw in hospital_keywords):
                # Clean common suffixes
                clean = re.sub(r'\s*(?:Ph|Tel|Fax|Email|Website|www)\b.*$', '', line, flags=re.IGNORECASE).strip()
                if len(clean) > 5:
                    return clean

        return ""

    def _regex_find_diagnosis(self, text: str) -> str:
        """Search raw text for diagnosis using Indian hospital bill patterns."""
        patterns = [
            r'(?:Primary|Provisional|Final|Clinical|Admitting|Principal)\s*Diagnosis\s*[:\-]\s*(.+?)(?:\n|$)',
            r'Diagnosis\s*[:\-]\s*(.+?)(?:\n|$)',
            r'Reason\s*(?:for|of)\s*Admission\s*[:\-]\s*(.+?)(?:\n|$)',
            r'Chief\s*Complaint\s*[:\-]\s*(.+?)(?:\n|$)',
            r'Admitted\s*(?:for|with)\s*[:\-]?\s*(.+?)(?:\n|$)',
            r'Condition\s*on\s*Admission\s*[:\-]\s*(.+?)(?:\n|$)',
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                diag = match.group(1).strip()
                # Clean up
                diag = re.sub(r'\s+', ' ', diag)
                diag = diag.rstrip('|').strip()
                if len(diag) > 2 and len(diag) < 200:
                    return diag
        return ""

    def _regex_find_ward_type(self, text: str) -> str:
        """Find ward/room type from raw text."""
        patterns = [
            r'(?:Ward|Room|Bed)\s*(?:Type|Category|Class)\s*[:\-]\s*(.+?)(?:\n|$)',
            r'(?:Patient|Admission)\s*(?:Type|Category|Class)\s*[:\-]\s*(.+?)(?:\n|$)',
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                ward = match.group(1).strip()
                if len(ward) > 1 and len(ward) < 50:
                    return ward

        # Direct keyword search in first portion of text
        text_upper = text[:3000].upper()
        ward_keywords = [
            ("NICU", "NICU"), ("PICU", "PICU"), ("ICCU", "ICCU"),
            ("ICU", "ICU"), ("HDU", "HDU"),
            ("SEMI PRIVATE", "Semi-Private"), ("SEMI-PRIVATE", "Semi-Private"),
            ("GENERAL WARD", "General Ward"), ("PRIVATE WARD", "Private"),
            ("DELUXE", "Deluxe"), ("SUITE", "Suite"),
        ]
        for keyword, label in ward_keywords:
            if keyword in text_upper:
                return label

        return ""

    def _regex_find_gross_amount(self, text: str) -> float:
        """Find gross/total bill amount from raw text using common Indian bill patterns."""
        patterns = [
            r'(?:Grand\s*Total|Gross\s*(?:Amount|Total)|Total\s*Bill\s*(?:Amount)?|Total\s*(?:Amount|Charges)|Net\s*(?:Amount|Total))\s*[:\-]?\s*(?:Rs\.?|INR|₹)?\s*([\d,]+(?:\.\d{1,2})?)',
            r'(?:Total\s*Outstanding|Amount\s*Payable|Bill\s*Total|Bill\s*Amount)\s*[:\-]?\s*(?:Rs\.?|INR|₹)?\s*([\d,]+(?:\.\d{1,2})?)',
        ]
        amounts = []
        for pattern in patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                val = self._safe_float(match.group(1))
                if val > 0:
                    amounts.append(val)
        # Return the largest match (gross is typically the largest total)
        return max(amounts) if amounts else 0.0

    def _regex_find_patient_payable(self, text: str) -> float:
        """Find patient payable / net payable from raw text."""
        patterns = [
            r'(?:Patient\s*Payable|Net\s*Payable|Balance\s*(?:Due|Payable|Outstanding)|Amount\s*Due)\s*[:\-]?\s*(?:Rs\.?|INR|₹)?\s*([\d,]+(?:\.\d{1,2})?)',
            r'(?:To\s*Be\s*Paid|Pay(?:able|ment)\s*(?:Amount|Due))\s*[:\-]?\s*(?:Rs\.?|INR|₹)?\s*([\d,]+(?:\.\d{1,2})?)',
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                val = self._safe_float(match.group(1))
                if val > 0:
                    return val
        return 0.0

    def _regex_extract_hospital(self, text: str) -> Dict:
        """Fallback regex extraction when AI is unavailable."""
        hospital_name = ""
        for line in text.split("\n"):
            line = line.strip()
            if line and len(line) > 3:
                hospital_name = line
                break

        amounts = re.findall(r'(?:Rs\.?|INR|₹)\s*([\d,]+(?:\.\d{2})?)', text)
        float_amounts = [float(a.replace(",", "")) for a in amounts]
        gross_amount = max(float_amounts) if float_amounts else 0.0

        patient_match = re.search(r'(?:Patient\s*Name|Name)\s*[:\-]\s*(.+?)(?:\n|$)', text, re.IGNORECASE)
        patient_name = patient_match.group(1).strip() if patient_match else ""

        return {
            "hospital_context": {
                "hospital_name": hospital_name, "hospital_type": "", "city": "", "state": "",
                "nabh_accredited": False,
            },
            "metadata": {
                "hospital_name": hospital_name, "hospital_address": "", "hospital_city": "",
                "hospital_state": "", "hospital_pincode": "", "hospital_type": "",
                "registration_number": "", "pan_number": "", "gst_number": "",
                "bill_number": "", "bill_date": "", "bill_type": "",
            },
            "patient_details": {
                "patient_name": patient_name, "uhid": "", "ip_number": "", "age": None, "gender": "",
                "admission_date": "", "admission_time": "", "discharge_date": "", "discharge_time": "",
                "los_days": 0, "primary_diagnosis": "", "secondary_diagnosis": "",
                "procedure_performed": "", "surgery_grade": "", "treating_doctor": "",
                "surgeon_name": "", "anaesthetist_name": "", "admission_type": "",
                "discharge_status": "", "patient_class": "", "bed_number": "", "ward_name": "",
                "company_payer": "", "policy_number": "", "deposit_paid": 0,
            },
            "bill_sections": [],
            "bill_summary": {
                "gross_amount": gross_amount, "gst_amount": 0, "discount": 0,
                "tpa_approved": 0, "tpa_deductions": 0, "copay": 0,
                "non_payable_by_insurer": 0, "advance_deposit_paid": 0, "refund_due": 0,
                "patient_payable": gross_amount, "total_outstanding": 0, "payment_mode": "",
            },
            "extraction_validation": {
                "extraction_confidence": "low",
                "confidence_reason": "Regex fallback — AI extraction was unavailable",
            },
        }

    # ================================================================
    # EXTRACTION VALIDATION (Phase 3)
    # ================================================================

    def validate_extraction(self, bill_data: Dict) -> Dict:
        """Run Phase 3 validation on extracted data."""
        validation = {
            "subtotal_checks": [],
            "grand_total_check": None,
            "column_confusion_flags": [],
            "date_consistency": True,
            "los_room_charge_match": True,
            "extraction_confidence": "medium",
            "confidence_reason": "",
        }

        sections = bill_data.get("bill_sections", [])
        total_calculated = 0.0

        # Check 1: Section subtotals
        for section in sections:
            # Compute calculated total if not already done by normalization
            calc = self._safe_float(section.get("calculated_section_total", 0))
            if calc == 0:
                # Calculate from line items
                calc = sum(
                    self._safe_float(item.get("amount"))
                    for sub in section.get("subsections", [])
                    for item in sub.get("line_items", [])
                )
            stated = self._safe_float(section.get("section_subtotal", 0))
            total_calculated += calc
            diff = abs(calc - stated)
            validation["subtotal_checks"].append({
                "section": section.get("section_name", ""),
                "calculated_sum": round(calc, 2),
                "bill_subtotal": round(stated, 2),
                "match": diff <= 5,
                "difference": round(diff, 2),
            })

        # Check 2: Grand total
        gross = self._safe_float(bill_data.get("bill_summary", {}).get("gross_amount"))
        diff = abs(total_calculated - gross)
        validation["grand_total_check"] = {
            "calculated_sum_of_sections": round(total_calculated, 2),
            "bill_grand_total": round(gross, 2),
            "match": diff <= 50,
            "difference": round(diff, 2),
        }

        # Check 3: Column confusion (amounts that look like identifiers)
        for section in sections:
            for sub in section.get("subsections", []):
                for item in sub.get("line_items", []):
                    amt = item.get("amount", 0)
                    vch = item.get("voucher_or_serial_no", "")
                    lab = item.get("lab_no", "")
                    if vch and str(int(amt)) == str(vch).strip():
                        validation["column_confusion_flags"].append(
                            f"Value {amt} appears as both Vch No and Amount — verify"
                        )
                    if lab and str(int(amt)) == str(lab).strip():
                        validation["column_confusion_flags"].append(
                            f"Value {amt} matches Lab No {lab} — likely wrong column"
                        )

        # Check 4: Date consistency
        admission = bill_data.get("patient_details", {}).get("admission_date", "")
        discharge = bill_data.get("patient_details", {}).get("discharge_date", "")
        # Simplified — just flag if admission/discharge are present
        if not admission or not discharge:
            validation["date_consistency"] = False

        # Determine confidence
        subtotal_mismatches = sum(1 for c in validation["subtotal_checks"] if not c["match"])
        grand_match = validation["grand_total_check"]["match"] if validation["grand_total_check"] else True
        confusion_count = len(validation["column_confusion_flags"])

        if subtotal_mismatches == 0 and grand_match and confusion_count == 0:
            validation["extraction_confidence"] = "high"
            validation["confidence_reason"] = "All subtotals match, grand total verified"
        elif subtotal_mismatches <= 2 and grand_match:
            validation["extraction_confidence"] = "medium"
            validation["confidence_reason"] = f"{subtotal_mismatches} minor subtotal differences"
        else:
            validation["extraction_confidence"] = "low"
            reasons = []
            if subtotal_mismatches > 2:
                reasons.append(f"{subtotal_mismatches} subtotal mismatches")
            if not grand_match:
                reasons.append("Grand total mismatch")
            if confusion_count > 0:
                reasons.append(f"{confusion_count} column confusion warnings")
            validation["confidence_reason"] = "; ".join(reasons)

        return validation

    # ================================================================
    # POLICY-BILL MATCHING
    # ================================================================

    def match_bill_against_policy(self, bill_data: Dict, policy_data: Dict, bill_type: str = "hospital") -> Dict:
        """Match hospital bill against health insurance policy."""
        result = {
            "total_bill_amount": 0.0,
            "total_covered": 0.0,
            "total_not_covered": 0.0,
            "copay_amount": 0.0,
            "deductible_amount": 0.0,
            "estimated_out_of_pocket": 0.0,
            "si_available": 0.0,
            "si_remaining_after": 0.0,
            "si_exhaustion_warning": False,
            "coverage_percentage": 0.0,
            "proportionate_deduction_warning": False,
            "line_items": [],
        }

        csd = policy_data.get("category_specific_data", policy_data.get("categorySpecificData", {}))
        coverage_amount = self._safe_float(policy_data.get("coverageAmount", policy_data.get("coverage_amount", 0)))
        claims_ytd = self._safe_float(policy_data.get("claims_ytd", 0))
        available_si = coverage_amount - claims_ytd
        result["si_available"] = available_si

        total_billed = 0.0
        total_covered = 0.0

        # Flatten all line items from dynamic sections
        all_items = self._flatten_all_line_items(bill_data)

        for item in all_items:
            amount = self._safe_float(item.get("amount", item.get("total_amount", 0)))
            total_billed += amount
            desc = item.get("description", "Unknown")
            section = item.get("_section", "")

            # Room charges get special treatment
            if any(kw in section.lower() for kw in ["stay", "room", "ward", "bed", "icu", "nicu"]):
                item_result = self._match_room_item(item, csd)
                if item_result.get("triggers_proportionate_deduction"):
                    result["proportionate_deduction_warning"] = True
            else:
                # Default: covered within SI
                item_result = {
                    "description": desc,
                    "billed_amount": amount,
                    "covered_amount": amount,
                    "excess_amount": 0.0,
                    "status": "covered",
                    "reason": "Within policy coverage",
                    "triggers_proportionate_deduction": False,
                }

            # Check implant sub-limits
            if item.get("is_implant"):
                implant_limit = self._safe_float(csd.get("implantSubLimit", 0))
                if implant_limit > 0 and amount > implant_limit:
                    item_result["covered_amount"] = implant_limit
                    item_result["excess_amount"] = amount - implant_limit
                    item_result["status"] = "partial"
                    item_result["reason"] = f"Implant sub-limit Rs.{implant_limit:,.0f}"

            result["line_items"].append(item_result)
            total_covered += item_result.get("covered_amount", 0)

        # Copay
        copay_str = str(csd.get("coPayment", csd.get("copay", "0")))
        copay_pct = self._extract_percentage(copay_str)
        copay_amount = total_covered * copay_pct / 100 if copay_pct > 0 else 0.0
        total_covered -= copay_amount

        # SI exhaustion
        si_excess = 0.0
        if total_covered > available_si:
            si_excess = total_covered - available_si
            total_covered = available_si
            result["si_exhaustion_warning"] = True

        not_covered = total_billed - total_covered - copay_amount
        result["total_bill_amount"] = total_billed
        result["total_covered"] = total_covered
        result["total_not_covered"] = not_covered
        result["copay_amount"] = copay_amount
        result["estimated_out_of_pocket"] = not_covered + copay_amount + si_excess
        result["si_remaining_after"] = max(0, available_si - total_covered)
        result["coverage_percentage"] = round(total_covered / total_billed * 100, 1) if total_billed > 0 else 0

        return result

    def _match_room_item(self, item: Dict, csd: Dict) -> Dict:
        """Match a room charge item against policy limits."""
        amount = self._safe_float(item.get("amount", item.get("total_amount", 0)))
        qty = max(1, self._safe_float(item.get("quantity", item.get("days", 1))))
        rate_per_day = amount / qty if qty > 0 else amount
        desc = item.get("description", "Room")

        room_rent_limit_str = str(csd.get("roomRentLimit", "No Limit"))

        if "no limit" in room_rent_limit_str.lower() or not room_rent_limit_str or room_rent_limit_str == "0":
            return {
                "description": desc,
                "billed_amount": amount,
                "covered_amount": amount,
                "excess_amount": 0.0,
                "status": "covered",
                "reason": "No room rent limit",
                "triggers_proportionate_deduction": False,
            }

        limit_match = re.search(r'(\d[\d,]*)', room_rent_limit_str)
        if limit_match:
            limit_per_day = float(limit_match.group(1).replace(",", ""))
            if rate_per_day <= limit_per_day:
                return {
                    "description": desc,
                    "billed_amount": amount,
                    "covered_amount": amount,
                    "excess_amount": 0.0,
                    "status": "covered",
                    "reason": f"Within limit Rs.{limit_per_day:,.0f}/day",
                    "triggers_proportionate_deduction": False,
                }
            else:
                covered = limit_per_day * qty
                return {
                    "description": desc,
                    "billed_amount": amount,
                    "covered_amount": covered,
                    "excess_amount": amount - covered,
                    "status": "partial",
                    "reason": f"Exceeds limit Rs.{limit_per_day:,.0f}/day. Proportionate deduction may apply.",
                    "triggers_proportionate_deduction": True,
                }

        return {
            "description": desc, "billed_amount": amount, "covered_amount": amount,
            "excess_amount": 0.0, "status": "covered", "reason": "Default covered",
            "triggers_proportionate_deduction": False,
        }

    # ================================================================
    # DISCREPANCY DETECTION (Phase 4)
    # ================================================================

    def detect_discrepancies(self, bill_data: Dict, bill_type: str = "hospital") -> List[Dict]:
        """Run all discrepancy checks from v2 spec — PROVABLE errors only, no govt rate comparison."""
        discrepancies = []
        disc_counter = [0]

        def next_id():
            disc_counter[0] += 1
            return f"DISC_{disc_counter[0]:03d}"

        all_items = self._flatten_all_line_items(bill_data)
        patient = bill_data.get("patient_details", {})
        summary = bill_data.get("bill_summary", {})
        context = bill_data.get("hospital_context", {})

        is_surgical = bool(patient.get("procedure_performed") or patient.get("surgery_grade"))

        # 4.1 Duplicate charges
        discrepancies.extend(self._check_duplicates(all_items, next_id))
        # 4.1 Cross-section duplicates
        discrepancies.extend(self._check_cross_section_duplicates(all_items, next_id))
        # 4.2 Calculation errors
        discrepancies.extend(self._check_calculation_errors(all_items, next_id))
        # 4.4 Unbundling
        discrepancies.extend(self._check_unbundling(all_items, patient, next_id))
        # 4.5 Repeat tests
        discrepancies.extend(self._check_repeat_tests(all_items, patient, next_id))
        # 4.6 Complimentary items
        discrepancies.extend(self._check_complimentary_charges(all_items, next_id))
        # 4.7 Date outside stay
        discrepancies.extend(self._check_date_outside_stay(all_items, patient, next_id))
        # 4.8 Phantom charges
        discrepancies.extend(self._check_phantom_charges(all_items, patient, next_id))
        # 4.9 Package violation
        discrepancies.extend(self._check_package_violation(all_items, bill_data, next_id))
        # 4.10 Excessive quantity
        discrepancies.extend(self._check_excessive_quantity(all_items, patient, next_id))
        # 4.12 Unnecessary tests (informational only)
        discrepancies.extend(self._check_unnecessary_tests(all_items, patient, is_surgical, next_id))
        # Excessive consultants
        discrepancies.extend(self._check_excessive_consultants(all_items, patient, next_id))

        # Sort by severity
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "informational": 4}
        discrepancies.sort(key=lambda d: severity_order.get(d.get("severity", "low"), 3))

        return discrepancies

    def _flatten_all_line_items(self, bill_data: Dict) -> List[Dict]:
        """Flatten all line items from dynamic bill_sections, adding _section metadata."""
        items = []

        # New dynamic sections format
        for section in bill_data.get("bill_sections", []):
            section_name = section.get("section_name", "")
            for sub in section.get("subsections", []):
                for item in sub.get("line_items", []):
                    item_copy = dict(item)
                    item_copy["_section"] = section_name
                    item_copy["_subsection"] = sub.get("subsection_name", "")
                    items.append(item_copy)

        # Legacy flat format fallback
        if not items:
            for section_key in ["room_charges", "professional_fees", "procedure_charges",
                                "investigation_charges", "medicine_charges",
                                "consumables_charges", "other_charges"]:
                for item in bill_data.get(section_key, []):
                    item_copy = dict(item)
                    item_copy["_section"] = section_key
                    # Map legacy fields to new field names
                    if "total_amount" in item_copy and "amount" not in item_copy:
                        item_copy["amount"] = item_copy["total_amount"]
                    items.append(item_copy)

        return items

    def _check_duplicates(self, items: List[Dict], next_id) -> List[Dict]:
        """4.1 Duplicate charges — same item + same date + same amount (±₹1 tolerance)."""
        discrepancies = []
        seen = defaultdict(list)

        for item in items:
            desc = (item.get("description") or "").lower().strip()
            date = (item.get("date") or "").strip()
            amount = self._safe_float(item.get("amount"))
            if desc and amount > 0:
                # Round to nearest rupee for comparison (avoid float precision issues)
                key = (desc, date, round(amount))
                seen[key].append(item)

        for key, group in seen.items():
            if len(group) > 1:
                desc, date, amount = key
                discrepancies.append({
                    "id": next_id(),
                    "type": "DUPLICATE_CHARGE",
                    "category": "billing_error",
                    "severity": "high",
                    "description": f"Duplicate charge: '{desc}' on {date or 'same date'} for Rs.{amount:,.0f} appears {len(group)} times",
                    "item_name": desc,
                    "section_found_in": group[0].get("_section", ""),
                    "line_items_involved": [desc] * len(group),
                    "billed_amount": amount * len(group),
                    "benchmark_amount": amount,
                    "benchmark_source": "Internal Calculation",
                    "overcharged_amount": amount * (len(group) - 1),
                    "confidence": 0.95,
                    "confidence_category": "high",
                    "applicable_law": "Consumer Protection Act 2019",
                    "action": "Request removal of duplicate charge",
                })

        return discrepancies

    def _check_cross_section_duplicates(self, items: List[Dict], next_id) -> List[Dict]:
        """4.1 Cross-section duplicates — same service in different sections."""
        discrepancies = []
        by_desc = defaultdict(list)

        for item in items:
            desc = (item.get("description") or "").lower().strip()
            amount = self._safe_float(item.get("amount"))
            if desc and amount > 0:
                by_desc[desc].append(item)

        for desc, group in by_desc.items():
            sections = set(item.get("_section", "") for item in group)
            if len(sections) > 1 and len(group) > 1:
                total = sum(self._safe_float(i.get("amount")) for i in group)
                discrepancies.append({
                    "id": next_id(),
                    "type": "CROSS_SECTION_DUPLICATE",
                    "category": "billing_error",
                    "severity": "medium",
                    "description": f"'{desc}' appears in {len(sections)} different sections: {', '.join(sections)}",
                    "item_name": desc,
                    "section_found_in": ", ".join(sections),
                    "line_items_involved": [desc],
                    "billed_amount": total,
                    "overcharged_amount": total / 2,
                    "confidence": 0.6,
                    "confidence_category": "medium",
                    "applicable_law": "General Best Practice",
                    "action": "Request clarification — same service billed in multiple sections",
                })

        return discrepancies

    def _check_calculation_errors(self, items: List[Dict], next_id) -> List[Dict]:
        """4.2 Arithmetic errors: qty × unit_rate ≠ amount."""
        discrepancies = []

        for item in items:
            qty = self._safe_float(item.get("quantity"))
            rate = self._safe_float(item.get("unit_rate"))
            amount = self._safe_float(item.get("amount"))

            if qty > 0 and rate > 0 and amount > 0:
                expected = qty * rate
                diff = abs(expected - amount)
                # Tolerance: ₹2 or 0.5% of expected, whichever is larger (avoids false positives from rounding)
                tolerance = max(2.0, expected * 0.005)
                if diff > tolerance:
                    discrepancies.append({
                        "id": next_id(),
                        "type": "CALCULATION_ERROR",
                        "category": "billing_error",
                        "severity": "high",
                        "description": f"Calculation error: {qty} x Rs.{rate:,.0f} = Rs.{expected:,.0f} but billed Rs.{amount:,.0f}",
                        "item_name": item.get("description", ""),
                        "section_found_in": item.get("_section", ""),
                        "billed_amount": amount,
                        "benchmark_amount": expected,
                        "benchmark_source": "Internal Calculation",
                        "overcharged_amount": amount - expected if amount > expected else 0,
                        "confidence": 0.95,
                        "confidence_category": "high",
                        "applicable_law": "Consumer Protection Act 2019",
                        "action": "Request correction of calculation",
                    })

        return discrepancies

    def _check_package_violation(self, items: List[Dict], bill_data: Dict, next_id) -> List[Dict]:
        """4.9 Package violation — items billed separately when a package rate exists."""
        discrepancies = []

        # Detect if this is a package bill
        all_descs = set()
        package_items = []
        for item in items:
            desc = (item.get("description") or "").lower()
            amount = self._safe_float(item.get("amount"))
            all_descs.add(desc)
            if any(kw in desc for kw in ["package", "bundle", "bundled", "inclusive"]):
                package_items.append(item)

        # Check bill_type from metadata
        bill_type = (bill_data.get("metadata", {}).get("bill_type") or "").lower()
        is_package_bill = "package" in bill_type or bool(package_items)

        if not is_package_bill or not package_items:
            return discrepancies

        # Items typically included in packages
        package_inclusions = [
            "room", "bed", "nursing", "diet", "food",
            "medicine", "pharmacy", "drug",
            "ot charge", "ot rental", "operation theatre",
            "ot consumable", "surgical consumable",
            "suture", "dressing", "glove", "drape",
            "physiotherapy", "physio",
        ]

        for pkg in package_items:
            pkg_desc = (pkg.get("description") or "").lower()
            pkg_amount = self._safe_float(pkg.get("amount"))
            violations = []

            for item in items:
                if item is pkg:
                    continue
                item_desc = (item.get("description") or "").lower()
                item_amount = self._safe_float(item.get("amount"))
                if item_amount <= 0:
                    continue

                for inclusion in package_inclusions:
                    if inclusion in item_desc:
                        violations.append(item.get("description", item_desc))
                        break

            if violations:
                discrepancies.append({
                    "id": next_id(),
                    "type": "PACKAGE_VIOLATION",
                    "category": "unbundling",
                    "severity": "medium",
                    "description": f"Package '{pkg_desc}' exists but {len(violations)} items billed separately that may be included: {', '.join(v[:30] for v in violations[:5])}",
                    "item_name": pkg_desc,
                    "line_items_involved": violations[:10],
                    "billed_amount": pkg_amount,
                    "overcharged_amount": 0,
                    "confidence": 0.55,
                    "confidence_category": "medium",
                    "applicable_law": "Consumer Protection Act 2019",
                    "action": "Request confirmation of package inclusions — separately billed items may already be covered",
                })

        return discrepancies

    def _check_excessive_quantity(self, items: List[Dict], patient: Dict, next_id) -> List[Dict]:
        """4.10 Excessive quantity — quantities unreasonable for LOS/procedure."""
        discrepancies = []
        los = max(1, int(self._safe_float(patient.get("los_days", 1))))

        for item in items:
            desc = (item.get("description") or "").lower()
            qty = self._safe_float(item.get("quantity"))
            amount = self._safe_float(item.get("amount"))

            if qty <= 0 or amount <= 0:
                continue

            # Diet/meal charges more than days of stay × 3 meals
            if any(kw in desc for kw in ["diet", "food", "meal"]):
                expected_max = los * 3 + 3  # 3 meals/day + buffer
                if qty > expected_max and qty > 6:
                    discrepancies.append({
                        "id": next_id(),
                        "type": "EXCESSIVE_QUANTITY",
                        "category": "unnecessary",
                        "severity": "low",
                        "description": f"'{item.get('description', '')}' qty {qty} seems excessive for {los}-day stay (expected max ~{expected_max})",
                        "item_name": item.get("description", ""),
                        "section_found_in": item.get("_section", ""),
                        "billed_amount": amount,
                        "overcharged_amount": 0,
                        "confidence": 0.35,
                        "confidence_category": "low",
                        "applicable_law": "General Best Practice",
                        "action": "Request itemized justification for quantity",
                    })

            # Consumable quantities — ICU patients use much more
            if any(kw in desc for kw in ["syringe", "glove", "cannula", "needle"]):
                patient_class = (patient.get("patient_class") or "").lower()
                is_icu = any(kw in patient_class for kw in ["icu", "iccu", "hdu", "nicu", "critical"])
                multiplier = 30 if is_icu else 10  # ICU uses ~3x more consumables
                expected_max = los * multiplier
                if qty > expected_max and qty > (100 if is_icu else 30):
                    discrepancies.append({
                        "id": next_id(),
                        "type": "EXCESSIVE_QUANTITY",
                        "category": "unnecessary",
                        "severity": "low",
                        "description": f"'{item.get('description', '')}' qty {qty} may be excessive for {los}-day stay",
                        "item_name": item.get("description", ""),
                        "section_found_in": item.get("_section", ""),
                        "billed_amount": amount,
                        "overcharged_amount": 0,
                        "confidence": 0.3,
                        "confidence_category": "low",
                        "applicable_law": "General Best Practice",
                        "action": "Request itemized justification for quantity",
                    })

        return discrepancies

    def _check_unbundling(self, items: List[Dict], patient: Dict, next_id) -> List[Dict]:
        """4.5 Unbundling detection — separately billed items that should be in package."""
        discrepancies = []
        all_descs = set()
        for item in items:
            d = (item.get("description") or "").lower()
            all_descs.add(d)

        procedure = (patient.get("procedure_performed") or "").lower()

        for proc_key, bundled_items in self.unbundling_patterns.items():
            # Check if this procedure was performed
            proc_found = proc_key in procedure
            if not proc_found:
                for d in all_descs:
                    if proc_key in d:
                        proc_found = True
                        break

            if proc_found:
                found_bundled = []
                for bundled in bundled_items:
                    for d in all_descs:
                        if bundled in d:
                            found_bundled.append(bundled)
                            break

                if found_bundled:
                    discrepancies.append({
                        "id": next_id(),
                        "type": "UNBUNDLED_PROCEDURE",
                        "category": "unbundling",
                        "severity": "high",
                        "description": f"Procedure '{proc_key}' detected with {len(found_bundled)} separately billed items that may be included in package: {', '.join(found_bundled)}",
                        "item_name": proc_key,
                        "line_items_involved": found_bundled,
                        "billed_amount": 0,
                        "overcharged_amount": 0,
                        "confidence": 0.65,
                        "confidence_category": "medium",
                        "applicable_law": "Clinical Establishments Act",
                        "action": f"Request bundled/package rate for {proc_key}",
                    })

        return discrepancies

    def _check_unnecessary_tests(self, items: List[Dict], patient: Dict, is_surgical: bool, next_id) -> List[Dict]:
        """4.6 Unnecessary test detection — diagnosis-specific with comorbidity awareness."""
        discrepancies = []
        diagnosis = (patient.get("primary_diagnosis") or "").lower()
        secondary = (patient.get("secondary_diagnosis") or "").lower()
        procedure = (patient.get("procedure_performed") or "").lower()
        all_diagnosis = f"{diagnosis} {secondary} {procedure}"

        # Find matching diagnosis
        unnecessary_tests = set()
        for diag_key, tests in self.unnecessary_tests_by_diagnosis.items():
            if diag_key in diagnosis or diag_key in procedure:
                unnecessary_tests.update(tests)

        if not unnecessary_tests:
            return discrepancies

        # Comorbidity awareness — if secondary diagnosis justifies a test, skip it
        # Build a set of tests justified by secondary diagnosis / comorbidities
        justified_by_comorbidity = set()
        comorbidity_keywords = ["diabetes", "hypertension", "cardiac", "renal", "liver",
                                "thyroid", "anemia", "obesity", "copd", "asthma"]
        has_comorbidities = any(c in all_diagnosis for c in comorbidity_keywords)

        # Standard admission tests justified by common comorbidities
        standard_medical_tests = {"cbc", "complete blood count", "blood sugar", "glucose",
                                  "serum creatinine", "creatinine", "electrolytes",
                                  "urine routine", "chest x-ray", "ecg", "electrocardiogram"}

        for item in items:
            desc = (item.get("description") or "").lower()
            amount = self._safe_float(item.get("amount"))
            section = (item.get("_section") or "").lower()

            # Only check investigation/diagnostic sections
            if not any(kw in section for kw in ["diagnos", "investig", "lab", "pathol", "radiol", "test"]):
                continue

            # Skip standard pre-op tests for surgical patients
            if is_surgical:
                is_preop = any(preop in desc for preop in self.standard_preop_tests)
                if is_preop:
                    continue

            # Skip standard admission tests for non-surgical patients (routine medical workup)
            if not is_surgical and any(std in desc for std in standard_medical_tests):
                continue

            for test_kw in unnecessary_tests:
                if test_kw in desc:
                    # If patient has comorbidities, lower severity and confidence
                    if has_comorbidities:
                        severity = "low"
                        confidence = 0.25
                        note = f" Note: Patient has comorbidities ({secondary or 'noted'}) that may justify this test."
                    else:
                        severity = "medium"
                        confidence = 0.45
                        note = ""
                    discrepancies.append({
                        "id": next_id(),
                        "type": "UNNECESSARY_TEST",
                        "category": "unnecessary",
                        "severity": severity,
                        "description": f"'{desc}' is typically unnecessary for {diagnosis or procedure}.{note}",
                        "item_name": desc,
                        "section_found_in": item.get("_section", ""),
                        "billed_amount": amount,
                        "overcharged_amount": amount,
                        "confidence": confidence,
                        "confidence_category": "low",
                        "applicable_law": "Clinical Guidelines",
                        "action": "Request clinical justification from treating physician",
                    })
                    break

        return discrepancies

    def _check_repeat_tests(self, items: List[Dict], patient: Dict, next_id) -> List[Dict]:
        """4.7 Repeat test detection with time-based severity."""
        discrepancies = []
        test_dates = defaultdict(list)

        patient_class = (patient.get("patient_class") or "").lower()
        is_icu = any(kw in patient_class for kw in ["icu", "iccu", "hdu", "nicu", "critical"])

        for item in items:
            desc = (item.get("description") or "").lower().strip()
            date_str = (item.get("date") or "").strip()
            amount = self._safe_float(item.get("amount"))
            section = (item.get("_section") or "").lower()

            if not any(kw in section for kw in ["diagnos", "investig", "lab", "pathol", "radiol", "test"]):
                continue

            if desc and date_str and amount > 0:
                test_dates[desc].append({"date": date_str, "amount": amount, "item": item})

        for test_name, occurrences in test_dates.items():
            if len(occurrences) <= 1:
                continue

            # ICU patients: frequent repeats of certain tests are normal
            if is_icu and any(kw in test_name for kw in self.icu_frequent_tests):
                continue

            # Same test, same date → HIGH severity duplicate
            dates = [o["date"] for o in occurrences]
            date_counts = defaultdict(int)
            for d in dates:
                date_counts[d] += 1

            for date, count in date_counts.items():
                if count > 1:
                    total_amount = sum(o["amount"] for o in occurrences if o["date"] == date)
                    discrepancies.append({
                        "id": next_id(),
                        "type": "REPEAT_TEST",
                        "category": "unnecessary",
                        "severity": "high",
                        "description": f"'{test_name}' repeated {count} times on {date}",
                        "item_name": test_name,
                        "section_found_in": occurrences[0]["item"].get("_section", ""),
                        "billed_amount": total_amount,
                        "overcharged_amount": total_amount * (count - 1) / count,
                        "confidence": 0.8,
                        "confidence_category": "high",
                        "applicable_law": "Clinical Guidelines",
                        "action": "Request removal of duplicate test or clinical justification",
                    })

            # Different dates but >2 occurrences total → MEDIUM
            if len(occurrences) > 2 and not any(d > 1 for d in date_counts.values()):
                total = sum(o["amount"] for o in occurrences)
                discrepancies.append({
                    "id": next_id(),
                    "type": "REPEAT_TEST",
                    "category": "unnecessary",
                    "severity": "medium",
                    "description": f"'{test_name}' performed {len(occurrences)} times across stay",
                    "item_name": test_name,
                    "section_found_in": occurrences[0]["item"].get("_section", ""),
                    "billed_amount": total,
                    "overcharged_amount": 0,
                    "confidence": 0.5,
                    "confidence_category": "medium",
                    "applicable_law": "Clinical Guidelines",
                    "action": "Request clinical justification for repeat tests",
                })

        return discrepancies

    def _check_complimentary_charges(self, items: List[Dict], next_id) -> List[Dict]:
        """4.8 Complimentary items that should not be charged."""
        discrepancies = []

        for item in items:
            desc = (item.get("description") or "").lower()
            amount = self._safe_float(item.get("amount"))
            section = (item.get("_section") or "").lower()

            if amount <= 0:
                continue

            # Skip items in OT/Surgical sections (gloves, masks etc. are legitimate there)
            is_surgical_section = any(kw in section for kw in ["ot ", "o.t.", "operation", "surgical", "surgery", "procedure"])

            for comp in self.complimentary_items:
                if comp in desc:
                    # If in surgical context and item is an OT exception, skip
                    if is_surgical_section and any(exc in desc for exc in self.complimentary_exceptions_in_ot):
                        break
                    # "Surgical gloves" in any section are legitimate
                    if "surgical" in desc and any(exc in desc for exc in self.complimentary_exceptions_in_ot):
                        break
                    discrepancies.append({
                        "id": next_id(),
                        "type": "COMPLIMENTARY_CHARGED",
                        "category": "compliance",
                        "severity": "medium" if amount > 100 else "low",
                        "description": f"'{item.get('description', '')}' (Rs.{amount:,.0f}) is a standard complimentary item",
                        "item_name": item.get("description", ""),
                        "section_found_in": item.get("_section", ""),
                        "billed_amount": amount,
                        "overcharged_amount": amount,
                        "confidence": 0.7,
                        "confidence_category": "medium",
                        "applicable_law": "General Best Practice",
                        "action": "Request removal — standard complimentary item included in room charges",
                    })
                    break

        return discrepancies

    def _check_date_outside_stay(self, items: List[Dict], patient: Dict, next_id) -> List[Dict]:
        """4.9 Flag charges with dates before admission or after discharge."""
        discrepancies = []
        admission = patient.get("admission_date", "")
        discharge = patient.get("discharge_date", "")

        if not admission or not discharge:
            return discrepancies

        # Parse dates (try multiple formats)
        adm_date = self._parse_date(admission)
        dis_date = self._parse_date(discharge)
        if not adm_date or not dis_date:
            return discrepancies

        for item in items:
            date_str = (item.get("date") or "").strip()
            if not date_str:
                continue

            item_date = self._parse_date(date_str)
            if not item_date:
                continue

            amount = self._safe_float(item.get("amount"))
            # Allow ±1 day for discharge-day billing
            if item_date < adm_date - timedelta(days=1) or item_date > dis_date + timedelta(days=1):
                discrepancies.append({
                    "id": next_id(),
                    "type": "DATE_OUTSIDE_STAY",
                    "category": "billing_error",
                    "severity": "high",
                    "description": f"'{item.get('description', '')}' dated {date_str} is outside stay period ({admission} to {discharge})",
                    "item_name": item.get("description", ""),
                    "section_found_in": item.get("_section", ""),
                    "billed_amount": amount,
                    "overcharged_amount": amount,
                    "confidence": 0.9,
                    "confidence_category": "high",
                    "applicable_law": "Consumer Protection Act 2019",
                    "action": "Request removal — service date is outside admission period",
                })

        return discrepancies

    def _check_phantom_charges(self, items: List[Dict], patient: Dict, next_id) -> List[Dict]:
        """4.10 Ghost charges that make no clinical sense."""
        discrepancies = []
        patient_class = (patient.get("patient_class") or "").lower()
        gender = (patient.get("gender") or "").upper()
        procedure = (patient.get("procedure_performed") or "").lower()
        is_surgical = bool(procedure or patient.get("surgery_grade"))

        # Collect what's in the bill
        all_descs = set()
        for item in items:
            all_descs.add((item.get("description") or "").lower())

        for item in items:
            desc = (item.get("description") or "").lower()
            amount = self._safe_float(item.get("amount"))
            if amount <= 0:
                continue

            # ICU charges when patient was in General Ward
            if any(kw in desc for kw in ["icu charge", "icu rent", "iccu charge"]):
                if "general" in patient_class and "icu" not in patient_class:
                    discrepancies.append({
                        "id": next_id(),
                        "type": "PHANTOM_CHARGE",
                        "category": "billing_error",
                        "severity": "high",
                        "description": f"ICU charges (Rs.{amount:,.0f}) but patient was in {patient_class}",
                        "item_name": item.get("description", ""),
                        "section_found_in": item.get("_section", ""),
                        "billed_amount": amount,
                        "overcharged_amount": amount,
                        "confidence": 0.7,
                        "confidence_category": "medium",
                        "applicable_law": "Consumer Protection Act 2019",
                        "action": "Request verification — ICU charges inconsistent with ward type",
                    })

            # Labour room charges for male patient or non-maternity case
            is_male = gender == "M"
            is_not_maternity = gender and gender != "F" and not any(
                kw in procedure for kw in ["delivery", "lscs", "c-section", "labour", "cesarean", "caesarean"]
            )
            if ("labour room" in desc or "labor room" in desc) and (is_male or is_not_maternity):
                discrepancies.append({
                    "id": next_id(),
                    "type": "PHANTOM_CHARGE",
                    "category": "billing_error",
                    "severity": "high",
                    "description": f"Labour room charges (Rs.{amount:,.0f}) for {'male' if is_male else 'non-maternity'} patient",
                    "item_name": item.get("description", ""),
                    "section_found_in": item.get("_section", ""),
                    "billed_amount": amount,
                    "overcharged_amount": amount,
                    "confidence": 0.95,
                    "confidence_category": "high",
                    "applicable_law": "Consumer Protection Act 2019",
                    "action": "Request removal — clinically impossible",
                })

            # Ventilator charges without ICU/critical care context
            if any(kw in desc for kw in ["ventilator", "mechanical ventilation"]):
                if patient_class and not any(kw in patient_class for kw in ["icu", "iccu", "hdu", "critical", "nicu"]):
                    discrepancies.append({
                        "id": next_id(),
                        "type": "PHANTOM_CHARGE",
                        "category": "billing_error",
                        "severity": "medium",
                        "description": f"Ventilator charges (Rs.{amount:,.0f}) but patient in {patient_class or 'non-ICU ward'}",
                        "item_name": item.get("description", ""),
                        "section_found_in": item.get("_section", ""),
                        "billed_amount": amount,
                        "overcharged_amount": amount,
                        "confidence": 0.6,
                        "confidence_category": "medium",
                        "applicable_law": "Consumer Protection Act 2019",
                        "action": "Request clinical documentation — ventilator use outside ICU needs justification",
                    })

        return discrepancies

    def _check_excessive_consultants(self, items: List[Dict], patient: Dict, next_id) -> List[Dict]:
        """Check for excessive consultant visits relative to LOS."""
        discrepancies = []
        los = max(1, int(self._safe_float(patient.get("los_days", 1))))
        admission_type = (patient.get("admission_type") or "").lower()

        # Consultant visit keywords — exclude procedure/surgery fees
        visit_keywords = ["consultant visit", "consultation", "doctor visit", "doctor charge",
                          "round visit", "visiting charge", "professional fee visit"]
        # Keywords that mean it's NOT a visit (procedure fees, surgery fees)
        exclude_keywords = ["surgery", "surgical", "procedure", "operation", "ot charge",
                           "anesthesia", "anaesthesia", "package"]

        visit_count = 0
        visit_total = 0.0
        for item in items:
            desc = (item.get("description") or "").lower()
            section = (item.get("_section") or "").lower()
            # Match on visit-specific keywords, not generic "fee" which catches procedure fees
            is_visit = any(kw in desc for kw in visit_keywords)
            is_excluded = any(kw in desc for kw in exclude_keywords)
            # Also check section-level: "Doctor Fees" / "Consultant" section
            if not is_visit and ("consult" in section or "doctor" in section) and not is_excluded:
                is_visit = "fee" in desc or "charge" in desc or "visit" in desc
            if is_visit and not is_excluded:
                visit_count += 1
                visit_total += self._safe_float(item.get("amount"))

        # Emergency/critical = more visits expected
        if admission_type in ("emergency", "critical"):
            expected_max = los * 3
        else:
            expected_max = los * 2
        if visit_count > expected_max and visit_count > 4:
            discrepancies.append({
                "id": next_id(),
                "type": "EXCESSIVE_CONSULTANT",
                "category": "unnecessary",
                "severity": "low",
                "description": f"{visit_count} consultant visits for {los}-day stay (expected max ~{expected_max})",
                "item_name": "Consultant visits",
                "billed_amount": visit_total,
                "overcharged_amount": 0,
                "confidence": 0.4,
                "confidence_category": "low",
                "applicable_law": "General Best Practice",
                "action": "Request visit log and clinical justification",
            })

        return discrepancies

    # ================================================================
    # SAVINGS CALCULATION (Phase 5)
    # ================================================================

    def calculate_savings(self, discrepancies: List[Dict]) -> Dict:
        """Calculate savings with 3-tier confidence model."""
        high_types = {
            "DUPLICATE_CHARGE", "CALCULATION_ERROR", "PRICE_ABOVE_MRP",
            "COMPLIMENTARY_CHARGED", "DATE_OUTSIDE_STAY", "PHANTOM_CHARGE",
        }
        medium_types = {
            "UNBUNDLED_PROCEDURE", "CROSS_SECTION_DUPLICATE",
            "REPEAT_TEST", "PACKAGE_VIOLATION",
        }
        low_types = {
            "UNNECESSARY_TEST", "EXCESSIVE_CONSULTANT", "EXCESSIVE_QUANTITY",
            "INFLATED_QUANTITY", "UPCODED_PROCEDURE", "NABH_VIOLATION",
        }

        high_total = 0.0
        medium_total = 0.0
        low_total = 0.0
        total = 0.0
        breakdown = defaultdict(float)
        dispute_items = []

        for d in discrepancies:
            overcharged = self._safe_float(d.get("overcharged_amount"))
            d_type = d.get("type", "")
            category = d.get("category", "")
            total += overcharged
            breakdown[category] += overcharged

            if d_type in high_types:
                high_total += overcharged
            elif d_type in medium_types:
                medium_total += overcharged
            elif d_type in low_types:
                low_total += overcharged
            else:
                low_total += overcharged

            if overcharged > 0:
                dispute_items.append(d.get("id", ""))

        conservative = high_total + (medium_total * 0.5)
        moderate = high_total + (medium_total * 0.75) + (low_total * 0.25)
        optimistic = high_total + medium_total + low_total

        # Sort dispute items by confidence (highest first)
        conf_map = {d.get("id"): d.get("confidence", 0) for d in discrepancies}
        dispute_items.sort(key=lambda x: conf_map.get(x, 0), reverse=True)

        return {
            "total_discrepancy_amount": round(total, 2),
            "high_confidence_savings": round(high_total, 2),
            "medium_confidence_savings": round(medium_total, 2),
            "low_confidence_savings": round(low_total, 2),
            "conservative_estimate": round(conservative, 2),
            "moderate_estimate": round(moderate, 2),
            "optimistic_estimate": round(optimistic, 2),
            "breakdown_by_type": dict(breakdown),
            "items_to_dispute": len(dispute_items),
            "dispute_priority_order": dispute_items,
        }

    # ================================================================
    # BILL HEALTH SCORE (Phase 6)
    # ================================================================

    def calculate_bill_health_score(self, bill_data: Dict, discrepancies: List[Dict],
                                     validation: Dict) -> Dict:
        """Calculate bill health score (0-100) with 4 factors per v2 spec."""
        scores = {}
        patient = bill_data.get("patient_details", {})
        hospital_ctx = bill_data.get("hospital_context", {})
        metadata = bill_data.get("metadata", {})

        # Detect bill detail level
        all_items = self._flatten_all_line_items(bill_data)
        items_without_rate = sum(1 for i in all_items if self._safe_float(i.get("unit_rate")) == 0)
        items_with_rate = len(all_items) - items_without_rate
        bill_type_str = (metadata.get("bill_type") or "").lower()
        is_true_summary = (
            len(all_items) <= 3 and items_with_rate == 0
        )
        is_interim = bill_type_str in ("interim", "estimate")
        is_category_breakdown = len(all_items) >= 4 and items_with_rate == 0

        # 1. Extraction completeness (0-20) — did we capture everything?
        confidence = validation.get("extraction_confidence", "medium")
        if confidence == "high":
            base_score = 20
        elif confidence == "medium":
            base_score = 14
        else:
            base_score = 6

        # Penalize for missing critical fields
        hospital_name = hospital_ctx.get("hospital_name") or metadata.get("hospital_name", "")
        missing_penalties = 0
        if not hospital_name:
            missing_penalties += 3
        if not patient.get("primary_diagnosis"):
            missing_penalties += 2
        if not patient.get("discharge_date"):
            missing_penalties += 2
        if not patient.get("admission_date"):
            missing_penalties += 3
        scores["extraction_completeness"] = max(2, base_score - missing_penalties)

        # 2. Billing accuracy (0-30) — calculation errors, duplicates, phantom charges, date errors
        accuracy_types = {"DUPLICATE_CHARGE", "CROSS_SECTION_DUPLICATE", "CALCULATION_ERROR",
                          "DATE_OUTSIDE_STAY", "PHANTOM_CHARGE"}
        accuracy_issues = [d for d in discrepancies if d.get("type") in accuracy_types]
        if len(accuracy_issues) == 0:
            scores["billing_accuracy"] = 30
        elif len(accuracy_issues) <= 1:
            scores["billing_accuracy"] = 22
        elif len(accuracy_issues) <= 3:
            scores["billing_accuracy"] = 12
        else:
            scores["billing_accuracy"] = 4

        # 3. Billing transparency (0-25) — is bill itemized? are charges clear?
        sections = bill_data.get("bill_sections", [])
        has_multiple_sections = len(sections) >= 3
        has_subtotals = all(s.get("section_subtotal", 0) > 0 for s in sections) if sections else False
        total_line_items = sum(
            len(item) for s in sections for sub in s.get("subsections", []) for item in [sub.get("line_items", [])]
        )
        # Items with unit_rate = truly itemized; without = just category totals
        items_with_rate = len(all_items) - items_without_rate

        if has_multiple_sections and has_subtotals and items_with_rate >= 10:
            scores["billing_transparency"] = 25
        elif has_multiple_sections and has_subtotals and total_line_items >= 10:
            scores["billing_transparency"] = 20
        elif total_line_items >= 8:
            # Good category breakdown even if not multi-section
            scores["billing_transparency"] = 15
        elif has_multiple_sections:
            scores["billing_transparency"] = 12
        elif total_line_items >= 5:
            scores["billing_transparency"] = 10
        else:
            scores["billing_transparency"] = 3

        # 4. Billing practices (0-25) — unbundling, complimentary charging, package violations
        practice_types = {"UNBUNDLED_PROCEDURE", "COMPLIMENTARY_CHARGED", "PACKAGE_VIOLATION",
                          "EXCESSIVE_QUANTITY", "REPEAT_TEST", "EXCESSIVE_CONSULTANT",
                          "PRICE_ABOVE_MRP", "NABH_VIOLATION"}
        practice_issues = [d for d in discrepancies if d.get("type") in practice_types]
        if len(practice_issues) == 0:
            scores["billing_practices"] = 25
        elif len(practice_issues) <= 2:
            scores["billing_practices"] = 18
        elif len(practice_issues) <= 5:
            scores["billing_practices"] = 10
        else:
            scores["billing_practices"] = 3

        # Penalty based on bill detail level
        if is_true_summary:
            # True summary (1-3 lump items) — heavy penalty, can't verify much
            scores["billing_accuracy"] = min(scores["billing_accuracy"], 12)
            scores["billing_practices"] = min(scores["billing_practices"], 10)
        elif is_interim:
            # Interim/estimate — moderate penalty (amounts may change)
            scores["billing_accuracy"] = min(scores["billing_accuracy"], 20)
            scores["billing_practices"] = min(scores["billing_practices"], 18)
        # Category breakdown (5+ categories, no unit rates) — no penalty;
        # transparency score already handles this via items_with_rate check

        total = sum(scores.values())

        if total >= 90:
            grade = "A"
        elif total >= 75:
            grade = "B"
        elif total >= 60:
            grade = "C"
        elif total >= 40:
            grade = "D"
        else:
            grade = "F"

        # Interpretation
        if is_true_summary:
            interpretation = "Bill has only lump-sum totals — request itemized bill for complete audit"
        elif is_interim:
            interpretation = "Interim/estimate bill — final amounts may differ"
        elif is_category_breakdown:
            interpretation = f"Bill has {len(all_items)} charge categories; request detailed breakup for deeper audit"
        elif grade == "A":
            interpretation = "Bill is well-itemized with fair pricing and no significant discrepancies"
        elif grade == "B":
            interpretation = "Bill is generally fair with minor concerns"
        elif grade == "C":
            interpretation = "Bill has moderate pricing concerns — review recommended"
        elif grade == "D":
            interpretation = "Bill has significant issues — detailed dispute recommended"
        else:
            interpretation = "Bill has critical pricing and accuracy issues — immediate action recommended"

        return {
            "score": total,
            "grade": grade,
            "interpretation": interpretation,
            "factors": scores,
        }

    # ================================================================
    # MAIN ENTRY POINT
    # ================================================================

    def analyze_bill(self, file_contents: List[bytes], filenames: List[str],
                     file_types: List[str], policy_data: Optional[Dict] = None) -> Dict:
        """
        Complete hospital bill analysis pipeline.
        1. Text extraction → 2. Structured extraction → 3. Validation
        4. Policy matching → 5. Discrepancy detection → 6. Savings → 7. Health score
        """
        # Step 1: Text extraction
        image_contents = []
        image_filenames = []
        pdf_texts = []

        for content, fname, ftype in zip(file_contents, filenames, file_types):
            if ftype == "image":
                image_contents.append(content)
                image_filenames.append(fname)
            elif ftype == "pdf":
                try:
                    pdf_text = self.extract_text_from_pdf(content)
                    pdf_texts.append(pdf_text)
                except Exception as e:
                    logger.warning(f"PDF extraction failed for {fname}: {e}")

        all_text = ""
        if image_contents:
            all_text += self.extract_text_from_images(image_contents, image_filenames)
        if pdf_texts:
            all_text += "\n".join(pdf_texts)

        if not all_text.strip():
            raise Exception("No text could be extracted from uploaded files")

        # Step 2: Structured extraction
        # Use GPT-4o for images, DeepSeek for PDFs
        source_type = "pdf" if pdf_texts and not image_contents else "image"
        bill_data = self.extract_structured_data(all_text, source_type=source_type)

        # Step 3: Validation
        validation = self.validate_extraction(bill_data)
        bill_data["extraction_validation"] = validation

        # Step 4: Policy matching
        coverage_analysis = None
        if policy_data:
            try:
                coverage_analysis = self.match_bill_against_policy(bill_data, policy_data)
            except Exception as e:
                logger.warning(f"Policy matching failed: {e}")

        # Step 5: Discrepancy detection (v2: provable errors only, no govt rate comparison)
        discrepancies = self.detect_discrepancies(bill_data, "hospital")

        # Step 6: Savings calculation
        savings = self.calculate_savings(discrepancies)

        # Step 7: Bill health score
        bill_health_score = self.calculate_bill_health_score(bill_data, discrepancies, validation)

        # Generate limitations
        limitations = self._generate_limitations(bill_data, validation)

        # Generate recommendations
        recommendations = self._generate_recommendations(discrepancies, savings, bill_data)

        return {
            "bill_type": "hospital",
            "audit_version": "2.0-india-no-govt-benchmark",
            "extracted_text": all_text,
            "bill_data": bill_data,
            "extraction_validation": validation,
            "coverage_analysis": coverage_analysis,
            "discrepancies": discrepancies,
            "savings": savings,
            "bill_health_score": bill_health_score,
            "limitations": limitations,
            "recommendations": recommendations,
        }

    def _generate_limitations(self, bill_data: Dict, validation: Dict) -> List[str]:
        """Generate honest limitations list."""
        limitations = []
        confidence = validation.get("extraction_confidence", "medium")
        patient = bill_data.get("patient_details", {})
        metadata = bill_data.get("metadata", {})
        hospital_ctx = bill_data.get("hospital_context", {})

        if confidence == "low":
            limitations.append("Extraction confidence is low — some values may be inaccurate. Manual verification recommended.")

        # Detect bill detail level
        bill_type = (metadata.get("bill_type") or "").lower()
        all_items = self._flatten_all_line_items(bill_data)
        items_without_rate = sum(1 for i in all_items if self._safe_float(i.get("unit_rate")) == 0)
        items_with_rate = len(all_items) - items_without_rate

        if bill_type in ("interim", "estimate"):
            limitations.append(f"This is a '{bill_type}' bill — not a final discharge bill. Final amounts may differ.")

        # Distinguish: true summary (≤3 lump items) vs category breakdown (5+ categories) vs itemized
        if all_items and items_with_rate == 0:
            if len(all_items) <= 3:
                # True summary — just 1-3 lump amounts
                limitations.append(
                    "Bill contains only lump-sum totals without any category breakdown. "
                    "Detailed discrepancy detection requires itemized charges."
                )
            elif len(all_items) <= 15:
                # Category-level breakdown — meaningful structure but no per-item detail
                limitations.append(
                    f"Bill has {len(all_items)} charge categories but individual line items within each category "
                    "(e.g., specific medicine names, individual test names with dates) are not listed. "
                    "Per-item pricing audit is limited to category-level checks."
                )
            else:
                # Many items but all missing unit_rate — likely OCR issue
                limitations.append(
                    "Unit rates could not be extracted for individual items — pricing checks are limited"
                )

        # Consolidate bulk charges into a single limitation (instead of one per item)
        bulk_keywords = [
            "pharmacy", "medicine", "med", "drug", "mat & med", "material",
            "lab", "radiology", "diagnostic", "investigation",
            "care team", "medical equipment", "equipment",
            "other charges", "miscellaneous", "consumable",
            "bed charges", "nursing", "diet",
        ]
        bulk_charges = []
        for item in all_items:
            desc = item.get("description", "")
            desc_lower = desc.lower()
            amount = self._safe_float(item.get("amount"))
            rate = self._safe_float(item.get("unit_rate"))
            if amount > 10000 and rate == 0 and any(kw in desc_lower for kw in bulk_keywords):
                bulk_charges.append(f"{desc} (Rs.{amount:,.0f})")

        if bulk_charges:
            if len(bulk_charges) <= 2:
                limitations.append(
                    f"High-value category charges without item-level breakup: {', '.join(bulk_charges)}"
                )
            else:
                limitations.append(
                    f"{len(bulk_charges)} high-value categories lack individual item breakup — "
                    f"request detailed bills for: {', '.join(bulk_charges[:3])}"
                    + (f" and {len(bulk_charges) - 3} more" if len(bulk_charges) > 3 else "")
                )

        # Missing critical fields
        hospital_name = hospital_ctx.get("hospital_name") or metadata.get("hospital_name", "")
        if not hospital_name:
            limitations.append("Hospital name could not be extracted from the bill")

        if not patient.get("primary_diagnosis"):
            limitations.append("Primary diagnosis not stated on bill — unnecessary test detection may be less accurate")

        if not patient.get("discharge_date"):
            if bill_type not in ("interim", "estimate"):
                limitations.append("Discharge date not found — date-based checks (date-outside-stay) are disabled")

        los = int(self._safe_float(patient.get("los_days", 0)))
        if los == 0 and patient.get("admission_date"):
            limitations.append("Length of stay is 0 days — quantity and duration-based checks may be less accurate")

        if not limitations:
            limitations.append("No significant limitations identified in this audit")

        return limitations

    def _generate_recommendations(self, discrepancies: List[Dict], savings: Dict,
                                    bill_data: Dict = None) -> List[str]:
        """Generate actionable recommendations."""
        recs = []
        bill_data = bill_data or {}
        metadata = bill_data.get("metadata", {})

        # Detect bill detail level
        bill_type = (metadata.get("bill_type") or "").lower()
        all_items = self._flatten_all_line_items(bill_data) if bill_data else []
        items_without_rate = sum(1 for i in all_items if self._safe_float(i.get("unit_rate")) == 0)
        items_with_rate = len(all_items) - items_without_rate

        is_interim = bill_type in ("interim", "estimate")
        is_true_summary = len(all_items) <= 3 and items_with_rate == 0
        is_category_breakdown = len(all_items) >= 4 and items_with_rate == 0

        if is_interim:
            recs.append(
                "This is an interim/estimate bill — request the FINAL DISCHARGE BILL for accurate audit"
            )
        elif is_true_summary:
            recs.append(
                "Request the ITEMIZED BILL with individual line items, unit rates, and service dates for a complete audit"
            )
        elif is_category_breakdown:
            recs.append(
                "Request detailed breakup within high-value categories (e.g., individual medicine names, test names with dates) for deeper audit"
            )

        # Check for bulk pharmacy/medicine charges
        for item in all_items:
            desc = (item.get("description") or "").lower()
            amount = self._safe_float(item.get("amount"))
            rate = self._safe_float(item.get("unit_rate"))
            if amount > 20000 and rate == 0 and any(kw in desc for kw in ["pharmacy", "medicine", "drug", "med"]):
                recs.append("Request detailed pharmacy breakup to verify individual medicine pricing against MRP")
                break

        # Discrepancy-based recommendations
        high_conf = [d for d in discrepancies if d.get("confidence_category") == "high"]
        if high_conf:
            recs.append(f"Dispute {len(high_conf)} high-confidence items first (calculation errors, duplicates)")

        unbundled = [d for d in discrepancies if d.get("type") == "UNBUNDLED_PROCEDURE"]
        if unbundled:
            recs.append("Request itemized OT consumables list and bundled package rates")

        conservative = savings.get("conservative_estimate", 0)
        if conservative > 0:
            recs.append(f"Conservative recoverable savings: Rs.{conservative:,.0f}")

        if not recs:
            recs.append("Bill appears fair — no significant action items identified")

        return recs

    # ================================================================
    # HELPER METHODS
    # ================================================================

    @staticmethod
    def _safe_float(value, default=0.0) -> float:
        """Safely convert value to float, handling Indian lakh/crore formats."""
        if value is None:
            return default
        try:
            if isinstance(value, str):
                value = value.replace("₹", "").replace("Rs.", "").replace("Rs", "").replace("INR", "").strip()
                # Handle lakh/crore shorthand: "1.5L" → 150000, "2.5Cr" → 25000000
                lakh_match = re.match(r'^([\d.]+)\s*(?:L|Lac|Lakh|Lacs)s?$', value, re.IGNORECASE)
                if lakh_match:
                    return float(lakh_match.group(1)) * 100000
                crore_match = re.match(r'^([\d.]+)\s*(?:Cr|Crore|Crs)s?$', value, re.IGNORECASE)
                if crore_match:
                    return float(crore_match.group(1)) * 10000000
                # Remove commas (works for both 1,52,699 Indian and 152,699 western)
                value = value.replace(",", "")
                # Remove trailing non-numeric chars like "/- " (common in Indian bills: "Rs. 1,52,699/-")
                value = re.sub(r'[/\-]+\s*$', '', value).strip()
            return float(value)
        except (ValueError, TypeError):
            return default

    @staticmethod
    def _extract_percentage(text: str) -> float:
        """Extract percentage from text like '20%' or '20 percent'."""
        match = re.search(r'(\d+(?:\.\d+)?)\s*%', str(text))
        return float(match.group(1)) if match else 0.0

    @staticmethod
    def _parse_date(date_str: str) -> Optional[datetime]:
        """Parse date string in multiple Indian formats."""
        formats = [
            "%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y",
            "%Y-%m-%d", "%d/%m/%y", "%d-%m-%y",
            "%d %b %Y", "%d %B %Y",
            "%d-%b-%Y", "%d-%b-%y",       # 01-Jan-2024, 01-Jan-24
            "%d/%b/%Y", "%d/%b/%y",       # 01/Jan/2024
            "%d %b, %Y", "%d %B, %Y",    # 01 Jan, 2024
            "%b %d, %Y", "%B %d, %Y",    # Jan 01, 2024
            "%Y/%m/%d",                    # 2024/01/15
        ]
        date_str = date_str.strip()
        # Remove time component if present (e.g., "01/01/2024 10:30")
        date_str = re.split(r'\s+\d{1,2}:\d{2}', date_str)[0].strip()
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        return None
