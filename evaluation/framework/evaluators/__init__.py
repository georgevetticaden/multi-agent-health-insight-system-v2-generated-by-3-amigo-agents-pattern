"""
Multi-Agent Evaluation Framework

This module provides a modular evaluation framework for testing different types of agents
in the multi-agent health insight system. Each agent type has its own specialized evaluator
that extends the base evaluation capabilities.

Agent Types:
- CMO (Chief Medical Officer): Orchestrator agent evaluation
- Cardiology: Specialist agent evaluation for cardiovascular medicine
"""

from .base_evaluator import BaseEvaluator, EvaluationResult

__all__ = ["BaseEvaluator", "EvaluationResult"]