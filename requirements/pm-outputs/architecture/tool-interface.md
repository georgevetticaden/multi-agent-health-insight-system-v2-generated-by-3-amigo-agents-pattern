# Tool Interface Documentation: Multi-Agent Health Insight System

## Overview

The Multi-Agent Health Insight System uses pre-built tools that abstract all data storage and querying capabilities. These tools are already implemented in the `backend/tools/` directory and provide a standardized interface for AI agents to interact with health data without needing to know implementation details.

**CRITICAL**: These tools are PROVIDED and should NOT be reimplemented. They handle all data persistence, security, and query optimization internally.

## Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                   AI Agents                         │
│  (CMO, Specialists, Visualization)                  │
└────────────────────┬───────────────────────────────┘
                     │ Uses
┌────────────────────┴───────────────────────────────┐
│                Tool Registry                        │
│  Unified interface for all tool access              │
└────────────────────┬───────────────────────────────┘
                     │ Delegates to
┌────────────────────┴───────────────────────────────┐
│              Pre-built Tools                        │
│  • execute_health_query_v2                         │
│  • snowflake_import_analyze_health_records_v2      │
└────────────────────┬───────────────────────────────┘
                     │ Accesses
┌────────────────────┴───────────────────────────────┐
│           Data Layer (Abstracted)                   │
│  Snowflake, Cortex Analyst, etc.                   │
└─────────────────────────────────────────────────────┘
```

## Available Tools

### 1. Health Query Executor Tool

**Tool Name**: `execute_health_query_v2`

**Purpose**: Execute natural language queries about health data using advanced NLP capabilities.

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "query": {
      "type": "string",
      "description": "Natural language query about health data",
      "minLength": 3,
      "maxLength": 500
    },
    "options": {
      "type": "object",
      "properties": {
        "include_raw_data": {
          "type": "boolean",
          "default": false
        },
        "max_results": {
          "type": "integer",
          "default": 100,
          "minimum": 1,
          "maximum": 1000
        }
      }
    }
  },
  "required": ["query"]
}
```

**Query Examples by Complexity**:

**Simple Queries** (Single data point retrieval):
- "What's my latest cholesterol level?"
- "Show my current medications"
- "What's my blood pressure today?"

**Standard Queries** (Trend analysis within single domain):
- "How has my cholesterol changed over the past year?"
- "Show my HbA1c trend for the last 6 months"
- "Compare my blood pressure before and after medication"

**Complex Queries** (Multi-domain correlation):
- "How do my medications correlate with my lab results?"
- "Analyze my cardiovascular risk factors"
- "Show the relationship between my weight and blood pressure"

**Return Schema**:
```json
{
  "type": "object",
  "properties": {
    "query": {
      "type": "string",
      "description": "Original query text"
    },
    "query_successful": {
      "type": "boolean"
    },
    "result": {
      "type": "object",
      "properties": {
        "data": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "date": {"type": "string", "format": "date"},
              "metric_name": {"type": "string"},
              "value": {"type": "number"},
              "unit": {"type": "string"},
              "reference_range": {"type": "string"},
              "status": {
                "type": "string",
                "enum": ["normal", "borderline", "abnormal", "critical"]
              }
            }
          }
        },
        "summary": {
          "type": "string",
          "description": "Natural language summary of results"
        },
        "statistics": {
          "type": "object",
          "properties": {
            "mean": {"type": "number"},
            "min": {"type": "number"},
            "max": {"type": "number"},
            "trend": {
              "type": "string",
              "enum": ["increasing", "decreasing", "stable", "variable"]
            }
          }
        },
        "visualization_hints": {
          "type": "object",
          "properties": {
            "chart_type": {
              "type": "string",
              "enum": ["line", "bar", "scatter", "area", "combo"]
            },
            "x_axis": {"type": "string"},
            "y_axis": {"type": "string"},
            "title": {"type": "string"},
            "grouping": {"type": "string"}
          }
        }
      }
    },
    "metadata": {
      "type": "object",
      "properties": {
        "query_confidence": {
          "type": "number",
          "minimum": 0,
          "maximum": 1
        },
        "data_sources": {
          "type": "array",
          "items": {"type": "string"}
        },
        "record_count": {"type": "integer"},
        "execution_time": {"type": "number"}
      }
    }
  }
}
```

### 2. Health Data Import Tool

**Tool Name**: `snowflake_import_analyze_health_records_v2`

