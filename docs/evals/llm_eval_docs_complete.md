## Document 2: Application-Centric AI Evals for Engineers and Technical PMs

**Application-Centric AI Evals for Engineers and Technical PMs**
*Shreya Shankar and Hamel Husain*
*May 2025*

Evaluating the complex, often subjective outputs of Large Language Models (LLMs) presents unique challenges distinct from traditional software testing or ML validation. We present a framework for application-centric LLM evaluation: the Analyze-Measure-Improve lifecycle.

#### Contents

1. Introduction
   1.1 What is Evaluation?
   1.2 The Three Gulfs of LLM Pipeline Development
   1.3 Why LLM Pipeline Evaluation is Challenging
   1.4 The LLM Evaluation Lifecycle: Bridging the Gulfs with Evaluation
   1.5 Summary

2. LLMs, Prompts, and Evaluation Basics
   2.1 Strengths and Weaknesses of LLMs
   2.2 Prompting Fundamentals
   2.3 Defining "Good": Types of Evaluation Metrics
   2.4 Foundation Models vs. Application-Centric Evals
   2.5 Eliciting Labels for Metric Computation
   2.6 Summary
   2.7 Glossary of Terms
   2.8 Exercises

3. Error Analysis
   3.1 Create a Starting Dataset
   3.2 Open Coding: Read and Label Traces
   3.3 Axial Coding: Structuring and Merging Failure Modes
   3.4 Labeling Traces after Structuring Failure Modes
   3.5 Iteration and Refining the Failure Taxonomy
   3.6 Common Pitfalls
   3.7 Summary
   3.8 Exercises

#### How To Read This Book

This book is a companion to the course AI Evals for Engineers and Product Managers (bit.ly/evals-ai). The course is designed for a broad audience ranging from engineers to technical product managers.

You will encounter code and math throughout the book. If you don't know how to code or are not familiar with the math, that's okay, just focus on the high-level concepts. You will gain tremendous value from understanding the process of evaluation, forming mental models, and recognizing common pitfalls.

We encourage you to engage with the examples and reflect on what makes evaluations work (or fail). Skip sections that feel out of scope from your role. When in doubt, ask questions in the course Discord. Think of this book as a flexible tool to support your learning.

Finally, this book is a rough draft that we will evolve over the next few months in response to student feedback. We would appreciate it if you kept this book to yourself for now. We will be working to publish an updated version of this book that is available to the public later this year.

### 1 Introduction

The past two years have seen rapid advances in the development and deployment of large language models (LLMs). Organizations are now embedding LLMs in critical pipelines in applications: customer service, content creation, decision support, and information extraction, among others (Bommasani et al. 2021; Zaharia et al. 2024). However, adoption is outpacing our ability to systematically evaluate LLM pipelines (Ward and Feldstein 2024).

Unlike traditional software, LLM pipelines do not produce deterministic outputs. Their responses are often subjective, context-dependent, and multifaceted. A response may be factually accurate but inappropriate (i.e., the "vibes are off"). They may sound persuasive while conveying incorrect information. These ambiguities make evaluation fundamentally different from conventional software testing and even traditional machine learning (ML).

**Note:** In traditional ML, outputs are well-defined—numbers, classes, or structured predictions. Standard metrics like accuracy or F1 score are widely used. Ground truth labels provide a clear target for evaluation. In contrast, LLM output can be open-ended, unstructured, and often subjective.

The core challenge is as follows: **How do we assess whether an LLM pipeline is performing adequately? And how do we diagnose where it is failing?** Our course focuses on this gap. Although significant work has been done on model development, prompting techniques, and pipeline architectures, rigorous evaluation has received comparatively little attention. In this reader, we will build a practical and theoretical foundation for LLM evaluation, with methods that you can immediately apply to your own projects.

**Note:** Our course is meant to be tool and model-agnostic; if a new LLM comes out tomorrow, our methodology will still be applicable.

#### Note to readers

This book focuses on evaluating LLM pipelines in specific applications. We don't cover general-purpose foundation model training or benchmarking. Our target audience is developers who integrate LLMs into real-world applications and need reliable evaluation methods. The approaches work with both commercial APIs and fine-tuned models.

### 1.1 What is Evaluation?

Before we dive into methods, we need a clear definition of evaluation.

**Evaluation** refers to systematic measurement of quality in an LLM pipeline. A good evaluation produces results that can be easily and unambiguously interpreted. Typically, this means a quantitative score, but it can also take the form of a structured qualitative summary or report.

Throughout this course, we will refer to an evaluation metric as an **eval**. A single pipeline will often use multiple evals to measure different aspects of performance. Evals can be operationalized in several ways. For example:

- **Background Monitoring** tracks evals passively over time to detect drift or degradation, without disrupting the primary workflow.
- **Guardrails** run evals in the critical path of the pipeline. If an eval fails, the pipeline can block the output, retry the operation, or fall back to a safer alternative before showing a result to the user.
- Evals can also be used to improve pipelines. For example, evals can label data for fine-tuning LLMs, select high-quality few-shot examples for prompts, or identify failure cases that motivate architectural changes.

Evals are essential not only to catch errors, but also to maintain user trust, ensure safety, monitor system behavior, and enable systematic improvement. Without them, teams are left guessing where failures occur and how best to fix them.

### 1.2 The Three Gulfs of LLM Pipeline Development

A useful framework for understanding LLM application development challenges is the "Three Gulfs" model (Figure 1), adapted from Shankar et al. (2025) and inspired by Norman (1988). This model captures the major gaps that developers must bridge when building any LLM pipeline.

**Example 1 (Email Processing Pipeline).** Consider a pipeline that processes incoming emails sent to an organization. The goal is to extract the sender's name, summarize the key requests, and categorize the emails.

At first glance, the task described in Example 1 seems simple. But each stage of development exposes new challenges across the Three Gulfs.

#### The Gulf of Comprehension (Developer → Data)

The first gulf separates us, the developer, from fully comprehending both our data and our pipeline's behavior on that data. Understanding the data itself—the inputs the pipeline will encounter, such as real user queries or documents like the emails in Example 1—is the starting point. At scale, it is difficult to know the characteristics of this input data distribution, detect errors within it, or identify unusual patterns. Thousands of inputs might arrive daily, with diverse formats and varying levels of clarity. We cannot realistically review each one manually.

**Hamel's Note:** The gulf of comprehension represents the fact that you must know what you want so you can effectively prompt a LLM, evaluate it, and debug it. Additionally, this process is iterative; our research and experience show that people refine their requirements to adapt to the behavior of the LLM. Shankar et al. (2024b). We discuss how to systematically look at data to inform your prompts in future sections.

Moreover, this gulf extends to understanding the LLM pipeline's actual outputs and common failure modes when applied to this data. Just as we cannot read every input, we also cannot manually inspect every output trace generated by the pipeline to grasp all the subtle ways it might succeed or fail across the input space. So the dual challenge is: how can we understand the important properties of our input data, and the spectrum of our pipeline's behaviors and failures on that data, without examining every single example?

#### The Gulf of Specification (Developer → LLM Pipeline)

The second gulf separates what we mean from what we actually specify in the pipeline. Our intent—the task we want the LLM to perform—is often only loosely captured by the prompts you write. Specifying tasks precisely in natural language is hard. Prompts must be detailed enough to remove ambiguity, and aligned with the structure and diversity of the data.

Even prompts that seem clear often leave crucial details unstated. For example, we might write:

*Extract the sender's name and summarize the key requests in this email.*

At first glance, this sounds specific. But important questions are left unanswered:

- Should the summary be a paragraph or a bulleted list?
- Should the sender be the display name, the full email address, or both?
- Should the summary include implicit requests, or only explicit ones?
- How concise or detailed should the summary be?

The LLM cannot infer these decisions unless we explicitly specify them. Without complete instructions, the model is forced to "guess" our true intent, often resulting in inconsistent outputs. The Gulf of Specification captures this gap between what we want and what we actually communicate.

**Hamel's Note:** Underspecified prompts are usually a direct result of not looking at the data (ignoring the "data" island).

**Shreya's Note:** In LLM development, prompt clarity surprisingly often matters as much as task complexity.

#### The Gulf of Generalization (Data → LLM Pipeline)

The third gulf separates our data from the pipeline's generalization behavior. Even if prompts are carefully written, LLMs may behave inconsistently across different inputs.

