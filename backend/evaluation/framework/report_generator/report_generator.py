"""
Main Report Generator for CMO Agent Evaluation

Coordinates HTML report generation and visualization creation.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from .html_report_generator import HTMLReportGenerator


class EvaluationReportGenerator:
    """Main report generator that creates HTML reports and visualizations"""
    
    def __init__(self, test_run_dir: Path):
        self.test_run_dir = test_run_dir
        self.report_dir = test_run_dir / "report"
        self.report_dir.mkdir(exist_ok=True, parents=True)
        
        # Set style for visualizations
        plt.style.use('seaborn-v0_8-darkgrid')
        sns.set_palette("husl")
    
    def generate_report(self, evaluation_results: Dict[str, Any]) -> Path:
        """Generate comprehensive HTML evaluation report with visualizations"""
        
        # Generate visualizations first
        if "results" in evaluation_results:
            self._generate_visualizations(evaluation_results, self.report_dir)
        
        # Generate HTML report
        html_generator = HTMLReportGenerator(self.test_run_dir)
        html_path = html_generator.generate_html_report(evaluation_results)
        
        # Save raw data to report directory
        raw_data_path = self.report_dir / "raw_results.json"
        with open(raw_data_path, 'w') as f:
            json.dump(evaluation_results, f, indent=2, default=str)
        
        return self.report_dir
    
    def _generate_visualizations(self, eval_results: Dict[str, Any], report_dir: Path):
        """Generate visualization charts"""
        
        results = eval_results.get("results", [])
        
        # 1. Overall Performance Bar Chart
        if results:
            self._create_dimension_scores_chart(results, report_dir)
        
        # 2. Complexity Accuracy Chart  
        if results:
            self._create_complexity_performance_chart(results, report_dir)
        
        # 3. Response Time Distribution
        if results:
            self._create_response_time_distribution(results, report_dir)
        
        # 4. Specialty Selection Heatmap
        if results:
            self._create_specialty_heatmap(results, report_dir)
    
    def _create_dimension_scores_chart(self, results: List[Dict[str, Any]], report_dir: Path):
        """Create bar chart of dimension scores vs targets"""
        if not results:
            return
        
        # Calculate dimension scores from results
        dimensions_data = {
            'complexity_classification': {'scores': [], 'target': 0.90},
            'specialty_selection': {'scores': [], 'target': 0.85},
            'analysis_quality': {'scores': [], 'target': 0.80},
            'tool_usage': {'scores': [], 'target': 0.90},
            'response_structure': {'scores': [], 'target': 0.95}
        }
        
        for result in results:
            dimensions_data['complexity_classification']['scores'].append(
                1.0 if result.get('complexity_correct', False) else 0.0
            )
            dimensions_data['specialty_selection']['scores'].append(
                result.get('specialty_f1', 0.0)
            )
            dimensions_data['analysis_quality']['scores'].append(
                result.get('analysis_quality_score', 0.0)
            )
            dimensions_data['tool_usage']['scores'].append(
                result.get('tool_success_rate', 0.0)
            )
            dimensions_data['response_structure']['scores'].append(
                1.0 if result.get('response_valid', False) else 0.0
            )
        
        dimensions = []
        scores = []
        targets = []
        
        for dim, data in dimensions_data.items():
            if data['scores']:
                dimensions.append(dim.replace("_", " ").title())
                scores.append(sum(data['scores']) / len(data['scores']))
                targets.append(data['target'])
        
        x = np.arange(len(dimensions))
        width = 0.35
        
        fig, ax = plt.subplots(figsize=(10, 6))
        bars1 = ax.bar(x - width/2, scores, width, label='Actual Score', alpha=0.8)
        bars2 = ax.bar(x + width/2, targets, width, label='Target Score', alpha=0.8)
        
        ax.set_xlabel('Evaluation Dimension')
        ax.set_ylabel('Score')
        ax.set_title('CMO Agent Performance by Dimension')
        ax.set_xticks(x)
        ax.set_xticklabels(dimensions, rotation=45, ha='right')
        ax.legend()
        ax.set_ylim(0, 1.1)
        
        # Add value labels on bars
        for bars in [bars1, bars2]:
            for bar in bars:
                height = bar.get_height()
                ax.annotate(f'{height:.2f}',
                          xy=(bar.get_x() + bar.get_width() / 2, height),
                          xytext=(0, 3),
                          textcoords="offset points",
                          ha='center', va='bottom')
        
        plt.tight_layout()
        plt.savefig(report_dir / "dimension_scores.png", dpi=300, bbox_inches='tight')
        plt.close()
    
    def _create_complexity_performance_chart(self, results: List[Dict[str, Any]], report_dir: Path):
        """Create chart showing performance by complexity level"""
        if not results:
            return
            
        # Group results by complexity
        by_complexity = {}
        for result in results:
            complexity = result.get('expected_complexity', 'UNKNOWN').upper()
            if complexity not in by_complexity:
                by_complexity[complexity] = {
                    'correct': [],
                    'f1_scores': [],
                    'quality_scores': []
                }
            
            by_complexity[complexity]['correct'].append(
                1.0 if result.get('complexity_correct', False) else 0.0
            )
            by_complexity[complexity]['f1_scores'].append(
                result.get('specialty_f1', 0.0)
            )
            by_complexity[complexity]['quality_scores'].append(
                result.get('analysis_quality_score', 0.0)
            )
        
        complexities = []
        accuracies = []
        f1_scores = []
        quality_scores = []
        
        for complexity, data in by_complexity.items():
            complexities.append(complexity)
            accuracies.append(sum(data['correct']) / len(data['correct']) if data['correct'] else 0)
            f1_scores.append(sum(data['f1_scores']) / len(data['f1_scores']) if data['f1_scores'] else 0)
            quality_scores.append(sum(data['quality_scores']) / len(data['quality_scores']) if data['quality_scores'] else 0)
        
        x = np.arange(len(complexities))
        width = 0.25
        
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.bar(x - width, accuracies, width, label='Complexity Accuracy', alpha=0.8)
        ax.bar(x, f1_scores, width, label='Specialty F1', alpha=0.8)
        ax.bar(x + width, quality_scores, width, label='Analysis Quality', alpha=0.8)
        
        ax.set_xlabel('Query Complexity')
        ax.set_ylabel('Score')
        ax.set_title('Performance Metrics by Query Complexity')
        ax.set_xticks(x)
        ax.set_xticklabels(complexities)
        ax.legend()
        ax.set_ylim(0, 1.1)
        
        plt.tight_layout()
        plt.savefig(report_dir / "complexity_performance.png", dpi=300, bbox_inches='tight')
        plt.close()
    
    def _create_response_time_distribution(self, individual_results: List[Dict[str, Any]], report_dir: Path):
        """Create histogram of response times"""
        # Handle different field names for response time
        response_times = []
        for r in individual_results:
            if "response_time_ms" in r:
                response_times.append(r["response_time_ms"])
            elif "total_response_time_ms" in r:
                response_times.append(r["total_response_time_ms"])
            elif "response_time" in r:
                response_times.append(r["response_time"])
        
        if not response_times:
            return
        
        plt.figure(figsize=(10, 6))
        plt.hist(response_times, bins=30, alpha=0.7, edgecolor='black')
        plt.axvline(np.mean(response_times), color='red', linestyle='dashed', 
                   linewidth=2, label=f'Mean: {np.mean(response_times):.0f}ms')
        plt.axvline(np.percentile(response_times, 95), color='orange', linestyle='dashed', 
                   linewidth=2, label=f'P95: {np.percentile(response_times, 95):.0f}ms')
        
        plt.xlabel('Response Time (ms)')
        plt.ylabel('Frequency')
        plt.title('Response Time Distribution')
        plt.legend()
        
        plt.tight_layout()
        plt.savefig(report_dir / "response_time_distribution.png", dpi=300, bbox_inches='tight')
        plt.close()
    
    def _create_specialty_heatmap(self, individual_results: List[Dict[str, Any]], report_dir: Path):
        """Create heatmap showing specialty selection patterns"""
        # Collect specialty co-occurrence data
        specialty_pairs = {}
        
        for result in individual_results:
            if result.get("actual_specialties"):
                # Parse the specialty string (it's stored as a string representation of a set)
                spec_str = result["actual_specialties"]
                try:
                    # Parse the set string
                    if spec_str.startswith("{") and spec_str.endswith("}"):
                        spec_str = spec_str[1:-1]
                    specialties = sorted([s.strip().strip("'") for s in spec_str.split(",") if s.strip()])
                    
                    for i, spec1 in enumerate(specialties):
                        for spec2 in specialties[i:]:
                            pair = (spec1, spec2)
                            if pair not in specialty_pairs:
                                specialty_pairs[pair] = 0
                            specialty_pairs[pair] += 1
                except:
                    continue
        
        if not specialty_pairs:
            return
        
        # Create matrix
        all_specialties = sorted(set(s for pair in specialty_pairs.keys() for s in pair))
        matrix = np.zeros((len(all_specialties), len(all_specialties)))
        
        for (spec1, spec2), count in specialty_pairs.items():
            i = all_specialties.index(spec1)
            j = all_specialties.index(spec2)
            matrix[i][j] = count
            if i != j:
                matrix[j][i] = count
        
        # Create heatmap
        plt.figure(figsize=(10, 8))
        sns.heatmap(matrix, 
                   xticklabels=[s.replace("_", " ").title() for s in all_specialties],
                   yticklabels=[s.replace("_", " ").title() for s in all_specialties],
                   annot=True, fmt='.0f', cmap='YlOrRd')
        
        plt.title('Specialty Co-occurrence Heatmap')
        plt.tight_layout()
        plt.savefig(report_dir / "specialty_heatmap.png", dpi=300, bbox_inches='tight')
        plt.close()