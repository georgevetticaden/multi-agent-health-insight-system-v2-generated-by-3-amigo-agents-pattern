"""
CMO Agent Evaluator

Core evaluation framework for testing the CMO agent based on Anthropic's best practices.
Implements automated evaluation across multiple dimensions with detailed metrics.
"""

import json
import re
import asyncio
import logging
from typing import Dict, List, Tuple, Optional, Set, Any
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path

from services.agents.cmo.cmo_agent import CMOAgent, QueryComplexity, SpecialistTask
from evaluation.criteria.cmo import (
    EvaluationDimension, 
    CMOEvaluationRubric,
    ComplexityClassificationCriteria,
    SpecialtySelectionCriteria
)
from evaluation.test_cases.cmo import TestCase, CMOTestCases
from evaluation.framework.llm_judge import LLMTestJudge, SpecialistSimilarityScorer
from anthropic import Anthropic

logger = logging.getLogger(__name__)


@dataclass
class EvaluationResult:
    """Result of evaluating a single test case"""
    # Core fields (no defaults)
    test_case_id: str
    query: str
    success: bool
    
    # Stage 1: Complexity classification (no defaults)
    expected_complexity: str
    actual_complexity: Optional[str]
    complexity_correct: bool
    
    # Stage 2: Specialist task creation (no defaults)
    expected_specialties: Set[str]
    actual_specialties: Set[str]  # From tasks, not text!
    
    # Specialty metrics (no defaults)
    specialty_precision: float
    specialty_recall: float
    specialty_f1: float
    
    # Analysis quality (no defaults)
    analysis_quality_score: float
    quality_breakdown: Dict[str, float]
    
    # Tool usage (no defaults)
    tool_calls_made: int
    tool_success_rate: float
    tool_relevance_score: float
    
    # Response structure (no defaults)
    response_valid: bool
    structure_errors: List[str]
    
    # Overall metadata (no defaults)
    total_response_time_ms: float  # analysis + task creation
    tokens_used: int
    
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
    error_message: Optional[str] = None
    approach_mentioned_specialties: Optional[Set[str]] = None
    key_data_points: Optional[List[str]] = None  # Expected keywords from test case


