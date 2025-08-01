"""
CMO Agent Evaluation Suite

This package contains all evaluation-specific content for the Chief Medical Officer (CMO) agent:
- dimensions.py: CMO-specific evaluation dimensions
- evaluator.py: CMO evaluator implementation
- judge_prompts/: LLM judge prompts for CMO evaluation

Test cases are now stored in JSON format under evaluation/data/test-suites/
"""

from .dimensions import CMO_DIMENSIONS
from .evaluator import CMOEvaluator

__all__ = ['CMO_DIMENSIONS', 'CMOEvaluator']