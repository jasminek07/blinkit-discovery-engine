import hashlib
from datetime import datetime
from typing import List, Dict, Any
from app_store_scraper import AppStore

def anonymize_author(author_name: str) -> str:
    """Anonymizes Apple App Store author names to maintain privacy."""
    if not author_name:
        return "Anonymized_User"
    return f"AppStoreUser_{hashlib.md5(author_name.encode('utf-8')).hexdigest()[:8]}"

def fetch_app_store_reviews(app_name: str = "blinkit", app_id: int = 962453676, count: int = 100) -> List[Dict[str, Any]]:
    """
    Fetches customer reviews for an Apple App Store application and normalizes them.
    
    Args:
        app_name: The name of the application on iOS App Store.
        app_id: The application ID (default: Blinkit app id).
        count: Number of reviews to fetch.
        
    Returns:
        List of normalized review dictionaries.
    """
    normalized_reviews = []
    try:
        # Initialize the AppStore client
        store = AppStore(country="in", app_name=app_name, app_id=app_id)
        # Fetch reviews
        store.review(how_many=count)
        
        for review in store.reviews:
            author_name = review.get("userName", "")
            title = review.get("title", "")
            comment = review.get("review", "")
            date_val = review.get("date")
            
            # Combine Title and Comment for richer contextual text representation
            full_text = f"{title}. {comment}" if title else comment
            
            # Format timestamp
            timestamp_str = datetime.now().isoformat()
            if isinstance(date_val, datetime):
                timestamp_str = date_val.isoformat()
            
            # Create a unique ID using the author hash and timestamp
            source_id = hashlib.md5(f"{author_name}_{timestamp_str}".encode('utf-8')).hexdigest()
            
            normalized_reviews.append({
                "source_id": source_id,
                "platform": "app_store",
                "timestamp": timestamp_str,
                "author_anonymized": anonymize_author(author_name),
                "raw_text": full_text,
                "metadata": {
                    "rating": review.get("rating"),
                    "is_edited": review.get("isEdited", False),
                    "title": title
                }
            })
    except Exception as e:
        print(f"Error fetching App Store reviews for {app_name}: {e}")
        # In case of API rate limits or errors, return an empty list
        return []
        
    return normalized_reviews
