"""
Anthropic API streaming utility with retry logic

Provides a unified interface for streaming API calls with consistent retry handling.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Union, AsyncGenerator
from dataclasses import dataclass
from enum import Enum

from anthropic import Anthropic
from anthropic.types import Message, ToolUseBlock, TextBlock

# Import tracing components
try:
    from services.tracing import get_trace_collector, TraceEventType
    TRACING_AVAILABLE = True
except ImportError:
    TRACING_AVAILABLE = False

logger = logging.getLogger(__name__)


class StreamingMode(Enum):
    """Different modes of streaming based on use case"""
    TOOL_USE = "tool_use"          # For tool calling scenarios
    TEXT_GENERATION = "text_generation"  # For pure text generation
    VISUALIZATION = "visualization"      # For visualization code generation


@dataclass
class StreamingResponse:
    """Unified response from streaming operations"""
    message: Optional[Message] = None
    content: str = ""
    tool_calls: List[ToolUseBlock] = None
    error: Optional[str] = None
    
    def __post_init__(self):
        if self.tool_calls is None:
            self.tool_calls = []


class AnthropicStreamingClient:
    """
    Unified client for Anthropic streaming API with retry logic
    
    Handles common patterns:
    - Retry on overload/rate limit errors
    - Exponential backoff
    - Consistent error handling
    - Different streaming modes
    """
    
    def __init__(
        self,
        client: Anthropic,
        max_retries: int = 5,
        initial_retry_delay: int = 3,
        max_retry_delay: int = 30
    ):
        self.client = client
        self.max_retries = max_retries
        self.initial_retry_delay = initial_retry_delay
        self.max_retry_delay = max_retry_delay
        
    async def stream_with_retry(
        self,
        model: str,
        messages: List[Dict[str, Any]],
        max_tokens: int,
        system: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        mode: StreamingMode = StreamingMode.TEXT_GENERATION,
        context_label: str = "API call",
        collect_content: bool = True
    ) -> StreamingResponse:
        """
        Execute streaming API call with retry logic
        
        Args:
            model: Anthropic model to use
            messages: Conversation messages
            max_tokens: Maximum tokens for response
            system: System prompt (optional)
            tools: Tool definitions (optional)
            mode: Streaming mode to determine processing
            context_label: Label for logging context
            collect_content: Whether to collect full content (for non-visualization modes)
            
        Returns:
            StreamingResponse with results
        """
        
        retry_delay = self.initial_retry_delay
        
        for attempt in range(self.max_retries):
            try:
                logger.info(f"{context_label} - attempt {attempt + 1}/{self.max_retries}")
                
                # Build kwargs for streaming
                kwargs = {
                    "model": model,
                    "messages": messages,
                    "max_tokens": max_tokens
                }
                
                if system:
                    kwargs["system"] = system
                if tools:
                    kwargs["tools"] = tools
                
                # Create stream
                stream = self.client.messages.stream(**kwargs)
                
                # Process based on mode
                if mode == StreamingMode.TOOL_USE:
                    return await self._process_tool_stream(stream, context_label)
                elif mode == StreamingMode.TEXT_GENERATION:
                    return await self._process_text_stream(stream, context_label, collect_content)
                else:  # VISUALIZATION mode is handled separately for async generation
                    return await self._process_text_stream(stream, context_label, collect_content)
                    
            except Exception as e:
                error_message = str(e).lower()
                # Be more specific about retryable errors
                is_retryable = (
                    any(term in error_message for term in ["overloaded", "rate_limit", "too_many_requests"]) or
                    "429" in error_message or  # HTTP 429 Too Many Requests
                    type(e).__name__ in ["RateLimitError", "APIStatusError"]
                )
                
                # Log the actual error for debugging
                logger.error(f"{context_label} - Error type: {type(e).__name__}, Message: {str(e)}")
                
                if is_retryable and attempt < self.max_retries - 1:
                    logger.warning(
                        f"{context_label} - API overloaded, attempt {attempt + 1}/{self.max_retries}, "
                        f"retrying in {retry_delay} seconds..."
                    )
                    await asyncio.sleep(retry_delay)
                    retry_delay = min(retry_delay * 2, self.max_retry_delay)
                else:
                    logger.error(f"{context_label} - streaming error: {str(e)}")
                    if attempt == self.max_retries - 1:
                        logger.error(f"{context_label} - failed after {self.max_retries} attempts")
                    raise
        
        # Should never reach here
        return StreamingResponse(error=f"{context_label} - Failed after all retry attempts")
    
    async def _process_tool_stream(
        self, 
        stream, 
        context_label: str
    ) -> StreamingResponse:
        """Process stream for tool use scenarios"""
        try:
            with stream as s:
                # Log streaming progress
                for event in s:
                    if event.type == "content_block_delta":
                        if hasattr(event.delta, 'type') and event.delta.type == "text_delta":
                            logger.debug(f"{context_label} streaming: {event.delta.text[:50]}...")
                
                # Get final message
                message = s.get_final_message()
                
            # Extract tool calls and text
            tool_calls = []
            content = ""
            
            for block in message.content:
                if isinstance(block, ToolUseBlock):
                    tool_calls.append(block)
                elif isinstance(block, TextBlock):
                    content += block.text
            
            return StreamingResponse(
                message=message,
                content=content,
                tool_calls=tool_calls
            )
        except Exception as e:
            logger.error(f"{context_label} - Error in _process_tool_stream: {type(e).__name__}: {str(e)}")
            raise
    
    async def _process_text_stream(
        self, 
        stream, 
        context_label: str,
        collect_content: bool = True
    ) -> StreamingResponse:
        """Process stream for text generation"""
        content = ""
        
        try:
            with stream as s:
                for event in s:
                    if event.type == "content_block_delta":
                        if hasattr(event.delta, 'type') and event.delta.type == "text_delta":
                            if collect_content:
                                content += event.delta.text
                            logger.debug(f"{context_label} streaming text...")
                
                # Get final message
                final_message = s.get_final_message()
                if final_message.content and collect_content:
                    # Use the complete content from final message
                    content = final_message.content[0].text if final_message.content else content
            
            return StreamingResponse(
                message=final_message,
                content=content
            )
        except Exception as e:
            logger.error(f"{context_label} - Error in _process_text_stream: {type(e).__name__}: {str(e)}")
            raise
    
    async def stream_visualization(
        self,
        model: str,
        messages: List[Dict[str, Any]],
        max_tokens: int,
        context_label: str = "Visualization"
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Special handling for visualization streaming that yields chunks
        
        This is separate because visualization needs to yield chunks as they come
        rather than collecting the full response.
        """
        
        retry_delay = self.initial_retry_delay
        code_block_started = False
        start_time = asyncio.get_event_loop().time()
        
        # Record prompt event if tracing is enabled
        prompt_event_id = None
        if TRACING_AVAILABLE:
            trace_collector = get_trace_collector()
            if trace_collector:
                prompt_data = {
                    "prompt_file": "visualization_generation.txt",
                    "model": model,
                    "max_tokens": max_tokens,
                    "messages": messages,
                    "message_count": len(messages),
                    "prompt_length": sum(len(msg.get('content', '')) for msg in messages)
                }
                
                prompt_event_id = await trace_collector.add_event(
                    event_type=TraceEventType.LLM_PROMPT,
                    agent_type="visualization",
                    stage="visualization_generation",
                    data=prompt_data
                )
        
        for attempt in range(self.max_retries):
            try:
                stream = self.client.messages.stream(
                    model=model,
                    messages=messages,
                    max_tokens=max_tokens
                )
                
                # Send code block start
                if not code_block_started:
                    yield {
                        "type": "text",
                        "content": "\n\n```javascript\n"
                    }
                    code_block_started = True
                
                # Stream the code as it's generated
                full_code = ""
                first_chunk = True
                code_block_detected = False
                
                try:
                    with stream as s:
                        for event in s:
                            if event.type == "content_block_delta":
                                if hasattr(event.delta, 'type') and event.delta.type == "text_delta":
                                    text = event.delta.text
                                    
                                    # Only remove code block markers at the very beginning
                                    if first_chunk and not code_block_detected:
                                        # Check if response starts with code block
                                        if text.strip().startswith("```"):
                                            code_block_detected = True
                                            # Remove the opening code block
                                            text = text.strip()
                                            if text.startswith("```javascript"):
                                                text = text.replace("```javascript", "", 1).lstrip("\n")
                                            elif text.startswith("```jsx"):
                                                text = text.replace("```jsx", "", 1).lstrip("\n")
                                            elif text.startswith("```"):
                                                text = text.replace("```", "", 1).lstrip("\n")
                                        first_chunk = False
                                    
                                    # Accumulate the full code
                                    full_code += text
                                    
                                    # Don't remove triple backticks from within the code
                                    # Only remove if it's the closing block at the very end
                                    if text.strip().endswith("```") and len(full_code.strip()) > 3:
                                        # Check if this might be the end
                                        text = text.rstrip()
                                        if text.endswith("```"):
                                            text = text[:-3].rstrip()
                                    
                                    # Yield the text
                                    if text:
                                        yield {
                                            "type": "text",
                                            "content": text
                                        }
                            elif event.type == "error" or (hasattr(event, 'error') and event.error):
                                # Handle streaming errors (like overloaded)
                                error_info = event.error if hasattr(event, 'error') else event
                                # Handle both dict and object formats
                                if isinstance(error_info, dict):
                                    error_type = error_info.get('type', '')
                                    error_msg = error_info.get('message', str(error_info))
                                else:
                                    error_type = getattr(error_info, 'type', '')
                                    error_msg = getattr(error_info, 'message', str(error_info))
                                
                                if 'overloaded' in error_type.lower() or 'overloaded' in error_msg.lower():
                                    raise Exception(f"overloaded_error: {error_msg}")
                                else:
                                    raise Exception(f"Stream error: {error_msg}")
                except Exception as e:
                    logger.error(f"Error during visualization streaming: {str(e)}")
                    # Make sure we have complete code even if streaming was interrupted
                    if full_code and not full_code.strip().endswith(';') and not full_code.strip().endswith('}'):
                        logger.warning("Code appears to be truncated, may cause syntax errors")
                    # Re-raise to trigger retry logic
                    raise
                
                # Send code block end
                yield {
                    "type": "text",
                    "content": "\n```"
                }
                
                # Record response event if tracing is enabled
                if TRACING_AVAILABLE and prompt_event_id:
                    trace_collector = get_trace_collector()
                    if trace_collector:
                        duration_ms = (asyncio.get_event_loop().time() - start_time) * 1000
                        response_data = {
                            "response_text": full_code,
                            "response_length": len(full_code),
                            "model": model,
                            "visualization_generated": True
                        }
                        
                        await trace_collector.add_event(
                            event_type=TraceEventType.LLM_RESPONSE,
                            agent_type="visualization",
                            stage="visualization_generation",
                            data=response_data,
                            duration_ms=duration_ms,
                            parent_event_id=prompt_event_id
                        )
                
                break  # Success, exit retry loop
                
            except Exception as e:
                error_message = str(e).lower()
                # Be more specific about retryable errors
                is_retryable = (
                    any(term in error_message for term in ["overloaded", "rate_limit", "too_many_requests"]) or
                    "429" in error_message or  # HTTP 429 Too Many Requests
                    type(e).__name__ in ["RateLimitError", "APIStatusError"]
                )
                
                # Log the actual error for debugging
                logger.error(f"{context_label} - Error type: {type(e).__name__}, Message: {str(e)}")
                
                if is_retryable and attempt < self.max_retries - 1:
                    logger.warning(
                        f"{context_label} - API overloaded, attempt {attempt + 1}/{self.max_retries}, "
                        f"retrying in {retry_delay} seconds..."
                    )
                    await asyncio.sleep(retry_delay)
                    retry_delay = min(retry_delay * 2, self.max_retry_delay)
                    
                    if code_block_started:
                        yield {
                            "type": "text",
                            "content": "\n```\n\n*[Retrying visualization generation due to high demand...]*\n"
                        }
                        code_block_started = False
                else:
                    logger.error(f"{context_label} streaming error after {attempt + 1} attempts: {str(e)}")
                    
                    if code_block_started:
                        yield {
                            "type": "text",
                            "content": "\n```"
                        }
                    
                    yield {
                        "type": "text",
                        "content": f"\n\n*[Unable to generate visualization due to an error]*"
                    }
                    break