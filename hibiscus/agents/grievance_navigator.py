"""
🌺 Hibiscus v0.9 | EAZR AI Insurance Intelligence Engine
Grievance navigator agent — IRDAI complaint process, ombudsman routing, escalation paths.
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
"""
import json
import time
from typing import Any, Dict, List, Optional, Tuple

from hibiscus.agents.base import BaseAgent, AgentResult
from hibiscus.llm.router import call_llm
from hibiscus.observability.logger import PipelineLogger
from hibiscus.orchestrator.state import HibiscusState

AGENT_SYSTEM_PROMPT = """You are Hibiscus, EAZR's grievance navigation specialist.

Your role: Be the user's advocate and guide through the insurance grievance and escalation process.

CRITICAL RULES:
1. Be emotionally supportive first — the user is frustrated, possibly dealing with a financial emergency
2. Be specific about timelines: Level 1 = 15 days SLA, Ombudsman = within 3 months of insurer rejection
3. Ombudsman service is COMPLETELY FREE — emphasize this
4. For every level: give the specific contact method (URL, address, phone)
5. ALWAYS mention: keep documentary evidence of every communication
6. NEVER discourage from filing — Indian consumers have strong regulatory protections
7. Mention: "You can file with IRDAI while the insurer's grievance is being processed"
8. Use ₹ symbol, Indian format

TONE: Empathetic, empowering, specific. The user is frustrated — be their champion.
Opening: "I understand how frustrating this is. Here's exactly how to fight this..."
"""

# Complete grievance escalation ladder
ESCALATION_LADDER = [
    {
        "level": 1,
        "name": "Internal Grievance — Insurer's GRO",
        "applicable_when": "First step — mandatory before approaching IRDAI or Ombudsman",
        "timeline": "Insurer must respond within 15 days (IRDAI mandate)",
        "cost": "Free",
        "how_to": [
            "Write a formal grievance letter to the insurer's Grievance Redressal Officer (GRO)",
            "Include: Policy number, nature of complaint, documents, expected resolution",
            "Send via: Registered post + email (keep tracking number and email timestamps)",
            "Also file through insurer's app/website grievance portal",
            "Get a written acknowledgment with reference number — this is your evidence",
        ],
        "contact": "Find GRO contact at insurer's website → Customer Service → Grievance Redressal",
        "escalation_trigger": "No response in 15 days OR unsatisfactory response",
        "irdai_reference": "IRDAI (Protection of Policyholders' Interests) Regulations 2017 — Regulation 13",
    },
    {
        "level": 2,
        "name": "IRDAI Bima Bharosa Portal",
        "applicable_when": "Insurer did not respond in 15 days, OR response is unsatisfactory",
        "timeline": "IRDAI forwards to insurer; insurer must resolve within 15 days",
        "cost": "Free",
        "how_to": [
            "Visit: bimabharosaportal.irdai.gov.in",
            "Register/login with your email or mobile",
            "Select 'Register Complaint' → choose insurer → fill complaint details",
            "Attach: Insurer's response (if any), your original documents, correspondence",
            "Note your complaint reference number",
            "IRDAI tracks resolution and intervenes if insurer does not respond",
        ],
        "contact": "bimabharosaportal.irdai.gov.in | IRDAI helpline: 155255 or 1800-4254-732",
        "escalation_trigger": "Not resolved within 30 days of IRDAI complaint",
        "irdai_reference": "IRDAI IGMS — Integrated Grievance Management System",
    },
    {
        "level": 3,
        "name": "Insurance Ombudsman",
        "applicable_when": [
            "Insurer rejected/ignored the complaint",
            "Within 3 months of insurer's final rejection letter",
            "Claim amount up to ₹50 lakh",
        ],
        "timeline": "Ombudsman must pass award within 3 months of receiving complete documents",
        "cost": "Completely FREE — no fees, no lawyers required",
        "how_to": [
            "Identify the Ombudsman office for your state (list at irdai.gov.in)",
            "Download the complaint form from irdai.gov.in/ombudsman",
            "Fill form and submit with all documents",
            "You can appear in person or submit written arguments",
            "Ombudsman holds hearings and passes a binding award",
            "Insurer must comply with award within 30 days",
        ],
        "contact": "17 offices across India — contact by state (see below)",
        "escalation_trigger": "Unhappy with ombudsman award, or claim above ₹50L",
        "irdai_reference": "Insurance Ombudsman Rules 2017",
        "important_note": "DO NOT exceed 3 months from insurer rejection — you lose the right to approach ombudsman",
    },
    {
        "level": 4,
        "name": "Consumer Forum",
        "applicable_when": "Claims above ₹50 lakh, or if ombudsman approach is not suitable",
        "timeline": "Variable — typically 6-18 months",
        "cost": "Small filing fee; lawyers recommended for complex cases",
        "how_to": [
            "DCDRC (District Consumer Disputes Redressal Commission): Claims up to ₹1 crore",
            "SCDRC (State Consumer Disputes Redressal Commission): Claims ₹1 crore to ₹10 crore",
            "NCDRC (National Consumer Disputes Redressal Commission): Claims above ₹10 crore",
            "Consumer complaint under Consumer Protection Act 2019",
            "Insurer can be held liable for deficiency in service",
        ],
        "contact": "consumerhelpline.gov.in | edaakhil.nic.in (online filing)",
        "escalation_trigger": "Dissatisfied with forum order",
        "irdai_reference": "Consumer Protection Act 2019",
    },
    {
        "level": 5,
        "name": "Civil Court",
        "applicable_when": "Last resort when all other remedies exhausted",
        "timeline": "2-10 years typically",
        "cost": "Filing fees + lawyer fees — significant",
        "how_to": [
            "Consult a lawyer with insurance litigation experience",
            "File civil suit in appropriate court",
        ],
        "contact": "Local civil court / High Court",
        "escalation_trigger": "Final option",
        "irdai_reference": "Code of Civil Procedure 1908",
    },
]

