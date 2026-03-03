"""
Document Ingestion Pipeline
=============================
Transforms raw insurance documents into searchable vector chunks in Qdrant.

Pipeline:
  1. Load raw content (JSON corpus files or text)
  2. Chunk with RecursiveCharacterTextSplitter (800 tokens, 100 overlap)
  3. Prepend contextual prefix to each chunk (improves retrieval by ~40%)
  4. Batch embed chunks (OpenAI text-embedding-3-small)
  5. Upsert to Qdrant insurance_knowledge collection

Contextual prefix pattern (per Anthropic contextual retrieval research):
  "This is from [source], section [section], about [category]. "
  Attaches document-level context to each chunk so retrieval works
  even when the chunk itself is missing key identifying info.

Run:
  python -m hibiscus.knowledge.rag.ingestion            # ingest all corpus
  python -m hibiscus.knowledge.rag.ingestion --file X   # ingest single file
"""
import asyncio
import hashlib
import json
import os
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from langchain_text_splitters import RecursiveCharacterTextSplitter

from hibiscus.config import settings
from hibiscus.knowledge.rag.client import rag_client, init_rag
from hibiscus.observability.logger import get_logger

logger = get_logger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────
CHUNK_SIZE = 800          # characters — balanced for insurance content density
CHUNK_OVERLAP = 100       # character overlap between chunks
CORPUS_DIR = Path(__file__).parent / "corpus"

# Splitter: tries paragraph → sentence → word → character boundaries
_splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP,
    separators=["\n\n", "\n", ". ", "? ", "! ", ", ", " ", ""],
    length_function=len,
    is_separator_regex=False,
)


# ── Contextual Prefix Builder ─────────────────────────────────────────────────

def _build_contextual_prefix(metadata: Dict[str, Any]) -> str:
    """
    Build a contextual prefix for a chunk.

    Anthropic's contextual retrieval research shows that prepending document-level
    context to each chunk significantly improves retrieval recall (by ~40%).

    The prefix answers: WHERE does this text come from? WHAT category is it?
    """
    parts = []

    source = metadata.get("source") or metadata.get("circular_no") or metadata.get("insurer")
    category = metadata.get("category")
    section = (
        metadata.get("section")
        or metadata.get("subject")
        or metadata.get("claim_type")
        or metadata.get("term")
    )
    date = metadata.get("date") or metadata.get("effective_date")

    if source:
        parts.append(f"Source: {source}")
    if date:
        parts.append(f"dated {date}")
    if category:
        parts.append(f"category: {category}")
    if section:
        parts.append(f"section: {section}")

    if not parts:
        return ""

    return "This is from " + ", ".join(parts) + ". "


def _stable_chunk_id(source: str, chunk_index: int, content: str) -> str:
    """
    Generate a stable, deterministic ID for a chunk.
    Same source + chunk_index always produces same ID.
    Prevents duplicate insertion on re-ingestion.
    """
    hash_input = f"{source}::{chunk_index}::{content[:100]}"
    return str(uuid.UUID(hashlib.md5(hash_input.encode()).hexdigest()))


# ── Core ingestion function ───────────────────────────────────────────────────

