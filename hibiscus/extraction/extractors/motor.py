"""Motor insurance extractor — 97 fields."""
from hibiscus.extraction.extractors.base import BaseExtractor


class MotorExtractor(BaseExtractor):
    category = "motor"
    prompt_file = "motor.txt"
    max_tokens = 4500
    temperature = 0.0
    timeout = 45


motor_extractor = MotorExtractor()
