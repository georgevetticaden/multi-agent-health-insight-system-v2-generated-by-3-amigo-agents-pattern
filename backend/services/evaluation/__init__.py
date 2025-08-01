"""
Evaluation service module with shared singleton instance.
"""

from .evaluation_service import EvaluationService

# Create a singleton instance to be shared across all API modules
_evaluation_service_instance = None

def get_evaluation_service() -> EvaluationService:
    """Get the shared evaluation service instance."""
    global _evaluation_service_instance
    if _evaluation_service_instance is None:
        import logging
        logger = logging.getLogger(__name__)
        logger.info("Creating new EvaluationService instance")
        _evaluation_service_instance = EvaluationService()
        logger.info(f"Created EvaluationService instance: {id(_evaluation_service_instance)}")
    else:
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Returning existing EvaluationService instance: {id(_evaluation_service_instance)}")
    return _evaluation_service_instance

# For backward compatibility, also export the class
__all__ = ['EvaluationService', 'get_evaluation_service']