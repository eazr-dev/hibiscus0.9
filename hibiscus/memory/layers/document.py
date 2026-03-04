"""
🌺 Hibiscus v0.9 | EAZR AI Insurance Intelligence Engine
Document memory (L6) — MongoDB storage for extracted policy data and analysis results.
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
"""
import time
from typing import Any, Dict, List, Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from hibiscus.config import settings
from hibiscus.observability.logger import get_logger

logger = get_logger(__name__)

# TODO: [SECURITY] Document memory stores extracted policy data which may contain
# PII. Ensure MongoDB has encryption at rest enabled (e.g., WiredTiger encryption
# or cloud-managed encryption). Consider field-level encryption for sensitive
# extraction fields (policyholder name, PAN, DOB, etc.).

# ── MongoDB connection singleton ──────────────────────────────────────────
_mongo_client: Optional[AsyncIOMotorClient] = None
_db: Optional[AsyncIOMotorDatabase] = None


async def init_mongo() -> None:
    """Initialize MongoDB connection. Called at app startup."""
    global _mongo_client, _db
    try:
        _mongo_client = AsyncIOMotorClient(
            settings.mongodb_url,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
        )
        _db = _mongo_client[settings.mongodb_db]
        # Test connection
        await _db.command("ping")

        # Create indexes
        await _db.hibiscus_documents.create_index([("user_id", 1), ("created_at", -1)])
        await _db.hibiscus_documents.create_index([("session_id", 1)])
        await _db.hibiscus_analyses.create_index([("user_id", 1), ("doc_id", 1)])

        logger.info("mongodb_connected", db=settings.mongodb_db)
    except Exception as e:
        logger.warning("mongodb_connection_failed", error=str(e), fallback="in_memory")
        _mongo_client = None
        _db = None


async def close_mongo() -> None:
    """Close MongoDB connection."""
    global _mongo_client, _db
    if _mongo_client:
        _mongo_client.close()
        _mongo_client = None
        _db = None


# ── In-memory fallback ────────────────────────────────────────────────────
_document_store: Dict[str, Dict] = {}
_analysis_store: Dict[str, Dict] = {}


async def store_document(
    user_id: str,
    session_id: str,
    doc_id: str,
    filename: str,
    file_type: str,
    extraction: Optional[Dict[str, Any]] = None,
    extraction_confidence: float = 0.0,
    analysis_id: Optional[str] = None,
    eazr_score: Optional[int] = None,
    score_breakdown: Optional[Dict[str, Any]] = None,
    gaps: Optional[list] = None,
    validation: Optional[Dict[str, Any]] = None,
) -> str:
    """Store a document and its extraction in document memory."""
    doc = {
        "doc_id": doc_id,
        "user_id": user_id,
        "session_id": session_id,
        "filename": filename,
        "file_type": file_type,
        "extraction": extraction,
        "extraction_confidence": extraction_confidence,
        "analysis_id": analysis_id,
        "eazr_score": eazr_score,
        "score_breakdown": score_breakdown,
        "gaps": gaps,
        "validation": validation,
        "created_at": time.time(),
        "updated_at": time.time(),
    }

    try:
        if _db is not None:
            await _db.hibiscus_documents.replace_one(
                {"doc_id": doc_id},
                doc,
                upsert=True,
            )
        else:
            _document_store[doc_id] = doc

        logger.info(
            "document_stored",
            doc_id=doc_id,
            user_id=user_id,
            filename=filename,
            has_extraction=bool(extraction),
        )
    except Exception as e:
        logger.warning("document_store_failed", doc_id=doc_id, error=str(e))
        _document_store[doc_id] = doc

    return doc_id


async def get_document(doc_id: str) -> Optional[Dict[str, Any]]:
    """Get a specific document by ID."""
    try:
        if _db is not None:
            doc = await _db.hibiscus_documents.find_one(
                {"doc_id": doc_id}, {"_id": 0}
            )
            return doc
        return _document_store.get(doc_id)
    except Exception as e:
        logger.warning("document_get_failed", doc_id=doc_id, error=str(e))
        return _document_store.get(doc_id)


