"""
Model configuration for different Claude models.

This module provides model-specific configurations including token limits
and other model-specific parameters.
"""

from typing import Dict, Any
from dataclasses import dataclass


@dataclass
class ModelConfig:
    """Configuration for a specific Claude model"""
    max_tokens: int
    context_window: int
    supports_tools: bool = True
    supports_streaming: bool = True


# Model configurations
MODEL_CONFIGS: Dict[str, ModelConfig] = {
    # Claude 3 models
    "claude-3-sonnet-20240229": ModelConfig(
        max_tokens=4096,
        context_window=200000,
        supports_tools=True,
        supports_streaming=True
    ),
    "claude-3-haiku-20240307": ModelConfig(
        max_tokens=4096,
        context_window=200000,
        supports_tools=True,
        supports_streaming=True
    ),
    
    # Claude 3.5 models
    "claude-3-5-sonnet-20240620": ModelConfig(
        max_tokens=8192,
        context_window=200000,
        supports_tools=True,
        supports_streaming=True
    ),
    "claude-3-5-sonnet-20241022": ModelConfig(
        max_tokens=8192,
        context_window=200000,
        supports_tools=True,
        supports_streaming=True
    ),
    "claude-3-7-sonnet-20250219": ModelConfig(
        max_tokens=8192,
        context_window=200000,
        supports_tools=True,
        supports_streaming=True
    ),
    # Claude Opus 4 models
    "claude-opus-4-20250514": ModelConfig(
        max_tokens=8192,
        context_window=200000,
        supports_tools=True,
        supports_streaming=True
    ),
    
    # Default fallback configuration
    "default": ModelConfig(
        max_tokens=4096,  # Conservative default
        context_window=200000,
        supports_tools=True,
        supports_streaming=True
    )
}


def get_model_config(model_name: str) -> ModelConfig:
    """
    Get configuration for a specific model.
    
    Args:
        model_name: Name of the Claude model
        
    Returns:
        ModelConfig for the specified model, or default if not found
    """
    return MODEL_CONFIGS.get(model_name, MODEL_CONFIGS["default"])


def get_safe_max_tokens(model_name: str, requested_tokens: int) -> int:
    """
    Get safe max_tokens value for a model.
    
    Args:
        model_name: Name of the Claude model
        requested_tokens: Requested number of tokens
        
    Returns:
        Safe number of tokens that doesn't exceed model limits
    """
    config = get_model_config(model_name)
    return min(requested_tokens, config.max_tokens)


def validate_model_config(model_name: str) -> None:
    """
    Validate that a model is supported.
    
    Args:
        model_name: Name of the Claude model
        
    Raises:
        ValueError: If model is not recognized
    """
    if model_name not in MODEL_CONFIGS:
        print(f"Warning: Model '{model_name}' not in predefined configs. Using default configuration.")