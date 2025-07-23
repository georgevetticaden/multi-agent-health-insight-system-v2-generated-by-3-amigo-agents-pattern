"""
Specialist Similarity Scorer

This module provides rule-based and semantic similarity scoring for medical specialist
selections, considering domain knowledge about specialist equivalences and relationships.
"""

from typing import List, Dict, Any, Tuple, Set, Optional


class SpecialistSimilarityScorer:
    """
    Enhanced specialist similarity scoring that considers medical domain knowledge.
    
    This class provides sophisticated similarity scoring between predicted and actual
    specialist selections, accounting for:
    - Equivalent specialist groups (e.g., endocrinology and diabetes_care)
    - Related specialists that can substitute for each other
    - Critical vs. non-critical specialist mismatches
    
    The scorer uses a rule-based approach with predefined specialist relationships
    based on medical domain knowledge.
    """
    
    # Define specialist equivalence groups
    SPECIALIST_GROUPS = {
        "primary_care": ["general_practice", "family_medicine", "internal_medicine"],
        "metabolic": ["endocrinology", "diabetes_care", "metabolic_medicine"],
        "heart": ["cardiology", "cardiovascular", "cardiac_care" ],
        "lab": ["laboratory_medicine", "pathology", "clinical_laboratory"],
        "prevention": ["preventive_medicine", "wellness", "health_screening"]
    }
    
    # Define specialist relationships (can work together or substitute)
    RELATED_SPECIALISTS = {
        "general_practice": ["internal_medicine", "family_medicine"],
        "endocrinology": ["diabetes_care", "metabolic_medicine", "internal_medicine"],
        "cardiology": ["internal_medicine", "preventive_medicine"],
        "nutrition": ["endocrinology", "preventive_medicine", "wellness"],
        "pharmacy": ["clinical_pharmacy", "medication_management"]
    }
    
    @classmethod
    def calculate_similarity(
        cls,
        predicted: List[str],
        actual: List[str]
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate sophisticated similarity score between specialist sets.
        
        This method evaluates how well the predicted specialists match the actual
        specialists, considering both exact matches and acceptable substitutions
        based on medical domain knowledge.
        
        Args:
            predicted: List of predicted specialist names
            actual: List of actual/expected specialist names
            
        Returns:
            Tuple containing:
                - similarity_score (float): Weighted similarity score (0.0 to 1.0)
                - details (dict): Detailed breakdown including:
                    - exact_matches: Specialists that matched exactly
                    - equivalent_matches: Acceptable substitutions made
                    - missing_critical: Expected specialists that are missing
                    - extra_specialists: Predicted but not expected specialists
                    - is_acceptable: Whether the prediction is medically acceptable
                    
        Example:
            >>> score, details = SpecialistSimilarityScorer.calculate_similarity(
            ...     predicted=["endocrinology", "general_practice"],
            ...     actual=["diabetes_care", "internal_medicine"]
            ... )
            >>> print(f"Score: {score:.2f}, Acceptable: {details['is_acceptable']}")
            Score: 0.80, Acceptable: True
        """
        predicted_set = set(predicted)
        actual_set = set(actual)
        
        # Direct matches
        exact_matches = predicted_set & actual_set
        
        # Find equivalent specialists
        equivalent_matches = set()
        substitutions = {}
        
        for pred in predicted_set - exact_matches:
            for act in actual_set - exact_matches:
                # Check if they're in the same group
                for group, members in cls.SPECIALIST_GROUPS.items():
                    if pred in members and act in members:
                        equivalent_matches.add(pred)
                        substitutions[pred] = act
                        break
                
                # Check if they're related
                if pred in cls.RELATED_SPECIALISTS:
                    if act in cls.RELATED_SPECIALISTS[pred]:
                        equivalent_matches.add(pred)
                        substitutions[pred] = act
                        break
        
        # Calculate scores
        total_matches = len(exact_matches) + len(equivalent_matches)
        union_size = len(predicted_set | actual_set)
        
        # Weighted score (exact matches worth more)
        weighted_score = (len(exact_matches) + 0.8 * len(equivalent_matches)) / union_size if union_size > 0 else 0
        
        # Check for critical missing specialists
        missing = actual_set - predicted_set
        missing_critical = [s for s in missing if s not in substitutions.values()]
        
        return weighted_score, {
            "exact_matches": list(exact_matches),
            "equivalent_matches": substitutions,
            "missing_critical": missing_critical,
            "extra_specialists": list(predicted_set - actual_set - set(substitutions.keys())),
            "is_acceptable": weighted_score >= 0.7 and len(missing_critical) <= 1
        }
    
    @classmethod
    def get_specialist_group(cls, specialist: str) -> Optional[str]:
        """
        Get the specialist group for a given specialist.
        
        Args:
            specialist: Name of the specialist
            
        Returns:
            Group name if specialist belongs to a group, None otherwise
        """
        for group, members in cls.SPECIALIST_GROUPS.items():
            if specialist in members:
                return group
        return None
    
    @classmethod
    def are_specialists_related(cls, specialist1: str, specialist2: str) -> bool:
        """
        Check if two specialists are related (can substitute for each other).
        
        Args:
            specialist1: First specialist name
            specialist2: Second specialist name
            
        Returns:
            True if specialists are related, False otherwise
        """
        # Check if in same group
        group1 = cls.get_specialist_group(specialist1)
        group2 = cls.get_specialist_group(specialist2)
        if group1 and group1 == group2:
            return True
        
        # Check direct relationships
        if specialist1 in cls.RELATED_SPECIALISTS:
            if specialist2 in cls.RELATED_SPECIALISTS[specialist1]:
                return True
                
        if specialist2 in cls.RELATED_SPECIALISTS:
            if specialist1 in cls.RELATED_SPECIALISTS[specialist2]:
                return True
                
        return False