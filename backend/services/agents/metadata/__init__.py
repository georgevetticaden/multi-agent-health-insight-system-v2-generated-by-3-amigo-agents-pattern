"""
Agent Metadata Package

Provides core metadata classes for agents to describe themselves
and their prompts. This package contains only agent-specific metadata,
not evaluation concepts.
"""

from .core import (
    AgentMetadata,
    PromptMetadata
)

__all__ = [
    'AgentMetadata',
    'PromptMetadata'
]