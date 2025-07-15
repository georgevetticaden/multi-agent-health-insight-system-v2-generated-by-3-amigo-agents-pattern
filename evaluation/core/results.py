"""
Evaluation Results and Scoring

This module contains classes for evaluation results, scoring logic,
and the evaluation rubric that processes dimension evaluations.
"""

from dataclasses import dataclass
from typing import Dict, Optional, Any
from abc import ABC, abstractmethod

from .dimensions import EvaluationDimension, EvaluationCriteria, QualityComponent


@dataclass
class ComponentEvaluation:
    """Result of evaluating a single quality component"""
    component: QualityComponent
    score: float
    details: Optional[Dict[str, Any]] = None


@dataclass
class DimensionEvaluation:
    """Result of evaluating a single dimension"""
    criteria: EvaluationCriteria
    component_scores: Dict[str, ComponentEvaluation]
    overall_score: float
    passed: bool
    details: Optional[Dict[str, Any]] = None
    
    @property
    def weighted_score(self) -> float:
        """Get the weighted score for overall calculation"""
        return self.overall_score * self.criteria.weight


class DimensionEvaluator(ABC):
    """Abstract base for evaluating a single dimension"""
    
    @abstractmethod
    async def evaluate(
        self, 
        agent_response: Any,
        test_case: Any,
        **kwargs
    ) -> DimensionEvaluation:
        """Evaluate this dimension and return scores"""
        pass