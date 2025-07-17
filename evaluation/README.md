# Multi-Agent Health System Evaluation Framework

This evaluation framework implements Anthropic's best practices for testing and evaluating AI systems, featuring a metadata-driven hybrid approach combining deterministic evaluation with LLM-based judgment for comprehensive testing of our multi-agent health insight system.

> **Note**: The evaluation framework follows a **metadata-driven architecture** with clean separation between the evaluation framework and agent implementations. BaseEvaluator provides a generic, extensible foundation while agent-specific evaluators implement domain-specific evaluation logic.

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

The evaluation framework provides comprehensive testing using a **metadata-driven hybrid approach** that combines:
- **Deterministic evaluation** for objective, rule-based metrics
- **LLM Judge evaluation** for semantic understanding and nuanced assessment
- **Metadata-driven configuration** from agent classes for flexible evaluation
- **Comprehensive failure analysis** with root cause identification and improvement suggestions

Following Anthropic's guidance that "LLM-based grading is fast and flexible, scalable and suitable for complex judgment," LLM Judge is integrated as a core component. The framework uses agent metadata to drive evaluation criteria, making it extensible and maintainable.

## Evaluation Architecture

```
Metadata-Driven Evaluation Framework
├── BaseEvaluator (Generic Framework)
│   ├── Metadata Loading & Management
│   ├── Dynamic Dimension Evaluation
│   ├── Component-based Scoring
│   ├── Test Suite Orchestration
│   └── Result Aggregation
├── Agent-Specific Evaluators
│   ├── CMOEvaluator (Orchestration Focus)
│   ├── SpecialistEvaluator (Medical Focus)
│   └── VisualizationEvaluator (Chart Focus)
├── Evaluation Methods
│   ├── Deterministic (Rule-based)
│   ├── LLM Judge (Semantic)
│   └── Hybrid (Combined)
└── LLM Judge Integration
    ├── Failure Analysis
    ├── Root Cause Identification
    └── Improvement Recommendations
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
│   │   │   ├── scoring/          # Component scoring prompts
│   │   │   └── failure_analysis/ # Failure analysis prompts
│   │   └── __init__.py
│   ├── specialist/               # Medical specialist evaluation
│   │   ├── dimensions.py         # Medical specialist dimensions
│   │   ├── evaluator.py          # Multi-specialty evaluator
│   │   ├── test_cases.py         # All specialist test cases
│   │   ├── judge_prompts/        # LLM judge prompts for specialists
│   │   │   ├── scoring/          # Component scoring prompts
│   │   │   └── failure_analysis/ # Failure analysis prompts
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
│   │   ├── base_evaluator.py    # BaseEvaluator with metadata framework
│   │   └── __init__.py
│   ├── llm_judge/                # LLM Judge implementation
│   │   ├── llm_test_judge.py     # Unified LLM Judge class
│   │   ├── specialist_similarity_scorer.py # Rule-based similarity
│   │   └── __init__.py
│   ├── report_generator/         # Report generation
│   │   ├── dynamic_report_generator.py # Metadata-driven reports
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
└── README.md                     # This file
```

## Core Principles and Concepts

This evaluation framework implements Anthropic's testing best practices with a **metadata-driven architecture** that enables flexible, maintainable evaluation across all agent types.

### Key Principles (Following Anthropic's Best Practices)

1. **Metadata-Driven Configuration**: Agent classes define their own evaluation criteria
2. **SMART Success Criteria**: Specific, Measurable, Achievable, Relevant targets
3. **Multi-dimensional Evaluation**: Test multiple aspects independently  
4. **Hybrid Evaluation Methods**: Combine deterministic rules with LLM judgment
5. **Extensible Framework**: BaseEvaluator provides generic infrastructure
6. **Component-Based Scoring**: Break complex dimensions into focused components
7. **Comprehensive Failure Analysis**: Root cause identification with actionable recommendations

### Metadata-Driven Architecture

The framework uses a clean separation between evaluation infrastructure and agent-specific logic:

#### **BaseEvaluator (Generic Framework)**
- Provides metadata loading and management
- Implements dynamic dimension evaluation
- Orchestrates test suite execution with concurrency control
- Aggregates results and generates summaries
- Offers utility methods for common evaluation tasks

