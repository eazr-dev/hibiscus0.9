"""
Frontend Router
Serves HTML pages and static frontend files
"""
import logging
from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from core.config import settings
from core.dependencies import (
    REDIS_AVAILABLE,
    MULTILINGUAL_AVAILABLE,
    VOICE_AVAILABLE
)

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(tags=["Frontend"])

# Frontend directory
FRONTEND_DIR = settings.FRONTEND_DIR


@router.get("/")
async def serve_home():
    """
    Serve home page (login page or API info)
    """
    login_path = FRONTEND_DIR / "login.html"
    if login_path.exists():
        return FileResponse(str(login_path))
    else:
        # Return API information page if login.html doesn't exist
        from ai_chat_components.enhanced_chatbot_handlers import FINANCIAL_ASSISTANCE_TYPES, INSURANCE_TYPES

        return HTMLResponse(f"""
        <html>
            <head>
                <title>Enhanced Financial Assistant API v4.0</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
                    .container {{ background: white; padding: 30px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); max-width: 1200px; margin: 0 auto; }}
                    h1 {{ color: #2c3e50; }}
                    h2 {{ color: #34495e; margin-top: 30px; }}
                    .feature {{ background: #ecf0f1; padding: 15px; margin: 10px 0; border-radius: 5px; }}
                    .available {{ color: #27ae60; }}
                    .unavailable {{ color: #e74c3c; }}
                    a {{ color: #3498db; text-decoration: none; }}
                    a:hover {{ text-decoration: underline; }}
                    ul {{ line-height: 1.8; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>✨ Enhanced Financial Assistant API v4.0</h1>
                    <p>Advanced financial services with chat memory, multiple chatbot options and quick actions</p>

                    <h2>📚 API Documentation</h2>
                    <ul>
                        <li><a href="/docs">📖 Interactive API Docs (Swagger)</a></li>
                        <li><a href="/redoc">📘 Alternative Documentation (ReDoc)</a></li>
                        <li><a href="/enhanced-health">🏥 Health Check</a></li>
                    </ul>

                    <h2>🆕 Chat Memory Features</h2>
                    <div class="feature">
                        <h3>💬 Conversation Memory</h3>
                        <p>Remembers conversation history and provides contextual responses</p>
                    </div>

                    <div class="feature">
                        <h3>👤 User Personalization</h3>
                        <p>Learns user preferences and provides personalized experiences</p>
                    </div>

                    <div class="feature">
                        <h3>🔍 Chat Analytics & Search</h3>
                        <p>Search conversation history and get detailed analytics</p>
                    </div>

                    <div class="feature">
                        <h3>📊 Data Export</h3>
                        <p>Export conversation data in JSON or CSV format</p>
                    </div>

                    <h2>🚀 Enhanced Features</h2>
                    <div class="feature">
                        <h3>💰 Multiple Loan Types</h3>
                        <p>Personal, Home, Vehicle, Education, Business, Gold loans with specific question flows</p>
                    </div>

                    <div class="feature">
                        <h3>🛡️ Multiple Insurance Types</h3>
                        <p>Health, Life, Motor, Travel, Home, Credit protection insurance</p>
                    </div>

                    <div class="feature">
                        <h3>⚡ Quick Account Services</h3>
                        <p>Instant balance check, transactions, bills, loan status - no chat required</p>
                    </div>

                    <h2>📊 System Status</h2>
                    <ul>
                        <li class="available">✅ Enhanced Chatbot: Functional</li>
                        <li class="available">✅ Chat Memory System: Active</li>
                        <li class="{'available' if REDIS_AVAILABLE else 'unavailable'}">{'✅' if REDIS_AVAILABLE else '⚠️'} Redis Caching: {'Available' if REDIS_AVAILABLE else 'Not Available (using in-memory)'}</li>
                        <li class="{'available' if MULTILINGUAL_AVAILABLE else 'unavailable'}">{'✅' if MULTILINGUAL_AVAILABLE else '⚠️'} Multilingual Support: {'Available' if MULTILINGUAL_AVAILABLE else 'Not Available'}</li>
                        <li class="{'available' if VOICE_AVAILABLE else 'unavailable'}">{'✅' if VOICE_AVAILABLE else '⚠️'} Voice Recognition: {'Available' if VOICE_AVAILABLE else 'Not Available'}</li>
                    </ul>

                    <h2>🔧 Available Services</h2>
                    <ul>
                        <li><strong>Loans:</strong> {', '.join(FINANCIAL_ASSISTANCE_TYPES.values())}</li>
                        <li><strong>Insurance:</strong> {', '.join(INSURANCE_TYPES.values())}</li>
                        <li><strong>Account Services:</strong> Balance, Transactions, Bills, Loan Status</li>
                        <li><strong>Memory Features:</strong> Chat History, Search, Analytics, Export</li>
                    </ul>

                    <h2>🔗 Quick Links</h2>
                    <ul>
                        <li><a href="/login">Login Page</a></li>
                        <li><a href="/chatbot">Chatbot Interface</a></li>
                        <li><a href="/admin">Admin Dashboard</a></li>
                    </ul>
                </div>
            </body>
        </html>
        """)


