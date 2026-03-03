# AGENTS.md - AI Agent Guidelines for EAZR Chat

This document provides guidance for AI agents working on the EAZR Chat codebase.

## Project Overview

EAZR Chat is a financial assistant application that helps users manage insurance policies, get financial advice through AI chat, and track their financial protection.

## Technology Stack

| Component | Technology |
|-----------|------------|
| Backend Framework | FastAPI 0.115.14 |
| Language | Python 3.12 |
| Database | MongoDB (Atlas in production) |
| Cache/Sessions | Redis |
| AI/LLM | OpenAI GPT, LangChain, LangGraph |
| Frontend | Flutter/Dart |
| Real-time | WebSocket |

## Directory Structure

```
eazr_chat/
├── botproject/              # Backend application
│   ├── app.py               # Main FastAPI entry point
│   ├── routers/             # API endpoint handlers
│   ├── services/            # Business logic
│   ├── models/              # Pydantic data models
│   ├── core/                # Config, middleware, utilities
│   ├── database_storage/    # MongoDB, Redis, S3
│   ├── ai_chat_components/  # LLM, chat processing
│   ├── session_security/    # Auth, tokens, sessions
│   └── websocket/           # Real-time communication
├── frontend/                # Flutter mobile app
├── scripts/
│   └── ralph/               # Autonomous AI loop
└── .env                     # Environment variables
```

## Code Patterns

### Adding a New Router

```python
# routers/my_feature.py
from fastapi import APIRouter, HTTPException, Request
from core.rate_limiter import limiter, RATE_LIMITS

router = APIRouter(
    prefix="/my-feature",
    tags=["My Feature"]
)

@router.get("/")
@limiter.limit(RATE_LIMITS.get("default", "100/minute"))
async def get_feature(request: Request):
    return {"success": True}
```

Register in `app.py`:
```python
try:
    from routers.my_feature import router as my_feature_router
    app.include_router(my_feature_router)
    logger.info("✓ My Feature router loaded")
except ImportError as e:
    logger.warning(f"⚠ My Feature router not available: {e}")
```

### Adding a New Service

```python
# services/my_service.py
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class MyService:
    def __init__(self):
        self.logger = logger

    def do_something(self, data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            # Implementation
            return {"success": True}
        except Exception as e:
            self.logger.error(f"Error: {e}")
            raise

# Singleton instance
my_service = MyService()
```

### Adding a New Model

```python
# models/my_model.py
from pydantic import BaseModel, Field
from typing import Optional

class MyRequest(BaseModel):
    """Request for my feature"""
    field_one: str = Field(..., description="Required field")
    field_two: Optional[int] = Field(None, description="Optional field")

class MyResponse(BaseModel):
    """Response from my feature"""
    success: bool
    data: Optional[dict] = None
    error: Optional[str] = None
```

### Error Handling

```python
from fastapi import HTTPException

# Standard error format
raise HTTPException(
    status_code=400,
    detail={
        "error_code": "VALIDATION_ERROR",
        "message": "Invalid input provided",
        "details": {"field": "reason"}
    }
)
```

### Authentication

```python
from core.dependencies import verify_token, verify_access_token

# Use verify_token for backwards compatibility
@router.get("/protected")
async def protected_endpoint(
    user_payload: dict = Depends(verify_token)
):
    user_id = user_payload.get("user_id")
    return {"user_id": user_id}

# Use verify_access_token for new token service
@router.get("/new-protected")
async def new_protected_endpoint(
    user_payload: dict = Depends(verify_access_token)
):
    user_id = user_payload.get("user_id")
    return {"user_id": user_id}
```

## Common Gotchas

### 1. Large Files
Some router files are very large (100K+ lines). Be careful when reading/editing:
- `routers/admin.py` - 184K lines
- `routers/policy_upload.py` - 244K lines
- Use grep/search to find specific functions

### 2. Bare Except Clauses
Legacy code has `except:` without specifying exception type. Always use:
```python
except Exception as e:
    logger.error(f"Error: {e}")
```

### 3. Circular Imports
Services can import each other. To avoid circular imports:
```python
# Import inside function if needed
def my_function():
    from services.other_service import other_service
    return other_service.do_something()
```

### 4. Environment Variables
Many have insecure defaults. Check `core/config.py` and `.env`:
- `JWT_SECRET` - Must be 32+ characters
- `ADMIN_PASSWORD` - Change from default
- MongoDB/Redis credentials - Use proper secrets

### 5. Rate Limiting
All public endpoints should have rate limiting:
```python
@router.post("/endpoint")
@limiter.limit(RATE_LIMITS.get("default", "100/minute"))
async def my_endpoint(request: Request):
    pass
```

## Testing

```bash
# Check Python syntax
cd botproject
python3 -m py_compile app.py

# Verify imports work
python3 -c "from app import app; print('OK')"

# Run development server
uvicorn app:app --reload --port 8000

# View API docs
open http://localhost:8000/docs
```

## Deployment

The application runs with:
```bash
uvicorn app:app --host 0.0.0.0 --port 8000
```

Environment determines database:
- `ENVIRONMENT=local` → Local MongoDB
- `ENVIRONMENT=production` → MongoDB Atlas

## Security Considerations

1. **Token Management**: Use `services/token_service.py` for JWT handling
2. **Input Validation**: Use `session_security/security_utils.py`
3. **Rate Limiting**: Always apply to public endpoints
4. **CORS**: Configured in `core/middleware.py`
5. **Secrets**: Never commit `.env` file

## Contact

For questions about the codebase, check:
- `scripts/ralph/progress.txt` for learnings
- `scripts/ralph/prd.json` for current tasks
- API docs at `/docs` endpoint
