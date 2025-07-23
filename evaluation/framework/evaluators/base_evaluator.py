"""
Base Evaluation Framework

This module provides the foundation for all agent evaluators in the multi-agent health system.
It defines common interfaces and shared evaluation logic that can be extended by specific
agent evaluators.

The BaseEvaluator class provides:
- Metadata-driven evaluation framework
- Generic dimension and component evaluation logic
- Common utility methods for evaluation tasks
- Test suite orchestration with concurrency control
- Result aggregation and summary generation

Key Features:
- Agent-agnostic evaluation infrastructure
- Metadata-driven configuration from agent classes
- Hybrid evaluation methods (deterministic + LLM judge)
- Concurrent test execution with configurable limits
- Comprehensive error handling and logging
- Extensible design for agent-specific evaluation logic

Evaluation Flow:
1. Load agent metadata containing evaluation criteria
2. Execute agent on test cases (implemented by subclasses)
3. Apply metadata-driven evaluation across dimensions
4. Calculate component scores using appropriate methods
5. Aggregate results and generate summaries

Extending BaseEvaluator:
- Override evaluate_single_test_case() for agent execution
- Override _evaluate_deterministic_component() for rule-based scoring
- Override _evaluate_llm_component() for semantic evaluation
- Override _evaluate_dimension_direct() for direct dimension scoring
- Override _create_summary() for custom aggregation logic

Usage:
    class MyAgentEvaluator(BaseEvaluator):
        def __init__(self, agent, client):
            super().__init__(client)
            self.agent = agent
            self.agent_metadata = agent.get_evaluation_metadata()
            
        async def evaluate_single_test_case(self, test_case):
            # Agent-specific evaluation logic
            pass

See Also:
    - CMOEvaluator: Example implementation for CMO agent evaluation
    - SpecialistEvaluator: Example implementation for specialist agent evaluation
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Tuple

from anthropic import Anthropic
# LLM Judge is now handled within specific evaluators

logger = logging.getLogger(__name__)

# Import tracing components
try:
    from services.tracing import get_trace_collector, TraceEventType, TraceContextManager
    TRACING_AVAILABLE = True
except ImportError as e:
    TRACING_AVAILABLE = False
    logger.warning(f"Tracing not available in evaluation: {e}")


@dataclass
class EvaluationResult:
    """
    Base result class for evaluating a single test case.
    
    This class provides the common structure for evaluation results
    across all agent types. Agent-specific evaluators should extend
    this class to add their own fields.
    
    Attributes:
        test_case_id: Unique identifier for the test case
        query: The query or input that was evaluated
        success: Boolean indicating if the test passed
        total_response_time_ms: Total time taken for evaluation
        tokens_used: Number of tokens consumed during evaluation
        error_message: Error message if evaluation failed
    
    Example:
        >>> result = EvaluationResult(
        ...     test_case_id="test_001",
        ...     query="What is my cholesterol level?",
        ...     success=True,
        ...     total_response_time_ms=1250.5,
        ...     tokens_used=450
        ... )
    """
    # Core fields required for all agent types
    test_case_id: str
    query: str
    success: bool
    total_response_time_ms: float
    tokens_used: int
    error_message: Optional[str] = None
    trace_id: Optional[str] = None  # Optional trace ID for debugging
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert evaluation result to dictionary"""
        return asdict(self)


