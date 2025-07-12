# Multi-Agent Health System Evaluation Framework

This evaluation framework implements Anthropic's best practices for testing and evaluating AI systems, featuring an integrated hybrid approach combining deterministic evaluation with LLM-based judgment for comprehensive testing of our multi-agent health insight system.

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
├── framework/                     # Core evaluation infrastructure
│   ├── evaluators/                # Agent-specific evaluators
│   │   ├── base_evaluator.py     # Base evaluation logic
│   │   ├── cmo/                  # CMO agent evaluation
│   │   │   ├── cmo_evaluator.py  # CMO-specific evaluator
│   │   │   └── __init__.py
│   │   └── cardiology/           # Cardiology specialist evaluation
│   │       ├── cardiology_evaluator.py
│   │       └── __init__.py
│   ├── llm_judge/                # LLM-based test failure analysis
│   │   ├── llm_test_judge.py     # Core LLM Judge implementation
│   │   ├── prompts/              # Externalized evaluation prompts
│   │   │   ├── cmo/              # CMO evaluation prompts
│   │   │   │   ├── complexity/   # Complexity classification analysis
│   │   │   │   ├── quality/      # Analysis quality evaluation
│   │   │   │   ├── specialist/   # Specialist selection comparison
│   │   │   │   ├── tool_usage/   # Tool usage effectiveness
│   │   │   │   └── response_structure/ # XML structure validation
│   │   │   └── cardiology/       # Cardiology evaluation prompts
│   │   │       ├── diagnostic/   # Diagnostic accuracy evaluation
│   │   │       ├── guideline/    # Guideline adherence evaluation
│   │   │       ├── risk/         # Risk assessment evaluation
│   │   │       ├── treatment/    # Treatment quality evaluation
│   │   │       └── reasoning/    # Clinical reasoning evaluation
│   │   └── __init__.py
│   ├── report_generator/         # HTML report generation
│   │   ├── report_generator.py   # Main coordinator (HTML + visualizations)
│   │   ├── html_report_generator.py # Template processor with Jinja2
│   │   ├── report_template.html  # Beautiful designer template
│   │   └── __init__.py
│   ├── evaluator.py              # Legacy CMO evaluator (backward compatibility)
│   └── __init__.py
├── cli/                          # Command-line interface
│   ├── run_evaluation.py         # Multi-agent CLI runner
│   └── __init__.py
├── criteria/                     # Success criteria and rubrics
│   ├── cmo/                      # CMO evaluation criteria
│   │   ├── cmo_evaluation_criteria.py
│   │   └── __init__.py
│   └── cardiology/               # Cardiology evaluation criteria
│       ├── cardiology_evaluation_criteria.py
│       └── __init__.py
├── test_cases/                   # Test case definitions
│   ├── cmo/                      # CMO test cases
│   │   ├── cmo_test_cases.py
│   │   └── __init__.py
│   └── cardiology/               # Cardiology test cases
│       ├── cardiology_test_cases.py
│       └── __init__.py
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

This evaluation framework implements Anthropic's testing best practices by mapping their core concepts to our medical multi-agent system.

### Key Principles (Following Anthropic's Best Practices)

1. **SMART Success Criteria**: Specific, Measurable, Achievable, Relevant targets
2. **Multi-dimensional Evaluation**: Test multiple aspects independently
3. **Hybrid Evaluation Methods**: Combine deterministic rules with LLM judgment
4. **Ground Truth Validation**: Expert-labeled test cases
5. **Continuous Improvement**: Learn from failures and iterate

### Core Concepts and Definitions

#### 1. **Evaluation Dimension**
An evaluation dimension is a specific aspect of model performance that can be measured independently. Following Anthropic's approach, each dimension should be:
- **Measurable**: Produces a numeric score (0-1 scale)
- **Independent**: Can be evaluated separately from other dimensions
- **Actionable**: Failures point to specific improvements

**Current evaluation dimensions:**

**CMO Agent:**
1. `complexity_classification` - Binary accuracy with LLM Judge for edge cases
2. `specialty_selection` - F1 score with medical appropriateness via LLM Judge
3. `analysis_quality` - Weighted components evaluated by LLM Judge
4. `tool_usage` - Deterministic success rate
5. `response_structure` - Deterministic XML validation

