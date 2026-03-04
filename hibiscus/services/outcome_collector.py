"""
🌺 Hibiscus v0.9 | EAZR AI Insurance Intelligence Engine
Outcome collector — gathers follow-up signals to measure recommendation effectiveness.
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
"""
import time
from datetime import datetime
from typing import List, Optional

from hibiscus.observability.logger import get_logger

logger = get_logger(__name__)

# ── Follow-up templates by advice type ───────────────────────────────────────
_FOLLOWUP_TEMPLATES = {
    "recommend": "A while back, I suggested looking into {summary}. Did you end up purchasing a policy?",
    "surrender": "We discussed surrendering your policy — {summary}. Did you decide what to do?",
    "claim": "Last time, I helped with claim guidance — {summary}. Were you able to file the claim successfully?",
    "tax": "We worked through your tax benefits — {summary}. Was the information helpful for your filing?",
    "calculate": "I ran some calculations for you — {summary}. Did those numbers help with your decision?",
    "compare": "We compared some insurance options — {summary}. Did you shortlist any plan?",
    "general": "Last time we discussed {summary}. How did that go?",
}

# Maximum number of follow-ups to inject per conversation
_MAX_FOLLOWUPS = 3

# Days before asking for follow-up
_DEFAULT_DAYS_THRESHOLD = 7


class OutcomeCollector:
    """
    Checks for pending outcomes and generates soft follow-up prompts.
    Designed to be non-intrusive: max 3 follow-ups, warm tone, easy to dismiss.
    """

    async def get_pending_followups(
        self,
        user_id: str,
        days_threshold: int = _DEFAULT_DAYS_THRESHOLD,
    ) -> str:
        """
        Get formatted follow-up text for outcomes pending longer than threshold.

        Returns empty string if no follow-ups needed.
        """
        try:
            from hibiscus.memory.layers.outcome import get_user_outcomes

            outcomes = await get_user_outcomes(user_id, limit=20)
            if not outcomes:
                return ""

            now = time.time()
            threshold_seconds = days_threshold * 86400
            pending = []

            for o in outcomes:
                if o.get("outcome") != "pending":
                    continue
                if o.get("action_taken") and o["action_taken"] != "pending":
                    continue

                created = o.get("created_at")
                if isinstance(created, str):
                    try:
                        created = datetime.fromisoformat(created).timestamp()
                    except (ValueError, TypeError):
                        continue
                elif isinstance(created, (int, float)):
                    pass
                else:
                    continue

                age_seconds = now - created
                if age_seconds >= threshold_seconds:
                    pending.append(o)

            if not pending:
                return ""

            # Generate follow-up prompts (most recent advice first, cap at MAX)
            followups = []
            for o in pending[:_MAX_FOLLOWUPS]:
                advice_type = o.get("advice_type", "general")
                summary = o.get("advice_summary", "your insurance query")
                # Truncate summary for natural conversation
                if len(summary) > 100:
                    summary = summary[:97] + "..."

                template = _FOLLOWUP_TEMPLATES.get(advice_type, _FOLLOWUP_TEMPLATES["general"])
                followups.append(template.format(summary=summary))

            if not followups:
                return ""

            header = "PENDING OUTCOME FOLLOW-UPS (mention naturally if relevant, do not force):"
            body = "\n".join(f"- {f}" for f in followups)
            return f"{header}\n{body}"

        except Exception as e:
            logger.warning("outcome_followup_failed", user_id=user_id, error=str(e))
            return ""

    async def record_advice_outcome(
        self,
        user_id: str,
        session_id: str,
        conversation_id: Optional[str],
        agent_name: str,
        response_text: str,
        policy_type: Optional[str] = None,
        insurer: Optional[str] = None,
    ) -> Optional[int]:
        """
        Record that advice was given by an agent.
        Called from memory_storage node after advice-giving agents complete.

        Maps agent names to advice types for the outcome system.
        """
        agent_to_advice = {
            "recommender": "recommend",
            "surrender_calculator": "surrender",
            "claims_guide": "claim",
            "tax_advisor": "tax",
            "calculator": "calculate",
            "risk_detector": "recommend",
            "portfolio_optimizer": "recommend",
        }

        advice_type = agent_to_advice.get(agent_name)
        if not advice_type:
            return None

        # Extract a concise summary from the response
        summary = response_text[:200].strip()
        if len(response_text) > 200:
            summary += "..."

        try:
            from hibiscus.memory.layers.outcome import record_outcome

            outcome_id = await record_outcome(
                user_id=user_id,
                session_id=session_id,
                advice_type=advice_type,
                advice_summary=summary,
                conversation_id=conversation_id,
                policy_type=policy_type,
                insurer=insurer,
            )
            logger.info(
                "advice_outcome_recorded",
                user_id=user_id,
                agent=agent_name,
                advice_type=advice_type,
                outcome_id=outcome_id,
            )
            return outcome_id

        except Exception as e:
            logger.warning(
                "advice_outcome_record_failed",
                user_id=user_id,
                agent=agent_name,
                error=str(e),
            )
            return None


# ── Module-level singleton ──────────────────────────────────────────────────
outcome_collector = OutcomeCollector()