class BaseEvaluator(ABC):
    """
    Abstract base class for all agent evaluators.
    
    This class provides a comprehensive framework for evaluating agents
    in the multi-agent health system. It implements the metadata-driven
    evaluation approach that allows for flexible, configurable evaluation
    without hardcoding agent-specific logic.
    
    Key Responsibilities:
    - Orchestrate test suite execution with concurrency control
    - Provide metadata-driven evaluation framework
    - Aggregate results and generate summaries
    - Offer utility methods for common evaluation tasks
    
    Architecture:
    - Template Method pattern for evaluation flow
    - Strategy pattern for evaluation methods (deterministic vs LLM)
    - Metadata-driven configuration from agent classes
    - Extensible design for agent-specific customization
    
    Subclass Requirements:
    - Must override evaluate_single_test_case() for agent execution
    - Should override component evaluation methods for scoring logic
    - Must set agent_metadata in __init__ from agent class
    - Can override summary logic for custom success criteria
    
    Usage Pattern:
        1. Initialize with agent and optional Anthropic client
        2. Load agent metadata containing evaluation criteria
        3. Call evaluate_test_suite() with test cases
        4. Receive comprehensive results with dimension scores
    """
    
    def __init__(self, anthropic_client: Optional[Anthropic] = None):
        """
        Initialize base evaluator with optional Anthropic client.
        
        Args:
            anthropic_client: Optional Anthropic client for LLM-based evaluation
            
        Note:
            Subclasses should set agent_metadata in their __init__ method
            by calling agent.get_evaluation_metadata()
        """
        self.anthropic_client = anthropic_client
        self.agent_metadata = None  # Should be set by subclasses
        # LLM Judge is now initialized in specific evaluators as needed
        
        # Set up tracing if available
        self.tracing_enabled = TRACING_AVAILABLE
        self.trace_collector = get_trace_collector() if TRACING_AVAILABLE else None
    
    @abstractmethod
    async def evaluate_single_test_case(self, test_case: Any) -> EvaluationResult:
        """
        Evaluate agent performance on a single test case.
        
        This method must be implemented by subclasses to provide
        agent-specific evaluation logic. It should:
        1. Execute the agent on the test case
        2. Collect raw evaluation data
        3. Apply metadata-driven evaluation
        4. Return comprehensive results
        
        Args:
            test_case: Test case object (specific to each agent type)
            
        Returns:
            EvaluationResult: Results containing:
            - Basic fields: test_case_id, query, success, response_time, tokens
            - Agent-specific fields: dimension scores, component breakdowns
            - Context: approach text, tool usage, task details
            - Analysis: failure analyses and recommendations
            
        Raises:
            NotImplementedError: If not implemented by subclass
        """
        pass
    
    def get_evaluation_dimensions(self) -> List[str]:
        """
        Get list of evaluation dimensions for this agent type from metadata.
        
        This method extracts the dimension names from the agent's evaluation
        metadata, providing a consistent interface across all evaluators.
        
        Returns:
            List of dimension names (e.g., ['complexity_classification', 'analysis_quality'])
            
        Returns:
            Empty list if no agent metadata is available
            
        Example:
            >>> evaluator.get_evaluation_dimensions()
            ['complexity_classification', 'specialty_selection', 'analysis_quality']
        """
        if not self.agent_metadata:
            return []
        return [criteria.dimension.name for criteria in self.agent_metadata.evaluation_criteria]
    
    def get_dimension_target(self, dimension: str) -> float:
        """
        Get target score for a specific evaluation dimension from metadata.
        
        This method looks up the target score for a dimension from the
        agent's evaluation metadata, providing the threshold for success.
        
        Args:
            dimension: Name of the evaluation dimension
            
        Returns:
            Target score (0.0 to 1.0) that the dimension must achieve
            to be considered successful
            
        Returns:
            0.8 as default if dimension not found or no metadata available
            
        Example:
            >>> evaluator.get_dimension_target('complexity_classification')
            0.90
        """
        if not self.agent_metadata:
            logger.warning(f"No agent metadata available for dimension '{dimension}', using default 0.8")
            return 0.8
            
        criteria = self._get_dimension_criteria(dimension)
        if criteria:
            return criteria.target_score
        
        logger.warning(f"No target score found for dimension '{dimension}' in metadata, using default 0.8")
        return 0.8
    
    async def evaluate_test_suite(
        self, 
        test_cases: List[Any], 
        max_concurrent: int = 5,
        test_ids: Optional[Set[str]] = None
    ) -> Dict[str, Any]:
        """
        Evaluate agent on a suite of test cases with concurrency control.
        
        This method orchestrates the evaluation of multiple test cases,
        managing concurrency to avoid overwhelming the system while
        maintaining good performance.
        
        Args:
            test_cases: List of test case objects to evaluate
            max_concurrent: Maximum number of concurrent evaluations (default: 5)
            test_ids: Optional set of specific test IDs to run (filters test_cases)
            
        Returns:
            Dictionary containing:
            - results: List of individual test results
            - aggregated: Aggregated metrics across all tests
            - summary: High-level summary with pass/fail status
            - overall_success: Boolean indicating overall success
            - timestamp: ISO timestamp of evaluation
            - test_count: Number of tests executed
            - agent_type: Type of agent evaluated
            
        Raises:
            ValueError: If no test cases provided or all filtered out
        """
        logger.info(f"🚀 EVALUATION FRAMEWORK: Starting evaluation of {len(test_cases)} test cases...")
        
        # Filter test cases if specific IDs provided
        if test_ids:
            test_cases = [tc for tc in test_cases if tc.id in test_ids]
            logger.info(f"🔍 Filtered to {len(test_cases)} test cases based on test_ids: {test_ids}")
        
        if not test_cases:
            logger.warning("⚠️ No test cases to evaluate")
            return {"results": [], "summary": {}, "overall_success": False}
        
        # Use semaphore to control concurrency
        logger.info(f"🔄 Running {len(test_cases)} test cases with max_concurrent={max_concurrent}")
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def eval_with_semaphore(tc):
            async with semaphore:
                logger.debug(f"Starting evaluation of test case: {tc.id}")
                
                # Use trace context manager if tracing is enabled
                if self.tracing_enabled and self.trace_collector:
                    # Start a new trace for this test case
                    trace_id = await self.trace_collector.start_trace(
                        source="evaluation",
                        initial_input=getattr(tc, 'query', str(tc)),
                        test_case_id=tc.id,
                        metadata={
                            "test_case_id": tc.id,
                            "evaluated_agent": getattr(self.agent_metadata, 'agent_type', 'unknown') if self.agent_metadata else 'unknown',
                            "evaluation_type": "single_test_case"
                        }
                    )
                    logger.debug(f"Started trace {trace_id} for test case {tc.id}")
                    
                    try:
                        # Important: The trace context should already be set by start_trace
                        # Let's verify it's available
                        from services.tracing import TraceContextManager
                        current_context = TraceContextManager.get_context()
                        if current_context:
                            logger.debug(f"Trace context available: {current_context.trace_id}")
                        else:
                            logger.warning(f"No trace context found after starting trace {trace_id}")
                        
                        result = await self.evaluate_single_test_case(tc)
                        
                        # Add trace_id to result if available
                        if trace_id and hasattr(result, '__dict__'):
                            result.trace_id = trace_id
                        
                        # End the trace
                        await self.trace_collector.end_trace(trace_id)
                        logger.debug(f"Ended trace {trace_id} for test case {tc.id}")
                        
                        logger.debug(f"Completed evaluation of test case: {tc.id} - {'SUCCESS' if result.success else 'FAILURE'}")
                        return result
                    except Exception as e:
                        # End trace even on error
                        if trace_id:
                            await self.trace_collector.end_trace(trace_id)
                        raise
                else:
                    # No tracing
                    result = await self.evaluate_single_test_case(tc)
                    logger.debug(f"Completed evaluation of test case: {tc.id} - {'SUCCESS' if result.success else 'FAILURE'}")
                    return result
        
        # Run evaluations concurrently
        logger.info(f"📊 Executing concurrent evaluations...")
        results = await asyncio.gather(
            *[eval_with_semaphore(tc) for tc in test_cases],
            return_exceptions=True
        )
        logger.info(f"✅ Concurrent evaluations complete")
        
        # Handle any exceptions
        logger.info(f"📊 Processing {len(results)} evaluation results...")
        valid_results = []
        failed_count = 0
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                failed_count += 1
                logger.error(f"❌ Test case {test_cases[i].id} failed: {result}")
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
        
        if failed_count > 0:
            logger.warning(f"⚠️ {failed_count} test cases failed due to exceptions")
        
        # Aggregate results
        logger.info(f"📊 Aggregating results from {len(valid_results)} test cases...")
        aggregated = self._aggregate_results(valid_results)
        
        # Create summary
        logger.info(f"📊 Creating evaluation summary...")
        summary = self._create_summary(aggregated)
        
        success_count = aggregated.get('successful_tests', 0)
        success_rate = aggregated.get('success_rate', 0.0)
        overall_success = summary.get('overall_success', False)
        
        logger.info(f"🏁 EVALUATION COMPLETE: Overall success: {'PASS' if overall_success else 'FAIL'}")
        logger.info(f"📊 Final results: {len(valid_results)} tests, {success_count} passed ({success_rate:.1%})")
        
        if aggregated.get('failed_tests'):
            logger.info(f"❌ Failed tests: {', '.join(aggregated.get('failed_tests', []))}")
        
        final_results = {
            "results": [result.to_dict() for result in valid_results],
            "aggregated": aggregated,
            "summary": summary,
            "overall_success": summary.get("overall_success", False),
            "timestamp": datetime.now().isoformat(),
            "test_count": len(valid_results),
            "agent_type": self.__class__.__name__.replace("Evaluator", "").lower(),
            "evaluation_framework_version": "2.0",  # Metadata-driven version
            "metadata_driven": True
        }
        
        logger.info(f"💾 Evaluation results ready: {len(final_results['results'])} test results, metadata-driven framework v2.0")
        return final_results
    
    def _aggregate_results(self, results: List[EvaluationResult]) -> Dict[str, Any]:
        """
        Aggregate evaluation results across all test cases.
        
        This method calculates common metrics like success rates,
        response times, and token usage across all test results.
        
        Args:
            results: List of EvaluationResult objects from individual tests
            
        Returns:
            Dictionary containing:
            - total_tests: Total number of tests
            - successful_tests: Number of successful tests
            - success_rate: Overall success rate (0.0 to 1.0)
            - average_response_time_ms: Average response time
            - total_tokens_used: Total tokens consumed
            - average_tokens_per_test: Average tokens per test
            - failed_tests: List of failed test case IDs
            - results: Full results for detailed analysis
            
        Note:
            Subclasses can override this method for agent-specific aggregation
            logic, such as dimension-based success criteria.
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
        
        This method generates a high-level summary of the evaluation
        results, including overall success determination and key metrics.
        
        Args:
            aggregated: Aggregated results from _aggregate_results()
            
        Returns:
            Dictionary containing:
            - overall_success: Boolean indicating if evaluation passed
            - success_rate: Success rate (0.0 to 1.0)
            - total_tests: Total number of tests
            - failed_tests: List of failed test case IDs
            - performance_metrics: Dict with timing and token metrics
            
        Note:
            This base implementation uses simple 80% success rate threshold.
            Subclasses should override for agent-specific success criteria,
            such as dimension-based thresholds.
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
        
        This method validates that a response contains the expected XML
        structure with proper opening/closing tags and non-empty content.
        
        Args:
            response: Response string to validate
            expected_tags: List of expected XML tags (without brackets)
            
        Returns:
            Tuple of (is_valid, list_of_errors) where:
            - is_valid: Boolean indicating if structure is valid
            - list_of_errors: List of specific validation errors found
            
        Example:
            >>> is_valid, errors = self._validate_response_structure(
            ...     "<complexity>STANDARD</complexity><approach>...</approach>",
            ...     ["complexity", "approach"]
            ... )
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
        Extract mentioned keywords from text using case-insensitive matching.
        
        This utility method searches for specific keywords in text,
        useful for evaluating coverage of key concepts or terms.
        
        Args:
            text: Text to search in
            keywords: List of keywords to look for
            
        Returns:
            Set of found keywords (original case from keywords list)
            
        Example:
            >>> found = self._extract_keywords_from_text(
            ...     "Patient has diabetes and hypertension",
            ...     ["diabetes", "hypertension", "obesity"]
            ... )
            >>> found  # {"diabetes", "hypertension"}
        """
        text_lower = text.lower()
        found_keywords = set()
        
        for keyword in keywords:
            if keyword.lower() in text_lower:
                found_keywords.add(keyword)
        
        return found_keywords
    
    def _get_dimension_criteria(self, dimension_name: str) -> Optional[Any]:
        """
        Get evaluation criteria for a specific dimension from agent metadata.
        
        This method searches the agent metadata for the evaluation criteria
        corresponding to the specified dimension name.
        
        Args:
            dimension_name: Name of the dimension to get criteria for
            
        Returns:
            EvaluationCriteria object containing:
            - dimension: Dimension object
            - target_score: Target score for the dimension
            - weight: Weight in overall evaluation
            - evaluation_method: Primary evaluation method
            - description: Human-readable description
            
        Returns:
            None if dimension not found in metadata
        """
        if not self.agent_metadata:
            return None
            
        for criteria in self.agent_metadata.evaluation_criteria:
            if criteria.dimension.name == dimension_name:
                return criteria
        return None
    
    def _get_quality_components(self, dimension_name: str) -> List[Any]:
        """
        Get quality components for a dimension from agent metadata.
        
        This method retrieves the quality components that make up a dimension,
        each with its own evaluation method and weight.
        
        Args:
            dimension_name: Name of the dimension to get components for
            
        Returns:
            List of QualityComponent objects, each containing:
            - name: Component name
            - description: Component description
            - weight: Component weight within the dimension
            - evaluation_method: DETERMINISTIC or LLM_JUDGE
            
        Returns:
            Empty list if dimension not found or has no components
        """
        if not self.agent_metadata:
            return []
            
        criteria = self._get_dimension_criteria(dimension_name)
        if not criteria:
            return []
        
        # Get the dimension object
        dimension = criteria.dimension
        
        # Get components from metadata
        return self.agent_metadata.quality_components.get(dimension, [])
    
    def _get_component_weight(self, dimension_name: str, component_name: str) -> float:
        """
        Get weight for a specific component within a dimension.
        
        This method looks up the weight of a specific component within
        a dimension, used for calculating weighted averages.
        
        Args:
            dimension_name: Name of the dimension
            component_name: Name of the component within the dimension
            
        Returns:
            Weight value (0.0 to 1.0) representing the component's
            importance within the dimension
            
        Returns:
            0.0 if component not found
        """
        components = self._get_quality_components(dimension_name)
        for component in components:
            if component.name == component_name:
                return component.weight
        return 0.0
    
    def _get_default_score_for_method(self, method) -> float:
        """
        Get default score when evaluation fails for a specific method.
        
        This method provides reasonable default scores when evaluation
        fails, based on the evaluation method type.
        
        Args:
            method: EvaluationMethod enum value (DETERMINISTIC or LLM_JUDGE)
            
        Returns:
            Default score (0.0 to 1.0) where:
            - DETERMINISTIC failures return 0.0 (no data = no score)
            - LLM_JUDGE failures return 0.5 (neutral score)
            
        Rationale:
            - Deterministic failures typically indicate missing data
            - LLM failures are often temporary and shouldn't penalize too heavily
        """
        # Import here to avoid circular imports
        from evaluation.core.dimensions import EvaluationMethod
        
        # Use 0.5 as neutral score for LLM Judge failures
        # Use 0.0 for deterministic failures (no data = no score)
        if method == EvaluationMethod.LLM_JUDGE:
            return 0.5
        return 0.0
    
    def _load_prompt(self, prompt_type: str, prompt_name: str, agent_type: str = None) -> str:
        """
        Load prompt from file with standardized directory structure.
        
        This method provides a consistent way to load evaluation prompts
        from the standardized directory structure across all evaluators.
        
        Args:
            prompt_type: Type of prompt ('scoring' or 'failure_analysis')
            prompt_name: Name of the prompt file (without .txt extension)
            agent_type: Agent type (if None, infers from class name)
            
        Returns:
            Prompt content as string
            
        Raises:
            FileNotFoundError: If prompt file doesn't exist
            
        Example:
            >>> prompt = self._load_prompt(
            ...     "scoring", "context_awareness", "cmo"
            ... )
            
        Directory Structure:
            evaluation/agents/{agent_type}/judge_prompts/{prompt_type}/{prompt_name}.txt
        """
        from pathlib import Path
        
        # Infer agent type from class name if not provided
        if agent_type is None:
            agent_type = self.__class__.__name__.lower().replace('evaluator', '')
        
        # Build path: evaluation/agents/{agent_type}/judge_prompts/{prompt_type}/{prompt_name}.txt
        base_path = Path(__file__).parent.parent.parent / "agents" / agent_type / "judge_prompts"
        prompt_file = base_path / prompt_type / f"{prompt_name}.txt"
        
        if not prompt_file.exists():
            raise FileNotFoundError(f"Prompt file not found: {prompt_file}")
        
        return prompt_file.read_text()
    
    async def _run_llm_judge_evaluation(
        self, 
        llm_judge,
        prompt_template: str, 
        **kwargs
    ) -> Any:
        """
        Helper method to run LLM Judge evaluation with error handling.
        
        This utility method provides a standardized way to execute LLM
        judge evaluations with proper error handling and logging.
        
        Args:
            llm_judge: LLM Judge instance to use for evaluation
            prompt_template: Template string for the evaluation prompt
            **kwargs: Variables to substitute in the template
            
        Returns:
            LLM Judge response object or None if evaluation failed
            
        Example:
            >>> result = await self._run_llm_judge_evaluation(
            ...     self.llm_judge,
            ...     "Evaluate the quality of: {text}",
            ...     text="Sample text to evaluate"
            ... )
        """
        if not llm_judge:
            logger.warning("LLM Judge not available - skipping semantic evaluation")
            return None
        
        try:
            prompt = prompt_template.format(**kwargs)
            response = await llm_judge.evaluate_with_prompt(prompt)
            return response
        except Exception as e:
            logger.error(f"LLM Judge evaluation failed: {e}")
            return None
    
    async def _evaluate_dimension_dynamic(self, dimension, result_data: Dict[str, Any], test_case: Any) -> Tuple[float, Dict[str, float]]:
        """
        Dynamically evaluate a dimension based on its metadata configuration.
        
        This is the core of the metadata-driven evaluation framework. It:
        1. Retrieves quality components for the dimension from metadata
        2. Evaluates each component using its specified method
        3. Calculates weighted final score based on component weights
        
        Args:
            dimension: Dimension object from agent metadata
            result_data: Dictionary containing raw evaluation data
            test_case: Test case object being evaluated
            
        Returns:
            Tuple of (final_score, component_scores_dict) where:
            - final_score: Weighted average of component scores (0.0 to 1.0)
            - component_scores_dict: Individual component scores by name
            
        Note:
            This method dispatches to _evaluate_deterministic_component() or
            _evaluate_llm_component() based on the component's evaluation method.
        """
        logger.debug(f"📊 Evaluating dimension '{dimension.name}' dynamically...")
        
        # Get components for this dimension
        components = self.agent_metadata.quality_components.get(dimension, [])
        
        if not components:
            # No components - evaluate dimension directly
            logger.debug(f"  No components found for {dimension.name}, evaluating directly")
            return await self._evaluate_dimension_direct(dimension, result_data, test_case)
        
        logger.debug(f"  Found {len(components)} components for {dimension.name}")
        
        # Import here to avoid circular imports
        from evaluation.core.dimensions import EvaluationMethod
        
        # Evaluate each component
        component_scores = {}
        for component in components:
            logger.info(f"    📊 Evaluating component '{component.name}' using {component.evaluation_method.value}")
            
            if component.evaluation_method == EvaluationMethod.DETERMINISTIC:
                logger.info(f"      🔢 Using deterministic evaluation for {component.name}")
                score = await self._evaluate_deterministic_component(component, dimension, result_data, test_case)
                logger.info(f"      ✅ Deterministic score: {score:.3f}")
            elif component.evaluation_method == EvaluationMethod.LLM_JUDGE:
                logger.info(f"      🤖 Using LLM Judge evaluation for {component.name}")
                score = await self._evaluate_llm_component(component, dimension, result_data, test_case)
                logger.info(f"      ✅ LLM Judge score: {score:.3f}")
            else:
                logger.warning(f"❌ Unknown evaluation method {component.evaluation_method} for component {component.name}")
                score = self._get_default_score_for_method(component.evaluation_method)
                logger.warning(f"      ⚠️  Default score: {score:.3f}")
            
            component_scores[component.name] = score
        
        # Calculate weighted final score using component weights
        weighted_sum = sum(
            component_scores[comp.name] * comp.weight 
            for comp in components 
            if comp.name in component_scores
        )
        total_weight = sum(comp.weight for comp in components if comp.name in component_scores)
        final_score = weighted_sum / total_weight if total_weight > 0 else 0.0
        
        logger.debug(f"  Final score for {dimension.name}: {final_score:.3f} (weighted from {len(component_scores)} components)")
        return final_score, component_scores
    
    async def _evaluate_dimension_direct(self, dimension, result_data: Dict[str, Any], test_case: Any) -> Tuple[float, Dict[str, float]]:
        """
        Evaluate dimension directly without components (fallback method).
        
        This method is called when a dimension has no quality components
        defined in metadata. It provides a fallback for simple binary
        or direct scoring scenarios.
        
        Args:
            dimension: Dimension object from metadata
            result_data: Dictionary containing raw evaluation data
            test_case: Test case object being evaluated
            
        Returns:
            Tuple of (score, empty_dict) where:
            - score: Direct dimension score (0.0 to 1.0)
            - empty_dict: Empty component breakdown
            
        Note:
            This base implementation returns 0.0 with a warning.
            Subclasses should override to provide agent-specific logic.
        """
        logger.warning(f"No direct evaluation implemented for dimension {dimension.name}")
        return 0.0, {}
    
    async def _evaluate_deterministic_component(self, component, dimension, result_data: Dict[str, Any], test_case: Any) -> float:
        """
        Evaluate a deterministic component using rule-based logic.
        
        This method is called for components with evaluation_method=DETERMINISTIC.
        It should use raw evaluation data to calculate scores using predefined
        rules and metrics.
        
        Args:
            component: QualityComponent object from metadata
            dimension: Dimension object from metadata
            result_data: Dictionary containing raw evaluation data
            test_case: Test case object being evaluated
            
        Returns:
            Component score (0.0 to 1.0)
            
        Note:
            This base implementation returns 0.0 with a warning.
            Subclasses must override to provide agent-specific deterministic
            evaluation logic such as:
            - Precision/recall calculations
            - Success rate calculations
            - Binary pass/fail determinations
        """
        logger.debug(f"      🔢 Evaluating deterministic component: {component.name}")
        logger.warning(f"No deterministic evaluation implemented for component {component.name} in dimension {dimension.name}")
        return 0.0
    
    async def _evaluate_llm_component(self, component, dimension, result_data: Dict[str, Any], test_case: Any) -> float:
        """
        Evaluate an LLM judge component using semantic analysis.
        
        This method is called for components with evaluation_method=LLM_JUDGE.
        It should use LLM-based evaluation to assess subjective qualities
        that require semantic understanding.
        
        Args:
            component: QualityComponent object from metadata
            dimension: Dimension object from metadata
            result_data: Dictionary containing raw evaluation data
            test_case: Test case object being evaluated
            
        Returns:
            Component score (0.0 to 1.0)
            
        Note:
            This base implementation returns default score with a warning.
            Subclasses must override to provide agent-specific LLM evaluation
            logic such as:
            - Context awareness assessment
            - Rationale quality evaluation
            - Comprehensiveness analysis
            - Concern identification accuracy
        """
        logger.debug(f"      🤖 Evaluating LLM component: {component.name}")
        logger.warning(f"No LLM evaluation implemented for component {component.name} in dimension {dimension.name}")
        return self._get_default_score_for_method(component.evaluation_method)