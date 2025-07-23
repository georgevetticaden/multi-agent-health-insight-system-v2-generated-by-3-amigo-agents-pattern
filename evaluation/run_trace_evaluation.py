#!/usr/bin/env python3
"""
Trace-based evaluation script for subprocess execution.

This script is run in a subprocess to evaluate test cases using trace data.
It imports and uses the real CMOEvaluator from the evaluation framework.
"""

import asyncio
import json
import logging
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add paths for imports
project_root = Path(__file__).parent.parent
backend_dir = project_root / "backend"
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(backend_dir))

# Import evaluation framework
from evaluation.agents.cmo.evaluator import CMOEvaluator, CMOEvaluationResult
from evaluation.agents.cmo.test_cases import TestCase as CMOTestCase
from evaluation.agents.cmo.dimensions import DimensionResult
from services.agents.models import QueryComplexity, MedicalSpecialty
from services.agents.cmo.cmo_agent import SpecialistTask
from anthropic import Anthropic


class MockCMOAgentForEval:
    """Mock CMO Agent that replays trace data."""
    
    def __init__(self, trace_data):
        self.trace_data = trace_data
        # Convert string values back to enums
        self.trace_data['complexity'] = QueryComplexity(trace_data['complexity'])
        for task in self.trace_data['specialist_tasks']:
            task['specialist'] = MedicalSpecialty(task['specialist'])
        logger.info(f"MockCMOAgent initialized with trace data")
    
    async def analyze_query_with_tools(self, query):
        """Return pre-extracted analysis data."""
        complexity = self.trace_data['complexity']
        approach = self.trace_data['approach']
        initial_data = self.trace_data['initial_data']
        
        logger.info(f"Returning analysis: complexity={complexity.value}, approach_len={len(approach)}")
        return complexity, approach, initial_data
    
    async def create_specialist_tasks(self, query, complexity, approach, initial_data):
        """Return pre-extracted specialist tasks."""
        tasks = []
        for task_data in self.trace_data['specialist_tasks']:
            task = SpecialistTask(
                specialist=task_data['specialist'],
                objective=task_data['objective'],
                context=task_data['context'],
                expected_output=task_data['expected_output'],
                priority=task_data['priority'],
                max_tool_calls=task_data['max_tool_calls']
            )
            tasks.append(task)
        
        logger.info(f"Returning {len(tasks)} specialist tasks")
        return tasks
    
    @staticmethod
    def get_evaluation_metadata():
        """Get evaluation metadata from real CMOAgent."""
        from services.agents.cmo.cmo_agent import CMOAgent
        return CMOAgent.get_evaluation_metadata()


async def run_evaluation(input_file: str):
    """Run the evaluation using input from file."""
    logger.info(f"Loading input from {input_file}")
    
    with open(input_file, 'r') as f:
        data = json.load(f)
    
    test_case_data = data['test_case']
    trace_data = data['trace_data']
    api_key = data.get('anthropic_api_key')
    
    # Convert test case
    test_case = CMOTestCase(
        id=test_case_data.get('id', 'unknown'),
        query=test_case_data.get('query', ''),
        expected_complexity=test_case_data.get('expected_complexity', 'SIMPLE'),
        expected_specialties=set(test_case_data.get('expected_specialties', [])),
        key_data_points=test_case_data.get('key_data_points', []),
        notes=test_case_data.get('notes', '')
    )
    
    # Create mock agent
    mock_agent = MockCMOAgentForEval(trace_data)
    
    # Create evaluator
    anthropic_client = Anthropic(api_key=api_key) if api_key else None
    evaluator = CMOEvaluator(
        cmo_agent=mock_agent,
        anthropic_client=anthropic_client
    )
    
    # Run evaluation
    logger.info("Running evaluation...")
    result = await evaluator.evaluate_single_test_case(test_case)
    
    # Convert result to dict
    result_dict = {
        'test_case_id': result.test_case_id,
        'overall_score': result.weighted_score,
        'dimension_results': convert_dimension_results(result),
        'execution_time_ms': result.total_response_time_ms,
        'metadata': {
            'approach_text': result.approach_text,
            'test_case_category': result.key_data_points[0] if result.key_data_points else 'general',
            'initial_data_gathered': result.initial_data_gathered,
            'specialist_tasks': result.specialist_tasks,
            'failure_analyses': result.failure_analyses
        }
    }
    
    # Output as JSON
    print(json.dumps(result_dict))


def convert_dimension_results(result):
    """Convert CMOEvaluationResult dimensions to dict format."""
    dimensions = {}
    
    dimensions['complexity_classification'] = {
        'score': result.complexity_classification_score,
        'normalized_score': result.complexity_classification_score,
        'components': {},
        'details': {
            'expected': result.expected_complexity,
            'actual': result.actual_complexity,
            'correct': result.complexity_correct
        },
        'evaluation_method': 'deterministic'
    }
    
    dimensions['specialty_selection'] = {
        'score': result.specialty_selection_score,
        'normalized_score': result.specialty_selection_score,
        'components': result.specialty_component_breakdown,
        'details': {
            'expected_specialties': list(result.expected_specialties),
            'actual_specialties': list(result.actual_specialties),
            'precision': result.specialty_component_breakdown.get('specialist_precision', 0.0),
            'recall': result.specialty_component_breakdown.get('specialist_recall', 0.0),
            'f1_score': result.specialty_selection_score
        },
        'evaluation_method': 'hybrid'
    }
    
    dimensions['analysis_quality'] = {
        'score': result.analysis_quality_score,
        'normalized_score': result.analysis_quality_score,
        'components': result.analysis_quality_breakdown,
        'details': {
            'approach_length': len(result.approach_text) if result.approach_text else 0,
            'approach_text': result.approach_text[:500] if result.approach_text else ""
        },
        'evaluation_method': 'hybrid'
    }
    
    dimensions['tool_usage'] = {
        'score': result.tool_usage_score,
        'normalized_score': result.tool_usage_score,
        'components': result.tool_component_breakdown,
        'details': {
            'tool_calls_made': result.tool_calls_made,
            'successful_tool_calls': result.tool_component_breakdown.get('tool_success_count', result.tool_calls_made),
            'success_rate': result.tool_component_breakdown.get('tool_success_rate', 1.0)
        },
        'evaluation_method': 'deterministic'
    }
    
    dimensions['response_structure'] = {
        'score': result.response_structure_score,
        'normalized_score': result.response_structure_score,
        'components': result.response_component_breakdown,
        'details': {
            'response_valid': result.response_valid,
            'structure_errors': result.structure_errors
        },
        'evaluation_method': 'deterministic'
    }
    
    return dimensions


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: run_trace_evaluation.py <input_file>")
        sys.exit(1)
    
    asyncio.run(run_evaluation(sys.argv[1]))