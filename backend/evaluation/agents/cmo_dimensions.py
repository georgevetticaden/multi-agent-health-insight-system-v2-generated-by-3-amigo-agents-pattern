from evaluation.core.dimensions import EvaluationDimension, dimension_registry


# CMO-specific dimensions
CMO_DIMENSIONS = {
    "complexity_classification": EvaluationDimension(
        name="complexity_classification",
        description="Accuracy in classifying query complexity",
        category="accuracy"
    ),
    "specialty_selection": EvaluationDimension(
        name="specialty_selection",
        description="Precision in selecting appropriate medical specialists",
        category="accuracy"
    )
}

# Register CMO dimensions
for dim in CMO_DIMENSIONS.values():
    dimension_registry.register(dim)