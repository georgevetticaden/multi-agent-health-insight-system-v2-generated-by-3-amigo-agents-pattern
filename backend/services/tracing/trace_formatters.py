"""
Formatting utilities for trace viewer.

Provides functions for formatting durations, data, and other trace elements
for better human readability.
"""

from typing import Any, Dict, List, Optional, Tuple
import json


def format_duration(duration_ms: Optional[float]) -> str:
    """
    Format duration from milliseconds to human-readable format.
    
    Args:
        duration_ms: Duration in milliseconds
        
    Returns:
        Formatted duration string
        
    Examples:
        - 543ms -> "543 ms"
        - 1234ms -> "1.2 sec"
        - 65432ms -> "1 min 5 sec"
        - 3665432ms -> "61 min 5 sec"
    """
    if duration_ms is None:
        return "N/A"
    
    # Less than 1 second
    if duration_ms < 1000:
        return f"{duration_ms:.0f} ms"
    
    # Less than 60 seconds
    elif duration_ms < 60000:
        seconds = duration_ms / 1000
        return f"{seconds:.1f} sec"
    
    # 60 seconds or more
    else:
        total_seconds = int(duration_ms / 1000)
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        
        if seconds == 0:
            return f"{minutes} min"
        else:
            return f"{minutes} min {seconds} sec"


def format_token_count(tokens: Optional[int]) -> str:
    """
    Format token count with appropriate units.
    
    Args:
        tokens: Number of tokens
        
    Returns:
        Formatted token string
    """
    if tokens is None:
        return "0"
    
    if tokens < 1000:
        return str(tokens)
    elif tokens < 1000000:
        return f"{tokens/1000:.1f}K"
    else:
        return f"{tokens/1000000:.1f}M"


def estimate_api_cost(total_tokens: int, model: str = "claude-3-5-sonnet") -> float:
    """
    Estimate API cost based on token usage.
    
    Args:
        total_tokens: Total tokens used
        model: Model name for pricing
        
    Returns:
        Estimated cost in USD
    """
    # Approximate pricing per 1M tokens (as of 2024)
    # These are rough estimates and should be updated based on actual pricing
    pricing_per_million = {
        "claude-3-5-sonnet": 15.00,  # $15 per 1M tokens
        "claude-3-opus": 75.00,      # $75 per 1M tokens
        "claude-3-haiku": 1.25,      # $1.25 per 1M tokens
        "claude-2.1": 24.00,         # $24 per 1M tokens
        "claude-2": 24.00,           # $24 per 1M tokens
        "claude-instant": 2.40,      # $2.40 per 1M tokens
    }
    
    # Default to sonnet pricing if model not found
    price_per_million = pricing_per_million.get(model, 15.00)
    
    # Calculate cost
    cost = (total_tokens / 1_000_000) * price_per_million
    
    return round(cost, 4)


def format_cost(cost: float) -> str:
    """
    Format cost with appropriate precision.
    
    Args:
        cost: Cost in USD
        
    Returns:
        Formatted cost string
    """
    if cost < 0.01:
        return f"${cost:.4f}"
    elif cost < 1.00:
        return f"${cost:.3f}"
    else:
        return f"${cost:.2f}"


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate text to specified length with suffix.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add when truncated
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def format_json_for_display(data: Any, indent: int = 2, max_depth: int = 5) -> str:
    """
    Format JSON data for display with proper indentation and depth control.
    
    Args:
        data: Data to format
        indent: Indentation level
        max_depth: Maximum depth to expand
        
    Returns:
        Formatted JSON string
    """
    try:
        return json.dumps(data, indent=indent, ensure_ascii=False)
    except Exception:
        return str(data)


def extract_prompt_components(messages: List[Dict[str, Any]], system_prompt: Optional[str] = None) -> Dict[str, Any]:
    """
    Extract and separate prompt components from message history.
    
    Args:
        messages: List of conversation messages
        system_prompt: Optional system prompt
        
    Returns:
        Dictionary with separated components
    """
    if not messages:
        return {
            "current_prompt": "",
            "conversation_history": [],
            "system_prompt": system_prompt or "",
            "history_size": 0
        }
    
    # Last message is typically the current prompt
    current_message = messages[-1] if messages else {"content": ""}
    
    # Previous messages are conversation history
    history = messages[:-1] if len(messages) > 1 else []
    
    return {
        "current_prompt": current_message.get("content", ""),
        "conversation_history": history,
        "system_prompt": system_prompt or "",
        "history_size": len(history),
        "total_messages": len(messages)
    }


def format_tool_result_summary(result: Any, tool_name: str) -> str:
    """
    Create a summary of tool results for display.
    
    Args:
        result: Tool execution result
        tool_name: Name of the tool
        
    Returns:
        Formatted summary string
    """
    if isinstance(result, dict):
        if "error" in result:
            return f"❌ Error: {result['error']}"
        
        if "query_successful" in result:
            success = result.get("query_successful", False)
            count = result.get("result_count", 0)
            
            if success:
                return f"✅ Success: {count} results found"
            else:
                return f"⚠️ No results found"
        
        # Generic dict summary
        keys = list(result.keys())[:3]
        return f"✅ Result with keys: {', '.join(keys)}"
    
    elif isinstance(result, list):
        return f"✅ List with {len(result)} items"
    
    elif isinstance(result, str):
        return f"✅ {truncate_text(result, 50)}"
    
    else:
        return f"✅ {type(result).__name__} result"


def calculate_performance_metrics(events: List[Any]) -> Dict[str, Any]:
    """
    Calculate performance metrics from trace events.
    
    Args:
        events: List of trace events
        
    Returns:
        Dictionary of performance metrics
    """
    metrics = {
        "avg_llm_response_time": 0,
        "avg_tool_execution_time": 0,
        "parallel_execution_savings": 0,
        "slowest_operation": None,
        "retry_count": 0,
        "error_rate": 0
    }
    
    # Calculate average response times
    llm_times = []
    tool_times = []
    
    for event in events:
        if hasattr(event, 'duration_ms') and event.duration_ms:
            if event.event_type.value == "llm_response":
                llm_times.append(event.duration_ms)
            elif event.event_type.value == "tool_result":
                tool_times.append(event.duration_ms)
    
    if llm_times:
        metrics["avg_llm_response_time"] = sum(llm_times) / len(llm_times)
    
    if tool_times:
        metrics["avg_tool_execution_time"] = sum(tool_times) / len(tool_times)
    
    # Find slowest operation
    all_timed_events = [e for e in events if hasattr(e, 'duration_ms') and e.duration_ms]
    if all_timed_events:
        slowest = max(all_timed_events, key=lambda e: e.duration_ms)
        metrics["slowest_operation"] = {
            "type": slowest.event_type.value,
            "duration": slowest.duration_ms,
            "agent": slowest.agent_type
        }
    
    # Calculate error rate
    total_operations = len([e for e in events if e.event_type.value in ["llm_prompt", "tool_invocation"]])
    errors = len([e for e in events if e.event_type.value == "error"])
    
    if total_operations > 0:
        metrics["error_rate"] = errors / total_operations
    
    return metrics