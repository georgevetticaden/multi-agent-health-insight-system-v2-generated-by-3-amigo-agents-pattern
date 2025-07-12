#!/usr/bin/env python3
"""
Quick setup verification script for the evaluation framework.
Run this to ensure all components are properly configured.
"""

import sys
import os
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent.parent))

import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_setup():
    """Verify evaluation framework setup"""
    logger.info("\n🔍 Checking Evaluation Framework Setup")
    logger.info("=" * 50)
    
    # Check environment
    issues = []
    
    # 1. Check API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        issues.append("ANTHROPIC_API_KEY environment variable not set")
    else:
        logger.info("✅ Anthropic API key found")
    
    # 2. Check imports
    try:
        from evaluation.criteria.cmo import CMOEvaluationRubric
        logger.info("✅ Evaluation criteria module loaded")
    except ImportError as e:
        issues.append(f"Failed to import criteria: {e}")
    
    try:
        from evaluation.test_cases.cmo import CMOTestCases
        test_count = len(CMOTestCases.get_all_test_cases())
        real_world_count = len(CMOTestCases.get_real_world_based_cases())
        logger.info(f"✅ Test cases loaded: {test_count} total, {real_world_count} from real queries")
    except ImportError as e:
        issues.append(f"Failed to import test cases: {e}")
    
    try:
        from evaluation.framework.evaluators.cmo import CMOEvaluator
        logger.info("✅ Evaluator framework loaded")
    except ImportError as e:
        issues.append(f"Failed to import evaluator: {e}")
    
    # 3. Check directories
    dirs_to_check = [
        ("results", "Results directory"),
        ("results/reports", "Reports directory"),
        ("results/real_world", "Real-world results directory")
    ]
    
    for dir_path, desc in dirs_to_check:
        full_path = Path(__file__).parent.parent / dir_path
        if full_path.exists():
            logger.info(f"✅ {desc} exists")
        else:
            logger.warning(f"⚠️  {desc} will be created on first run")
    
    # 4. Check test categories
    try:
        from evaluation.test_cases.cmo import CMOTestCases
        categories = set()
        for tc in CMOTestCases.get_all_test_cases():
            categories.add(tc.category)
        logger.info(f"📊 Test categories available: {', '.join(sorted(categories))}")
    except Exception as e:
        issues.append(f"Failed to analyze test categories: {e}")
    
    # Summary
    logger.info("\n" + "=" * 50)
    if issues:
        logger.error("❌ Setup Issues Found:")
        for issue in issues:
            logger.error(f"  - {issue}")
        return False
    else:
        logger.info("✅ All checks passed! The evaluation framework is ready to use.")
        logger.info("\n📚 Quick Start Commands:")
        logger.info("  python -m evaluation.cli.run_evaluation --test example")
        logger.info("  python -m evaluation.cli.run_evaluation --test comprehensive")
        logger.info("  python -m evaluation.cli.run_evaluation --test real-world")
        return True


if __name__ == "__main__":
    success = check_setup()
    sys.exit(0 if success else 1)