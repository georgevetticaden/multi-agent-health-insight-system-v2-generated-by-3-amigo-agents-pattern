"""
CMO Agent Evaluation Criteria and Rubrics

Based on Anthropic's best practices for AI evaluation, this module defines
specific, measurable criteria for evaluating the CMO agent's performance.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Set
from enum import Enum


class EvaluationDimension(Enum):
    """Dimensions for CMO agent evaluation"""
    COMPLEXITY_CLASSIFICATION = "complexity_classification"
    SPECIALTY_SELECTION = "specialty_selection"
    ANALYSIS_QUALITY = "analysis_quality"
    TOOL_USAGE = "tool_usage"
    RESPONSE_STRUCTURE = "response_structure"


@dataclass
class EvaluationCriteria:
    """Defines success criteria for a specific evaluation dimension"""
    dimension: EvaluationDimension
    description: str
    target_score: float  # 0.0 to 1.0
    measurement_method: str
    weight: float = 1.0  # For weighted scoring


@dataclass
class ComplexityClassificationCriteria:
    """Criteria for evaluating query complexity classification"""
    
    # Mapping of query characteristics to expected complexity
    COMPLEXITY_INDICATORS = {
        "SIMPLE": {
            "indicators": [
                "single specific value lookup",
                "one data point",
                "direct fact",
                "current status only",
                "single metric"
            ],
            "max_specialists": 1,
            "max_data_points": 2
        },
        "STANDARD": {
            "indicators": [
                "comparison of 2-3 values",
                "trend over short period",
                "basic correlation",
                "multiple related metrics",
                "medication review"
            ],
            "max_specialists": 3,
            "max_data_points": 5
        },
        "COMPLEX": {
            "indicators": [
                "longitudinal analysis",
                "multiple system interaction",
                "pattern recognition",
                "risk assessment",
                "comprehensive medication analysis"
            ],
            "max_specialists": 5,
            "max_data_points": 10
        },
        "COMPREHENSIVE": {
            "indicators": [
                "full health review",
                "multi-year trends",
                "complete system analysis",
                "holistic assessment",
                "preventive care planning"
            ],
            "max_specialists": 8,
            "max_data_points": None  # Unlimited
        }
    }
    
    @classmethod
    def get_criteria(cls) -> EvaluationCriteria:
        return EvaluationCriteria(
            dimension=EvaluationDimension.COMPLEXITY_CLASSIFICATION,
            description="Accuracy of query complexity classification",
            target_score=0.90,  # 90% accuracy target
            measurement_method="F1 score against expert labels"
        )


@dataclass
class SpecialtySelectionCriteria:
    """Criteria for evaluating medical specialty selection"""
    
    # Mapping of query topics to expected specialties
    SPECIALTY_MAPPINGS = {
        "blood_sugar": ["endocrinology", "general_practice"],
        "hba1c": ["endocrinology", "laboratory_medicine"],
        "cholesterol": ["cardiology", "laboratory_medicine"],
        "blood_pressure": ["cardiology", "general_practice"],
        "medications": ["pharmacy", "general_practice"],
        "diet": ["nutrition", "preventive_medicine"],
        "exercise": ["preventive_medicine", "general_practice"],
        "weight": ["nutrition", "endocrinology", "general_practice"],
        "comprehensive_review": ["general_practice", "preventive_medicine", "data_analysis"]
    }
    
    @classmethod
    def get_criteria(cls) -> EvaluationCriteria:
        return EvaluationCriteria(
            dimension=EvaluationDimension.SPECIALTY_SELECTION,
            description="Appropriateness of specialist selection",
            target_score=0.85,  # 85% F1 score target
            measurement_method="Precision/Recall against optimal specialty sets"
        )


@dataclass
class AnalysisQualityCriteria:
    """Criteria for evaluating analysis quality"""
    
    QUALITY_CHECKLIST = {
        "data_gathering": {
            "description": "Appropriate initial data query",
            "weight": 0.2
        },
        "context_awareness": {
            "description": "Considers date/time context correctly",
            "weight": 0.15
        },
        "specialist_rationale": {
            "description": "Clear reasoning for specialist selection",
            "weight": 0.2
        },
        "comprehensive_approach": {
            "description": "Identifies all relevant aspects",
            "weight": 0.25
        },
        "concern_identification": {
            "description": "Notes potential health concerns",
            "weight": 0.2
        }
    }
    
    @classmethod
    def get_criteria(cls) -> EvaluationCriteria:
        return EvaluationCriteria(
            dimension=EvaluationDimension.ANALYSIS_QUALITY,
            description="Comprehensiveness and accuracy of analysis",
            target_score=0.80,  # 80% quality score target
            measurement_method="Weighted checklist evaluation"
        )


@dataclass
class ToolUsageCriteria:
    """Criteria for evaluating tool usage effectiveness"""
    
    TOOL_USAGE_METRICS = {
        "success_rate": {
            "description": "Percentage of successful tool calls",
            "target": 0.95,
            "weight": 0.4
        },
        "relevance": {
            "description": "Tool calls relevant to query",
            "target": 0.90,
            "weight": 0.3
        },
        "efficiency": {
            "description": "Minimal redundant calls",
            "target": 0.85,
            "weight": 0.3
        }
    }
    
    @classmethod
    def get_criteria(cls) -> EvaluationCriteria:
        return EvaluationCriteria(
            dimension=EvaluationDimension.TOOL_USAGE,
            description="Effectiveness of tool usage",
            target_score=0.90,  # 90% weighted score target
            measurement_method="Weighted metrics evaluation"
        )


@dataclass
class ResponseStructureCriteria:
    """Criteria for evaluating response structure compliance"""
    
    REQUIRED_ELEMENTS = {
        "complexity_tag": {
            "description": "Contains <complexity> tag",
            "required": True
        },
        "approach_tag": {
            "description": "Contains <approach> tag",
            "required": True
        },
        "valid_complexity": {
            "description": "Complexity value is valid enum",
            "required": True
        },
        "approach_content": {
            "description": "Approach contains required sections",
            "required": True
        }
    }
    
    @classmethod
    def get_criteria(cls) -> EvaluationCriteria:
        return EvaluationCriteria(
            dimension=EvaluationDimension.RESPONSE_STRUCTURE,
            description="Compliance with expected response format",
            target_score=0.95,  # 95% compliance target
            measurement_method="Binary checklist evaluation"
        )


class CMOEvaluationRubric:
    """Complete evaluation rubric for CMO agent"""
    
    def __init__(self):
        self.criteria = {
            EvaluationDimension.COMPLEXITY_CLASSIFICATION: ComplexityClassificationCriteria.get_criteria(),
            EvaluationDimension.SPECIALTY_SELECTION: SpecialtySelectionCriteria.get_criteria(),
            EvaluationDimension.ANALYSIS_QUALITY: AnalysisQualityCriteria.get_criteria(),
            EvaluationDimension.TOOL_USAGE: ToolUsageCriteria.get_criteria(),
            EvaluationDimension.RESPONSE_STRUCTURE: ResponseStructureCriteria.get_criteria()
        }
    
    def get_overall_target(self) -> float:
        """Calculate weighted overall target score"""
        total_weight = sum(c.weight for c in self.criteria.values())
        weighted_sum = sum(c.target_score * c.weight for c in self.criteria.values())
        return weighted_sum / total_weight
    
    def evaluate_performance(self, scores: Dict[EvaluationDimension, float]) -> Dict[str, any]:
        """Evaluate performance against criteria"""
        results = {
            "dimension_scores": {},
            "overall_score": 0.0,
            "passed": True,
            "failed_dimensions": []
        }
        
        total_weight = 0.0
        weighted_sum = 0.0
        
        for dimension, criteria in self.criteria.items():
            score = scores.get(dimension, 0.0)
            passed = score >= criteria.target_score
            
            results["dimension_scores"][dimension.value] = {
                "score": score,
                "target": criteria.target_score,
                "passed": passed,
                "weight": criteria.weight
            }
            
            if not passed:
                results["failed_dimensions"].append(dimension.value)
                results["passed"] = False
            
            weighted_sum += score * criteria.weight
            total_weight += criteria.weight
        
        results["overall_score"] = weighted_sum / total_weight if total_weight > 0 else 0.0
        results["overall_target"] = self.get_overall_target()
        
        return results