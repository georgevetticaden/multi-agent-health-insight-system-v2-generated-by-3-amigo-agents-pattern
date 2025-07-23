"""
Agent-specific evaluation suites

This package contains complete evaluation suites for each agent type.
Each agent subdirectory contains:
- dimensions.py: Agent-specific evaluation dimensions
- evaluator.py: Evaluator implementation
- judge_prompts/: LLM judge prompts

Test cases are now stored in JSON format under evaluation/data/test-suites/
"""

from .cmo import CMO_DIMENSIONS, CMOEvaluator
from .specialist import MEDICAL_DIMENSIONS, SpecialistEvaluator
from .visualization import VISUALIZATION_DIMENSIONS

__all__ = [
    'CMO_DIMENSIONS',
    'CMOEvaluator',
    'MEDICAL_DIMENSIONS',
    'SpecialistEvaluator',
    'VISUALIZATION_DIMENSIONS'
]