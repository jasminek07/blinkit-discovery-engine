import sys
import numpy as np
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.modeling.clustering import get_hdbscan_params, perform_clustering

def test_hdbscan_params():
    # Test boundary limits
    assert get_hdbscan_params(50) == (3, 1)      # Small
    assert get_hdbscan_params(150) == (10, 3)    # Medium
    assert get_hdbscan_params(1500) == (15, 5)   # Large

def test_clustering_with_insufficient_data():
    reviews = [
        {"source_id": "1", "cleaned_text": "First comment."},
        {"source_id": "2", "cleaned_text": "Second comment."}
    ]
    embeddings = [[0.1] * 384, [0.2] * 384]
    
    result = perform_clustering(reviews, embeddings)
    assert result["stats"]["total_clusters"] == 1
    assert result["stats"]["total_records"] == 2
    assert len(result["clusters"]["0"]["reviews"]) == 2

def test_clustering_normal_flow():
    # We will generate 20 dummy reviews with 2 clear semantic groups (embeddings)
    reviews = []
    embeddings = []
    
    # Group A: centered around [0.1, 0.1]
    for i in range(10):
        reviews.append({
            "source_id": f"group_A_{i}",
            "cleaned_text": f"This is review group A number {i}"
        })
        # Mock embeddings with small random offset
        offset = np.random.normal(0, 0.01, 128)
        vector = np.concatenate([np.array([0.9]*64) + offset[:64], np.array([0.0]*64) + offset[64:]])
        embeddings.append(vector.tolist())
        
    # Group B: centered around [0.0, 0.9]
    for i in range(10):
        reviews.append({
            "source_id": f"group_B_{i}",
            "cleaned_text": f"This is review group B number {i}"
        })
        # Mock embeddings
        offset = np.random.normal(0, 0.01, 128)
        vector = np.concatenate([np.array([0.0]*64) + offset[:64], np.array([0.9]*64) + offset[64:]])
        embeddings.append(vector.tolist())
        
    result = perform_clustering(reviews, embeddings)
    
    # Verify stats
    assert result["stats"]["total_records"] == 20
    assert "clusters" in result
    assert "noise" in result
    
    # Check that clusters are formed
    assert result["stats"]["total_clusters"] >= 1
    
    for label, cluster in result["clusters"].items():
        assert "theme_id" in cluster
        assert "reviews" in cluster
        assert "centroid_review" in cluster
        assert len(cluster["reviews"]) > 0
        
        # Verify centroid is part of the cluster's reviews
        centroid_id = cluster["centroid_review"]["source_id"]
        review_ids = [r["source_id"] for r in cluster["reviews"]]
        assert centroid_id in review_ids
