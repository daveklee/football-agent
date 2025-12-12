"""Tool output filtering and compression for reduced context usage.

This module wraps tool outputs to compress them before they're added to
the conversation context. Especially important for browser tools which
can return massive accessibility snapshots.
"""
import re
import json
import logging
from typing import Any, Dict, Optional, Callable
from functools import wraps

from app.utils.context_manager import (
    compress_browser_snapshot,
    compress_tool_output,
    estimate_tokens,
    truncate_to_tokens,
    DEFAULT_MAX_BROWSER_SNAPSHOT_TOKENS,
    DEFAULT_MAX_TOOL_OUTPUT_TOKENS,
)

logger = logging.getLogger(__name__)


# =============================================================================
# BROWSER-SPECIFIC FILTERS
# =============================================================================

def filter_browser_snapshot(snapshot: str, max_tokens: int = DEFAULT_MAX_BROWSER_SNAPSHOT_TOKENS) -> str:
    """Filter and compress browser accessibility snapshot.
    
    This is optimized for Yahoo Fantasy Football pages, keeping relevant
    elements while removing noise.
    
    Args:
        snapshot: Raw accessibility snapshot
        max_tokens: Maximum tokens to return
        
    Returns:
        Filtered snapshot
    """
    if not snapshot:
        return snapshot
    
    original_tokens = estimate_tokens(snapshot)
    
    # If small enough, return as-is
    if original_tokens <= max_tokens:
        return snapshot
    
    logger.info(f"Filtering browser snapshot: {original_tokens} tokens -> max {max_tokens}")
    
    lines = snapshot.split('\n')
    
    # Priority 1: Interactive elements (buttons, links, inputs)
    interactive = []
    # Priority 2: Player/roster related content
    roster_content = []
    # Priority 3: Other meaningful content
    other_content = []
    
    # Patterns for interactive elements
    interactive_patterns = [
        r'button',
        r'link\s',
        r'textbox',
        r'combobox',
        r'checkbox',
        r'radio',
        r'switch',
        r'menuitem',
        r'tab\s',
        r'option',
    ]
    interactive_re = re.compile('|'.join(interactive_patterns), re.IGNORECASE)
    
    # Patterns for roster/fantasy content (Yahoo Fantasy specific)
    roster_patterns = [
        r'player',
        r'roster',
        r'lineup',
        r'bench',
        r'flex',
        r'qb|rb|wr|te|k|def',
        r'start',
        r'proj',
        r'points',
        r'score',
        r'vs\.',
        r'opponent',
        r'matchup',
        r'waiver',
        r'trade',
        r'add|drop',
        r'move',
        r'slot',
    ]
    roster_re = re.compile('|'.join(roster_patterns), re.IGNORECASE)
    
    # Skip patterns (noise)
    skip_patterns = [
        r'^\s*-\s*generic\s*$',
        r'^\s*-\s*none\s*$',
        r'^\s*-\s*paragraph\s*$',
        r'^\s*-\s*group\s*$',
        r'^\s*StaticText\s*$',
        r'advertisement',
        r'sponsor',
        r'cookie',
        r'privacy',
        r'terms\s+of\s+service',
    ]
    skip_re = re.compile('|'.join(skip_patterns), re.IGNORECASE)
    
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        
        # Skip noise
        if skip_re.search(line):
            continue
        
        # Truncate very long lines
        if len(line) > 200:
            line = line[:200] + "..."
        
        # Categorize by priority
        if interactive_re.search(line):
            interactive.append(line)
        elif roster_re.search(line):
            roster_content.append(line)
        else:
            # Only keep shallow elements (not deeply nested)
            indent = len(line) - len(line.lstrip())
            if indent < 10 and len(stripped) > 3:
                other_content.append(line)
    
    # Build output with priority
    output_lines = []
    current_tokens = 0
    
    # Add header
    header = f"[Browser snapshot filtered from {original_tokens} tokens]\n"
    output_lines.append(header)
    current_tokens += estimate_tokens(header)
    
    # Add interactive elements first (most important)
    for line in interactive:
        line_tokens = estimate_tokens(line)
        if current_tokens + line_tokens < max_tokens * 0.5:  # 50% for interactive
            output_lines.append(line)
            current_tokens += line_tokens
    
    # Add roster content
    for line in roster_content:
        line_tokens = estimate_tokens(line)
        if current_tokens + line_tokens < max_tokens * 0.85:  # 85% total
            output_lines.append(line)
            current_tokens += line_tokens
    
    # Fill remaining with other content
    for line in other_content:
        line_tokens = estimate_tokens(line)
        if current_tokens + line_tokens < max_tokens:
            output_lines.append(line)
            current_tokens += line_tokens
        else:
            break
    
    result = '\n'.join(output_lines)
    
    # Add truncation notice if we couldn't fit everything
    if len(interactive) + len(roster_content) + len(other_content) > len(output_lines) - 1:
        result += f"\n[... additional content truncated]"
    
    final_tokens = estimate_tokens(result)
    logger.info(f"Browser snapshot filtered: {original_tokens} -> {final_tokens} tokens ({(1 - final_tokens/original_tokens)*100:.1f}% reduction)")
    
    return result


