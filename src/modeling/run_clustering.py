import os
import sys
import json
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.vector_db.chroma_client import ChromaVectorStore
from src.modeling.clustering import perform_clustering

def run_clustering_on_dataset():
    print("🔮 Starting Vector DB Ingestion & Clustering Execution...")
    
    # 1. Load normalized reviews from disk
    normalized_path = PROJECT_ROOT / "data" / "normalized_reviews.json"
    if not normalized_path.exists():
        print(f"❌ Error: Normalized reviews file not found at {normalized_path}. Please run Phase 2 Ingestion first.")
        sys.exit(1)
        
    with open(normalized_path, "r", encoding="utf-8") as f:
        reviews = json.load(f)
        
    print(f"Loaded {len(reviews)} normalized reviews from disk.")
    if len(reviews) == 0:
        print("⚠️ Warning: Normalized reviews dataset is empty. Cannot run clustering.")
        return
        
    # 2. Ingest into Chroma Vector Database
    print("Connecting to ChromaDB and generating local BGE-small embeddings...")
    store = ChromaVectorStore(collection_name="blinkit_live_reviews")
    store.reset_database()
    
    store.add_reviews(reviews)
    print(f"Successfully ingested {len(reviews)} reviews into vector DB.")
    
    # 3. Retrieve documents and embeddings
    # Chroma get() method can return embeddings if requested
    get_results = store.collection.get(include=["embeddings", "documents", "metadatas"])
    
    ids = get_results.get("ids", [])
    embeddings = get_results.get("embeddings", [])
    documents = get_results.get("documents", [])
    metadatas = get_results.get("metadatas", [])
    
    if embeddings is None or len(embeddings) == 0:
        print("❌ Error: Failed to retrieve embeddings from ChromaDB. Make sure sentence-transformers is running correctly.")
        sys.exit(1)
        
    # Reconstruct review structures with retrieved items
    retrieved_reviews = []
    for idx in range(len(ids)):
        doc_meta = metadatas[idx]
        
        # Reconstruct metadata dict
        meta_dict = {}
        main_fields = {}
        for k, v in doc_meta.items():
            if k.startswith("meta_"):
                meta_dict[k[5:]] = v
            else:
                main_fields[k] = v
                
        retrieved_reviews.append({
            "source_id": ids[idx],
            "cleaned_text": documents[idx],
            "platform": main_fields.get("platform", ""),
            "timestamp": main_fields.get("timestamp", ""),
            "author_anonymized": main_fields.get("author_anonymized", ""),
            "metadata": meta_dict
        })
        
    # 4. Perform Clustering
    print("Running UMAP dimensionality reduction & HDBSCAN density clustering...")
    clustering_results = perform_clustering(retrieved_reviews, embeddings)
    
    # 5. Output results
    stats = clustering_results["stats"]
    print("\n================ CLUSTERING STATISTICS ================")
    print(f"Total reviews processed  : {stats['total_records']}")
    print(f"Identified Clusters     : {stats['total_clusters']}")
    print(f"Noise reviews (outliers): {stats['noise_count']}")
    print("========================================================\n")
    
    # Detail each cluster
    for label, cluster in clustering_results["clusters"].items():
        print(f"📁 [Cluster/Theme ID: {label}] (Size: {cluster['size']} reviews)")
        print(f"📌 Centroid / Representative Review:")
        print(f"   \"{cluster['centroid_review']['cleaned_text']}\"")
        print("📝 Member Reviews:")
        for idx, r in enumerate(cluster["reviews"][:3]):
            print(f"   {idx+1}. [{r['platform'].upper()}] \"{r['cleaned_text']}\"")
        if cluster['size'] > 3:
            print(f"   ... and {cluster['size'] - 3} more reviews.")
        print("-" * 56)
        
    # Detail noise
    if clustering_results["noise"]:
        print(f"⚠️ [Noise/Outliers] (Size: {len(clustering_results['noise'])} reviews)")
        for idx, r in enumerate(clustering_results["noise"][:5]):
            print(f"   * [{r['platform'].upper()}] \"{r['cleaned_text']}\"")
        if len(clustering_results["noise"]) > 5:
            print(f"   ... and {len(clustering_results['noise']) - 5} more outlier reviews.")

if __name__ == "__main__":
    run_clustering_on_dataset()
