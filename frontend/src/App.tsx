import React from 'react';
import { BrowserRouter as Router, Route, Routes, useParams } from 'react-router-dom';
import TwoPanelLayout from './components/TwoPanelLayout';
import TestCaseThreePanelLayout from './components/test-case-management/TestCaseThreePanelLayout';
import './index.css';

function TestCaseManagementRoute() {
  const { traceId } = useParams<{ traceId: string }>();
  
  if (!traceId) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-semibold text-gray-900 mb-2">No Trace ID Provided</h1>
          <p className="text-gray-600">Please access this page from the Health Insight System.</p>
        </div>
      </div>
    );
  }

  return <TestCaseThreePanelLayout traceId={traceId} />;
}

function App() {
  // Check if we're on the test case management route
  const isTestCaseRoute = window.location.pathname.startsWith('/test-case-management/');
  
  if (isTestCaseRoute) {
    return (
      <Router>
        <Routes>
          <Route path="/test-case-management/:traceId" element={<TestCaseManagementRoute />} />
        </Routes>
      </Router>
    );
  }
  
  return <TwoPanelLayout />;
}

export default App;