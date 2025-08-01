"""
Hierarchical HTML generator for trace viewer.

Creates an intuitive, hierarchical view of trace events organized by
agents and showing clear parent-child relationships.
"""

import html
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
    
    # Generate HTML without QE panel
    html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Trace Analysis - {trace.trace_id}</title>
    <style>
        {_generate_css()}
        /* Remove QE-specific styles and adjust layout */
        body {{
            margin: 0;
            padding: 0;
        }}
        .main-layout {{
            display: block !important;
        }}
        .trace-panel {{
            width: 100% !important;
            border-left: none !important;
        }}
        .container {{
            max-width: 100%;
        }}
    </style>
    <script>
        console.log('[TIMELINE NAV DEBUGGING] Head script starting...');
        const TRACE_ID = '{trace.trace_id}';
        
        // Initialize trace viewer JavaScript only
        {_generate_javascript()}
        console.log('[TIMELINE NAV DEBUGGING] Head script completed.');
    </script>
</head>
<body>
    <div class="container">
        {_generate_header(trace, summary)}
        {_generate_filter_panel()}
        {_generate_summary_cards(sections, summary)}
        {_generate_timeline(sections)}
        {_generate_agent_analysis_section(sections)}
    </div>
</body>
</html>
    """
    
    return html


def generate_hierarchical_trace_html_embedded(trace: CompleteTrace, hideHeader: bool = False, hideFilters: bool = False) -> str:
    """
    Generate embedded hierarchical HTML view of trace without QE interface.
    
    Args:
        trace: Complete trace object
        hideHeader: Whether to hide the header section
        hideFilters: Whether to hide the filters panel
        
    Returns:
        Self-contained HTML string for embedding
    """
    # Build hierarchy
    sections, summary = build_trace_hierarchy(trace)
    
    # Generate HTML without QE panel
    html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Trace Analysis - {trace.trace_id}</title>
    <style>
        {_generate_css()}
        /* Embedded-specific styles */
        body {{
            background-color: white;
        }}
        .main-layout {{
            display: block !important;
        }}
        .trace-panel {{
            width: 100% !important;
            border-left: none !important;
        }}
        .container {{
            max-width: 100%;
            padding: 10px;
        }}
        {'' if not hideHeader else '.header { display: none; }'}
    </style>
    <script>
        const TRACE_ID = '{trace.trace_id}';
        
        // Initialize trace viewer JavaScript (without QE functionality)
        {_generate_javascript()}
    </script>
</head>
<body>
    <div class="main-layout">
        <div class="trace-panel">
            <div class="container">
                {_generate_header(trace, summary) if not hideHeader else ''}
                {_generate_filter_panel() if not hideFilters else ''}
                {_generate_summary_cards(sections, summary)}
                {_generate_timeline(sections)}
                {_generate_agent_analysis_section(sections)}
            </div>
        </div>
    </div>
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
        
        /* Compact Header for Embedded View */
        .compact-header {
            background-color: #f8f9fa;
            border-bottom: 1px solid #e9ecef;
            padding: 8px 20px;
            margin-bottom: 20px;
        }
        
        .trace-info {
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 0.875rem;
        }
        
        .trace-id {
            font-weight: 600;
            color: #495057;
        }
        
        .trace-meta {
            color: #6c757d;
        }
        
        /* Filter Panel Container */
        .filter-panel-container {
            background: white;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
            overflow: hidden;
        }
        
        .filter-panel-header {
            padding: 15px 20px;
            cursor: pointer;
            user-select: none;
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: #f8f9fa;
            border-bottom: 1px solid #e9ecef;
            transition: background-color 0.2s;
        }
        
        .filter-panel-header:hover {
            background: #e9ecef;
        }
        
        .filter-panel-title {
            font-weight: 600;
            color: #2c3e50;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .collapse-icon {
            transition: transform 0.3s;
            display: inline-block;
        }
        
        .collapse-icon.rotated {
            transform: rotate(-90deg);
        }
        
        .filter-panel-summary {
            font-size: 14px;
            color: #6c757d;
        }
        
        /* Filter Panel */
        .filter-panel {
            padding: 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 15px;
            transition: max-height 0.3s ease-out, opacity 0.3s;
            max-height: 500px;
            opacity: 1;
        }
        
        .filter-panel.collapsed {
            max-height: 0;
            opacity: 0;
            padding: 0 20px;
            overflow: hidden;
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
        
        .filter-preset {
            padding: 6px 12px;
            border: 1px solid #dee2e6;
            border-radius: 4px;
            background: white;
            color: #495057;
            font-size: 13px;
            cursor: pointer;
            transition: all 0.2s;
        }
        
        .filter-preset:hover {
            background: #e9ecef;
            border-color: #adb5bd;
        }
        
        .filter-preset.reset {
            background: #f8f9fa;
            color: #dc3545;
            border-color: #dc3545;
        }
        
        .filter-preset.reset:hover {
            background: #dc3545;
            color: white;
        }
        
        .filter-status {
            font-size: 13px;
            color: #6c757d;
            font-style: italic;
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
        
        /* Performance-based color coding */
        .summary-card.performance-good .value {
            color: #2ecc71;
        }
        
        .summary-card.performance-warning .value {
            color: #f39c12;
        }
        
        .summary-card.performance-critical .value {
            color: #e74c3c;
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
            flex-wrap: wrap;
            gap: 15px;
        }
        
        /* Zoom controls */
        .zoom-controls {
            display: flex;
            align-items: center;
            gap: 10px;
            background: #f8f9fa;
            padding: 5px 10px;
            border-radius: 6px;
        }
        
        .zoom-controls button {
            background: white;
            border: 1px solid #dee2e6;
            border-radius: 4px;
            padding: 4px 8px;
            cursor: pointer;
            font-size: 14px;
            transition: all 0.2s;
        }
        
        .zoom-controls button:hover {
            background: #e9ecef;
            border-color: #adb5bd;
        }
        
        .zoom-controls button:active {
            transform: scale(0.95);
        }
        
        .zoom-level {
            font-size: 13px;
            color: #6c757d;
            min-width: 50px;
            text-align: center;
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
            cursor: pointer;
            transition: all 0.2s;
        }
        
        .timeline-agent-label:hover {
            background: #e9ecef;
            transform: translateX(5px);
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        
        .timeline-agent-label.cmo {
            border-left-color: #e74c3c;
            background: #fee;
        }
        
        .timeline-agent-label.cardiology,
        .timeline-agent-label.endocrinology,
        .timeline-agent-label.laboratory_medicine,
        .timeline-agent-label.pharmacy,
        .timeline-agent-label.nutrition,
        .timeline-agent-label.preventive_medicine {
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
        
        /* Removed CSS tooltip - using JS tooltip for better control */
        
        .timeline-stage-bar.cmo {
            background: #e74c3c;
            border: 1px solid #c0392b;
        }
        
        .timeline-stage-bar.cardiology,
        .timeline-stage-bar.endocrinology,
        .timeline-stage-bar.laboratory_medicine,
        .timeline-stage-bar.pharmacy,
        .timeline-stage-bar.nutrition,
        .timeline-stage-bar.preventive_medicine {
            background: #2ecc71;
            border: 1px solid #27ae60;
        }
        
        .timeline-stage-bar.visualization {
            background: #9b59b6;
            border: 1px solid #8e44ad;
        }
        
        /* Anomaly detection - unusually long stages */
        .timeline-stage-bar.anomaly {
            border: 3px solid #e74c3c !important;
            box-shadow: 0 0 10px rgba(231, 76, 60, 0.5);
        }
        
        .timeline-stage-bar.anomaly .stage-bar-content::before {
            content: '⚠️';
            position: absolute;
            top: -15px;
            right: 5px;
            font-size: 12px;
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
        
        /* Execution order badge */
        .execution-order {
            position: absolute;
            top: -8px;
            left: -8px;
            background: #2c3e50;
            color: white;
            width: 20px;
            height: 20px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 10px;
            font-weight: bold;
            border: 2px solid white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
            z-index: 10;
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
            position: relative;
            overflow: visible;
        }
        
        .timeline-stage-bar.running::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            height: 100%;
            width: 100%;
            background: linear-gradient(90deg, 
                rgba(255,255,255,0) 0%, 
                rgba(255,255,255,0.3) 50%, 
                rgba(255,255,255,0) 100%);
            animation: shimmer 2s infinite;
        }
        
        @keyframes shimmer {
            0% { transform: translateX(-100%); }
            100% { transform: translateX(100%); }
        }
        
        /* Progress indicator for incomplete stages */
        .progress-indicator {
            position: absolute;
            bottom: -20px;
            left: 0;
            width: 100%;
            height: 3px;
            background: rgba(0,0,0,0.1);
            border-radius: 2px;
            overflow: hidden;
        }
        
        .progress-bar {
            height: 100%;
            background: #3498db;
            animation: progress 3s infinite;
            border-radius: 2px;
        }
        
        @keyframes progress {
            0% { width: 0%; }
            50% { width: 80%; }
            100% { width: 100%; }
        }
        
        @keyframes pulse {
            0% { opacity: 1; box-shadow: 0 2px 8px rgba(0,0,0,0.15); }
            50% { opacity: 0.8; box-shadow: 0 2px 12px rgba(0,0,0,0.25); }
            100% { opacity: 1; box-shadow: 0 2px 8px rgba(0,0,0,0.15); }
        }
        
        @keyframes flash {
            0%, 100% { background-color: inherit; }
            50% { background-color: #fff3cd; }
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
            animation: pulse-highlight 1.5s infinite;
        }
        
        @keyframes pulse-highlight {
            0% { box-shadow: 0 0 10px currentColor; }
            50% { box-shadow: 0 0 20px currentColor, 0 0 30px currentColor; }
            100% { box-shadow: 0 0 10px currentColor; }
        }
        
        .timeline-stage-bar.dimmed {
            opacity: 0.2 !important;
            filter: grayscale(50%);
        }
        
        .timeline-stage-bar.related {
            opacity: 0.8 !important;
            border-width: 3px;
            animation: glow 2s ease-in-out infinite;
        }
        
        @keyframes glow {
            0%, 100% { opacity: 0.8; }
            50% { opacity: 1; }
        }
        
        /* Relationship indicators */
        .relationship-label {
            position: absolute;
            background: rgba(0, 0, 0, 0.8);
            color: white;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 11px;
            z-index: 100;
            pointer-events: none;
            white-space: nowrap;
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
        
        /* Agent Metrics Table */
        .agent-metrics-table {
            width: 100%;
            border-collapse: collapse;
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }
        
        .agent-metrics-table thead {
            background: #f8f9fa;
            border-bottom: 2px solid #e9ecef;
        }
        
        .agent-metrics-table th {
            padding: 12px 15px;
            text-align: left;
            font-weight: 600;
            color: #2c3e50;
            font-size: 13px;
            cursor: pointer;
            user-select: none;
            position: relative;
            white-space: nowrap;
        }
        
        .agent-metrics-table th:hover {
            background: #e9ecef;
        }
        
        .agent-metrics-table th.sortable::after {
            content: '↕';
            position: absolute;
            right: 10px;
            color: #bdc3c7;
            font-size: 11px;
        }
        
        .agent-metrics-table th.sorted-asc::after {
            content: '↑';
            color: #3498db;
        }
        
        .agent-metrics-table th.sorted-desc::after {
            content: '↓';
            color: #3498db;
        }
        
        .agent-metrics-table tbody tr {
            border-bottom: 1px solid #f1f1f1;
            transition: background 0.2s;
        }
        
        .agent-metrics-table tbody tr:hover {
            background: #f8f9fa;
        }
        
        .agent-metrics-table td {
            padding: 10px 15px;
            font-size: 13px;
            color: #2c3e50;
        }
        
        .agent-metrics-table .agent-name-cell {
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .agent-type-indicator {
            width: 4px;
            height: 20px;
            border-radius: 2px;
            background: #3498db;
        }
        
        .agent-type-indicator.cmo {
            background: #e74c3c;
        }
        
        .agent-type-indicator.specialist {
            background: #2ecc71;
        }
        
        .agent-type-indicator.visualization {
            background: #9b59b6;
        }
        
        .duration-cell {
            font-weight: 500;
        }
        
        .duration-cell.fast {
            color: #2ecc71;
        }
        
        .duration-cell.medium {
            color: #f39c12;
        }
        
        .duration-cell.slow {
            color: #e74c3c;
        }
        
        .metric-value {
            font-weight: 500;
        }
        
        .efficiency-value {
            color: #3498db;
            font-weight: 600;
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
        
        /* Formatted content styles */
        .formatted-response {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }
        
        .task-card {
            transition: box-shadow 0.3s ease;
        }
        
        .task-card:hover {
            box-shadow: 0 2px 10px rgba(0,0,0,0.1) !important;
        }
        
        .format-toggle button {
            transition: all 0.2s ease;
        }
        
        .format-toggle button:hover {
            background: #f8f9fa !important;
            border-color: #adb5bd !important;
        }
        
        .query-results table {
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        
        .query-results th {
            font-weight: 600;
            color: #2c3e50;
        }
        
        .data-value {
            color: #3498db;
            font-weight: 500;
        }
    """


