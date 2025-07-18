"""
Dynamic HTML Report Generator for Agent Evaluation

Uses agent metadata to dynamically generate evaluation reports without hardcoding.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from jinja2 import Environment, FileSystemLoader
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

from evaluation.core.dimensions import (
    EvaluationDimension,
    EvaluationCriteria
)


class DynamicHTMLReportGenerator:
    """Generates evaluation reports dynamically based on agent metadata"""
    
    def __init__(self, test_run_dir: Path, agent_type: str):
        self.test_run_dir = test_run_dir
        self.report_dir = test_run_dir / "report"
        self.report_dir.mkdir(exist_ok=True, parents=True)
        self.agent_type = agent_type
        
        # Get metadata directly from agent class
        self.agent_metadata = None
        
        if agent_type == "cmo":
            from services.agents.cmo.cmo_agent import CMOAgent
            self.agent_metadata = CMOAgent.get_evaluation_metadata()
        elif agent_type == "cardiology":
            from services.agents.specialist.specialist_agent import SpecialistAgent
            from services.agents.models import MedicalSpecialty
            self.agent_metadata = SpecialistAgent.get_evaluation_metadata(MedicalSpecialty.CARDIOLOGY)
        # Add more specialist types as needed
        elif agent_type in ["endocrinology", "laboratory_medicine", "pharmacy", "nutrition", 
                            "preventive_medicine", "data_analysis", "general_practice"]:
            from services.agents.specialist.specialist_agent import SpecialistAgent
            from services.agents.models import MedicalSpecialty
            specialty = MedicalSpecialty(agent_type)
            self.agent_metadata = SpecialistAgent.get_evaluation_metadata(specialty)
        else:
            raise ValueError(f"Unknown agent type: {agent_type}. Agent must provide metadata via get_evaluation_metadata() method.")
        
        # Setup Jinja2 environment
        template_dir = Path(__file__).parent
        self.env = Environment(loader=FileSystemLoader(template_dir))
    
    def generate_html_report(self, evaluation_results: Dict[str, Any]) -> Path:
        """Generate HTML report using agent metadata"""
        
        # Generate visualizations
        if "results" in evaluation_results:
            self._generate_visualizations(evaluation_results)
        
        # Prepare template data with metadata
        template_data = self._prepare_template_data(evaluation_results)
        
        # Add agent-specific metadata
        template_data['agent_metadata'] = self.agent_metadata.to_report_data()
        
        # Load template and render
        template_file = "report_template_health_insight.html"
        template = self.env.get_template(template_file)
        html_content = template.render(**template_data)
        
        # Save HTML report
        html_path = self.report_dir / "report.html"
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # Save raw results
        raw_data_path = self.report_dir / "raw_results.json"
        with open(raw_data_path, 'w') as f:
            json.dump(evaluation_results, f, indent=2, default=str)
        
        return self.report_dir
    
    def _prepare_template_data(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare template data using agent metadata"""
        
        eval_results = results
        individual_results = results.get("results", [])
        
        # Basic report info
        test_suite = results.get('test_type', 'Unknown').replace('-', ' ').title()
        timestamp = results.get('timestamp', datetime.now().isoformat())[:19]
        
        # Calculate dimension scores dynamically based on metadata
        dimension_scores = self._calculate_dimension_scores_dynamic(individual_results)
        
        # Executive summary
        summary = eval_results.get("summary", {})
        overall_result = "PASS" if summary.get("overall_success", False) else "FAIL"
        # Use weighted_score for overall score, not success_rate
        overall_score = summary.get("weighted_score", 0.0) * 100
        
        # Test statistics
        total_tests = len(individual_results) if individual_results else 0
        
        # Calculate failed dimensions dynamically
        failed_dimensions = []
        for dim_name, data in dimension_scores.items():
            if not data['passed']:
                # Convert dimension enum value to display name
                failed_dimensions.append(dim_name.replace('_', ' ').title())
        
        # Test case summary
        test_summary = []
        tests_passed = 0
        
        for result in individual_results:
            failed_dims = self._get_failed_dimensions_dynamic(result)
            # Use evaluation_success (weighted score) for test status
            test_passed = result.get('evaluation_success', False)
            weighted_score = result.get('weighted_score', 0.0)
            
            if test_passed:
                tests_passed += 1
            
            test_summary.append({
                'test_case_id': result.get('test_case_id', 'Unknown'),
                'status': f"✅ PASS ({weighted_score:.1%})" if test_passed else f"❌ FAIL ({weighted_score:.1%})",
                'status_color': "rgba(16,185,129,0.2)" if test_passed else "rgba(239,68,68,0.2)",
                'status_text_color': "#6ee7b7" if test_passed else "#fca5a5",
                'failed_dimensions': failed_dims,
                'failed_dimensions_text': ", ".join(failed_dims) if failed_dims else "None",
                'response_time': result.get('total_response_time_ms', 0),
                'complexity': result.get('expected_complexity', 'Unknown'),
                'complexity_color': self._get_complexity_color(result.get('expected_complexity', '')),
                'complexity_text_color': self._get_complexity_text_color(result.get('expected_complexity', '')),
                'query': result.get('query', 'Query not available'),
                'weighted_score': weighted_score
            })
        
        # Dimension performance - dynamic based on metadata
        dimension_performance = self._prepare_dimension_performance_with_macro_analysis(
            dimension_scores, results.get('macro_analyses', {})
        )
        
        # Get prompts from metadata
        prompts_tested = self._get_prompts_tested_dynamic()
        
        # Test cases detailed
        test_cases = []
        for result in individual_results:
            test_cases.append(self._prepare_test_case_data_dynamic(result))
        
        # Collect prompt improvements from all test cases
        prompt_improvements = self._collect_prompt_improvements(individual_results)
        
        # Prepare consolidated recommendations from macro analysis
        consolidated_recommendations = self._prepare_consolidated_recommendations(
            results.get('macro_analyses', {})
        )
        
        return {
            'report_title': f'{self.agent_type.upper()} Agent Eval Report',
            'agent_type': self.agent_type,
            'agent_description': self.agent_metadata.description,
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
            'prompts_tested': prompts_tested,
            'test_cases': test_cases,
            'prompt_improvements': prompt_improvements,
            'consolidated_recommendations': consolidated_recommendations,
            'additional_charts': self._get_additional_charts(),
            'summary': summary  # Add summary for template access
        }
    
    def _calculate_dimension_scores_dynamic(self, results: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Calculate dimension scores dynamically based on agent metadata"""
        dimension_scores = {}
        
        # Initialize scores for each dimension defined in metadata
        for criteria in self.agent_metadata.evaluation_criteria:
            dim_name = criteria.dimension.name if hasattr(criteria.dimension, 'name') else str(criteria.dimension)
            dimension_scores[dim_name] = {
                'target': criteria.target_score,
                'scores': [],
                'criteria': criteria
            }
        
        # Collect scores from results
        for result in results:
            # Map result fields to dimensions dynamically
            for dim_name, dim_data in dimension_scores.items():
                score = self._extract_dimension_score(result, dim_name)
                if score is not None:
                    dim_data['scores'].append(score)
        
        # Calculate averages and determine pass/fail
        final_scores = {}
        for dim_name, data in dimension_scores.items():
            if data['scores']:
                avg_score = sum(data['scores']) / len(data['scores'])
                final_scores[dim_name] = {
                    'score_percent': avg_score * 100,
                    'target_percent': data['target'] * 100,
                    'passed': avg_score >= data['target']
                }
        
        return final_scores
    
    def _extract_dimension_score(self, result: Dict[str, Any], dimension: str) -> Optional[float]:
        """Extract score for a dimension from result data"""
        # Only use the metadata-driven dynamic score field
        dynamic_score_key = f"{dimension}_score"
        return result.get(dynamic_score_key, None)
    
    def _get_failed_dimensions_dynamic(self, result: Dict[str, Any]) -> List[str]:
        """Get failed dimensions based on agent metadata"""
        failed = []
        
        for criteria in self.agent_metadata.evaluation_criteria:
            dim_name = criteria.dimension.name if hasattr(criteria.dimension, 'name') else str(criteria.dimension)
            score = self._extract_dimension_score(result, dim_name)
            
            if score is not None and score < criteria.target_score:
                failed.append(dim_name.replace('_', ' ').title())
        
        return failed
    
    def _get_prompts_tested_dynamic(self) -> List[Dict[str, str]]:
        """Get prompts from agent metadata"""
        prompts = []
        
        for prompt in self.agent_metadata.prompts:
            prompts.append({
                'filename': prompt.filename,
                'url': f"../../../services/agents/{self.agent_type}/prompts/{prompt.filename}",
                'description': prompt.description,
                'purpose': prompt.purpose,
                'dimensions': [],  # No longer tracking dimensions per prompt
                'dimension_description': None
            })
        
        return prompts
    
    def _get_method_icon_dynamic(self, criteria: EvaluationCriteria) -> str:
        """Get icon based on evaluation methods used"""
        from evaluation.core.dimensions import EvaluationMethod
        
        methods_found = set()
        components = self.agent_metadata.get_quality_components(criteria.dimension)
        
        # Collect all unique evaluation methods
        for component in components:
            methods_found.add(component.evaluation_method)
        
        # If we have multiple different methods, it's hybrid
        if len(methods_found) > 1:
            return "🔀"  # hybrid
        elif len(methods_found) == 1:
            method = list(methods_found)[0]
            if method == EvaluationMethod.DETERMINISTIC:
                return "🔢"
            elif method == EvaluationMethod.LLM_JUDGE:
                return "🤖"
            else:
                return "🔀"  # default to hybrid icon
        else:
            # No components, use criteria's method
            if criteria.evaluation_method == EvaluationMethod.DETERMINISTIC:
                return "🔢"
            elif criteria.evaluation_method == EvaluationMethod.LLM_JUDGE:
                return "🤖"
            else:
                return "🔀"
    
    def _get_primary_method(self, criteria: EvaluationCriteria) -> str:
        """Get primary evaluation method - returns Hybrid if multiple methods are used"""
        methods_found = set()
        components = self.agent_metadata.get_quality_components(criteria.dimension)
        
        # Collect all unique evaluation methods from components
        for component in components:
            methods_found.add(component.evaluation_method)
        
        # If we have multiple different methods, it's hybrid
        if len(methods_found) > 1:
            return "Hybrid"
        elif len(methods_found) == 1:
            # Single method across all components
            return list(methods_found)[0].value.replace('_', ' ').title()
        else:
            # No components, fallback to the criteria's evaluation method
            return criteria.evaluation_method.value.replace('_', ' ').title()
    
    def _get_method_icon(self, method) -> str:
        """Get method icon for evaluation method enum"""
        # Import here to avoid circular imports
        from evaluation.core.dimensions import EvaluationMethod
        
        if method == EvaluationMethod.DETERMINISTIC:
            return "🔢"
        elif method == EvaluationMethod.LLM_JUDGE:
            return "🤖"
        elif method == EvaluationMethod.HYBRID:
            return "🔀"
        else:
            return "❓"
    
    def _prepare_test_case_data_dynamic(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare test case data using metadata"""
        failed_dimensions = self._get_failed_dimensions_dynamic(result)
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
            'evaluation_dimensions': self._prepare_evaluation_dimensions_dynamic(result),
            'quality_breakdown': None,
            'total_quality_score': None,
            'failure_analysis': None,
            'trace_id': result.get('trace_id'),  # Add trace ID for debugging links
            'has_trace': bool(result.get('trace_id')),  # Boolean for template conditionals
            'trace_date': self._get_trace_date(result)  # Get actual trace date
        }
        
        # Add quality breakdown if available
        if 'quality_breakdown' in result:
            test_data['quality_breakdown'] = self._prepare_quality_breakdown_dynamic(result)
            test_data['total_quality_score'] = f"{result.get('analysis_quality_score', 0):.3f}"
        
        # Add failure analysis
        if failed_dimensions:
            test_data['failure_analysis'] = self._prepare_failure_analysis_dynamic(result, failed_dimensions)
            # Add prompt improvements for this specific test case
            test_data['prompt_improvements'] = self._prepare_test_case_prompt_improvements(result)
        
        return test_data
    
    def _prepare_evaluation_dimensions_dynamic(self, result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Prepare evaluation dimensions using metadata"""
        dimensions = []
        
        for criteria in self.agent_metadata.evaluation_criteria:
            dim_name = criteria.dimension.name if hasattr(criteria.dimension, 'name') else str(criteria.dimension)
            score = self._extract_dimension_score(result, dim_name)
            
            if score is not None:
                # Get expected/actual values based on dimension type
                expected, actual = self._get_dimension_values(result, dim_name)
                
                passed = score >= criteria.target_score
                
                # Get quality components from metadata and breakdowns
                quality_components = None
                dimension_note = None
                
                # Get components from metadata
                components = self.agent_metadata.get_quality_components(criteria.dimension)
                if components:
                    quality_components = []
                    # Get the breakdown for this dimension - map dimension names to actual breakdown keys
                    breakdown_key_map = {
                        'specialty_selection': 'specialty_component_breakdown',
                        'analysis_quality': 'analysis_quality_breakdown',
                        'tool_usage': 'tool_component_breakdown',
                        'response_structure': 'response_component_breakdown'
                    }
                    breakdown_key = breakdown_key_map.get(dim_name, f"{dim_name}_component_breakdown")
                    
                    if breakdown_key in result:
                        breakdown = result[breakdown_key]
                    elif dim_name == 'analysis_quality' and 'quality_breakdown' in result:
                        breakdown = result['quality_breakdown']
                    else:
                        breakdown = {}
                    
                    # Build component data from metadata
                    for component in components:
                        comp_score = breakdown.get(component.name, 0.0)
                        quality_components.append({
                            'name': component.name.replace('_', ' ').title(),
                            'weight': f"{component.weight:.2f}",
                            'score': f"{comp_score:.2f}",
                            'weighted': f"{comp_score * component.weight:.3f}",
                            'description': component.description,
                            'method': component.evaluation_method.value.replace('_', ' ').title(),
                            'method_icon': self._get_method_icon(component.evaluation_method)
                        })
                else:
                    # Add explanatory notes for dimensions without components
                    dimension_notes = {
                        'complexity_classification': 'Binary evaluation: Either the complexity level matches expected or it doesn\'t',
                        'specialty_selection': 'Set-based evaluation: Measures precision/recall/F1 of selected specialties',
                        'tool_usage': 'Binary evaluation: Checks if tools were used effectively',
                        'response_structure': 'Binary evaluation: Validates XML structure compliance'
                    }
                    dimension_note = dimension_notes.get(dim_name)
                
                # Get failure analysis and prompt improvements for failed dimensions
                failure_info = None
                if not passed:
                    failure_info = self._get_dimension_failure_info(result, dim_name)
                
                # Determine if row should be expandable (has components OR has failure info OR has dimension note)
                is_expandable = quality_components is not None or failure_info is not None or dimension_note is not None
                
                dimensions.append({
                    'name': dim_name.replace('_', ' ').title(),
                    'method': self._get_primary_method(criteria),
                    'method_icon': self._get_method_icon_dynamic(criteria),
                    'expected': expected,
                    'actual': actual,
                    'score': f"{score:.2f}",
                    'target': f"{criteria.target_score:.2f}",
                    'status': "✅ PASS" if passed else "❌ FAIL",
                    'status_color': "rgba(16,185,129,0.2)" if passed else "rgba(239,68,68,0.2)",
                    'status_text_color': "#6ee7b7" if passed else "#fca5a5",
                    'expected_small': len(str(expected)) > 50,
                    'actual_small': len(str(actual)) > 50,
                    'is_expandable': is_expandable,
                    'has_components': quality_components is not None,
                    'components': quality_components,
                    'has_failure_info': failure_info is not None,
                    'failure_info': failure_info,
                    'dimension_note': dimension_note
                })
        
        return dimensions
    
    def _get_dimension_failure_info(self, result: Dict[str, Any], dimension: str) -> Optional[Dict[str, Any]]:
        """Get failure analysis and prompt improvements for a dimension"""
        # Check if we have failure analyses (new format)
        if 'failure_analyses' in result and result['failure_analyses']:
            # Find the analysis for this dimension
            for analysis in result['failure_analyses']:
                if analysis.get('dimension') == dimension:
                    # Build failure info from new format
                    failure_info = {
                        'prompt_files': [],
                        'root_cause': analysis.get('root_cause', ''),
                        'recommendations': analysis.get('recommendations', []),
                        'priority': analysis.get('priority', 'medium')
                    }
                    
                    # Add prompt file if available
                    if analysis.get('prompt_file'):
                        prompt_file = analysis['prompt_file']
                        if '/' in prompt_file:
                            prompt_file = prompt_file.split('/')[-1]
                        failure_info['prompt_files'].append({
                            'name': prompt_file,
                            'full_path': f'backend/services/agents/{self.agent_type}/prompts/{prompt_file}'
                        })
                    
                    return failure_info
        
        # Fallback to old format for backward compatibility
        analysis_key_map = {
            'specialty_selection': 'specialist_analysis',
            'analysis_quality': 'quality_analysis',
            'complexity_classification': 'complexity_analysis',
            'tool_usage': 'tool_usage_analysis',
            'response_structure': 'response_structure_analysis'
        }
        
        analysis_key = analysis_key_map.get(dimension)
        if not analysis_key or analysis_key not in result:
            return None
        
        analysis = result[analysis_key]
        
        # Build failure info
        failure_info = {
            'prompt_files': [],
            'root_cause': '',
            'recommendations': []
        }
        
        # Handle specialist analysis
        if dimension == 'specialty_selection':
            prompt_file = analysis.get('prompt_file', '3_assign_specialist_tasks.txt')
            if '/' in prompt_file:
                prompt_file = prompt_file.split('/')[-1]
            
            failure_info['prompt_files'].append({
                'name': prompt_file,
                'full_path': f'backend/services/agents/{self.agent_type}/prompts/{prompt_file}'
            })
            failure_info['root_cause'] = analysis.get('reasoning', analysis.get('issue_description', ''))
            failure_info['recommendations'] = analysis.get('specific_changes', [])
            failure_info['priority'] = analysis.get('priority', 'medium')
            
        # Handle quality analysis  
        elif dimension == 'analysis_quality' and 'prompt_improvements' in analysis:
            failure_info['root_cause'] = analysis.get('root_cause', '')
            for prompt_file, improvements in analysis['prompt_improvements'].items():
                if improvements.get('needs_update'):
                    failure_info['prompt_files'].append({
                        'name': prompt_file,
                        'full_path': f'backend/services/agents/{self.agent_type}/prompts/{prompt_file}'
                    })
                    failure_info['recommendations'].extend(improvements.get('specific_changes', []))
            failure_info['priority'] = analysis.get('overall_priority', 'medium')
        
        # Handle other analyses
        else:
            prompt_file = analysis.get('prompt_file', '')
            if prompt_file:
                if '/' not in prompt_file:
                    prompt_file_path = f'backend/services/agents/{self.agent_type}/prompts/{prompt_file}'
                else:
                    prompt_file_path = prompt_file
                    prompt_file = prompt_file.split('/')[-1]
                
                failure_info['prompt_files'].append({
                    'name': prompt_file,
                    'full_path': prompt_file_path
                })
            
            failure_info['root_cause'] = analysis.get('reasoning', analysis.get('root_cause', ''))
            failure_info['recommendations'] = analysis.get('specific_changes', analysis.get('recommendations', []))
            failure_info['priority'] = analysis.get('priority', 'medium')
        
        return failure_info if failure_info['prompt_files'] else None
    
    def _get_dimension_values(self, result: Dict[str, Any], dimension: str) -> tuple:
        """Get expected and actual values for a dimension"""
        if dimension == 'complexity_classification':
            return result.get('expected_complexity', 'N/A'), result.get('actual_complexity', 'N/A')
        elif dimension == 'specialty_selection':
            expected = result.get('expected_specialties', set())
            actual = result.get('actual_specialties', set())
            return ', '.join(sorted(expected)), ', '.join(sorted(actual))
        elif dimension == 'tool_usage':
            return 'Effective', f"{result.get('tool_calls_made', 0)} calls"
        elif dimension == 'response_structure':
            return 'Valid XML', 'Valid' if result.get('response_valid', False) else 'Invalid'
        else:
            return '≥' + f"{self._get_dimension_target(dimension):.2f}", f"{result.get(dimension + '_score', 0):.2f}"
    
    def _get_dimension_target(self, dimension: str) -> float:
        """Get target score for a dimension"""
        for criteria in self.agent_metadata.evaluation_criteria:
            if (criteria.dimension.name if hasattr(criteria.dimension, 'name') else str(criteria.dimension)) == dimension:
                return criteria.target_score
        return 0.8  # default
    
    def _get_trace_date(self, result: Dict[str, Any]) -> str:
        """Get the date when the trace was stored"""
        # If we have trace metadata with a timestamp, use that
        if 'trace_start_time' in result:
            try:
                trace_time = datetime.fromisoformat(result['trace_start_time'])
                return trace_time.strftime("%Y-%m-%d")
            except:
                pass
        
        # Otherwise use current date (trace was just created)
        return datetime.now().strftime("%Y-%m-%d")
    
    def _prepare_quality_breakdown_dynamic(self, result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Prepare quality breakdown using metadata"""
        breakdown = []
        quality_criteria = None
        
        # Find the analysis quality dimension
        for criteria in self.agent_metadata.evaluation_criteria:
            if criteria.dimension.name == 'analysis_quality':
                quality_criteria = criteria
                break
        
        if not quality_criteria or 'quality_breakdown' not in result:
            return breakdown
        
        # Get quality components for this dimension
        quality_components = self.agent_metadata.get_quality_components(quality_criteria.dimension)
        
        # Map result components to dimension components
        for component in quality_components:
            score = result['quality_breakdown'].get(component.name, 0.0)
            weighted = component.weight * score
            
            breakdown.append({
                'name': component.name.replace('_', ' ').title(),
                'weight': f"{component.weight:.2f}",
                'score': f"{score:.2f}",
                'weighted': f"{weighted:.3f}",
                'description': component.description
            })
        
        return breakdown
    
    def _prepare_failure_analysis_dynamic(self, result: Dict[str, Any], failed_dimensions: List[str]) -> List[Dict[str, Any]]:
        """Prepare failure analysis using metadata"""
        analysis = []
        
        # Map dimension names to analysis data
        for dim_name in failed_dimensions:
            # Find the dimension criteria
            criteria = None
            for c in self.agent_metadata.evaluation_criteria:
                if (c.dimension.name if hasattr(c.dimension, 'name') else str(c.dimension)).replace('_', ' ').title() == dim_name:
                    criteria = c
                    break
            
            if not criteria:
                continue
            
            # Get analysis data for this dimension
            # Map dimension names to the actual analysis keys used in results
            analysis_key_map = {
                'specialty_selection': 'specialist_analysis',
                'analysis_quality': 'quality_analysis',
                'complexity_classification': 'complexity_analysis',
                'tool_usage': 'tool_usage_analysis',
                'response_structure': 'response_structure_analysis'
            }
            
            dim_key = criteria.dimension.name if hasattr(criteria.dimension, 'name') else str(criteria.dimension)
            analysis_key = analysis_key_map.get(dim_key, f"{dim_key}_analysis")
            
            if analysis_key in result:
                analysis_data = result[analysis_key]
                
                # Get prompt file from analysis data or use a default
                prompt_file = analysis_data.get('prompt_file', '')
                if not prompt_file:
                    # Try to determine prompt file based on dimension
                    dimension_to_prompt = {
                        'complexity_classification': '1_gather_data_assess_complexity.txt',
                        'specialty_selection': '3_assign_specialist_tasks.txt',
                        'analysis_quality': '2_define_analytical_approach.txt',
                        'tool_usage': '1_gather_data_assess_complexity.txt',
                        'response_structure': '1_gather_data_assess_complexity.txt'
                    }
                    prompt_file = dimension_to_prompt.get(dim_key, 'unknown')
                
                # Use the prompt file path from analysis data or construct it
                if '/' in prompt_file:
                    # Full path already provided
                    prompt_file_path = prompt_file
                else:
                    # Just filename, construct path
                    prompt_file_path = f'backend/services/agents/{self.agent_type}/prompts/{prompt_file}'
                
                # Handle different analysis structures
                if 'prompt_improvements' in analysis_data:
                    # New quality analysis structure with multiple prompt improvements
                    for prompt_name, improvements in analysis_data.get('prompt_improvements', {}).items():
                        if improvements.get('needs_update', False):
                            analysis.append({
                                'icon': self._get_dimension_icon(criteria.dimension),
                                'title': f'{dim_name} Issue - {prompt_name}',
                                'description': analysis_data.get('overall_issue_description', f'{dim_name} below threshold'),
                                'root_cause': analysis_data.get('root_cause', ''),
                                'priority': improvements.get('priority', 'MEDIUM').upper(),
                                'priority_color': self._get_priority_color(improvements.get('priority', 'medium')),
                                'prompt_file': f'backend/services/agents/{self.agent_type}/prompts/{prompt_name}',
                                'recommendations': improvements.get('specific_changes', []),
                                'expected_impact': analysis_data.get('expected_impact'),
                                'issues': improvements.get('issues', [])
                            })
                else:
                    # Original structure for other analyses
                    analysis.append({
                        'icon': self._get_dimension_icon(criteria.dimension),
                        'title': f'{dim_name} Issue',
                        'description': analysis_data.get('issue_description', f'{dim_name} below threshold'),
                        'root_cause': analysis_data.get('reasoning', ''),
                        'priority': analysis_data.get('priority', 'MEDIUM').upper(),
                        'priority_color': self._get_priority_color(analysis_data.get('priority', 'medium')),
                        'prompt_file': prompt_file_path,
                        'recommendations': analysis_data.get('specific_changes', []),
                        'expected_impact': analysis_data.get('expected_impact')
                    })
        
        return analysis
    
    def _get_dimension_icon(self, dimension: EvaluationDimension) -> str:
        """Get icon for a dimension"""
        # Map dimension names to icons
        icon_map = {
            "complexity_classification": "⚠️",
            "specialty_selection": "👥",
            "analysis_quality": "📊",
            "tool_usage": "🔧",
            "response_structure": "📋",
            "medical_accuracy": "🏥",
            "recommendation_quality": "💡",
            "synthesis_quality": "🔄"
        }
        # Get the dimension name (handle both string and EvaluationDimension)
        dim_name = dimension.name if hasattr(dimension, 'name') else str(dimension)
        return icon_map.get(dim_name, "📌")
    
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
    
    def _get_priority_color(self, priority: str) -> str:
        """Get color for priority badge"""
        if priority.lower() == 'high':
            return "linear-gradient(135deg, #ef4444, #dc2626)"
        elif priority.lower() == 'medium':
            return "linear-gradient(135deg, #f59e0b, #d97706)"
        else:
            return "linear-gradient(135deg, #10b981, #059669)"
    
    def _get_test_suite_description(self, test_suite: str) -> str:
        """Get short description for test suite"""
        if test_suite.lower() == "real world":
            return "Production-grade test cases derived from actual user queries and clinical scenarios"
        return "Comprehensive evaluation of agent capabilities"
    
    def _get_test_suite_detailed_description(self, test_suite: str) -> str:
        """Get detailed description for test suite"""
        if test_suite.lower() == "real world":
            return f"The Real World test suite evaluates the {self.agent_type.upper()} Agent's performance on queries taken from production usage."
        return ""
    
    def _collect_prompt_improvements(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Collect and organize all prompt improvements from LLM Judge analyses"""
        prompt_improvements = {}
        
        # Collect improvements from each result
        for result in results:
            # Check new format first (failure_analyses)
            if 'failure_analyses' in result and result['failure_analyses']:
                for analysis in result['failure_analyses']:
                    if analysis.get('prompt_file'):
                        prompt_file = analysis['prompt_file']
                        if '/' in prompt_file:
                            prompt_file = prompt_file.split('/')[-1]
                        
                        if prompt_file not in prompt_improvements:
                            prompt_improvements[prompt_file] = {
                                'issues': set(),
                                'changes': set(),
                                'priorities': [],
                                'test_cases': []
                            }
                        
                        prompt_improvements[prompt_file]['issues'].add(analysis.get('root_cause', ''))
                        prompt_improvements[prompt_file]['changes'].update(analysis.get('recommendations', []))
                        prompt_improvements[prompt_file]['priorities'].append(analysis.get('priority', 'medium'))
                        prompt_improvements[prompt_file]['test_cases'].append(result.get('test_case_id', 'Unknown'))
                continue  # Skip old format processing for this result
            
            # Fallback to old format for backward compatibility
            # Check quality analysis for prompt improvements
            if 'quality_analysis' in result and 'prompt_improvements' in result['quality_analysis']:
                for prompt_file, improvements in result['quality_analysis']['prompt_improvements'].items():
                    if improvements.get('needs_update', False):
                        if prompt_file not in prompt_improvements:
                            prompt_improvements[prompt_file] = {
                                'issues': set(),
                                'changes': set(),
                                'priorities': [],
                                'test_cases': []
                            }
                        
                        # Aggregate issues and changes
                        prompt_improvements[prompt_file]['issues'].update(improvements.get('issues', []))
                        prompt_improvements[prompt_file]['changes'].update(improvements.get('specific_changes', []))
                        prompt_improvements[prompt_file]['priorities'].append(improvements.get('priority', 'medium'))
                        prompt_improvements[prompt_file]['test_cases'].append(result.get('test_case_id', 'Unknown'))
            
            # Check specialist analysis
            if 'specialist_analysis' in result and 'specific_changes' in result['specialist_analysis']:
                prompt_file = result['specialist_analysis'].get('prompt_file', '3_assign_specialist_tasks.txt')
                if '/' in prompt_file:
                    prompt_file = prompt_file.split('/')[-1]
                
                if prompt_file not in prompt_improvements:
                    prompt_improvements[prompt_file] = {
                        'issues': set(),
                        'changes': set(),
                        'priorities': [],
                        'test_cases': []
                    }
                
                prompt_improvements[prompt_file]['issues'].add(result['specialist_analysis'].get('issue_description', ''))
                prompt_improvements[prompt_file]['changes'].update(result['specialist_analysis'].get('specific_changes', []))
                prompt_improvements[prompt_file]['priorities'].append(result['specialist_analysis'].get('priority', 'medium'))
                prompt_improvements[prompt_file]['test_cases'].append(result.get('test_case_id', 'Unknown'))
        
        # Convert sets to lists and determine overall priority
        organized_improvements = []
        for prompt_file, data in prompt_improvements.items():
            # Determine overall priority (highest priority wins)
            priority_order = {'high': 3, 'medium': 2, 'low': 1}
            priorities = data['priorities']
            if priorities:
                overall_priority = max(priorities, key=lambda p: priority_order.get(p, 0))
            else:
                overall_priority = 'medium'
            
            organized_improvements.append({
                'file': prompt_file,
                'full_path': f'backend/services/agents/{self.agent_type}/prompts/{prompt_file}',
                'issues': list(data['issues']),
                'changes': list(data['changes']),
                'priority': overall_priority,
                'affected_tests': data['test_cases'],
                'test_count': len(set(data['test_cases']))
            })
        
        # Sort by priority
        priority_order = {'high': 3, 'medium': 2, 'low': 1}
        organized_improvements.sort(key=lambda x: priority_order.get(x['priority'], 0), reverse=True)
        
        return {
            'has_improvements': len(organized_improvements) > 0,
            'total_files': len(organized_improvements),
            'improvements': organized_improvements
        }
    
    def _prepare_test_case_prompt_improvements(self, result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Prepare prompt improvement recommendations for a specific test case"""
        improvements = []
        
        # Check new format first (failure_analyses)
        if 'failure_analyses' in result and result['failure_analyses']:
            for analysis in result['failure_analyses']:
                if analysis.get('prompt_file') and analysis.get('recommendations'):
                    improvements.append({
                        'dimension': analysis.get('dimension', 'Unknown'),
                        'prompt_file': analysis['prompt_file'],
                        'recommendations': analysis['recommendations'],
                        'priority': analysis.get('priority', 'medium'),
                        'root_cause': analysis.get('root_cause', '')
                    })
            return improvements
        
        # Fallback to old format for backward compatibility
        # Check if we have quality analysis with prompt improvements
        if 'quality_analysis' in result and 'prompt_improvements' in result['quality_analysis']:
            for prompt_file, improvement_data in result['quality_analysis']['prompt_improvements'].items():
                if improvement_data.get('needs_update', False):
                    improvements.append({
                        'prompt_file': prompt_file,
                        'issues': improvement_data.get('issues', []),
                        'changes': improvement_data.get('specific_changes', []),
                        'priority': improvement_data.get('priority', 'medium'),
                        'dimension': 'Analysis Quality'
                    })
        
        # Check specialist analysis
        if 'specialist_analysis' in result:
            analysis = result['specialist_analysis']
            if 'prompt_file' in analysis and 'specific_changes' in analysis:
                prompt_file = analysis['prompt_file']
                if '/' in prompt_file:
                    prompt_file = prompt_file.split('/')[-1]
                
                improvements.append({
                    'prompt_file': prompt_file,
                    'issues': [analysis.get('issue_description', '')],
                    'changes': analysis.get('specific_changes', []),
                    'priority': analysis.get('priority', 'medium'),
                    'dimension': 'Specialist Selection',
                    'missing_specialists': analysis.get('missing_specialists_reason', {})
                })
        
        # Check complexity analysis
        if 'complexity_analysis' in result:
            analysis = result['complexity_analysis']
            if hasattr(analysis, 'prompt_file') or 'prompt_file' in analysis:
                prompt_file = analysis.get('prompt_file') if isinstance(analysis, dict) else getattr(analysis, 'prompt_file', None)
                if prompt_file:
                    recommendations = analysis.get('recommendations', []) if isinstance(analysis, dict) else getattr(analysis, 'recommendations', [])
                    improvements.append({
                        'prompt_file': prompt_file,
                        'issues': [analysis.get('root_cause', '') if isinstance(analysis, dict) else getattr(analysis, 'root_cause', '')],
                        'changes': recommendations,
                        'priority': analysis.get('priority', 'medium') if isinstance(analysis, dict) else getattr(analysis, 'priority', 'medium'),
                        'dimension': 'Complexity Classification'
                    })
        
        return improvements
    
    def _get_additional_charts(self) -> List[Dict[str, str]]:
        """Get additional chart data"""
        return [
            {
                'name': 'Complexity Performance',
                'url': './complexity_performance.png',
                'description': 'Metrics by query complexity',
                'insights': 'See if certain query types perform better'
            },
            {
                'name': 'Response Time Distribution',
                'url': './response_time_distribution.png',
                'description': 'Histogram of processing times',
                'insights': 'Understand performance consistency'
            }
        ]
    
    def _generate_visualizations(self, results: Dict[str, Any]):
        """Generate visualization charts for the report"""
        
        # Set up matplotlib style
        plt.style.use('dark_background')
        sns.set_palette("husl")
        
        individual_results = results.get("results", [])
        if not individual_results:
            return
        
        # Generate dimension scores chart
        self._generate_dimension_scores_chart(individual_results)
        
        # Generate complexity performance chart if applicable
        if self.agent_type == "cmo":
            self._generate_complexity_performance_chart(individual_results)
        
        # Generate response time distribution
        self._generate_response_time_chart(individual_results)
        
        # Generate specialist heatmap for CMO
        if self.agent_type == "cmo":
            self._generate_specialty_heatmap(individual_results)
    
    def _generate_dimension_scores_chart(self, results: List[Dict[str, Any]]):
        """Generate bar chart of dimension scores"""
        
        # Calculate average scores per dimension
        dimension_scores = self._calculate_dimension_scores_dynamic(results)
        
        if not dimension_scores:
            return
        
        # Prepare data for plotting
        dimensions = list(dimension_scores.keys())
        scores = [d['score_percent'] / 100 for d in dimension_scores.values()]
        targets = [d['target_percent'] / 100 for d in dimension_scores.values()]
        
        # Create figure
        fig, ax = plt.subplots(figsize=(10, 6))
        
        x = np.arange(len(dimensions))
        width = 0.35
        
        # Plot bars
        bars1 = ax.bar(x - width/2, scores, width, label='Actual', color='#10b981')
        bars2 = ax.bar(x + width/2, targets, width, label='Target', color='#6366f1')
        
        # Customize
        ax.set_xlabel('Evaluation Dimensions')
        ax.set_ylabel('Score')
        ax.set_title('Evaluation Dimension Performance')
        ax.set_xticks(x)
        ax.set_xticklabels([d.replace('_', ' ').title() for d in dimensions], rotation=45, ha='right')
        ax.legend()
        ax.set_ylim(0, 1.1)
        
        # Add value labels
        for bar in bars1:
            height = bar.get_height()
            ax.annotate(f'{height:.2f}',
                       xy=(bar.get_x() + bar.get_width() / 2, height),
                       xytext=(0, 3),
                       textcoords="offset points",
                       ha='center', va='bottom')
        
        plt.tight_layout()
        plt.savefig(self.report_dir / 'dimension_scores.png', dpi=150, bbox_inches='tight')
        plt.close()
    
    def _generate_complexity_performance_chart(self, results: List[Dict[str, Any]]):
        """Generate performance by complexity chart"""
        
        # Group results by complexity
        complexity_groups = {}
        for result in results:
            complexity = result.get('expected_complexity', 'Unknown')
            if complexity not in complexity_groups:
                complexity_groups[complexity] = []
            complexity_groups[complexity].append(result)
        
        if not complexity_groups:
            return
        
        # Calculate metrics per complexity
        complexities = []
        success_rates = []
        avg_times = []
        
        for complexity, group_results in sorted(complexity_groups.items()):
            complexities.append(complexity)
            
            # Success rate
            successes = sum(1 for r in group_results if self._is_test_passed(r))
            success_rates.append(successes / len(group_results) if group_results else 0)
            
            # Average time
            times = [r.get('total_response_time_ms', 0) / 1000 for r in group_results]
            avg_times.append(np.mean(times) if times else 0)
        
        # Create figure with subplots
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
        
        # Success rate chart
        bars1 = ax1.bar(complexities, success_rates, color='#10b981')
        ax1.set_xlabel('Query Complexity')
        ax1.set_ylabel('Success Rate')
        ax1.set_title('Success Rate by Complexity')
        ax1.set_ylim(0, 1.1)
        
        for bar, rate in zip(bars1, success_rates):
            ax1.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.01,
                    f'{rate:.1%}', ha='center', va='bottom')
        
        # Response time chart
        bars2 = ax2.bar(complexities, avg_times, color='#f59e0b')
        ax2.set_xlabel('Query Complexity')
        ax2.set_ylabel('Average Response Time (s)')
        ax2.set_title('Response Time by Complexity')
        
        for bar, time in zip(bars2, avg_times):
            ax2.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.1,
                    f'{time:.1f}s', ha='center', va='bottom')
        
        plt.tight_layout()
        plt.savefig(self.report_dir / 'complexity_performance.png', dpi=150, bbox_inches='tight')
        plt.close()
    
    def _generate_response_time_chart(self, results: List[Dict[str, Any]]):
        """Generate response time distribution histogram"""
        
        # Extract response times
        response_times = []
        for result in results:
            time_ms = result.get('total_response_time_ms', 0)
            if time_ms > 0:
                response_times.append(time_ms / 1000)  # Convert to seconds
        
        if not response_times:
            return
        
        # Create histogram
        fig, ax = plt.subplots(figsize=(10, 6))
        
        n, bins, patches = ax.hist(response_times, bins=20, color='#8b5cf6', alpha=0.7, edgecolor='white')
        
        # Add statistics
        mean_time = np.mean(response_times)
        median_time = np.median(response_times)
        
        ax.axvline(mean_time, color='#ef4444', linestyle='dashed', linewidth=2, label=f'Mean: {mean_time:.1f}s')
        ax.axvline(median_time, color='#10b981', linestyle='dashed', linewidth=2, label=f'Median: {median_time:.1f}s')
        
        ax.set_xlabel('Response Time (seconds)')
        ax.set_ylabel('Frequency')
        ax.set_title('Response Time Distribution')
        ax.legend()
        
        plt.tight_layout()
        plt.savefig(self.report_dir / 'response_time_distribution.png', dpi=150, bbox_inches='tight')
        plt.close()
    
    def _generate_specialty_heatmap(self, results: List[Dict[str, Any]]):
        """Generate heatmap of specialist selection patterns"""
        
        # Extract specialist combinations
        specialist_pairs = {}
        
        for result in results:
            specialists = sorted(result.get('actual_specialties', []))
            if len(specialists) >= 2:
                # Count all pairs
                for i in range(len(specialists)):
                    for j in range(i + 1, len(specialists)):
                        pair = (specialists[i], specialists[j])
                        specialist_pairs[pair] = specialist_pairs.get(pair, 0) + 1
        
        if not specialist_pairs:
            return
        
        # Get unique specialists
        all_specialists = set()
        for pair in specialist_pairs:
            all_specialists.update(pair)
        all_specialists = sorted(all_specialists)
        
        # Create matrix
        n = len(all_specialists)
        matrix = np.zeros((n, n))
        
        for (spec1, spec2), count in specialist_pairs.items():
            i = all_specialists.index(spec1)
            j = all_specialists.index(spec2)
            matrix[i][j] = count
            matrix[j][i] = count  # Symmetric
        
        # Create heatmap
        fig, ax = plt.subplots(figsize=(10, 8))
        
        sns.heatmap(matrix, 
                    xticklabels=[s.replace('_', ' ').title() for s in all_specialists],
                    yticklabels=[s.replace('_', ' ').title() for s in all_specialists],
                    annot=True, 
                    fmt='g', 
                    cmap='YlOrRd',
                    cbar_kws={'label': 'Co-occurrence Count'})
        
        ax.set_title('Specialist Selection Patterns')
        plt.tight_layout()
        plt.savefig(self.report_dir / 'specialty_heatmap.png', dpi=150, bbox_inches='tight')
        plt.close()
    
    def _is_test_passed(self, result: Dict[str, Any]) -> bool:
        """Check if a test passed based on all dimensions"""
        failed_dims = self._get_failed_dimensions_dynamic(result)
        return len(failed_dims) == 0
    
    def _prepare_dimension_performance_with_macro_analysis(
        self, 
        dimension_scores: Dict[str, Dict[str, Any]], 
        macro_analyses: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Prepare dimension performance data with macro analysis for expandable rows"""
        dimension_performance = []
        
        for dim_name, data in dimension_scores.items():
            # Find criteria by dimension name
            criteria = None
            for c in self.agent_metadata.evaluation_criteria:
                if c.dimension.name == dim_name:
                    criteria = c
                    break
            
            if criteria:
                passed = data['passed']
                
                # Check if we have macro analysis for this dimension
                macro_analysis = macro_analyses.get(dim_name)
                has_macro_analysis = macro_analysis is not None and not passed
                
                dim_perf = {
                    'name': dim_name.replace('_', ' ').title(),
                    'score_percent': f"{data['score_percent']:.1f}",
                    'target_percent': f"{data['target_percent']:.1f}",
                    'score_percentage': data['score_percent'],  # For progress bar width
                    'actual_score': f"{data['score_percent']:.1f}%",
                    'target_score': f"{data['target_percent']:.1f}%",
                    'passed': passed,
                    'score_color': "#10b981" if passed else "#ef4444",
                    'progress_gradient': "linear-gradient(to right, #10b981, #059669)" if passed else "linear-gradient(to right, #ef4444, #dc2626)",
                    'method_icon': self._get_method_icon_dynamic(criteria),
                    'method': self._get_primary_method(criteria),
                    'description': criteria.description,
                    'icon': self._get_method_icon_dynamic(criteria),
                    'has_macro_analysis': has_macro_analysis,
                    'is_expandable': has_macro_analysis  # Only expandable if failed and has analysis
                }
                
                # Add macro analysis data if available
                if has_macro_analysis:
                    pattern_analysis = macro_analysis.get('pattern_analysis', {})
                    dim_perf['macro_analysis'] = {
                        'common_patterns': pattern_analysis.get('common_patterns', []),
                        'systemic_root_cause': pattern_analysis.get('systemic_root_cause', ''),
                        'contributing_factors': pattern_analysis.get('contributing_factors', []),
                        'prompt_coverage_gaps': macro_analysis.get('prompt_coverage_gaps', []),
                        'expected_improvement': macro_analysis.get('expected_improvement', {})
                    }
                
                dimension_performance.append(dim_perf)
        
        return dimension_performance
    
    def _prepare_consolidated_recommendations(
        self, 
        macro_analyses: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Prepare consolidated recommendations from macro analyses"""
        all_recommendations = []
        
        # Collect all recommendations from all dimensions
        for dimension, analysis in macro_analyses.items():
            if analysis and 'consolidated_recommendations' in analysis:
                for rec in analysis['consolidated_recommendations']:
                    # Add dimension info to recommendation
                    rec['dimension'] = dimension.replace('_', ' ').title()
                    all_recommendations.append(rec)
        
        # Sort by priority
        priority_order = {'CRITICAL': 4, 'HIGH': 3, 'MEDIUM': 2, 'LOW': 1}
        all_recommendations.sort(
            key=lambda x: priority_order.get(x.get('priority', 'MEDIUM'), 2), 
            reverse=True
        )
        
        # Group by priority
        recommendations_by_priority = {
            'CRITICAL': [],
            'HIGH': [],
            'MEDIUM': [],
            'LOW': []
        }
        
        for rec in all_recommendations:
            priority = rec.get('priority', 'MEDIUM')
            if priority in recommendations_by_priority:
                recommendations_by_priority[priority].append(rec)
        
        # Calculate statistics
        total_recommendations = len(all_recommendations)
        affected_files = set()
        for rec in all_recommendations:
            if rec.get('prompt_file'):
                affected_files.add(rec['prompt_file'])
        
        return {
            'has_recommendations': total_recommendations > 0,
            'total_recommendations': total_recommendations,
            'total_affected_files': len(affected_files),
            'recommendations_by_priority': recommendations_by_priority,
            'all_recommendations': all_recommendations
        }