#!/usr/bin/env python3
"""
Daily Fantasy Football Agent Runner

This script runs the fantasy football agent with the weekly setup prompt.
It's designed to be run via cron or manually.
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

log_file = os.path.join(log_dir, f"daily_run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

DAILY_PROMPT = """
Check on my Yahoo fantasy football team and do everything you need to so I can be in a good position for this week to win!  Do the following at a minimum:
Update my lineup and move any players around into the correct positions based on my league's unique positions and scoring rules.
Evaluate and take action on any pending trades.
Propose any new trades that would help give the team a significantly greater chance to win or improve our team's ability to recover from injuries or upcoming bye weeks. Make sure trades are fair and have a good chance of being accepted by an opponent. Include a nice note about the trade when proposing.  Keep in mind this league is full of friends and nice people, except Ross who is very bad at proposing fair trades.
Take action on any waiver wire pickups based on research and your best knowledge of current events and how to significantly improve the chances of a weekly or season win, or to help the team's chances of recovering well from an injury or upcoming bye weeks.
Handle player injuries as needed.  If a player is considered out but may recover and play again and is worth keeping, moving the player to IR. If the player won't play again this season or isn't worth keeping, drop the player and pickup a new one. Move players off of IR to the active roster as they recover, and drop the worst players as needed to keep the team at the right number of active players.

Keep in mind the following facts about my fantasy football league as you do all these tasks:
* It has special scoring rules that put extra weight on touchdowns compared to a normal league
* It has some strange positions compared to a normal league, including 2 QBs and optional tight ends
* It has .5 PPR
* IR positions do not count against roster positions for active players
"""

async def run_daily_task():
    """Run the daily agent task."""
    logger.info("=" * 80)
    logger.info("Starting daily agent run")
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
            parts=[types.Part(text=DAILY_PROMPT)]
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
        logger.info("Daily run completed successfully")
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error(f"Error during daily run: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    # Run the async task
    asyncio.run(run_daily_task())
