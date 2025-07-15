# Multi-Agent Health System Evaluation Framework

This evaluation framework implements Anthropic's best practices for testing and evaluating AI systems, featuring an integrated hybrid approach combining deterministic evaluation with LLM-based judgment for comprehensive testing of our multi-agent health insight system.

> **Note**: The evaluation framework follows an **agent-centric organization** where all evaluation content for each agent (dimensions, evaluators, test cases, and judge prompts) is consolidated under `evaluation/agents/{agent_name}/`. This provides better modularity and makes it easier to add new agents.

## Table of Contents
- [Overview](#overview)
- [Evaluation Architecture](#evaluation-architecture)
- [Directory Structure](#directory-structure)
- [Core Principles and Concepts](#core-principles-and-concepts)
- [Evaluation Methods](#evaluation-methods)
- [How Core Concepts Connect](#how-core-concepts-connect)
- [Agent Evaluation Specifications](#agent-evaluation-specifications)
- [Running Evaluations](#running-evaluations)
- [Understanding Reports](#understanding-reports)
- [Metrics and Scoring](#metrics-and-scoring)
- [Best Practices](#best-practices)

## Overview

The evaluation framework provides comprehensive testing using a **hybrid approach** that combines:
- **Deterministic evaluation** for objective, rule-based metrics
- **LLM Judge evaluation** for semantic understanding and nuanced assessment
- **Integrated failure analysis** with root cause identification and improvement suggestions

Following Anthropic's guidance that "LLM-based grading is fast and flexible, scalable and suitable for complex judgment," LLM Judge is integrated as a core component. This provides:
- More accurate semantic evaluation
- Automatic root cause analysis for failures
- Specific prompt improvement suggestions
- Pattern identification across test failures

### Foundation Model vs. Application-Centric Evaluation

**Foundation Model Evaluation** (like MMLU, GSM8k, HELM):
- Assesses general capabilities of base LLMs
- Uses public benchmarks across broad domains
- Useful for initial model selection
- Like "standardized tests" for LLMs

**Application-Centric Evaluation** (Our Focus):
- Assesses specific pipeline performance on specific tasks
- Uses domain-specific metrics and real-world data
- Captures nuances of medical multi-agent workflows
- Like "job-specific performance evaluations"

**Why Generic Metrics Are Insufficient**:
Research shows that generic metrics like "helpfulness" or "truthfulness" provide limited value for specific applications. Our health system requires:
- **Medical accuracy** rather than general factual accuracy
- **Clinical reasoning** rather than general reasoning
- **Safety warnings** appropriate for health contexts
- **Multi-agent coordination** specific to medical workflows

As noted in the research: *"You should be extremely skeptical of generic metrics for your application. In most cases, they are a distraction and provide illusory benefit."*

## Evaluation Architecture

```
Multi-Agent Evaluation Framework (Hybrid Approach)
├── Deterministic Evaluation (Fast, Objective)
│   ├── Response Structure Validation
│   ├── Tool Call Success Metrics
│   ├── Basic Classification Checks
│   └── Performance Metrics
└── LLM Judge Evaluation (Semantic, Nuanced)
    ├── Component Scoring
    │   ├── Comprehensive Approach (concept coverage)
    │   ├── Specialist Selection (medical appropriateness)
    │   ├── Analysis Quality (clinical reasoning)
    │   └── Concern Identification (risk assessment)
    ├── Failure Analysis
    │   ├── Root Cause Identification
    │   ├── Pattern Detection
    │   └── Failure Mode Analysis
    └── Recommendations Engine
        ├── Specific Prompt Improvements
        ├── Priority Ranking
        └── Expected Impact Metrics
```

## Directory Structure

```
evaluation/
├── agents/                        # Agent-specific evaluation suites
│   ├── cmo/                      # CMO agent evaluation
│   │   ├── dimensions.py         # CMO-specific evaluation dimensions
│   │   ├── evaluator.py          # CMO evaluator implementation
│   │   ├── test_cases.py         # CMO test case definitions
│   │   ├── judge_prompts/        # LLM judge prompts for CMO
│   │   │   ├── complexity/       # Complexity classification analysis
│   │   │   ├── quality/          # Analysis quality evaluation
│   │   │   ├── specialist/       # Specialist selection comparison
│   │   │   ├── tool_usage/       # Tool usage effectiveness
│   │   │   └── response_structure/ # XML structure validation
│   │   └── __init__.py
│   ├── specialist/               # Medical specialist evaluation
│   │   ├── dimensions.py         # Medical specialist dimensions
│   │   ├── evaluator.py          # Multi-specialty evaluator
│   │   ├── test_cases.py         # All specialist test cases
│   │   ├── judge_prompts/        # LLM judge prompts for specialists
│   │   │   ├── medical_accuracy/ # Medical accuracy evaluation
│   │   │   ├── comprehensive_coverage/ # Coverage evaluation
│   │   │   ├── risk/             # Risk assessment evaluation
│   │   │   ├── recommendation_quality/ # Recommendation quality
│   │   │   └── tool_usage/       # Tool usage effectiveness
│   │   └── __init__.py
│   └── visualization/            # Visualization agent evaluation
│       ├── dimensions.py         # Visualization dimensions
│       ├── evaluator.py          # (TODO) Visualization evaluator
│       ├── test_cases.py         # (TODO) Visualization test cases
│       └── __init__.py
├── core/                         # Core evaluation types and interfaces
│   ├── dimensions.py             # Dimension types and registry
│   ├── results.py                # Evaluation result types
│   ├── rubrics.py                # Evaluation rubric logic
│   ├── agent_evaluation_metadata.py # Bridge to agent metadata
│   └── __init__.py
├── framework/                    # Evaluation execution framework
│   ├── evaluators/               # Evaluation execution components
│   │   ├── base_evaluator.py    # Base evaluator class
│   │   └── __init__.py
│   ├── llm_judge/                # LLM Judge implementation
│   │   ├── llm_test_judge.py     # LLM Judge class
│   │   └── __init__.py
│   ├── report_generator/         # Report generation
│   │   ├── dynamic_report_generator.py # Main report generator
│   │   ├── report_template.html  # HTML template
│   │   └── __init__.py
│   └── __init__.py
├── cli/                          # Command-line interface
│   ├── run_evaluation.py         # Multi-agent CLI runner
│   └── __init__.py
├── utils/                        # Evaluation utilities
│   ├── logging_config.py         # Logging configuration
│   ├── check_setup.py            # Setup verification
│   └── __init__.py
├── test_runs/                    # All test outputs (created on first run)
│   └── {agent}-{test_type}_{timestamp}/ # Unique directory per test run
│       ├── evaluation.log        # Log file for this run
│       ├── results.json          # Raw evaluation results
│       └── report/               # Report directory
│           ├── report.html       # Beautiful HTML report
│           ├── raw_results.json  # Copy of raw results
│           └── *.png            # Visualization charts
└── README.md                     # This file (includes methodology)
```

## Core Principles and Concepts

This evaluation framework implements Anthropic's testing best practices and follows the **Analyze-Measure-Improve lifecycle** from application-centric AI evaluation research. It bridges the "Three Gulfs" of LLM development by providing systematic evaluation methods for our medical multi-agent system.

### Key Principles (Following Anthropic's Best Practices)

1. **SMART Success Criteria**: Specific, Measurable, Achievable, Relevant targets
2. **Multi-dimensional Evaluation**: Test multiple aspects independently  
3. **Hybrid Evaluation Methods**: Combine deterministic rules with LLM judgment
4. **Ground Truth Validation**: Expert-labeled test cases
5. **Continuous Improvement**: Learn from failures and iterate
6. **Application-Centric Focus**: Domain-specific metrics over generic benchmarks

### The Three Gulfs of LLM Development

Our evaluation framework addresses the fundamental challenges identified in LLM application development:

#### 1. **Gulf of Comprehension** (Developer → Data)
**What it is**: The gap between understanding our data and our pipeline's behavior on that data.

**In our system**: We need to understand the variety of health queries users ask and how our multi-agent system responds across different medical domains. Without systematic evaluation, we can't manually inspect every query or agent response.

**How we address it**: Through the **Analyze** phase - systematic error analysis using structured datasets and trace examination.

#### 2. **Gulf of Specification** (Developer → LLM Pipeline)  
**What it is**: The gap between what we intend our system to do and what we actually specify in prompts.

**In our system**: Health queries are complex and multi-faceted. Our prompts must clearly specify how the CMO should classify complexity, which specialists to engage, and how specialists should format their responses.

**How we address it**: Through the **Measure** phase - quantitative evaluation of whether our prompts elicit the intended behavior from agents.

#### 3. **Gulf of Generalization** (Data → LLM Pipeline)
**What it is**: The gap between our training/test data and how the system performs on new, diverse inputs.

**In our system**: Medical queries vary greatly in complexity, urgency, and domain. Our agents must generalize across different patient contexts and medical specialties.

**How we address it**: Through the **Improve** phase - iterative refinement based on evaluation findings.

### Core Concepts and Definitions

#### 1. **Evaluation Dimension Registry**
**Definition**: A centralized system for managing evaluation criteria that avoids duplication and ensures consistency across agents.

**What it solves**: In traditional evaluation systems, each agent might define its own version of "accuracy" or "quality," leading to inconsistent measurement. Our registry provides a single source of truth.

**How it works**: 
- **Common dimensions** shared across all agents (analysis_quality, tool_usage, response_structure, error_handling)
- **Agent-specific dimensions** tailored to each agent type (e.g., `complexity_classification` for CMO, `medical_accuracy` for specialists)
- **Dynamic dimension creation** through the `dimension_registry.get_or_create()` method

**Connection to research**: This implements the principle of "application-centric evaluation" where metrics are designed for our specific use case rather than generic benchmarks.

```python
# Example of dimension registration
medical_accuracy = dimension_registry.get_or_create(
    "medical_accuracy",
    DimensionCategory.MEDICAL,
    "Accuracy of medical assessments and recommendations"
)
```

**Current evaluation dimensions:**

**CMO Agent:**
1. `complexity_classification` - Accuracy in classifying query complexity (SIMPLE/STANDARD/COMPLEX/COMPREHENSIVE)
2. `specialty_selection` - Precision in selecting appropriate medical specialists
3. `task_delegation` - Effectiveness of task creation and delegation to specialists
4. `agent_coordination` - Quality of multi-agent orchestration and coordination
5. `synthesis_quality` - Quality of synthesizing findings from multiple specialists
6. Plus common dimensions: `analysis_quality`, `tool_usage`, `response_structure`, `error_handling`

**Medical Specialist Agents (All 8 Specialties):**
1. `medical_accuracy` - Accuracy of medical assessments and recommendations
2. `evidence_quality` - Quality and appropriateness of evidence provided
3. `clinical_reasoning` - Sound clinical reasoning and decision-making
4. `specialty_expertise` - Demonstration of specialty-specific knowledge
5. `patient_safety` - Appropriate safety considerations and warnings
6. Plus common dimensions: `analysis_quality`, `tool_usage`, `response_structure`, `error_handling`

**Visualization Agent:**
1. `chart_appropriateness` - Selection of appropriate chart types for data
2. `data_accuracy` - Accurate representation of data in visualizations
3. `visual_clarity` - Clarity and readability of generated visualizations
4. `self_contained` - Visualizations are self-contained with embedded data
5. `accessibility` - Accessibility features in visualizations

#### 2. **Quality Components**
**Definition**: Specific, measurable sub-aspects that comprise complex evaluation dimensions.

**What it solves**: Some dimensions like "medical_accuracy" are too broad to evaluate as a single metric. Quality components break them into focused, measurable parts.

**How it works**: Each quality component has:
- **Name**: Clear identifier (e.g., "factual_accuracy")
- **Description**: What specifically is being measured
- **Weight**: Relative importance (0.0 to 1.0)
- **Evaluation method**: "deterministic", "llm_judge", or "hybrid"

**Connection to research**: This follows the principle of "reference-based vs reference-free metrics" where we choose the most appropriate evaluation method for each component.

**Example - Medical Accuracy Quality Components:**
| Component | Weight | Evaluation Method | What We Measure |
|-----------|--------|------------------|-----------------|
| Factual Accuracy | 60% | LLM Judge | Correctness of medical facts and interpretations |
| Clinical Relevance | 40% | LLM Judge | Relevance to the clinical question |

#### 3. **Evaluation Criteria and Rubrics**
**Definition**: Specific rules and thresholds that define success for each evaluation dimension.

**What it solves**: Without clear criteria, evaluation becomes subjective and inconsistent. Criteria provide objective standards for pass/fail decisions.

**How it works**: Each criterion includes:
- **Dimension**: The aspect being evaluated
- **Target Score**: Minimum required score (0.0 to 1.0)
- **Weight**: Importance in overall evaluation
- **Measurement Method**: "deterministic", "llm_judge", or "hybrid"
- **Measurement Description**: How the score is calculated

**Connection to research**: This implements "direct grading against rubrics" with clear definitions for consistent evaluation.

**Why binary thresholds work**: Following research findings, we use binary pass/fail decisions rather than complex Likert scales, which produce more consistent and actionable results.

**Example - CMO Agent Criteria:**
```python
EvaluationCriteria(
    dimension=CMO_DIMENSIONS["complexity_classification"],
    description="Accuracy in classifying query complexity",
    target_score=0.90,
    weight=0.20,
    measurement_method="hybrid",
    measurement_description="Binary accuracy against expert-labeled complexity"
)
```

#### 4. **Agent-Centric Test Case Structure**
**Definition**: Test cases organized by agent type with flexible, specialty-specific expectations.

**What it solves**: Generic test cases don't capture the nuances of different medical specialties. Our structure allows for both common patterns and specialty-specific requirements.

**How it works**:
- **Multi-specialty test cases** for specialist agents
- **Specialty-specific expectations** through flexible dictionaries
- **Real-world test cases** based on actual production queries
- **Synthetic test case generation** using structured dimensions

**Connection to research**: This follows the "synthetic data generation" methodology using dimensions and tuples to create representative test cases.

**Test case dimensions for health queries**:
- **Complexity**: Simple, standard, complex, comprehensive
- **Medical domain**: Cardiology, endocrinology, pharmacy, etc.
- **Urgency**: Routine, urgent, emergency
- **Data quality**: Complete, partial, conflicting

**Example - Specialist Test Case:**
```python
SpecialistTestCase(
    id="cardio_lipid_001",
    specialty=MedicalSpecialty.CARDIOLOGY,
    query="Analyze cholesterol trends over 12 years",
    expected_findings={"persistent_low_hdl_syndrome", "mixed_dyslipidemia"},
    expected_recommendations={"increase_statin_intensity", "lifestyle_modification"},
    expected_safety_concerns={"cardiovascular_risk"},
    specialty_specific_expectations={
        "focus_areas": ["lipid_management", "risk_stratification"],
        "clinical_guidelines": ["2018 AHA/ACC Cholesterol Guidelines"]
    }
)
```

#### 5. **LLM Judge Rubrics**
**Definition**: Structured prompts that guide LLM-based evaluation with clear, consistent criteria.

**What it solves**: LLM evaluation can be inconsistent without proper prompts. Our rubrics provide structured, repeatable evaluation that mimics human expert judgment.

**How it works**: Following Anthropic's guidance for "detailed, clear rubrics," our LLM Judge uses structured evaluation prompts organized by agent and dimension.

**Connection to research**: This implements "LLM-as-judge" evaluation methodology, which is "fast and flexible, scalable and suitable for complex judgment."

**Key features**:
- **Structured format**: Consistent XML-based evaluation structure
- **Domain expertise**: Medical knowledge embedded in prompts
- **Scoring guidance**: Clear 0.0-1.0 scoring with explanations
- **Failure analysis**: Root cause identification and improvement suggestions

```xml
<evaluation_task>
Evaluate the medical accuracy of this specialist analysis.

<query>{original_query}</query>
<specialty>{medical_specialty}</specialty>
<agent_response>{agent_response}</agent_response>
<expected_findings>{expected_findings}</expected_findings>

Score 0.0-1.0 based on:
1. Factual accuracy of medical statements
2. Clinical relevance to the query
3. Appropriateness for the specialty
4. Safety considerations

<thinking>
Analyze each medical statement for accuracy...
</thinking>

<score>0.85</score>
<analysis>The specialist correctly identified key conditions but missed some risk factors</analysis>
</evaluation_task>
```

## Evaluation Methods

Our evaluation framework uses three complementary methods, following the research principle of choosing the most appropriate evaluation method for each specific criterion:

### 1. Reference-Based Evaluation (Deterministic)
**Definition**: Compares LLM output against known, ground-truth answers using exact matching or rule-based validation.

**When to use**: 
- Structure validation (XML tags, JSON format)
- Exact matching (tool calls, API parameters)
- Performance metrics (response time, token usage)

**Advantages**: 
- Fast execution (0.1s)
- Consistent results
- No API costs
- Objective measurement

**Examples in our system**:
- XML tag validation for agent responses
- Tool call parameter verification
- Response time measurement
- Success rate tracking

**Connection to research**: This implements "reference-based metrics" that compare against a known correct answer or format.

### 2. Reference-Free Evaluation (LLM Judge)
**Definition**: Evaluates LLM output based on inherent properties or adherence to rules, without requiring a specific "golden" answer.

**When to use**:
- Medical appropriateness and accuracy
- Clinical reasoning quality
- Concept coverage and comprehensiveness
- Semantic understanding

**Advantages**:
- Understands context and nuance
- Handles variations in correct answers
- Provides explanations and failure analysis
- Can assess subjective qualities

**Examples in our system**:
- Medical accuracy assessment
- Clinical reasoning evaluation
- Specialist selection appropriateness
- Safety concern identification

**Models Used**: Claude-3.5-Sonnet for comprehensive evaluation

**Connection to research**: This implements "reference-free metrics" that check desired properties directly, and "LLM-as-judge" methodology for complex judgment.

### 3. Hybrid Evaluation
**Definition**: Combines deterministic rules with LLM judgment for comprehensive assessment.

**When to use**:
- Complex criteria that benefit from both approaches
- Fallback mechanisms for edge cases
- Multi-step validation processes

**Examples in our system**:
- Complexity classification: deterministic rules with LLM fallback for edge cases
- Tool usage evaluation: deterministic success checking + LLM quality assessment
- Evidence quality: rule-based source validation + LLM content assessment

**Connection to research**: This addresses the research finding that "combining approaches" often yields more robust evaluation than any single method.

## Core Evaluation Types and Interfaces

The evaluation framework uses several core types that ensure consistency and reusability across all agents:

### Evaluation Dimensions
```python
from evaluation.core.dimensions import EvaluationDimension, DimensionCategory

# Categories organize dimensions by type
class DimensionCategory(Enum):
    COMMON = "common"           # Shared across all agents
    ORCHESTRATION = "orchestration"  # CMO-specific
    MEDICAL = "medical"         # Specialist-specific
    VISUALIZATION = "visualization"  # Visualization-specific
```

### Quality Components
```python
from evaluation.core.dimensions import QualityComponent

# Components break down complex dimensions
component = QualityComponent(
    name="factual_accuracy",
    description="Correctness of medical facts and interpretations",
    weight=0.6,
    evaluation_method="llm_judge"
)
```

### Evaluation Criteria
```python
from evaluation.core.dimensions import EvaluationCriteria

# Criteria define success thresholds
criteria = EvaluationCriteria(
    dimension=medical_accuracy_dimension,
    description="Medical accuracy of specialist analysis",
    target_score=0.85,
    weight=0.30,
    measurement_method="llm_judge"
)
```

### Results and Scoring
```python
from evaluation.core.results import DimensionEvaluation, ComponentEvaluation

# Results capture both scores and explanations
result = DimensionEvaluation(
    dimension="medical_accuracy",
    score=0.92,
    passed=True,
    components=[component_eval1, component_eval2],
    explanation="Strong medical reasoning with minor gaps"
)
```

### Relationship to Agent Metadata
The core evaluation types maintain a clean separation between agent metadata (what the agent is) and evaluation logic (how we test it):

1. **Agent classes** define their metadata in `services/agents/metadata/core.py`
2. **Evaluation framework** uses these types through `evaluation/core/agent_evaluation_metadata.py`
3. **No duplicate definitions** exist between agent and evaluation code

## The Analyze-Measure-Improve Lifecycle

Our evaluation framework implements the **Analyze-Measure-Improve lifecycle** from application-centric AI evaluation research, specifically adapted for multi-agent health systems:

### Phase 1: Analyze (Qualitative Error Analysis)
**Goal**: Bridge the Gulf of Comprehension by systematically identifying failure modes.

**Process**:
1. **Create Starting Dataset**: Generate ~100 diverse health queries covering different complexities, specialties, and scenarios
2. **Open Coding**: Manually examine agent traces to identify patterns and failure modes
3. **Axial Coding**: Group similar failures into structured categories (e.g., "missing_constraints", "persona_mismatch")
4. **Theoretical Saturation**: Continue until no new failure types emerge

**In our system**: 
- Use synthetic query generation with dimensions (complexity, specialty, urgency)
- Examine full multi-agent traces (CMO → specialists → visualization)
- Identify health-specific failure modes (medical accuracy, safety concerns, clinical reasoning)

**Output**: Structured taxonomy of failure modes with examples

### Phase 2: Measure (Quantitative Evaluation)
**Goal**: Bridge the Gulf of Specification by quantifying how often failures occur.

**Process**:
1. **Develop Evaluators**: Create automated tests for each identified failure mode
2. **Scale Testing**: Run evaluations across larger datasets (1000+ queries)
3. **Statistical Analysis**: Compute failure rates, confidence intervals, and patterns
4. **Prioritization**: Identify most frequent and impactful failures

**In our system**:
- Implement both deterministic and LLM-judge evaluators
- Test across all 8 medical specialties
- Measure agent-specific performance (CMO orchestration, specialist accuracy)
- Track performance over time and across different query types

**Output**: Quantitative metrics and failure rate data

### Phase 3: Improve (Targeted Interventions)
**Goal**: Bridge the Gulf of Generalization by making data-driven improvements.

**Process**:
1. **Prompt Engineering**: Refine prompts based on specific failure patterns
2. **Architecture Changes**: Modify multi-agent workflows to address systemic issues
3. **Data Augmentation**: Add training examples for problematic cases
4. **Validation**: Re-run evaluations to measure improvement

**In our system**:
- Update specialist prompts based on medical accuracy failures
- Refine CMO complexity classification logic
- Improve specialist selection algorithms
- Enhance safety warning systems

**Output**: Improved system performance with measured gains

### Cycling Through the Lifecycle
This creates a continuous improvement loop:
1. **Analyze** new production data for emerging failure modes
2. **Measure** system performance on representative test sets
3. **Improve** based on quantitative findings
4. **Repeat** to maintain and enhance system quality

## How Core Concepts Connect

The evaluation framework components work together in a structured flow aligned with the lifecycle:

```
Agent Metadata (Backend)
    ↓
Evaluation Dimensions (Registry-based)
    ↓
Test Cases (Agent-specific)
    ↓
Agent Execution (Multi-agent workflow)
    ↓
Evaluation Methods (Deterministic + LLM Judge + Hybrid)
    ↓
Evaluation Criteria (Thresholds & targets)
    ↓
Results & Reports (Pass/Fail + Improvements)
```

### Evaluation Process Flow

1. **Agent Metadata Loading**: Agents define their own evaluation metadata through `get_evaluation_metadata()` methods
2. **Dimension Registration**: Dimensions are registered in the global registry by agent-specific modules
3. **Test Case Selection**: Choose from agent-specific test cases with specialty support
4. **Agent Execution**: Execute the agent with the test case input
5. **Multi-Dimensional Evaluation**: Each dimension measured independently using appropriate methods
6. **Scoring & Aggregation**: Individual scores computed and weighted for overall assessment
7. **Failure Analysis**: LLM Judge identifies root causes and improvement recommendations
8. **Report Generation**: Comprehensive reports with visualizations and actionable insights

## Agent Evaluation Specifications

The framework supports evaluation of all agents in the multi-agent health system:

### 1. **CMO Agent (Chief Medical Officer)** - Fully Implemented
- **Orchestration Dimensions**: Query complexity classification, specialist selection, task delegation, agent coordination
- **Synthesis Capabilities**: Quality of synthesizing findings from multiple specialists
- **Common Dimensions**: Analysis quality, tool usage, response structure, error handling
- **Test Coverage**: 10+ test cases across all complexity levels

### 2. **Medical Specialist Agents** - All 8 Specialties Supported
The specialist evaluation system now supports all medical specialties with a single, flexible evaluator:

**Supported Specialties:**
- **General Practice**: Comprehensive assessment, differential diagnosis, referrals
- **Cardiology**: Heart health, blood pressure, cardiovascular disease
- **Endocrinology**: Diabetes, thyroid, hormones, metabolic health
- **Laboratory Medicine**: Lab tests, blood work, diagnostic results
- **Pharmacy**: Medications, dosages, interactions, adherence
- **Nutrition**: Diet, weight, nutritional health
- **Preventive Medicine**: Risk factors, screening, prevention
- **Data Analysis**: Statistical analysis, trends, correlations

**Evaluation Dimensions (All Specialties):**
- Medical Accuracy: Factual correctness and clinical relevance
- Evidence Quality: Strength and relevance of evidence sources
- Clinical Reasoning: Logical flow and differential diagnosis
- Specialty Expertise: Domain knowledge and technical accuracy
- Patient Safety: Risk identification and safety recommendations

**Dynamic Specialty Configuration:**
Each specialty has specific focus areas and evaluation criteria:
```python
# Example - Cardiology Configuration
"cardiology": {
    "focus_areas": ["diagnoses", "risk_factors", "urgency"],
    "key_findings": ["cardiac_conditions", "cardiovascular_risks"],
    "requires_guidelines": True
}
```

**Test Coverage**: 9 test cases across all specialties with real-world scenarios

### 3. **Visualization Agent** - Framework Ready
- **Dimensions Defined**: Chart appropriateness, data accuracy, visual clarity, self-contained design, accessibility
- **Evaluator**: Template available for implementation
- **Test Cases**: Framework ready for test case addition


## Running Evaluations

### Quick Start

The evaluation framework implements the **Analyze-Measure-Improve** lifecycle. Here's how to run evaluations:

```bash
# 1. Navigate to project root (where you see backend/, evaluation/, frontend/ directories)
# IMPORTANT: Do NOT run from backend/ directory!
cd /path/to/your/multi-agent-health-insight-system-v2-generated-by-3-amigo-agents-pattern

# 2. Verify you're in the right directory
ls -la  # Should show: backend/ evaluation/ frontend/ docs/ requirements/
pwd    # Should end with your project name, NOT /backend

# 3. Set up environment variable (required for LLM evaluation)
# Option 1: Set environment variable directly
export ANTHROPIC_API_KEY=your_api_key_here

# Option 2: Use existing backend/.env file (automatically detected)
# The CLI will automatically load from backend/.env if it exists

# Option 3: Create .env file in project root
echo "ANTHROPIC_API_KEY=your_api_key_here" > .env

# Option 4: Create .env file in evaluation directory
echo "ANTHROPIC_API_KEY=your_api_key_here" > evaluation/.env

# 4. Run evaluations following the Analyze-Measure-Improve lifecycle

# ANALYZE Phase: Run small-scale qualitative evaluation
python -m evaluation.cli.run_evaluation --agent cmo --test example
python -m evaluation.cli.run_evaluation --agent specialist --test example --specialty cardiology

# MEASURE Phase: Run comprehensive quantitative evaluation
python -m evaluation.cli.run_evaluation --agent cmo --test comprehensive
python -m evaluation.cli.run_evaluation --agent specialist --test comprehensive

# Medical Specialist Evaluation (all 8 specialties supported)
python -m evaluation.cli.run_evaluation --agent specialist --specialty cardiology --test comprehensive
python -m evaluation.cli.run_evaluation --agent specialist --specialty endocrinology --test comprehensive
python -m evaluation.cli.run_evaluation --agent specialist --specialty pharmacy --test comprehensive
python -m evaluation.cli.run_evaluation --agent specialist --specialty nutrition --test comprehensive
python -m evaluation.cli.run_evaluation --agent specialist --specialty laboratory_medicine --test comprehensive
python -m evaluation.cli.run_evaluation --agent specialist --specialty preventive_medicine --test comprehensive
python -m evaluation.cli.run_evaluation --agent specialist --specialty data_analysis --test comprehensive
python -m evaluation.cli.run_evaluation --agent specialist --specialty general_practice --test comprehensive

# IMPROVE Phase: Run real-world tests to validate improvements
python -m evaluation.cli.run_evaluation --agent cmo --test real-world
python -m evaluation.cli.run_evaluation --agent specialist --test real-world

# Run specific test categories (following structured dimensions)
python -m evaluation.cli.run_evaluation --agent cmo --test complexity
python -m evaluation.cli.run_evaluation --agent cmo --test specialty
python -m evaluation.cli.run_evaluation --agent specialist --category lipid_management
```

**Following Research Best Practices**:
- Start with small datasets (~100 queries) to reach theoretical saturation
- Use structured dimensions (complexity, specialty, urgency) for test case generation
- Combine reference-based (deterministic) and reference-free (LLM judge) evaluation
- Focus on application-specific metrics rather than generic benchmarks

### Setup Verification

Before running evaluations, verify your setup:

```bash
# 1. Check that you're in the right directory
pwd  # Should end with your project name, NOT /backend

# 2. Verify directory structure
ls -la  # Should show: backend/ evaluation/ frontend/ docs/ requirements/

# 3. Test framework imports (without API key)
python -c "
import sys
import os
sys.path.append('backend')
from evaluation.agents.specialist import SpecialistTestCases
from services.agents.models import MedicalSpecialty
print('✅ Framework imports work correctly')
print('✅ Ready to run evaluations')
"

# 4. Check API key (if you have one)
echo $ANTHROPIC_API_KEY  # Should show your API key
```

### Command Line Options

| Parameter | Description | Values | Example |
|-----------|-------------|---------|----------|
| `--agent` | Agent type to evaluate | cmo, specialist | `--agent specialist` |
| `--test` | Type of evaluation | comprehensive, real-world, example | `--test comprehensive` |
| `--specialty` | Specialist type (for specialist agent) | cardiology, endocrinology, pharmacy, etc. | `--specialty cardiology` |
| `--category` | Test category | Varies by agent | `--category diabetes` |
| `--test-ids` | Specific test IDs | Comma-separated IDs | `--test-ids cardio_001,endo_001` |
| `--concurrent` | Max parallel tests | Integer (default: 5) | `--concurrent 10` |

### Agent-Specific Test Types

**CMO Agent:**
- `example`: Single example test (good for quick validation)
- `complexity`: Complexity classification tests (tests CMO's ability to classify query complexity)
- `specialty`: Specialty selection tests (tests CMO's specialist selection logic)
- `comprehensive`: Full test suite (all CMO test cases)
- `real-world`: Production-based tests (tests based on actual user queries)

**Specialist Agent:**
- `example`: Single test case (quick validation, use with `--specialty` flag)
- `comprehensive`: All specialist tests (all specialties combined)
- `real-world`: Real-world based tests (production query patterns)

**Note**: For specialist agents, use the `--specialty` flag to specify which specialty to test:
- `cardiology`: Cardiology-specific tests
- `endocrinology`: Endocrinology-specific tests
- `pharmacy`: Pharmacy-specific tests  
- `nutrition`: Nutrition-specific tests
- `laboratory_medicine`: Laboratory medicine tests
- `preventive_medicine`: Preventive medicine tests
- `data_analysis`: Data analysis tests
- `general_practice`: General practice tests

**Combining Parameters:**
```bash
# Use --specialty with --test for targeted testing
python -m evaluation.cli.run_evaluation --agent specialist --specialty cardiology --test example
python -m evaluation.cli.run_evaluation --agent specialist --specialty endocrinology --test comprehensive

# Use --category for specific clinical areas
python -m evaluation.cli.run_evaluation --agent specialist --category diabetes
python -m evaluation.cli.run_evaluation --agent specialist --category lipid_management

# Use --test-ids for specific test cases
python -m evaluation.cli.run_evaluation --agent specialist --test-ids cardio_lipid_001,endo_diabetes_001
```

## Understanding Reports

### Report Structure

Evaluation reports are generated as both HTML and markdown with comprehensive analysis:

#### 1. **Executive Summary**
- Overall pass/fail status
- Dimension performance table with visual indicators
- Failed dimension summary with counts

#### 2. **Dimension Analysis**
- Detailed breakdown by evaluation dimension
- Target vs actual scores
- Method indicators (🔧 Deterministic, 🧠 LLM Judge, 🔄 Hybrid)

#### 3. **Test Results Detail**
- Individual test case results
- LLM Judge failure analysis for each failed dimension
- Specific improvement recommendations with file paths

#### 4. **Failure Analysis**
- Root cause analysis across all failures
- Pattern identification
- Priority ranking of issues

#### 5. **Visualizations**
- Dimension performance charts
- Complexity distribution analysis
- Response time metrics
- Specialty selection patterns

### Report Features

**Interactive Elements:**
- Collapsible test sections
- Progress bars for dimension scores
- Animated failure analysis cards
- Embedded charts and visualizations

**Actionable Insights:**
- Specific prompt file paths for improvements
- Priority levels for each issue
- Expected impact assessments
- Implementation recommendations

## Metrics and Scoring

### Dimension Registry Scoring

Each dimension is scored independently using its configured method:

```python
# Example dimension scoring
medical_accuracy_score = await evaluator.evaluate_medical_accuracy(
    parsed_response, test_case
)
# Returns: (score: float, breakdown: Dict[str, float])
```

### Overall Evaluation Logic

```python
# All dimensions must meet their targets independently
overall_pass = all(
    dimension_score >= dimension_target 
    for dimension_score, dimension_target in dimensions
)

# Weighted average for reporting
weighted_score = sum(
    score * weight for score, weight in dimension_weights
) / sum(weights)
```

### Rubric-based Scoring

Each evaluation criteria defines:
- **Target Score**: Minimum required performance
- **Weight**: Contribution to overall score
- **Measurement Method**: How the score is calculated
- **Quality Components**: Sub-metrics for complex dimensions

## Best Practices

### 1. Agent-Centric Organization
- **Keep all evaluation content for an agent in one directory** - This improves maintainability and makes it easier to understand what's being tested
- **Use consistent naming patterns across agents** - Follow the pattern: `evaluation/agents/{agent_name}/`
- **Maintain clean separation** - Agent metadata stays in `services/`, evaluation logic in `evaluation/`

### 2. Dimension Management (Following Research Principles)
- **Register dimensions in agent-specific modules** - Avoid duplication while allowing customization
- **Use descriptive dimension names and categories** - Clear names reduce ambiguity in evaluation
- **Leverage common dimensions across similar agents** - Consistency enables comparison across agents
- **Prefer binary judgments over Likert scales** - Research shows binary decisions are more consistent and actionable

### 3. Test Case Design (Application-Centric Approach)
- **Create specialty-specific test cases with appropriate context** - Generic test cases miss domain-specific failures
- **Include real-world scenarios based on production queries** - Synthetic data should reflect actual usage patterns
- **Use structured dimensions for synthetic generation** - Follow the tuple-based approach (complexity, specialty, urgency)
- **Aim for ~100 diverse test cases per agent** - This typically reaches theoretical saturation for most systems

### 4. LLM Judge Optimization (Structured Evaluation)
- **Organize prompts by agent and dimension** - Clear organization improves maintainability
- **Use structured evaluation formats** - XML-based prompts with clear scoring guidance
- **Provide clear rubrics and scoring criteria** - Detailed rubrics reduce variability in LLM judgments
- **Include failure analysis capabilities** - LLM judges should identify root causes and suggest improvements

### 5. Continuous Improvement (Lifecycle Integration)
- **Regular evaluation runs across all agents** - Automated testing prevents regression
- **Track metrics over time** - Trend analysis identifies gradual degradation
- **Update test cases based on production patterns** - Keep evaluation relevant to actual usage
- **Refine evaluation criteria based on results** - Evaluation criteria should evolve with system understanding
- **Follow the Analyze-Measure-Improve cycle** - Systematic improvement based on evidence

## Adding New Agents

To add evaluation support for a new agent type, follow this pattern:

### 1. Create Agent Evaluation Directory
```bash
mkdir -p evaluation/agents/{agent_name}
```

### 2. Define Evaluation Dimensions
```python
# evaluation/agents/{agent_name}/dimensions.py
from evaluation.core.dimensions import dimension_registry, DimensionCategory

{AGENT_NAME}_DIMENSIONS = {
    "dimension1": dimension_registry.get_or_create(
        "dimension1",
        DimensionCategory.MEDICAL,
        "Description of dimension1"
    ),
    # ... other dimensions
}
```

### 3. Create Test Cases
```python
# evaluation/agents/{agent_name}/test_cases.py
@dataclass
class {AgentName}TestCase:
    id: str
    query: str
    expected_findings: Set[str]
    # ... other fields

class {AgentName}TestCases:
    @staticmethod
    def get_all_test_cases() -> List[{AgentName}TestCase]:
        # Return test cases
```

### 4. Implement Evaluator
```python
# evaluation/agents/{agent_name}/evaluator.py
from evaluation.framework.evaluators import BaseEvaluator

class {AgentName}Evaluator(BaseEvaluator):
    def get_evaluation_dimensions(self) -> List[str]:
        # Return dimensions from {AGENT_NAME}_DIMENSIONS
    
    async def evaluate_single_test_case(self, test_case) -> EvaluationResult:
        # Implement evaluation logic
```

### 5. Add LLM Judge Prompts
```bash
mkdir -p evaluation/agents/{agent_name}/judge_prompts/{dimension}
# Add .txt files with evaluation prompts
```

### 6. Update Package Structure
```python
# evaluation/agents/{agent_name}/__init__.py
from .dimensions import {AGENT_NAME}_DIMENSIONS
from .evaluator import {AgentName}Evaluator
from .test_cases import {AgentName}TestCases

__all__ = ['{AGENT_NAME}_DIMENSIONS', '{AgentName}Evaluator', '{AgentName}TestCases']
```

### 7. Update CLI
```python
# evaluation/cli/run_evaluation.py
from evaluation.agents.{agent_name} import {AgentName}Evaluator, {AgentName}TestCases

# Add to evaluator_map
self.evaluator_map["{agent_name}"] = self._create_{agent_name}_evaluator
self.test_case_map["{agent_name}"] = {AgentName}TestCases
```

## Advanced Features

### Multi-Specialty Support
The specialist evaluation system supports dynamic specialty configuration:
- Single evaluator handles all 8 medical specialties
- Specialty-specific focus areas and requirements
- Dynamic response parsing based on specialty
- Flexible test case structure with specialty-specific expectations

### Agent Metadata Integration
Agents define their own evaluation metadata:
```python
# In agent implementation
@classmethod
def get_evaluation_metadata(cls, specialty: MedicalSpecialty) -> AgentEvaluationMetadata:
    # Return evaluation criteria and quality components
```

### Dimension Registry System
Flexible dimension management:
- Common dimensions shared across agents
- Agent-specific dimensions registered dynamically
- Category-based organization (COMMON, ORCHESTRATION, MEDICAL, etc.)
- Singleton registry for consistency

### Pattern Analysis
Automatic identification of patterns across failures:
- Common failure modes by dimension
- Specialty-specific issues
- Systematic prompt weaknesses
- Performance trends over time

## Troubleshooting

### Setup Verification
```bash
# Run from project root, not backend directory
python -m evaluation.utils.check_setup
```

### Common Issues

#### 1. **ModuleNotFoundError: No module named 'evaluation'**
**Problem**: Running from wrong directory
**Solution**: 
```bash
# ❌ Wrong - Don't run from backend directory
cd backend
python -m evaluation.cli.run_evaluation --agent cmo --test example

# ✅ Correct - Run from project root
cd /path/to/multi-agent-health-insight-system-v2-generated-by-3-amigo-agents-pattern
python -m evaluation.cli.run_evaluation --agent cmo --test example
```

#### 2. **ValueError: ANTHROPIC_API_KEY environment variable not set**
**Problem**: Missing API key
**Solution**: The CLI automatically looks for .env files in multiple locations. Choose any option:

```bash
# Option 1: Set environment variable directly
export ANTHROPIC_API_KEY=your_api_key_here

# Option 2: If you already have backend/.env, it will be automatically detected
# No action needed if backend/.env already contains ANTHROPIC_API_KEY

# Option 3: Create .env file in project root
echo "ANTHROPIC_API_KEY=your_api_key_here" > .env

# Option 4: Create .env file in evaluation directory  
echo "ANTHROPIC_API_KEY=your_api_key_here" > evaluation/.env

# Option 5: Copy existing backend/.env to project root
cp backend/.env .env
```

**Recent Fix**: The CLI now automatically loads .env files from project root, backend/, and evaluation/ directories in that order.

#### 3. **Import Errors for Agent Classes**
**Problem**: Python path issues
**Solution**: Ensure you're running from project root where the evaluation CLI can find the backend directory

#### 4. **Dimension Not Found Errors**
**Problem**: Agent-specific dimensions not properly registered
**Solution**: Check that agent-specific dimensions are properly imported in the dimension registry

#### 5. **Test Case Structure Errors**
**Problem**: Test case structure doesn't match agent expectations
**Solution**: Verify test case structure matches the `SpecialistTestCase` format

#### 6. **LLM Judge Parsing Errors**
**Problem**: Errors like "got an unexpected keyword argument" or "object has no attribute 'value'"
**Solution**: These issues have been resolved in recent updates. If you encounter them:
- Ensure you're running the latest version of the evaluation framework
- Check that dataclass structures match the JSON responses from LLM Judge
- Verify that dimension attribute access uses `.name` instead of `.value`

**Recent Fix**: Updated all LLM Judge dataclasses to match JSON response structures and fixed dimension attribute access throughout the codebase.

### Debug Mode
```bash
# Enable debug logging
LOG_LEVEL=DEBUG python -m evaluation.cli.run_evaluation --agent specialist --test example --specialty cardiology
```

### Directory Structure Verification
If you're unsure about the correct directory structure:
```bash
# You should see these directories from project root:
ls -la
# Should show: backend/ evaluation/ frontend/ docs/ requirements/

# The evaluation CLI should be here:
ls -la evaluation/cli/
# Should show: run_evaluation.py
```

## Recent Enhancements

### 1. **Agent-Centric Reorganization** (Current)
- All evaluation content consolidated under `evaluation/agents/{agent_name}/`
- Improved modularity and discoverability
- Consistent patterns across all agents

### 2. **Multi-Specialty Specialist Support** (Current)
- Single `SpecialistEvaluator` handles all 8 medical specialties
- Dynamic specialty configuration and response parsing
- Comprehensive test coverage across all specialties

### 3. **Dimension Registry System** (Current)
- Flexible dimension management with category-based organization
- Common dimensions shared across agents
- Dynamic dimension registration
- Clean separation of concerns

### 4. **Agent Metadata Integration** (Current)
- Agents define their own evaluation metadata
- Clean separation between agent metadata and evaluation logic
- Evaluation criteria and quality components defined per agent

### 5. **Enhanced Test Case Structure** (Current)
- Specialty-specific expectations through flexible dictionaries
- Real-world test cases based on production queries
- Category-based test organization
- Comprehensive coverage across all agent types

### 6. **LLM Judge Prompt Consolidation** (Current)
- Consolidated all LLM Judge prompts under agent-centric organization
- Removed duplicate framework-level prompts directory
- All prompts now located in `evaluation/agents/{agent_name}/judge_prompts/`
- Improved maintainability and consistency

## Future Enhancements

1. **Visualization Agent Implementation**
   - Complete evaluator implementation
   - Chart-specific test cases
   - Visual quality assessment

2. **End-to-End Testing**
   - Full conversation flow validation
   - Multi-agent coordination testing
   - System-level performance metrics

3. **Advanced Analytics**
   - Performance trending over time
   - Comparative analysis across agents
   - Predictive failure detection

4. **Production Integration**
   - Real-time evaluation monitoring
   - Automated alert systems
   - Continuous improvement loops

---

## Research References and Further Reading

This evaluation framework is built on research-backed principles from application-centric AI evaluation:

### Core Research Documentation
- **Primary Reference**: [`docs/evals/llm_eval_docs_complete.md`](../docs/evals/llm_eval_docs_complete.md) - Complete guide to LLM evaluation methodology
- **Key Concepts**: The Three Gulfs of LLM Development, Analyze-Measure-Improve lifecycle, Reference-based vs Reference-free evaluation
- **Methodologies**: Grounded theory approach to error analysis, structured test case generation, LLM-as-judge evaluation

### Research Principles Applied
1. **Error Analysis**: Systematic identification of failure modes using open coding and axial coding
2. **Test Case Generation**: Structured dimensions and tuples for diverse, representative test cases
3. **Evaluation Methods**: Hybrid approach combining deterministic rules with LLM judgment
4. **Application-Centric Focus**: Domain-specific metrics over generic benchmarks
5. **Continuous Improvement**: Iterative refinement based on quantitative evidence

### Key Research Findings Implemented
- **"You should be extremely skeptical of generic metrics"** - We use medical-specific dimensions
- **"Binary judgments are more consistent than Likert scales"** - We use pass/fail criteria
- **"LLM-based grading is fast and flexible"** - We integrate LLM judges for complex assessment
- **"~100 test cases typically reach theoretical saturation"** - Our test suite sizing follows this guidance
- **"Synthetic data should target anticipated failures"** - Our generation uses structured dimensions

### Methodology Alignment
- **Grounded Theory**: Our error analysis follows open coding → axial coding → theoretical saturation
- **Structured Test Generation**: We use (complexity, specialty, urgency) dimensions for comprehensive coverage
- **Hybrid Evaluation**: We combine reference-based (deterministic) with reference-free (LLM judge) methods
- **Application-Centric**: We focus on health-specific metrics rather than generic benchmarks

For questions or contributions, see the project documentation.