async def ingest_document(
    content: str,
    metadata: Dict[str, Any],
    collection: str = None,
) -> int:
    """
    Ingest a single document into the Qdrant knowledge base.

    Steps:
    1. Chunk the text using RecursiveCharacterTextSplitter
    2. Prepend contextual prefix to each chunk
    3. Generate stable chunk IDs
    4. Upsert to Qdrant

    Args:
        content    : Full text content of the document
        metadata   : Document-level metadata dict. Required fields vary by type.
                     Common fields: source, category, date, section
        collection : Override target collection (defaults to insurance_knowledge)

    Returns:
        Number of chunks ingested (0 on failure or empty content).
    """
    if not content or not content.strip():
        logger.warning("ingest_document_empty_content", metadata=metadata)
        return 0

    target_collection = collection or settings.qdrant_collection_knowledge

    start_ms = int(time.time() * 1000)
    source = (
        metadata.get("source")
        or metadata.get("circular_no")
        or metadata.get("term")
        or metadata.get("insurer")
        or "unknown"
    )

    logger.info(
        "ingest_document_start",
        source=source,
        content_length=len(content),
        collection=target_collection,
    )

    # ── Step 1: Chunk ─────────────────────────────────────────────────────────
    raw_chunks = _splitter.split_text(content)

    if not raw_chunks:
        logger.warning("ingest_document_no_chunks", source=source)
        return 0

    # ── Step 2: Contextual prefix ─────────────────────────────────────────────
    prefix = _build_contextual_prefix(metadata)
    enriched_chunks = [prefix + chunk if prefix else chunk for chunk in raw_chunks]

    # ── Step 3: Build document list ───────────────────────────────────────────
    documents = []
    for idx, chunk_text in enumerate(enriched_chunks):
        chunk_id = _stable_chunk_id(source, idx, chunk_text)
        documents.append(
            {
                "id": chunk_id,
                "content": chunk_text,
                "metadata": {
                    **metadata,
                    "chunk_index": idx,
                    "chunk_total": len(enriched_chunks),
                    "has_prefix": bool(prefix),
                },
            }
        )

    # ── Step 4: Upsert to Qdrant ──────────────────────────────────────────────
    upserted = await rag_client.upsert(target_collection, documents)

    latency_ms = int(time.time() * 1000) - start_ms
    logger.info(
        "ingest_document_complete",
        source=source,
        chunks_created=len(raw_chunks),
        chunks_upserted=upserted,
        collection=target_collection,
        latency_ms=latency_ms,
    )

    return upserted


# ── Corpus-level ingestion ────────────────────────────────────────────────────

def _glossary_item_to_document(item: Dict[str, Any]) -> tuple[str, Dict[str, Any]]:
    """Convert a glossary JSON item to (content, metadata) for ingestion."""
    term = item.get("term", "")
    definition = item.get("definition", "")
    example = item.get("example", "")
    indian_context = item.get("indian_context", "")
    related = item.get("related_terms", [])

    content_parts = [f"Term: {term}", f"Definition: {definition}"]
    if example:
        content_parts.append(f"Example: {example}")
    if indian_context:
        content_parts.append(f"Indian context: {indian_context}")
    if related:
        content_parts.append(f"Related terms: {', '.join(related)}")

    content = "\n".join(content_parts)

    metadata = {
        "term": term,
        "category": item.get("category", "glossary"),
        "source": "hibiscus_insurance_glossary",
        "doc_type": "glossary",
    }
    return content, metadata


def _circular_item_to_document(item: Dict[str, Any]) -> tuple[str, Dict[str, Any]]:
    """Convert an IRDAI circular JSON item to (content, metadata) for ingestion."""
    circular_no = item.get("circular_no", "")
    subject = item.get("subject", "")
    date = item.get("date", "")
    key_points = item.get("key_points", [])
    consumer_rights = item.get("consumer_rights", [])

    content_parts = [
        f"Circular: {circular_no}",
        f"Subject: {subject}",
        f"Date: {date}",
    ]
    if key_points:
        content_parts.append("Key Points:")
        for pt in key_points:
            content_parts.append(f"- {pt}")
    if consumer_rights:
        content_parts.append("Consumer Rights:")
        for right in consumer_rights:
            content_parts.append(f"- {right}")

    content = "\n".join(content_parts)

    metadata = {
        "circular_no": circular_no,
        "subject": subject,
        "date": date,
        "category": item.get("category", "regulation"),
        "source": item.get("source", "irdai.gov.in"),
        "doc_type": "irdai_circular",
    }
    return content, metadata


