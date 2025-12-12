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
Optimize my fantasy football lineup for this week using Yahoo website projections.

WORKFLOW:
1. Check if league rules are already known (check_if_rules_known). If not, discover them.
2. Navigate to my Yahoo Fantasy team page using playwright__browser_navigate
3. Extract player projections from the "Proj Pts" column:
   - Call get_projection_extraction_script to get the JavaScript
   - Run it via playwright__browser_evaluate
   - These projections are calculated using MY league's specific scoring rules!
4. Analyze the lineup:
   - Start players with the HIGHEST projected points
   - Bench players with lower projections
   - Respect position requirements (don't bench my only QB, etc.)
   - Consider injury status (don't start injured players)
5. Execute lineup changes:
   - Use playwright__browser_snapshot to see the roster
   - Use playwright__browser_click to swap players
   - Verify changes with playwright__browser_take_screenshot

IMPORTANT:
- The Yahoo website projections are the MOST ACCURATE because they use MY league's scoring rules
- Use the extracted Proj Pts values as the PRIMARY decision factor
- Higher projection = Start, Lower projection = Bench

DO NOT:
- Propose or evaluate trades
- Make waiver wire pickups or drops  
- Move players to/from IR
- Try to get projections from any source OTHER than the Yahoo website

Make the best sit/start decisions to maximize projected points for this week.
"""

async def run_lineup_optimization():
    """Run the lineup optimization task."""
    logger.info("=" * 80)
    logger.info("Starting lineup optimization run")
    logger.info("=" * 80)
    
    # Track execution log for email summary
    execution_log = []
    error_details = None
    
    # Generate unique IDs for this run
    session_id = str(uuid.uuid4())
    
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
        
        # Generate unique IDs for this run
        user_id = "cli_user"
        
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
