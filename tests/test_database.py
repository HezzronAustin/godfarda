import pytest
from datetime import datetime
from src.storage.database import Document, Conversation, AgentState

def test_document_creation(db_session):
    # Create a test document
    doc = Document(
        external_id="test-doc-1",
        content="Test content",
        meta_data={"type": "test"},
        embedding_id="emb-1"
    )
    
    db_session.add(doc)
    db_session.commit()
    
    # Retrieve and verify
    saved_doc = db_session.query(Document).filter_by(external_id="test-doc-1").first()
    assert saved_doc is not None
    assert saved_doc.content == "Test content"
    assert saved_doc.meta_data == {"type": "test"}

def test_conversation_creation(db_session):
    # Create a test conversation
    conv = Conversation(
        query="test query",
        context={"context": "test"},
        response="test response",
        meta_data={"type": "test"}
    )
    
    db_session.add(conv)
    db_session.commit()
    
    # Retrieve and verify
    saved_conv = db_session.query(Conversation).first()
    assert saved_conv is not None
    assert saved_conv.query == "test query"
    assert saved_conv.response == "test response"

def test_agent_state_creation(db_session):
    # Create a test agent state
    state = AgentState(
        agent_id="test-agent-1",
        state={"status": "active"}
    )
    
    db_session.add(state)
    db_session.commit()
    
    # Retrieve and verify
    saved_state = db_session.query(AgentState).filter_by(agent_id="test-agent-1").first()
    assert saved_state is not None
    assert saved_state.state == {"status": "active"}
