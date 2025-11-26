"""Research Agent for finding information using Google Search."""
import logging
from typing import Optional, Any

try:
    from google.adk.agents import Agent
    from google.adk.tools.google_search_tool import GoogleSearchTool
    from google.adk.models.google_llm import Gemini
    ADK_AVAILABLE = True
except ImportError:
    ADK_AVAILABLE = False
    # Fallback classes for type hinting if ADK not available
    class Agent: pass
    class GoogleSearchTool: pass
    class Gemini: pass

from app.utils.config import settings

logger = logging.getLogger(__name__)

class ResearchAgent(Agent):
    """Agent specialized in researching information using Google Search."""
    
    def __init__(self, model_name: Optional[str] = None):
        if not ADK_AVAILABLE:
            logger.warning("ADK not available, ResearchAgent will not function correctly.")
            super().__init__(name="research_agent")
            return
            
        # Use provided model name or default from settings
        # We use gemini-2.5-pro as it supports tools well
        model_id = model_name or settings.model_name
        
        try:
            llm = Gemini(model=model_id)
        except Exception as e:
            logger.warning(f"Failed to initialize Gemini model: {e}. Using string model name.")
            llm = model_id
            
        # Initialize Google Search tool
        search_tool = GoogleSearchTool()
        
        instruction = """
You are a specialized Research Agent for a Fantasy Football Manager.
Your goal is to find accurate, up-to-date information to answer specific questions.

You have access to Google Search. Use it to find:
- Player news and injury updates
- Weather conditions for games
- Team depth charts and roster changes
- Expert analysis and projections
- General football knowledge

When answering:
1. ALWAYS use the google_search tool to find the most recent information.
2. Summarize the findings clearly and concisely.
3. Cite sources if possible (URLs are provided by the search tool).
4. If you cannot find the information, state that clearly.
5. Focus ONLY on the requested information.
"""
        
        super().__init__(
            name="research_agent",
            model=llm,
            tools=[search_tool],
            instruction=instruction
        )
        logger.info(f"ResearchAgent initialized with model {model_id}")