**Specialist Agents** (Coming Soon):
- Domain expertise accuracy
- Tool calling precision
- Confidence score calibration
- Finding relevance
- Recommendation quality

**Visualization Agent** (Coming Soon):
- Chart appropriateness
- Data accuracy
- Visual clarity
- Insight extraction

#### 2. **Quality Components (Analysis Quality Dimension Only)**
Quality components are the specific measurable aspects that make up the **Analysis Quality dimension**. These are now evaluated using LLM Judge for better semantic understanding:

| Component | Weight | Evaluation Method | What We Measure |
|-----------|--------|------------------|-----------------|
| Data Gathering | 20% | Deterministic | Did the agent make appropriate tool calls? |
| Context Awareness | 15% | LLM Judge | Recognition of temporal/contextual elements |
| Specialist Rationale | 20% | LLM Judge | Quality of reasoning for specialist selection |
| Comprehensive Approach | 25% | LLM Judge | Semantic coverage of key medical concepts |
| Concern Identification | 20% | LLM Judge | Identification of relevant health risks |

#### 3. **Evaluation Criteria (Rubrics)**
Evaluation criteria define the specific rules and thresholds for each dimension. Per Anthropic's best practices, criteria should be:
- **Objective**: Based on measurable outputs, not subjective judgment
- **Graduated**: Multiple levels of performance, not just pass/fail
- **Domain-specific**: Tailored to the specific use case

**Example in our framework:**
```python
class CMOEvaluationRubric:
    COMPLEXITY_ACCURACY_TARGET = 0.90    # 90% correct classification required
    SPECIALTY_F1_TARGET = 0.85          # 85% F1 score for specialist selection
    ANALYSIS_QUALITY_TARGET = 0.80      # 80% quality score required
    TOOL_SUCCESS_TARGET = 0.90          # 90% tool call success rate
    STRUCTURE_VALIDITY_TARGET = 0.95    # 95% valid XML responses
```

#### 4. **Test Case Structure**
A test case is a structured input-output pair with expected behaviors. Following Anthropic's testing methodology:
- **Ground truth labels**: Expert-validated expected outputs
- **Comprehensive coverage**: Tests edge cases and failure modes
- **Real-world grounding**: Based on actual usage patterns

**Example in our framework:**
```python
TestCase(
    id="complex_001",
    query="Analyze medication adherence patterns and correlate with cholesterol",
    expected_complexity="COMPLEX",
    expected_specialties={"pharmacy", "cardiology", "data_analysis"},
    key_data_points=["medications", "adherence", "cholesterol", "correlation"],
    category="medications",
    notes="Tests multi-factor correlation analysis"
)
```

#### 5. **LLM Judge Rubrics**

Following Anthropic's guidance for "detailed, clear rubrics," our LLM Judge uses structured evaluation prompts:

```xml
<evaluation_task>
Evaluate the comprehensive approach of this medical analysis.

<query>{original_query}</query>
<expected_concepts>{key_medical_concepts}</expected_concepts>
<agent_analysis>{agent_response}</agent_analysis>

Score 0.0-1.0 based on:
1. Coverage of expected medical concepts (semantic, not literal matching)
2. Identification of relevant clinical aspects beyond those listed
3. Appropriate depth of analysis for query complexity
4. Medical accuracy and completeness

<thinking>
Analyze each expected concept and identify semantic equivalents...
</thinking>

<score>0.85</score>
<covered>HDL cholesterol (as "high-density lipoprotein"), trends, cardiovascular risk</covered>
<missed>Temporal patterns, medication correlation</missed>
<reasoning>The analysis covered lipid metrics well but failed to emphasize longitudinal trends</reasoning>
</evaluation_task>
```

### Success Criteria Implementation

Per Anthropic's SMART framework, our success criteria are:

1. **Specific**: Each dimension targets a precise aspect (e.g., "accurate complexity classification" not "good performance")
2. **Measurable**: All dimensions produce quantitative scores (0-1 scale) or binary outcomes
3. **Achievable**: Targets based on AI research benchmarks (e.g., 85% F1 for classification tasks)
4. **Relevant**: Aligned with medical system needs (e.g., high accuracy for patient safety)

