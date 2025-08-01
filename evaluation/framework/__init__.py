"""Core evaluation framework"""

# Import base components
from .evaluators import BaseEvaluator, EvaluationResult

# Import report generator
from .report_generator import DynamicHTMLReportGenerator

# Note: Agent-specific evaluators are now in evaluation.agents.{agent_name}
# Import them directly from there, e.g.:
# from evaluation.agents.cmo import CMOEvaluator
# from evaluation.agents.specialist import SpecialistEvaluator

__all__ = [
    # Base classes
    "BaseEvaluator",
    "EvaluationResult",
    # Report generation
    "DynamicHTMLReportGenerator"
]