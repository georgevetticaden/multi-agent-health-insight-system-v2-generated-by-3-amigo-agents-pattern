import React, { useState, useEffect } from 'react';
import { Activity, ClipboardCheck, Maximize2, Minimize2 } from 'lucide-react';
import TraceViewerPanel from './TraceViewerPanel';
import EvalReportViewer from '../components/EvalReportViewer';
import { EvaluationReport } from '../types';

interface MiddlePanelProps {
  traceId: string;
  evaluationReport: EvaluationReport | null;
  isEvaluating: boolean;
  evaluationEvents?: any[];
  onEventSelect?: (eventId: string) => void;
  selectedEvent?: string | null;
  switchToReportTab?: boolean;
  onTabChange?: (tab: 'trace' | 'report') => void;
}

const MiddlePanel: React.FC<MiddlePanelProps> = ({
  traceId,
  evaluationReport,
  isEvaluating,
  evaluationEvents = [],
  onEventSelect,
  selectedEvent,
  switchToReportTab,
  onTabChange
}) => {
  const [activeTab, setActiveTab] = useState<'trace' | 'report'>('trace');
  const [isFullscreen, setIsFullscreen] = useState(false);

  // Switch to report tab when requested OR when evaluation starts
  useEffect(() => {
    if (switchToReportTab || isEvaluating) {
      setActiveTab('report');
    }
  }, [switchToReportTab, isEvaluating]);

  const handleTabChange = (tab: 'trace' | 'report') => {
    setActiveTab(tab);
    onTabChange?.(tab);
  };

  const toggleFullscreen = () => {
    setIsFullscreen(!isFullscreen);
  };

  return (
    <div className={`h-full flex flex-col ${isFullscreen ? 'fixed inset-0 z-50 bg-white' : ''}`}>
      {/* Header with Tabs */}
      <div className="border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div className="flex">
            <button
              onClick={() => handleTabChange('trace')}
              className={`flex items-center gap-2 px-4 py-3 border-b-2 transition-colors ${
                activeTab === 'trace'
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-600 hover:text-gray-900'
              }`}
            >
              <Activity className="w-4 h-4" />
              <span className="font-medium">Health Query Trace</span>
            </button>
            
            <button
              onClick={() => handleTabChange('report')}
              className={`flex items-center gap-2 px-4 py-3 border-b-2 transition-colors ${
                activeTab === 'report'
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-600 hover:text-gray-900'
              }`}
              disabled={!evaluationReport && !isEvaluating}
            >
              <ClipboardCheck className="w-4 h-4" />
              <span className="font-medium">Evaluation Report</span>
              {isEvaluating && (
                <div className="w-4 h-4 animate-spin text-blue-600">
                  <svg className="w-full h-full" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                </div>
              )}
              {evaluationReport && !isEvaluating && (
                <span className={`text-xs px-2 py-0.5 rounded-full ${
                  evaluationReport.overall_score >= 0.8 
                    ? 'bg-green-100 text-green-700'
                    : evaluationReport.overall_score >= 0.6
                    ? 'bg-yellow-100 text-yellow-700'
                    : 'bg-red-100 text-red-700'
                }`}>
                  {(evaluationReport.overall_score * 100).toFixed(0)}%
                </span>
              )}
            </button>
          </div>
          <button
            onClick={toggleFullscreen}
            className="p-1.5 hover:bg-gray-100 rounded transition-colors mr-2"
            title={isFullscreen ? "Exit fullscreen" : "Enter fullscreen"}
          >
            {isFullscreen ? (
              <Minimize2 className="w-4 h-4 text-gray-600" />
            ) : (
              <Maximize2 className="w-4 h-4 text-gray-600" />
            )}
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-hidden">
        {activeTab === 'trace' ? (
          <TraceViewerPanel
            traceId={traceId}
            onEventSelect={onEventSelect}
            selectedEvent={selectedEvent}
          />
        ) : (
          <div className="h-full">
            {isEvaluating ? (
              <div className="flex flex-col h-full">
                {/* Header */}
                <div className="px-6 py-4 border-b border-gray-200">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900">Evaluation in Progress</h3>
                      <p className="text-sm text-gray-600 mt-1">Following the Analyze → Measure → Improve lifecycle</p>
                    </div>
                    <div className="w-8 h-8 animate-spin text-blue-600">
                      <svg className="w-full h-full" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                    </div>
                  </div>
                </div>
                
                {/* Events List */}
                <div className="flex-1 overflow-y-auto px-6 py-4 bg-gradient-to-b from-gray-50 to-white">
                  <div className="space-y-3">
                    {evaluationEvents.map((event, index) => {
                      // Determine event style based on type
                      const isComplete = event.type === 'evaluation_complete' || event.type === 'overall_score';
                      const isDimension = event.type === 'dimension_result';
                      const isDiagnostic = event.type === 'diagnostic' || event.type === 'diagnostic_complete';
                      const isLLMJudge = event.type === 'llm_judge_eval' || event.type === 'llm_judge_result';
                      
                      const bgColor = isComplete ? 'bg-green-50 border-green-200' : 
                                    isDimension ? (event.passed ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200') :
                                    isDiagnostic ? 'bg-purple-50 border-purple-200' :
                                    isLLMJudge ? 'bg-blue-50 border-blue-200' :
                                    'bg-white border-gray-200';
                                    
                      const iconBg = isComplete ? 'bg-green-100' :
                                   isDimension ? (event.passed ? 'bg-green-100' : 'bg-red-100') :
                                   isDiagnostic ? 'bg-purple-100' :
                                   isLLMJudge ? 'bg-blue-100' :
                                   'bg-gray-100';
                                   
                      const iconColor = isComplete ? 'text-green-600' :
                                      isDimension ? (event.passed ? 'text-green-600' : 'text-red-600') :
                                      isDiagnostic ? 'text-purple-600' :
                                      isLLMJudge ? 'text-blue-600' :
                                      'text-gray-600';
                      
                      return (
                        <div key={index} className={`flex items-start gap-3 p-3 rounded-lg border ${bgColor} transition-all duration-300 animate-fadeIn`}>
                          <div className={`flex-shrink-0 w-10 h-10 ${iconBg} rounded-full flex items-center justify-center ${iconColor}`}>
                            <span className="text-xl">{event.message?.charAt(0) || '•'}</span>
                          </div>
                          <div className="flex-1">
                            <p className="text-sm font-medium text-gray-900">{event.message}</p>
                            {event.timestamp && (
                              <p className="text-xs text-gray-500 mt-0.5">
                                {new Date(event.timestamp).toLocaleTimeString()}
                              </p>
                            )}
                            {event.dimension && (
                              <p className="text-xs text-gray-600 mt-1">
                                <span className="font-medium">Dimension:</span> {event.dimension.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                              </p>
                            )}
                            {event.score !== undefined && (
                              <div className="mt-2">
                                <div className="flex items-center gap-2">
                                  <div className="flex-1 bg-gray-200 rounded-full h-1.5 overflow-hidden">
                                    <div 
                                      className={`h-full transition-all duration-500 ${event.passed ? 'bg-green-500' : 'bg-red-500'}`}
                                      style={{ width: `${event.score * 100}%` }}
                                    />
                                  </div>
                                  <span className={`text-xs font-medium ${event.passed ? 'text-green-600' : 'text-red-600'}`}>
                                    {(event.score * 100).toFixed(1)}%
                                  </span>
                                </div>
                              </div>
                            )}
                          </div>
                        </div>
                      );
                    })}
                    {evaluationEvents.length === 0 && (
                      <div className="text-center py-12">
                        <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                          <Activity className="w-8 h-8 text-gray-400" />
                        </div>
                        <p className="text-sm text-gray-500">Waiting for evaluation to start...</p>
                        <p className="text-xs text-gray-400 mt-1">Events will appear here as the evaluation progresses</p>
                      </div>
                    )}
                  </div>
                </div>
                
                {/* Footer */}
                <div className="px-6 py-3 border-t border-gray-200 bg-gray-50">
                  <p className="text-xs text-gray-600 text-center">
                    Evaluation typically takes 30-60 seconds to complete
                  </p>
                </div>
              </div>
            ) : evaluationReport ? (
              <EvalReportViewer report={evaluationReport} />
            ) : (
              <div className="flex items-center justify-center h-full">
                <div className="text-center">
                  <ClipboardCheck className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                  <p className="text-gray-600">No evaluation report yet</p>
                  <p className="text-sm text-gray-500 mt-1">
                    Run an evaluation to see results here
                  </p>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default MiddlePanel;