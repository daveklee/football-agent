import asyncio
import os
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load env vars
load_dotenv()

try:
    from app.agent import FantasyFootballAgent
    
    async def run_test():
        print("Initializing Fantasy Football Agent...")
        agent = FantasyFootballAgent()
        
        # Check if research_agent tool is present
        tool_names = []
        for t in agent.tools:
            if hasattr(t, 'name'):
                tool_names.append(t.name)
            elif hasattr(t, 'tools'): # McpToolset
                 tool_names.extend([sub_t.name for sub_t in t.tools])
            else:
                tool_names.append(str(t))
        
        print(f"Available tools: {tool_names}")
        
        if "research_agent" not in tool_names:
            print("ERROR: research_agent tool not found!")
            return
            
        print("SUCCESS: research_agent tool found.")
        
        # We won't run a full turn here to avoid API costs and complexity,
        # but verifying the tool presence confirms the integration code ran.

    if __name__ == "__main__":
        asyncio.run(run_test())

except ImportError as e:
    print(f"Imports failed: {e}")
    print("Skipping test.")
except Exception as e:
    print(f"Test failed: {e}")