# State-wise ombudsman offices (partial list — most major states)
OMBUDSMAN_OFFICES = {
    "Maharashtra": {
        "jurisdiction": ["Maharashtra", "Goa"],
        "address": "3rd Floor, Jeevan Seva Annexe, S.V. Road, Santacruz (W), Mumbai — 400 054",
        "phone": "022-26106960 / 26106552",
        "email": "bimalokpal.mumbai@ecoi.co.in",
    },
    "Delhi": {
        "jurisdiction": ["Delhi", "Haryana", "Himachal Pradesh", "J&K", "Punjab"],
        "address": "2/2 A, Universal Insurance Building, Asaf Ali Road, New Delhi — 110 002",
        "phone": "011-23239633 / 23237532",
        "email": "bimalokpal.newdelhi@ecoi.co.in",
    },
    "Karnataka": {
        "jurisdiction": ["Karnataka"],
        "address": "Jeevan Soudha Building, PID No. 57-27-N-19, Ground Floor, 19/19, 24th Main Road, JP Nagar, Phase 1, Bengaluru — 560 078",
        "phone": "080-26652049 / 26652048",
        "email": "bimalokpal.bengaluru@ecoi.co.in",
    },
    "Tamil Nadu": {
        "jurisdiction": ["Tamil Nadu", "Pondicherry"],
        "address": "Fathima Akhtar Court, 4th Floor, 453 (old 312), Anna Salai, Teynampet, Chennai — 600 018",
        "phone": "044-24333668 / 24335284",
        "email": "bimalokpal.chennai@ecoi.co.in",
    },
    "West Bengal": {
        "jurisdiction": ["West Bengal", "Sikkim", "Andaman & Nicobar"],
        "address": "Hindustan Building Annexe, 4th Floor, 4, C.R. Avenue, Kolkata — 700 072",
        "phone": "033-22124339 / 22124340",
        "email": "bimalokpal.kolkata@ecoi.co.in",
    },
    "Telangana": {
        "jurisdiction": ["Andhra Pradesh", "Telangana", "Yanam"],
        "address": "6-2-46, 1st Floor, Moin Court, Lane Opp. Saleem Function Palace, A.C. Guards, Lakdi-Ka-Pool, Hyderabad — 500 004",
        "phone": "040-65504123 / 23312122",
        "email": "bimalokpal.hyderabad@ecoi.co.in",
    },
    "Gujarat": {
        "jurisdiction": ["Gujarat", "Dadra & Nagar Haveli", "Daman & Diu"],
        "address": "Office of the Insurance Ombudsman, Jeevan Prakash Building, 6th Floor, Tilak Marg, Relief Road, Ahmedabad — 380 001",
        "phone": "079-25501201 / 25501202",
        "email": "bimalokpal.ahmedabad@ecoi.co.in",
    },
    "Rajasthan": {
        "jurisdiction": ["Rajasthan"],
        "address": "Jeevan Nidhi II Building, Bhawani Singh Road, Jaipur — 302 005",
        "phone": "0141-2740363",
        "email": "bimalokpal.jaipur@ecoi.co.in",
    },
    "Uttar Pradesh": {
        "jurisdiction": ["Uttar Pradesh", "Uttarakhand"],
        "address": "Jeevan Bhawan, Phase 2, 6th Floor, Nawal Kishore Road, Hazratganj, Lucknow — 226 001",
        "phone": "0522-2231330 / 2231331",
        "email": "bimalokpal.lucknow@ecoi.co.in",
    },
    "Madhya Pradesh": {
        "jurisdiction": ["Madhya Pradesh", "Chhattisgarh"],
        "address": "Janak Vihar Complex, 2nd Floor, 6, Malviya Nagar, Opp. Airtel, Near New Market, Bhopal — 462 003",
        "phone": "0755-2769201 / 2769202",
        "email": "bimalokpal.bhopal@ecoi.co.in",
    },
}