def filter_browser_screenshot_result(result: Any) -> Any:
    """Filter screenshot tool result.
    
    Screenshots return metadata + base64 image. We keep metadata but
    note that the image is available (the LLM can still see it).
    """
    if isinstance(result, dict):
        # Keep essential metadata, note that image exists
        filtered = {
            "status": result.get("status", "unknown"),
            "message": result.get("message", "Screenshot captured"),
        }
        if "width" in result:
            filtered["dimensions"] = f"{result.get('width')}x{result.get('height')}"
        return filtered
    return result


def filter_yahoo_api_result(result: Any, max_tokens: int = DEFAULT_MAX_TOOL_OUTPUT_TOKENS) -> Any:
    """Filter Yahoo Fantasy API results.
    
    Yahoo API can return large roster/player data. Keep essential fields.
    """
    if not isinstance(result, dict):
        return compress_tool_output("yahoo", result, max_tokens)
    
    # Essential fields to keep for roster data
    roster_essential_fields = {
        'player_id', 'name', 'position', 'team', 'status',
        'projected_points', 'actual_points', 'roster_position',
        'is_starter', 'eligible_positions', 'injury_status',
        'bye_week', 'opponent', 'game_time'
    }
    
    def filter_player(player: dict) -> dict:
        """Keep only essential player fields."""
        if not isinstance(player, dict):
            return player
        return {k: v for k, v in player.items() if k in roster_essential_fields}
    
    filtered = {}
    for key, value in result.items():
        if key in ('roster', 'players', 'starters', 'bench'):
            if isinstance(value, list):
                filtered[key] = [filter_player(p) for p in value]
            else:
                filtered[key] = value
        elif isinstance(value, str) and len(value) > 500:
            filtered[key] = value[:500] + "..."
        else:
            filtered[key] = value
    
    # Final compression check
    return compress_tool_output("yahoo", filtered, max_tokens)


# =============================================================================
# GENERIC OUTPUT FILTER
# =============================================================================

def filter_tool_output(tool_name: str, result: Any) -> Any:
    """Filter any tool output based on tool type.
    
    Args:
        tool_name: Name of the tool
        result: Tool output
        
    Returns:
        Filtered output
    """
    tool_lower = tool_name.lower()
    
    # Browser snapshot filtering
    if 'snapshot' in tool_lower:
        if isinstance(result, str):
            return filter_browser_snapshot(result)
        elif isinstance(result, dict) and 'content' in result:
            result['content'] = filter_browser_snapshot(result['content'])
            return result
    
    # Screenshot filtering
    if 'screenshot' in tool_lower:
        return filter_browser_screenshot_result(result)
    
    # Yahoo API filtering
    if 'yahoo' in tool_lower:
        return filter_yahoo_api_result(result)
    
    # Generic compression for other tools
    return compress_tool_output(tool_name, result)


# =============================================================================
# TOOL WRAPPER FOR ADK
# =============================================================================

class ToolOutputFilter:
    """Wrapper that filters tool outputs before returning to LLM.
    
    This can be used to wrap MCP toolsets or individual tools.
    """
    
    def __init__(
        self,
        max_snapshot_tokens: int = DEFAULT_MAX_BROWSER_SNAPSHOT_TOKENS,
        max_output_tokens: int = DEFAULT_MAX_TOOL_OUTPUT_TOKENS,
        enabled: bool = True
    ):
        self.max_snapshot_tokens = max_snapshot_tokens
        self.max_output_tokens = max_output_tokens
        self.enabled = enabled
        self._stats = {
            "calls_filtered": 0,
            "tokens_saved": 0,
        }
    
    def filter(self, tool_name: str, result: Any) -> Any:
        """Filter a tool result.
        
        Args:
            tool_name: Name of the tool
            result: Tool output
            
        Returns:
            Filtered output
        """
        if not self.enabled:
            return result
        
        original_tokens = estimate_tokens(str(result))
        filtered = filter_tool_output(tool_name, result)
        filtered_tokens = estimate_tokens(str(filtered))
        
        self._stats["calls_filtered"] += 1
        self._stats["tokens_saved"] += max(0, original_tokens - filtered_tokens)
        
        if original_tokens != filtered_tokens:
            logger.debug(f"Tool {tool_name}: {original_tokens} -> {filtered_tokens} tokens")
        
        return filtered
    
    def get_stats(self) -> dict:
        """Get filtering statistics."""
        return dict(self._stats)
    
    def reset_stats(self):
        """Reset statistics."""
        self._stats = {"calls_filtered": 0, "tokens_saved": 0}


# Global filter instance
_output_filter: Optional[ToolOutputFilter] = None


def get_output_filter() -> ToolOutputFilter:
    """Get or create the global output filter."""
    global _output_filter
    if _output_filter is None:
        _output_filter = ToolOutputFilter()
    return _output_filter


def create_filtered_tool_callback(original_callback: Optional[Callable] = None) -> Callable:
    """Create a tool callback that filters outputs.
    
    This can be used as on_tool_result_callback in ADK agents.
    
    Args:
        original_callback: Optional original callback to chain
        
    Returns:
        Callback function that filters tool outputs
    """
    output_filter = get_output_filter()
    
    async def filtered_callback(tool: Any, args: Dict[str, Any], tool_context: Any, result: Any) -> Any:
        # Get tool name
        tool_name = getattr(tool, 'name', str(tool))
        
        # Filter the result
        filtered_result = output_filter.filter(tool_name, result)
        
        # Chain to original callback if provided
        if original_callback:
            return await original_callback(tool, args, tool_context, filtered_result)
        
        return filtered_result
    
    return filtered_callback



