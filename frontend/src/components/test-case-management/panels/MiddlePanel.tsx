import React, { useState, useEffect } from 'react';
import { Activity, ClipboardCheck, Maximize2, Minimize2 } from 'lucide-react';
import TraceViewerPanel from './TraceViewerPanel';
import EvalReportViewer from '../components/EvalReportViewer';
import { EvaluationReport } from '../types';

interface MiddlePanelProps {
  traceId: string;
  evaluationReport: EvaluationReport | null;
  isEvaluating: boolean;
  onEventSelect?: (eventId: string) => void;
  selectedEvent?: string | null;
  switchToReportTab?: boolean;
  onTabChange?: (tab: 'trace' | 'report') => void;
}

const MiddlePanel: React.FC<MiddlePanelProps> = ({
  traceId,
  evaluationReport,
  isEvaluating,
  onEventSelect,
  selectedEvent,
  switchToReportTab,
  onTabChange
}) => {
  const [activeTab, setActiveTab] = useState<'trace' | 'report'>('trace');
  const [isFullscreen, setIsFullscreen] = useState(false);

  // Switch to report tab when requested
  useEffect(() => {
    if (switchToReportTab) {
      setActiveTab('report');
    }
  }, [switchToReportTab]);

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
              {evaluationReport && (
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
              <div className="flex items-center justify-center h-full">
                <div className="text-center">
                  <div className="w-8 h-8 animate-spin text-blue-600 mx-auto mb-2">
                    <svg className="w-full h-full" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                  </div>
                  <p className="text-gray-900 font-medium">Running Evaluation...</p>
                  <p className="text-sm text-gray-600 mt-1">This may take up to 30 seconds</p>
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