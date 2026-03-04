"""
Life insurance extractor — 60 fields.
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
"""
from hibiscus.extraction.extractors.base import BaseExtractor


class LifeExtractor(BaseExtractor):
    category = "life"
    prompt_file = "life.txt"
    max_tokens = 4000
    temperature = 0.0
    timeout = 45


life_extractor = LifeExtractor()