#### **Agent-Specific Evaluators**
- Extend BaseEvaluator for domain-specific logic
- Implement agent execution and data collection
- Define component-specific evaluation methods
- Handle agent-specific failure analysis

#### **Agent Metadata Integration**
Agents define their evaluation criteria through `get_evaluation_metadata()` methods:

```python
# Example from CMOAgent
@classmethod
def get_evaluation_metadata(cls) -> AgentEvaluationMetadata:
    return AgentEvaluationMetadata(
        agent_metadata=cls.get_metadata(),
        evaluation_criteria=[
            EvaluationCriteria(
                dimension=complexity_classification,
                target_score=0.90,
                weight=0.20,
                evaluation_method=EvaluationMethod.DETERMINISTIC
            ),
            # ... other criteria
        ],
        quality_components={
            specialty_selection: [
                QualityComponent(
                    name="specialist_precision",
                    weight=0.6,
                    evaluation_method=EvaluationMethod.DETERMINISTIC
                ),
                # ... other components
            ]
        }
    )
```

### Core Concepts and Definitions

#### 1. **Evaluation Dimension Registry**
**Definition**: A centralized system for managing evaluation criteria that avoids duplication and ensures consistency across agents.

**Current evaluation dimensions:**

**CMO Agent:**
1. `complexity_classification` - Accuracy in classifying query complexity (SIMPLE/STANDARD/COMPLEX/COMPREHENSIVE)
2. `specialty_selection` - Precision in selecting appropriate medical specialists
3. `analysis_quality` - Comprehensiveness and quality of medical analysis orchestration
4. `tool_usage` - Effectiveness of health data tool usage
5. `response_structure` - Compliance with expected XML response format

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

Each quality component has:
- **Name**: Clear identifier (e.g., "specialist_precision")
- **Description**: What specifically is being measured
- **Weight**: Relative importance (0.0 to 1.0)
- **Evaluation method**: DETERMINISTIC, LLM_JUDGE, or HYBRID

**Example - Specialty Selection Quality Components:**
| Component | Weight | Evaluation Method | What We Measure |
|-----------|--------|------------------|-----------------|
| Specialist Precision | 60% | Deterministic | Accuracy of specialist selection using similarity scoring |
| Specialist Rationale | 40% | LLM Judge | Quality of reasoning for specialist choices |

#### 3. **Evaluation Criteria and Rubrics**
**Definition**: Specific rules and thresholds that define success for each evaluation dimension.

Each criterion includes:
- **Dimension**: The aspect being evaluated
- **Target Score**: Minimum required score (0.0 to 1.0)
- **Weight**: Importance in overall evaluation
- **Evaluation Method**: Primary evaluation approach
- **Description**: Human-readable explanation

#### 4. **Component-Based Evaluation**
Complex dimensions are broken down into focused components, each evaluated independently and then combined using weighted averages. This allows for:
- **Granular assessment** of different aspects
- **Flexible weighting** based on importance
- **Method diversity** (deterministic + LLM judge within one dimension)
- **Detailed feedback** on specific areas for improvement

## Evaluation Methods

The framework uses three complementary methods, with the appropriate method chosen based on the component's evaluation_method configuration:

### 1. **Deterministic Evaluation**
**When to use**: Structure validation, exact matching, performance metrics, rule-based calculations

**Examples**:
- XML tag validation for agent responses
- Specialist precision using similarity scoring
- Tool call success rates
- Response time measurement

**Implementation**: Implemented in `_evaluate_deterministic_component()` methods in agent evaluators.

### 2. **LLM Judge Evaluation**
**When to use**: Semantic understanding, subjective quality assessment, medical appropriateness

**Examples**:
- Medical accuracy assessment
- Clinical reasoning evaluation
- Specialist selection rationale
- Analysis comprehensiveness

**Implementation**: Implemented in `_evaluate_llm_component()` methods using LLMTestJudge.

### 3. **Hybrid Evaluation**
**When to use**: Dimensions that benefit from both deterministic and semantic evaluation

**Examples**:
- Specialty selection: deterministic precision + LLM rationale assessment
- Analysis quality: deterministic data gathering + LLM comprehensiveness
- Tool usage: deterministic success rates + LLM relevance assessment

**Implementation**: Automatic combination of component scores using metadata-defined weights.

## How Core Concepts Connect

