"""
Agent-specific evaluation suites

This package contains complete evaluation suites for each agent type.
Each agent subdirectory contains:
- dimensions.py: Agent-specific evaluation dimensions
- evaluator.py: Evaluator implementation
- test_cases.py: Test case definitions
- judge_prompts/: LLM judge prompts
"""

from .cmo import CMO_DIMENSIONS, CMOEvaluator, CMOTestCases
from .specialist import (
    MEDICAL_DIMENSIONS, 
    SpecialistEvaluator, 
    SpecialistTestCases
)
from .visualization import VISUALIZATION_DIMENSIONS

__all__ = [
    'CMO_DIMENSIONS',
    'CMOEvaluator',
    'CMOTestCases',
    'MEDICAL_DIMENSIONS',
    'SpecialistEvaluator',
    'SpecialistTestCases',
    'VISUALIZATION_DIMENSIONS'
]