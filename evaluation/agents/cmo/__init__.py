"""
CMO Agent Evaluation Suite

This package contains all evaluation-specific content for the Chief Medical Officer (CMO) agent:
- dimensions.py: CMO-specific evaluation dimensions
- evaluator.py: CMO evaluator implementation
- test_cases.py: CMO test case definitions
- judge_prompts/: LLM judge prompts for CMO evaluation
"""

from .dimensions import CMO_DIMENSIONS
from .evaluator import CMOEvaluator
from .test_cases import TestCase, CMOTestCases

__all__ = ['CMO_DIMENSIONS', 'CMOEvaluator', 'TestCase', 'CMOTestCases']