The metadata-driven architecture creates a clean flow from agent definition to evaluation results:

```
Agent Class
    ↓ (defines via get_evaluation_metadata())
Evaluation Metadata
    ↓ (contains)
Evaluation Criteria & Quality Components
    ↓ (loaded by)
BaseEvaluator
    ↓ (uses for)
Dynamic Dimension Evaluation
    ↓ (dispatches to)
Agent-Specific Component Methods
    ↓ (produces)
Component Scores
    ↓ (aggregated into)
Dimension Scores
    ↓ (combined into)
Overall Evaluation Results
```

### Evaluation Process Flow

1. **Agent Metadata Loading**: BaseEvaluator loads metadata from agent classes
2. **Test Case Selection**: Choose from agent-specific test cases
3. **Agent Execution**: Agent-specific evaluator executes the agent
4. **Data Collection**: Raw evaluation data collected (facts, not scores)
5. **Dynamic Evaluation**: BaseEvaluator._evaluate_dimension_dynamic() processes each dimension
6. **Component Evaluation**: Dispatch to deterministic or LLM evaluation methods
7. **Score Aggregation**: Weighted combination of component scores
8. **Failure Analysis**: LLM Judge identifies root causes for failed dimensions
9. **Report Generation**: Comprehensive reports with actionable insights

## Agent Evaluation Specifications

### 1. **CMO Agent (Chief Medical Officer)** - Fully Implemented
**Evaluator**: `CMOEvaluator` extends `BaseEvaluator`
**Architecture**: Metadata-driven with CMO-specific component evaluation methods

**Evaluation Dimensions**:
- **Complexity Classification**: Binary accuracy against expert-labeled complexity
- **Specialty Selection**: Hybrid evaluation with precision calculation + rationale assessment
- **Analysis Quality**: Multi-component evaluation including data gathering, context awareness, comprehensiveness
- **Tool Usage**: Success rate calculation + relevance assessment
- **Response Structure**: XML validation + required field checking

**Key Features**:
- Two-stage evaluation (query analysis + task creation)
- Semantic similarity scoring for specialist selection
- Comprehensive failure analysis with LLM Judge
- Real-time progress tracking

### 2. **Medical Specialist Agents** - All 8 Specialties Supported
**Evaluator**: `SpecialistEvaluator` extends `BaseEvaluator`
**Architecture**: Single evaluator with dynamic specialty configuration

**Supported Specialties**:
- General Practice, Cardiology, Endocrinology, Laboratory Medicine
- Pharmacy, Nutrition, Preventive Medicine, Data Analysis

**Evaluation Dimensions**:
- **Medical Accuracy**: Factual correctness + clinical relevance
- **Evidence Quality**: Source validation + content assessment
- **Clinical Reasoning**: Logical flow + differential diagnosis
- **Specialty Expertise**: Domain knowledge + technical accuracy
- **Patient Safety**: Risk identification + safety recommendations

**Key Features**:
- Specialty-specific evaluation criteria
- Dynamic response parsing
- Medical guideline compliance checking
- Safety concern identification

### 3. **Visualization Agent** - Framework Ready
**Evaluator**: Template available for implementation
**Architecture**: Will extend BaseEvaluator with visualization-specific methods

**Planned Dimensions**:
- Chart appropriateness, data accuracy, visual clarity
- Self-contained design, accessibility features

## Running Evaluations

### Quick Start

```bash
# 1. Navigate to project root
cd /path/to/multi-agent-health-insight-system-v2-generated-by-3-amigo-agents-pattern

# 2. Verify directory structure
ls -la  # Should show: backend/ evaluation/ frontend/ docs/

# 3. Set up environment variable
export ANTHROPIC_API_KEY=your_api_key_here

# 4. Run evaluations
# Single test for quick validation
python -m evaluation.cli.run_evaluation --agent cmo --test example

# Comprehensive evaluation
python -m evaluation.cli.run_evaluation --agent cmo --test comprehensive

# Specialist evaluation with specific specialty
python -m evaluation.cli.run_evaluation --agent specialist --specialty cardiology --test comprehensive

# Real-world test cases
python -m evaluation.cli.run_evaluation --agent cmo --test real-world
```

### Command Line Options

