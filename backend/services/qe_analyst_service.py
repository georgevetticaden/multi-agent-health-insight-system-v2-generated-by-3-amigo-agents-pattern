import json
import logging
from typing import Dict, Any, Optional, AsyncGenerator
from pathlib import Path
import asyncio
from datetime import datetime

from .agents.qe import QEAgent
# Event types for streaming
class EventType:
    TEXT = "text"
    THINKING = "thinking"
    TOOL_RESULT = "tool_result"
    ERROR = "error"

logger = logging.getLogger(__name__)

class QEAnalystService:
    """Service for orchestrating QE Agent interactions with trace analysis"""
    
    def __init__(self):
        self.agents: Dict[str, QEAgent] = {}  # Store agents by trace_id
        
        # Use unified evaluation data config
        from evaluation.data.config import EvaluationDataConfig
        self.traces_dir = EvaluationDataConfig.TRACES_DIR
        logger.info(f"Using unified trace storage: {self.traces_dir}")
        
    def _get_trace_file_path(self, trace_id: str) -> Optional[Path]:
        """Find the trace file for a given trace ID"""
        # Search in today's folder first
        today = datetime.now().strftime("%Y-%m-%d")
        today_dir = self.traces_dir / today
        
        if today_dir.exists():
            # Try new naming pattern first (HHMMSS_trace_id.json)
            for trace_file in today_dir.glob(f"*_{trace_id}.json"):
                if trace_file.exists():
                    return trace_file
            
            # Look for the trace data file (try old naming conventions)
            trace_file = today_dir / f"{trace_id}.json"
            if trace_file.exists():
                return trace_file
            # Try legacy format
            trace_file = today_dir / f"{trace_id}.trace.json"
            if trace_file.exists():
                return trace_file
        
        # Search in all date folders
        for date_dir in sorted(self.traces_dir.iterdir(), reverse=True):
            if date_dir.is_dir():
                # Try new naming pattern first
                for trace_file in date_dir.glob(f"*_{trace_id}.json"):
                    if trace_file.exists():
                        return trace_file
                
                trace_file = date_dir / f"{trace_id}.json"
                if trace_file.exists():
                    return trace_file
                # Try legacy format
                trace_file = date_dir / f"{trace_id}.trace.json"
                if trace_file.exists():
                    return trace_file
        
        return None
    
    def _extract_trace_context(self, trace_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract relevant context from trace data"""
        context = {
            "query": None,
            "complexity": None,
            "specialists": [],
            "stages": {},
            "tool_calls": []
        }
        
        # Find the query
        for event in trace_data.get("events", []):
            if event.get("event_type") == "user_query":
                context["query"] = event.get("data", {}).get("query", "Unknown query")
                break
        
        # Find complexity and specialists from task creation
        for event in trace_data.get("events", []):
            if event.get("stage") == "task_creation":
                if event.get("event_type") == "llm_response":
                    response = event.get("data", {}).get("response_text", "")
                    # Extract complexity
                    if "<complexity>" in response:
                        start = response.find("<complexity>") + 12
                        end = response.find("</complexity>", start)
                        if end > start:
                            context["complexity"] = response[start:end].strip()
                    
                    # Extract specialists from task assignments
                    if "<specialist>" in response:
                        import re
                        specialists = re.findall(r'<specialist>([^<]+)</specialist>', response)
                        context["specialists"] = [s.strip().lower().replace(" ", "_") for s in specialists]
        
        # Extract key stages
        current_stage = None
        for event in trace_data.get("events", []):
            stage = event.get("stage")
            if stage and stage != current_stage:
                current_stage = stage
                if stage not in context["stages"]:
                    context["stages"][stage] = {
                        "status": "completed",
                        "events": []
                    }
            
            if current_stage:
                context["stages"][current_stage]["events"].append({
                    "type": event.get("event_type"),
                    "timestamp": event.get("timestamp")
                })
        
        # Extract tool calls
        for event in trace_data.get("events", []):
            if event.get("event_type") == "tool_invocation":
                context["tool_calls"].append({
                    "tool": event.get("data", {}).get("tool_name"),
                    "stage": event.get("stage"),
                    "parameters": event.get("data", {}).get("parameters", {})
                })
        
        return context
    
    def _get_or_create_agent(self, trace_id: str) -> QEAgent:
        """Get existing agent or create new one for trace"""
        if trace_id not in self.agents:
            self.agents[trace_id] = QEAgent(trace_id)
        return self.agents[trace_id]
    
    async def process_qe_request(
        self,
        trace_id: str,
        message: str,
        stage_context: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Process a QE chat request
        
        Args:
            trace_id: The trace ID to analyze
            message: User's message
            stage_context: Optional context about the stage being discussed
        """
        try:
            # Get or create agent
            agent = self._get_or_create_agent(trace_id)
            
            # Load trace context if not already loaded
            if not agent.current_trace_context:
                trace_file = self._get_trace_file_path(trace_id)
                if not trace_file:
                    yield {
                        "type": EventType.ERROR,
                        "content": f"Trace file not found for ID: {trace_id}"
                    }
                    return
                
                # Load and parse trace
                with open(trace_file, 'r') as f:
                    trace_data = json.load(f)
                
                # Extract context
                context = self._extract_trace_context(trace_data)
                agent.set_trace_context(context)
                
                # Yield initial context confirmation
                yield {
                    "type": EventType.THINKING,
                    "content": f"Analyzing trace for query: {context['query'][:100]}..."
                }
                await asyncio.sleep(0.001)  # Allow client to process
            
            # Process the message through the agent
            async for chunk in agent.analyze_user_feedback(message, stage_context):
                # Transform to our event format
                if chunk["type"] == "text":
                    yield {
                        "type": EventType.TEXT,
                        "content": chunk["content"]
                    }
                elif chunk["type"] == "test_case":
                    yield {
                        "type": EventType.TOOL_RESULT,
                        "content": chunk["content"],
                        "data": {
                            "format": "python",
                            "copyable": True
                        }
                    }
                elif chunk["type"] == "test_case_update":
                    # Pass through test case update event
                    yield {
                        "type": "test_case_update",
                        "content": chunk["content"]
                    }
                elif chunk["type"] == "action_menu":
                    # Pass through action menu events
                    yield {
                        "type": "action_menu",
                        "content": chunk["content"]
                    }
                elif chunk["type"] == "start_evaluation":
                    # Pass through evaluation start event
                    yield {
                        "type": "start_evaluation",
                        "content": chunk["content"]
                    }
                elif chunk["type"] == "save_test_case":
                    # Pass through save test case event
                    yield {
                        "type": "save_test_case",
                        "content": chunk["content"]
                    }
                elif chunk["type"] == "error":
                    yield {
                        "type": EventType.ERROR,
                        "content": chunk["content"]
                    }
                
                # Small delay for streaming
                await asyncio.sleep(0.001)
                
        except Exception as e:
            logger.error(f"Error processing QE request: {e}")
            yield {
                "type": EventType.ERROR,
                "content": f"Error processing request: {str(e)}"
            }
    
    def get_agent_summary(self, trace_id: str) -> Optional[Dict[str, Any]]:
        """Get summary of QE agent conversation"""
        agent = self.agents.get(trace_id)
        if agent:
            return agent.get_conversation_summary()
        return None
    
    def reset_agent(self, trace_id: str):
        """Reset agent conversation for a trace"""
        if trace_id in self.agents:
            self.agents[trace_id].reset_conversation()
    
    def set_evaluation_result(self, trace_id: str, result: Dict[str, Any]) -> bool:
        """Set evaluation result for a QE Agent
        
        Args:
            trace_id: The trace ID for the agent
            result: Evaluation result data from frontend
            
        Returns:
            True if agent was found and updated, False otherwise
        """
        agent = self.agents.get(trace_id)
        if agent:
            agent.set_evaluation_result(result)
            logger.info(f"Set evaluation result for trace {trace_id}")
            return True
        else:
            logger.warning(f"No QE Agent found for trace {trace_id}")
            return False
    
    def cleanup_old_agents(self, max_age_minutes: int = 30):
        """Clean up agents that haven't been used recently"""
        # TODO: Implement cleanup based on last activity timestamp
        pass