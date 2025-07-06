# Health Data Tool Interface Documentation

## Overview

The Multi-Agent Health Insight System comes with pre-built tools that abstract health data storage and querying capabilities. These tools are already implemented in the `backend/tools/` directory and provide a standardized interface for AI agents to interact with health data without needing to know implementation details.

## Available Tools

### 1. Health Data Import Tool

**Tool Name**: `snowflake_import_analyze_health_records_v2`

**Purpose**: Import health data from extracted JSON files into the data warehouse and return comprehensive statistics.

**Input Parameters**:
```json
{
  "file_directory": "string - Directory path containing extracted JSON health data files"
}
```

**Expected File Formats**:
- `lab_results_*.json` - Laboratory test results
- `medications_*.json` - Medication history and prescriptions
- `vitals_*.json` - Vital signs (blood pressure, heart rate, etc.)
- `clinical_data_consolidated.json` - Consolidated clinical information

**Return Value**:
```json
{
  "success": true,
  "message": "Successfully imported health data",
  "import_id": "unique-import-identifier",
  "total_records": 1234,
  "records_by_category": {
    "lab_results": 450,
    "medications": 234,
    "vitals": 550
  },
  "date_range": {
    "start": "2013-01-15",
    "end": "2025-06-30"
  },
  "data_quality": {
    "completeness": 95.2,
    "records_with_dates": 98.5
  },
  "key_insights": [
    "12 years of comprehensive health data",
    "Regular monitoring patterns detected",
    "Complete medication history available"
  ]
}
```

### 2. Health Query Executor Tool

**Tool Name**: `execute_health_query_v2`

**Purpose**: Execute natural language queries about health data using advanced NLP capabilities.

**Input Parameters**:
```json
{
  "query": "string - Natural language query about health data"
}
```

**Example Queries**:
- "What's my cholesterol trend over the past year?"
- "Show me all abnormal lab results from 2024"
- "How has my blood pressure changed since starting medication?"
- "What's my average HbA1c level?"
- "List all medications I've taken for diabetes"

**Return Value**:
```json
{
  "query": "original query text",
  "query_successful": true,
  "result": {
    "data": [
      {
        "date": "2024-06-15",
        "test_name": "Total Cholesterol",
        "value": 185,
        "unit": "mg/dL",
        "reference_range": "< 200",
        "status": "Normal"
      }
    ],
    "summary": "Your cholesterol has decreased by 15% over the past year",
    "visualization_hints": {
      "chart_type": "line",
      "x_axis": "date",
      "y_axis": "value",
      "title": "Cholesterol Trend"
    }
  },
  "metadata": {
    "query_confidence": 0.95,
    "data_sources": ["lab_results"],
    "record_count": 12
  }
}
```

## Tool Registry Interface

The `ToolRegistry` class provides a unified interface for tool management:

```python
class ToolRegistry:
    def get_tool_definitions() -> List[Dict[str, Any]]:
        """Returns tool definitions in Anthropic's format"""
    
    async def execute_tool(tool_name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Executes a tool by name with given input"""
    
    def get_tool_description(tool_name: str) -> str:
        """Returns detailed description for a specific tool"""
```

## Integration with AI Agents

### For CMO Agent
The Chief Medical Officer uses these tools for initial data assessment:
```python
# Query available health data
result = await tool_registry.execute_tool(
    "execute_health_query_v2",
    {"query": "Summarize all available health data categories"}
)
```

### For Specialist Agents
Each specialist can query domain-specific data:
```python
# Cardiology specialist querying heart-related data
result = await tool_registry.execute_tool(
    "execute_health_query_v2",
    {"query": "Show all cardiovascular metrics including cholesterol, blood pressure, and heart rate"}
)
```

### For Visualization Agent
The visualization agent uses query results to generate appropriate charts:
```python
# Get data for visualization
result = await tool_registry.execute_tool(
    "execute_health_query_v2",
    {"query": "Get monthly average blood pressure readings for the past year"}
)
# Use result["result"]["visualization_hints"] to generate appropriate chart
```

## Best Practices

1. **Query Specificity**: More specific queries return better results
   - ❌ "Show me my data"
   - ✅ "Show my cholesterol levels from the past 6 months"

2. **Date Ranges**: Include time periods for trend analysis
   - "...over the past year"
   - "...since January 2024"
   - "...between March and June 2024"

3. **Metric Names**: Use standard medical terminology
   - Cholesterol (Total, LDL, HDL)
   - HbA1c (not "blood sugar average")
   - Blood Pressure (Systolic/Diastolic)

4. **Error Handling**: Always check `success` or `query_successful` flags

## Data Schema (Abstracted)

While the tools handle data storage internally, they expect health data in these categories:

### Lab Results
- Test name, value, unit, reference range
- Collection date and time
- Normal/Abnormal flags

### Medications
- Drug name, dosage, frequency
- Start and end dates
- Prescribing physician
- Adherence information

### Vitals
- Blood pressure (systolic/diastolic)
- Heart rate
- Temperature
- Weight/BMI
- Respiratory rate

### Clinical Data
- Diagnoses with ICD codes
- Procedures
- Allergies
- Immunizations

## Security & Privacy

- All data operations are logged for audit trails
- Patient identifiers are handled securely
- No raw data is exposed outside the tool interface
- Tools implement appropriate access controls

## Extension Points

While these tools are pre-built, the system is designed for extensibility:
- New tool methods can be added to the registry
- Additional data categories can be supported
- Query capabilities can be enhanced with new patterns
- Visualization hints can be expanded for new chart types

## CRITICAL REMINDERS FOR IMPLEMENTATION

1. **These tools are PROVIDED** - They will exist in `backend/tools/` when you start
2. **DO NOT reimplement** - Simply import: `from tools.tool_registry import ToolRegistry`
3. **DO NOT create database connections** - Tools handle all data access
4. **DO NOT modify tool files** - They are pre-built and tested
5. **DO use them directly** - Pass tool definitions to Anthropic API calls

### Example Agent Implementation
```python
# This is how EVERY agent should use tools
from anthropic import Anthropic
from tools.tool_registry import ToolRegistry

class AnySpecialistAgent:
    def __init__(self):
        self.client = Anthropic()
        self.tools = ToolRegistry()  # Just instantiate
    
    async def analyze(self, query):
        response = await self.client.messages.create(
            model="claude-3-sonnet-20240229",
            messages=[{"role": "user", "content": query}],
            tools=self.tools.get_tool_definitions(),  # Pass definitions
            max_tokens=4000
        )
        # Handle tool calls in response
        return response
```