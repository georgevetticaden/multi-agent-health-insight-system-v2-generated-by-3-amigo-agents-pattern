#!/usr/bin/env python3
"""
Quick test to verify report generation is working after fixing the import.
"""

import asyncio
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_report_generation():
    """Test that report generation works with a simple evaluation result."""
    
    try:
        from services.evaluation.report_service import EvaluationReportService
        logger.info("✅ Import successful!")
        
        # Create a test evaluation result
        test_case = {
            "id": "test_report_001",
            "query": "What are my latest blood pressure readings?",
            "expected_complexity": "SIMPLE",
            "expected_specialties": ["cardiology"],
            "key_data_points": ["blood_pressure"],
            "trace_id": "test_trace_123"
        }
        
        evaluation_result = {
            "test_case_id": "test_report_001",
            "overall_score": 0.85,
            "dimension_results": {
                "complexity_classification": {
                    "score": 1.0,
                    "normalized_score": 1.0,
                    "details": {
                        "expected": "SIMPLE",
                        "actual": "SIMPLE",
                        "correct": True
                    }
                },
                "tool_usage": {
                    "score": 0.8,
                    "normalized_score": 0.8,
                    "details": {
                        "tool_calls_made": 2,
                        "successful_tool_calls": 2,
                        "success_rate": 1.0
                    }
                }
            },
            "execution_time_ms": 1234
        }
        
        # Test report generation
        report_service = EvaluationReportService()
        logger.info("Creating report...")
        
        report_path = report_service.generate_report_from_evaluation(
            evaluation_id="test_eval_001",
            test_case=test_case,
            evaluation_result=evaluation_result,
            agent_type="cmo"
        )
        
        logger.info(f"✅ Report generated at: {report_path}")
        
        # Check if report exists
        report_html = Path(report_path) / "report.html"
        if report_html.exists():
            logger.info(f"✅ Report HTML exists: {report_html}")
            logger.info(f"📊 Open in browser: file://{report_html.absolute()}")
        else:
            logger.error("❌ Report HTML not found!")
            
    except Exception as e:
        logger.error(f"❌ Test failed: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(test_report_generation())