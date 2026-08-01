import os
import sys
import shutil
import json
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Setup temporary test database directory before importing config/store
TEST_DB_PATH = PROJECT_ROOT / "data" / "test_chroma_db"
os.environ["CHROMA_DB_PATH"] = str(TEST_DB_PATH)

from src.vector_db.chroma_client import ChromaVectorStore, flatten_metadata

def test_flatten_metadata():
    review = {
        "source_id": "rev_123",
        "platform": "play_store",
        "timestamp": "2026-07-29T12:00:00",
        "author_anonymized": "User_abc",
        "metadata": {
            "score": 5,
            "thumbs_up_count": 10,
            "redundant_key": "some_value"
        }
    }
    flat = flatten_metadata(review)
    assert flat["source_id"] == "rev_123"
    assert flat["platform"] == "play_store"
    assert flat["meta_score"] == 5
    assert flat["meta_thumbs_up_count"] == 10
    assert flat["meta_redundant_key"] == "some_value"

def test_vector_store_ingestion_and_query():
    # Clean up test DB path if exists
    if TEST_DB_PATH.exists():
        shutil.rmtree(TEST_DB_PATH)
        
    store = ChromaVectorStore(collection_name="test_reviews_collection")
    store.reset_database()
    
    # Verify starting empty
    assert len(store.get_all_reviews()) == 0
    
    # Sample test reviews
    test_reviews = [
        {
            "source_id": "test_1",
            "cleaned_text": "Blinkit delivery is incredibly fast, got my grocery package in just 8 minutes today!",
            "platform": "play_store",
            "timestamp": "2026-07-29T10:00:00",
            "author_anonymized": "User_1",
            "metadata": {"score": 5}
        },
        {
            "source_id": "test_2",
            "cleaned_text": "The price of organic shampoo is too expensive compared to other grocery stores.",
            "platform": "app_store",
            "timestamp": "2026-07-29T10:05:00",
            "author_anonymized": "User_2",
            "metadata": {"score": 2}
        },
        {
            "source_id": "test_3",
            "cleaned_text": "I am worried about product quality of milk packets as they leak often.",
            "platform": "reddit",
            "timestamp": "2026-07-29T10:10:00",
            "author_anonymized": "User_3",
            "metadata": {"score": 3}
        }
    ]
    
    # Ingest
    store.add_reviews(test_reviews)
    
    # Verify count
    all_stored = store.get_all_reviews()
    assert len(all_stored) == 3
    
    # Query semantic match for "fast delivery"
    query_results = store.query_reviews("very quick delivery service", limit=1)
    assert len(query_results) == 1
    # Test 1 should rank first as it is about "incredibly fast delivery"
    assert query_results[0]["source_id"] == "test_1"
    assert query_results[0]["metadata"]["score"] == 5
    assert query_results[0]["platform"] == "play_store"
    
    # Query semantic match for "expensive pricing"
    query_results_price = store.query_reviews("high product price", limit=1)
    assert len(query_results_price) == 1
    # Test 2 should rank first as it is about "too expensive pricing"
    assert query_results_price[0]["source_id"] == "test_2"
    assert query_results_price[0]["platform"] == "app_store"

    # Query semantic match for "leakage or bad quality milk"
    query_results_quality = store.query_reviews("leaking milk packets quality", limit=1)
    assert len(query_results_quality) == 1
    assert query_results_quality[0]["source_id"] == "test_3"
    
    # Clean up test DB path after test completes
    if TEST_DB_PATH.exists():
        shutil.rmtree(TEST_DB_PATH)
