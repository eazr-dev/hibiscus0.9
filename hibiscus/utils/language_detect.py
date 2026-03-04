"""
Language Detection — Script-Based + Keyword Heuristic
=====================================================
Detects: English (en), Hindi (hi), Hinglish (hinglish), Tamil (ta), Telugu (te), Marathi (mr)

Algorithm:
1. Count characters per Unicode script
2. >30% Devanagari + >30% Latin → Hinglish
3. >50% Devanagari → check Marathi keywords → "mr" or "hi"
4. >50% Tamil script → "ta"
5. >50% Telugu script → "te"
6. Default: English

No LLM call. Pure computation. Microsecond latency.
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
"""
import re
from typing import Dict

# ── Language display names (for prompt injection) ────────────────────────────
_LANGUAGE_NAMES: Dict[str, str] = {
    "en": "English",
    "hi": "Hindi",
    "hinglish": "Hinglish (Hindi-English mix)",
    "ta": "Tamil",
    "te": "Telugu",
    "mr": "Marathi",
}

# ── Marathi-specific keywords (not commonly used in Hindi) ───────────────────
_MARATHI_KEYWORDS = {
    "आहे", "नाही", "काय", "कसे", "माझा", "माझी", "माझे", "तुमचा", "तुमची",
    "होते", "करा", "सांगा", "पाहिजे", "आम्ही", "तुम्ही", "केले", "केला",
    "विमा", "पॉलिसी", "दावा",
}

# ── Hinglish indicators (Roman script Hindi words) ───────────────────────────
_HINGLISH_WORDS = {
    "kya", "hai", "hain", "mera", "meri", "mere", "kaise", "kitna", "kitni",
    "kab", "kaha", "kyun", "koi", "agar", "lekin", "aur", "ya", "nahi",
    "nahin", "hoga", "hogi", "milega", "milegi", "chahiye", "wala", "wali",
    "bolo", "batao", "samjhao", "bataiye", "bataye", "samjhaiye",
    "accha", "theek", "sahi", "galat", "achha", "thik",
    "policy", "bima", "kist", "jama", "dawa", "ilaaj",
    "paisa", "paise", "rupaye", "lakh", "crore",
    "abhi", "pehle", "baad", "jaldi", "zaruri", "zaroori",
    "ho", "kar", "de", "le", "ja", "aa",
    "ji", "sahab", "bhai", "didi",
    "yeh", "woh", "kuch", "sab", "bahut", "zyada", "kam",
    "jeb", "rashi", "dena", "hoga",
}


def detect_language(text: str) -> Dict[str, str]:
    """
    Detect the primary language of a text string.

    Returns:
        {
            "language": "en" | "hi" | "hinglish" | "ta" | "te" | "mr",
            "language_name": "English" | "Hindi" | ...,
            "script": "latin" | "devanagari" | "tamil" | "telugu" | "mixed",
        }
    """
    if not text or not text.strip():
        return {"language": "en", "language_name": "English", "script": "latin"}

    # Count characters by script
    devanagari = 0
    tamil = 0
    telugu = 0
    latin = 0
    total = 0

    for ch in text:
        cp = ord(ch)
        if cp < 0x20 or ch.isspace() or ch.isdigit():
            continue
        total += 1
        if 0x0900 <= cp <= 0x097F:
            devanagari += 1
        elif 0x0B80 <= cp <= 0x0BFF:
            tamil += 1
        elif 0x0C00 <= cp <= 0x0C7F:
            telugu += 1
        elif (0x0041 <= cp <= 0x005A) or (0x0061 <= cp <= 0x007A):
            latin += 1

    if total == 0:
        return {"language": "en", "language_name": "English", "script": "latin"}

    dev_ratio = devanagari / total
    latin_ratio = latin / total
    tamil_ratio = tamil / total
    telugu_ratio = telugu / total

    # Hinglish: significant mix of Devanagari and Latin
    if dev_ratio > 0.2 and latin_ratio > 0.2:
        return {"language": "hinglish", "language_name": _LANGUAGE_NAMES["hinglish"], "script": "mixed"}

    # Predominantly Devanagari — distinguish Hindi vs Marathi
    if dev_ratio > 0.4:
        # Check for Marathi-specific words
        words = set(re.findall(r'[\u0900-\u097F]+', text))
        marathi_hits = words & _MARATHI_KEYWORDS
        if len(marathi_hits) >= 2:
            return {"language": "mr", "language_name": _LANGUAGE_NAMES["mr"], "script": "devanagari"}
        return {"language": "hi", "language_name": _LANGUAGE_NAMES["hi"], "script": "devanagari"}

    # Tamil script
    if tamil_ratio > 0.4:
        return {"language": "ta", "language_name": _LANGUAGE_NAMES["ta"], "script": "tamil"}

    # Telugu script
    if telugu_ratio > 0.4:
        return {"language": "te", "language_name": _LANGUAGE_NAMES["te"], "script": "telugu"}

    # Roman-script Hinglish (most common Indian internet language)
    if latin_ratio > 0.5:
        words_lower = set(text.lower().split())
        hinglish_hits = words_lower & _HINGLISH_WORDS
        # If >=3 Hinglish words OR >=25% of words are Hinglish → classify as Hinglish
        word_count = len(words_lower)
        if len(hinglish_hits) >= 3 or (word_count > 0 and len(hinglish_hits) / word_count >= 0.25):
            return {"language": "hinglish", "language_name": _LANGUAGE_NAMES["hinglish"], "script": "latin"}

    # Default: English
    return {"language": "en", "language_name": _LANGUAGE_NAMES["en"], "script": "latin"}


def get_language_instruction(language: str) -> str:
    """
    Generate a prompt instruction for the detected language.
    Returns empty string for English (no special instruction needed).
    """
    if language == "en":
        return ""

    name = _LANGUAGE_NAMES.get(language, language)

    if language == "hinglish":
        return (
            f"LANGUAGE: Respond in {name}. Mix Hindi and English naturally. "
            "Keep ALL insurance terms in English: hospitalisation, critical illness, "
            "pre-existing condition, cashless, reimbursement, sum insured, premium, "
            "waiting period, claim, policy, deductible, co-pay, network hospital, TPA. "
            "Example: 'Aapka sum insured ₹10 lakh hai aur copay 20% hai.'"
        )

    if language == "hi":
        return (
            f"LANGUAGE: Respond in {name} (Devanagari script). "
            "Keep ALL insurance terms in English: hospitalisation, critical illness, "
            "pre-existing condition, cashless, reimbursement, sum insured, premium, "
            "waiting period, claim, policy, deductible, co-pay, network hospital, TPA. "
            "Example: 'आपका sum insured ₹10 लाख है और copay 20% है।'"
        )

    if language == "mr":
        return (
            f"LANGUAGE: Respond in {name} (Devanagari script). "
            "Keep ALL insurance terms in English. "
            "Example: 'तुमचा sum insured ₹10 लाख आहे आणि copay 20% आहे.'"
        )

    if language == "ta":
        return (
            f"LANGUAGE: Respond in {name} (Tamil script). "
            "Keep ALL insurance terms in English. "
            "Example: 'உங்கள் sum insured ₹10 லட்சம், copay 20%.'"
        )

    if language == "te":
        return (
            f"LANGUAGE: Respond in {name} (Telugu script). "
            "Keep ALL insurance terms in English. "
            "Example: 'మీ sum insured ₹10 లక్షలు, copay 20%.'"
        )

    return ""