def _generate_javascript() -> str:
    """Generate JavaScript for interactivity"""
    return """
        console.log('[TIMELINE NAV DEBUGGING] Script block executing...');
        
        // Smart content formatter
        function formatEventData(data, container) {
            try {
                const parsed = typeof data === 'string' ? JSON.parse(data) : data;
                
                // Check if it has response_text field that needs special formatting
                if (parsed.response_text) {
                    container.innerHTML = formatResponseText(parsed);
                } else if (parsed.tool_name || parsed.tool_input) {
                    container.innerHTML = formatToolData(parsed);
                } else if (parsed.results && Array.isArray(parsed.results)) {
                    container.innerHTML = formatQueryResults(parsed);
                } else {
                    // Default JSON formatting
                    container.innerHTML = formatJSON(parsed);
                }
            } catch (e) {
                // Fallback to raw display
                container.innerHTML = `<pre style="background: #f8f9fa; padding: 10px; border-radius: 4px; margin: 5px 0; font-size: 12px; white-space: pre-wrap; word-wrap: break-word; overflow-wrap: break-word; max-width: 100%; max-height: 500px; overflow-y: auto;">${escapeHtml(data)}</pre>`;
            }
        }
        
        function formatResponseText(data) {
            let html = '<div class="formatted-response">';
            
            // Show response text with proper formatting
            const responseText = data.response_text;
            
            // Check for different response types
            if (responseText.includes('<initial_assessment>') && responseText.includes('</initial_assessment>')) {
                // Format initial assessment response
                html += formatInitialAssessment(responseText);
            } else if ((responseText.includes('<tasks>') && responseText.includes('</tasks>')) || 
                (responseText.includes('endocrinology\\n') || responseText.includes('laboratory_medicine\\n') || 
                 responseText.includes('nutrition\\n') || responseText.includes('cardiology\\n') ||
                 responseText.includes('pharmacy\\n') || responseText.includes('preventive_medicine\\n'))) {
                html += formatTaskResponse(responseText);
            } else {
                // Regular text formatting
                html += formatTextContent(responseText);
            }
            
            // Add metadata
            html += '<div class="response-metadata" style="margin-top: 15px; padding-top: 15px; border-top: 1px solid #e9ecef;">';
            if (data.model) {
                html += `<span class="metadata-item"><strong>Model:</strong> ${data.model}</span>`;
            }
            if (data.usage) {
                html += `<span class="metadata-item" style="margin-left: 20px;"><strong>Tokens:</strong> ${data.usage.total_tokens || 0}</span>`;
            }
            if (data.stop_reason) {
                html += `<span class="metadata-item" style="margin-left: 20px;"><strong>Stop:</strong> ${data.stop_reason}</span>`;
            }
            html += '</div>';
            
            html += '</div>';
            return html;
        }
        
        function formatInitialAssessment(text) {
            let html = '<div class="initial-assessment">';
            
            // Extract and format the reflection if present
            const reflectionMatch = text.match(/<search_quality_reflection>([\\s\\S]*?)<\\/search_quality_reflection>/);
            if (reflectionMatch) {
                html += '<div class="assessment-section" style="margin-bottom: 20px;">';
                html += '<h4 style="color: #2c3e50; margin-bottom: 10px;">🔍 Search Quality Reflection</h4>';
                html += formatTextContent(reflectionMatch[1].trim());
                html += '</div>';
            }
            
            // Extract and highlight the quality score
            const scoreMatch = text.match(/<search_quality_score>(\\d+)<\\/search_quality_score>/);
            if (scoreMatch) {
                const score = parseInt(scoreMatch[1]);
                const scoreColor = score >= 4 ? '#27ae60' : score >= 3 ? '#f39c12' : '#e74c3c';
                html += `<div class="quality-score" style="margin-bottom: 20px;">
                    <span style="font-weight: bold;">Quality Score: </span>
                    <span style="background: ${scoreColor}; color: white; padding: 4px 12px; border-radius: 20px; font-weight: bold;">
                        ${score}/5
                    </span>
                </div>`;
            }
            
            // Extract complexity level
            const complexityMatch = text.match(/<complexity>([^<]+)<\\/complexity>/);
            if (complexityMatch) {
                const complexity = complexityMatch[1].trim();
                const complexityColors = {
                    'SIMPLE': '#3498db',
                    'STANDARD': '#9b59b6',
                    'COMPLEX': '#e67e22',
                    'COMPREHENSIVE': '#e74c3c'
                };
                const color = complexityColors[complexity] || '#95a5a6';
                html += `<div class="complexity-level" style="margin-bottom: 20px;">
                    <span style="font-weight: bold;">Complexity: </span>
                    <span style="background: ${color}; color: white; padding: 4px 12px; border-radius: 20px; font-weight: bold;">
                        ${complexity}
                    </span>
                </div>`;
            }
            
            // Extract and format key findings
            const findingsMatch = text.match(/<key_findings>([\\s\\S]*?)<\\/key_findings>/);
            if (findingsMatch) {
                html += '<div class="key-findings" style="margin-bottom: 20px;">';
                html += '<h4 style="color: #2c3e50; margin-bottom: 10px;">📊 Key Findings</h4>';
                const findings = findingsMatch[1].trim();
                // Check if findings are bullet points
                if (findings.includes('\\n-') || findings.includes('\\n•')) {
                    html += formatList(findings);
                } else {
                    html += formatTextContent(findings);
                }
                html += '</div>';
            }
            
            // Show any remaining content
            const remainingText = text
                .replace(/<search_quality_reflection>[\\s\\S]*?<\\/search_quality_reflection>/g, '')
                .replace(/<search_quality_score>[\\s\\S]*?<\\/search_quality_score>/g, '')
                .replace(/<initial_assessment>[\\s\\S]*?<\\/initial_assessment>/g, '')
                .replace(/<complexity>[\\s\\S]*?<\\/complexity>/g, '')
                .replace(/<key_findings>[\\s\\S]*?<\\/key_findings>/g, '')
                .trim();
            
            if (remainingText) {
                html += '<div class="additional-content" style="margin-top: 20px; padding-top: 20px; border-top: 1px solid #e9ecef;">';
                html += formatTextContent(remainingText);
                html += '</div>';
            }
            
            html += '</div>';
            return html;
        }
        
        function formatTaskResponse(text) {
            let html = '<div class="task-response">';
            
            console.log('formatTaskResponse called, text includes <tasks>:', text.includes('<tasks>'));
            console.log('Text first 200 chars:', text.substring(0, 200));
            
            // Check if it's XML format
            if (text.includes('<tasks>') && text.includes('</tasks>')) {
                console.log('XML format detected');
                
                // Extract intro text
                const introMatch = text.match(/^([\\s\\S]*?)<tasks>/);
                if (introMatch) {
                    html += formatTextContent(introMatch[1].trim());
                }
                
                // Parse XML tasks
                const tasksMatch = text.match(/<tasks>([\\s\\S]*?)<\\/tasks>/);
                if (tasksMatch) {
                    console.log('Tasks XML found');
                    const tasksXml = tasksMatch[1];
                    const tasks = parseTasksXML(tasksXml);
                    
                    console.log('Parsed tasks count:', tasks.length);
                    
                    html += '<div class="tasks-container" style="margin-top: 15px;">';
                    tasks.forEach((task, index) => {
                        html += formatTaskCard(task, index + 1);
                    });
                    html += '</div>';
                } else {
                    console.log('No tasks XML match found');
                }
            } else {
                // Try to parse the non-XML format
                const tasks = parseNonXMLTasks(text);
                if (tasks.length > 0) {
                    // Extract intro text (everything before first specialist name or task emoji)
                    const firstTaskIndex = Math.min(
                        text.indexOf('\\nendocrinology\\n') >= 0 ? text.indexOf('\\nendocrinology\\n') : Infinity,
                        text.indexOf('\\nlaboratory_medicine\\n') >= 0 ? text.indexOf('\\nlaboratory_medicine\\n') : Infinity,
                        text.indexOf('\\nnutrition\\n') >= 0 ? text.indexOf('\\nnutrition\\n') : Infinity,
                        text.indexOf('\\npharmacy\\n') >= 0 ? text.indexOf('\\npharmacy\\n') : Infinity,
                        text.indexOf('\\ncardiology\\n') >= 0 ? text.indexOf('\\ncardiology\\n') : Infinity,
                        text.indexOf('\\npreventive_medicine\\n') >= 0 ? text.indexOf('\\npreventive_medicine\\n') : Infinity,
                        text.indexOf('👨‍⚕️ Task') >= 0 ? text.indexOf('👨‍⚕️ Task') : Infinity
                    );
                    
                    if (firstTaskIndex > 0 && firstTaskIndex < Infinity) {
                        html += formatTextContent(text.substring(0, firstTaskIndex).trim());
                    }
                    
                    html += '<div class="tasks-container" style="margin-top: 15px;">';
                    tasks.forEach((task, index) => {
                        html += formatTaskCard(task, index + 1);
                    });
                    html += '</div>';
                } else {
                    // Fallback to regular text formatting
                    html += formatTextContent(text);
                }
            }
            
            html += '</div>';
            return html;
        }
        
        function parseNonXMLTasks(text) {
            const tasks = [];
            
            console.log('parseNonXMLTasks called with text length:', text.length);
            console.log('First 500 chars:', text.substring(0, 500));
            
            // First try the format with specialist names followed by task details
            const specialistPattern = /\\n\\s*(endocrinology|laboratory_medicine|nutrition|cardiology|pharmacy|preventive_medicine)\\s*\\n([\\s\\S]*?)(?=\\n\\s*(?:endocrinology|laboratory_medicine|nutrition|cardiology|pharmacy|preventive_medicine)\\s*\\n|$)/gi;
            const specialistMatches = Array.from(text.matchAll(specialistPattern));
            
            console.log('Specialist matches found:', specialistMatches.length);
            
            if (specialistMatches.length > 0) {
                // Parse specialist-based format
                for (const match of specialistMatches) {
                    const specialist = match[1].toLowerCase();
                    const taskContent = match[2].trim();
                    const lines = taskContent.split('\\n').map(line => line.trim()).filter(line => line);
                    
                    console.log('Processing specialist:', specialist);
                    console.log('Task lines:', lines);
                    
                    const task = {
                        specialist: specialist,
                        objective: '',
                        context: '',
                        expected_output: '',
                        priority: '',
                        tool_queries: []
                    };
                    
                    // Parse the content more carefully
                    // The format appears to be:
                    // objective (first non-empty line)
                    // context (second non-empty line)
                    // expected_output (marked with <expected_output> tags or third line)
                    // priority (single digit on its own line)
                    // tool_queries (marked with <tool_queries> tags or lines starting with -)
                    
                    let fullContent = taskContent;
                    
                    // Check for XML-style tags within the content
                    const objectiveMatch = fullContent.match(/<objective>([\\s\\S]*?)<\\/objective>/);
                    const contextMatch = fullContent.match(/<context>([\\s\\S]*?)<\\/context>/);
                    const expectedOutputMatch = fullContent.match(/<expected_output>([\\s\\S]*?)<\\/expected_output>/);
                    const priorityMatch = fullContent.match(/<priority>(\\d+)<\\/priority>/) || fullContent.match(/\\n\\s*(\\d)\\s*\\n/);
                    const toolQueriesMatch = fullContent.match(/<tool_queries>([\\s\\S]*?)<\\/tool_queries>/);
                    
                    if (objectiveMatch) {
                        task.objective = objectiveMatch[1].trim();
                    } else if (lines.length > 0) {
                        task.objective = lines[0];
                    }
                    
                    if (contextMatch) {
                        task.context = contextMatch[1].trim();
                    } else if (lines.length > 1) {
                        task.context = lines[1];
                    }
                    
                    if (expectedOutputMatch) {
                        task.expected_output = expectedOutputMatch[1].trim();
                    } else {
                        // Look for lines between context and priority
                        let i = 2;
                        while (i < lines.length && !lines[i].match(/^\\d+$/)) {
                            if (!lines[i].startsWith('-') && !lines[i].startsWith('"')) {
                                task.expected_output += (task.expected_output ? ' ' : '') + lines[i];
                            } else {
                                break;
                            }
                            i++;
                        }
                    }
                    
                    if (priorityMatch) {
                        task.priority = priorityMatch[1];
                    }
                    
                    if (toolQueriesMatch) {
                        const queries = toolQueriesMatch[1].trim().split('\\n');
                        queries.forEach(query => {
                            const cleaned = query.replace(/^[-•*"']\\s*|["']$/g, '').trim();
                            if (cleaned) {
                                task.tool_queries.push(cleaned);
                            }
                        });
                    } else {
                        // Look for lines that look like queries (starting with - or quotes)
                        lines.forEach(line => {
                            if (line.match(/^[-"']/) || line.includes('show') || line.includes('calculate') || line.includes('plot') || line.includes('determine')) {
                                const cleaned = line.replace(/^[-•*"']\\s*|["']$/g, '').trim();
                                if (cleaned) {
                                    task.tool_queries.push(cleaned);
                                }
                            }
                        });
                    }
                    
                    tasks.push(task);
                }
            } else {
                // Try the emoji-based format (👨‍⚕️ Task N:)
                const taskPattern = /👨‍⚕️\\s*Task\\s*\\d+:([\\s\\S]*?)(?=👨‍⚕️\\s*Task\\s*\\d+:|$)/g;
                const matches = text.matchAll(taskPattern);
                
                for (const match of matches) {
                    const taskContent = match[1].trim();
                    const task = {
                        specialist: '',
                        objective: '',
                        context: '',
                        expected_output: '',
                        priority: '',
                        tool_queries: []
                    };
                    
                    // Parse fields from the task content
                    const lines = taskContent.split('\\n');
                    let currentField = '';
                    
                    for (const line of lines) {
                        const trimmed = line.trim();
                        
                        // Check for field labels
                        if (trimmed.match(/^Priority\\s*\\d*$/)) {
                            currentField = 'priority';
                            const priorityMatch = trimmed.match(/Priority\\s*(\\d+)/);
                            if (priorityMatch) {
                                task.priority = priorityMatch[1];
                            }
                        } else if (trimmed.startsWith('Objective:')) {
                            currentField = 'objective';
                            const value = trimmed.substring('Objective:'.length).trim();
                            if (value) task.objective = value;
                        } else if (trimmed.startsWith('Context:')) {
                            currentField = 'context';
                            const value = trimmed.substring('Context:'.length).trim();
                            if (value) task.context = value;
                        } else if (trimmed.startsWith('Expected Output:')) {
                            currentField = 'expected_output';
                            const value = trimmed.substring('Expected Output:'.length).trim();
                            if (value) task.expected_output = value;
                        } else if (trimmed.startsWith('Tool Queries:')) {
                            currentField = 'tool_queries';
                        } else if (currentField === 'tool_queries' && trimmed) {
                            task.tool_queries.push(trimmed.replace(/^[-•*]\\s*/, ''));
                        } else if (currentField && trimmed && currentField !== 'tool_queries') {
                            task[currentField] = (task[currentField] ? task[currentField] + ' ' : '') + trimmed;
                        }
                    }
                    
                    // Set default priority if not found
                    if (!task.priority) {
                        task.priority = '2';
                    }
                    
                    tasks.push(task);
                }
            }
            
            return tasks;
        }
        
        function parseTasksXML(xml) {
            console.log('parseTasksXML called');
            const tasks = [];
            
            // Create a temporary DOM parser to handle the XML properly
            const parser = new DOMParser();
            const xmlDoc = parser.parseFromString('<root>' + xml + '</root>', 'text/xml');
            
            const taskElements = xmlDoc.getElementsByTagName('task');
            console.log('Found task elements:', taskElements.length);
            
            for (let i = 0; i < taskElements.length; i++) {
                const taskElement = taskElements[i];
                
                const task = {
                    specialist: getElementText(taskElement, 'specialist'),
                    objective: getElementText(taskElement, 'objective'),
                    context: getElementText(taskElement, 'context'),
                    expected_output: getElementText(taskElement, 'expected_output'),
                    priority: getElementText(taskElement, 'priority'),
                    tool_queries: extractToolQueriesFromElement(taskElement)
                };
                
                console.log('Parsed task:', task);
                tasks.push(task);
            }
            
            console.log('Total tasks parsed:', tasks.length);
            return tasks;
        }
        
        function getElementText(parent, tagName) {
            const element = parent.getElementsByTagName(tagName)[0];
            return element ? element.textContent.trim() : '';
        }
        
        function extractToolQueriesFromElement(taskElement) {
            const toolQueriesElement = taskElement.getElementsByTagName('tool_queries')[0];
            if (!toolQueriesElement) return [];
            
            const queries = [];
            const text = toolQueriesElement.textContent;
            const lines = text.split('\\n');
            
            lines.forEach(line => {
                const cleaned = line.trim();
                if (cleaned.startsWith('-')) {
                    const query = cleaned.substring(1).trim().replace(/^["']|["']$/g, '');
                    if (query) queries.push(query);
                }
            });
            
            return queries;
        }
        
        function extractXMLValue(xml, tag) {
            console.log(`Extracting ${tag} from:`, xml.substring(0, 100));
            const regex = new RegExp(`<${tag}>([\\s\\S]*?)<\\/${tag}>`, 'i');
            const match = xml.match(regex);
            console.log(`Match for ${tag}:`, match);
            const value = match ? match[1].trim() : '';
            console.log(`Extracted ${tag}:`, value);
            return value;
        }
        
        function extractToolQueries(xml) {
            const queriesMatch = xml.match(/<tool_queries>([\\s\\S]*?)<\\/tool_queries>/);
            if (!queriesMatch) {
                console.log('No tool_queries match found');
                return [];
            }
            
            console.log('Tool queries content:', queriesMatch[1]);
            
            const queries = [];
            const lines = queriesMatch[1].split('\\n');
            lines.forEach(line => {
                const cleaned = line.trim();
                if (cleaned.startsWith('-')) {
                    const query = cleaned.substring(1).trim().replace(/^["']|["']$/g, '');
                    console.log('Adding query:', query);
                    queries.push(query);
                }
            });
            
            console.log('Total queries extracted:', queries.length);
            return queries;
        }
        
        function formatTaskCard(task, number) {
            console.log('formatTaskCard called with task:', task);
            console.log('Task specialist:', task.specialist);
            console.log('Task objective:', task.objective);
            console.log('Task context:', task.context);
            console.log('Task priority:', task.priority);
            
            const priorityColors = {
                '1': '#e74c3c',
                '2': '#f39c12',
                '3': '#3498db'
            };
            
            const specialistEmojis = {
                'endocrinology': '🔬',
                'nutrition': '🥗',
                'laboratory_medicine': '🧪',
                'cardiology': '❤️',
                'pharmacy': '💊',
                'preventive_medicine': '🛡️'
            };
            
            const emoji = specialistEmojis[task.specialist] || '👨‍⚕️';
            const priorityColor = priorityColors[task.priority] || '#95a5a6';
            
            let html = `
                <div class="task-card" style="border: 1px solid #e9ecef; border-radius: 8px; padding: 15px; margin-bottom: 15px; background: #f8f9fa;">
                    <div class="task-header" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                        <h4 style="margin: 0; color: #2c3e50; font-size: 16px;">
                            ${emoji} Task ${number}: ${capitalizeFirst(task.specialist)}
                        </h4>
                        <span class="priority-badge" style="background: ${priorityColor}; color: white; padding: 2px 8px; border-radius: 12px; font-size: 12px;">
                            Priority ${task.priority || '?'}
                        </span>
                    </div>
                    
                    <div class="task-content">
                        <div class="task-field" style="margin-bottom: 10px;">
                            <strong style="color: #7f8c8d;">Objective:</strong>
                            <div style="margin-left: 10px; color: #2c3e50;">${task.objective || '<em style="color: #999;">Not specified</em>'}</div>
                        </div>
                        
                        <div class="task-field" style="margin-bottom: 10px;">
                            <strong style="color: #7f8c8d;">Context:</strong>
                            <div style="margin-left: 10px; color: #34495e; font-size: 13px;">${task.context || '<em style="color: #999;">Not specified</em>'}</div>
                        </div>
                        
                        <div class="task-field" style="margin-bottom: 10px;">
                            <strong style="color: #7f8c8d;">Expected Output:</strong>
                            <div style="margin-left: 10px; color: #27ae60; font-size: 13px;">${task.expected_output || '<em style="color: #999;">Not specified</em>'}</div>
                        </div>
            `;
            
            if (task.tool_queries && task.tool_queries.length > 0) {
                html += `
                        <div class="task-field">
                            <strong style="color: #7f8c8d;">Tool Queries:</strong>
                            <ul style="margin: 5px 0 0 20px; padding-left: 20px;">
                `;
                task.tool_queries.forEach(query => {
                    html += `<li style="color: #3498db; font-size: 13px; font-family: monospace;">${escapeHtml(query)}</li>`;
                });
                html += `
                            </ul>
                        </div>
                `;
            }
            
            html += `
                    </div>
                </div>
            `;
            
            return html;
        }
        
        function formatTextContent(text) {
            // Convert newlines to proper formatting
            let formatted = escapeHtml(text);
            
            // Convert double newlines to paragraphs
            const paragraphs = formatted.split('\\n\\n');
            let html = '';
            
            paragraphs.forEach(para => {
                if (para.trim()) {
                    // Check if it's a list
                    if (para.includes('\\n-') || para.includes('\\n•') || para.includes('\\n*')) {
                        html += formatList(para);
                    } else {
                        html += `<p style="margin: 10px 0;">${para.replace(/\\n/g, '<br>')}</p>`;
                    }
                }
            });
            
            return html;
        }
        
        function formatList(text) {
            const lines = text.split('\\n');
            let html = '<ul style="margin: 10px 0;">';
            let inList = false;
            
            lines.forEach(line => {
                const trimmed = line.trim();
                if (trimmed.startsWith('-') || trimmed.startsWith('•') || trimmed.startsWith('*')) {
                    inList = true;
                    html += `<li>${trimmed.substring(1).trim()}</li>`;
                } else if (inList && trimmed) {
                    // Continuation of previous list item
                    html = html.replace(/<\\/li>$/, ' ' + trimmed + '</li>');
                }
            });
            
            html += '</ul>';
            return html;
        }
        
        function formatToolData(data) {
            let html = '<div class="tool-data">';
            
            html += `<h4 style="margin: 0 0 10px 0; color: #2c3e50;">🔧 ${data.tool_name || 'Tool Invocation'}</h4>`;
            
            if (data.tool_input) {
                html += '<div class="tool-input" style="background: #f8f9fa; padding: 10px; border-radius: 4px; margin-top: 10px;">';
                html += '<strong>Input:</strong>';
                
                if (data.tool_input.query) {
                    html += `<div style="margin-top: 5px; color: #3498db; font-family: monospace;">${escapeHtml(data.tool_input.query)}</div>`;
                } else {
                    html += formatJSON(data.tool_input);
                }
                
                html += '</div>';
            }
            
            html += '</div>';
            return html;
        }
        
        function formatQueryResults(data) {
            let html = '<div class="query-results">';
            
            if (data.query) {
                html += `<div class="query-text" style="margin-bottom: 10px;"><strong>Query:</strong> <span style="color: #3498db; font-family: monospace;">${escapeHtml(data.query)}</span></div>`;
            }
            
            if (data.interpretation) {
                html += `<div class="interpretation" style="margin-bottom: 10px; padding: 10px; background: #e8f4fd; border-radius: 4px;"><strong>Interpretation:</strong><br>${escapeHtml(data.interpretation)}</div>`;
            }
            
            if (data.results && data.results.length > 0) {
                html += `<div class="results-summary" style="margin-bottom: 10px;"><strong>Results:</strong> ${data.results.length} records found</div>`;
                
                // Show first few results in a table
                html += '<div style="overflow-x: auto;"><table style="width: 100%; border-collapse: collapse; font-size: 12px;">';
                
                // Headers
                const headers = Object.keys(data.results[0]);
                html += '<thead><tr style="background: #f8f9fa;">';
                headers.forEach(header => {
                    html += `<th style="padding: 8px; border: 1px solid #dee2e6; text-align: left;">${header}</th>`;
                });
                html += '</tr></thead>';
                
                // Rows (first 5)
                html += '<tbody>';
                data.results.slice(0, 5).forEach((row, index) => {
                    html += `<tr style="background: ${index % 2 === 0 ? 'white' : '#f8f9fa'};">`;
                    headers.forEach(header => {
                        const value = row[header];
                        html += `<td style="padding: 8px; border: 1px solid #dee2e6;">${value !== null ? escapeHtml(String(value)) : '<em>null</em>'}</td>`;
                    });
                    html += '</tr>';
                });
                html += '</tbody>';
                html += '</table></div>';
                
                if (data.results.length > 5) {
                    html += `<div style="margin-top: 10px; color: #7f8c8d; font-style: italic;">... and ${data.results.length - 5} more records</div>`;
                }
            }
            
            html += '</div>';
            return html;
        }
        
        function formatJSON(obj) {
            const json = JSON.stringify(obj, null, 2);
            const highlighted = json
                .replace(/"([^"]+)":/g, '<span style="color: #a333c8;">"$1"</span>:')
                .replace(/: "([^"]*)"/g, ': <span style="color: #0d7e20;">"$1"</span>')
                .replace(/: (\\d+)/g, ': <span style="color: #1a71bd;">$1</span>')
                .replace(/: (true|false)/g, ': <span style="color: #d73502;">$1</span>')
                .replace(/: null/g, ': <span style="color: #7f8c8d;">null</span>');
            
            return `<pre style="background: #f8f9fa; padding: 10px; border-radius: 4px; margin: 5px 0; font-size: 12px; white-space: pre-wrap; word-wrap: break-word; overflow-wrap: break-word; max-width: 100%; max-height: 500px; overflow-y: auto;">${highlighted}</pre>`;
        }
        
        function capitalizeFirst(str) {
            return str.charAt(0).toUpperCase() + str.slice(1);
        }
        
        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
        
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
        
        function toggleFormatting(eventId) {
            const formattedDiv = document.getElementById('formatted-' + eventId);
            const rawDiv = document.getElementById('raw-' + eventId);
            const toggleBtn = document.getElementById('format-toggle-' + eventId);
            
            if (rawDiv.style.display === 'none') {
                // Show raw view
                formattedDiv.style.display = 'none';
                rawDiv.style.display = 'block';
                toggleBtn.textContent = '📄 View Formatted';
            } else {
                // Show formatted view
                if (!formattedDiv.innerHTML) {
                    // First time - format the content
                    const content = JSON.parse(formattedDiv.dataset.content);
                    formatEventData(content, formattedDiv);
                }
                formattedDiv.style.display = 'block';
                rawDiv.style.display = 'none';
                toggleBtn.textContent = '📝 View Raw';
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
            console.log('[TIMELINE NAV DEBUGGING] DOMContentLoaded fired');
            console.log('[TIMELINE NAV DEBUGGING] Document body exists:', !!document.body);
            console.log('[TIMELINE NAV DEBUGGING] formatEventData defined:', typeof formatEventData);
            
            const firstAgent = document.querySelector('.agent-header');
            if (firstAgent) {
                console.log('[TIMELINE NAV DEBUGGING] Found first agent, clicking...');
                firstAgent.click();
            } else {
                console.log('[TIMELINE NAV DEBUGGING] No agent header found');
            }
            
            // Add click handlers for timeline stages
            const timelineBars = document.querySelectorAll('.timeline-stage-bar');
            console.log('[TIMELINE NAV DEBUGGING] Found timeline stage bars:', timelineBars.length);
            
            if (timelineBars.length === 0) {
                console.log('[TIMELINE NAV DEBUGGING] No timeline bars found, checking page structure...');
                console.log('[TIMELINE NAV DEBUGGING] All classes with timeline:', 
                    Array.from(document.querySelectorAll('[class*="timeline"]')).map(el => el.className));
            }
            
            timelineBars.forEach((bar, index) => {
                console.log('[TIMELINE NAV DEBUGGING] Bar', index, 'data-stage-id:', bar.getAttribute('data-stage-id'));
                // Single click with Ctrl/Cmd for navigation
                bar.addEventListener('click', function(e) {
                    const stageId = this.getAttribute('data-stage-id');
                    console.log('[TIMELINE NAV DEBUGGING] Click event:', {
                        stageId: stageId,
                        ctrlKey: e.ctrlKey,
                        metaKey: e.metaKey,
                        target: e.target
                    });
                    
                    // Regular click now triggers navigation (expanding agent and stage)
                    console.log('[TIMELINE NAV DEBUGGING] Click detected, navigating to agent stage...');
                    e.preventDefault();
                    navigateToAgentStage(stageId);
                    
                    // Also highlight related stages for visual feedback
                    highlightRelatedStages(stageId);
                });
                
                // Update tooltip on hover
                bar.addEventListener('mouseenter', function() {
                    const existingTooltip = this.querySelector('.stage-bar-hover');
                    if (!existingTooltip) {
                        const tooltip = document.createElement('div');
                        tooltip.className = 'stage-bar-hover';
                        tooltip.innerHTML = 'Click to navigate to this stage in Agent Analysis';
                        tooltip.style.cssText = `
                            position: absolute;
                            bottom: -25px;
                            left: 50%;
                            transform: translateX(-50%);
                            background: rgba(0, 0, 0, 0.9);
                            color: white;
                            padding: 5px 10px;
                            border-radius: 4px;
                            font-size: 11px;
                            white-space: nowrap;
                            pointer-events: none;
                            z-index: 1000;
                        `;
                        this.appendChild(tooltip);
                    }
                });
                
                bar.addEventListener('mouseleave', function() {
                    const tooltip = this.querySelector('.stage-bar-hover');
                    if (tooltip && tooltip.innerHTML === 'Click to navigate to this stage in Agent Analysis') {
                        tooltip.remove();
                    }
                });
            });
            
            // Load filter preferences from localStorage
            loadFilterPreferences();
        });
        
        function saveFilterPreferences() {
            const preferences = {
                showCMO: document.getElementById('filter-cmo').checked,
                showSpecialists: document.getElementById('filter-specialists').checked,
                showVisualization: document.getElementById('filter-visualization').checked,
                minDuration: document.getElementById('duration-filter').value,
                viewMode: document.querySelector('.view-toggle button.active').textContent.toLowerCase()
            };
            localStorage.setItem('traceViewerFilters', JSON.stringify(preferences));
        }
        
        function loadFilterPreferences() {
            // Check URL parameters first
            const urlParams = new URLSearchParams(window.location.search);
            const hideFilters = urlParams.get('hideFilters') === 'true';
            
            if (hideFilters) {
                // If hideFilters is true, keep the panel collapsed and don't show it
                const filterPanel = document.getElementById('filter-panel');
                const filterContainer = document.querySelector('.filter-panel-container');
                if (filterPanel) {
                    filterPanel.classList.add('collapsed');
                }
                if (filterContainer) {
                    filterContainer.style.display = 'none';
                }
                return; // Don't load saved preferences if filters are hidden
            }
            
            const saved = localStorage.getItem('traceViewerFilters');
            if (saved) {
                try {
                    const preferences = JSON.parse(saved);
                    
                    // Apply saved preferences
                    document.getElementById('filter-cmo').checked = preferences.showCMO !== false;
                    document.getElementById('filter-specialists').checked = preferences.showSpecialists !== false;
                    document.getElementById('filter-visualization').checked = preferences.showVisualization !== false;
                    document.getElementById('duration-filter').value = preferences.minDuration || '0';
                    
                    // Apply view mode
                    if (preferences.viewMode) {
                        document.querySelectorAll('.view-toggle button').forEach(btn => {
                            btn.classList.remove('active');
                            if (btn.textContent.toLowerCase() === preferences.viewMode) {
                                btn.classList.add('active');
                            }
                        });
                        setView(preferences.viewMode);
                    }
                    
                    // Apply filters
                    filterAgents();
                    filterByDuration();
                } catch (e) {
                    console.error('Failed to load filter preferences:', e);
                }
            }
        }
        
        function navigateToAgentStage(stageId) {
            console.log('[TIMELINE NAV DEBUGGING] navigateToAgentStage called with:', stageId);
            
            // Parse stage ID (format: "agent-stage")
            const parts = stageId.split('-');
            const agentType = parts[0];
            const stageName = parts.slice(1).join('-');
            
            console.log('[TIMELINE NAV DEBUGGING] Parsed:', {
                agentType: agentType,
                stageName: stageName
            });
            
            // First, collapse all agents
            console.log('[TIMELINE NAV DEBUGGING] Collapsing all agents...');
            document.querySelectorAll('.agent-section').forEach(section => {
                const header = section.querySelector('.agent-header');
                const content = section.querySelector('.agent-content');
                if (header && content) {
                    header.classList.remove('expanded');
                    content.classList.remove('show');
                }
            });
            
            // Find and expand the target agent
            console.log('[TIMELINE NAV DEBUGGING] Looking for agent header:', `#agent-${agentType}-header`);
            const targetAgentHeader = document.getElementById(`agent-${agentType}-header`);
            if (targetAgentHeader) {
                console.log('[TIMELINE NAV DEBUGGING] Found target agent header:', targetAgentHeader.id);
                const targetAgentSection = targetAgentHeader.parentElement;
                const content = targetAgentSection.querySelector('.agent-content');
                
                if (targetAgentHeader && content) {
                    console.log('[TIMELINE NAV DEBUGGING] Expanding agent section');
                    // Expand the agent
                    targetAgentHeader.classList.add('expanded');
                    content.classList.add('show');
                    
                    // Find and expand the specific stage within the agent
                    setTimeout(() => {
                        console.log('[TIMELINE NAV DEBUGGING] Looking for stage headers...');
                        const stageHeaders = content.querySelectorAll('.stage-header');
                        console.log('[TIMELINE NAV DEBUGGING] Found stage headers:', stageHeaders.length);
                        
                        let foundStage = false;
                        stageHeaders.forEach((stageHeader, index) => {
                            const stageSection = stageHeader.parentElement;
                            const stageContent = stageSection.querySelector('.stage-content');
                            
                            // Check if this is the target stage - look for h4 element
                            const stageNameElement = stageHeader.querySelector('h4');
                            console.log('[TIMELINE NAV DEBUGGING] Stage header', index, ':', {
                                hasNameElement: !!stageNameElement,
                                nameElementText: stageNameElement ? stageNameElement.textContent : 'N/A',
                                stageHeaderClass: stageHeader.className
                            });
                            
                            if (stageNameElement) {
                                // Remove emoji and trim the stage text
                                const stageText = stageNameElement.textContent.replace(/^📍\s*/, '').toLowerCase().trim();
                                const targetText = stageName.replace(/_/g, ' ').toLowerCase();
                                const exactMatch = stageText === targetText;
                                const startsWithMatch = stageText.startsWith(targetText);
                                console.log('[TIMELINE NAV DEBUGGING] Comparing stage:', {
                                    stageText: stageText,
                                    targetText: targetText,
                                    exactMatch: exactMatch,
                                    startsWithMatch: startsWithMatch,
                                    willMatch: exactMatch || startsWithMatch
                                });
                                
                                // Use exact match or starts with to avoid false positives
                                if (exactMatch || startsWithMatch) {
                                    foundStage = true;
                                    console.log('[TIMELINE NAV DEBUGGING] Found matching stage!');
                                    // Expand this stage
                                    stageHeader.classList.add('expanded');
                                    if (stageContent) {
                                        stageContent.classList.add('show');
                                    }
                                    
                                    // Scroll to the stage
                                    console.log('[TIMELINE NAV DEBUGGING] Scrolling to stage');
                                    stageSection.scrollIntoView({ behavior: 'smooth', block: 'center' });
                                    
                                    // Highlight the stage briefly
                                    stageSection.style.backgroundColor = '#fffacd';
                                    setTimeout(() => {
                                        stageSection.style.backgroundColor = '';
                                    }, 2000);
                                } else {
                                    // Collapse other stages
                                    stageHeader.classList.remove('expanded');
                                    if (stageContent) {
                                        stageContent.classList.remove('show');
                                    }
                                }
                            }
                        });
                        
                        if (!foundStage) {
                            console.log('[TIMELINE NAV DEBUGGING] WARNING: No matching stage found for:', stageName);
                        }
                    }, 100);
                    
                    // Scroll to the agent section
                    targetAgentSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
            } else {
                console.log('[TIMELINE NAV DEBUGGING] Agent header not found for:', agentType);
            }
        }
        
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
                        addRelationshipLabel(bar, 'receives task');
                    });
                    addRelationshipLabel(clickedStage, 'assigns tasks');
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
                            addRelationshipLabel(bar, 'provides input');
                        }
                    });
                    addRelationshipLabel(clickedStage, 'synthesizes findings');
                }
            } else if (stageType.includes('specialist')) {
                // Highlight CMO task creation
                const cmoTaskBar = document.querySelector('[data-stage-id="cmo-task_creation"]');
                if (cmoTaskBar) {
                    cmoTaskBar.classList.remove('dimmed');
                    cmoTaskBar.classList.add('related');
                    drawFlowArrow(cmoTaskBar, clickedStage, false);
                    addRelationshipLabel(cmoTaskBar, 'task source');
                }
                
                // Highlight CMO synthesis
                const cmoSynthesisBar = document.querySelector('[data-stage-id="cmo-synthesis"], [data-stage-id="cmo-final_synthesis"]');
                if (cmoSynthesisBar && stageName.includes('synthesis')) {
                    cmoSynthesisBar.classList.remove('dimmed');
                    cmoSynthesisBar.classList.add('related');
                    drawFlowArrow(clickedStage, cmoSynthesisBar, true);
                    addRelationshipLabel(cmoSynthesisBar, 'receives findings');
                }
                addRelationshipLabel(clickedStage, 'analyzing');
            } else if (stageType === 'visualization') {
                // Highlight CMO synthesis as input
                const cmoSynthesisBar = document.querySelector('[data-stage-id="cmo-synthesis"], [data-stage-id="cmo-final_synthesis"]');
                if (cmoSynthesisBar) {
                    cmoSynthesisBar.classList.remove('dimmed');
                    cmoSynthesisBar.classList.add('related');
                    drawFlowArrow(cmoSynthesisBar, clickedStage, false);
                    addRelationshipLabel(cmoSynthesisBar, 'data source');
                }
                addRelationshipLabel(clickedStage, 'generating chart');
            }
            
            // Click anywhere else to reset
            setTimeout(() => {
                document.addEventListener('click', function resetHighlight(e) {
                    if (!e.target.closest('.timeline-stage-bar')) {
                        document.querySelectorAll('.timeline-stage-bar').forEach(bar => {
                            bar.classList.remove('highlighted', 'dimmed', 'related');
                        });
                        document.querySelectorAll('.flow-arrow').forEach(arrow => arrow.remove());
                        document.querySelectorAll('.relationship-label').forEach(label => label.remove());
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
        
        function addRelationshipLabel(element, text) {
            const label = document.createElement('div');
            label.className = 'relationship-label';
            label.textContent = text;
            const rect = element.getBoundingClientRect();
            label.style.left = rect.left + rect.width / 2 - 50 + 'px';
            label.style.top = rect.bottom + 5 + 'px';
            document.body.appendChild(label);
        }
        
        // Toggle filter panel
        function toggleFilterPanel() {
            const panel = document.getElementById('filter-panel');
            const icon = document.getElementById('filter-collapse-icon');
            const summary = document.getElementById('filter-panel-summary');
            
            if (panel.classList.contains('collapsed')) {
                panel.classList.remove('collapsed');
                icon.classList.remove('rotated');
                icon.textContent = '▼';
                summary.textContent = '(Click to collapse)';
            } else {
                panel.classList.add('collapsed');
                icon.classList.add('rotated');
                icon.textContent = '▼';
                summary.textContent = '(Click to expand)';
            }
        }
        
        // Filter functions
        function filterAgents() {
            const showCMO = document.getElementById('filter-cmo').checked;
            const showSpecialists = document.getElementById('filter-specialists').checked;
            const showVisualization = document.getElementById('filter-visualization').checked;
            
            // List of specialist agent types
            const specialistTypes = ['cardiology', 'endocrinology', 'laboratory_medicine', 
                                   'pharmacy', 'nutrition', 'preventive_medicine'];
            
            let visibleLanes = 0;
            let totalLanes = 0;
            
            // Filter timeline lanes
            document.querySelectorAll('.timeline-lane-row').forEach(row => {
                const label = row.querySelector('.timeline-agent-label');
                let shouldShow = false;
                totalLanes++;
                
                // Check if it's CMO
                if (label.classList.contains('cmo')) {
                    shouldShow = showCMO;
                } 
                // Check if it's visualization
                else if (label.classList.contains('visualization')) {
                    shouldShow = showVisualization;
                } 
                // Check if it's any specialist type
                else {
                    for (const specialist of specialistTypes) {
                        if (label.classList.contains(specialist)) {
                            shouldShow = showSpecialists;
                            break;
                        }
                    }
                }
                
                row.style.display = shouldShow ? 'flex' : 'none';
                if (shouldShow) visibleLanes++;
            });
            
            // Filter agent sections
            let visibleSections = 0;
            let totalSections = 0;
            
            document.querySelectorAll('.agent-section').forEach(section => {
                const header = section.querySelector('.agent-header');
                const title = section.querySelector('.agent-title');
                const titleText = title ? title.textContent.toLowerCase() : '';
                let shouldShow = false;
                totalSections++;
                
                // Check by header class first
                if (header.classList.contains('cmo')) {
                    shouldShow = showCMO;
                } 
                // For specialists and visualization, check the title text
                else if (titleText.includes('visualization')) {
                    shouldShow = showVisualization;
                } 
                // Check if it's a specialist
                else if (header.classList.contains('specialist') || 
                         titleText.includes('specialist') ||
                         specialistTypes.some(type => titleText.includes(type))) {
                    shouldShow = showSpecialists;
                }
                
                section.style.display = shouldShow ? 'block' : 'none';
                if (shouldShow) visibleSections++;
            });
            
            updateFilterStatus(visibleSections, totalSections);
            saveFilterPreferences();
        }
        
        function updateFilterStatus(visible, total) {
            const status = document.getElementById('filter-status');
            if (visible === total) {
                status.textContent = 'Showing all items';
            } else {
                status.textContent = `Showing ${visible} of ${total} agents`;
            }
        }
        
        function applyPreset(preset) {
            const cmoCheckbox = document.getElementById('filter-cmo');
            const specialistsCheckbox = document.getElementById('filter-specialists');
            const visualizationCheckbox = document.getElementById('filter-visualization');
            const durationFilter = document.getElementById('duration-filter');
            
            switch(preset) {
                case 'all':
                    cmoCheckbox.checked = true;
                    specialistsCheckbox.checked = true;
                    visualizationCheckbox.checked = true;
                    durationFilter.value = '0';
                    break;
                case 'critical':
                    // Show only longest running stages
                    cmoCheckbox.checked = true;
                    specialistsCheckbox.checked = true;
                    visualizationCheckbox.checked = true;
                    durationFilter.value = '10000'; // 10s+
                    break;
                case 'errors':
                    // This would need error detection logic
                    alert('Error filtering requires error detection implementation');
                    return;
            }
            
            filterAgents();
            filterByDuration();
        }
        
        function resetFilters() {
            document.getElementById('filter-cmo').checked = true;
            document.getElementById('filter-specialists').checked = true;
            document.getElementById('filter-visualization').checked = true;
            document.getElementById('duration-filter').value = '0';
            
            // Reset all opacity changes
            document.querySelectorAll('.timeline-stage-bar').forEach(bar => {
                bar.style.opacity = '1';
            });
            
            filterAgents();
            
            // Reset zoom
            zoomTimeline('reset');
        }
        
        function filterByDuration() {
            const minDuration = parseInt(document.getElementById('duration-filter').value);
            
            document.querySelectorAll('.timeline-stage-bar').forEach(bar => {
                const durationText = bar.querySelector('.stage-bar-time').textContent;
                const duration = parseDuration(durationText);
                bar.style.opacity = duration >= minDuration ? '1' : '0.3';
            });
            saveFilterPreferences();
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
        
        // Zoom functionality
        let zoomLevel = 100;
        
        function zoomTimeline(action) {
            const wrapper = document.querySelector('.timeline-wrapper');
            const levelDisplay = document.getElementById('zoom-level');
            
            if (action === 'in') {
                zoomLevel = Math.min(200, zoomLevel + 25);
            } else if (action === 'out') {
                zoomLevel = Math.max(50, zoomLevel - 25);
            } else if (action === 'reset') {
                zoomLevel = 100;
            }
            
            wrapper.style.transform = `scaleX(${zoomLevel / 100})`;
            wrapper.style.transformOrigin = 'left center';
            levelDisplay.textContent = zoomLevel + '%';
            
            // Adjust container width to prevent overflow
            const container = document.querySelector('.timeline-container');
            if (zoomLevel > 100) {
                container.style.overflowX = 'auto';
            } else {
                container.style.overflowX = 'auto';
            }
        }
        
        // Table sorting functionality
        let sortColumn = null;
        let sortDirection = 'asc';
        
        function sortTable(columnIndex, columnName) {
            const table = document.querySelector('.agent-metrics-table');
            const tbody = table.querySelector('tbody');
            const rows = Array.from(tbody.querySelectorAll('tr'));
            const headers = table.querySelectorAll('th');
            
            // Update sort direction
            if (sortColumn === columnIndex) {
                sortDirection = sortDirection === 'asc' ? 'desc' : 'asc';
            } else {
                sortDirection = 'asc';
                sortColumn = columnIndex;
            }
            
            // Update header classes
            headers.forEach((header, idx) => {
                header.classList.remove('sorted-asc', 'sorted-desc');
                if (idx === columnIndex) {
                    header.classList.add(`sorted-${sortDirection}`);
                }
            });
            
            // Sort rows
            rows.sort((a, b) => {
                const aValue = getCellValue(a, columnIndex);
                const bValue = getCellValue(b, columnIndex);
                
                // Numeric comparison for numeric columns
                if (columnIndex > 0) {
                    const aNum = parseFloat(aValue) || 0;
                    const bNum = parseFloat(bValue) || 0;
                    return sortDirection === 'asc' ? aNum - bNum : bNum - aNum;
                }
                
                // String comparison for agent name
                return sortDirection === 'asc' ? 
                    aValue.localeCompare(bValue) : 
                    bValue.localeCompare(aValue);
            });
            
            // Reorder rows
            rows.forEach(row => tbody.appendChild(row));
        }
        
        function getCellValue(row, columnIndex) {
            const cell = row.cells[columnIndex];
            // Extract numeric value from duration cells (e.g., "2m 15s" -> 135)
            if (columnIndex === 1) {
                const text = cell.textContent;
                let seconds = 0;
                const minMatch = text.match(/(\d+)\s*m/);
                const secMatch = text.match(/(\d+(?:\.\d+)?)\s*s/);
                if (minMatch) seconds += parseInt(minMatch[1]) * 60;
                if (secMatch) seconds += parseFloat(secMatch[1]);
                return seconds;
            }
            // For other cells, try to extract numeric value
            const text = cell.textContent.trim();
            const numMatch = text.match(/[\d,]+(?:\.\d+)?/);
            return numMatch ? numMatch[0].replace(/,/g, '') : text;
        }
        
        function scrollToAgent(agentType) {
            // Find the corresponding agent section
            const sections = document.querySelectorAll('.agent-section');
            let targetSection = null;
            
            sections.forEach(section => {
                const title = section.querySelector('.agent-title');
                if (title) {
                    const titleText = title.textContent.toLowerCase();
                    if (agentType === 'cmo' && titleText.includes('chief medical officer')) {
                        targetSection = section;
                    } else if (titleText.includes(agentType.replace('_', ' '))) {
                        targetSection = section;
                    }
                }
            });
            
            if (targetSection) {
                // Scroll to the section
                targetSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
                
                // Flash the section header to draw attention
                const header = targetSection.querySelector('.agent-header');
                if (header) {
                    header.style.animation = 'flash 0.5s ease 3';
                    setTimeout(() => {
                        header.style.animation = '';
                    }, 1500);
                }
                
                // Expand the section if collapsed
                const content = targetSection.querySelector('.agent-content');
                if (content && !content.classList.contains('show')) {
                    header.click();
                }
            }
        }
    """


