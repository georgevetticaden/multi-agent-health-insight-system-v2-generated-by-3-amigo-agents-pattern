"""
Cardiology Specialist Agent Test Cases

Comprehensive test cases for evaluating the Cardiology specialist agent's performance
in cardiovascular health assessment, diagnosis, and treatment recommendations.
Based on real-world test queries from the multi-agent health system.
"""

from dataclasses import dataclass
from typing import List, Set, Dict, Optional, Any
from enum import Enum


class DiagnosticConfidence(Enum):
    """Confidence levels for diagnostic assessments"""
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    DEFINITIVE = "definitive"


@dataclass
class CardiologyTestCase:
    """Test case for Cardiology specialist evaluation"""
    id: str
    query: str
    patient_context: Dict[str, Any]  # Relevant patient data
    expected_diagnoses: Set[str]  # Possible differential diagnoses
    expected_tests: Set[str]  # Recommended diagnostic tests
    expected_risk_factors: Set[str]  # Identified cardiovascular risk factors
    expected_recommendations: Set[str]  # Treatment/lifestyle recommendations
    expected_medications: Set[str]  # Expected medication recommendations
    expected_monitoring: Set[str]  # Follow-up monitoring requirements
    expected_confidence: DiagnosticConfidence
    clinical_guidelines: List[str]  # Relevant guidelines to follow
    category: str  # Type of cardiac condition/assessment
    urgency_level: str  # emergency, urgent, routine
    description: str
    based_on_real_case: bool = False
    notes: Optional[str] = None
    key_findings: Optional[List[str]] = None  # Key findings to identify
    
    def __post_init__(self):
        """Validate test case fields"""
        valid_urgencies = {"emergency", "urgent", "routine"}
        if self.urgency_level not in valid_urgencies:
            raise ValueError(f"Invalid urgency level: {self.urgency_level}")
        
        # Set default empty list for key_findings if None
        if self.key_findings is None:
            self.key_findings = []


