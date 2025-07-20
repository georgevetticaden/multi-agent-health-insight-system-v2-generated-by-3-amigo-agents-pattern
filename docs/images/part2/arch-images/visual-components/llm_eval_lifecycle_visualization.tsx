import React from 'react';
import { Search, BarChart3, Wrench, Brain, Users, Heart, CheckCircle } from 'lucide-react';

const LLMEvalLifecycleVisualization = () => {
  return (
    <div className="w-full bg-gradient-to-br from-blue-50 via-purple-50 to-pink-50 p-8 overflow-x-auto">
      {/* Title */}
      <div className="text-center mb-12">
        <h2 className="text-5xl font-bold mb-3">
          <span className="bg-gradient-to-r from-pink-600 via-blue-600 to-green-600 bg-clip-text text-transparent">
            The LLM Evaluation Lifecycle Applied to Multi-Agent Health Systems
          </span>
        </h2>
        <p className="text-3xl text-gray-700 max-w-4xl mx-auto">
          Transforming multi-agent chaos into systematic evaluation excellence
        </p>
      </div>

      {/* Main Lifecycle Container */}
      <div className="max-w-6xl mx-auto">
        <div className="relative" style={{ height: '800px' }}>
          {/* Center Hub */}
          <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 z-20">
            <div className="w-64 h-64 bg-white rounded-full shadow-2xl border-4 border-purple-300 flex flex-col items-center justify-center">
              <div className="flex items-center gap-3 mb-3">
                <Brain className="w-10 h-10 text-blue-600" />
                <Users className="w-10 h-10 text-purple-600" />
              </div>
              <h3 className="text-3xl font-bold text-gray-800 text-center">Multi-Agent<br/>Health System</h3>
              <div className="text-center mt-3">
                <p className="text-lg text-gray-600">8 Specialist Agents</p>
                <p className="text-base text-gray-500">21+ LLM Calls</p>
                <p className="text-base text-gray-500">15+ Tool Invocations</p>
              </div>
            </div>
          </div>

          {/* Circular Arrows Background */}
          <svg className="absolute inset-0 w-full h-full" viewBox="0 0 800 800" style={{ zIndex: 1 }}>
            <defs>
              <marker id="arrowhead" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto">
                <polygon points="0 0, 10 3, 0 6" fill="#9CA3AF" />
              </marker>
            </defs>
            {/* Circular path with arrows */}
            <path
              d="M 400 150 A 250 250 0 0 1 650 400 A 250 250 0 0 1 400 650 A 250 250 0 0 1 150 400 A 250 250 0 0 1 400 150"
              fill="none"
              stroke="#9CA3AF"
              strokeWidth="3"
              strokeDasharray="10 5"
              markerEnd="url(#arrowhead)"
              markerMid="url(#arrowhead)"
            />
          </svg>

          {/* Analyze Phase - Top */}
          <div className="absolute top-0 left-1/2 transform -translate-x-1/2" style={{ width: '380px', zIndex: 10 }}>
            <div className="bg-gradient-to-br from-pink-100 to-rose-100 rounded-xl p-6 border-2 border-pink-300 shadow-xl">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-14 h-14 bg-pink-500 rounded-full flex items-center justify-center">
                  <Search className="w-8 h-8 text-white" />
                </div>
                <div>
                  <h3 className="text-3xl font-bold text-pink-800">1. Analyze</h3>
                  <p className="text-pink-600 text-base">Identify failure patterns</p>
                </div>
              </div>
              
              <div className="grid grid-cols-2 gap-3">
                <div className="bg-white/80 rounded-lg p-3">
                  <h4 className="font-semibold text-pink-700 mb-2 text-base">Key Steps:</h4>
                  <ul className="text-sm text-gray-700 space-y-1">
                    <li>• Query Dimensions</li>
                    <li>• Diverse Queries</li>
                    <li>• Tracing</li>
                    <li>• Open/Axial Coding</li>
                  </ul>
                </div>
                
                <div className="space-y-2">
                  <div className="bg-white rounded p-2 border border-pink-200">
                    <div className="flex items-center gap-1 mb-1">
                      <Heart className="w-4 h-4 text-pink-500" />
                      <span className="text-sm font-semibold">HbA1c Query</span>
                    </div>
                    <p className="text-sm text-gray-600">Misclassified complexity</p>
                  </div>
                  
                  <div className="bg-pink-200/50 rounded p-2 text-center">
                    <p className="text-pink-700 font-bold text-base">→ Failure Taxonomy</p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Measure Phase - Bottom Right */}
          <div className="absolute bottom-20 right-20" style={{ width: '380px', zIndex: 10 }}>
            <div className="bg-gradient-to-br from-blue-100 to-cyan-100 rounded-xl p-6 border-2 border-blue-300 shadow-xl">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-14 h-14 bg-blue-500 rounded-full flex items-center justify-center">
                  <BarChart3 className="w-8 h-8 text-white" />
                </div>
                <div>
                  <h3 className="text-3xl font-bold text-blue-800">2. Measure</h3>
                  <p className="text-blue-600 text-base">Quantify performance</p>
                </div>
              </div>
              
              <div className="grid grid-cols-2 gap-3">
                <div className="bg-white/80 rounded-lg p-3">
                  <h4 className="font-semibold text-blue-700 mb-2 text-base">Key Steps:</h4>
                  <ul className="text-sm text-gray-700 space-y-1">
                    <li>• Metadata Architecture</li>
                    <li>• Self-Defining Criteria</li>
                    <li>• Test Case Design</li>
                    <li>• Component Scoring</li>
                  </ul>
                </div>
                
                <div className="space-y-2">
                  <div className="bg-white rounded p-2 border border-blue-200">
                    <div className="flex items-center gap-1 mb-1">
                      <BarChart3 className="w-4 h-4 text-blue-500" />
                      <span className="text-sm font-semibold">CMO: 73.4%</span>
                    </div>
                    <p className="text-sm text-gray-600">21 test cases</p>
                  </div>
                  
                  <div className="bg-blue-200/50 rounded p-2 text-center">
                    <p className="text-blue-700 font-bold text-base">→ Eval Scores</p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Improve Phase - Bottom Left */}
          <div className="absolute bottom-20 left-20" style={{ width: '380px', zIndex: 10 }}>
            <div className="bg-gradient-to-br from-green-100 to-emerald-100 rounded-xl p-6 border-2 border-green-300 shadow-xl">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-14 h-14 bg-green-500 rounded-full flex items-center justify-center">
                  <Wrench className="w-8 h-8 text-white" />
                </div>
                <div>
                  <h3 className="text-3xl font-bold text-green-800">3. Improve</h3>
                  <p className="text-green-600 text-base">Fix systematic failures</p>
                </div>
              </div>
              
              <div className="grid grid-cols-2 gap-3">
                <div className="bg-white/80 rounded-lg p-3">
                  <h4 className="font-semibold text-green-700 mb-2 text-base">Key Steps:</h4>
                  <ul className="text-sm text-gray-700 space-y-1">
                    <li>• LLM-as-Judge</li>
                    <li>• Medical Scoring</li>
                    <li>• Root Cause Analysis</li>
                    <li>• Remediation</li>
                  </ul>
                </div>
                
                <div className="space-y-2">
                  <div className="bg-white rounded p-2 border border-green-200">
                    <div className="flex items-center gap-1 mb-1">
                      <CheckCircle className="w-4 h-4 text-green-500" />
                      <span className="text-sm font-semibold">Prompt Fix</span>
                    </div>
                    <p className="text-sm text-gray-600">Added correlation rules</p>
                  </div>
                  
                  <div className="bg-green-200/50 rounded p-2 text-center">
                    <p className="text-green-700 font-bold text-base">→ Improvements</p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Phase Labels on the Circle */}
          <div className="absolute" style={{ top: 'calc(50% - 80px)', right: '118px', transform: 'translateY(-50%)' }}>
            <p className="text-gray-500 font-semibold text-2xl">Collect & Organize</p>
          </div>
          
          <div className="absolute left-1/2 transform -translate-x-1/2" style={{ bottom: '90px' }}>
            <p className="text-gray-500 font-semibold text-2xl">Quantify & Score</p>
          </div>
          
          <div className="absolute" style={{ top: 'calc(50% - 75px)', left: '168px', transform: 'translateY(-50%)' }}>
            <p className="text-gray-500 font-semibold text-2xl">Fix & Iterate</p>
          </div>
        </div>

        {/* Bottom Summary */}
        <div className="mt-6 bg-white rounded-xl p-8 shadow-lg border-2 border-gray-200">
          <div className="text-center">
            <h3 className="text-3xl font-bold text-gray-800 mb-4">The Continuous Improvement Engine</h3>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto leading-relaxed">
              Each cycle through Analyze → Measure → Improve transforms multi-agent complexity 
              into systematic, measurable progress.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LLMEvalLifecycleVisualization;