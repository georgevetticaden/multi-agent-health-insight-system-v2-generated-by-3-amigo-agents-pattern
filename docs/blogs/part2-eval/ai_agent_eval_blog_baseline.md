# When 8 AI Agents Walk Into a Health Query: An Eval Framework Story

*How the Three Gulfs Framework and 100 Test Cases Transformed Multi-Agent Chaos into Systematic Improvement*

In a recent interview, Kevin Weil—OpenAI's Chief Product Officer—made an [insightful prediction](https://www.youtube.com/watch?v=scsW6_2SPC4) about the skills that will define successful AI product development:

> *"Writing Evals is going to become a core skill for product managers. It is such a critical part of making good product with AI."*

Weil wasn't talking about traditional software testing—he was talking about a fundamental shift in how we build and maintain intelligent systems. Recently, a former colleague mentioned Parlance Labs' ["AI Evals For Engineers & PMs" course](https://maven.com/parlance-labs/evals?promoCode=li-dm-35&li_fat_id=da3708f9-2bfe-4dfa-959f-532297c843b7&utm_medium=cpc&utm_source=linkedin), which I'm currently halfway through. As I've been applying the course methodology while building the multi-agent health system I described in [Part 1](https://medium.com/@george.vetticaden/the-3-amigo-agents-the-claude-code-development-pattern-i-discovered-while-implementing-anthropics-67b392ab4e3f), I've discovered why Weil's observation runs deeper than most realize.

While Part 1 focused on the "3 Amigo Agents" development pattern and multi-agent orchestration architecture, this Part 2 dives into the sophisticated evaluation framework I built to systematically assess these agents. The challenges of evaluating multi-agent AI systems map directly onto what the course calls the "Three Gulfs of LLM Pipeline Development"—and solving them requires an entirely new approach to systematic evaluation.

## The Three Gulfs: Why Non-Deterministic × 8 = Eval Crisis

The course framework identifies three critical gaps that developers must bridge when building any LLM application:

*[Image: Three Gulfs of LLM Pipeline Development - The fundamental challenges that developers must bridge when building AI systems, from the Parlance Labs course. Each gulf represents a different type of failure that traditional testing approaches cannot address.]*

**The Gulf of Comprehension** separates us from truly understanding our data and our pipeline's behavior at scale. When my CMO agent processes thousands of potential health queries—from simple medication questions to complex multi-factor analysis requests—I can't manually review every input or trace every reasoning path.

**The Gulf of Specification** separates what we mean from what we actually communicate to our AI systems. Even detailed prompts often leave crucial decisions unstated. When I tell my CMO agent to "analyze health complexity," what constitutes simple versus comprehensive analysis? Should fatigue combined with medication changes trigger specialist consultation?

**The Gulf of Generalization** separates our carefully crafted prompts from consistent performance across diverse inputs. My agents might handle diabetes management perfectly but fail on medication interaction scenarios they haven't seen before.

These gulfs multiply exponentially in multi-agent systems. What's challenging with one agent becomes overwhelming with eight specialists coordinating in parallel. 

*[Image: The Three Gulfs Multiplied - Visual progression from single agent (×1) to multi-agent system (×8 agents, ×21 LLM, ×15 tools) to exponential complexity explosion.]*

The visualization above shows the cascade effect: a single health query like our HbA1c example triggers 21+ LLM calls and 15+ tool invocations across 8 agents over 90+ seconds. Each coordination point introduces new ambiguities. Each agent adds new failure modes. Traditional testing can't handle non-deterministic outputs from one agent—let alone eight agents making interdependent decisions. This complexity explosion demands entirely new evaluation methodologies.

## The LLM Eval Lifecycle: A Systematic Path Through Chaos

An important construct I learned over the last few weeks in the AI Evals course is the Analyze-Measure-Improve lifecycle—a powerful framework for taming this complexity. It's a systematic approach to understanding, quantifying, and fixing the emergent behaviors of non-deterministic AI systems.

When dealing with 8 specialist agents making 21+ LLM calls and 15+ tool invocations, ad-hoc debugging becomes impossible. This structured approach transforms overwhelming complexity into actionable insights.

*[Image: The LLM Evaluation Lifecycle - The Analyze → Measure → Improve cycle applied to multi-agent health system evaluation.]*

This blog walks through each phase as applied to my production multi-agent system:

**Analyze**: Systematically collect and categorize failure patterns across 100 diverse health queries. Build a failure taxonomy specific to multi-agent coordination through structured dimensions, comprehensive tracing, and rigorous coding techniques.

**Measure**: Transform qualitative insights into quantitative metrics using metadata-driven architecture and component-based scoring. Each agent self-defines its evaluation criteria while hierarchical tracing enables precise performance measurement across 5 key dimensions.

**Improve**: Leverage LLM-as-judge for automated root cause analysis and targeted remediation. The framework prescribes specific prompt improvements with file paths and expected impact assessments.

Each phase builds on the previous, creating a continuous improvement engine. Let's dive into how this lifecycle transforms multi-agent chaos into systematic excellence.

## From Chaos to Order: The Analyze Phase

The Analyze-Measure-Improve lifecycle begins with systematic analysis of representative examples to qualitatively identify failure modes. Rather than generating dummy test data or relying on whatever random health queries come to mind—which we're accustomed to in traditional development—this phase demands methodical data collection and rigorous qualitative analysis to develop what the course calls "a well-understood, application-specific vocabulary of failure."

### Engineering Order: From Query Dimensions to Diverse Test Cases

I begin by defining five key dimensions that systematically vary different aspects of health queries. This structured approach prevents the naive method of simply prompting an LLM to "give us user queries"—which typically produces generic, repetitive examples that miss real usage patterns.

**The Five Health Query Dimensions:**

1. **Health Data Type**: Lab Results, Medications, Vital Signs, Clinical Notes, Allergies, Procedures, Immunizations, Risk Factors
2. **Analysis Complexity**: Simple Lookup, Trend Analysis, Comparative Analysis, Correlation Analysis, Predictive Modeling, Comprehensive Summary  
3. **Time Scope**: Latest Results, Last 3 Months, Last 6 Months, Last Year, Multi-Year Trends, Specific Date Range, Longitudinal
4. **Medical Specialty Context**: Cardiology, Laboratory Medicine, Endocrinology, Pharmacy, Preventive Care, Data Analysis, General Medicine, Nutrition
5. **Query Scenario**: Clear and Specific, Partially Ambiguous, Complex Multi-Factor, Vague Intent, Out of Scope, Edge Case

The next step is generating 100 structured tuples from these dimensions. I create the first 25 by hand to ensure diverse coverage and realistic combinations, then use an LLM to generate the remaining 75 while maintaining quality and variety. Each tuple combines one element from each dimension—for example: `(Lab Results, Correlation Analysis, Multi-Year Trends, Endocrinology, Complex Multi-Factor)`.

These structured tuples then convert into natural language queries that reflect real user needs.

*[Insert Visual: Dimension Generation Framework - A flowchart showing how 5 dimensions combine to create structured tuples, then convert to natural language queries]*

One query becomes particularly revealing—I'll use it throughout this blog to demonstrate each evaluation phase: **"How has my HbA1c level changed since I started taking metformin, has my dosage been adjusted over time based on my lab results, and is there a correlation between these changes and my weight measurements during the same period?"**

This HbA1c query exemplifies multi-agent complexity: three medical domains (endocrinology, laboratory medicine, pharmacy), correlation analysis across multiple data types, multi-year timeframe, and sophisticated specialist coordination. Watch how this single query exposes critical system failures and drives targeted improvements throughout the evaluation lifecycle.

### The Analyze Phase Deepens: From Queries to Failure Patterns

With 100 diverse test cases ready, we've only completed the first step of the Analyze phase. The real work—transforming raw execution data into actionable insights—requires two more critical steps:

**Open Coding**: Systematically reading through execution traces and annotating specific behaviors, failures, and patterns. Think of it as detective work where every decision, every coordination point, and every output gets scrutinized.

**Axial Coding**: Clustering these granular observations into a coherent taxonomy of failure modes. This transforms scattered findings into structured categories that can be systematically measured and improved.

But here's the challenge: in multi-agent systems with 8 specialists making 21+ LLM calls and 15+ tool invocations across 90+ seconds, you can't do this analysis without deep observability. We need to see not just what happened, but how agents reasoned, which health data tools they invoked, why they made specific choices, and where coordination broke down.

This is where comprehensive tracing becomes essential.

### Seeing Into the Abyss: Multi-Agent Trace Architecture

Traditional evaluation approaches fall apart when dealing with multi-agent conversations that span minutes, involve 21+ LLM calls and 15+ tool invocations, and coordinate across multiple specialists. As the course emphasizes, "there is no substitute for examining real outputs on real data"—but in multi-agent systems, this means capturing complete reasoning chains, health data tool invocations, and coordination patterns.

I built a custom tracing framework specifically for multi-agent evaluation. While tools like LangSmith provide excellent general-purpose tracing, my evaluation lifecycle demanded application-specific capabilities: custom metrics tailored to healthcare domains, agent relationship tracking, and deep visibility into tool invocation patterns. Additionally, building a standalone solution avoided the dependency complexity that often comes with larger frameworks, keeping the evaluation system focused and maintainable.

*[Image: Trace Analysis Report - Comprehensive execution summary for our HbA1c query showing 5 agents, 19 LLM calls, 8 tool invocations, and detailed performance metrics across 6 minutes 59 seconds of orchestrated analysis.]*

The tracing framework captures every detail: when the CMO agent receives our HbA1c query, how it classifies complexity, which specialists it selects, how tasks are distributed, what health data tools each specialist invokes, and how insights are synthesized. This granular observability becomes essential for the next phase.

*[Image: Detailed Trace Analysis — Drilling into the CMO's query analysis stage reveals every LLM call, tool invocation, and decision point—from initial complexity assessment through specialist task distribution.]*

### Finding Patterns in Chaos: Open Coding Agent Failures

With comprehensive traces illuminating every decision, I apply Open Coding—a technique adapted from grounded theory that involves carefully reading each trace and making detailed annotations about observed behaviors and potential failures. This isn't casual bug hunting; it's systematic qualitative analysis.

For our HbA1c query trace, the open coding process revealed three critical failure patterns:

#### 1. Incorrect Complexity Classification

The CMO agent classified this multi-domain correlation analysis as "STANDARD" rather than "COMPLEX." The trace revealed the agent's reasoning: *"To analyze the patient's HbA1c trends in relation to their metformin therapy and weight."* The agent focused on the analysis task but missed the multi-factor correlation complexity spanning three medical domains.

*[Image: Complexity Misclassification - The Health Insight Assistant shows the CMO incorrectly assessing this multi-domain correlation query as "STANDARD" complexity.]*

#### 2. Incomplete Specialist Team Assembly  

The CMO assembled only three specialists—Endocrinology, Nutrition, and Pharmacy—missing critical expertise. For a query involving lab result correlations and preventive health implications, the complete team should have included Laboratory Medicine and Preventive Medicine specialists. This gap meant missing key analytical perspectives.

*[Image: Incomplete Medical Team - Only 3 of 5 required specialists were selected, missing Laboratory Medicine and Preventive Medicine expertise needed for comprehensive correlation analysis.]*

#### 3. Missed Correlation in Final Analysis

Despite weight increasing from 192.9 to 226.62 lbs during the metformin treatment period, the CMO's final synthesis stated: *"The data does not show a clear relationship between your weight changes and glycemic control while on metformin."* This directly contradicted the data pattern and failed to address a key aspect of the original query.

*[Image: Analysis Failure - The CMO's final response incorrectly states no relationship between weight changes and glycemic control, missing the 30+ pound weight gain correlation.]*

These failures weren't random bugs—they represented systematic patterns that would recur across similar complex queries, making them perfect candidates for the next phase of analysis.

### Order from Chaos: Axial Coding the Failure Taxonomy

The Analyze phase culminates in Axial Coding—the systematic process that transforms our detailed failure observations into a structured taxonomy ready for measurement.

Axial Coding transforms scattered observations into structured understanding. By clustering similar failure patterns from Open Coding, I build a coherent taxonomy of recurring failure types. After analyzing dozens of health query traces, five distinct failure dimensions emerged for the CMO agent:

1. **Complexity Classification**: Accuracy in categorizing query complexity levels (SIMPLE/STANDARD/COMPLEX/COMPREHENSIVE)
2. **Specialty Selection**: Precision in selecting appropriate medical specialists for coordination
3. **Analysis Quality**: Comprehensiveness of orchestrated medical analysis across specialists
4. **Tool Usage**: Effectiveness of health data tool usage and information gathering
5. **Response Structure**: Compliance with expected XML format for downstream processing

This structured categorization delivers exactly what the course identifies as the Analyze phase's critical output: "a clear, consistent set of defined failure modes that allows us to precisely describe, and subsequently measure, how and why our LLM pipeline isn't meeting expectations."

## From Taxonomy to Metrics: The Measure Phase

With our failure taxonomy complete—five distinct dimensions where our CMO agent can fail—we enter the Measure phase. This is where qualitative insights transform into quantitative metrics, enabling systematic evaluation at scale.

The challenge: how do we measure something as subjective as "Analysis Quality" or as nuanced as "Specialist Selection"? Traditional software testing offers binary pass/fail assertions. But when an agent must choose between 8 specialists based on semantic understanding of medical queries, we need more sophisticated measurement approaches.

The Measure phase answers four critical questions:
- **How** do we score each dimension? (Evaluation Methods)
- **What** framework orchestrates the process? (Metadata-Driven Architecture)
- **What** are we measuring against? (Test Cases from Failure Analysis)
- **Who** scores semantic quality at scale? (LLM-as-Judge)

Let's explore how the framework transforms our five failure dimensions into measurable, improvable metrics.

## Three Ways to Measure: The Eval Methods

The framework implements three complementary evaluation methods, each suited to different aspects of agent behavior:

**Deterministic Evaluation** handles the objective and measurable. When the CMO agent selects specialists, we can calculate precision mathematically—did it select 3 of the 5 required specialists? That's 60% precision. Tool success rates, response times, and structural compliance all fall into this category.

**LLM Judge Evaluation** tackles the subjective and semantic. When assessing whether the CMO's specialist selection rationale makes medical sense, we need an evaluator that understands clinical context. The LLM Judge reads the agent's reasoning and scores it based on medical appropriateness and logical coherence.

**Hybrid Evaluation** combines both approaches for nuanced assessment. Specialist Selection exemplifies this: we measure precision deterministically (60%) while evaluating selection rationale with an LLM Judge (40%), creating a balanced score that captures both accuracy and reasoning quality.

This three-method approach ensures we can measure everything from hard metrics to soft skills, giving us complete visibility into agent performance.

*[Image: Dimension Evaluation Report - Real evaluation results showing all three measurement methods in action: Deterministic evaluation for Complexity Classification (binary pass/fail), Hybrid evaluation for Specialty Selection combining deterministic precision (60%) with LLM Judge rationale assessment (40%), demonstrating how different dimensions require different evaluation approaches.]*

With our evaluation methods defined, we need a systematic way to apply them. This requires two key components: a framework that knows which method to use for each dimension, and concrete test cases that define what success looks like. Let's explore how metadata-driven architecture orchestrates this evaluation process.

## Metadata-Driven Architecture: From Simple Scores to Component Precision

Rather than hard-coding evaluation rules, the framework uses metadata-driven architecture where each agent declares how it should be evaluated. This self-defining approach ensures evaluation criteria evolve with agent capabilities.

### Basic Dimension Configuration

The CMO agent's metadata defines its five evaluation dimensions:

```python
evaluation_criteria = [
    EvaluationCriteria(
        dimension="complexity_classification",
        target_score=0.90,  # Must achieve 90% accuracy
        weight=0.20,        # 20% of total evaluation
        evaluation_method=EvaluationMethod.DETERMINISTIC
    ),
    EvaluationCriteria(
        dimension="specialty_selection",
        target_score=0.85,
        weight=0.25,        # Most important dimension
        evaluation_method=EvaluationMethod.HYBRID
    ),
    # ... other dimensions
]
```

### Component-Based Scoring for Complex Dimensions

But some dimensions resist simple scoring. "Analysis Quality" encompasses data gathering, context awareness, comprehensive approach, and concern identification. A single score obscures which aspects excel or fail.

The framework solves this through component-based metadata:

```python
quality_components = {
    dimension_registry.get("analysis_quality"): [
        QualityComponent(
            name="data_gathering",
            description="Appropriate tool calls to gather health data",
            weight=0.20,
            evaluation_method=EvaluationMethod.DETERMINISTIC
        ),
        QualityComponent(
            name="context_awareness",
            description="Consideration of temporal context and patient history",
            weight=0.15,
            evaluation_method=EvaluationMethod.LLM_JUDGE
        ),
        QualityComponent(
            name="comprehensive_approach",
            description="Coverage of all relevant medical concepts",
            weight=0.25,
            evaluation_method=EvaluationMethod.LLM_JUDGE
        ),
        QualityComponent(
            name="concern_identification",
            description="Identification of health concerns and risks",
            weight=0.20,
            evaluation_method=EvaluationMethod.LLM_JUDGE
        )
    ],
}
```

For our HbA1c query, this granularity revealed the pattern: agents excelled at data gathering (1.00) but struggled with context awareness (0.70), missing the correlation between weight gain and glycemic control. This component breakdown transforms vague failures ("poor analysis") into actionable insights ("improve temporal correlation detection").

*[Insert Visual: Component-Based Quality Scoring - Screenshot showing Analysis Quality dimension broken into Data Gathering (Deterministic), Context Awareness (LLM Judge), Comprehensive Approach (LLM Judge), and Concern Identification (LLM Judge) with individual scores and weights]*

The metadata architecture operationalizes our failure taxonomy. Each dimension from our Analyze phase—Complexity Classification, Specialty Selection, Analysis Quality—now has precise evaluation rules, methods, and thresholds. The framework automatically orchestrates the right evaluation approach for each component, calculates weighted scores, and determines success. But defining how to evaluate is only half the equation.

We've now answered two of our four critical questions: we know *how* to score each dimension through three evaluation methods, and we have the *framework* that orchestrates the entire process with metadata-driven architecture (including component-based scoring for complex dimensions). But the third question remains: *what* are we measuring against? This is where our failure taxonomy transforms into concrete test cases—each one encoding the expected behaviors we discovered during the Analyze phase.

## From Failure Analysis to Test Cases

The metadata architecture provides the evaluation framework, but what exactly are we evaluating? This is where test cases bridge our qualitative analysis with quantitative measurement.

Each test case crystallizes the insights from our Open and Axial Coding into concrete expectations. Our HbA1c query—which revealed three critical failures—now becomes test case `complex_002`:

```python
TestCase(
    id="complex_002",
    query="How has my HbA1c level changed since I started taking metformin...",
    expected_complexity="COMPLEX",  # From our failure analysis
    expected_specialties={"endocrinology", "laboratory_medicine", 
                         "preventative_medicine", "pharmacy", "nutrition"},
    key_data_points=["hba1c_trend", "metformin_initiation", 
                    "dose_adjustments", "weight_correlation"],
    description="Three-way correlation analysis: medication, lab results, and weight",
    based_on_real_query=True,
    notes="Real query 4 - Found suboptimal dosing and weight gain correlation"
)
```

Notice how each field maps directly to our failure taxonomy:
- `expected_complexity` tests our first dimension (Complexity Classification)
- `expected_specialties` validates Specialty Selection
- `key_data_points` ensures comprehensive Analysis Quality
- The `based_on_real_query` flag indicates this came from actual system testing

This systematic approach transforms ad-hoc testing into structured evaluation. Every insight from the Analyze phase becomes a measurable expectation, creating a feedback loop that continuously improves agent performance.

With test cases defining our expectations, we can now measure agent performance across all dimensions. But our fourth critical question remains: *who* scores semantic quality at scale? Many evaluation components require understanding beyond deterministic rules—medical reasoning, contextual awareness, comprehensive analysis. This is where our LLM Judge becomes indispensable.

## LLM-as-Judge: Semantic Eval at Scale

Many evaluation components require semantic understanding—you can't deterministically score 'context awareness' or 'medical reasoning quality.' The LLM Judge serves as our semantic evaluation engine, understanding medical context and assessing quality where deterministic rules fall short. Unlike generic evaluation, our judges receive specialized prompts for healthcare assessment.

When evaluating specialist selection rationale, the judge considers:
- Medical appropriateness of chosen specialists
- Logical reasoning for exclusions
- Domain expertise alignment with query needs
- Coordination complexity considerations

For our HbA1c query, the LLM Judge scored the selection rationale at 0.90 despite missing two specialists. The reasoning was sound—the agent correctly identified the need for endocrinology and nutrition expertise—but incomplete in scope.

*[Image: Specialist Selection Evaluation - Hybrid evaluation in action showing Specialist Precision scoring 0.75 (missing pharmacy and preventive medicine) while Specialist Rationale scores 0.90, demonstrating how LLM Judge can recognize sound reasoning even when the selection itself is incomplete.]*

The LLM Judge achieves this nuanced evaluation through carefully crafted prompts:

```
Evaluate the specialist selection rationale in this CMO analysis.
CMO Analysis:
{analysis}

Rate on a scale of 0.0 to 1.0 how well the CMO:
1. Provided clear reasoning for each specialist selection
2. Explained how each specialist contributes to answering the query
3. Justified the team composition based on medical needs

Respond with your evaluation in this exact format:
<score>0.0-1.0</score>
<reasoning>Brief explanation of the score</reasoning>
```

This structured approach ensures consistent semantic evaluation across hundreds of test cases, capturing reasoning quality that deterministic rules would miss.

## LLM Judge as Diagnostic Engine: The Improve Phase

Measurement without improvement is just expensive monitoring. The Improve phase closes the loop, transforming evaluation insights into concrete enhancements.

The transition from Measure to Improve builds on the evaluation framework's most powerful feature: every failed dimension becomes a drill-down diagnostic opportunity. Our CMO evaluation report reveals two critical failures that cascade through the system.

*[Image: CMO Evaluation Report - Overall evaluation showing 73.4% success rate with failures in Complexity Classification and Specialty Selection dimensions, highlighting where targeted improvements are needed.]*

Clicking into each failed dimension reveals how the same LLM Judge that scored performance now serves as our diagnostic engine. Let's examine both failures:

**Complexity Classification Failure (Score: 0.00)**

*[Image: Complexity Classification Drill-Down - LLM Judge analysis revealing root cause: "The prompt does not provide clear enough guidance on what constitutes a COMPLEX query versus a STANDARD query, leading to misclassification in cases involving multiple related data points and potential correlations."]*

The misclassification as STANDARD instead of COMPLEX triggered a cascade of downstream errors. The LLM Judge prescribes surgical fixes:
- **MODIFY RULE**: Change "Trend analysis, 2-3 related metrics, moderate complexity" to "Queries involving up to 2 related clinical metrics over time"
- **ADD EXAMPLE**: Our exact HbA1c query as a COMPLEX template
- **Target File**: `1_gather_data_assess_complexity.txt`

**Specialty Selection Failure (Score: 0.81)**

*[Image: Specialty Selection Drill-Down - Hybrid evaluation showing 0.75 precision (missing pharmacy and preventive medicine) with LLM Judge identifying: "The pharmacy and preventive_medicine specialists were incorrectly excluded from the selection, even though the query mentioned metformin dosage adjustments and correlations with weight changes over time."]*

Despite scoring 0.90 on selection rationale, the agent missed critical specialists. The root cause analysis reveals pattern gaps:
- **ADD Rule**: "ALWAYS include pharmacy when query mentions: medication names, dosages, dosage adjustments, or medication adherence"
- **ADD Rule**: "ALWAYS include preventive_medicine when query asks about correlations between lab values/medications and risk factors like weight"
- **ADD Keywords**: ['medication', 'drug', 'dosage', 'dose', 'prescription'] for pharmacy detection

This drill-down capability transforms abstract scores into actionable improvements. Each recommendation includes the exact prompt file and expected impact, enabling rapid iteration cycles where today's failures become tomorrow's successes.

## The Skill That Defines AI's Future

Kevin Weil was right: evaluation has become the defining skill for AI product development. But it's more than he predicted—it's a fundamental shift from catching bugs to understanding reasoning, from binary pass/fail to semantic assessment, from testing single functions to orchestrating multi-agent symphonies. The organizations that master evaluation-driven development will build systems that improve continuously through structured feedback rather than hoping better prompts solve architectural challenges. They'll understand not just that their AI systems work, but why they work and how to make them work better. In an age where AI makes the decisions that matter, this understanding—this systematic approach to evaluation—separates products that mysteriously fail from those that evolve into something remarkable.

---

*George Vetticaden is an AI Agent Product Leader with 14+ months of experience building enterprise AI agent platforms. He recently served as VP of Agents at a leading AI startup, where he led the development of agent building tools and document intelligence solutions.*

*Connect with him on [LinkedIn](https://linkedin.com/in/georgevetticaden) to discuss the future of AI evaluation frameworks.*

*Read Part 1: [The 3 Amigo Agents: The Claude Code Development Pattern I Discovered While Implementing Anthropic's Multi-Agent Architecture](link)*