"""Personal accident insurance extractor — 54 fields."""
from hibiscus.extraction.extractors.base import BaseExtractor


class PAExtractor(BaseExtractor):
    category = "pa"
    prompt_file = "pa.txt"
    max_tokens = 3500
    temperature = 0.0
    timeout = 45


pa_extractor = PAExtractor()
