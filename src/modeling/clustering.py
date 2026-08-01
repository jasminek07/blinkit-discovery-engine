import numpy as np
# pyrefly: ignore [missing-import]
import umap
# pyrefly: ignore [missing-import]
import hdbscan
from typing import List, Dict, Any, Tuple

def get_hdbscan_params(num_records: int) -> Tuple[int, int]:
    """
    Returns dynamic HDBSCAN hyperparameters based on dataset size.
    
    Args:
        num_records: The count of clean records (N).
        
    Returns:
        A tuple of (min_cluster_size, min_samples)
    """
    if num_records < 100:
        return 3, 1
    elif 100 <= num_records < 1000:
        return 10, 3
    else:
        return 15, 5

def perform_clustering(reviews: List[Dict[str, Any]], embeddings: List[List[float]]) -> Dict[str, Any]:
    """
    Performs UMAP dimension reduction and HDBSCAN clustering on review embeddings.
    
    Args:
        reviews: List of review dictionaries.
        embeddings: List of embedding vectors matching the reviews.
        
    Returns:
        Dictionary containing grouped clusters, noise records, and representative centroids.
    """
    N = len(reviews)
    
    # Boundary check: Not enough data points to perform meaningful clustering
    if N < 3:
        # All items are returned as a single cluster or noise
        return {
            "clusters": {
                "0": {
                    "theme_id": "0",
                    "reviews": reviews,
                    "centroid_review": reviews[0] if reviews else None,
                    "keyword_snippet": "Too few reviews to cluster"
                }
            },
            "noise": [],
            "stats": {"total_clusters": 1, "noise_count": 0, "total_records": N}
        }
        
    # Convert embeddings to 2D numpy array
    embedding_matrix = np.array(embeddings, dtype=np.float32)
    
    # 1. Dimension Reduction using UMAP
    # UMAP n_neighbors must satisfy: 2 <= n_neighbors < N
    n_neighbors = max(2, min(15, N - 1))
    
    try:
        # Project embeddings to 5-dimensional space
        reducer = umap.UMAP(
            n_neighbors=n_neighbors,
            n_components=5,
            metric="cosine",
            random_state=42
        )
        reduced_matrix = reducer.fit_transform(embedding_matrix)
    except Exception as e:
        print(f"UMAP reduction failed: {e}. Falling back to raw embeddings for clustering.")
        reduced_matrix = embedding_matrix
        
    # 2. Density Clustering using HDBSCAN
    min_cluster_size, min_samples = get_hdbscan_params(N)
    
    try:
        clusterer = hdbscan.HDBSCAN(
            min_cluster_size=min_cluster_size,
            min_samples=min_samples,
            metric="euclidean"
        )
        cluster_labels = clusterer.fit_predict(reduced_matrix)
    except Exception as e:
        print(f"HDBSCAN clustering failed: {e}. Labeling all records as noise.")
        cluster_labels = np.array([-1] * N)
        
    # 3. Organize Clusters, Noise, and Centroids
    clusters_dict = {}
    noise_list = []
    
    # Group review indices by cluster label
    labels_groups: Dict[int, List[int]] = {}
    for idx, label in enumerate(cluster_labels):
        if label == -1:
            noise_list.append(reviews[idx])
        else:
            if label not in labels_groups:
                labels_groups[label] = []
            labels_groups[label].append(idx)
            
    # Calculate Centroids in the UMAP space
    for label, indices in labels_groups.items():
        cluster_reviews = [reviews[idx] for idx in indices]
        
        # Calculate cluster centroid in UMAP space
        cluster_vectors = reduced_matrix[indices]
        mean_vector = np.mean(cluster_vectors, axis=0)
        
        # Find index closest to the mean vector (Euclidean distance)
        distances = np.linalg.norm(cluster_vectors - mean_vector, axis=1)
        closest_index = indices[np.argmin(distances)]
        centroid_review = reviews[closest_index]
        
        clusters_dict[str(label)] = {
            "theme_id": str(label),
            "reviews": cluster_reviews,
            "centroid_review": centroid_review,
            "size": len(cluster_reviews)
        }
        
    return {
        "clusters": clusters_dict,
        "noise": noise_list,
        "stats": {
            "total_clusters": len(clusters_dict),
            "noise_count": len(noise_list),
            "total_records": N
        }
    }
