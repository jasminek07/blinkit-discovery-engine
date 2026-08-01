import hashlib
from datetime import datetime
from typing import List, Dict, Any
from google_play_scraper import reviews, Sort

def anonymize_author(author_name: str) -> str:
    """Anonymizes author names using MD5 hashing to protect privacy."""
    if not author_name:
        return "Anonymized_User"
    return f"PlayStoreUser_{hashlib.md5(author_name.encode('utf-8')).hexdigest()[:8]}"

def fetch_play_store_reviews(app_id: str = "com.grofers.customerapp", count: int = 5000) -> List[Dict[str, Any]]:
    """
    Fetches reviews for a given Google Play Store application from the past 3 months and normalizes them.
    
    Args:
        app_id: The Android application package name (default: Blinkit app id).
        count: Hard safety limit on the number of reviews to download.
        
    Returns:
        List of normalized review dictionaries.
    """
    from datetime import datetime, timedelta
    
    cutoff_date = datetime.now() - timedelta(days=90)
    normalized_reviews = []
    continuation_token = None
    
    print(f"Fetching Play Store reviews newer than {cutoff_date.isoformat()}...")
    
    try:
        while True:
            if continuation_token:
                result, continuation_token = reviews(
                    app_id,
                    continuation_token=continuation_token
                )
            else:
                result, continuation_token = reviews(
                    app_id,
                    lang='en',
                    country='in',
                    sort=Sort.NEWEST,
                    count=200
                )
            
            if not result:
                break
                
            reached_cutoff = False
            for review in result:
                at_datetime = review.get("at")
                
                # Halt if review is older than 90 days (3 months)
                if isinstance(at_datetime, datetime) and at_datetime < cutoff_date:
                    reached_cutoff = True
                    break
                    
                review_id = review.get("reviewId", "")
                author_name = review.get("userName", "")
                content = review.get("content", "")
                
                timestamp_str = datetime.now().isoformat()
                if isinstance(at_datetime, datetime):
                    timestamp_str = at_datetime.isoformat()
                
                normalized_reviews.append({
                    "source_id": review_id,
                    "platform": "play_store",
                    "timestamp": timestamp_str,
                    "author_anonymized": anonymize_author(author_name),
                    "raw_text": content,
                    "metadata": {
                        "score": review.get("score"),
                        "thumbs_up_count": review.get("thumbsUpCount"),
                        "app_version": review.get("reviewCreatedVersion")
                    }
                })
                
            if reached_cutoff or not continuation_token:
                break
                
            if len(normalized_reviews) >= count:
                break
                
    except Exception as e:
        print(f"Error fetching Play Store reviews for {app_id}: {e}")
        
    return normalized_reviews
