import React from 'react';
import { Search, BarChart3, Wrench, Brain, Users, Heart, CheckCircle } from 'lucide-react';

const LLMEvalLifecycleVisualization = () => {
  return (
    <div className="w-full bg-gradient-to-br from-blue-50 via-purple-50 to-pink-50 p-8 overflow-x-auto">
      {/* Title */}
      <div className="text-center mb-12">
        <h2 className="font-bold mb-3" style={{ fontSize: '44px' }}>
          <span className="bg-gradient-to-r from-pink-600 via-blue-600 to-green-600 bg-clip-text text-transparent">
            The Agent Eval Lifecycle Applied to Multi-Agent Health Systems
          </span>
        </h2>
        <p className="text-gray-700 max-w-4xl mx-auto" style={{ fontSize: '29px' }}>
          Transforming multi-agent chaos into systematic evaluation excellence
        </p>
      </div>

      {/* Main Lifecycle Container */}
      <div className="max-w-7xl mx-auto">
        <div className="relative" style={{ height: '1000px' }}>
          {/* Center Hub */}
          <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 z-20">
            <div className="w-80 h-80 bg-white rounded-full shadow-2xl border-4 border-purple-300 flex flex-col items-center justify-center">
              <div className="flex items-center gap-3 mb-3">
                <Brain className="w-12 h-12 text-blue-600" />
                <Users className="w-12 h-12 text-purple-600" />
              </div>
              <h3 className="text-4xl font-bold text-gray-800 text-center">Multi-Agent<br/>Health System</h3>
              <div className="text-center mt-3">
                <p className="text-2xl text-gray-600">8 Specialist Agents</p>
                <p className="text-xl text-gray-500">21+ LLM Calls</p>
                <p className="text-xl text-gray-500">15+ Tool Invocations</p>
              </div>
            </div>
          </div>

          {/* Circular Arrows Background */}
          <svg className="absolute inset-0 w-full h-full" viewBox="0 0 1000 1000" style={{ zIndex: 1 }}>
            <defs>
              <marker id="arrowhead" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto">
                <polygon points="0 0, 10 3, 0 6" fill="#9CA3AF" />
              </marker>
            </defs>
            {/* Circular path with arrows */}
            <path
              d="M 500 120 A 380 380 0 0 1 880 500 A 380 380 0 0 1 500 880 A 380 380 0 0 1 120 500 A 380 380 0 0 1 500 120"
              fill="none"
              stroke="#9CA3AF"
              strokeWidth="3"
              strokeDasharray="10 5"
              markerEnd="url(#arrowhead)"
              markerMid="url(#arrowhead)"
            />
          </svg>

          {/* Analyze Phase - Top */}
          <div className="absolute left-1/2 transform -translate-x-1/2" style={{ top: '-25px', width: '500px', zIndex: 10 }}>
            <div className="bg-gradient-to-br from-pink-100 to-rose-100 rounded-xl p-8 border-2 border-pink-300 shadow-xl">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-16 h-16 bg-pink-500 rounded-full flex items-center justify-center">
                  <Search className="w-10 h-10 text-white" />
                </div>
                <div>
                  <h3 className="text-4xl font-bold text-pink-800">1. Analyze</h3>
                  <p className="text-pink-600 text-xl">Build vocabulary of failure</p>
                </div>
              </div>
              
              <div className="grid grid-cols-2 gap-3">
                <div className="bg-white/80 rounded-lg p-4">
                  <h4 className="font-semibold text-pink-700 mb-2 text-xl">Key Steps:</h4>
                  <ul className="text-lg text-gray-700 space-y-1">
                    <li>• Query Dimensions</li>
                    <li>• Diverse Queries</li>
                    <li>• Multi-Agent Tracing</li>
                    <li>• Open Coding</li>
                    <li>• Axial Coding</li>
                  </ul>
                </div>
                
                <div className="space-y-2">
                  <div className="bg-white rounded p-3 border border-pink-200">
                    <div className="flex items-center gap-1 mb-1">
                      <Heart className="w-5 h-5 text-pink-500" />
                      <span className="text-lg font-semibold">HbA1c Query</span>
                    </div>
                    <p className="text-lg text-gray-600">Misclassified complexity</p>
                  </div>
                  
                  <div className="bg-pink-200/50 rounded p-3 text-center">
                    <p className="text-pink-700 font-bold text-xl">→ Failure Taxonomy</p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Measure Phase - Bottom Right */}
          <div className="absolute" style={{ bottom: '-10px', right: '-10px', width: '500px', zIndex: 10 }}>
            <div className="bg-gradient-to-br from-blue-100 to-cyan-100 rounded-xl p-8 border-2 border-blue-300 shadow-xl">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-16 h-16 bg-blue-500 rounded-full flex items-center justify-center">
                  <BarChart3 className="w-10 h-10 text-white" />
                </div>
                <div>
                  <h3 className="text-4xl font-bold text-blue-800">2. Measure</h3>
                  <p className="text-blue-600 text-xl">Quantify performance</p>
                </div>
              </div>
              
              <div className="grid grid-cols-2 gap-3">
                <div className="bg-white/80 rounded-lg p-4">
                  <h4 className="font-semibold text-blue-700 mb-2 text-xl">Key Steps:</h4>
                  <ul className="text-lg text-gray-700 space-y-1">
                    <li>• Metadata Architecture</li>
                    <li>• Eval Methods</li>
                    <li>• Test Case Design</li>
                    <li>• LLM-as-Judge</li>
                  </ul>
                </div>
                
                <div className="space-y-2">
                  <div className="bg-white rounded p-3 border border-blue-200">
                    <div className="flex items-center gap-1 mb-1">
                      <BarChart3 className="w-5 h-5 text-blue-500" />
                      <span className="text-lg font-semibold">CMO: 73.4%</span>
                    </div>
                    <p className="text-lg text-gray-600">21 test cases</p>
                  </div>
                  
                  <div className="bg-blue-200/50 rounded p-3 text-center">
                    <p className="text-blue-700 font-bold text-xl">→ Eval Scores</p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Improve Phase - Bottom Left */}
          <div className="absolute" style={{ bottom: '30px', left: '30px', width: '500px', zIndex: 10 }}>
            <div className="bg-gradient-to-br from-green-100 to-emerald-100 rounded-xl p-8 border-2 border-green-300 shadow-xl">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-16 h-16 bg-green-500 rounded-full flex items-center justify-center">
                  <Wrench className="w-10 h-10 text-white" />
                </div>
                <div>
                  <h3 className="text-4xl font-bold text-green-800">3. Improve</h3>
                  <p className="text-green-600 text-xl">Diagnose & prescribe fixes</p>
                </div>
              </div>
              
              <div className="grid grid-cols-2 gap-3">
                <div className="bg-white/80 rounded-lg p-4">
                  <h4 className="font-semibold text-green-700 mb-2 text-xl">Key Steps:</h4>
                  <ul className="text-lg text-gray-700 space-y-1">
                    <li>• LLM-as-Diagnostic-Engine</li>
                    <li>• Root Cause Analysis</li>
                    <li>• Targeted Fixes</li>
                  </ul>
                </div>
                
                <div className="space-y-2">
                  <div className="bg-white rounded p-3 border border-green-200">
                    <div className="flex items-center gap-1 mb-1">
                      <CheckCircle className="w-5 h-5 text-green-500" />
                      <span className="text-lg font-semibold">Prompt Fix</span>
                    </div>
                    <p className="text-lg text-gray-600">Added correlation rules</p>
                  </div>
                  
                  <div className="bg-green-200/50 rounded p-3 text-center">
                    <p className="text-green-700 font-bold text-xl">→ Improvements</p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Phase Labels on the Circle */}
          <div className="absolute" style={{ top: '45%', right: '200px', transform: 'translateY(-50%)' }}>
            <p className="text-gray-500 font-semibold text-3xl">Understand Failures</p>
          </div>
          
          <div className="absolute left-1/2 transform -translate-x-1/2" style={{ bottom: '200px', marginLeft: '15px' }}>
            <p className="text-gray-500 font-semibold text-3xl">Measure & Track</p>
          </div>
          
          <div className="absolute" style={{ top: '45%', left: '200px', transform: 'translateY(-50%)' }}>
            <p className="text-gray-500 font-semibold text-3xl">Diagnose & Fix</p>
          </div>
        </div>

        {/* Bottom Summary */}
        <div className="mt-6 bg-white rounded-xl p-8 shadow-lg border-2 border-gray-200">
          <div className="text-center">
            <h3 className="font-bold text-gray-800 mb-4" style={{ fontSize: '28px' }}>The Eval-Driven Development Engine</h3>
            <p className="text-gray-700 max-w-4xl mx-auto" style={{ fontSize: '29px' }}>
              This three-phase cycle transforms chaotic multi-agent failures<br />
              into systematic improvements through continuous evaluation.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LLMEvalLifecycleVisualization;