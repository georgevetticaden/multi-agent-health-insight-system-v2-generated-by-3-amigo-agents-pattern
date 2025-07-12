"""Core evaluation framework"""

# Import base components
from .evaluators import BaseEvaluator, EvaluationResult

# Import specific evaluators
from .evaluators.cmo import CMOEvaluator, CMOEvaluationResult
from .evaluators.cardiology import CardiologyEvaluator, CardiologyEvaluationResult

# Import report generator
from .report_generator import EvaluationReportGenerator

# For backward compatibility, keep CMOEvaluator at top level
from .evaluator import CMOEvaluator as LegacyCMOEvaluator

__all__ = [
    # Base classes
    "BaseEvaluator",
    "EvaluationResult",
    # Specific evaluators
    "CMOEvaluator",
    "CMOEvaluationResult", 
    "CardiologyEvaluator",
    "CardiologyEvaluationResult",
    # Report generation
    "EvaluationReportGenerator",
    # Legacy support
    "LegacyCMOEvaluator"
]