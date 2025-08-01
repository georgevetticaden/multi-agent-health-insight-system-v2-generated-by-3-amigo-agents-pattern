"""
Visualization Agent Evaluation Dimensions

Defines evaluation dimensions specific to the visualization agent.
"""

from evaluation.core.dimensions import dimension_registry, DimensionCategory

# Register Visualization dimensions when this module is imported
VISUALIZATION_DIMENSIONS = {
    "chart_appropriateness": dimension_registry.get_or_create(
        "chart_appropriateness",
        DimensionCategory.VISUALIZATION,
        "Selection of appropriate chart types for data"
    ),
    "data_accuracy": dimension_registry.get_or_create(
        "data_accuracy",
        DimensionCategory.VISUALIZATION,
        "Accurate representation of data in visualizations"
    ),
    "visual_clarity": dimension_registry.get_or_create(
        "visual_clarity",
        DimensionCategory.VISUALIZATION,
        "Clarity and readability of generated visualizations"
    ),
    "self_contained": dimension_registry.get_or_create(
        "self_contained",
        DimensionCategory.VISUALIZATION,
        "Visualizations are self-contained with embedded data"
    ),
    "accessibility": dimension_registry.get_or_create(
        "accessibility",
        DimensionCategory.VISUALIZATION,
        "Accessibility features in visualizations"
    )
}

# Export for easy access
__all__ = ['VISUALIZATION_DIMENSIONS']