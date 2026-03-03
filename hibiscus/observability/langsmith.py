"""
LangSmith Tracing Integration
================================
Provides distributed tracing for the Hibiscus pipeline via LangSmith.

Each conversation is traced as a LangSmith run, with child spans for:
- Intent classification
- Agent execution (each agent = child run)
- LLM calls (logged via LiteLLM callbacks)
- Guardrail checks

Disabled gracefully if LANGSMITH_API_KEY is not set.

Usage:
    from hibiscus.observability.langsmith import tracer

    async with tracer.pipeline_run(session_id, user_message) as run:
        # ... pipeline execution ...
        run.add_metadata({"agents": ["policy_analyzer"]})
"""
import os
import time
import uuid
from contextlib import asynccontextmanager
from typing import Any, Optional
from .logger import get_logger

logger = get_logger("observability.langsmith")

_langsmith_enabled = False
_langsmith_client = None


def _init_langsmith() -> bool:
    """Initialize LangSmith client. Returns True if enabled."""
    global _langsmith_enabled, _langsmith_client

    api_key = os.getenv("LANGSMITH_API_KEY")
    if not api_key:
        logger.info("LangSmith disabled — no LANGSMITH_API_KEY set")
        return False

    try:
        from langsmith import Client
        project = os.getenv("LANGSMITH_PROJECT", "hibiscus")
        _langsmith_client = Client(api_key=api_key)
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_PROJECT"] = project
        _langsmith_enabled = True
        logger.info(f"LangSmith tracing enabled → project={project}")
        return True
    except ImportError:
        logger.warning("langsmith package not installed — tracing disabled. Run: pip install langsmith")
        return False
    except Exception as e:
        logger.warning(f"LangSmith init failed: {e} — continuing without tracing")
        return False


# Initialize on module load
_langsmith_enabled = _init_langsmith()


class PipelineRun:
    """
    Context manager for a single Hibiscus pipeline run.
    Creates a LangSmith run (or no-ops if LangSmith is disabled).
    """

    def __init__(
        self,
        session_id: str,
        user_message: str,
        run_id: Optional[str] = None,
    ):
        self.session_id = session_id
        self.user_message = user_message
        self.run_id = run_id or str(uuid.uuid4())
        self._start_time = time.time()
        self._metadata: dict[str, Any] = {}
        self._child_runs: list[dict] = []
        self._ls_run_id: Optional[str] = None
        self._error: Optional[str] = None

    def add_metadata(self, metadata: dict) -> None:
        """Add metadata to the run."""
        self._metadata.update(metadata)

    def record_agent(
        self,
        agent_name: str,
        confidence: float,
        latency_ms: float,
        sources: list[str],
        error: Optional[str] = None,
    ) -> None:
        """Record an agent execution as a child span."""
        self._child_runs.append({
            "agent": agent_name,
            "confidence": confidence,
            "latency_ms": round(latency_ms, 1),
            "sources": sources,
            "error": error,
        })

        if _langsmith_enabled and _langsmith_client:
            try:
                child_run_id = str(uuid.uuid4())
                _langsmith_client.create_run(
                    name=f"agent:{agent_name}",
                    run_type="chain",
                    inputs={"session_id": self.session_id},
                    outputs={"confidence": confidence, "sources": sources},
                    error=error,
                    parent_run_id=self._ls_run_id,
                    extra={"latency_ms": latency_ms},
                    id=child_run_id,
                    end_time=time.time(),
                )
            except Exception as e:
                logger.debug(f"LangSmith child run error: {e}")

    def record_guardrail(
        self,
        guardrail: str,
        passed: bool,
        modifications: list[str],
    ) -> None:
        """Record a guardrail check."""
        self._metadata[f"guardrail_{guardrail}"] = {
            "passed": passed,
            "modifications": modifications,
        }

    def record_error(self, error: str) -> None:
        """Record a pipeline error."""
        self._error = error

    async def _start_ls_run(self) -> None:
        """Start a LangSmith run."""
        if not _langsmith_enabled or not _langsmith_client:
            return
        try:
            self._ls_run_id = str(uuid.uuid4())
            _langsmith_client.create_run(
                name="hibiscus_pipeline",
                run_type="chain",
                inputs={
                    "session_id": self.session_id,
                    "user_message": self.user_message[:200],  # Truncate for privacy
                },
                id=self._ls_run_id,
                start_time=self._start_time,
                tags=["hibiscus", "v2"],
            )
        except Exception as e:
            logger.debug(f"LangSmith run start error: {e}")

    async def _end_ls_run(self, output: Optional[str] = None) -> None:
        """End the LangSmith run."""
        if not _langsmith_enabled or not _langsmith_client or not self._ls_run_id:
            return
        try:
            latency = round((time.time() - self._start_time) * 1000, 1)
            _langsmith_client.update_run(
                run_id=self._ls_run_id,
                outputs={"response": (output or "")[:500], "latency_ms": latency},
                error=self._error,
                extra={
                    "metadata": self._metadata,
                    "agents_run": [r["agent"] for r in self._child_runs],
                    "avg_confidence": (
                        sum(r["confidence"] for r in self._child_runs) / len(self._child_runs)
                        if self._child_runs else 0.0
                    ),
                },
                end_time=time.time(),
            )
        except Exception as e:
            logger.debug(f"LangSmith run end error: {e}")


class HibiscusTracer:
    """Main tracer singleton. Create pipeline runs for each conversation turn."""

    @asynccontextmanager
    async def pipeline_run(self, session_id: str, user_message: str):
        """
        Context manager for a Hibiscus pipeline run.

        Usage:
            async with tracer.pipeline_run(session_id, message) as run:
                run.add_metadata({"agents": ["policy_analyzer"]})
                run.record_agent("policy_analyzer", confidence=0.9, ...)
        """
        run = PipelineRun(session_id=session_id, user_message=user_message)
        await run._start_ls_run()
        try:
            yield run
        except Exception as e:
            run.record_error(str(e))
            raise
        finally:
            await run._end_ls_run()

    def is_enabled(self) -> bool:
        return _langsmith_enabled

    def log_feedback(self, run_id: str, score: float, comment: str = "") -> None:
        """Log user feedback for a run (1-5 score → normalized 0-1)."""
        if not _langsmith_enabled or not _langsmith_client:
            return
        try:
            normalized = (score - 1) / 4  # 1-5 → 0.0-1.0
            _langsmith_client.create_feedback(
                run_id=run_id,
                key="user_rating",
                score=normalized,
                comment=comment,
            )
        except Exception as e:
            logger.debug(f"LangSmith feedback error: {e}")


# Module-level singleton
tracer = HibiscusTracer()
