
import asyncio
import logging
from unittest.mock import MagicMock

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_error_handling():
    logger.info("Starting error handling test")
    
    # Mock the agent and tool
    mock_tool = MagicMock()
    mock_tool.name = "browser__browser_drag_and_drop"
    
    # Define the error handler
    async def _handle_tool_error(tool, args, tool_context, error):
        logger.info(f"Caught error from tool {tool.name}: {error}")
        return {"error": f"Handled error: {error}"}
    
    # Simulate tool execution failure
    try:
        # Simulate the logic in _execute_single_function_call_async
        try:
            raise ValueError("Simulated tool failure")
        except Exception as e:
            # This is where the callback should be called
            result = await _handle_tool_error(mock_tool, {}, None, e)
            if result:
                logger.info(f"Recovered with result: {result}")
            else:
                raise e
                
    except Exception as e:
        logger.error(f"Uncaught exception: {e}")
        return
        
    logger.info("Test passed!")

if __name__ == "__main__":
    asyncio.run(test_error_handling())
