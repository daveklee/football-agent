"""FastAPI Backend server for the Fantasy Football Agent."""
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any, Optional
import uvicorn

from app.agent import agent
from app.utils.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Fantasy Football Agent API",
    description="API for managing Yahoo Fantasy Football team via AI agent",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "Fantasy Football Agent API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.post("/api/optimize-lineup")
async def optimize_lineup(week: Optional[int] = None) -> Dict[str, Any]:
    """Optimize lineup for a given week."""
    try:
        result = await agent.optimize_lineup(week=week)
        return {"success": True, "result": result}
    except Exception as e:
        logger.error(f"Error optimizing lineup: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/evaluate-waiver-wire")
async def evaluate_waiver_wire() -> Dict[str, Any]:
    """Evaluate waiver wire pickups."""
    try:
        result = await agent.evaluate_waiver_wire()
        return {"success": True, "result": result}
    except Exception as e:
        logger.error(f"Error evaluating waiver wire: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/evaluate-trades")
async def evaluate_trades() -> Dict[str, Any]:
    """Evaluate pending trades and propose new ones."""
    try:
        result = await agent.evaluate_trades()
        return {"success": True, "result": result}
    except Exception as e:
        logger.error(f"Error evaluating trades: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/weekly-management")
async def weekly_management() -> Dict[str, Any]:
    """Run all weekly management tasks."""
    try:
        result = await agent.run_weekly_management()
        return {"success": True, "result": result}
    except Exception as e:
        logger.error(f"Error running weekly management: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/team-data")
async def get_team_data() -> Dict[str, Any]:
    """Get current team data."""
    try:
        result = await agent._yahoo_tools.get_team_data()
        return {"success": True, "result": result}
    except Exception as e:
        logger.error(f"Error getting team data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def run_server(host: str = "0.0.0.0", port: int = None):
    """Run the FastAPI server."""
    if port is None:
        port = settings.adk_web_port
    
    logger.info(f"Starting FastAPI server on {host}:{port}")
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run_server()

