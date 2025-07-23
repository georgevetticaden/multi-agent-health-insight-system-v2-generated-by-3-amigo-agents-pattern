import React, { useState, useRef, useEffect } from 'react';
import { FileText, Loader2, Play, Save, Download, MoreVertical, Maximize2, Minimize2 } from 'lucide-react';
import TestCaseDisplay from '../components/TestCaseDisplay';
import { TestCase } from '../types';

interface TestCasePanelProps {
  testCase: TestCase | null;
  isEvaluating: boolean;
  onTestCaseChange: (testCase: TestCase) => void;
  onRunEvaluation?: () => void;
  onSaveTestCase?: () => void;
}

const TestCasePanel: React.FC<TestCasePanelProps> = ({
  testCase,
  isEvaluating,
  onTestCaseChange,
  onRunEvaluation,
  onSaveTestCase
}) => {
  const [showActionsDropdown, setShowActionsDropdown] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const [isFullscreen, setIsFullscreen] = useState(false);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setShowActionsDropdown(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const toggleFullscreen = () => {
    setIsFullscreen(!isFullscreen);
  };

  return (
    <div className={`h-full flex flex-col ${isFullscreen ? 'fixed inset-0 z-50 bg-white' : ''}`}>
      {/* Header */}
      <div className="px-4 py-3 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <FileText className="w-4 h-4 text-indigo-600" />
            <h2 className="font-semibold text-gray-900">Test Case</h2>
            {/* Actions Dropdown */}
            <div className="relative" ref={dropdownRef}>
              <button
                onClick={() => setShowActionsDropdown(!showActionsDropdown)}
                className="p-1.5 hover:bg-gray-100 rounded transition-colors"
                title="Actions"
              >
                <MoreVertical className="w-4 h-4 text-gray-600" />
              </button>
              
              {showActionsDropdown && (
                <div className="absolute right-0 mt-1 w-48 bg-white rounded-md shadow-lg border border-gray-200 z-10">
                  <div className="py-1">
                    <button
                      onClick={() => {
                        setShowActionsDropdown(false);
                        onRunEvaluation?.();
                      }}
                      disabled={isEvaluating}
                      className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                    >
                      <Play className="w-4 h-4" />
                      Run Evaluation
                    </button>
                    
                    <button
                      onClick={() => {
                        setShowActionsDropdown(false);
                        onSaveTestCase?.();
                      }}
                      className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 flex items-center gap-2"
                    >
                      <Save className="w-4 h-4" />
                      Save Test Case
                    </button>
                    
                    <button
                      onClick={() => {
                        setShowActionsDropdown(false);
                        onSaveTestCase?.();
                        onRunEvaluation?.();
                      }}
                      disabled={isEvaluating}
                      className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                    >
                      <Download className="w-4 h-4" />
                      Save & Run
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
          <button
            onClick={toggleFullscreen}
            className="p-1.5 hover:bg-gray-100 rounded transition-colors"
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
        {testCase ? (
          <TestCaseDisplay 
            testCase={testCase}
            onRunEvaluation={onRunEvaluation}
            onSaveTestCase={onSaveTestCase}
            isEvaluating={isEvaluating}
          />
        ) : (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <Loader2 className="w-8 h-8 animate-spin text-gray-400 mx-auto mb-2" />
              <p className="text-gray-600">Loading test case...</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default TestCasePanel;