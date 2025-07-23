"""
CMO Agent Evaluator

This module contains the CMO-specific evaluation logic, extending the base evaluator
framework with CMO-specific dimensions and test logic.

The CMOEvaluator provides metadata-driven evaluation of the Chief Medical Officer agent
across multiple dimensions including complexity classification, specialist selection,
analysis quality, tool usage, and response structure.

Key Features:
- Metadata-driven evaluation using agent-specific configuration
- Two-stage evaluation: query analysis and task creation
- Hybrid evaluation methods (deterministic + LLM judge)
- Component-based scoring with configurable weights
- Comprehensive failure analysis with actionable recommendations
- Real-time evaluation with progress tracking

Evaluation Dimensions:
- complexity_classification: Accuracy in classifying query complexity
- specialty_selection: Precision in selecting appropriate medical specialists
- analysis_quality: Comprehensiveness and quality of medical analysis
- tool_usage: Effectiveness of health data tool usage
- response_structure: Compliance with expected XML response format

Evaluation Flow:
1. Execute CMO agent on test case (query analysis + task creation)
2. Collect raw evaluation data (facts, not scores)
3. Apply metadata-driven evaluation across all dimensions
4. Calculate component scores using appropriate methods
5. Aggregate weighted scores into final dimension scores
6. Analyze failures and provide recommendations

Usage:
    evaluator = CMOEvaluator(cmo_agent, anthropic_client)
    result = await evaluator.evaluate_single_test_case(test_case)
    
See Also:
    - BaseEvaluator: Parent class providing generic evaluation framework
    - CMOAgent: The agent being evaluated
    - LLMTestJudge: LLM-based evaluation and failure analysis
"""

import re
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set, Any

from services.agents.cmo.cmo_agent import CMOAgent, QueryComplexity, SpecialistTask
from evaluation.framework.evaluators import BaseEvaluator, EvaluationResult
from evaluation.framework.llm_judge import SpecialistSimilarityScorer, LLMTestJudge, FailureAnalysis
from evaluation.core.dimensions import EvaluationMethod
from evaluation.core import EvaluationCriteria, QualityComponent
from anthropic import Anthropic

logger = logging.getLogger(__name__)


class EvaluationConstants:
    """
    Constants for evaluation that aren't part of agent metadata.
    
    These constants define evaluation behavior that is specific to the
    test framework rather than the agent being evaluated.
    """
    # Overall test suite success threshold
    OVERALL_SUCCESS_THRESHOLD = 0.75
    
    # Task quality evaluation weights (not dimension-specific)
    TASK_QUALITY_WEIGHTS = {
        "completeness": 0.4,
        "specificity": 0.4,
        "diversity": 0.2
    }


@dataclass
class CMOEvaluationResult(EvaluationResult):
    """
    CMO-specific evaluation result with metadata-driven dimension scores.
    
    This class extends the base EvaluationResult to include CMO-specific
    evaluation data and metadata-driven dimension scores.
    
    Attributes:
        Raw Data Fields:
            - expected_complexity: Expected complexity from test case
            - actual_complexity: Actual complexity determined by agent
            - complexity_correct: Whether complexity classification was correct
            - expected_specialties: Expected specialists from test case
            - actual_specialties: Actual specialists selected by agent
            - response_valid: Whether response had valid XML structure
            - structure_errors: List of XML structure errors
            - tool_calls_made: Number of tool calls attempted
            
        Metadata-Driven Dimension Scores:
            - complexity_classification_score: Score for complexity classification
            - specialty_selection_score: Score for specialist selection
            - analysis_quality_score: Score for analysis quality
            - tool_usage_score: Score for tool usage effectiveness
            - response_structure_score: Score for response structure
            
        Component Breakdowns:
            - specialty_component_breakdown: Component scores for specialty selection
            - analysis_quality_breakdown: Component scores for analysis quality
            - tool_component_breakdown: Component scores for tool usage
            - response_component_breakdown: Component scores for response structure
            
        Context and Metadata:
            - approach_text: Agent's approach description
            - initial_data_gathered: Raw data from initial analysis
            - specialist_tasks: Serialized specialist tasks created
            - failure_analyses: Detailed failure analyses for failed dimensions
    """
    
    # Raw data for evaluation (facts, not scores)
    expected_complexity: str = ""
    actual_complexity: Optional[str] = None
    complexity_correct: bool = False
    expected_specialties: Set[str] = field(default_factory=set)
    actual_specialties: Set[str] = field(default_factory=set)
    response_valid: bool = False
    structure_errors: List[str] = field(default_factory=list)
    tool_calls_made: int = 0
    
    # Metadata-driven dimension scores (the ONLY scores we trust)
    complexity_classification_score: float = 0.0
    specialty_selection_score: float = 0.0
    analysis_quality_score: float = 0.0
    tool_usage_score: float = 0.0
    response_structure_score: float = 0.0
    
    # Component breakdowns for each dimension
    specialty_component_breakdown: Dict[str, float] = field(default_factory=dict)
    analysis_quality_breakdown: Dict[str, float] = field(default_factory=dict)
    tool_component_breakdown: Dict[str, float] = field(default_factory=dict)
    response_component_breakdown: Dict[str, float] = field(default_factory=dict)
    
    # Context and metadata
    approach_text: Optional[str] = None
    initial_data_gathered: Optional[Dict[str, Any]] = None
    analysis_time_ms: float = 0.0
    specialist_tasks: Optional[List[Dict[str, Any]]] = None
    task_creation_success: bool = False
    task_creation_time_ms: float = 0.0
    task_creation_error: Optional[str] = None
    task_count: int = 0
    approach_mentioned_specialties: Optional[Set[str]] = None
    key_data_points: Optional[List[str]] = None
    
    # Failure analyses from LLM Judge
    failure_analyses: Optional[List[Dict[str, Any]]] = None
    
    # Weighted scoring
    weighted_score: float = 0.0
    dimension_success_rate: float = 0.0  # Percentage of dimensions that passed
    evaluation_success: bool = False  # Did test meet quality targets (vs execution success)


