#!/usr/bin/env python3
"""Test script to generate a new evaluation report with the updated template."""

import sys
from pathlib import Path
import json

# Add paths
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "backend"))
sys.path.insert(0, str(project_root))

from evaluation.framework.report_generator.dynamic_report_generator import DynamicHTMLReportGenerator

# Load existing results
results_path = Path("test_runs/cmo-example_20250716_083430/results.json")
with open(results_path) as f:
    results = json.load(f)

# Create new report directory
test_run_dir = Path("test_runs/cmo-example_test_light_theme")
test_run_dir.mkdir(exist_ok=True, parents=True)

# Copy results
new_results_path = test_run_dir / "results.json"
with open(new_results_path, 'w') as f:
    json.dump(results, f, indent=2)

# Generate report with new template
generator = DynamicHTMLReportGenerator(test_run_dir, "cmo", use_health_insight_theme=True)
report_dir = generator.generate_html_report(results)

print(f"Report generated at: {report_dir / 'report.html'}")
print(f"Open with: open {report_dir / 'report.html'}")