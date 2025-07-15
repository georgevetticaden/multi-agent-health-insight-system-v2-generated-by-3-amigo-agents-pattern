"""
Medical Specialist Agent Test Cases

Comprehensive test cases for evaluating all medical specialist agents including
cardiology, endocrinology, laboratory medicine, pharmacy, nutrition, and preventive medicine.
"""

from dataclasses import dataclass, field
from typing import List, Set, Dict, Optional, Any
from enum import Enum
from services.agents.models import MedicalSpecialty


class DiagnosticConfidence(Enum):
    """Confidence levels for diagnostic assessments"""
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    DEFINITIVE = "definitive"


@dataclass
class SpecialistTestCase:
    """Generalized test case for any medical specialist evaluation"""
    id: str
    specialty: MedicalSpecialty
    query: str
    patient_context: Dict[str, Any] = field(default_factory=dict)
    expected_findings: Set[str] = field(default_factory=set)  # General findings expected
    expected_recommendations: Set[str] = field(default_factory=set)
    expected_safety_concerns: Set[str] = field(default_factory=set)
    category: str = "general_assessment"
    urgency_level: str = "routine"  # emergency, urgent, routine
    description: str = ""
    based_on_real_case: bool = False
    notes: Optional[str] = None
    
    # Specialty-specific expectations (flexible dictionary)
    specialty_specific_expectations: Dict[str, Any] = field(default_factory=dict)
    
    
    def __post_init__(self):
        """Validate test case fields"""
        valid_urgencies = {"emergency", "urgent", "routine"}
        if self.urgency_level not in valid_urgencies:
            raise ValueError(f"Invalid urgency level: {self.urgency_level}")




