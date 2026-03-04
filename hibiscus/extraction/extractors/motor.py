"""
🌺 Hibiscus v0.9 | EAZR AI Insurance Intelligence Engine
Motor insurance extractor — IDV, NCB, add-ons, depreciation schedule, garage network.
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
"""
from hibiscus.extraction.extractors.base import BaseExtractor


class MotorExtractor(BaseExtractor):
    category = "motor"
    prompt_file = "motor.txt"
    max_tokens = 4500
    temperature = 0.0
    timeout = 45


motor_extractor = MotorExtractor()