**Example - Our Multidimensional Success Criteria:**
```python
EVALUATION_DIMENSIONS = {
    "complexity_classification": {
        "method": "hybrid",  # Deterministic with LLM fallback
        "weight": 0.20,
        "target": 0.90,
        "rationale": "Misclassification leads to wrong specialist assignment"
    },
    "specialty_selection": {
        "method": "llm_judge",  # Semantic understanding required
        "weight": 0.25,
        "target": 0.85,
        "rationale": "Medical appropriateness matters more than exact matches"
    },
    "analysis_quality": {
        "method": "llm_judge",  # Nuanced clinical assessment
        "weight": 0.25,
        "target": 0.80,
        "rationale": "Ensures comprehensive medical analysis"
    },
    "tool_usage": {
        "method": "deterministic",  # Objective success metrics
        "weight": 0.15,
        "target": 0.90,
        "rationale": "Data gathering is critical for accurate analysis"
    },
    "response_structure": {
        "method": "deterministic",  # Format validation
        "weight": 0.15,
        "target": 0.95,
        "rationale": "XML structure required for system integration"
    }
}
```

## Evaluation Methods

Three complementary methods are used to evaluate different aspects:

### 1. Deterministic Evaluation
Used for objective, measurable criteria:
- **When to use**: Structure validation, exact matching, performance metrics
- **Advantages**: Fast (0.1s), consistent, no API costs
- **Examples**: XML tag validation, tool call counting, response time measurement

### 2. LLM Judge Evaluation
Used for semantic and nuanced assessment:
- **When to use**: Medical appropriateness, concept coverage, reasoning quality
- **Advantages**: Understands context, handles variations, provides explanations
- **Examples**: Specialist selection validity, comprehensive approach scoring
- **Models Used**: 
  - Claude-3-Haiku: High-volume component scoring
  - Claude-3-Sonnet: Detailed failure analysis
  - Claude-3-Opus: Complex pattern identification

**Enhanced Coverage**: LLM Judge now analyzes ALL dimension failures:
- **Complexity Classification**: Misclassification root cause analysis
- **Specialist Selection**: Medical appropriateness and substitution analysis
- **Analysis Quality**: Component weakness identification and improvements
- **Tool Usage**: Effectiveness analysis and query optimization suggestions
- **Response Structure**: XML format validation and structure improvements

### 3. Hybrid Evaluation
Combines both methods for comprehensive assessment:
- **Example**: Complexity classification uses deterministic rules with LLM fallback for edge cases

## How Core Concepts Connect

The evaluation framework components work together in a structured flow:

```
Test Cases (Input)
    ↓
Agent Execution (CMO → Specialists)
    ↓
Evaluation Dimensions (5 aspects measured)
    ├── Complexity Classification
    ├── Specialty Selection  
    ├── Analysis Quality → Quality Components (5 sub-metrics)
    ├── Tool Usage
    └── Response Structure
    ↓
Evaluation Methods (How we measure)
    ├── Deterministic (Rules-based)
    ├── LLM Judge (Semantic understanding)
    └── Hybrid (Combined approach)
    ↓
Evaluation Criteria (Thresholds & targets)
    ↓
Results & Reports (Pass/Fail + Improvements)
```

### Evaluation Process Flow

1. **Test Case Selection**: Choose from 100+ expert-validated test cases
2. **Agent Execution**: 
   - Stage 1: CMO analyzes query and determines complexity
   - Stage 2: CMO creates specialist tasks based on analysis
3. **Multi-Dimensional Evaluation**:
   - Each dimension measured independently
   - Quality dimension broken into 5 components
   - Methods chosen based on what's being measured
4. **Scoring & Aggregation**:
   - Individual scores computed per dimension
   - Weighted average for overall score
   - Must meet ALL thresholds to pass
5. **Failure Analysis**:
   - LLM Judge identifies root causes
   - Pattern detection across failures
   - Specific improvement recommendations
6. **Report Generation**:
   - Executive summary with pass/fail
   - Detailed breakdowns per dimension
   - Visualizations and trends
   - Actionable next steps


## Agent Evaluation Specifications

The framework supports evaluation of all agents in the multi-agent health system:

