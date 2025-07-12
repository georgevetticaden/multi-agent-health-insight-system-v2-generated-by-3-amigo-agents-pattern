"""
Cardiology Specialist Agent Evaluation Criteria and Rubrics

Defines specific, measurable criteria for evaluating the Cardiology specialist agent's
performance in cardiovascular assessment and clinical decision-making.
"""

from dataclasses import dataclass
from typing import Dict, List, Set
from enum import Enum


class CardiologyDimension(Enum):
    """Dimensions for Cardiology specialist evaluation"""
    DIAGNOSTIC_ACCURACY = "diagnostic_accuracy"
    GUIDELINE_ADHERENCE = "guideline_adherence"
    RISK_ASSESSMENT = "risk_assessment"
    TREATMENT_QUALITY = "treatment_quality"
    CLINICAL_REASONING = "clinical_reasoning"


@dataclass
class EvaluationCriteria:
    """Defines success criteria for a specific evaluation dimension"""
    dimension: CardiologyDimension
    description: str
    target_score: float  # 0.0 to 1.0
    measurement_method: str
    weight: float = 1.0  # For weighted scoring


@dataclass
class DiagnosticAccuracyCriteria:
    """Criteria for evaluating diagnostic accuracy"""
    
    DIAGNOSTIC_COMPONENTS = {
        "differential_diagnosis": {
            "description": "Comprehensive differential diagnosis list",
            "weight": 0.30,
            "evaluation_points": [
                "Identifies metabolic syndrome components",
                "Recognizes dyslipidemia patterns",
                "Considers medication-related issues",
                "Identifies cardiovascular risk syndromes"
            ]
        },
        "primary_diagnosis": {
            "description": "Correct primary diagnosis identification",
            "weight": 0.35,
            "evaluation_points": [
                "Correctly identifies persistent low HDL syndrome",
                "Recognizes medication nonadherence patterns",
                "Identifies metabolic syndrome criteria",
                "Diagnoses diabetic complications"
            ]
        },
        "diagnostic_tests": {
            "description": "Appropriate diagnostic test selection",
            "weight": 0.20,
            "evaluation_points": [
                "Orders complete lipid panels at appropriate intervals",
                "Includes apolipoprotein and genetic testing when indicated",
                "Monitors kidney function and proteinuria",
                "Assesses glycemic control markers"
            ]
        },
        "urgency_assessment": {
            "description": "Correct urgency level determination",
            "weight": 0.15,
            "evaluation_points": [
                "Recognizes urgent need for medication optimization",
                "Identifies high-risk metabolic patterns",
                "Prioritizes cardiovascular risk reduction",
                "Appropriate follow-up timing"
            ]
        }
    }
    
    @classmethod
    def get_criteria(cls) -> EvaluationCriteria:
        return EvaluationCriteria(
            dimension=CardiologyDimension.DIAGNOSTIC_ACCURACY,
            description="Accuracy of cardiovascular diagnosis and workup",
            target_score=0.85,  # 85% accuracy target
            measurement_method="Weighted component scoring with clinical validation",
            weight=0.25
        )


@dataclass
class GuidelineAdherenceCriteria:
    """Criteria for evaluating adherence to clinical guidelines"""
    
    GUIDELINE_CATEGORIES = {
        "acc_aha": "ACC/AHA Guidelines",
        "esc": "European Society of Cardiology",
        "nice": "NICE Guidelines",
        "local_protocols": "Institution-specific protocols"
    }
    
    ADHERENCE_CHECKLIST = {
        "guideline_citation": {
            "description": "References appropriate guidelines",
            "weight": 0.20
        },
        "recommendation_alignment": {
            "description": "Recommendations align with guidelines",
            "weight": 0.40
        },
        "contraindication_check": {
            "description": "Identifies contraindications per guidelines",
            "weight": 0.25
        },
        "evidence_level": {
            "description": "Notes evidence level for recommendations",
            "weight": 0.15
        }
    }
    
    @classmethod
    def get_criteria(cls) -> EvaluationCriteria:
        return EvaluationCriteria(
            dimension=CardiologyDimension.GUIDELINE_ADHERENCE,
            description="Adherence to established cardiovascular guidelines",
            target_score=0.90,  # 90% adherence target
            measurement_method="Guideline compliance checklist",
            weight=0.20
        )


@dataclass
class RiskAssessmentCriteria:
    """Criteria for cardiovascular risk assessment"""
    
    RISK_ASSESSMENT_TOOLS = {
        "ascvd_score": "10-year ASCVD risk calculation",
        "metabolic_syndrome_criteria": "ATP III metabolic syndrome assessment",
        "diabetes_risk_score": "Diabetes progression risk",
        "ckd_progression": "Kidney disease progression risk",
        "statin_benefit": "Statin benefit assessment"
    }
    
    RISK_COMPONENTS = {
        "tool_selection": {
            "description": "Appropriate risk calculator selection",
            "weight": 0.25,
            "evaluation_points": [
                "Uses ASCVD calculator for lipid management decisions",
                "Applies metabolic syndrome criteria",
                "Assesses diabetes progression risk",
                "Evaluates kidney disease impact"
            ]
        },
        "factor_identification": {
            "description": "Complete risk factor identification",
            "weight": 0.30,
            "evaluation_points": [
                "Identifies persistent low HDL as major risk",
                "Recognizes prediabetes progression",
                "Notes weight gain impact",
                "Identifies medication adherence issues"
            ]
        },
        "score_calculation": {
            "description": "Accurate risk score calculation",
            "weight": 0.25,
            "evaluation_points": [
                "Calculates 10-year ASCVD risk",
                "Determines metabolic syndrome presence",
                "Assesses composite cardiovascular risk",
                "Stratifies urgency appropriately"
            ]
        },
        "risk_communication": {
            "description": "Clear risk communication to patient",
            "weight": 0.20,
            "evaluation_points": [
                "Explains HDL importance clearly",
                "Communicates urgency of intervention",
                "Provides specific risk numbers",
                "Offers actionable steps"
            ]
        }
    }
    
    @classmethod
    def get_criteria(cls) -> EvaluationCriteria:
        return EvaluationCriteria(
            dimension=CardiologyDimension.RISK_ASSESSMENT,
            description="Quality of cardiovascular risk assessment",
            target_score=0.85,  # 85% quality target
            measurement_method="Risk assessment component evaluation",
            weight=0.20
        )


