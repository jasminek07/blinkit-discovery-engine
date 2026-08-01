import warnings
# pyrefly: ignore [missing-import]
from chromadb.utils import embedding_functions

def get_embedding_function():
    """
    Returns the local BAAI/bge-small-en-v1.5 embedding function.
    ChromaDB handles downloading and caching this model automatically.
    """
    return embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="BAAI/bge-small-en-v1.5"
    )