| Parameter | Description | Values | Example |
|-----------|-------------|---------|----------|
| `--agent` | Agent type to evaluate | cmo, specialist | `--agent specialist` |
| `--test` | Type of evaluation | comprehensive, real-world, example | `--test comprehensive` |
| `--specialty` | Specialist type | cardiology, endocrinology, etc. | `--specialty cardiology` |
| `--concurrent` | Max parallel tests | Integer (default: 5) | `--concurrent 10` |

### Agent-Specific Test Types

**CMO Agent:**
- `example`: Single example test
- `complexity`: Complexity classification focused tests
- `specialty`: Specialist selection focused tests
- `comprehensive`: Full test suite
- `real-world`: Production-based tests

**Specialist Agent:**
- `example`: Single test case (use with `--specialty`)
- `comprehensive`: All specialist tests
- `real-world`: Real-world based tests

## Understanding Reports

### Report Structure

The metadata-driven reports provide comprehensive analysis:

#### 1. **Executive Summary**
- Overall pass/fail status based on dimension thresholds
- Dimension performance table with method indicators
- Failed dimension summary with specific scores vs targets

#### 2. **Dimension Analysis**
- Component-level breakdowns for each dimension
- Evaluation method indicators (🔧 Deterministic, 🧠 LLM Judge, 🔄 Hybrid)
- Target vs actual scores with visual progress bars

#### 3. **Test Results Detail**
- Individual test case results with full context
- LLM Judge failure analysis for each failed dimension
- Specific improvement recommendations with file paths

#### 4. **Failure Analysis**
- Root cause analysis across all failures
- Pattern identification by dimension and component
- Priority ranking of issues with expected impact

## Metrics and Scoring

### Metadata-Driven Scoring

Each dimension is scored using its metadata-defined components:

```python
# Example: Specialty Selection Dimension
# Component 1: Specialist Precision (60%, Deterministic)
precision_score = calculate_precision_from_raw_data(actual, expected)

# Component 2: Specialist Rationale (40%, LLM Judge)
rationale_score = await llm_judge.evaluate_rationale(analysis_text)

# Final dimension score (weighted average)
final_score = (precision_score * 0.6) + (rationale_score * 0.4)
```

### Weighted Scoring System

The framework now uses a weighted scoring approach that provides more nuanced evaluation results:

#### **Test Case Scoring**
Each test case receives:
- **Individual dimension scores**: Each dimension evaluated independently (0.0-1.0)
- **Weighted score**: Weighted average across all dimensions based on importance
- **Dimension success rate**: Percentage of dimensions meeting their target scores
- **Evaluation success**: Whether the weighted score meets the overall threshold (default 0.75)

```python
# Weighted score calculation for a test case
weighted_score = sum(
    dimension_score * criteria.weight 
    for dimension_score, criteria in results
) / sum(criteria.weight for criteria in evaluation_criteria)

# Evaluation success (quality-based)
evaluation_success = weighted_score >= 0.75  # Default threshold

# Dimension success rate
dimension_success_rate = passed_dimensions / total_dimensions
```

#### **Overall Suite Scoring**
The overall evaluation uses:
- **Average weighted score**: Mean of all test case weighted scores
- **Success rate**: Percentage of test cases meeting the evaluation threshold
- **Overall success**: Whether average weighted score meets threshold

```python
# Overall suite evaluation
average_weighted_score = mean(test.weighted_score for test in results)
success_rate = sum(1 for test in results if test.evaluation_success) / total_tests
overall_success = average_weighted_score >= 0.75
```

### Scoring Philosophy

The weighted scoring system reflects that:
1. **Partial success is meaningful**: A test scoring 0.74 is much better than one scoring 0.30
2. **Dimensions have different importance**: Critical dimensions (e.g., medical accuracy) have higher weights
3. **Near-misses provide valuable feedback**: Detailed analysis for scores close to targets
4. **Execution vs Evaluation success**: A test can run successfully but fail quality evaluation

## Best Practices

### 1. **Metadata-Driven Design**
- **Define evaluation criteria in agent classes** - Keep evaluation configuration close to implementation
- **Use quality components for complex dimensions** - Enable granular assessment and targeted improvements
- **Leverage BaseEvaluator infrastructure** - Avoid reimplementing common evaluation logic

