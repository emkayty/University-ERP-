"""
ML Search API - Django Ninja Endpoint.
Phase 1 Module 07.
"""

import time
import logging

from ninja import NinjaAPI, Schema, Query
from typing import Optional

logger = logging.getLogger(__name__)

api = NinjaAPI()


class SearchRequest(Schema):
    """Semantic search request."""
    query: str
    top_k: int = 10


class SearchResultItem(Schema):
    """Individual search result."""
    id: int
    code: str
    title: str
    department: str
    faculty: Optional[str] = None
    similarity: Optional[float] = None
    score: Optional[float] = None


class SearchResponse(Schema):
    """Search response."""
    results: list[SearchResultItem]
    total: int
    execution_time_ms: int
    search_type: str


@api.post("/search/semantic/", response=SearchResponse)
def semantic_course_search(
    request: SearchRequest,
    tenant_id: str = Query(..., description="Tenant slug"),
):
    """
    Hybrid semantic + full-text course search.
    
    Uses sentence-transformers/all-MiniLM-L6-v2 embeddings
    combined with pgvector cosine similarity
    and PostgreSQL full-text search.
    Results re-ranked via Reciprocal Rank Fusion.
    """
    start_time = time.time()
    
    try:
        from apps.ml.search.services import semantic_course_search, embed_query
        
        # Check if embeddings are available
        query_embedding = embed_query(request.query)
        search_type = "hybrid" if query_embedding else "fulltext"
        
        # Perform search
        results = semantic_course_search(
            query=request.query,
            tenant_id=tenant_id,
            top_k=request.top_k,
        )
        
        execution_time = int((time.time() - start_time) * 1000)
        
        return SearchResponse(
            results=[
                SearchResultItem(
                    id=r.get("id", 0),
                    code=r.get("code", ""),
                    title=r.get("title", ""),
                    department=r.get("department", ""),
                    faculty=r.get("faculty"),
                    similarity=r.get("similarity"),
                    score=r.get("score"),
                )
                for r in results
            ],
            total=len(results),
            execution_time_ms=execution_time,
            search_type=search_type,
        )
    
    except Exception as e:
        logger.error(f"Search error: {e}")
        return SearchResponse(
            results=[],
            total=0,
            execution_time_ms=int((time.time() - start_time) * 1000),
            search_type="error",
        )


@api.post("/search/fulltext/", response=SearchResponse)
def fulltext_course_search(
    request: SearchRequest,
    tenant_id: str = Query(..., description="Tenant slug"),
):
    """Full-text course search."""
    start_time = time.time()
    
    try:
        from apps.ml.search.services import basic_course_search
        
        results = basic_course_search(
            query=request.query,
            tenant_id=tenant_id,
            top_k=request.top_k,
        )
        
        execution_time = int((time.time() - start_time) * 1000)
        
        return SearchResponse(
            results=[
                SearchResultItem(
                    id=r.get("id", 0),
                    code=r.get("code", ""),
                    title=r.get("title", ""),
                    department=r.get("department", ""),
                    faculty=r.get("faculty"),
                )
                for r in results
            ],
            total=len(results),
            execution_time_ms=execution_time,
            search_type="fulltext",
        )
    
    except Exception as e:
        logger.error(f"Full-text search error: {e}")
        return SearchResponse(
            results=[],
            total=0,
            execution_time_ms=int((time.time() - start_time) * 1000),
            search_type="error",
        )