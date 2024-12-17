import asyncio
import os
import logging
import pytest
from src.tools.ai.ollama.chat import OllamaChatTool

# Get the current directory path
current_dir = os.path.dirname(os.path.abspath(__file__))
log_dir = os.path.join(current_dir, 'logs')
os.makedirs(log_dir, exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(log_dir, 'ollama_test.log'))
    ]
)
logger = logging.getLogger(__name__)

@pytest.fixture
def ollama():
    """Fixture to create an OllamaChatTool instance."""
    return OllamaChatTool()

@pytest.mark.asyncio
async def test_chat_initialization(ollama):
    """Test that the Ollama chat tool initializes correctly."""
    assert isinstance(ollama, OllamaChatTool)
    assert ollama.base_url == "http://localhost:11434/api"

@pytest.mark.asyncio
async def test_chat_response(ollama):
    """Test that the Ollama chat tool can get responses."""
    logger.info("Testing chat response...")
    
    request_data = {
        "model": "llama3.2",
        "messages": [
            {
                "role": "user",
                "content": "Hello, how are you?"
            }
        ]
    }
    
    response = await ollama.execute(request_data)
    
    assert response is not None
    assert hasattr(response, 'success')
    assert hasattr(response, 'data')
    assert hasattr(response, 'error')
    
    if response.success:
        logger.info(f"Got response: {response.data}")
        assert isinstance(response.data, dict)
        assert 'message' in response.data
        assert 'content' in response.data['message']
    else:
        logger.error(f"Failed to get response: {response.error}")
        pytest.fail(f"Failed to get response: {response.error}")

@pytest.mark.asyncio
async def test_invalid_request(ollama):
    """Test handling of invalid request."""
    logger.info("Testing invalid request handling...")
    
    # Empty request data should fail
    response = await ollama.execute({})
    
    assert response is not None
    assert not response.success
    assert response.error is not None
