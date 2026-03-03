"""
Application configuration and settings
"""
import os
import logging
from pathlib import Path
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from ai_chat_components.llm_config import get_llm
from ai_chat_components.vectore_store import prepare_vectorstore

# Configure logging
logging.captureWarnings(True)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


class Settings:
    """Application settings"""

    # App Info
    APP_NAME: str = "Enhanced Financial Assistant with Chat Memory"
    APP_DESCRIPTION: str = "AI Assistant with advanced chatbot capabilities, memory system and multiple financial services"
    APP_VERSION: str = "4.0.0"

    # Directories
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    FRONTEND_DIR: Path = BASE_DIR / "frontend"

    # API Keys
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

    # URLs
    BASE_URL: str = os.getenv("BASE_URL", "http://localhost:8000")

    # CORS Configuration
    ALLOWED_ORIGINS_RAW: str = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8000,http://192.168.1.4:3000")
    ALLOWED_ORIGINS: list = [origin.strip() for origin in ALLOWED_ORIGINS_RAW.split(",")]
    VERCEL_PATTERN: str = r"https://eazr-ai-v2.*\.vercel\.app"

    # Environment Configuration
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "local")  # 'local' or 'production'

    # MongoDB Configuration - Environment-based selection
    MONGODB_URI_LOCAL: str = os.getenv("MONGODB_URI_LOCAL", "mongodb://localhost:27017/")
    MONGODB_DB_LOCAL: str = os.getenv("MONGODB_DB_LOCAL", "insurance_analysis_db")

    MONGODB_URI_PRODUCTION: str = os.getenv("MONGODB_URI_PRODUCTION", "")
    MONGODB_DB_PRODUCTION: str = os.getenv("MONGODB_DB_PRODUCTION", "insurance_analysis_db")

    # Connection Pool Settings
    MONGO_MAX_POOL_SIZE: int = int(os.getenv("MONGO_MAX_POOL_SIZE", "50"))
    MONGO_MIN_POOL_SIZE: int = int(os.getenv("MONGO_MIN_POOL_SIZE", "10"))
    MONGO_CONNECT_TIMEOUT: int = int(os.getenv("MONGO_CONNECT_TIMEOUT", "5000"))
    MONGO_SOCKET_TIMEOUT: int = int(os.getenv("MONGO_SOCKET_TIMEOUT", "10000"))

    @property
    def MONGODB_URI(self) -> str:
        """Get MongoDB URI based on environment"""
        if self.ENVIRONMENT == "production":
            return self.MONGODB_URI_PRODUCTION
        else:
            return self.MONGODB_URI_LOCAL

    @property
    def MONGODB_DATABASE(self) -> str:
        """Get MongoDB database name based on environment"""
        if self.ENVIRONMENT == "production":
            return self.MONGODB_DB_PRODUCTION
        else:
            return self.MONGODB_DB_LOCAL

    # Redis Configuration
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))

    # Security
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "your-secret-key-here")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 14  # 14 days

    # PostgreSQL — Insurance Product Database (insurance_india)
    PG_INSURANCE_HOST: str = os.getenv("PG_INSURANCE_HOST", os.getenv("TYPEORM_HOST", "localhost"))
    PG_INSURANCE_PORT: int = int(os.getenv("PG_INSURANCE_PORT", os.getenv("TYPEORM_PORT", "5432")))
    PG_INSURANCE_USER: str = os.getenv("PG_INSURANCE_USER", os.getenv("TYPEORM_USERNAME", "postgres"))
    PG_INSURANCE_PASSWORD: str = os.getenv("PG_INSURANCE_PASSWORD", os.getenv("TYPEORM_PASSWORD", ""))
    PG_INSURANCE_DB: str = os.getenv("PG_INSURANCE_DB", "insurance_india")

    @property
    def PG_INSURANCE_DSN(self) -> str:
        """PostgreSQL DSN for the insurance_india database."""
        return (
            f"postgresql://{self.PG_INSURANCE_USER}:{self.PG_INSURANCE_PASSWORD}"
            f"@{self.PG_INSURANCE_HOST}:{self.PG_INSURANCE_PORT}/{self.PG_INSURANCE_DB}"
        )

    # AWS S3 Configuration
    AWS_ACCESS_KEY_ID: str = os.getenv("AWS_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY: str = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    AWS_BUCKET_NAME: str = os.getenv("AWS_BUCKET_NAME", "")

    def __init__(self):
        """Initialize settings and create directories"""
        self.FRONTEND_DIR.mkdir(exist_ok=True)

        # Log environment configuration
        logger.info(f"🔧 Environment: {self.ENVIRONMENT}")
        logger.info(f"📊 MongoDB: {'Production (Atlas)' if self.ENVIRONMENT == 'production' else 'Local'}")
        logger.info(f"🔗 MongoDB URI: {self.MONGODB_URI[:30]}..." if self.MONGODB_URI else "⚠️  MongoDB URI not configured")
        logger.info(f"💾 Database: {self.MONGODB_DATABASE}")


# Global settings instance
settings = Settings()


# -------------------- LLM & RAG Setup --------------------

# Initialize LLM
_llm_instance = None

def get_llm_instance():
    """Get or create LLM instance"""
    global _llm_instance
    if _llm_instance is None:
        _llm_instance = get_llm(use_case='general')
        logger.info("✓ LLM instance initialized")
    return _llm_instance


# Initialize embeddings
_embeddings = None

def get_embeddings():
    """Get or create embeddings instance"""
    global _embeddings
    if _embeddings is None:
        _embeddings = OpenAIEmbeddings(openai_api_key=settings.OPENAI_API_KEY)
        logger.info("✓ Embeddings initialized")
    return _embeddings


# Initialize vectorstore
_vectorstore = None

def get_vectorstore():
    """Get or create vectorstore instance"""
    global _vectorstore
    if _vectorstore is None:
        embeddings = get_embeddings()
        try:
            _vectorstore = FAISS.load_local(
                "faiss_index",
                embeddings,
                allow_dangerous_deserialization=True
            )
            logger.info("✓ Loaded existing FAISS vectorstore")
        except Exception as e:
            logger.info("  Creating new vectorstore...")
            _vectorstore = prepare_vectorstore()
            _vectorstore.save_local("faiss_index")
            logger.info("✓ Created and saved new vectorstore")
    return _vectorstore


# Initialize RAG chain
_rag_chain = None

def get_rag_chain():
    """Get or create RAG chain instance"""
    global _rag_chain
    if _rag_chain is None:
        llm = get_llm_instance()
        vectorstore = get_vectorstore()
        retriever = vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 3}
        )

        rag_prompt_template = """
Context from documents: {context}
Question: {question}

Provide a comprehensive answer based on the context. If the context doesn't contain enough information, supplement with general knowledge but clearly distinguish between document-based and general information.

Answer:
"""

        rag_prompt = PromptTemplate(
            template=rag_prompt_template,
            input_variables=["context", "question"]
        )

        _rag_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=retriever,
            chain_type_kwargs={"prompt": rag_prompt},
            return_source_documents=True
        )
        logger.info("✓ RAG chain initialized")

    return _rag_chain


# CORS origin validator
def validate_cors_origin(origin: str) -> bool:
    """Validate origin against allowed patterns, supporting wildcards"""
    for allowed in settings.ALLOWED_ORIGINS:
        if allowed == origin:
            return True
        # Support wildcard patterns (e.g., https://eazr-ai-v2-*.vercel.app)
        if '*' in allowed:
            import fnmatch
            if fnmatch.fnmatch(origin, allowed):
                return True
    return False
