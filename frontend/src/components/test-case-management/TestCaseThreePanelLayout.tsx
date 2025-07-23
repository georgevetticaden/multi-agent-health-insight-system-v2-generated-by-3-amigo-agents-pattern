import React, { useState, useRef, useEffect } from 'react';
import { GripVertical } from 'lucide-react';
import TestCaseHeader from './TestCaseHeader';
import QEAgentPanel from './panels/QEAgentPanel';
import MiddlePanel from './panels/MiddlePanel';
import TestCasePanel from './panels/TestCasePanel';
import { TestCase, EvaluationReport } from './types';

interface TestCaseThreePanelLayoutProps {
  traceId: string;
}

const TestCaseThreePanelLayout: React.FC<TestCaseThreePanelLayoutProps> = ({ traceId }) => {
  // Panel width states - intelligent defaults
  const [leftPanelWidth, setLeftPanelWidth] = useState(30); // 30%
  const [middlePanelWidth, setMiddlePanelWidth] = useState(40); // 40%
  // Right panel width is calculated: 100 - left - middle = 30%

  const containerRef = useRef<HTMLDivElement>(null);
  const isDraggingRef = useRef<string | null>(null);

  // Test case management states
  const [testCase, setTestCase] = useState<TestCase | null>(null);
  const [evaluationReport, setEvaluationReport] = useState<EvaluationReport | null>(null);
  const [isEvaluating, setIsEvaluating] = useState(false);
  const [selectedTraceEvent, setSelectedTraceEvent] = useState<string | null>(null);
  const [switchToReportTab, setSwitchToReportTab] = useState(false);

  // Load initial test case from trace
  useEffect(() => {
    loadTestCaseFromTrace();
  }, [traceId]);

  const loadTestCaseFromTrace = async () => {
    try {
      console.log('🔍 [TEST CASE LOADING] Creating test case from trace:', traceId);
      
      const response = await fetch('/api/test-cases/from-trace', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ trace_id: traceId })
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.error('🔴 [TEST CASE LOADING] API error:', response.status, errorText);
        throw new Error(`Failed to create test case from trace: ${response.status} ${errorText}`);
      }

      const testCaseData = await response.json();
      console.log('✅ [TEST CASE LOADING] Test case created:', testCaseData);
      setTestCase(testCaseData);
    } catch (error) {
      console.error('🔴 [TEST CASE LOADING] Error loading test case:', error);
    }
  };

  // Handle test case updates from QE Agent
  const handleTestCaseUpdate = async (updates: Partial<TestCase>) => {
    if (!testCase) return;

    // Apply updates locally first (merge with existing)
    const localUpdate = {
      ...testCase,
      ...updates,
      // Preserve actual values - don't let them be overwritten by expected values
      actual_complexity: testCase.actual_complexity,
      actual_specialties: testCase.actual_specialties
    };
    setTestCase(localUpdate);

    try {
      const response = await fetch(`/api/test-cases/${testCase.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updates)
      });

      if (!response.ok) {
        throw new Error('Failed to update test case');
      }

      const updatedTestCase = await response.json();
      // Merge server response but still preserve actual values
      setTestCase({
        ...updatedTestCase,
        actual_complexity: testCase.actual_complexity,
        actual_specialties: testCase.actual_specialties
      });
    } catch (error) {
      console.error('Error updating test case:', error);
      // Revert to original on error
      setTestCase(testCase);
    }
  };

  // Handle run evaluation
  const handleRunEvaluation = async () => {
    if (!testCase) return;
    
    setIsEvaluating(true);
    setSwitchToReportTab(true);
    try {
      const response = await fetch(`/api/test-cases/${testCase.id}/evaluate`, {
        method: 'POST'
      });

      if (!response.ok) {
        throw new Error('Evaluation failed');
      }

      const result = await response.json();
      
      // Set the evaluation report with the data we have
      setEvaluationReport({
        test_case_id: testCase.id,
        evaluation_id: result.evaluation_id,
        overall_score: result.overall_score,
        report_url: result.report_url,
        report_dir: result.report_dir,
        dimension_results: {},  // Will be populated from the HTML report
        execution_time_ms: 0    // Will be populated from the HTML report
      });
    } catch (error) {
      console.error('Evaluation error:', error);
      alert('Error running evaluation. Please try again.');
    } finally {
      setIsEvaluating(false);
    }
  };

  // Handle save test case
  const handleSaveTestCase = () => {
    if (!testCase) return;
    
    // In a real implementation, this would save to backend
    console.log('Saving test case:', testCase);
    alert('Test case saved successfully!');
  };

  // Handle evaluation start
  const handleEvaluationStart = () => {
    setIsEvaluating(true);
    setEvaluationReport(null);
    setSwitchToReportTab(true);
  };

  // Handle evaluation complete
  const handleEvaluationComplete = (report: EvaluationReport) => {
    setIsEvaluating(false);
    setEvaluationReport(report);
  };

  // Panel resize handlers
  const startResize = (divider: 'left' | 'right') => {
    console.log(`[RESIZE] Starting resize for ${divider} divider`);
    isDraggingRef.current = divider;
    document.body.style.cursor = 'col-resize';
    document.body.style.userSelect = 'none';
  };

  // Store panel widths in refs to avoid stale closures
  const leftPanelWidthRef = useRef(leftPanelWidth);
  const middlePanelWidthRef = useRef(middlePanelWidth);
  
  // Update refs when state changes
  useEffect(() => {
    leftPanelWidthRef.current = leftPanelWidth;
    console.log(`[RESIZE] Updated leftPanelWidthRef to: ${leftPanelWidth}%`);
  }, [leftPanelWidth]);
  
  useEffect(() => {
    middlePanelWidthRef.current = middlePanelWidth;
    console.log(`[RESIZE] Updated middlePanelWidthRef to: ${middlePanelWidth}%`);
  }, [middlePanelWidth]);

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isDraggingRef.current || !containerRef.current) {
        return;
      }
      
      e.preventDefault();
      const containerRect = containerRef.current.getBoundingClientRect();
      const containerWidth = containerRect.width;
      const relativeX = e.clientX - containerRect.left;
      const percentX = (relativeX / containerWidth) * 100;
      
      console.log(`[RESIZE] Mouse move - Divider: ${isDraggingRef.current}, X: ${e.clientX}, RelativeX: ${relativeX}, PercentX: ${percentX.toFixed(2)}%`);

      if (isDraggingRef.current === 'left') {
        // Resizing left panel - mouse position directly sets the panel width
        const newLeftWidth = Math.min(60, Math.max(15, percentX));
        console.log(`[RESIZE] Left divider - mouse at ${percentX.toFixed(2)}%, setting width to ${newLeftWidth.toFixed(2)}%`);
        setLeftPanelWidth(newLeftWidth);
      } else if (isDraggingRef.current === 'right') {
        // Resizing middle panel - the divider position determines the end of middle panel
        const currentLeft = leftPanelWidthRef.current;
        const minMiddle = 15; // Minimum middle panel width
        const minRight = 15; // Minimum right panel width
        
        // The divider position is where the middle panel ends
        // So middle width = divider position - left panel width
        const newMiddleWidth = percentX - currentLeft;
        
        // Apply constraints
        const maxMiddle = 100 - currentLeft - minRight; // Leave space for right panel
        const constrainedMiddleWidth = Math.min(maxMiddle, Math.max(minMiddle, newMiddleWidth));
        
        console.log(`[RESIZE] Right divider - mouse at ${percentX.toFixed(2)}%, left: ${currentLeft.toFixed(2)}%, middle will be ${constrainedMiddleWidth.toFixed(2)}%`);
        setMiddlePanelWidth(constrainedMiddleWidth);
      }
    };

    const handleMouseUp = (e: MouseEvent) => {
      console.log(`[RESIZE] Mouse up event - Current dragging: ${isDraggingRef.current}`);
      if (isDraggingRef.current) {
        console.log(`[RESIZE] Stopping resize for ${isDraggingRef.current} divider`);
        isDraggingRef.current = null;
        document.body.style.cursor = '';
        document.body.style.userSelect = '';
      }
    };

    // Add global listeners
    console.log('[RESIZE] Adding event listeners');
    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
    document.addEventListener('mouseleave', handleMouseUp);

    // Cleanup
    return () => {
      console.log('[RESIZE] Removing event listeners');
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
      document.removeEventListener('mouseleave', handleMouseUp);
      // Ensure we clean up if component unmounts while dragging
      if (isDraggingRef.current) {
        console.log(`[RESIZE] Cleanup - was dragging ${isDraggingRef.current}`);
        isDraggingRef.current = null;
        document.body.style.cursor = '';
        document.body.style.userSelect = '';
      }
    };
  }, []); // No dependencies - set up once

  const rightPanelWidth = 100 - leftPanelWidth - middlePanelWidth;
  
  // Log panel widths on render
  useEffect(() => {
    console.log(`[PANELS] Current widths - Left: ${leftPanelWidth.toFixed(2)}%, Middle: ${middlePanelWidth.toFixed(2)}%, Right: ${rightPanelWidth.toFixed(2)}%`);
  }, [leftPanelWidth, middlePanelWidth, rightPanelWidth]);

  return (
    <div className="h-screen bg-gray-50 flex flex-col overflow-hidden">
      {/* Header */}
      <TestCaseHeader />

      {/* Three Panel Layout */}
      <div ref={containerRef} className="flex-1 flex overflow-hidden relative">
        {/* Left Panel - QE Agent Chat */}
        <div 
          className="flex-shrink-0 border-r border-gray-200 bg-white flex flex-col h-full"
          style={{ width: `${leftPanelWidth}%` }}
        >
          <QEAgentPanel
            traceId={traceId}
            testCase={testCase}
            onTestCaseUpdate={handleTestCaseUpdate}
            onEvaluationStart={handleEvaluationStart}
            onEvaluationComplete={handleEvaluationComplete}
          />
        </div>

        {/* Left Resizer */}
        <div
          className="w-1 hover:w-2 bg-gray-300 hover:bg-gray-400 cursor-col-resize flex items-center justify-center transition-all"
          onMouseDown={(e) => {
            e.preventDefault();
            e.stopPropagation();
            startResize('left');
          }}
        >
          <GripVertical className="w-4 h-4 text-gray-600 opacity-0 hover:opacity-100" />
        </div>

        {/* Middle Panel - Trace Viewer and Evaluation Report */}
        <div 
          className="flex-shrink-0 border-r border-gray-200 bg-white flex flex-col h-full"
          style={{ width: `${middlePanelWidth}%` }}
        >
          <MiddlePanel
            traceId={traceId}
            evaluationReport={evaluationReport}
            isEvaluating={isEvaluating}
            onEventSelect={setSelectedTraceEvent}
            selectedEvent={selectedTraceEvent}
            switchToReportTab={switchToReportTab}
            onTabChange={() => setSwitchToReportTab(false)}
          />
        </div>

        {/* Right Resizer */}
        <div
          className="w-1 hover:w-2 bg-gray-300 hover:bg-gray-400 cursor-col-resize flex items-center justify-center transition-all"
          onMouseDown={(e) => {
            e.preventDefault();
            e.stopPropagation();
            startResize('right');
          }}
        >
          <GripVertical className="w-4 h-4 text-gray-600 opacity-0 hover:opacity-100" />
        </div>

        {/* Right Panel - Test Case & Evaluation Report */}
        <div 
          className="flex-shrink-0 bg-white flex flex-col h-full"
          style={{ width: `${rightPanelWidth}%` }}
        >
          <TestCasePanel
            testCase={testCase}
            isEvaluating={isEvaluating}
            onTestCaseChange={setTestCase}
            onRunEvaluation={handleRunEvaluation}
            onSaveTestCase={handleSaveTestCase}
          />
        </div>
      </div>
    </div>
  );
};

export default TestCaseThreePanelLayout;