"""
Dispute Letter Generator
Generates professional dispute letters for hospital billing discrepancies.
"""

import logging
from io import BytesIO
from typing import Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.colors import HexColor
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    logger.warning("ReportLab not available for dispute letter PDF generation")


# Discrepancy type to dispute paragraph templates
DISCREPANCY_TEMPLATES = {
    "DUPLICATE_CHARGE": (
        "We have identified a duplicate charge for '{item_name}' amounting to Rs.{amount}. "
        "This item appears to have been charged more than once. We request immediate removal "
        "of the duplicate entry."
    ),
    "CROSS_SECTION_DUPLICATE": (
        "The item '{item_name}' (Rs.{amount}) appears in multiple sections of the bill. "
        "This cross-section duplication results in the patient being charged twice for the same "
        "service/consumable. We request removal of the duplicate entry."
    ),
    "CALCULATION_ERROR": (
        "We have identified a mathematical error in the billing for '{item_name}'. "
        "The calculated amount should be Rs.{benchmark} but Rs.{amount} has been charged. "
        "We request correction of this calculation error."
    ),
    "PRICE_ABOVE_MRP": (
        "The item '{item_name}' has been billed at Rs.{amount} which exceeds the Maximum Retail "
        "Price (MRP). Charging above MRP is a violation of the Drugs (Prices Control) Order, 2013 "
        "under the Essential Commodities Act. We request the rate be corrected to MRP or below."
    ),
    "PACKAGE_VIOLATION": (
        "The bill includes a package rate for the procedure, yet '{item_name}' (Rs.{amount}) "
        "has been billed separately. Items included in the package should not be charged again. "
        "We request removal of the separately billed amount or clarification of package inclusions."
    ),
    "UNBUNDLED_PROCEDURE": (
        "The procedure '{item_name}' appears to have been unbundled, with component charges "
        "listed separately. Standard medical billing practices include these components within "
        "the package/bundled rate. We request a consolidated package rate be applied."
    ),
    "UNNECESSARY_TEST": (
        "The investigation '{item_name}' does not appear to be clinically indicated for the "
        "diagnosed condition as per standard medical protocols. We request clinical justification "
        "for this test and its relevance to the treatment provided."
    ),
    "REPEAT_TEST": (
        "The investigation '{item_name}' has been performed multiple times within a short period. "
        "Standard medical protocols typically do not require such frequent repetition for the "
        "diagnosed condition. We request clinical justification for each repeat test."
    ),
    "EXCESSIVE_CONSULTANT": (
        "The number of consultant visits appears to exceed the typical requirement for the "
        "length of stay. We request a detailed visit log showing the clinical necessity of each visit."
    ),
    "COMPLIMENTARY_CHARGED": (
        "The bill includes a charge for '{item_name}' (Rs.{amount}) which is typically provided "
        "as a complimentary service/amenity included in the room rent or nursing charges. "
        "We request this charge be removed as per standard hospital practice."
    ),
    "DATE_OUTSIDE_STAY": (
        "The item '{item_name}' (Rs.{amount}) is dated outside the patient's admission period. "
        "Services rendered before admission or after discharge should not be included in the "
        "inpatient bill. We request this charge be reviewed and removed."
    ),
    "PHANTOM_CHARGE": (
        "The bill includes a charge for '{item_name}' (Rs.{amount}) which is inconsistent with "
        "the patient's treatment record. For example, ICU charges during a general ward stay or "
        "ventilator charges without intubation records. We request clinical documentation "
        "justifying this charge."
    ),
    "NABH_VIOLATION": (
        "The billing for '{item_name}' does not comply with NABH (National Accreditation Board "
        "for Hospitals) billing standards. NABH-accredited hospitals are expected to maintain "
        "transparent and standardized billing practices. We request correction."
    ),
    "EXCESSIVE_QUANTITY": (
        "The quantity billed for '{item_name}' appears excessive relative to the length of stay "
        "and treatment provided. We request itemized justification for the quantity charged."
    ),
}


def generate_dispute_letter_text(audit_data: Dict[str, Any]) -> str:
    """
    Generate a professional dispute letter as plain text.

    Args:
        audit_data: Complete audit result dict

    Returns:
        Formatted dispute letter text
    """
    bill_data = audit_data.get("bill_data", {})
    discrepancies = audit_data.get("discrepancies", [])
    savings = audit_data.get("savings", {})

    if not discrepancies:
        return "No discrepancies were identified in this bill. No dispute letter is required."

    metadata = bill_data.get("metadata", {})
    today = datetime.utcnow().strftime("%d %B %Y")

    return _generate_hospital_letter(metadata, bill_data, discrepancies, savings, today)


