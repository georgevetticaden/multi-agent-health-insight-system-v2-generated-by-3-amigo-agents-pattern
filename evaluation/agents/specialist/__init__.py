"""
Medical Specialist Agent Evaluation Suite

This package contains all evaluation-specific content for medical specialist agents:
- dimensions.py: Medical specialist-specific evaluation dimensions
- evaluator.py: Specialist evaluator implementation for all specialties
- judge_prompts/: LLM judge prompts for specialist evaluation

Test cases are now stored in JSON format under evaluation/data/test-suites/
"""

from .dimensions import MEDICAL_DIMENSIONS
from .evaluator import SpecialistEvaluator, SpecialistEvaluationResult

__all__ = [
    'MEDICAL_DIMENSIONS', 
    'SpecialistEvaluator',
    'SpecialistEvaluationResult'
]