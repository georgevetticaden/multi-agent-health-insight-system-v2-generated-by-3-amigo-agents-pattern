#!/usr/bin/env python3
"""
Test script for unified evaluator and report generation.

This script helps verify that:
1. The CLI evaluator works with traces
2. Reports are generated correctly
3. All evaluation dimensions show proper scores
"""

import asyncio
import json
import logging
from pathlib import Path
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_unified_evaluator():
    """Test the unified evaluator with a sample trace."""
    
    # 1. Find a recent trace file
    trace_dir = Path("traces/2025-07-21")
    if not trace_dir.exists():
        trace_dir = Path("backend/traces/2025-07-21")
    
    trace_files = list(trace_dir.glob("*.json"))
    if not trace_files:
        logger.error(f"No trace files found in {trace_dir}")
        return
    
    # Use the most recent trace
    trace_file = sorted(trace_files, key=lambda x: x.stat().st_mtime)[-1]
    logger.info(f"Using trace file: {trace_file}")
    
    # 2. Load the trace
    with open(trace_file, 'r') as f:
        trace_data = json.load(f)
    
    trace_id = trace_data.get("trace_id", "unknown")
    query = "Unknown query"
    
    # Find the query in trace events
    for event in trace_data.get("events", []):
        if event.get("event_type") == "user_query":
            query = event.get("data", {}).get("query", "Unknown query")
            break
    
    logger.info(f"Trace ID: {trace_id}")
    logger.info(f"Query: {query[:100]}...")
    
    # 3. Create a test case
    test_case = {
        "id": f"test_{trace_id[:8]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "query": query,
        "expected_complexity": "STANDARD",  # You can analyze trace to determine this
        "expected_specialties": ["cardiology", "laboratory_medicine"],  # Example
        "key_data_points": ["blood pressure", "lab results"],
        "category": "unified_test",
        "notes": "Generated for testing unified evaluator",
        "trace_id": trace_id
    }
    
    logger.info(f"Created test case: {test_case['id']}")
    
    # 4. Run evaluation using the service
    from services.evaluation.evaluation_service import EvaluationService
    
    eval_service = EvaluationService()
    
    try:
        # Start evaluation
        evaluation_id = await eval_service.run_evaluation(
            test_case_data=test_case,
            agent_type="cmo"
        )
        
        logger.info(f"Started evaluation: {evaluation_id}")
        
        # Wait for completion
        logger.info("Waiting for evaluation to complete...")
        await asyncio.sleep(2)  # Give it time to start
        
        # Stream progress
        async for event in eval_service.stream_evaluation_progress(evaluation_id):
            event_type = event.get("type")
            content = event.get("content")
            
            logger.info(f"[{event_type}] {content}")
            
            if event_type == "result":
                result_data = event.get("data", {})
                logger.info("\n=== EVALUATION RESULTS ===")
                logger.info(f"Overall Score: {result_data.get('overall_score', 0) * 100:.1f}%")
                
                # Check dimensions
                dimensions = result_data.get("dimension_results", {})
                for dim_name, dim_data in dimensions.items():
                    score = dim_data.get("normalized_score", 0) * 100
                    logger.info(f"{dim_name}: {score:.1f}%")
                
                # Check report URL
                report_url = result_data.get("report_url")
                if report_url:
                    logger.info(f"\n📊 Report URL: {report_url}")
                    logger.info("✅ Report generation successful!")
                else:
                    logger.error("❌ No report URL found!")
                
                break
            elif event_type == "error":
                logger.error(f"Evaluation failed: {content}")
                break
        
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)


async def check_report_contents():
    """Check if generated reports have all expected content."""
    
    report_dir = Path("evaluation_results/qe_reports")
    if not report_dir.exists():
        logger.error(f"Report directory not found: {report_dir}")
        return
    
    # Find most recent report
    report_dirs = [d for d in report_dir.iterdir() if d.is_dir()]
    if not report_dirs:
        logger.error("No reports found")
        return
    
    latest_report = sorted(report_dirs, key=lambda x: x.stat().st_mtime)[-1]
    report_html = latest_report / "report" / "report.html"
    
    if not report_html.exists():
        logger.error(f"Report HTML not found: {report_html}")
        return
    
    logger.info(f"\nChecking report: {report_html}")
    
    # Read report content
    with open(report_html, 'r') as f:
        content = f.read()
    
    # Check for key sections
    checks = {
        "Executive Summary": "Executive Summary" in content,
        "Overall Score": "Overall Score" in content,
        "Dimension Scores": "Dimension Scores" in content,
        "Complexity Classification": "complexity_classification" in content,
        "Specialty Selection": "specialty_selection" in content,
        "Tool Usage": "tool_usage" in content,
        "Response Structure": "response_structure" in content,
        "Test Case Details": "Test Case" in content,
        "Visualizations": '<canvas' in content or 'chart' in content
    }
    
    logger.info("\nReport Content Checks:")
    all_passed = True
    for check_name, passed in checks.items():
        status = "✅" if passed else "❌"
        logger.info(f"{status} {check_name}")
        if not passed:
            all_passed = False
    
    if all_passed:
        logger.info("\n✅ All report sections present!")
    else:
        logger.error("\n❌ Some report sections missing!")
    
    logger.info(f"\nOpen report in browser: file://{report_html.absolute()}")


if __name__ == "__main__":
    # Run the test
    asyncio.run(test_unified_evaluator())
    
    # Check report contents
    asyncio.run(check_report_contents())