@router.get("/login")
async def serve_login():
    """
    Serve login page
    """
    login_path = FRONTEND_DIR / "login.html"
    if login_path.exists():
        return FileResponse(str(login_path))
    else:
        return HTMLResponse("""
            <html>
                <head><title>Login</title></head>
                <body>
                    <h1>Login Page</h1>
                    <p>Please add login.html to the frontend directory</p>
                    <p><a href="/">Back to Home</a></p>
                </body>
            </html>
        """)


@router.get("/chatbot")
async def serve_chatbot():
    """
    Serve chatbot page
    """
    chatbot_path = FRONTEND_DIR / "chatbot.html"
    if chatbot_path.exists():
        return FileResponse(str(chatbot_path))
    else:
        return HTMLResponse("""
            <html>
                <head><title>Chatbot</title></head>
                <body>
                    <h1>Enhanced Chatbot Page</h1>
                    <p>Please add chatbot.html to the frontend directory</p>
                    <p><a href="/">Back to Home</a></p>
                </body>
            </html>
        """)


@router.get("/chatbot.html")
async def serve_chatbot_html():
    """
    Serve chatbot.html (alternative route)
    """
    chatbot_path = FRONTEND_DIR / "chatbot.html"
    if chatbot_path.exists():
        return FileResponse(str(chatbot_path))
    else:
        raise HTTPException(status_code=404, detail="Chatbot page not found")


@router.get("/admin")
async def serve_admin():
    """
    Serve admin dashboard page
    """
    admin_path = FRONTEND_DIR / "admin.html"
    if admin_path.exists():
        return FileResponse(str(admin_path))
    else:
        return HTMLResponse("""
            <html>
                <head><title>Admin Dashboard</title></head>
                <body>
                    <h1>Admin Dashboard</h1>
                    <p>Please add admin.html to the frontend directory</p>
                    <p><a href="/">Back to Home</a></p>
                </body>
            </html>
        """)


@router.get("/qr-scan.html")
async def serve_qr_scan():
    """
    Serve QR scan page for mobile
    """
    qr_scan_path = FRONTEND_DIR / "qr-scan.html"
    if qr_scan_path.exists():
        return FileResponse(str(qr_scan_path))
    else:
        return HTMLResponse("""
            <html>
                <head><title>QR Scan</title></head>
                <body>
                    <h1>QR Scan</h1>
                    <p>QR scan page not found</p>
                    <p><a href="/">Back to Home</a></p>
                </body>
            </html>
        """)


@router.get("/favicon.ico")
async def serve_favicon():
    """
    Serve favicon
    """
    # Try multiple favicon locations
    for favicon_name in ["favicon.svg", "favicon.ico", "favicon.png"]:
        favicon_path = FRONTEND_DIR / favicon_name
        if favicon_path.exists():
            media_types = {
                ".svg": "image/svg+xml",
                ".ico": "image/x-icon",
                ".png": "image/png"
            }
            ext = favicon_path.suffix
            return FileResponse(str(favicon_path), media_type=media_types.get(ext, "image/x-icon"))

    # Return 204 No Content if favicon not found (prevents error logs)
    from fastapi import Response
    return Response(status_code=204)