class CMOEvaluator(BaseEvaluator):
    """
    Evaluates CMO agent performance using metadata-driven hybrid evaluation.
    
    This evaluator extends BaseEvaluator to provide CMO-specific evaluation logic
    across multiple dimensions. It uses a hybrid approach combining deterministic
    metrics with LLM judge assessments for comprehensive evaluation.
    
    The evaluation process consists of two main stages:
    1. Agent Execution: Run the CMO agent on test cases
    2. Evaluation: Apply metadata-driven scoring across all dimensions
    
    Attributes:
        cmo_agent: The CMO agent instance being evaluated
        llm_judge: LLM judge instance for semantic evaluation
        agent_metadata: Metadata containing evaluation criteria and components
    
    Example:
        >>> evaluator = CMOEvaluator(cmo_agent, anthropic_client)
        >>> test_cases = CMOTestCases.get_complexity_test_suite()
        >>> results = await evaluator.evaluate_test_suite(test_cases)
    """
    
    def __init__(self, cmo_agent: CMOAgent, anthropic_client: Optional[Anthropic] = None):
        """
        Initialize the CMO evaluator with agent and optional LLM judge.
        
        Args:
            cmo_agent: The CMO agent instance to evaluate
            anthropic_client: Optional Anthropic client for LLM judge evaluation
            
        Raises:
            ValueError: If agent_metadata cannot be loaded
        """
        super().__init__(anthropic_client)
        self.cmo_agent = cmo_agent
        
        # Initialize LLM Judge for both scoring and failure analysis
        self.llm_judge = None
        if anthropic_client:
            self.llm_judge = LLMTestJudge(
                anthropic_client=anthropic_client,
                model="claude-opus-4-20250514"  # Use Opus 4 for evaluation, claude-3-7-sonnet-20250219 or claude-opus-4-20250514
            )
        
        # Get metadata from the agent class and set it for BaseEvaluator
        self.agent_metadata = CMOAgent.get_evaluation_metadata()
        if not self.agent_metadata:
            raise ValueError("Failed to load agent evaluation metadata")
    
    async def evaluate_single_test_case(self, test_case) -> CMOEvaluationResult:
        """
        Evaluate CMO agent performance on a single test case.
        
        This method executes the complete evaluation pipeline:
        1. Stage 1: Query analysis (complexity assessment + initial data gathering)
        2. Stage 2: Task creation (specialist selection + task generation)
        3. Data collection: Extract raw facts for evaluation
        4. Evaluation: Apply metadata-driven scoring across all dimensions
        5. Failure analysis: Identify issues and provide recommendations
        
        Args:
            test_case: CMO test case containing query, expected complexity, 
                      expected specialties, and key data points
                      
        Returns:
            CMOEvaluationResult containing:
            - Raw evaluation data (complexity, specialties, tool usage, etc.)
            - Metadata-driven dimension scores
            - Component-level breakdowns
            - Failure analyses with recommendations
            - Performance metrics (response time, tokens)
            
        Raises:
            Exception: If agent execution fails (returns result with error)
        """
        # Import test case type
        from evaluation.agents.cmo.test_cases import TestCase
        
        logger.info(f"Evaluating test case: {test_case.id} - {test_case.query[:50]}...")
        
        start_time = datetime.now()
        
        try:
            # Stage 1: Analyze query
            logger.info(f"🔍 EVALUATION STAGE 1: Analyzing query for test case {test_case.id}")
            logger.debug("Stage 1: Calling analyze_query_with_tools...")
            analysis_start = datetime.now()
            complexity, approach, initial_data = await self.cmo_agent.analyze_query_with_tools(
                test_case.query
            )
            analysis_time_ms = (datetime.now() - analysis_start).total_seconds() * 1000
            logger.info(f"✅ Stage 1 complete - Complexity: {complexity.value}, Approach length: {len(approach)} chars, Time: {analysis_time_ms:.1f}ms")
            logger.debug(f"Initial data keys: {list(initial_data.keys()) if initial_data else 'None'}")
            logger.debug(f"Tool calls made during analysis: {len(initial_data.get('tool_calls', [])) if initial_data else 0}")
            
            # Reconstruct the full analysis with XML tags for validation
            analysis = f"<complexity>{complexity.value.upper()}</complexity>\n<approach>{approach}</approach>"
            
            # Extract actual values from Stage 1
            actual_complexity = complexity.value if complexity else None
            
            # Optional: Extract specialists mentioned in approach text (for comparison)
            approach_mentioned_specialties = self._extract_specialties_from_analysis(analysis)
            
            # Stage 2: Create specialist tasks
            logger.info(f"🏥 EVALUATION STAGE 2: Creating specialist tasks for test case {test_case.id}")
            logger.debug("Stage 2: Calling create_specialist_tasks...")
            task_start = datetime.now()
            specialist_tasks = []
            task_creation_success = True
            task_creation_error = None
            
            try:
                specialist_tasks = await self.cmo_agent.create_specialist_tasks(
                    query=test_case.query,
                    complexity=complexity,
                    approach=approach,
                    initial_data=initial_data
                )
                logger.info(f"✅ Stage 2 complete - Created {len(specialist_tasks)} tasks")
                logger.debug(f"Specialists selected: {[task.specialist.value for task in specialist_tasks]}")
            except Exception as e:
                logger.error(f"❌ Task creation failed: {str(e)}")
                task_creation_success = False
                task_creation_error = str(e)
            
            task_creation_time_ms = (datetime.now() - task_start).total_seconds() * 1000
            
            # Extract actual specialists from tasks (this is what matters!)
            actual_specialties = {task.specialist.value for task in specialist_tasks}
            
            # Serialize specialist tasks for storage
            serialized_tasks = [
                {
                    "specialist": task.specialist.value,
                    "objective": task.objective,
                    "context": task.context[:200] + "..." if len(task.context) > 200 else task.context,
                    "expected_output": task.expected_output,
                    "priority": task.priority,
                    "max_tool_calls": task.max_tool_calls
                }
                for task in specialist_tasks
            ]
            
            # Collect raw data for evaluation (no scoring, just facts)
            logger.info(f"📊 EVALUATION STAGE 3: Collecting raw data for test case {test_case.id}")
            complexity_correct = actual_complexity == test_case.expected_complexity.lower()
            logger.debug(f"Complexity evaluation: Expected={test_case.expected_complexity.lower()}, Actual={actual_complexity}, Correct={complexity_correct}")
            
            # Collect specialty data (true positives, false positives, false negatives)
            specialty_data = self._collect_specialty_data(
                test_case.expected_specialties,
                actual_specialties
            )
            
            # Validate response structure
            response_valid, structure_errors = self._validate_response_structure_cmo(analysis)
            
            # Collect tool usage data
            tool_data = self._collect_tool_usage_data(initial_data)
            
            # Prepare result data for metadata-driven evaluation
            result_data = {
                # Raw data for complexity classification
                'complexity_correct': complexity_correct,
                'actual_complexity': actual_complexity,
                'expected_complexity': test_case.expected_complexity,
                
                # Raw data for specialty selection
                'actual_specialties': actual_specialties,
                'expected_specialties': test_case.expected_specialties,
                'true_positives': specialty_data['true_positives'],
                'false_positives': specialty_data['false_positives'],
                'false_negatives': specialty_data['false_negatives'],
                
                # Raw data for analysis quality
                'approach_text': approach,
                'initial_data_gathered': initial_data,
                'query': test_case.query,
                'key_data_points': test_case.key_data_points,
                
                # Raw data for tool usage
                'tool_calls_made': tool_data['calls_made'],
                'successful_tool_calls': tool_data['successful_calls'],
                'tool_call_details': tool_data['call_details'],
                
                # Raw data for response structure
                'response_valid': response_valid,
                'structure_errors': structure_errors,
                'has_all_required_fields': len(structure_errors) == 0,
                
                # Task creation data
                'specialist_tasks': specialist_tasks,
                'task_count': len(specialist_tasks),
                'task_creation_success': task_creation_success
            }
            
            # Evaluate dimensions dynamically
            logger.info(f"📊 EVALUATION STAGE 4: Evaluating dimensions for test case {test_case.id}")
            dynamic_dimension_scores = {}
            dynamic_component_breakdowns = {}
            
            for criteria in self.agent_metadata.evaluation_criteria:
                logger.debug(f"Evaluating dimension: {criteria.dimension.name} (target: {criteria.target_score:.2f})")
                dimension_score, component_breakdown = await self._evaluate_dimension_dynamic(
                    criteria.dimension, result_data, test_case
                )
                dynamic_dimension_scores[criteria.dimension.name] = dimension_score
                dynamic_component_breakdowns[criteria.dimension.name] = component_breakdown
                
                status = "✅ PASS" if dimension_score >= criteria.target_score else "❌ FAIL"
                logger.info(f"  {status} {criteria.dimension.name}: {dimension_score:.3f} (target: {criteria.target_score:.2f})")
                
                if component_breakdown:
                    logger.debug(f"    Component breakdown: {component_breakdown}")
            
            # Calculate total time and tokens
            total_response_time_ms = (datetime.now() - start_time).total_seconds() * 1000
            tokens_used = len(test_case.query.split()) + len(analysis.split()) + len(str(serialized_tasks).split())
            
            # Analyze failures for dimensions that didn't meet thresholds
            logger.info(f"🔍 EVALUATION STAGE 5: Analyzing failures for test case {test_case.id}")
            failure_analyses = []
            failed_dimensions = []
            
            if self.llm_judge:
                # Check each dimension against its target
                for criteria in self.agent_metadata.evaluation_criteria:
                    dimension_name = criteria.dimension.name
                    dimension_score = dynamic_dimension_scores.get(dimension_name, 0.0)
                    
                    if dimension_score < criteria.target_score:
                        failed_dimensions.append(dimension_name)
                        # Dimension failed - run failure analysis
                        logger.info(f"🔍 Running LLM Judge failure analysis for {dimension_name}: {dimension_score:.2f} < {criteria.target_score:.2f}")
                        
                        try:
                            analysis_start = datetime.now()
                            analysis = await self._analyze_dimension_failure(
                                dimension_name, 
                                dimension_score,
                                criteria.target_score,
                                result_data, 
                                test_case,
                                dynamic_component_breakdowns
                            )
                            analysis_time = (datetime.now() - analysis_start).total_seconds() * 1000
                            
                            if analysis:
                                logger.info(f"✅ Failure analysis complete for {dimension_name} (took {analysis_time:.1f}ms)")
                                logger.debug(f"  Root cause: {analysis.root_cause[:100]}...")
                                logger.debug(f"  Recommendations: {len(analysis.recommendations)} items")
                                failure_analyses.append({
                                    'dimension': analysis.dimension,
                                    'root_cause': analysis.root_cause,
                                    'specific_issues': analysis.specific_issues,
                                    'recommendations': analysis.recommendations,
                                    'priority': analysis.priority,
                                    'prompt_file': analysis.prompt_file,
                                    'expected_impact': analysis.expected_impact
                                })
                            else:
                                logger.warning(f"⚠️ No failure analysis returned for {dimension_name}")
                        except Exception as e:
                            logger.error(f"❌ Failed to analyze {dimension_name} failure: {e}")
                            
                if failed_dimensions:
                    logger.info(f"📊 Failed dimensions: {', '.join(failed_dimensions)}")
                else:
                    logger.info(f"✅ All dimensions passed thresholds")
            else:
                logger.warning(f"⚠️ LLM Judge not available - skipping failure analysis")
            
            # Calculate weighted score and evaluation success
            weighted_score = self._calculate_weighted_score(dynamic_dimension_scores)
            dimension_success_rate = self._calculate_dimension_success_rate(dynamic_dimension_scores)
            
            # Evaluation success: weighted score meets overall threshold (default 0.75)
            evaluation_success = weighted_score >= EvaluationConstants.OVERALL_SUCCESS_THRESHOLD
            
            # Final stage - prepare results
            logger.info(f"📊 EVALUATION STAGE 6: Finalizing results for test case {test_case.id}")
            logger.info(f"  Total time: {total_response_time_ms:.1f}ms")
            logger.info(f"  Tokens used: {tokens_used}")
            logger.info(f"  Failure analyses: {len(failure_analyses)}")
            logger.info(f"  Weighted score: {weighted_score:.3f}")
            logger.info(f"  Dimension success rate: {dimension_success_rate:.1%}")
            
            # Execution success (test ran without errors)
            execution_success = complexity_correct and response_valid and task_creation_success
            logger.info(f"🏁 EVALUATION COMPLETE for test case {test_case.id}:")
            logger.info(f"  Execution: {'SUCCESS' if execution_success else 'FAILURE'}")
            logger.info(f"  Evaluation: {'PASS' if evaluation_success else 'FAIL'} (score: {weighted_score:.3f})")
            
            return CMOEvaluationResult(
                # Base fields
                test_case_id=test_case.id,
                query=test_case.query,
                success=execution_success,
                total_response_time_ms=total_response_time_ms,
                tokens_used=tokens_used,
                
                # Raw data for evaluation
                expected_complexity=test_case.expected_complexity,
                actual_complexity=actual_complexity,
                complexity_correct=complexity_correct,
                expected_specialties=test_case.expected_specialties,
                actual_specialties=actual_specialties,
                response_valid=response_valid,
                structure_errors=structure_errors,
                tool_calls_made=result_data.get('tool_calls_made', 0),
                
                # Metadata-driven dimension scores
                complexity_classification_score=dynamic_dimension_scores.get("complexity_classification", 0.0),
                specialty_selection_score=dynamic_dimension_scores.get("specialty_selection", 0.0),
                analysis_quality_score=dynamic_dimension_scores.get("analysis_quality", 0.0),
                tool_usage_score=dynamic_dimension_scores.get("tool_usage", 0.0),
                response_structure_score=dynamic_dimension_scores.get("response_structure", 0.0),
                
                # Component breakdowns
                specialty_component_breakdown=dynamic_component_breakdowns.get("specialty_selection", {}),
                analysis_quality_breakdown=dynamic_component_breakdowns.get("analysis_quality", {}),
                tool_component_breakdown=dynamic_component_breakdowns.get("tool_usage", {}),
                response_component_breakdown=dynamic_component_breakdowns.get("response_structure", {}),
                
                # Context and metadata
                approach_text=approach,
                initial_data_gathered=initial_data,
                analysis_time_ms=analysis_time_ms,
                specialist_tasks=serialized_tasks,
                task_creation_success=task_creation_success,
                task_creation_time_ms=task_creation_time_ms,
                task_creation_error=task_creation_error,
                task_count=len(specialist_tasks),
                approach_mentioned_specialties=approach_mentioned_specialties,
                key_data_points=test_case.key_data_points,
                
                # Failure analyses
                failure_analyses=failure_analyses if failure_analyses else None,
                
                # Weighted scoring
                weighted_score=weighted_score,
                dimension_success_rate=dimension_success_rate,
                evaluation_success=evaluation_success
            )
            
        except Exception as e:
            logger.error(f"❌ EVALUATION FAILED for test case {test_case.id}: {str(e)}")
            total_response_time_ms = (datetime.now() - start_time).total_seconds() * 1000
            logger.debug(f"  Error occurred after {total_response_time_ms:.1f}ms")
            
            return CMOEvaluationResult(
                # Base fields
                test_case_id=test_case.id,
                query=test_case.query,
                success=False,
                total_response_time_ms=total_response_time_ms,
                tokens_used=0,
                error_message=str(e),
                
                # Raw data (defaults for error case)
                expected_complexity=test_case.expected_complexity,
                actual_complexity=None,
                complexity_correct=False,
                expected_specialties=test_case.expected_specialties,
                actual_specialties=set(),
                response_valid=False,
                structure_errors=[],
                tool_calls_made=0,
                
                # All dimension scores are 0 on error
                complexity_classification_score=0.0,
                specialty_selection_score=0.0,
                analysis_quality_score=0.0,
                tool_usage_score=0.0,
                response_structure_score=0.0,
                
                # Empty component breakdowns on error
                specialty_component_breakdown={},
                analysis_quality_breakdown={},
                tool_component_breakdown={},
                response_component_breakdown={}
            )
    
    def _collect_specialty_data(self, expected: Set[str], actual: Set[str]) -> Dict[str, Any]:
        """
        Collect raw specialty selection data for evaluation.
        
        This method extracts the fundamental facts about specialist selection
        without performing any scoring calculations.
        
        Args:
            expected: Set of expected specialist names from test case
            actual: Set of actual specialist names from agent output
            
        Returns:
            Dictionary containing:
            - true_positives: Count of correctly selected specialists
            - false_positives: Count of incorrectly selected specialists
            - false_negatives: Count of missed specialists
            - total_expected: Total number of expected specialists
            - total_actual: Total number of actual specialists
        """
        true_positives = len(expected.intersection(actual))
        false_positives = len(actual - expected)
        false_negatives = len(expected - actual)
        
        return {
            'true_positives': true_positives,
            'false_positives': false_positives,
            'false_negatives': false_negatives,
            'total_expected': len(expected),
            'total_actual': len(actual)
        }
    
    def _collect_tool_usage_data(self, initial_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Collect raw tool usage data for evaluation.
        
        This method extracts tool usage facts from the agent's initial data
        gathering phase without performing scoring calculations.
        
        Args:
            initial_data: Dictionary containing tool execution results from agent
            
        Returns:
            Dictionary containing:
            - calls_made: Number of tool calls attempted
            - successful_calls: Number of successful tool calls
            - data_found: Whether any data was retrieved
            - result_count: Number of data records found
            - call_details: Additional context about tool usage
        """
        calls_made = initial_data.get('tool_calls_made', 0)
        data_available = initial_data.get('data_available', False)
        result_count = initial_data.get('result_count', 0)
        
        # Determine successful calls (simplified logic)
        successful_calls = calls_made if data_available else 0
        
        return {
            'calls_made': calls_made,
            'successful_calls': successful_calls,
            'data_found': data_available,
            'result_count': result_count,
            'call_details': {
                'query': initial_data.get('query', ''),
                'summary': initial_data.get('summary', '')
            }
        }
    
    def _extract_specialties_from_analysis(self, analysis: str) -> Set[str]:
        """
        Extract medical specialties mentioned in analysis text.
        
        This method uses keyword matching to identify medical specialties
        mentioned in the agent's analysis text, useful for comparison
        with actual task assignments.
        
        Args:
            analysis: Analysis text from the agent
            
        Returns:
            Set of specialty names found in the text
        """
        # Common medical specialties that might be mentioned
        specialties = {
            'cardiology', 'endocrinology', 'neurology', 'oncology', 'psychiatry',
            'dermatology', 'orthopedics', 'urology', 'gastroenterology', 'pulmonology',
            'nephrology', 'hematology', 'rheumatology', 'infectious_disease',
            'emergency_medicine', 'family_medicine', 'internal_medicine',
            'data_analysis', 'laboratory_medicine', 'radiology', 'pathology',
            'pharmacy', 'nutrition', 'physical_therapy', 'preventive_medicine'
        }
        
        analysis_lower = analysis.lower()
        found_specialties = set()
        
        for specialty in specialties:
            # Check for exact match or variations
            specialty_variations = [
                specialty,
                specialty.replace('_', ' '),
                specialty.replace('_', '-')
            ]
            
            for variation in specialty_variations:
                if variation in analysis_lower:
                    found_specialties.add(specialty)
                    break
        
        return found_specialties

    def _validate_response_structure_cmo(self, analysis: str) -> Tuple[bool, List[str]]:
        """
        Validate CMO-specific response structure.
        
        Args:
            analysis: Analysis text to validate
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        expected_tags = ["complexity", "approach"]
        return self._validate_response_structure(analysis, expected_tags)

    # LLM Judge evaluation methods - these provide CMO-specific semantic evaluation
    
    async def _llm_judge_context_awareness(self, analysis: str, query: str) -> float:
        """
        Evaluate temporal context awareness using LLM Judge.
        
        This method assesses whether the agent's analysis demonstrates
        appropriate consideration of temporal context and patient history.
        
        Args:
            analysis: Agent's analysis text
            query: Original patient query
            
        Returns:
            Score from 0.0 to 1.0 indicating context awareness quality
        """
        logger.debug(f"          🤖 LLM Judge evaluating context awareness...")
        if not self.llm_judge:
            logger.debug(f"          LLM Judge not available, returning default score")
            return self._get_default_score_for_method(EvaluationMethod.LLM_JUDGE)
        
        try:
            result = await self.llm_judge.score_context_awareness(analysis=analysis, query=query)
            logger.debug(f"          Context awareness score: {result.score:.3f}")
            logger.debug(f"          Reasoning: {result.reasoning[:100]}...")
            return result.score
        except Exception as e:
            logger.warning(f"LLM Judge context awareness evaluation failed: {e}")
            return self._get_default_score_for_method(EvaluationMethod.LLM_JUDGE)

    async def _llm_judge_specialist_rationale(self, analysis: str, query: str = "", specialists: List[str] = None) -> float:
        """
        Evaluate specialist selection rationale using LLM Judge.
        
        This method assesses the quality of reasoning provided for
        specialist selection decisions.
        
        Args:
            analysis: Agent's analysis text containing specialist rationale
            query: Original patient query for context
            specialists: List of actual specialists selected (optional)
            
        Returns:
            Score from 0.0 to 1.0 indicating rationale quality
        """
        logger.info(f"          🤖 LLM Judge evaluating specialist rationale...")
        logger.info(f"          Analysis length: {len(analysis)} characters")
        logger.info(f"          Query length: {len(query)} characters" if query else "          No query provided")
        
        if not self.llm_judge:
            logger.warning(f"          ❌ LLM Judge not available, returning default score (0.5)")
            return self._get_default_score_for_method(EvaluationMethod.LLM_JUDGE)
        
        try:
            # Use provided specialists or try to extract from analysis
            if specialists is None:
                specialists = list(self._extract_specialties_from_analysis(analysis))
                logger.info(f"          Specialists extracted from analysis: {specialists}")
            else:
                logger.info(f"          Specialists provided: {specialists}")
            
            logger.info(f"          Query for context: {query[:100]}..." if query else "          No query provided")
            
            logger.info(f"          🚀 Calling LLM Judge score_specialist_rationale...")
            result = await self.llm_judge.score_specialist_rationale(
                approach=analysis, 
                specialists=specialists, 
                query=query
            )
            logger.info(f"          ✅ LLM Judge returned specialist rationale score: {result.score:.3f}")
            logger.info(f"          📝 LLM Judge reasoning: {result.reasoning[:200]}...")
            
            if result.score == 0.0:
                logger.warning(f"          ⚠️  LLM Judge returned exactly 0.0 - this may indicate an issue")
                logger.warning(f"          📄 Full reasoning: {result.reasoning}")
            
            return result.score
        except Exception as e:
            logger.error(f"          ❌ LLM Judge specialist rationale evaluation failed: {e}")
            logger.error(f"          📊 Returning default LLM Judge score (0.5)")
            return self._get_default_score_for_method(EvaluationMethod.LLM_JUDGE)

    async def _llm_judge_comprehensive_approach(self, analysis: str, key_concepts: List[str], query: str) -> float:
        """
        Evaluate comprehensiveness of the medical approach using LLM Judge.
        
        This method assesses whether the agent's analysis covers all
        relevant medical concepts and areas for the given query.
        
        Args:
            analysis: Agent's analysis text
            key_concepts: List of key medical concepts expected to be covered
            query: Original patient query
            
        Returns:
            Score from 0.0 to 1.0 indicating approach comprehensiveness
        """
        logger.debug(f"          🤖 LLM Judge evaluating comprehensive approach...")
        logger.debug(f"          Key concepts to cover: {key_concepts}")
        if not self.llm_judge:
            logger.debug(f"          LLM Judge not available, returning default score")
            return self._get_default_score_for_method(EvaluationMethod.LLM_JUDGE)
        
        try:
            result = await self.llm_judge.score_comprehensive_approach(
                analysis=analysis, 
                query=query, 
                key_areas=key_concepts
            )
            logger.debug(f"          Comprehensive approach score: {result.score:.3f}")
            logger.debug(f"          Reasoning: {result.reasoning[:100]}...")
            return result.score
        except Exception as e:
            logger.warning(f"LLM Judge comprehensive approach evaluation failed: {e}")
            return self._get_default_score_for_method(EvaluationMethod.LLM_JUDGE)

    async def _llm_judge_concern_identification(self, analysis: str, query: str) -> float:
        """
        Evaluate health concern identification using LLM Judge.
        
        This method assesses the agent's ability to identify and articulate
        relevant health concerns and risks from the patient query.
        
        Args:
            analysis: Agent's analysis text
            query: Original patient query
            
        Returns:
            Score from 0.0 to 1.0 indicating concern identification quality
        """
        logger.debug(f"          🤖 LLM Judge evaluating concern identification...")
        if not self.llm_judge:
            logger.debug(f"          LLM Judge not available, returning default score")
            return self._get_default_score_for_method(EvaluationMethod.LLM_JUDGE)
        
        try:
            result = await self.llm_judge.score_concern_identification(analysis=analysis, query=query)
            logger.debug(f"          Concern identification score: {result.score:.3f}")
            logger.debug(f"          Reasoning: {result.reasoning[:100]}...")
            return result.score
        except Exception as e:
            logger.warning(f"LLM Judge concern identification evaluation failed: {e}")
            return self._get_default_score_for_method(EvaluationMethod.LLM_JUDGE)
    
    def _calculate_weighted_score(self, dimension_scores: Dict[str, float]) -> float:
        """
        Calculate weighted score for a test case based on dimension scores and weights.
        
        Args:
            dimension_scores: Dictionary mapping dimension names to scores
            
        Returns:
            Weighted average score (0.0 to 1.0)
        """
        total_weight = 0.0
        weighted_sum = 0.0
        
        for criteria in self.agent_metadata.evaluation_criteria:
            dimension_name = criteria.dimension.name
            dimension_score = dimension_scores.get(dimension_name, 0.0)
            weight = criteria.weight
            
            weighted_sum += dimension_score * weight
            total_weight += weight
            
        return weighted_sum / total_weight if total_weight > 0 else 0.0
    
    def _calculate_dimension_success_rate(self, dimension_scores: Dict[str, float]) -> float:
        """
        Calculate percentage of dimensions that met their target scores.
        
        Args:
            dimension_scores: Dictionary mapping dimension names to scores
            
        Returns:
            Success rate (0.0 to 1.0)
        """
        total_dimensions = 0
        passed_dimensions = 0
        
        for criteria in self.agent_metadata.evaluation_criteria:
            dimension_name = criteria.dimension.name
            dimension_score = dimension_scores.get(dimension_name, 0.0)
            target_score = criteria.target_score
            
            total_dimensions += 1
            if dimension_score >= target_score:
                passed_dimensions += 1
        
        return passed_dimensions / total_dimensions if total_dimensions > 0 else 0.0
    
    def _create_summary(self, aggregated: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create evaluation summary using weighted scoring approach.
        
        This implementation uses weighted scores across dimensions to provide
        a more nuanced evaluation than simple pass/fail.
        
        Args:
            aggregated: Aggregated results from test suite
            
        Returns:
            Dictionary containing:
            - overall_success: Whether average weighted score meets threshold
            - weighted_score: Average weighted score across all tests
            - success_rate: Percentage of tests meeting evaluation threshold
            - total_tests: Total number of tests
            - failed_tests: List of test IDs that didn't meet threshold
            - performance_metrics: Average response time and token usage
        """
        if not aggregated:
            return {"overall_success": False, "weighted_score": 0.0}
        
        # Get the aggregated results
        results = aggregated.get("results", [])
        total_tests = aggregated.get("total_tests", 0)
        
        if total_tests == 0:
            return {"overall_success": False, "weighted_score": 0.0}
        
        # Calculate metrics based on weighted scores
        total_weighted_score = 0.0
        tests_passing_threshold = 0
        failed_tests = []
        
        for result in results:
            # Get weighted score from result
            weighted_score = result.get('weighted_score', 0.0)
            total_weighted_score += weighted_score
            
            # Check if test meets evaluation threshold
            if result.get('evaluation_success', False):
                tests_passing_threshold += 1
            else:
                failed_tests.append(result.get('test_case_id'))
        
        # Calculate average weighted score
        average_weighted_score = total_weighted_score / total_tests
        
        # Overall success if average weighted score meets threshold
        overall_success = average_weighted_score >= EvaluationConstants.OVERALL_SUCCESS_THRESHOLD
        
        # Success rate based on evaluation success (not execution success)
        success_rate = tests_passing_threshold / total_tests if total_tests > 0 else 0.0
        
        return {
            "overall_success": overall_success,
            "weighted_score": average_weighted_score,
            "success_rate": success_rate,
            "total_tests": total_tests,
            "failed_tests": failed_tests,
            "performance_metrics": {
                "avg_response_time_ms": aggregated.get("average_response_time_ms", 0),
                "avg_tokens_per_test": aggregated.get("average_tokens_per_test", 0)
            }
        }
    
    
    async def _evaluate_dimension_direct(self, dimension, result_data, test_case) -> Tuple[float, Dict[str, float]]:
        """
        Evaluate dimension directly without components (CMO-specific implementation).
        
        This method provides direct evaluation for dimensions that don't have
        component-based scoring.
        
        Args:
            dimension: Dimension object from metadata
            result_data: Dictionary containing raw evaluation data
            test_case: Test case object
            
        Returns:
            Tuple of (score, empty_component_breakdown)
        """
        if dimension.name == "complexity_classification":
            score = 1.0 if result_data.get('complexity_correct', False) else 0.0
            return score, {}
        
        # Add other direct evaluations as needed
        return 0.0, {}
    
    async def _evaluate_deterministic_component(self, component, dimension, result_data, test_case) -> float:
        """
        Evaluate a deterministic component using raw data and rule-based logic.
        
        This method implements CMO-specific deterministic evaluation logic
        for each component type, calculating scores from raw evaluation data.
        
        Args:
            component: QualityComponent object from metadata
            dimension: Dimension object from metadata
            result_data: Dictionary containing raw evaluation data
            test_case: Test case object
            
        Returns:
            Component score from 0.0 to 1.0
        """
        if dimension.name == "specialty_selection":
            if component.name == "specialist_precision":
                # Calculate precision from raw data
                actual_specialties = result_data.get('actual_specialties', set())
                expected_specialties = result_data.get('expected_specialties', set())
                
                if not actual_specialties:
                    return 0.0
                if not expected_specialties:
                    return 1.0  # No expected specialties, any selection is valid
                
                # Use semantic similarity for precision calculation
                try:
                    similarity_result = SpecialistSimilarityScorer.calculate_similarity(
                        predicted=list(actual_specialties),
                        actual=list(expected_specialties)
                    )
                    if isinstance(similarity_result, tuple):
                        return similarity_result[0]  # Semantic score
                except Exception as e:
                    logger.warning(f"Similarity scoring failed: {e}, using exact match")
                    # Fallback to exact match
                    true_positives = len(expected_specialties.intersection(actual_specialties))
                    return true_positives / len(actual_specialties) if actual_specialties else 0.0
        
        elif dimension.name == "tool_usage":
            if component.name == "tool_success_rate":
                # Calculate success rate from raw data
                calls_made = result_data.get('tool_calls_made', 0)
                successful_calls = result_data.get('successful_tool_calls', 0)
                
                # Use updated totals from initial_data_gathered if available
                initial_data = result_data.get('initial_data_gathered', {})
                if isinstance(initial_data, dict):
                    calls_made = initial_data.get('total_tool_calls_all_stages', calls_made)
                    successful_calls = initial_data.get('total_successful_tool_calls', successful_calls)
                
                return successful_calls / calls_made if calls_made > 0 else 0.0
                
            elif component.name == "tool_relevance":
                # Check if tool calls resulted in relevant data
                calls_made = result_data.get('tool_calls_made', 0)
                # Check in multiple places for data availability
                tool_details = result_data.get('tool_call_details', {})
                data_found = (
                    tool_details.get('data_found', False) or
                    result_data.get('initial_data_gathered', {}).get('data_available', False)
                )
                score = 1.0 if calls_made > 0 and data_found else 0.0
                logger.debug(f"          Tool relevance: {score:.3f} (calls: {calls_made}, data_found: {data_found})")
                return score
        
        elif dimension.name == "response_structure":
            if component.name == "xml_validity":
                valid = result_data.get('response_valid', False)
                logger.debug(f"          XML validity: {1.0 if valid else 0.0} (valid: {valid})")
                return 1.0 if valid else 0.0
            elif component.name == "required_fields":
                # Check if all required fields are present
                has_fields = result_data.get('has_all_required_fields', False)
                logger.debug(f"          Required fields: {1.0 if has_fields else 0.0} (has_all: {has_fields})")
                return 1.0 if has_fields else 0.0
        
        elif dimension.name == "analysis_quality":
            if component.name == "data_gathering":
                # Check if initial data was gathered
                initial_data = result_data.get('initial_data_gathered', {})
                data_available = initial_data and initial_data.get('data_available', False)
                logger.debug(f"          Data gathering: {1.0 if data_available else 0.0} (available: {data_available})")
                return 1.0 if data_available else 0.0
        
        logger.debug(f"          No deterministic evaluation for {component.name} in {dimension.name}, returning 0.0")
        return 0.0
    
    async def _evaluate_llm_component(self, component, dimension, result_data, test_case) -> float:
        """
        Evaluate an LLM judge component using semantic analysis.
        
        This method implements CMO-specific LLM evaluation logic for
        components that require semantic understanding and judgment.
        
        Args:
            component: QualityComponent object from metadata
            dimension: Dimension object from metadata
            result_data: Dictionary containing raw evaluation data
            test_case: Test case object
            
        Returns:
            Component score from 0.0 to 1.0
        """
        if not self.llm_judge:
            logger.warning(f"LLM Judge not available for {component.name}")
            return self._get_default_score_for_method(EvaluationMethod.LLM_JUDGE)
        
        if dimension.name == "specialty_selection":
            if component.name == "specialist_rationale":
                # Evaluate the rationale for specialist selection
                logger.info(f"      🎯 Routing to LLM Judge for specialty_selection.specialist_rationale")
                approach_text = result_data.get('approach_text', '')
                query = result_data.get('query', '')
                actual_specialties = result_data.get('actual_specialties', set())
                # Convert set to list of specialist names
                specialists = list(actual_specialties) if actual_specialties else []
                logger.info(f"         📄 Approach text available: {bool(approach_text)} ({len(approach_text)} chars)")
                logger.info(f"         🔍 Query available: {bool(query)} ({len(query) if query else 0} chars)")
                logger.info(f"         👥 Actual specialists: {specialists}")
                return await self._llm_judge_specialist_rationale(approach_text, query, specialists)
        
        elif dimension.name == "analysis_quality":
            if component.name == "context_awareness":
                # Evaluate temporal context awareness
                approach_text = result_data.get('approach_text', '')
                query = result_data.get('query', '')
                return await self._llm_judge_context_awareness(approach_text, query)
                
            elif component.name == "specialist_rationale":
                # Evaluate specialist task assignment rationale
                approach_text = result_data.get('approach_text', '')
                query = result_data.get('query', '')
                actual_specialties = result_data.get('actual_specialties', set())
                # Convert set to list of specialist names
                specialists = list(actual_specialties) if actual_specialties else []
                return await self._llm_judge_specialist_rationale(approach_text, query, specialists)
                
            elif component.name == "comprehensive_approach":
                # Evaluate comprehensiveness of approach
                approach_text = result_data.get('approach_text', '')
                key_data_points = result_data.get('key_data_points', [])
                query = result_data.get('query', '')
                return await self._llm_judge_comprehensive_approach(approach_text, key_data_points, query)
                
            elif component.name == "concern_identification":
                # Evaluate health concern identification
                approach_text = result_data.get('approach_text', '')
                query = result_data.get('query', '')
                return await self._llm_judge_concern_identification(approach_text, query)
        
        return 0.0
    
    async def _analyze_dimension_failure(
        self, 
        dimension_name: str, 
        actual_score: float,
        target_score: float,
        result_data: Dict[str, Any], 
        test_case: Any,
        component_breakdowns: Dict[str, Dict[str, float]] = None
    ) -> Optional[FailureAnalysis]:
        """
        Analyze why a dimension failed to meet its target score.
        
        This method uses LLM Judge to perform deep failure analysis,
        identifying root causes and providing actionable recommendations
        for improvement.
        
        Args:
            dimension_name: Name of the failed dimension
            actual_score: Actual score achieved
            target_score: Target score that was missed
            result_data: Raw evaluation data
            test_case: Test case that failed
            component_breakdowns: Optional component score breakdowns
            
        Returns:
            FailureAnalysis object containing:
            - Root cause analysis
            - Specific issues identified
            - Actionable recommendations
            - Priority level for fixes
            
        Returns:
            None if LLM Judge is not available
        """
        if not self.llm_judge:
            return None
        
        try:
            # Map dimension to appropriate analysis method
            if dimension_name == "complexity_classification":
                return await self.llm_judge.analyze_complexity_mismatch(
                    agent_type="cmo",
                    test_case={"query": test_case.query},
                    actual_complexity=result_data.get('actual_complexity', 'Unknown'),
                    expected_complexity=test_case.expected_complexity,
                    approach_text=result_data.get('approach_text', '')
                )
            
            elif dimension_name == "specialty_selection":
                # Extract actual and expected specialists
                actual_specialties = result_data.get('actual_specialties', set())
                expected_specialties = test_case.expected_specialties
                missing_critical = list(set(expected_specialties) - set(actual_specialties))
                
                return await self.llm_judge.analyze_specialist_mismatch(
                    agent_type="cmo",
                    test_case={"query": test_case.query},
                    actual_specialists=list(actual_specialties),
                    expected_specialists=list(expected_specialties),
                    approach_text=result_data.get('approach_text', ''),
                    f1_score=actual_score,  # Use the actual dimension score
                    missing_critical=missing_critical
                )
            
            elif dimension_name == "analysis_quality":
                return await self.llm_judge.analyze_quality_issues(
                    agent_type="cmo",
                    query=test_case.query,
                    approach_text=result_data.get('approach_text', ''),
                    quality_breakdown=component_breakdowns.get('analysis_quality', {}) if component_breakdowns else {},
                    key_data_points=test_case.key_data_points or [],
                    quality_score=actual_score,
                    target_score=target_score
                )
            
            elif dimension_name == "tool_usage":
                # Use updated tool call counts if available
                initial_data = result_data.get('initial_data_gathered', {})
                
                # Get tool counts from updated values if available
                if isinstance(initial_data, dict) and 'total_tool_calls_all_stages' in initial_data:
                    tool_calls_made = initial_data.get('total_tool_calls_all_stages', result_data.get('tool_calls_made', 0))
                    successful_calls = initial_data.get('total_successful_tool_calls', result_data.get('successful_tool_calls', 0))
                else:
                    tool_calls_made = result_data.get('tool_calls_made', 0)
                    successful_calls = result_data.get('successful_tool_calls', 0)
                
                tool_success_rate = successful_calls / tool_calls_made if tool_calls_made > 0 else 0.0
                
                logger.info(f"Tool usage LLM Judge parameters:")
                logger.info(f"  - tool_calls_made: {tool_calls_made}")
                logger.info(f"  - successful_calls: {successful_calls}")
                logger.info(f"  - tool_success_rate: {tool_success_rate}")
                
                return await self.llm_judge.analyze_tool_usage_issues(
                    agent_type="cmo",
                    query=test_case.query,
                    tool_calls_made=tool_calls_made,
                    tool_success_rate=tool_success_rate,
                    tool_relevance_score=result_data.get('tool_relevance_score', 0.0),
                    initial_data_gathered=initial_data
                )
            
            elif dimension_name == "response_structure":
                return await self.llm_judge.analyze_response_structure_issues(
                    agent_type="cmo",
                    query=test_case.query,
                    structure_errors=result_data.get('structure_errors', []),
                    approach_text=result_data.get('approach_text', '')
                )
            
            else:
                logger.warning(f"No failure analysis available for dimension: {dimension_name}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to analyze {dimension_name} failure: {e}")
            return None
    
    # ==================== Macro Analysis Methods ====================
    
    async def perform_macro_analysis(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform macro-level analysis on failed dimensions.
        
        This method analyzes patterns across all test failures for each dimension
        that's performing below its target score. It adds consolidated recommendations
        and identifies systemic issues.
        
        Args:
            results: Complete evaluation results from all tests
            
        Returns:
            Updated results with 'macro_analyses' key containing cross-test patterns
        """
        logger.info("📊 Starting macro-level analysis across all test failures")
        
        # Aggregate dimension data across all tests
        dimension_aggregates = self._aggregate_dimension_failures(results)
        
        # Perform macro analysis for each failed dimension
        macro_analyses = {}
        
        for dimension_name, dim_data in dimension_aggregates.items():
            if dim_data['avg_score'] < dim_data['target_score']:
                logger.info(f"🔍 Performing macro analysis for {dimension_name} " +
                           f"(avg: {dim_data['avg_score']:.2%} < target: {dim_data['target_score']:.2%})")
                
                # Prepare data for LLM Judge
                analysis_data = {
                    'dimension_name': dimension_name,
                    'total_tests': dim_data['total_tests'],
                    'avg_score': dim_data['avg_score'],
                    'target_score': dim_data['target_score'],
                    'failure_rate': dim_data['failure_rate'],
                    'failed_tests': dim_data['failed_tests']
                }
                
                # Get macro analysis from LLM Judge
                macro_analysis = await self.llm_judge.analyze_dimension_patterns(
                    agent_type='cmo',
                    dimension_name=dimension_name,
                    dimension_data=analysis_data
                )
                
                if macro_analysis:
                    macro_analyses[dimension_name] = macro_analysis
                    logger.info(f"✅ Macro analysis complete for {dimension_name}")
                else:
                    logger.warning(f"❌ Failed to get macro analysis for {dimension_name}")
        
        # Add macro analyses to results
        results['macro_analyses'] = macro_analyses
        logger.info(f"📊 Macro analysis complete: {len(macro_analyses)} dimensions analyzed")
        
        return results
    
    def _aggregate_dimension_failures(self, results: Dict[str, Any]) -> Dict[str, Dict]:
        """
        Aggregate failure data by dimension across all tests.
        
        This method collects all test results for each dimension, calculates
        average scores, and gathers detailed failure information including
        individual LLM Judge analyses.
        
        Args:
            results: Complete evaluation results
            
        Returns:
            Dictionary mapping dimension names to aggregated data
        """
        dimension_aggregates = {}
        
        # Process each test result
        for test_result in results.get('results', []):
            # Process each dimension by looking for dimension scores directly
            for criteria in self.agent_metadata.evaluation_criteria:
                dim_name = criteria.dimension.name
                score_key = f"{dim_name}_score"
                
                if score_key in test_result:
                    score = test_result[score_key]
                    
                    # Initialize dimension aggregate if not exists
                    if dim_name not in dimension_aggregates:
                        dimension_aggregates[dim_name] = {
                            'total_tests': 0,
                            'failed_tests': [],
                            'all_scores': [],
                            'target_score': criteria.target_score,
                            'unique_prompt_files': set()  # Track all mentioned prompt files
                        }
                    
                    agg = dimension_aggregates[dim_name]
                    agg['total_tests'] += 1
                    agg['all_scores'].append(score)
                    
                    # If failed, collect detailed data
                    if score < criteria.target_score:
                        failed_test_data = {
                            'test_id': test_result['test_case_id'],
                            'query': test_result.get('query', ''),
                            'score': score,
                            'target': criteria.target_score
                        }
                        
                        # Add individual failure analysis if available
                        if 'failure_analyses' in test_result:
                            for fa in test_result['failure_analyses']:
                                if fa['dimension'] == dim_name:
                                    failed_test_data.update({
                                        'root_cause': fa.get('root_cause'),
                                        'recommendations': fa.get('recommendations', []),
                                        'priority': fa.get('priority'),
                                        'prompt_files': []
                                    })
                                    
                                    # Extract prompt files
                                    if fa.get('prompt_file'):
                                        failed_test_data['prompt_files'].append(fa['prompt_file'])
                                        agg['unique_prompt_files'].add(fa['prompt_file'])
                                    
                                    # Also check for prompt_files list
                                    if fa.get('prompt_files'):
                                        for pf in fa['prompt_files']:
                                            if isinstance(pf, dict):
                                                filename = pf.get('name', pf.get('filename', ''))
                                                if filename:
                                                    failed_test_data['prompt_files'].append(filename)
                                                    agg['unique_prompt_files'].add(filename)
                                            else:
                                                failed_test_data['prompt_files'].append(str(pf))
                                                agg['unique_prompt_files'].add(str(pf))
                                    break
                        
                        agg['failed_tests'].append(failed_test_data)
        
        # Calculate aggregated metrics and convert sets to lists
        for dim_name, agg in dimension_aggregates.items():
            agg['avg_score'] = sum(agg['all_scores']) / len(agg['all_scores']) if agg['all_scores'] else 0
            agg['failure_rate'] = len(agg['failed_tests']) / agg['total_tests'] if agg['total_tests'] > 0 else 0
            agg['unique_prompt_files'] = list(agg['unique_prompt_files'])
            del agg['all_scores']  # Not needed anymore
            
            logger.debug(f"Dimension {dim_name}: {agg['total_tests']} tests, " +
                        f"{len(agg['failed_tests'])} failures, " +
                        f"avg score: {agg['avg_score']:.2%}")
        
        return dimension_aggregates