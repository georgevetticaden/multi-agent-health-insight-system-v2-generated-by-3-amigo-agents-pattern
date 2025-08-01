import asyncio
import logging
import time
import copy
from typing import Dict, List, Any, Optional, Union
from anthropic import Anthropic, APIError, APITimeoutError, APIConnectionError

# Import tracing components if available
try:
    from services.tracing import (
        get_trace_collector, TraceContextManager, TraceEventType,
        LLMPromptData, LLMResponseData
    )
    TRACING_AVAILABLE = True
except ImportError:
    TRACING_AVAILABLE = False

logger = logging.getLogger(__name__)

class AnthropicStreamingClient:
    """Wrapper for Anthropic client with retry logic, streaming support, and integrated tracing"""
    
    def __init__(self, client: Anthropic, max_retries: int = 3):
        self.client = client
        self.max_retries = max_retries
        self.trace_collector = get_trace_collector() if TRACING_AVAILABLE else None
        self._metadata = {}  # Store metadata for tracing
    
    def set_metadata(self, **kwargs):
        """
        Set metadata for the next LLM call.
        
        Args:
            **kwargs: Metadata fields (agent_type, stage, prompt_file, etc.)
        """
        self._metadata.update(kwargs)
    
    def clear_metadata(self):
        """Clear current metadata"""
        self._metadata.clear()
        
    async def create_message_with_retry_async(
        self,
        model: str,
        messages: List[Dict[str, Any]],
        system: Optional[str] = None,
        max_tokens: int = 4000,
        temperature: float = 0.0,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[Dict[str, Any]] = None,
        stream: bool = False
    ):
        """Async version of create_message_with_retry with proper tracing support"""
        
        # Check if we should trace this call
        should_trace = (TRACING_AVAILABLE and 
                       self.trace_collector and 
                       TraceContextManager.is_tracing())
        
        if should_trace:
            # We're in an async context, use async tracing
            return await self._create_message_with_tracing(
                model=model,
                messages=messages,
                system=system,
                max_tokens=max_tokens,
                temperature=temperature,
                tools=tools,
                tool_choice=tool_choice,
                stream=stream
            )
        
        # Regular retry logic without tracing
        return await self._create_message_with_retry_no_trace(
            model=model,
            messages=messages,
            system=system,
            max_tokens=max_tokens,
            temperature=temperature,
            tools=tools,
            tool_choice=tool_choice,
            stream=stream
        )
    
    def create_message_with_retry(
        self,
        model: str,
        messages: List[Dict[str, Any]],
        system: Optional[str] = None,
        max_tokens: int = 4000,
        temperature: float = 0.0,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[Dict[str, Any]] = None,
        stream: bool = False
    ):
        """Create message with exponential backoff retry logic and optional tracing"""
        
        # Check if we should trace this call
        should_trace = (TRACING_AVAILABLE and 
                       self.trace_collector and 
                       TraceContextManager.is_tracing())
        
        if should_trace:
            # We need to handle async tracing in a sync context
            import asyncio
            try:
                # Check if we're already in an event loop
                loop = asyncio.get_running_loop()
                # If we get here, we're in an async context already
                # We cannot use run_until_complete in an active loop, so we need to create a task
                # and await it properly. Since this is a sync method, we'll just fall back to
                # non-traced execution in async contexts to avoid blocking
                logger.warning("Cannot trace synchronous call from async context - falling back to non-traced execution")
                # Fall through to regular execution
            except RuntimeError:
                # No event loop running, create one
                return asyncio.run(self._create_message_with_tracing(
                    model=model,
                    messages=messages,
                    system=system,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    tools=tools,
                    tool_choice=tool_choice,
                    stream=stream
                ))
        
        # Regular retry logic without tracing
        for attempt in range(self.max_retries):
            try:
                kwargs = {
                    "model": model,
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "stream": stream
                }
                
                if system:
                    kwargs["system"] = system
                if tools:
                    kwargs["tools"] = tools
                if tool_choice:
                    kwargs["tool_choice"] = tool_choice
                
                return self.client.messages.create(**kwargs)
                
            except (APITimeoutError, APIConnectionError) as e:
                if attempt == self.max_retries - 1:
                    logger.error(f"Max retries reached: {e}")
                    raise
                
                wait_time = 2 ** attempt
                logger.warning(f"API error on attempt {attempt + 1}, retrying in {wait_time}s: {e}")
                time.sleep(wait_time)
                
            except APIError as e:
                logger.error(f"API error: {e}")
                raise
                
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                raise
    
    async def _create_message_with_tracing(
        self,
        model: str,
        messages: List[Dict[str, Any]],
        system: Optional[str] = None,
        max_tokens: int = 4000,
        temperature: float = 0.0,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[Dict[str, Any]] = None,
        stream: bool = False
    ):
        """Create message with tracing and retry logic"""
        
        # Get current trace context
        context = TraceContextManager.get_context()
        if not context:
            logger.warning("No trace context available, falling back to regular call")
            return self.create_message_with_retry(
                model=model, messages=messages, system=system,
                max_tokens=max_tokens, temperature=temperature,
                tools=tools, tool_choice=tool_choice, stream=stream
            )
        
        # Extract metadata - prefer instance metadata over context
        agent_type = self._metadata.get('agent_type') or context.current_agent or 'unknown'
        stage = self._metadata.get('stage') or context.current_stage or 'unknown'
        prompt_file = self._metadata.get('prompt_file') or context.current_prompt_file
        
        # Build prompt text for logging
        prompt_text = self._build_prompt_text(messages, system)
        
        # Record prompt event
        start_time = time.time()
        prompt_event_id = None
        
        try:
            # Create prompt data with deep copy of messages to preserve state
            prompt_data = {
                "prompt_file": prompt_file,
                "populated_prompt": prompt_text,
                "model": model,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "messages": copy.deepcopy(messages),  # Deep copy to preserve current state
                "system_prompt": system,
                "tools": [t.get('name', 'unknown') for t in tools] if tools else [],
                "message_count": len(messages),
                "prompt_length": len(prompt_text)
            }
            
            # Add any additional metadata
            prompt_data.update(self._metadata)
            
            # Record prompt event (already in async context)
            prompt_event_id = await self.trace_collector.add_event(
                event_type=TraceEventType.LLM_PROMPT,
                agent_type=agent_type,
                stage=stage,
                data=prompt_data,
                metadata=self._metadata.copy()
            )
                
        except Exception as e:
            logger.error(f"Failed to record prompt event: {e}")
        
        # Make the actual API call with retries
        response = None
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                kwargs = {
                    "model": model,
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "stream": stream
                }
                
                if system:
                    kwargs["system"] = system
                if tools:
                    kwargs["tools"] = tools
                if tool_choice:
                    kwargs["tool_choice"] = tool_choice
                
                response = self.client.messages.create(**kwargs)
                break  # Success!
                
            except (APITimeoutError, APIConnectionError) as e:
                last_error = e
                if attempt == self.max_retries - 1:
                    logger.error(f"Max retries reached: {e}")
                    raise
                
                wait_time = 2 ** attempt
                logger.warning(f"API error on attempt {attempt + 1}, retrying in {wait_time}s: {e}")
                time.sleep(wait_time)
                
            except Exception as e:
                last_error = e
                logger.error(f"Unexpected error: {e}")
                raise
        
        # Record response event (only for non-streaming responses)
        if response and not stream:
            try:
                response_text = self._extract_response_text(response)
                tool_calls = self._extract_tool_calls(response)
                
                response_data = {
                    "response_text": response_text,
                    "stop_reason": response.stop_reason,
                    "usage": {
                        "input_tokens": response.usage.input_tokens,
                        "output_tokens": response.usage.output_tokens,
                        "total_tokens": response.usage.input_tokens + response.usage.output_tokens
                    },
                    "model": response.model,
                    "tool_calls": tool_calls,
                    "response_length": len(response_text)
                }
                
                # Record response event (already in async context)
                response_event_id = await self.trace_collector.add_event(
                    event_type=TraceEventType.LLM_RESPONSE,
                    agent_type=agent_type,
                    stage=stage,
                    data=response_data,
                    duration_ms=(time.time() - start_time) * 1000,
                    tokens_used=response_data["usage"]["total_tokens"],
                    parent_event_id=prompt_event_id,
                    metadata=self._metadata.copy()
                )
                
                # Automatically trace tool invocations if present
                if tool_calls and hasattr(response, 'content'):
                    for content_block in response.content:
                        if hasattr(content_block, 'type') and content_block.type == 'tool_use':
                            tool_event_id = await self.trace_collector.add_event(
                                event_type=TraceEventType.TOOL_INVOCATION,
                                agent_type=agent_type,
                                stage=stage,
                                data={
                                    "tool_name": getattr(content_block, 'name', 'unknown'),
                                    "tool_input": getattr(content_block, 'input', {}),
                                    "tool_id": getattr(content_block, 'id', 'unknown')
                                },
                                parent_event_id=response_event_id,
                                metadata=self._metadata.copy()
                            )
                            logger.debug(f"Auto-traced tool invocation: {getattr(content_block, 'name', 'unknown')}")
                    
            except Exception as e:
                logger.error(f"Failed to record response event: {e}")
                
                # Record error event if we have a prompt event
                if prompt_event_id:
                    try:
                        await self.trace_collector.add_event(
                            event_type=TraceEventType.ERROR,
                            agent_type=agent_type,
                            stage=stage,
                            data={
                                "error_type": "response_recording_error",
                                "error_message": str(e),
                                "prompt_event_id": prompt_event_id
                            },
                            metadata=self._metadata.copy()
                        )
                    except:
                        pass
        
        # Clear metadata after use
        self.clear_metadata()
        
        return response
    
    async def _create_message_with_retry_no_trace(
        self,
        model: str,
        messages: List[Dict[str, Any]],
        system: Optional[str] = None,
        max_tokens: int = 4000,
        temperature: float = 0.0,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[Dict[str, Any]] = None,
        stream: bool = False
    ):
        """Async version of retry logic without tracing"""
        for attempt in range(self.max_retries):
            try:
                kwargs = {
                    "model": model,
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "stream": stream
                }
                
                if system:
                    kwargs["system"] = system
                if tools:
                    kwargs["tools"] = tools
                if tool_choice:
                    kwargs["tool_choice"] = tool_choice
                
                return self.client.messages.create(**kwargs)
                
            except (APITimeoutError, APIConnectionError) as e:
                if attempt == self.max_retries - 1:
                    logger.error(f"Max retries reached: {e}")
                    raise
                
                wait_time = 2 ** attempt
                logger.warning(f"API error on attempt {attempt + 1}, retrying in {wait_time}s: {e}")
                await asyncio.sleep(wait_time)
                
            except Exception as e:
                logger.error(f"Unexpected error during async LLM call: {e}")
                raise
    
    def _build_prompt_text(self, messages: List[Dict[str, Any]], system_prompt: Optional[str] = None) -> str:
        """Build a readable prompt text from messages"""
        parts = []
        
        if system_prompt:
            parts.append(f"SYSTEM: {system_prompt}")
            parts.append("")
        
        for msg in messages:
            role = msg.get('role', 'unknown').upper()
            content = msg.get('content', '')
            
            if isinstance(content, list):
                # Handle multimodal content
                text_parts = []
                for item in content:
                    if isinstance(item, dict):
                        if item.get('type') == 'text':
                            text_parts.append(item.get('text', ''))
                        elif item.get('type') == 'tool_use':
                            tool_name = item.get('name', 'unknown_tool')
                            text_parts.append(f"[TOOL_USE: {tool_name}]")
                        elif item.get('type') == 'tool_result':
                            text_parts.append(f"[TOOL_RESULT]")
                        else:
                            text_parts.append(f"[{item.get('type', 'unknown').upper()}]")
                content = '\n'.join(text_parts)
            
            parts.append(f"{role}: {content}")
        
        return '\n\n'.join(parts)
    
    def _extract_response_text(self, response) -> str:
        """Extract text content from Anthropic response"""
        if hasattr(response, 'content') and response.content:
            text_parts = []
            for content_block in response.content:
                if hasattr(content_block, 'text'):
                    text_parts.append(content_block.text)
                elif hasattr(content_block, 'type'):
                    if content_block.type == 'text':
                        text_parts.append(getattr(content_block, 'text', ''))
                    elif content_block.type == 'tool_use':
                        tool_name = getattr(content_block, 'name', 'unknown_tool')
                        text_parts.append(f"[TOOL_USE: {tool_name}]")
            return '\n'.join(text_parts)
        
        return str(response)
    
    def _extract_tool_calls(self, response) -> List[str]:
        """Extract tool call names from response"""
        tool_calls = []
        
        if hasattr(response, 'content') and response.content:
            for content_block in response.content:
                if hasattr(content_block, 'type') and content_block.type == 'tool_use':
                    tool_name = getattr(content_block, 'name', 'unknown_tool')
                    tool_calls.append(tool_name)
        
        return tool_calls
    
    async def stream_visualization(
        self,
        model: str,
        messages: List[Dict[str, Any]],
        max_tokens: int,
        context_label: str = "Visualization"
    ):
        """
        Special handling for visualization streaming that yields chunks
        
        This delegates to the original streaming client for now since visualization
        streaming has special requirements that don't fit the standard tracing pattern.
        """
        # Import the original streaming client
        from utils.anthropic_streaming import AnthropicStreamingClient as OriginalStreamingClient
        
        # Create a temporary instance of the original client
        original_client = OriginalStreamingClient(self.client)
        
        # Delegate to the original implementation
        async for chunk in original_client.stream_visualization(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            context_label=context_label
        ):
            yield chunk