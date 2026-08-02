import sys
import os
import json
import time
from pathlib import Path
from fastapi.testclient import TestClient

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Force mock environment settings
os.environ["GEMINI_API_KEY"] = "dummy_gemini_api_key"
os.environ["CHROMA_DB_PATH"] = "./data/test_chroma_db"

from src.config import settings
settings.chroma_db_path = "./data/test_chroma_db"

from src.api.main import app, REPORT_CACHE_PATH

client = TestClient(app)

def test_api_endpoints():
    # 1. Clean report cache file if exists
    if REPORT_CACHE_PATH.exists():
        REPORT_CACHE_PATH.unlink()
        
    # Ingest mock reviews to disk so the compiler has inputs to process
    test_reviews = [
        # Group 1: Convenience / Delivery
        {
            "source_id": "api_test_1",
            "cleaned_text": "Blinkit delivery is fast. I like rapid grocery delivery.",
            "platform": "play_store",
            "timestamp": "2026-07-29T10:00:00",
            "author_anonymized": "User_api_1",
            "metadata": {"score": 5}
        },
        {
            "source_id": "api_test_2",
            "cleaned_text": "The delivery guy was extremely fast, got my groceries quickly.",
            "platform": "play_store",
            "timestamp": "2026-07-29T10:01:00",
            "author_anonymized": "User_api_2",
            "metadata": {"score": 5}
        },
        {
            "source_id": "api_test_3",
            "cleaned_text": "Fast delivery service and very quick doorstep arrival.",
            "platform": "play_store",
            "timestamp": "2026-07-29T10:02:00",
            "author_anonymized": "User_api_3",
            "metadata": {"score": 5}
        },
        {
            "source_id": "api_test_4",
            "cleaned_text": "Super quick and convenient grocery delivery within minutes.",
            "platform": "play_store",
            "timestamp": "2026-07-29T10:03:00",
            "author_anonymized": "User_api_4",
            "metadata": {"score": 5}
        },
        # Group 2: Price Sensitive
        {
            "source_id": "api_test_5",
            "cleaned_text": "This milk is expensive, price is too high.",
            "platform": "play_store",
            "timestamp": "2026-07-29T10:04:00",
            "author_anonymized": "User_api_5",
            "metadata": {"score": 2}
        },
        {
            "source_id": "api_test_6",
            "cleaned_text": "Organic products here are very expensive, costing too much money.",
            "platform": "play_store",
            "timestamp": "2026-07-29T10:05:00",
            "author_anonymized": "User_api_6",
            "metadata": {"score": 2}
        },
        {
            "source_id": "api_test_7",
            "cleaned_text": "The handling charge and prices are too high compared to other apps.",
            "platform": "play_store",
            "timestamp": "2026-07-29T10:06:00",
            "author_anonymized": "User_api_7",
            "metadata": {"score": 2}
        },
        {
            "source_id": "api_test_8",
            "cleaned_text": "Items are overpriced, it cost a lot of money to order regular items.",
            "platform": "play_store",
            "timestamp": "2026-07-29T10:07:00",
            "author_anonymized": "User_api_8",
            "metadata": {"score": 2}
        },
        # Group 3: Trust / Quality
        {
            "source_id": "api_test_9",
            "cleaned_text": "Milk packets are defective, scam return.",
            "platform": "play_store",
            "timestamp": "2026-07-29T10:08:00",
            "author_anonymized": "User_api_9",
            "metadata": {"score": 1}
        },
        {
            "source_id": "api_test_10",
            "cleaned_text": "Damaged packets delivered, worst quality products.",
            "platform": "play_store",
            "timestamp": "2026-07-29T10:09:00",
            "author_anonymized": "User_api_10",
            "metadata": {"score": 1}
        },
        {
            "source_id": "api_test_11",
            "cleaned_text": "Defective grocery items and bad return support.",
            "platform": "play_store",
            "timestamp": "2026-07-29T10:10:00",
            "author_anonymized": "User_api_11",
            "metadata": {"score": 1}
        },
        {
            "source_id": "api_test_12",
            "cleaned_text": "Scammed by delivery, defective product and no refund.",
            "platform": "play_store",
            "timestamp": "2026-07-29T10:11:00",
            "author_anonymized": "User_api_12",
            "metadata": {"score": 1}
        }
    ]
    
    normalized_path = PROJECT_ROOT / "data" / "normalized_reviews.json"
    normalized_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save original content of normalized reviews if exists, to restore it later
    original_normalized_content = None
    if normalized_path.exists():
        with open(normalized_path, "r", encoding="utf-8") as f:
            original_normalized_content = f.read()
            
    with open(normalized_path, "w", encoding="utf-8") as f:
        json.dump(test_reviews, f, indent=2)
        
    # 2. Query Report Endpoint (First query: Compiles and caches)
    t0 = time.time()
    response = client.get("/api/report")
    t1 = time.time()
    
    assert response.status_code == 200
    data = response.json()
    assert "executive_summary" in data
    assert "themes" in data
    assert "opportunities" in data
    assert "cohorts_breakdown" in data
    
    # Check cached report exists
    assert REPORT_CACHE_PATH.exists()
    
    # 3. Query Report Endpoint (Second query: Reads from cache)
    t2 = time.time()
    response_cached = client.get("/api/report")
    t3 = time.time()
    
    assert response_cached.status_code == 200
    # Cached access must be <= 50ms, well below the 200ms threshold
    cache_response_time = (t3 - t2) * 1000
    assert cache_response_time <= 200
    print(f"Cached API response time: {cache_response_time:.2f}ms")
    
    # 4. Query Themes Endpoint
    response_themes = client.get("/api/themes")
    assert response_themes.status_code == 200
    themes = response_themes.json()
    assert len(themes) > 0
    assert "theme_name" in themes[0]
    assert "opportunity_score" in themes[0]
    
    # 5. Query Drilldown Endpoint
    theme_id = themes[0]["theme_id"]
    response_drilldown = client.get(f"/api/drilldown?theme_id={theme_id}")
    assert response_drilldown.status_code == 200
    drilldown = response_drilldown.json()
    assert "reviews" in drilldown
    assert len(drilldown["reviews"]) > 0

    # 6. Query Search Endpoint
    response_search = client.get("/api/search?q=Why do users repeatedly buy from the same categories?")
    assert response_search.status_code == 200
    search_data = response_search.json()
    assert "answer" in search_data
    assert "confidence" in search_data
    assert "supporting_quotes" in search_data

    # Clean up test files
    if REPORT_CACHE_PATH.exists():
        REPORT_CACHE_PATH.unlink()
        
    # Restore original normalized reviews if saved, otherwise delete the file
    if original_normalized_content is not None:
        with open(normalized_path, "w", encoding="utf-8") as f:
            f.write(original_normalized_content)
    elif normalized_path.exists():
        normalized_path.unlink()
    
    # Do not delete the database directory here to avoid lock/readonly issues with active handles.
    # It will be cleaned up at the start of the next run.
    pass
