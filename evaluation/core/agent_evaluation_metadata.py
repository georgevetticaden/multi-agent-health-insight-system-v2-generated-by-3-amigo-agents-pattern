"""
Agent Evaluation Metadata

This module provides the bridge between agent metadata and evaluation criteria.
It combines agent descriptive metadata with evaluation-specific information.
"""

from dataclasses import dataclass
from typing import Dict, List, Any, Optional

from services.agents.metadata.core import AgentMetadata
from .dimensions import EvaluationDimension, EvaluationCriteria, QualityComponent


@dataclass
class AgentEvaluationMetadata:
    """
    Complete metadata for agent evaluation, combining agent metadata with
    evaluation-specific information.
    """
    # Core agent metadata
    agent_metadata: AgentMetadata
    
    # Evaluation-specific additions
    evaluation_criteria: List[EvaluationCriteria]
    quality_components: Dict[EvaluationDimension, List[QualityComponent]]
    
    @property
    def agent_type(self) -> str:
        return self.agent_metadata.agent_type
    
    @property
    def agent_class(self) -> str:
        return self.agent_metadata.agent_class
    
    @property
    def description(self) -> str:
        return self.agent_metadata.description
    
    @property
    def prompts(self):
        """Return basic prompt metadata from agent"""
        return self.agent_metadata.prompts
    
    @property
    def config(self) -> Dict[str, Any]:
        return self.agent_metadata.config
    
    def get_criteria_by_dimension(self, dimension: EvaluationDimension) -> Optional[EvaluationCriteria]:
        """Get criteria for a specific dimension"""
        for criteria in self.evaluation_criteria:
            if criteria.dimension == dimension:
                return criteria
        return None
    
    def get_quality_components(self, dimension: EvaluationDimension) -> List[QualityComponent]:
        """Get quality components for a dimension"""
        return self.quality_components.get(dimension, [])
    
    def get_dimensions(self) -> List[EvaluationDimension]:
        """Get all evaluation dimensions for this agent"""
        return [criteria.dimension for criteria in self.evaluation_criteria]
    
    def to_report_data(self) -> Dict[str, Any]:
        """Convert to report-friendly format"""
        base_data = self.agent_metadata.to_dict()
        
        # Add evaluation-specific data
        base_data["evaluation_criteria"] = [
            {
                "dimension": c.dimension.name,
                "category": c.dimension.category,
                "description": c.description,
                "target_score": c.target_score,
                "weight": c.weight,
                "evaluation_method": c.evaluation_method.value if hasattr(c.evaluation_method, 'value') else c.evaluation_method
            }
            for c in self.evaluation_criteria
        ]
        
        # Group dimensions by category
        dimensions_by_category = {}
        for criteria in self.evaluation_criteria:
            category = criteria.dimension.category
            if category not in dimensions_by_category:
                dimensions_by_category[category] = []
            dimensions_by_category[category].append(criteria.dimension.name)
        
        base_data["dimensions_by_category"] = dimensions_by_category
        
        return base_data