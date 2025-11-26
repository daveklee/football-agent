"""Tools for the agent to interact with persistent memory."""
import logging
from typing import Dict, Any

from app.utils.fact_memory import FactMemory

logger = logging.getLogger(__name__)

# Initialize global memory instance
_fact_memory = FactMemory()

def remember_fact(fact: str) -> Dict[str, Any]:
    """Remember a useful fact, preference, or note for future reference.
    
    Use this tool to store information that should be persisted across different
    sessions and days. Examples:
    - User preferences (e.g., "User dislikes trading with Ross")
    - Strategic notes (e.g., "Need to pick up a backup QB for Week 9 bye")
    - Team context (e.g., "We are prioritizing floor over ceiling this week")
    
    Args:
        fact: The text content of the fact to remember.
        
    Returns:
        Confirmation message with the fact ID.
    """
    try:
        fact_id = _fact_memory.add_fact(fact)
        return {
            "status": "success",
            "message": f"Successfully stored fact: '{fact}'",
            "fact_id": fact_id
        }
    except Exception as e:
        logger.error(f"Error storing fact: {e}")
        return {
            "status": "error",
            "message": f"Failed to store fact: {str(e)}"
        }

def get_all_facts() -> Dict[str, Any]:
    """Retrieve all stored facts.
    
    Returns:
        List of all stored facts.
    """
    return {"facts": _fact_memory.get_all_facts()}