### 1. **CMO Agent (Chief Medical Officer)** - Fully Implemented
   - Query Complexity Classification
   - Medical Specialty Selection
   - Task Creation and Delegation
   - Analysis Quality
   - Tool Usage Effectiveness
   - Response Structure Validation

### 2. **Cardiology Specialist Agent** - Fully Implemented
   - Diagnostic Accuracy (with focus on metabolic syndrome, dyslipidemia patterns)
   - Clinical Guideline Adherence (2018 ACC/AHA guidelines)
   - Cardiovascular Risk Assessment (ASCVD, metabolic syndrome criteria)
   - Treatment Recommendation Quality (medication optimization, adherence strategies)
   - Clinical Reasoning Evaluation
   
   **Real-World Test Cases**:
   - Lipid trend analysis over 12 years
   - Medication adherence correlation with outcomes
   - Metabolic syndrome identification
   - Diabetes impact on cardiovascular risk

### 3. **Other Specialist Agents** - Template Available
   - Easily add new specialists using the cardiology pattern
   - Define agent-specific evaluation dimensions
   - Create specialized test cases
   - Implement custom LLM Judge prompts

### 4. **System-Level Evaluation** - Coming Soon
   - End-to-end performance
   - Multi-agent coordination
   - Response synthesis quality

## Multi-Agent Evaluation Framework

The evaluation framework has been refactored to support multiple agent types with a modular, extensible architecture:

### Key Features

1. **Base Classes**: 
   - `BaseEvaluator`: Common evaluation logic for all agents
   - `EvaluationResult`: Base result class that can be extended

2. **Agent-Specific Components**:
   - Each agent has its own evaluator, test cases, and criteria
   - Organized in dedicated directories for clarity
   - Easy to add new agents without modifying core framework

3. **Flexible Test Selection**:
   - Different test types per agent
   - Category-based test filtering
   - Support for agent-specific test parameters

4. **Unified CLI**:
   - Single command interface for all agents
   - Agent selection via `--agent` parameter
   - Consistent reporting across agent types

### CMO Agent Evaluation

The CMO evaluation tests the complete two-stage workflow:

1. **Stage 1**: `analyze_query_with_tools` - Query analysis and complexity classification
2. **Stage 2**: `create_specialist_tasks` - Specialist task creation and delegation

#### Evaluation Dimensions

