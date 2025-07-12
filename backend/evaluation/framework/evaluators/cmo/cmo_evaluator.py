"""
CMO Agent Evaluator

This module contains the CMO-specific evaluation logic, extending the base evaluator
framework with CMO-specific dimensions and test logic.
"""

import re
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Set, Any

from services.agents.cmo.cmo_agent import CMOAgent, QueryComplexity, SpecialistTask
from evaluation.framework.evaluators.base_evaluator import BaseEvaluator, EvaluationResult
from evaluation.framework.llm_judge import SpecialistSimilarityScorer
from anthropic import Anthropic

logger = logging.getLogger(__name__)


@dataclass
class CMOEvaluationResult(EvaluationResult):
    """CMO-specific evaluation result extending the base result"""
    
    # Stage 1: Complexity classification
    expected_complexity: str = ""
    actual_complexity: Optional[str] = None
    complexity_correct: bool = False
    
    # Stage 2: Specialist task creation
    expected_specialties: Set[str] = field(default_factory=set)
    actual_specialties: Set[str] = field(default_factory=set)  # From tasks, not text!
    
    # Specialty metrics
    specialty_precision: float = 0.0
    specialty_recall: float = 0.0
    specialty_f1: float = 0.0
    
    # Analysis quality
    analysis_quality_score: float = 0.0
    quality_breakdown: Dict[str, float] = field(default_factory=dict)
    
    # Tool usage
    tool_calls_made: int = 0
    tool_success_rate: float = 0.0
    tool_relevance_score: float = 0.0
    
    # Response structure
    response_valid: bool = False
    structure_errors: List[str] = field(default_factory=list)
    
    # Fields with defaults (must come after all non-default fields)
    approach_text: Optional[str] = None
    initial_data_gathered: Optional[Dict[str, Any]] = None
    analysis_time_ms: float = 0.0
    specialist_tasks: Optional[List[Dict[str, Any]]] = None  # Serialized SpecialistTask objects
    task_creation_success: bool = False
    task_creation_time_ms: float = 0.0
    task_creation_error: Optional[str] = None
    task_count: int = 0
    task_quality_score: float = 0.0
    task_quality_breakdown: Optional[Dict[str, float]] = None
    approach_mentioned_specialties: Optional[Set[str]] = None
    key_data_points: Optional[List[str]] = None  # Expected keywords from test case


