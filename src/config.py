import os
from pathlib import Path
from dotenv import load_dotenv

# Locate project root and load dotenv configuration
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DOTENV_PATH = PROJECT_ROOT / ".env"

if DOTENV_PATH.exists():
    load_dotenv(DOTENV_PATH)
else:
    load_dotenv()

class Settings:
    """Manages system configuration settings loaded from environment variables."""
    def __init__(self):
        # Reddit Client credentials
        self.reddit_client_id: str = os.getenv("REDDIT_CLIENT_ID", "dummy_reddit_client_id")
        self.reddit_client_secret: str = os.getenv("REDDIT_CLIENT_SECRET", "dummy_reddit_client_secret")
        self.reddit_user_agent: str = os.getenv("REDDIT_USER_AGENT", "BlinkitDiscoveryEngine/1.0")

        # Google AI Studio / Gemini Configuration
        self.gemini_api_key: str = os.getenv("GEMINI_API_KEY", "dummy_gemini_api_key")
        self.gemini_model_name: str = os.getenv("GEMINI_MODEL_NAME", "gemini-2.5-flash")

        # Database settings
        self.chroma_db_path: str = os.getenv("CHROMA_DB_PATH", "./data/chroma_db")

        # API Host Configuration
        self.api_host: str = os.getenv("API_HOST", "127.0.0.1")
        self.api_port: int = int(os.getenv("API_PORT", "8000"))
        self.env: str = os.getenv("ENV", "development")

# Global configurations instance
settings = Settings()
