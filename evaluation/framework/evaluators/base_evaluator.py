"""
Base Evaluation Framework

This module provides the foundation for all agent evaluators in the multi-agent health system.
It defines common interfaces and shared evaluation logic that can be extended by specific
agent evaluators.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Tuple

from anthropic import Anthropic
from evaluation.framework.llm_judge import LLMTestJudge

logger = logging.getLogger(__name__)


@dataclass
class EvaluationResult:
    """Base result class for evaluating a single test case"""
    # Core fields required for all agent types
    test_case_id: str
    query: str
    success: bool
    total_response_time_ms: float
    tokens_used: int
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert evaluation result to dictionary"""
        return asdict(self)


class BaseEvaluator(ABC):
    """
    Abstract base class for all agent evaluators.
    
    Provides common evaluation infrastructure while allowing agent-specific
    implementation of evaluation dimensions and logic.
    """
    
    def __init__(self, anthropic_client: Optional[Anthropic] = None):
        """Initialize base evaluator with optional LLM Judge capabilities"""
        # Initialize LLM Judge for semantic evaluation
        if anthropic_client:
            self.llm_judge = LLMTestJudge(
                anthropic_client=anthropic_client,
                model="claude-3-haiku-20240307"  # Cost-effective model for evaluation
            )
        else:
            self.llm_judge = None
            logger.warning("No Anthropic client provided - LLM Judge features disabled")
    
    @abstractmethod
    async def evaluate_single_test_case(self, test_case: Any) -> EvaluationResult:
        """
        Evaluate agent performance on a single test case.
        
        Args:
            test_case: Test case object (specific to each agent type)
            
        Returns:
            EvaluationResult: Results of the evaluation
        """
        pass
    
    @abstractmethod
    def get_evaluation_dimensions(self) -> List[str]:
        """
        Get list of evaluation dimensions for this agent type.
        
        Returns:
            List of dimension names (e.g., ['complexity_classification', 'analysis_quality'])
        """
        pass
    
    @abstractmethod
    def get_dimension_target(self, dimension: str) -> float:
        """
        Get target score for a specific evaluation dimension.
        
        Args:
            dimension: Name of the evaluation dimension
            
        Returns:
            Target score (0.0 to 1.0)
        """
        pass
    
    async def evaluate_test_suite(
        self, 
        test_cases: List[Any], 
        max_concurrent: int = 5,
        test_ids: Optional[Set[str]] = None
    ) -> Dict[str, Any]:
        """
        Evaluate agent on a suite of test cases with concurrency control.
        
        Args:
            test_cases: List of test case objects
            max_concurrent: Maximum number of concurrent evaluations
            test_ids: Optional set of specific test IDs to run
            
        Returns:
            Dictionary containing aggregated results and summary
        """
        logger.info(f"Starting evaluation of {len(test_cases)} test cases...")
        
        # Filter test cases if specific IDs provided
        if test_ids:
            test_cases = [tc for tc in test_cases if tc.id in test_ids]
            logger.info(f"Filtered to {len(test_cases)} test cases based on test_ids")
        
        if not test_cases:
            logger.warning("No test cases to evaluate")
            return {"results": [], "summary": {}, "overall_success": False}
        
        # Use semaphore to control concurrency
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def eval_with_semaphore(tc):
            async with semaphore:
                return await self.evaluate_single_test_case(tc)
        
        # Run evaluations concurrently
        results = await asyncio.gather(
            *[eval_with_semaphore(tc) for tc in test_cases],
            return_exceptions=True
        )
        
        # Handle any exceptions
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Test case {test_cases[i].id} failed: {result}")
                # Create a failed result
                failed_result = EvaluationResult(
                    test_case_id=test_cases[i].id,
                    query=test_cases[i].query,
                    success=False,
                    total_response_time_ms=0.0,
                    tokens_used=0,
                    error_message=str(result)
                )
                valid_results.append(failed_result)
            else:
                valid_results.append(result)
        
        # Aggregate results
        aggregated = self._aggregate_results(valid_results)
        
        # Create summary
        summary = self._create_summary(aggregated)
        
        logger.info(f"Evaluation complete. Overall success: {summary.get('overall_success', False)}")
        
        return {
            "results": [result.to_dict() for result in valid_results],
            "aggregated": aggregated,
            "summary": summary,
            "overall_success": summary.get("overall_success", False),
            "timestamp": datetime.now().isoformat(),
            "test_count": len(valid_results),
            "agent_type": self.__class__.__name__.replace("Evaluator", "").lower()
        }
    
    def _aggregate_results(self, results: List[EvaluationResult]) -> Dict[str, Any]:
        """
        Aggregate evaluation results across all test cases.
        
        This base implementation provides common aggregation logic.
        Subclasses can override for agent-specific aggregation.
        """
        if not results:
            return {}
        
        # Basic aggregation
        total_tests = len(results)
        successful_tests = sum(1 for r in results if r.success)
        
        # Response time statistics
        response_times = [r.total_response_time_ms for r in results if r.total_response_time_ms > 0]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        # Token usage statistics  
        total_tokens = sum(r.tokens_used for r in results)
        avg_tokens = total_tokens / total_tests if total_tests > 0 else 0
        
        return {
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "success_rate": successful_tests / total_tests if total_tests > 0 else 0,
            "average_response_time_ms": avg_response_time,
            "total_tokens_used": total_tokens,
            "average_tokens_per_test": avg_tokens,
            "failed_tests": [r.test_case_id for r in results if not r.success],
            "results": [r.__dict__ if hasattr(r, '__dict__') else r for r in results]  # Include full results for summary
        }
    
    def _create_summary(self, aggregated: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create evaluation summary from aggregated results.
        
        This base implementation provides common summary logic.
        Subclasses should override for agent-specific summaries.
        """
        if not aggregated:
            return {"overall_success": False}
        
        # Basic pass/fail logic based on success rate
        success_rate = aggregated.get("success_rate", 0)
        overall_success = success_rate >= 0.8  # 80% success threshold
        
        return {
            "overall_success": overall_success,
            "success_rate": success_rate,
            "total_tests": aggregated.get("total_tests", 0),
            "failed_tests": aggregated.get("failed_tests", []),
            "performance_metrics": {
                "avg_response_time_ms": aggregated.get("average_response_time_ms", 0),
                "avg_tokens_per_test": aggregated.get("average_tokens_per_test", 0)
            }
        }
    
    def _validate_response_structure(self, response: str, expected_tags: List[str]) -> Tuple[bool, List[str]]:
        """
        Generic XML response structure validation.
        
        Args:
            response: Response string to validate
            expected_tags: List of expected XML tags
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        import re
        
        errors = []
        
        for tag in expected_tags:
            # Check for opening and closing tags
            opening_pattern = f"<{tag}>"
            closing_pattern = f"</{tag}>"
            
            if opening_pattern not in response:
                errors.append(f"Missing opening tag: <{tag}>")
            
            if closing_pattern not in response:
                errors.append(f"Missing closing tag: </{tag}>")
            
            # Check for content between tags
            content_pattern = f"<{tag}>(.*?)</{tag}>"
            match = re.search(content_pattern, response, re.DOTALL)
            if match and not match.group(1).strip():
                errors.append(f"Empty content in tag: {tag}")
        
        return len(errors) == 0, errors
    
    def _extract_keywords_from_text(self, text: str, keywords: List[str]) -> Set[str]:
        """
        Extract mentioned keywords from text (case-insensitive).
        
        Args:
            text: Text to search in
            keywords: List of keywords to look for
            
        Returns:
            Set of found keywords
        """
        text_lower = text.lower()
        found_keywords = set()
        
        for keyword in keywords:
            if keyword.lower() in text_lower:
                found_keywords.add(keyword)
        
        return found_keywords
    
    async def _run_llm_judge_evaluation(
        self, 
        prompt_template: str, 
        **kwargs
    ) -> Any:
        """
        Helper method to run LLM Judge evaluation with error handling.
        
        Args:
            prompt_template: Template string for the prompt
            **kwargs: Variables to substitute in the template
            
        Returns:
            LLM Judge response or None if unavailable
        """
        if not self.llm_judge:
            logger.warning("LLM Judge not available - skipping semantic evaluation")
            return None
        
        try:
            prompt = prompt_template.format(**kwargs)
            response = await self.llm_judge.evaluate_with_prompt(prompt)
            return response
        except Exception as e:
            logger.error(f"LLM Judge evaluation failed: {e}")
            return None