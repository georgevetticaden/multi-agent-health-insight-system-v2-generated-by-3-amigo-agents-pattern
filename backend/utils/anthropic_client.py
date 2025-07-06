import logging
import time
from typing import Dict, List, Any, Optional
from anthropic import Anthropic, APIError, APITimeoutError, APIConnectionError

logger = logging.getLogger(__name__)

class AnthropicStreamingClient:
    """Wrapper for Anthropic client with retry logic and streaming support"""
    
    def __init__(self, client: Anthropic, max_retries: int = 3):
        self.client = client
        self.max_retries = max_retries
        
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
        """Create message with exponential backoff retry logic"""
        
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