In the email processing example, imagine an email that mentions a public figure, like Elon Musk or Donald Trump, within the body text. The model might mistakenly extract these names as the sender, even though they are unrelated to the actual email metadata. This is not a prompting error. It is a generalization failure: the model applies the instructions incorrectly because it has not generalized properly across diverse data.

**Note:** The pipeline described in https://www.docetl.org/showcase/ai-rfi-response-analysis exhibits this failure mode.

The Gulf of Generalization reminds us that even when prompts are clear and well-scoped, LLMs may still exhibit biases, inconsistencies, or unexpected behaviors when encountering new or unusual inputs. Even as models get better, the Gulf of Generalization will always exist to some degree, because no model will ever be perfectly accurate on all inputs (Kalai and Vempala 2024).

### 1.3 Why LLM Pipeline Evaluation is Challenging

Developing effective evaluations for LLM pipelines is hard. It is a sufficiently different problem from traditional software engineering and machine learning operations (MLOps) that new approaches are required.

First, each application requires bridging the Three Gulfs anew. The specific ways in which understanding fails, prompts fall short, or generalization breaks down are unique to our task and dataset. There are no universal evaluation recipes.

Second, requirements often emerge only after interacting with early outputs. We might initially expect summaries to be written in prose but later realize that bulleted lists are easier for users to scan. Evaluation criteria must evolve alongside system development (Shankar et al. 2024b).

Third, appropriate metrics are rarely obvious at the outset. Unlike traditional software, where correctness is well-defined, LLM pipelines involve tradeoffs: factual accuracy, completeness, conciseness, style, and more. Choosing the right metrics depends on the specific goals of our application—and often requires experimentation.

Finally, there is no substitute for examining real outputs on real data. Generic benchmarks cannot capture the specific failure modes of our pipeline. For Example 1, without inspecting a diverse set of extracted senders, we would not notice that the model sometimes misidentifies public figures as senders. Systematic evaluation requires careful, hands-on analysis of representative examples.

**Hamel's Note:** If you are not willing to look at some data manually on a regular cadence you are wasting your time with evals. Furthermore, you are wasting your time more generally.

### 1.4 The LLM Evaluation Lifecycle: Bridging the Gulfs with Evaluation

The Three Gulfs—Comprehension, Specification, and Generalization—highlight the core challenges inherent in developing reliable LLM pipelines. **Evaluation provides the systematic means to understand and address these challenges.** In this course, we introduce a practical, iterative approach centered around evaluation: the **Analyze-Measure-Improve lifecycle**, depicted in Figure 2. This lifecycle provides a repeatable method for using evaluation to build, validate, and refine LLM pipelines, specifically aimed at overcoming the Three Gulfs.

The lifecycle begins with **Analyze**, directly tackling the Gulf of Comprehension. We inspect the pipeline's behavior on representative data to qualitatively identify failure modes. This critical first step illuminates why the pipeline might be struggling. Failures uncovered often point clearly to ambiguous instructions (Specification issues) or inconsistent performance across inputs (Generalization issues).

The findings from Analyze guide our next actions. Failures stemming directly from poor Specification—unclear prompts or ambiguous instructions—can often be addressed immediately in the Improve phase. We simply make the instructions clearer. However, other failures, particularly those suggesting inconsistent generalization or complex interactions, require deeper investigation. Understanding their true frequency, impact, and root causes demands quantitative data before effective improvements can be made.

This need for data drives the **Measure** phase. Here, we develop and deploy specific evaluators (evals) to quantitatively assess the failure modes identified in Analyze, especially those needing further scrutiny. Measurement provides hard numbers on failure rates and patterns. This data is crucial for prioritizing which problems to fix first and for diagnosing the underlying causes of tricky generalization failures.

Finally, the **Improve** phase leverages the findings from both previous phases to actively bridge the Gulfs of Specification and Generalization. We make targeted interventions. This includes direct fixes to prompts and instructions addressing Specification issues identified during Analyze. It also involves data-driven efforts—guided by the quantitative results from Measure—such as engineering better examples, refining retrieval strategies, adjusting architectures, or fine-tuning models to enhance generalization.

Cycling through Analyze, Measure, and Improve (Figure 2) creates a powerful feedback loop. It uses structured evaluation to systematically navigate the complexities posed by the Three Gulfs, leading to more reliable and effective LLM applications. We will cover each phase of the evaluation lifecycle in greater depth in the upcoming sections.

### 1.5 Summary

Effective evaluation is the foundation of reliable LLM applications. Without it, development reduces to guesswork. The key takeaways from this lecture are:

- Evaluation is not optional. It is essential for any serious LLM application.
- The Three Gulfs model helps categorize and diagnose different sources of failure.
- Choosing appropriate metrics requires examining our specific data and use case—not relying on generic benchmarks.
- The Analyze-Measure-Improve lifecycle provides a structured, repeatable method for building better evaluations over time.

In the next sections, we will dive deeper into evaluation metrics and systematic error analysis techniques.

## 2 LLMs, Prompts, and Evaluation Basics

### Note to readers

This section assumes the reader has a foundational understanding of Large Language Models (LLMs): that they are AI systems trained on vast amounts of text data to understand and generate human-like language, and that we interact with and instruct them using textual inputs known as prompts. For a glossary of specific terminology introduced and used throughout this chapter, please refer to Section 2.7.

In this section, we will first understand what LLMs are generally good at and where their limitations lie. Then, we'll explore how we interact with these models through prompting. Finally, we will introduce fundamental concepts of evaluation itself: defining what "good" means through metrics, understanding the important differences between evaluating foundation models versus specific applications, and exploring methods to gather feedback and assess results.

Readers new to this area may find some of the terminology unfamiliar or ambiguous. Rather than interrupt the narrative flow, we've placed definitions of essential terms in a glossary at the end of this chapter.

### 2.1 Strengths and Weaknesses of LLMs

LLMs are capable at producing fluent, coherent, and grammatically correct text. This extends to editing tasks such as simplifying sentences, adjusting tone, or rephrasing input for clarity. Their ability to make sense of information across a prompt enables effective summarization, translation, and question answering. Because they learn broad statistical patterns during training, they seemingly generalize to new tasks easily. A single prompt or a few demonstrations are often enough to guide the model, without retraining (Brown et al. 2020).

Despite their strengths, LLMs face limitations that stem from their architecture, training objective, and probabilistic nature.

#### Algorithmic generalization

One way to reason about the limitations of Transformers is to think about the kinds of "algorithms" they cannot do. They lack internal mechanisms for loops or recursion. This prevents reliable execution of tasks needing variable iterative steps. Examples include arbitrary-precision arithmetic or complex graph traversal. Generalization on algorithmic tasks beyond the training distribution is often poor; for example, a model trained on 3-digit addition may fail on 5-digit sums (Qian et al. 2022). Theoretical limits exist on the types tasks Transformers can perform (Hahn 2020; Weiss et al. 2021; Zhou et al. 2024).

**Note:** Techniques involving "test-time computation," such as Chain-of-Thought prompting (Wei et al. 2022), scratchpads (Nye et al. 2021), or equipping models with external tools (like calculators, code interpreters, or dedicated search/retrieval systems) (Schick et al. 2023), aim to mitigate these algorithmic limitations.

Moreover, LLM processing is also limited by an effective context window often shorter than the advertised maximum. While models may technically accept long inputs, empirical studies show that attention quality and output reliability degrade with length (Li et al. 2024).

#### Reliability and Consistency

LLM outputs are probabilistic. Generation involves sampling from a distribution over possible next tokens. This introduces nondeterminism: even identical prompts can yield different outputs. Such variability is at odds with the expectations of traditional software systems. While deterministic decoding methods like greedy sampling can reduce randomness, they often degrade output quality and accuracy.

In addition to nondeterminism, models lack built-in mechanisms for global consistency. They may contradict earlier statements within a single output or across turns in a conversation.

Moreover, LLMs also display significant prompt sensitivity (Sclar et al. 2024). Small changes in phrasing—rewording a question, shifting example order, or introducing irrelevant tokens—can lead to dramatically different completions. It remains an open question whether this reflects shallow pattern matching, overfitting to training distributions, or emergent properties of large-scale optimization.

#### Factuality

