"""Life insurance extractor — 60 fields."""
from hibiscus.extraction.extractors.base import BaseExtractor


class LifeExtractor(BaseExtractor):
    category = "life"
    prompt_file = "life.txt"
    max_tokens = 4000
    temperature = 0.0
    timeout = 45


life_extractor = LifeExtractor()
