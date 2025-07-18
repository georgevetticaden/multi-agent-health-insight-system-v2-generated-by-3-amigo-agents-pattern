"""
Data models for the tracing system.

Defines the structure for trace events, complete traces, and specialized
data types for different kinds of events (LLM calls, tool invocations, etc.)
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum
from datetime import datetime


class TraceEventType(Enum):
    """Types of events that can be captured in a trace"""
    USER_QUERY = "user_query"
    LLM_PROMPT = "llm_prompt"
    LLM_RESPONSE = "llm_response"
    TOOL_INVOCATION = "tool_invocation"
    TOOL_RESULT = "tool_result"
    INTERMEDIATE_STEP = "intermediate_step"
    FINAL_RESULT = "final_result"
    EVALUATION_STEP = "evaluation_step"
    ERROR = "error"
    STAGE_START = "stage_start"
    STAGE_END = "stage_end"


@dataclass
class TraceEvent:
    """Represents a single event in the execution trace"""
    event_id: str
    trace_id: str
    timestamp: str
    event_type: TraceEventType
    agent_type: str  # "cmo", "specialist", "llm_judge", "user", etc.
    stage: str  # "analysis", "task_creation", "synthesis", etc.
    
    # Event-specific data
    data: Dict[str, Any]
    
    # Hierarchy and timing
    parent_event_id: Optional[str] = None
    duration_ms: Optional[float] = None
    tokens_used: Optional[int] = None
    
    # Additional context
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LLMPromptData:
    """Specialized data structure for LLM prompt events"""
    prompt_file: Optional[str]
    template: Optional[str]
    populated_prompt: str
    model: str
    temperature: float
    max_tokens: int
    messages: List[Dict[str, str]]
    system_prompt: Optional[str] = None
    tools: List[str] = field(default_factory=list)


@dataclass
class LLMResponseData:
    """Specialized data structure for LLM response events"""
    response_text: str
    stop_reason: str
    usage: Dict[str, int]  # input_tokens, output_tokens, total_tokens
    model: str
    tool_calls: List[str] = field(default_factory=list)


@dataclass
class ToolInvocationData:
    """Specialized data structure for tool invocation events"""
    tool_name: str
    tool_type: str
    parameters: Dict[str, Any]
    query: Optional[str] = None


@dataclass
class ToolResultData:
    """Specialized data structure for tool result events"""
    tool_name: str
    success: bool
    result: Any
    error: Optional[str] = None
    rows_returned: Optional[int] = None
    result_summary: Optional[str] = None


@dataclass
class CompleteTrace:
    """Complete execution trace for a single operation"""
    trace_id: str
    source: str  # "evaluation" or "production"
    start_time: str
    end_time: Optional[str]
    initial_input: str
    
    # Context information
    user_id: Optional[str] = None
    test_case_id: Optional[str] = None
    session_id: Optional[str] = None
    
    # Trace data
    events: List[TraceEvent] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Performance metrics
    total_duration_ms: Optional[float] = None
    
    def add_event(self, event: TraceEvent):
        """Add an event to this trace"""
        self.events.append(event)
        
    def get_events_by_type(self, event_type: TraceEventType) -> List[TraceEvent]:
        """Get all events of a specific type"""
        return [e for e in self.events if e.event_type == event_type]
        
    def get_events_by_agent(self, agent_type: str) -> List[TraceEvent]:
        """Get all events from a specific agent"""
        return [e for e in self.events if e.agent_type == agent_type]
        
    def calculate_summary(self) -> Dict[str, Any]:
        """Calculate summary statistics for this trace"""
        if not self.events:
            return {}
            
        # Count events by type
        event_counts = {}
        for event in self.events:
            event_type = event.event_type.value
            event_counts[event_type] = event_counts.get(event_type, 0) + 1
            
        # Calculate totals
        total_llm_calls = len(self.get_events_by_type(TraceEventType.LLM_PROMPT))
        total_tool_calls = len(self.get_events_by_type(TraceEventType.TOOL_INVOCATION))
        total_tokens = sum(e.tokens_used or 0 for e in self.events if e.tokens_used)
        
        # Find errors
        errors = self.get_events_by_type(TraceEventType.ERROR)
        
        # Get unique agents and stages
        agents = list(set(e.agent_type for e in self.events))
        stages = list(set(e.stage for e in self.events))
        
        return {
            "event_counts": event_counts,
            "total_events": len(self.events),
            "llm_calls": total_llm_calls,
            "tool_calls": total_tool_calls,
            "total_tokens": total_tokens,
            "errors": len(errors),
            "error_messages": [e.data.get("error_message", "") for e in errors],
            "agents_involved": agents,
            "stages_executed": stages,
            "duration_ms": self.total_duration_ms
        }