class CardiologyTestCases:
    """Comprehensive test cases for Cardiology specialist evaluation"""
    
    @staticmethod
    def get_lipid_trend_analysis_cases() -> List[CardiologyTestCase]:
        """Test cases for lipid trend analysis based on real-world query 1"""
        return [
            CardiologyTestCase(
                id="cardio_lipid_001",
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
                expected_diagnoses={
                    "persistent_low_hdl_syndrome",
                    "mixed_dyslipidemia",
                    "metabolic_syndrome",
                    "possible_familial_lipid_disorder"
                },
                expected_tests={
                    "complete_lipid_panel",
                    "apolipoprotein_b",
                    "lipoprotein_a",
                    "genetic_lipid_testing"
                },
                expected_risk_factors={
                    "persistently_low_hdl",
                    "historical_severe_hypertriglyceridemia",
                    "inadequate_statin_response",
                    "metabolic_dysfunction"
                },
                expected_recommendations={
                    "increase_statin_intensity",
                    "hdl_raising_strategies",
                    "lifestyle_modification",
                    "consider_pcsk9_inhibitor"
                },
                expected_medications={
                    "rosuvastatin_20_40mg",
                    "ezetimibe_continuation",
                    "consider_fenofibrate",
                    "omega_3_fatty_acids"
                },
                expected_monitoring={
                    "lipid_panel_every_3_months",
                    "liver_function_monitoring",
                    "ck_if_symptoms"
                },
                expected_confidence=DiagnosticConfidence.HIGH,
                clinical_guidelines=["2018 AHA/ACC Cholesterol Guidelines", "NLA Recommendations"],
                category="lipid_management",
                urgency_level="urgent",
                description="Long-term lipid management with persistent HDL deficiency",
                based_on_real_case=True,
                key_findings=[
                    "HDL persistently below 40 mg/dL for 12 years",
                    "Triglycerides dropped from 426 to 95 mg/dL",
                    "Recent triglyceride increase to 153 mg/dL",
                    "Missing total cholesterol measurements since 2022"
                ]
            )
        ]
    
    @staticmethod
    def get_medication_adherence_cases() -> List[CardiologyTestCase]:
        """Test cases for medication adherence and correlation analysis based on real-world query 2"""
        return [
            CardiologyTestCase(
                id="cardio_adherence_001",
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
                    },
                    "metabolic_status": {
                        "hba1c": "5.7-6.3% (prediabetic)",
                        "weight_gain": "26.7 pounds in one year"
                    }
                },
                expected_diagnoses={
                    "medication_nonadherence",
                    "statin_inadequate_response",
                    "metabolic_syndrome",
                    "insulin_resistance"
                },
                expected_tests={
                    "medication_adherence_assessment",
                    "statin_response_genetic_testing",
                    "insulin_resistance_markers",
                    "comprehensive_metabolic_panel"
                },
                expected_risk_factors={
                    "poor_medication_adherence",
                    "prediabetes",
                    "weight_gain",
                    "metabolic_dysfunction"
                },
                expected_recommendations={
                    "adherence_improvement_strategies",
                    "medication_optimization",
                    "metabolic_management",
                    "frequent_monitoring"
                },
                expected_medications={
                    "high_intensity_statin",
                    "continue_ezetimibe",
                    "consider_pcsk9_inhibitor",
                    "metformin_for_prediabetes"
                },
                expected_monitoring={
                    "monthly_adherence_check",
                    "labs_every_6_8_weeks",
                    "pharmacy_refill_tracking"
                },
                expected_confidence=DiagnosticConfidence.HIGH,
                clinical_guidelines=["ACC/AHA Statin Guidelines", "Medication Adherence Best Practices"],
                category="medication_management",
                urgency_level="urgent",
                description="Complex medication adherence issues with metabolic complications",
                based_on_real_case=True,
                key_findings=[
                    "Multiple medication switches suggest side effects or inadequate response",
                    "Current dual therapy failing to achieve targets",
                    "Underlying metabolic issues interfering with treatment",
                    "Irregular monitoring indicates poor follow-up"
                ]
            )
        ]
    
    @staticmethod
    def get_metabolic_syndrome_cases() -> List[CardiologyTestCase]:
        """Test cases for metabolic syndrome and cardiovascular risk based on real-world query 3"""
        return [
            CardiologyTestCase(
                id="cardio_metabolic_001",
                query="Evaluate abnormal lab results showing metabolic syndrome and cardiovascular risk",
                patient_context={
                    "current_labs": {
                        "hba1c": 6.1,
                        "hdl": 33,
                        "triglycerides": 153,
                        "bun": 23,
                        "creatinine": 1.26
                    },
                    "physical_exam": {
                        "weight_gain": "26.7 pounds in one year",
                        "bmi": 26.9,
                        "bp": "124/80"
                    },
                    "risk_progression": {
                        "hba1c_trend": "5.7% to 6.1%",
                        "kidney_function": "Stage 2 CKD (eGFR 73)"
                    }
                },
                expected_diagnoses={
                    "metabolic_syndrome",
                    "prediabetes",
                    "stage_2_ckd",
                    "dyslipidemia",
                    "cardiovascular_disease_risk"
                },
                expected_tests={
                    "oral_glucose_tolerance_test",
                    "urine_protein_albumin_ratio",
                    "apolipoprotein_b",
                    "hscrp",
                    "ekg"
                },
                expected_risk_factors={
                    "prediabetes",
                    "low_hdl",
                    "elevated_triglycerides",
                    "weight_gain",
                    "kidney_disease",
                    "borderline_hypertension"
                },
                expected_recommendations={
                    "weight_loss_11_23_pounds",
                    "exercise_150_min_weekly",
                    "dietary_modification",
                    "diabetes_prevention_program"
                },
                expected_medications={
                    "metformin",
                    "statin_therapy",
                    "consider_ace_inhibitor",
                    "aspirin_if_ascvd_high"
                },
                expected_monitoring={
                    "quarterly_metabolic_panel",
                    "kidney_function_every_3_6_months",
                    "annual_cardiac_evaluation"
                },
                expected_confidence=DiagnosticConfidence.DEFINITIVE,
                clinical_guidelines=["ATP III Metabolic Syndrome", "ADA Prediabetes Guidelines", "KDIGO CKD Guidelines"],
                category="metabolic_cardiovascular",
                urgency_level="urgent",
                description="Metabolic syndrome with multiple cardiovascular risk factors",
                based_on_real_case=True,
                key_findings=[
                    "Meets criteria for metabolic syndrome",
                    "Progression toward diabetes",
                    "Early kidney disease",
                    "Significant weight gain contributing to risk"
                ]
            )
        ]
    
    @staticmethod
    def get_diabetes_cardiovascular_risk_cases() -> List[CardiologyTestCase]:
        """Test cases for diabetes impact on cardiovascular risk based on real-world query 4"""
        return [
            CardiologyTestCase(
                id="cardio_diabetes_001",
                query="Analyze HbA1c changes with metformin and correlation with weight and cardiovascular risk",
                patient_context={
                    "diabetes_management": {
                        "hba1c_trend": "5.7% to 6.3%",
                        "medications": ["metformin", "dosage_adjustments_unknown"],
                        "weight_changes": "significant gain"
                    },
                    "cardiovascular_impact": {
                        "hdl": "persistently low",
                        "bp": "borderline elevated",
                        "metabolic_syndrome": "present"
                    },
                    "comorbidities": {
                        "prediabetes_to_diabetes_progression": True,
                        "dyslipidemia": True,
                        "kidney_disease": "Stage 2"
                    }
                },
                expected_diagnoses={
                    "type_2_diabetes_progression",
                    "diabetic_dyslipidemia",
                    "cardiometabolic_syndrome",
                    "diabetic_nephropathy_early"
                },
                expected_tests={
                    "fasting_glucose",
                    "ogtt",
                    "cpeptide",
                    "microalbumin_creatinine_ratio",
                    "comprehensive_lipid_panel"
                },
                expected_risk_factors={
                    "poor_glycemic_control",
                    "weight_gain",
                    "insulin_resistance",
                    "diabetic_dyslipidemia",
                    "early_nephropathy"
                },
                expected_recommendations={
                    "intensify_diabetes_management",
                    "weight_loss_program",
                    "cardiovascular_risk_reduction",
                    "lifestyle_intensive_intervention"
                },
                expected_medications={
                    "metformin_optimization",
                    "consider_glp1_agonist",
                    "statin_therapy",
                    "ace_inhibitor_arb"
                },
                expected_monitoring={
                    "quarterly_hba1c",
                    "annual_diabetic_panel",
                    "cardiovascular_assessment"
                },
                expected_confidence=DiagnosticConfidence.HIGH,
                clinical_guidelines=["ADA Standards of Care", "ACC/AHA Diabetes CVD Guidelines"],
                category="diabetes_cardiovascular",
                urgency_level="urgent",
                description="Diabetes progression with significant cardiovascular implications",
                based_on_real_case=True,
                key_findings=[
                    "Poor glycemic control despite metformin",
                    "Weight gain worsening metabolic status",
                    "Multiple cardiovascular risk factors",
                    "Early diabetic complications"
                ]
            )
        ]
    
    @staticmethod
    def get_all_test_cases() -> List[CardiologyTestCase]:
        """Get all cardiology test cases"""
        all_cases = []
        all_cases.extend(CardiologyTestCases.get_lipid_trend_analysis_cases())
        all_cases.extend(CardiologyTestCases.get_medication_adherence_cases())
        all_cases.extend(CardiologyTestCases.get_metabolic_syndrome_cases())
        all_cases.extend(CardiologyTestCases.get_diabetes_cardiovascular_risk_cases())
        return all_cases
    
    @staticmethod
    def get_test_cases_by_category(category: str) -> List[CardiologyTestCase]:
        """Get test cases for a specific category"""
        category_map = {
            "lipid_management": CardiologyTestCases.get_lipid_trend_analysis_cases,
            "medication_management": CardiologyTestCases.get_medication_adherence_cases,
            "metabolic_cardiovascular": CardiologyTestCases.get_metabolic_syndrome_cases,
            "diabetes_cardiovascular": CardiologyTestCases.get_diabetes_cardiovascular_risk_cases
        }
        
        if category in category_map:
            return category_map[category]()
        
        # Return all test cases in that category
        all_cases = CardiologyTestCases.get_all_test_cases()
        return [case for case in all_cases if case.category == category]
    
    @staticmethod
    def get_test_cases_by_urgency(urgency: str) -> List[CardiologyTestCase]:
        """Get test cases filtered by urgency level"""
        all_cases = CardiologyTestCases.get_all_test_cases()
        return [case for case in all_cases if case.urgency_level == urgency]
    
    # Test suite methods for CLI consistency (matching CMO pattern)
    @classmethod
    def get_diagnostic_test_suite(cls) -> List[CardiologyTestCase]:
        """Get test suite for diagnostic accuracy evaluation"""
        # Include a mix of different diagnostic scenarios
        return (
            cls.get_lipid_trend_analysis_cases()[:1] +
            cls.get_metabolic_syndrome_cases()[:1] +
            cls.get_diabetes_cardiovascular_risk_cases()[:1]
        )
    
    @classmethod
    def get_treatment_test_suite(cls) -> List[CardiologyTestCase]:
        """Get test suite for treatment recommendation evaluation"""
        # Focus on cases requiring medication optimization
        return (
            cls.get_medication_adherence_cases()[:1] +
            cls.get_lipid_trend_analysis_cases()[:1]
        )
    
    @classmethod
    def get_comprehensive_test_suite(cls) -> List[CardiologyTestCase]:
        """Get comprehensive test suite covering all evaluation dimensions"""
        # Balanced selection from each category
        return (
            cls.get_lipid_trend_analysis_cases()[:1] +
            cls.get_medication_adherence_cases()[:1] +
            cls.get_metabolic_syndrome_cases()[:1] +
            cls.get_diabetes_cardiovascular_risk_cases()[:1]
        )
    
    @classmethod
    def get_real_world_test_suite(cls) -> List[CardiologyTestCase]:
        """Get test suite based on real-world queries"""
        # All 4 test cases are based on real-world queries
        return cls.get_all_test_cases()