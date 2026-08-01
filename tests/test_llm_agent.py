import sys
import time
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.llm_agent.groq_client import RateLimiter, GroqClient
from src.llm_agent.validator import (
    find_best_verbatim_match,
    validate_and_ground_quotes,
    calculate_theme_confidence
)
from src.llm_agent.synthesizer import prepare_cluster_prompt

def test_rate_limiter():
    # Test rate limiter restricts call frequency
    limiter = RateLimiter(requests_per_minute=60) # 1.0s delay
    start_time = time.time()
    limiter.wait()
    limiter.wait()
    end_time = time.time()
    elapsed = end_time - start_time
    assert elapsed >= 0.9  # delay is around 1s

def test_find_best_verbatim_match():
    original_reviews = [
        {"source_id": "1", "cleaned_text": "Blinkit delivery is incredibly fast and convenient.", "platform": "play_store"},
        {"source_id": "2", "cleaned_text": "Price of organic milk is too high here.", "platform": "app_store"},
    ]
    
    # Slight typo or truncation in LLM quote
    hallucinated = "Blinkit delivery is incredibly fast"
    match = find_best_verbatim_match(hallucinated, original_reviews)
    assert match is not None
    assert match["source_id"] == "1"
    assert match["cleaned_text"] == "Blinkit delivery is incredibly fast and convenient."

def test_validate_and_ground_quotes():
    original_reviews = [
        {"source_id": "1", "cleaned_text": "Blinkit delivery is incredibly fast and convenient.", "platform": "play_store", "timestamp": "2026-07-29T10:00:00"},
        {"source_id": "2", "cleaned_text": "Price of organic milk is too high here.", "platform": "app_store", "timestamp": "2026-07-29T10:05:00"},
    ]
    
    # Mock LLM insight with modified/hallucinated quotes
    llm_insight = {
        "theme_name": "Test Theme",
        "supporting_quotes": [
            # Direct match
            {"text": "Price of organic milk is too high here."},
            # Modified quote (needs grounding)
            {"text": "Blinkit delivery is fast"}
        ]
    }
    
    grounded = validate_and_ground_quotes(llm_insight, original_reviews)
    
    quotes = grounded["supporting_quotes"]
    assert len(quotes) == 2
    
    # Verify both are converted to their verbatim equivalents
    assert quotes[0]["text"] == "Price of organic milk is too high here."
    assert quotes[0]["source_platform"] == "app_store"
    
    assert quotes[1]["text"] == "Blinkit delivery is incredibly fast and convenient."
    assert quotes[1]["source_platform"] == "play_store"

def test_calculate_theme_confidence():
    # Large multi-platform cluster
    reviews_large = []
    for i in range(40):
        reviews_large.append({"platform": "play_store" if i % 2 == 0 else "app_store"})
    reviews_large.append({"platform": "reddit"})
    
    # Small single-platform cluster
    reviews_small = [{"platform": "play_store"}, {"platform": "play_store"}]
    
    score_large = calculate_theme_confidence(reviews_large, avg_distance=0.1)
    score_small = calculate_theme_confidence(reviews_small, avg_distance=0.6)
    
    assert score_large > score_small
    assert 0.0 <= score_large <= 1.0
    assert 0.0 <= score_small <= 1.0

def test_prepare_cluster_prompt_capping():
    # Generate 30 dummy reviews
    reviews = [{"cleaned_text": f"Review {i}", "platform": "play", "timestamp": ""} for i in range(30)]
    prompt_str = prepare_cluster_prompt("0", reviews)
    import json
    prompt_dict = json.loads(prompt_str)
    
    # Check that it has been capped/budgeted to 20
    assert len(prompt_dict["sampled_reviews"]) == 20
    assert prompt_dict["total_reviews_in_cluster"] == 30
