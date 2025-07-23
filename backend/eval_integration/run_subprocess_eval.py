#!/usr/bin/env python3
"""
Subprocess evaluation runner with proper path configuration.

This script sets up all necessary paths before importing any modules,
ensuring that both the evaluation framework and backend services can be imported.
"""

import sys
import json
import asyncio
import logging
from pathlib import Path

# Configure paths BEFORE any imports
script_path = Path(__file__).resolve()
backend_dir = script_path.parent.parent  # backend directory
project_root = backend_dir.parent  # project root
evaluation_dir = project_root / "evaluation"  # evaluation framework

# Add all necessary paths
sys.path.insert(0, str(backend_dir))  # For 'services' imports
sys.path.insert(0, str(project_root))  # For 'evaluation' imports

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

logger.info(f"Python paths configured:")
logger.info(f"  Backend: {backend_dir}")
logger.info(f"  Project root: {project_root}")
logger.info(f"  Evaluation: {evaluation_dir}")
logger.info(f"  sys.path: {sys.path[:3]}")

# Now we can import everything
try:
    # Backend imports
    from services.agents.models import QueryComplexity, MedicalSpecialty
    from services.agents.cmo.cmo_agent import SpecialistTask, CMOAgent
    
    # Evaluation framework imports
    from evaluation.agents.cmo.evaluator import CMOEvaluator, CMOEvaluationResult
    from evaluation.cli.test_case_converter import CMOTestCase
    
    # Other imports
    from anthropic import Anthropic
    
    logger.info("All imports successful!")
except ImportError as e:
    logger.error(f"Import failed: {e}")
    logger.error(f"Current working directory: {Path.cwd()}")
    logger.error(f"Python path: {sys.path}")
    raise


class MockCMOAgentForEval:
    """Mock CMO Agent that replays trace data."""
    
    def __init__(self, trace_data):
        self.trace_data = trace_data
        # Convert string values back to enums
        self.trace_data['complexity'] = QueryComplexity(trace_data['complexity'])
        for task in self.trace_data['specialist_tasks']:
            task['specialist'] = MedicalSpecialty(task['specialist'])
        logger.info(f"MockCMOAgent initialized with trace data")
        logger.info(f"  Complexity: {self.trace_data['complexity'].value}")
        logger.info(f"  Approach length: {len(self.trace_data.get('approach', ''))}")
        logger.info(f"  Specialist tasks: {len(self.trace_data['specialist_tasks'])}")
    
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
        specialists = [t.specialist.value for t in tasks]
        logger.info(f"  Specialists: {specialists}")
        return tasks
    
    @staticmethod
    def get_evaluation_metadata():
        """Get evaluation metadata from real CMOAgent."""
        return CMOAgent.get_evaluation_metadata()