LLMs possess no internal notion of "truth." Their objective is to produce text that is statistically likely—not factually verified. As a result, they can hallucinate (Kalai and Vempala 2024). A model may confidently assert incorrect claims or fabricate details that sound plausible but are entirely false. There is no inherent mechanism to cross-check outputs against trusted knowledge sources or the external world. To achieve factual accuracy, systems must incorporate additional components such as retrieval-augmented generation (RAG) or external tools.

**Key Takeaway 2.1**
We should treat LLMs as powerful but imperfect components. We can leverage their strengths in language generation and understanding, but always anticipate variability, potential inaccuracies, and limitations in multi-step reasoning.

Given these strengths and weaknesses, how do we effectively interact with LLMs? The primary method is prompting.

### 2.2 Prompting Fundamentals

Prompting is the act of crafting the input text given to the LLM to elicit the desired output. A well-structured prompt typically includes several key pieces:

**Note:** For an interactive tutorial on prompt engineering concepts, see the guide by Anthropic: https://github.com/anthropics/prompt-eng-interactive-tutorial, as well as a guide by OpenAI: https://cookbook.openai.com/examples/gpt4-1_prompting_guide.

#### 1. Role and Objective:
- Clearly define the persona or role the LLM should adopt and its overall goal. This helps set the stage for the desired behavior.
- Example: "You are an expert technical writer tasked with explaining complex AI concepts to a non-technical audience."

#### 2. Instructions / Response Rules:
- This is a core component, providing clear, specific, and unambiguous directives for the task. For newer models that interpret instructions literally, it's vital to be explicit about what to do and what not to do.
- Use bullet points or numbered lists for clarity, especially for multiple instructions.
- Example:
  - "Summarize the following research paper abstract."
  - "The summary must be exactly three sentences long."
  - "Avoid using technical jargon above a high-school reading level."
  - "Do not include any personal opinions or interpretations."
