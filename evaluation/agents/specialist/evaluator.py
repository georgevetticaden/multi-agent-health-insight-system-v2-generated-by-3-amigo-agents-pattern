"""
Medical Specialist Agent Evaluator

This module contains the generalized specialist evaluation logic that can handle
all medical specialties (cardiology, endocrinology, etc.) with specialty-specific
customization through configuration.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Set, Any

from services.agents.specialist.specialist_agent import SpecialistAgent
from evaluation.framework.evaluators import BaseEvaluator, EvaluationResult
from anthropic import Anthropic
from services.agents.models import SpecialistTask, MedicalSpecialty

logger = logging.getLogger(__name__)


@dataclass
class SpecialistEvaluationResult(EvaluationResult):
    """Specialist-specific evaluation result extending the base result"""
    
    # Specialty information
    specialty: MedicalSpecialty = None
    
    # Medical accuracy
    expected_findings: Set[str] = field(default_factory=set)
    actual_findings: Set[str] = field(default_factory=set)
    medical_accuracy_score: float = 0.0
    accuracy_breakdown: Dict[str, float] = field(default_factory=dict)
    
    # Evidence quality
    evidence_referenced: List[str] = field(default_factory=list)
    evidence_quality_score: float = 0.0
    evidence_breakdown: Dict[str, float] = field(default_factory=dict)
    
    # Clinical reasoning
    clinical_reasoning_score: float = 0.0
    reasoning_breakdown: Dict[str, float] = field(default_factory=dict)
    
    # Specialty expertise
    specialty_expertise_score: float = 0.0
    expertise_breakdown: Dict[str, float] = field(default_factory=dict)
    
    # Patient safety
    safety_concerns_identified: Set[str] = field(default_factory=set)
    expected_safety_concerns: Set[str] = field(default_factory=set)
    patient_safety_score: float = 0.0
    safety_breakdown: Dict[str, float] = field(default_factory=dict)
    
    # Tool usage (for data_analysis and other tool-heavy specialties)
    tool_calls_made: int = 0
    tool_success_rate: float = 0.0
    tool_usage_score: float = 0.0
    
    # Additional specialist fields
    recommendations: Set[str] = field(default_factory=set)
    expected_recommendations: Set[str] = field(default_factory=set)
    urgency_assessment: Optional[str] = None
    confidence_level: Optional[str] = None
    
    # Specialty-specific fields (flexible dictionary for any specialty)
    specialty_specific_data: Dict[str, Any] = field(default_factory=dict)


class SpecialistEvaluator(BaseEvaluator):
    """Evaluates Medical Specialist agent performance for any specialty"""
    
    def __init__(self, 
                 specialist_agent: SpecialistAgent, 
                 specialty: MedicalSpecialty,
                 anthropic_client: Optional[Anthropic] = None):
        super().__init__(anthropic_client)
        self.specialist_agent = specialist_agent
        self.specialty = specialty
        
        # Get metadata from the agent class for this specific specialty
        self.agent_metadata = SpecialistAgent.get_evaluation_metadata(specialty)
        
        # Load specialty-specific configurations if needed
        self.specialty_config = self._load_specialty_config(specialty)
    
    def _load_specialty_config(self, specialty: MedicalSpecialty) -> Dict[str, Any]:
        """Load specialty-specific evaluation configuration"""
        # For now, return a basic config. Can be extended to load from YAML/JSON files
        configs = {
            MedicalSpecialty.CARDIOLOGY: {
                "focus_areas": ["diagnoses", "risk_factors", "urgency"],
                "key_findings": ["cardiac_conditions", "cardiovascular_risks"],
                "requires_guidelines": True
            },
            MedicalSpecialty.ENDOCRINOLOGY: {
                "focus_areas": ["hormone_levels", "metabolic_status", "diabetes_management"],
                "key_findings": ["endocrine_disorders", "metabolic_conditions"],
                "requires_lab_interpretation": True
            },
            MedicalSpecialty.LABORATORY_MEDICINE: {
                "focus_areas": ["test_interpretation", "abnormal_values", "clinical_correlation"],
                "key_findings": ["lab_abnormalities", "diagnostic_patterns"],
                "requires_reference_ranges": True
            },
            MedicalSpecialty.PHARMACY: {
                "focus_areas": ["medication_review", "interactions", "adherence"],
                "key_findings": ["drug_interactions", "dosing_issues"],
                "requires_drug_database": True
            },
            MedicalSpecialty.NUTRITION: {
                "focus_areas": ["dietary_assessment", "nutritional_status", "recommendations"],
                "key_findings": ["nutritional_deficiencies", "dietary_risks"],
                "requires_calorie_calculations": True
            },
            MedicalSpecialty.PREVENTIVE_MEDICINE: {
                "focus_areas": ["screening_recommendations", "risk_assessment", "prevention_strategies"],
                "key_findings": ["preventable_conditions", "screening_gaps"],
                "requires_guidelines": True
            },
            MedicalSpecialty.DATA_ANALYSIS: {
                "focus_areas": ["trend_analysis", "correlations", "statistical_significance"],
                "key_findings": ["data_patterns", "health_trends"],
                "requires_statistical_tools": True
            },
            MedicalSpecialty.GENERAL_PRACTICE: {
                "focus_areas": ["comprehensive_assessment", "differential_diagnosis", "referrals"],
                "key_findings": ["general_health_issues", "system_review"],
                "requires_broad_knowledge": True
            }
        }
        
        return configs.get(specialty, {
            "focus_areas": ["general_assessment"],
            "key_findings": ["clinical_findings"],
            "requires_guidelines": False
        })
    
    def get_evaluation_dimensions(self) -> List[str]:
        """Get evaluation dimensions from agent metadata"""
        return [criteria.dimension.value for criteria in self.agent_metadata.evaluation_criteria]
    
    def get_dimension_target(self, dimension: str) -> float:
        """Get target score for evaluation dimension"""
        for criteria in self.agent_metadata.evaluation_criteria:
            if criteria.dimension.value == dimension:
                return criteria.target_score
        
        # Default target if dimension not found
        return 0.8  # Default to 80%
    
    async def evaluate_single_test_case(self, test_case) -> SpecialistEvaluationResult:
        """Evaluate specialist on a single test case"""
        # Import test case type
        from evaluation.agents.specialist.test_cases import SpecialistTestCase
        
        logger.info(f"Evaluating {self.specialty.value} test case: {test_case.id} - {test_case.query[:50]}...")
        
        start_time = datetime.now()
        
        try:
            # Create a proper SpecialistTask
            task = SpecialistTask(
                specialist=self.specialty,
                objective=test_case.query,
                context=getattr(test_case, 'patient_context', ''),
                expected_output=f"Comprehensive {self.specialty.value} assessment",
                priority=1
            )
            
            # Execute specialist agent with the task
            response = await self.specialist_agent.execute_task(task)
            
            # Parse response based on specialty
            parsed_response = self._parse_specialist_response(response, self.specialty)
            
            # Evaluate each dimension using common medical dimensions
            medical_accuracy_score, accuracy_breakdown = await self._evaluate_medical_accuracy(
                parsed_response, test_case
            )
            
            evidence_quality_score, evidence_breakdown = await self._evaluate_evidence_quality(
                parsed_response, test_case
            )
            
            clinical_reasoning_score, reasoning_breakdown = await self._evaluate_clinical_reasoning(
                parsed_response, test_case
            )
            
            specialty_expertise_score, expertise_breakdown = await self._evaluate_specialty_expertise(
                parsed_response, test_case
            )
            
            patient_safety_score, safety_breakdown = await self._evaluate_patient_safety(
                parsed_response, test_case
            )
            
            # Calculate tool usage if applicable
            tool_usage_score = self._calculate_tool_usage_score(parsed_response)
            
            # Calculate total time and tokens
            total_response_time_ms = (datetime.now() - start_time).total_seconds() * 1000
            tokens_used = len(test_case.query.split()) + len(str(response).split())
            
            # Determine success based on all dimensions meeting targets
            success = all([
                medical_accuracy_score >= self.get_dimension_target("medical_accuracy"),
                evidence_quality_score >= self.get_dimension_target("evidence_quality"),
                clinical_reasoning_score >= self.get_dimension_target("clinical_reasoning"),
                specialty_expertise_score >= self.get_dimension_target("specialty_expertise"),
                patient_safety_score >= self.get_dimension_target("patient_safety")
            ])
            
            # Build specialty-specific data based on the specialty
            specialty_data = self._build_specialty_specific_data(parsed_response, test_case)
            
            return SpecialistEvaluationResult(
                test_case_id=test_case.id,
                query=test_case.query,
                success=success,
                total_response_time_ms=total_response_time_ms,
                tokens_used=tokens_used,
                specialty=self.specialty,
                expected_findings=getattr(test_case, 'expected_findings', set()),
                actual_findings=parsed_response.get("findings", set()),
                medical_accuracy_score=medical_accuracy_score,
                accuracy_breakdown=accuracy_breakdown,
                evidence_referenced=parsed_response.get("evidence", []),
                evidence_quality_score=evidence_quality_score,
                evidence_breakdown=evidence_breakdown,
                clinical_reasoning_score=clinical_reasoning_score,
                reasoning_breakdown=reasoning_breakdown,
                specialty_expertise_score=specialty_expertise_score,
                expertise_breakdown=expertise_breakdown,
                safety_concerns_identified=parsed_response.get("safety_concerns", set()),
                expected_safety_concerns=getattr(test_case, 'expected_safety_concerns', set()),
                patient_safety_score=patient_safety_score,
                safety_breakdown=safety_breakdown,
                tool_calls_made=parsed_response.get("tool_calls", 0),
                tool_success_rate=parsed_response.get("tool_success_rate", 0.0),
                tool_usage_score=tool_usage_score,
                recommendations=parsed_response.get("recommendations", set()),
                expected_recommendations=getattr(test_case, 'expected_recommendations', set()),
                urgency_assessment=parsed_response.get("urgency"),
                confidence_level=parsed_response.get("confidence"),
                specialty_specific_data=specialty_data
            )
            
        except Exception as e:
            logger.error(f"Evaluation failed for test case {test_case.id}: {str(e)}")
            total_response_time_ms = (datetime.now() - start_time).total_seconds() * 1000
            
            return SpecialistEvaluationResult(
                test_case_id=test_case.id,
                query=test_case.query,
                success=False,
                total_response_time_ms=total_response_time_ms,
                tokens_used=0,
                error_message=str(e),
                specialty=self.specialty,
                medical_accuracy_score=0.0,
                evidence_quality_score=0.0,
                clinical_reasoning_score=0.0,
                specialty_expertise_score=0.0,
                patient_safety_score=0.0,
                tool_usage_score=0.0
            )
    
    def _parse_specialist_response(self, response: Any, specialty: MedicalSpecialty) -> Dict[str, Any]:
        """Parse the specialist response to extract structured information"""
        import re
        from services.agents.models import SpecialistResult
        
        # Base parsing for all specialties
        parsed = {
            "findings": set(),
            "evidence": [],
            "recommendations": set(),
            "safety_concerns": set(),
            "confidence": None,
            "urgency": None,
            "tool_calls": 0,
            "tool_success_rate": 0.0
        }
        
        # Convert response to string for parsing
        response_text = str(response)
        
        # Extract common patterns
        # Findings/Diagnoses
        findings_patterns = [
            r"(?:findings?|diagnos[ie]s|assessment):\s*([^\n]+)",
            r"identified:\s*([^\n]+)",
            r"detected:\s*([^\n]+)"
        ]
        for pattern in findings_patterns:
            matches = re.findall(pattern, response_text, re.IGNORECASE)
            for match in matches:
                parsed["findings"].update([f.strip() for f in match.split(",")])
        
        # Evidence/Guidelines
        evidence_patterns = [
            r"(?:guidelines?|evidence|studies?|research):\s*([^\n]+)",
            r"based on:\s*([^\n]+)",
            r"according to:\s*([^\n]+)"
        ]
        for pattern in evidence_patterns:
            matches = re.findall(pattern, response_text, re.IGNORECASE)
            parsed["evidence"].extend(matches)
        
        # Recommendations
        rec_patterns = [
            r"recommend(?:ation)?s?:\s*([^\n]+)",
            r"suggest(?:ion)?s?:\s*([^\n]+)",
            r"advise?:\s*([^\n]+)"
        ]
        for pattern in rec_patterns:
            matches = re.findall(pattern, response_text, re.IGNORECASE)
            for match in matches:
                parsed["recommendations"].update([r.strip() for r in match.split(",")])
        
        # Urgency
        urgency_match = re.search(r"urgency:\s*(\w+)", response_text, re.IGNORECASE)
        if urgency_match:
            parsed["urgency"] = urgency_match.group(1)
        
        # Confidence
        confidence_match = re.search(r"confidence:\s*(\w+)", response_text, re.IGNORECASE)
        if confidence_match:
            parsed["confidence"] = confidence_match.group(1)
        
        # Add specialty-specific parsing
        if specialty == MedicalSpecialty.CARDIOLOGY:
            # Look for cardiovascular-specific terms
            risk_patterns = [r"risk factors?:\s*([^\n]+)", r"cardiovascular risk:\s*([^\n]+)"]
            for pattern in risk_patterns:
                matches = re.findall(pattern, response_text, re.IGNORECASE)
                for match in matches:
                    parsed["findings"].update([f"Risk: {r.strip()}" for r in match.split(",")])
        
        elif specialty == MedicalSpecialty.LABORATORY_MEDICINE:
            # Look for lab values
            lab_patterns = [r"(\w+):\s*([\d.]+)\s*(?:mg/dL|mmol/L|g/dL|%)", r"abnormal:\s*([^\n]+)"]
            for match in re.findall(lab_patterns[0], response_text):
                parsed["findings"].add(f"{match[0]}: {match[1]}")
        
        elif specialty == MedicalSpecialty.PHARMACY:
            # Look for medication-related information
            interaction_patterns = [r"interaction:\s*([^\n]+)", r"contraindication:\s*([^\n]+)"]
            for pattern in interaction_patterns:
                matches = re.findall(pattern, response_text, re.IGNORECASE)
                for match in matches:
                    parsed["safety_concerns"].add(match.strip())
        
        # Tool usage counting (if response contains tool call information)
        tool_matches = re.findall(r"tool_call|execute_health_query", response_text, re.IGNORECASE)
        parsed["tool_calls"] = len(tool_matches)
        
        return parsed
    
    async def _evaluate_medical_accuracy(self, parsed_response: Dict, test_case) -> Tuple[float, Dict]:
        """Evaluate medical accuracy of the specialist's findings"""
        expected_findings = getattr(test_case, 'expected_findings', set())
        actual_findings = parsed_response.get("findings", set())
        
        if not expected_findings:
            # If no expected findings, give full score if reasonable findings present
            score = 1.0 if len(actual_findings) > 0 else 0.5
            breakdown = {"findings_present": score}
        else:
            # Calculate precision and recall
            correct_findings = actual_findings & expected_findings
            precision = len(correct_findings) / len(actual_findings) if actual_findings else 0
            recall = len(correct_findings) / len(expected_findings) if expected_findings else 0
            f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
            
            breakdown = {
                "precision": precision,
                "recall": recall,
                "f1_score": f1_score
            }
            score = f1_score
        
        return score, breakdown
    
    async def _evaluate_evidence_quality(self, parsed_response: Dict, test_case) -> Tuple[float, Dict]:
        """Evaluate quality of evidence and references"""
        evidence = parsed_response.get("evidence", [])
        
        # Score based on presence and quality of evidence
        has_evidence = len(evidence) > 0
        evidence_score = 1.0 if has_evidence else 0.0
        
        # Specialty-specific evidence requirements
        if self.specialty_config.get("requires_guidelines", False):
            has_guidelines = any("guideline" in e.lower() for e in evidence)
            evidence_score *= 0.8 if has_guidelines else 0.5
        
        breakdown = {
            "has_evidence": has_evidence,
            "evidence_count": len(evidence),
            "specialty_requirements_met": evidence_score > 0.8
        }
        
        return evidence_score, breakdown
    
    async def _evaluate_clinical_reasoning(self, parsed_response: Dict, test_case) -> Tuple[float, Dict]:
        """Evaluate clinical reasoning quality"""
        # For now, use LLM judge or simple heuristics
        # Check if response shows logical progression
        response_text = str(parsed_response)
        
        # Look for reasoning indicators
        reasoning_indicators = [
            "because", "therefore", "suggests", "indicates",
            "consistent with", "likely", "differential"
        ]
        
        reasoning_count = sum(1 for indicator in reasoning_indicators 
                            if indicator in response_text.lower())
        
        reasoning_score = min(reasoning_count / 3, 1.0)  # Expect at least 3 reasoning indicators
        
        breakdown = {
            "reasoning_indicators": reasoning_count,
            "logical_flow": reasoning_score
        }
        
        return reasoning_score, breakdown
    
    async def _evaluate_specialty_expertise(self, parsed_response: Dict, test_case) -> Tuple[float, Dict]:
        """Evaluate demonstration of specialty-specific expertise"""
        # Check for specialty-specific terminology and concepts
        focus_areas = self.specialty_config.get("focus_areas", [])
        
        response_text = str(parsed_response).lower()
        found_areas = []
        
        for area in focus_areas:
            if area.replace("_", " ") in response_text:
                found_areas.append(area)
        
        expertise_score = len(found_areas) / len(focus_areas) if focus_areas else 0.5
        
        breakdown = {
            "specialty_focus_areas_covered": len(found_areas),
            "total_focus_areas": len(focus_areas),
            "coverage_ratio": expertise_score
        }
        
        return expertise_score, breakdown
    
    async def _evaluate_patient_safety(self, parsed_response: Dict, test_case) -> Tuple[float, Dict]:
        """Evaluate patient safety considerations"""
        identified_concerns = parsed_response.get("safety_concerns", set())
        expected_concerns = getattr(test_case, 'expected_safety_concerns', set())
        
        # Base score on identification of safety issues
        if expected_concerns:
            correct_concerns = identified_concerns & expected_concerns
            safety_score = len(correct_concerns) / len(expected_concerns)
        else:
            # If no specific concerns expected, score based on appropriate caution
            safety_score = 0.8 if len(identified_concerns) > 0 else 1.0
        
        breakdown = {
            "safety_concerns_identified": len(identified_concerns),
            "expected_concerns_found": safety_score
        }
        
        return safety_score, breakdown
    
    def _calculate_tool_usage_score(self, parsed_response: Dict) -> float:
        """Calculate tool usage effectiveness score"""
        tool_calls = parsed_response.get("tool_calls", 0)
        success_rate = parsed_response.get("tool_success_rate", 0.0)
        
        if tool_calls == 0:
            return 0.5  # Neutral score if no tools used
        
        # Score based on appropriate tool usage and success rate
        return min(tool_calls / 3, 1.0) * success_rate
    
    def _build_specialty_specific_data(self, parsed_response: Dict, test_case) -> Dict[str, Any]:
        """Build specialty-specific data for the evaluation result"""
        specialty_data = {}
        
        if self.specialty == MedicalSpecialty.CARDIOLOGY:
            # Add cardiology-specific data
            specialty_data["risk_factors"] = [f for f in parsed_response.get("findings", []) if "risk" in f.lower()]
            specialty_data["cardiac_tests"] = [f for f in parsed_response.get("findings", []) if any(test in f.lower() for test in ["ecg", "echo", "stress"])]
            
        elif self.specialty == MedicalSpecialty.LABORATORY_MEDICINE:
            # Add lab-specific data
            specialty_data["abnormal_values"] = [f for f in parsed_response.get("findings", []) if "abnormal" in f.lower() or "high" in f.lower() or "low" in f.lower()]
            
        elif self.specialty == MedicalSpecialty.PHARMACY:
            # Add pharmacy-specific data
            specialty_data["medications_reviewed"] = len([f for f in parsed_response.get("findings", []) if "medication" in f.lower()])
            specialty_data["interactions_found"] = len([c for c in parsed_response.get("safety_concerns", []) if "interaction" in c.lower()])
        
        # Add more specialty-specific data as needed
        
        return specialty_data


