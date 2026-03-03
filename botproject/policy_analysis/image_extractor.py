"""
Image Text Extraction
Extract text from insurance policy images using OpenAI GPT-4o Vision API.
"""
import base64
import logging
import os

logger = logging.getLogger(__name__)

# Supported image formats
SUPPORTED_IMAGE_FORMATS = {'.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp'}


def is_image_file(filename: str) -> bool:
    """Check if file is a supported image format"""
    if not filename:
        return False
    ext = os.path.splitext(filename.lower())[1]
    return ext in SUPPORTED_IMAGE_FORMATS


def extract_text_from_images_deepseek(image_contents: list, image_filenames: list) -> str:
    """
    Extract text from multiple insurance policy images using DeepSeek Vision API.

    Args:
        image_contents: List of image bytes
        image_filenames: List of corresponding filenames

    Returns:
        Extracted text from all images combined
    """
    try:
        from openai import OpenAI

        openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        if not image_contents:
            return ""

        # Build content array with all images
        content_parts = [
            {
                "type": "text",
                "text": """You are an expert OCR system specialized in extracting text from Indian insurance policy documents.

TASK: Extract ALL text from the provided insurance policy image(s) accurately.

INSTRUCTIONS:
1. Extract every piece of text visible in the image(s)
2. Preserve the document structure (headings, sections, tables)
3. Include all policy details: policy number, holder name, coverage, premium, dates, etc.
4. Extract table data in a readable format
5. Include fine print and footnotes
6. Maintain number accuracy (policy numbers, amounts, dates)
7. If multiple pages/images provided, process all and combine the text

OUTPUT FORMAT:
- Return the extracted text in a clean, readable format
- Preserve paragraph breaks and section separations
- Format tables as aligned text
- Do NOT add any commentary or interpretation - only extract the actual text

Begin extraction:"""
            }
        ]

        # Add all images to the request
        for i, (img_content, filename) in enumerate(zip(image_contents, image_filenames)):
            # Determine image type
            ext = os.path.splitext(filename.lower())[1]
            mime_type_map = {
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.png': 'image/png',
                '.webp': 'image/webp',
                '.gif': 'image/gif',
                '.bmp': 'image/bmp'
            }
            mime_type = mime_type_map.get(ext, 'image/jpeg')

            # Encode image to base64
            base64_image = base64.b64encode(img_content).decode('utf-8')

            content_parts.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:{mime_type};base64,{base64_image}"
                }
            })

        # Call OpenAI GPT-4o Vision API (DeepSeek does not support image_url content type)
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": content_parts
                }
            ],
            max_tokens=8000,
            temperature=0.0
        )

        extracted_text = response.choices[0].message.content.strip()
        logger.info(f"Successfully extracted text from {len(image_contents)} image(s) using DeepSeek Vision")

        return extracted_text

    except Exception as e:
        logger.error(f"Error extracting text from images with DeepSeek: {e}")
        raise Exception(f"Failed to extract text from images: {str(e)}")
