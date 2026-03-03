"""
Hibiscus Configuration
======================
All settings via Pydantic BaseSettings — validates env vars at startup.
"""
from functools import lru_cache
from typing import Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class HibiscusSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Service Identity ────────────────────────────────────────────
    app_name: str = "hibiscus"
    app_version: str = "5.0.0"
    hibiscus_env: str = Field(default="development", alias="HIBISCUS_ENV")
    hibiscus_port: int = Field(default=8001, alias="HIBISCUS_PORT")
    hibiscus_log_level: str = Field(default="INFO", alias="HIBISCUS_LOG_LEVEL")
    hibiscus_secret_key: str = Field(default="dev-secret-change-me", alias="HIBISCUS_SECRET_KEY")

    # ── LLM Providers ───────────────────────────────────────────────
    deepseek_api_key: str = Field(default="", alias="DEEPSEEK_API_KEY")
    anthropic_api_key: str = Field(default="", alias="ANTHROPIC_API_KEY")
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    zhipu_api_key: str = Field(default="", alias="GLM_API_KEY")
    zhipu_base_url: str = Field(default="https://api.z.ai/api/paas/v4/", alias="GLM_BASE_URL")

    # ── LLM Models ──────────────────────────────────────────────────
    deepseek_v3_model: str = "deepseek/deepseek-chat"        # Tier 1 — 80%
    deepseek_r1_model: str = "deepseek/deepseek-reasoner"    # Tier 2 — 15%
    claude_sonnet_model: str = "anthropic/claude-sonnet-4-5" # Tier 3 — 5%
    embedding_model: str = "embedding-2"                     # GLM embeddings (primary)

    # ── LLM Config ──────────────────────────────────────────────────
    llm_temperature: float = Field(default=0.3, alias="LLM_TEMPERATURE")
    llm_max_tokens: int = Field(default=4096, alias="LLM_MAX_TOKENS")
    llm_timeout: int = Field(default=30, alias="LLM_TIMEOUT")
    reasoning_max_tokens: int = 8192  # R1 needs more for chain-of-thought
    reasoning_timeout: int = 60       # R1 is slower

    # ── EAZR Existing API ────────────────────────────────────────────
    eazr_api_base: str = Field(default="http://localhost:8000", alias="EAZR_API_BASE")
    eazr_api_timeout: int = 90        # Large PDFs take time
    eazr_api_retries: int = 3

    # ── Redis (Session Memory — L1) ──────────────────────────────────
    redis_url: str = Field(default="redis://localhost:6379/1", alias="REDIS_URL")
    redis_session_ttl: int = 3600     # 1 hour session TTL
    redis_cache_ttl: int = 300        # 5 min for analysis cache

    # ── MongoDB (Document Memory — L6) ───────────────────────────────
    mongodb_url: str = Field(default="mongodb://localhost:27017/", alias="MONGODB_URL")
    mongodb_db: str = Field(default="hibiscus_db", alias="MONGODB_DB")

    # ── PostgreSQL (User Profile, Outcomes) ──────────────────────────
    postgresql_url: str = Field(
        default="postgresql+asyncpg://eazr:eazr_secure_2024@localhost:5432/insurance_india",
        alias="POSTGRESQL_URL"
    )

    # ── Neo4j (Knowledge Graph) ───────────────────────────────────────
    neo4j_uri: str = Field(default="bolt://localhost:7687", alias="NEO4J_URI")
    neo4j_user: str = Field(default="neo4j", alias="NEO4J_USER")
    neo4j_password: str = Field(default="", alias="NEO4J_PASSWORD")

    # ── Qdrant (RAG + Vector Memory) ──────────────────────────────────
    qdrant_host: str = Field(default="localhost", alias="QDRANT_HOST")
    qdrant_port: int = Field(default=6333, alias="QDRANT_PORT")
    qdrant_collection_knowledge: str = "insurance_knowledge"
    qdrant_collection_conversations: str = "user_conversations"
    qdrant_collection_insights: str = "user_knowledge"

    # ── Observability ─────────────────────────────────────────────────
    langsmith_api_key: str = Field(default="", alias="LANGSMITH_API_KEY")
    langsmith_project: str = Field(default="hibiscus", alias="LANGSMITH_PROJECT")

    # ── Web Search ────────────────────────────────────────────────────
    tavily_api_key: str = Field(default="", alias="TAVILY_API_KEY")

    # ── Auth / Security ───────────────────────────────────────────────
    # JWT secret shared with botproject. Empty string = dev mode (auth skipped).
    jwt_secret: str = Field(default="", alias="JWT_SECRET")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")

    # ── Guardrails ────────────────────────────────────────────────────
    confidence_threshold_high: float = 0.85    # State as fact
    confidence_threshold_medium: float = 0.70  # Add caveat
    confidence_threshold_low: float = 0.50     # Explicit uncertainty
    # Below low threshold → don't state, ask user

    # ── Computed Properties ───────────────────────────────────────────
    @property
    def is_production(self) -> bool:
        return self.hibiscus_env == "production"

    @property
    def has_deepseek(self) -> bool:
        return bool(self.deepseek_api_key)

    @property
    def has_anthropic(self) -> bool:
        return bool(self.anthropic_api_key)

    @property
    def has_neo4j(self) -> bool:
        return bool(self.neo4j_password)

    @property
    def has_langsmith(self) -> bool:
        return bool(self.langsmith_api_key)


@lru_cache(maxsize=1)
def get_settings() -> HibiscusSettings:
    """Cached settings singleton."""
    return HibiscusSettings()


# Module-level singleton for direct import
settings = get_settings()
