"""
Unified Tracing System for Multi-Agent Health Insight System

This module provides comprehensive tracing capabilities for both evaluation
and production environments, capturing the complete execution sequence of
LLM prompts, tool invocations, and intermediate steps.
"""

from .trace_collector import TraceCollector, get_trace_collector
from .trace_models import (
    TraceEvent, 
    TraceEventType, 
    CompleteTrace,
    LLMPromptData,
    LLMResponseData,
    ToolInvocationData,
    ToolResultData
)
from .trace_context import TraceContext, TraceContextManager
from .storage import TraceStorage, FileSystemTraceStorage, InMemoryTraceStorage

__all__ = [
    'TraceCollector',
    'get_trace_collector',
    'TraceEvent',
    'TraceEventType',
    'CompleteTrace',
    'LLMPromptData',
    'LLMResponseData',
    'ToolInvocationData',
    'ToolResultData',
    'TraceContext',
    'TraceContextManager',
    'TraceStorage',
    'FileSystemTraceStorage',
    'InMemoryTraceStorage',
    'TRACING_ENABLED',
    'TRACE_STORAGE_TYPE',
    'TRACE_STORAGE_PATH',
    'TRACE_RETENTION_DAYS',
    'TRACE_SAMPLING_RATE'
]

# Configuration
import os
from pathlib import Path

TRACING_ENABLED = os.getenv("ENABLE_TRACING", "true").lower() == "true"
TRACE_STORAGE_TYPE = os.getenv("TRACE_STORAGE_TYPE", "filesystem")
TRACE_STORAGE_PATH = Path(os.getenv("TRACE_STORAGE_PATH", "./traces"))
TRACE_RETENTION_DAYS = int(os.getenv("TRACE_RETENTION_DAYS", "30"))
TRACE_SAMPLING_RATE = float(os.getenv("TRACE_SAMPLING_RATE", "1.0"))  # 100% for eval, lower for prod