"""
Tool registry for Anthropic function calling
"""
from typing import Dict, Any, List
from tools.health_data_importer import HealthDataImporter
from tools.health_query_executor import HealthQueryExecutor

class ToolRegistry:
    """Registry of tools available for Anthropic function calling"""
    
    def __init__(self):
        self.importer = HealthDataImporter()
        self.query_executor = HealthQueryExecutor()
        
    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """Get tool definitions in Anthropic format"""
        return [
            {
                "name": "snowflake_import_analyze_health_records_v2",
                "description": "Import health data from directory of JSON files into Snowflake and return comprehensive statistics",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "file_directory": {
                            "type": "string",
                            "description": "Directory path containing extracted JSON health data files"
                        }
                    },
                    "required": ["file_directory"]
                }
            },
            {
                "name": "execute_health_query_v2",
                "description": "Execute natural language health queries using Cortex Analyst",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Natural language query about health data"
                        }
                    },
                    "required": ["query"]
                }
            }
        ]
    
    async def execute_tool(self, tool_name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool by name with given input"""
        
        if tool_name == "snowflake_import_analyze_health_records_v2":
            return await self.importer.import_health_records(
                file_directory=tool_input["file_directory"]
            )
        
        elif tool_name == "execute_health_query_v2":
            return await self.query_executor.execute_health_query(
                query=tool_input["query"]
            )
        
        else:
            raise ValueError(f"Unknown tool: {tool_name}")
    
    def get_tool_description(self, tool_name: str) -> str:
        """Get detailed description for a specific tool"""
        
        descriptions = {
            "snowflake_import_analyze_health_records_v2": """
Import health data from extracted JSON files into Snowflake data warehouse.
This tool processes lab results, medications, vitals, and clinical data files,
creating proper database records and calculating comprehensive statistics
for dashboard visualization.

The tool expects JSON files with specific naming patterns:
- lab_results_*.json
- medications_*.json
- vitals_*.json
- clinical_data_consolidated.json

Returns detailed import statistics including:
- Total records imported by category
- Timeline coverage (years of data)
- Data quality metrics
- Key insights for visualization
            """,
            
            "execute_health_query_v2": """
Execute natural language queries about health data using Snowflake Cortex Analyst.
This tool translates questions like "What's my cholesterol trend?" into SQL,
executes the query, and returns formatted results with health-specific metrics.

Supports queries about:
- Lab results and trends
- Medication history and adherence
- Vital signs over time
- Clinical conditions
- Correlations between different health metrics

Returns query results with interpretation and visualization-ready data.
            """
        }
        
        return descriptions.get(tool_name, "No description available")