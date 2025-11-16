"""Example usage of the Fantasy Football Agent."""
import asyncio
import logging
from app.agent import agent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def example_optimize_lineup():
    """Example: Optimize lineup for a specific week."""
    logger.info("Example: Optimizing lineup for week 5")
    result = await agent.optimize_lineup(week=5)
    logger.info(f"Result: {result}")
    return result


async def example_evaluate_waiver_wire():
    """Example: Evaluate waiver wire pickups."""
    logger.info("Example: Evaluating waiver wire")
    result = await agent.evaluate_waiver_wire()
    logger.info(f"Result: {result}")
    return result


async def example_evaluate_trades():
    """Example: Evaluate pending trades."""
    logger.info("Example: Evaluating trades")
    result = await agent.evaluate_trades()
    logger.info(f"Result: {result}")
    return result


async def example_full_weekly_management():
    """Example: Run full weekly management."""
    logger.info("Example: Running full weekly management")
    result = await agent.run_weekly_management()
    logger.info(f"Result: {result}")
    return result


async def example_get_team_data():
    """Example: Get current team data."""
    logger.info("Example: Getting team data")
    result = await agent.yahoo_tools.get_team_data()
    logger.info(f"Team: {result.get('team_name', 'Unknown')}")
    logger.info(f"Roster size: {len(result.get('roster', []))}")
    return result


async def main():
    """Run example functions."""
    print("=" * 60)
    print("Fantasy Football Agent - Example Usage")
    print("=" * 60)
    print()
    
    # Uncomment the examples you want to run:
    
    # Get team data
    # await example_get_team_data()
    
    # Optimize lineup
    # await example_optimize_lineup()
    
    # Evaluate waiver wire
    # await example_evaluate_waiver_wire()
    
    # Evaluate trades
    # await example_evaluate_trades()
    
    # Full weekly management
    # await example_full_weekly_management()
    
    print("\n" + "=" * 60)
    print("Examples completed. Uncomment functions in example_usage.py to run them.")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
