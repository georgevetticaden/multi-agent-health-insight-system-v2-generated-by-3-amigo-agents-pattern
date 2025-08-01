from enum import Enum
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

class QueryComplexity(Enum):
    SIMPLE = "simple"
    STANDARD = "standard"
    COMPLEX = "complex"
    COMPREHENSIVE = "comprehensive"

class MedicalSpecialty(Enum):
    ENDOCRINOLOGY = "endocrinology"
    CARDIOLOGY = "cardiology"
    NUTRITION = "nutrition"
    PREVENTIVE_MEDICINE = "preventive_medicine"
    LABORATORY_MEDICINE = "laboratory_medicine"
    PHARMACY = "pharmacy"

@dataclass
class SpecialistTask:
    specialist: MedicalSpecialty
    objective: str
    context: str
    expected_output: str
    priority: int = 1
    dependencies: List[str] = field(default_factory=list)
    max_tool_calls: int = 5

@dataclass
class SpecialistResult:
    specialist: MedicalSpecialty
    findings: str
    recommendations: List[str]
    concerns: List[str]
    data_points: Dict[str, Any]
    tool_calls_made: int
    confidence_level: float