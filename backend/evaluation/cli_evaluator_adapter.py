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

from evaluation.agents.cmo.evaluator import CMOEvaluator, CMOEvaluationResult
from evaluation.agents.cmo.test_cases import TestCase as CMOTestCase
from evaluation.trace_parser import TraceDataExtractor, MockSpecialistTask
from services.tracing.models import CompleteTrace
from services.agents.cmo.models import QueryComplexity

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
        self._evaluator = None
    
    @property
    def evaluator(self):
        """Lazy load the evaluator."""
        if self._evaluator is None:
            # Create a minimal CMO agent if not provided (just for metadata)
            if self.cmo_agent is None:
                from services.agents.cmo.cmo_agent import CMOAgent
                from tools.tool_registry import ToolRegistry
                self.cmo_agent = CMOAgent(
                    tools=ToolRegistry(),
                    streaming_client=None  # Not needed for evaluation
                )
            
            # Create the evaluator
            self._evaluator = CMOEvaluator(
                cmo_agent=self.cmo_agent,
                anthropic_client=self.anthropic_client
            )
        return self._evaluator
    
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
        
        This method mimics what happens inside evaluate_single_test_case
        but uses our extracted data instead of calling the agent.
        """
        # We'll need to create a custom version of the evaluator
        # that can accept pre-extracted data. For now, let's create
        # a monkey-patched version
        
        original_analyze = self.evaluator.cmo_agent.analyze_query_with_tools
        original_create_tasks = self.evaluator.cmo_agent.create_specialist_tasks
        
        try:
            # Monkey patch to return our extracted data
            async def mock_analyze(query):
                return complexity, approach, initial_data
            
            async def mock_create_tasks(query, complexity, approach, initial_data):
                return specialist_tasks
            
            self.evaluator.cmo_agent.analyze_query_with_tools = mock_analyze
            self.evaluator.cmo_agent.create_specialist_tasks = mock_create_tasks
            
            # Now run the evaluation
            result = await self.evaluator.evaluate_single_test_case(test_case)
            
            return result
            
        finally:
            # Restore original methods
            self.evaluator.cmo_agent.analyze_query_with_tools = original_analyze
            self.evaluator.cmo_agent.create_specialist_tasks = original_create_tasks


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
        logger.info(f"  - Overall score: {result.weighted_score:.2%}")
        logger.info(f"  - Complexity correct: {result.complexity_correct}")
        logger.info(f"  - Specialists F1 score: {result.specialty_f1_score:.2%}")
        
        # Convert to dict for API response
        logger.info("Converting result to dict format...")
        result_dict = self._convert_result_to_dict(result)
        
        logger.info(f"=== TRACE EVALUATION SERVICE COMPLETE ===")
        return result_dict
    
    def _load_trace(self, trace_path: str) -> CompleteTrace:
        """Load trace from file."""
        import json
        
        with open(trace_path, 'r') as f:
            trace_data = json.load(f)
        
        # Convert to CompleteTrace object
        from services.tracing.models import CompleteTrace
        return CompleteTrace.from_dict(trace_data)
    
    def _convert_result_to_dict(self, result: CMOEvaluationResult) -> Dict[str, Any]:
        """Convert CMOEvaluationResult to dict format."""
        return {
            "test_case_id": result.test_case_id,
            "overall_score": result.weighted_score,
            "dimension_results": {
                "complexity_classification": {
                    "score": result.complexity_classification_score,
                    "normalized_score": result.complexity_classification_score,
                    "details": {
                        "expected": result.expected_complexity,
                        "actual": result.actual_complexity,
                        "correct": result.complexity_correct
                    }
                },
                "specialty_selection": {
                    "score": result.specialty_selection_score,
                    "normalized_score": result.specialty_selection_score,
                    "components": result.specialty_component_breakdown,
                    "details": {
                        "expected_specialties": list(result.expected_specialties),
                        "actual_specialties": list(result.actual_specialties),
                        "precision": result.specialty_precision,
                        "recall": result.specialty_recall,
                        "f1_score": result.specialty_f1_score
                    }
                },
                "analysis_quality": {
                    "score": result.analysis_quality_score,
                    "normalized_score": result.analysis_quality_score,
                    "components": result.analysis_quality_breakdown,
                    "details": {}
                },
                "tool_usage": {
                    "score": result.tool_usage_score,
                    "normalized_score": result.tool_usage_score,
                    "components": result.tool_component_breakdown,
                    "details": {
                        "tool_calls_made": result.tool_calls_made,
                        "successful_tool_calls": result.tool_success_count,
                        "success_rate": result.tool_success_rate
                    }
                },
                "response_structure": {
                    "score": result.response_structure_score,
                    "normalized_score": result.response_structure_score,
                    "components": result.response_component_breakdown,
                    "details": {
                        "response_valid": result.response_valid,
                        "structure_errors": result.structure_errors
                    }
                }
            },
            "execution_time_ms": result.response_time_ms,
            "metadata": {
                "approach_text": result.approach_text,
                "test_case_category": getattr(result, 'test_case_category', 'general')
            }
        }