"""
Semantic Search Service - Course Search with pgvector.
Phase 1 Module 07 - AI Features.
"""

import logging
from typing import Optional

from django.conf import settings

logger = logging.getLogger(__name__)

# Lazy load model - avoid loading on every request
_model = None


def get_embedding_model():
    """Lazily load sentence transformer model."""
    global _model
    
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            model_name = getattr(
                settings,
                "EMBEDDING_MODEL",
                "sentence-transformers/all-MiniLM-L6-v2"
            )
            _model = SentenceTransformer(model_name)
            logger.info(f"Loaded embedding model: {model_name}")
        except ImportError:
            logger.warning("sentence-transformers not installed")
            return None
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            return None
    
    return _model


def embed_query(query: str) -> Optional[list]:
    """Generate embedding for a query string."""
    model = get_embedding_model()
    if not model:
        return None
    
    embedding = model.encode(query)
    return embedding.tolist()


def embed_texts(texts: list[str]) -> Optional[list[list]]:
    """Generate embeddings for multiple texts."""
    model = get_embedding_model()
    if not model:
        return None
    
    embeddings = model.encode(texts)
    return embeddings.tolist()


def semantic_course_search(
    query: str,
    tenant_id: str,
    top_k: int = 10,
) -> list[dict]:
    """
    Hybrid search: semantic + full-text.
    
    Uses pgvector cosine similarity for semantic search
    and PostgreSQL full-text for keyword search.
    Results re-ranked by Reciprocal Rank Fusion.
    """
    from django.db import connection
    
    # Get query embedding
    query_embedding = embed_query(query)
    if not query_embedding:
        # Fallback to basic search
        return basic_course_search(query, tenant_id, top_k)
    
    # Build embedding array for PostgreSQL
    embedding_str = "[" + ",".join(map(str, query_embedding)) + "]"
    
    # Semantic search SQL
    semantic_sql = f"""
        SELECT 
            c.id,
            c.code,
            c.name as title,
            d.name as department,
            f.name as faculty,
            1 - (c.embedding <=> '%s'::vector) as similarity
        FROM institutional_programme c
        JOIN institutional_department d ON c.department_id = d.id
        JOIN institutional_faculty f ON d.faculty_id = f.id
        WHERE f.university_id IN (
            SELECT id FROM tenants_university WHERE slug = '{tenant_id}'
        )
        AND c.embedding IS NOT NULL
        ORDER BY c.embedding <=> '%s'::vector
        LIMIT {top_k * 2}
    """ % (embedding_str, embedding_str)
    
    try:
        with connection.cursor() as cursor:
            cursor.execute(semantic_sql)
            columns = [col[0] for col in cursor.description]
            semantic_results = [
                dict(zip(columns, row))
                for row in cursor.fetchall()
            ]
    except Exception as e:
        logger.error(f"Semantic search error: {e}")
        semantic_results = []
    
    # Basic full-text fallback
    fulltext = basic_course_search(query, tenant_id, top_k * 2)
    
    # Reciprocal Rank Fusion
    return reciprocal_rank_fusion(
        [semantic_results, fulltext],
        top_k=top_k
    )


def basic_course_search(
    query: str,
    tenant_id: str,
    top_k: int = 10,
) -> list[dict]:
    """Basic PostgreSQL full-text search."""
    from django.db import connection
    
    sql = """
        SELECT 
            c.id,
            c.code,
            c.name as title,
            d.name as department,
            f.name as faculty
        FROM institutional_programme c
        JOIN institutional_department d ON c.department_id = d.id
        JOIN institutional_faculty f ON d.faculty_id = f.id
        WHERE f.university_id IN (
            SELECT id FROM tenants_university WHERE slug = %s
        )
        AND (
            c.name ILIKE %s 
            OR c.code ILIKE %s 
            OR d.name ILIKE %s
        )
        ORDER BY c.name
        LIMIT %s
    """
    
    search_term = f"%{query}%"
    
    try:
        with connection.cursor() as cursor:
            cursor.execute(sql, [tenant_id, search_term, search_term, search_term, top_k])
            columns = [col[0] for col in cursor.description]
            return [
                dict(zip(columns, row))
                for row in cursor.fetchall()
            ]
    except Exception as e:
        logger.error(f"Full-text search error: {e}")
        return []


def reciprocal_rank_fusion(
    result_lists: list[list[dict]],
    top_k: int = 10,
    k: float = 60.0,
) -> list[dict]:
    """
    Reciprocal Rank Fusion for re-ranking search results.
    
    RRF score = sum(1 / (k + rank)) for each result across all lists
    """
    from collections import defaultdict
    
    rrf_scores = defaultdict(float)
    doc_scores = {}
    
    # Score each document
    for results in result_lists:
        for rank, result in enumerate(results, 1):
            doc_id = result.get("id")
            if doc_id:
                rrf_scores[doc_id] += 1.0 / (k + rank)
                if doc_id not in doc_scores:
                    doc_scores[doc_id] = result
    
    # Sort by RRF score
    sorted_ids = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
    
    # Build final results
    final_results = []
    for doc_id, score in sorted_ids[:top_k]:
        result = doc_scores[doc_id].copy()
        result["score"] = round(score, 4)
        final_results.append(result)
    
    return final_results


# Celery task for embedding courses
def embed_all_courses_task():
    """Celery task to embed all courses."""
    from apps.institutional.models import Programme
    
    courses = Programme.objects.all()
    
    for course in courses:
        embed_single_course(course)


def embed_single_course(course):
    """Embed a single course."""
    text = f"{course.name} {course.code} {course.department.name}"
    
    embeddings = embed_texts([text])
    if embeddings:
        # Save embedding
        from apps.ml.search.models import CourseEmbedding
        
        CourseEmbedding.objects.update_or_create(
            course=course,
            defaults={"embedding": embeddings[0]}
        )


# Mock for when sentence-transformers is not available
def mock_semantic_search(query: str, tenant_id: str, top_k: int = 10) -> list[dict]:
    """Mock semantic search when model not available."""
    # Use basic search as fallback
    return basic_course_search(query, tenant_id, top_k)