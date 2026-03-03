"""
Legal Content Router
API endpoints for Privacy Policy and Terms & Conditions

Logic:
- If content is present (non-empty) → Display content directly in the app
- If url is present (non-empty) → Open/load the URL in a WebView
- Only one will be populated at a time (mutual exclusivity)
"""
import logging
from fastapi import APIRouter

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api", tags=["Legal"])

# ==================== CONFIGURATION ====================
# Configure these values based on your requirements
# Set either content OR url for each, not both

PRIVACY_POLICY_CONFIG = {
    # Option 1: HTML content (for displaying directly in app)
    "content": "",

    # Option 2: URL (for opening in WebView)
    "url": "https://www.eazr.life/privacy-policy"
}

TERMS_CONDITIONS_CONFIG = {
    # Option 1: HTML content (for displaying directly in app)
    "content": """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Terms and Conditions - Eazr</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif; line-height: 1.6; color: #333; padding: 20px; background: #fff; }
        .container { max-width: 800px; margin: 0 auto; }
        h1 { color: #1a1a2e; font-size: 24px; margin-bottom: 10px; }
        h2 { color: #1a1a2e; font-size: 18px; margin: 25px 0 10px 0; }
        h3 { color: #333; font-size: 16px; margin: 15px 0 8px 0; }
        p { margin-bottom: 12px; font-size: 14px; }
        ul, ol { margin: 10px 0 15px 20px; font-size: 14px; }
        li { margin-bottom: 8px; }
        .effective-date { color: #666; font-size: 13px; margin-bottom: 20px; }
        .highlight { background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 15px 0; border-left: 4px solid #4361ee; }
        .warning { background: #fff3cd; padding: 15px; border-radius: 8px; margin: 15px 0; border-left: 4px solid #ffc107; }
        a { color: #4361ee; text-decoration: none; }
        hr { border: none; border-top: 1px solid #eee; margin: 25px 0; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Terms and Conditions</h1>
        <p class="effective-date">Effective Date: December 12, 2025</p>

        <p>Welcome to Eazr! These Terms and Conditions ("Terms") govern your use of the Eazr mobile application and services. By accessing or using our services, you agree to be bound by these Terms.</p>

        <h2>1. Acceptance of Terms</h2>
        <p>By downloading, installing, or using the Eazr app, you acknowledge that you have read, understood, and agree to be bound by these Terms. If you do not agree to these Terms, please do not use our services.</p>

        <h2>2. Description of Services</h2>
        <p>Eazr provides an AI-powered insurance management platform that helps you:</p>
        <ul>
            <li>Store and organize your insurance policies in one place</li>
            <li>Analyze your insurance coverage and identify gaps</li>
            <li>Receive personalized insurance recommendations</li>
            <li>Track policy renewals and expiration dates</li>
            <li>Get assistance with insurance-related queries through our AI chatbot</li>
        </ul>

        <div class="highlight">
            <strong>Important:</strong> Eazr is an insurance management and advisory platform. We do not sell insurance policies directly. Any insurance purchases are made through licensed insurance providers.
        </div>

        <h2>3. User Accounts</h2>
        <h3>3.1 Registration</h3>
        <p>To use certain features of our services, you must create an account. You agree to provide accurate, current, and complete information during registration.</p>

        <h3>3.2 Account Security</h3>
        <p>You are responsible for maintaining the confidentiality of your account credentials and for all activities that occur under your account. Notify us immediately of any unauthorized use.</p>

        <h3>3.3 Account Termination</h3>
        <p>We reserve the right to suspend or terminate your account if you violate these Terms or engage in fraudulent or illegal activities.</p>

        <h2>4. User Responsibilities</h2>
        <p>When using Eazr, you agree to:</p>
        <ul>
            <li>Provide accurate and truthful information about yourself and your insurance policies</li>
            <li>Upload only genuine insurance documents that belong to you or your family members</li>
            <li>Not use the service for any illegal or unauthorized purpose</li>
            <li>Not attempt to access other users' accounts or data</li>
            <li>Not interfere with or disrupt the service or servers</li>
            <li>Comply with all applicable laws and regulations</li>
        </ul>

        <h2>5. Policy Document Upload</h2>
        <p>When you upload insurance documents to Eazr:</p>
        <ul>
            <li>You confirm that you have the right to upload such documents</li>
            <li>You grant us permission to process and analyze these documents using our AI technology</li>
            <li>We will extract and store relevant policy information to provide our services</li>
            <li>Your documents are encrypted and stored securely</li>
        </ul>

        <h2>6. AI-Powered Features</h2>
        <div class="warning">
            <strong>Disclaimer:</strong> Our AI-powered analysis and recommendations are provided for informational purposes only and should not be considered as professional insurance advice. Always consult with a licensed insurance advisor for important insurance decisions.
        </div>

        <h2>7. Intellectual Property</h2>
        <p>All content, features, and functionality of Eazr, including but not limited to text, graphics, logos, icons, and software, are the exclusive property of Eazr and are protected by copyright, trademark, and other intellectual property laws.</p>

        <h2>8. Privacy</h2>
        <p>Your privacy is important to us. Please review our <a href="#">Privacy Policy</a> to understand how we collect, use, and protect your personal information.</p>

        <h2>9. Limitation of Liability</h2>
        <p>To the maximum extent permitted by law:</p>
        <ul>
            <li>Eazr is provided "as is" without warranties of any kind</li>
            <li>We are not liable for any indirect, incidental, special, or consequential damages</li>
            <li>Our total liability shall not exceed the amount paid by you for our services in the past 12 months</li>
            <li>We are not responsible for decisions made based on information provided by our AI</li>
        </ul>

        <h2>10. Indemnification</h2>
        <p>You agree to indemnify and hold harmless Eazr and its officers, directors, employees, and agents from any claims, damages, losses, or expenses arising from your use of our services or violation of these Terms.</p>

        <h2>11. Modifications to Terms</h2>
        <p>We reserve the right to modify these Terms at any time. We will notify you of significant changes through the app or via email. Your continued use of Eazr after such modifications constitutes acceptance of the updated Terms.</p>

        <h2>12. Governing Law</h2>
        <p>These Terms shall be governed by and construed in accordance with the laws of India. Any disputes arising from these Terms shall be subject to the exclusive jurisdiction of the courts in Bangalore, Karnataka.</p>

        <h2>13. Contact Us</h2>
        <p>If you have any questions about these Terms, please contact us at:</p>
        <ul>
            <li>Email: support@eazr.in</li>
            <li>Address: Eazr Technologies Pvt. Ltd., Bangalore, India</li>
        </ul>

        <hr>
        <p style="font-size: 12px; color: #666; text-align: center;">© 2025 Eazr Technologies Pvt. Ltd. All rights reserved.</p>
    </div>
</body>
</html>
""",

    # Option 2: URL (for opening in WebView) - not used when content is provided
    "url": "https://www.eazr.in/terms-and-conditions"
}


