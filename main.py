"""Main entry point for the Fantasy Football Agent."""
import asyncio
import logging
import sys

# Try importing ADK components
try:
    from google.adk import AgentRunner
    ADK_AVAILABLE = True
except ImportError:
    try:
        from google.adk.agents import AgentRunner
        ADK_AVAILABLE = True
    except ImportError:
        ADK_AVAILABLE = False
        logging.warning("ADK AgentRunner not found. Agent will run in standalone mode.")

from app.agent import agent, root_agent

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Main function to run the agent."""
    logger.info("Starting Fantasy Football Agent")
    
    try:
        if ADK_AVAILABLE:
            # Create agent runner for ADK web interface
            runner = AgentRunner(agent=agent)
            logger.info("Agent initialized. Use ADK web interface to interact.")
            logger.info("Run './start_adk_web.sh' or 'adk web --port 8080' to start the web interface.")
            logger.info("ADK web server will use port 8080 (configurable via ADK_WEB_PORT env var).")
            logger.info("MCP servers use stdio transport (no ports needed).")
            return runner
        else:
            # Standalone mode - run agent directly
            logger.info("Running agent in standalone mode (ADK not available)")
            logger.info("Agent is ready. Use the agent methods directly.")
            
            # Example: Run weekly management
            # Uncomment to run automatically:
            # result = await agent.run_weekly_management()
            # logger.info(f"Weekly management result: {result}")
            
            return agent
    except Exception as e:
        logger.error(f"Error starting agent: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    result = asyncio.run(main())
    logger.info("Agent started successfully!")
    logger.info("To use ADK web interface, run: make run-web or ./start_adk_web.sh")
    # Keep running for web interface
    # In production, this would be handled by ADK's deployment system
