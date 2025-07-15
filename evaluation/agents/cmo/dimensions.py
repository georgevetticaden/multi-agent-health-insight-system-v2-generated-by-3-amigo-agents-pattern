"""
CMO Agent Evaluation Dimensions

Defines evaluation dimensions specific to the Chief Medical Officer (CMO) agent.
"""

from evaluation.core.dimensions import dimension_registry, DimensionCategory

# Register CMO-specific dimensions when this module is imported
CMO_DIMENSIONS = {
    "complexity_classification": dimension_registry.get_or_create(
        "complexity_classification",
        DimensionCategory.ORCHESTRATION,
        "Accuracy in classifying query complexity (SIMPLE/STANDARD/COMPLEX/COMPREHENSIVE)"
    ),
    "specialty_selection": dimension_registry.get_or_create(
        "specialty_selection",
        DimensionCategory.ORCHESTRATION,
        "Precision in selecting appropriate medical specialists"
    ),
    "task_delegation": dimension_registry.get_or_create(
        "task_delegation",
        DimensionCategory.ORCHESTRATION,
        "Effectiveness of task creation and delegation to specialists"
    ),
    "agent_coordination": dimension_registry.get_or_create(
        "agent_coordination",
        DimensionCategory.ORCHESTRATION,
        "Quality of multi-agent orchestration and coordination"
    ),
    "synthesis_quality": dimension_registry.get_or_create(
        "synthesis_quality",
        DimensionCategory.ORCHESTRATION,
        "Quality of synthesizing findings from multiple specialists"
    )
}

# Export for easy access
__all__ = ['CMO_DIMENSIONS']