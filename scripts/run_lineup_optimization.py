#!/usr/bin/env python3
"""
Daily Fantasy Football Lineup Optimization Script

This script runs the fantasy football agent with a focused lineup optimization prompt.
It's designed to optimize lineups based on current player projections without handling
trades, waivers, or injury management.
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

log_file = os.path.join(log_dir, f"lineup_optimization_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

LINEUP_OPTIMIZATION_PROMPT = """
Optimize my fantasy football lineup for this week based on current player projections and league-specific rules.

Focus exclusively on lineup optimization:
1. Check if league rules are already known. If not, discover them from both the Yahoo Fantasy API and by navigating to the league settings page in the browser to get complete scoring rules.
2. Retrieve my current roster and this week's matchup data using the Yahoo Fantasy MCP tools.
3. Analyze the lineup using YOUR OWN reasoning, with these priorities in order:
   a. FIRST PRIORITY: Use Yahoo's projected points for THIS WEEK as the primary decision factor (available in the roster/matchup data)
   b. SECOND PRIORITY: Consider any injury news, weather alerts, or late-breaking information that Yahoo's projections may not reflect
   c. THIRD PRIORITY: Factor in matchup quality, recent performance trends, and game flow expectations
4. Make lineup decisions that respect my league's specific scoring rules and position requirements:
   * If PPR league: Prioritize high-reception players
   * If Standard league: Prioritize touchdown-dependent players  
   * Consider my league's exact position requirements (2 QB, FLEX, SUPERFLEX, etc.)
5. Execute lineup changes using the Playwright MCP browser tools:
   * Navigate to the Yahoo Fantasy Football lineup page
   * Use screenshots to see the current lineup
   * Click to select and move players to optimal positions
   * Verify changes were successful

DO NOT:
- Propose or evaluate trades
- Make waiver wire pickups or drops
- Move players to/from IR
- Handle any roster transactions beyond lineup optimization

Keep in mind:
* My league has special scoring rules that put extra weight on touchdowns compared to a normal league
* It has some unique positions including 2 QBs and optional tight ends
* It uses 0.5 PPR scoring
* IR positions do not count against roster positions for active players

Make the best sit/start decisions possible to maximize my team's projected points for this week.
"""

async def run_lineup_optimization():
    """Run the lineup optimization task."""
    logger.info("=" * 80)
    logger.info("Starting lineup optimization run")
    logger.info("=" * 80)
    
    # Track execution log for email summary
    execution_log = []
    error_details = None
    
    try:
        # Initialize session service
        # Use DatabaseSessionService for persistence (SQLite)
        db_path = os.path.join(os.getcwd(), "sessions.db")
        db_url = f"sqlite:///{db_path}"
        logger.info(f"Using persistent session storage at {db_url}")
        session_service = DatabaseSessionService(db_url=db_url)
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
        
        logger.info("Sending lineup optimization prompt to agent...")
        
        # Create the message
        message = types.Content(
            role="user",
            parts=[types.Part(text=LINEUP_OPTIMIZATION_PROMPT)]
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
        logger.info("Lineup optimization completed successfully")
        logger.info("=" * 80)
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"Error during lineup optimization: {e}", exc_info=True)
        logger.info("Attempting to send error email...")
        
    finally:
        # Send email summary (even if there was an error)
        try:
            from app.utils.email_sender import EmailSender
            email_sender = EmailSender()
            
            if email_sender.is_configured():
                logger.info("Sending email summary...")
                success = email_sender.send_lineup_optimization_email(
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
    asyncio.run(run_lineup_optimization())