def _claims_item_to_document(item: Dict[str, Any]) -> tuple[str, Dict[str, Any]]:
    """Convert a claims process JSON item to (content, metadata) for ingestion."""
    insurer = item.get("insurer", "")
    claim_type = item.get("claim_type", "")
    process = item.get("process", [])
    documents_needed = item.get("documents_needed", [])
    tpa = item.get("tpa", "")
    toll_free = item.get("toll_free", "")

    content_parts = [
        f"Insurer: {insurer}",
        f"Claim Type: {claim_type}",
    ]
    if process:
        content_parts.append("Process:")
        for step in process:
            content_parts.append(f"  {step}")
    if documents_needed:
        content_parts.append(f"Documents Required: {', '.join(documents_needed)}")
    if tpa:
        content_parts.append(f"TPA: {tpa}")
    if toll_free:
        content_parts.append(f"Toll-Free: {toll_free}")

    timeline_cashless = item.get("timeline_cashless_auth", "")
    timeline_reimb = item.get("reimbursement_timeline", "")
    if timeline_cashless:
        content_parts.append(f"Cashless Authorization Timeline: {timeline_cashless}")
    if timeline_reimb:
        content_parts.append(f"Reimbursement Timeline: {timeline_reimb}")

    content = "\n".join(content_parts)

    metadata = {
        "insurer": insurer,
        "claim_type": claim_type,
        "category": "claims_process",
        "source": f"{insurer.lower().replace(' ', '_')}_claims_guide",
        "doc_type": "claims_process",
    }
    return content, metadata


def _tax_item_to_document(item: Dict[str, Any]) -> tuple[str, Dict[str, Any]]:
    """Convert a tax rules JSON item to (content, metadata) for ingestion."""
    section = item.get("section", "")
    title = item.get("title", "")
    description = item.get("description", "")
    conditions = item.get("conditions", [])
    limits = item.get("limits", {})
    examples = item.get("examples", [])
    notes = item.get("notes", [])

    content_parts = [
        f"Tax Section: {section}",
        f"Title: {title}",
    ]
    if description:
        content_parts.append(f"Description: {description}")
    if conditions:
        content_parts.append("Conditions:")
        for cond in conditions:
            content_parts.append(f"- {cond}")
    if limits:
        content_parts.append("Limits:")
        for k, v in limits.items():
            content_parts.append(f"  {k}: {v}")
    if examples:
        content_parts.append("Examples:")
        for ex in examples:
            content_parts.append(f"- {ex}")
    if notes:
        content_parts.append("Notes:")
        for note in notes:
            content_parts.append(f"- {note}")

    content = "\n".join(content_parts)

    metadata = {
        "section": section,
        "title": title,
        "category": item.get("category", "tax_rules"),
        "source": "income_tax_act_insurance",
        "doc_type": "tax_rule",
    }
    return content, metadata


def _generic_item_to_document(item: Dict[str, Any], category: str) -> tuple[str, Dict[str, Any]]:
    """Fallback converter: serialize the whole item as text."""
    content = json.dumps(item, ensure_ascii=False, indent=2)
    metadata = {
        "category": category,
        "source": f"corpus_{category}",
        "doc_type": category,
    }
    return content, metadata


# ── Corpus loader ─────────────────────────────────────────────────────────────

def _detect_item_type(item: Dict[str, Any]) -> str:
    """Detect the type of a corpus item from its fields."""
    if "term" in item and "definition" in item:
        return "glossary"
    if "circular_no" in item:
        return "circular"
    if "insurer" in item and "claim_type" in item:
        return "claims"
    if "section" in item and ("80" in str(item.get("section", "")) or "10" in str(item.get("section", ""))):
        return "tax"
    return "generic"


async def ingest_corpus_file(file_path: Path) -> int:
    """
    Ingest a single corpus JSON file into Qdrant.

    Handles JSON arrays of objects. Auto-detects document type from field structure.

    Returns total chunks upserted from this file.
    """
    if not file_path.exists():
        logger.error("corpus_file_not_found", path=str(file_path))
        return 0

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as exc:
        logger.error("corpus_file_invalid_json", path=str(file_path), error=str(exc))
        return 0

    if not isinstance(data, list):
        data = [data]

    total = 0
    category = file_path.parent.name  # directory name = category

    logger.info(
        "corpus_file_ingestion_start",
        file=str(file_path.name),
        category=category,
        item_count=len(data),
    )

    for idx, item in enumerate(data):
        if not isinstance(item, dict):
            continue

        item_type = _detect_item_type(item)

        if item_type == "glossary":
            content, metadata = _glossary_item_to_document(item)
        elif item_type == "circular":
            content, metadata = _circular_item_to_document(item)
        elif item_type == "claims":
            content, metadata = _claims_item_to_document(item)
        elif item_type == "tax":
            content, metadata = _tax_item_to_document(item)
        else:
            content, metadata = _generic_item_to_document(item, category)

        metadata["corpus_file"] = str(file_path.name)
        metadata["item_index"] = idx

        chunks = await ingest_document(content, metadata)
        total += chunks

    logger.info(
        "corpus_file_ingestion_complete",
        file=str(file_path.name),
        total_chunks=total,
    )

    return total


