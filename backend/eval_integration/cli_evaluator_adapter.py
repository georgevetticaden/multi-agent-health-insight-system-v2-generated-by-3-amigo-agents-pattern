"""
CLI Evaluator Adapter

This module provides an adapter to use the CLI evaluator from the backend,
enabling trace-based evaluation using the FULL evaluation framework.

Instead of reimplementing evaluation logic, this adapter:
1. Extracts data from traces using TraceDataExtractor
2. Creates a MockCMOAgent with the extracted data
3. Uses the real CMOEvaluator from the evaluation framework
4. Returns the comprehensive evaluation results with all features
"""

import sys
import os
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
import json
from datetime import datetime

# Create a logger for this module
logger = logging.getLogger(__name__)

# Import from backend modules  
from eval_integration.mock_agents import MockCMOAgent
from eval_integration.trace_parser import TraceDataExtractor
from eval_integration.subprocess_evaluator import run_evaluation_subprocess
from services.tracing.trace_models import CompleteTrace, TraceEvent, TraceEventType
from services.agents.models import QueryComplexity, MedicalSpecialty


class CLIEvaluatorAdapter:
    """
    Adapter to use the FULL CLI evaluation framework with trace data.
    
    This adapter:
    1. Extracts data from execution traces
    2. Creates a MockCMOAgent that replays the trace data
    3. Uses the real CMOEvaluator with all its features
    4. Returns comprehensive evaluation results
    
    This ensures we get:
    - Full LLM Judge evaluation with sophisticated prompts
    - Hybrid evaluation methods (deterministic + LLM)
    - Component-based scoring with proper weights
    - Comprehensive failure analysis
    - Semantic similarity scoring for specialists
    """
    
    def __init__(self, cmo_agent=None, anthropic_client=None):
        """
        Initialize the adapter.
        
        Args:
            cmo_agent: Optional CMO agent (not used - we create MockCMOAgent)
            anthropic_client: Anthropic client for LLM judge evaluation
        """
        self.extractor = TraceDataExtractor()
        self.anthropic_client = anthropic_client
    
    async def evaluate_from_trace(
        self,
        test_case: Dict[str, Any],
        trace: CompleteTrace
    ) -> Dict[str, Any]:
        """
        Evaluate a test case using trace data with the FULL evaluation framework.
        
        This method:
        1. Extracts data from the trace
        2. Runs evaluation in subprocess to avoid import issues
        3. Returns the comprehensive results
        
        Args:
            test_case: Test case dict from QE Agent
            trace: Complete trace of the execution
            
        Returns:
            Dictionary with comprehensive evaluation results including:
            - All dimension scores with component breakdowns
            - LLM Judge analysis results
            - Failure analyses with recommendations
            - Full metadata and context
        """
        logger.info(f"=== CLI EVALUATOR ADAPTER: Starting FULL framework evaluation ===")
        logger.info(f"Test case ID: {test_case.get('id', 'unknown')}")
        logger.info(f"Trace ID: {trace.trace_id}")
        
        # Extract data from trace
        logger.info("Extracting evaluation data from trace...")
        complexity, approach, initial_data, specialist_tasks = \
            self.extractor.extract_cmo_evaluation_data(trace)
        
        logger.info(f"Extracted data:")
        logger.info(f"  - Complexity: {complexity.value}")
        logger.info(f"  - Approach length: {len(approach)} chars")
        logger.info(f"  - Initial data tool calls: {initial_data.get('tool_calls_made', 0)}")
        logger.info(f"  - Specialist tasks: {len(specialist_tasks)} tasks")
        logger.info(f"  - Specialists: {[task.specialist.value for task in specialist_tasks]}")
        
        # Convert to serializable format for subprocess
        trace_data = {
            'complexity': complexity.value,  # Convert enum to string
            'approach': approach,
            'initial_data': initial_data,
            'specialist_tasks': [
                {
                    'specialist': task.specialist.value,  # Convert enum to string
                    'objective': task.objective,
                    'context': task.context,
                    'expected_output': task.expected_output,
                    'priority': task.priority,
                    'max_tool_calls': task.max_tool_calls
                }
                for task in specialist_tasks
            ]
        }
        
        # Get API key if available
        api_key = None
        if self.anthropic_client:
            # Try to extract API key from client
            try:
                api_key = self.anthropic_client.api_key
                logger.info(f"✅ API key extracted from Anthropic client (length: {len(api_key) if api_key else 0})")
            except:
                # Try environment as fallback
                from dotenv import load_dotenv
                load_dotenv()
                api_key = os.environ.get('ANTHROPIC_API_KEY')
                if api_key:
                    logger.info(f"✅ API key found in environment variable (length: {len(api_key)})")
                else:
                    logger.warning("⚠️  No API key available - LLM Judge will be disabled")
        else:
            # No client provided, try environment
            from dotenv import load_dotenv
            load_dotenv()
            api_key = os.environ.get('ANTHROPIC_API_KEY')
            if api_key:
                logger.info(f"✅ API key found in environment variable (length: {len(api_key)})")
            else:
                logger.warning("⚠️  No API key available - LLM Judge will be disabled")
        
        # Run evaluation in subprocess
        logger.info("Running evaluation in subprocess...")
        try:
            result = run_evaluation_subprocess(test_case, trace_data, api_key)
            logger.info(f"=== FULL EVALUATION COMPLETE ===")
            logger.info(f"Overall score: {result.get('overall_score', 0):.3f}")
            return result
        except Exception as e:
            logger.error(f"Subprocess evaluation failed: {e}")
            # No fallback - fail properly
            raise RuntimeError(f"Evaluation failed: {str(e)}. The full evaluation framework must be used.")
    
    def _create_fallback_result(
        self,
        test_case: Dict[str, Any],
        complexity: QueryComplexity,
        approach: str,
        initial_data: Dict[str, Any],
        specialist_tasks: List[Any]
    ) -> Dict[str, Any]:
        """Create a fallback result if subprocess evaluation fails."""
        logger.warning("Using fallback evaluation result")
        
        # Basic scoring logic
        complexity_score = 1.0 if test_case.get('expected_complexity', '').upper() == complexity.value.upper() else 0.0
        
        expected_specs = set(test_case.get('expected_specialties', []))
        actual_specs = set([task.specialist.value for task in specialist_tasks])
        precision = len(expected_specs & actual_specs) / len(actual_specs) if actual_specs else 0
        recall = len(expected_specs & actual_specs) / len(expected_specs) if expected_specs else 0
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        tool_score = min(1.0, initial_data.get('tool_calls_made', 0) / 3.0)
        
        # Calculate weighted overall score
        overall_score = (
            0.3 * complexity_score +
            0.3 * f1_score +
            0.2 * tool_score +
            0.1 * (1.0 if approach else 0.0) +
            0.1 * 1.0  # Structure always valid in fallback
        )
        
        return {
            'test_case_id': test_case.get('id', 'unknown'),
            'overall_score': overall_score,
            'dimension_results': {
                'complexity_classification': {
                    'score': complexity_score,
                    'normalized_score': complexity_score,
                    'components': {},
                    'details': {
                        'expected': test_case.get('expected_complexity', 'SIMPLE'),
                        'actual': complexity.value,
                        'correct': complexity_score == 1.0
                    },
                    'evaluation_method': 'deterministic'
                },
                'specialty_selection': {
                    'score': f1_score,
                    'normalized_score': f1_score,
                    'components': {
                        'specialist_precision': precision,
                        'specialist_recall': recall
                    },
                    'details': {
                        'expected_specialties': list(expected_specs),
                        'actual_specialties': list(actual_specs),
                        'precision': precision,
                        'recall': recall,
                        'f1_score': f1_score
                    },
                    'evaluation_method': 'deterministic'
                },
                'analysis_quality': {
                    'score': 0.7,  # Default score
                    'normalized_score': 0.7,
                    'components': {},
                    'details': {
                        'approach_length': len(approach),
                        'approach_text': approach[:500]
                    },
                    'evaluation_method': 'fallback'
                },
                'tool_usage': {
                    'score': tool_score,
                    'normalized_score': tool_score,
                    'components': {},
                    'details': {
                        'tool_calls_made': initial_data.get('tool_calls_made', 0),
                        'successful_tool_calls': initial_data.get('tool_calls_made', 0),
                        'success_rate': 1.0
                    },
                    'evaluation_method': 'deterministic'
                },
                'response_structure': {
                    'score': 1.0,
                    'normalized_score': 1.0,
                    'components': {},
                    'details': {
                        'response_valid': True,
                        'structure_errors': []
                    },
                    'evaluation_method': 'deterministic'
                }
            },
            'execution_time_ms': 0,
            'metadata': {
                'approach_text': approach,
                'test_case_category': test_case.get('category', 'general'),
                'initial_data_gathered': initial_data,
                'specialist_tasks': len(specialist_tasks),
                'failure_analyses': [],
                'fallback_mode': True
            }
        }


