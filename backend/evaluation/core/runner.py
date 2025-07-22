import asyncio
import time
import logging
from typing import Dict, Any, Optional, Callable, AsyncGenerator
from dataclasses import dataclass

from .models import (
    TestCase, 
    EvaluationResult, 
    DimensionResult,
    AgentEvaluationMetadata,
    EvaluationCriteria
)
from .dimensions import EvaluationMethod
from .evaluators import DeterministicEvaluator, LLMJudgeEvaluator

logger = logging.getLogger(__name__)


@dataclass
class EvaluationProgress:
    """Progress update during evaluation"""
    stage: str
    dimension: Optional[str] = None
    progress: float = 0.0
    message: str = ""
    

class EvaluationRunner:
    """Runs evaluations for test cases against agent metadata"""
    
    def __init__(self):
        self.deterministic_evaluator = DeterministicEvaluator()
        self.llm_evaluator = LLMJudgeEvaluator()
    
    async def evaluate_test_case(
        self,
        test_case: TestCase,
        agent_metadata: AgentEvaluationMetadata,
        progress_callback: Optional[Callable[[EvaluationProgress], None]] = None
    ) -> EvaluationResult:
        """
        Evaluate a single test case against agent evaluation criteria
        
        Args:
            test_case: The test case to evaluate
            agent_metadata: Agent's evaluation metadata
            progress_callback: Optional callback for progress updates
            
        Returns:
            EvaluationResult with scores for all dimensions
        """
        logger.info(f"=== EVALUATION RUNNER START ===")
        logger.info(f"Test case ID: {test_case.id}")
        logger.info(f"Agent: {agent_metadata.agent_metadata.agent_type}")
        logger.info(f"Number of evaluation criteria: {len(agent_metadata.evaluation_criteria)}")
        
        start_time = time.time()
        dimension_results = {}
        
        # Report starting
        if progress_callback:
            await progress_callback(EvaluationProgress(
                stage="starting",
                progress=0.0,
                message=f"Starting evaluation for test case: {test_case.id}"
            ))
        
        # Evaluate each criteria
        total_criteria = len(agent_metadata.evaluation_criteria)
        for idx, criteria in enumerate(agent_metadata.evaluation_criteria):
            dimension_name = criteria.dimension.name
            logger.info(f"\nEvaluating dimension {idx+1}/{total_criteria}: {dimension_name}")
            logger.info(f"  Method: {criteria.evaluation_method.value}")
            logger.info(f"  Weight: {criteria.weight}")
            logger.info(f"  Target score: {criteria.target_score}")
            
            # Report dimension start
            if progress_callback:
                await progress_callback(EvaluationProgress(
                    stage="evaluating_dimension",
                    dimension=dimension_name,
                    progress=(idx / total_criteria) * 100,
                    message=f"Evaluating {dimension_name}"
                ))
            
            # Evaluate based on method
            if criteria.evaluation_method == EvaluationMethod.DETERMINISTIC:
                logger.info(f"  Using deterministic evaluation for {dimension_name}")
                result = await self._evaluate_deterministic(test_case, criteria, agent_metadata)
            elif criteria.evaluation_method == EvaluationMethod.LLM_JUDGE:
                logger.info(f"  Using LLM judge evaluation for {dimension_name}")
                result = await self._evaluate_llm_judge(test_case, criteria, agent_metadata)
            elif criteria.evaluation_method == EvaluationMethod.HYBRID:
                logger.info(f"  Using hybrid evaluation for {dimension_name}")
                result = await self._evaluate_hybrid(test_case, criteria, agent_metadata)
            else:
                raise ValueError(f"Unknown evaluation method: {criteria.evaluation_method}")
            
            logger.info(f"  Result: score={result.score:.2f}, normalized={result.normalized_score:.2%}")
            if result.details:
                logger.info(f"  Details: {result.details}")
            
            dimension_results[dimension_name] = result
            
            # Report dimension complete
            if progress_callback:
                await progress_callback(EvaluationProgress(
                    stage="dimension_complete",
                    dimension=dimension_name,
                    progress=((idx + 1) / total_criteria) * 100,
                    message=f"Completed {dimension_name}: {result.normalized_score:.2f}"
                ))
        
        # Calculate overall score
        logger.info("\nCalculating overall score...")
        overall_score = self._calculate_overall_score(
            dimension_results, 
            agent_metadata.evaluation_criteria
        )
        logger.info(f"Overall score: {overall_score:.2%}")
        
        execution_time = (time.time() - start_time) * 1000
        logger.info(f"Total execution time: {execution_time:.0f}ms")
        
        # Report completion
        if progress_callback:
            await progress_callback(EvaluationProgress(
                stage="complete",
                progress=100.0,
                message=f"Evaluation complete. Overall score: {overall_score:.2f}"
            ))
        
        logger.info(f"=== EVALUATION RUNNER COMPLETE ===")
        
        return EvaluationResult(
            test_case_id=test_case.id,
            agent_type=agent_metadata.agent_metadata.agent_type,
            overall_score=overall_score,
            dimension_results=dimension_results,
            execution_time_ms=execution_time,
            metadata={
                "test_case_category": test_case.category,
                "trace_id": test_case.trace_id
            }
        )
    
    async def _evaluate_deterministic(
        self,
        test_case: TestCase,
        criteria: EvaluationCriteria,
        agent_metadata: AgentEvaluationMetadata
    ) -> DimensionResult:
        """Evaluate using deterministic rules"""
        return await self.deterministic_evaluator.evaluate(
            test_case, 
            criteria,
            agent_metadata.quality_components.get(criteria.dimension, [])
        )
    
    async def _evaluate_llm_judge(
        self,
        test_case: TestCase,
        criteria: EvaluationCriteria,
        agent_metadata: AgentEvaluationMetadata
    ) -> DimensionResult:
        """Evaluate using LLM judge"""
        return await self.llm_evaluator.evaluate(
            test_case,
            criteria,
            agent_metadata.quality_components.get(criteria.dimension, [])
        )
    
    async def _evaluate_hybrid(
        self,
        test_case: TestCase,
        criteria: EvaluationCriteria,
        agent_metadata: AgentEvaluationMetadata
    ) -> DimensionResult:
        """Evaluate using hybrid approach"""
        logger.info(f"  === HYBRID EVALUATION START for {criteria.dimension.name} ===")
        
        # Get components for this dimension
        components = agent_metadata.quality_components.get(criteria.dimension, [])
        logger.info(f"  Total components for dimension: {len(components)}")
        
        # Separate by evaluation method
        deterministic_components = [c for c in components if c.evaluation_method == EvaluationMethod.DETERMINISTIC]
        llm_components = [c for c in components if c.evaluation_method == EvaluationMethod.LLM_JUDGE]
        
        logger.info(f"  Deterministic components: {len(deterministic_components)} - {[c.name for c in deterministic_components]}")
        logger.info(f"  LLM Judge components: {len(llm_components)} - {[c.name for c in llm_components]}")
        
        # Evaluate each type
        logger.info(f"  Running deterministic evaluation...")
        det_result = await self.deterministic_evaluator.evaluate(
            test_case, criteria, deterministic_components
        )
        logger.info(f"  Deterministic result: score={det_result.score:.2f}, components={list(det_result.components.keys())}")
        
        logger.info(f"  Running LLM judge evaluation...")
        llm_result = await self.llm_evaluator.evaluate(
            test_case, criteria, llm_components
        )
        logger.info(f"  LLM judge result: score={llm_result.score:.2f}, components={list(llm_result.components.keys())}")
        
        # Combine results
        all_components = {}
        all_components.update(det_result.components)
        all_components.update(llm_result.components)
        logger.info(f"  Combined components: {list(all_components.keys())}")
        
        # Calculate weighted score
        total_weight = sum(c.weight for c in components) or 1.0
        weighted_score = 0.0
        
        for component in components:
            if component.name in all_components:
                component_score = all_components[component.name]
                contribution = component_score * component.weight
                weighted_score += contribution
                logger.info(f"    Component '{component.name}': score={component_score:.2f} * weight={component.weight} = {contribution:.3f}")
            else:
                logger.warning(f"    Component '{component.name}' not found in results!")
        
        final_score = weighted_score / total_weight if total_weight > 0 else 0
        logger.info(f"  Total weight: {total_weight}, Weighted score: {weighted_score:.3f}, Final score: {final_score:.3f}")
        logger.info(f"  === HYBRID EVALUATION END for {criteria.dimension.name} ===")
        
        return DimensionResult(
            dimension_name=criteria.dimension.name,
            score=final_score,
            components=all_components,
            details={
                "deterministic_components": len(deterministic_components),
                "llm_components": len(llm_components)
            },
            evaluation_method="hybrid"
        )
    
    def _calculate_overall_score(
        self,
        dimension_results: Dict[str, DimensionResult],
        criteria_list: list[EvaluationCriteria]
    ) -> float:
        """Calculate weighted overall score"""
        total_score = 0.0
        total_weight = 0.0
        
        for criteria in criteria_list:
            if criteria.dimension.name in dimension_results:
                result = dimension_results[criteria.dimension.name]
                total_score += result.normalized_score * criteria.weight
                total_weight += criteria.weight
        
        return total_score / total_weight if total_weight > 0 else 0.0