def _generate_hospital_letter(metadata, bill_data, discrepancies, savings, today):
    """Generate hospital billing dispute letter."""
    patient = bill_data.get("patient_details", {})
    summary = bill_data.get("bill_summary", {})
    hospital_name = metadata.get("hospital_name", "[Hospital Name]")
    patient_name = patient.get("patient_name", "[Patient Name]")
    bill_number = metadata.get("bill_number", "[Bill Number]")
    admission_date = patient.get("admission_date", "[Admission Date]")
    discharge_date = patient.get("discharge_date", "[Discharge Date]")
    hospital_address = metadata.get("hospital_address", metadata.get("hospital_city", "[City]"))

    letter = f"""Date: {today}

To,
The Billing Manager / Medical Superintendent
{hospital_name}
{hospital_address}

Subject: Request for Bill Review and Correction
Patient: {patient_name}
Bill No: {bill_number}
Admission: {admission_date} to {discharge_date}

Dear Sir/Madam,

I am writing regarding the above-referenced hospital bill issued upon discharge. After careful review of the itemized bill, I have identified the following discrepancies that require your attention and correction.

"""

    # Group discrepancies by severity for organized presentation
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "informational": 4}
    sorted_discrepancies = sorted(
        discrepancies,
        key=lambda d: severity_order.get(d.get("severity", "medium").lower(), 2),
    )

    # Add discrepancy paragraphs
    for i, d in enumerate(sorted_discrepancies, 1):
        d_type = d.get("type", "")
        template = DISCREPANCY_TEMPLATES.get(d_type, "")

        if template:
            amount = d.get("billed_amount", d.get("overcharged_amount", 0))
            benchmark = d.get("benchmark_amount", 0)
            variance = 0
            if benchmark and amount:
                variance = round((amount - benchmark) / benchmark * 100, 1) if benchmark > 0 else 0

            paragraph = template.format(
                item_name=d.get("item_name", "Item"),
                amount=f"{amount:,.0f}" if amount else "0",
                benchmark=f"{benchmark:,.0f}" if benchmark else "N/A",
                variance=f"{variance}" if variance else "N/A",
            )
        else:
            paragraph = f"Discrepancy identified: {d.get('description', 'See details')}. {d.get('action', '')}"

        severity_label = d.get("severity", "medium").upper()
        letter += f"{i}. [{severity_label}] {d.get('type', '').replace('_', ' ').title()}\n"
        letter += f"   {paragraph}\n\n"

    # Summary
    total_disputed = savings.get("optimistic_estimate", 0)
    moderate = savings.get("moderate_estimate", 0)
    conservative = savings.get("conservative_estimate", 0)

    letter += f"""SUMMARY
{'='*50}
Total items disputed: {len(discrepancies)}
Total amount in question: Rs. {total_disputed:,.2f}
Moderate recovery estimate: Rs. {moderate:,.2f}
Conservative recovery estimate: Rs. {conservative:,.2f}

I request that you review the above items and provide a revised bill within 7 working days. Should you require any clarification, I am available for discussion.

Please note that if the above concerns are not addressed satisfactorily, I reserve the right to escalate the matter to:
1. Hospital Grievance Committee
2. Insurance Regulatory and Development Authority of India (IRDAI)
3. Consumer Disputes Redressal Forum
4. National Consumer Helpline (1800-11-4000)

I trust you will treat this matter with the urgency it deserves.

Thanking you,

{patient_name}
Date: {today}

Enclosures:
1. Copy of original itemized bill
2. Policy coverage details (if insured)

---
DISCLAIMER: This letter was generated by EAZR Bill Audit Intelligence for informational purposes.
The analysis is based on standard hospital billing practices and consumer protection laws.
Users should verify findings independently before submission.
"""

    return letter


def generate_dispute_letter_pdf(audit_data: Dict[str, Any]) -> BytesIO:
    """
    Generate dispute letter as PDF.

    Args:
        audit_data: Complete audit result dict

    Returns:
        BytesIO buffer containing the PDF
    """
    if not REPORTLAB_AVAILABLE:
        raise Exception("ReportLab is required for PDF generation")

    letter_text = generate_dispute_letter_text(audit_data)
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=60,
        leftMargin=60,
        topMargin=50,
        bottomMargin=50,
    )

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name='LetterBody',
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        alignment=TA_JUSTIFY,
        spaceAfter=8,
    ))
    styles.add(ParagraphStyle(
        name='LetterHeading',
        fontName='Helvetica-Bold',
        fontSize=11,
        spaceAfter=4,
        spaceBefore=12,
    ))

    elements = []

    # Convert plain text to paragraphs
    for line in letter_text.split("\n"):
        line = line.strip()
        if not line:
            elements.append(Spacer(1, 6))
        elif line.startswith("Subject:") or line.startswith("SUMMARY") or line.startswith("Enclosures:"):
            elements.append(Paragraph(f"<b>{line}</b>", styles['LetterHeading']))
        elif line.startswith("==="):
            continue
        elif line.startswith("DISCLAIMER:") or line.startswith("---"):
            elements.append(Paragraph(f"<i>{line}</i>", styles['LetterBody']))
        else:
            # Escape HTML characters
            safe_line = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            elements.append(Paragraph(safe_line, styles['LetterBody']))

    doc.build(elements)
    buffer.seek(0)

    logger.info(f"Dispute letter PDF generated, {buffer.getbuffer().nbytes} bytes")
    return buffer