- For complex instruction sets, consider breaking them into sub-categories (e.g., ### Tone and Style, ### Information to Exclude).

#### 3. Context:
- The relevant background information, data, or text the LLM needs to perform the task. This could be a customer email, a document to summarize, a code snippet to debug, or user dialogue history.
- Example: "[Insert the full text of the customer email here]"
- When providing multiple documents or long context, clear delimiters are crucial (see point 7).

#### 4. Examples (Few-Shot Prompting):
- Provide one or more examples of desired input-output pairs. This is highly effective for guiding the model towards the correct format, style, and level of detail. Examples can also clarify nuanced instructions or demonstrate complex tool usage.
- Example: Showing one or two sample emails and their ideal bullet-point action items, or a sample input and the correctly formatted JSON output.
- Ensure that any important behavior demonstrated in your examples is also explicitly stated in your rules/instructions.

#### 5. Reasoning Steps (Inducing Chain-of-Thought):
- For more complex problems, you can instruct the model to "think step by step" or outline a specific reasoning process. This technique, often called Chain-of-Thought (CoT) prompting, encourages the model to break down the problem and can lead to more accurate and well-reasoned outputs, even for models not explicitly trained for internal reasoning.
- Example: "Before generating the summary, first identify the main hypothesis, then list the key supporting evidence, and finally explain the primary conclusion. Then, write the summary."

#### 6. Output Formatting Constraints:
- Explicitly define the desired structure, format, or constraints for the LLM's response. This is critical for programmatic use of the output.
- Example: "Respond using only JSON format with the following keys: sender_name (string), main_issue (string), and suggested_action_items (array of strings)." Or, "Ensure your response is a single paragraph and ends with a question to the user."

#### 7. Delimiters and Structure:
- Use clear delimiters (e.g., Markdown section headers like ### Instructions ###, triple backticks for code/text blocks, XML tags) to separate different parts of your prompt, such as instructions, context, and examples. This helps the model understand the distinct components of your input, especially in long or complex prompts.
- A general recommended prompt organization, especially for complex prompts or long contexts, is to place overarching instructions or role definitions at the beginning, followed by context and examples, and potentially reiterating key instructions or output format requirements at the end.

The goal of effective prompting is to bridge the Gulf of Specification we discussed in Section 1—making our intent as explicit and unambiguous as possible for the model. What seems obvious to us might be unclear to the LLM. E.g., is "summarize" meant to be extractive or abstractive? Should the tone be formal or informal? Precision in our prompt is key.

However, finding the perfect prompt is rarely immediate. It's an iterative process. We'll write a prompt, test it on various inputs, analyze the outputs (using evaluation techniques we'll discuss in future sections), identify failure modes, and refine the prompt accordingly.

**Hamel's Note:** There are many tools that will write prompts for you and optimize them. It's important that you avoid these in the beginning stages of development, as writing the prompt forces you to externalize your specification and clarify your thinking. People who delegate prompt writing to a black box too aggressively struggle to fully understand their failure modes. After you have some reps with looking at your data, you can introduce these tools (but do so carefully).

An iterative refinement process hinges on having clear ways to judge whether the output is good or bad. This brings us to the concept of evaluation metrics.

### 2.3 Defining "Good": Types of Evaluation Metrics

Evaluation metrics provide systematic measurements of the quality of our LLM pipeline. At a high level, evals fall into two categories: reference-based and reference-free (Yan 2023).

#### Reference-Based Metrics

These evals compare the LLM's output against a known, ground-truth answer. We often call this known answer a "reference" or "golden" output. To use reference-based metrics, we must prepare the correct reference answers in advance for our test data. This is much like having an official answer key to grade a multiple-choice test. Reference-based metrics are often valuable during the development cycle, e.g., as unit tests. We typically use them in offline testing stages where curating ground truth is feasible, as we will explore further in ??.

Simple examples include:
- Check if the LLM output exactly matches the reference string (e.g., for short-answer extraction).
- Verify if the output contains specific keywords expected from the reference.

Beyond simple string comparisons, reference-based checks can become more complex. Sometimes, this involves executing the result and comparing the result with a reference output. For example:
- Executing generated SQL and checking if the output result or table matches a known correct result or table.
- Running LLM-generated code against pre-defined unit tests and verifying the results align with expected outcomes.

**Note:** For LLM-generated SQL, there are often many logically-equivalent but syntactically different SQL queries.

However, complexity can also arise in the comparison step itself, even without execution. We might need a sophisticated method—an "oracle" like an LLM judge or a human—to determine if the output is semantically equivalent or acceptably close to the reference. For example, an LLM itself could check if a generated paragraph conveys the same core meaning as a reference paragraph, even with different wording.

In some cases, we might combine approaches, such as executing generated code and then using an oracle to evaluate whether the runtime behavior aligns with the intended reference behavior.

#### Reference-Free Metrics

Alternatively, reference-free metrics evaluate an LLM's output based on its inherent properties or whether it follows certain rules, operating without a specific "golden" answer. This approach becomes crucial when dealing with output that is subjective, creative, or where multiple valid responses can exist. The goal is to check the desired properties of the output directly.

For example, when evaluating a text summarizer, a reference-free metric might involve checking if the summary introduces speculative claims or opinions not actually present in the original source material. For a customer service chatbot, we could assess whether it appropriately refrains from offering definitive medical or financial advice, instead guiding users toward expert consultation. When evaluating generated code, such metrics can verify if the code includes explanatory comments for non-trivial logic, or if it avoids using functions known to be deprecated. In a different domain, like marketing copy, we might use reference-free checks to ensure the text contains a clear call-to-action while also excluding specific types of overly aggressive sales phrases that are inconsistent with brand guidelines. These examples illustrate how reference-free qualities are highly application-specific.

Reference-free checks can also involve execution, but focus on validity rather than comparing results. For instance, we can assess if generated SQL executes without syntax errors or if generated code compiles cleanly and passes linter checks. Or, does a generated API call use valid parameter names and types according to the defined schema? Defining acceptable quality—avoiding speculation, using valid code, adhering to brand voice—depends entirely on the specific use case and requirements (Liu et al. 2024; Shankar et al. 2024a). In production, generating real-time ground truth is often impractical, making these self-contained checks vital (a topic that we revisit in ??).

The distinction between reference-based and reference-free metrics highlights a broader point: the way we evaluate depends heavily on what we are evaluating.

**Hamel's Note:** Why should you care about reference-free vs based? Reference-based metrics are preferred when it is feasible to have them. You can often derive a reference-based way of evaluating a failure by isolating intermediate steps, or reverse engineering references. For example, for you can construct a reference-based dataset to test retrieval by using a LLM to generate queries for specific documents such that you get (query, document) pairs. More on this later.

### 2.4 Foundation Models vs. Application-Centric Evals

We often hear about LLMs that achieve impressive results on public benchmarks such as MMLU (Hendrycks et al. 2021), HELM (Liang et al. 2023), or GSM8k (Cobbe et al. 2021). It is important for us to understand how these evaluations differ from those we typically perform for our own applications.

We can think of foundation model evals (the popular benchmarks) as assessing the general capabilities and knowledge of the base LLM itself. The methodology typically involves public datasets that cover areas such as math, coding, and general purpose reasoning. For engineers and product builders, these benchmarks offer a rough sense of a model's overall power. They can be useful for initial model selection; a higher benchmark score might indicate a better starting point for our application.

**Shreya's Note:** Think of foundation model evals as "standardized tests." When hiring people, we rely on more than standardized test scores. The same principle applies when picking LLMs to use in our applications—we need application-specific evals.

In contrast, application evals represent our primary day-to-day focus. Their purpose is assessing if our specific pipeline performs successfully on our specific task using our realistic data. Foundation models undergo extensive alignment (SFT/RLHF) using provider-specific data and preferences. However, this general post-training process and its resulting model "taste" are opaque to us. There is no guarantee that it matches our application's specific requirements. So, we have to rely heavily on metrics that we design ourselves to capture our specific quality criteria. Examples include measuring helpfulness according to our users' goals, ensuring adherence to our specific output formats, or enforcing safety constraints relevant to our domain.

**Hamel's Note:** You should be extremely skeptical of generic metrics for your application. In most cases, they are a distraction and provide illusory benefit. The quickest smell that an evaluation has gone off the rails is to see a dashboard packed with generic metrics like "{hallucination, helpfulness, conciseness, truthfulness}score".

Since application-specific evaluations often involve criteria beyond simple right/wrong answers, we need methods to systematically capture these judgments. How do we actually generate these evaluation signals?

### 2.5 Eliciting Labels for Metric Computation

How do we actually generate the scores or labels needed to compute our metrics? This question is especially pertinent for reference-free metrics, where there is no golden answer key. How can we systematically judge qualities defined by our application, like "helpfulness" or "appropriateness"? The process often requires methods for eliciting structured judgment, using either human reviewers or sometimes another LLM (as we will discuss in ??).

#### Direct Grading or Scoring

The most common method of evaluations for AI applications is Direct Grading or Scoring. Here, an evaluator assesses a single output against a predefined rubric. This rubric might use a scale (e.g., 1-5 helpfulness) or categorical labels (e.g., Pass/Fail, Tone: Formal/Informal/Casual). Evaluators can be human annotators, domain experts, or a well-prompted "LLM-as-judge," or an LLM that has been prompted to assess outputs according to the rubric. Obtaining reliable direct grades demands extremely clear, unambiguous definitions for every possible score or label.

**Note:** Defining distinct, objective criteria for each point on a 1-5 scale, for example, can be surprisingly difficult. Especially in the beginning of the lifecycle of an AI application, it is not clear what each numeric point means. For this reason, simpler binary judgments (like Yes/No for "Is this summary faithful to the source?") are often easier to define consistently and can be a very effective starting point.

Direct grading is most useful when our primary goal is assessing the absolute quality of a single pipeline's output against our specific, predefined standards.

#### Relative Comparisons

Other methods focus instead on relative comparisons. Pairwise comparison presents an evaluator with two outputs (A and B) generated for the same input prompt. The evaluator must then choose which output is better based on a specific, clearly defined criterion or rubric—for example, "Which response more directly answers the user's question?" or "Which summary is more factually consistent with the source document?" While this still requires unambiguous comparison criteria, making this relative choice between two options is frequently cognitively easier for evaluators than assigning a precise score from a multi-level scale. Ranking extends this relative judgement idea. Evaluators order three or more outputs generated for the same input from best to worst, according to the same clearly defined quality dimension specified in the comparison rubric. Ranking provides more granular relative information than pairwise comparison, though it typically requires more evaluator effort. These relative judgment methods are particularly useful when our main goal is to compare different systems or outputs directly. We might use them for A/B testing different prompts, comparing candidate models, or selecting the best response when our pipeline generates multiple options for a single input. Foundation model providers frequently use pairwise comparisons and ranking during post-training. For us developing applications, these relative methods might be most relevant when comparing distinct pipeline versions (perhaps ones that score similarly on direct grading metrics) or if we are fine-tuning models ourselves.

**Key Takeaway 2.2 Eliciting Feedback**
Generating evaluation data, especially for reference-free metrics, often relies on structured judgment based on clear criteria. Common methods we use include direct grading against rubrics (assessing absolute quality, requires clear definitions for each level), pairwise comparison (A vs. B based on a criterion, assessing relative quality), and ranking multiple outputs (more granular relative assessment).

### 2.6 Summary

In this section, we built a conceptual foundation for evaluating LLM applications. We came to understand them as powerful but fallible engineering components, possessing distinct strengths and weaknesses stemming from their design and training. We saw that prompting is our primary interface for directing these components. Effective prompting requires care, precision, and iteration. We defined evaluation metrics and explored the distinction between reference-based and reference-free approaches. We contrasted the world of general foundation model benchmarks with the specific, context-dependent needs of application evaluation—the core focus of our work here. We then explored practical ways we can elicit evaluation feedback, particularly for subjective qualities, using methods like grading, pairwise comparisons, and ranking.

With this landscape mapped out, we are now prepared to explore into the practical, iterative process of building effective evaluations. The next chapter introduces the Analyze-Measure-Improve lifecycle.

### 2.7 Glossary of Terms

The following glossary defines core concepts referenced throughout this chapter. If you're encountering unfamiliar terms or want a refresher, this section offers a concise reference.

- **Large Language Model (LLM):** A model trained on massive text corpora to generate and understand human-like language.
- **Foundation Model:** A large, general-purpose model trained on diverse data. During pre-training, it learns to predict the next token in a sequence, allowing it to internalize grammar, facts, and language structure.
- **Token:** The smallest unit of text processed by an LLM, often a word, subword, or punctuation mark.
- **Context Window:** The sequence of previous tokens an LLM uses to generate the next one. This is bounded in size, and limits coherence over long passages.
- **Prompt:** The input text used to elicit an output from an LLM. Prompts include instructions, context, examples, and formatting constraints.
- **Evaluation / Metric:** A method for judging output quality. Metrics can be reference-based (using ground truth) or reference-free (checking properties).
- **Pre-training:** The initial training phase where the LLM learns by predicting the next token across vast text datasets. This phase imparts broad linguistic and factual knowledge.
- **Attention:** A mechanism in transformer models that computes relevance scores between tokens, allowing the model to selectively focus on different parts of the input.
- **Post-training:** The stage after pre-training that aligns the model with human intent. This includes Supervised Fine-Tuning (SFT) and Reinforcement Learning from Human Feedback (RLHF), and more recently, Direct Preference Optimization (DPO).
- **Supervised Fine-Tuning (SFT):** Additional training using labeled examples of desired prompt-response behavior to guide the model's outputs.
- **RLHF (Reinforcement Learning from Human Feedback):** A technique where human preferences are used to train a reward model, which then guides LLM fine-tuning.
- **DPO (Direct Preference Optimization):** A recent method that skips the reward model and fine-tunes directly using human preference rankings.

### 2.8 Exercises

#### 1. Prompt Engineering

You need to summarize customer support emails into a list of action items.

(a) Write a zero-shot prompt including instruction and formatting constraints.
(b) Extend it to a one-shot prompt with an example.

**Solution 2.1**
(a) Zero-shot:
"Summarize the following support email into bullet-point action items. Email: [EMAIL TEXT]"

(b) One-shot:
"Example: Email: 'My account locked...'; Action items: – Reset password – Verify email on file –-– Now summarize: [EMAIL TEXT]"

#### 2. Metric Classification

For each of these metrics, state whether it is reference-based or reference-free, and justify in one sentence:

(a) Exact match accuracy against ground-truth SQL.
(b) Checking generated code compiles without errors.
(c) ROUGE score against human summary.
(d) Verifying no speculative claims in a generated summary.

**Solution 2.2**
(a) Reference-based—compares to known SQL. (b) Reference-free—checks validity of code, no ground truth. (c) Reference-based—measures overlap with human summary. (d) Reference-free—checks property of output, not against reference.

#### 3. Foundation vs. Application Evals

Suppose you choose between GPT-4 and Claude for a legal-document summarizer.

(a) Name one foundation benchmark you would consult and why.
(b) Design an application-specific eval test for fidelity to client needs.

**Solution 2.3**
(a) MMLU—measures general reasoning across domains. (b) Collect 20 real legal memos, have attorneys rate summaries on accuracy and relevance, binary Pass/Fail.

#### 4. Eliciting Labels (Travel Assistant)

You need to evaluate whether a travel assistant's flight recommendations respect the user's budget constraint.

(a) Write a direct-grading rubric with two labels: Within Budget and Over Budget, and clear criteria for each.
(b) Draft a pairwise-comparison instruction for an annotator to choose which of two flight suggestion lists better adheres to the budget.
(c) In 2–3 sentences, explain when you would prefer direct grading versus pairwise comparison for this task.

**Solution 2.4**
(a) Direct-Grading Rubric:
Within Budget: All suggested flights have price ≤ user's maxPrice.
Over Budget: At least one suggested flight exceeds the user's maxPrice.

(b) Pairwise-Comparison Instruction:
```
You are given a user query: "Find flights under $300 from JFK to LAX." You also have two lists of three flight options (A and B). Choose which list better respects the budget constraint and reply with "A" or "B," followed by a one-sentence justification.
```

(c) When to Use:
Direct grading is ideal when you need an absolute adherence rate and the criterion is unambiguous. Pairwise comparison is preferable when distinguishing among borderline cases or when annotators find relative judgments easier than strict binary labels.

## 3 Error Analysis

The process of developing robust evaluations for LLM applications is inherently iterative. It involves creating test cases, assessing performance, and refining the system based on those observations. High-level guides, such as Anthropic's documentation on creating empirical evaluations for Claude (Anthropic 2024), often depict this as a cycle of developing test cases, engineering prompts, testing, and refining (Figure 3).

**Note:** See, for example, Anthropic's guide: https://docs.anthropic.com/en/docs/build-with-claude/develop-tests

This section, and indeed our overall "Analyze-Measure-Improve" lifecycle (Figure 2), provides a detailed, step-by-step methodology for the Analyze portion of this iterative loop—specifically focusing on how we systematically surface failure modes by bootstrapping initial datasets and structuring our understanding of errors.

We ground our discussion in a running example: a real estate CRM assistant.

**Example 2 (Real Estate Agent).** The assistant powers real estate agents' workflows. Given natural language queries, it can generate SQL queries to retrieve listing data, summarize trends, draft emails to clients, and read calendars. Typical user queries might include: "Find me 3-bedroom homes under $600k near downtown. Email the top 2 matches to my client. Figure out if there are showings available for this weekend."

**Note:** This example is taken from Husain (2025)'s "Field Guide to Rapidly Improving AI Products."

The pipeline is agentic. An LLM call interprets the user's request and returns structured actions. Each action—querying listings, drafting an email, reading the showings calendar—invokes a downstream tool. Outputs are fed back to the LLM, which may issue further actions based on new information. The process repeats until the system validates and executes all operations.

**Note:** By agentic, we mean an architecture where an LLM decides what the next step in the pipeline should be should be.

In the rest of this section, we will detail the steps of error analysis, as depicted in Figure 4.

### 3.1 Create a Starting Dataset

Every error analysis starts with traces: the full sequence of inputs, outputs, and actions taken by the pipeline for a given input.

Ideally, we want to start with around 100 traces. This gives enough coverage to surface a wide range of failure modes and push toward theoretical saturation—the point at which analyzing additional traces is unlikely to reveal sufficiently new categories or types of errors, as existing concepts are well-developed and new data largely confirms them (Morse 1995). If 100 real user queries already exist, we sample them directly. If more are available, even better. Diversity matters: traces should stress different parts of the system, not just repeat the same feature path. To achieve this, we can cluster queries using embeddings or keyword heuristics and sample across clusters. Random sampling works too when the query pool is small.

In early-stage pipelines, however, real user traces are often sparse. In those cases, we generate synthetic data—but carefully. We should not simply prompt an LLM to "give us user queries." Naively generated queries tend to be generic, repetitive, and fail to capture real usage patterns. Instead, we will generate synthetic queries more systematically.

**Note:** Interestingly, for many applications, the variety of fundamental user intents (i.e., underlying query types) is often surprisingly limited– -perhaps on the order of 10 to 20 core types. Understanding these core query types is highly beneficial when bootstrapping a starting dataset, especially if real user traces are sparse. This principle is observable even in complex systems like web search engines: while users can type almost anything into a search bar, a significant portion of queries can be categorized into recognizable underlying intents such as navigational (e.g., trying to reach a specific website like "youtube"), informational (e.g., seeking an answer like "what is the capital of France"), transactional (e.g., looking to perform an action like "buy cheap flights to London"), or local queries (e.g., "pizza near me"). Identifying such underlying types helps in structuring the generation or sampling of test cases.

First, before prompting anything, we define key dimensions of the query space. Note that dimensions will be different for every application. These dimensions help us systematically vary different aspects of a user's request.

#### Dimension

A dimension is a way to categorize different parts of a user query. Each dimension represents one axis of variation. For example, in a real estate assistant, useful dimensions might include:
- **Feature:** what task the user wants to perform (e.g., property search, scheduling)
- **Client Persona:** the type of client being served (e.g., first-time buyer, investor)
- **Scenario Type:** how clearly the user expresses their intent (e.g., well-specified, ambiguous)

Our application can have many useful dimensions. We recommend starting with at least three. Do not choose these dimensions arbitrarily! Instead, choose the dimensions that describe where your AI application is likely to fail. For example, in the real estate example, we might have discovered through usage or qualitative data that certain personas (e.g., investors) are experiencing issues when using specific features (e.g., property search).

**Note:** If you do not know where your product might fail, build intuition by using the product yourself. Alternatively, recruit a few people to use the product and use those failures to motivate the dimensions.

Once we've defined our dimensions, we create structured combinations of them.

#### Tuple

A tuple is a specific combination of values—one from each dimension—that defines a particular use case. For example:
- **Feature:** Property Search
- **Client Persona:** Investor
- **Scenario Type:** Ambiguous

This tuple describes a case where an investor is searching for properties, but the request may be underspecified or vague. We use these tuples as inputs to generate realistic queries.

Here are two example queries sketched from different tuples:
- **Tuple:** (Feature: 'Property Search', Persona: 'First Time Buyer', Scenario: 'Specific Query')
  **Query:** Find 3-bedroom homes under $600k near downtown that allow pets.
- **Tuple:** (Feature: 'Property Search', Persona: 'Investor', Scenario: 'Vague Query')
  **Query:** Look up showings for good properties in San Mateo County.

Writing 20 of these tuples by hand helps us understand our problem better. If we're unsure, we can ask domain experts for example tuples. Once we have a small set of example tuples and queries, we use an LLM to scale up to 100 or more. But instead of having the LLM generate full queries directly—which often leads to repetitive phrasing—we break the process into two steps. First, we sample structured tuples: feature, persona, and scenario. Then, for each tuple, we generate a natural-language query using a second prompt. This separation leads to more diverse and realistic results than simply asking an LLM to generate synthetic data for our task in one single prompt. We illustrate the full process in Figure 5.

**Hamel's Note:** Don't begin generating synthetic data without a hypothesis about where your AI app will fail. At the outset, synthetic data should target these anticipated failures. After gaining familiarity, you can expand the scope beyond your hypotheses to discover new errors.

In the first step, we prompt the LLM like this:

```
Generate 10 random combinations of (feature, client persona, scenario) for a real estate CRM assistant.

The dimensions are:
Feature: what task the agent wants to perform. Possible values: property search, market analysis, scheduling, email drafting.

Client persona: the type of client the agent is working with. Possible values: first-time homebuyer, investor, luxury buyer.

Scenario: how well-formed or challenging the query is. Possible values:
• exact match (clearly specified and feasible),
• ambiguous request (unclear or underspecified),
• shouldn't be handled (invalid or out-of-scope).

Output each tuple in the format: (feature, client persona, scenario)

Avoid duplicates. Vary values across dimensions. The goal is to create a diverse set of queries for our assistant.
```

For each LLM-generated tuple, we then generate a full query in natural language. The second prompt might look like:

```
We are generating synthetic user queries for a real estate CRM assistant. The assistant helps agents manage client requests by searching listings, analyzing markets, drafting emails, and reading calendars.

Given:
Feature: Scheduling 
Client Persona: First-time homebuyer 
Scenario: Ambiguous request

Write a realistic query that an agent might enter into the system to fulfill this client's request. The query should reflect the client's needs and the ambiguity of the scenario.

Example:
"Find showings for affordable homes with short notice availability."

Now generate a new query.
```

We continue sampling, generating, and filtering until we reach 100 high-quality, diverse examples. When phrasing is awkward or content is off-target, we discard and regenerate. It is better to be aggressive in quality control here: downstream evaluation is entirely based on the representativeness and realism of these traces.

**Note:** Why 100? This is a rough heuristic that helps people get started. We will share more intuition behind this number later. The most important part is to being the flywheel of looking at data to improve your product.

With a strong synthetic dataset in place, we're ready to start generating and reading traces to identify failure modes.

### 3.2 Open Coding: Read and Label Traces

With a data set of queries in hand, the next step is to run the assistant on all queries and collect complete traces.

A trace records the entire sequence of steps taken by the pipeline: the initial user query, every LLM output, each downstream tool invocation (such as database queries, email drafts, calendar proposals), and the final user-facing results. We collect all intermediate and final steps, not just the surface output. Failures often arise inside the chain, not only at the end. Once traces are collected, we begin systematically reading and labeling them.

This process is adapted from grounded theory (Glaser and Strauss 2017), a methodology from qualitative research that builds theories and taxonomies directly from data. Rather than starting with a fixed list of error types, we observe how the system behaves, label interesting or problematic patterns, and let the structure of failures emerge naturally.

**Note:** Arawjo (2025) also espouse thinking about error analysis through the lens of grounded theory.

In grounded theory, coding refers to assigning short descriptive labels to parts of the data that seem important (Strauss et al. 1990). We adopt the same idea here. For each trace, we read carefully and write brief notes about what we observe: where outputs are incorrect, where actions are surprising, or where the behavior feels wrong or unexpected. Each note is a potential signal of a failure mode or quality concern.

**Note:** Grounded theory calls this process "open coding."

When beginning, we recommend examining the entire trace as a whole and noting the first (most upstream) failure observed. Traces can be complex with many steps, and it is important not to get bogged down at this stage.

We record each trace and its corresponding open-coded notes into a simple table or spreadsheet. When traces are long, it is often desirable to use an observability tool that can render traces in a more humans readable fashion out of the box. We will discuss this more in ??. At this stage, the structure is minimal: one column for the trace identifier, a column for the trace, and a column for the free-form annotation.

We illustrate with a few realistic traces from the real estate CRM assistant in Table 1. Note that for brevity, we only present a summary of each trace step.

| User Query | Trace Steps (Summary) | First-Pass Annotation |
|------------|----------------------|----------------------|
| Find 3-bedroom homes under $600k near downtown that allow pets. | • Generate SQL query (missing pet constraint)<br>• Return 2 listings<br>• Draft email to client | Missing constraint: pet-friendly requirement ignored. |
| Set up showings for these two homes this weekend. | • Parse dates (Saturday, Sunday)<br>• Calendar API shows agent unavailable Saturday<br>• Propose showings both days | Invalid action: proposed unavailable times. |
| Send a property list to my investor client in San Mateo. | • Search for high ROI properties<br>• Draft casual email about starter homes | Persona mismatch: wrong tone and property type. |

**Table 1:** Examples of early traces and open-coded annotations. Each trace surfaces a distinct failure pattern before formal categorization.

At this stage, we do not attempt to group or formalize errors. We simply collect a rich set of raw observations. We can also assign each trace a holistic binary judgment: acceptable or unacceptable—a fourth column in our spreadsheet. This column is optional. Making a clear yes or no decision forces sharper thinking than vague scores (e.g., 3 out of 5). Even when the judgment feels borderline, we pick a side, and this process will clarify our evaluation criteria. However, the column may not be used in future steps, so it is okay to disregard making a holistic binary judgement.

Sometimes, when starting with initial labeling, it can be challenging to articulate precisely what feels "off" about a trace, or how to describe an observed failure. If we find ourselves stuck, a helpful strategy is to switch temporarily to a more "top-down" approach. Instead of waiting for themes to purely emerge, we can consider a list of common LLM failure categories and actively look for their manifestations in our specific application's traces. For example, knowing that "hallucination" (generating plausible but false information) is a common LLM issue, we could specifically inpsect each trace for instances where the assistant might be inventing facts, misrepresenting source information, or fabricating details—and when annotating, we can specifically describe how the hallucination occurred. Similarly, we could look for issues related to structured output (e.g., malformed JSON, incorrect list formatting), adherence to length constraints, or maintaining stylistic consistency, drawing inspiration from common output control types developers often need (Liu et al. 2024). Vir et al. (2025) provide a large dataset of assertion criteria that can be used for inspiration.

**Note:** Indeed, some failure modes or thresholds for what constitutes "bad" output only become clear after observing enough data. For instance, the GitHub Copilot team found that auto-generating excessively long code completions could be undesirable. While initially determining a precise length threshold for "too long" might seem arbitrary, an empirical approach can be taken: collect a set of completions that are weakly labeled as problematic (e.g., they correlate with low user acceptance rates or other negative feedback), and then analyze this set—perhaps by computing the average length—to establish a heuristic cutoff. This illustrates how data-driven insights can help define and refine certain failure criteria (Berryman et al. 2025).

**Note:** The goal isn't to force our traces into these predefined failure modes, but rather to use them as lenses to help identify and articulate specific problems that might otherwise be hard to pin down during initial labeling or open coding.

This initial round of annotation continues until we have surfaced a sufficiently broad set of failures. As a rule of thumb, we proceed until at least 20 bad traces are labeled and no fundamentally new failure modes are appearing. This point is known as theoretical saturation (Morse 1995): when additional traces reveal few or no new kinds of errors.

Reaching saturation depends primarily on the system's complexity, not merely on input diversity. Simple query types may saturate quickly. More complex agentic behavior (such as multi-step calendar and client personalization workflows) often requires deeper exploration.

Once a sufficient body of open-coded traces and early failure notes has been collected, we are ready to move to the next step: organizing these observations into structured failure modes.

### 3.3 Axial Coding: Structuring and Merging Failure Modes

Open labeling or coding produces a valuable but chaotic collection of observations. Each trace yields its own raw notes: missing constraints, invalid actions, inappropriate tones, hallucinated facts. At this stage, the data is rich but unstructured. Without further organization, we cannot meaningfully quantify failures.

To impose structure, we draw on the next phase of grounded theory methodology: axial coding (Strauss et al. 1990; Glaser and Strauss 2017). Axial coding is the process of identifying relationships among codes generated in the first pass (i.e., open codes) and grouping them into higher-order categories. It moves us from isolated observations to a coherent list of unique, recurring failure types.

In our context, axial coding means reading through the body of open-coded traces and clustering similar failure notes together. Some patterns are obvious. Traces where the assistant proposes showings for weekends when the real estate agent is marked unavailable, or drafts emails listing properties outside a buyer's stated budget, cluster naturally into a broader failure mode: violation of user constraints.

Other failures reveal deeper distinctions only after reading several traces. In early coding, hallucinations of property features—claiming a home has solar panels when it does not—and hallucinations of client activity—scheduling a tour that the user never requested—were initially grouped together. But over time, it becomes clear they differ meaningfully: one misleads about external facts; the other fabricates user intent. We split them into hallucinated listing metadata and hallucinated user actions.

We present another example of splitting failure modes. An email drafted for a first-time buyer that uses investor jargon ("high cap rate returns") is not the same as a casual, slang-filled email sent to a luxury client ("sick penthouse deal coming in hot"). Both seem like "bad communication" at first. On closer review, the first reflects persona misidentification; the second reflects inappropriate tone and style—and we can classify them differently.

Axial coding requires careful judgment. When in doubt, consult a domain expert. The goal is to define a small, coherent, non-overlapping set of binary failure types, each easy to recognize and apply consistently during trace annotation.

While early clustering is often done manually, it is also possible to use a language model to assist the process. For example, after open coding 30–50 traces, we can paste the raw failure notes into our favorite LLM (e.g., ChatGPT, Claude) and ask it to propose preliminary groupings. A simple, effective prompt might look like:

```
Below is a list of open-ended annotations describing failures in an LLM-driven real estate CRM assistant. Please group them into a small set of coherent failure categories, where each category captures similar types of mistakes. Each group should have a short descriptive title and a brief one-line definition. Do not invent new failure types; only cluster based on what is present in the notes.
```

LLM-generated groupings can help organize initial ideas, but they should not be accepted blindly. Proposed clusters often require manual review and adjustment to accurately reflect the system's behavior and the application's specific requirements.

At the end of axial coding, we have a list of distinct, binary failure modes, along with representative examples illustrating each one. These examples provide essential reference points as we move into the next stage: systematically labeling and quantifying failures across all traces.

**Note:** There are other ways to cluster queries using classical machine learning techniques, but we have found that using a LLM to categorize annotations is both effective and pragmatic.

### 3.4 Labeling Traces after Structuring Failure Modes

At this stage, we have two artifacts:

1. A collection of traces, each with its initial, freeform "first-pass annotations."
2. A defined list of structured, binary failure modes (from axial coding), which represent the higher-order categories of errors we've identified.

Our next goal is to systematically apply these structured failure modes to each trace, creating a dataset ready for quantification. This means for every trace, and for each defined failure mode, we determine if that specific failure is present (1) or absent (0).

The process of assigning these structured labels bridges the gap from qualitative observation to quantitative data:

#### Review and Map Open Codes to Structured Failures

We revisit our initial spreadsheet of traces and their first-pass annotations. For each trace, we compare its freeform annotation against our defined list of structured failure modes.

- If we manually derived the failure modes in the previous step (axial coding), this involves applying that derived mapping.
- If an LLM assisted in generating the failure mode categories, we now need to ensure these categories are consistently applied back to each trace's original annotation. This might involve the engineer carefully reviewing each trace's open code and assigning the appropriate structured failure mode(s). Alternatively, one could prompt an LLM for each trace: "Given this annotation on a trace: '[open_annotation here]' and our list of defined failure modes: '[list_of_failure_modes]', which failure modes apply?" Any LLM-assisted mapping requires human review and spot-checking to ensure accuracy and consistency, and to refine the failure mode definitions if discrepancies arise. This review process itself is valuable, as it deepens our understanding of the failure modes and their manifestations

#### Populating the Structured Data Table

We augment our spreadsheet (or database table) by adding new columns, one for each structured failure mode. For each trace, we then populate these columns with a 1 if the failure mode is present for that trace (based on the mapping above) and a 0 if it's absent.

For example, if a first-pass annotation for a trace was "SQL query missed the budget constraint and also used an aggressive tone in the generated email," and our structured failure modes include "Missing SQL Constraint" and "Inappropriate Tone," this trace would get a 1 in both those columns and 0s in others.

During this process, it is common to discover inconsistencies or edge cases that force a reevaluation. Some traces initially annotated as problematic may, on closer inspection, not cleanly match any defined failure mode. Other traces may reveal nuances that suggest refinements to the categories. We allow ourselves to adjust annotations or revise failure mode definitions as needed.

Once labeling is complete, we can quantify the prevalence of each failure mode. We can compute error rates for each failure mode, if in a spreadsheet (e.g., using a formula like SUM(column) to count occurrences, then dividing by the total number of traces to get a rate). Python libraries like Pandas, or features like pivot tables in spreadsheets, allow for more flexible aggregation, filtering, and calculation of failure rates across different segments of the data. This quantification allows us to see, for each failure mode, how often it appears across the dataset, which is critical for prioritization in the Improve phase.

### 3.5 Iteration and Refining the Failure Taxonomy

Error analysis is rarely a one-shot effort; iteration is important. It's common to conduct two or three rounds of reviewing traces and refining the failure mode taxonomy. Early rounds often uncover initially missed failure modes, or reveal that the initial definitions for failure categories need adjustment. As we analyze more traces—either by labeling existing unlabeled ones or by sampling new queries as described in Section 3.1—our understanding of the data (thereby bridging the Gulf of Comprehension as in Figure 1) improves. We continually refine the taxonomy by merging similar categories, splitting overly broad ones, or clarifying definitions as new error patterns emerge.

In the real estate CRM assistant project, a second round of analysis might expose a new error not apparent in the first batch; the assistant may occasionally misinterpret location names by defaulting to local cities without explicit clarification. For example, perhaps a user asking about "Springfield" listings received results from the wrong state entirely. This would surface the need for stronger disambiguation rules in both query generation and downstream SQL templates, leading us to add location ambiguity errors as a distinct failure mode.

Iteration is not endless. In practice, two serious rounds of open coding and re-annotation are often sufficient to approach theoretical saturation. Beyond that point, additional sampling typically yields diminishing returns, with few genuinely new failure types emerging.

### 3.6 Common Pitfalls

The most common mistake in early error analysis is failing to test on representative data. If the initial query set does not reflect the diversity and difficulty of real user behavior, the traces produced are uninformative. Either no serious failures occur, or the few failures that appear are not the ones that would arise in production.

A second common failure is skipping open coding altogether. Instead of reading real traces and observing how the system actually fails, teams often default to generic categories pulled from LLM research: "hallucination," "staying on task," "verbosity." These broad labels may sound reasonable, but without grounding in real examples, they often miss critical application-specific issues. In the real estate CRM assistant, for instance, errors like proposing unavailable showings or misidentifying client personas are far more damaging than generic verbosity.

**Hamel's Note:** The abuse of generic metrics is endemic in the industry as many eval vendors promote off the shelf metrics, which ensnare unsuspecting engineers into superfluous metrics and tasks.

Another frequent pitfall is the inappropriate use of Likert scales during early annotation. A Likert scale asks annotators to rate qualities (such as relevance or helpfulness) on a numeric scale, typically 1 to 5 or 1 to 7. While widely used in LLM evaluations (Chiang et al. 2023; Zheng et al. 2023; Kim et al. 2023), Likert scales introduce substantial noise when applied without a detailed rubric. This phenomenon has been widely observed in annotation and survey research: when rubrics are underspecified, rating scales lead to lower inter-annotator agreement and higher subjective variance (Artstein and Poesio 2008). In contrast, forcing binary decisions about specific failure modes—whether a problem occurred or not—produces more reproducible annotations (Husain 2025; Shankar et al. 2024a; Yan 2024).

Finally, treating initial annotations and failure modes as fixed is a critical error. It is normal for annotation schemas to evolve after reviewing more data. New examples may reveal edge cases that require refining definitions. Freezing the schema too early locks evaluation infrastructure around an incomplete understanding of system behavior.

**Note:** A critical misstep in error analysis is excluding domain experts from the labeling process, especially for applications that require deep subject matter knowledge. Outsourcing this task to those without domain expertise, like general developers or IT staff, often leads to superficial or incorrect labeling. Making the data and labeling process accessible to domain experts is important; building or tailoring simple annotation interfaces can be helpful for this, as we discuss further in ??.

Overall, a careful, iterative error analysis phase avoids these mistakes. It ensures that evaluation metrics are shaped by the real behaviors of the system under realistic conditions, not by assumptions or borrowed taxonomies.

### 3.7 Summary

The Analyze phase is the cornerstone of effective LLM evaluation, providing the deep, qualitative understanding necessary before any meaningful measurement or improvement can occur. This section detailed a systematic, iterative approach to error analysis. We began by emphasizing the importance of bootstrapping a diverse initial dataset (Section 3.1), using real user queries when available or, if not, a structured method for generating representative synthetic queries based on important application dimensions.

We then walked through the process of reading and labeling traces (Section 3.2) using techniques adapted from grounded theory. This involves open coding—making detailed, first-pass annotations on observed behaviors and potential failures—and continuing until theoretical saturation is approached. We also discussed strategies for when annotators get stuck, such as using a top-down approach by checking for known LLM failure types.

Next, we covered how to move from these raw observations to a manageable taxonomy by structuring failure modes (Section 3.3) through "axial coding." This step involves clustering similar open codes into a small, coherent, and non-overlapping set of binary failure categories.

Finally, we detailed the process of quantifying failure modes (Section 3.4). Throughout, we highlighted the importance of iteration (Section 3.5) in refining this failure taxonomy and cautioned against common pitfalls (Section 3.6) such as using unrepresentative data or skipping deep qualitative review.

Ultimately, the Analyze phase is not primarily about calculating performance scores. Instead, its critical output is a well-understood, application-specific vocabulary of failure: a clear, consistent set of defined failure modes that allows us to precisely describe, and subsequently measure, how and why our LLM pipeline isn't meeting expectations. This foundation is essential before proceeding to measure these failures at scale.

### 3.8 Exercises

#### 1. Synthetic Data Generation (Travel Assistant)

Define three key dimensions for a travel booking assistant. Then:

(a) List at least three values for each dimension.
(b) Write a prompt to generate 10 random structured tuples.
(c) Write a prompt to convert one example tuple—e.g. (Find Flight, Luxury Traveler, Flexible Dates)—into a natural-language query.

**Solution 3.1**

Dimensions and values:
- **Task Type:** {Find Flight, Find Hotel, Find Flight+Hotel, Activity Recommendation, General Inquiry}
- **Traveler Profile:** {Budget Traveler, Business Traveler, Family Vacationer, Luxury Traveler, Solo Backpacker}
- **Date Flexibility:** {Exact Dates, Flexible Dates, Open-Ended}

(b) Prompt to generate tuples:
```
Generate 10 random combinations of (Task Type, Traveler Profile, Date Flexibility) for a travel booking assistant. Possible values: Task Type: Find Flight, Find Hotel, Find Flight+Hotel, Activity Recommendation, General Inquiry. Traveler Profile: Budget Traveler, Business Traveler, Family Vacationer, Luxury Traveler, Solo Backpacker. Date Flexibility: Exact Dates, Flexible Dates, Open-Ended. Output each as: (Task Type, Traveler Profile, Date Flexibility) Ensure no duplicates and good coverage.
```

(c) Prompt to convert one tuple to a query:
```
We are generating synthetic user queries for a travel assistant. Given: Task Type: Find Flight Traveler Profile: Luxury Traveler Date Flexibility: Flexible Dates Write a realistic query a luxury traveler might use, reflecting flexibility in travel dates. Example (for another tuple): (Find Hotel, Business Traveler, Exact Dates) → "Need a 4-star hotel near the airport in Seattle from Sept 10–12, must have airport shuttle." Now generate a query for (Find Flight, Luxury Traveler, Flexible Dates).
```

#### 2. Synthetic Data Generation (E-Commerce Chatbot)

Define three key dimensions for an e-commerce chatbot. Then:

(a) List at least three values for each dimension.
(b) Write a prompt to generate 10 random structured tuples.
(c) Write a prompt to convert one example tuple into a natural-language query.

**Solution 3.2**

Dimensions and values:
- **Intent:** {Search Product, Compare Prices, Check Availability, Track Order, Return Request}
- **Customer Segment:** {Bargain Hunter, Brand-Loyal, Gift Shopper, Bulk Buyer}
- **Urgency:** {Immediate Need, Planned Purchase, Browsing}

(b) Prompt to generate tuples:
```
Generate 10 random combinations of (Intent, Customer Segment, Urgency) for an e-commerce chatbot. Intent: Search Product, Compare Prices, Check Availability, Track Order, Return Request. Customer Segment: Bargain Hunter, Brand-Loyal, Gift Shopper, Bulk Buyer. Urgency: Immediate Need, Planned Purchase, Browsing. Output each as: (Intent, Customer Segment, Urgency) No duplicates; maximize variety.
```

(c) Prompt to convert one tuple to a query:
```
We are generating synthetic user queries for an e-commerce chatbot. Given: Intent: Compare Prices Customer Segment: Bargain Hunter Urgency: Planned Purchase Write a realistic query a bargain hunter planning ahead might enter. Example (for another tuple): (Search Product, Gift Shopper, Immediate Need) → "I need a birthday gift–-best-rated wireless earbuds under $100, today." Now generate a query for (Compare Prices, Bargain Hunter, Planned Purchase).
```

#### 3. Open Coding Practice (Travel Assistant)

Below is a multi-step agent trace. Perform open coding: write purely observational notes on each issue and identify the first (upstream) significant failure.

**User Query:**
Book a budget flight from NYC to Rome on July 15 and a hostel nearby.

**Trace Steps:**
1. LLM → FlightSearch API
   ```
   FlightSearch(origin="NYC",
                destination="Rome",
                date="2025-07-15",
                class="economy",
                maxPrice=100)
   ```

2. API → LLM
   ```
   [] // no matching economy flights under $100
   ```

3. LLM → FlightSearch API
   ```
   FlightSearch(origin="NYC",
                destination="Rome",
                date="2025-07-15",
                class="business")
   ```

4. API → LLM
   ```
   [{flight:"BA100",class:"business",price:350},
    {flight:"UA200",class:"business",price:400}]
   ```

5. LLM → HotelSearch API
   ```
   HotelSearch(location="Trastevere",
               date="2025-07-15",
               maxPrice=80)
   ```

6. API → LLM
   ```
   ["Hostel A – Trastevere, $75/night",
    "Hostel B – Trastevere, $65/night"]
   ```

7. LLM → User
   ```
   Here are business-class flights and hostels in Trastevere...
   ```

**Solution 3.3**
- "Second flight search call drops the budget filter."
- "All flights returned are business class at $350+."
- "Hotel suggestions are in Trastevere, not near the Colosseum."

First significant failure: Step 3's FlightSearch call no longer enforces the user's budget or economy preference.

#### 4. Open Coding Practice (E-Commerce Chatbot)

Perform open coding on this trace:

**User Query:**
Find noise-cancelling headphones under $200 with at least 20h battery life.

**Trace Steps:**
1. LLM → ProductSearch API
   ```
   ProductSearch(category="headphones",
                 filters={price<=200})
   ```

2. API → LLM
   ```
   [{id:123,name:"Model X",price:250,battery:22}]
   ```

3. LLM → User
   ```
   "Model X: $250, 22h battery life."
   ```

**Solution 3.4**
- "Search results include a $250 model despite price<=200."
- "Battery-life filter was never applied."
- "Final suggestion ignores budget constraint."

First significant failure: Step 1's ProductSearch call omitted the battery-life filter, leading to out-of-budget results.

#### 5. Axial Coding Practice (Cross-Domain)

You have collected these raw annotations:
- "Omitted budget filter in flight search."
- "Returned business class instead of economy."
- "Suggested hostel in wrong area."
- "Missed battery-life constraint."
- "Recommended out-of-stock item."
- "Used casual tone for a business inquiry."
- "Scheduled hotel check-in on an unavailable date."
- "Provided inaccurate product specs."
- "Ignored shipping urgency."
- "Generated flight date different from request."

Cluster these into 3–4 structured, binary failure modes. For each, give a title and one-line definition.

**Solution 3.5**
- **Constraint Violation (Search):** Fails to apply user-specified filters (price, battery, availability) in retrieval steps.
- **Action/Timing Conflict:** Proposes actions or dates that violate known constraints (availability, dates).
- **Persona/Tone Mismatch:** Uses an inappropriate style or tone for the user's context.
- **Factual Inaccuracy:** Invents or misreports data (features, specs, locations) not supported by sources.

#### 6. Failure Mode Instance Augmentation

Suppose a particular failure mode—e.g. "Location Ambiguity"—appears very infrequently in your collected traces. Describe how you would generate more queries likely to trigger that failure and then run them through your pipeline to collect additional instances. For one domain (travel or e-commerce):

(a) Write a prompt template that generates queries targeting that failure mode.
(b) Provide one example prompt and the synthetic query it produces.

**Solution 3.6**

Strategy: Use an LLM prompt to create user queries containing ambiguous place names, so that running them through the travel assistant yields mislocalized results.

(a) Prompt template (Travel, Location Ambiguity):
```
Generate 15 user queries that mention a city name with multiple possible locations (e.g. "Springfield," "Paris," "Bristol") without specifying state or country. The goal is to trigger the assistant's wrong-city interpretation. Output one query per line.
```

(b) Example:
```
Find me a flight from Springfield to Chicago on June 20.
```

When this query is run through the pipeline, it should produce a trace where the assistant uses the wrong "Springfield" (e.g. Springfield, MO instead of MA), giving another instance of the Location Ambiguity failure.