**Purpose**: Import and analyze health data from various sources.

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "file_directory": {
      "type": "string",
      "description": "Directory path containing health data files"
    },
    "import_options": {
      "type": "object",
      "properties": {
        "file_patterns": {
          "type": "array",
          "items": {"type": "string"},
          "default": ["*.json", "*.csv"]
        },
        "validation_level": {
          "type": "string",
          "enum": ["strict", "moderate", "lenient"],
          "default": "moderate"
        },
        "duplicate_handling": {
          "type": "string",
          "enum": ["skip", "update", "version"],
          "default": "skip"
        }
      }
    }
  },
  "required": ["file_directory"]
}
```

**Expected File Formats**:
- `lab_results_YYYY-MM-DD.json`
- `medications_current.json`
- `vitals_YYYY-MM.json`
- `clinical_data_consolidated.json`

**Return Schema**:
```json
{
  "type": "object",
  "properties": {
    "success": {"type": "boolean"},
    "import_id": {"type": "string", "format": "uuid"},
    "summary": {
      "type": "object",
      "properties": {
        "total_files_processed": {"type": "integer"},
        "total_records_imported": {"type": "integer"},
        "records_by_category": {
          "type": "object",
          "additionalProperties": {"type": "integer"}
        },
        "validation_errors": {"type": "integer"},
        "warnings": {
          "type": "array",
          "items": {"type": "string"}
        }
      }
    },
    "data_quality": {
      "type": "object",
      "properties": {
        "completeness_score": {"type": "number"},
        "consistency_score": {"type": "number"},
        "timeliness_score": {"type": "number"}
      }
    }
  }
}
```

## Tool Registry Interface

The `ToolRegistry` class provides a unified interface for all tool operations:

```python
from typing import List, Dict, Any, Optional
from tools.base import ToolDefinition, ToolResult

class ToolRegistry:
    """Central registry for all available tools."""
    
    def __init__(self):
        """Initialize with all available tools."""
        self._tools = self._load_tools()
    
    def get_tool_definitions(self) -> List[ToolDefinition]:
        """
        Returns tool definitions in Anthropic's format.
        
        Returns:
            List of tool definitions for AI agent use.
        """
    
    async def execute_tool(
        self, 
        tool_name: str, 
        tool_input: Dict[str, Any],
        timeout: Optional[float] = 30.0
    ) -> ToolResult:
        """
        Executes a tool by name with given input.
        
        Args:
            tool_name: Name of the tool to execute
            tool_input: Input parameters for the tool
            timeout: Maximum execution time in seconds
            
        Returns:
            ToolResult with success status and data
            
        Raises:
            ToolNotFoundError: If tool doesn't exist
            ToolExecutionError: If tool fails to execute
        """
    
    def get_tool_description(self, tool_name: str) -> str:
        """
        Returns detailed description for a specific tool.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            Detailed description including usage examples
        """
    
    def validate_tool_input(
        self, 
        tool_name: str, 
        tool_input: Dict[str, Any]
    ) -> List[str]:
        """
        Validates input against tool schema.
        
        Args:
            tool_name: Name of the tool
            tool_input: Input to validate
            
        Returns:
            List of validation errors (empty if valid)
        """
```

## Integration Patterns

### 1. Direct Tool Usage in Agents

```python
from anthropic import Anthropic
from tools.tool_registry import ToolRegistry

class HealthAgent:
    def __init__(self):
        self.client = Anthropic()
        self.tools = ToolRegistry()
    
    async def analyze_health_query(self, query: str):
        # Direct tool execution
        result = await self.tools.execute_tool(
            "execute_health_query_v2",
            {"query": query}
        )
        
        if result.success:
            return self._process_health_data(result.data)
        else:
            return self._handle_error(result.error)
```

### 2. Tool Usage with Anthropic's Native Tool Calling

```python
async def analyze_with_tools(self, user_query: str):
    # Get tool definitions in Anthropic format
    tools = self.tools.get_tool_definitions()
    
    # Let Claude decide which tools to use
    response = await self.client.messages.create(
        model="claude-3-sonnet-20240229",
        messages=[{
            "role": "user",
            "content": user_query
        }],
        tools=tools,
        max_tokens=4000
    )
    
    # Process tool calls in response
    for tool_call in response.tool_calls:
        result = await self.tools.execute_tool(
            tool_call.name,
            tool_call.input
        )
        # Handle result...
