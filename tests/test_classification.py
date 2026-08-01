import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.classification.cohort_classifier import CohortClassifier
from src.classification.opportunity_scorer import OpportunityScorer

def test_cohort_classification():
    classifier = CohortClassifier(confidence_threshold=0.55)
    
    # Convenience-first match
    segment, score = classifier.classify_review("The delivery was extremely fast and quick!")
    assert segment == "convenience_first"
    assert score >= 0.55
    
    # Price-sensitive match
    segment, score = classifier.classify_review("Too expensive pricing and handling charge is added.")
    assert segment == "price_sensitive"
    assert score >= 0.55
    
    # Trust-conscious match
    segment, score = classifier.classify_review("This is a scam. I want a refund for defective items.")
    assert segment == "trust_conscious"
    assert score >= 0.55
    
    # Exploratory match
    segment, score = classifier.classify_review("I like to try organic tea and explore home decor options.")
    assert segment == "exploratory_shopper"
    
    # Low-confidence fallback to Uncategorized
    # "ok" triggers no patterns, returns Uncategorized
    segment, score = classifier.classify_review("ok")
    assert segment == "Uncategorized"
    
    # Multi-category conflicting review triggers low confidence -> Uncategorized
    # "fast search buy rs return" triggers convenience, price, trust, mission
    segment, score = classifier.classify_review("fast search buy rs return")
    assert segment == "Uncategorized"

def test_opportunity_scorer():
    scorer = OpportunityScorer(confidence_threshold=0.55)
    
    # 2 sample clusters
    clusters = {
        "0": {
            "reviews": [
                {"cleaned_text": "worst app scam refund please.", "metadata": {"score": 1}, "platform": "play_store"},
                {"cleaned_text": "scam app defective item refund.", "metadata": {"score": 1}, "platform": "play_store"},
                {"cleaned_text": "slow app bad quality trust issue.", "metadata": {"score": 2}, "platform": "play_store"}
            ],
            "centroid_review": {"cleaned_text": "scam app defective item refund."}
        },
        "1": {
            "reviews": [
                {"cleaned_text": "nice app very fast delivery.", "metadata": {"score": 5}, "platform": "play_store"},
                {"cleaned_text": "convenient fast door step delivery.", "metadata": {"score": 5}, "platform": "play_store"}
            ],
            "centroid_review": {"cleaned_text": "nice app very fast delivery."}
        }
    }
    
    opp_matrix = scorer.compute_opportunity_matrix(clusters, total_records=5)
    
    # We should have 2 opportunity items returned
    assert len(opp_matrix) == 2
    
    # Cluster 0 should be ranked first because its reviews have much lower scores (ratings=1,2),
    # meaning higher pain severity, and larger reach (3/5 vs 2/5).
    assert opp_matrix[0]["theme_id"] == "0"
    assert opp_matrix[0]["opportunity_score"] > opp_matrix[1]["opportunity_score"]
    assert opp_matrix[0]["dominant_segment"] == "trust_conscious"
    assert opp_matrix[1]["dominant_segment"] == "convenience_first"