class CMOEvaluator:
    """Evaluates CMO agent performance using hybrid approach (Deterministic + LLM Judge)"""
    
    def __init__(self, cmo_agent: CMOAgent, anthropic_client: Optional[Anthropic] = None):
        self.cmo_agent = cmo_agent
        self.rubric = CMOEvaluationRubric()
        
        # Initialize LLM Judge for semantic evaluation
        if anthropic_client:
            self.llm_judge = LLMTestJudge(
                anthropic_client=anthropic_client,
                model="claude-3-haiku-20240307"  # Use Haiku for cost-effective component scoring
            )
        else:
            # If no client provided, LLM Judge features will be disabled
            self.llm_judge = None
            logger.warning("No Anthropic client provided - LLM Judge features disabled")
        
    async def evaluate_single_test_case(self, test_case: TestCase) -> EvaluationResult:
        """Evaluate CMO agent on a single test case - both stages"""
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
                specialist_tasks = await self.cmo_agent.create_specialist_tasks(
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
            response_valid, structure_errors = self._validate_response_structure(analysis)
            
            # Calculate total time and tokens
            total_response_time_ms = (datetime.now() - start_time).total_seconds() * 1000
            tokens_used = len(test_case.query.split()) + len(analysis.split()) + len(str(serialized_tasks).split())
            
            return EvaluationResult(
                test_case_id=test_case.id,
                query=test_case.query,
                success=True,
                # Stage 1 results
                expected_complexity=test_case.expected_complexity,
                actual_complexity=actual_complexity,
                complexity_correct=complexity_correct,
                approach_text=approach,
                initial_data_gathered=initial_data,
                analysis_time_ms=analysis_time_ms,
                # Stage 2 results
                expected_specialties=test_case.expected_specialties,
                actual_specialties=actual_specialties,
                specialist_tasks=serialized_tasks,
                task_creation_success=task_creation_success,
                task_creation_time_ms=task_creation_time_ms,
                task_creation_error=task_creation_error,
                # Metrics
                specialty_precision=specialty_metrics["precision"],
                specialty_recall=specialty_metrics["recall"],
                specialty_f1=specialty_metrics["f1"],
                analysis_quality_score=quality_score,
                quality_breakdown=quality_breakdown,
                task_count=len(specialist_tasks),
                task_quality_score=task_quality_score,
                task_quality_breakdown=task_quality_breakdown,
                tool_calls_made=tool_metrics["calls_made"],
                tool_success_rate=tool_metrics["success_rate"],
                tool_relevance_score=tool_metrics["relevance_score"],
                response_valid=response_valid,
                structure_errors=structure_errors,
                total_response_time_ms=total_response_time_ms,
                tokens_used=tokens_used,
                approach_mentioned_specialties=approach_mentioned_specialties,
                key_data_points=test_case.key_data_points
            )
            
        except Exception as e:
            logger.error(f"Error evaluating test case {test_case.id}: {str(e)}")
            return EvaluationResult(
                test_case_id=test_case.id,
                query=test_case.query,
                success=False,
                # Stage 1 results
                expected_complexity=test_case.expected_complexity,
                actual_complexity=None,
                complexity_correct=False,
                approach_text=None,
                initial_data_gathered=None,
                analysis_time_ms=0.0,
                # Stage 2 results
                expected_specialties=test_case.expected_specialties,
                actual_specialties=set(),
                specialist_tasks=[],
                task_creation_success=False,
                task_creation_time_ms=0.0,
                task_creation_error=str(e),
                # Metrics
                specialty_precision=0.0,
                specialty_recall=0.0,
                specialty_f1=0.0,
                analysis_quality_score=0.0,
                quality_breakdown={},
                task_count=0,
                task_quality_score=0.0,
                task_quality_breakdown={},
                tool_calls_made=0,
                tool_success_rate=0.0,
                tool_relevance_score=0.0,
                response_valid=False,
                structure_errors=["Exception occurred"],
                total_response_time_ms=(datetime.now() - start_time).total_seconds() * 1000,
                tokens_used=0,
                error_message=str(e),
                approach_mentioned_specialties=set(),
                key_data_points=test_case.key_data_points
            )
    
    def _extract_specialties_from_analysis(self, analysis: str) -> Set[str]:
        """Extract mentioned specialties from the analysis text"""
        # Map of specialty terms to standardized names
        specialty_mappings = {
            "endocrinolog": "endocrinology",
            "cardiolog": "cardiology",
            "nutrition": "nutrition",
            "general practice": "general_practice",
            "preventive medicine": "preventive_medicine",
            "laboratory": "laboratory_medicine",
            "lab medicine": "laboratory_medicine",
            "pharmacy": "pharmacy",
            "pharmacist": "pharmacy",
            "data analy": "data_analysis"
        }
        
        analysis_lower = analysis.lower()
        found_specialties = set()
        
        for term, specialty in specialty_mappings.items():
            if term in analysis_lower:
                found_specialties.add(specialty)
        
        return found_specialties
    
    async def _calculate_specialty_metrics(
        self, 
        expected: Set[str], 
        actual: Set[str],
        query: str,
        approach_text: str
    ) -> Dict[str, float]:
        """Calculate specialty metrics using LLM Judge for semantic evaluation"""
        if not expected and not actual:
            return {"precision": 1.0, "recall": 1.0, "f1": 1.0}
        
        if not actual:
            return {"precision": 0.0, "recall": 0.0, "f1": 0.0}
        
        # First calculate basic metrics
        true_positives = len(expected & actual)
        false_positives = len(actual - expected)
        false_negatives = len(expected - actual)
        
        basic_precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0.0
        basic_recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0.0
        basic_f1 = 2 * (basic_precision * basic_recall) / (basic_precision + basic_recall) if (basic_precision + basic_recall) > 0 else 0.0
        
        # If LLM Judge available, use semantic evaluation
        if self.llm_judge and basic_f1 < 1.0:
            try:
                judgment = await self.llm_judge.judge_specialist_similarity(
                    list(actual),
                    list(expected),
                    query,
                    approach_text
                )
                
                # Use LLM Judge's semantic score if it recognizes valid substitutions
                if judgment.is_similar and judgment.similarity_score > basic_f1:
                    logger.debug(f"LLM Judge improved specialty score from {basic_f1:.2f} to {judgment.similarity_score:.2f}")
                    return {
                        "precision": judgment.similarity_score,
                        "recall": judgment.similarity_score,
                        "f1": judgment.similarity_score,
                        "llm_judge_used": True,
                        "llm_judge_reasoning": judgment.reasoning
                    }
            except Exception as e:
                logger.error(f"LLM Judge error in specialty evaluation: {e}")
        
        return {
            "precision": basic_precision,
            "recall": basic_recall,
            "f1": basic_f1,
            "llm_judge_used": False
        }
    
    async def _evaluate_analysis_quality(
        self, 
        analysis: str, 
        tool_results: Dict[str, Any],
        test_case: TestCase
    ) -> Tuple[float, Dict[str, float]]:
        """Evaluate analysis quality using hybrid approach (deterministic + LLM Judge)"""
        quality_scores = {}
        
        # Deterministic: Check for data gathering
        quality_scores["data_gathering"] = 1.0 if tool_results else 0.0
        
        # LLM Judge: Context awareness (if available)
        if self.llm_judge:
            try:
                context_score = await self._llm_judge_context_awareness(analysis, test_case.query)
                quality_scores["context_awareness"] = context_score
            except:
                # Fallback to deterministic
                context_patterns = [r"current", r"today", r"this year", r"last year", r"\d{4}"]
                quality_scores["context_awareness"] = 1.0 if any(re.search(p, analysis, re.I) for p in context_patterns) else 0.5
        else:
            # Deterministic fallback
            context_patterns = [r"current", r"today", r"this year", r"last year", r"\d{4}"]
            quality_scores["context_awareness"] = 1.0 if any(re.search(p, analysis, re.I) for p in context_patterns) else 0.5
        
        # LLM Judge: Specialist rationale quality
        if self.llm_judge:
            try:
                rationale_score = await self._llm_judge_specialist_rationale(analysis)
                quality_scores["specialist_rationale"] = rationale_score
            except:
                # Fallback to deterministic
                rationale_patterns = [r"need", r"require", r"specialist", r"expert", r"because", r"since"]
                quality_scores["specialist_rationale"] = 1.0 if any(re.search(p, analysis, re.I) for p in rationale_patterns) else 0.0
        else:
            rationale_patterns = [r"need", r"require", r"specialist", r"expert", r"because", r"since"]
            quality_scores["specialist_rationale"] = 1.0 if any(re.search(p, analysis, re.I) for p in rationale_patterns) else 0.0
        
        # LLM Judge: Comprehensive approach (semantic coverage)
        if self.llm_judge:
            try:
                comprehensive_score = await self._llm_judge_comprehensive_approach(
                    analysis, test_case.key_data_points, test_case.query
                )
                quality_scores["comprehensive_approach"] = comprehensive_score
            except:
                # Fallback to deterministic
                mentioned_aspects = sum(1 for kd in test_case.key_data_points if kd.lower() in analysis.lower())
                quality_scores["comprehensive_approach"] = min(1.0, mentioned_aspects / max(1, len(test_case.key_data_points)))
        else:
            mentioned_aspects = sum(1 for kd in test_case.key_data_points if kd.lower() in analysis.lower())
            quality_scores["comprehensive_approach"] = min(1.0, mentioned_aspects / max(1, len(test_case.key_data_points)))
        
        # LLM Judge: Concern identification
        if self.llm_judge:
            try:
                concern_score = await self._llm_judge_concern_identification(analysis, test_case.query)
                quality_scores["concern_identification"] = concern_score
            except:
                # Fallback to deterministic
                concern_patterns = [r"concern", r"risk", r"monitor", r"attention", r"important", r"note"]
                quality_scores["concern_identification"] = 1.0 if any(re.search(p, analysis, re.I) for p in concern_patterns) else 0.5
        else:
            concern_patterns = [r"concern", r"risk", r"monitor", r"attention", r"important", r"note"]
            quality_scores["concern_identification"] = 1.0 if any(re.search(p, analysis, re.I) for p in concern_patterns) else 0.5
        
        # Calculate weighted average
        weights = {
            "data_gathering": 0.2,
            "context_awareness": 0.15,
            "specialist_rationale": 0.2,
            "comprehensive_approach": 0.25,
            "concern_identification": 0.2
        }
        
        total_score = sum(quality_scores[k] * weights[k] for k in quality_scores)
        
        return total_score, quality_scores
    
    def _evaluate_tool_usage(self, tool_results: Dict[str, Any]) -> Dict[str, float]:
        """Evaluate tool usage effectiveness"""
        if not tool_results:
            return {
                "calls_made": 0,
                "success_rate": 0.0,
                "relevance_score": 0.0
            }
        
        # For now, we'll use simplified metrics
        # In a real implementation, we'd analyze the actual tool calls
        return {
            "calls_made": 1,  # Simplified: assume 1 call was made
            "success_rate": 1.0 if tool_results else 0.0,
            "relevance_score": 0.9  # Placeholder - would analyze query relevance
        }
    
    def _validate_response_structure(self, analysis: str) -> Tuple[bool, List[str]]:
        """Validate the response follows expected structure"""
        errors = []
        
        # Only log details if there's an issue
        has_complexity = "<complexity>" in analysis
        has_approach = "<approach>" in analysis
        
        if not has_complexity or not has_approach:
            logger.debug(f"Response validation issue - has_complexity: {has_complexity}, has_approach: {has_approach}")
            logger.debug(f"First 500 chars of analysis: {analysis[:500]}")
        
        # Check for required XML tags
        if "<complexity>" not in analysis:
            errors.append("Missing <complexity> tag")
        if "<approach>" not in analysis:
            errors.append("Missing <approach> tag")
        
        # Extract and validate complexity value
        complexity_match = re.search(r"<complexity>(.*?)</complexity>", analysis, re.DOTALL)
        if complexity_match:
            complexity_value = complexity_match.group(1).strip()
            valid_values = ["SIMPLE", "STANDARD", "COMPLEX", "COMPREHENSIVE"]
            if complexity_value not in valid_values:
                errors.append(f"Invalid complexity value: {complexity_value}")
        
        # Check approach content
        approach_match = re.search(r"<approach>(.*?)</approach>", analysis, re.DOTALL)
        if approach_match:
            approach_content = approach_match.group(1).strip()
            if len(approach_content) < 50:  # Arbitrary minimum length
                errors.append("Approach content too brief")
        
        return len(errors) == 0, errors
    
    def _evaluate_task_quality(
        self, 
        tasks: List[SpecialistTask], 
        complexity: QueryComplexity,
        test_case: TestCase
    ) -> Tuple[float, Dict[str, float]]:
        """Evaluate the quality of created specialist tasks"""
        quality_scores = {}
        
        if not tasks:
            return 0.0, {
                "task_count_score": 0.0,
                "task_definition_score": 0.0,
                "priority_order_score": 0.0,
                "specialist_coverage_score": 0.0
            }
        
        # 1. Task count appropriateness
        expected_ranges = {
            QueryComplexity.SIMPLE: (1, 1),
            QueryComplexity.STANDARD: (2, 3),
            QueryComplexity.COMPLEX: (3, 5),
            QueryComplexity.COMPREHENSIVE: (5, 8)
        }
        
        min_expected, max_expected = expected_ranges.get(complexity, (1, 8))
        task_count = len(tasks)
        
        if min_expected <= task_count <= max_expected:
            quality_scores["task_count_score"] = 1.0
        elif task_count < min_expected:
            quality_scores["task_count_score"] = task_count / min_expected
        else:
            quality_scores["task_count_score"] = max_expected / task_count
        
        # 2. Task definition quality (check if tasks have proper fields)
        well_defined_tasks = sum(
            1 for task in tasks
            if len(task.objective) > 20 and len(task.context) > 30 and len(task.expected_output) > 20
        )
        quality_scores["task_definition_score"] = well_defined_tasks / len(tasks) if tasks else 0.0
        
        # 3. Priority ordering (check if priorities make sense)
        priorities = [task.priority for task in tasks]
        # Check if priorities are unique and sequential (1, 2, 3...)
        expected_priorities = list(range(1, len(tasks) + 1))
        if sorted(priorities) == expected_priorities:
            quality_scores["priority_order_score"] = 1.0
        else:
            # Partial credit for having some order
            quality_scores["priority_order_score"] = 0.5
        
        # 4. Specialist coverage (how well do assigned specialists match expected)
        assigned_specialists = {task.specialist.value for task in tasks}
        expected_specialists = test_case.expected_specialties
        
        if expected_specialists:
            overlap = len(assigned_specialists & expected_specialists)
            coverage = overlap / len(expected_specialists)
            quality_scores["specialist_coverage_score"] = coverage
        else:
            # If no expected specialists, just check if we have some
            quality_scores["specialist_coverage_score"] = 1.0 if assigned_specialists else 0.0
        
        # Calculate overall score
        weights = {
            "task_count_score": 0.25,
            "task_definition_score": 0.25,
            "priority_order_score": 0.20,
            "specialist_coverage_score": 0.30
        }
        
        total_score = sum(
            quality_scores[metric] * weights[metric]
            for metric in weights
        )
        
        return total_score, quality_scores
    
    async def evaluate_test_suite(
        self, 
        test_cases: List[TestCase],
        parallel: bool = True,
        max_concurrent: int = 5
    ) -> Dict[str, Any]:
        """Evaluate CMO agent on multiple test cases"""
        logger.info(f"Starting evaluation of {len(test_cases)} test cases")
        
        if parallel:
            # Run evaluations in parallel with concurrency limit
            semaphore = asyncio.Semaphore(max_concurrent)
            
            async def eval_with_semaphore(tc):
                async with semaphore:
                    return await self.evaluate_single_test_case(tc)
            
            results = await asyncio.gather(
                *[eval_with_semaphore(tc) for tc in test_cases]
            )
        else:
            # Run evaluations sequentially
            results = []
            for tc in test_cases:
                result = await self.evaluate_single_test_case(tc)
                results.append(result)
        
        # Aggregate results
        aggregated = self._aggregate_results(results)
        
        return {
            "individual_results": [asdict(r) for r in results],
            "aggregated_metrics": aggregated,
            "evaluation_summary": self._create_summary(aggregated)
        }
    
    def _aggregate_results(self, results: List[EvaluationResult]) -> Dict[str, Any]:
        """Aggregate evaluation results across all test cases"""
        if not results:
            return {}
        
        successful_results = [r for r in results if r.success]
        
        return {
            "total_test_cases": len(results),
            "successful_evaluations": len(successful_results),
            "failed_evaluations": len(results) - len(successful_results),
            
            # Stage 1: Complexity classification metrics
            "complexity_accuracy": sum(r.complexity_correct for r in successful_results) / len(successful_results) if successful_results else 0.0,
            "avg_analysis_time_ms": sum(r.analysis_time_ms for r in successful_results) / len(successful_results) if successful_results else 0.0,
            
            # Stage 2: Task creation metrics
            "task_creation_success_rate": sum(r.task_creation_success for r in successful_results) / len(successful_results) if successful_results else 0.0,
            "avg_task_creation_time_ms": sum(r.task_creation_time_ms for r in successful_results) / len(successful_results) if successful_results else 0.0,
            "avg_task_count": sum(r.task_count for r in successful_results) / len(successful_results) if successful_results else 0.0,
            "avg_task_quality": sum(r.task_quality_score for r in successful_results) / len(successful_results) if successful_results else 0.0,
            
            # Specialty selection metrics (from actual tasks)
            "specialty_avg_precision": sum(r.specialty_precision for r in successful_results) / len(successful_results) if successful_results else 0.0,
            "specialty_avg_recall": sum(r.specialty_recall for r in successful_results) / len(successful_results) if successful_results else 0.0,
            "specialty_avg_f1": sum(r.specialty_f1 for r in successful_results) / len(successful_results) if successful_results else 0.0,
            
            # Analysis quality
            "avg_analysis_quality": sum(r.analysis_quality_score for r in successful_results) / len(successful_results) if successful_results else 0.0,
            
            # Tool usage
            "avg_tool_success_rate": sum(r.tool_success_rate for r in successful_results) / len(successful_results) if successful_results else 0.0,
            "avg_tool_relevance": sum(r.tool_relevance_score for r in successful_results) / len(successful_results) if successful_results else 0.0,
            
            # Response structure
            "response_validity_rate": sum(r.response_valid for r in successful_results) / len(successful_results) if successful_results else 0.0,
            
            # Overall performance
            "avg_total_response_time_ms": sum(r.total_response_time_ms for r in successful_results) / len(successful_results) if successful_results else 0.0,
            "avg_tokens_used": sum(r.tokens_used for r in successful_results) / len(successful_results) if successful_results else 0.0,
            
            # By complexity breakdown
            "by_complexity": self._aggregate_by_complexity(successful_results)
        }
    
    def _aggregate_by_complexity(self, results: List[EvaluationResult]) -> Dict[str, Dict[str, float]]:
        """Aggregate results by complexity level"""
        complexity_groups = {}
        
        for result in results:
            complexity = result.expected_complexity
            if complexity not in complexity_groups:
                complexity_groups[complexity] = []
            complexity_groups[complexity].append(result)
        
        aggregated = {}
        for complexity, group in complexity_groups.items():
            aggregated[complexity] = {
                "count": len(group),
                "accuracy": sum(r.complexity_correct for r in group) / len(group),
                "specialty_f1": sum(r.specialty_f1 for r in group) / len(group),
                "quality_score": sum(r.analysis_quality_score for r in group) / len(group),
                "task_quality": sum(r.task_quality_score for r in group) / len(group),
                "avg_task_count": sum(r.task_count for r in group) / len(group),
                "avg_response_time_ms": sum(r.total_response_time_ms for r in group) / len(group)
            }
        
        return aggregated
    
    def _create_summary(self, aggregated: Dict[str, Any]) -> Dict[str, Any]:
        """Create evaluation summary with pass/fail determination"""
        dimension_scores = {
            EvaluationDimension.COMPLEXITY_CLASSIFICATION: aggregated.get("complexity_accuracy", 0.0),
            EvaluationDimension.SPECIALTY_SELECTION: aggregated.get("specialty_avg_f1", 0.0),
            EvaluationDimension.ANALYSIS_QUALITY: aggregated.get("avg_analysis_quality", 0.0),
            EvaluationDimension.TOOL_USAGE: aggregated.get("avg_tool_success_rate", 0.0),
            EvaluationDimension.RESPONSE_STRUCTURE: aggregated.get("response_validity_rate", 0.0)
        }
        
        evaluation_result = self.rubric.evaluate_performance(dimension_scores)
        
        return {
            "overall_result": "PASS" if evaluation_result["passed"] else "FAIL",
            "dimension_results": evaluation_result["dimension_scores"],
            "overall_score": evaluation_result["overall_score"],
            "overall_target": evaluation_result["overall_target"],
            "failed_dimensions": evaluation_result["failed_dimensions"],
            "recommendations": self._generate_recommendations(evaluation_result)
        }
    
    def _generate_recommendations(self, evaluation_result: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on evaluation results"""
        recommendations = []
        
        for dimension in evaluation_result["failed_dimensions"]:
            if dimension == "complexity_classification":
                recommendations.append("Review and refine complexity classification prompts - consider adding more examples")
            elif dimension == "specialty_selection":
                recommendations.append("Improve specialty selection logic - ensure all relevant specialists are identified")
            elif dimension == "analysis_quality":
                recommendations.append("Enhance analysis prompts to ensure comprehensive coverage of key aspects")
            elif dimension == "tool_usage":
                recommendations.append("Optimize tool usage patterns - ensure relevant and efficient tool calls")
            elif dimension == "response_structure":
                recommendations.append("Enforce stricter response format validation in prompts")
        
        return recommendations
    
    # LLM Judge helper methods for quality component evaluation
    
    async def _llm_judge_context_awareness(self, analysis: str, query: str) -> float:
        """Use LLM Judge to evaluate context awareness"""
        prompt = f"""Evaluate if this medical analysis shows appropriate temporal/contextual awareness.

<query>{query}</query>
<analysis>{analysis}</analysis>

Score 0.0-1.0 based on:
- Recognition of time-based elements in the query
- Appropriate use of temporal context
- Awareness of data timeframes

Provide only a score between 0.0 and 1.0."""
        
        response = await self.llm_judge.anthropic_client.messages.create(
            model=self.llm_judge.model,
            max_tokens=10,
            messages=[{"role": "user", "content": prompt}]
        )
        
        try:
            score = float(response.content[0].text.strip())
            return min(1.0, max(0.0, score))
        except:
            return 0.5  # Default middle score on error
    
    async def _llm_judge_specialist_rationale(self, analysis: str) -> float:
        """Use LLM Judge to evaluate specialist selection rationale"""
        prompt = f"""Evaluate the quality of reasoning for specialist selection in this analysis.

<analysis>{analysis}</analysis>

Score 0.0-1.0 based on:
- Clear justification for each specialist
- Medical appropriateness of reasoning
- Logical connection between query needs and specialists

Provide only a score between 0.0 and 1.0."""
        
        response = await self.llm_judge.anthropic_client.messages.create(
            model=self.llm_judge.model,
            max_tokens=10,
            messages=[{"role": "user", "content": prompt}]
        )
        
        try:
            score = float(response.content[0].text.strip())
            return min(1.0, max(0.0, score))
        except:
            return 0.0  # Default low score on error
    
    async def _llm_judge_comprehensive_approach(self, analysis: str, key_concepts: List[str], query: str) -> float:
        """Use LLM Judge to evaluate comprehensive coverage semantically"""
        prompt = f"""Evaluate how comprehensively this medical analysis covers the expected concepts.

<query>{query}</query>
<expected_concepts>{', '.join(key_concepts)}</expected_concepts>
<analysis>{analysis}</analysis>

Score 0.0-1.0 based on semantic coverage of concepts, not literal matching.
For example, "HDL cholesterol" covers "hdl_cholesterol", "blood sugar" covers "glucose".

Provide only a score between 0.0 and 1.0."""
        
        response = await self.llm_judge.anthropic_client.messages.create(
            model=self.llm_judge.model,
            max_tokens=10,
            messages=[{"role": "user", "content": prompt}]
        )
        
        try:
            score = float(response.content[0].text.strip())
            return min(1.0, max(0.0, score))
        except:
            # Fallback to deterministic
            mentioned = sum(1 for kc in key_concepts if kc.lower() in analysis.lower())
            return mentioned / max(1, len(key_concepts))
    
    async def _llm_judge_concern_identification(self, analysis: str, query: str) -> float:
        """Use LLM Judge to evaluate health concern identification"""
        prompt = f"""Evaluate how well this analysis identifies relevant health concerns.

<query>{query}</query>
<analysis>{analysis}</analysis>

Score 0.0-1.0 based on:
- Identification of potential health risks
- Appropriate level of concern
- Medical relevance of identified issues

Provide only a score between 0.0 and 1.0."""
        
        response = await self.llm_judge.anthropic_client.messages.create(
            model=self.llm_judge.model,
            max_tokens=10,
            messages=[{"role": "user", "content": prompt}]
        )
        
        try:
            score = float(response.content[0].text.strip())
            return min(1.0, max(0.0, score))
        except:
            return 0.5  # Default middle score on error