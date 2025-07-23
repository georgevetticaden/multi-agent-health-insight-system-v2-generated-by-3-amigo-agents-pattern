"""
Mock agents for trace-based evaluation.

This module provides mock implementations of agents that replay
data from execution traces instead of making actual API calls.
"""

from .mock_cmo_agent import MockCMOAgent

__all__ = ['MockCMOAgent']