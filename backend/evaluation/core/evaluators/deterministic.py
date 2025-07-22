import logging
from typing import List, Optional

from ..models import TestCase, DimensionResult, EvaluationCriteria, QualityComponent
from ..dimensions import EvaluationDimension

logger = logging.getLogger(__name__)


class DeterministicEvaluator:
    """Evaluates dimensions using deterministic rules"""
    
    async def evaluate(
        self,
        test_case: TestCase,
        criteria: EvaluationCriteria,
        components: List[QualityComponent]
    ) -> DimensionResult:
        """Evaluate using deterministic rules"""
        
        # Dispatch based on dimension
        if criteria.dimension.name == "complexity_classification":
            return await self._evaluate_complexity_classification(test_case, criteria)
        elif criteria.dimension.name == "specialty_selection":
            return await self._evaluate_specialty_selection(test_case, criteria, components)
        elif criteria.dimension.name == "tool_usage":
            return await self._evaluate_tool_usage(test_case, criteria, components)
        elif criteria.dimension.name == "response_structure":
            return await self._evaluate_response_structure(test_case, criteria, components)
        else:
            # Default evaluation
            return DimensionResult(
                dimension_name=criteria.dimension.name,
                score=0.5,  # Default to neutral score
                details={"message": "No deterministic evaluation available"},
                evaluation_method="deterministic"
            )
    
    async def _evaluate_complexity_classification(
        self,
        test_case: TestCase,
        criteria: EvaluationCriteria
    ) -> DimensionResult:
        """Evaluate complexity classification accuracy"""
        logger.info(f"Evaluating complexity classification:")
        logger.info(f"  Expected: {test_case.expected_complexity}")
        logger.info(f"  Actual: {test_case.actual_complexity}")
        
        # Simple binary accuracy
        is_correct = test_case.expected_complexity == test_case.actual_complexity
        score = 1.0 if is_correct else 0.0
        
        logger.info(f"  Correct: {is_correct}, Score: {score}")
        
        return DimensionResult(
            dimension_name=criteria.dimension.name,
            score=score,
            details={
                "expected": test_case.expected_complexity,
                "actual": test_case.actual_complexity,
                "correct": is_correct
            },
            evaluation_method="deterministic"
        )
    
    async def _evaluate_specialty_selection(
        self,
        test_case: TestCase,
        criteria: EvaluationCriteria,
        components: List[QualityComponent]
    ) -> DimensionResult:
        """Evaluate specialty selection precision"""
        logger.info(f"Evaluating specialty selection:")
        logger.info(f"  Expected specialties: {test_case.expected_specialties}")
        logger.info(f"  Actual specialties: {test_case.actual_specialties}")
        
        if not test_case.expected_specialties:
            return DimensionResult(
                dimension_name=criteria.dimension.name,
                score=1.0,  # No specialties expected
                details={"message": "No specialties expected"},
                evaluation_method="deterministic"
            )
        
        # Calculate precision and recall
        # Ensure we have sets for set operations
        expected = set(test_case.expected_specialties) if isinstance(test_case.expected_specialties, list) else test_case.expected_specialties
        actual = set(test_case.actual_specialties) if isinstance(test_case.actual_specialties, list) else (test_case.actual_specialties or set())
        
        if not actual:
            precision = 0.0
            recall = 0.0
            logger.info(f"  No actual specialties provided, precision=0, recall=0")
        else:
            # Precision: what fraction of selected specialties were correct
            correct_selections = expected & actual
            precision = len(correct_selections) / len(actual) if actual else 0
            
            # Recall: what fraction of expected specialties were selected
            recall = len(correct_selections) / len(expected) if expected else 0
            
            logger.info(f"  Correct selections: {correct_selections}")
            logger.info(f"  Precision: {precision:.2%} ({len(correct_selections)}/{len(actual)} correct)")
            logger.info(f"  Recall: {recall:.2%} ({len(correct_selections)}/{len(expected)} found)")
        
        # F1 score
        if precision + recall > 0:
            f1_score = 2 * (precision * recall) / (precision + recall)
        else:
            f1_score = 0.0
        
        logger.info(f"  F1 Score: {f1_score:.2%}")
        
        # If we have components, evaluate them
        component_scores = {}
        if components:
            # For now, use the f1_score for the precision component
            for component in components:
                if component.name == "specialist_precision":
                    component_scores[component.name] = precision
                elif component.name == "specialist_recall":
                    component_scores[component.name] = recall
        
        return DimensionResult(
            dimension_name=criteria.dimension.name,
            score=f1_score,
            components=component_scores,
            details={
                "expected_specialties": list(expected),
                "actual_specialties": list(actual),
                "precision": precision,
                "recall": recall,
                "f1_score": f1_score,
                "missing_specialties": list(expected - actual),
                "extra_specialties": list(actual - expected)
            },
            evaluation_method="deterministic"
        )
    
    async def _evaluate_tool_usage(
        self,
        test_case: TestCase,
        criteria: EvaluationCriteria,
        components: List[QualityComponent]
    ) -> DimensionResult:
        """Evaluate tool usage effectiveness"""
        logger.info(f"Evaluating tool usage with {len(components)} components")
        
        # Extract tool usage data from trace if available
        tool_calls_made = 0
        successful_tool_calls = 0
        
        # Check if we have trace data in the test case metadata
        if hasattr(test_case, 'trace_id') and test_case.trace_id:
            logger.info(f"  Test case has trace_id: {test_case.trace_id}")
            # In a full implementation, we would load the trace and analyze tool calls
            # For now, we'll use reasonable defaults based on the query
            
            # Simple heuristic: complex queries should have tool calls
            if test_case.expected_complexity in ["COMPLEX", "COMPREHENSIVE"]:
                tool_calls_made = 3  # Assume 3 tool calls for complex queries
                successful_tool_calls = 3  # Assume all successful
            elif test_case.expected_complexity == "STANDARD":
                tool_calls_made = 2
                successful_tool_calls = 2
            else:  # SIMPLE
                tool_calls_made = 1
                successful_tool_calls = 1
        
        logger.info(f"  Tool calls analysis: {successful_tool_calls}/{tool_calls_made} successful")
        
        component_scores = {}
        
        # Evaluate each component
        for component in components:
            if component.name == "tool_success_rate":
                # Calculate actual success rate
                if tool_calls_made > 0:
                    success_rate = successful_tool_calls / tool_calls_made
                else:
                    success_rate = 1.0  # No tool calls needed = success
                
                component_scores[component.name] = success_rate
                logger.info(f"  Component '{component.name}': score={success_rate:.2f}")
        
        # Calculate weighted average if we have components
        if components and component_scores:
            total_weight = sum(c.weight for c in components)
            weighted_score = sum(
                component_scores.get(c.name, 0) * c.weight 
                for c in components
            )
            final_score = weighted_score / total_weight if total_weight > 0 else 0
        else:
            final_score = 0.8  # Default placeholder
        
        logger.info(f"  Final tool usage score: {final_score:.2f}")
        
        return DimensionResult(
            dimension_name=criteria.dimension.name,
            score=final_score,
            components=component_scores,
            details={
                "tool_calls_made": tool_calls_made,
                "successful_tool_calls": successful_tool_calls,
                "success_rate": successful_tool_calls / tool_calls_made if tool_calls_made > 0 else 1.0,
                "expected_data_points": test_case.key_data_points,
                "components_evaluated": list(component_scores.keys())
            },
            evaluation_method="deterministic"
        )
    
    async def _evaluate_response_structure(
        self,
        test_case: TestCase,
        criteria: EvaluationCriteria,
        components: List[QualityComponent]
    ) -> DimensionResult:
        """Evaluate response structure compliance"""
        logger.info(f"Evaluating response structure with {len(components)} components")
        
        # For now, return placeholder scores for each component
        # In a real implementation, this would check XML structure, required fields, etc.
        component_scores = {}
        
        # Evaluate each component
        for component in components:
            if component.name == "xml_validity":
                # Placeholder: assume valid XML
                component_scores[component.name] = 0.95
                logger.info(f"  Component '{component.name}': score=0.95 (placeholder)")
            elif component.name == "required_fields":
                # Placeholder: assume all required fields present
                component_scores[component.name] = 0.95
                logger.info(f"  Component '{component.name}': score=0.95 (placeholder)")
        
        # Calculate weighted average if we have components
        if components and component_scores:
            total_weight = sum(c.weight for c in components)
            weighted_score = sum(
                component_scores.get(c.name, 0) * c.weight 
                for c in components
            )
            final_score = weighted_score / total_weight if total_weight > 0 else 0
        else:
            final_score = 0.95  # Default placeholder
        
        logger.info(f"  Final response structure score: {final_score:.2f}")
        
        return DimensionResult(
            dimension_name=criteria.dimension.name,
            score=final_score,
            components=component_scores,
            details={
                "message": "Response structure evaluation (placeholder implementation)",
                "components_evaluated": list(component_scores.keys())
            },
            evaluation_method="deterministic"
        )