@router.get("/{filename:path}.css")
async def serve_css(filename: str):
    """
    Serve CSS files from frontend directory
    """
    css_path = FRONTEND_DIR / f"{filename}.css"
    if css_path.exists() and css_path.parent == FRONTEND_DIR:
        return FileResponse(str(css_path), media_type="text/css")
    raise HTTPException(status_code=404, detail="CSS file not found")


@router.get("/{filename:path}.js")
async def serve_js(filename: str):
    """
    Serve JavaScript files from frontend directory
    """
    js_path = FRONTEND_DIR / f"{filename}.js"
    if js_path.exists() and js_path.parent == FRONTEND_DIR:
        return FileResponse(str(js_path), media_type="application/javascript")
    raise HTTPException(status_code=404, detail="JS file not found")


@router.get("/policy-viewer")
async def serve_policy_viewer():
    """
    Serve policy analysis viewer page
    """
    viewer_path = FRONTEND_DIR / "policy-viewer.html"
    if viewer_path.exists():
        return FileResponse(str(viewer_path))
    else:
        return HTMLResponse("""
            <html>
                <head><title>Policy Viewer</title></head>
                <body>
                    <h1>Policy Analysis Viewer</h1>
                    <p>Please add policy-viewer.html to the frontend directory</p>
                    <p><a href="/">Back to Home</a></p>
                </body>
            </html>
        """)


@router.get("/aieazr")
async def serve_aieazr_homepage():
    """
    Serve the main Eazr AI homepage with advanced animations
    """
    index_path = FRONTEND_DIR / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    else:
        return HTMLResponse("""
            <html>
                <head><title>Eazr AI</title></head>
                <body>
                    <h1>Eazr AI Homepage</h1>
                    <p>Please add index.html to the frontend directory</p>
                    <p><a href="/">Back to Home</a></p>
                </body>
            </html>
        """)


@router.get("/tpl_reg")
async def serve_tpl_registration():
    """
    Serve TPL (Tapovan Premier League) registration page
    """
    tpl_path = settings.BASE_DIR / "tpl_website" / "index.html"
    if tpl_path.exists():
        return FileResponse(str(tpl_path))
    else:
        return HTMLResponse("""
            <html>
                <head><title>TPL Registration</title></head>
                <body>
                    <h1>TPL Registration Page</h1>
                    <p>TPL registration page not found</p>
                    <p><a href="/">Back to Home</a></p>
                </body>
            </html>
        """, status_code=404)


@router.get("/tpl_reg/{filename:path}")
async def serve_tpl_assets(filename: str):
    """
    Serve TPL website static assets (images, etc.)
    """
    tpl_dir = settings.BASE_DIR / "tpl_website"
    file_path = tpl_dir / filename

    # Security check: ensure file is within tpl_website directory
    try:
        file_path = file_path.resolve()
        tpl_dir = tpl_dir.resolve()
        if not str(file_path).startswith(str(tpl_dir)):
            raise HTTPException(status_code=403, detail="Access denied")
    except Exception:
        raise HTTPException(status_code=403, detail="Access denied")

    if file_path.exists() and file_path.is_file():
        # Determine media type based on extension
        media_types = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".svg": "image/svg+xml",
            ".css": "text/css",
            ".js": "application/javascript",
            ".html": "text/html",
            ".md": "text/markdown"
        }
        media_type = media_types.get(file_path.suffix.lower(), "application/octet-stream")
        return FileResponse(str(file_path), media_type=media_type)

    raise HTTPException(status_code=404, detail="File not found")


@router.get("/.well-known/{path:path}")
async def serve_well_known(path: str):
    """
    Handle .well-known requests (Chrome DevTools, etc.)
    Returns 404 for these requests
    """
    from fastapi import Response
    return Response(status_code=404)
