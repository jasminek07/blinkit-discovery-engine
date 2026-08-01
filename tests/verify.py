import sys
from pathlib import Path

# Add project root to sys.path to allow imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import settings

def test_settings_loaded():
    """Verify that settings are parsed correctly from environment."""
    assert settings.reddit_client_id is not None
    assert settings.reddit_client_secret is not None
    assert settings.groq_api_key is not None
    assert settings.groq_model_name == "llama-3.3-70b-versatile"
    assert settings.api_port == 8000
    assert settings.env == "development"
    print("✅ Settings Loaded Test Passed")

def test_project_directories_exist():
    """Verify that all required subdirectories are created and valid."""
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
        directory.mkdir(parents=True, exist_ok=True)
        assert directory.exists()
        assert directory.is_dir()
    print("✅ Project Directories Test Passed")

if __name__ == "__main__":
    print("Starting Phase 1 Verification Tests...")
    try:
        test_settings_loaded()
        test_project_directories_exist()
        print("🎉 All Phase 1 Verification Tests Passed Successfully!")
        sys.exit(0)
    except AssertionError as e:
        print(f"❌ Test Failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        sys.exit(1)
