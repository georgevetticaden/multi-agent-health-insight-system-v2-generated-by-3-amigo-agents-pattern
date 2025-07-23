# The Eval-Driven Agent Development Playbook

*How to Navigate the Three Gulfs and Build Systematically Improving Multi-Agent Systems*

In a recent interview, Kevin Weil—OpenAI's Chief Product Officer—made an insightful prediction about the skills that will define successful AI product development:

> *"Writing Evals is going to become a core skill for product managers. It is such a critical part of making good product with AI."*

For more than a week, I've been thoroughly enjoying Parlance Labs' ["AI Evals For Engineers & PMs" course](https://maven.com/parlance-labs/evals?promoCode=li-dm-35&li_fat_id=da3708f9-2bfe-4dfa-959f-532297c843b7&utm_medium=cpc&utm_source=linkedin) while building the multi-agent health system from [Part 1](https://medium.com/@george.vetticaden/the-3-amigo-agents-the-claude-code-development-pattern-i-discovered-while-implementing-anthropics-67b392ab4e3f). The course crystallized what Weil was really saying—evaluating AI agents isn't an extension of traditional testing. It's an entirely new discipline that requires us to build quality systems in fundamentally different ways.

While Part 1 explored the "3 Amigo Agents" pattern and multi-agent orchestration, in Part 2 I'll share what I learned about this paradigm shift through the course's "Three Gulfs of LLM Pipeline Development" framework—lessons drawn from evaluating a real-world multi-agent application with all the complexity that entails. Finally, I'll reveal the Eval Development Studio and AI assistant I built to turn this methodology into a practical workflow.

## The Three Gulfs: Why Non-Deterministic × 8 = Eval Crisis

The Parlance Labs course identifies three fundamental challenges that developers face when building any LLM application:

*[Image: Three Gulfs of LLM Pipeline Development from Parlance Labs—showing how traditional testing fails at each stage: Comprehension (understanding data at scale), Specification (translating intent to prompts), and Generalization (handling diverse inputs).]*

**The Gulf of Comprehension** means we can't understand what our systems actually do. When my CMO agent processes health queries, I can't trace every reasoning path or validate every decision. The agent's thinking becomes opaque at scale.

**The Gulf of Specification** is the gap between what we want and what we tell our agents. "Analyze health complexity" sounds clear until you realize: Should fatigue plus medication changes trigger a specialist? What makes analysis "comprehensive" versus "standard"? Our prompts leave countless decisions unspecified.

**The Gulf of Generalization** ensures our agents fail in unexpected ways. They might excel at diabetes management but stumble on rare drug interactions. What works for common cases breaks for edge cases we didn't anticipate.

These gulfs multiply exponentially in multi-agent systems. What's challenging with one agent becomes overwhelming with eight specialists coordinating in parallel.

*[Image: The Three Gulfs cascade from single agent simplicity to multi-agent chaos—showing how 8 agents create 21+ coordination points and 90+ seconds of processing, making traditional testing impossible.]*

The multiplication effect reveals why traditional testing fails: we're not debugging code anymore—we're trying to understand emergent behaviors from dozens of interdependent decisions. This complexity demands a fundamentally different approach to evaluation.

## The LLM Eval Lifecycle: A Systematic Path Through Chaos

The Parlance Labs course introduces the Analyze-Measure-Improve lifecycle—the framework that makes AI evaluation manageable. Instead of ad-hoc debugging that never scales, this approach gives you a systematic way to understand, quantify, and fix AI behaviors.

*[Image: The LLM Evaluation Lifecycle - The Analyze → Measure → Improve cycle applied to multi-agent health system evaluation.]*

Here's how each phase works in practice:

**Analyze**: Run 100 diverse health queries—from "What's my latest blood pressure?" to "How do my medications interact with my lab results?" Watch what fails, spot the patterns, and organize them into categories you can actually fix.

**Measure**: Turn "that doesn't look right" into numbers you can track. Score each failure type separately—did the agent pick the wrong specialists? Miss key data? The framework shows exactly where things break down.

**Improve**: Let AI diagnose AI. When your CMO agent keeps misreading complex queries as simple ones, the framework pinpoints why and suggests specific prompt fixes that actually work.

Each phase feeds the next, creating continuous improvement. Let me walk you through how this works with a production multi-agent system.

## From Chaos to Order: The Analyze Phase

The Analyze phase starts with a simple goal: understand how your AI fails. But instead of testing random queries and hoping to catch problems, you need a systematic approach.

One of the most valuable insights from the course was learning to build a "vocabulary of failure"—a structured catalog of all the ways your agents mess up, organized so you can actually fix them. This isn't just debugging; it's building a language to describe and tackle AI failures systematically.

### Engineering Order: From Query Dimensions to Diverse Test Cases

Instead of throwing random health queries at your agents and hoping to catch problems, the course taught me to break down queries into their core components—what they call "dimensions." Think of dimensions as the building blocks of any health question: what type of data, how complex the analysis, what timeframe, which medical area, and how clear the request is.

**The Five Health Query Dimensions:**

1. **Health Data Type**: Lab Results, Medications, Vital Signs, Clinical Notes, Allergies, Procedures, Immunizations, Risk Factors
2. **Analysis Complexity**: Simple Lookup, Trend Analysis, Comparative Analysis, Correlation Analysis, Predictive Modeling, Comprehensive Summary  
3. **Time Scope**: Latest Results, Last 3 Months, Last 6 Months, Last Year, Multi-Year Trends, Specific Date Range, Longitudinal
4. **Medical Specialty Context**: Cardiology, Laboratory Medicine, Endocrinology, Pharmacy, Preventive Care, Data Analysis, General Medicine, Nutrition
5. **Query Scenario**: Clear and Specific, Partially Ambiguous, Complex Multi-Factor, Vague Intent, Out of Scope, Edge Case

*[Image: From Dimensions to Diverse Health Queries - Systematic generation of representative test cases for multi-agent evaluation]*

I hand-crafted 25 combinations to ensure quality, then used an LLM to generate 75 more—giving me 100 structured test cases that mirror real-world usage. Each combines one element from each dimension, like: `(Lab Results, Correlation Analysis, Multi-Year Trends, Endocrinology, Complex Multi-Factor)`.

These combinations become natural queries. One query in particular became my running example throughout the evaluation lifecycle because it touches so many aspects:

**"How has my HbA1c level changed since I started taking metformin, has my dosage been adjusted over time based on my lab results, and is there a correlation between these changes and my weight measurements during the same period?"**

This query hits everything at once: three medical domains, correlation analysis, multi-year data, and complex coordination. I'll use it to demonstrate each phase of the evaluation process—from identifying failures to measuring performance to implementing fixes.

### The Analyze Phase Deepens: From Queries to Failure Patterns

With 100 diverse test cases ready, we've only completed the first step of the Analyze phase. Now comes the hard part: making sense of what actually happens when your agents process them.

The course taught me two essential techniques:

**Open Coding**: Read through every execution trace and mark what went wrong. Tag each failure point—where the agent misunderstood the query, picked wrong specialists, or missed crucial data. You're building a detailed catalog of everything that fails.

**Axial Coding**: Take all those individual failures you found and group them into patterns. Maybe you notice that medication queries always miss dosage history, or that complex correlations get simplified to basic lookups. These patterns become your failure categories—the foundation for everything that follows.

But here's the challenge: in multi-agent systems with dozens of LLM calls and tool invocations creating hundreds of decision points, you can't analyze failures without seeing the full picture. You need visibility into how agents reasoned, which tools they chose, why they made specific decisions, and where coordination broke down.

This is where comprehensive tracing becomes essential.

### Seeing Into the Abyss: Multi-Agent Trace Architecture

Traditional evaluation tools break down with multi-agent systems. When agents coordinate, make dozens of decisions, and invoke multiple tools across minutes of processing, you need to see everything—not just final outputs, but the entire chain of reasoning and coordination.

I built a custom tracing framework specifically for multi-agent evaluation. While tools like LangSmith work great for single agents, I needed healthcare-specific metrics, agent relationship tracking, and deep visibility into how specialists coordinate. Building it myself also kept the system focused and maintainable.

*[Image: Trace Analysis Report - Comprehensive execution summary for our HbA1c query showing 5 agents, 19 LLM calls, 8 tool invocations, and detailed performance metrics across 6 minutes 59 seconds of orchestrated analysis.]*

The framework captures everything that matters: how the CMO interprets the query, which specialists it picks, how tasks get distributed, what data each agent retrieves, and how they combine their findings. Without this visibility, you're debugging blind.

*[Image: Detailed Trace Analysis — Drilling into the CMO's query analysis stage reveals every LLM call, tool invocation, and decision point—from initial complexity assessment through specialist task distribution.]*

### Finding Patterns in Chaos: Open Coding Agent Failures

With traces showing every decision, I could finally see where things went wrong. Open Coding means reading through each trace and marking specific failures—not just bugs, but patterns in how the AI misunderstands, miscategorizes, or misses connections.

For our HbA1c query, three major failures jumped out:

#### 1. Incorrect Complexity Classification

The CMO agent labeled this multi-domain correlation query as "STANDARD" instead of "COMPLEX." The trace showed its flawed reasoning: *"To analyze the patient's HbA1c trends in relation to their metformin therapy and weight."* It saw the analysis task but missed that it needed to correlate data across three medical domains.

*[Image: Complexity Misclassification - The Health Insight Assistant shows the CMO incorrectly assessing this multi-domain correlation query as "STANDARD" complexity.]*

#### 2. Incomplete Specialist Team Assembly  

The CMO picked only three specialists—Endocrinology, Nutrition, and Pharmacy—but missed Laboratory Medicine and Preventive Medicine. For a query about lab correlations and health implications, those missing specialists meant missing crucial insights.

*[Image: Incomplete Medical Team - Only 3 of 5 required specialists were selected, missing Laboratory Medicine and Preventive Medicine expertise needed for comprehensive correlation analysis.]*

#### 3. Missed Correlation in Final Analysis

Here's where it really failed: weight increased from 192.9 to 226.62 lbs during the metformin treatment period, yet the CMO concluded: *"The data does not show a clear relationship between your weight changes and glycemic control while on metformin."* A 30+ pound weight gain, and it saw no connection.

*[Image: Analysis Failure - The CMO's final response incorrectly states no relationship between weight changes and glycemic control, missing the 30+ pound weight gain correlation.]*

These weren't one-off bugs. They were systematic failures that would happen again with similar queries—exactly the kind of patterns you need to identify before you can fix them.

### Order from Chaos: Axial Coding the Failure Taxonomy

Axial Coding is where you turn scattered failures into actionable categories. I took all those individual problems from Open Coding and grouped them into patterns. After analyzing dozens of health queries, I found the CMO agent fails in five consistent ways:

1. **Complexity Classification**: Getting query complexity wrong (SIMPLE/STANDARD/COMPLEX/COMPREHENSIVE)
2. **Specialty Selection**: Picking the wrong medical specialists 
3. **Analysis Quality**: Missing key insights when coordinating specialist findings
4. **Tool Usage**: Not pulling the right health data
5. **Response Structure**: Breaking the expected XML format for downstream systems

This taxonomy became my foundation for everything that followed—a clear vocabulary for describing exactly how and why my agents fail. Now I could measure each failure type and track improvements systematically.

## From Taxonomy to Metrics: The Measure Phase

With five clear failure categories identified, the Measure phase tackles the next challenge: turning observations into numbers you can track and improve.

The problem is that "Analysis Quality" and "Specialist Selection" aren't binary pass/fail tests. When an agent picks specialists based on understanding medical context, you need smarter ways to measure success than traditional testing provides.

The Measure phase answers four key questions:
- **How** do we score each dimension? (Evaluation Methods)
- **What** framework runs the evaluation? (Metadata-Driven Architecture)  
- **What** are we measuring against? (Test Cases from Failure Analysis)
- **Who** judges semantic quality at scale? (LLM-as-Judge)

Here's how the framework turns those five failure dimensions into metrics that actually drive improvement.

## Three Ways to Measure: The Eval Methods

The framework uses three different measurement approaches, each suited to different aspects of agent behavior:

**Deterministic Evaluation** measures what's black and white. Did the CMO pick 3 of the 5 required specialists? That's 60% precision—simple math. Tool success, response times, XML compliance—these all have clear right/wrong answers.

**LLM Judge Evaluation** handles the gray areas. When you need to know if the agent's reasoning makes medical sense, you need an evaluator that understands context. The LLM Judge reads the agent's explanation and scores whether the logic holds up.

**Hybrid Evaluation** combines both for the full picture. Take Specialist Selection: we score accuracy with math (60% precision) and reasoning quality with an LLM Judge (40% weight). This captures both whether the agent got it right AND why it made those choices.

*[Image: Dimension Evaluation Report - Real evaluation results showing all three measurement methods in action: Deterministic evaluation for Complexity Classification (binary pass/fail), Hybrid evaluation for Specialty Selection combining deterministic precision (60%) with LLM Judge rationale assessment (40%), demonstrating how different dimensions require different evaluation approaches.]*

With these three methods, you can measure everything from concrete metrics to nuanced reasoning. Next, we need a system that knows when to use each method.

## Self-Scoring Agents: Defining Their Own Evaluation Criteria

Instead of hard-coding evaluation rules, each agent defines its own evaluation criteria through metadata. This self-defining approach ensures evaluation criteria evolve with agent capabilities.

### Basic Dimension Configuration

The CMO agent declares how to evaluate its five dimensions:

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

But "Analysis Quality" isn't one thing—it's data gathering, context awareness, comprehensive coverage, and risk identification. A single score hides which parts work and which don't.

The framework breaks it down:

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

For our HbA1c query, this revealed exactly where things broke: perfect data gathering (1.00) but weaker context awareness (0.80)—the agent struggled to connect weight changes with blood sugar trends. Now "fix analysis quality" becomes "improve temporal correlation detection."

*[Image: Component-Based Quality Scoring - Analysis Quality dimension broken into Data Gathering, Context Awareness, Comprehensive Approach, and Concern Identification with individual scores and weights]*

The metadata architecture brings our failure taxonomy to life. Each dimension from the Analyze phase now has evaluation rules, scoring methods, and success thresholds. The framework handles the complexity—applying the right evaluation method, calculating weighted scores, determining pass/fail.

We've answered two of our four Measure phase questions: we know **how** to score (three evaluation methods) and we have the **framework** to run it (metadata-driven architecture). But we still need to answer: **what** are we measuring against? That's where test cases come in—turning our failure discoveries into concrete expectations.

## From Failure Analysis to Test Cases

Test cases turn our failure discoveries into concrete expectations. Each one captures what we learned during Open and Axial Coding.

Our HbA1c query that exposed three failures becomes test case `complex_002`:

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

Each field tests a specific dimension:
- `expected_complexity` → Complexity Classification
- `expected_specialties` → Specialty Selection  
- `key_data_points` → Analysis Quality
- `based_on_real_query` → Tracks real failures we found

This approach transforms random testing into systematic improvement. Every failure becomes a test case, every test case prevents future failures.

With evaluation methods, metadata framework, and test cases in place, we face our final challenge: who judges the subjective stuff? When you need to score "medical reasoning" or "contextual awareness," deterministic rules won't cut it. Enter the LLM Judge.

## LLM-as-Judge: Semantic Eval at Scale

You can't use math to score "context awareness" or "medical reasoning." These require understanding, not just pattern matching. That's where the LLM Judge comes in—it evaluates the things deterministic rules can't touch.

When judging specialist selection, it looks at:
- Did the agent pick medically appropriate specialists?
- Does the reasoning make sense?
- Do the specialists match what the query needs?
- Is the team set up for good coordination?

For our HbA1c query, something interesting happened: the agent picked wrong (0.75 precision—missing pharmacy and preventive medicine) but explained its choices well (0.90 rationale). The LLM Judge recognized the logic was sound even though the selection was incomplete.

*[Image: Specialist Selection Evaluation - Hybrid evaluation showing Specialist Precision at 0.75 (missing pharmacy and preventive medicine) while Specialist Rationale scores 0.90, demonstrating how LLM Judge recognizes sound reasoning despite incomplete selection.]*

Here's how the LLM Judge evaluates:

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

This structured prompting ensures consistent evaluation across hundreds of test cases, catching the nuanced reasoning that makes agents effective—or reveals why they fail.

## LLM Judge as Diagnostic Engine: The Improve Phase

Measurement without improvement is just expensive monitoring. The Improve phase transforms evaluation insights into concrete fixes.

The same LLM Judge that scored performance now switches roles—from evaluator to diagnostician. Instead of just telling you something failed, it analyzes why it failed and prescribes specific fixes. Every failed dimension in the framework includes these drill-down diagnostics.

Our CMO evaluation report shows where improvements are needed.

*[Image: CMO Evaluation Report - Overall evaluation showing 73.4% success rate with failures in Complexity Classification and Specialty Selection dimensions, highlighting where targeted improvements are needed.]*

Click any failure to see the LLM Judge diagnose root causes and prescribe fixes:

### Complexity Classification Failure (Score: 0.00)

*[Image: Complexity Classification Drill-Down - LLM Judge analysis revealing root cause: "The prompt does not provide clear enough guidance on what constitutes a COMPLEX query versus a STANDARD query, leading to misclassification in cases involving multiple related data points and potential correlations."]*

The agent called our multi-domain query STANDARD instead of COMPLEX. The Judge's prescription:
- **MODIFY**: Change "Trend analysis, 2-3 related metrics" to "Queries involving up to 2 related clinical metrics over time"
- **ADD**: Our HbA1c query as a COMPLEX example
- **TARGET**: `1_gather_data_assess_complexity.txt`

### Specialty Selection Failure (Score: 0.81)

*[Image: Specialty Selection Drill-Down - Hybrid evaluation showing 0.75 precision (missing pharmacy and preventive medicine) with LLM Judge identifying: "The pharmacy and preventive_medicine specialists were incorrectly excluded from the selection, even though the query mentioned metformin dosage adjustments and correlations with weight changes over time."]*

Good reasoning (0.90) but missed two specialists. The fix:
- **ADD**: "ALWAYS include pharmacy when query mentions: medication names, dosages, dosage adjustments"
- **ADD**: "ALWAYS include preventive_medicine for correlations between lab values/medications and risk factors"
- **ADD KEYWORDS**: ['medication', 'drug', 'dosage', 'dose', 'prescription']

Each recommendation specifies the exact file to modify and what impact to expect. The framework turns evaluation failures into targeted improvements that prevent similar issues in future queries.

## From Theory to Practice: The Eval Development Studio

All this methodology means nothing without tools that make it accessible. That's why I built the Eval Development Studio—a workspace where the Analyze-Measure workflow happens naturally.

Here's how it works: After running any health query, click "Create Test Case" to enter the Studio. The Eval Development Assistant (EDA) immediately analyzes your trace and creates an initial test case. But here's the key—it starts with expected values matching what actually happened. Your job is to fix that.

*[Image: Eval Development Studio interface showing the three-panel layout: agent chat, trace/evaluation report, and test case editor]*

The EDA guides you through Open Coding in real-time. Tell it "the complexity should be COMPLEX, not STANDARD" and watch it update the test case. Spot missing specialists? The EDA adds them to the expected list. It's like pair programming for evaluation—you bring domain expertise, the EDA handles the mechanics.

When you're ready, click Run Evaluation. The same trace that revealed failures now gets scored against your corrected expectations. No re-running agents, no waiting. Just instant feedback showing exactly where your agent fails and why.

This tight loop—trace → identify failures → update expectations → measure → see results—transforms evaluation from a chore into a conversation. The Studio makes eval-driven development not just possible, but natural.

## The Skill That Defines AI's Future

Kevin Weil was right: evaluation has become the defining skill for AI product development. But it goes deeper than he suggested.

We've moved from catching bugs to understanding reasoning. From binary pass/fail to measuring judgment and context. From testing single functions to evaluating how multiple agents coordinate and make decisions together.

The organizations that master eval-driven development will build AI that gets better systematically. Instead of hoping a clever prompt fixes everything, they'll have structured feedback loops that identify failures, diagnose root causes, and guide improvements. They'll know exactly where their agents fail, why they fail, and how to fix them.

This is the real paradigm shift: AI evaluation isn't about checking if something works. It's about understanding how AI thinks, decides, and reasons—then making it better. In a world where AI handles critical decisions, that understanding makes the difference between systems that fail mysteriously and those that improve predictably.

---

*George Vetticaden is an AI Agent Product Leader with 14+ months of experience building enterprise AI agent platforms. He recently served as VP of Agents at a leading AI startup, where he led the development of agent building tools and document intelligence solutions.*

*Connect with him on [LinkedIn](https://linkedin.com/in/georgevetticaden) to discuss the future of AI evaluation frameworks.*

*Read Part 1: [The 3 Amigo Agents: The Claude Code Development Pattern I Discovered While Implementing Anthropic's Multi-Agent Architecture](link)*