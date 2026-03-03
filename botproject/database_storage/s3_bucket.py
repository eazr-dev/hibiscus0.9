def upload_pdf_to_s3(pdf_buffer, filename, bucket_name):
    """
    Upload PDF buffer to S3 bucket

    Args:
        pdf_buffer: PDF BytesIO buffer
        filename: Name for the file (e.g., 'test_report.pdf')
        bucket_name: S3 bucket name

    Returns:
        dict: Upload result
    """
    import boto3
    import os
    from datetime import datetime
    from dotenv import load_dotenv

    load_dotenv()

    try:
        # Initialize S3 client with environment variables
        s3_client = boto3.client(
            's3',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_REGION', 'ap-south-1')
        )
        
        # Upload to S3
        pdf_buffer.seek(0)  # Reset buffer position
        s3_client.put_object(
            Bucket=bucket_name,
            Key=f"reports/{filename}",
            Body=pdf_buffer.getvalue(),
            ContentType='application/pdf',
        )

        
        region = "ap-south-1"
        s3_url = f"https://{bucket_name}.s3.{region}.amazonaws.com/reports/{filename}"
        
        return {
            "success": True,
            "s3_url": s3_url,
            "message": f"PDF uploaded successfully to S3: reports/{filename}"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
    

def upload_image_to_s3(image_buffer, filename, bucket_name="raceabove-dev", content_type=None):
    """
    Upload image buffer to S3 bucket in eaza_images folder

    Args:
        image_buffer: Image BytesIO buffer or base64 string
        filename: Name for the file (e.g., 'profile_pic_282.jpg')
        bucket_name: S3 bucket name (default: 'raceabove-dev')
        content_type: Optional content type (e.g., 'image/png'). Auto-detected from filename if not provided.

    Returns:
        dict: Upload result with S3 URL
    """
    import boto3
    import base64
    import os
    from io import BytesIO
    from datetime import datetime
    from dotenv import load_dotenv

    load_dotenv()

    # Content type mapping based on file extension
    CONTENT_TYPE_MAP = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.webp': 'image/webp',
        '.svg': 'image/svg+xml',
        '.bmp': 'image/bmp',
    }

    try:
        # Initialize S3 client with environment variables
        s3_client = boto3.client(
            's3',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_REGION', 'ap-south-1')
        )

        # Handle base64 string input
        if isinstance(image_buffer, str):
            # Remove data URL prefix if present
            if image_buffer.startswith('data:'):
                header, data = image_buffer.split(',', 1)
                # Extract content type from header
                content_type = header.split(':')[1].split(';')[0]
            else:
                data = image_buffer
                content_type = content_type or 'image/jpeg'  # Default

            # Decode base64 to bytes
            image_bytes = base64.b64decode(data)
            image_buffer = BytesIO(image_bytes)
        else:
            # Auto-detect content type from filename if not provided
            if not content_type and filename:
                file_ext = '.' + filename.split('.')[-1].lower() if '.' in filename else ''
                content_type = CONTENT_TYPE_MAP.get(file_ext, 'image/jpeg')
            else:
                content_type = content_type or 'image/jpeg'
        
        # Generate unique filename with timestamp if needed
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"image_{timestamp}.jpg"
        
        # Ensure proper file extension
        if '.' not in filename:
            filename += '.jpg'
        
        # Upload to S3 in eaza_images folder
        image_buffer.seek(0)  # Reset buffer position
        s3_client.put_object(
            Bucket=bucket_name,
            Key=f"eaza_images/{filename}",  # Changed folder from 'reports' to 'eaza_images'
            Body=image_buffer.getvalue() if hasattr(image_buffer, 'getvalue') else image_buffer.read(),
            ContentType=content_type,
        )
        
        # Generate S3 URL
        region = "ap-south-1"
        s3_url = f"https://{bucket_name}.s3.{region}.amazonaws.com/eaza_images/{filename}"
        
        return {
            "success": True,
            "s3_url": s3_url,
            "message": f"Image uploaded successfully to S3: eaza_images/{filename}",
            "filename": filename
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to upload image to S3: {str(e)}"
        }


# Helper function to upload profile picture from file
