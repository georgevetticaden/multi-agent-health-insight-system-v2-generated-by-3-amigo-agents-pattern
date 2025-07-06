# Visualization Agent Pattern

## Overview

The Visualization Agent is a critical component that generates self-contained React components as code artifacts. This pattern ensures dynamic, data-driven visualizations that perfectly match the analysis results.

## Key Characteristics

1. **Self-Contained Components**: No external data props needed
2. **Embedded Data**: Data is hardcoded directly in the component
3. **Streamed as Code**: Delivered as ```javascript code blocks
4. **Post-Synthesis Timing**: Called AFTER analysis is complete

## Implementation Pattern

### Backend: Visualization Agent

```python
# services/agents/visualization/visualization_agent.py
class VisualizationAgent:
    def __init__(self, anthropic_client):
        self.client = anthropic_client
        self.prompts = VisualizationPrompts()
        
    async def stream_visualization(
        self, 
        query: str, 
        specialist_results: list,
        synthesis_text: str
    ) -> AsyncGenerator[dict, None]:
        # Extract key data points from synthesis
        key_data = self._extract_key_data_points(specialist_results, synthesis_text)
        
        # Generate prompt
        prompt = self.prompts.get_generation_prompt(
            query=query,
            synthesis_text=synthesis_text,
            key_data_points=key_data
        )
        
        # Stream the code
        async for chunk in self._stream_code(prompt):
            yield {"type": "text", "content": chunk}
```

### Prompts Structure

```
services/agents/visualization/prompts/
├── generation_base.txt      # Main template
├── instructions_general.txt # Component requirements
├── example_time_series.txt  # Time series example
├── example_correlation.txt  # Correlation example
└── example_abnormal.txt     # Abnormal values example
```

### Key Prompt Instructions

```text
# generation_base.txt
Create a self-contained React visualization component that directly answers this query.

Query: "{query}"

## Medical Analysis Summary:
{synthesis_summary}

## Key Data Points:
{key_data_points}

## CRITICAL INSTRUCTIONS:
1. Create a SELF-CONTAINED component with embedded data
2. Extract specific values mentioned in the analysis
3. Start with: const HealthVisualization = () => {
4. Embed data as: const rawData = [...]
5. DO NOT include imports or exports
6. Use Recharts components (already available)
7. Keep under 400 lines for reliable generation
```

### Frontend: CodeArtifact Component

```typescript
// components/CodeArtifact.tsx
import * as Recharts from 'recharts';
import * as Babel from '@babel/standalone';

const CodeArtifact = ({ code, isStreaming }) => {
  const renderedComponent = useMemo(() => {
    if (isStreaming) return null;
    
    try {
      // Transform JSX
      const transformed = Babel.transform(code, {
        presets: ['react']
      });
      
      // Make dependencies available
      window.Recharts = Recharts;
      window.React = React;
      
      // Execute code
      const Component = eval(transformed.code);
      return <Component />;
      
    } catch (error) {
      return <div>Error: {error.message}</div>;
    }
  }, [code, isStreaming]);
  
  return (
    <div>
      {isStreaming ? (
        <pre>{code}</pre>
      ) : (
        renderedComponent
      )}
    </div>
  );
};
```

## Integration Flow

1. **Orchestrator completes synthesis**
   ```python
   synthesis = await self.cmo_agent.synthesize(results)
   ```

2. **Check for data and trigger visualization**
   ```python
   if has_data:
       async for chunk in self.visualization_agent.stream_visualization(
           query, specialist_results, synthesis_text
       ):
           yield chunk
   ```

3. **Frontend detects code artifact**
   ```typescript
   // In message processing
   if (message.content.includes('```javascript')) {
     // Extract code and render with CodeArtifact
   }
   ```

## Critical Success Factors

### 1. Data Extraction
The visualization agent MUST extract exact values from the synthesis:
```python
def _extract_key_data_points(self, results, synthesis):
    # Parse synthesis for specific numbers
    # Example: "cholesterol increased from 117 to 161"
    # Extract: [{date: "2024-01", value: 117}, {date: "2025-01", value: 161}]
```

### 2. Component Structure
Generated components MUST follow this pattern:
```javascript
const HealthVisualization = () => {
  // Embedded data
  const rawData = [
    { date: "2024-01-15", value: 117, metric: "Total Cholesterol" },
    { date: "2025-01-15", value: 161, metric: "Total Cholesterol" }
  ];
  
  // Component logic
  return (
    <div className="p-6">
      <ResponsiveContainer width="100%" height={400}>
        <LineChart data={rawData}>
          {/* Chart configuration */}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};
```

### 3. Prompt Engineering
The prompts must:
- Include working examples
- Specify exact component structure
- Emphasize self-contained nature
- Provide clear data embedding instructions

## Common Patterns

### Time Series Visualization
```javascript
const rawData = [
  { date: "2024-01", value: 120, unit: "mg/dL" },
  { date: "2024-02", value: 125, unit: "mg/dL" },
  // ... more data points
];
```

### Comparison Visualization
```javascript
const beforeAfter = [
  { period: "Before", value: 145, metric: "LDL Cholesterol" },
  { period: "After", value: 95, metric: "LDL Cholesterol" }
];
```

### Multi-Metric Dashboard
```javascript
const metrics = [
  { name: "Total Cholesterol", value: 185, normal: "< 200", status: "normal" },
  { name: "LDL", value: 110, normal: "< 100", status: "borderline" },
  { name: "HDL", value: 55, normal: "> 40", status: "normal" }
];
```

## Error Prevention

1. **No Imports**: Never include import statements
2. **Valid JSX**: Escape special characters properly
3. **Complete Components**: Ensure closing braces
4. **Data Validation**: Handle empty or missing data
5. **Responsive Design**: Use ResponsiveContainer

## Testing the Pattern

```python
# Test prompt generation
prompt = visualization_agent.prompts.get_generation_prompt(
    query="Show my cholesterol trend",
    synthesis_text="Cholesterol increased from 150 to 180",
    key_data_points={"cholesterol": [150, 180]}
)

# Verify component structure
assert "const HealthVisualization = () => {" in generated_code
assert "const rawData = [" in generated_code
assert "ResponsiveContainer" in generated_code
```

## Key Takeaway

The Visualization Agent is NOT optional for data analysis systems. It provides the critical link between numerical analysis and visual understanding, creating dynamic visualizations that exactly match the synthesized insights.