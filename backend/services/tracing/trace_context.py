"""
Context management for tracing system.

Provides thread-safe context management using contextvars to track
the current trace across async operations without explicit parameter passing.
"""

import contextvars
from typing import Optional, Dict, Any
from dataclasses import dataclass, field


@dataclass
class TraceContext:
    """Context information for the current trace operation"""
    trace_id: str
    source: str  # "evaluation" or "production"
    user_id: Optional[str] = None
    test_case_id: Optional[str] = None
    session_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Current execution context
    current_agent: Optional[str] = None
    current_stage: Optional[str] = None
    current_prompt_file: Optional[str] = None


# Context variable for current trace - automatically propagated across async calls
current_trace_context: contextvars.ContextVar[Optional[TraceContext]] = contextvars.ContextVar(
    'current_trace_context', 
    default=None
)


class TraceContextManager:
    """Manages trace context across async operations"""
    
    @staticmethod
    def set_context(context: TraceContext):
        """Set the current trace context"""
        current_trace_context.set(context)
    
    @staticmethod
    def get_context() -> Optional[TraceContext]:
        """Get the current trace context"""
        return current_trace_context.get()
    
    @staticmethod
    def clear_context():
        """Clear the current trace context"""
        current_trace_context.set(None)
        
    @staticmethod
    def update_context(**kwargs):
        """Update fields in the current context"""
        context = current_trace_context.get()
        if context:
            for key, value in kwargs.items():
                if hasattr(context, key):
                    setattr(context, key, value)
            current_trace_context.set(context)
    
    @staticmethod
    def is_tracing() -> bool:
        """Check if we're currently in a trace context"""
        return current_trace_context.get() is not None
        
    @staticmethod
    def get_trace_id() -> Optional[str]:
        """Get the current trace ID, if any"""
        context = current_trace_context.get()
        return context.trace_id if context else None