@dataclass
class TreatmentQualityCriteria:
    """Criteria for treatment recommendation quality"""
    
    TREATMENT_CATEGORIES = {
        "pharmacological": {
            "description": "Medication selection and dosing",
            "components": ["drug_choice", "dosing", "interactions", "monitoring"],
            "real_world_focus": [
                "Statin intensification for inadequate response",
                "HDL-raising strategies",
                "Medication adherence interventions",
                "Metabolic syndrome management"
            ]
        },
        "adherence_strategies": {
            "description": "Medication adherence improvement",
            "components": ["barriers", "solutions", "monitoring", "support"],
            "real_world_focus": [
                "Automatic refill programs",
                "90-day prescriptions",
                "Side effect management",
                "Cost considerations"
            ]
        },
        "lifestyle": {
            "description": "Lifestyle modification counseling",
            "components": ["diet", "exercise", "weight", "monitoring"],
            "real_world_focus": [
                "150 minutes weekly exercise",
                "Mediterranean diet for HDL",
                "Weight loss targets (5-10%)",
                "Diabetes prevention program"
            ]
        }
    }
    
    QUALITY_METRICS = {
        "evidence_based": {
            "description": "Recommendations based on evidence",
            "weight": 0.30
        },
        "individualized": {
            "description": "Tailored to patient specifics",
            "weight": 0.25
        },
        "safety_considered": {
            "description": "Safety and contraindications addressed",
            "weight": 0.25
        },
        "follow_up_plan": {
            "description": "Clear follow-up recommendations",
            "weight": 0.20
        }
    }
    
    @classmethod
    def get_criteria(cls) -> EvaluationCriteria:
        return EvaluationCriteria(
            dimension=CardiologyDimension.TREATMENT_QUALITY,
            description="Quality of treatment recommendations",
            target_score=0.85,  # 85% quality target
            measurement_method="Treatment quality checklist evaluation",
            weight=0.20
        )


@dataclass
class ClinicalReasoningCriteria:
    """Criteria for clinical reasoning quality"""
    
    REASONING_COMPONENTS = {
        "pathophysiology": {
            "description": "Understanding of disease mechanisms",
            "weight": 0.25
        },
        "data_synthesis": {
            "description": "Integration of clinical data",
            "weight": 0.30
        },
        "clinical_judgment": {
            "description": "Sound clinical decision-making",
            "weight": 0.25
        },
        "uncertainty_handling": {
            "description": "Appropriate handling of uncertainty",
            "weight": 0.20
        }
    }
    
    @classmethod
    def get_criteria(cls) -> EvaluationCriteria:
        return EvaluationCriteria(
            dimension=CardiologyDimension.CLINICAL_REASONING,
            description="Quality of clinical reasoning and decision-making",
            target_score=0.80,  # 80% quality target
            measurement_method="Clinical reasoning component analysis",
            weight=0.15
        )


class CardiologyEvaluationRubric:
    """Complete evaluation rubric for Cardiology specialist agent"""
    
    # Direct access to target values
    DIAGNOSTIC_ACCURACY_TARGET = 0.85
    GUIDELINE_ADHERENCE_TARGET = 0.90
    RISK_ASSESSMENT_TARGET = 0.85
    TREATMENT_QUALITY_TARGET = 0.85
    CLINICAL_REASONING_TARGET = 0.80
    
    def __init__(self):
        self.criteria = {
            CardiologyDimension.DIAGNOSTIC_ACCURACY: DiagnosticAccuracyCriteria.get_criteria(),
            CardiologyDimension.GUIDELINE_ADHERENCE: GuidelineAdherenceCriteria.get_criteria(),
            CardiologyDimension.RISK_ASSESSMENT: RiskAssessmentCriteria.get_criteria(),
            CardiologyDimension.TREATMENT_QUALITY: TreatmentQualityCriteria.get_criteria(),
            CardiologyDimension.CLINICAL_REASONING: ClinicalReasoningCriteria.get_criteria()
        }
    
    def get_overall_target(self) -> float:
        """Calculate weighted overall target score"""
        total_weight = sum(c.weight for c in self.criteria.values())
        weighted_sum = sum(c.target_score * c.weight for c in self.criteria.values())
        return weighted_sum / total_weight
    
    def evaluate_performance(self, scores: Dict[CardiologyDimension, float]) -> Dict[str, any]:
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