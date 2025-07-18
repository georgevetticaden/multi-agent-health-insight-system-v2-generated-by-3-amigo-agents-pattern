"""
Trace hierarchy builder for creating hierarchical event structures.

Organizes flat event lists into hierarchical trees based on relationships
between events (LLM calls, tool invocations, responses, etc.).
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from .trace_models import TraceEvent, TraceEventType, CompleteTrace


@dataclass
class HierarchicalEvent:
    """Represents an event with its children in a hierarchy"""
    event: TraceEvent
    children: List['HierarchicalEvent'] = field(default_factory=list)
    event_index: int = 0
    level: int = 0
    
    @property
    def is_llm_call(self) -> bool:
        return self.event.event_type == TraceEventType.LLM_PROMPT
    
    @property
    def is_tool_invocation(self) -> bool:
        return self.event.event_type == TraceEventType.TOOL_INVOCATION
    
    @property
    def has_tool_calls(self) -> bool:
        if self.event.event_type == TraceEventType.LLM_RESPONSE:
            return bool(self.event.data and self.event.data.get('tool_calls'))
        return False


@dataclass
class StageInfo:
    """Information about a stage within an agent's execution"""
    stage_name: str
    events: List[HierarchicalEvent] = field(default_factory=list)
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    duration_ms: float = 0
    llm_calls: int = 0
    tool_calls: int = 0
    tokens_used: int = 0

@dataclass
class AgentSection:
    """Groups events by agent with metadata"""
    agent_name: str
    agent_type: str
    stages: Dict[str, StageInfo] = field(default_factory=dict)
    events: List[HierarchicalEvent] = field(default_factory=list)
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    total_duration_ms: float = 0
    llm_calls: int = 0
    tool_calls: int = 0
    tokens_used: int = 0
    key_findings: List[str] = field(default_factory=list)
    

