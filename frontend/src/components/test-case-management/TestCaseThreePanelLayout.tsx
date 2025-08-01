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
  const [evaluationId, setEvaluationId] = useState<string | null>(null);
  const [evaluationEvents, setEvaluationEvents] = useState<any[]>([]);

  // Load initial test case from trace
  useEffect(() => {
    loadTestCaseFromTrace();
  }, [traceId]);
  
  // Clear any stale evaluation state on mount
  useEffect(() => {
    // If we have an evaluationId but we're not evaluating, clear it
    if (evaluationId && !isEvaluating) {
      console.log('🧹 Clearing stale evaluation ID on mount:', evaluationId);
      setEvaluationId(null);
    }
  }, []);

  // Poll for evaluation events
  useEffect(() => {
    console.log(`[POLLING EFFECT] evaluationId: ${evaluationId}, isEvaluating: ${isEvaluating}`);
    if (!evaluationId || !isEvaluating) {
      console.log(`[POLLING EFFECT] Skipping - missing evaluationId or not evaluating`);
      return;
    }
    
    console.log(`[POLLING EFFECT] Starting polling for evaluation ${evaluationId}`);
    let intervalId: NodeJS.Timeout;
    let eventIndex = 0;
    let shouldStop = false;
    
    const pollEvents = async () => {
      if (shouldStop) return;
      
      console.log(`[POLL] Fetching events - evaluationId: ${evaluationId}, eventIndex: ${eventIndex}`);
      
      try {
        const startTime = Date.now();
        const response = await fetch(`/api/evaluation/events/${evaluationId}?start_index=${eventIndex}`);
        const fetchTime = Date.now() - startTime;
        console.log(`[POLL] Fetch completed in ${fetchTime}ms`);
        
        if (!response.ok) {
          console.error(`❌ Failed to fetch events: ${response.status} ${response.statusText}`);
          const errorText = await response.text();
          console.error('Error response:', errorText);
          
          // If evaluation not found (404), stop polling and clear state
          if (response.status === 404 || errorText.includes('not found')) {
            console.log('🛑 Evaluation not found, stopping polling and clearing state');
            shouldStop = true;
            setIsEvaluating(false);
            setEvaluationId(null);
          }
          return;
        }
        
        const data = await response.json();
        console.log(`[POLL] Received response - events: ${data.events?.length || 0}, status: ${data.status}`);
        
        if (data.events && data.events.length > 0) {
          // The backend now returns only NEW events based on start_index
          // So we can simply append all events returned
          setEvaluationEvents(prev => {
            const updated = [...prev, ...data.events];
            return updated;
          });
          
          // Update eventIndex OUTSIDE of setState to avoid closure issues
          eventIndex += data.events.length;
          
          // Check if evaluation is complete
          const completeEvent = data.events.find((e: any) => 
            e.type === 'evaluation_complete' || e.type === 'overall_score'
          );
          
          if (completeEvent || data.status === 'completed') {
            shouldStop = true;
            
            // Wait longer to let users see the completed events
            setTimeout(() => {
              // Find the overall score event to get the score
              const scoreEvent = data.events.find((e: any) => e.type === 'overall_score');
              const overallScore = scoreEvent?.score || 0.5;
              
              // Extract evaluation ID from the run directory
              // The evaluation ID is in the event data
              const evalId = evaluationId;
              
              // Set the evaluation report
              // The report URL format is /api/qe/report/{evaluation_id}/report.html
              setEvaluationReport({
                test_case_id: testCase?.id || '',
                evaluation_id: evalId,
                overall_score: overallScore,
                report_url: `/api/qe/report/${evalId}/report.html`,
                report_dir: '',
                dimension_results: {},
                execution_time_ms: 0
              });
              
              setIsEvaluating(false);
            }, 3000); // 3 seconds to view the completed events
          }
        }
        
        // Also check if status is failed
        if (data.status === 'failed') {
          shouldStop = true;
          setIsEvaluating(false);
        }
      } catch (error) {
        console.error('❌ Error polling evaluation events:', error);
      }
    };
    
    // Start polling immediately
    pollEvents();
    
    // Poll every second
    intervalId = setInterval(() => {
      if (shouldStop) {
        clearInterval(intervalId);
        return;
      }
      pollEvents();
    }, 1000);
    
    // Cleanup
    return () => {
      shouldStop = true;
      if (intervalId) clearInterval(intervalId);
    };
  }, [evaluationId, isEvaluating]);

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
      actual_specialties: testCase.actual_specialties,
      actual_key_data_points: testCase.actual_key_data_points
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
        actual_specialties: testCase.actual_specialties,
        actual_key_data_points: testCase.actual_key_data_points
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
    setEvaluationEvents([]); // Clear previous events
    setEvaluationReport(null); // Clear previous report
    
    try {
      const response = await fetch(`/api/test-cases/${testCase.id}/evaluate`, {
        method: 'POST'
      });

      if (!response.ok) {
        throw new Error('Evaluation failed');
      }

      const result = await response.json();
      console.log(`[EVALUATION START] Received evaluation ID: ${result.evaluation_id}`);
      
      // Store evaluation ID for event polling
      setEvaluationId(result.evaluation_id);
      console.log(`[EVALUATION START] Set evaluationId state`);
    } catch (error) {
      console.error('Evaluation error:', error);
      alert('Error running evaluation. Please try again.');
      setIsEvaluating(false);
    }
  };

  // Handle save test case
  const handleSaveTestCase = async () => {
    if (!testCase) return;
    
    try {
      // Prepare test case data for saving
      const saveData = {
        id: testCase.id,
        query: testCase.query,
        expected_complexity: testCase.expected_complexity,
        expected_specialties: testCase.expected_specialties,
        key_data_points: testCase.key_data_points,
        expected_cost_threshold: testCase.expected_cost_threshold,
        notes: testCase.notes,
        category: testCase.category || 'general',
        based_on_real_query: testCase.based_on_real_query !== false,
        trace_id: testCase.trace_id
      };

      const response = await fetch('/api/test-cases/save-to-storage', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(saveData),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to save test case');
      }

      const result = await response.json();
      console.log('Test case saved successfully:', result);
      
      // Show success message in UI instead of alert
      // The success will be visible through the running evaluation
    } catch (error) {
      console.error('Error saving test case:', error);
      // Don't show error alert - let the evaluation proceed
      // The user will see if there are issues through the evaluation results
    }
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
            evaluationEvents={evaluationEvents}
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