import asyncio
from src.storage.database import init_db
from src.rag.core import RAGSystem, Document
from config.settings import settings
import uuid

async def main():
    # Initialize the database engine
    engine = init_db(settings.DATABASE_URL)
    
    # Create RAG system with a persistent directory
    rag = RAGSystem(engine, persist_directory="./chroma_db")
    
    # Add some example documents
    doc1 = Document(
        id=str(uuid.uuid4()),
        content="Python is a high-level programming language known for its simplicity and readability. It has extensive libraries for machine learning and data science.",
        metadata={"type": "programming", "language": "python", "domain": "general"}
    )
    
    doc2 = Document(
        id=str(uuid.uuid4()),
        content="JavaScript is a programming language commonly used for web development. It runs in browsers and can create interactive web applications.",
        metadata={"type": "programming", "language": "javascript", "domain": "web"}
    )
    
    await rag.add_document(doc1)
    await rag.add_document(doc2)
    
    # Search for documents with semantic similarity
    print("\nSearching for web development related content:")
    results = await rag.search("What programming language is best for web development?")
    for doc in results:
        print(f"\nContent: {doc.content}")
        print(f"Relevance Score: {doc.metadata.get('relevance_score', 'N/A')}")
        
    # Get context about Python
    print("\nGetting context about Python:")
    context = await rag.get_context("Tell me about Python's features and capabilities")
    for doc in context["documents"]:
        print(f"\nContent: {doc.content}")
        print(f"Relevance Score: {doc.metadata.get('relevance_score', 'N/A')}")
        
    # Ask a question using Ollama
    print("\nAsking a question using Ollama:")
    answer = await rag.ask("Which language would you recommend for a beginner who wants to learn programming?")
    print(f"\nAnswer: {answer}")

if __name__ == "__main__":
    asyncio.run(main())
