"""
Health insurance extractor — 84 fields.
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
"""
from hibiscus.extraction.extractors.base import BaseExtractor


class HealthExtractor(BaseExtractor):
    category = "health"
    prompt_file = "health.txt"
    max_tokens = 4000
    temperature = 0.0
    timeout = 45


health_extractor = HealthExtractor()