def _generate_filter_panel() -> str:
    """Generate filter configuration panel"""
    return """
    <div class="filter-panel-container">
        <div class="filter-panel-header" onclick="toggleFilterPanel()">
            <span class="filter-panel-title">
                <span class="collapse-icon" id="filter-collapse-icon">▼</span>
                Filters & View Options
            </span>
            <span class="filter-panel-summary" id="filter-panel-summary">
                (Click to expand)
            </span>
        </div>
        <div class="filter-panel collapsed" id="filter-panel">
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
            
            <div class="filter-group">
                <span class="filter-label">Presets:</span>
                <button class="filter-preset" onclick="applyPreset('all')">All</button>
                <button class="filter-preset" onclick="applyPreset('critical')">Critical Path</button>
                <button class="filter-preset" onclick="applyPreset('errors')">Errors Only</button>
                <button class="filter-preset reset" onclick="resetFilters()">↺ Reset</button>
            </div>
            
            <div class="view-toggle">
                <button class="active" onclick="setView('detailed')">Detailed</button>
                <button onclick="setView('simplified')">Simplified</button>
            </div>
            
            <div class="filter-status" id="filter-status">
                Showing all items
            </div>
        </div>
    </div>
    """


def _generate_header(trace: CompleteTrace, summary: Dict[str, Any]) -> str:
    """Generate header section"""
    total_cost = estimate_api_cost(summary.get('total_tokens', 0))
    
    # For embedded view, just show minimal trace info
    return f"""
    <div class="compact-header">
        <div class="trace-info">
            <span class="trace-id">Trace: {trace.trace_id[:8]}...</span>
            <span class="trace-meta">Duration: {format_duration(trace.total_duration_ms)} • Cost: {format_cost(total_cost)}</span>
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
    
    # Determine performance classes
    total_duration_ms = summary.get('total_duration_ms', 0)
    duration_class = "performance-good" if total_duration_ms < 30000 else "performance-warning" if total_duration_ms < 120000 else "performance-critical"
    
    # Token efficiency
    token_efficiency = summary['total_tokens'] / summary['total_llm_calls'] if summary['total_llm_calls'] > 0 else 0
    token_class = "performance-good" if token_efficiency < 5000 else "performance-warning" if token_efficiency < 10000 else "performance-critical"
    
    # Cost performance
    total_cost = estimate_api_cost(summary.get('total_tokens', 0))
    cost_class = "performance-good" if total_cost < 0.10 else "performance-warning" if total_cost < 0.50 else "performance-critical"
    
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
            <div class="summary-card {token_class}">
                <div class="icon">🎯</div>
                <div class="value">{format_token_count(summary['total_tokens'])}</div>
                <div class="label">Tokens Used</div>
            </div>
            <div class="summary-card {cost_class}">
                <div class="icon">💰</div>
                <div class="value">{format_cost(total_cost)}</div>
                <div class="label">Est. Cost</div>
            </div>
        </div>
        
        <h4 style="margin: 30px 0 15px 0; color: #2c3e50;">Agent Performance Comparison</h4>
        {_generate_agent_metrics_table(agent_metrics)}
    </div>
    """


