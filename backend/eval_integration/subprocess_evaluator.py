"""
Subprocess-based evaluator for running CLI evaluation framework.

This module runs the evaluation in a subprocess to avoid import path issues
when running from the backend directory.
"""

import json
import logging
import os
import subprocess
import sys
import tempfile
import threading
import queue
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


def parse_evaluation_event(line: str) -> Optional[Dict[str, Any]]:
    """
    Parse subprocess output line for key evaluation lifecycle events.
    
    Returns event dict with type, message, and metadata if line contains a key event.
    """
    # Skip empty lines
    if not line or not line.strip():
        return None
        
    # Key event patterns based on the evaluation lifecycle
    if "Loading trace from:" in line:
        return {"type": "trace_load", "message": "🔍 Loading execution trace"}
    
    elif "Extracting evaluation data from trace" in line:
        return {"type": "trace_extract", "message": "📊 Extracting evaluation data from trace"}
    
    elif "Test case created:" in line:
        return {"type": "test_case_ready", "message": "📋 Test case prepared"}
    
    elif "Running evaluation in subprocess" in line:
        return {"type": "subprocess_start", "message": "🚀 Starting evaluation subprocess"}
    
    elif "EVALUATION STAGE" in line:
        # Extract stage info
        if "Analyzing query" in line:
            return {"type": "dimension_start", "message": "📏 Evaluating Complexity Classification"}
        elif "Creating specialist tasks" in line:
            return {"type": "dimension_start", "message": "👥 Evaluating Specialty Selection"}
        elif "Evaluating dimensions" in line:
            return {"type": "dimension_evaluation", "message": "📊 Evaluating all dimensions"}
        elif "Analyzing failures" in line:
            return {"type": "diagnostic_start", "message": "🔍 LLM-as-Judge analyzing failures"}
        elif "Finalizing results" in line:
            return {"type": "finalizing", "message": "📊 Finalizing evaluation results"}
    
    # Dimension results
    elif "PASS" in line and ":" in line and any(dim in line for dim in ["complexity_classification", "specialty_selection", "analysis_quality", "tool_usage", "response_structure"]):
        # Parse: ✅ PASS analysis_quality: 0.850 (target: 0.80)
        parts = line.split(":")
        if len(parts) >= 2:
            dim_name = parts[0].split()[-1]
            score_part = parts[1].strip().split()[0]
            try:
                score = float(score_part)
                return {
                    "type": "dimension_result",
                    "message": f"✅ {dim_name}: {score:.3f}",
                    "dimension": dim_name,
                    "score": score,
                    "passed": True
                }
            except:
                pass
    
    elif "FAIL" in line and ":" in line and any(dim in line for dim in ["complexity_classification", "specialty_selection", "analysis_quality", "tool_usage", "response_structure"]):
        # Parse: ❌ FAIL complexity_classification: 0.000 (target: 0.90)
        parts = line.split(":")
        if len(parts) >= 2:
            dim_name = parts[0].split()[-1]
            score_part = parts[1].strip().split()[0]
            try:
                score = float(score_part)
                return {
                    "type": "dimension_result", 
                    "message": f"❌ {dim_name}: {score:.3f}",
                    "dimension": dim_name,
                    "score": score,
                    "passed": False
                }
            except:
                pass
    
    # LLM-as-Judge events
    elif "LLM Judge evaluating" in line or "LLM-as-Judge evaluating" in line:
        if "specialist rationale" in line:
            return {"type": "llm_judge_eval", "message": "🤖 LLM-as-Judge evaluating specialist rationale..."}
        elif "context awareness" in line:
            return {"type": "llm_judge_eval", "message": "🤖 LLM-as-Judge scoring context awareness..."}
        elif "comprehensive approach" in line:
            return {"type": "llm_judge_eval", "message": "🤖 LLM-as-Judge assessing comprehensive approach..."}
    
    elif "LLM Judge score:" in line or "LLM-as-Judge score:" in line:
        # Extract score
        try:
            score = float(line.split(":")[-1].strip())
            return {"type": "llm_judge_result", "message": f"✅ LLM-as-Judge score: {score:.3f}"}
        except:
            pass
    
    # Diagnostic events
    elif "LLM Judge failure analysis" in line or "diagnosing" in line:
        if "complexity" in line.lower():
            return {"type": "diagnostic", "message": "🔍 LLM-as-Judge diagnosing complexity failure..."}
        elif "specialty" in line.lower() or "specialist" in line.lower():
            return {"type": "diagnostic", "message": "🔍 LLM-as-Judge diagnosing specialty selection failure..."}
    
    elif "recommendations" in line and ("Generated" in line or "items" in line):
        # Extract count
        import re
        match = re.search(r'\d+', line)
        if match:
            count = match.group()
            return {"type": "diagnostic_complete", "message": f"💡 LLM-as-Judge generated {count} improvement recommendations"}
    
    # Final results
    elif "EVALUATION COMPLETE" in line:
        return {"type": "evaluation_start_complete", "message": "🏁 Evaluation stages complete"}
    
    elif "Weighted score:" in line:
        try:
            score = float(line.split(":")[-1].strip())
            return {"type": "overall_score", "message": f"📊 Evaluation complete: Overall Score {score:.3f}"}
        except:
            pass
    
    elif "Failed dimensions:" in line:
        try:
            count = int(line.split(":")[-1].strip())
            return {"type": "failed_dimensions", "count": count}
        except:
            pass
    
    elif "Evaluation complete!" in line:
        return {"type": "evaluation_complete", "message": "✅ Evaluation analysis finished"}
    
    return None


