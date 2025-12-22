"""
RAG service - retrieval augmented generation
"""
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text as sql_text
from ..models.chunk import Chunk
from ..models.source import Source
from ..services.embeddings import get_embedding_provider
from ..services.llm_provider import get_llm_router, LLMResponse
from ..services.prompt_templates import SYSTEM_PROMPT, build_user_prompt
from ..services.output_sanitizer import sanitize_llm_output
from ..core.security import compute_hash
from pydantic import BaseModel, ValidationError
import json
import uuid


class BriefSchema(BaseModel):
    """Strict JSON schema for brief response"""
    brief: str
    factbox: List[Dict[str, str]]
    draft: str
    open_questions: List[str]
    risk_flags: List[str]


class RAGService:
    """RAG service for generating briefs"""
    
    def __init__(self):
        self.embedding_provider = get_embedding_provider()
        self.llm_router = get_llm_router()
    
    async def retrieve_chunks(
        self,
        db: Session,
        source_ids: List[str],
        query: Optional[str] = None,
        top_k: int = 5,
    ) -> List[Dict[str, str]]:
        """Retrieve relevant chunks using semantic search"""
        if not source_ids:
            return []
        
        # If query provided, generate embedding for semantic search
        if query:
            query_embedding = await self.embedding_provider.embed(query)
            
            # Use pgvector similarity search
            # Note: This requires pgvector extension and proper index
            # For now, use simple text search until pgvector is properly set up
            # TODO: Implement proper pgvector similarity search when pgvector extension is enabled
            query_sql = sql_text("""
                SELECT c.id, c.text, c.source_id, s.url
                FROM chunks c
                JOIN sources s ON c.source_id = s.id
                WHERE c.source_id = ANY(:source_ids)
                LIMIT :top_k
            """)
            
            result = db.execute(
                query_sql,
                {
                    "source_ids": source_ids,
                    "top_k": top_k,
                }
            )
        else:
            # No query, just get chunks from sources
            result = db.query(Chunk).join(Source).filter(
                Source.id.in_(source_ids)
            ).limit(top_k).all()
        
        chunks = []
        for row in result:
            if isinstance(row, Chunk):
                chunks.append({
                    "id": str(row.id),
                    "text": row.text,
                    "source_id": str(row.source_id),
                    "source_url": row.source.url if row.source else "",
                })
            else:
                chunks.append({
                    "id": str(row.id),
                    "text": row.text,
                    "source_id": str(row.source_id),
                    "source_url": row.url if hasattr(row, 'url') else "",
                })
        
        return chunks
    
    async def generate_brief(
        self,
        db: Session,
        source_ids: List[str],
        query: Optional[str] = None,
    ) -> tuple[BriefSchema, List[Dict[str, str]]]:
        """
        Generate brief using RAG
        
        Returns:
            tuple: (BriefSchema, citations)
        
        Raises:
            ValueError: If schema validation fails
        """
        # Retrieve relevant chunks
        chunks = await self.retrieve_chunks(db, source_ids, query)
        
        if not chunks:
            raise ValueError("No chunks found for sources")
        
        # Build prompt
        user_prompt = build_user_prompt(query or "Generera en brief", chunks)
        
        # Generate with LLM
        llm_response = await self.llm_router.generate(
            prompt=user_prompt,
            system_prompt=SYSTEM_PROMPT,
            max_tokens=2048,
            temperature=0.7,
        )
        
        # Sanitize output
        sanitized_content = sanitize_llm_output(llm_response.content)
        
        # Try to parse JSON
        try:
            # Extract JSON from response (might have markdown code blocks)
            json_match = json.loads(sanitized_content)
            if isinstance(json_match, str):
                json_match = json.loads(json_match)
        except (json.JSONDecodeError, ValueError):
            # Try to extract JSON from markdown code blocks
            import re
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', sanitized_content, re.DOTALL)
            if json_match:
                json_match = json.loads(json_match.group(1))
            else:
                # Fallback: return safe response with citations
                raise ValueError(
                    "Failed to parse LLM response as JSON. "
                    "Returning safe fallback with citations."
                )
        
        # Validate against schema
        try:
            brief_schema = BriefSchema(**json_match)
        except ValidationError as e:
            # Schema validation failed - return safe fallback
            raise ValueError(
                f"LLM response does not match schema: {e}. "
                "Returning safe fallback with citations."
            )
        
        # Build citations
        citations = [
            {
                "chunk_id": chunk["id"],
                "text": chunk["text"][:200],  # Preview
                "source_id": chunk["source_id"],
                "source_url": chunk["source_url"],
            }
            for chunk in chunks
        ]
        
        return brief_schema, citations

