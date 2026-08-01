import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.ingestion.cleaner import (
    clean_text_formatting,
    scrub_pii,
    is_english_or_hinglish,
    clean_and_normalize_records
)
from src.ingestion.play_store import fetch_play_store_reviews
from src.ingestion.app_store import fetch_app_store_reviews
from src.ingestion.reddit import fetch_reddit_discussions

def test_clean_text_formatting():
    # Test HTML removal
    html_text = "<p>Blinkit app is <b>great</b>!</p>"
    assert clean_text_formatting(html_text) == "Blinkit app is great!"
    
    # Test URL replacement
    url_text = "Check this out https://google.com/test website"
    assert clean_text_formatting(url_text) == "Check this out [URL] website"

def test_scrub_pii():
    # Test Email redaction
    email_text = "Contact me at user@example.com for queries"
    assert "user@example.com" not in scrub_pii(email_text)
    assert "[EMAIL_REDACTED]" in scrub_pii(email_text)
    
    # Test Phone Number redaction
    phone_text = "My phone number is +91 9876543210 or 8765432109"
    sanitized = scrub_pii(phone_text)
    assert "9876543210" not in sanitized
    assert "8765432109" not in sanitized
    assert "[PHONE_REDACTED]" in sanitized

    # Test Aadhaar Card redaction
    aadhaar_text = "Aadhaar: 1234 5678 9012"
    assert "[AADHAAR_REDACTED]" in scrub_pii(aadhaar_text)

    # Test PAN Card redaction
    pan_text = "My PAN number is ABCDE1234F"
    assert "[PAN_REDACTED]" in scrub_pii(pan_text)

    # Test UPI ID redaction
    upi_text = "Send money to receiver@upi address"
    assert "[UPI_REDACTED]" in scrub_pii(upi_text)

def test_is_english_or_hinglish():
    # English: should pass
    assert is_english_or_hinglish("This is a standard review in English language.") is True
    
    # Hinglish (Romanized): should pass
    assert is_english_or_hinglish("App bohot acha chal raha hai delivery fast hai.") is True
    
    # Devanagari script: should fail
    assert is_english_or_hinglish("यह एक हिंदी समीक्षा है।") is False
    
    # Chinese/non-latin: should fail
    assert is_english_or_hinglish("这是一个中文评论。") is False

def test_clean_and_normalize_records():
    raw_records = [
        # Standard record - valid
        {
            "source_id": "1",
            "raw_text": "Blinkit service is very quick and convenient today.",
            "platform": "play_store"
        },
        # Short comment - should be filtered
        {
            "source_id": "2",
            "raw_text": "nice app",
            "platform": "play_store"
        },
        # Non-English/Hinglish (Devanagari) - should be filtered
        {
            "source_id": "3",
            "raw_text": "डिलिवरी लेट है बहुत गुस्सा आया।",
            "platform": "app_store"
        },
        # Duplicate review - should be filtered
        {
            "source_id": "4",
            "raw_text": "Blinkit service is very quick and convenient today.",
            "platform": "reddit"
        },
        # Record with PII - should be cleaned
        {
            "source_id": "5",
            "raw_text": "Call me at +91 9999999999 to resolve order issues.",
            "platform": "play_store"
        }
    ]
    
    cleaned = clean_and_normalize_records(raw_records)
    
    # Out of 5 records, 2 should remain (record 1, and record 5 with sanitized text)
    # Record 2 is too short, Record 3 is Devanagari, Record 4 is duplicate of Record 1.
    assert len(cleaned) == 2
    
    # Check that raw_text is removed and cleaned_text is present
    assert "raw_text" not in cleaned[0]
    assert "cleaned_text" in cleaned[0]
    assert cleaned[0]["cleaned_text"] == "Blinkit service is very quick and convenient today."
    
    # Check that record 5 PII is scrubbed
    assert "[PHONE_REDACTED]" in cleaned[1]["cleaned_text"]
    assert "9999999999" not in cleaned[1]["cleaned_text"]

def test_scrapers_initialization():
    """Verify that scrapers return list structures and handle dummy values gracefully."""
    # Play Store - should return empty list or reviews list depending on network
    play_reviews = fetch_play_store_reviews(app_id="com.grofers.customerapp", count=2)
    assert isinstance(play_reviews, list)
    
    # App Store - should return empty list or reviews list depending on network
    app_reviews = fetch_app_store_reviews(app_name="blinkit", app_id=962453676, count=2)
    assert isinstance(app_reviews, list)

    # Reddit - should return empty list with dummy credentials
    reddit_reviews = fetch_reddit_discussions(subreddits=["india"], count=2)
    assert isinstance(reddit_reviews, list)
    assert len(reddit_reviews) == 0  # because dummy settings are active

def test_pipeline_file_generation():
    """Verify that raw and normalized reviews files exist and do not contain unwanted metadata keys."""
    import json
    from src.ingestion.run_ingestion import KEYS_TO_REMOVE
    
    raw_path = PROJECT_ROOT / "data" / "raw_reviews.json"
    normalized_path = PROJECT_ROOT / "data" / "normalized_reviews.json"
    
    assert raw_path.exists()
    assert normalized_path.exists()
    
    # Check raw reviews schema
    with open(raw_path, "r", encoding="utf-8") as f:
        raw_data = json.load(f)
    assert isinstance(raw_data, list)
    if len(raw_data) > 0:
        for rec in raw_data:
            # Check root level keys
            for key in KEYS_TO_REMOVE:
                assert key not in rec
            # Check metadata level keys
            metadata = rec.get("metadata", {})
            for key in KEYS_TO_REMOVE:
                assert key not in metadata
                
    # Check normalized reviews schema
    with open(normalized_path, "r", encoding="utf-8") as f:
        normalized_data = json.load(f)
    assert isinstance(normalized_data, list)
    if len(normalized_data) > 0:
        for rec in normalized_data:
            # Check root level keys
            for key in KEYS_TO_REMOVE:
                assert key not in rec
            # Check metadata level keys
            metadata = rec.get("metadata", {})
            for key in KEYS_TO_REMOVE:
                assert key not in metadata

