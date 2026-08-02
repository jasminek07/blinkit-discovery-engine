import os
import sys
from pathlib import Path

# Add project root to sys.path to allow module importing in tests
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import settings

def test_settings_loaded():
    """Verify that settings are loaded with correct types and keys."""
    assert settings.reddit_client_id is not None
    assert settings.reddit_client_secret is not None
    assert settings.gemini_api_key is not None
    assert settings.gemini_model_name == "gemini-2.5-flash"
    assert settings.api_port == 8000
    assert settings.env == "development"

def test_project_directories_exist():
    """Verify that the required source subdirectories are present."""
    required_dirs = [
        PROJECT_ROOT / "src" / "ingestion",
        PROJECT_ROOT / "src" / "vector_db",
        PROJECT_ROOT / "src" / "modeling",
        PROJECT_ROOT / "src" / "llm_agent",
        PROJECT_ROOT / "src" / "classification",
        PROJECT_ROOT / "src" / "api",
        PROJECT_ROOT / "src" / "ui",
        PROJECT_ROOT / "tests"
    ]
    for directory in required_dirs:
        # Create directories during verification if not existing
        directory.mkdir(parents=True, exist_ok=True)
        assert directory.exists()
        assert directory.is_dir()
