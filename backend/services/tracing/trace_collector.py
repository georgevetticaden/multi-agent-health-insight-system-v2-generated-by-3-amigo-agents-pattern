"""
Central trace collection and management.

Provides the main TraceCollector class that coordinates trace collection
across the entire system, managing trace lifecycle and storage.
"""

import asyncio
import uuid
import time
from typing import Dict, List, Optional, Any
from datetime import datetime
from contextlib import asynccontextmanager

from .trace_models import (
    TraceEvent, 
    TraceEventType, 
    CompleteTrace
)
from .trace_context import TraceContext, TraceContextManager
from .storage import TraceStorage, InMemoryTraceStorage, FileSystemTraceStorage


class TraceCollector:
    """
    Central coordinator for trace collection.
    
    Manages the lifecycle of traces from creation to storage,
    provides event recording capabilities, and handles context management.
    """
    
    def __init__(self, storage_backend: Optional[TraceStorage] = None):
        self.active_traces: Dict[str, CompleteTrace] = {}
        self.storage = storage_backend or self._create_default_storage()
        self._lock = asyncio.Lock()
        
    def _create_default_storage(self) -> TraceStorage:
        """Create default storage backend based on configuration"""
        # Import at runtime to avoid circular imports
        import os
        from pathlib import Path
        
        storage_type = os.getenv("TRACE_STORAGE_TYPE", "filesystem")
        
        # Use new unified evaluation data config if available
        try:
            from evaluation.data.config import EvaluationDataConfig
            EvaluationDataConfig.init_directories()
            storage_path = EvaluationDataConfig.TRACES_DIR
        except ImportError:
            # Fallback to environment variable or default
            storage_path = Path(os.getenv("TRACE_STORAGE_PATH", "./traces"))
        
        if storage_type == "filesystem":
            return FileSystemTraceStorage(storage_path)
        else:
            return InMemoryTraceStorage()
    
    async def start_trace(self, 
                         source: str,
                         initial_input: str,
                         user_id: Optional[str] = None,
                         test_case_id: Optional[str] = None,
                         session_id: Optional[str] = None,
                         metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Start a new trace and return trace ID.
        
        Args:
            source: "evaluation" or "production"
            initial_input: The initial user query or input
            user_id: Optional user identifier (for production)
            test_case_id: Optional test case ID (for evaluation)
            session_id: Optional session identifier
            metadata: Additional trace metadata
            
        Returns:
            Unique trace ID
        """
        trace_id = str(uuid.uuid4())
        
        # Create trace context
        context = TraceContext(
            trace_id=trace_id,
            source=source,
            user_id=user_id,
            test_case_id=test_case_id,
            session_id=session_id,
            metadata=metadata or {}
        )
        
        # Set context for async operations
        TraceContextManager.set_context(context)
        
        # Create trace
        async with self._lock:
            trace = CompleteTrace(
                trace_id=trace_id,
                source=source,
                start_time=datetime.now().isoformat(),
                end_time=None,
                initial_input=initial_input,
                user_id=user_id,
                test_case_id=test_case_id,
                session_id=session_id,
                events=[],
                summary={},
                metadata=metadata or {}
            )
            
            self.active_traces[trace_id] = trace
        
        # Record initial event
        await self.add_event(
            event_type=TraceEventType.USER_QUERY,
            agent_type="user",
            stage="input",
            data={"query": initial_input}
        )
        
        return trace_id
    
    async def add_event(self, 
                       event_type: TraceEventType,
                       agent_type: str,
                       stage: str,
                       data: Dict[str, Any],
                       **kwargs) -> Optional[str]:
        """
        Add an event to the current trace.
        
        Args:
            event_type: Type of event
            agent_type: Which agent/component generated this event
            stage: Current processing stage
            data: Event-specific data
            **kwargs: Additional event properties (duration_ms, tokens_used, etc.)
            
        Returns:
            Event ID if added successfully, None if no active trace
        """
        context = TraceContextManager.get_context()
        if not context:
            # No active trace - silently ignore (allows system to work without tracing)
            return None
        
        event_id = str(uuid.uuid4())
        
        event = TraceEvent(
            event_id=event_id,
            trace_id=context.trace_id,
            timestamp=datetime.now().isoformat(),
            event_type=event_type,
            agent_type=agent_type,
            stage=stage,
            data=data,
            duration_ms=kwargs.get('duration_ms'),
            tokens_used=kwargs.get('tokens_used'),
            parent_event_id=kwargs.get('parent_event_id'),
            metadata=kwargs.get('metadata', {})
        )
        
        async with self._lock:
            if context.trace_id in self.active_traces:
                self.active_traces[context.trace_id].add_event(event)
        
        return event_id
    
    async def end_trace(self, trace_id: Optional[str] = None) -> Optional[CompleteTrace]:
        """
        End a trace and store it.
        
        Args:
            trace_id: Optional trace ID to end. If not provided, uses current context.
            
        Returns:
            The completed trace if successful, None otherwise
        """
        context = TraceContextManager.get_context()
        if not trace_id and context:
            trace_id = context.trace_id
        
        if not trace_id:
            return None
        
        async with self._lock:
            if trace_id in self.active_traces:
                trace = self.active_traces[trace_id]
                trace.end_time = datetime.now().isoformat()
                
                # Calculate duration
                start = datetime.fromisoformat(trace.start_time)
                end = datetime.fromisoformat(trace.end_time)
                trace.total_duration_ms = (end - start).total_seconds() * 1000
                
                # Generate summary
                trace.summary = trace.calculate_summary()
                
                # Store trace
                await self.storage.store_trace(trace)
                
                # Remove from active traces
                del self.active_traces[trace_id]
                
                # Clear context
                TraceContextManager.clear_context()
                
                return trace
        
        return None
    
    @asynccontextmanager
    async def trace_operation(self, 
                             agent_type: str,
                             stage: str,
                             **kwargs):
        """
        Context manager for tracing a specific operation.
        
        Args:
            agent_type: Agent performing the operation
            stage: Stage name
            **kwargs: Additional metadata for the operation
        """
        start_time = time.time()
        
        # Record start event
        start_event_id = await self.add_event(
            event_type=TraceEventType.STAGE_START,
            agent_type=agent_type,
            stage=stage,
            data={"operation": f"Starting {stage}", **kwargs}
        )
        
        try:
            yield start_event_id
        finally:
            # Record end event with duration
            duration_ms = (time.time() - start_time) * 1000
            await self.add_event(
                event_type=TraceEventType.STAGE_END,
                agent_type=agent_type,
                stage=stage,
                data={"operation": f"Completed {stage}"},
                duration_ms=duration_ms,
                parent_event_id=start_event_id
            )
    
    async def get_active_trace(self, trace_id: Optional[str] = None) -> Optional[CompleteTrace]:
        """
        Get an active trace by ID or from current context.
        
        Args:
            trace_id: Optional trace ID. If not provided, uses current context.
            
        Returns:
            The active trace if found, None otherwise
        """
        if not trace_id:
            context = TraceContextManager.get_context()
            if context:
                trace_id = context.trace_id
        
        if not trace_id:
            return None
        
        async with self._lock:
            return self.active_traces.get(trace_id)
    
    async def get_stored_trace(self, trace_id: str) -> Optional[CompleteTrace]:
        """
        Get a stored trace by ID.
        
        Args:
            trace_id: Trace identifier
            
        Returns:
            The stored trace if found, None otherwise
        """
        return await self.storage.get_trace(trace_id)
    
    async def list_traces(self, 
                         filters: Optional[Dict[str, Any]] = None,
                         limit: int = 100,
                         offset: int = 0) -> List[Dict[str, Any]]:
        """
        List stored traces with optional filters.
        
        Args:
            filters: Optional filters (source, user_id, date_range, etc.)
            limit: Maximum number of traces to return
            offset: Number of traces to skip
            
        Returns:
            List of trace metadata
        """
        return await self.storage.list_traces(filters, limit, offset)
    
    def update_context(self, **kwargs):
        """
        Update the current trace context.
        
        Args:
            **kwargs: Context fields to update (current_agent, current_stage, etc.)
        """
        TraceContextManager.update_context(**kwargs)
    
    def is_tracing(self) -> bool:
        """Check if we're currently in a trace context"""
        return TraceContextManager.is_tracing()
    
    def get_current_trace_id(self) -> Optional[str]:
        """Get the current trace ID, if any"""
        return TraceContextManager.get_trace_id()


# Global trace collector instance
_global_trace_collector: Optional[TraceCollector] = None


def get_trace_collector() -> TraceCollector:
    """
    Get or create the global trace collector instance.
    
    Returns:
        The global TraceCollector instance
    """
    global _global_trace_collector
    if _global_trace_collector is None:
        _global_trace_collector = TraceCollector()
    return _global_trace_collector


def set_trace_collector(collector: TraceCollector):
    """
    Set the global trace collector instance.
    
    Args:
        collector: TraceCollector instance to use globally
    """
    global _global_trace_collector
    _global_trace_collector = collector