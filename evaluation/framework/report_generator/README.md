# Report Generator Module

This module provides comprehensive HTML report generation for CMO Agent evaluations using Jinja2 templates and modern web design.

## Module Structure

```
report_generator/
├── __init__.py                    # Module exports
├── report_generator.py            # Main coordinator (HTML + visualizations)
├── html_report_generator.py       # HTML template processor
├── report_template_health_insight.html  # Jinja2 template with health insight theme
└── README.md                      # This file
```

## Template Structure

### report_template_health_insight.html
The main template file that generates the complete HTML report with:

- **Light health insight theme** with clean, medical-grade styling
- **Interactive collapsible sections** for detailed information
- **Progress bars** for dimension performance visualization
- **Animated failure cards** with gradient borders and pulse effects
- **Responsive design** that works on different screen sizes

## Template Variables

The template uses these main data structures:

### Basic Info
- `report_title`: Title of the report
- `test_suite`: Name of the test suite (e.g., "Real World")
- `timestamp`: When the evaluation was run
- `overall_result`: "PASSED" or "FAILED"
- `overall_score`: Overall score as percentage

### Test Summary
- `test_summary`: Array of test case summaries with status and failed dimensions
- `tests_passed`: Number of tests that passed
- `total_tests`: Total number of tests

### Dimension Performance
- `dimension_performance`: Array of dimension scores with progress bars
- `dimension_failure_details`: Breakdown of failures by dimension

### Test Cases
- `test_cases`: Detailed data for each test case including:
  - Health query and response
  - Evaluation dimensions table
  - Quality breakdown (collapsible)
  - Failure analysis cards

## Styling Features

### Health Insight Theme
- Light gradient background with subtle medical-grade styling
- Clean card design with health insight branding
- Accessible color scheme optimized for medical data visualization

### Interactive Elements
- Collapsible sections with smooth animations
- Hover effects on clickable elements
- Animated progress bars with target indicators

### Failure Analysis
- Gradient-bordered cards with pulse animation
- Color-coded priority badges
- Structured recommendation boxes

## Usage

The template is automatically used by `HTMLReportGenerator`:

```python
from evaluation.framework.report_generator import EvaluationReportGenerator

generator = EvaluationReportGenerator(test_run_dir)
report_path = generator.generate_report(results, format_type="html")
```

## Customization

To customize the template:

1. Edit `report_template_health_insight.html` directly
2. Modify CSS styles in the `<style>` section
3. Update template variables in `html_report_generator.py`
4. Add new sections by extending the template structure

## Browser Compatibility

The template uses modern CSS features:
- CSS Grid and Flexbox
- Backdrop filters (glassmorphism)
- CSS animations and transitions
- Modern color functions

Supports all modern browsers (Chrome, Firefox, Safari, Edge).