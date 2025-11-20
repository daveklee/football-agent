
import asyncio
import logging
from typing import Any, Dict, List
from unittest.mock import MagicMock, AsyncMock

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Mock Google ADK components since we might not have full environment
class MockTool:
    def __init__(self, name):
        self.name = name

class MockModel:
    def __init__(self):
        self.responses = []
        self.call_count = 0
        
    def add_response(self, response):
        self.responses.append(response)
        
    async def generate_content_async(self, *args, **kwargs):
        if self.call_count < len(self.responses):
            response = self.responses[self.call_count]
            self.call_count += 1
            return response
        return MagicMock(text="No more responses")

# Mock the Agent class to simulate the loop
class MockAgent:
    def __init__(self, model, tools):
        self.model = model
        self.tools = tools
        self.history = []
        
    async def run(self, user_input):
        logger.info(f"User: {user_input}")
        self.history.append({"role": "user", "parts": [user_input]})
        
        # Simulate one turn of the loop
        response = await self.model.generate_content_async(self.history)
        
        logger.info(f"Model response: {response}")
        
        # Check for function calls
        if hasattr(response, 'candidates') and response.candidates:
            candidate = response.candidates[0]
            if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                for part in candidate.content.parts:
                    if hasattr(part, 'function_call'):
                        logger.info(f"Function call detected: {part.function_call.name}")
                        # In a real agent, this would execute the tool and continue
                        # If the agent stops here, that's the bug
                        return "Function call detected"
        
        return "No function call"

async def reproduce_issue():
    logger.info("Starting reproduction script")
    
    # Setup mock model response that mimics the user's report
    # text + function_call + finish_reason: STOP
    
    mock_function_call = MagicMock()
    mock_function_call.name = "browser__browser_drag_and_drop"
    mock_function_call.args = {"source_ref": "s2e1115", "target_ref": "s2e874"}
    
    mock_part_text = MagicMock()
    mock_part_text.text = "Okay, I've analyzed the page. I've located Travis Kelce..."
    
    mock_part_fc = MagicMock()
    mock_part_fc.function_call = mock_function_call
    
    mock_content = MagicMock()
    mock_content.parts = [mock_part_text, mock_part_fc]
    
    mock_candidate = MagicMock()
    mock_candidate.content = mock_content
    mock_candidate.finish_reason = 1 # STOP
    
    mock_response = MagicMock()
    mock_response.candidates = [mock_candidate]
    
    model = MockModel()
    model.add_response(mock_response)
    
    agent = MockAgent(model, [MockTool("browser__browser_drag_and_drop")])
    
    result = await agent.run("Move Travis Kelce to starting lineup")
    logger.info(f"Result: {result}")

if __name__ == "__main__":
    asyncio.run(reproduce_issue())
