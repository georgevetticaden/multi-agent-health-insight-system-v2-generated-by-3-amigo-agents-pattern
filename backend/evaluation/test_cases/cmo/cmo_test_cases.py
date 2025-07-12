"""
CMO Agent Test Cases

Comprehensive test cases for evaluating the CMO agent's performance across
different query types and complexity levels. Based on Anthropic's testing best practices
and real-world query analysis from the multi-agent health system.
"""

from dataclasses import dataclass
from typing import List, Set, Dict, Optional
from enum import Enum


@dataclass
class TestCase:
    """Individual test case for CMO evaluation"""
    id: str
    query: str
    expected_complexity: str  # SIMPLE, STANDARD, COMPLEX, COMPREHENSIVE
    expected_specialties: Set[str]
    key_data_points: List[str]  # Expected data points to query
    description: str
    category: str  # Category for grouping similar tests
    edge_case: bool = False
    notes: Optional[str] = None
    based_on_real_query: bool = False  # Indicates if based on actual system test
    prompts_tested: Optional[Dict[str, str]] = None  # Maps prompt purpose to file path
    
    def __post_init__(self):
        """Add default prompt mapping if not specified"""
        if self.prompts_tested is None:
            self.prompts_tested = {
                "system": "backend/services/agents/cmo/prompts/system.txt",
                "stage1_analysis": "backend/services/agents/cmo/prompts/analyze_query.txt",
                "stage2_task_creation": "backend/services/agents/cmo/prompts/task_creation.txt"
            }


