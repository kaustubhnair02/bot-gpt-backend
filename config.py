from pydantic_settings import BaseSettings
import logging
import sys
import os

class Settings(BaseSettings):
    # MongoDB
    MONGODB_URL: str = "mongodb://localhost:27017"
    DATABASE_NAME: str = "bot_gpt"
    
    # LLM
    LLM_PROVIDER: str = "groq"
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.1-8b-instant"
    
    # RAG
    CHUNK_SIZE: int = 500
    TOP_K: int = 3
    
    class Config:
        env_file = ".env"

settings = Settings()


# Simple logging setup
def setup_logging():
    """Setup basic logging configuration"""
    # Create logs directory
    os.makedirs("logs", exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("logs/bot_gpt.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )


