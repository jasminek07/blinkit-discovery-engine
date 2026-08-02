import sys
import os
import json
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

from src.api.main import app
from src.vector_db.chroma_client import ChromaVectorStore

client = TestClient(app)

def test_chat_endpoints():
    print("Initializing test database collection...")
    # Initialize chroma store and add mock reviews for similarity retrieval
    store = ChromaVectorStore(collection_name="blinkit_live_reviews")
    store.reset_database()
    
    test_reviews = [
        {
            "source_id": "chat_test_1",
            "cleaned_text": "Blinkit delivery is incredibly fast, got my grocery package in just 8 minutes today!",
            "platform": "play_store",
            "timestamp": "2026-07-29T10:00:00",
            "author_anonymized": "User_chat_1",
            "metadata": {"score": 5}
        },
        {
            "source_id": "chat_test_2",
            "cleaned_text": "I am worried about product quality of milk packets as they leak often.",
            "platform": "play_store",
            "timestamp": "2026-07-29T10:05:00",
            "author_anonymized": "User_chat_2",
            "metadata": {"score": 2}
        }
    ]
    
    store.add_reviews(test_reviews)
    
    # 1. Test first turn query
    print("Testing multi-turn chat turn 1...")
    response_t1 = client.post("/api/chat", json={
        "message": "Why do users repeatedly buy from the same product categories?",
        "history": []
    })
    
    assert response_t1.status_code == 200
    data_t1 = response_t1.json()
    assert "reply" in data_t1
    assert "confidence" in data_t1
    assert "supporting_quotes" in data_t1
    assert len(data_t1["supporting_quotes"]) > 0
    print("Turn 1 check passed.")

    # 2. Test second turn follow-up with history
    print("Testing multi-turn chat turn 2 (with history)...")
    history_t2 = [
        {"role": "user", "content": "Why do users repeatedly buy from the same product categories?"},
        {"role": "assistant", "content": data_t1["reply"]}
    ]
    response_t2 = client.post("/api/chat", json={
        "message": "What prevents users from exploring new categories?",
        "history": history_t2
    })
    
    assert response_t2.status_code == 200
    data_t2 = response_t2.json()
    assert "reply" in data_t2
    assert "confidence" in data_t2
    assert len(data_t2["supporting_quotes"]) > 0
    print("Turn 2 check passed.")

    # 3. Test unrelated query capability guardrail rejection
    print("Testing unrelated query rejection...")
    response_unrelated = client.post("/api/chat", json={
        "message": "Who is the prime minister of France?",
        "history": []
    })
    assert response_unrelated.status_code == 200
    data_unrelated = response_unrelated.json()
    assert data_unrelated["reply"] == "Answering this is beyond my capabilities right now"
    assert data_unrelated["confidence"] == "Low"
    assert len(data_unrelated["supporting_quotes"]) == 0
    print("Unrelated query rejection check passed.")

    # 4. Test newly allowed specific related questions
    print("Testing specific related questions...")
    for q_text, expected_keyword in [
        ("what is the most ordere category", "ordered categories"),
        ("what issues people face with address change", "delivery address post-order"),
        ("what issues users face with exchange and retuen", "exchange and returns")
    ]:
        res_q = client.post("/api/chat", json={"message": q_text, "history": []})
        assert res_q.status_code == 200
        data_q = res_q.json()
        assert expected_keyword in data_q["reply"]
        assert len(data_q["supporting_quotes"]) > 0
    print("Specific related questions checks passed.")

    # Do not delete the database directory here to avoid lock/readonly issues with active handles.
    # It will be cleaned up at the start of the next run.
    pass

if __name__ == "__main__":
    test_chat_endpoints()
    print("All chatbot integration tests passed successfully!")
