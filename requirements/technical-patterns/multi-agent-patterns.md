# Multi-Agent System Patterns

## Overview
This document describes reusable patterns for building multi-agent systems based on Anthropic's research: ["How we built our multi-agent research system"](https://www.anthropic.com/engineering/built-multi-agent-research-system).

## Core Patterns

### 1. Orchestrator-Worker Pattern

**Purpose**: Coordinate multiple specialized agents to handle complex requests.

**When to Use**:
- Request requires multiple types of expertise
- Subtasks can be parallelized
- Need to synthesize multiple perspectives
- Complexity exceeds single agent capabilities

**Implementation**:
```python
class Orchestrator:
    async def process_request(self, request):
        # 1. Analyze request complexity
        complexity = self.assess_complexity(request)
        
        # 2. Decompose into specialist tasks
        tasks = self.create_tasks(request, complexity)
        
        # 3. Execute specialists
        if self.can_parallelize(tasks):
            results = await self.execute_parallel(tasks)
        else:
            results = await self.execute_sequential(tasks)
        
        # 4. Synthesize results
        return self.synthesize(results)
```

**Key Principles**:
- Orchestrator understands the domain but doesn't do deep analysis
- Workers are specialists with focused expertise
- Clear task boundaries prevent overlap
- Synthesis combines insights intelligently

### 2. Specialist Agent Pattern

**Purpose**: Create agents with deep, focused expertise in specific areas.

**IMPORTANT**: Use ONE SpecialistAgent class with different prompts, NOT multiple classes.

**Implementation**:
```python
# Define specialties as enum
class Specialty(Enum):
    CARDIOLOGY = "cardiology"
    DATA_ANALYSIS = "data_analysis"
    # ... other specialties

# Single agent class handles all specialties
class SpecialistAgent:
    def __init__(self, specialty, tools, system_prompt):
        self.specialty = specialty
        self.tools = tools  # Domain-specific tools
        self.system_prompt = system_prompt  # Expertise definition
    
    async def analyze(self, task, context):
        # Focused analysis within specialty
        # Uses specialized tools
        # Returns structured results
```

**Best Practices**:
- Each specialist has a clear, non-overlapping domain
- Specialists receive only relevant context
- Tools are appropriate to the specialty
- Results follow consistent structure

### 3. Progressive Disclosure Pattern

**Purpose**: Show analysis progress in real-time to maintain user engagement.

**Implementation**:
```python
async def stream_progress():
    yield {"type": "orchestrator_thinking", "message": "Analyzing request..."}
    yield {"type": "specialist_activated", "specialist": "name", "task": "description"}
    yield {"type": "specialist_progress", "specialist": "name", "progress": 50}
    yield {"type": "specialist_complete", "specialist": "name", "summary": "findings"}
    yield {"type": "synthesis_started", "message": "Combining insights..."}
    yield {"type": "complete", "result": final_result}
```

**UI Considerations**:
- Show which specialists are working
- Display progress for long-running tasks
- Reveal insights as they're discovered
- Maintain visual hierarchy

### 4. Parallel Execution Pattern

**Purpose**: Execute independent specialist tasks simultaneously for better performance.

**Decision Criteria**:
```python
def can_parallelize(tasks):
    # Check if tasks have dependencies
    # Consider resource constraints
    # Evaluate benefit vs complexity
    
    return all([
        no_dependencies_between(tasks),
        resources_available(),
        parallel_benefit_exceeds_overhead(tasks)
    ])
```

**Implementation Strategies**:
- Use asyncio for Python implementations
- Implement proper error isolation
- Set reasonable timeouts
- Handle partial failures gracefully

### 5. Context Management Pattern

**Purpose**: Provide each agent with focused, relevant context without overwhelming.

**Principles**:
```python
def prepare_specialist_context(task, full_context):
    return {
        "task": task.description,
        "relevant_data": filter_by_domain(full_context, task.domain),
        "constraints": task.constraints,
        "expected_output": task.output_schema
    }
```

**Guidelines**:
- Don't send entire conversation history
- Filter data by relevance
- Include only necessary background
- Maintain context boundaries

### 6. Result Synthesis Pattern

**Purpose**: Combine multiple specialist outputs into coherent, actionable insights.

**Approach**:
```python
def synthesize_results(specialist_results):
    # 1. Identify common themes
    themes = extract_common_themes(specialist_results)
    
    # 2. Resolve conflicts
    resolution = resolve_conflicts(specialist_results)
    
    # 3. Prioritize insights
    priorities = rank_by_importance(specialist_results)
    
    # 4. Create narrative
    return create_coherent_narrative(themes, resolution, priorities)
```

**Key Techniques**:
- Look for convergent insights
- Handle conflicting opinions explicitly
- Maintain specialist attribution
- Create actionable recommendations

### 7. Error Resilience Pattern

**Purpose**: Handle failures gracefully without breaking the entire system.

**Strategies**:
```python
async def execute_with_resilience(specialist, task):
    try:
        return await specialist.analyze(task)
    except SpecialistTimeout:
        return {"status": "timeout", "partial_result": specialist.partial_result}
    except SpecialistError as e:
        return {"status": "error", "fallback": use_fallback_approach(task)}
```

**Principles**:
- Specialist failures shouldn't cascade
- Provide partial results when possible
- Use fallback strategies
- Log failures for improvement

## Anti-Patterns to Avoid

### 1. Mega-Orchestrator
❌ Orchestrator tries to do analysis itself
✅ Orchestrator only coordinates

### 2. Overlapping Specialists
❌ Multiple specialists cover same domain
✅ Clear, distinct specialist boundaries

### 3. Context Flooding
❌ Sending all data to every specialist
✅ Filtered, relevant context only

### 4. Serial Processing
❌ Always processing specialists sequentially
✅ Parallel when independent

### 5. Silent Failures
❌ Hiding specialist errors
✅ Graceful degradation with transparency

## Performance Considerations

### Token Usage
- Multi-agent systems use more tokens (10-20x)
- Optimize context per specialist
- Cache common computations
- Monitor token usage per request type

### Latency
- Parallel execution reduces wall time
- Streaming updates improve perceived performance
- Set aggressive timeouts for specialists
- Implement request prioritization

### Scaling
- Specialists can run on different instances
- Orchestrator becomes the bottleneck
- Consider multiple orchestrator instances
- Implement proper load balancing

## Conclusion

These patterns provide a foundation for building robust multi-agent systems. The key is to:
1. Start with clear agent boundaries
2. Implement proper orchestration
3. Handle failures gracefully
4. Optimize for user experience
5. Monitor and iterate

Remember: The goal is to leverage specialized expertise while maintaining system coherence and user trust.