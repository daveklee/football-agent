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
    from google.adk.agents import Agent
    from google.adk.tools.google_search_tool import GoogleSearchTool
    from google.adk.models.google_llm import Gemini
    
    class ResearchAgent(Agent):
        def __init__(self):
            # Use a specific model for research
            model_name = os.getenv("MODEL_NAME", "gemini-2.5-pro")
            llm = Gemini(model=model_name)
            
            tools = [GoogleSearchTool()]
            
            super().__init__(
                name="research_agent",
                model=llm,
                tools=tools,
                instruction="You are a research assistant. Use Google Search to answer questions. Provide concise summaries."
            )

    async def run_test():
        print("Initializing Research Agent...")
        agent = ResearchAgent()
        
        query = "Who is the current starting quarterback for the Kansas City Chiefs?"
        print(f"Query: {query}")
        
        # Run the agent
        # Note: Agent.run_async yields events. We need to process them or use a runner.
        # For this test, we'll try to use a simple runner simulation or just iterate events.
        
        print("Running agent...")
        response_text = ""
        
        # Simple event loop simulation
        async for event in agent.run_async(input=query):
            print(f"Event: {type(event).__name__}")
            if hasattr(event, 'text') and event.text:
                print(f"Text: {event.text}")
                response_text += event.text
            elif hasattr(event, 'tool_calls'):
                print(f"Tool calls: {event.tool_calls}")
            elif hasattr(event, 'tool_results'):
                print(f"Tool results: {event.tool_results}")
                
        print(f"\nFinal Response: {response_text}")

    if __name__ == "__main__":
        asyncio.run(run_test())

except ImportError as e:
    print(f"ADK imports failed: {e}")
    print("Skipping test.")
