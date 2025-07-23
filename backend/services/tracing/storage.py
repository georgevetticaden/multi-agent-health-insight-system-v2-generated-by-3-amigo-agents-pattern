"""
Storage backends for trace data.

Provides different storage options for traces including filesystem and
in-memory storage. Can be extended with database backends for production.
"""

import json
import asyncio
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import asdict
from enum import Enum

from .trace_models import CompleteTrace
from .html_generator import generate_trace_viewer_html
from .hierarchical_html_generator import generate_hierarchical_trace_html


def serialize_trace(trace: CompleteTrace) -> dict:
    """Custom serialization that properly handles enums"""
    def convert_value(obj):
        if isinstance(obj, Enum):
            return obj.value
        elif isinstance(obj, dict):
            return {k: convert_value(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_value(item) for item in obj]
        elif hasattr(obj, '__dict__'):
            return convert_value(obj.__dict__)
        else:
            return obj
    
    # Use asdict but then convert enum values
    trace_dict = asdict(trace)
    return convert_value(trace_dict)


class TraceStorage(ABC):
    """Abstract base class for trace storage backends"""
    
    @abstractmethod
    async def store_trace(self, trace: CompleteTrace) -> bool:
        """
        Store a completed trace.
        
        Args:
            trace: The completed trace to store
            
        Returns:
            True if stored successfully, False otherwise
        """
        pass
    
    @abstractmethod
    async def get_trace(self, trace_id: str) -> Optional[CompleteTrace]:
        """
        Retrieve a trace by ID.
        
        Args:
            trace_id: The unique trace identifier
            
        Returns:
            The trace if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def list_traces(self, 
                         filters: Optional[Dict[str, Any]] = None,
                         limit: int = 100,
                         offset: int = 0) -> List[Dict[str, Any]]:
        """
        List traces with optional filters.
        
        Args:
            filters: Optional filters (source, user_id, date_range, etc.)
            limit: Maximum number of traces to return
            offset: Number of traces to skip
            
        Returns:
            List of trace metadata (not full traces)
        """
        pass
    
    @abstractmethod
    async def delete_trace(self, trace_id: str) -> bool:
        """
        Delete a trace by ID.
        
        Args:
            trace_id: The unique trace identifier
            
        Returns:
            True if deleted successfully, False if not found
        """
        pass


class InMemoryTraceStorage(TraceStorage):
    """In-memory storage for traces - useful for testing and development"""
    
    def __init__(self, max_traces: int = 1000):
        self.traces: Dict[str, CompleteTrace] = {}
        self.max_traces = max_traces
        self._lock = asyncio.Lock()
    
    async def store_trace(self, trace: CompleteTrace) -> bool:
        """Store trace in memory"""
        async with self._lock:
            # If we're at capacity, remove oldest trace
            if len(self.traces) >= self.max_traces:
                oldest_id = min(self.traces.keys(), 
                              key=lambda tid: self.traces[tid].start_time)
                del self.traces[oldest_id]
            
            self.traces[trace.trace_id] = trace
            return True
    
    async def get_trace(self, trace_id: str) -> Optional[CompleteTrace]:
        """Get trace from memory"""
        async with self._lock:
            return self.traces.get(trace_id)
    
    async def list_traces(self, 
                         filters: Optional[Dict[str, Any]] = None,
                         limit: int = 100,
                         offset: int = 0) -> List[Dict[str, Any]]:
        """List traces from memory"""
        async with self._lock:
            traces = list(self.traces.values())
            
            # Apply filters
            if filters:
                if 'source' in filters:
                    traces = [t for t in traces if t.source == filters['source']]
                if 'user_id' in filters:
                    traces = [t for t in traces if t.user_id == filters['user_id']]
                if 'test_case_id' in filters:
                    traces = [t for t in traces if t.test_case_id == filters['test_case_id']]
            
            # Sort by start time (newest first)
            traces.sort(key=lambda t: t.start_time, reverse=True)
            
            # Apply pagination
            traces = traces[offset:offset + limit]
            
            # Return metadata only
            return [{
                'trace_id': t.trace_id,
                'source': t.source,
                'start_time': t.start_time,
                'end_time': t.end_time,
                'duration_ms': t.total_duration_ms,
                'user_id': t.user_id,
                'test_case_id': t.test_case_id,
                'session_id': t.session_id,
                'event_count': len(t.events),
                'initial_input': t.initial_input[:100] + '...' if len(t.initial_input) > 100 else t.initial_input
            } for t in traces]
    
    async def delete_trace(self, trace_id: str) -> bool:
        """Delete trace from memory"""
        async with self._lock:
            if trace_id in self.traces:
                del self.traces[trace_id]
                return True
            return False


class FileSystemTraceStorage(TraceStorage):
    """Filesystem-based storage for traces"""
    
    def __init__(self, base_dir: Path, retention_days: int = 30):
        self.base_dir = Path(base_dir)
        self.retention_days = retention_days
        self._lock = asyncio.Lock()
        
        # Ensure base directory exists
        self.base_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_trace_path(self, trace_id: str, start_time: Optional[str] = None) -> Path:
        """Get the file path for a trace"""
        if start_time:
            # Use start time to organize by date
            dt = datetime.fromisoformat(start_time)
            date = dt.date()
            date_dir = self.base_dir / date.strftime("%Y-%m-%d")
            # Include timestamp in filename for easier sorting: HHMMSS_trace_id
            time_prefix = dt.strftime("%H%M%S")
            return date_dir / f"{time_prefix}_{trace_id}.json"
        else:
            # Search across all date directories
            date_dir = self.base_dir
            # When searching, we need to handle both old and new naming patterns
            return date_dir / f"*_{trace_id}.json"
    
    async def store_trace(self, trace: CompleteTrace) -> bool:
        """Store trace to filesystem"""
        try:
            # Create date directory
            date = datetime.fromisoformat(trace.start_time).date()
            date_dir = self.base_dir / date.strftime("%Y-%m-%d")
            date_dir.mkdir(parents=True, exist_ok=True)
            
            # Store JSON trace
            trace_path = self._get_trace_path(trace.trace_id, trace.start_time)
            
            async with self._lock:
                with open(trace_path, 'w', encoding='utf-8') as f:
                    json.dump(serialize_trace(trace), f, indent=2, default=str, ensure_ascii=False)
                
                # Generate and store both HTML viewers
                # 1. Original timeline viewer
                html_path = trace_path.with_suffix('.html')
                html_content = generate_trace_viewer_html(trace)
                with open(html_path, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                
                # 2. New hierarchical viewer
                hierarchical_path = trace_path.with_suffix('.hierarchical.html')
                hierarchical_content = generate_hierarchical_trace_html(trace)
                with open(hierarchical_path, 'w', encoding='utf-8') as f:
                    f.write(hierarchical_content)
            
            # Cleanup old traces
            await self._cleanup_old_traces()
            
            return True
            
        except Exception as e:
            print(f"Error storing trace {trace.trace_id}: {e}")
            return False
    
    async def get_trace(self, trace_id: str) -> Optional[CompleteTrace]:
        """Get trace from filesystem"""
        try:
            # Search for trace file across date directories
            for date_dir in self.base_dir.iterdir():
                if date_dir.is_dir() and date_dir.name.count('-') == 2:  # YYYY-MM-DD format
                    # Try new naming pattern first (HHMMSS_trace_id.json)
                    for trace_file in date_dir.glob(f"*_{trace_id}.json"):
                        async with self._lock:
                            with open(trace_file, 'r', encoding='utf-8') as f:
                                data = json.load(f)
                        
                        # Convert back to CompleteTrace
                        return self._dict_to_trace(data)
                    
                    # Fallback to old naming pattern (trace_id.json)
                    trace_path = date_dir / f"{trace_id}.json"
                    if trace_path.exists():
                        async with self._lock:
                            with open(trace_path, 'r', encoding='utf-8') as f:
                                data = json.load(f)
                        
                        # Convert back to CompleteTrace
                        return self._dict_to_trace(data)
            
            return None
            
        except Exception as e:
            print(f"Error retrieving trace {trace_id}: {e}")
            return None
    
    async def list_traces(self, 
                         filters: Optional[Dict[str, Any]] = None,
                         limit: int = 100,
                         offset: int = 0) -> List[Dict[str, Any]]:
        """List traces from filesystem"""
        try:
            traces = []
            
            # Scan date directories (newest first)
            date_dirs = [d for d in self.base_dir.iterdir() 
                        if d.is_dir() and d.name.count('-') == 2]
            date_dirs.sort(reverse=True)
            
            for date_dir in date_dirs:
                # Get all JSON files, sort by filename to get time order (newest first)
                trace_files = sorted(date_dir.glob("*.json"), reverse=True)
                for trace_file in trace_files:
                    try:
                        async with self._lock:
                            with open(trace_file, 'r', encoding='utf-8') as f:
                                data = json.load(f)
                        
                        # Apply filters
                        if filters:
                            if 'source' in filters and data.get('source') != filters['source']:
                                continue
                            if 'user_id' in filters and data.get('user_id') != filters['user_id']:
                                continue
                            if 'test_case_id' in filters and data.get('test_case_id') != filters['test_case_id']:
                                continue
                        
                        # Add metadata
                        traces.append({
                            'trace_id': data['trace_id'],
                            'source': data['source'],
                            'start_time': data['start_time'],
                            'end_time': data.get('end_time'),
                            'duration_ms': data.get('total_duration_ms'),
                            'user_id': data.get('user_id'),
                            'test_case_id': data.get('test_case_id'),
                            'session_id': data.get('session_id'),
                            'event_count': len(data.get('events', [])),
                            'initial_input': (data.get('initial_input', '')[:100] + '...') 
                                           if len(data.get('initial_input', '')) > 100 
                                           else data.get('initial_input', '')
                        })
                        
                    except Exception as e:
                        print(f"Error reading trace file {trace_file}: {e}")
                        continue
            
            # Apply pagination
            traces = traces[offset:offset + limit]
            return traces
            
        except Exception as e:
            print(f"Error listing traces: {e}")
            return []
    
    async def delete_trace(self, trace_id: str) -> bool:
        """Delete trace from filesystem"""
        try:
            # Search for trace file
            for date_dir in self.base_dir.iterdir():
                if date_dir.is_dir() and date_dir.name.count('-') == 2:
                    trace_path = date_dir / f"{trace_id}.json"
                    html_path = date_dir / f"{trace_id}.html"
                    hierarchical_path = date_dir / f"{trace_id}.hierarchical.html"
                    if trace_path.exists():
                        async with self._lock:
                            trace_path.unlink()
                            # Also delete HTML files if they exist
                            if html_path.exists():
                                html_path.unlink()
                            if hierarchical_path.exists():
                                hierarchical_path.unlink()
                        return True
            
            return False
            
        except Exception as e:
            print(f"Error deleting trace {trace_id}: {e}")
            return False
    
    async def _cleanup_old_traces(self):
        """Remove traces older than retention period"""
        try:
            cutoff_date = datetime.now().date() - timedelta(days=self.retention_days)
            
            for date_dir in self.base_dir.iterdir():
                if date_dir.is_dir() and date_dir.name.count('-') == 2:
                    try:
                        dir_date = datetime.strptime(date_dir.name, "%Y-%m-%d").date()
                        if dir_date < cutoff_date:
                            # Remove entire directory
                            import shutil
                            shutil.rmtree(date_dir)
                    except ValueError:
                        # Invalid date format, skip
                        continue
                        
        except Exception as e:
            print(f"Error during trace cleanup: {e}")
    
    def _dict_to_trace(self, data: Dict[str, Any]) -> CompleteTrace:
        """Convert dictionary back to CompleteTrace object"""
        from .trace_models import TraceEvent, TraceEventType
        
        # Convert events
        events = []
        for event_data in data.get('events', []):
            # Handle both old format (with class prefix) and new format
            event_type_str = event_data['event_type']
            if event_type_str.startswith('TraceEventType.'):
                # Old format: extract the enum name
                event_type_str = event_type_str.split('.')[1].lower()
            
            events.append(TraceEvent(
                event_id=event_data['event_id'],
                trace_id=event_data['trace_id'],
                timestamp=event_data['timestamp'],
                event_type=TraceEventType(event_type_str),
                agent_type=event_data['agent_type'],
                stage=event_data['stage'],
                data=event_data['data'],
                parent_event_id=event_data.get('parent_event_id'),
                duration_ms=event_data.get('duration_ms'),
                tokens_used=event_data.get('tokens_used'),
                metadata=event_data.get('metadata', {})
            ))
        
        return CompleteTrace(
            trace_id=data['trace_id'],
            source=data['source'],
            start_time=data['start_time'],
            end_time=data.get('end_time'),
            initial_input=data['initial_input'],
            user_id=data.get('user_id'),
            test_case_id=data.get('test_case_id'),
            session_id=data.get('session_id'),
            events=events,
            summary=data.get('summary', {}),
            metadata=data.get('metadata', {}),
            total_duration_ms=data.get('total_duration_ms')
        )