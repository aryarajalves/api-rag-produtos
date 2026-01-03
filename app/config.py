import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    """Configurações centralizadas da aplicação"""
    
    # Supabase
    SUPABASE_URL: str = os.getenv("SUPABASE_URL")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY")
    
    # Gemini AI
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY")
    
    # Configurações da API
    PRODUCTS_LIMIT: int = int(os.getenv("PRODUCTS_LIMIT", "5"))
    MAX_CONCURRENT_AI_REQUESTS: int = int(os.getenv("MAX_CONCURRENT_AI_REQUESTS", "5"))
    AI_QUEUE_TIMEOUT: int = int(os.getenv("AI_QUEUE_TIMEOUT", "30"))
    
    # Configurações do Worker
    EMBEDDING_UPDATE_INTERVAL_MINUTES: int = int(os.getenv("EMBEDDING_UPDATE_INTERVAL_MINUTES", "10"))
    
    # Redis (Cache)
    REDIS_URL: str = os.getenv("REDIS_URL", "")

    # Segurança
    API_KEY: str = os.getenv("API_KEY", "")

settings = Settings()
