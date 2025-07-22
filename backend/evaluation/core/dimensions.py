from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional


class EvaluationMethod(Enum):
    """Methods for evaluating dimensions"""
    DETERMINISTIC = "deterministic"  # Rule-based, exact matching
    LLM_JUDGE = "llm_judge"          # LLM-based evaluation
    HYBRID = "hybrid"                # Combination of both


@dataclass
class EvaluationDimension:
    """Represents a dimension of evaluation"""
    name: str
    description: str
    category: str  # e.g., "accuracy", "quality", "compliance"
    
    def __hash__(self):
        return hash(self.name)
    
    def __eq__(self, other):
        if isinstance(other, EvaluationDimension):
            return self.name == other.name
        return False


class DimensionRegistry:
    """Registry for evaluation dimensions"""
    
    def __init__(self):
        self._dimensions: Dict[str, EvaluationDimension] = {}
        self._register_common_dimensions()
    
    def _register_common_dimensions(self):
        """Register common dimensions used across agents"""
        common_dimensions = [
            EvaluationDimension(
                name="analysis_quality",
                description="Quality and comprehensiveness of analysis",
                category="quality"
            ),
            EvaluationDimension(
                name="tool_usage",
                description="Effectiveness of tool usage",
                category="accuracy"
            ),
            EvaluationDimension(
                name="response_structure",
                description="Compliance with expected response format",
                category="compliance"
            ),
            EvaluationDimension(
                name="completeness",
                description="Completeness of the response",
                category="quality"
            ),
            EvaluationDimension(
                name="accuracy",
                description="Factual accuracy of the response",
                category="accuracy"
            )
        ]
        
        for dim in common_dimensions:
            self.register(dim)
    
    def register(self, dimension: EvaluationDimension):
        """Register a new dimension"""
        self._dimensions[dimension.name] = dimension
    
    def get(self, name: str) -> Optional[EvaluationDimension]:
        """Get a dimension by name"""
        return self._dimensions.get(name)
    
    def all(self) -> Dict[str, EvaluationDimension]:
        """Get all registered dimensions"""
        return self._dimensions.copy()


# Global dimension registry
dimension_registry = DimensionRegistry()