def _generate_agent_metrics_table(metrics: List[Dict[str, Any]]) -> str:
    """Generate agent metrics comparison table"""
    # Sort by duration by default
    metrics.sort(key=lambda x: x['duration'], reverse=True)
    
    table_rows = []
    for metric in metrics:
        agent_class = "cmo" if metric['type'] == "cmo" else "specialist" if "specialist" in metric['type'].lower() else "visualization"
        
        # Calculate efficiency metrics
        tokens_per_sec = (metric['tokens'] / (metric['duration'] / 1000)) if metric['duration'] > 0 else 0
        avg_tokens_per_call = (metric['tokens'] / metric['llm_calls']) if metric['llm_calls'] > 0 else 0
        
        # Determine duration class for color coding
        duration_ms = metric['duration']
        duration_class = "fast" if duration_ms < 30000 else "medium" if duration_ms < 120000 else "slow"
        
        table_rows.append(f"""
        <tr>
            <td>
                <div class="agent-name-cell">
                    <div class="agent-type-indicator {agent_class}"></div>
                    {metric['name']}
                </div>
            </td>
            <td class="duration-cell {duration_class}">{format_duration(metric['duration'])}</td>
            <td class="metric-value">{metric['stages']}</td>
            <td class="metric-value">{metric['llm_calls']}</td>
            <td class="metric-value">{metric['tool_calls']}</td>
            <td class="metric-value">{format_token_count(metric['tokens'])}</td>
            <td class="metric-value">{format_duration(metric['avg_response'])}</td>
            <td class="efficiency-value">{tokens_per_sec:.0f}</td>
            <td class="efficiency-value">{avg_tokens_per_call:.0f}</td>
        </tr>
        """)
    
    return f"""
    <table class="agent-metrics-table">
        <thead>
            <tr>
                <th class="sortable" onclick="sortTable(0, 'agent')">Agent</th>
                <th class="sortable sorted-desc" onclick="sortTable(1, 'duration')">Duration</th>
                <th class="sortable" onclick="sortTable(2, 'stages')">Stages</th>
                <th class="sortable" onclick="sortTable(3, 'llm_calls')">LLM Calls</th>
                <th class="sortable" onclick="sortTable(4, 'tool_calls')">Tool Calls</th>
                <th class="sortable" onclick="sortTable(5, 'tokens')">Tokens</th>
                <th class="sortable" onclick="sortTable(6, 'avg_response')">Avg Response</th>
                <th class="sortable" onclick="sortTable(7, 'speed')">Speed (tok/s)</th>
                <th class="sortable" onclick="sortTable(8, 'efficiency')">Efficiency (tok/call)</th>
            </tr>
        </thead>
        <tbody>
            {"".join(table_rows)}
        </tbody>
    </table>
    """


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
    
    # Calculate average duration for anomaly detection
    durations = [s['duration_ms'] for s in all_stages if s['duration_ms'] > 0]
    avg_duration = sum(durations) / len(durations) if durations else 0
    anomaly_threshold = avg_duration * 3  # 3x average is considered anomalous
    
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
    
    # Group stages by agent for lanes and assign execution order
    agent_lanes = {}
    execution_order = 1
    stages_by_time = sorted(all_stages, key=lambda x: x['start_time'])
    
    for stage in stages_by_time:
        stage['global_execution_order'] = execution_order
        execution_order += 1
    
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
                status_class = "success" if stage['stage_info'].end_time else "running"
                
                # Check for anomaly (unusually long duration)
                anomaly_class = "anomaly" if stage['duration_ms'] > anomaly_threshold and stage['duration_ms'] > 30000 else ""
                
                stages_html.append(f"""
                <div class="timeline-stage-bar cmo {status_class} {anomaly_class}" 
                     style="left: {left_percent:.1f}%; width: {width_percent:.1f}%;"
                     title="{hover_info}"
                     data-stage-id="cmo-{stage['stage_name']}">
                    <div class="execution-order">{stage['global_execution_order']}</div>
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
                <div class="timeline-agent-label cmo" onclick="scrollToAgent('cmo')">CMO - Planning</div>
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
            status_class = "success" if stage['stage_info'].end_time else "running"
            
            # Check for anomaly
            anomaly_class = "anomaly" if stage['duration_ms'] > anomaly_threshold and stage['duration_ms'] > 30000 else ""
            
            stages_html.append(f"""
            <div class="timeline-stage-bar {specialist_type} {status_class} {anomaly_class}" 
                 style="left: {left_percent:.1f}%; width: {width_percent:.1f}%;"
                 title="{hover_info}"
                 data-stage-id="{specialist_type}-{stage['stage_name']}">
                <div class="execution-order">{stage['global_execution_order']}</div>
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
            <div class="timeline-agent-label {specialist_type}" onclick="scrollToAgent('{specialist_type}')">{lane['name']}</div>
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
            status_class = "success" if stage['stage_info'].end_time else "running"
            
            stages_html.append(f"""
            <div class="timeline-stage-bar cmo {status_class}" 
                 style="left: {left_percent:.1f}%; width: {width_percent:.1f}%;"
                 title="{hover_info}"
                 data-stage-id="cmo-{stage['stage_name']}">
                <div class="execution-order">{stage['global_execution_order']}</div>
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
            <div class="timeline-agent-label cmo" onclick="scrollToAgent('cmo')">CMO - Synthesis</div>
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
            status_class = "success" if stage['stage_info'].end_time else "running"
            
            stages_html.append(f"""
            <div class="timeline-stage-bar visualization {status_class}" 
                 style="left: {left_percent:.1f}%; width: {width_percent:.1f}%;"
                 title="{hover_info}"
                 data-stage-id="visualization-{stage['stage_name']}">
                <div class="execution-order">{stage['global_execution_order']}</div>
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
            <div class="timeline-agent-label visualization" onclick="scrollToAgent('visualization')">{lane['name']}</div>
            <div class="timeline-track">
                {"".join(stages_html)}
            </div>
        </div>
        """)
    
    # Add time axis
    time_markers = _generate_time_axis(min_time, max_time, timeline_width)
    
    # Calculate performance summary
    total_time = (max_time - min_time).total_seconds() if all_stages else 0
    
    # Calculate time saved by parallel execution
    sequential_time = sum(s['duration_ms'] / 1000 for s in all_stages)  # Total if run sequentially
    time_saved = sequential_time - total_time if sequential_time > total_time else 0
    savings_percent = (time_saved / sequential_time * 100) if sequential_time > 0 else 0
    
    # Count parallel operations
    parallel_stages = len([s for s in all_stages if any(
        other['start_time'] <= s['start_time'] <= other.get('end_time', other['start_time']) 
        for other in all_stages if other != s
    )])
    
    return f"""
    <div class="timeline-section">
        <div class="timeline-header">
            <div>
                <h2>📊 Execution Timeline</h2>
                <span style="font-size: 13px; color: #7f8c8d;">
                    Total: {int(total_time)}s | Sequential: {int(sequential_time)}s | 
                    <span style="color: #2ecc71; font-weight: 600;">Saved: {int(time_saved)}s ({savings_percent:.0f}%)</span> | 
                    {parallel_stages} parallel operations
                </span>
            </div>
            <div class="zoom-controls">
                <button onclick="zoomTimeline('out')">−</button>
                <span class="zoom-level" id="zoom-level">100%</span>
                <button onclick="zoomTimeline('in')">+</button>
                <button onclick="zoomTimeline('reset')">Reset</button>
            </div>
        </div>
        <div class="timeline-container">
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


def _generate_agent_analysis_section(sections: List[AgentSection]) -> str:
    """Generate the complete agent analysis section with header and content"""
    return f"""
    <div class="timeline-section" style="margin-bottom: 20px;">
        <div class="timeline-header">
            <h2>📋 Agent Analysis Details</h2>
            <span style="font-size: 13px; color: #7f8c8d;">
                Detailed execution breakdown by agent with hierarchical event trees
            </span>
        </div>
        <div class="agent-details-container" style="margin-top: 20px;">
            {_generate_agent_sections(sections)}
        </div>
    </div>
    """


def _generate_agent_analysis_header() -> str:
    """Generate header for agent analysis details section"""
    return """
    <div class="timeline-section" style="margin-bottom: 20px;">
        <div class="timeline-header">
            <h2>📋 Agent Analysis Details</h2>
            <span style="font-size: 13px; color: #7f8c8d;">
                Detailed execution breakdown by agent with hierarchical event trees
            </span>
        </div>
    </div>
    """


def _generate_agent_sections(sections: List[AgentSection]) -> str:
    """Generate agent sections with hierarchical events"""
    sections_html = []
    
    for i, section in enumerate(sections):
        # Use agent type in ID for navigation
        agent_id = f"agent-{section.agent_type}"
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
        response_preview = truncate_text(data.get('response_text', ''), 300)  # Increased from 150
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
            <pre style="background: #f8f9fa; padding: 10px; border-radius: 4px; margin: 5px 0; font-size: 12px; white-space: pre-wrap; word-wrap: break-word; overflow-wrap: break-word; max-width: 100%; max-height: 500px; overflow-y: auto;">
{components['current_prompt']}</pre>
            
            {f'<strong>System Prompt:</strong><pre style="background: #f8f9fa; padding: 10px; border-radius: 4px; margin: 5px 0; font-size: 12px; white-space: pre-wrap; word-wrap: break-word; overflow-wrap: break-word; max-width: 100%; max-height: 500px; overflow-y: auto;">{system_prompt}</pre>' if system_prompt else ''}
            
            {f'<details><summary><strong>Conversation History ({components["history_size"]} messages)</strong></summary><pre style="background: #f8f9fa; padding: 10px; border-radius: 4px; margin: 5px 0; font-size: 12px; white-space: pre-wrap; word-wrap: break-word; overflow-wrap: break-word; max-width: 100%; max-height: 500px; overflow-y: auto;">{json.dumps(components["conversation_history"], indent=2)}</pre></details>' if components['history_size'] > 0 else ''}
        </div>
        """
        
    elif event.event_type == TraceEventType.LLM_RESPONSE:
        # Show response text with formatting option
        response_text = data.get('response_text', '')
        
        return f"""
        <div style="margin-top: 10px;" id="event-{event.event_id}-details-content">
            <div class="format-toggle" style="margin-bottom: 10px;">
                <button onclick="toggleFormatting('{event.event_id}')" style="padding: 4px 8px; border: 1px solid #dee2e6; border-radius: 4px; background: white; cursor: pointer; font-size: 12px;">
                    <span id="format-toggle-{event.event_id}">📝 View Raw</span>
                </button>
            </div>
            <div id="formatted-{event.event_id}"></div>
            <div id="raw-{event.event_id}" style="display: none;">
                <pre style="background: #f8f9fa; padding: 10px; border-radius: 4px; margin: 5px 0; font-size: 12px; white-space: pre-wrap; word-wrap: break-word; overflow-wrap: break-word; max-width: 100%; max-height: 500px; overflow-y: auto;">
{html.escape(response_text)}</pre>
            </div>
            <script>
                (function() {{
                    const eventId = {json.dumps(event.event_id)};
                    const eventData = {json.dumps(json.dumps(data))};
                    
                    document.getElementById('formatted-' + eventId).dataset.content = eventData;
                    
                    // Defer initialization until all scripts are loaded
                    window.addEventListener('load', function() {{
                        setTimeout(function() {{
                            const formattedDiv = document.getElementById('formatted-' + eventId);
                            if (formattedDiv && !formattedDiv.innerHTML) {{
                                try {{
                                    const content = JSON.parse(formattedDiv.dataset.content);
                                    if (typeof formatEventData === 'function') {{
                                        formatEventData(content, formattedDiv);
                                    }} else {{
                                        // Retry once more after a delay
                                        setTimeout(function() {{
                                            if (typeof formatEventData === 'function') {{
                                                formatEventData(content, formattedDiv);
                                            }}
                                        }}, 100);
                                    }}
                                }} catch (e) {{
                                    console.error('Error formatting event data:', e);
                                }}
                            }}
                        }}, 50);
                    }});
                }})();
            </script>
        </div>
        """
        
    elif event.event_type == TraceEventType.TOOL_RESULT:
        # Show full tool results
        result_data = data.get('result_data', {})
        metadata = event.metadata or {}
        full_output = metadata.get('tool_output', result_data)
        
        return f"""
        <div style="margin-top: 10px;" id="event-{event.event_id}-details-content">
            <div class="format-toggle" style="margin-bottom: 10px;">
                <button onclick="toggleFormatting('{event.event_id}')" style="padding: 4px 8px; border: 1px solid #dee2e6; border-radius: 4px; background: white; cursor: pointer; font-size: 12px;">
                    <span id="format-toggle-{event.event_id}">📝 View Raw</span>
                </button>
            </div>
            <div id="formatted-{event.event_id}"></div>
            <div id="raw-{event.event_id}" style="display: none;">
                <pre style="background: #f8f9fa; padding: 10px; border-radius: 4px; margin: 5px 0; font-size: 12px; white-space: pre-wrap; word-wrap: break-word; overflow-wrap: break-word; max-width: 100%; max-height: 300px; overflow-y: auto;">
{json.dumps(full_output, indent=2)}</pre>
            </div>
            <script>
                (function() {{
                    const eventId = {json.dumps(event.event_id)};
                    const eventData = {json.dumps(json.dumps(full_output))};
                    
                    document.getElementById('formatted-' + eventId).dataset.content = eventData;
                    
                    // Defer initialization until all scripts are loaded
                    window.addEventListener('load', function() {{
                        setTimeout(function() {{
                            const formattedDiv = document.getElementById('formatted-' + eventId);
                            if (formattedDiv && !formattedDiv.innerHTML) {{
                                try {{
                                    const content = JSON.parse(formattedDiv.dataset.content);
                                    if (typeof formatEventData === 'function') {{
                                        formatEventData(content, formattedDiv);
                                    }} else {{
                                        // Retry once more after a delay
                                        setTimeout(function() {{
                                            if (typeof formatEventData === 'function') {{
                                                formatEventData(content, formattedDiv);
                                            }}
                                        }}, 100);
                                    }}
                                }} catch (e) {{
                                    console.error('Error formatting event data:', e);
                                }}
                            }}
                        }}, 50);
                    }});
                }})();
            </script>
        </div>
        """
        
    else:
        # Default detailed view with formatting option
        return f"""
        <div style="margin-top: 10px;" id="event-{event.event_id}-details-content">
            <div class="format-toggle" style="margin-bottom: 10px;">
                <button onclick="toggleFormatting('{event.event_id}')" style="padding: 4px 8px; border: 1px solid #dee2e6; border-radius: 4px; background: white; cursor: pointer; font-size: 12px;">
                    <span id="format-toggle-{event.event_id}">📝 View Raw</span>
                </button>
            </div>
            <div id="formatted-{event.event_id}"></div>
            <div id="raw-{event.event_id}" style="display: none;">
                <pre style="background: #f8f9fa; padding: 10px; border-radius: 4px; margin: 5px 0; font-size: 12px; white-space: pre-wrap; word-wrap: break-word; overflow-wrap: break-word; max-width: 100%; max-height: 500px; overflow-y: auto;">
{json.dumps(data, indent=2)}</pre>
            </div>
            <script>
                (function() {{
                    const eventId = {json.dumps(event.event_id)};
                    const eventData = {json.dumps(json.dumps(data))};
                    
                    document.getElementById('formatted-' + eventId).dataset.content = eventData;
                    
                    // Defer initialization until all scripts are loaded
                    window.addEventListener('load', function() {{
                        setTimeout(function() {{
                            const formattedDiv = document.getElementById('formatted-' + eventId);
                            if (formattedDiv && !formattedDiv.innerHTML) {{
                                try {{
                                    const content = JSON.parse(formattedDiv.dataset.content);
                                    if (typeof formatEventData === 'function') {{
                                        formatEventData(content, formattedDiv);
                                    }} else {{
                                        // Retry once more after a delay
                                        setTimeout(function() {{
                                            if (typeof formatEventData === 'function') {{
                                                formatEventData(content, formattedDiv);
                                            }}
                                        }}, 100);
                                    }}
                                }} catch (e) {{
                                    console.error('Error formatting event data:', e);
                                }}
                            }}
                        }}, 50);
                    }});
                }})();
            </script>
        </div>
        """

def _generate_qe_css() -> str:
    """Generate CSS specific to QE panel"""
    return """
        /* Two-panel layout */
        .main-layout {
            display: flex;
            height: 100vh;
            overflow: hidden;
        }
        
        .qe-panel {
            width: 35%;
            min-width: 400px;
            max-width: 600px;
            background: #f8f9fa;
            border-right: 1px solid #dee2e6;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        
        .resizer {
            width: 4px;
            background: #dee2e6;
            cursor: col-resize;
            position: relative;
        }
        
        .resizer:hover {
            background: #6c757d;
        }
        
        .trace-panel {
            flex: 1;
            overflow: auto;
        }
        
        /* QE Chat styles */
        .qe-header {
            padding: 1rem;
            background: white;
            border-bottom: 1px solid #dee2e6;
        }
        
        .qe-header h2 {
            margin: 0;
            font-size: 1.25rem;
            color: #333;
        }
        
        .qe-header p {
            margin: 0.5rem 0 0 0;
            font-size: 0.875rem;
            color: #6c757d;
        }
        
        .qe-messages {
            flex: 1;
            overflow-y: auto;
            padding: 1rem;
            background: #f8f9fa;
        }
        
        .qe-message {
            margin-bottom: 1rem;
            animation: fadeIn 0.3s ease-in;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .qe-message.user {
            text-align: right;
        }
        
        .qe-message.user .message-content {
            background: #007bff;
            color: white;
            display: inline-block;
            padding: 0.75rem 1rem;
            border-radius: 18px 18px 4px 18px;
            max-width: 80%;
            text-align: left;
        }
        
        .qe-message.assistant {
            text-align: left;
        }
        
        .qe-message.assistant .message-content {
            background: white;
            border: 1px solid #dee2e6;
            display: inline-block;
            padding: 0.75rem 1rem;
            border-radius: 18px 18px 18px 4px;
            max-width: 90%;
        }
        
        .qe-message.thinking .message-content {
            background: #e9ecef;
            font-style: italic;
            color: #6c757d;
        }
        
        .qe-input-container {
            padding: 1rem;
            background: white;
            border-top: 1px solid #dee2e6;
        }
        
        .qe-input-wrapper {
            display: flex;
            gap: 0.5rem;
        }
        
        #qe-input {
            flex: 1;
            padding: 0.75rem;
            border: 1px solid #ced4da;
            border-radius: 8px;
            resize: none;
            font-family: inherit;
            font-size: 0.875rem;
            min-height: 80px;
        }
        
        #qe-input:focus {
            outline: none;
            border-color: #80bdff;
            box-shadow: 0 0 0 0.2rem rgba(0,123,255,.25);
        }
        
        .qe-send-btn {
            padding: 0.75rem 1.5rem;
            background: #007bff;
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 500;
            align-self: flex-end;
        }
        
        .qe-send-btn:hover {
            background: #0056b3;
        }
        
        .qe-send-btn:disabled {
            background: #6c757d;
            cursor: not-allowed;
        }
        
        /* Test case display */
        .test-case-container {
            margin-top: 1rem;
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            overflow: hidden;
        }
        
        .action-menu {
            margin-top: 0.5rem;
            padding: 0;
            line-height: 1.5;
            font-size: 14px;
        }
        
        .action-menu strong {
            color: #495057;
            font-weight: 600;
            display: inline;
            margin-right: 0.25rem;
        }
        
        .action-menu br + br {
            display: none;
        }
        
        /* Evaluation results */
        .evaluation-result {
            margin-top: 1rem;
            padding: 1rem;
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 8px;
        }
        
        .evaluation-result h4 {
            margin: 0 0 0.5rem 0;
            color: #28a745;
        }
        
        .result-summary {
            margin-bottom: 1rem;
            line-height: 1.6;
        }
        
        .dimension-scores {
            width: 100%;
            border-collapse: collapse;
            margin-top: 0.5rem;
        }
        
        .dimension-scores th,
        .dimension-scores td {
            padding: 0.5rem;
            text-align: left;
            border-bottom: 1px solid #dee2e6;
        }
        
        .dimension-scores th {
            background: #e9ecef;
            font-weight: 600;
        }
        
        .dimension-scores tr:last-child td {
            border-bottom: none;
        }
        
        .test-case-header {
            padding: 0.75rem 1rem;
            background: #e9ecef;
            border-bottom: 1px solid #dee2e6;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .test-case-header span {
            font-weight: 500;
            color: #495057;
        }
        
        .copy-btn {
            padding: 0.25rem 0.75rem;
            background: #28a745;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.75rem;
        }
        
        .copy-btn:hover {
            background: #218838;
        }
        
        .copy-btn.copied {
            background: #6c757d;
        }
        
        /* Evaluation Progress Styles */
        .evaluation-progress {
            background: #f8f9fa;
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            padding: 1.5rem;
        }
        
        .evaluation-progress h4 {
            margin: 0 0 1rem 0;
            color: #2c3e50;
        }
        
        .progress-steps {
            display: flex;
            flex-direction: column;
            gap: 0.75rem;
            margin-bottom: 1rem;
        }
        
        .progress-step {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            padding: 0.75rem;
            border-radius: 6px;
            background: white;
            border: 1px solid #e5e7eb;
            transition: all 0.3s ease;
        }
        
        .progress-step.pending {
            opacity: 0.6;
        }
        
        .progress-step.active {
            background: #e3f2fd;
            border-color: #2196f3;
            box-shadow: 0 0 0 3px rgba(33, 150, 243, 0.1);
            animation: pulse 2s infinite;
        }
        
        .progress-step.completed {
            background: #e8f5e9;
            border-color: #4caf50;
        }
        
        .progress-step.error {
            background: #ffebee;
            border-color: #f44336;
        }
        
        .step-icon {
            font-size: 1.25rem;
            width: 2rem;
            text-align: center;
        }
        
        .step-label {
            flex: 1;
            font-size: 0.9rem;
            font-weight: 500;
        }
        
        .progress-details {
            max-height: 200px;
            overflow-y: auto;
            font-size: 0.85rem;
            border-top: 1px solid #e5e7eb;
            padding-top: 0.75rem;
            margin-top: 1rem;
        }
        
        .progress-detail {
            padding: 0.25rem 0;
            color: #6c757d;
        }
        
        .progress-detail .timestamp {
            font-family: monospace;
            color: #999;
            margin-right: 0.5rem;
        }
        
        .error-message {
            color: #f44336;
            font-weight: 500;
            padding: 0.5rem;
            background: #ffebee;
            border-radius: 4px;
            margin-top: 0.5rem;
        }
        
        /* Enhanced Result Display */
        .result-summary {
            display: flex;
            gap: 2rem;
            margin: 1rem 0;
            align-items: center;
        }
        
        .overall-score {
            text-align: center;
            padding: 1rem;
            border-radius: 8px;
            background: #f8f9fa;
            border: 2px solid #e5e7eb;
        }
        
        .overall-score.high {
            background: #e8f5e9;
            border-color: #4caf50;
        }
        
        .overall-score.medium {
            background: #fff3e0;
            border-color: #ff9800;
        }
        
        .overall-score.low {
            background: #ffebee;
            border-color: #f44336;
        }
        
        .score-label {
            display: block;
            font-size: 0.875rem;
            color: #6c757d;
            margin-bottom: 0.25rem;
        }
        
        .score-value {
            display: block;
            font-size: 1.5rem;
            font-weight: bold;
        }
        
        .pass-fail {
            font-size: 1.25rem;
            font-weight: 600;
            padding: 0.5rem 1rem;
            border-radius: 6px;
        }
        
        .pass-fail.passed {
            color: #2e7d32;
            background: #e8f5e9;
        }
        
        .pass-fail.failed {
            color: #c62828;
            background: #ffebee;
        }
        
        .dimensions-section {
            margin-top: 1.5rem;
        }
        
        .dimensions-section h5 {
            margin: 0 0 0.75rem 0;
            color: #495057;
        }
        
        .dimension-item {
            margin-bottom: 0.75rem;
            padding: 0.75rem;
            background: white;
            border: 1px solid #e5e7eb;
            border-radius: 6px;
        }
        
        .dimension-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0.5rem;
        }
        
        .dimension-name {
            font-weight: 600;
            text-transform: capitalize;
        }
        
        .dimension-score {
            font-weight: bold;
            padding: 0.25rem 0.5rem;
            border-radius: 4px;
            font-size: 0.875rem;
        }
        
        .dimension-score.high {
            background: #e8f5e9;
            color: #2e7d32;
        }
        
        .dimension-score.medium {
            background: #fff3e0;
            color: #ef6c00;
        }
        
        .dimension-score.low {
            background: #ffebee;
            color: #c62828;
        }
        
        .dimension-feedback {
            font-size: 0.85rem;
            color: #6c757d;
            line-height: 1.4;
        }
        
        .execution-details {
            margin-top: 1rem;
            padding-top: 1rem;
            border-top: 1px solid #e5e7eb;
            font-size: 0.875rem;
            color: #6c757d;
        }
        
        .test-case-code {
            padding: 1rem;
            overflow-x: auto;
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            font-size: 0.8125rem;
            line-height: 1.5;
            white-space: pre;
        }
        
        /* Stage context indicator */
        .stage-context {
            margin-bottom: 0.5rem;
            padding: 0.5rem 0.75rem;
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 4px;
            font-size: 0.8125rem;
            color: #856404;
        }
        
        /* Streaming indicator */
        .streaming-indicator {
            display: inline-block;
            margin-left: 0.5rem;
        }
        
        .streaming-indicator span {
            display: inline-block;
            width: 4px;
            height: 4px;
            background: #007bff;
            border-radius: 50%;
            margin: 0 1px;
            animation: pulse 1.4s infinite;
        }
        
        .streaming-indicator span:nth-child(2) {
            animation-delay: 0.2s;
        }
        
        .streaming-indicator span:nth-child(3) {
            animation-delay: 0.4s;
        }
        
        @keyframes pulse {
            0%, 60%, 100% { opacity: 0.3; }
            30% { opacity: 1; }
        }
    """


def _generate_qe_javascript() -> str:
    """Generate JavaScript for QE chat functionality"""
    return """
        // QE Chat functionality
        let qeEventSource = null;
        let currentStreamingMessage = null;
        let isStreaming = false;
        
        // Initialize resizer when DOM is ready
        document.addEventListener('DOMContentLoaded', function() {
            const resizer = document.getElementById('resizer');
            const qePanel = document.querySelector('.qe-panel');
            const tracePanel = document.querySelector('.trace-panel');
            
            if (resizer && qePanel && tracePanel) {
                let isResizing = false;
                
                resizer.addEventListener('mousedown', (e) => {
                    isResizing = true;
                    document.body.style.cursor = 'col-resize';
                    e.preventDefault();
                });
                
                document.addEventListener('mousemove', (e) => {
                    if (!isResizing) return;
                    
                    const newWidth = e.clientX;
                    if (newWidth > 400 && newWidth < window.innerWidth - 600) {
                        qePanel.style.width = newWidth + 'px';
                    }
                });
                
                document.addEventListener('mouseup', () => {
                    isResizing = false;
                    document.body.style.cursor = 'default';
                });
            }
        });
        
        // QE Chat functions
        window.sendQEMessage = function() {
            const input = document.getElementById('qe-input');
            const message = input.value.trim();
            
            if (!message || isStreaming) return;
            
            // Clear input
            input.value = '';
            input.style.height = '80px';
            
            // Display user message
            appendMessage('user', message);
            
            // Get stage context if user clicked on a stage
            const stageContext = getCurrentStageContext();
            
            // Start streaming
            startQEStream(message, stageContext);
        }
        
        function getCurrentStageContext() {
            // Check if user has highlighted a stage
            const highlightedStage = document.querySelector('.stage-name.highlighted');
            if (highlightedStage) {
                return {
                    stage_name: highlightedStage.textContent.replace(/📍\\s*/, ''),
                    stage_id: highlightedStage.closest('.stage-header')?.id
                };
            }
            return null;
        }
        
        function startQEStream(message, stageContext) {
            // Close any existing stream
            if (qeEventSource) {
                qeEventSource.close();
            }
            
            // Mark as streaming
            isStreaming = true;
            updateSendButton();
            
            // Build URL with parameters
            const params = new URLSearchParams({
                trace_id: TRACE_ID,
                message: message
            });
            
            if (stageContext) {
                params.append('stage_name', stageContext.stage_name);
                params.append('stage_id', stageContext.stage_id);
            }
            
            const url = `/api/qe/chat/stream?${params}`;
            
            // Create streaming message
            currentStreamingMessage = createStreamingMessage();
            
            // Start SSE connection
            qeEventSource = new EventSource(url);
            
            qeEventSource.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    handleQEStreamData(data);
                } catch (e) {
                    console.error('Error parsing QE stream data:', e);
                }
            };
            
            qeEventSource.onerror = (error) => {
                // Check if the stream is just closing normally
                if (qeEventSource.readyState === EventSource.CLOSED) {
                    console.log('QE stream closed');
                    finishStreaming();
                    return;
                }
                
                console.error('QE stream error:', error);
                finishStreaming();
                if (currentStreamingMessage) {
                    updateStreamingMessage('Error: Connection lost');
                }
            };
        }
        
        function handleQEStreamData(data) {
            if (data.type === 'text') {
                updateStreamingMessage(data.content);
            } else if (data.type === 'report_link') {
                // Handle special report link type
                if (currentStreamingMessage) {
                    // Finish any current streaming message first
                    finishStreaming();
                }
                displayReportLink(data.url, data.text);
            } else if (data.type === 'test_case' || data.type === 'tool_result') {
                // Display test case
                displayTestCase(data.content);
            } else if (data.type === 'action_menu') {
                // Display action menu after test case
                displayActionMenu(data.content);
            } else if (data.type === 'start_evaluation') {
                // Start evaluation
                startEvaluation(data.content);
            } else if (data.type === 'save_test_case') {
                // Save test case
                saveTestCase(data.content);
            } else if (data.type === 'thinking') {
                updateStreamingMessage(data.content, 'thinking');
            } else if (data.type === 'error') {
                updateStreamingMessage('Error: ' + data.content);
                finishStreaming();
            }
        }
        
        function createStreamingMessage() {
            const messageDiv = document.createElement('div');
            messageDiv.className = 'qe-message assistant streaming';
            messageDiv.innerHTML = `
                <div class="message-content">
                    <span class="streaming-content"></span>
                    <span class="streaming-indicator">
                        <span></span><span></span><span></span>
                    </span>
                </div>
            `;
            
            const messagesContainer = document.getElementById('qe-messages');
            messagesContainer.appendChild(messageDiv);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
            
            return messageDiv;
        }
        
        function updateStreamingMessage(content, type = 'text') {
            if (!currentStreamingMessage) return;
            
            const contentSpan = currentStreamingMessage.querySelector('.streaming-content');
            const currentText = contentSpan.textContent;
            
            // Append content
            contentSpan.textContent = currentText + content;
            
            // Update styling if needed
            if (type === 'thinking') {
                currentStreamingMessage.classList.add('thinking');
            }
            
            // Scroll to bottom
            const messagesContainer = document.getElementById('qe-messages');
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }
        
        function finishStreaming() {
            isStreaming = false;
            updateSendButton();
            
            if (currentStreamingMessage) {
                currentStreamingMessage.classList.remove('streaming');
                const indicator = currentStreamingMessage.querySelector('.streaming-indicator');
                if (indicator) indicator.remove();
            }
            
            currentStreamingMessage = null;
            
            if (qeEventSource) {
                qeEventSource.close();
                qeEventSource = null;
            }
        }
        
        function appendMessage(type, content) {
            const messageDiv = document.createElement('div');
            messageDiv.className = `qe-message ${type}`;
            messageDiv.innerHTML = `<div class="message-content">${escapeHtml(content)}</div>`;
            
            const messagesContainer = document.getElementById('qe-messages');
            messagesContainer.appendChild(messageDiv);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }
        
        function displayTestCase(testCaseCode) {
            const messageDiv = document.createElement('div');
            messageDiv.className = 'qe-message assistant';
            messageDiv.innerHTML = `
                <div class="message-content">
                    <div class="test-case-container">
                        <div class="test-case-header">
                            <span>Generated Test Case</span>
                            <button class="copy-btn" onclick="copyTestCase(this, '${escapeHtml(testCaseCode).replace(/'/g, "\\'")}')">
                                Copy
                            </button>
                        </div>
                        <pre class="test-case-code">${escapeHtml(testCaseCode)}</pre>
                    </div>
                </div>
            `;
            
            const messagesContainer = document.getElementById('qe-messages');
            messagesContainer.appendChild(messageDiv);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
            
            // Don't finish streaming here - let action menu display after
            // finishStreaming();
        }
        
        function displayActionMenu(actionMenuText) {
            const messageDiv = document.createElement('div');
            messageDiv.className = 'qe-message assistant';
            
            // Convert the action menu text to formatted HTML with minimal formatting
            const formattedMenu = actionMenuText
                .replace(/\\*\\*(.*?)\\*\\*/g, '<strong>$1</strong>')
                .replace(/\\n\\n/g, '<br><br>')
                .replace(/\\n/g, '<br>')
                .replace(/- /g, '<span style="color: #6c757d; margin-left: 1rem;">•</span> ');
            
            messageDiv.innerHTML = `
                <div class="message-content">
                    <div class="action-menu">
                        ${formattedMenu}
                    </div>
                </div>
            `;
            
            const messagesContainer = document.getElementById('qe-messages');
            messagesContainer.appendChild(messageDiv);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
            
            // Finish streaming after action menu is displayed
            finishStreaming();
        }
        
        function displayReportLink(url, text) {
            const messageDiv = document.createElement('div');
            messageDiv.className = 'qe-message assistant';
            
            messageDiv.innerHTML = `
                <div class="message-content">
                    <a href="${url}" target="_blank" 
                       style="display: inline-block; padding: 0.5rem 1rem; 
                              background: #0066cc; color: white; 
                              text-decoration: none; border-radius: 4px;
                              font-weight: 500; font-size: 14px;
                              box-shadow: 0 2px 4px rgba(0,102,204,0.2);
                              transition: all 0.2s ease;"
                       onmouseover="this.style.background='#0052a3'; this.style.boxShadow='0 4px 8px rgba(0,102,204,0.3)';"
                       onmouseout="this.style.background='#0066cc'; this.style.boxShadow='0 2px 4px rgba(0,102,204,0.2)';">
                        📊 ${text}
                    </a>
                </div>
            `;
            
            const messagesContainer = document.getElementById('qe-messages');
            messagesContainer.appendChild(messageDiv);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }
        
        function copyTestCase(button, code) {
            // Decode the escaped code
            const decodedCode = code.replace(/\\\\'/g, "'");
            
            navigator.clipboard.writeText(decodedCode).then(() => {
                button.textContent = 'Copied!';
                button.classList.add('copied');
                
                setTimeout(() => {
                    button.textContent = 'Copy';
                    button.classList.remove('copied');
                }, 2000);
            }).catch(err => {
                console.error('Failed to copy:', err);
                alert('Failed to copy test case');
            });
        }
        
        async function startEvaluation(testCase) {
            // Create progress tracking message
            const progressDiv = document.createElement('div');
            progressDiv.className = 'qe-message assistant';
            const timestamp = Date.now();
            progressDiv.innerHTML = `
                <div class="message-content">
                    <div class="evaluation-progress">
                        <h4>🚀 Evaluation Progress</h4>
                        <div class="progress-steps" id="progress-steps-${timestamp}">
                            <div class="progress-step pending" data-step="initialization">
                                <span class="step-icon">⏳</span>
                                <span class="step-label">Initializing evaluation...</span>
                            </div>
                            <div class="progress-step pending" data-step="query_execution">
                                <span class="step-icon">⏳</span>
                                <span class="step-label">Running query</span>
                            </div>
                            <div class="progress-step pending" data-step="dimension_evaluation">
                                <span class="step-icon">⏳</span>
                                <span class="step-label">Evaluating dimensions</span>
                            </div>
                            <div class="progress-step pending" data-step="completion">
                                <span class="step-icon">⏳</span>
                                <span class="step-label">Finalizing results</span>
                            </div>
                        </div>
                        <div class="progress-details" id="progress-details-${timestamp}"></div>
                    </div>
                </div>
            `;
            document.getElementById('qe-messages').appendChild(progressDiv);
            scrollToBottom();
            
            const progressStepsId = `progress-steps-${timestamp}`;
            const progressDetailsId = `progress-details-${timestamp}`;
            
            try {
                // Call evaluation API
                const response = await fetch('/api/evaluation/run', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        test_case: testCase,
                        agent_type: 'cmo'
                    })
                });
                
                if (!response.ok) {
                    throw new Error(`Failed to start evaluation: ${response.statusText}`);
                }
                
                const result = await response.json();
                const evaluationId = result.evaluation_id;
                
                // Update initialization step
                updateProgressStep(progressStepsId, 'initialization', 'active');
                
                // Start streaming evaluation progress
                streamEvaluationProgress(evaluationId, progressStepsId, progressDetailsId);
                
            } catch (error) {
                updateProgressStep(progressStepsId, 'initialization', 'error');
                document.getElementById(progressDetailsId).innerHTML = 
                    `<div class="error-message">❌ Failed to start evaluation: ${error.message}</div>`;
            }
        }
        
        function streamEvaluationProgress(evaluationId, progressStepsId, progressDetailsId) {
            const eventSource = new EventSource(`/api/evaluation/stream/${evaluationId}`);
            let currentStep = 'initialization';
            let evaluationCompleted = false;
            
            eventSource.onmessage = (event) => {
                const data = JSON.parse(event.data);
                
                if (data.type === 'progress') {
                    // Update progress based on content
                    const content = data.content.toLowerCase();
                    
                    if (content.includes('initializ')) {
                        updateProgressStep(progressStepsId, 'initialization', 'completed');
                        currentStep = 'initialization';
                    } else if (content.includes('query') || content.includes('cmo agent')) {
                        updateProgressStep(progressStepsId, 'initialization', 'completed');
                        updateProgressStep(progressStepsId, 'query_execution', 'active');
                        currentStep = 'query_execution';
                    } else if (content.includes('evaluat') || content.includes('dimension')) {
                        updateProgressStep(progressStepsId, 'initialization', 'completed');
                        updateProgressStep(progressStepsId, 'query_execution', 'completed');
                        updateProgressStep(progressStepsId, 'dimension_evaluation', 'active');
                        currentStep = 'dimension_evaluation';
                    } else if (content.includes('complet') || content.includes('final')) {
                        updateProgressStep(progressStepsId, 'initialization', 'completed');
                        updateProgressStep(progressStepsId, 'query_execution', 'completed');
                        updateProgressStep(progressStepsId, 'dimension_evaluation', 'completed');
                        updateProgressStep(progressStepsId, 'completion', 'active');
                        currentStep = 'completion';
                    }
                    
                    // Add to details
                    const detailsDiv = document.getElementById(progressDetailsId);
                    if (detailsDiv) {
                        const detailLine = document.createElement('div');
                        detailLine.className = 'progress-detail';
                        detailLine.innerHTML = `<span class="timestamp">${new Date().toLocaleTimeString()}</span> ${data.content}`;
                        detailsDiv.appendChild(detailLine);
                        detailsDiv.scrollTop = detailsDiv.scrollHeight;
                    }
                    
                } else if (data.type === 'result') {
                    // Mark evaluation as completed
                    evaluationCompleted = true;
                    
                    // Mark all steps as completed
                    updateProgressStep(progressStepsId, 'initialization', 'completed');
                    updateProgressStep(progressStepsId, 'query_execution', 'completed');
                    updateProgressStep(progressStepsId, 'dimension_evaluation', 'completed');
                    updateProgressStep(progressStepsId, 'completion', 'completed');
                    
                    // Store result for QE Agent access
                    window.lastEvaluationResult = data.data;
                    console.log('Received evaluation result:', data.data);
                    console.log('Report URL:', data.data.report_url);
                    
                    // Send result to backend QE Agent
                    sendEvaluationResultToQEAgent(data.data);
                    
                    // Display result
                    displayEvaluationResult(data.data);
                    eventSource.close();
                    
                } else if (data.type === 'error') {
                    // Mark current step as error
                    updateProgressStep(progressStepsId, currentStep, 'error');
                    
                    const detailsDiv = document.getElementById(progressDetailsId);
                    if (detailsDiv) {
                        detailsDiv.innerHTML += `<div class="error-message">❌ ${data.content}</div>`;
                    }
                    eventSource.close();
                }
            };
            
            eventSource.onerror = (event) => {
                // Don't show error if evaluation completed successfully
                if (evaluationCompleted) {
                    eventSource.close();
                    return;
                }
                
                // Check if the EventSource is in the CLOSED state (which happens on successful completion)
                if (eventSource.readyState === EventSource.CLOSED) {
                    // This is likely just the stream closing normally
                    console.log('Evaluation stream closed normally');
                    return;
                }
                
                // Only show error if evaluation didn't complete
                updateProgressStep(progressStepsId, currentStep, 'error');
                const detailsDiv = document.getElementById(progressDetailsId);
                if (detailsDiv) {
                    detailsDiv.innerHTML += '<div class="error-message">❌ Lost connection to evaluation stream</div>';
                }
                eventSource.close();
            };
        }
        
        function updateProgressStep(stepsContainerId, stepName, status) {
            const step = document.querySelector(`#${stepsContainerId} [data-step="${stepName}"]`);
            if (!step) return;
            
            // Remove all status classes
            step.classList.remove('pending', 'active', 'completed', 'error');
            step.classList.add(status);
            
            // Update icon based on status
            const iconSpan = step.querySelector('.step-icon');
            switch(status) {
                case 'active':
                    iconSpan.innerHTML = '⚡';
                    break;
                case 'completed':
                    iconSpan.innerHTML = '✅';
                    break;
                case 'error':
                    iconSpan.innerHTML = '❌';
                    break;
                default:
                    iconSpan.innerHTML = '⏳';
            }
        }
        
        async function sendEvaluationResultToQEAgent(result) {
            try {
                const response = await fetch(`/api/qe/evaluation-result/${TRACE_ID}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(result)
                });
                
                if (!response.ok) {
                    console.error('Failed to send evaluation result to QE Agent:', response.statusText);
                } else {
                    console.log('Successfully sent evaluation result to QE Agent');
                }
            } catch (error) {
                console.error('Error sending evaluation result to QE Agent:', error);
            }
        }
        
        function displayEvaluationResult(result) {
            const messageDiv = document.createElement('div');
            messageDiv.className = 'qe-message assistant';
            
            const overallScore = (result.overall_score * 100).toFixed(1);
            const overallScoreNum = parseFloat(overallScore);
            const passed = overallScoreNum >= 70; // Assuming 70% is passing
            
            // Format dimension results
            const dimensionItems = Object.entries(result.dimension_results)
                .map(([name, dim]) => {
                    const score = (dim.normalized_score * 100).toFixed(1);
                    const scoreNum = parseFloat(score);
                    const scoreClass = scoreNum >= 80 ? 'high' : scoreNum >= 50 ? 'medium' : 'low';
                    const displayName = name.replace(/_/g, ' ');
                    // Generate feedback from details or use default
                    let feedback = '';
                    if (dim.feedback) {
                        feedback = dim.feedback;
                    } else if (dim.details) {
                        // Create feedback from details
                        if (dim.details.message) {
                            feedback = dim.details.message;
                        } else if (dim.details.expected && dim.details.actual) {
                            feedback = `Expected: ${dim.details.expected}, Actual: ${dim.details.actual}`;
                        } else if (dim.details.precision !== undefined && dim.details.recall !== undefined) {
                            feedback = `Precision: ${(dim.details.precision * 100).toFixed(1)}%, Recall: ${(dim.details.recall * 100).toFixed(1)}%`;
                        } else {
                            feedback = `Evaluated using ${dim.evaluation_method}`;
                        }
                    } else {
                        feedback = `Evaluated using ${dim.evaluation_method}`;
                    }
                    
                    return `
                        <div class="dimension-item">
                            <div class="dimension-header">
                                <span class="dimension-name">${displayName}</span>
                                <span class="dimension-score ${scoreClass}">${score}%</span>
                            </div>
                            <div class="dimension-feedback">${feedback}</div>
                        </div>
                    `;
                }).join('');
            
            const overallClass = overallScoreNum >= 80 ? 'high' : overallScoreNum >= 50 ? 'medium' : 'low';
            
            messageDiv.innerHTML = `
                <div class="message-content">
                    <div class="evaluation-result">
                        <h4>📊 Evaluation Complete</h4>
                        <div class="result-summary">
                            <div class="overall-score ${overallClass}">
                                <span class="score-label">Overall Score</span>
                                <span class="score-value">${overallScore}%</span>
                            </div>
                            <div class="pass-fail ${passed ? 'passed' : 'failed'}">
                                ${passed ? '✅ PASSED' : '❌ FAILED'}
                            </div>
                        </div>
                        
                        <div class="dimensions-section">
                            <h5>Dimension Scores</h5>
                            ${dimensionItems}
                        </div>
                        
                        <div class="execution-details">
                            <span>🏃 Test Case: ${result.test_case_id}</span><br>
                            <span>⏱️ Execution time: ${(result.execution_time_ms / 1000).toFixed(2)}s</span>
                        </div>
                        
                        ${result.report_url ? `
                        <div class="report-link" style="margin-top: 1rem;">
                            <a href="${result.report_url}" target="_blank" class="view-report-btn" 
                               style="display: inline-block; padding: 0.5rem 1rem; background: #0066cc; 
                                      color: white; text-decoration: none; border-radius: 4px;">
                                📊 View Full Evaluation Report
                            </a>
                        </div>
                        ` : ''}
                    </div>
                    
                    <div class="action-menu" style="margin-top: 20px; padding: 1rem; background: #f8f9fa; border-radius: 8px;">
                        <strong>What would you like to do next?</strong><br><br>
                        
                        <strong>Continue testing:</strong><br>
                        • Type "new" to create another test case<br>
                        • Type "refine" to update this test case<br>
                        • Type "save" to save this test case<br><br>
                        
                        <strong>View results:</strong><br>
                        • Type "details" for full evaluation report<br>
                        • Type "export" to download results
                    </div>
                </div>
            `;
            
            const messagesContainer = document.getElementById('qe-messages');
            messagesContainer.appendChild(messageDiv);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }
        
        function scrollToBottom() {
            const messages = document.getElementById('qe-messages');
            if (messages) {
                messages.scrollTop = messages.scrollHeight;
            }
        }
        
        async function saveTestCase(testCase) {
            try {
                const response = await fetch('/api/evaluation/test-case/save', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        test_case: testCase,
                        session_id: window.currentTraceId // Use trace ID as session
                    })
                });
                
                if (!response.ok) {
                    throw new Error(`Failed to save: ${response.statusText}`);
                }
                
                const result = await response.json();
                appendMessage('assistant', `✅ ${result.message}`);
                
            } catch (error) {
                appendMessage('assistant', `❌ Failed to save test case: ${error.message}`);
            }
        }
        
        function updateSendButton() {
            const button = document.querySelector('.qe-send-btn');
            const input = document.getElementById('qe-input');
            
            if (isStreaming) {
                button.disabled = true;
                button.textContent = 'Streaming...';
            } else {
                button.disabled = input.value.trim() === '';
                button.textContent = 'Send';
            }
        }
        
        function escapeHtml(str) {
            const div = document.createElement('div');
            div.textContent = str;
            return div.innerHTML;
        }
        
        // Auto-resize textarea
        document.addEventListener('DOMContentLoaded', () => {
            const textarea = document.getElementById('qe-input');
            if (textarea) {
                textarea.addEventListener('input', () => {
                    textarea.style.height = '80px';
                    textarea.style.height = Math.min(textarea.scrollHeight, 200) + 'px';
                    updateSendButton();
                });
                
                textarea.addEventListener('keydown', (e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        sendQEMessage();
                    }
                });
            }
            
            // Initialize stage click integration
            document.addEventListener('click', (e) => {
                const stageHeader = e.target.closest('.stage-header');
                if (stageHeader && e.ctrlKey) {
                    // Add context to QE input
                    const stageName = stageHeader.querySelector('.stage-name').textContent.replace(/📍\\s*/, '');
                    const input = document.getElementById('qe-input');
                    input.value = `Looking at stage "${stageName}": `;
                    input.focus();
                }
            });
        });
    """


def _generate_qe_chat_panel(trace: CompleteTrace) -> str:
    """Generate the QE chat panel HTML"""
    # Extract query from trace
    query = "Unknown query"
    for event in trace.events:
        if event.event_type == TraceEventType.USER_QUERY:
            query = event.data.get("query", query)
            break
    
    return f"""
        <div class="qe-header">
            <h2>🔍 QE Agent - Test Case Generator</h2>
            <p>Analyze this trace and generate test cases for evaluation</p>
        </div>
        
        <div class="qe-messages" id="qe-messages">
            <div class="qe-message assistant">
                <div class="message-content">
                    Hello! I'm the QE (Quality Evaluation) Agent. I can help you analyze this trace and generate test cases for the CMO agent evaluation.
                    
                    <br><br>
                    <strong>Query analyzed:</strong> "{html.escape(query[:100])}{'...' if len(query) > 100 else ''}"
                    
                    <br><br>
                    Tell me what issues you've identified, or click on a stage in the trace viewer (with Ctrl) to discuss specific problems.
                </div>
            </div>
        </div>
        
        <div class="qe-input-container">
            <div class="qe-input-wrapper">
                <textarea 
                    id="qe-input" 
                    placeholder="Describe the issue you found (e.g., 'The complexity should be COMPLEX not STANDARD')"
                    rows="3"
                ></textarea>
                <button class="qe-send-btn" onclick="sendQEMessage()">Send</button>
            </div>
        </div>
    """