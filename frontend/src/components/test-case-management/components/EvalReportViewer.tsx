import React, { useState } from 'react';
import { ChevronDown, ChevronRight, CheckCircle, XCircle, AlertCircle, ExternalLink, BarChart2 } from 'lucide-react';
import { EvaluationReport, DimensionResult } from '../types';

interface EvalReportViewerProps {
  report: EvaluationReport;
}

const EvalReportViewer: React.FC<EvalReportViewerProps> = ({ report }) => {
  const [expandedDimensions, setExpandedDimensions] = useState<Set<string>>(new Set());

  const toggleDimension = (dimension: string) => {
    const newExpanded = new Set(expandedDimensions);
    if (newExpanded.has(dimension)) {
      newExpanded.delete(dimension);
    } else {
      newExpanded.add(dimension);
    }
    setExpandedDimensions(newExpanded);
  };

  const getScoreColor = (score: number) => {
    if (score >= 0.8) return 'text-green-600';
    if (score >= 0.6) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getScoreIcon = (score: number) => {
    if (score >= 0.8) return <CheckCircle className="w-5 h-5 text-green-600" />;
    if (score >= 0.6) return <AlertCircle className="w-5 h-5 text-yellow-600" />;
    return <XCircle className="w-5 h-5 text-red-600" />;
  };

  const dimensionOrder = [
    'complexity_classification',
    'specialty_selection',
    'analysis_quality',
    'tool_usage',
    'response_structure'
  ];

  const dimensionLabels: Record<string, string> = {
    complexity_classification: 'Complexity Classification',
    specialty_selection: 'Specialty Selection',
    analysis_quality: 'Analysis Quality',
    tool_usage: 'Tool Usage',
    response_structure: 'Response Structure'
  };

  return (
    <div className="h-full overflow-y-scroll">
      {/* Overall Score Header */}
      <div className="px-4 py-6 bg-gradient-to-r from-blue-50 to-blue-100 border-b border-blue-200">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Evaluation Report</h3>
            <p className="text-sm text-gray-600 mt-1">
              Test Case: {report.test_case_id.slice(0, 8)}...
            </p>
          </div>
          <div className="text-center">
            <div className={`text-3xl font-bold ${getScoreColor(report.overall_score)}`}>
              {(report.overall_score * 100).toFixed(1)}%
            </div>
            <p className="text-sm text-gray-600">Overall Score</p>
          </div>
        </div>

        {/* Quick Stats */}
        <div className="grid grid-cols-3 gap-4 mt-4">
          <div className="bg-white/70 rounded-lg px-3 py-2">
            <p className="text-xs text-gray-600">Execution Time</p>
            <p className="text-sm font-semibold">{report.execution_time_ms.toFixed(0)}ms</p>
          </div>
          <div className="bg-white/70 rounded-lg px-3 py-2">
            <p className="text-xs text-gray-600">Dimensions Passed</p>
            <p className="text-sm font-semibold">
              {Object.values(report.dimension_results).filter(d => d.normalized_score >= 0.75).length}/
              {Object.keys(report.dimension_results).length}
            </p>
          </div>
          <div className="bg-white/70 rounded-lg px-3 py-2">
            <p className="text-xs text-gray-600">Evaluation ID</p>
            <p className="text-sm font-semibold truncate" title={report.evaluation_id}>
              {report.evaluation_id?.slice(0, 12)}...
            </p>
          </div>
        </div>
      </div>

      {/* Dimension Results */}
      <div className="px-4 py-4 space-y-3">
        {dimensionOrder.map(dimKey => {
          const dimension = report.dimension_results[dimKey];
          if (!dimension) return null;
          
          const isExpanded = expandedDimensions.has(dimKey);
          
          return (
            <div key={dimKey} className="border border-gray-200 rounded-lg overflow-hidden">
              {/* Dimension Header */}
              <button
                onClick={() => toggleDimension(dimKey)}
                className="w-full px-4 py-3 bg-gray-50 hover:bg-gray-100 transition-colors flex items-center justify-between"
              >
                <div className="flex items-center gap-3">
                  {isExpanded ? (
                    <ChevronDown className="w-4 h-4 text-gray-600" />
                  ) : (
                    <ChevronRight className="w-4 h-4 text-gray-600" />
                  )}
                  <span className="font-medium text-gray-900">
                    {dimensionLabels[dimKey] || dimKey}
                  </span>
                  {getScoreIcon(dimension.normalized_score)}
                </div>
                <div className="flex items-center gap-4">
                  <span className={`font-semibold ${getScoreColor(dimension.normalized_score)}`}>
                    {(dimension.normalized_score * 100).toFixed(0)}%
                  </span>
                  <span className="text-xs text-gray-500">
                    {dimension.evaluation_method}
                  </span>
                </div>
              </button>

              {/* Dimension Details */}
              {isExpanded && (
                <div className="p-4 bg-white border-t border-gray-200">
                  {/* Component Scores */}
                  {dimension.components && Object.keys(dimension.components).length > 0 && (
                    <div className="mb-4">
                      <h4 className="text-sm font-semibold text-gray-700 mb-2">Component Scores</h4>
                      <div className="space-y-2">
                        {Object.entries(dimension.components).map(([component, score]) => (
                          <div key={component} className="flex items-center justify-between">
                            <span className="text-sm text-gray-600">
                              {component.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                            </span>
                            <div className="flex items-center gap-2">
                              <div className="w-24 bg-gray-200 rounded-full h-2">
                                <div
                                  className={`h-2 rounded-full ${
                                    score >= 0.8 ? 'bg-green-500' :
                                    score >= 0.6 ? 'bg-yellow-500' : 'bg-red-500'
                                  }`}
                                  style={{ width: `${score * 100}%` }}
                                />
                              </div>
                              <span className="text-sm font-medium w-12 text-right">
                                {(score * 100).toFixed(0)}%
                              </span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Details */}
                  {dimension.details && Object.keys(dimension.details).length > 0 && (
                    <div>
                      <h4 className="text-sm font-semibold text-gray-700 mb-2">Details</h4>
                      <div className="bg-gray-50 rounded-md p-3">
                        <pre className="text-xs text-gray-600 whitespace-pre-wrap">
                          {JSON.stringify(dimension.details, null, 2)}
                        </pre>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Full HTML Report in iframe */}
      {report.report_url && (
        <div className="px-4 py-4 border-t border-gray-200">
          <div className="mb-3 flex items-center justify-between">
            <h4 className="text-sm font-semibold text-gray-700">Full Evaluation Report</h4>
            <a
              href={report.report_url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1 text-sm text-blue-600 hover:text-blue-700"
            >
              <span>Open in new tab</span>
              <ExternalLink className="w-3 h-3" />
            </a>
          </div>
          <div className="border border-gray-300 rounded-lg overflow-hidden" style={{ height: '600px' }}>
            <iframe
              src={report.report_url}
              className="w-full h-full"
              title="Evaluation Report"
              sandbox="allow-scripts allow-same-origin"
            />
          </div>
        </div>
      )}
    </div>
  );
};

export default EvalReportViewer;