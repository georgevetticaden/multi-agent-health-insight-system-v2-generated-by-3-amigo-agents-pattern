"""
Evaluation Dimensions Core Types

This module provides the core dimension types and registry system.
Agent-specific dimensions are registered in evaluation/agents/*.
"""

from dataclasses import dataclass
from typing import Dict, List, Set, Optional
from enum import Enum


@dataclass
class EvaluationDimension:
    """Represents an evaluation dimension with metadata"""
    name: str
    category: str  # "common", "orchestration", "medical", "technical", etc.
    description: str
    
    def __hash__(self):
        return hash(self.name)
    
    def __eq__(self, other):
        if isinstance(other, EvaluationDimension):
            return self.name == other.name
        elif isinstance(other, str):
            return self.name == other
        return False
    
    def __str__(self):
        return self.name


class DimensionCategory(Enum):
    """Categories of evaluation dimensions"""
    COMMON = "common"  # Shared across all agents
    ORCHESTRATION = "orchestration"  # CMO-specific
    MEDICAL = "medical"  # Medical specialist-specific
    TECHNICAL = "technical"  # Technical execution
    VISUALIZATION = "visualization"  # Visualization agent-specific


class EvaluationMethod(Enum):
    """Methods for evaluating components and dimensions"""
    DETERMINISTIC = "deterministic"  # Rule-based, algorithmic evaluation
    LLM_JUDGE = "llm_judge"  # LLM-based semantic evaluation
    HYBRID = "hybrid"  # Mix of deterministic and LLM judge (at dimension level)


class DimensionRegistry:
    """Registry for evaluation dimensions"""
    
    def __init__(self):
        self._dimensions: Dict[str, EvaluationDimension] = {}
        self._register_common_dimensions()
    
    def _register_common_dimensions(self):
        """Register dimensions common to all agents"""
        # Common analysis dimensions
        self.register(
            "analysis_quality",
            DimensionCategory.COMMON,
            "Overall quality and comprehensiveness of analysis"
        )
        self.register(
            "tool_usage",
            DimensionCategory.COMMON,
            "Effectiveness and appropriateness of tool usage"
        )
        self.register(
            "response_structure",
            DimensionCategory.COMMON,
            "Compliance with expected response format and structure"
        )
        self.register(
            "error_handling",
            DimensionCategory.COMMON,
            "Graceful handling of errors and edge cases"
        )
    
    def register(self, name: str, category: DimensionCategory, description: str) -> EvaluationDimension:
        """Register a new dimension"""
        dimension = EvaluationDimension(name, category.value, description)
        self._dimensions[name] = dimension
        return dimension
    
    def get(self, name: str) -> Optional[EvaluationDimension]:
        """Get a dimension by name"""
        return self._dimensions.get(name)
    
    def get_or_create(self, name: str, category: DimensionCategory, description: str) -> EvaluationDimension:
        """Get existing dimension or create new one"""
        if name in self._dimensions:
            return self._dimensions[name]
        return self.register(name, category, description)
    
    def get_by_category(self, category: DimensionCategory) -> List[EvaluationDimension]:
        """Get all dimensions in a category"""
        return [d for d in self._dimensions.values() if d.category == category.value]
    
    def get_common_dimensions(self) -> List[EvaluationDimension]:
        """Get dimensions common to all agents"""
        return self.get_by_category(DimensionCategory.COMMON)
    
    def get_all_dimensions(self) -> List[EvaluationDimension]:
        """Get all registered dimensions"""
        return list(self._dimensions.values())
    
    def exists(self, name: str) -> bool:
        """Check if a dimension is registered"""
        return name in self._dimensions


# Global dimension registry - singleton instance
dimension_registry = DimensionRegistry()


@dataclass
class QualityComponent:
    """Defines a quality component within an evaluation dimension"""
    name: str
    description: str
    weight: float  # Weight within its dimension (should sum to 1.0)
    evaluation_method: EvaluationMethod  # Method for evaluating this component


@dataclass
class EvaluationCriteria:
    """Defines success criteria for a single evaluation dimension"""
    dimension: EvaluationDimension  # Now uses the flexible dimension type
    description: str
    target_score: float  # Expected minimum score (0.0 to 1.0)
    evaluation_method: EvaluationMethod  # Method for evaluating this dimension
    evaluation_description: str
    weight: float = 1.0  # Weight in overall evaluation
    
    def is_passing(self, score: float) -> bool:
        """Simple check if a score meets this criterion"""
        return score >= self.target_score


__all__ = [
    'EvaluationDimension',
    'DimensionCategory',
    'EvaluationMethod',
    'DimensionRegistry',
    'dimension_registry',
    'QualityComponent',
    'EvaluationCriteria'
]