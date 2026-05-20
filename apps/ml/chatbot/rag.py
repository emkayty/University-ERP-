"""
RAG Chatbot for University Policy Queries.
Phase 2 - AI Domain 4.
"""

import logging
import hashlib
from dataclasses import dataclass
from typing import Optional

from django.conf import settings

logger = logging.getLogger(__name__)

# Cache settings
CACHE_TTL = 60 * 60 * 24  # 24 hours


@dataclass
class ChatbotResponse:
    """Chatbot response."""
    response: str
    sources: list[dict]
    confidence: float
    routed_to_human: bool


def get_embedding_model():
    """Get sentence transformer model."""
    try:
        from sentence_transformers import SentenceTransformer
        return SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    except ImportError:
        return None


def get_llm():
    """Get LLM (Ollama or fallback)."""
    try:
        from langchain_community.llms import Ollama
        return Ollama(model="llama3.2")
    except Exception:
        return None


def semantic_search(query: str, tenant_id: str, top_k: int = 5) -> list[dict]:
    """Search policy chunks by semantic similarity."""
    from django.db import connection
    
    # Get embedding
    model = get_embedding_model()
    if not model:
        return []
    
    query_embedding = model.encode(query).tolist()
    embedding_str = "[" + ",".join(map(str, query_embedding)) + "]"
    
    sql = """
        SELECT id, content, source, page_number, 
               1 - (embedding <=> '%s'::vector) as similarity
        FROM ml_policy_chunk
        WHERE tenant_id = %s
        ORDER BY embedding <=> '%s'::vector
        LIMIT %s
    """ % (embedding_str, tenant_id, embedding_str, top_k)
    
    try:
        with connection.cursor() as cursor:
            cursor.execute(sql)
            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    except Exception as e:
        logger.error(f"Semantic search error: {e}")
        return []


def build_prompt(query: str, context: list[dict], history: list) -> str:
    """Build prompt with context and history."""
    context_str = "\n\n".join([
        f"Source: {c.get('source', 'Unknown')} (Page {c.get('page_number', 'N/A')})\n{c.get('content', '')}"
        for c in context
    ])
    
    history_str = ""
    for msg in history[-5:]:  # Last 5 messages
        role = msg.get("role", "user")
        content = msg.get("content", "")
        history_str += f"{role}: {content}\n"
    
    prompt = f"""You are a helpful university assistant. Use the following context to answer questions accurately.

Context:
{context_str}

Previous conversation:
{history_str}

User: {query}

Assistant:"""
    
    return prompt


def query_chatbot(
    query: str,
    tenant_id: str,
    session_history: list,
) -> ChatbotResponse:
    """
    Main RAG query pipeline.
    
    1. Semantic search policy chunks
    2. Build prompt with context + history
    3. Primary: Ollama (local)
    4. Fallback: Cached FAQ or human
    5. Confidence check: < 0.6 routes to human
    """
    # Check cache first
    cache_key = f"chatbot_cache_{hashlib.md5(query.encode()).hexdigest()}"
    
    from django.core.cache import cache
    cached = cache.get(cache_key)
    if cached:
        logger.info("Returning cached response")
        return ChatbotResponse(**cached)
    
    # Semantic search
    results = semantic_search(query, tenant_id)
    
    if not results:
        # No relevant context - route to human
        return ChatbotResponse(
            response="I couldn't find relevant information. Please contact the registry for assistance.",
            sources=[],
            confidence=0.0,
            routed_to_human=True,
        )
    
    # Check confidence (top result similarity)
    top_score = results[0].get("similarity", 0)
    if top_score < 0.6:
        return ChatbotResponse(
            response="I'm not confident about this answer. Let me connect you with a staff member.",
            sources=[],
            confidence=top_score,
            routed_to_human=True,
        )
    
    # Build prompt
    prompt = build_prompt(query, results, session_history)
    
    # Get LLM response
    llm = get_llm()
    if llm:
        try:
            response = llm(prompt)
        except Exception as e:
            logger.error(f"LLM error: {e}")
            response = "I apologize, but I'm having trouble processing your request."
    else:
        # Fallback to FAQ
        response = "Please visit the student portal for fee payment guidelines."
    
    # Format sources
    sources = [
        {
            "title": r.get("source", ""),
            "page": r.get("page_number", ""),
            "similarity": r.get("similarity", 0),
        }
        for r in results[:3]
    ]
    
    # Cache response
    result = ChatbotResponse(
        response=response,
        sources=sources,
        confidence=top_score,
        routed_to_human=False,
    )
    
    cache.set(cache_key, {
        "response": result.response,
        "sources": result.sources,
        "confidence": result.confidence,
        "routed_to_human": result.routed_to_human,
    }, CACHE_TTL)
    
    return result


# WhatsApp webhook
def handle_whatsapp_message(from_number: str, message: str) -> str:
    """Handle incoming WhatsApp message."""
    # Route to RAG
    response = query_chatbot(
        query=message,
        tenant_id="default",  # Would extract from phone number
        session_history=[],
    )
    
    return response.response


# SMS Keyword Bot
def handle_sms_keyword(phone: str, keyword: str, params: list) -> str:
    """Handle SMS keyword commands."""
    
    if keyword.upper() == "RESULT":
        # RESULT [MATRIC]
        if not params:
            return "Usage: RESULT [MATRIC_NUMBER]"
        
        from apps.students.models import Student
        try:
            student = Student.objects.get(matric_number__icontains=params[0])
            # Return current semester results summary
            return f"Your current CGPA: {student.current_cgpa}"
        except Student.DoesNotExist:
            return "Student not found"
    
    elif keyword.upper() == "FEES":
        # FEES [MATRIC]
        if not params:
            return "Usage: FEES [MATRIC_NUMBER]"
        
        from apps.finance.models import Invoice
        try:
            student = Student.objects.get(matric_number__icontains=params[0])
            outstanding = Invoice.objects.filter(
                student=student,
                state__in=["invoice_created", "partial_payment"],
            ).aggregate(total=models.Sum("outstanding"))["total"] or 0
            
            return f"Outstanding fees: ₦{outstanding}"
        except Student.DoesNotExist:
            return "Student not found"
    
    elif keyword.upper() == "HOSTEL":
        # HOSTEL - return status
        from apps.hostel.models import HostelApplication
        from apps.students.models import Student
        
        # Would need to identify student from phone
        return "Please provide your matric number: HOSTEL [MATRIC]"
    
    return "Unknown command. Available: RESULT, FEES, HOSTEL"