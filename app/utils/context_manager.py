"""Context window management for reducing token usage with Gemini.

This module provides utilities to:
1. Estimate token counts for text
2. Compress/truncate tool outputs (especially browser snapshots)
3. Manage conversation history to stay within context limits
4. Summarize verbose outputs
"""
import re
import logging
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# Approximate tokens per character for English text
# Gemini uses a similar tokenization to other LLMs (~4 chars per token)
CHARS_PER_TOKEN = 4

# Default context limits (Gemini 2.5 Pro has 1M context, but staying efficient)
DEFAULT_MAX_CONTEXT_TOKENS = 100_000  # Conservative limit for efficiency
DEFAULT_MAX_TOOL_OUTPUT_TOKENS = 8_000  # Max tokens per tool output
DEFAULT_MAX_BROWSER_SNAPSHOT_TOKENS = 4_000  # Browser snapshots can be huge
DEFAULT_MAX_HISTORY_TOKENS = 50_000  # Max tokens for conversation history


@dataclass
class ContextBudget:
    """Tracks context window budget and usage."""
    max_tokens: int = DEFAULT_MAX_CONTEXT_TOKENS
    system_prompt_tokens: int = 0
    history_tokens: int = 0
    current_turn_tokens: int = 0
    
    @property
    def used_tokens(self) -> int:
        return self.system_prompt_tokens + self.history_tokens + self.current_turn_tokens
    
    @property
    def remaining_tokens(self) -> int:
        return max(0, self.max_tokens - self.used_tokens)
    
    @property
    def usage_percentage(self) -> float:
        return (self.used_tokens / self.max_tokens) * 100 if self.max_tokens > 0 else 0


def estimate_tokens(text: str) -> int:
    """Estimate token count for a string.
    
    Args:
        text: The text to estimate tokens for
        
    Returns:
        Estimated token count
    """
    if not text:
        return 0
    return len(text) // CHARS_PER_TOKEN


def truncate_to_tokens(text: str, max_tokens: int, suffix: str = "\n... [truncated]") -> str:
    """Truncate text to approximately max_tokens.
    
    Args:
        text: Text to truncate
        max_tokens: Maximum tokens to allow
        suffix: Suffix to add when truncating
        
    Returns:
        Truncated text
    """
    if not text:
        return text
    
    estimated = estimate_tokens(text)
    if estimated <= max_tokens:
        return text
    
    # Calculate max chars (accounting for suffix)
    suffix_tokens = estimate_tokens(suffix)
    max_chars = (max_tokens - suffix_tokens) * CHARS_PER_TOKEN
    
    if max_chars <= 0:
        return suffix
    
    return text[:max_chars] + suffix


def compress_browser_snapshot(snapshot: str, max_tokens: int = DEFAULT_MAX_BROWSER_SNAPSHOT_TOKENS) -> str:
    """Compress a browser accessibility snapshot to reduce token usage.
    
    Browser snapshots contain lots of redundant information. This function:
    1. Removes excessive whitespace
    2. Filters out non-interactive/non-essential elements
    3. Truncates very long text content
    4. Keeps structure but reduces verbosity
    
    Args:
        snapshot: Raw browser snapshot text
        max_tokens: Maximum tokens to allow
        
    Returns:
        Compressed snapshot
    """
    if not snapshot:
        return snapshot
    
    original_tokens = estimate_tokens(snapshot)
    
    # If already under limit, return as-is
    if original_tokens <= max_tokens:
        return snapshot
    
    logger.info(f"Compressing browser snapshot from ~{original_tokens} to ~{max_tokens} tokens")
    
    lines = snapshot.split('\n')
    compressed_lines = []
    
    # Patterns to identify important vs. skippable elements
    important_patterns = [
        r'button',
        r'link',
        r'input',
        r'select',
        r'checkbox',
        r'radio',
        r'heading',
        r'tab',
        r'menu',
        r'dialog',
        r'alert',
        r'table',
        r'row',
        r'cell',
        r'listitem',
        r'player',  # Fantasy football specific
        r'roster',
        r'lineup',
        r'bench',
        r'score',
        r'points',
        r'projection',
    ]
    important_regex = re.compile('|'.join(important_patterns), re.IGNORECASE)
    
    # Patterns to skip (decorative/structural elements)
    skip_patterns = [
        r'^\s*-\s*generic\s*$',
        r'^\s*-\s*group\s*$',
        r'^\s*-\s*region\s*$',
        r'^\s*-\s*separator\s*$',
        r'^\s*-\s*img\s+',  # Images without alt text
        r'^\s*StaticText\s*$',
        r'^\s*-\s*none\s*$',
    ]
    skip_regex = re.compile('|'.join(skip_patterns), re.IGNORECASE)
    
    for line in lines:
        # Skip empty lines
        if not line.strip():
            continue
        
        # Skip purely decorative elements
        if skip_regex.search(line):
            continue
        
        # Keep important interactive elements
        if important_regex.search(line):
            # Truncate very long lines (e.g., long text content)
            if len(line) > 200:
                line = line[:200] + "..."
            compressed_lines.append(line)
        else:
            # For non-important lines, only keep if they have meaningful content
            # and are not too deeply nested (reduce structural noise)
            indent_level = len(line) - len(line.lstrip())
            if indent_level < 12 and len(line.strip()) > 5:  # Not too deep, has content
                # Truncate long lines
                if len(line) > 150:
                    line = line[:150] + "..."
                compressed_lines.append(line)
    
    compressed = '\n'.join(compressed_lines)
    
    # If still too large, do a hard truncate
    compressed_tokens = estimate_tokens(compressed)
    if compressed_tokens > max_tokens:
        compressed = truncate_to_tokens(
            compressed, 
            max_tokens,
            suffix="\n... [snapshot truncated - use targeted selectors for more detail]"
        )
    
    final_tokens = estimate_tokens(compressed)
    logger.info(f"Browser snapshot compressed: {original_tokens} -> {final_tokens} tokens ({(1 - final_tokens/original_tokens)*100:.1f}% reduction)")
    
    return compressed


