"""
Hibiscus API Router
===================
Aggregates all sub-routers into the main APIRouter.
All routes mounted under /hibiscus/ prefix in main.py.
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
"""
from fastapi import APIRouter

from hibiscus.api.chat import router as chat_router
from hibiscus.api.health import router as health_router
from hibiscus.api.analyze import router as analyze_router
from hibiscus.api.portfolio import router as portfolio_router
from hibiscus.api.websocket import router as ws_router

router = APIRouter()

# Mount sub-routers
router.include_router(chat_router, tags=["Chat"])
router.include_router(health_router, tags=["Health"])
router.include_router(analyze_router, tags=["Analysis"])
router.include_router(portfolio_router, tags=["Portfolio"])
router.include_router(ws_router, tags=["WebSocket"])