class TraceEvaluationService:
    """
    High-level service for trace-based evaluation.
    
    This service provides a clean interface for the QE Agent to evaluate
    test cases using traces.
    """
    
    def __init__(self, anthropic_client=None):
        self.adapter = CLIEvaluatorAdapter(anthropic_client=anthropic_client)
        self.logger = logger
    
    async def evaluate_test_case_from_trace(
        self,
        test_case: Dict[str, Any],
        trace_path: str
    ) -> Dict[str, Any]:
        """
        Evaluate a test case from a trace file.
        
        Args:
            test_case: Test case from QE Agent
            trace_path: Path to the trace file
            
        Returns:
            Evaluation results in dict format
        """
        logger.info(f"=== TRACE EVALUATION SERVICE START ===")
        logger.info(f"Test case: {test_case.get('id', 'unknown')}")
        logger.info(f"Trace path: {trace_path}")
        
        # Load the trace
        logger.info("Loading trace from file...")
        trace = self._load_trace(trace_path)
        logger.info(f"Loaded trace with ID: {trace.trace_id}")
        logger.info(f"Trace has {len(trace.events)} events")
        
        # Run evaluation
        logger.info("Running evaluation using CLI evaluator adapter...")
        result = await self.adapter.evaluate_from_trace(test_case, trace)
        
        logger.info(f"Evaluation result:")
        logger.info(f"  - Overall score: {result.get('overall_score', 0):.2%}")
        logger.info(f"  - Test case ID: {result.get('test_case_id', 'unknown')}")
        
        logger.info(f"=== TRACE EVALUATION SERVICE COMPLETE ===")
        return result
    
    def _load_trace(self, trace_path: str) -> CompleteTrace:
        """
        Load trace from file with error handling.
        
        Args:
            trace_path: Path to the trace JSON file
            
        Returns:
            CompleteTrace object
            
        Raises:
            FileNotFoundError: If trace file doesn't exist
            json.JSONDecodeError: If trace file is not valid JSON
            ValueError: If trace data is missing required fields
        """
        import json
        from datetime import datetime
        
        try:
            with open(trace_path, 'r') as f:
                trace_data = json.load(f)
        except FileNotFoundError:
            logger.error(f"Trace file not found: {trace_path}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in trace file: {e}")
            raise
        
        # Validate required fields
        if not trace_data.get('trace_id'):
            raise ValueError("Trace data missing required field: trace_id")
        
        # Convert events to TraceEvent objects with error handling
        events = []
        for i, event_data in enumerate(trace_data.get('events', [])):
            try:
                # Convert event_type string to enum
                event_type_str = event_data.get('event_type', '')
                try:
                    event_type = TraceEventType(event_type_str)
                except ValueError:
                    logger.warning(f"Unknown event type '{event_type_str}' in event {i}, using ERROR")
                    event_type = TraceEventType.ERROR
                
                event = TraceEvent(
                    event_id=event_data.get('event_id', f'unknown_{i}'),
                    trace_id=event_data.get('trace_id', trace_data.get('trace_id', '')),
                    timestamp=event_data.get('timestamp', datetime.now().isoformat()),
                    event_type=event_type,
                    agent_type=event_data.get('agent_type', ''),
                    stage=event_data.get('stage', ''),
                    data=event_data.get('data', {}),
                    parent_event_id=event_data.get('parent_event_id'),
                    duration_ms=event_data.get('duration_ms'),
                    tokens_used=event_data.get('tokens_used'),
                    metadata=event_data.get('metadata', {})
                )
                events.append(event)
            except Exception as e:
                logger.error(f"Error processing event {i}: {e}")
                # Continue processing other events
        
        # Create CompleteTrace object
        return CompleteTrace(
            trace_id=trace_data.get('trace_id', ''),
            source=trace_data.get('source', 'production'),
            start_time=trace_data.get('start_time', datetime.now().isoformat()),
            end_time=trace_data.get('end_time', datetime.now().isoformat()),
            initial_input=trace_data.get('user_query', ''),
            user_id=trace_data.get('user_id'),
            test_case_id=trace_data.get('test_case_id'),
            session_id=trace_data.get('session_id'),
            events=events,
            summary=trace_data.get('summary', {}),
            metadata=trace_data.get('metadata', {}),
            total_duration_ms=trace_data.get('duration_ms', 0)
        )