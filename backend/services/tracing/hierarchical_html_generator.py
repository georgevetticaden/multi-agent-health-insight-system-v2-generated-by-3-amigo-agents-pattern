"""
Hierarchical HTML generator for trace viewer.

Creates an intuitive, hierarchical view of trace events organized by
agents and showing clear parent-child relationships.
"""

import json
from typing import Dict, Any, List, Tuple
from .trace_models import CompleteTrace, TraceEventType, TraceEvent
from .trace_hierarchy import build_trace_hierarchy, HierarchicalEvent, AgentSection, StageInfo
from .trace_formatters import (
    format_duration, format_token_count, estimate_api_cost,
    format_cost, truncate_text, extract_prompt_components
)


def generate_hierarchical_trace_html(trace: CompleteTrace) -> str:
    """
    Generate hierarchical HTML view of trace.
    
    Args:
        trace: Complete trace object
        
    Returns:
        Self-contained HTML string
    """
    # Build hierarchy
    sections, summary = build_trace_hierarchy(trace)
    
    # Generate HTML
    html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Trace Analysis - {trace.trace_id}</title>
    <style>
        {_generate_css()}
    </style>
</head>
<body>
    <div class="container">
        {_generate_header(trace, summary)}
        {_generate_filter_panel()}
        {_generate_summary_cards(sections, summary)}
        {_generate_timeline(sections)}
        {_generate_agent_sections(sections)}
    </div>
    
    <script>
        {_generate_javascript()}
    </script>