def run_evaluation_subprocess(
    test_case_data: Dict[str, Any], 
    trace_data: Dict[str, Any],
    anthropic_api_key: Optional[str] = None,
    event_callback: Optional[callable] = None
) -> Dict[str, Any]:
    """
    Run evaluation in a subprocess using the CLI evaluation framework.
    
    Args:
        test_case_data: Test case dict from QE Agent
        trace_data: Extracted trace data (complexity, approach, etc.)
        anthropic_api_key: API key for LLM judge evaluation
        event_callback: Callback for storing events (will be called in parent process)
        
    Returns:
        Evaluation results dictionary with events
    """
    logger.info("=== SUBPROCESS EVALUATOR START ===")
    
    # Collect events locally
    collected_events = []
    
    # Use the new subprocess evaluation script
    backend_dir = Path(__file__).parent.parent
    project_root = backend_dir.parent  # Define project_root
    eval_script = backend_dir / "eval_integration" / "run_subprocess_eval.py"
    
    if not eval_script.exists():
        logger.error(f"Evaluation script not found at {eval_script}")
        raise FileNotFoundError(f"Evaluation script not found: {eval_script}")
    
    # Prepare input data
    input_data = {
        "test_case": test_case_data,
        "trace_data": trace_data,
        "anthropic_api_key": anthropic_api_key
    }
    
    # Write input to temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(input_data, f)
        input_file = f.name
    
    try:
        # Run evaluation in subprocess with real-time streaming
        logger.info(f"Running evaluation script: {eval_script}")
        cmd = [sys.executable, str(eval_script), input_file]
        
        # Set environment variables for subprocess
        env = os.environ.copy()
        env['PYTHONUNBUFFERED'] = '1'  # Ensure unbuffered output
        
        # Start subprocess with Popen for real-time streaming
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,  # Line buffered
            universal_newlines=True,
            cwd=str(project_root),
            env=env
        )
        
        # Queues to collect output
        stdout_queue = queue.Queue()
        stderr_queue = queue.Queue()
        
        # Thread function to read output in real-time
        def read_output(pipe, output_queue, prefix):
            """Read output from pipe and log in real-time."""
            try:
                for line in iter(pipe.readline, ''):
                    if line:
                        line = line.rstrip('\n\r')
                        if line.strip():  # Only log non-empty lines
                            logger.info(f"{prefix}: {line}")
                            output_queue.put(line)
                            
                            # Parse and collect evaluation events from both STDOUT and STDERR
                            event = parse_evaluation_event(line)
                            if event:
                                # Add timestamp to event
                                event['timestamp'] = datetime.now().isoformat()
                                collected_events.append(event)
                                # Call the event callback in real-time
                                # This runs in the parent process thread, so it CAN modify parent process memory!
                                if event_callback:
                                    try:
                                        logger.info(f"Real-time event callback for: {event.get('type', 'unknown')}")
                                        event_callback(event)
                                    except Exception as e:
                                        logger.error(f"Error in event callback: {e}")
                pipe.close()
            except Exception as e:
                logger.error(f"Error reading {prefix}: {e}")
            finally:
                output_queue.put(None)  # Signal end of output
        
        # Start threads to read stdout and stderr
        logger.info("=== SUBPROCESS REAL-TIME OUTPUT START ===")
        stdout_thread = threading.Thread(
            target=read_output, 
            args=(process.stdout, stdout_queue, "SUBPROCESS")
        )
        stderr_thread = threading.Thread(
            target=read_output, 
            args=(process.stderr, stderr_queue, "SUBPROCESS-ERR")
        )
        
        stdout_thread.start()
        stderr_thread.start()
        
        # Wait for process to complete
        return_code = process.wait(timeout=300)  # 5 minute timeout
        
        # Wait for reading threads to complete
        stdout_thread.join(timeout=5)
        stderr_thread.join(timeout=5)
        
        logger.info("=== SUBPROCESS REAL-TIME OUTPUT END ===")
        
        # Collect all output for processing
        stdout_lines = []
        stderr_lines = []
        
        # Drain stdout queue
        while True:
            try:
                line = stdout_queue.get_nowait()
                if line is None:
                    break
                stdout_lines.append(line)
            except queue.Empty:
                break
        
        # Drain stderr queue
        while True:
            try:
                line = stderr_queue.get_nowait()
                if line is None:
                    break
                stderr_lines.append(line)
            except queue.Empty:
                break
        
        if return_code != 0:
            logger.error(f"Evaluation failed with code {return_code}")
            logger.error(f"STDERR: {chr(10).join(stderr_lines)}")
            raise RuntimeError(f"Evaluation failed with code {return_code}")
        
        # Find JSON output in stdout (should be the last line)
        json_output = None
        for line in reversed(stdout_lines):
            line = line.strip()
            if line.startswith('{') and line.endswith('}'):
                try:
                    # Validate it's valid JSON
                    json.loads(line)
                    json_output = line
                    break
                except json.JSONDecodeError:
                    continue
        
        if not json_output:
            logger.error("No valid JSON output found in subprocess stdout")
            logger.error(f"All stdout lines: {stdout_lines}")
            raise RuntimeError("No valid JSON output from evaluation subprocess")
        
        # Parse output
        output = json.loads(json_output)
        
        # Add collected events to the output
        output['collected_events'] = collected_events
        logger.info(f"Collected {len(collected_events)} events during evaluation")
        
        logger.info("=== SUBPROCESS EVALUATOR COMPLETE ===")
        return output
        
    finally:
        # Clean up temp file
        Path(input_file).unlink(missing_ok=True)