async def get_latest_document(user_id: str) -> Optional[Dict[str, Any]]:
    """Get the most recently uploaded document for a user."""
    try:
        if _db is not None:
            doc = await _db.hibiscus_documents.find_one(
                {"user_id": user_id},
                sort=[("created_at", -1)],
                projection={"_id": 0},
            )
            return doc

        # In-memory fallback
        user_docs = [d for d in _document_store.values() if d.get("user_id") == user_id]
        if user_docs:
            return sorted(user_docs, key=lambda d: d.get("created_at", 0), reverse=True)[0]
        return None

    except Exception as e:
        logger.warning("document_get_latest_failed", user_id=user_id, error=str(e))
        user_docs = [d for d in _document_store.values() if d.get("user_id") == user_id]
        if user_docs:
            return sorted(user_docs, key=lambda d: d.get("created_at", 0), reverse=True)[0]
        return None


async def get_user_documents(user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Get all documents for a user, most recent first."""
    try:
        if _db is not None:
            cursor = _db.hibiscus_documents.find(
                {"user_id": user_id},
                sort=[("created_at", -1)],
                limit=limit,
                projection={"_id": 0, "extraction": 0},  # Exclude large fields
            )
            return await cursor.to_list(length=limit)

        user_docs = [d for d in _document_store.values() if d.get("user_id") == user_id]
        return sorted(user_docs, key=lambda d: d.get("created_at", 0), reverse=True)[:limit]

    except Exception as e:
        logger.warning("document_list_failed", user_id=user_id, error=str(e))
        return []


async def store_analysis_result(
    user_id: str,
    session_id: str,
    analysis: Dict[str, Any],
) -> None:
    """Store a policy analysis result (from policy_analyzer agent)."""
    doc_id = analysis.get("structured_data", {}).get("doc_id", f"analysis_{int(time.time())}")

    result = {
        "user_id": user_id,
        "session_id": session_id,
        "doc_id": doc_id,
        "agent": analysis.get("agent", "policy_analyzer"),
        "confidence": analysis.get("confidence", 0.0),
        "eazr_score": analysis.get("structured_data", {}).get("eazr_score"),
        "score_breakdown": analysis.get("structured_data", {}).get("score_breakdown", {}),
        "extraction": analysis.get("structured_data", {}).get("extraction", {}),
        "response_summary": analysis.get("response", "")[:500],  # Store summary only
        "sources": analysis.get("sources", []),
        "created_at": time.time(),
    }

    try:
        if _db is not None:
            await _db.hibiscus_analyses.replace_one(
                {"user_id": user_id, "doc_id": doc_id},
                result,
                upsert=True,
            )
        else:
            _analysis_store[f"{user_id}:{doc_id}"] = result

        logger.info(
            "analysis_stored",
            user_id=user_id,
            doc_id=doc_id,
            confidence=result["confidence"],
            eazr_score=result["eazr_score"],
        )
    except Exception as e:
        logger.warning("analysis_store_failed", error=str(e))
        _analysis_store[f"{user_id}:{doc_id}"] = result


async def update_extraction(doc_id: str, extraction: Dict[str, Any], confidence: float) -> None:
    """Update the extraction data for an existing document."""
    try:
        if _db is not None:
            await _db.hibiscus_documents.update_one(
                {"doc_id": doc_id},
                {"$set": {
                    "extraction": extraction,
                    "extraction_confidence": confidence,
                    "updated_at": time.time(),
                }},
            )
        elif doc_id in _document_store:
            _document_store[doc_id]["extraction"] = extraction
            _document_store[doc_id]["extraction_confidence"] = confidence
            _document_store[doc_id]["updated_at"] = time.time()
    except Exception as e:
        logger.warning("extraction_update_failed", doc_id=doc_id, error=str(e))
