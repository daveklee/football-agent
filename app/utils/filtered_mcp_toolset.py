"""Filtered MCP Toolset wrapper that compresses tool outputs.

This module provides utilities for filtering MCP tool outputs to reduce
context window usage. Instead of wrapping the toolset (which breaks ADK
validation), we provide a post-processing approach using ADK callbacks.
"""
import logging
from typing import Any, Dict, List, Optional
from functools import wraps

logger = logging.getLogger(__name__)

# Try to import ADK MCP toolset
try:
    from google.adk.tools.mcp_tool import McpToolset
    from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    McpToolset = None
    StdioConnectionParams = None

from app.utils.tool_output_filter import filter_tool_output, get_output_filter
from app.utils.context_manager import estimate_tokens


# Global stats for tracking filtering effectiveness
_filtering_stats = {
    "total_calls": 0,
    "tokens_before": 0,
    "tokens_after": 0,
}


def get_filtering_stats() -> Dict[str, Any]:
    """Get global filtering statistics."""
    stats = dict(_filtering_stats)
    if stats["tokens_before"] > 0:
        stats["total_reduction"] = f"{(1 - stats['tokens_after'] / stats['tokens_before']) * 100:.1f}%"
        stats["tokens_saved"] = stats["tokens_before"] - stats["tokens_after"]
    return stats


def reset_filtering_stats():
    """Reset global filtering statistics."""
    global _filtering_stats
    _filtering_stats = {"total_calls": 0, "tokens_before": 0, "tokens_after": 0}


def create_filtered_mcp_toolset(
    connection_params: Any,
    tool_name_prefix: str = '',
    filter_enabled: bool = True,
    max_snapshot_tokens: int = 4000,
    max_output_tokens: int = 8000,
) -> Any:
    """Create an MCP toolset.
    
    Note: Direct output filtering via toolset wrapping is not supported by ADK.
    Instead, use the tool output filter callback system or post-process outputs.
    The filter_enabled parameter is kept for API compatibility but filtering
    happens via the agent's callback system.
    
    Args:
        connection_params: MCP connection parameters
        tool_name_prefix: Prefix for tool names
        filter_enabled: Whether filtering is intended (logged for debugging)
        max_snapshot_tokens: Max tokens for browser snapshots (used by callbacks)
        max_output_tokens: Max tokens for other outputs (used by callbacks)
        
    Returns:
        McpToolset instance
    """
    if not MCP_AVAILABLE:
        raise ImportError("Google ADK MCP tools not available")
    
    if filter_enabled:
        logger.info(f"MCP toolset '{tool_name_prefix}' created - output filtering via agent callbacks")
    
    return McpToolset(
        connection_params=connection_params,
        tool_name_prefix=tool_name_prefix
    )

