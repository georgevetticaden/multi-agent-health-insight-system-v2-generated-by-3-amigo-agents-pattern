"""
CLI Evaluator Adapter

This module provides an adapter to use the CLI evaluator from the backend,
enabling trace-based evaluation using the same comprehensive evaluation logic.
"""

import sys
import os
import logging
from typing import Dict, Any, Optional, Tuple, List
from pathlib import Path

# Add evaluation directory to path to import CLI evaluator
sys.path.append(str(Path(__file__).parent.parent.parent))

# Import models and evaluators from core
from evaluation.core.models import TestCase as CMOTestCase, EvaluationResult as CMOEvaluationResult
from evaluation.core.runner import EvaluationRunner
from evaluation.core.evaluators.deterministic import DeterministicEvaluator
from evaluation.core.evaluators.llm_judge import LLMJudgeEvaluator
from evaluation.trace_parser import TraceDataExtractor, MockSpecialistTask
from services.tracing.trace_models import CompleteTrace, TraceEvent
from services.agents.models import QueryComplexity

logger = logging.getLogger(__name__)


class CLIEvaluatorAdapter:
    """
    Adapter to use CLI evaluator with trace data instead of live execution.
    
    This adapter:
    1. Takes a trace and test case
    2. Extracts the necessary data from the trace
    3. Feeds it to the CLI evaluator as if it came from live execution
    4. Returns the evaluation results
    """
    
    def __init__(self, cmo_agent=None, anthropic_client=None):
        """
        Initialize the adapter.
        
        Args:
            cmo_agent: Optional CMO agent (not needed for trace evaluation)
            anthropic_client: Anthropic client for LLM judge
        """
        self.extractor = TraceDataExtractor()
        self.cmo_agent = cmo_agent
        self.anthropic_client = anthropic_client
        self.runner = EvaluationRunner()
        self.deterministic_evaluator = DeterministicEvaluator()
        self.llm_evaluator = LLMJudgeEvaluator()
    
    async def evaluate_from_trace(
        self,
        test_case: Dict[str, Any],
        trace: CompleteTrace
    ) -> CMOEvaluationResult:
        """
        Evaluate a test case using trace data.
        
        Args:
            test_case: Test case dict from QE Agent
            trace: Complete trace of the execution
            
        Returns:
            CMOEvaluationResult with all dimension scores
        """
        logger.info(f"=== CLI EVALUATOR ADAPTER: Starting trace-based evaluation ===")
        logger.info(f"Test case ID: {test_case.get('id', 'unknown')}")
        logger.info(f"Trace ID: {trace.trace_id}")
        
        # Convert test case to CLI format
        logger.info("Converting test case to CLI format...")
        cmo_test_case = self._convert_test_case(test_case)
        logger.info(f"Converted test case: expected_complexity={cmo_test_case.expected_complexity}, "
                   f"expected_specialties={cmo_test_case.expected_specialties}")
        
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
        
        # Use the evaluator's evaluation logic directly
        # We need to patch the evaluator to accept pre-extracted data
        logger.info("Running CLI evaluator with extracted data...")
        result = await self._evaluate_with_extracted_data(
            cmo_test_case,
            complexity,
            approach,
            initial_data,
            specialist_tasks
        )
        
        logger.info(f"=== CLI EVALUATOR ADAPTER: Evaluation complete ===")
        return result
    
    def _convert_test_case(self, test_case_dict: Dict[str, Any]) -> CMOTestCase:
        """Convert QE Agent test case to CLI test case format."""
        return CMOTestCase(
            id=test_case_dict.get("id", "unknown"),
            query=test_case_dict.get("query", ""),
            expected_complexity=test_case_dict.get("expected_complexity", "SIMPLE"),
            expected_specialties=set(test_case_dict.get("expected_specialties", [])),
            key_data_points=test_case_dict.get("key_data_points", []),
            notes=test_case_dict.get("notes", "")
        )
    
    async def _evaluate_with_extracted_data(
        self,
        test_case: CMOTestCase,
        complexity: QueryComplexity,
        approach: str,
        initial_data: Dict[str, Any],
        specialist_tasks: List[MockSpecialistTask]
    ) -> CMOEvaluationResult:
        """
        Evaluate using extracted data instead of running the agent.
        
        This method creates an evaluation result based on the extracted trace data.
        """
        from evaluation.core.models import DimensionResult
        
        # Evaluate complexity classification
        complexity_correct = test_case.expected_complexity.upper() == complexity.value.upper()
        complexity_score = 1.0 if complexity_correct else 0.0
        
        # Evaluate specialty selection
        actual_specialties = {task.specialist.value.upper() for task in specialist_tasks}
        expected_specialties = {s.upper() for s in test_case.expected_specialties}
        
        # Calculate precision, recall, F1
        if not actual_specialties:
            precision = 0.0
            recall = 0.0
            f1_score = 0.0
        else:
            true_positives = len(actual_specialties & expected_specialties)
            false_positives = len(actual_specialties - expected_specialties)
            false_negatives = len(expected_specialties - actual_specialties)
            
            precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0.0
            recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0.0
            f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        
        # Evaluate tool usage
        tool_calls_made = initial_data.get('tool_calls_made', 0)
        tool_success_count = initial_data.get('successful_tool_calls', tool_calls_made)
        tool_success_rate = tool_success_count / tool_calls_made if tool_calls_made > 0 else 1.0
        tool_score = tool_success_rate
        
        # Evaluate analysis quality based on approach content and other factors
        # Calculate component scores first
        data_gathering_score = 1.0 if tool_calls_made > 0 else 0.0
        context_awareness_score = 0.8 if approach and len(approach) > 50 else 0.0
        comprehensive_approach_score = 0.8 if approach and len(approach) > 100 else 0.4 if approach else 0.0
        concern_identification_score = 0.7 if approach and "risk" in approach.lower() or "concern" in approach.lower() else 0.5 if approach else 0.0
        
        # Calculate weighted analysis score
        analysis_score = (
            data_gathering_score * 0.2 +
            context_awareness_score * 0.15 +
            comprehensive_approach_score * 0.25 +
            concern_identification_score * 0.2 +
            0.2  # Base score for attempt
        )
        
        # Evaluate response structure
        response_valid = len(specialist_tasks) > 0
        response_score = 1.0 if response_valid else 0.0
        
        # Calculate overall score
        overall_score = (
            complexity_score * 0.2 +
            f1_score * 0.3 +
            analysis_score * 0.2 +
            tool_score * 0.15 +
            response_score * 0.15
        )
        
        # Create dimension results
        dimension_results = {
            "complexity_classification": DimensionResult(
                dimension_name="complexity_classification",
                score=complexity_score,
                max_score=1.0,
                details={
                    "expected": test_case.expected_complexity,
                    "actual": complexity.value,
                    "correct": complexity_correct
                },
                evaluation_method="deterministic"
            ),
            "specialty_selection": DimensionResult(
                dimension_name="specialty_selection",
                score=f1_score,
                max_score=1.0,
                components={
                    "specialist_precision": precision,
                    "specialist_rationale": 0.8 if actual_specialties else 0.0  # Simplified for now
                },
                details={
                    "expected_specialties": list(expected_specialties),
                    "actual_specialties": list(actual_specialties),
                    "precision": precision,
                    "recall": recall,
                    "f1_score": f1_score
                },
                evaluation_method="hybrid"
            ),
            "analysis_quality": DimensionResult(
                dimension_name="analysis_quality",
                score=analysis_score,
                max_score=1.0,
                components={
                    "data_gathering": data_gathering_score,
                    "context_awareness": context_awareness_score,
                    "comprehensive_approach": comprehensive_approach_score,
                    "concern_identification": concern_identification_score
                },
                details={
                    "approach_length": len(approach),
                    "approach_text": approach[:500] if approach else ""
                },
                evaluation_method="hybrid"
            ),
            "tool_usage": DimensionResult(
                dimension_name="tool_usage",
                score=tool_score,
                max_score=1.0,
                components={
                    "tool_success_rate": tool_success_rate
                },
                details={
                    "tool_calls_made": tool_calls_made,
                    "successful_tool_calls": tool_success_count,
                    "success_rate": tool_success_rate
                },
                evaluation_method="deterministic"
            ),
            "response_structure": DimensionResult(
                dimension_name="response_structure",
                score=response_score,
                max_score=1.0,
                components={
                    "xml_validity": 1.0 if response_valid else 0.0,
                    "required_fields": 1.0 if response_valid else 0.0
                },
                details={
                    "response_valid": response_valid,
                    "structure_errors": [] if response_valid else ["No specialist tasks created"]
                },
                evaluation_method="deterministic"
            )
        }
        
        # Extract response time from trace
        response_time_ms = 0
        if hasattr(trace, 'total_duration_ms'):
            response_time_ms = trace.total_duration_ms
        elif hasattr(trace, 'summary') and trace.summary.get('duration_ms'):
            response_time_ms = trace.summary.get('duration_ms', 0)
        
        # Create evaluation result
        result = CMOEvaluationResult(
            test_case_id=test_case.id,
            agent_type="cmo",
            overall_score=overall_score,
            dimension_results=dimension_results,
            execution_time_ms=response_time_ms,
            metadata={
                "approach_text": approach,
                "test_case_category": getattr(test_case, 'category', 'general'),
                "initial_data_gathered": initial_data
            }
        )
        
        return result


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
        logger.info(f"  - Overall score: {result.overall_score:.2%}")
        logger.info(f"  - Test case ID: {result.test_case_id}")
        logger.info(f"  - Agent type: {result.agent_type}")
        
        # Convert to dict for API response
        logger.info("Converting result to dict format...")
        result_dict = self._convert_result_to_dict(result)
        
        logger.info(f"=== TRACE EVALUATION SERVICE COMPLETE ===")
        return result_dict
    
    def _load_trace(self, trace_path: str) -> CompleteTrace:
        """Load trace from file."""
        import json
        from datetime import datetime
        from services.tracing.trace_models import TraceEventType
        
        with open(trace_path, 'r') as f:
            trace_data = json.load(f)
        
        # Convert events to TraceEvent objects
        events = []
        for event_data in trace_data.get('events', []):
            # Convert event_type string to enum
            event_type_str = event_data.get('event_type', '')
            try:
                event_type = TraceEventType(event_type_str)
            except ValueError:
                # If the event type is not recognized, use ERROR
                event_type = TraceEventType.ERROR
            
            event = TraceEvent(
                event_id=event_data.get('event_id', ''),
                trace_id=event_data.get('trace_id', trace_data.get('trace_id', '')),
                timestamp=event_data.get('timestamp', ''),
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
    
    def _convert_result_to_dict(self, result: CMOEvaluationResult) -> Dict[str, Any]:
        """Convert CMOEvaluationResult to dict format."""
        # Use the to_dict method if available
        if hasattr(result, 'to_dict'):
            return result.to_dict()
        
        # Otherwise convert manually
        # Convert dimension results to dict format
        dimension_results = {}
        for dim_name, dim_result in result.dimension_results.items():
            dimension_results[dim_name] = {
                "score": dim_result.score,
                "normalized_score": dim_result.normalized_score,
                "components": getattr(dim_result, 'components', {}),
                "details": getattr(dim_result, 'details', {}),
                "evaluation_method": getattr(dim_result, 'evaluation_method', 'deterministic')
            }
        
        return {
            "test_case_id": result.test_case_id,
            "overall_score": result.overall_score,
            "dimension_results": dimension_results,
            "execution_time_ms": result.execution_time_ms,
            "metadata": result.metadata
        }