</body>
</html>
    """
    
    return html


def _generate_css() -> str:
    """Generate CSS styles"""
    return """
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 0;
            background-color: #f5f7fa;
            color: #2c3e50;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }
        
        /* Header Styles */
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 12px;
            margin-bottom: 30px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        }
        
        .header h1 {
            margin: 0 0 10px 0;
            font-size: 28px;
            font-weight: 600;
        }
        
        .header-meta {
            display: flex;
            gap: 30px;
            margin-top: 15px;
            font-size: 14px;
            opacity: 0.9;
        }
        
        /* Summary Section */
        .summary-section {
            background: white;
            padding: 30px;
            border-radius: 12px;
            margin-bottom: 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }
        
        /* Filter Panel */
        .filter-panel {
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 15px;
        }
        
        .filter-group {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .filter-label {
            font-size: 14px;
            color: #2c3e50;
            font-weight: 600;
        }
        
        .filter-checkbox {
            display: flex;
            align-items: center;
            gap: 5px;
            padding: 5px 10px;
            background: #f8f9fa;
            border-radius: 4px;
            cursor: pointer;
            transition: all 0.2s;
        }
        
        .filter-checkbox:hover {
            background: #e9ecef;
        }
        
        .filter-checkbox input[type="checkbox"] {
            cursor: pointer;
        }
        
        .filter-checkbox label {
            cursor: pointer;
            font-size: 13px;
            color: #495057;
        }
        
        .view-toggle {
            display: flex;
            gap: 5px;
            background: #f8f9fa;
            padding: 4px;
            border-radius: 6px;
        }
        
        .view-toggle button {
            padding: 6px 12px;
            border: none;
            background: transparent;
            color: #495057;
            cursor: pointer;
            border-radius: 4px;
            font-size: 13px;
            transition: all 0.2s;
        }
        
        .view-toggle button.active {
            background: white;
            color: #2c3e50;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        
        .view-toggle button:hover:not(.active) {
            background: rgba(255,255,255,0.5);
        }
        
        .filter-group select {
            padding: 6px 10px;
            border: 1px solid #dee2e6;
            border-radius: 4px;
            font-size: 13px;
            color: #495057;
            background: white;
            cursor: pointer;
        }
        
        /* Summary Cards */
        .summary-cards {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 15px;
            margin-bottom: 30px;
        }
        
        .summary-card {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
            text-align: center;
            transition: transform 0.2s;
        }
        
        .summary-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        }
        
        .summary-card .icon {
            font-size: 32px;
            margin-bottom: 10px;
        }
        
        .summary-card .value {
            font-size: 32px;
            font-weight: 700;
            color: #2c3e50;
            margin: 10px 0;
        }
        
        .summary-card .label {
            font-size: 14px;
            color: #7f8c8d;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        /* Timeline */
        .timeline-section {
            background: white;
            padding: 25px;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }
        
        .timeline-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }
        
        .timeline-header h2 {
            margin: 0;
            color: #2c3e50;
            font-size: 20px;
        }
        
        .timeline-container {
            position: relative;
            overflow-x: auto;
            padding: 20px 0;
        }
        
        .timeline-wrapper {
            min-width: 1200px;
            position: relative;
        }
        
        /* Time Axis */
        .timeline-axis {
            position: relative;
            height: 30px;
            border-bottom: 2px solid #e9ecef;
            margin-bottom: 10px;
        }
        
        .time-marker {
            position: absolute;
            bottom: 0;
            font-size: 11px;
            color: #7f8c8d;
            transform: translateX(-50%);
        }
        
        .time-marker::before {
            content: '';
            position: absolute;
            bottom: -2px;
            left: 50%;
            width: 1px;
            height: 8px;
            background: #bdc3c7;
            transform: translateX(-50%);
        }
        
        /* Vertical gridlines */
        .time-marker::after {
            content: '';
            position: absolute;
            bottom: -10px;
            left: 50%;
            width: 1px;
            height: calc(100vh - 200px);
            background: rgba(189, 195, 199, 0.15);
            transform: translateX(-50%);
            z-index: 0;
        }
        
        /* Timeline Lanes */
        .timeline-lanes {
            position: relative;
        }
        
        .timeline-lane-row {
            display: flex;
            align-items: center;
            height: 60px;
            margin-bottom: 5px;
            position: relative;
        }
        
        /* Group specialists visually */
        .specialist-group {
            background: rgba(46, 204, 113, 0.05);
            border: 1px solid rgba(46, 204, 113, 0.2);
            border-radius: 8px;
            padding: 10px 0;
            margin: 10px 0;
            position: relative;
        }
        
        .specialist-group::before {
            content: 'Medical Specialists';
            position: absolute;
            top: -10px;
            left: 20px;
            background: white;
            padding: 0 10px;
            font-size: 11px;
            color: #2ecc71;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .timeline-agent-label {
            flex: 0 0 200px;
            font-weight: 600;
            color: #2c3e50;
            font-size: 13px;
            padding: 8px 15px;
            background: #f8f9fa;
            border-radius: 6px;
            border-left: 4px solid #3498db;
            margin-right: 20px;
            text-align: center;
        }
        
        .timeline-agent-label.cmo {
            border-left-color: #e74c3c;
            background: #fee;
        }
        
        .timeline-agent-label.cardiology,
        .timeline-agent-label.endocrinology,
        .timeline-agent-label.laboratory_medicine,
        .timeline-agent-label.pharmacy {
            border-left-color: #2ecc71;
            background: #efe;
        }
        
        .timeline-agent-label.visualization {
            border-left-color: #9b59b6;
            background: #fef;
        }
        
        /* Timeline Track */
        .timeline-track {
            flex: 1;
            position: relative;
            height: 40px;
            background: #f8f9fa;
            border-radius: 4px;
            background-image: repeating-linear-gradient(
                90deg,
                transparent,
                transparent 10%,
                rgba(0,0,0,0.02) 10%,
                rgba(0,0,0,0.02) 10.1%
            );
        }
        
        /* Highlight parallel execution */
        .specialist-group .timeline-track {
            background-color: #f0fcf4;
        }
        
        /* Stage Bars */
        .timeline-stage-bar {
            position: absolute;
            top: 5px;
            height: 30px;
            border-radius: 4px;
            transition: all 0.2s;
            cursor: pointer;
            overflow: hidden;
            min-width: 60px;
        }
        
        .timeline-stage-bar:hover {
            transform: translateY(-2px);
            box-shadow: 0 2px 8px rgba(0,0,0,0.15);
            z-index: 10;
        }
        
        .timeline-stage-bar.cmo {
            background: #e74c3c;
            border: 1px solid #c0392b;
        }
        
        .timeline-stage-bar.cardiology,
        .timeline-stage-bar.endocrinology,
        .timeline-stage-bar.laboratory_medicine,
        .timeline-stage-bar.pharmacy {
            background: #2ecc71;
            border: 1px solid #27ae60;
        }
        
        .timeline-stage-bar.visualization {
            background: #9b59b6;
            border: 1px solid #8e44ad;
        }
        
        .stage-bar-content {
            padding: 4px 8px;
            color: white;
            font-size: 11px;
            display: flex;
            flex-direction: column;
            position: relative;
            z-index: 2;
            justify-content: center;
            height: 100%;
        }
        
        /* Status indicators */
        .timeline-stage-bar.success::after {
            content: '✓';
            position: absolute;
            right: 8px;
            top: 50%;
            transform: translateY(-50%);
            color: white;
            font-size: 14px;
            font-weight: bold;
            opacity: 0.9;
        }
        
        .timeline-stage-bar.error::after {
            content: '✗';
            position: absolute;
            right: 8px;
            top: 50%;
            transform: translateY(-50%);
            color: white;
            font-size: 14px;
            font-weight: bold;
        }
        
        .timeline-stage-bar.running {
            animation: pulse 1.5s infinite;
        }
        
        @keyframes pulse {
            0% { opacity: 1; box-shadow: 0 2px 8px rgba(0,0,0,0.15); }
            50% { opacity: 0.8; box-shadow: 0 2px 12px rgba(0,0,0,0.25); }
            100% { opacity: 1; box-shadow: 0 2px 8px rgba(0,0,0,0.15); }
        }
        
        .stage-bar-name {
            font-weight: 600;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        
        .stage-bar-time {
            font-size: 10px;
            opacity: 0.9;
        }
        
        /* Stage Bar Hover Details */
        .stage-bar-hover {
            position: absolute;
            bottom: 100%;
            left: 50%;
            transform: translateX(-50%);
            background: rgba(0, 0, 0, 0.9);
            color: white;
            padding: 8px 12px;
            border-radius: 6px;
            font-size: 11px;
            white-space: nowrap;
            display: none;
            margin-bottom: 8px;
            z-index: 100;
        }
        
        .stage-bar-hover::after {
            content: '';
            position: absolute;
            top: 100%;
            left: 50%;
            transform: translateX(-50%);
            width: 0;
            height: 0;
            border-left: 6px solid transparent;
            border-right: 6px solid transparent;
            border-top: 6px solid rgba(0, 0, 0, 0.9);
        }
        
        .timeline-stage-bar:hover .stage-bar-hover {
            display: block;
        }
        
        .hover-metric {
            margin: 2px 0;
        }
        
        /* Flow arrows and critical path visualization */
        .flow-arrow {
            position: absolute;
            height: 2px;
            background: rgba(52, 152, 219, 0.3);
            transform-origin: left center;
            pointer-events: none;
            z-index: 1;
            transition: opacity 0.3s;
        }
        
        .flow-arrow::after {
            content: '';
            position: absolute;
            right: -8px;
            top: -3px;
            width: 0;
            height: 0;
            border-left: 8px solid rgba(52, 152, 219, 0.5);
            border-top: 4px solid transparent;
            border-bottom: 4px solid transparent;
        }
        
        .flow-arrow.critical {
            background: rgba(231, 76, 60, 0.5);
            height: 3px;
            box-shadow: 0 0 8px rgba(231, 76, 60, 0.5);
        }
        
        .flow-arrow.critical::after {
            border-left-color: rgba(231, 76, 60, 0.8);
        }
        
        /* Stage highlighting for interaction */
        .timeline-stage-bar.highlighted {
            opacity: 1 !important;
            transform: translateY(-2px) scaleY(1.1);
            box-shadow: 0 0 10px currentColor;
            z-index: 20;
        }
        
        .timeline-stage-bar.dimmed {
            opacity: 0.3 !important;
        }
        
        .timeline-stage-bar.related {
            opacity: 0.7 !important;
            border-width: 2px;
        }
        
        /* Timeline legend */
        .timeline-legend {
            position: absolute;
            top: 10px;
            right: 10px;
            background: rgba(255, 255, 255, 0.95);
            padding: 10px;
            border-radius: 4px;
            font-size: 11px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .legend-item {
            display: flex;
            align-items: center;
            margin: 5px 0;
        }
        
        .legend-color {
            width: 30px;
            height: 3px;
            margin-right: 8px;
            border-radius: 2px;
        }
        
        .legend-color.cmo {
            background: #e74c3c;
        }
        
        .legend-color.specialist {
            background: #3498db;
        }
        
        .legend-color.visualization {
            background: #2ecc71;
        }
        
        .legend-color.flow {
            background: rgba(52, 152, 219, 0.5);
        }
        
        .legend-color.critical {
            background: rgba(231, 76, 60, 0.5);
        }
        
        /* Agent Sections */
        .agent-section {
            background: white;
            border-radius: 10px;
            margin-bottom: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
            overflow: hidden;
        }
        
        /* Stage Sections */
        .stage-section {
            margin: 15px 0;
            border: 1px solid #e9ecef;
            border-radius: 8px;
            overflow: hidden;
        }
        
        .stage-header {
            background: #f8f9fa;
            padding: 12px 15px;
            cursor: pointer;
            user-select: none;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .stage-header:hover {
            background: #e9ecef;
        }
        
        .stage-header h4 {
            margin: 0;
            color: #2c3e50;
            font-size: 15px;
            font-weight: 600;
        }
        
        .stage-meta {
            display: flex;
            gap: 15px;
            font-size: 12px;
            color: #7f8c8d;
            align-items: center;
        }
        
        .stage-toggle {
            margin-left: auto;
            font-size: 14px;
            color: #95a5a6;
            transition: transform 0.3s;
        }
        
        .stage-header.expanded .stage-toggle {
            transform: rotate(180deg);
        }
        
        .stage-content {
            padding: 15px;
            display: none;
        }
        
        .stage-content.show {
            display: block;
        }
        
        .agent-header {
            background: #f8f9fa;
            padding: 20px;
            cursor: pointer;
            user-select: none;
            display: flex;
            justify-content: space-between;
            align-items: center;
            transition: background 0.2s;
        }
        
        .agent-header:hover {
            background: #e9ecef;
        }
        
        .agent-header.cmo {
            border-left: 5px solid #e74c3c;
        }
        
        .agent-header.specialist {
            border-left: 5px solid #2ecc71;
        }
        
        .agent-info {
            flex: 1;
        }
        
        .agent-title {
            font-size: 18px;
            font-weight: 600;
            color: #2c3e50;
            margin-bottom: 5px;
        }
        
        .agent-meta {
            display: flex;
            gap: 20px;
            font-size: 13px;
            color: #7f8c8d;
        }
        
        .toggle-icon {
            font-size: 20px;
            color: #7f8c8d;
            transition: transform 0.3s;
        }
        
        .agent-header.expanded .toggle-icon {
            transform: rotate(180deg);
        }
        
        .agent-content {
            display: none;
            padding: 20px;
        }
        
        .agent-content.show {
            display: block;
        }
        
        /* Event Hierarchy */
        .event-tree {
            margin: 0;
            padding: 0;
        }
        
        .event-node {
            margin: 10px 0;
            position: relative;
        }
        
        .event-node.level-1 {
            margin-left: 30px;
        }
        
        .event-node.level-2 {
            margin-left: 60px;
        }
        
        .event-node.level-3 {
            margin-left: 90px;
        }
        
        .event-connector {
            position: absolute;
            left: -20px;
            top: 0;
            bottom: 0;
            width: 1px;
            background: #ddd;
        }
        
        .event-connector::before {
            content: '';
            position: absolute;
            left: 0;
            top: 20px;
            width: 15px;
            height: 1px;
            background: #ddd;
        }
        
        .event-card {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 15px;
            border: 1px solid #e9ecef;
            position: relative;
            transition: all 0.2s;
        }
        
        .event-card:hover {
            background: #fff;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }
        
        .event-card.llm-prompt {
            border-left: 3px solid #3498db;
            background: #e8f4fd;
        }
        
        .event-card.llm-response {
            border-left: 3px solid #2ecc71;
            background: #e8f8f5;
        }
        
        .event-card.tool-invocation {
            border-left: 3px solid #f39c12;
            background: #fef5e7;
        }
        
        .event-card.tool-result {
            border-left: 3px solid #9b59b6;
            background: #f4ecf7;
        }
        
        .event-header-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }
        
        .event-type-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            color: white;
        }
        
        .event-type-badge.llm-prompt {
            background: #3498db;
        }
        
        .event-type-badge.llm-response {
            background: #2ecc71;
        }
        
        .event-type-badge.tool-invocation {
            background: #f39c12;
        }
        
        .event-type-badge.tool-result {
            background: #9b59b6;
        }
        
        .event-metadata {
            display: flex;
            gap: 15px;
            font-size: 12px;
            color: #7f8c8d;
        }
        
        .event-content {
            margin-top: 10px;
        }
        
        .event-summary {
            font-size: 14px;
            color: #2c3e50;
            margin-bottom: 10px;
        }
        
        .event-details {
            display: none;
            margin-top: 10px;
            padding-top: 10px;
            border-top: 1px solid #e9ecef;
        }
        
        .event-details.show {
            display: block;
        }
        
        .show-details-btn {
            color: #3498db;
            cursor: pointer;
            font-size: 13px;
            text-decoration: none;
            display: inline-flex;
            align-items: center;
            gap: 5px;
        }
        
        .show-details-btn:hover {
            text-decoration: underline;
        }
        
        /* Key Findings */
        .key-findings {
            background: #e8f4fd;
            border-radius: 8px;
            padding: 15px;
            margin-top: 15px;
        }
        
        .key-findings h4 {
            margin: 0 0 10px 0;
            color: #2980b9;
            font-size: 14px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .findings-list {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
        }
        
        .finding-badge {
            background: white;
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 13px;
            border: 1px solid #3498db;
            color: #2980b9;
        }
        
        /* Agent Metrics */
        .agent-metrics {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 15px;
        }
        
        .agent-metric-card {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 15px;
            border-left: 4px solid #3498db;
            transition: all 0.2s;
        }
        
        .agent-metric-card:hover {
            background: #fff;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .agent-metric-card.cmo {
            border-left-color: #e74c3c;
        }
        
        .agent-metric-card.specialist {
            border-left-color: #2ecc71;
        }
        
        .agent-metric-card.visualization {
            border-left-color: #9b59b6;
        }
        
        .agent-metric-efficiency {
            display: flex;
            justify-content: space-between;
            margin-top: 10px;
            padding-top: 10px;
            border-top: 1px solid #e9ecef;
            font-size: 11px;
        }
        
        .efficiency-item {
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        
        .efficiency-label {
            color: #7f8c8d;
            font-size: 10px;
            text-transform: uppercase;
        }
        
        .efficiency-value {
            font-weight: 600;
            color: #2ecc71;
            margin-top: 2px;
        }
        
        .agent-metric-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }
        
        .agent-name {
            font-weight: 600;
            color: #2c3e50;
            font-size: 14px;
        }
        
        .agent-duration {
            background: #3498db;
            color: white;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 12px;
        }
        
        .agent-metric-details {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 8px;
        }
        
        .metric-item {
            display: flex;
            justify-content: space-between;
            font-size: 12px;
        }
        
        .metric-label {
            color: #7f8c8d;
        }
        
        .metric-value {
            font-weight: 600;
            color: #2c3e50;
        }
        
        /* Utility Classes */
        .hidden {
            display: none;
        }
        
        .copy-btn {
            background: none;
            border: 1px solid #bdc3c7;
            border-radius: 4px;
            padding: 4px 8px;
            cursor: pointer;
            font-size: 12px;
            color: #7f8c8d;
            transition: all 0.2s;
        }
        
        .copy-btn:hover {
            background: #3498db;
            color: white;
            border-color: #3498db;
        }
        
        /* Scrollbar Styling */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }
        
        ::-webkit-scrollbar-track {
            background: #f1f1f1;
        }
        
        ::-webkit-scrollbar-thumb {
            background: #888;
            border-radius: 4px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: #555;
        }
        
        /* Data Value Highlighting */
        .data-value {
            background: #fff3cd;
            padding: 2px 6px;
            border-radius: 4px;
            font-weight: 600;
            color: #856404;
            border: 1px solid #ffeaa7;
            font-family: 'Courier New', monospace;
            display: inline-block;
            margin: 0 2px;
        }
        
        .data-value.data-glucose {
            background: #d1ecf1;
            color: #0c5460;
            border-color: #bee5eb;
        }
        
        .data-value.data-bp {
            background: #f8d7da;
            color: #721c24;
            border-color: #f5c6cb;
        }
        
        .data-value.data-cholesterol {
            background: #d4edda;
            color: #155724;
            border-color: #c3e6cb;
        }
        
        .data-value.data-hba1c {
            background: #e2e3e5;
            color: #383d41;
            border-color: #d6d8db;
        }
        
        /* Data Flow Connectors */
        .data-flow-indicator {
            position: absolute;
            left: -30px;
            top: 50%;
            transform: translateY(-50%);
            width: 20px;
            height: 20px;
            background: #3498db;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 10px;
            font-weight: bold;
        }
        
        .has-data-flow {
            position: relative;
        }
        
        .has-data-flow::before {
            content: '';
            position: absolute;
            left: -20px;
            top: 0;
            bottom: 0;
            width: 2px;
            background: linear-gradient(to bottom, #3498db, #2ecc71);
        }
    """


def _generate_javascript() -> str:
    """Generate JavaScript for interactivity"""
    return """
        function toggleAgent(agentId) {
            const header = document.getElementById(agentId + '-header');
            const content = document.getElementById(agentId + '-content');
            
            header.classList.toggle('expanded');
            content.classList.toggle('show');
        }
        
        function toggleStage(header) {
            const parent = header.parentElement;
            const content = parent.querySelector('.stage-content');
            const toggle = header.querySelector('.stage-toggle');
            
            header.classList.toggle('expanded');
            content.classList.toggle('show');
            
            // Update toggle arrow
            if (header.classList.contains('expanded')) {
                toggle.textContent = '▼';
            } else {
                toggle.textContent = '▶';
            }
        }
        
        function toggleEventDetails(eventId) {
            const details = document.getElementById(eventId + '-details');
            const btn = document.getElementById(eventId + '-btn');
            
            details.classList.toggle('show');
            
            if (details.classList.contains('show')) {
                btn.innerHTML = '▼ Hide Details';
            } else {
                btn.innerHTML = '▶ Show Details';
            }
        }
        
        function copyEventData(eventId) {
            const eventData = document.getElementById(eventId + '-data').textContent;
            navigator.clipboard.writeText(eventData).then(() => {
                showToast('Event data copied to clipboard!');
            });
        }
        
        function showToast(message) {
            const toast = document.createElement('div');
            toast.style.cssText = `
                position: fixed;
                bottom: 20px;
                right: 20px;
                background: #27ae60;
                color: white;
                padding: 10px 20px;
                border-radius: 4px;
                z-index: 1000;
                animation: slideIn 0.3s ease;
            `;
            toast.textContent = message;
            document.body.appendChild(toast);
            
            setTimeout(() => {
                toast.style.animation = 'slideOut 0.3s ease';
                setTimeout(() => document.body.removeChild(toast), 300);
            }, 2000);
        }
        
        // Add CSS animations
        const style = document.createElement('style');
        style.textContent = `
            @keyframes slideIn {
                from { transform: translateX(100%); opacity: 0; }
                to { transform: translateX(0); opacity: 1; }
            }
            @keyframes slideOut {
                from { transform: translateX(0); opacity: 1; }
                to { transform: translateX(100%); opacity: 0; }
            }
        `;
        document.head.appendChild(style);
        
        // Auto-expand first agent on load
        document.addEventListener('DOMContentLoaded', () => {
            const firstAgent = document.querySelector('.agent-header');
            if (firstAgent) {
                firstAgent.click();
            }
            
            // Add click handlers for timeline stages
            document.querySelectorAll('.timeline-stage-bar').forEach(bar => {
                bar.addEventListener('click', function() {
                    const stageId = this.getAttribute('data-stage-id');
                    highlightRelatedStages(stageId);
                });
            });
        });
        
        function highlightRelatedStages(stageId) {
            // Clear existing highlights
            document.querySelectorAll('.timeline-stage-bar').forEach(bar => {
                bar.classList.remove('highlighted', 'dimmed', 'related');
            });
            
            // Clear existing arrows
            document.querySelectorAll('.flow-arrow').forEach(arrow => arrow.remove());
            
            // Highlight clicked stage
            const clickedStage = document.querySelector(`[data-stage-id="${stageId}"]`);
            if (!clickedStage) return;
            
            clickedStage.classList.add('highlighted');
            
            // Get stage type and lane
            const stageType = stageId.split('-')[0];
            const stageName = stageId.split('-').slice(1).join('-');
            
            // Dim all other stages
            document.querySelectorAll('.timeline-stage-bar').forEach(bar => {
                if (bar !== clickedStage) {
                    bar.classList.add('dimmed');
                }
            });
            
            // Draw flow arrows based on stage relationships
            if (stageType === 'cmo') {
                if (stageName === 'task_creation') {
                    // Draw arrows from task_creation to all specialists
                    drawFlowArrows(clickedStage, '.timeline-stage-bar[data-stage-id*="specialist"]', false);
                    
                    // Highlight related specialists
                    document.querySelectorAll('.timeline-stage-bar[data-stage-id*="analysis"]').forEach(bar => {
                        bar.classList.remove('dimmed');
                        bar.classList.add('related');
                    });
                } else if (stageName === 'synthesis' || stageName === 'final_synthesis') {
                    // Draw arrows from all specialists to synthesis
                    document.querySelectorAll('.timeline-stage-bar[data-stage-id*="synthesis"]').forEach(source => {
                        if (source !== clickedStage && source.getAttribute('data-stage-id').includes('specialist')) {
                            drawFlowArrow(source, clickedStage, true);
                        }
                    });
                    
                    // Highlight specialist synthesis stages
                    document.querySelectorAll('.timeline-stage-bar[data-stage-id*="synthesis"]').forEach(bar => {
                        if (bar !== clickedStage) {
                            bar.classList.remove('dimmed');
                            bar.classList.add('related');
                        }
                    });
                }
            } else if (stageType.includes('specialist')) {
                // Highlight CMO task creation
                const cmoTaskBar = document.querySelector('[data-stage-id="cmo-task_creation"]');
                if (cmoTaskBar) {
                    cmoTaskBar.classList.remove('dimmed');
                    cmoTaskBar.classList.add('related');
                    drawFlowArrow(cmoTaskBar, clickedStage, false);
                }
                
                // Highlight CMO synthesis
                const cmoSynthesisBar = document.querySelector('[data-stage-id="cmo-synthesis"], [data-stage-id="cmo-final_synthesis"]');
                if (cmoSynthesisBar && stageName.includes('synthesis')) {
                    cmoSynthesisBar.classList.remove('dimmed');
                    cmoSynthesisBar.classList.add('related');
                    drawFlowArrow(clickedStage, cmoSynthesisBar, true);
                }
            } else if (stageType === 'visualization') {
                // Highlight CMO synthesis as input
                const cmoSynthesisBar = document.querySelector('[data-stage-id="cmo-synthesis"], [data-stage-id="cmo-final_synthesis"]');
                if (cmoSynthesisBar) {
                    cmoSynthesisBar.classList.remove('dimmed');
                    cmoSynthesisBar.classList.add('related');
                    drawFlowArrow(cmoSynthesisBar, clickedStage, false);
                }
            }
            
            // Click anywhere else to reset
            setTimeout(() => {
                document.addEventListener('click', function resetHighlight(e) {
                    if (!e.target.closest('.timeline-stage-bar')) {
                        document.querySelectorAll('.timeline-stage-bar').forEach(bar => {
                            bar.classList.remove('highlighted', 'dimmed', 'related');
                        });
                        document.querySelectorAll('.flow-arrow').forEach(arrow => arrow.remove());
                        document.removeEventListener('click', resetHighlight);
                    }
                }, { once: true });
            }, 100);
        }
        
        function drawFlowArrow(source, target, isCritical) {
            const sourceRect = source.getBoundingClientRect();
            const targetRect = target.getBoundingClientRect();
            const containerRect = document.querySelector('.timeline-container').getBoundingClientRect();
            
            const arrow = document.createElement('div');
            arrow.className = 'flow-arrow' + (isCritical ? ' critical' : '');
            
            // Calculate positions relative to container
            const x1 = sourceRect.right - containerRect.left;
            const y1 = sourceRect.top + sourceRect.height / 2 - containerRect.top;
            const x2 = targetRect.left - containerRect.left;
            const y2 = targetRect.top + targetRect.height / 2 - containerRect.top;
            
            const distance = Math.sqrt(Math.pow(x2 - x1, 2) + Math.pow(y2 - y1, 2));
            const angle = Math.atan2(y2 - y1, x2 - x1) * (180 / Math.PI);
            
            arrow.style.left = x1 + 'px';
            arrow.style.top = y1 + 'px';
            arrow.style.width = distance + 'px';
            arrow.style.transform = `rotate(${angle}deg)`;
            
            document.querySelector('.timeline-container').appendChild(arrow);
        }
        
        function drawFlowArrows(source, targetSelector, isCritical) {
            document.querySelectorAll(targetSelector).forEach(target => {
                drawFlowArrow(source, target, isCritical);
            });
        }
        
        // Filter functions
        function filterAgents() {
            const showCMO = document.getElementById('filter-cmo').checked;
            const showSpecialists = document.getElementById('filter-specialists').checked;
            const showVisualization = document.getElementById('filter-visualization').checked;
            
            // Filter timeline lanes
            document.querySelectorAll('.timeline-lane-row').forEach(row => {
                const label = row.querySelector('.timeline-agent-label');
                if (label.classList.contains('cmo')) {
                    row.style.display = showCMO ? 'flex' : 'none';
                } else if (label.classList.contains('visualization')) {
                    row.style.display = showVisualization ? 'flex' : 'none';
                } else {
                    row.style.display = showSpecialists ? 'flex' : 'none';
                }
            });
            
            // Filter agent sections
            document.querySelectorAll('.agent-section').forEach(section => {
                const header = section.querySelector('.agent-header');
                if (header.classList.contains('cmo')) {
                    section.style.display = showCMO ? 'block' : 'none';
                } else if (header.classList.contains('visualization')) {
                    section.style.display = showVisualization ? 'block' : 'none';
                } else {
                    section.style.display = showSpecialists ? 'block' : 'none';
                }
            });
        }
        
        function filterByDuration() {
            const minDuration = parseInt(document.getElementById('duration-filter').value);
            
            document.querySelectorAll('.timeline-stage-bar').forEach(bar => {
                const durationText = bar.querySelector('.stage-bar-time').textContent;
                const duration = parseDuration(durationText);
                bar.style.opacity = duration >= minDuration ? '1' : '0.3';
            });
        }
        
        function parseDuration(text) {
            // Parse duration text like "1 min 30 sec" to milliseconds
            let ms = 0;
            const minMatch = text.match(/(\d+)\s*min/);
            const secMatch = text.match(/(\d+(?:\.\d+)?)\s*sec/);
            const msMatch = text.match(/(\d+(?:\.\d+)?)\s*ms/);
            
            if (minMatch) ms += parseInt(minMatch[1]) * 60000;
            if (secMatch) ms += parseFloat(secMatch[1]) * 1000;
            if (msMatch) ms += parseFloat(msMatch[1]);
            
            return ms;
        }
        
        function setView(viewType) {
            document.querySelectorAll('.view-toggle button').forEach(btn => {
                btn.classList.remove('active');
            });
            event.target.classList.add('active');
            
            if (viewType === 'simplified') {
                // Hide detailed event trees
                document.querySelectorAll('.event-tree').forEach(tree => {
                    tree.style.display = 'none';
                });
                // Show only key findings
                document.querySelectorAll('.key-findings').forEach(findings => {
                    findings.style.display = 'block';
                });
            } else {
                // Show everything
                document.querySelectorAll('.event-tree').forEach(tree => {
                    tree.style.display = 'block';
                });
            }
        }
    """


def _generate_filter_panel() -> str:
    """Generate filter configuration panel"""
    return """
    <div class="filter-panel">
        <div class="filter-group">
            <span class="filter-label">Show Agents:</span>
            <div class="filter-checkbox">
                <input type="checkbox" id="filter-cmo" checked onchange="filterAgents()">
                <label for="filter-cmo">CMO</label>
            </div>
            <div class="filter-checkbox">
                <input type="checkbox" id="filter-specialists" checked onchange="filterAgents()">
                <label for="filter-specialists">Specialists</label>
            </div>
            <div class="filter-checkbox">
                <input type="checkbox" id="filter-visualization" checked onchange="filterAgents()">
                <label for="filter-visualization">Visualization</label>
            </div>
        </div>
        
        <div class="filter-group">
            <span class="filter-label">Min Duration:</span>
            <select id="duration-filter" onchange="filterByDuration()">
                <option value="0">All</option>
                <option value="1000">≥ 1s</option>
                <option value="5000">≥ 5s</option>
                <option value="10000">≥ 10s</option>
                <option value="30000">≥ 30s</option>
            </select>
        </div>
        
        <div class="view-toggle">
            <button class="active" onclick="setView('detailed')">Detailed</button>
            <button onclick="setView('simplified')">Simplified</button>
        </div>
    </div>
    """


def _generate_header(trace: CompleteTrace, summary: Dict[str, Any]) -> str:
    """Generate header section"""
    total_cost = estimate_api_cost(summary.get('total_tokens', 0))
    
    return f"""
    <div class="header">
        <h1>🔍 Trace Analysis Report</h1>
        <div class="header-meta">
            <div>
                <strong>Trace ID:</strong> {trace.trace_id}
            </div>
            <div>
                <strong>Duration:</strong> {format_duration(trace.total_duration_ms)}
            </div>
            <div>
                <strong>Start Time:</strong> {trace.start_time}
            </div>
            <div>
                <strong>Cost:</strong> {format_cost(total_cost)}
            </div>
        </div>
        <div style="margin-top: 15px; padding-top: 15px; border-top: 1px solid rgba(255,255,255,0.2);">
            <strong>Query:</strong> {truncate_text(trace.initial_input, 200)}
        </div>
    </div>
    """


def _generate_summary_cards(sections: List[AgentSection], summary: Dict[str, Any]) -> str:
    """Generate summary cards with agent breakdown"""
    
    # Calculate agent-specific metrics
    agent_metrics = []
    for section in sections:
        success_rate = 100  # Calculate based on errors if needed
        avg_response_time = section.total_duration_ms / section.llm_calls if section.llm_calls > 0 else 0
        
        agent_metrics.append({
            'name': section.agent_name,
            'type': section.agent_type,
            'stages': len(section.stages),
            'duration': section.total_duration_ms,
            'llm_calls': section.llm_calls,
            'tool_calls': section.tool_calls,
            'tokens': section.tokens_used,
            'avg_response': avg_response_time
        })
    
    # Sort by duration to show slowest agents
    agent_metrics.sort(key=lambda x: x['duration'], reverse=True)
    
    return f"""
    <div class="summary-section">
        <h3 style="margin-bottom: 20px; color: #2c3e50;">Execution Summary</h3>
        
        <div class="summary-cards">
            <div class="summary-card">
                <div class="icon">👥</div>
                <div class="value">{summary['total_agents']}</div>
                <div class="label">Agents Involved</div>
            </div>
            <div class="summary-card">
                <div class="icon">📊</div>
                <div class="value">{summary.get('total_stages', 0)}</div>
                <div class="label">Execution Stages</div>
            </div>
            <div class="summary-card">
                <div class="icon">🔵</div>
                <div class="value">{summary['total_llm_calls']}</div>
                <div class="label">LLM Calls</div>
            </div>
            <div class="summary-card">
                <div class="icon">🔧</div>
                <div class="value">{summary['total_tool_calls']}</div>
                <div class="label">Tool Calls</div>
            </div>
            <div class="summary-card">
                <div class="icon">🎯</div>
                <div class="value">{format_token_count(summary['total_tokens'])}</div>
                <div class="label">Tokens Used</div>
            </div>
            <div class="summary-card">
                <div class="icon">💰</div>
                <div class="value">{format_cost(estimate_api_cost(summary['total_tokens']))}</div>
                <div class="label">Est. Cost</div>
            </div>
        </div>
        
        <h4 style="margin: 30px 0 15px 0; color: #2c3e50;">Agent Performance</h4>
        <div class="agent-metrics">
            {_generate_agent_metric_cards(agent_metrics)}
        </div>
    </div>
    """


def _generate_agent_metric_cards(metrics: List[Dict[str, Any]]) -> str:
    """Generate individual agent metric cards with enhanced metrics"""
    cards = []
    
    for metric in metrics[:5]:  # Show top 5 agents by duration
        agent_class = "cmo" if metric['type'] == "cmo" else "specialist" if "specialist" in metric['type'].lower() else "visualization"
        
        # Calculate efficiency metrics
        tokens_per_sec = (metric['tokens'] / (metric['duration'] / 1000)) if metric['duration'] > 0 else 0
        avg_tokens_per_call = (metric['tokens'] / metric['llm_calls']) if metric['llm_calls'] > 0 else 0
        
        cards.append(f"""
        <div class="agent-metric-card {agent_class}">
            <div class="agent-metric-header">
                <span class="agent-name">{metric['name']}</span>
                <span class="agent-duration">{format_duration(metric['duration'])}</span>
            </div>
            <div class="agent-metric-details">
                <div class="metric-item">
                    <span class="metric-label">Stages:</span>
                    <span class="metric-value">{metric['stages']}</span>
                </div>
                <div class="metric-item">
                    <span class="metric-label">LLM Calls:</span>
                    <span class="metric-value">{metric['llm_calls']}</span>
                </div>
                <div class="metric-item">
                    <span class="metric-label">Tool Calls:</span>
                    <span class="metric-value">{metric['tool_calls']}</span>
                </div>
                <div class="metric-item">
                    <span class="metric-label">Avg Response:</span>
                    <span class="metric-value">{format_duration(metric['avg_response'])}</span>
                </div>
            </div>
            <div class="agent-metric-efficiency">
                <div class="efficiency-item">
                    <span class="efficiency-label">Speed:</span>
                    <span class="efficiency-value">{tokens_per_sec:.0f} tok/s</span>
                </div>
                <div class="efficiency-item">
                    <span class="efficiency-label">Efficiency:</span>
                    <span class="efficiency-value">{avg_tokens_per_call:.0f} tok/call</span>
                </div>
            </div>
        </div>
        """)
    
    return "".join(cards)


def _generate_timeline(sections: List[AgentSection]) -> str:
    """Generate temporal timeline visualization showing true execution flow"""
    
    # Collect all stages with timing info
    all_stages = []
    
    for section in sections:
        for stage_name, stage_info in section.stages.items():
            # Calculate actual start/end times
            start_time = stage_info.first_event_time or stage_info.start_time
            if start_time:
                all_stages.append({
                    'agent_name': section.agent_name,
                    'agent_type': section.agent_type,
                    'stage_name': stage_name,
                    'stage_info': stage_info,
                    'start_time': start_time,
                    'duration_ms': stage_info.duration_ms or 0,
                    'execution_order': stage_info.execution_order
                })
    
    if not all_stages:
        return '<div class="timeline-section"><p>No timeline data available</p></div>'
    
    # Sort by start time to find min/max
    all_stages.sort(key=lambda x: x['start_time'])
    
    # Calculate timeline bounds
    try:
        from datetime import datetime
        min_time = datetime.fromisoformat(all_stages[0]['start_time'].replace('Z', '+00:00'))
        max_time = min_time
        
        for stage in all_stages:
            stage_time = datetime.fromisoformat(stage['start_time'].replace('Z', '+00:00'))
            stage['start_datetime'] = stage_time
            
            # Calculate end time
            if stage['duration_ms'] > 0:
                from datetime import timedelta
                end_time = stage_time + timedelta(milliseconds=stage['duration_ms'])
                if end_time > max_time:
                    max_time = end_time
        
        # Total timeline duration
        total_duration = (max_time - min_time).total_seconds() * 1000  # in ms
        timeline_width = 1200  # pixels
        
    except Exception as e:
        # Fallback to simple ordering
        return _generate_simple_timeline(sections)
    
    # Group stages by agent for lanes
    agent_lanes = {}
    for stage in all_stages:
        agent_key = stage['agent_type']
        if agent_key not in agent_lanes:
            agent_lanes[agent_key] = {
                'name': stage['agent_name'],
                'type': stage['agent_type'],
                'stages': []
            }
        agent_lanes[agent_key]['stages'].append(stage)
    
    # Order lanes: CMO -> Specialists -> Visualization
    specialist_lanes = [k for k in agent_lanes.keys() if k not in ['cmo', 'visualization']]
    
    # Generate timeline HTML
    timeline_html = []
    
    # Special handling for CMO - split into two rows
    if 'cmo' in agent_lanes:
        cmo_lane = agent_lanes['cmo']
        
        # Separate CMO stages into planning and synthesis
        planning_stages = []
        synthesis_stages = []
        
        for stage in cmo_lane['stages']:
            if 'synthesis' in stage['stage_name'].lower() or 'final_synthesis' in stage['stage_name'].lower():
                synthesis_stages.append(stage)
            else:
                planning_stages.append(stage)
        
        # Render CMO planning row
        if planning_stages:
            stages_html = []
            for stage in planning_stages:
                # Calculate position and width
                offset_ms = (stage['start_datetime'] - min_time).total_seconds() * 1000
                left_percent = (offset_ms / total_duration) * 100 if total_duration > 0 else 0
                
                # Limit bar width to prevent excessive scrolling
                raw_width = (stage['duration_ms'] / total_duration) * 100 if total_duration > 0 else 5
                width_percent = min(20, max(5, raw_width))  # Min 5%, Max 20%
                
                # Format stage name
                display_name = _format_stage_name(stage['stage_name'])
                
                # Create detailed hover info
                hover_info = _create_stage_hover_info(stage, display_name)
                
                # Determine stage status (completed stages have end_time)
                status_class = "success" if stage['stage_info'].end_time else ""
                
                stages_html.append(f"""
                <div class="timeline-stage-bar cmo {status_class}" 
                     style="left: {left_percent:.1f}%; width: {width_percent:.1f}%;"
                     title="{hover_info}"
                     data-stage-id="cmo-{stage['stage_name']}">
                    <div class="stage-bar-content">
                        <div class="stage-bar-name">{display_name}</div>
                        <div class="stage-bar-time">{format_duration(stage['duration_ms'])}</div>
                    </div>
                    <div class="stage-bar-hover">
                        <div class="hover-metric">🔵 {stage['stage_info'].llm_calls} LLM</div>
                        <div class="hover-metric">🔧 {stage['stage_info'].tool_calls} Tools</div>
                        <div class="hover-metric">🎯 {format_token_count(stage['stage_info'].tokens_used)}</div>
                    </div>
                </div>
                """)
            
            timeline_html.append(f"""
            <div class="timeline-lane-row">
                <div class="timeline-agent-label cmo">CMO - Planning</div>
                <div class="timeline-track">
                    {"".join(stages_html)}
                </div>
            </div>
            """)
    
    # Render specialist lanes (grouped together)
    if specialist_lanes:
        timeline_html.append('<div class="specialist-group">')
    
    for specialist_type in specialist_lanes:
        if specialist_type not in agent_lanes:
            continue
            
        lane = agent_lanes[specialist_type]
        stages_html = []
        
        for stage in lane['stages']:
            # Calculate position and width
            offset_ms = (stage['start_datetime'] - min_time).total_seconds() * 1000
            left_percent = (offset_ms / total_duration) * 100 if total_duration > 0 else 0
            
            # Limit bar width to prevent excessive scrolling
            raw_width = (stage['duration_ms'] / total_duration) * 100 if total_duration > 0 else 5
            width_percent = min(20, max(5, raw_width))  # Min 5%, Max 20%
            
            # Format stage name
            display_name = _format_stage_name(stage['stage_name'])
            
            # Create detailed hover info
            hover_info = _create_stage_hover_info(stage, display_name)
            
            # Determine stage status
            status_class = "success" if stage['stage_info'].end_time else ""
            
            stages_html.append(f"""
            <div class="timeline-stage-bar {specialist_type} {status_class}" 
                 style="left: {left_percent:.1f}%; width: {width_percent:.1f}%;"
                 title="{hover_info}"
                 data-stage-id="{specialist_type}-{stage['stage_name']}">
                <div class="stage-bar-content">
                    <div class="stage-bar-name">{display_name}</div>
                    <div class="stage-bar-time">{format_duration(stage['duration_ms'])}</div>
                </div>
                <div class="stage-bar-hover">
                    <div class="hover-metric">🔵 {stage['stage_info'].llm_calls} LLM</div>
                    <div class="hover-metric">🔧 {stage['stage_info'].tool_calls} Tools</div>
                    <div class="hover-metric">🎯 {format_token_count(stage['stage_info'].tokens_used)}</div>
                </div>
            </div>
            """)
        
        timeline_html.append(f"""
        <div class="timeline-lane-row">
            <div class="timeline-agent-label {specialist_type}">{lane['name']}</div>
            <div class="timeline-track">
                {"".join(stages_html)}
            </div>
        </div>
        """)
    
    # Close specialist group
    if specialist_lanes:
        timeline_html.append('</div>')
    
    # Render CMO synthesis row (after specialists)
    if 'cmo' in agent_lanes and synthesis_stages:
        stages_html = []
        for stage in synthesis_stages:
            # Calculate position and width
            offset_ms = (stage['start_datetime'] - min_time).total_seconds() * 1000
            left_percent = (offset_ms / total_duration) * 100 if total_duration > 0 else 0
            
            # Limit bar width to prevent excessive scrolling
            raw_width = (stage['duration_ms'] / total_duration) * 100 if total_duration > 0 else 5
            width_percent = min(20, max(5, raw_width))  # Min 5%, Max 20%
            
            # Format stage name
            display_name = _format_stage_name(stage['stage_name'])
            
            # Create detailed hover info
            hover_info = _create_stage_hover_info(stage, display_name)
            
            # Determine stage status
            status_class = "success" if stage['stage_info'].end_time else ""
            
            stages_html.append(f"""
            <div class="timeline-stage-bar cmo {status_class}" 
                 style="left: {left_percent:.1f}%; width: {width_percent:.1f}%;"
                 title="{hover_info}"
                 data-stage-id="cmo-{stage['stage_name']}">
                <div class="stage-bar-content">
                    <div class="stage-bar-name">{display_name}</div>
                    <div class="stage-bar-time">{format_duration(stage['duration_ms'])}</div>
                </div>
                <div class="stage-bar-hover">
                    <div class="hover-metric">🔵 {stage['stage_info'].llm_calls} LLM</div>
                    <div class="hover-metric">🔧 {stage['stage_info'].tool_calls} Tools</div>
                    <div class="hover-metric">🎯 {format_token_count(stage['stage_info'].tokens_used)}</div>
                </div>
            </div>
            """)
        
        timeline_html.append(f"""
        <div class="timeline-lane-row">
            <div class="timeline-agent-label cmo">CMO - Synthesis</div>
            <div class="timeline-track">
                {"".join(stages_html)}
            </div>
        </div>
        """)
    
    # Render visualization agent lane (if present)
    if 'visualization' in agent_lanes:
        lane = agent_lanes['visualization']
        stages_html = []
        
        for stage in lane['stages']:
            # Calculate position and width
            offset_ms = (stage['start_datetime'] - min_time).total_seconds() * 1000
            left_percent = (offset_ms / total_duration) * 100 if total_duration > 0 else 0
            
            # Limit bar width to prevent excessive scrolling
            raw_width = (stage['duration_ms'] / total_duration) * 100 if total_duration > 0 else 5
            width_percent = min(20, max(5, raw_width))  # Min 5%, Max 20%
            
            # Format stage name
            display_name = _format_stage_name(stage['stage_name'])
            
            # Create detailed hover info
            hover_info = _create_stage_hover_info(stage, display_name)
            
            # Determine stage status
            status_class = "success" if stage['stage_info'].end_time else ""
            
            stages_html.append(f"""
            <div class="timeline-stage-bar visualization {status_class}" 
                 style="left: {left_percent:.1f}%; width: {width_percent:.1f}%;"
                 title="{hover_info}"
                 data-stage-id="visualization-{stage['stage_name']}">
                <div class="stage-bar-content">
                    <div class="stage-bar-name">{display_name}</div>
                    <div class="stage-bar-time">{format_duration(stage['duration_ms'])}</div>
                </div>
                <div class="stage-bar-hover">
                    <div class="hover-metric">🔵 {stage['stage_info'].llm_calls} LLM</div>
                    <div class="hover-metric">🔧 {stage['stage_info'].tool_calls} Tools</div>
                    <div class="hover-metric">🎯 {format_token_count(stage['stage_info'].tokens_used)}</div>
                </div>
            </div>
            """)
        
        timeline_html.append(f"""
        <div class="timeline-lane-row">
            <div class="timeline-agent-label visualization">{lane['name']}</div>
            <div class="timeline-track">
                {"".join(stages_html)}
            </div>
        </div>
        """)
    
    # Add time axis
    time_markers = _generate_time_axis(min_time, max_time, timeline_width)
    
    return f"""
    <div class="timeline-section">
        <div class="timeline-header">
            <h2>📊 Execution Timeline</h2>
            <span style="font-size: 13px; color: #7f8c8d;">
                Showing actual execution times and durations (click stages to see relationships)
            </span>
        </div>
        <div class="timeline-container">
            <div class="timeline-legend">
                <div class="legend-item">
                    <div class="legend-color cmo"></div>
                    <span>CMO (Orchestrator)</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color specialist"></div>
                    <span>Medical Specialists</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color visualization"></div>
                    <span>Visualization Agent</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color flow"></div>
                    <span>Task Flow</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color critical"></div>
                    <span>Critical Path</span>
                </div>
            </div>
            <div class="timeline-wrapper">
                {time_markers}
                <div class="timeline-lanes">
                    {"".join(timeline_html)}
                </div>
            </div>
        </div>
    </div>
    """


def _create_stage_hover_info(stage: Dict[str, Any], display_name: str) -> str:
    """Create detailed hover information for a stage"""
    start_time = stage.get('start_time', 'N/A')
    end_time = stage['stage_info'].end_time or 'In Progress'
    tokens_per_sec = (stage['stage_info'].tokens_used / (stage['duration_ms'] / 1000)) if stage['duration_ms'] > 0 and stage['stage_info'].tokens_used > 0 else 0
    
    return f"""{display_name}
━━━━━━━━━━━━━━━━━━━━━
Duration: {format_duration(stage['duration_ms'])}
Start: {start_time.split('T')[1].split('.')[0] if 'T' in str(start_time) else start_time}
End: {end_time.split('T')[1].split('.')[0] if 'T' in str(end_time) else end_time}
━━━━━━━━━━━━━━━━━━━━━
LLM Calls: {stage['stage_info'].llm_calls}
Tool Calls: {stage['stage_info'].tool_calls}
Tokens: {format_token_count(stage['stage_info'].tokens_used)}
Speed: {tokens_per_sec:.0f} tokens/sec"""


def _format_stage_name(stage_name: str) -> str:
    """Format stage name for display"""
    name_map = {
        'query_analysis': 'Query Analysis',
        'task_creation': 'Task Creation',
        'synthesis': 'Synthesis',
        'final_synthesis': 'Final Synthesis',
        'analysis': 'Medical Analysis',
        'specialist_execution': 'Analysis',
        'medical_analysis': 'Medical Analysis',
        'findings_synthesis': 'Synthesis',
        'visualization_generation': 'Chart Generation',
        'visualization': 'Visualization'
    }
    return name_map.get(stage_name, stage_name.replace('_', ' ').title())


def _generate_time_axis(min_time, max_time, width: int) -> str:
    """Generate time axis markers"""
    duration = (max_time - min_time).total_seconds()
    
    # Determine appropriate interval
    if duration < 10:  # Less than 10 seconds
        interval = 1  # 1 second
    elif duration < 60:  # Less than 1 minute
        interval = 5  # 5 seconds
    elif duration < 300:  # Less than 5 minutes
        interval = 30  # 30 seconds
    else:
        interval = 60  # 1 minute
    
    markers = []
    current = 0
    while current <= duration:
        left_percent = (current / duration) * 100 if duration > 0 else 0
        label = f"{int(current)}s" if current < 60 else f"{current/60:.1f}m"
        markers.append(f'<div class="time-marker" style="left: {left_percent:.1f}%;">{label}</div>')
        current += interval
    
    return f'<div class="timeline-axis">{"".join(markers)}</div>'


def _generate_simple_timeline(sections: List[AgentSection]) -> str:
    """Fallback simple timeline if datetime parsing fails"""
    timeline_html = []
    
    for section in sections:
        if not section.stages:
            continue
            
        stages_html = []
        for stage_name, stage_info in section.stages.items():
            display_name = _format_stage_name(stage_name)
            stages_html.append(f"""
            <div class="timeline-stage {section.agent_type}">
                <div class="stage-name">{display_name}</div>
                <div class="stage-stats">
                    <span>⏱️ {format_duration(stage_info.duration_ms)}</span>
                    <span>🔵 {stage_info.llm_calls}</span>
                    <span>🔧 {stage_info.tool_calls}</span>
                </div>
            </div>
            """)
        
        timeline_html.append(f"""
        <div class="timeline-lane-row">
            <div class="timeline-agent-label {section.agent_type}">{section.agent_name}</div>
            <div class="timeline-stages">
                {"".join(stages_html)}
            </div>
        </div>
        """)
    
    return f"""
    <div class="timeline-section">
        <div class="timeline-header">
            <h2>📊 Execution Timeline</h2>
        </div>
        <div class="timeline-container">
            {"".join(timeline_html)}
        </div>
    </div>
    """


def _generate_agent_sections(sections: List[AgentSection]) -> str:
    """Generate agent sections with hierarchical events"""
    sections_html = []
    
    for i, section in enumerate(sections):
        agent_id = f"agent-{i}"
        agent_class = "cmo" if section.agent_type == "cmo" else "specialist"
        
        # Generate stage sections
        stages_html = []
        sorted_stages = sorted(section.stages.items(), key=lambda x: x[1].start_time or "")
        
        for idx, (stage_name, stage_info) in enumerate(sorted_stages):
            stage_id = f"{agent_id}-{stage_name.replace(' ', '-')}"
            stage_events_html = _generate_event_tree(stage_info.events, stage_id)
            
            # Determine if stage should be expanded by default
            is_synthesis = "synthesis" in stage_name.lower()
            is_final_stage = (idx == len(sorted_stages) - 1)
            has_errors = any(e.event.event_type == TraceEventType.ERROR for e in stage_info.events)
            
            # Expand synthesis stages, final stages, or stages with errors
            expand_by_default = is_synthesis or is_final_stage or has_errors
            
            stages_html.append(f"""
            <div class="stage-section">
                <div class="stage-header {'expanded' if expand_by_default else ''}" onclick="toggleStage(this)">
                    <h4>📍 {stage_name.replace('_', ' ').title()}</h4>
                    <div class="stage-meta">
                        <span>⏱️ {format_duration(stage_info.duration_ms)}</span>
                        <span>🔵 {stage_info.llm_calls} LLM calls</span>
                        <span>🔧 {stage_info.tool_calls} tool calls</span>
                        <span class="stage-toggle">{'▼' if expand_by_default else '▶'}</span>
                    </div>
                </div>
                <div class="stage-content {'show' if expand_by_default else ''}">
                    {stage_events_html}
                </div>
            </div>
            """)
        
        # Generate key findings if any
        findings_html = ""
        if section.key_findings:
            findings_items = "".join(
                f'<span class="finding-badge">{finding}</span>'
                for finding in section.key_findings[:5]
            )
            findings_html = f"""
            <div class="key-findings">
                <h4>Key Findings</h4>
                <div class="findings-list">
                    {findings_items}
                </div>
            </div>
            """
        
        # Create stages summary for header
        stages_summary = ", ".join(sorted(section.stages.keys()))
        
        sections_html.append(f"""
        <div class="agent-section">
            <div class="agent-header {agent_class}" id="{agent_id}-header" onclick="toggleAgent('{agent_id}')">
                <div class="agent-info">
                    <div class="agent-title">{section.agent_name}</div>
                    <div class="agent-meta">
                        <span>📋 Stages: {stages_summary}</span>
                        <span>⏱️ {format_duration(section.total_duration_ms)}</span>
                        <span>🔵 {section.llm_calls} LLM calls</span>
                        <span>🔧 {section.tool_calls} tool calls</span>
                        <span>🎯 {format_token_count(section.tokens_used)} tokens</span>
                    </div>
                </div>
                <div class="toggle-icon">▼</div>
            </div>
            <div class="agent-content" id="{agent_id}-content">
                {findings_html}
                <div class="stages-container">
                    {"".join(stages_html)}
                </div>
            </div>
        </div>
        """)
    
    return "\n".join(sections_html)


def _generate_event_tree(events: List[HierarchicalEvent], agent_id: str) -> str:
    """Generate hierarchical event tree"""
    html_parts = []
    
    for event in events:
        # Skip phantom events with Unknown stage
        if event.event.event_type in [TraceEventType.STAGE_START, TraceEventType.STAGE_END]:
            stage_name = event.event.data.get('stage', '') if event.event.data else ''
            if not stage_name or stage_name.lower() == 'unknown':
                continue
        
        html_parts.append(_generate_event_node(event, agent_id))
    
    return "\n".join(html_parts)


def _generate_event_node(event: HierarchicalEvent, agent_id: str) -> str:
    """Generate single event node with children"""
    event_id = f"{agent_id}-event-{event.event_index}"
    event_type = event.event.event_type.value.lower().replace('_', '-')
    
    # Generate event summary based on type
    summary = _generate_event_summary(event.event)
    
    # Generate detailed view
    details = _generate_event_details(event.event)
    
    # Generate children recursively
    children_html = ""
    if event.children:
        children_parts = []
        for child in event.children:
            children_parts.append(_generate_event_node(child, agent_id))
        children_html = "\n".join(children_parts)
    
    # Build the node
    connector = '<div class="event-connector"></div>' if event.level > 0 else ''
    
    return f"""
    <div class="event-node level-{event.level}">
        {connector}
        <div class="event-card {event_type}">
            <div class="event-header-row">
                <span class="event-type-badge {event_type}">
                    {_get_event_icon(event.event.event_type)} {event.event.event_type.value}
                </span>
                <div class="event-metadata">
                    <span>{event.event.timestamp}</span>
                    {f'<span>{format_duration(event.event.duration_ms)}</span>' if event.event.duration_ms else ''}
                    {f'<span>{format_token_count(event.event.tokens_used)} tokens</span>' if event.event.tokens_used else ''}
                    <button class="copy-btn" onclick="copyEventData('{event_id}')">📋</button>
                </div>
            </div>
            <div class="event-content">
                <div class="event-summary">
                    {summary}
                </div>
                <a class="show-details-btn" id="{event_id}-btn" onclick="toggleEventDetails('{event_id}')">
                    ▶ Show Details
                </a>
                <div class="event-details" id="{event_id}-details">
                    {details}
                </div>
                <div class="hidden" id="{event_id}-data">{json.dumps(event.event.data, indent=2)}</div>
            </div>
        </div>
        {children_html}
    </div>
    """


def _get_event_icon(event_type: TraceEventType) -> str:
    """Get icon for event type"""
    icons = {
        TraceEventType.USER_QUERY: "👤",
        TraceEventType.LLM_PROMPT: "📝",
        TraceEventType.LLM_RESPONSE: "💬",
        TraceEventType.TOOL_INVOCATION: "🔧",
        TraceEventType.TOOL_RESULT: "📊",
        TraceEventType.STAGE_START: "▶️",
        TraceEventType.STAGE_END: "⏹️",
        TraceEventType.ERROR: "❌"
    }
    return icons.get(event_type, "📌")


def _generate_event_summary(event: TraceEvent) -> str:
    """Generate human-readable event summary with highlighted data values"""
    data = event.data or {}
    
    if event.event_type == TraceEventType.LLM_PROMPT:
        prompt_file = data.get('prompt_file', 'Unknown')
        model = data.get('model', 'Unknown')
        return f"<strong>Prompt:</strong> {prompt_file} | <strong>Model:</strong> {model}"
        
    elif event.event_type == TraceEventType.LLM_RESPONSE:
        response_preview = truncate_text(data.get('response_text', ''), 150)
        tool_calls = data.get('tool_calls', [])
        if tool_calls:
            return f"<strong>Response:</strong> Requesting tools: {', '.join(tool_calls)}"
        else:
            return f"<strong>Response:</strong> {response_preview}"
            
    elif event.event_type == TraceEventType.TOOL_INVOCATION:
        tool_name = data.get('tool_name', 'Unknown')
        tool_input = data.get('tool_input', {})
        query = tool_input.get('query', '') if isinstance(tool_input, dict) else ''
        # Highlight the query
        highlighted_query = f'<span class="data-value">{query}</span>' if query else 'N/A'
        return f"<strong>Tool:</strong> {tool_name} | <strong>Query:</strong> {highlighted_query}"
        
    elif event.event_type == TraceEventType.TOOL_RESULT:
        success = data.get('success', False)
        result_data = data.get('result_data', {})
        if success and result_data:
            count = result_data.get('result_count', 0)
            # Extract and highlight key values
            results = result_data.get('results', [])
            if results and len(results) > 0:
                first_result = results[0]
                # Check for various health data types
                value_fields = [
                    ('GLUCOSE_VALUE', 'UNIT', 'glucose'),
                    ('VALUE_NUMERIC', 'MEASUREMENT_DIMENSION', 'numeric'),
                    ('SYSTOLIC_BP', 'UNIT', 'bp'),
                    ('HDL_CHOLESTEROL', 'UNIT', 'cholesterol'),
                    ('LDL_CHOLESTEROL', 'UNIT', 'cholesterol'),
                    ('HBA1C_VALUE', 'UNIT', 'hba1c')
                ]
                
                for value_field, unit_field, data_type in value_fields:
                    if value_field in first_result:
                        value = first_result.get(value_field)
                        unit = first_result.get(unit_field, '')
                        date = first_result.get('RECORD_DATE', '')
                        # Highlight the value with data type
                        highlighted_value = f'<span class="data-value data-{data_type}">{value} {unit}</span>'
                        return f"<strong>✅ Result:</strong> {highlighted_value} on {date} ({count} total results)"
                
            return f"<strong>✅ Success:</strong> <span class='data-value'>{count}</span> results found"
        else:
            error = data.get('error', 'Unknown error')
            return f"<strong>❌ Failed:</strong> {error}"
            
    elif event.event_type == TraceEventType.STAGE_START:
        stage = data.get('stage', 'Unknown')
        return f"<strong>Starting:</strong> {stage}"
        
    elif event.event_type == TraceEventType.STAGE_END:
        stage = data.get('stage', 'Unknown')
        return f"<strong>Completed:</strong> {stage}"
        
    else:
        return f"<strong>{event.event_type.value}:</strong> Event occurred"


def _generate_event_details(event: TraceEvent) -> str:
    """Generate detailed event view"""
    data = event.data or {}
    
    if event.event_type == TraceEventType.LLM_PROMPT:
        # Extract prompt components
        messages = data.get('messages', [])
        system_prompt = data.get('system_prompt', '')
        components = extract_prompt_components(messages, system_prompt)
        
        return f"""
        <div style="margin-top: 10px;">
            <strong>Current Prompt:</strong>
            <pre style="background: #f8f9fa; padding: 10px; border-radius: 4px; margin: 5px 0; font-size: 12px;">
{components['current_prompt']}</pre>
            
            {f'<strong>System Prompt:</strong><pre style="background: #f8f9fa; padding: 10px; border-radius: 4px; margin: 5px 0; font-size: 12px;">{system_prompt}</pre>' if system_prompt else ''}
            
            {f'<details><summary><strong>Conversation History ({components["history_size"]} messages)</strong></summary><pre style="background: #f8f9fa; padding: 10px; border-radius: 4px; margin: 5px 0; font-size: 12px;">{json.dumps(components["conversation_history"], indent=2)}</pre></details>' if components['history_size'] > 0 else ''}
        </div>
        """
        
    elif event.event_type == TraceEventType.TOOL_RESULT:
        # Show full tool results
        result_data = data.get('result_data', {})
        metadata = event.metadata or {}
        full_output = metadata.get('tool_output', result_data)
        
        return f"""
        <div style="margin-top: 10px;">
            <strong>Full Results:</strong>
            <pre style="background: #f8f9fa; padding: 10px; border-radius: 4px; margin: 5px 0; font-size: 12px; max-height: 300px; overflow-y: auto;">
{json.dumps(full_output, indent=2)}</pre>
        </div>
        """
        
    else:
        # Default detailed view
        return f"""
        <div style="margin-top: 10px;">
            <pre style="background: #f8f9fa; padding: 10px; border-radius: 4px; margin: 5px 0; font-size: 12px;">
{json.dumps(data, indent=2)}</pre>
        </div>
        """