"""
LLM provider interface and implementations
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from pydantic import BaseModel
import httpx
from ..core.config import settings


class LLMResponse(BaseModel):
    """Structured LLM response"""
    content: str
    model: str
    usage: Optional[Dict[str, int]] = None


class LLMProvider(ABC):
    """Abstract base class for LLM providers"""
    
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
    ) -> LLMResponse:
        """Generate text from prompt"""
        pass


class LocalOllamaProvider(LLMProvider):
    """Local Ollama provider"""
    
    def __init__(self):
        self.base_url = settings.ollama_base_url
        self.model = settings.ollama_llm_model
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
    ) -> LLMResponse:
        """Generate text using Ollama"""
        # Validate Ollama URL is local
        if not self.base_url.startswith(("http://localhost", "http://127.0.0.1", "http://ollama", "http://host.docker.internal")):
            raise ValueError(
                f"Remote Ollama URLs blocked for security: {self.base_url}. "
                "Ollama has no auth locally."
            )
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": messages,
                    "options": {
                        "temperature": temperature,
                        "num_predict": max_tokens or 2048,
                    },
                    "stream": False,
                }
            )
            response.raise_for_status()
            data = response.json()
            
            return LLMResponse(
                content=data.get("message", {}).get("content", ""),
                model=self.model,
                usage=data.get("usage"),
            )


class CloudProviderStub(LLMProvider):
    """Cloud provider stub (disabled by default)"""
    
    def __init__(self):
        self.enabled = False
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
    ) -> LLMResponse:
        """Cloud provider (disabled)"""
        raise NotImplementedError(
            "Cloud provider is disabled. "
            "Enable by setting CLOUD_LLM_ENABLED=true and configuring cloud credentials."
        )


class LLMRouter:
    """Router for switching between LLM providers"""
    
    def __init__(self):
        self.local_provider = LocalOllamaProvider()
        self.cloud_provider = CloudProviderStub()
        self.default_provider = self.local_provider
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        use_cloud: bool = False,
    ) -> LLMResponse:
        """Route to appropriate provider"""
        if use_cloud and self.cloud_provider.enabled:
            return await self.cloud_provider.generate(
                prompt, system_prompt, max_tokens, temperature
            )
        else:
            return await self.default_provider.generate(
                prompt, system_prompt, max_tokens, temperature
            )


def get_llm_router() -> LLMRouter:
    """Get the configured LLM router"""
    return LLMRouter()