def create_evaluation_script() -> str:
    """Create the evaluation script that runs in subprocess."""
    return '''#!/usr/bin/env python3
"""
Trace-based evaluation script for subprocess execution.

This script is run in a subprocess to evaluate test cases using trace data.
It imports and uses the real CMOEvaluator from the evaluation framework.
"""

import asyncio
import json
import logging
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add evaluation framework to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import evaluation framework
from evaluation.agents.cmo.evaluator import CMOEvaluator, CMOEvaluationResult
from evaluation.cli.test_case_converter import CMOTestCase
from evaluation.agents.cmo.dimensions import DimensionResult
from services.agents.models import QueryComplexity, MedicalSpecialty
from services.agents.cmo.cmo_agent import SpecialistTask
from anthropic import Anthropic


class MockCMOAgentForEval:
    """Mock CMO Agent that replays trace data."""
    
    def __init__(self, trace_data):
        self.trace_data = trace_data
        # Convert string values back to enums
        self.trace_data['complexity'] = QueryComplexity(trace_data['complexity'])
        for task in self.trace_data['specialist_tasks']:
            task['specialist'] = MedicalSpecialty(task['specialist'])
        logger.info(f"MockCMOAgent initialized with trace data")
    
    async def analyze_query_with_tools(self, query):
        """Return pre-extracted analysis data."""
        complexity = self.trace_data['complexity']
        approach = self.trace_data['approach']
        initial_data = self.trace_data['initial_data']
        
        logger.info(f"Returning analysis: complexity={complexity.value}, approach_len={len(approach)}")
        return complexity, approach, initial_data
    
    async def create_specialist_tasks(self, query, complexity, approach, initial_data):
        """Return pre-extracted specialist tasks."""
        tasks = []
        for task_data in self.trace_data['specialist_tasks']:
            task = SpecialistTask(
                specialist=task_data['specialist'],
                objective=task_data['objective'],
                context=task_data['context'],
                expected_output=task_data['expected_output'],
                priority=task_data['priority'],
                max_tool_calls=task_data['max_tool_calls']
            )
            tasks.append(task)
        
        logger.info(f"Returning {len(tasks)} specialist tasks")
        return tasks
    
    @staticmethod
    def get_evaluation_metadata():
        """Get evaluation metadata from real CMOAgent."""
        from services.agents.cmo.cmo_agent import CMOAgent
        return CMOAgent.get_evaluation_metadata()


async def run_evaluation(input_file: str):
    """Run the evaluation using input from file."""
    logger.info(f"Loading input from {input_file}")
    
    with open(input_file, 'r') as f:
        data = json.load(f)
    
    test_case_data = data['test_case']
    trace_data = data['trace_data']
    api_key = data.get('anthropic_api_key')
    
    # Convert test case
    test_case = CMOTestCase(
        id=test_case_data.get('id', 'unknown'),
        query=test_case_data.get('query', ''),
        expected_complexity=test_case_data.get('expected_complexity', 'SIMPLE'),
        expected_specialties=set(test_case_data.get('expected_specialties', [])),
        key_data_points=test_case_data.get('key_data_points', []),
        notes=test_case_data.get('notes', '')
    )
    
    # Create mock agent
    mock_agent = MockCMOAgentForEval(trace_data)
    
    # Create evaluator
    anthropic_client = Anthropic(api_key=api_key) if api_key else None
    evaluator = CMOEvaluator(
        cmo_agent=mock_agent,
        anthropic_client=anthropic_client
    )
    
    # Run evaluation
    logger.info("Running evaluation...")
    result = await evaluator.evaluate_single_test_case(test_case)
    
    # Convert result to dict
    result_dict = {
        'test_case_id': result.test_case_id,
        'overall_score': result.weighted_score,
        'dimension_results': convert_dimension_results(result),
        'execution_time_ms': result.total_response_time_ms,
        'metadata': {
            'approach_text': result.approach_text,
            'test_case_category': result.key_data_points[0] if result.key_data_points else 'general',
            'initial_data_gathered': result.initial_data_gathered,
            'specialist_tasks': result.specialist_tasks,
            'failure_analyses': result.failure_analyses
        }
    }
    
    # Output as JSON
    print(json.dumps(result_dict))


def convert_dimension_results(result):
    """Convert CMOEvaluationResult dimensions to dict format."""
    dimensions = {}
    
    dimensions['complexity_classification'] = {
        'score': result.complexity_classification_score,
        'normalized_score': result.complexity_classification_score,
        'components': {},
        'details': {
            'expected': result.expected_complexity,
            'actual': result.actual_complexity,
            'correct': result.complexity_correct
        },
        'evaluation_method': 'deterministic'
    }
    
    dimensions['specialty_selection'] = {
        'score': result.specialty_selection_score,
        'normalized_score': result.specialty_selection_score,
        'components': result.specialty_component_breakdown,
        'details': {
            'expected_specialties': list(result.expected_specialties),
            'actual_specialties': list(result.actual_specialties),
            'precision': result.specialty_component_breakdown.get('specialist_precision', 0.0),
            'recall': result.specialty_component_breakdown.get('specialist_recall', 0.0),
            'f1_score': result.specialty_selection_score
        },
        'evaluation_method': 'hybrid'
    }
    
    dimensions['analysis_quality'] = {
        'score': result.analysis_quality_score,
        'normalized_score': result.analysis_quality_score,
        'components': result.analysis_quality_breakdown,
        'details': {
            'approach_length': len(result.approach_text) if result.approach_text else 0,
            'approach_text': result.approach_text[:500] if result.approach_text else ""
        },
        'evaluation_method': 'hybrid'
    }
    
    dimensions['tool_usage'] = {
        'score': result.tool_usage_score,
        'normalized_score': result.tool_usage_score,
        'components': result.tool_component_breakdown,
        'details': {
            'tool_calls_made': result.tool_calls_made,
            'successful_tool_calls': result.tool_component_breakdown.get('tool_success_count', result.tool_calls_made),
            'success_rate': result.tool_component_breakdown.get('tool_success_rate', 1.0)
        },
        'evaluation_method': 'deterministic'
    }
    
    dimensions['response_structure'] = {
        'score': result.response_structure_score,
        'normalized_score': result.response_structure_score,
        'components': result.response_component_breakdown,
        'details': {
            'response_valid': result.response_valid,
            'structure_errors': result.structure_errors
        },
        'evaluation_method': 'deterministic'
    }
    
    return dimensions


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: run_trace_evaluation.py <input_file>")
        sys.exit(1)
    
    asyncio.run(run_evaluation(sys.argv[1]))
'''