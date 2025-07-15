"""
Evaluation Rubrics

This module contains the evaluation rubric logic for scoring and aggregating
dimension evaluations into overall performance metrics.
"""

from typing import Dict, List, Any

from .dimensions import EvaluationDimension, EvaluationCriteria
from .results import DimensionEvaluation


class EvaluationRubric:
    """
    Evaluation rubric that contains the logic for scoring and aggregation.
    This is separate from metadata and can be reused across agents.
    """
    
    def __init__(self, criteria: List[EvaluationCriteria]):
        self.criteria = {c.dimension: c for c in criteria}
        self._validate_weights()
    
    def _validate_weights(self):
        """Ensure weights are properly normalized"""
        total_weight = sum(c.weight for c in self.criteria.values())
        if abs(total_weight - 1.0) > 0.01 and total_weight > 0:
            # Auto-normalize weights
            for criteria in self.criteria.values():
                criteria.weight = criteria.weight / total_weight
    
    def get_overall_target(self) -> float:
        """Calculate weighted overall target score"""
        total_weight = sum(c.weight for c in self.criteria.values())
        if total_weight == 0:
            return 0.0
        weighted_sum = sum(c.target_score * c.weight for c in self.criteria.values())
        return weighted_sum / total_weight
    
    def get_dimension_weights(self) -> Dict[str, float]:
        """Get normalized weights for each dimension"""
        return {
            dim.name: criteria.weight 
            for dim, criteria in self.criteria.items()
        }
    
    def evaluate_performance(
        self, 
        dimension_evaluations: Dict[EvaluationDimension, DimensionEvaluation]
    ) -> Dict[str, Any]:
        """
        Evaluate overall performance from individual dimension evaluations.
        This is the core rubric logic, separated from metadata.
        """
        results = {
            "dimension_scores": {},
            "overall_score": 0.0,
            "overall_target": self.get_overall_target(),
            "passed": True,
            "failed_dimensions": [],
            "weighted_scores": {}
        }
        
        total_weight = 0.0
        weighted_sum = 0.0
        
        for dimension, evaluation in dimension_evaluations.items():
            dim_name = dimension.name
            
            results["dimension_scores"][dim_name] = {
                "score": evaluation.overall_score,
                "target": evaluation.criteria.target_score,
                "passed": evaluation.passed,
                "weight": evaluation.criteria.weight,
                "weighted_score": evaluation.weighted_score,
                "measurement_method": evaluation.criteria.measurement_method,
                "component_scores": {
                    name: comp_eval.score 
                    for name, comp_eval in evaluation.component_scores.items()
                }
            }
            
            if not evaluation.passed:
                results["failed_dimensions"].append(dim_name)
                results["passed"] = False
            
            weighted_sum += evaluation.weighted_score
            total_weight += evaluation.criteria.weight
        
        results["overall_score"] = weighted_sum / total_weight if total_weight > 0 else 0.0
        results["weighted_scores"] = {
            dim.name: eval.weighted_score 
            for dim, eval in dimension_evaluations.items()
        }
        
        return results