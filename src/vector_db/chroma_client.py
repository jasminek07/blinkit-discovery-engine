# pyrefly: ignore [missing-import]
import chromadb
from typing import List, Dict, Any
from src.config import settings
from src.vector_db.embeddings import get_embedding_function

def flatten_metadata(review: Dict[str, Any]) -> Dict[str, Any]:
    """Flattens nested review dictionaries into a single-level metadata dictionary for ChromaDB."""
    flat_meta = {
        "source_id": review.get("source_id", ""),
        "platform": review.get("platform", ""),
        "timestamp": review.get("timestamp", ""),
        "author_anonymized": review.get("author_anonymized", "")
    }
    
    # Extract any fields from nested metadata dictionary
    meta_dict = review.get("metadata", {})
    if isinstance(meta_dict, dict):
        for k, v in meta_dict.items():
            # ChromaDB only accepts simple types: str, int, float, bool
            if isinstance(v, (str, int, float, bool)):
                flat_meta[f"meta_{k}"] = v
                
    return flat_meta

class ChromaVectorStore:
    """Manages connection, ingestion, and querying against ChromaDB vector index."""
    def __init__(self, collection_name: str = "blinkit_user_reviews"):
        # Set up persistent database client
        self.client = chromadb.PersistentClient(path=settings.chroma_db_path)
        self.embedding_fn = get_embedding_function()
        
        # Get or create the vector collection with Cosine Distance metric
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.embedding_fn,
            metadata={"hnsw:space": "cosine"}
        )

    def add_reviews(self, reviews: List[Dict[str, Any]]):
        """Ingests clean reviews, generating embeddings and storing associated metadata tags."""
        if not reviews:
            return
            
        ids = []
        documents = []
        metadatas = []
        
        for review in reviews:
            source_id = review.get("source_id", "")
            cleaned_text = review.get("cleaned_text", "")
            
            if not source_id or not cleaned_text:
                continue
                
            ids.append(source_id)
            documents.append(cleaned_text)
            metadatas.append(flatten_metadata(review))
            
        if ids:
            self.collection.add(
                ids=ids,
                documents=documents,
                metadatas=metadatas
            )

    def query_reviews(self, query_text: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Queries the vector index for semantic similarity using cosine distance."""
        results = self.collection.query(
            query_texts=[query_text],
            n_results=limit
        )
        
        reconstructed = []
        if results and results.get("ids") and len(results["ids"][0]) > 0:
            for idx in range(len(results["ids"][0])):
                doc_id = results["ids"][0][idx]
                doc_text = results["documents"][0][idx]
                doc_meta = results["metadatas"][0][idx]
                distance = results["distances"][0][idx] if "distances" in results else None
                
                # Unpack meta_ variables back to sub-metadata
                metadata = {}
                main_fields = {}
                for k, v in doc_meta.items():
                    if k.startswith("meta_"):
                        metadata[k[5:]] = v
                    else:
                        main_fields[k] = v
                        
                reconstructed.append({
                    "source_id": doc_id,
                    "cleaned_text": doc_text,
                    "platform": main_fields.get("platform", ""),
                    "timestamp": main_fields.get("timestamp", ""),
                    "author_anonymized": main_fields.get("author_anonymized", ""),
                    "metadata": metadata,
                    "distance": distance
                })
                
        return reconstructed

    def get_all_reviews(self) -> List[Dict[str, Any]]:
        """Returns all reviews stored in the vector database."""
        results = self.collection.get()
        reconstructed = []
        
        if results and results.get("ids"):
            for idx in range(len(results["ids"])):
                doc_id = results["ids"][idx]
                doc_text = results["documents"][idx]
                doc_meta = results["metadatas"][idx]
                
                metadata = {}
                main_fields = {}
                for k, v in doc_meta.items():
                    if k.startswith("meta_"):
                        metadata[k[5:]] = v
                    else:
                        main_fields[k] = v
                        
                reconstructed.append({
                    "source_id": doc_id,
                    "cleaned_text": doc_text,
                    "platform": main_fields.get("platform", ""),
                    "timestamp": main_fields.get("timestamp", ""),
                    "author_anonymized": main_fields.get("author_anonymized", ""),
                    "metadata": metadata
                })
                
        return reconstructed

    def reset_database(self):
        """Clears all records by deleting and recreating the collection."""
        try:
            self.client.delete_collection(self.collection.name)
        except Exception:
            pass
        self.collection = self.client.get_or_create_collection(
            name=self.collection.name,
            embedding_function=self.embedding_fn,
            metadata={"hnsw:space": "cosine"}
        )
