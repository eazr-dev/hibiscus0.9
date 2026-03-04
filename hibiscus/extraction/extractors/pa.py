"""
🌺 Hibiscus v0.9 | EAZR AI Insurance Intelligence Engine
Personal accident extractor — accidental death benefit, disability grading, exclusions.
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
"""
from hibiscus.extraction.extractors.base import BaseExtractor


class PAExtractor(BaseExtractor):
    category = "pa"
    prompt_file = "pa.txt"
    max_tokens = 3500
    temperature = 0.0
    timeout = 45


pa_extractor = PAExtractor()