### 2. **Component-Based Evaluation**
- **Break complex dimensions into focused components** - Makes evaluation more precise and actionable
- **Use appropriate evaluation methods per component** - Deterministic for objective measures, LLM for subjective
- **Weight components based on importance** - Reflect domain expertise in component weights

### 3. **Extensible Architecture**
- **Extend BaseEvaluator for new agent types** - Inherit common infrastructure and utilities
- **Implement agent-specific component methods** - Focus on domain-specific evaluation logic
- **Use metadata to drive evaluation flow** - Avoid hardcoding evaluation criteria

### 4. **Comprehensive Testing**
- **Test across all complexity levels** - Ensure robust performance across different scenarios
- **Include real-world test cases** - Validate against actual usage patterns
- **Use failure analysis for improvements** - Leverage LLM Judge insights for targeted enhancements

## Adding New Agents

To add evaluation support for a new agent type:

### 1. **Extend BaseEvaluator**
```python
class NewAgentEvaluator(BaseEvaluator):
    def __init__(self, agent, anthropic_client):
        super().__init__(anthropic_client)
        self.agent = agent
        self.agent_metadata = agent.get_evaluation_metadata()
    
    async def evaluate_single_test_case(self, test_case):
        # Agent-specific execution and data collection
        
    async def _evaluate_deterministic_component(self, component, dimension, result_data, test_case):
        # Agent-specific deterministic evaluation
        
    async def _evaluate_llm_component(self, component, dimension, result_data, test_case):
        # Agent-specific LLM evaluation
```

### 2. **Define Agent Metadata**
```python
# In agent implementation
@classmethod
def get_evaluation_metadata(cls) -> AgentEvaluationMetadata:
    return AgentEvaluationMetadata(
        agent_metadata=cls.get_metadata(),
        evaluation_criteria=[...],
        quality_components={...}
    )
```

### 3. **Create Test Cases and Prompts**
- Add test cases in `evaluation/agents/{agent_name}/test_cases.py`
- Add LLM judge prompts in `evaluation/agents/{agent_name}/judge_prompts/`
- Update CLI to support the new agent type

## Troubleshooting

### Common Issues

#### 1. **ModuleNotFoundError: No module named 'evaluation'**
**Solution**: Run from project root, not backend directory

#### 2. **ValueError: ANTHROPIC_API_KEY environment variable not set**
**Solution**: Set environment variable or use .env file

#### 3. **Agent metadata not found**
**Solution**: Ensure agent implements `get_evaluation_metadata()` method

#### 4. **Component evaluation errors**
**Solution**: Check that component names match between metadata and evaluator methods

### Debug Mode
```bash
LOG_LEVEL=DEBUG python -m evaluation.cli.run_evaluation --agent cmo --test example
```

## Current Capabilities

### **Metadata-Driven Architecture**
- BaseEvaluator provides generic, extensible evaluation framework
- Agent-specific evaluators focus on domain logic
- Clean separation between evaluation infrastructure and agent implementation

### **Weighted Scoring System**
- Nuanced evaluation using weighted dimension scores
- Distinguishes between execution success and evaluation quality
- Average weighted scores determine overall test suite success
- Near-miss analysis provides targeted feedback for scores close to thresholds

### **Component-Based Evaluation**
- Complex dimensions broken into focused components
- Flexible weighting and evaluation method assignment
- Granular feedback for targeted improvements

### **Unified LLM Judge**
- Single LLMTestJudge class for all evaluation and failure analysis
- Comprehensive failure analysis with root cause identification
- Near-miss detection with specific improvement suggestions
- Structured prompt organization by agent and component

### **Enhanced BaseEvaluator**
- Comprehensive utility methods for common evaluation tasks
- Dynamic dimension evaluation framework
- Robust error handling and logging
- Extensible design for new agent types

## Future Enhancements

1. **Advanced Analytics**
   - Performance trending over time
   - Comparative analysis across agents
   - Predictive failure detection

2. **Production Integration**
   - Real-time evaluation monitoring
   - Automated improvement suggestions
   - Continuous integration testing

3. **Enhanced Visualization**
   - Interactive evaluation dashboards
   - Component-level performance tracking
   - Failure pattern visualization

---

This evaluation framework provides a robust, metadata-driven foundation for evaluating multi-agent health systems. The architecture enables consistent, comprehensive evaluation while maintaining flexibility for agent-specific requirements.