class GrievanceNavigatorAgent(BaseAgent):
    """Guides users through insurance grievance and ombudsman escalation."""

    name = "grievance_navigator"
    description = "IRDAI complaint and ombudsman guide"
    default_tier = "deepseek_v3"

    async def execute(self, state: HibiscusState) -> AgentResult:
        plog = PipelineLogger(
            component=f"agent.{self.name}",
            request_id=state.get("request_id", "?"),
            session_id=state.get("session_id", "?"),
            user_id=state.get("user_id", "?"),
        )
        start = time.time()
        plog.agent_start(agent=self.name, model=self.default_tier, task=state.get("intent", ""))

        try:
            message = state.get("message", "")
            emotional_state = state.get("emotional_state", "neutral")

            # ── Step 1: Determine escalation level ────────────────────────
            plog.step_start("determine_escalation_level")
            current_level, level_confidence = self._determine_level(message)
            plog.step_complete(
                "determine_escalation_level",
                level=current_level,
                confidence=level_confidence,
            )

            # ── Step 2: Extract context ────────────────────────────────────
            user_state = self._extract_user_state(message, state)
            insurer = self._extract_insurer(message)
            ombudsman_office = self._get_ombudsman_office(user_state)

            # ── Step 3: Build relevant escalation steps ────────────────────
            # Show current level + next 2 levels
            relevant_steps = ESCALATION_LADDER[max(0, current_level - 1):]

            # ── Step 4: LLM synthesis ──────────────────────────────────────
            plog.step_start("llm_synthesis")
            is_distressed = emotional_state in ("distressed", "frustrated", "urgent") or (
                any(w in message.lower() for w in ["cheated", "fraud", "unfair", "wrong", "unjust"])
            )

            synthesis_prompt = self._build_synthesis_prompt(
                message=message,
                current_level=current_level,
                relevant_steps=relevant_steps,
                insurer=insurer,
                user_state=user_state,
                ombudsman_office=ombudsman_office,
                is_distressed=is_distressed,
            )

            llm_response = await call_llm(
                messages=[
                    {
                        "role": "system",
                        "content": self._system_prompt + "\n\n" + AGENT_SYSTEM_PROMPT,
                    },
                    {"role": "user", "content": synthesis_prompt},
                ],
                tier=self.default_tier,
                conversation_id=state.get("conversation_id", "?"),
                agent=self.name,
            )

            response_text = llm_response["content"]
            plog.step_complete("llm_synthesis")

            # ── Step 5: Sources ────────────────────────────────────────────
            sources = [
                {
                    "type": "regulation",
                    "reference": "Insurance Ombudsman Rules 2017",
                    "confidence": 0.95,
                },
                {
                    "type": "regulation",
                    "reference": "IRDAI (Protection of Policyholders' Interests) Regulations 2017",
                    "confidence": 0.95,
                },
                {
                    "type": "regulation",
                    "reference": "Consumer Protection Act 2019",
                    "confidence": 0.90,
                },
            ]

            confidence = 0.88
            latency_ms = int((time.time() - start) * 1000)

            return AgentResult(
                response=response_text,
                confidence=confidence,
                sources=sources,
                latency_ms=latency_ms,
                tokens_in=llm_response.get("tokens_in", 0),
                tokens_out=llm_response.get("tokens_out", 0),
                structured_data={
                    "current_escalation_level": current_level,
                    "insurer_mentioned": insurer,
                    "user_state": user_state,
                    "ombudsman_office": ombudsman_office,
                    "escalation_ladder": [
                        {
                            "level": s["level"],
                            "name": s["name"],
                            "timeline": s["timeline"],
                            "cost": s["cost"],
                        }
                        for s in ESCALATION_LADDER
                    ],
                },
                follow_up_suggestions=[
                    "Would you like help drafting a formal grievance letter?",
                    "Should I find the exact ombudsman office contact for your state?",
                    "Want to know what documents you need to file an ombudsman complaint?",
                ],
            )

        except Exception as e:
            plog.error("grievance_navigator", error=str(e))
            return AgentResult(
                response=self._error_response(),
                confidence=0.0,
                sources=[],
            )

    # ── Private helpers ────────────────────────────────────────────────────

    def _determine_level(self, message: str) -> Tuple[int, float]:
        """Determine which escalation level the user is at."""
        msg_lower = message.lower()

        level_keywords = {
            1: ["not responded", "no response", "first complaint", "just filed", "filed complaint",
                "grievance officer"],
            2: ["irdai", "igms", "bima bharosa", "escalated", "already complained"],
            3: ["ombudsman", "not resolved even", "rejected by irdai", "3 months"],
            4: ["consumer forum", "ncdrc", "scdrc", "court", "legal action"],
        }

        for level in [4, 3, 2, 1]:  # Check highest first
            keywords = level_keywords[level]
            if any(kw in msg_lower for kw in keywords):
                return level, 0.80

        # Default to level 1 (start of process)
        if any(w in msg_lower for w in ["complaint", "issue", "problem", "rejected", "unfair"]):
            return 1, 0.70

        return 1, 0.60

    def _extract_user_state(
        self, message: str, state: HibiscusState
    ) -> Optional[str]:
        """Extract user's state for ombudsman jurisdiction."""
        msg_lower = message.lower()

        states_list = [
            "maharashtra", "mumbai", "pune",
            "delhi", "ncr", "gurgaon", "noida",
            "karnataka", "bengaluru", "bangalore",
            "tamil nadu", "chennai",
            "west bengal", "kolkata",
            "telangana", "hyderabad",
            "andhra pradesh",
            "gujarat", "ahmedabad", "surat",
            "rajasthan", "jaipur",
            "uttar pradesh", "lucknow",
            "madhya pradesh", "bhopal",
        ]

        state_to_canonical = {
            "mumbai": "Maharashtra", "pune": "Maharashtra",
            "delhi": "Delhi", "ncr": "Delhi", "gurgaon": "Delhi", "noida": "Delhi",
            "bengaluru": "Karnataka", "bangalore": "Karnataka",
            "chennai": "Tamil Nadu",
            "kolkata": "West Bengal",
            "hyderabad": "Telangana",
            "ahmedabad": "Gujarat", "surat": "Gujarat",
            "jaipur": "Rajasthan",
            "lucknow": "Uttar Pradesh",
            "bhopal": "Madhya Pradesh",
        }

        for state_kw in states_list:
            if state_kw in msg_lower:
                return state_to_canonical.get(state_kw, state_kw.title())

        # From user profile
        user_profile = state.get("user_profile") or {}
        if user_profile.get("state"):
            return user_profile["state"]
        if user_profile.get("city"):
            city = user_profile["city"].lower()
            return state_to_canonical.get(city, None)

        return None

    def _get_ombudsman_office(
        self, user_state: Optional[str]
    ) -> Optional[Dict[str, Any]]:
        """Get ombudsman office for user's state."""
        if not user_state:
            return None
        return OMBUDSMAN_OFFICES.get(user_state)

    def _extract_insurer(self, message: str) -> Optional[str]:
        """Extract insurer from message."""
        known_insurers = [
            "lic", "life insurance corporation",
            "hdfc life", "sbi life", "icici prudential", "max life",
            "bajaj allianz", "kotak mahindra", "tata aia",
            "star health", "niva bupa", "care health",
            "hdfc ergo", "icici lombard", "new india",
            "reliance general", "go digit",
        ]
        msg_lower = message.lower()
        for insurer in known_insurers:
            if insurer in msg_lower:
                return insurer.title()
        return None

    def _build_synthesis_prompt(
        self,
        message: str,
        current_level: int,
        relevant_steps: List[Dict[str, Any]],
        insurer: Optional[str],
        user_state: Optional[str],
        ombudsman_office: Optional[Dict[str, Any]],
        is_distressed: bool,
    ) -> str:
        """Build synthesis prompt with all grievance data."""
        tone_instruction = ""
        if is_distressed:
            tone_instruction = (
                "\nTONE: User is clearly frustrated/distressed. "
                "Open with ONE sentence: 'I completely understand your frustration — you have strong legal rights here.' "
                "Then give the practical path forward. End with: 'You are protected by IRDAI regulations. "
                "These escalation channels exist exactly for situations like yours.'"
            )

        insurer_text = f"Insurer in question: {insurer}" if insurer else "No specific insurer mentioned"
        state_text = f"User's state: {user_state}" if user_state else "State not mentioned"

        ombudsman_text = ""
        if ombudsman_office:
            ombudsman_text = f"""
OMBUDSMAN OFFICE FOR {user_state.upper()}:
  Address: {ombudsman_office.get('address', 'See irdai.gov.in')}
  Phone: {ombudsman_office.get('phone', 'See irdai.gov.in')}
  Email: {ombudsman_office.get('email', 'See irdai.gov.in')}
  Jurisdiction: {', '.join(ombudsman_office.get('jurisdiction', [user_state]))}
"""
        else:
            ombudsman_text = "\nOMBUDSMAN OFFICE: State not identified — direct user to irdai.gov.in for their state's office"

        steps_text = json.dumps(relevant_steps[:3], indent=2, ensure_ascii=False)

        return f"""The user needs help with an insurance grievance or complaint escalation.
{tone_instruction}

USER'S SITUATION: {message}
CURRENT ESCALATION LEVEL: {current_level} (showing from this level onwards)
{insurer_text}
{state_text}
{ombudsman_text}

ESCALATION STEPS (from current level):
{steps_text}

INSTRUCTIONS FOR RESPONSE:

1. Acknowledge the situation (1 sentence, empathetic)

2. "WHERE YOU STAND" section:
   - What level you are at
   - What options you have from here

3. "WHAT TO DO NOW" — specific numbered steps for the CURRENT level:
   - Exact action to take
   - What to include/attach
   - How to send (registered post + email)
   - What to expect and when

4. "NEXT STEPS IF NOT RESOLVED" — brief preview of Level {current_level + 1}:
   - When to escalate (specific trigger)
   - How to approach

5. OMBUDSMAN KEY FACTS (always include):
   - Service is COMPLETELY FREE
   - Must approach within 3 months of insurer rejection
   - For claims up to ₹50 lakh
   - Binding on the insurer

6. If ombudsman office provided: include the full contact details

7. DOCUMENTS TO KEEP (always mention):
   - Original policy, all correspondence, rejection letters
   - Timestamps and reference numbers of all communications
   - "Take registered post receipts — they are evidence of submission date"

8. IMPORTANT: Mention IRDAI Bima Bharosa: bimabharosaportal.irdai.gov.in

9. End: "You have rights. These escalation channels were created to protect you."

Do not generalize — be specific to this user's current situation.
"""


# ── Module-level run function (called by agent_dispatch) ──────────────────
_agent = GrievanceNavigatorAgent()


async def run(state: HibiscusState) -> Dict[str, Any]:
    """Entry point for agent_dispatch."""
    return await _agent(state)
