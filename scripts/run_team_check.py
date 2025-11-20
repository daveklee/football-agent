#!/usr/bin/env python3
"""
Team Check Fantasy Football Agent Runner

This script runs the fantasy football agent with the team check prompt.
It's designed to be run via command line.
"""
import asyncio
import logging
import os
import sys
import uuid
import warnings
from datetime import datetime

# Suppress asyncio cleanup warnings that occur during MCP session shutdown
# These are harmless and occur due to the synchronous wrapper around async code
warnings.filterwarnings('ignore', category=RuntimeWarning, module='asyncio')
logging.getLogger('asyncio').setLevel(logging.CRITICAL)

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from app.agent import agent
from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.genai import types

# Configure logging
log_dir = os.path.join(PROJECT_ROOT, "logs")
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

log_file = os.path.join(log_dir, f"team_check_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

TEAM_CHECK_PROMPT = """
You are a fantasy football expert that always does your own research about current stats and news before making any decision.  Check the state of my fantasy football team and see if there are any gaps to address -- examples include a new injury where a player might need to be placed on IR if they are not playing for a few weeks, or dropped if they will not play again this season, or bye weeks where the team will end up without enough active players to fill all the spots, or underperforming players that don't seem to be doing very well this season.  Also, see if any backup players are needed for positions that we don't have adequate protection from future possible injuries in our starting lineup.  Then, check the waiver wire to see if anyone is available that might be good to pickup this week that will significantly improve our team's chances of winning this week or the season as a whole, and drop the player that you think is best to drop if needed (the lowest performing player given all the positions we need to fill each week).
"""

async def run_team_check():
    """Run the team check agent task."""
    logger.info("=" * 80)
    logger.info("Starting team check agent run")
    logger.info("=" * 80)
    
    try:
        # Create runner with in-memory session service
        session_service = InMemorySessionService()
        runner = Runner(
            app_name="fantasy-football-agent",
            agent=agent,
            session_service=session_service
        )
        
        # Generate unique IDs for this run
        user_id = "cli_user"
        session_id = str(uuid.uuid4())
        
        logger.info(f"Session ID: {session_id}")
        
        # Create the session
        await session_service.create_session(
            app_name="fantasy-football-agent",
            user_id=user_id,
            session_id=session_id
        )
        
        logger.info("Sending prompt to agent...")
        
        # Create the message
        message = types.Content(
            role="user",
            parts=[types.Part(text=TEAM_CHECK_PROMPT)]
        )
        
        # Run the agent (synchronous wrapper around async)
        event_count = 0
        for event in runner.run(
            user_id=user_id,
            session_id=session_id,
            new_message=message
        ):
            event_count += 1
            
            # Log model responses
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        logger.info(f"Agent: {part.text[:200]}...")
            
            # Log function calls
            function_calls = event.get_function_calls()
            if function_calls:
                for fc in function_calls:
                    logger.info(f"Tool call: {fc.name}")
        
        logger.info(f"Processed {event_count} events")
        logger.info("=" * 80)
        logger.info("Team check run completed successfully")
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error(f"Error during team check run: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    # Run the async task
    asyncio.run(run_team_check())
