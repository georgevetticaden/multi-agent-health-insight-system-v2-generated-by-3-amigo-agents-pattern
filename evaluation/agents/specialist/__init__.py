"""
Medical Specialist Agent Evaluation Suite

This package contains all evaluation-specific content for medical specialist agents:
- dimensions.py: Medical specialist-specific evaluation dimensions
- evaluator.py: Specialist evaluator implementation for all specialties
- test_cases.py: Specialist test case definitions for all specialties
- judge_prompts/: LLM judge prompts for specialist evaluation
"""

from .dimensions import MEDICAL_DIMENSIONS
from .evaluator import SpecialistEvaluator, SpecialistEvaluationResult
from .test_cases import SpecialistTestCase, SpecialistTestCases

__all__ = [
    'MEDICAL_DIMENSIONS', 
    'SpecialistEvaluator',
    'SpecialistEvaluationResult',
    'SpecialistTestCase',
    'SpecialistTestCases'
]