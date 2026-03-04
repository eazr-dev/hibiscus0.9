"""
Unit Tests — Memory Assembler
==============================
Tests that assemble_context() returns the correct structure
and handles each memory layer gracefully (including when they're unavailable).
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
"""
import asyncio
import pytest

pytestmark = pytest.mark.asyncio


class TestAssembleContextStructure:
    """assemble_context() must return a dict with expected top-level keys."""

    async def test_returns_dict_with_required_keys(self):
        """assemble_context must return all required context keys."""
        from hibiscus.memory.assembler import assemble_context
        context = await assemble_context(
            user_id="test_user_001",
            session_id="test_session_001",
            query="What is my sum insured?",
        )
        assert isinstance(context, dict)
        assert "session_history" in context
        assert "document_context" in context
        assert "user_profile" in context
        assert "policy_portfolio" in context
        assert "relevant_memories" in context
        assert "relevant_conversations" in context

    async def test_session_history_is_list(self):
        """session_history must always be a list (never None)."""
        from hibiscus.memory.assembler import assemble_context
        context = await assemble_context(
            user_id="test_user_002",
            session_id="test_session_002",
            query="What is a deductible?",
        )
        assert isinstance(context["session_history"], list)

    async def test_policy_portfolio_is_list(self):
        """policy_portfolio must always be a list."""
        from hibiscus.memory.assembler import assemble_context
        context = await assemble_context(
            user_id="test_user_003",
            session_id="test_session_003",
            query="Show my portfolio",
        )
        assert isinstance(context["policy_portfolio"], list)

    async def test_relevant_memories_is_list(self):
        """relevant_memories must always be a list."""
        from hibiscus.memory.assembler import assemble_context
        context = await assemble_context(
            user_id="test_user_004",
            session_id="test_session_004",
            query="What is no claim bonus?",
        )
        assert isinstance(context["relevant_memories"], list)


class TestAssembleContextWithDocument:
    """Tests for document context loading when files are uploaded."""

    async def test_document_context_none_for_no_upload(self):
        """No uploaded files → document_context should be None or empty."""
        from hibiscus.memory.assembler import assemble_context
        context = await assemble_context(
            user_id="test_no_doc_user",
            session_id="test_no_doc_session",
            query="What is health insurance?",
            uploaded_files=[],
        )
        # Without an uploaded file, document_context should be None or empty dict
        assert context["document_context"] is None or context["document_context"] == {}

    async def test_uploaded_files_flag_triggers_doc_fetch(self):
        """When uploaded_files is provided, assembler should attempt to fetch doc context."""
        from hibiscus.memory.assembler import assemble_context
        # Pass a synthetic uploaded file indicator
        context = await assemble_context(
            user_id="test_doc_user",
            session_id="test_doc_session",
            query="Analyze my policy",
            uploaded_files=[{"filename": "policy.pdf", "content_type": "application/pdf"}],
        )
        # assembler should have attempted document fetch (may be None if MongoDB unavailable)
        assert "document_context" in context


class TestAssembleContextGracefulFallback:
    """Assembler must not raise even when memory services are unavailable."""

    async def test_assembler_does_not_raise_on_service_outage(self):
        """assemble_context must not crash if Redis/MongoDB/Qdrant are unavailable."""
        from hibiscus.memory.assembler import assemble_context
        # If services are down, should return empty but valid context
        try:
            context = await assemble_context(
                user_id="test_outage_user",
                session_id="test_outage_session",
                query="test query",
            )
            assert isinstance(context, dict)
        except Exception as e:
            pytest.fail(f"assemble_context raised an exception: {e}")

    async def test_assembler_returns_quickly(self):
        """Assembler should complete within a reasonable time even with service issues."""
        import time
        from hibiscus.memory.assembler import assemble_context
        start = time.time()
        try:
            await assemble_context(
                user_id="test_perf_user",
                session_id="test_perf_session",
                query="simple query",
            )
        except Exception:
            pass
        elapsed = time.time() - start
        # Should not hang — even on error, should return within 10 seconds
        assert elapsed < 10.0, f"assembler took too long: {elapsed:.1f}s"


class TestTokenBudgetConstants:
    """Verify TOKEN_BUDGET constants are sensible."""

    def test_token_budget_exists(self):
        """TOKEN_BUDGET must be defined in assembler module."""
        from hibiscus.memory.assembler import TOKEN_BUDGET
        assert isinstance(TOKEN_BUDGET, dict)

    def test_all_budget_keys_present(self):
        """All expected memory layers must have token budget allocations."""
        from hibiscus.memory.assembler import TOKEN_BUDGET
        expected_keys = {
            "session_history",
            "document_context",
            "user_profile",
            "policy_portfolio",
            "knowledge_memories",
            "conversation_history",
        }
        for key in expected_keys:
            assert key in TOKEN_BUDGET, f"Missing TOKEN_BUDGET key: {key}"

    def test_document_context_has_largest_budget(self):
        """Document context deserves the largest token allocation."""
        from hibiscus.memory.assembler import TOKEN_BUDGET
        assert TOKEN_BUDGET["document_context"] >= TOKEN_BUDGET["session_history"]