| Dimension | Code | Method | Metric | Target | Notes |
|-----------|------|--------|--------|--------|-------|
| **Complexity Classification** | `complexity_classification` | Hybrid (deterministic + LLM Judge for edge cases) | Binary accuracy | ≥ 90% | Ensures correct query categorization |
| **Specialty Selection** | `specialty_selection` | LLM Judge | Medical appropriateness score | ≥ 85% | Evaluates if selected specialists can adequately address the query |
| **Analysis Quality** | `analysis_quality` | LLM Judge | Weighted average of 5 quality components | ≥ 80% | See [Quality Components](#quality-components-analysis-quality-dimension-only) for breakdown |
| **Tool Usage** | `tool_usage` | Deterministic | Success rate of tool calls | ≥ 90% | Measures effectiveness of data retrieval |
| **Response Structure** | `response_structure` | Deterministic | Binary validation | ≥ 95% | Ensures XML compliance for system integration |

## Running Evaluations

### Quick Start

```bash
# Navigate to backend directory
cd backend

# CMO Agent Evaluation (default)
python -m evaluation.cli.run_evaluation --agent cmo --test comprehensive

# Cardiology Specialist Evaluation
python -m evaluation.cli.run_evaluation --agent cardiology --test example

# Run real-world tests for both agents (consistent pattern)
python -m evaluation.cli.run_evaluation --agent cmo --test real-world
python -m evaluation.cli.run_evaluation --agent cardiology --test real-world

# Run specific test category
python -m evaluation.cli.run_evaluation --agent cmo --category diabetes

# Run cardiology diagnostic tests
python -m evaluation.cli.run_evaluation --agent cardiology --test diagnostic

# Run cardiology treatment tests
python -m evaluation.cli.run_evaluation --agent cardiology --test treatment

# Run cardiology real-world tests (consistent with CMO)
python -m evaluation.cli.run_evaluation --agent cardiology --test real-world

# Run cardiology tests by category (optional filtering)
python -m evaluation.cli.run_evaluation --agent cardiology --test category --category lipid_management

# Run cardiology tests by urgency level (optional filtering)
python -m evaluation.cli.run_evaluation --agent cardiology --test urgency --category emergency

# Run with specific test IDs
python -m evaluation.cli.run_evaluation --agent cmo --test-ids standard_001,complex_002
```

### Command Line Options

| Parameter | Description | Values | Example |
|-----------|-------------|---------|----------|
| `--agent` | Agent type to evaluate | cmo, cardiology | `--agent cardiology` |
| `--test` | Type of evaluation | Varies by agent (see below) | `--test comprehensive` |
| `--category` | Test category | Varies by agent | `--category diabetes` |
| `--test-ids` | Specific test IDs | Comma-separated IDs | `--test-ids simple_001,complex_002` |
| `--concurrent` | Max parallel tests | Integer (default: 5) | `--concurrent 10` |

#### CMO Agent Test Types
- `example`: Single example test
- `complexity`: Complexity classification tests
- `specialty`: Specialty selection tests
- `comprehensive`: Full test suite
- `real-world`: Production-based tests
- `all`: All available tests

#### Cardiology Agent Test Types
- `example`: Single lipid trend analysis case
- `diagnostic`: Diagnostic accuracy evaluation tests
- `treatment`: Treatment recommendation evaluation tests
- `comprehensive`: Full test suite covering all dimensions
- `real-world`: Test cases based on actual system queries
- `all`: All cardiology tests
- `category`: Tests by clinical category (optional)
  - Categories: `lipid_management`, `medication_management`, `metabolic_cardiovascular`, `diabetes_cardiovascular`
- `urgency`: Tests by urgency level (optional)
  - Levels: `emergency`, `urgent`, `routine`

Note: LLM Judge is integrated into the standard evaluation flow for all evaluations.

## Understanding Reports

### Report Structure

The evaluation report has been redesigned for clarity and actionability:

#### 1. **Report Header**
Simple markdown format that works perfectly in preview mode:
```markdown
# 📊 CMO Agent Evaluation Report

**Test Suite:** Real World  
**Date:** 2025-06-27T11:52:10  
**Evaluation Type:** Hybrid (Deterministic + LLM Judge)

---
```

#### 2. **Executive Summary**
Immediate understanding of overall results:
```markdown
## Executive Summary

**Overall Result**: **FAIL** (100% of 4 tests executed successfully)

**Failed Dimensions**: Complexity Classification, Analysis Quality

### Dimension Performance

| Dimension | Score | Target | Status | Method | Description |
|-----------|-------|--------|--------|--------|-------------|
| Complexity Classification | 0.750 | 0.900 | ❌ FAIL | 🔄 Hybrid | Accuracy of query complexity classification |
| Analysis Quality | 0.742 | 0.800 | ❌ FAIL | 🧠 LLM Judge | Comprehensiveness of medical analysis |
| Specialty Selection | 0.925 | 0.850 | ✅ PASS | 🧠 LLM Judge | Precision in selecting appropriate medical specialists |
| Tool Usage | 1.000 | 0.900 | ✅ PASS | 🔧 Deterministic | Effectiveness of tool calls |
| Response Structure | 1.000 | 0.950 | ✅ PASS | 🔧 Deterministic | Compliance with XML format |

**Test Failures by Dimension:**
- Complexity Classification: 1 test failed
- Analysis Quality: 4 tests failed
```

#### 3. **Failure Analysis Summary**
High-level patterns identified across all failed tests:

```markdown
## 🔍 Failure Analysis Summary

### Complexity Classification Issues
Found 1 test(s) with misclassified complexity.

**Common Pattern**: The CMO is over-analyzing a straightforward trend request by adding specialist requirements 
and detailed medical interpretations that weren't asked for in the original query.

### Analysis Quality Issues
Found 4 test(s) below quality threshold.
**Most common issue**: Comprehensive Approach (failed in 4 tests)

> 💡 **Note**: Detailed analysis for each test is available in the Test Results section below.
```

#### 4. **Test Results Detail**
Each test now includes integrated analysis with LLM Judge feedback for failed dimensions:

```markdown
## Test Results Detail

**Prompts Being Tested:**
- [`1_initial_analysis.txt`](../../../services/agents/cmo/prompts/1_initial_analysis.txt) - Analyzes query complexity
- [`2_initial_analysis_summarize.txt`](../../../services/agents/cmo/prompts/2_initial_analysis_summarize.txt) - Summarizes findings
- [`3_task_creation.txt`](../../../services/agents/cmo/prompts/3_task_creation.txt) - Creates specialist tasks

### Test Case: standard_001 ❌

**Query:**  
What's my cholesterol trend over my entire data? I want to see trends across the top 4 cholesterol metrics including Triglycerides across that time period

**Response Time:** 72.6s

#### Evaluation Summary

| Dimension | Expected | Actual | Score | Target | Status |
|-----------|----------|--------|-------|--------|--------|
| **Complexity Classification** | STANDARD | COMPLEX | 0.00 | 0.90 | ❌ FAIL |
| **Specialist Selection** | cardiology, data_analysis, endocrinology | cardiology, data_analysis, endocrinology, laboratory_medicine, preventive_medicine | 0.90 | 0.85 | ✅ PASS |
| **Analysis Quality** | ≥0.80 | 0.79 | 0.79 | 0.80 | ❌ FAIL |
| **Tool Usage** | Effective | 1 calls | 1.00 | 0.90 | ✅ PASS |
| **Response Structure** | Valid XML | Valid | 1.00 | 0.95 | ✅ PASS |

#### 🔬 Failed Dimension Analysis

**Complexity Classification Issue:**
- **Problem**: The CMO is over-analyzing a straightforward trend request
- **Root Cause**: Turning simple trend visualization into complex medical analysis
- **Priority**: HIGH
- **Recommended Changes**:
  - Add explicit guidance that trend analysis requests should be classified as STANDARD
  - Include example: 'Queries asking to view trends without medical interpretation = STANDARD'
  - Add clarification that complexity should be based on explicit ask in query

**Analysis Quality Issue:**
- **Weak Areas**: Comprehensive Approach - Missed: ldl_cholesterol, trends, date_range
- **Overall Score**: 0.79 (target: 0.80)

#### Agent's Analysis
<details>
<summary>View the agent's full medical approach</summary>

```
[Agent's detailed medical analysis would appear here]
```
</details>
```

#### 5. **Visualizations**
Report includes visual insights at the end:

```markdown
## Visualizations

Click on any chart below to view detailed performance insights:

| Chart | What It Shows | Key Insights |
|-------|---------------|--------------|
| **[Dimension Scores](./dimension_scores.png)** | Bar chart comparing actual vs target scores | Quickly identify which dimensions are failing |
| **[Complexity Performance](./complexity_performance.png)** | Metrics by query complexity (STANDARD vs COMPLEX) | See if certain query types perform better |
| **[Response Time Distribution](./response_time_distribution.png)** | Histogram of processing times | Understand performance consistency |
| **[Specialty Heatmap](./specialty_heatmap.png)** | Which specialists are selected together | Identify common specialist combinations |
```

### Interpreting Evaluation Methods

Each score shows its evaluation method:
- 🔧 **Deterministic**: Rule-based evaluation
- 🧠 **LLM Judge**: Semantic evaluation
- 🔄 **Hybrid**: Combined approach

## Metrics and Scoring

### Overall Evaluation Logic
```python
# All dimensions must meet their targets independently
overall_pass = all(
    dimension_score >= dimension_target 
    for dimension_score, dimension_target in dimensions
)
```

### LLM Judge Scoring Scale
- **Binary**: Pass/Fail for clear criteria
- **Ordinal (1-5)**: For graduated quality assessment
- **Continuous (0-1)**: For nuanced scoring with explanations

## Best Practices

### 1. Test Case Design
- Include edge cases and ambiguous scenarios
- Use real-world queries when possible
- Balance different complexity levels
- Include failure scenarios

### 2. Prompt Iteration
- Use failure analysis to guide improvements
- Test changes against full evaluation suite
- Track performance trends over time
- Document rationale for changes

### 3. Cost Management
- Cache LLM Judge results for identical inputs
- Use appropriate models for each task
- Batch evaluations when possible
- Monitor API usage

### 4. Continuous Improvement
- Regular evaluation runs (daily/weekly)
- Track metrics over time
- Update test cases based on production queries
- Refine LLM Judge rubrics based on results

## Advanced Features

### Pattern Analysis
The framework automatically identifies patterns across failures:
- Common failure modes
- Trigger phrases or query types
- Systematic prompt weaknesses

### Automated Learning Loop
1. Run evaluation → Identify failures
2. LLM Judge analyzes root causes
3. Generate specific improvements
4. Test improvements → Measure impact
5. Iterate until targets met

### Custom Rubrics
Add domain-specific evaluation criteria:
```python
# In criteria/custom_rubrics.py
CUSTOM_RUBRICS = {
    "medication_safety": {
        "method": "llm_judge",
        "prompt": "Evaluate medication interaction awareness...",
        "weight": 0.30,
        "target": 0.95  # Higher threshold for safety
    }
}
```

## Recent Enhancements

### 1. **Comprehensive LLM Judge Analysis** (June 2025)
The evaluation framework now generates LLM Judge analysis for ALL dimension failures, not just complexity classification:

- **Analysis Quality Issues**: Root cause analysis with specific prompt improvements
- **Tool Usage Failures**: Identifies ineffective tool calls and suggests improvements
- **Response Structure Issues**: Pinpoints XML formatting problems
- **Specialist Selection**: Semantic similarity evaluation with acceptable substitutions

### 2. **Beautiful HTML Report Generation**
Evaluation reports are generated as stunning HTML documents with modern design:

- **Dark Gradient Theme**: Beautiful dark theme with glassmorphism effects
- **Interactive Elements**: Collapsible sections with smooth animations  
- **Progress Bars**: Visual dimension performance with target indicators
- **Failure Analysis Cards**: Animated cards with gradient borders and recommendations
- **Responsive Design**: Works perfectly on desktop and mobile devices
- **Embedded Visualizations**: Charts integrated directly in the report
- **Individual Test Summaries**: Clear tables showing dimension failures per test
- **Real World Test Suite Context**: Production-grade test descriptions

#### Report Generation
HTML reports are automatically generated with every evaluation:
```bash
# Generates HTML report with visualizations
python -m evaluation.cli.run_evaluation --test real-world
```

Reports are saved as `report.html` and can be opened directly in any modern browser. The reports include:
- Executive summary with overall results
- Detailed test case analysis with collapsible sections
- LLM Judge failure analysis with specific recommendations
- Performance visualizations and charts

### 3. **Modular Architecture & Externalized Prompts**
The evaluation framework is organized into focused modules:

```
evaluation/framework/
├── evaluators/                    # Agent-specific evaluators
│   ├── base_evaluator.py         # Base class for all evaluators
│   ├── cmo/                      # CMO agent evaluator
│   └── cardiology/               # Cardiology specialist evaluator
├── llm_judge/                     # LLM Judge evaluation module
│   ├── llm_test_judge.py         # Core LLM Judge implementation
│   └── prompts/                  # Externalized evaluation prompts
│       ├── cmo/                  # CMO evaluation prompts
│       │   ├── complexity/       # Complexity classification analysis
│       │   ├── quality/          # Analysis quality evaluation  
│       │   ├── specialist/       # Specialist selection comparison
│       │   ├── tool_usage/       # Tool usage effectiveness
│       │   └── response_structure/ # XML structure validation
│       └── cardiology/           # Cardiology evaluation prompts
│           ├── diagnostic/       # Diagnostic accuracy
│           ├── guideline/        # Guideline adherence
│           ├── risk/             # Risk assessment
│           ├── treatment/        # Treatment quality
│           └── reasoning/        # Clinical reasoning
└── report_generator/             # HTML report generation module
    ├── report_generator.py       # Main coordinator
    ├── html_report_generator.py  # Template processor
    └── report_template.html      # Jinja2 template
```

This modular structure keeps related components together, making the system easier to maintain, test, and extend.

### 4. **Specific Prompt Recommendations**
All recommendations now include exact file paths:

- Complexity issues → `backend/services/agents/cmo/prompts/1_initial_analysis.txt`
- Specialist selection → `backend/services/agents/cmo/prompts/3_task_creation.txt`
- Quality improvements → Specific sections within prompts to modify

### 5. **Test Execution Improvements**
- **Better Error Messages**: Clear feedback when dimensions fail
- **Response Time Tracking**: Performance metrics for each test
- **Specialist Name Display**: Shows actual specialist names instead of just counts

## Troubleshooting

### Setup Verification
```bash
cd backend
python -m evaluation.utils.check_setup
```

### Common Issues
1. **Import Errors**: Ensure you're in the `backend` directory
2. **API Key Missing**: Set `ANTHROPIC_API_KEY` environment variable
3. **Memory Issues**: Reduce concurrency with `--concurrent` flag
4. **Timeout Errors**: Increase timeout in evaluation scripts

### Debug Mode
```bash
# Run with debug logging
LOG_LEVEL=DEBUG python -m evaluation.cli.run_evaluation --test example
```

## Adding New Agents

To add evaluation support for a new agent type, follow this pattern:

### 1. Create Directory Structure
```bash
# Create directories for your new agent
mkdir -p evaluation/test_cases/{agent_name}
mkdir -p evaluation/criteria/{agent_name}
mkdir -p evaluation/framework/evaluators/{agent_name}
mkdir -p evaluation/framework/llm_judge/prompts/{agent_name}
```

### 2. Define Test Cases
Create `evaluation/test_cases/{agent_name}/{agent_name}_test_cases.py`:
```python
@dataclass
class {AgentName}TestCase:
    id: str
    query: str
    # Agent-specific expected outputs
    expected_dimension1: Any
    expected_dimension2: Any
    # ... other fields

class {AgentName}TestCases:
    @staticmethod
    def get_all_test_cases() -> List[{AgentName}TestCase]:
        # Return test cases
```

### 3. Define Evaluation Criteria
Create `evaluation/criteria/{agent_name}/{agent_name}_evaluation_criteria.py`:
```python
class {AgentName}Dimension(Enum):
    DIMENSION1 = "dimension1"
    DIMENSION2 = "dimension2"
    # ... other dimensions

class {AgentName}EvaluationRubric:
    # Define target scores for each dimension
```

### 4. Implement Evaluator
Create `evaluation/framework/evaluators/{agent_name}/{agent_name}_evaluator.py`:
```python
class {AgentName}Evaluator(BaseEvaluator):
    def get_evaluation_dimensions(self) -> List[str]:
        # Return list of dimensions
    
    async def evaluate_single_test_case(self, test_case) -> EvaluationResult:
        # Implement evaluation logic
```

### 5. Add LLM Judge Prompts
Create prompts in `evaluation/framework/llm_judge/prompts/{agent_name}/`:
- Create subdirectories for each evaluation dimension
- Add `.txt` files with evaluation prompts

### 6. Update CLI
Add your agent to `evaluation/cli/run_evaluation.py`:
```python
self.evaluator_map["{agent_name}"] = self._create_{agent_name}_evaluator
self.test_case_map["{agent_name}"] = {AgentName}TestCases
```

### 7. Test Your Implementation
```bash
python -m evaluation.cli.run_evaluation --agent {agent_name} --test example
```

## Future Enhancements

1. **Additional Specialist Agents**: 
   - Endocrinology, Neurology, Oncology specialists
   - Each with domain-specific evaluation criteria
   
2. **End-to-End Testing**: 
   - Full conversation flow validation
   - Multi-agent coordination testing
   
3. **A/B Testing Framework**: 
   - Compare prompt versions
   - Statistical significance testing
   
4. **Automated Ground Truth**: 
   - Multi-annotator consensus
   - Expert validation workflows
   
5. **Production Monitoring**: 
   - Real-time performance tracking
   - Continuous evaluation in production

## Real-World Test Evaluation

The framework includes real-world test cases based on actual production queries. These tests validate:
- System behavior under realistic conditions
- Specialist selection appropriateness
- Analysis quality on complex queries
- Edge case handling

Run real-world tests with:
```bash
python -m evaluation.cli.run_evaluation --test real-world
```

---

For questions or contributions, see [CONTRIBUTING.md](../CONTRIBUTING.md)