def compress_tool_output(
    tool_name: str, 
    output: Any, 
    max_tokens: int = DEFAULT_MAX_TOOL_OUTPUT_TOKENS
) -> Any:
    """Compress tool output based on tool type.
    
    Args:
        tool_name: Name of the tool that produced the output
        output: The tool output to compress
        max_tokens: Maximum tokens to allow
        
    Returns:
        Compressed output
    """
    # Handle string outputs
    if isinstance(output, str):
        # Browser snapshot compression
        if 'snapshot' in tool_name.lower() or 'browser' in tool_name.lower():
            return compress_browser_snapshot(output, max_tokens)
        
        # General text truncation
        return truncate_to_tokens(output, max_tokens)
    
    # Handle dict outputs
    if isinstance(output, dict):
        return _compress_dict_output(tool_name, output, max_tokens)
    
    # Handle list outputs
    if isinstance(output, list):
        return _compress_list_output(tool_name, output, max_tokens)
    
    return output


def _compress_dict_output(tool_name: str, output: dict, max_tokens: int) -> dict:
    """Compress dictionary output."""
    # Convert to string to check size
    import json
    try:
        output_str = json.dumps(output, indent=2, default=str)
    except:
        output_str = str(output)
    
    if estimate_tokens(output_str) <= max_tokens:
        return output
    
    # Compress nested values
    compressed = {}
    for key, value in output.items():
        if isinstance(value, str):
            compressed[key] = truncate_to_tokens(value, max_tokens // len(output))
        elif isinstance(value, (dict, list)):
            # Recursively compress with reduced budget
            compressed[key] = compress_tool_output(tool_name, value, max_tokens // len(output))
        else:
            compressed[key] = value
    
    return compressed


def _compress_list_output(tool_name: str, output: list, max_tokens: int) -> list:
    """Compress list output."""
    import json
    try:
        output_str = json.dumps(output, indent=2, default=str)
    except:
        output_str = str(output)
    
    if estimate_tokens(output_str) <= max_tokens:
        return output
    
    # If list is very long, truncate to first N items
    max_items = max(5, max_tokens // 500)  # At least 5 items, or estimate based on tokens
    
    if len(output) > max_items:
        compressed = output[:max_items]
        # Add indicator that list was truncated
        compressed.append({"_truncated": f"... {len(output) - max_items} more items"})
        return compressed
    
    # Compress individual items
    per_item_budget = max_tokens // len(output) if output else max_tokens
    return [compress_tool_output(tool_name, item, per_item_budget) for item in output]


def summarize_conversation_history(
    messages: List[Dict[str, Any]], 
    max_tokens: int = DEFAULT_MAX_HISTORY_TOKENS
) -> List[Dict[str, Any]]:
    """Summarize conversation history to fit within token budget.
    
    Strategy:
    1. Keep the most recent messages intact (most relevant)
    2. Compress older tool outputs
    3. Summarize very old messages if needed
    
    Args:
        messages: List of conversation messages
        max_tokens: Maximum tokens for history
        
    Returns:
        Compressed message history
    """
    if not messages:
        return messages
    
    # Calculate total tokens
    total_tokens = sum(estimate_tokens(str(m)) for m in messages)
    
    if total_tokens <= max_tokens:
        return messages
    
    logger.info(f"Compressing conversation history from ~{total_tokens} to ~{max_tokens} tokens")
    
    # Keep last 5 messages intact (most recent context)
    keep_recent = min(5, len(messages))
    recent_messages = messages[-keep_recent:]
    older_messages = messages[:-keep_recent] if len(messages) > keep_recent else []
    
    # Calculate budget for older messages
    recent_tokens = sum(estimate_tokens(str(m)) for m in recent_messages)
    older_budget = max(0, max_tokens - recent_tokens)
    
    if older_budget <= 0 or not older_messages:
        return recent_messages
    
    # Compress older messages
    compressed_older = []
    per_message_budget = older_budget // len(older_messages)
    
    for msg in older_messages:
        compressed_msg = dict(msg)
        
        # Compress content if it's a string
        if 'content' in compressed_msg and isinstance(compressed_msg['content'], str):
            compressed_msg['content'] = truncate_to_tokens(
                compressed_msg['content'], 
                per_message_budget
            )
        
        # Compress tool outputs
        if 'tool_output' in compressed_msg:
            compressed_msg['tool_output'] = compress_tool_output(
                compressed_msg.get('tool_name', 'unknown'),
                compressed_msg['tool_output'],
                per_message_budget // 2
            )
        
        compressed_older.append(compressed_msg)
    
    return compressed_older + recent_messages


class ContextManager:
    """Manages context window budget for an agent session."""
    
    def __init__(
        self,
        max_context_tokens: int = DEFAULT_MAX_CONTEXT_TOKENS,
        max_tool_output_tokens: int = DEFAULT_MAX_TOOL_OUTPUT_TOKENS,
        max_browser_snapshot_tokens: int = DEFAULT_MAX_BROWSER_SNAPSHOT_TOKENS,
        max_history_tokens: int = DEFAULT_MAX_HISTORY_TOKENS
    ):
        self.max_context_tokens = max_context_tokens
        self.max_tool_output_tokens = max_tool_output_tokens
        self.max_browser_snapshot_tokens = max_browser_snapshot_tokens
        self.max_history_tokens = max_history_tokens
        self.budget = ContextBudget(max_tokens=max_context_tokens)
        self._message_history: List[Dict[str, Any]] = []
    
    def set_system_prompt_tokens(self, tokens: int):
        """Record system prompt token usage."""
        self.budget.system_prompt_tokens = tokens
    
    def compress_tool_output(self, tool_name: str, output: Any) -> Any:
        """Compress a tool output based on tool type."""
        # Use stricter limits for browser tools
        if 'browser' in tool_name.lower() or 'snapshot' in tool_name.lower():
            max_tokens = self.max_browser_snapshot_tokens
        else:
            max_tokens = self.max_tool_output_tokens
        
        compressed = compress_tool_output(tool_name, output, max_tokens)
        
        # Update budget
        self.budget.current_turn_tokens += estimate_tokens(str(compressed))
        
        return compressed
    
    def add_message(self, message: Dict[str, Any]):
        """Add a message to history, compressing if needed."""
        self._message_history.append(message)
        
        # Check if we need to compress history
        history_tokens = sum(estimate_tokens(str(m)) for m in self._message_history)
        
        if history_tokens > self.max_history_tokens:
            self._message_history = summarize_conversation_history(
                self._message_history,
                self.max_history_tokens
            )
        
        self.budget.history_tokens = sum(estimate_tokens(str(m)) for m in self._message_history)
    
    def get_compressed_history(self) -> List[Dict[str, Any]]:
        """Get the compressed message history."""
        return self._message_history
    
    def reset_turn(self):
        """Reset current turn token count."""
        self.budget.current_turn_tokens = 0
    
    def get_status(self) -> Dict[str, Any]:
        """Get current context budget status."""
        return {
            "max_tokens": self.budget.max_tokens,
            "used_tokens": self.budget.used_tokens,
            "remaining_tokens": self.budget.remaining_tokens,
            "usage_percentage": f"{self.budget.usage_percentage:.1f}%",
            "breakdown": {
                "system_prompt": self.budget.system_prompt_tokens,
                "history": self.budget.history_tokens,
                "current_turn": self.budget.current_turn_tokens
            }
        }


# Singleton instance for global access
_context_manager: Optional[ContextManager] = None


def get_context_manager() -> ContextManager:
    """Get or create the global context manager."""
    global _context_manager
    if _context_manager is None:
        _context_manager = ContextManager()
    return _context_manager


def reset_context_manager():
    """Reset the global context manager."""
    global _context_manager
    _context_manager = None


