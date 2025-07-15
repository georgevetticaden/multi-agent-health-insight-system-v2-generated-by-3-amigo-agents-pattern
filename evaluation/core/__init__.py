"""
Evaluation Core Package

Provides core evaluation types including dimensions, results, and rubrics.
"""

from .dimensions import (
    EvaluationDimension,
    DimensionCategory,
    DimensionRegistry,
    dimension_registry,
    QualityComponent,
    EvaluationCriteria
)

from .results import (
    ComponentEvaluation,
    DimensionEvaluation,
    DimensionEvaluator
)

from .rubrics import EvaluationRubric

from .agent_evaluation_metadata import AgentEvaluationMetadata

__all__ = [
    # Dimensions
    'EvaluationDimension',
    'DimensionCategory',
    'DimensionRegistry',
    'dimension_registry',
    'QualityComponent',
    'EvaluationCriteria',
    # Results
    'ComponentEvaluation',
    'DimensionEvaluation',
    'DimensionEvaluator',
    # Rubrics
    'EvaluationRubric',
    # Agent Evaluation Metadata
    'AgentEvaluationMetadata'
]