import pytest
from src.rag.core import Document, RAGSystem
import chromadb
from chromadb.config import Settings
import uuid

@pytest.fixture
def chroma_client():
    settings = chromadb.Settings(
        allow_reset=True,
        is_persistent=False
    )
    client = chromadb.Client(settings)
    yield client
    client.reset()

@pytest.mark.asyncio
async def test_document_addition(rag_system):
    # Create a test document
    doc = Document(
        id="test-1",
        content="This is a test document about artificial intelligence.",
        metadata={"type": "test", "topic": "AI"}
    )
    
    # Add document
    await rag_system.add_document(doc)
    
    # Search for the document
    results = await rag_system.search("artificial intelligence")
    assert len(results) > 0
    assert any(d.id == "test-1" for d in results)

@pytest.mark.asyncio
async def test_context_retrieval(rag_system):
    # Add multiple test documents
    docs = [
        Document(
            id="test-1",
            content="Python is a popular programming language.",
            metadata={"type": "test", "topic": "programming"}
        ),
        Document(
            id="test-2",
            content="Machine learning is a subset of AI.",
            metadata={"type": "test", "topic": "AI"}
        )
    ]
    
    for doc in docs:
        await rag_system.add_document(doc)
    
    # Get context for a query
    context = await rag_system.get_context("What is Python?")
    assert context["query"] == "What is Python?"
    assert len(context["documents"]) > 0
    
@pytest.mark.asyncio
async def test_search_relevance(rag_system):
    # Add test documents
    docs = [
        Document(
            id="test-1",
            content="Neural networks are a type of machine learning model.",
            metadata={"type": "test", "topic": "ML"}
        ),
        Document(
            id="test-2",
            content="Database systems store and retrieve data.",
            metadata={"type": "test", "topic": "databases"}
        )
    ]
    
    for doc in docs:
        await rag_system.add_document(doc)
    
    # Search for ML-related content
    results = await rag_system.search("machine learning neural networks")
    assert len(results) > 0
    assert results[0].id == "test-1"  # Most relevant document should be first

@pytest.mark.asyncio
async def test_rag_system_with_custom_client(db_engine, chroma_client):
    # Create RAG system with custom client
    rag = RAGSystem(db_engine, chroma_client)
    
    # Add test document
    doc_id = str(uuid.uuid4())
    test_doc = Document(
        id=doc_id,
        content="This is a test document about artificial intelligence.",
        metadata={"source": "test", "type": "article"}
    )
    await rag.add_document(test_doc)
    
    # Test search functionality
    results = await rag.search("artificial intelligence")
    assert len(results) > 0
    assert results[0].content == test_doc.content
    assert results[0].metadata == test_doc.metadata
    
    # Test context retrieval
    context = await rag.get_context("artificial intelligence")
    assert "documents" in context
    assert len(context["documents"]) > 0
    assert "timestamp" in context
    assert "query" in context
    assert context["query"] == "artificial intelligence"

@pytest.mark.asyncio
async def test_rag_system_collection_reuse(db_engine, chroma_client):
    # Create first RAG system
    rag1 = RAGSystem(db_engine, chroma_client)
    
    # Add document using first system
    doc_id = str(uuid.uuid4())
    test_doc = Document(
        id=doc_id,
        content="Test document for collection reuse",
        metadata={"source": "test", "type": "article"}
    )
    await rag1.add_document(test_doc)
    
    # Create second RAG system with same client
    rag2 = RAGSystem(db_engine, chroma_client)
    
    # Verify document is accessible through second system
    results = await rag2.search("collection reuse")
    assert len(results) > 0
    assert results[0].content == test_doc.content
