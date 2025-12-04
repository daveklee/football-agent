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
from google.adk.sessions.database_session_service import DatabaseSessionService
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
Check on my Yahoo fantasy football team and do everything you need to so I can be in a good position for this week to win! Do the following at a minimum:

Update my lineup and move any players around into the correct positions based on my league's unique positions and scoring rules.

Evaluate and take action on any pending trades.

Propose any new trades that would help give the team a significantly greater chance to win or improve our team's ability to recover from injuries or upcoming bye weeks. Make sure trades are fair and have a good chance of being accepted by an opponent. Include a nice note about the trade when proposing.

Take action on any waiver wire pickups based on research and your best knowledge of current events and how to significantly improve the chances of a weekly or season win, or to help the team's chances of recovering well from an injury or upcoming bye weeks.

Handle player injuries as needed. If a player is considered out but may recover and play again and is worth keeping, move the player to IR. If the player won't play again this season or isn't worth keeping, drop the player and pickup a new one. Move players off of IR to the active roster as they recover, and drop the worst players as needed to keep the team at the right number of active players.
"""


async def run_daily_task():
    """Run the daily agent task."""
    logger.info("=" * 80)
    logger.info("Starting daily agent run")
    logger.info("=" * 80)
    
    # Track execution log for email summary
    execution_log = []
    error_details = None
    # Generate unique IDs for this run
    user_id = "cli_user"
    session_id = str(uuid.uuid4())
    logger.info(f"Session ID: {session_id}")

    try:
        # Initialize session service
        # Use DatabaseSessionService for persistence (SQLite)
        # Use absolute path to project root for consistency across runs
        PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        db_path = os.path.join(PROJECT_ROOT, "sessions.db")
        # Use aiosqlite driver for async support
        db_url = f"sqlite+aiosqlite:///{db_path}"
        logger.info(f"Using persistent session storage at {db_url}")
        session_service = DatabaseSessionService(db_url=db_url)

        runner = Runner(
            app_name="fantasy-football-agent",
            agent=agent,
            session_service=session_service
        )
        
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
        
        # Run the agent asynchronously
        event_count = 0
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=message
        ):
            event_count += 1
            timestamp = datetime.now().strftime('%H:%M:%S')
            
            # Log model responses and capture for email
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        logger.info(f"Agent: {part.text[:200]}...")
                        # Capture full response for email summary
                        execution_log.append({
                            'timestamp': timestamp,
                            'type': 'text',
                            'content': part.text
                        })
            
            # Log function calls and capture for email
            function_calls = event.get_function_calls()
            if function_calls:
                for fc in function_calls:
                    logger.info(f"Tool call: {fc.name}")
                    # Capture tool call for email summary
                    execution_log.append({
                        'timestamp': timestamp,
                        'type': 'tool',
                        'name': fc.name,
                        'args': str(fc.args) if hasattr(fc, 'args') else ''
                    })
        
        logger.info(f"Processed {event_count} events")
        logger.info("=" * 80)
        logger.info("Daily run completed successfully")
        logger.info("=" * 80)
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"Error during daily run: {e}", exc_info=True)
        logger.info("Attempting to send error email...")
        
    finally:
        # Send email summary (even if there was an error)
        try:
            from app.utils.email_sender import EmailSender
            email_sender = EmailSender()
            
            if email_sender.is_configured():
                logger.info("Sending email summary...")
                success = email_sender.send_summary_email(
                    execution_log=execution_log,
                    session_id=session_id,
                    event_count=event_count if 'event_count' in locals() else 0,
                    error_details=error_details
                )
                if success:
                    logger.info("Email summary sent successfully")
                else:
                    logger.warning("Failed to send email summary")
            else:
                logger.info("Email not configured - skipping email summary")
        except Exception as e:
            logger.error(f"Error sending email summary: {e}", exc_info=True)


if __name__ == "__main__":
    # Run the async task
    asyncio.run(run_daily_task())
