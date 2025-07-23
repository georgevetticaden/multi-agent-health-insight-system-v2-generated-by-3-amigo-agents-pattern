"""
Trace Parser for Evaluation

Extracts evaluation data from execution traces to enable trace-based evaluation
using the same logic as live evaluation.

This parser is designed to work with the CLI evaluator by extracting the exact
data that would be returned from live CMO agent execution.
"""

import json
import logging
import re
from typing import Dict, List, Tuple, Any, Optional, Set
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass

from services.tracing.trace_models import CompleteTrace, TraceEvent, TraceEventType
from services.agents.models import QueryComplexity, MedicalSpecialty

logger = logging.getLogger(__name__)


@dataclass
class MockSpecialistTask:
    """Mock specialist task to match CMOAgent output."""
    specialist: MedicalSpecialty
    objective: str
    context: str
    expected_output: str
    priority: str
    max_tool_calls: int = 3


class TraceDataExtractor:
    """
    Extracts evaluation data from execution traces.
    
    This class is designed to extract data in the exact format that the
    CLI evaluator expects from CMOAgent execution.
    """
    
    def __init__(self):
        self.logger = logger
    
    def extract_cmo_evaluation_data(self, trace: CompleteTrace) -> Tuple[QueryComplexity, str, Dict[str, Any], List[MockSpecialistTask]]:
        """
        Extract CMO evaluation data from trace in the format expected by CLI evaluator.
        
        Returns:
            - complexity: QueryComplexity enum
            - approach: The analytical approach text
            - initial_data: Initial data gathering results (including tool calls)
            - specialist_tasks: List of specialist tasks created
            
        This matches the output of:
        - CMOAgent.analyze_query_with_tools() -> (complexity, approach, initial_data)
        - CMOAgent.create_specialist_tasks() -> List[SpecialistTask]
        """
        logger.info(f"=== TRACE DATA EXTRACTION START ===")
        logger.info(f"Extracting data from trace with {len(trace.events)} events")
        
        # Extract Stage 1 data (query analysis)
        logger.info("Stage 1: Extracting query analysis data...")
        complexity = self._extract_complexity_enum(trace)
        logger.info(f"  - Extracted complexity: {complexity.value}")
        
        approach = self._extract_approach(trace)
        logger.info(f"  - Extracted approach: {len(approach)} characters")
        if approach:
            logger.info(f"    First 100 chars: {approach[:100]}...")
        
        initial_data = self._extract_initial_data_cmo_format(trace)
        logger.info(f"  - Extracted initial data:")
        logger.info(f"    Tool calls made: {initial_data.get('tool_calls_made', 0)}")
        logger.info(f"    Successful calls: {len([tc for tc in initial_data.get('tool_calls', []) if tc.get('success')])}")
        
        # Extract execution time
        execution_time = self._extract_execution_time(trace)
        initial_data['execution_time_ms'] = execution_time
        logger.info(f"  - Extracted execution time: {execution_time}ms")
        
        # Extract Stage 2 data (specialist tasks)
        logger.info("Stage 2: Extracting specialist tasks...")
        specialist_tasks = self._extract_specialist_tasks_as_objects(trace)
        logger.info(f"  - Extracted {len(specialist_tasks)} specialist tasks")
        for i, task in enumerate(specialist_tasks):
            logger.info(f"    Task {i+1}: {task.specialist.value} (priority: {task.priority})")
        
        logger.info(f"=== TRACE DATA EXTRACTION COMPLETE ===")
        return complexity, approach, initial_data, specialist_tasks
    
    def _extract_query(self, trace: CompleteTrace) -> str:
        """Extract the original query from trace."""
        for event in trace.events:
            if event.event_type == TraceEventType.USER_QUERY:
                return event.data.get("query", "")
        return ""
    
    def _extract_complexity_enum(self, trace: CompleteTrace) -> QueryComplexity:
        """Extract complexity as QueryComplexity enum."""
        complexity_str = "SIMPLE"  # Default
        
        # Look for complexity in stage end events
        for event in trace.events:
            if (event.event_type == TraceEventType.STAGE_END and 
                event.stage == "query_analysis"):
                complexity_str = event.data.get("complexity", "SIMPLE")
                break
        
        # Fallback: look in LLM responses
        if complexity_str == "SIMPLE":
            for event in trace.events:
                if (event.event_type == TraceEventType.LLM_RESPONSE and
                    event.stage == "query_analysis"):
                    content = event.data.get("content", "")
                    if "<complexity>" in content:
                        match = re.search(r'<complexity>(.*?)</complexity>', content)
                        if match:
                            complexity_str = match.group(1).upper()
                            break
        
        # Convert to enum - QueryComplexity enum values are lowercase
        try:
            return QueryComplexity(complexity_str.lower())
        except (KeyError, ValueError):
            logger.warning(f"Unknown complexity: {complexity_str}, defaulting to SIMPLE")
            return QueryComplexity.SIMPLE
    
    def _extract_approach(self, trace: CompleteTrace) -> str:
        """Extract analytical approach from trace."""
        # First try to find in the proper prompt phase
        for event in trace.events:
            if (event.event_type == TraceEventType.LLM_RESPONSE and
                event.stage == "query_analysis" and
                event.data.get("prompt_file") == "2_define_analytical_approach.txt"):
                # Try both 'content' and 'response_text' fields
                content = event.data.get("response_text", event.data.get("content", ""))
                if "<approach>" in content:
                    match = re.search(r'<approach>(.*?)</approach>', content, re.DOTALL)
                    if match:
                        return match.group(1).strip()
        
        # Fallback: look in any query analysis response
        for event in trace.events:
            if (event.event_type == TraceEventType.LLM_RESPONSE and
                event.stage == "query_analysis"):
                # Try both 'content' and 'response_text' fields
                content = event.data.get("response_text", event.data.get("content", ""))
                if "<approach>" in content:
                    match = re.search(r'<approach>(.*?)</approach>', content, re.DOTALL)
                    if match:
                        return match.group(1).strip()
        return ""
    
    def _extract_initial_data_cmo_format(self, trace: CompleteTrace) -> Dict[str, Any]:
        """
        Extract initial data in the format CMOAgent returns.
        
        The CMOAgent returns initial_data with structure like:
        {
            'tool_calls': [...],  # List of tool call details
            'tool_calls_made': 3,  # Count
            'health_context': {...},  # Merged results
            ...
        }
        """
        initial_data = {
            'tool_calls': [],
            'tool_calls_made': 0,
            'health_context': {},
            'total_tool_calls_all_stages': 0,  # Track total across all stages
            'tool_calls_by_stage': {},  # Track by stage for debugging
            'data_available': False  # Track if data was successfully gathered
        }
        
        # Count tool calls across ALL stages, not just query_analysis
        all_tool_calls = []
        tool_calls_by_stage = {}
        
        for i, event in enumerate(trace.events):
            if event.event_type == TraceEventType.TOOL_INVOCATION:
                stage = event.stage or 'unknown'
                
                tool_call = {
                    'tool_name': event.data.get("tool_name", ""),
                    'parameters': event.data.get("parameters", {}),
                    'stage': stage,
                    'success': False,
                    'result': None
                }
                
                # Find corresponding result
                for j in range(i + 1, len(trace.events)):
                    result_event = trace.events[j]
                    if (result_event.event_type == TraceEventType.TOOL_RESULT and
                        result_event.data.get("tool_name") == tool_call["tool_name"]):
                        tool_call['success'] = not result_event.data.get("error", False)
                        tool_call['result'] = result_event.data.get("result")
                        
                        # Merge successful results into health_context if from query_analysis
                        if stage == "query_analysis" and tool_call['success'] and tool_call['result']:
                            initial_data['health_context'].update(tool_call['result'])
                        break
                
                all_tool_calls.append(tool_call)
                
                # Track by stage
                if stage not in tool_calls_by_stage:
                    tool_calls_by_stage[stage] = []
                tool_calls_by_stage[stage].append(tool_call)
        
        # Store query_analysis tool calls for backward compatibility
        initial_data['tool_calls'] = [tc for tc in all_tool_calls if tc['stage'] == 'query_analysis']
        initial_data['tool_calls_made'] = len(initial_data['tool_calls'])
        
        # Calculate successful tool calls
        successful_query_calls = len([tc for tc in initial_data['tool_calls'] if tc.get('success', False)])
        successful_all_calls = len([tc for tc in all_tool_calls if tc.get('success', False)])
        
        initial_data['successful_tool_calls'] = successful_query_calls  # For backward compatibility
        initial_data['total_successful_tool_calls'] = successful_all_calls  # All stages
        
        # Store total tool calls across all stages
        initial_data['total_tool_calls_all_stages'] = len(all_tool_calls)
        initial_data['tool_calls_by_stage'] = {
            stage: len(calls) for stage, calls in tool_calls_by_stage.items()
        }
        
        # Extract data_available from query_analysis stage events
        for event in trace.events:
            if (event.stage == "query_analysis" and 
                hasattr(event, 'data') and 
                isinstance(event.data, dict) and 
                'data_available' in event.data):
                initial_data['data_available'] = event.data['data_available']
                logger.info(f"  - Found data_available: {initial_data['data_available']}")
                break
        
        # If no explicit data_available found, infer from successful tool calls
        if not initial_data['data_available'] and successful_query_calls > 0:
            initial_data['data_available'] = True
            logger.info(f"  - Inferred data_available: True (from {successful_query_calls} successful calls)")
        
        logger.info(f"  - Tool calls by stage: {initial_data['tool_calls_by_stage']}")
        logger.info(f"  - Total tool calls across all stages: {initial_data['total_tool_calls_all_stages']}")
        logger.info(f"  - Successful tool calls (query stage): {successful_query_calls}/{initial_data['tool_calls_made']}")
        logger.info(f"  - Successful tool calls (all stages): {successful_all_calls}/{len(all_tool_calls)}")
        logger.info(f"  - Data available: {initial_data['data_available']}")
        
        return initial_data
    
    def _extract_specialist_tasks_as_objects(self, trace: CompleteTrace) -> List[MockSpecialistTask]:
        """Extract specialist tasks as MockSpecialistTask objects."""
        tasks = []
        
        # Look for LLM response in task_creation stage
        for event in trace.events:
            if (event.event_type == TraceEventType.LLM_RESPONSE and
                event.stage == "task_creation"):
                # Try both 'response_text' and 'content' fields
                content = event.data.get("response_text", event.data.get("content", ""))
                tasks = self._parse_tasks_from_xml_as_objects(content)
                if tasks:
                    break
        
        # Fallback: check STAGE_END event for specialists list
        if not tasks:
            for event in trace.events:
                if (event.event_type == TraceEventType.STAGE_END and
                    event.stage == "task_creation"):
                    specialists = event.data.get("specialists", [])
                    # Convert specialist names to tasks (basic fallback)
                    for spec in specialists:
                        try:
                            # MedicalSpecialty enum values are lowercase
                            spec_lower = spec.lower()
                            # Handle common variations
                            if spec_lower == 'preventive_medicine' or spec_lower == 'preventative_medicine':
                                spec_lower = 'preventive_medicine'
                            elif spec_lower == 'lab' or spec_lower == 'lab_medicine':
                                spec_lower = 'laboratory_medicine'
                            specialty = MedicalSpecialty(spec_lower)
                        except (KeyError, ValueError):
                            logger.warning(f"Unknown specialty: {spec}, using laboratory_medicine as default")
                            specialty = MedicalSpecialty.LABORATORY_MEDICINE
                        
                        task = MockSpecialistTask(
                            specialist=specialty,
                            objective=f"Analyze data for {spec}",
                            context="Extracted from stage end event",
                            expected_output="Analysis results",
                            priority="MEDIUM",
                            max_tool_calls=3
                        )
                        tasks.append(task)
                    break
        
        return tasks
    
    def _parse_tasks_from_xml_as_objects(self, xml_content: str) -> List[MockSpecialistTask]:
        """Parse specialist tasks from XML response as objects."""
        tasks = []
        
        # Try both <task> and <specialist_task> formats
        patterns = [
            # New format: <task>
            re.compile(
                r'<task>.*?'
                r'<specialist>(.*?)</specialist>.*?'
                r'<objective>(.*?)</objective>.*?'
                r'<context>(.*?)</context>.*?'
                r'<expected_output>(.*?)</expected_output>.*?'
                r'<priority>(.*?)</priority>.*?'
                r'</task>',
                re.DOTALL
            ),
            # Old format: <specialist_task>
            re.compile(
                r'<specialist_task>.*?'
                r'<specialty>(.*?)</specialty>.*?'
                r'<priority>(.*?)</priority>.*?'
                r'<objective>(.*?)</objective>.*?'
                r'<context>(.*?)</context>.*?'
                r'<expected_output>(.*?)</expected_output>.*?'
                r'</specialist_task>',
                re.DOTALL
            )
        ]
        
        for pattern in patterns:
            matches = list(pattern.finditer(xml_content))
            if matches:
                for match in matches:
                    groups = match.groups()
                    
                    # Handle different group orders
                    if len(groups) == 5:
                        if pattern == patterns[0]:  # <task> format
                            specialty_str, objective, context, expected_output, priority = groups
                        else:  # <specialist_task> format
                            specialty_str, priority, objective, context, expected_output = groups
                    else:
                        logger.warning(f"Unexpected number of groups in XML match: {len(groups)}")
                        continue
                    
                    try:
                        # Handle both 'specialist' and 'specialty' field names
                        # MedicalSpecialty enum values are lowercase
                        specialty_str = specialty_str.strip().lower()
                        # Handle common variations
                        if specialty_str == 'preventive_medicine' or specialty_str == 'preventative_medicine':
                            specialty_str = 'preventive_medicine'
                        elif specialty_str == 'lab' or specialty_str == 'lab_medicine':
                            specialty_str = 'laboratory_medicine'
                        specialty = MedicalSpecialty(specialty_str)
                    except (KeyError, ValueError):
                        logger.warning(f"Unknown specialty in XML: {specialty_str}, using laboratory_medicine as default")
                        specialty = MedicalSpecialty.LABORATORY_MEDICINE
                    
                    # Convert priority numbers to text if needed
                    priority_str = priority.strip()
                    if priority_str.isdigit():
                        priority_map = {"1": "HIGH", "2": "MEDIUM", "3": "LOW"}
                        priority_str = priority_map.get(priority_str, "MEDIUM")
                    
                    task = MockSpecialistTask(
                        specialist=specialty,
                        objective=objective.strip(),
                        context=context.strip(),
                        expected_output=expected_output.strip(),
                        priority=priority_str,
                        max_tool_calls=3
                    )
                    tasks.append(task)
                break  # Stop after first successful pattern
        
        return tasks
    
    def _extract_execution_time(self, trace: CompleteTrace) -> float:
        """Extract total execution time from trace events."""
        # Try to get from trace summary first
        if trace.total_duration_ms is not None and trace.total_duration_ms > 0:
            logger.info(f"  - Using total_duration_ms from trace: {trace.total_duration_ms}ms")
            return trace.total_duration_ms
        
        # Look for duration in summary
        if hasattr(trace, 'summary') and trace.summary:
            if 'duration_ms' in trace.summary:
                duration = trace.summary['duration_ms']
                logger.info(f"  - Using duration_ms from summary: {duration}ms")
                return float(duration)
        
        # Otherwise calculate from events
        start_time = None
        end_time = None
        
        # Find first and last event timestamps
        for event in trace.events:
            if event.timestamp:
                if start_time is None:
                    start_time = event.timestamp
                end_time = event.timestamp
        
        # Calculate duration if we have timestamps
        if start_time and end_time:
            try:
                from datetime import datetime
                start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                duration = (end_dt - start_dt).total_seconds() * 1000  # Convert to ms
                logger.info(f"  - Calculated duration from timestamps: {duration}ms")
                return duration
            except Exception as e:
                logger.warning(f"Failed to parse timestamps for duration calculation: {e}")
        
        # Default to a reasonable value if we can't calculate
        logger.warning("Could not extract execution time, using default 300ms")
        return 300.0  # Default to 300ms instead of 0


class TraceBasedEvaluationAdapter:
    """
    Adapter to use CLI evaluator with trace data.
    
    This allows the comprehensive CLI evaluation logic to work with
    traces instead of live execution.
    """
    
    def __init__(self, evaluator):
        self.evaluator = evaluator
        self.extractor = TraceDataExtractor()
    
    async def evaluate_from_trace(self, test_case, trace: CompleteTrace):
        """
        Evaluate a test case using trace data instead of live execution.
        
        This method extracts data from the trace and feeds it to the
        evaluator as if it came from live execution.
        """
        # Extract evaluation data from trace
        trace_data = self.extractor.extract_from_trace(trace)
        
        # Create a mock agent response that matches what live execution would return
        mock_complexity = trace_data["complexity"]
        mock_approach = trace_data["approach"]
        mock_initial_data = trace_data["initial_data"]
        mock_tasks = trace_data["specialist_tasks"]
        
        # Call evaluator's evaluation logic directly, bypassing agent execution
        # This would require refactoring the CLI evaluator to separate
        # execution from evaluation
        return await self.evaluator.evaluate_with_data(
            test_case=test_case,
            complexity=mock_complexity,
            approach=mock_approach,
            initial_data=mock_initial_data,
            specialist_tasks=mock_tasks
        )