async def run_evaluation(input_data: dict):
    """Run the evaluation using provided data."""
    logger.info("=== SUBPROCESS EVALUATION START ===")
    
    test_case_data = input_data['test_case']
    trace_data = input_data['trace_data']
    api_key = input_data.get('anthropic_api_key')
    
    # Convert test case
    logger.info(f"Converting test case: {test_case_data.get('id', 'unknown')}")
    test_case = CMOTestCase(
        id=test_case_data.get('id', 'unknown'),
        query=test_case_data.get('query', ''),
        description=test_case_data.get('notes', 'QE-generated test case'),  # Use notes as description
        category=test_case_data.get('category', 'general'),  # Add category field
        expected_complexity=test_case_data.get('expected_complexity', 'SIMPLE'),
        expected_specialties=set(test_case_data.get('expected_specialties', [])),
        key_data_points=test_case_data.get('key_data_points', []),
        notes=test_case_data.get('notes', '')
    )
    logger.info(f"Test case created: expected_complexity={test_case.expected_complexity}, "
                f"expected_specialties={test_case.expected_specialties}")
    
    # Update trace data to use total tool calls across all stages
    if 'total_tool_calls_all_stages' in trace_data.get('initial_data', {}):
        total_calls = trace_data['initial_data']['total_tool_calls_all_stages']
        total_successful = trace_data['initial_data'].get('total_successful_tool_calls', 0)
        logger.info(f"Updating trace data to use total tool calls: {total_calls} total, {total_successful} successful")
        trace_data['initial_data']['tool_calls_made'] = total_calls
        trace_data['initial_data']['successful_tool_calls'] = total_successful
    
    # Create mock agent
    logger.info("Creating MockCMOAgent...")
    mock_agent = MockCMOAgentForEval(trace_data)
    
    # Create evaluator
    logger.info("Creating CMOEvaluator...")
    anthropic_client = Anthropic(api_key=api_key) if api_key else None
    if anthropic_client:
        logger.info("✅ Anthropic client created - LLM Judge evaluation ENABLED")
        logger.info(f"   API key length: {len(api_key) if api_key else 0}")
        logger.info(f"   API key prefix: {api_key[:10]}..." if api_key and len(api_key) > 10 else "N/A")
    else:
        logger.warning("⚠️  No Anthropic API key provided - LLM Judge evaluation DISABLED")
    
    # Log evaluation configuration
    logger.info("CMOEvaluator configuration:")
    logger.info(f"  - Mock agent: {type(mock_agent).__name__}")
    logger.info(f"  - Has Anthropic client: {anthropic_client is not None}")
    
    evaluator = CMOEvaluator(
        cmo_agent=mock_agent,
        anthropic_client=anthropic_client
    )
    
    # Check if evaluator has LLM Judge
    if hasattr(evaluator, 'llm_judge'):
        logger.info(f"  - LLM Judge configured: {evaluator.llm_judge is not None}")
    else:
        logger.warning("  - No llm_judge attribute found on evaluator")
    
    # Run evaluation
    logger.info("Running evaluation with CMOEvaluator...")
    result = await evaluator.evaluate_single_test_case(test_case)
    
    # Use execution time from trace if evaluator didn't calculate it
    if result.total_response_time_ms == 0 and 'execution_time_ms' in trace_data.get('initial_data', {}):
        result.total_response_time_ms = trace_data['initial_data']['execution_time_ms']
    
    logger.info(f"Evaluation complete!")
    logger.info(f"  Success: {result.success}")
    logger.info(f"  Weighted score: {result.weighted_score:.3f}")
    logger.info(f"  Complexity score: {result.complexity_classification_score:.3f} (target: 0.90)")
    logger.info(f"  Specialist score: {result.specialty_selection_score:.3f} (target: 0.85)")
    logger.info(f"  Analysis quality: {result.analysis_quality_score:.3f} (target: 0.80)")
    logger.info(f"  Tool usage: {result.tool_usage_score:.3f} (target: 0.90)")
    logger.info(f"  Response structure: {result.response_structure_score:.3f} (target: 0.95)")
    logger.info(f"  Execution time: {result.total_response_time_ms:.0f}ms")
    
    # Check which dimensions failed
    failed_dimensions = []
    if result.complexity_classification_score < 0.90:
        failed_dimensions.append(f"complexity_classification ({result.complexity_classification_score:.3f} < 0.90)")
    if result.specialty_selection_score < 0.85:
        failed_dimensions.append(f"specialty_selection ({result.specialty_selection_score:.3f} < 0.85)")
    if result.analysis_quality_score < 0.80:
        failed_dimensions.append(f"analysis_quality ({result.analysis_quality_score:.3f} < 0.80)")
    if result.tool_usage_score < 0.90:
        failed_dimensions.append(f"tool_usage ({result.tool_usage_score:.3f} < 0.90)")
    if result.response_structure_score < 0.95:
        failed_dimensions.append(f"response_structure ({result.response_structure_score:.3f} < 0.95)")
    
    if failed_dimensions:
        logger.info(f"  ❌ Failed dimensions: {len(failed_dimensions)}")
        for dim in failed_dimensions:
            logger.info(f"    - {dim}")
    
    # Log failure analyses
    if hasattr(result, 'failure_analyses') and result.failure_analyses:
        logger.info(f"  ✅ Failure analyses: {len(result.failure_analyses)} dimensions failed")
        for analysis in result.failure_analyses:
            dimension = analysis.get('dimension', 'Unknown')
            priority = analysis.get('priority', 'Unknown')
            root_cause = analysis.get('root_cause', 'N/A')
            recommendations = analysis.get('recommendations', [])
            
            logger.info(f"    - {dimension}: {priority} priority")
            
            if root_cause and root_cause.strip():
                logger.info(f"      Root cause: {root_cause[:100]}...")
            else:
                logger.warning(f"      ⚠️  Root cause is empty for {dimension}")
                logger.warning(f"      ⚠️  Full analysis object: {analysis}")
                
            if recommendations and len(recommendations) > 0:
                logger.info(f"      Recommendations: {len(recommendations)} items")
            else:
                logger.warning(f"      ⚠️  No recommendations for {dimension}")
    else:
        logger.warning("  ⚠️  No failure analyses found in result")
        # Debug: Check if result object has the attribute at all
        logger.warning(f"     Result type: {type(result).__name__}")
        logger.warning(f"     Has failure_analyses attr: {hasattr(result, 'failure_analyses')}")
        if hasattr(result, 'failure_analyses'):
            logger.warning(f"     failure_analyses value: {result.failure_analyses}")
            logger.warning(f"     failure_analyses type: {type(result.failure_analyses)}")
    
    # Log LLM Judge usage in components
    logger.info("=== COMPONENT EVALUATION METHODS ===")
    
    # Helper function to get actual component evaluation method from metadata
    def get_component_method(dimension_name, comp_name):
        """Get the actual evaluation method from component metadata."""
        try:
            # Import here to avoid circular imports
            from backend.services.agents.cmo.cmo_agent import CMOAgent
            metadata = CMOAgent.get_evaluation_metadata()
            
            # Find the dimension and component
            for criteria in metadata.evaluation_criteria:
                if criteria.dimension.name == dimension_name:
                    if hasattr(criteria.dimension, 'components'):
                        for comp in criteria.dimension.components:
                            if comp.name == comp_name:
                                return comp.evaluation_method.value.lower()
            
            # Fallback: try to find in quality_components
            if hasattr(metadata, 'quality_components'):
                for dim, components in metadata.quality_components.items():
                    if dim.name == dimension_name:
                        for comp in components:
                            if comp.name == comp_name:
                                return comp.evaluation_method.value.lower()
            
            return 'unknown'
        except Exception as e:
            logger.debug(f"Could not determine evaluation method for {dimension_name}.{comp_name}: {e}")
            return 'unknown'
    
    # Check analysis quality components
    if hasattr(result, 'analysis_quality_breakdown') and result.analysis_quality_breakdown:
        logger.info("Analysis Quality Components:")
        for comp_name, comp_data in result.analysis_quality_breakdown.items():
            if isinstance(comp_data, dict):
                method = comp_data.get('evaluation_method', 'unknown')
                score = comp_data.get('score', 0.0)
            else:
                # comp_data is just a float score - get actual method from metadata
                method = get_component_method('analysis_quality', comp_name)
                score = comp_data
            logger.info(f"  - {comp_name}: {score:.3f} ({method})")
    
    # Check specialty selection components
    if hasattr(result, 'specialty_component_breakdown') and result.specialty_component_breakdown:
        logger.info("Specialty Selection Components:")
        for comp_name, comp_data in result.specialty_component_breakdown.items():
            if isinstance(comp_data, dict):
                method = comp_data.get('evaluation_method', 'unknown')
                score = comp_data.get('score', comp_data)
            else:
                # comp_data is just a float score - get actual method from metadata
                method = get_component_method('specialty_selection', comp_name)
                score = comp_data
            logger.info(f"  - {comp_name}: {score:.3f} ({method})")
    
    # Check tool usage components
    if hasattr(result, 'tool_component_breakdown') and result.tool_component_breakdown:
        logger.info("Tool Usage Components:")
        for comp_name, comp_data in result.tool_component_breakdown.items():
            if isinstance(comp_data, dict):
                method = comp_data.get('evaluation_method', 'unknown')
                score = comp_data.get('score', 0.0)
            else:
                # comp_data is just a float score - get actual method from metadata
                method = get_component_method('tool_usage', comp_name)
                score = comp_data
            logger.info(f"  - {comp_name}: {score:.3f} ({method})")
    
    # Check response structure components
    if hasattr(result, 'response_component_breakdown') and result.response_component_breakdown:
        logger.info("Response Structure Components:")
        for comp_name, comp_data in result.response_component_breakdown.items():
            if isinstance(comp_data, dict):
                method = comp_data.get('evaluation_method', 'unknown')
                score = comp_data.get('score', 0.0)
            else:
                # comp_data is just a float score - get actual method from metadata
                method = get_component_method('response_structure', comp_name)
                score = comp_data
            logger.info(f"  - {comp_name}: {score:.3f} ({method})")
    
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
            'specialist_tasks': len(result.specialist_tasks) if result.specialist_tasks else 0,
            'failure_analyses': result.failure_analyses if hasattr(result, 'failure_analyses') and result.failure_analyses else [],
            'llm_judge_enabled': anthropic_client is not None,
            'llm_judge_run': anthropic_client is not None,
            'component_evaluation_methods': extract_component_methods(result)
        }
    }
    
    logger.info("=== SUBPROCESS EVALUATION COMPLETE ===")
    return result_dict