def build_trace_hierarchy(trace: CompleteTrace) -> Tuple[List[AgentSection], Dict[str, Any]]:
    """
    Build hierarchical structure from flat event list.
    
    Returns:
        - List of agent sections with hierarchical events
        - Summary statistics
    """
    # Group events by agent only (not stage)
    agent_groups: Dict[str, AgentSection] = {}
    
    # Track relationships
    llm_prompt_stack: List[HierarchicalEvent] = []
    pending_tool_results: Dict[str, HierarchicalEvent] = {}
    
    for i, event in enumerate(trace.events):
        agent_type = event.agent_type
        stage = event.stage
        
        # Skip system/user events for agent grouping
        if agent_type in ['system', 'user']:
            continue
            
        # Create agent section if needed
        if agent_type not in agent_groups:
            agent_groups[agent_type] = AgentSection(
                agent_name=_format_agent_name(agent_type),
                agent_type=agent_type,
                start_time=event.timestamp
            )
        
        section = agent_groups[agent_type]
        
        # Create stage if needed
        if stage not in section.stages:
            section.stages[stage] = StageInfo(
                stage_name=stage,
                start_time=event.timestamp
            )
        
        stage_info = section.stages[stage]
        hierarchical_event = HierarchicalEvent(event=event, event_index=i)
        
        # Handle different event types
        if event.event_type == TraceEventType.LLM_PROMPT:
            # New LLM call - this is a top-level event in the stage
            stage_info.events.append(hierarchical_event)
            stage_info.llm_calls += 1
            section.llm_calls += 1
            llm_prompt_stack.append(hierarchical_event)
            
        elif event.event_type == TraceEventType.LLM_RESPONSE:
            # Response to the most recent prompt
            if llm_prompt_stack:
                parent = llm_prompt_stack[-1]
                parent.children.append(hierarchical_event)
                hierarchical_event.level = 1
                
                # Check if this response includes tool calls
                if hierarchical_event.has_tool_calls:
                    # Keep the prompt on stack for tool results
                    pass
                else:
                    # Pop the prompt since it's complete
                    llm_prompt_stack.pop()
            else:
                # Orphaned response
                stage_info.events.append(hierarchical_event)
                
        elif event.event_type == TraceEventType.TOOL_INVOCATION:
            # Tool invocation - child of the LLM response
            if llm_prompt_stack and llm_prompt_stack[-1].children:
                # Add as child of the most recent LLM response
                llm_response = llm_prompt_stack[-1].children[-1]
                llm_response.children.append(hierarchical_event)
                hierarchical_event.level = 2
                
                # Track for linking with result
                tool_id = event.data.get('tool_id') if event.data else None
                if tool_id:
                    pending_tool_results[tool_id] = hierarchical_event
                    
            stage_info.tool_calls += 1
            section.tool_calls += 1
            
        elif event.event_type == TraceEventType.TOOL_RESULT:
            # Tool result - link to invocation
            tool_id = event.data.get('linked_tool_invocation_id') if event.data else None
            if tool_id and tool_id in pending_tool_results:
                parent = pending_tool_results[tool_id]
                parent.children.append(hierarchical_event)
                hierarchical_event.level = 3
                del pending_tool_results[tool_id]
            else:
                # Orphaned result
                if llm_prompt_stack:
                    llm_prompt_stack[-1].children.append(hierarchical_event)
                    hierarchical_event.level = 1
                else:
                    stage_info.events.append(hierarchical_event)
                    
        elif event.event_type in [TraceEventType.STAGE_START, TraceEventType.STAGE_END]:
            # Stage markers - top level
            stage_info.events.append(hierarchical_event)
            if event.event_type == TraceEventType.STAGE_END:
                stage_info.end_time = event.timestamp
                
        else:
            # Other events - add as top level
            stage_info.events.append(hierarchical_event)
        
        # Update metrics
        if event.tokens_used:
            stage_info.tokens_used += event.tokens_used
            section.tokens_used += event.tokens_used
        if event.duration_ms:
            stage_info.duration_ms += event.duration_ms
            section.total_duration_ms += event.duration_ms
            
        # Extract key findings
        if event.event_type == TraceEventType.LLM_RESPONSE and event.data:
            _extract_key_findings(event, section.key_findings)
    
    # Flatten stages into events for each agent section
    for section in agent_groups.values():
        # Sort stages by start time
        sorted_stages = sorted(section.stages.items(), key=lambda x: x[1].start_time or "")
        
        # Flatten events from all stages into section events
        for stage_name, stage_info in sorted_stages:
            section.events.extend(stage_info.events)
        
        # Update section end time
        if section.stages:
            last_stage = sorted_stages[-1][1]
            section.end_time = last_stage.end_time or last_stage.start_time
    
    # Convert to list and sort by first event time
    sections = list(agent_groups.values())
    sections.sort(key=lambda s: s.start_time or "")
    
    # Calculate summary (count actual agents, not stages)
    unique_agents = set(s.agent_type for s in sections)
    summary = {
        "total_agents": len(unique_agents),
        "total_llm_calls": sum(s.llm_calls for s in sections),
        "total_tool_calls": sum(s.tool_calls for s in sections),
        "total_tokens": sum(s.tokens_used for s in sections),
        "total_duration_ms": trace.total_duration_ms or 0,
        "total_stages": sum(len(s.stages) for s in sections)
    }
    
    return sections, summary


def _format_agent_name(agent_type: str) -> str:
    """Format agent type into readable name"""
    name_map = {
        "cmo": "Chief Medical Officer (CMO)",
        "cardiology": "Cardiology Specialist",
        "endocrinology": "Endocrinology Specialist",
        "laboratory_medicine": "Laboratory Medicine Specialist",
        "pharmacy": "Pharmacy Specialist",
        "nutrition": "Nutrition Specialist",
        "preventive_medicine": "Preventive Medicine Specialist",
        "user": "User",
        "system": "System"
    }
    return name_map.get(agent_type.lower(), agent_type.title())


def _extract_key_findings(event: TraceEvent, findings: List[str]) -> None:
    """Extract key findings from LLM responses"""
    if not event.data:
        return
        
    response_text = event.data.get('response_text', '')
    
    # Look for specific patterns
    if 'glucose' in response_text.lower() and 'mg/dl' in response_text.lower():
        # Extract glucose values
        import re
        glucose_pattern = r'(\d+(?:\.\d+)?)\s*mg/dL'
        matches = re.findall(glucose_pattern, response_text)
        for value in matches[:1]:  # Just first one
            findings.append(f"Glucose: {value} mg/dL")
            
    # Look for complexity assessment
    if 'complexity' in response_text.lower():
        for complexity in ['simple', 'standard', 'complex', 'comprehensive']:
            if complexity in response_text.lower():
                findings.append(f"Complexity: {complexity.upper()}")
                break
                
    # Look for key terms
    key_terms = ['elevated', 'normal', 'low', 'concerning', 'stable', 'improved']
    for term in key_terms:
        if term in response_text.lower():
            findings.append(f"Status: {term.capitalize()}")
            break