class SpecialistTestCases:
    """Comprehensive test cases for all medical specialist evaluations"""
    
    # ===== CARDIOLOGY TEST CASES =====
    @staticmethod
    def get_cardiology_lipid_trend_cases() -> List[SpecialistTestCase]:
        """Test cases for lipid trend analysis based on real-world query 1"""
        return [
            SpecialistTestCase(
                id="cardio_lipid_001",
                specialty=MedicalSpecialty.CARDIOLOGY,
                query="Analyze cholesterol trends over 12 years including HDL, LDL, Total Cholesterol, and Triglycerides",
                patient_context={
                    "historical_data": {
                        "2013": {"hdl": 25, "ldl": 100, "total": 186, "triglycerides": 426},
                        "2020": {"hdl": 40, "ldl": 85, "total": 145, "triglycerides": 95},
                        "2025": {"hdl": 42, "ldl": 122, "total": None, "triglycerides": 153}
                    },
                    "current_medications": ["rosuvastatin 5mg", "ezetimibe 10mg"],
                    "treatment_history": "Multiple statin switches over years"
                },
                expected_findings={
                    "persistent_low_hdl_syndrome",
                    "mixed_dyslipidemia",
                    "metabolic_syndrome",
                    "possible_familial_lipid_disorder"
                },
                expected_safety_concerns={
                    "cardiovascular_risk"
                },
                expected_recommendations={
                    "increase_statin_intensity",
                    "hdl_raising_strategies",
                    "lifestyle_modification",
                    "consider_pcsk9_inhibitor"
                },
                specialty_specific_expectations={
                    "tests": {
                        "complete_lipid_panel",
                        "apolipoprotein_b",
                        "lipoprotein_a",
                        "genetic_lipid_testing"
                    },
                    "risk_factors": {
                        "persistently_low_hdl",
                        "historical_severe_hypertriglyceridemia",
                        "inadequate_statin_response",
                        "metabolic_dysfunction"
                    },
                    "medications": {
                        "rosuvastatin_20_40mg",
                        "ezetimibe_continuation",
                        "consider_fenofibrate",
                        "omega_3_fatty_acids"
                    },
                    "monitoring": {
                        "lipid_panel_every_3_months",
                        "liver_function_monitoring",
                        "ck_if_symptoms"
                    },
                    "confidence": "HIGH",
                    "clinical_guidelines": ["2018 AHA/ACC Cholesterol Guidelines", "NLA Recommendations"],
                    "focus_areas": ["lipid_management", "risk_stratification"]
                },
                category="lipid_management",
                urgency_level="urgent",
                description="Long-term lipid management with persistent HDL deficiency",
                based_on_real_case=True,
                notes="HDL persistently below 40 mg/dL for 12 years; Triglycerides dropped from 426 to 95 mg/dL; Recent triglyceride increase to 153 mg/dL; Missing total cholesterol measurements since 2022"
            )
        ]
    
    @staticmethod
    def get_cardiology_medication_adherence_cases() -> List[SpecialistTestCase]:
        """Test cases for medication adherence and correlation analysis"""
        return [
            SpecialistTestCase(
                id="cardio_adherence_001",
                specialty=MedicalSpecialty.CARDIOLOGY,
                query="Analyze cholesterol medication adherence patterns and correlation with lab results",
                patient_context={
                    "medication_history": [
                        {"drug": "rosuvastatin", "doses": ["5mg", "10mg", "20mg"], "switches": "multiple"},
                        {"drug": "atorvastatin", "doses": ["10mg"], "switches": "discontinued"},
                        {"drug": "ezetimibe", "doses": ["10mg"], "added": "late 2024"}
                    ],
                    "lab_patterns": {
                        "best_control": "mid-2021 to mid-2022 (LDL 54-66)",
                        "current": {"ldl": 85, "hdl": 33, "triglycerides": 153},
                        "gaps": "up to 658 days between tests"
                    }
                },
                expected_findings={
                    "medication_nonadherence",
                    "statin_inadequate_response",
                    "metabolic_syndrome"
                },
                expected_recommendations={
                    "medication_reconciliation",
                    "adherence_strategies",
                    "regular_monitoring_schedule"
                },
                category="medication_management",
                urgency_level="routine",
                description="Medication adherence assessment with lab correlation",
                based_on_real_case=True
            )
        ]
    
    # ===== ENDOCRINOLOGY TEST CASES =====
    @staticmethod
    def get_endocrinology_diabetes_cases() -> List[SpecialistTestCase]:
        """Test cases for diabetes and metabolic assessment"""
        return [
            SpecialistTestCase(
                id="endo_diabetes_001",
                specialty=MedicalSpecialty.ENDOCRINOLOGY,
                query="Evaluate diabetes risk and metabolic status based on recent HbA1c trends",
                patient_context={
                    "lab_values": {
                        "hba1c_trend": ["5.7%", "6.0%", "6.3%"],
                        "fasting_glucose": [105, 112, 118],
                        "weight_gain": "26.7 pounds in one year"
                    },
                    "risk_factors": ["family_history", "sedentary_lifestyle", "obesity"]
                },
                expected_findings={
                    "prediabetes",
                    "insulin_resistance",
                    "metabolic_syndrome",
                    "weight_gain_concern"
                },
                expected_recommendations={
                    "lifestyle_intervention",
                    "weight_management_program",
                    "consider_metformin",
                    "quarterly_monitoring"
                },
                specialty_specific_expectations={
                    "hormonal_assessments": ["insulin_levels", "c_peptide"],
                    "metabolic_markers": ["lipid_panel", "liver_enzymes"]
                },
                category="diabetes_prevention",
                urgency_level="routine",
                description="Prediabetes evaluation with metabolic assessment"
            )
        ]
    
    # ===== LABORATORY MEDICINE TEST CASES =====
    @staticmethod
    def get_laboratory_medicine_interpretation_cases() -> List[SpecialistTestCase]:
        """Test cases for lab result interpretation"""
        return [
            SpecialistTestCase(
                id="lab_interpretation_001",
                specialty=MedicalSpecialty.LABORATORY_MEDICINE,
                query="Interpret comprehensive metabolic panel with abnormal values",
                patient_context={
                    "lab_results": {
                        "glucose": 118,
                        "bun": 25,
                        "creatinine": 1.3,
                        "egfr": 58,
                        "alt": 45,
                        "ast": 38,
                        "albumin": 3.2
                    },
                    "reference_ranges": {
                        "glucose": "70-100",
                        "bun": "7-20",
                        "creatinine": "0.7-1.2",
                        "egfr": ">60",
                        "alt": "7-40",
                        "ast": "10-40",
                        "albumin": "3.5-5.0"
                    }
                },
                expected_findings={
                    "impaired_fasting_glucose",
                    "mild_renal_impairment",
                    "elevated_bun",
                    "mild_transaminitis",
                    "hypoalbuminemia"
                },
                expected_recommendations={
                    "renal_function_monitoring",
                    "diabetes_screening",
                    "liver_evaluation",
                    "nutritional_assessment"
                },
                expected_safety_concerns={
                    "medication_dose_adjustment_needed",
                    "contrast_media_caution"
                },
                category="metabolic_panel",
                urgency_level="routine",
                description="Comprehensive metabolic panel interpretation"
            )
        ]
    
    # ===== PHARMACY TEST CASES =====
    @staticmethod
    def get_pharmacy_medication_review_cases() -> List[SpecialistTestCase]:
        """Test cases for medication review and interactions"""
        return [
            SpecialistTestCase(
                id="pharm_review_001",
                specialty=MedicalSpecialty.PHARMACY,
                query="Review current medications for interactions and optimization",
                patient_context={
                    "current_medications": [
                        "rosuvastatin 20mg daily",
                        "ezetimibe 10mg daily",
                        "metformin 500mg twice daily",
                        "lisinopril 10mg daily",
                        "aspirin 81mg daily"
                    ],
                    "conditions": ["dyslipidemia", "prediabetes", "hypertension"],
                    "labs": {"ck": "normal", "liver_enzymes": "normal", "egfr": 58}
                },
                expected_findings={
                    "no_major_interactions",
                    "appropriate_statin_dose",
                    "metformin_dose_suboptimal"
                },
                expected_recommendations={
                    "increase_metformin_to_1000mg_bid",
                    "monitor_renal_function",
                    "continue_current_regimen"
                },
                expected_safety_concerns={
                    "metformin_renal_adjustment_if_egfr_drops",
                    "statin_myopathy_monitoring"
                },
                category="medication_reconciliation",
                urgency_level="routine",
                description="Comprehensive medication review"
            )
        ]
    
    # ===== NUTRITION TEST CASES =====
    @staticmethod
    def get_nutrition_assessment_cases() -> List[SpecialistTestCase]:
        """Test cases for nutritional assessment"""
        return [
            SpecialistTestCase(
                id="nutrition_assessment_001",
                specialty=MedicalSpecialty.NUTRITION,
                query="Evaluate nutritional status and provide dietary recommendations for metabolic syndrome",
                patient_context={
                    "anthropometrics": {
                        "bmi": 32.5,
                        "weight_gain": "26.7 pounds in one year",
                        "waist_circumference": "42 inches"
                    },
                    "labs": {
                        "hdl": 33,
                        "triglycerides": 153,
                        "glucose": 118,
                        "albumin": 3.2
                    },
                    "dietary_history": "high carbohydrate intake, limited vegetables"
                },
                expected_findings={
                    "obesity_class_1",
                    "central_adiposity",
                    "poor_dietary_quality",
                    "mild_protein_deficiency"
                },
                expected_recommendations={
                    "mediterranean_diet",
                    "caloric_reduction_500_750_daily",
                    "increase_protein_intake",
                    "reduce_refined_carbohydrates"
                },
                specialty_specific_expectations={
                    "caloric_target": "1800-2000 kcal/day",
                    "macros": {"protein": "25%", "carbs": "40%", "fat": "35%"}
                },
                category="weight_management",
                urgency_level="routine",
                description="Nutritional assessment for metabolic syndrome"
            )
        ]
    
    # ===== PREVENTIVE MEDICINE TEST CASES =====
    @staticmethod
    def get_preventive_medicine_screening_cases() -> List[SpecialistTestCase]:
        """Test cases for preventive care and screening"""
        return [
            SpecialistTestCase(
                id="prevent_screening_001",
                specialty=MedicalSpecialty.PREVENTIVE_MEDICINE,
                query="Assess cardiovascular risk and recommend appropriate screening",
                patient_context={
                    "demographics": {"age": 55, "sex": "male"},
                    "risk_factors": [
                        "dyslipidemia",
                        "prediabetes",
                        "obesity",
                        "family_history_cad"
                    ],
                    "current_screenings": {
                        "colonoscopy": "never",
                        "cardiac_stress_test": "never",
                        "carotid_ultrasound": "never"
                    }
                },
                expected_findings={
                    "high_cardiovascular_risk",
                    "overdue_cancer_screening",
                    "multiple_modifiable_risk_factors"
                },
                expected_recommendations={
                    "cardiac_stress_test",
                    "coronary_calcium_score",
                    "colonoscopy_screening",
                    "annual_preventive_exam"
                },
                specialty_specific_expectations={
                    "ascvd_risk_score": ">20%",
                    "screening_intervals": {
                        "lipids": "annually",
                        "diabetes": "annually",
                        "cancer": "per_guidelines"
                    }
                },
                category="risk_assessment",
                urgency_level="routine",
                description="Comprehensive preventive care assessment"
            )
        ]
    
    @staticmethod
    def get_comprehensive_health_cases() -> List[SpecialistTestCase]:
        """Test cases for comprehensive primary care assessment"""
        return [
            SpecialistTestCase(
                id="gp_comprehensive_001",
                specialty=MedicalSpecialty.PREVENTIVE_MEDICINE,
                query="Provide comprehensive assessment and care coordination",
                patient_context={
                    "chief_complaints": ["fatigue", "weight_gain"],
                    "chronic_conditions": ["dyslipidemia", "prediabetes", "obesity"],
                    "recent_changes": {
                        "weight": "+26.7 lbs in 1 year",
                        "energy": "decreased",
                        "sleep": "poor quality"
                    }
                },
                expected_findings={
                    "metabolic_syndrome",
                    "possible_sleep_apnea",
                    "deconditioning",
                    "multiple_risk_factors"
                },
                expected_recommendations={
                    "sleep_study_referral",
                    "endocrinology_referral",
                    "structured_weight_loss_program",
                    "coordinate_specialist_care"
                },
                expected_safety_concerns={
                    "cardiovascular_risk",
                    "diabetes_progression_risk"
                },
                category="comprehensive_care",
                urgency_level="routine",
                description="Primary care comprehensive assessment"
            )
        ]
    
    # ===== AGGREGATE METHODS =====
    @classmethod
    def get_all_test_cases(cls) -> List[SpecialistTestCase]:
        """Get all test cases across all specialties"""
        all_cases = []
        
        # Cardiology
        all_cases.extend(cls.get_cardiology_lipid_trend_cases())
        all_cases.extend(cls.get_cardiology_medication_adherence_cases())
        
        # Endocrinology
        all_cases.extend(cls.get_endocrinology_diabetes_cases())
        
        # Laboratory Medicine
        all_cases.extend(cls.get_laboratory_medicine_interpretation_cases())
        
        # Pharmacy
        all_cases.extend(cls.get_pharmacy_medication_review_cases())
        
        # Nutrition
        all_cases.extend(cls.get_nutrition_assessment_cases())
        
        # Preventive Medicine
        all_cases.extend(cls.get_preventive_medicine_screening_cases())
        
        # Data Analysis
        all_cases.extend(cls.get_data_analysis_trend_cases())
        
        # General Practice
        all_cases.extend(cls.get_general_practice_comprehensive_cases())
        
        return all_cases
    
    @classmethod
    def get_test_cases_by_specialty(cls, specialty: MedicalSpecialty) -> List[SpecialistTestCase]:
        """Get test cases for a specific specialty"""
        specialty_methods = {
            MedicalSpecialty.CARDIOLOGY: [
                cls.get_cardiology_lipid_trend_cases,
                cls.get_cardiology_medication_adherence_cases
            ],
            MedicalSpecialty.ENDOCRINOLOGY: [cls.get_endocrinology_diabetes_cases],
            MedicalSpecialty.LABORATORY_MEDICINE: [cls.get_laboratory_medicine_interpretation_cases],
            MedicalSpecialty.PHARMACY: [cls.get_pharmacy_medication_review_cases],
            MedicalSpecialty.NUTRITION: [cls.get_nutrition_assessment_cases],
            MedicalSpecialty.PREVENTIVE_MEDICINE: [cls.get_preventive_medicine_screening_cases],
        }
        
        cases = []
        for method in specialty_methods.get(specialty, []):
            cases.extend(method())
        
        return cases
    
    @classmethod
    def get_test_cases_by_category(cls, category: str) -> List[SpecialistTestCase]:
        """Get test cases by category across all specialties"""
        all_cases = cls.get_all_test_cases()
        return [case for case in all_cases if case.category == category]
    
    @classmethod
    def get_real_world_based_cases(cls) -> List[SpecialistTestCase]:
        """Get only test cases based on real-world queries"""
        all_cases = cls.get_all_test_cases()
        return [case for case in all_cases if case.based_on_real_case]