class CMOTestCases:
    """Comprehensive test cases for CMO agent evaluation based on real system behavior"""
    
    @staticmethod
    def get_simple_queries() -> List[TestCase]:
        """Test cases for SIMPLE complexity queries"""
        return [
            TestCase(
                id="simple_001",
                query="What is my current blood sugar level?",
                expected_complexity="SIMPLE",
                expected_specialties={"general_practice"},
                key_data_points=["glucose", "latest"],
                description="Single value lookup - current glucose",
                category="glucose"
            ),
            TestCase(
                id="simple_002",
                query="What was my last HbA1c reading?",
                expected_complexity="SIMPLE",
                expected_specialties={"endocrinology"},
                key_data_points=["hba1c", "latest"],
                description="Single value lookup - HbA1c",
                category="diabetes"
            ),
            TestCase(
                id="simple_003",
                query="What is my current weight?",
                expected_complexity="SIMPLE",
                expected_specialties={"general_practice"},
                key_data_points=["weight", "latest"],
                description="Single value lookup - weight",
                category="vitals"
            ),
            TestCase(
                id="simple_004",
                query="Am I taking metformin?",
                expected_complexity="SIMPLE",
                expected_specialties={"pharmacy"},
                key_data_points=["medications", "metformin", "current"],
                description="Single medication check",
                category="medications"
            ),
            TestCase(
                id="simple_005",
                query="What is my latest HDL cholesterol?",
                expected_complexity="SIMPLE",
                expected_specialties={"cardiology"},
                key_data_points=["hdl_cholesterol", "latest"],
                description="Single lipid value lookup",
                category="lipids"
            )
        ]
    
    @staticmethod
    def get_standard_queries() -> List[TestCase]:
        """Test cases for STANDARD complexity queries - based on real system tests"""
        return [
            TestCase(
                id="standard_001",
                query="What's my cholesterol trend over my entire data? I want to see trends across the top 4 cholesterol metrics including Triglycerides across that time period",
                expected_complexity="STANDARD",
                expected_specialties={"cardiology", "endocrinology", "data_analysis"},
                key_data_points=["hdl_cholesterol", "ldl_cholesterol", "total_cholesterol", "triglycerides", "trends", "date_range"],
                description="Multi-metric trend analysis over time",
                category="lipids",
                based_on_real_query=True,
                notes="Real query 1 - System selected 3 specialists for cholesterol trend analysis"
            ),
            TestCase(
                id="standard_002",
                query="Show my abnormal lab results from labs this year?",
                expected_complexity="STANDARD",
                expected_specialties={"endocrinology", "laboratory_medicine", "preventive_medicine"},
                key_data_points=["lab_results", "abnormal_flags", "current_year", "reference_ranges"],
                description="Identify abnormal values with clinical context",
                category="diagnostics",
                based_on_real_query=True,
                notes="Real query 3 - Found HbA1c, BUN, HDL, Triglycerides abnormalities"
            ),
            TestCase(
                id="standard_003",
                query="How has my blood pressure changed over the last 6 months?",
                expected_complexity="STANDARD",
                expected_specialties={"cardiology", "general_practice"},
                key_data_points=["blood_pressure", "systolic", "diastolic", "6_months", "trend"],
                description="Blood pressure trend analysis",
                category="cardiovascular"
            ),
            TestCase(
                id="standard_004",
                query="Compare my HbA1c levels from this year to last year",
                expected_complexity="STANDARD",
                expected_specialties={"endocrinology", "laboratory_medicine"},
                key_data_points=["hba1c", "yearly_comparison", "prediabetes_threshold"],
                description="Year-over-year diabetic marker comparison",
                category="diabetes"
            ),
            TestCase(
                id="standard_005",
                query="Are my cholesterol medications working based on my recent labs?",
                expected_complexity="STANDARD",
                expected_specialties={"cardiology", "pharmacy"},
                key_data_points=["cholesterol_medications", "ldl_trends", "medication_start_date", "effectiveness"],
                description="Simple medication effectiveness check",
                category="medications"
            )
        ]
    
    @staticmethod
    def get_complex_queries() -> List[TestCase]:
        """Test cases for COMPLEX complexity queries - based on real system tests"""
        return [
            TestCase(
                id="complex_001",
                query="Analyze cholesterol relevant medication adherence patterns over that time period and how do they correlate with these cholesterol lab results.",
                expected_complexity="COMPLEX",
                expected_specialties={"pharmacy", "cardiology", "laboratory_medicine", "endocrinology", "data_analysis"},
                key_data_points=["statin_history", "medication_switches", "ldl_correlation", "hdl_patterns", "triglyceride_response", "adherence_gaps"],
                description="Multi-factor correlation between medications and lab outcomes",
                category="medications",
                based_on_real_query=True,
                notes="Real query 2 - Analyzed statin switches, ezetimibe addition, and lab correlations"
            ),
            TestCase(
                id="complex_002",
                query="How has my HbA1c level changed since I started taking metformin, has my dosage been adjusted over time based on my lab results, and is there a correlation between these changes and my weight measurements during the same period?",
                expected_complexity="COMPLEX",
                expected_specialties={"endocrinology", "pharmacy", "nutrition"},
                key_data_points=["hba1c_trend", "metformin_initiation", "dose_adjustments", "weight_correlation", "glycemic_control", "temporal_analysis"],
                description="Three-way correlation analysis: medication, lab results, and weight",
                category="diabetes",
                based_on_real_query=True,
                notes="Real query 4 - Found suboptimal dosing and weight gain correlation"
            ),
            TestCase(
                id="complex_003",
                query="Identify concerning patterns in my cardiovascular risk factors including blood pressure, cholesterol panels, weight changes, and relevant medications over the past 3 years",
                expected_complexity="COMPLEX",
                expected_specialties={"cardiology", "endocrinology", "preventive_medicine", "pharmacy", "data_analysis"},
                key_data_points=["cvd_risk_factors", "lipid_panels", "bp_trends", "weight_trajectory", "medication_timeline", "risk_stratification"],
                description="Comprehensive cardiovascular risk assessment",
                category="cardiovascular"
            ),
            TestCase(
                id="complex_004",
                query="Analyze the relationship between my prediabetic status, cholesterol management, and weight gain, including medication effectiveness",
                expected_complexity="COMPLEX",
                expected_specialties={"endocrinology", "cardiology", "nutrition", "pharmacy"},
                key_data_points=["hba1c_prediabetes", "metabolic_syndrome", "lipid_response", "weight_gain_pattern", "medication_optimization"],
                description="Metabolic syndrome component analysis",
                category="metabolic"
            ),
            TestCase(
                id="complex_005",
                query="Review my kidney function markers over time and their relationship to my medications and other health conditions",
                expected_complexity="COMPLEX",
                expected_specialties={"laboratory_medicine", "general_practice", "pharmacy", "preventive_medicine"},
                key_data_points=["bun", "creatinine", "egfr", "medication_nephrotoxicity", "diabetes_impact", "hydration_status"],
                description="Kidney function analysis with multiple contributing factors",
                category="renal"
            )
        ]
    
    @staticmethod
    def get_comprehensive_queries() -> List[TestCase]:
        """Test cases for COMPREHENSIVE complexity queries"""
        return [
            TestCase(
                id="comprehensive_001",
                query="Provide a complete health assessment including all my conditions, medications, lab trends, and recommendations for improvement based on my entire medical history",
                expected_complexity="COMPREHENSIVE",
                expected_specialties={"general_practice", "endocrinology", "cardiology", "pharmacy", 
                                    "laboratory_medicine", "nutrition", "preventive_medicine", "data_analysis"},
                key_data_points=["complete_history", "all_conditions", "all_medications", "all_labs", 
                               "trend_analysis", "risk_assessment", "personalized_recommendations"],
                description="Full health review with all available data",
                category="comprehensive"
            ),
            TestCase(
                id="comprehensive_002",
                query="Analyze my metabolic health journey from 2013 to present, including weight fluctuations, diabetes progression, cholesterol management, and medication history with future risk projections",
                expected_complexity="COMPREHENSIVE",
                expected_specialties={"endocrinology", "cardiology", "nutrition", "pharmacy", 
                                    "preventive_medicine", "data_analysis"},
                key_data_points=["12_year_history", "weight_cycles", "prediabetes_progression", 
                               "lipid_management", "medication_timeline", "future_risk_modeling"],
                description="Long-term metabolic health trajectory analysis",
                category="comprehensive",
                notes="Based on patterns from real queries showing 2013-2025 data"
            ),
            TestCase(
                id="comprehensive_003",
                query="Create a personalized health optimization plan addressing my prediabetes, cholesterol issues, recent weight gain, and suboptimal medication dosing",
                expected_complexity="COMPREHENSIVE",
                expected_specialties={"preventive_medicine", "endocrinology", "cardiology", 
                                    "nutrition", "pharmacy", "general_practice"},
                key_data_points=["current_health_status", "optimization_targets", "medication_adjustments", 
                               "lifestyle_modifications", "monitoring_plan", "prevention_strategies"],
                description="Personalized intervention planning based on current health state",
                category="comprehensive",
                notes="Addresses issues found in real test queries"
            )
        ]
    
    @staticmethod
    def get_edge_cases() -> List[TestCase]:
        """Edge cases and data quality challenges based on real system observations"""
        return [
            TestCase(
                id="edge_001",
                query="Why is my HDL showing 147 mg/dL when normal range is 40-60?",
                expected_complexity="SIMPLE",
                expected_specialties={"laboratory_medicine", "data_analysis"},
                key_data_points=["hdl_outlier", "data_quality", "lab_error"],
                description="Data quality issue - physiologically improbable value",
                category="edge_case",
                edge_case=True,
                notes="Real data showed HDL of 147 mg/dL - likely lab or data entry error"
            ),
            TestCase(
                id="edge_002",
                query="Analyze my medication adherence when prescription dates are missing",
                expected_complexity="STANDARD",
                expected_specialties={"pharmacy", "data_analysis"},
                key_data_points=["prescription_data", "missing_timestamps", "adherence_estimation"],
                description="Missing data handling - prescriptions without timing",
                category="edge_case",
                edge_case=True,
                notes="Real system encountered prescriptions without start/end dates"
            ),
            TestCase(
                id="edge_003",
                query="Show my cholesterol trends when I have 658-day gaps between tests",
                expected_complexity="STANDARD",
                expected_specialties={"cardiology", "data_analysis", "laboratory_medicine"},
                key_data_points=["sparse_data", "interpolation", "gap_handling"],
                description="Sparse data handling - large measurement gaps",
                category="edge_case",
                edge_case=True,
                notes="Real data showed gaps up to 658 days between measurements"
            ),
            TestCase(
                id="edge_004",
                query="health",
                expected_complexity="SIMPLE",
                expected_specialties={"general_practice"},
                key_data_points=["clarification_needed"],
                description="Extremely vague query requiring clarification",
                category="edge_case",
                edge_case=True
            ),
            TestCase(
                id="edge_005",
                query="Why did I gain 26.7 pounds in one year after being stable for 3 years?",
                expected_complexity="STANDARD",
                expected_specialties={"endocrinology", "nutrition", "general_practice"},
                key_data_points=["weight_change", "rapid_gain", "contributing_factors", "timeline"],
                description="Significant health change requiring investigation",
                category="edge_case",
                edge_case=True,
                notes="Real data showed sudden weight gain from 200 to 226.62 lbs"
            )
        ]
    
    @classmethod
    def get_all_test_cases(cls) -> List[TestCase]:
        """Get all test cases"""
        return (
            cls.get_simple_queries() +
            cls.get_standard_queries() +
            cls.get_complex_queries() +
            cls.get_comprehensive_queries() +
            cls.get_edge_cases()
        )
    
    @classmethod
    def get_test_cases_by_complexity(cls, complexity: str) -> List[TestCase]:
        """Get test cases for a specific complexity level"""
        all_cases = cls.get_all_test_cases()
        return [tc for tc in all_cases if tc.expected_complexity == complexity]
    
    @classmethod
    def get_test_cases_by_category(cls, category: str) -> List[TestCase]:
        """Get test cases for a specific category"""
        all_cases = cls.get_all_test_cases()
        return [tc for tc in all_cases if tc.category == category]
    
    @classmethod
    def get_real_world_based_cases(cls) -> List[TestCase]:
        """Get test cases based on real system queries"""
        all_cases = cls.get_all_test_cases()
        return [tc for tc in all_cases if tc.based_on_real_query]
    
    # Test suite methods for CLI consistency
    @classmethod
    def get_complexity_test_suite(cls) -> List[TestCase]:
        """Get test suite for complexity classification evaluation"""
        return (
            cls.get_simple_queries()[:2] +
            cls.get_standard_queries()[:2] +
            cls.get_complex_queries()[:2] +
            cls.get_comprehensive_queries()[:1]
        )
    
    @classmethod
    def get_specialty_test_suite(cls) -> List[TestCase]:
        """Get test suite for specialty selection evaluation"""
        # Focus on cases with varied specialty requirements
        return [
            tc for tc in cls.get_all_test_cases()
            if len(tc.expected_specialties) >= 2
        ][:10]
    
    @classmethod
    def get_comprehensive_test_suite(cls) -> List[TestCase]:
        """Get comprehensive test suite covering all aspects"""
        return (
            cls.get_simple_queries()[:1] +
            cls.get_standard_queries()[:2] +
            cls.get_complex_queries()[:2] +
            cls.get_comprehensive_queries()[:1] +
            cls.get_edge_cases()[:2]
        )
    
    @classmethod
    def get_real_world_test_suite(cls) -> List[TestCase]:
        """Get test suite based on real-world queries"""
        # Return only the test cases actually based on real queries
        return [
            tc for tc in cls.get_all_test_cases()
            if tc.based_on_real_query
        ]