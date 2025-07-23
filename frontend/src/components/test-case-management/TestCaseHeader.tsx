import React from 'react';
import { ChevronLeft, HelpCircle } from 'lucide-react';

const TestCaseHeader: React.FC = () => {
  const handleBack = () => {
    window.close();
  };

  const handleHelp = () => {
    alert('Test Case Management Help:\n\n1. Review the trace in the middle panel\n2. Chat with QE Agent to refine test case\n3. Type "run" to execute evaluation\n4. View results in the right panel');
  };

  return (
    <header className="bg-gradient-to-r from-blue-600 to-blue-700 text-white shadow-lg">
      <div className="px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">Eval Driven Agent Development Dashboard</h1>
            <p className="text-blue-100 text-sm mt-1">Create and manage test cases for continuous agent improvement</p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={handleBack}
              className="flex items-center gap-2 px-3 py-1.5 bg-white/10 hover:bg-white/20 rounded-md transition-colors"
            >
              <ChevronLeft className="w-4 h-4" />
              <span className="text-sm">Back to Health Insights</span>
            </button>
            
            <button
              onClick={handleHelp}
              className="p-2 hover:bg-white/10 rounded-md transition-colors"
              title="Help"
            >
              <HelpCircle className="w-5 h-5" />
            </button>
            
            {/* User Avatar */}
            <div className="flex items-center gap-2 bg-white/10 px-3 py-1.5 rounded-md">
              <div className="w-8 h-8 bg-gradient-to-br from-purple-500 to-pink-500 rounded-full flex items-center justify-center text-white font-semibold text-sm">
                GV
              </div>
              <span className="text-sm">George V.</span>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};

export default TestCaseHeader;