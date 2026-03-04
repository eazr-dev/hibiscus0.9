"""
🌺 Hibiscus v0.9 | EAZR AI Insurance Intelligence Engine
Request ID middleware — generates unique trace IDs for every API call.
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
"""
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
