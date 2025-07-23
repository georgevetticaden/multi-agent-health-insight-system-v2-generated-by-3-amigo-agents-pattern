"""
Mock CMO Agent for Trace-Based Evaluation

This module provides a mock implementation of the CMOAgent that replays
data extracted from execution traces instead of making actual API calls.

The MockCMOAgent implements the same interface as the real CMOAgent but
returns pre-extracted data, allowing the full evaluation framework to be
used for trace-based evaluation without code duplication.
"""

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

# Import the types we need to match CMOAgent interface
from services.agents.models import QueryComplexity, MedicalSpecialty
from services.agents.cmo.cmo_agent import SpecialistTask

logger = logging.getLogger(__name__)


class MockCMOAgent:
    """
    Mock CMOAgent that replays trace data for evaluation.
    
    This class implements the same interface as CMOAgent but returns
    pre-extracted data from traces instead of making actual API calls.
    
    Attributes:
        trace_data: Dictionary containing extracted trace data including:
            - complexity: QueryComplexity enum
            - approach: Analytical approach text
            - initial_data: Initial data gathering results
            - specialist_tasks: List of specialist tasks
    """
    
    def __init__(self, trace_data: Dict[str, Any]):
        """
        Initialize the mock agent with extracted trace data.
        
        Args:
            trace_data: Dictionary containing:
                - complexity: QueryComplexity enum
                - approach: str - The analytical approach
                - initial_data: Dict - Initial data gathering results
                - specialist_tasks: List[MockSpecialistTask] - Tasks to convert
                
        Raises:
            ValueError: If required fields are missing
        """
        # Validate required fields
        required_fields = ['complexity', 'approach', 'initial_data', 'specialist_tasks']
        missing_fields = [field for field in required_fields if field not in trace_data]
        if missing_fields:
            raise ValueError(f"Missing required fields in trace_data: {missing_fields}")
        
        self.trace_data = trace_data
        logger.info("="*60)
        logger.info("MockCMOAgent.__init__: Initialized with trace data")
        logger.info(f"  - Complexity: {trace_data.get('complexity')} (type: {type(trace_data.get('complexity')).__name__})")
        logger.info(f"  - Approach length: {len(trace_data.get('approach', ''))} characters")
        logger.info(f"  - Initial data keys: {list(trace_data.get('initial_data', {}).keys())}")
        logger.info(f"  - Specialist tasks: {len(trace_data.get('specialist_tasks', []))} tasks")
        
        # Log specialists if available
        if trace_data.get('specialist_tasks'):
            specialists = [task.specialist.value for task in trace_data['specialist_tasks']]
            logger.info(f"  - Specialists in tasks: {specialists}")
        logger.info("="*60)
    
    async def analyze_query_with_tools(self, query: str) -> tuple[QueryComplexity, str, Dict[str, Any]]:
        """
        Mock implementation of query analysis.
        
        Returns pre-extracted data from the trace instead of calling API.
        
        Args:
            query: The health query (ignored - we use trace data)
            
        Returns:
            Tuple of (complexity, approach, initial_data) from trace
        """
        logger.info("="*60)
        logger.info("MockCMOAgent.analyze_query_with_tools() called")
        logger.info(f"Input query: {query[:100]}..." if len(query) > 100 else f"Input query: {query}")
        logger.info("Returning pre-extracted data from trace:")
        
        complexity = self.trace_data.get('complexity', QueryComplexity.SIMPLE)
        approach = self.trace_data.get('approach', '')
        initial_data = self.trace_data.get('initial_data', {})
        
        # Log complexity details
        logger.info(f"1. COMPLEXITY: {complexity.value}")
        logger.info(f"   - Type: {type(complexity).__name__}")
        logger.info(f"   - Enum value: {complexity.name}")
        
        # Log approach details
        logger.info(f"2. APPROACH:")
        logger.info(f"   - Length: {len(approach)} characters")
        logger.info(f"   - First 200 chars: {approach[:200]}..." if len(approach) > 200 else f"   - Full text: {approach}")
        
        # Log initial data details
        logger.info(f"3. INITIAL DATA:")
        logger.info(f"   - Tool calls made: {initial_data.get('tool_calls_made', 0)}")
        logger.info(f"   - Tool calls list length: {len(initial_data.get('tool_calls', []))}")
        logger.info(f"   - Available keys: {list(initial_data.keys())}")
        
        if initial_data.get('tool_calls'):
            logger.info("   - Tool call details:")
            for i, tool_call in enumerate(initial_data['tool_calls'][:3]):  # Show first 3
                logger.info(f"     Tool {i+1}: {tool_call.get('tool_name', 'unknown')} - Success: {tool_call.get('success', False)}")
        
        logger.info("="*60)
        
        return complexity, approach, initial_data
    
    async def create_specialist_tasks(
        self,
        query: str,
        complexity: QueryComplexity,
        approach: str,
        initial_data: Dict[str, Any]
    ) -> List[SpecialistTask]:
        """
        Mock implementation of specialist task creation.
        
        Converts MockSpecialistTask objects from trace to real SpecialistTask objects.
        
        Args:
            query: The health query (ignored)
            complexity: Query complexity (ignored)
            approach: Analytical approach (ignored)
            initial_data: Initial data (ignored)
            
        Returns:
            List of SpecialistTask objects converted from trace data
        """
        logger.info("="*60)
        logger.info("MockCMOAgent.create_specialist_tasks() called")
        logger.info("Input parameters (all ignored - using trace data):")
        logger.info(f"  - Query: {query[:50]}..." if len(query) > 50 else f"  - Query: {query}")
        logger.info(f"  - Complexity: {complexity.value}")
        logger.info(f"  - Approach length: {len(approach)} chars")
        logger.info(f"  - Initial data keys: {list(initial_data.keys())}")
        logger.info("Converting pre-extracted specialist tasks from trace:")
        
        mock_tasks = self.trace_data.get('specialist_tasks', [])
        logger.info(f"Number of mock tasks to convert: {len(mock_tasks)}")
        
        specialist_tasks = []
        
        for i, mock_task in enumerate(mock_tasks):
            logger.info(f"\nTask {i+1}:")
            logger.info(f"  - Specialist: {mock_task.specialist.value} ({type(mock_task.specialist).__name__})")
            logger.info(f"  - Priority: {mock_task.priority}")
            logger.info(f"  - Max tool calls: {mock_task.max_tool_calls}")
            logger.info(f"  - Objective: {mock_task.objective[:100]}..." if len(mock_task.objective) > 100 else f"  - Objective: {mock_task.objective}")
            logger.info(f"  - Context length: {len(mock_task.context)} chars")
            logger.info(f"  - Expected output length: {len(mock_task.expected_output)} chars")
            
            # Convert MockSpecialistTask to real SpecialistTask
            task = SpecialistTask(
                specialist=mock_task.specialist,  # Already a MedicalSpecialty enum
                objective=mock_task.objective,
                context=mock_task.context,
                expected_output=mock_task.expected_output,
                priority=mock_task.priority,
                max_tool_calls=mock_task.max_tool_calls
            )
            specialist_tasks.append(task)
            logger.info(f"  ✓ Successfully converted to SpecialistTask")
        
        logger.info(f"\nSummary:")
        logger.info(f"  - Total tasks converted: {len(specialist_tasks)}")
        logger.info(f"  - Specialists involved: {[task.specialist.value for task in specialist_tasks]}")
        logger.info("="*60)
        
        return specialist_tasks
    
    @staticmethod
    def get_evaluation_metadata():
        """
        Return the evaluation metadata from the real CMOAgent.
        
        This ensures we use the same metadata for evaluation.
        """
        from services.agents.cmo.cmo_agent import CMOAgent
        return CMOAgent.get_evaluation_metadata()