async def ingest_corpus(corpus_dir: Path = CORPUS_DIR) -> Dict[str, int]:
    """
    Ingest all corpus JSON files from the corpus directory tree.

    Walks all subdirectories under corpus_dir, ingests every .json file.
    Skips README files and non-JSON files.

    Returns:
        Dict mapping file name to chunks ingested.
    """
    if not corpus_dir.exists():
        logger.error("corpus_dir_not_found", path=str(corpus_dir))
        return {}

    json_files = sorted(corpus_dir.rglob("*.json"))

    if not json_files:
        logger.warning("corpus_no_json_files", path=str(corpus_dir))
        return {}

    logger.info(
        "corpus_ingestion_start",
        corpus_dir=str(corpus_dir),
        file_count=len(json_files),
    )

    start_ms = int(time.time() * 1000)
    results: Dict[str, int] = {}
    grand_total = 0

    for file_path in json_files:
        chunks = await ingest_corpus_file(file_path)
        results[str(file_path.relative_to(corpus_dir))] = chunks
        grand_total += chunks

    latency_ms = int(time.time() * 1000) - start_ms
    logger.info(
        "corpus_ingestion_complete",
        files_ingested=len(json_files),
        total_chunks=grand_total,
        latency_ms=latency_ms,
    )

    # Print summary to stdout for operator visibility
    print("\n=== Hibiscus RAG Corpus Ingestion Summary ===")
    for fname, count in results.items():
        print(f"  {fname:<60} {count:>6} chunks")
    print(f"\n  Total: {grand_total} chunks across {len(json_files)} files")
    print(f"  Time:  {latency_ms / 1000:.1f}s")
    print("=" * 48)

    return results


# ── __main__ ──────────────────────────────────────────────────────────────────

async def _main() -> None:
    """CLI entry point for running ingestion directly."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Hibiscus RAG corpus ingestion tool",
        epilog="Example: python -m hibiscus.knowledge.rag.ingestion --file glossary/insurance_terms.json",
    )
    parser.add_argument(
        "--file",
        type=str,
        default=None,
        help="Ingest a single file relative to corpus dir. If omitted, ingest all.",
    )
    parser.add_argument(
        "--collection",
        type=str,
        default=settings.qdrant_collection_knowledge,
        help=f"Target Qdrant collection (default: {settings.qdrant_collection_knowledge})",
    )
    parser.add_argument(
        "--corpus-dir",
        type=str,
        default=str(CORPUS_DIR),
        help=f"Path to corpus directory (default: {CORPUS_DIR})",
    )
    args = parser.parse_args()

    # Initialize RAG client
    print(f"Connecting to Qdrant at {settings.qdrant_host}:{settings.qdrant_port}...")
    await init_rag()

    if not rag_client.is_available:
        print("ERROR: Qdrant is not available. Ensure it is running and try again.")
        print(f"  Expected: {settings.qdrant_host}:{settings.qdrant_port}")
        return

    corpus_dir = Path(args.corpus_dir)

    if args.file:
        target_file = corpus_dir / args.file
        print(f"Ingesting single file: {target_file}")
        chunks = await ingest_corpus_file(target_file)
        print(f"Ingested {chunks} chunks from {args.file}")
    else:
        print(f"Ingesting all corpus files from {corpus_dir}")
        await ingest_corpus(corpus_dir)


if __name__ == "__main__":
    asyncio.run(_main())