class CMOEvaluator(BaseEvaluator):
    """Evaluates CMO agent performance using hybrid approach (Deterministic + LLM Judge)"""
    
    def __init__(self, cmo_agent: CMOAgent, anthropic_client: Optional[Anthropic] = None):
        super().__init__(anthropic_client)
        self.cmo_agent = cmo_agent
        
        # Import CMO-specific criteria
        from evaluation.criteria.cmo import CMOEvaluationRubric
        self.rubric = CMOEvaluationRubric()
    
    def get_evaluation_dimensions(self) -> List[str]:
        """Get CMO evaluation dimensions"""
        return [
            "complexity_classification",
            "specialty_selection", 
            "analysis_quality",
            "tool_usage",
            "response_structure"
        ]
    
    def get_dimension_target(self, dimension: str) -> float:
        """Get target score for CMO evaluation dimension"""
        targets = {
            "complexity_classification": self.rubric.COMPLEXITY_ACCURACY_TARGET,
            "specialty_selection": self.rubric.SPECIALTY_F1_TARGET,
            "analysis_quality": self.rubric.ANALYSIS_QUALITY_TARGET,
            "tool_usage": self.rubric.TOOL_SUCCESS_TARGET,
            "response_structure": self.rubric.STRUCTURE_VALIDITY_TARGET
        }
        return targets.get(dimension, 0.8)  # Default to 80%
    
    async def evaluate_single_test_case(self, test_case) -> CMOEvaluationResult:
        """Evaluate CMO agent on a single test case - both stages"""
        # Import test case type
        from evaluation.test_cases.cmo import TestCase
        
        logger.info(f"Evaluating test case: {test_case.id} - {test_case.query[:50]}...")
        
        start_time = datetime.now()
        
        try:
            # Stage 1: Analyze query
            logger.debug("Stage 1: Calling analyze_query_with_tools...")
            analysis_start = datetime.now()
            complexity, approach, initial_data = await self.cmo_agent.analyze_query_with_tools(
                test_case.query
            )
            analysis_time_ms = (datetime.now() - analysis_start).total_seconds() * 1000
            logger.debug(f"Stage 1 complete - Complexity: {complexity.value}, Approach length: {len(approach)} chars")
            
            # Reconstruct the full analysis with XML tags for validation
            analysis = f"<complexity>{complexity.value.upper()}</complexity>\n<approach>{approach}</approach>"
            
            # Extract actual values from Stage 1
            actual_complexity = complexity.value if complexity else None
            
            # Optional: Extract specialists mentioned in approach text (for comparison)
            approach_mentioned_specialties = self._extract_specialties_from_analysis(analysis)
            
            # Stage 2: Create specialist tasks
            logger.debug("Stage 2: Calling create_specialist_tasks...")
            task_start = datetime.now()
            specialist_tasks = []
            task_creation_success = True
            task_creation_error = None
            
            try:
                specialist_tasks = self.cmo_agent.create_specialist_tasks(
                    query=test_case.query,
                    complexity=complexity,
                    approach=approach,
                    initial_data=initial_data
                )
                logger.debug(f"Stage 2 complete - Created {len(specialist_tasks)} tasks")
            except Exception as e:
                logger.error(f"Task creation failed: {str(e)}")
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
            
            # Evaluate each dimension
            complexity_correct = actual_complexity == test_case.expected_complexity.lower()
            
            # Calculate specialty metrics using LLM Judge for semantic evaluation
            specialty_metrics = await self._calculate_specialty_metrics(
                test_case.expected_specialties,
                actual_specialties,
                test_case.query,
                approach
            )
            
            # Evaluate analysis quality using hybrid approach
            quality_score, quality_breakdown = await self._evaluate_analysis_quality(
                analysis, initial_data, test_case
            )
            
            # Evaluate task quality
            task_quality_score, task_quality_breakdown = self._evaluate_task_quality(
                specialist_tasks, complexity, test_case
            )
            
            # Evaluate tool usage
            tool_metrics = self._evaluate_tool_usage(initial_data)
            
            # Validate response structure
            response_valid, structure_errors = self._validate_response_structure_cmo(analysis)
            
            # Calculate total time and tokens
            total_response_time_ms = (datetime.now() - start_time).total_seconds() * 1000
            tokens_used = len(test_case.query.split()) + len(analysis.split()) + len(str(serialized_tasks).split())
            
            return CMOEvaluationResult(
                test_case_id=test_case.id,
                query=test_case.query,
                success=complexity_correct and response_valid and task_creation_success,
                expected_complexity=test_case.expected_complexity,
                actual_complexity=actual_complexity,
                complexity_correct=complexity_correct,
                expected_specialties=test_case.expected_specialties,
                actual_specialties=actual_specialties,
                specialty_precision=specialty_metrics["precision"],
                specialty_recall=specialty_metrics["recall"],
                specialty_f1=specialty_metrics["f1"],
                analysis_quality_score=quality_score,
                quality_breakdown=quality_breakdown,
                tool_calls_made=tool_metrics["calls_made"],
                tool_success_rate=tool_metrics["success_rate"],
                tool_relevance_score=tool_metrics["relevance_score"],
                response_valid=response_valid,
                structure_errors=structure_errors,
                total_response_time_ms=total_response_time_ms,
                tokens_used=tokens_used,
                approach_text=approach,
                initial_data_gathered=initial_data,
                analysis_time_ms=analysis_time_ms,
                specialist_tasks=serialized_tasks,
                task_creation_success=task_creation_success,
                task_creation_time_ms=task_creation_time_ms,
                task_creation_error=task_creation_error,
                task_count=len(specialist_tasks),
                task_quality_score=task_quality_score,
                task_quality_breakdown=task_quality_breakdown,
                approach_mentioned_specialties=approach_mentioned_specialties,
                key_data_points=test_case.key_data_points
            )
            
        except Exception as e:
            logger.error(f"Evaluation failed for test case {test_case.id}: {str(e)}")
            total_response_time_ms = (datetime.now() - start_time).total_seconds() * 1000
            
            return CMOEvaluationResult(
                test_case_id=test_case.id,
                query=test_case.query,
                success=False,
                expected_complexity=test_case.expected_complexity,
                actual_complexity=None,
                complexity_correct=False,
                expected_specialties=test_case.expected_specialties,
                actual_specialties=set(),
                specialty_precision=0.0,
                specialty_recall=0.0,
                specialty_f1=0.0,
                analysis_quality_score=0.0,
                quality_breakdown={},
                tool_calls_made=0,
                tool_success_rate=0.0,
                tool_relevance_score=0.0,
                response_valid=False,
                structure_errors=[],
                total_response_time_ms=total_response_time_ms,
                tokens_used=0,
                error_message=str(e)
            )
    
    def _extract_specialties_from_analysis(self, analysis: str) -> Set[str]:
        """Extract specialty mentions from analysis text"""
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

    async def _calculate_specialty_metrics(
        self, 
        expected: Set[str], 
        actual: Set[str], 
        query: str, 
        approach: str
    ) -> Dict[str, float]:
        """Calculate specialty selection metrics using LLM Judge for semantic evaluation"""
        
        if not expected:
            return {"precision": 1.0, "recall": 1.0, "f1": 1.0}
        
        if not actual:
            return {"precision": 0.0, "recall": 0.0, "f1": 0.0}
        
        # Use LLM Judge for semantic similarity if available
        if self.llm_judge:
            try:
                # SpecialistSimilarityScorer uses class methods, no instantiation needed
                similarity_result = SpecialistSimilarityScorer.calculate_similarity(
                    predicted=list(actual),
                    actual=list(expected)
                )
                semantic_score = similarity_result[0]  # First element is the score
                
                # Convert semantic score to precision/recall format
                # If semantic score is high, both precision and recall should be high
                precision = semantic_score
                recall = semantic_score
                f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
                
                return {"precision": precision, "recall": recall, "f1": f1}
                
            except Exception as e:
                logger.warning(f"LLM Judge specialty evaluation failed, falling back to exact matching: {e}")
        
        # Fallback to exact matching
        true_positives = len(expected.intersection(actual))
        precision = true_positives / len(actual) if actual else 0.0
        recall = true_positives / len(expected) if expected else 0.0
        f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        
        return {"precision": precision, "recall": recall, "f1": f1}

    async def _evaluate_analysis_quality(
        self, 
        analysis: str, 
        initial_data: Dict[str, Any], 
        test_case
    ) -> Tuple[float, Dict[str, float]]:
        """Evaluate analysis quality using hybrid approach (deterministic + LLM Judge)"""
        
        quality_components = {}
        
        # Data Gathering (20%) - Deterministic
        data_score = 1.0 if initial_data and any(initial_data.values()) else 0.0
        quality_components["data_gathering"] = data_score
        
        # Context Awareness (15%) - LLM Judge
        context_score = await self._llm_judge_context_awareness(analysis, test_case.query)
        quality_components["context_awareness"] = context_score if context_score is not None else 0.5
        
        # Specialist Rationale (20%) - LLM Judge  
        rationale_score = await self._llm_judge_specialist_rationale(analysis)
        quality_components["specialist_rationale"] = rationale_score if rationale_score is not None else 0.5
        
        # Comprehensive Approach (25%) - LLM Judge
        comprehensive_score = await self._llm_judge_comprehensive_approach(
            analysis, test_case.key_data_points, test_case.query
        )
        quality_components["comprehensive_approach"] = comprehensive_score if comprehensive_score is not None else 0.5
        
        # Concern Identification (20%) - LLM Judge
        concern_score = await self._llm_judge_concern_identification(analysis, test_case.query)
        quality_components["concern_identification"] = concern_score if concern_score is not None else 0.5
        
        # Calculate weighted average
        weights = {
            "data_gathering": 0.20,
            "context_awareness": 0.15,
            "specialist_rationale": 0.20,
            "comprehensive_approach": 0.25,
            "concern_identification": 0.20
        }
        
        total_score = sum(
            quality_components[component] * weights[component]
            for component in quality_components
        )
        
        return total_score, quality_components

    def _evaluate_task_quality(
        self, 
        tasks: List[SpecialistTask], 
        complexity: QueryComplexity, 
        test_case
    ) -> Tuple[float, Dict[str, float]]:
        """Evaluate the quality of created specialist tasks"""
        
        if not tasks:
            return 0.0, {}
        
        quality_metrics = {}
        
        # Task completeness - do all tasks have required fields?
        completeness_score = 0.0
        for task in tasks:
            if all([task.objective, task.context, task.expected_output]):
                completeness_score += 1.0
        completeness_score /= len(tasks)
        quality_metrics["completeness"] = completeness_score
        
        # Task specificity - are objectives specific enough?
        specificity_score = 0.0
        for task in tasks:
            # Simple heuristic: longer, more detailed objectives are likely more specific
            if len(task.objective) > 50 and any(word in task.objective.lower() 
                                              for word in ['analyze', 'evaluate', 'assess', 'examine']):
                specificity_score += 1.0
        specificity_score /= len(tasks) if tasks else 1
        quality_metrics["specificity"] = specificity_score
        
        # Task diversity - are different specialists used?
        specialists_used = {task.specialist.value for task in tasks}
        diversity_score = len(specialists_used) / max(len(tasks), 1)
        quality_metrics["diversity"] = min(diversity_score, 1.0)
        
        # Overall task quality
        overall_score = (
            completeness_score * 0.4 +
            specificity_score * 0.4 +
            diversity_score * 0.2
        )
        
        return overall_score, quality_metrics

    def _evaluate_tool_usage(self, tool_results: Dict[str, Any]) -> Dict[str, float]:
        """Evaluate tool usage effectiveness"""
        
        if not tool_results:
            return {
                "calls_made": 0,
                "success_rate": 0.0,
                "relevance_score": 0.0
            }
        
        # Count successful vs failed tool calls
        calls_made = len(tool_results)
        successful_calls = sum(1 for result in tool_results.values() 
                             if result and not isinstance(result, str) or "error" not in str(result).lower())
        
        success_rate = successful_calls / calls_made if calls_made > 0 else 0.0
        
        # Simple relevance heuristic - if tools returned data, they were likely relevant
        relevance_score = 1.0 if any(tool_results.values()) else 0.0
        
        return {
            "calls_made": calls_made,
            "success_rate": success_rate,
            "relevance_score": relevance_score
        }

    def _validate_response_structure_cmo(self, analysis: str) -> Tuple[bool, List[str]]:
        """Validate CMO-specific response structure"""
        expected_tags = ["complexity", "approach"]
        return self._validate_response_structure(analysis, expected_tags)

    # LLM Judge evaluation methods (placeholder implementations)
    async def _llm_judge_context_awareness(self, analysis: str, query: str) -> float:
        """Evaluate context awareness using LLM Judge"""
        if not self.llm_judge:
            return 0.5  # Default score when LLM Judge unavailable
        
        # Implementation would use LLM Judge to evaluate context awareness
        # For now, return a placeholder score
        return 0.7

    async def _llm_judge_specialist_rationale(self, analysis: str) -> float:
        """Evaluate specialist selection rationale using LLM Judge"""
        if not self.llm_judge:
            return 0.5  # Default score when LLM Judge unavailable
        
        # Implementation would use LLM Judge to evaluate rationale quality
        # For now, return a placeholder score
        return 0.7

    async def _llm_judge_comprehensive_approach(self, analysis: str, key_concepts: List[str], query: str) -> float:
        """Evaluate comprehensive approach using LLM Judge"""
        if not self.llm_judge:
            return 0.5  # Default score when LLM Judge unavailable
        
        # Implementation would use LLM Judge to evaluate comprehensiveness
        # For now, return a placeholder score
        return 0.7

    async def _llm_judge_concern_identification(self, analysis: str, query: str) -> float:
        """Evaluate concern identification using LLM Judge"""
        if not self.llm_judge:
            return 0.5  # Default score when LLM Judge unavailable
        
        # Implementation would use LLM Judge to evaluate concern identification
        # For now, return a placeholder score
        return 0.7