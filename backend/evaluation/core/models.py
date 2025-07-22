from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set
from enum import Enum
from datetime import datetime

from services.agents.metadata.core import AgentMetadata


@dataclass
class QualityComponent:
    """Represents a component of quality evaluation"""
    name: str
    description: str
    weight: float
    evaluation_method: 'EvaluationMethod'
    
    def __post_init__(self):
        if not 0 <= self.weight <= 1:
            raise ValueError(f"Weight must be between 0 and 1, got {self.weight}")


@dataclass
class EvaluationCriteria:
    """Defines evaluation criteria for a specific dimension"""
    dimension: 'EvaluationDimension'
    description: str
    target_score: float
    weight: float
    evaluation_method: 'EvaluationMethod'
    evaluation_description: str
    
    def __post_init__(self):
        if not 0 <= self.weight <= 1:
            raise ValueError(f"Weight must be between 0 and 1, got {self.weight}")
        if not 0 <= self.target_score <= 1:
            raise ValueError(f"Target score must be between 0 and 1, got {self.target_score}")


@dataclass
class AgentEvaluationMetadata:
    """Complete evaluation metadata for an agent"""
    agent_metadata: AgentMetadata
    evaluation_criteria: List[EvaluationCriteria]
    quality_components: Dict['EvaluationDimension', List[QualityComponent]] = field(default_factory=dict)
    
    def __post_init__(self):
        # Validate weights sum to 1.0
        total_weight = sum(c.weight for c in self.evaluation_criteria)
        if abs(total_weight - 1.0) > 0.01:  # Allow small floating point errors
            raise ValueError(f"Evaluation criteria weights must sum to 1.0, got {total_weight}")


@dataclass
class TestCase:
    """Represents a test case for evaluation"""
    id: str
    query: str
    expected_complexity: str
    actual_complexity: Optional[str] = None
    expected_specialties: Set[str] = field(default_factory=set)
    actual_specialties: Set[str] = field(default_factory=set)
    key_data_points: List[str] = field(default_factory=list)
    category: str = "general"
    notes: str = ""
    based_on_real_query: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    trace_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "query": self.query,
            "expected_complexity": self.expected_complexity,
            "actual_complexity": self.actual_complexity,
            "expected_specialties": list(self.expected_specialties),
            "actual_specialties": list(self.actual_specialties),
            "key_data_points": self.key_data_points,
            "category": self.category,
            "notes": self.notes,
            "based_on_real_query": self.based_on_real_query,
            "created_at": self.created_at.isoformat(),
            "trace_id": self.trace_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TestCase':
        """Create from dictionary"""
        data = data.copy()
        data['expected_specialties'] = set(data.get('expected_specialties', []))
        data['actual_specialties'] = set(data.get('actual_specialties', []))
        if 'created_at' in data and isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        return cls(**data)


@dataclass
class DimensionResult:
    """Result for a single evaluation dimension"""
    dimension_name: str
    score: float
    max_score: float = 1.0
    components: Dict[str, float] = field(default_factory=dict)
    details: Dict[str, Any] = field(default_factory=dict)
    evaluation_method: str = ""
    
    @property
    def normalized_score(self) -> float:
        """Get score normalized to 0-1 range"""
        return self.score / self.max_score if self.max_score > 0 else 0


@dataclass
class EvaluationResult:
    """Complete evaluation result for a test case"""
    test_case_id: str
    agent_type: str
    overall_score: float
    dimension_results: Dict[str, DimensionResult]
    execution_time_ms: float
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "test_case_id": self.test_case_id,
            "agent_type": self.agent_type,
            "overall_score": self.overall_score,
            "dimension_results": {
                name: {
                    "dimension_name": result.dimension_name,
                    "score": result.score,
                    "max_score": result.max_score,
                    "normalized_score": result.normalized_score,
                    "components": result.components,
                    "details": result.details,
                    "evaluation_method": result.evaluation_method
                }
                for name, result in self.dimension_results.items()
            },
            "execution_time_ms": self.execution_time_ms,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }