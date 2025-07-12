"""
HTML Report Generator for CMO Agent Evaluation

Generates beautiful HTML reports using the designer's template with Jinja2 templating.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
from jinja2 import Environment, FileSystemLoader

class HTMLReportGenerator:
    """Generates styled HTML evaluation reports"""
    
    def __init__(self, test_run_dir: Path):
        self.test_run_dir = test_run_dir
        self.report_dir = test_run_dir / "report"
        self.report_dir.mkdir(exist_ok=True, parents=True)
        
        # Setup Jinja2 environment
        template_dir = Path(__file__).parent
        self.env = Environment(loader=FileSystemLoader(template_dir))
        
    def generate_html_report(self, evaluation_results: Dict[str, Any]) -> Path:
        """Generate beautiful HTML report using designer template"""
        
        # Prepare template data
        template_data = self._prepare_template_data(evaluation_results)
        
        # Load template and render
        template = self.env.get_template("report_template.html")
        html_content = template.render(**template_data)
        
        # Save HTML report
        html_path = self.report_dir / "report.html"
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return html_path
    
    def _prepare_template_data(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare all data needed for the template"""
        
        # New format from the evaluation framework
        if "results" not in results:
            raise ValueError("No evaluation results found")
            
        eval_results = results
        individual_results = results.get("results", [])
        
        # Basic report info
        test_suite = results.get('test_type', 'Unknown').replace('-', ' ').title()
        timestamp = results.get('timestamp', datetime.now().isoformat())[:19]
        
        # Executive summary data  
        summary = eval_results.get("summary", {})
        
        # Get overall result and score
        overall_result = "PASS" if summary.get("overall_success", False) else "FAIL"
        overall_score = summary.get("success_rate", 0.0) * 100
        
        # Get test statistics
        total_tests = 0
        if "aggregated" in eval_results:
            metrics = eval_results["aggregated"]
            total_tests = metrics.get("total_tests", 0)
        else:
            total_tests = len(individual_results)
        
        # Failed dimensions
        failed_dimensions = []
        dimension_scores = self._calculate_dimension_scores(individual_results)
        for dim, data in dimension_scores.items():
            if not data['passed']:
                failed_dimensions.append(dim.replace('_', ' ').title())
        
        # Test case summary
        test_summary = []
        tests_passed = 0
        
        for result in individual_results:
            failed_dims = self._get_failed_dimensions(result)
            # A test passes only if NO dimensions failed
            test_passed = len(failed_dims) == 0
            if test_passed:
                tests_passed += 1
            
            test_summary.append({
                'test_case_id': result.get('test_case_id', result.get('id', 'Unknown')),
                'status': "✅ PASS" if test_passed else "❌ FAIL",
                'status_color': "rgba(16,185,129,0.2)" if test_passed else "rgba(239,68,68,0.2)",
                'status_text_color': "#6ee7b7" if test_passed else "#fca5a5",
                'failed_dimensions_text': ", ".join(failed_dims) if failed_dims else "None",
                'complexity': result.get('expected_complexity', 'Unknown'),
                'complexity_color': self._get_complexity_color(result.get('expected_complexity', '')),
                'complexity_text_color': self._get_complexity_text_color(result.get('expected_complexity', ''))
            })
        
        # Dimension performance - calculate from individual results
        dimension_performance = []
        for dim, data in dimension_scores.items():
            passed = data['passed']
            dimension_performance.append({
                'name': dim.replace('_', ' ').title(),
                'score_percent': f"{data['score_percent']:.1f}",
                'target_percent': f"{data['target_percent']:.1f}",
                'score_color': "#10b981" if passed else "#ef4444",
                'progress_gradient': "linear-gradient(to right, #10b981, #059669)" if passed else "linear-gradient(to right, #ef4444, #dc2626)",
                'method_icon': self._get_method_icon(dim),
                'method': self._get_method_name(dim),
                'description': self._get_dimension_description(dim)
            })
        
        # Dimension failure details
        dimension_failure_details = []
        dim_counts = self._calculate_dimension_failures(individual_results)
        for dim, failed_count in dim_counts.items():
            if failed_count > 0:
                percentage = (failed_count / total_tests * 100)
                dimension_failure_details.append({
                    'dimension': dim.replace('_', ' ').title(),
                    'failed_count': failed_count,
                    'total_count': total_tests,
                    'percentage': f"{percentage:.0f}"
                })
        
        # Failure patterns
        failure_patterns = self._extract_failure_patterns(eval_results)
        
        # Test cases detailed
        test_cases = []
        for result in individual_results:
            test_cases.append(self._prepare_test_case_data(result))
        
        return {
            'report_title': 'CMO Agent Evaluation Report',
            'test_suite': test_suite,
            'test_suite_description': self._get_test_suite_description(test_suite),
            'test_suite_detailed_description': self._get_test_suite_detailed_description(test_suite),
            'timestamp': timestamp,
            'overall_result': overall_result,
            'overall_result_icon': "🔴" if overall_result == 'FAIL' else "🟢",
            'overall_result_color': "linear-gradient(135deg, #ef4444, #dc2626)" if overall_result == 'FAIL' else "linear-gradient(135deg, #10b981, #059669)",
            'overall_score': f"{overall_score:.1f}",
            'total_tests': total_tests,
            'failed_dimensions': failed_dimensions,
            'test_summary': test_summary,
            'tests_passed': tests_passed,
            'dimension_performance': dimension_performance,
            'dimension_failure_details': dimension_failure_details,
            'failure_patterns': failure_patterns,
            'prompts_tested': self._get_prompts_tested(),
            'test_cases': test_cases,
            'additional_charts': self._get_additional_charts()
        }
    
    def _calculate_dimension_scores(self, results: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Calculate dimension scores from individual results"""
        dimensions = {
            'complexity_classification': {'target': 0.90, 'scores': []},
            'specialty_selection': {'target': 0.85, 'scores': []},
            'analysis_quality': {'target': 0.80, 'scores': []},
            'tool_usage': {'target': 0.90, 'scores': []},
            'response_structure': {'target': 0.95, 'scores': []}
        }
        
        for result in results:
            # Complexity classification
            if 'complexity_correct' in result:
                dimensions['complexity_classification']['scores'].append(
                    1.0 if result['complexity_correct'] else 0.0
                )
            
            # Specialty selection
            if 'specialty_f1' in result:
                dimensions['specialty_selection']['scores'].append(result['specialty_f1'])
            
            # Analysis quality
            if 'analysis_quality_score' in result:
                dimensions['analysis_quality']['scores'].append(result['analysis_quality_score'])
            
            # Tool usage
            if 'tool_success_rate' in result:
                dimensions['tool_usage']['scores'].append(result['tool_success_rate'])
            
            # Response structure
            if 'response_valid' in result:
                dimensions['response_structure']['scores'].append(
                    1.0 if result['response_valid'] else 0.0
                )
        
        # Calculate averages and determine pass/fail
        dimension_results = {}
        for dim, data in dimensions.items():
            if data['scores']:
                avg_score = sum(data['scores']) / len(data['scores'])
                dimension_results[dim] = {
                    'score_percent': avg_score * 100,
                    'target_percent': data['target'] * 100,
                    'passed': avg_score >= data['target']
                }
        
        return dimension_results
    
    def _get_failed_dimensions(self, result: Dict[str, Any]) -> List[str]:
        """Get list of failed dimensions for a test result"""
        failed = []
        if not result.get('complexity_correct', False):
            failed.append("Complexity")
        if result.get('specialty_f1', 0) < 0.85:
            failed.append("Specialists")
        if result.get('analysis_quality_score', 0) < 0.80:
            failed.append("Quality")
        if result.get('tool_success_rate', 0) < 0.90:
            failed.append("Tools")
        if not result.get('response_valid', False):
            failed.append("Structure")
        return failed
    
    def _get_complexity_color(self, complexity: str) -> str:
        """Get background color for complexity badge"""
        if complexity.upper() == 'COMPLEX':
            return "rgba(168,85,247,0.2)"
        return "rgba(59,130,246,0.2)"
    
    def _get_complexity_text_color(self, complexity: str) -> str:
        """Get text color for complexity badge"""
        if complexity.upper() == 'COMPLEX':
            return "#d8b4fe"
        return "#93bbfc"
    
    def _get_method_icon(self, dimension: str) -> str:
        """Get method icon for dimension"""
        icons = {
            "complexity_classification": "🔄",
            "specialty_selection": "🧠",
            "analysis_quality": "🧠",
            "tool_usage": "🔧",
            "response_structure": "🔧"
        }
        return icons.get(dimension, "🔧")
    
    def _get_method_name(self, dimension: str) -> str:
        """Get method name for dimension"""
        methods = {
            "complexity_classification": "Hybrid",
            "specialty_selection": "LLM Judge",
            "analysis_quality": "LLM Judge",
            "tool_usage": "Deterministic",
            "response_structure": "Deterministic"
        }
        return methods.get(dimension, "Deterministic")
    
    def _get_dimension_description(self, dimension: str) -> str:
        """Get description for dimension"""
        descriptions = {
            "complexity_classification": "Accuracy of query complexity classification",
            "specialty_selection": "Precision in selecting appropriate medical specialists",
            "analysis_quality": "Comprehensiveness of medical analysis",
            "tool_usage": "Effectiveness of tool calls",
            "response_structure": "Compliance with XML format"
        }
        return descriptions.get(dimension, "")
    
    def _calculate_dimension_failures(self, results: List[Dict[str, Any]]) -> Dict[str, int]:
        """Calculate failure counts by dimension"""
        counts = {
            "complexity_classification": 0,
            "specialty_selection": 0,
            "analysis_quality": 0,
            "tool_usage": 0,
            "response_structure": 0
        }
        
        for r in results:
            if not r.get("complexity_correct", False):
                counts["complexity_classification"] += 1
            if r.get("specialty_f1", 0) < 0.85:
                counts["specialty_selection"] += 1
            if r.get("analysis_quality_score", 0) < 0.8:
                counts["analysis_quality"] += 1
            if r.get("tool_success_rate", 0) < 0.9:
                counts["tool_usage"] += 1
            if not r.get("response_valid", False):
                counts["response_structure"] += 1
        
        return counts
    
    def _extract_failure_patterns(self, eval_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract failure patterns for the report"""
        patterns = []
        
        # Get individual results
        individual_results = eval_results.get("results", [])
        if not individual_results:
            return patterns
        
        # Analyze patterns
        dim_counts = self._calculate_dimension_failures(individual_results)
        total_tests = len(individual_results)
        
        if dim_counts["complexity_classification"] > 0:
            patterns.append({
                'title': 'Complexity Classification Issues',
                'description': f'Found {dim_counts["complexity_classification"]} test(s) with misclassified complexity.',
                'common_pattern': 'The CMO is over-analyzing straightforward requests by adding unnecessary clinical interpretation and specialist requirements.'
            })
        
        if dim_counts["analysis_quality"] > 0:
            patterns.append({
                'title': 'Analysis Quality Issues',
                'description': f'Found {dim_counts["analysis_quality"]} test(s) below quality threshold.',
                'common_pattern': 'Comprehensive Approach component failing due to missed key medical concepts and keywords.'
            })
        
        return patterns
    
    def _get_test_suite_description(self, test_suite: str) -> str:
        """Get short description for test suite"""
        if test_suite.lower() == "real world":
            return "Production-grade test cases derived from actual user queries and clinical scenarios"
        return "Comprehensive evaluation of agent capabilities"
    
    def _get_test_suite_detailed_description(self, test_suite: str) -> str:
        """Get detailed description for test suite"""
        if test_suite.lower() == "real world":
            return "The Real World test suite evaluates the CMO Agent's performance on queries taken from production usage, representing the complexity and nuance of actual medical questions. These tests validate the agent's ability to handle real clinical scenarios with appropriate medical reasoning, specialist selection, and comprehensive analysis."
        return ""
    
    def _get_prompts_tested(self) -> List[Dict[str, str]]:
        """Get list of prompts being tested"""
        return [
            {
                'filename': '1_initial_analysis.txt',
                'url': '../../../services/agents/cmo/prompts/1_initial_analysis.txt',
                'description': 'Analyzes query complexity'
            },
            {
                'filename': '2_initial_analysis_summarize.txt',
                'url': '../../../services/agents/cmo/prompts/2_initial_analysis_summarize.txt',
                'description': 'Summarizes findings'
            },
            {
                'filename': '3_task_creation.txt',
                'url': '../../../services/agents/cmo/prompts/3_task_creation.txt',
                'description': 'Creates specialist tasks'
            }
        ]
    
    def _prepare_test_case_data(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare data for a single test case"""
        failed_dimensions = self._get_failed_dimensions(result)
        test_passed = len(failed_dimensions) == 0
        
        # Basic test info
        test_data = {
            'test_case_id': result['test_case_id'],
            'query': result['query'],
            'status_icon': "✅" if test_passed else "❌",
            'status_text': "PASSED" if test_passed else "FAILED",
            'status_badge_color': "linear-gradient(135deg, #10b981, #059669)" if test_passed else "linear-gradient(135deg, #ef4444, #dc2626)",
            'approach_text': result.get('approach_text', ''),
            'response_time': f"{result.get('total_response_time_ms', 0) / 1000:.1f}" if result.get('total_response_time_ms') else None,
            'evaluation_dimensions': self._prepare_evaluation_dimensions(result),
            'quality_breakdown': None,
            'total_quality_score': None,
            'failure_analysis': None
        }
        
        # Add quality breakdown if quality failed
        if result.get('analysis_quality_score', 1.0) < 0.80 and 'quality_breakdown' in result:
            test_data['quality_breakdown'] = self._prepare_quality_breakdown(result)
            test_data['total_quality_score'] = f"{result.get('analysis_quality_score', 0):.3f}"
        
        # Add failure analysis
        if failed_dimensions:
            test_data['failure_analysis'] = self._prepare_failure_analysis(result, failed_dimensions)
        
        return test_data
    
    def _prepare_evaluation_dimensions(self, result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Prepare evaluation dimensions table data"""
        dimensions = []
        
        # Complexity Classification
        complexity_score = 1.0 if result['complexity_correct'] else 0.0
        complexity_status = "✅ PASS" if result['complexity_correct'] else "❌ FAIL"
        dimensions.append({
            'name': 'Complexity Classification',
            'expected': result['expected_complexity'],
            'actual': result.get('actual_complexity', 'N/A').upper(),
            'score': f"{complexity_score:.2f}",
            'target': '0.90',
            'status': complexity_status,
            'status_color': "rgba(16,185,129,0.2)" if result['complexity_correct'] else "rgba(239,68,68,0.2)",
            'status_text_color': "#6ee7b7" if result['complexity_correct'] else "#fca5a5"
        })
        
        # Specialist Selection
        f1_score = result.get('specialty_f1', 0)
        specialists_status = "✅ PASS" if f1_score >= 0.85 else "❌ FAIL"
        # Handle both sets and string representations
        expected_specs = result.get('expected_specialties', set())
        actual_specs = result.get('actual_specialties', set())
        if isinstance(expected_specs, str):
            expected_specs = eval(expected_specs)
        if isinstance(actual_specs, str):
            actual_specs = eval(actual_specs)
        dimensions.append({
            'name': 'Specialist Selection',
            'expected': ', '.join(sorted(expected_specs)),
            'actual': ', '.join(sorted(actual_specs)),
            'score': f"{f1_score:.2f}",
            'target': '0.85',
            'status': specialists_status,
            'status_color': "rgba(16,185,129,0.2)" if f1_score >= 0.85 else "rgba(239,68,68,0.2)",
            'status_text_color': "#6ee7b7" if f1_score >= 0.85 else "#fca5a5",
            'expected_small': True,
            'actual_small': True
        })
        
        # Analysis Quality
        quality_score = result.get('analysis_quality_score', 0)
        quality_status = "✅ PASS" if quality_score >= 0.80 else "❌ FAIL"
        dimensions.append({
            'name': 'Analysis Quality',
            'expected': '≥0.80',
            'actual': f"{quality_score:.2f}",
            'score': f"{quality_score:.2f}",
            'target': '0.80',
            'status': quality_status,
            'status_color': "rgba(16,185,129,0.2)" if quality_score >= 0.80 else "rgba(239,68,68,0.2)",
            'status_text_color': "#6ee7b7" if quality_score >= 0.80 else "#fca5a5"
        })
        
        # Tool Usage
        tool_score = result.get('tool_success_rate', 0)
        tool_status = "✅ PASS" if tool_score >= 0.90 else "❌ FAIL"
        tool_calls = result.get('tool_calls_made', 0)
        dimensions.append({
            'name': 'Tool Usage',
            'expected': 'Effective',
            'actual': f"{tool_calls} calls",
            'score': f"{tool_score:.2f}",
            'target': '0.90',
            'status': tool_status,
            'status_color': "rgba(16,185,129,0.2)" if tool_score >= 0.90 else "rgba(239,68,68,0.2)",
            'status_text_color': "#6ee7b7" if tool_score >= 0.90 else "#fca5a5"
        })
        
        # Response Structure
        structure_score = 1.0 if result.get('response_valid', False) else 0.0
        structure_status = "✅ PASS" if structure_score >= 0.95 else "❌ FAIL"
        dimensions.append({
            'name': 'Response Structure',
            'expected': 'Valid XML',
            'actual': 'Valid' if result.get('response_valid', False) else 'Invalid',
            'score': f"{structure_score:.2f}",
            'target': '0.95',
            'status': structure_status,
            'status_color': "rgba(16,185,129,0.2)" if structure_score >= 0.95 else "rgba(239,68,68,0.2)",
            'status_text_color': "#6ee7b7" if structure_score >= 0.95 else "#fca5a5"
        })
        
        return dimensions
    
    def _prepare_quality_breakdown(self, result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Prepare quality breakdown table data"""
        breakdown = []
        
        component_descriptions = {
            "data_gathering": "Made appropriate tool calls to gather health data",
            "context_awareness": "Mentioned dates, timeframes, or temporal context",
            "specialist_rationale": "Clear reasoning provided for specialist selection",
            "comprehensive_approach": "Coverage of expected medical concepts and keywords",
            "concern_identification": "Identified specific health concerns or risks"
        }
        
        weights = {
            "data_gathering": 0.20,
            "context_awareness": 0.15,
            "specialist_rationale": 0.20,
            "comprehensive_approach": 0.25,
            "concern_identification": 0.20
        }
        
        for component, score in result['quality_breakdown'].items():
            weight = weights.get(component, 0.0)
            weighted = weight * score
            description = component_descriptions.get(component, "")
            
            # Special handling for comprehensive_approach to show keywords
            if component == "comprehensive_approach" and score < 0.5:
                if 'key_data_points' in result:
                    approach_text = result.get('approach_text', '').lower()
                    keywords = result['key_data_points']
                    found = []
                    missed = []
                    for kw in keywords:
                        if kw.lower().replace('_', ' ') in approach_text or kw.lower().replace('_', '') in approach_text:
                            found.append(kw)
                        else:
                            missed.append(kw)
                    
                    found_count = len(found)
                    total_count = len(keywords)
                    if missed:
                        description = f"{found_count}/{total_count} keywords. ✗ Missed: {', '.join(missed)}"
                    else:
                        description = f"{found_count}/{total_count} keywords found"
            
            breakdown.append({
                'name': component.replace('_', ' ').title(),
                'weight': f"{weight:.2f}",
                'score': f"{score:.2f}",
                'weighted': f"{weighted:.3f}",
                'description': description
            })
        
        return breakdown
    
    def _prepare_failure_analysis(self, result: Dict[str, Any], failed_dimensions: List[str]) -> List[Dict[str, Any]]:
        """Prepare failure analysis data"""
        analysis = []
        
        # Complexity issues
        if "Complexity" in failed_dimensions:
            if 'complexity_analysis' in result:
                # New format from LLM Judge
                ca = result['complexity_analysis']
                analysis.append({
                    'icon': '⚠️',
                    'title': 'Complexity Classification Issue',
                    'description': ca.get('issue_description', 'Complexity misclassified'),
                    'root_cause': ca.get('reasoning', ''),
                    'priority': ca.get('priority', 'MEDIUM').upper(),
                    'priority_color': self._get_priority_color(ca.get('priority', 'medium')),
                    'prompt_file': ca.get('prompt_file', 'backend/services/agents/cmo/prompts/1_initial_analysis.txt'),
                    'recommendations': ca.get('specific_changes', []),
                    'expected_impact': None
                })
            elif 'complexity_recommendation' in result:
                # Old format (backward compatibility)
                rec = result['complexity_recommendation']
                analysis.append({
                    'icon': '⚠️',
                    'title': 'Complexity Classification Issue',
                    'description': rec['issue_description'],
                    'root_cause': rec.get('reasoning', ''),
                    'priority': rec.get('priority', 'MEDIUM').upper(),
                    'priority_color': self._get_priority_color(rec.get('priority', 'medium')),
                    'prompt_file': rec.get('prompt_file', 'backend/services/agents/cmo/prompts/1_initial_analysis.txt'),
                    'recommendations': rec.get('specific_changes', []),
                    'expected_impact': None
                })
        
        # Specialist selection issues
        if "Specialist" in failed_dimensions and 'specialist_analysis' in result:
            sa = result['specialist_analysis']
            recommendations = sa.get('specific_changes', [])
            
            # Add missing specialist reasons as recommendations if available
            if sa.get('missing_specialists_reason'):
                for spec, reason in sa['missing_specialists_reason'].items():
                    recommendations.append(f"Missing {spec}: {reason}")
            
            analysis.append({
                'icon': '👥',
                'title': 'Specialist Selection Issue',
                'description': sa.get('issue_description', 'Incorrect specialist selection'),
                'root_cause': sa.get('reasoning', ''),
                'priority': sa.get('priority', 'HIGH').upper(),
                'priority_color': self._get_priority_color(sa.get('priority', 'high')),
                'prompt_file': sa.get('prompt_file', 'backend/services/agents/cmo/prompts/3_task_creation.txt'),
                'recommendations': recommendations,
                'expected_impact': f"Better specialist coverage for {', '.join(sa.get('missing_specialists_reason', {}).keys())}" if sa.get('missing_specialists_reason') else None
            })
        
        # Quality issues
        if "Quality" in failed_dimensions and 'quality_analysis' in result:
            qa = result['quality_analysis']
            analysis.append({
                'icon': '📊',
                'title': 'Analysis Quality Issue',
                'description': qa['issue_description'],
                'root_cause': qa.get('root_cause', ''),
                'priority': qa.get('priority', 'MEDIUM').upper(),
                'priority_color': self._get_priority_color(qa.get('priority', 'medium')),
                'prompt_file': qa.get('prompt_file', 'backend/services/agents/cmo/prompts/1_initial_analysis.txt'),
                'recommendations': qa.get('specific_improvements', []),
                'expected_impact': qa.get('expected_impact', '')
            })
        
        return analysis
    
    def _get_priority_color(self, priority: str) -> str:
        """Get color for priority badge"""
        if priority.lower() == 'high':
            return "linear-gradient(135deg, #ef4444, #dc2626)"
        elif priority.lower() == 'medium':
            return "linear-gradient(135deg, #f59e0b, #d97706)"
        else:
            return "linear-gradient(135deg, #10b981, #059669)"
    
    def _get_additional_charts(self) -> List[Dict[str, str]]:
        """Get additional chart data"""
        return [
            {
                'name': 'Complexity Performance',
                'url': './complexity_performance.png',
                'description': 'Metrics by query complexity (STANDARD vs COMPLEX)',
                'insights': 'See if certain query types perform better'
            },
            {
                'name': 'Response Time Distribution',
                'url': './response_time_distribution.png',
                'description': 'Histogram of processing times',
                'insights': 'Understand performance consistency'
            },
            {
                'name': 'Specialty Heatmap',
                'url': './specialty_heatmap.png',
                'description': 'Which specialists are selected together',
                'insights': 'Identify common specialist combinations'
            }
        ]