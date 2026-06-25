import os
import logging
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient

logger = logging.getLogger(__name__)

class VectorService:
    def __init__(self):
        self.qdrant_url = os.getenv("QDRANT_URL", "http://qdrant:6333")
        self.collection_name = "uphill_athlete_materials"
        self.embeddings = None
        self.vector_store = None
        self._initialize()

    def _initialize(self):
        try:
            logger.info("Initializing Google Gemini Embeddings (gemini-embedding-2)...")
            self.embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-2")
            logger.info(f"Connecting to Qdrant at {self.qdrant_url}...")
            client = QdrantClient(url=self.qdrant_url)
            
            # We don't create the collection here, just connect to it
            self.vector_store = QdrantVectorStore(
                client=client,
                collection_name=self.collection_name,
                embedding=self.embeddings,
            )
            logger.info("Successfully connected to Qdrant Vector Store.")
        except Exception as e:
            logger.error(f"Failed to initialize VectorService: {e}")

    def semantic_search(self, query: str, k: int = 5, collection_name: str = None):
        """
        Search the vector database for the top k most relevant documents.
        Returns a formatted string of context or an empty string if failed.
        """
        target_collection = collection_name or self.collection_name
        
        try:
            logger.info(f"Performing semantic search for: '{query}' in {target_collection} (k={k})")
            
            client = QdrantClient(url=self.qdrant_url)
            store = QdrantVectorStore(
                client=client,
                collection_name=target_collection,
                embedding=self.embeddings,
            )
            
            docs = store.similarity_search(query, k=k)
            
            if not docs:
                return ""
                
            context_parts = []
            for idx, doc in enumerate(docs, 1):
                source = doc.metadata.get('source', 'Unknown Source')
                truncated_content = doc.page_content.strip()
                context_parts.append(
                    f"[Document #{idx}] Source: {source}\n"
                    f"Content: {truncated_content}"
                )
            
            return (
                "\n\n=== GROUNDING REFERENCE DATABASE (RAG) ===\n" +
                "\n\n".join(context_parts) +
                "\n=========================================\n"
            )
            
        except Exception as e:
            logger.error(f"Error during semantic search: {e}")
            return ""

vector_service = VectorService()


def get_qdrant_client():
    return vector_service.vector_store.client
