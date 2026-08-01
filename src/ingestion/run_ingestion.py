import os
import json
import sys
from pathlib import Path
from typing import List, Dict, Any

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.ingestion.play_store import fetch_play_store_reviews
from src.ingestion.app_store import fetch_app_store_reviews
from src.ingestion.reddit import fetch_reddit_discussions
from src.ingestion.cleaner import clean_and_normalize_records

# Define target keys to remove from any record
KEYS_TO_REMOVE = {
    "reviewId", "userName", "userImage", "reviewCreatedVersion", 
    "at", "replyContent", "repliedAt", "app_version"
}

def sanitize_metadata_keys(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Recursively removes unwanted review keys from records and metadata."""
    sanitized = []
    for rec in records:
        cleaned_rec = {}
        for k, v in rec.items():
            if k in KEYS_TO_REMOVE:
                continue
            if k == "metadata" and isinstance(v, dict):
                # Clean nested metadata dictionaries
                cleaned_metadata = {mk: mv for mk, mv in v.items() if mk not in KEYS_TO_REMOVE}
                cleaned_rec[k] = cleaned_metadata
            else:
                cleaned_rec[k] = v
        sanitized.append(cleaned_rec)
    return sanitized

def run_ingestion_pipeline(play_count: int = 5000, app_count: int = 0, reddit_count: int = 0):
    """
    Runs the full ingestion, cleaning, and normalization pipeline.
    Saves raw reviews to data/raw_reviews.json and normalized reviews to data/normalized_reviews.json.
    """
    print("🚀 Starting User Discovery Ingestion Pipeline...")
    
    # 1. Fetch from sources (Google Play Store ONLY)
    print("Fetching Google Play Store reviews for the past 3 months...")
    play_reviews = fetch_play_store_reviews(app_id="com.grofers.customerapp", count=play_count)
    print(f"Collected {len(play_reviews)} Play Store reviews.")
    
    all_raw = play_reviews
    
    if not all_raw:
        # For testing purposes, if scrapers return nothing (e.g. offline), we provide some mock data
        print("⚠️ No reviews fetched from APIs. Adding sample mock reviews for pipeline validation...")
        all_raw = [
            {
                "source_id": "mock_1",
                "platform": "play_store",
                "timestamp": "2026-07-29T12:00:00",
                "author_anonymized": "PlayStoreUser_abc123",
                "raw_text": "Blinkit delivery is really fast. I buy milk and bread every day. Need more options for fresh organic vegetables though.",
                "metadata": {"score": 4, "userName": "ObsoleteName", "reviewId": "obsolete_id"}
            },
            {
                "source_id": "mock_2",
                "platform": "app_store",
                "timestamp": "2026-07-29T12:05:00",
                "author_anonymized": "AppStoreUser_def456",
                "raw_text": "Placing order for organic tea, but it keeps giving transaction failed. Payer details: user@upi address. Phone no is 9876543210. Please fix this.",
                "metadata": {"rating": 2, "reviewCreatedVersion": "4.2.1"}
            },
            {
                "source_id": "mock_3",
                "platform": "reddit",
                "timestamp": "2026-07-29T12:10:00",
                "author_anonymized": "RedditUser_ghi789",
                "raw_text": "Why do people only order groceries on Blinkit? I tried ordering electronics but they had no reviews or ratings. Trust issues are real.",
                "metadata": {"subreddit": "bangalore", "score": 15}
            }
        ]
        
    # 2. Sanitize and remove the unwanted keys from raw records
    sanitized_raw = sanitize_metadata_keys(all_raw)
    
    # Ensure data directory exists
    data_dir = PROJECT_ROOT / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Save raw reviews
    raw_path = data_dir / "raw_reviews.json"
    with open(raw_path, "w", encoding="utf-8") as f:
        json.dump(sanitized_raw, f, indent=2, ensure_ascii=False)
    print(f"✅ Stored {len(sanitized_raw)} raw reviews in {raw_path.relative_to(PROJECT_ROOT)}")
    
    # 3. Clean and normalize records
    cleaned_records = clean_and_normalize_records(sanitized_raw)
    
    # Save normalized reviews
    normalized_path = data_dir / "normalized_reviews.json"
    with open(normalized_path, "w", encoding="utf-8") as f:
        json.dump(cleaned_records, f, indent=2, ensure_ascii=False)
    print(f"✅ Stored {len(cleaned_records)} normalized reviews in {normalized_path.relative_to(PROJECT_ROOT)}")
    
    print("🎉 Pipeline Run Completed successfully.")

if __name__ == "__main__":
    run_ingestion_pipeline()