# ==================== API ENDPOINTS ====================

@router.get("/privacy-policy")
async def get_privacy_policy():
    """
    Get Privacy Policy Content

    Returns either:
    - content: HTML string to display directly in app
    - url: Web URL to load in WebView

    Only one will be populated at a time.

    Frontend Logic:
    - If content is non-empty → Display content in WebView/Text widget
    - If url is non-empty → Load URL in WebView
    """
    return {
        "success": True,
        "data": {
            "content": PRIVACY_POLICY_CONFIG["content"],
            "url": PRIVACY_POLICY_CONFIG["url"] if not PRIVACY_POLICY_CONFIG["content"] else ""
        }
    }


@router.get("/terms-and-conditions")
async def get_terms_and_conditions():
    """
    Get Terms and Conditions Content

    Returns either:
    - content: HTML string to display directly in app
    - url: Web URL to load in WebView

    Only one will be populated at a time.

    Frontend Logic:
    - If content is non-empty → Display content in WebView/Text widget
    - If url is non-empty → Load URL in WebView
    """
    return {
        "success": True,
        "data": {
            "content": TERMS_CONDITIONS_CONFIG["content"],
            "url": TERMS_CONDITIONS_CONFIG["url"] if not TERMS_CONDITIONS_CONFIG["content"] else ""
        }
    }
