import React from 'react';
import { Eye, Settings, Network, ArrowRight, AlertTriangle, Brain, Users, Zap } from 'lucide-react';

const ThreeGulfsVisualization = () => {
  return (
    <div className="w-full bg-gradient-to-br from-blue-50 via-purple-50 to-pink-50 p-8">
      {/* Title */}
      <div className="text-center mb-12">
        <h2 className="font-bold mb-3" style={{ fontSize: '44px' }}>
          <span className="bg-gradient-to-r from-pink-600 via-blue-600 to-green-600 bg-clip-text text-transparent">
            The Three Gulfs: Single Agent → Multi-Agent Explosion
          </span>
        </h2>
        <p className="text-gray-700 max-w-4xl mx-auto" style={{ fontSize: '29px' }}>
          How evaluation complexity multiplies exponentially with agent coordination
        </p>
      </div>

      {/* Main Content */}
      <div className="max-w-6xl mx-auto">
        <div className="flex items-center justify-center gap-8">
          
          {/* Left Panel: Single Agent */}
          <div className="bg-gradient-to-br from-blue-100 to-cyan-100 rounded-xl p-8 border-2 border-blue-300 shadow-xl" style={{ width: '400px' }}>
            <div className="flex items-center gap-3 mb-6">
              <div className="w-16 h-16 bg-blue-500 rounded-full flex items-center justify-center">
                <Brain className="w-10 h-10 text-white" />
              </div>
              <div>
                <h3 className="text-4xl font-bold text-blue-800">Single Agent</h3>
                <p className="text-blue-600 text-xl">Already challenging</p>
              </div>
            </div>
            
            {/* Three Gulfs */}
            <div className="space-y-3">
              <div className="bg-white/80 rounded-lg p-4">
                <div className="flex items-center gap-3 mb-2">
                  <Eye className="w-6 h-6 text-blue-600" />
                  <h4 className="font-semibold text-blue-700 text-xl">Gulf of Comprehension</h4>
                </div>
                <p className="text-lg text-gray-700">• Non-deterministic outputs</p>
                <p className="text-lg text-gray-700">• Hidden reasoning paths</p>
              </div>
              
              <div className="bg-white/80 rounded-lg p-4">
                <div className="flex items-center gap-3 mb-2">
                  <Settings className="w-6 h-6 text-orange-600" />
                  <h4 className="font-semibold text-orange-700 text-xl">Gulf of Specification</h4>
                </div>
                <p className="text-lg text-gray-700">• Ambiguous prompts</p>
                <p className="text-lg text-gray-700">• Implicit assumptions</p>
              </div>
              
              <div className="bg-white/80 rounded-lg p-4">
                <div className="flex items-center gap-3 mb-2">
                  <Network className="w-6 h-6 text-purple-600" />
                  <h4 className="font-semibold text-purple-700 text-xl">Gulf of Generalization</h4>
                </div>
                <p className="text-lg text-gray-700">• Edge case surprises</p>
                <p className="text-lg text-gray-700">• Inconsistent behavior</p>
              </div>
            </div>
          </div>

          {/* Center Arrow */}
          <div className="flex flex-col items-center">
            <div className="relative">
              <div className="w-24 h-24 bg-white rounded-full shadow-xl flex items-center justify-center border-4 border-purple-300">
                <ArrowRight className="w-12 h-12 text-purple-600" />
              </div>
              <div className="absolute -top-6 left-1/2 transform -translate-x-1/2">
                <span className="text-4xl font-bold text-red-600">×8</span>
              </div>
            </div>
            <p className="text-2xl text-gray-600 mt-3">agents</p>
          </div>

          {/* Right Panel: Multi-Agent Explosion */}
          <div className="bg-gradient-to-br from-pink-100 to-rose-100 rounded-xl p-8 border-2 border-pink-300 shadow-xl" style={{ width: '400px' }}>
            <div className="flex items-center gap-3 mb-6">
              <div className="w-16 h-16 bg-pink-500 rounded-full flex items-center justify-center">
                <Users className="w-10 h-10 text-white" />
              </div>
              <div>
                <h3 className="text-4xl font-bold text-pink-800">8 Agents</h3>
                <p className="text-pink-600 text-xl">Exponential cascade</p>
              </div>
            </div>
            
            {/* Explosion Metrics */}
            <div className="bg-white/80 rounded-lg p-4 mb-4">
              <div className="flex items-center gap-2 mb-3">
                <Zap className="w-6 h-6 text-red-600" />
                <h4 className="font-semibold text-red-700 text-xl">Cascade Effect</h4>
              </div>
              
              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <span className="text-lg text-gray-700">LLM Calls:</span>
                  <span className="text-2xl font-bold text-red-600">21+</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-lg text-gray-700">Tool Invocations:</span>
                  <span className="text-2xl font-bold text-orange-600">15+</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-lg text-gray-700">Processing Time:</span>
                  <span className="text-2xl font-bold text-purple-600">90+ sec</span>
                </div>
              </div>
            </div>
            
            {/* Complexity Indicators */}
            <div className="space-y-2">
              <div className="bg-pink-200/50 rounded p-3">
                <p className="text-lg text-pink-700 font-semibold">→ Coordination ambiguities</p>
              </div>
              <div className="bg-pink-200/50 rounded p-3">
                <p className="text-lg text-pink-700 font-semibold">→ Compound failure modes</p>
              </div>
              <div className="bg-pink-200/50 rounded p-3">
                <p className="text-lg text-pink-700 font-semibold">→ Emergent behaviors</p>
              </div>
            </div>
            
            {/* Bottom Alert */}
            <div className="mt-4 bg-red-200/50 rounded p-3 text-center">
              <p className="text-red-700 font-bold text-xl">Traditional testing fails</p>
            </div>
          </div>
          
        </div>

        {/* Bottom Summary */}
        <div className="mt-8 bg-white rounded-xl p-8 shadow-lg border-2 border-gray-200">
          <div className="text-center">
            <h3 className="font-bold text-gray-800 mb-4" style={{ fontSize: '28px' }}>The Multiplication Effect</h3>
            <p className="text-gray-600 max-w-4xl mx-auto leading-relaxed" style={{ fontSize: '22px' }}>
              Each gulf multiplies across agents. A simple health query triggers cascading decisions through 8 specialists, creating interdependent failures that traditional testing cannot handle.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ThreeGulfsVisualization;