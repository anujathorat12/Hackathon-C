import os
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseModel):
    # Primary & Fallback LLM Provider Chain (comma-separated list, e.g. "groq,openrouter,mistral,gemini")
    LLM_PROVIDER_CHAIN: str = os.getenv("LLM_PROVIDER_CHAIN", "groq,openrouter,mistral,gemini")

    # Groq Configuration
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_BASE_URL: str = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", os.getenv("LLM_MODEL", "openai/gpt-oss-120b"))

    # OpenRouter Configuration
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    OPENROUTER_BASE_URL: str = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    OPENROUTER_MODEL: str = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.3-70b-instruct")

    # Mistral Configuration
    MISTRAL_API_KEY: str = os.getenv("MISTRAL_API_KEY", "")
    MISTRAL_BASE_URL: str = os.getenv("MISTRAL_BASE_URL", "https://api.mistral.ai/v1")
    MISTRAL_MODEL: str = os.getenv("MISTRAL_MODEL", "mistral-small-latest")

    # Gemini Configuration (OpenAI-compatible endpoint)
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_BASE_URL: str = os.getenv("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")

    # Legacy alias
    LLM_MODEL: str = os.getenv("LLM_MODEL", "openai/gpt-oss-120b")

    MONGODB_URI: str = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    VECTOR_DB_TYPE: str = os.getenv("VECTOR_DB_TYPE", "chroma")
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

settings = Settings()
