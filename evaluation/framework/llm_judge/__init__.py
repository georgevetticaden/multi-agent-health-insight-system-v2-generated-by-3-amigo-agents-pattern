"""
LLM Judge Module for Agent Evaluation

This module provides AI-powered evaluation capabilities for the multi-agent
health insight system. It includes both scoring and failure analysis functionality
to comprehensively evaluate agent performance.

Components:
- LLMTestJudge: Main class for all LLM evaluation operations
- SpecialistSimilarityScorer: Rule-based specialist matching scorer
- ScoringResult: Result from scoring operations
- FailureAnalysis: Detailed failure analysis with recommendations
"""

from .llm_test_judge import (
    LLMTestJudge,
    ScoringResult,
    FailureAnalysis
)

from .specialist_similarity_scorer import SpecialistSimilarityScorer

__all__ = [
    'LLMTestJudge',
    'ScoringResult',
    'FailureAnalysis',
    'SpecialistSimilarityScorer'
]