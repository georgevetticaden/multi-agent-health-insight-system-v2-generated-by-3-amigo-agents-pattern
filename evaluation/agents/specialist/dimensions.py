"""
Medical Specialist Agent Evaluation Dimensions

Defines evaluation dimensions specific to medical specialist agents.
"""

from evaluation.core.dimensions import dimension_registry, DimensionCategory

# Register Medical Specialist dimensions when this module is imported
MEDICAL_DIMENSIONS = {
    "medical_accuracy": dimension_registry.get_or_create(
        "medical_accuracy",
        DimensionCategory.MEDICAL,
        "Accuracy of medical assessments and recommendations"
    ),
    "evidence_quality": dimension_registry.get_or_create(
        "evidence_quality",
        DimensionCategory.MEDICAL,
        "Quality and appropriateness of evidence provided"
    ),
    "clinical_reasoning": dimension_registry.get_or_create(
        "clinical_reasoning",
        DimensionCategory.MEDICAL,
        "Sound clinical reasoning and decision-making"
    ),
    "specialty_expertise": dimension_registry.get_or_create(
        "specialty_expertise",
        DimensionCategory.MEDICAL,
        "Demonstration of specialty-specific knowledge"
    ),
    "patient_safety": dimension_registry.get_or_create(
        "patient_safety",
        DimensionCategory.MEDICAL,
        "Appropriate safety considerations and warnings"
    )
}

# Export for easy access
__all__ = ['MEDICAL_DIMENSIONS']