```

### 3. Specialist-Specific Tool Usage

```python
# Cardiology Specialist
async def analyze_cardiovascular_data(self, task: SpecialistTask):
    # Query for cardiovascular-specific data
    cardio_result = await self.tools.execute_tool(
        "execute_health_query_v2",
        {
            "query": "Get all cardiovascular metrics including cholesterol, blood pressure, and heart rate",
            "options": {
                "include_raw_data": True,
                "max_results": 500
            }
        }
    )
    
    # Additional targeted queries
    medication_result = await self.tools.execute_tool(
        "execute_health_query_v2",
        {"query": "List all cardiovascular medications with adherence data"}
    )
    
    return self._synthesize_cardio_insights(cardio_result, medication_result)
```

### 4. Error Handling Pattern

```python
async def safe_tool_execution(self, tool_name: str, tool_input: dict):
    try:
        # Validate input first
        errors = self.tools.validate_tool_input(tool_name, tool_input)
        if errors:
            return {"success": False, "errors": errors}
        
        # Execute with timeout
        result = await self.tools.execute_tool(
            tool_name, 
            tool_input,
            timeout=30.0
        )
        
        return result
        
    except ToolNotFoundError:
        return {"success": False, "error": "Tool not available"}
    except ToolExecutionError as e:
        return {"success": False, "error": str(e), "partial_data": e.partial_data}
    except asyncio.TimeoutError:
        return {"success": False, "error": "Tool execution timed out"}
```

## Best Practices

### 1. Query Construction

**DO:**
- Use specific medical terminology
- Include time ranges for trends
- Specify units when asking for values
- Use patient-friendly language alternatives

**DON'T:**
- Use ambiguous terms like "recent" without context
- Combine too many concepts in one query
- Assume data availability

**Examples:**
```python
# Good
"Show my LDL cholesterol trend over the past 2 years"
"What medications am I taking for hypertension?"

# Bad
"Show all my data"
"What's wrong with me?"
```

### 2. Result Processing

Always check for:
- Query success status
- Data completeness
- Confidence scores
- Visualization hints

```python
if result.query_successful:
    data = result.result.data
    if len(data) > 0:
        # Process data
        if result.metadata.query_confidence > 0.8:
            # High confidence processing
        else:
            # Include uncertainty in response
```

### 3. Performance Optimization

- Batch related queries when possible
- Cache frequently accessed data in agent memory
- Use query options to limit data size
- Implement progressive data loading

### 4. Security Considerations

- Never log full tool responses (may contain PHI)
- Sanitize error messages before displaying
- Use audit logging for compliance
- Implement rate limiting per session

## Tool Extension Points

While tools are pre-built, the system supports:

### 1. New Tool Registration
```python
# Future enhancement example
tool_registry.register_tool(
    name="analyze_genetic_data",
    definition=GeneticAnalysisTool(),
    category="advanced_diagnostics"
)
```

### 2. Tool Composition
```python
# Combining multiple tools
async def complex_analysis(query):
    # First get the data
    data = await tools.execute_tool("execute_health_query_v2", {...})
    
    # Then get predictions
    predictions = await tools.execute_tool("predict_health_trends", {
        "historical_data": data.result
    })
    
    return combine_results(data, predictions)
```

### 3. Custom Tool Wrappers
```python
class SpecialistToolWrapper:
    """Wraps tools with specialist-specific logic."""
    
    def __init__(self, tool_registry, specialty):
        self.tools = tool_registry
        self.specialty = specialty
    
    async def query_specialty_data(self, condition):
        # Add specialty context to queries
        query = f"For {self.specialty} analysis: {condition}"
        return await self.tools.execute_tool(
            "execute_health_query_v2",
            {"query": query}
        )
```

## Troubleshooting

### Common Issues

1. **Tool Not Found**
   - Ensure tools are imported from `backend/tools/`
   - Check tool name spelling
   - Verify ToolRegistry initialization

2. **Timeout Errors**
   - Increase timeout for complex queries
   - Break down complex queries
   - Check data volume

3. **Low Confidence Results**
   - Refine query specificity
   - Check data availability
   - Use alternative phrasings

4. **Validation Errors**
   - Check input schema requirements
   - Ensure required fields present
   - Validate data types

## Summary

The tool interface provides a powerful abstraction layer that:
- Hides data complexity from agents
- Ensures consistent data access patterns
- Handles security and compliance internally
- Enables natural language data queries
- Supports future extensibility

Remember: **NEVER reimplement these tools**. They are provided, tested, and optimized for the health domain.