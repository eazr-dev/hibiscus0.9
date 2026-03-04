"""
Travel insurance extractor — 71 fields.
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
"""
from hibiscus.extraction.extractors.base import BaseExtractor


class TravelExtractor(BaseExtractor):
    category = "travel"
    prompt_file = "travel.txt"
    max_tokens = 4000
    temperature = 0.0
    timeout = 45


travel_extractor = TravelExtractor()