def extract_component_methods(result):
    """Extract which evaluation methods were used for each component."""
    methods = {}
    
    # Check each component breakdown
    for attr_name in ['specialty_component_breakdown', 'analysis_quality_breakdown', 
                      'tool_component_breakdown', 'response_component_breakdown']:
        if hasattr(result, attr_name):
            breakdown = getattr(result, attr_name)
            if breakdown and isinstance(breakdown, dict):
                for comp_name, comp_data in breakdown.items():
                    if isinstance(comp_data, dict) and 'evaluation_method' in comp_data:
                        methods[comp_name] = comp_data['evaluation_method']
    
    return methods


def convert_dimension_results(result):
    """Convert CMOEvaluationResult dimensions to dict format."""
    dimensions = {}
    
    # Complexity Classification
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
    
    # Specialty Selection
    # Check if any component used LLM Judge
    has_specialty_llm = any(
        comp_data.get('evaluation_method') == 'llm_judge' if isinstance(comp_data, dict) else False
        for comp_data in result.specialty_component_breakdown.values()
    )
    
    dimensions['specialty_selection'] = {
        'score': result.specialty_selection_score,
        'normalized_score': result.specialty_selection_score,
        'components': result.specialty_component_breakdown,
        'details': {
            'expected_specialties': list(result.expected_specialties),
            'actual_specialties': list(result.actual_specialties),
            'precision': result.specialty_component_breakdown.get('specialist_precision', 0.0),
            'recall': result.specialty_component_breakdown.get('specialist_recall', 0.0),
            'f1_score': result.specialty_selection_score,
            'has_llm_components': has_specialty_llm
        },
        'evaluation_method': 'hybrid' if has_specialty_llm else 'deterministic'
    }
    
    # Analysis Quality
    # Check if any component used LLM Judge
    has_llm_judge = any(
        comp_data.get('evaluation_method') == 'llm_judge' if isinstance(comp_data, dict) else False
        for comp_data in result.analysis_quality_breakdown.values()
    )
    
    dimensions['analysis_quality'] = {
        'score': result.analysis_quality_score,
        'normalized_score': result.analysis_quality_score,
        'components': result.analysis_quality_breakdown,
        'details': {
            'approach_length': len(result.approach_text) if result.approach_text else 0,
            'approach_text': result.approach_text[:500] if result.approach_text else "",
            'llm_judge_feedback': '',  # Not stored at result level
            'has_llm_components': has_llm_judge
        },
        'evaluation_method': 'hybrid' if has_llm_judge else 'deterministic'
    }
    
    # Tool Usage
    # Get total tool calls including all stages
    total_tool_calls = result.tool_calls_made
    successful_tool_calls = result.tool_calls_made  # Default to all successful
    
    if hasattr(result, 'initial_data_gathered') and isinstance(result.initial_data_gathered, dict):
        total_tool_calls = result.initial_data_gathered.get('total_tool_calls_all_stages', result.tool_calls_made)
        successful_tool_calls = result.initial_data_gathered.get('total_successful_tool_calls', result.tool_calls_made)
    
    # Calculate success rate
    success_rate = successful_tool_calls / total_tool_calls if total_tool_calls > 0 else 1.0
    
    dimensions['tool_usage'] = {
        'score': result.tool_usage_score,
        'normalized_score': result.tool_usage_score,
        'components': result.tool_component_breakdown,
        'details': {
            'tool_calls_made': total_tool_calls,
            'successful_tool_calls': successful_tool_calls,
            'success_rate': success_rate,
            'tool_calls_by_stage': result.initial_data_gathered.get('tool_calls_by_stage', {}) if hasattr(result, 'initial_data_gathered') else {}
        },
        'evaluation_method': 'deterministic'
    }
    
    # Response Structure
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
        print("Usage: run_subprocess_eval.py <input_file>")
        sys.exit(1)
    
    # Load input data
    with open(sys.argv[1], 'r') as f:
        input_data = json.load(f)
    
    # Run evaluation
    result = asyncio.run(run_evaluation(input_data))
    
    # Output result as JSON
    print(json.dumps(result))