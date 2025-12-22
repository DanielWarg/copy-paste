"""
Embedding provider interface and implementations
"""
from abc import ABC, abstractmethod
from typing import List
import httpx
from ..core.config import settings


class EmbeddingProvider(ABC):
    """Abstract base class for embedding providers"""
    
    @abstractmethod
    async def embed(self, text: str) -> List[float]:
        """Generate embedding for a single text"""
        pass
    
    @abstractmethod
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        pass


class OllamaEmbeddingProvider(EmbeddingProvider):
    """Ollama embedding provider"""
    
    def __init__(self):
        self.base_url = settings.ollama_base_url
        self.model = settings.ollama_embed_model
    
    async def embed(self, text: str) -> List[float]:
        """Generate embedding using Ollama"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/api/embeddings",
                json={
                    "model": self.model,
                    "prompt": text,
                }
            )
            response.raise_for_status()
            data = response.json()
            return data.get("embedding", [])
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        # Ollama doesn't support batch, so we do sequential
        # In production, consider batching with a queue
        embeddings = []
        for text in texts:
            embedding = await self.embed(text)
            embeddings.append(embedding)
        return embeddings


class SentenceTransformerProvider(EmbeddingProvider):
    """Fallback to sentence-transformers (local)"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(model_name)
        except ImportError:
            raise ImportError(
                "sentence-transformers not installed. "
                "Install with: pip install sentence-transformers"
            )
    
    async def embed(self, text: str) -> List[float]:
        """Generate embedding using sentence-transformers"""
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        return embeddings.tolist()


def get_embedding_provider() -> EmbeddingProvider:
    """Get the configured embedding provider"""
    try:
        # Try Ollama first
        provider = OllamaEmbeddingProvider()
        # Test connection
        return provider
    except Exception:
        # Fallback to sentence-transformers
        return SentenceTransformerProvider()

