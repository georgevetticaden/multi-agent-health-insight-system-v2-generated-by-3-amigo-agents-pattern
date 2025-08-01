import React from 'react';
import { Database, Activity, Clock, Stethoscope, FileQuestion, ArrowRight, Sparkles, FileText, Heart } from 'lucide-react';

const DimensionGenerationFramework = () => {
  return (
    <div className="w-full bg-gradient-to-br from-purple-50 via-blue-50 to-pink-50 p-8 overflow-x-auto">
      {/* Title */}
      <div className="text-center mb-10">
        <h2 className="text-5xl font-bold mb-3">
          <span className="bg-gradient-to-r from-purple-600 via-blue-600 to-pink-600 bg-clip-text text-transparent">
            From Dimensions to Diverse Health Queries
          </span>
        </h2>
        <p className="text-2xl text-gray-700 max-w-4xl mx-auto">
          Systematic generation of representative test cases for multi-agent evaluation
        </p>
      </div>

      {/* Main Flow Container */}
      <div className="max-w-7xl mx-auto">
        <div className="flex items-center justify-between gap-6">
          
          {/* Step 1: 5 Dimensions */}
          <div className="flex-1 max-w-sm">
            <div className="bg-white rounded-xl p-6 shadow-lg border-2 border-purple-200">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-14 h-14 bg-purple-500 rounded-full flex items-center justify-center">
                  <Database className="w-8 h-8 text-white" />
                </div>
                <h3 className="text-3xl font-bold text-purple-800">5 Dimensions</h3>
              </div>
              
              <div className="space-y-3">
                <div className="bg-purple-50 rounded-lg p-3 border border-purple-200">
                  <div className="flex items-center gap-2 mb-1">
                    <Database className="w-6 h-6 text-purple-600" />
                    <span className="font-semibold text-lg text-purple-700">Health Data Type</span>
                  </div>
                  <p className="text-base text-gray-600">Lab Results, Medications, Vital Signs...</p>
                </div>
                
                <div className="bg-purple-50 rounded-lg p-3 border border-purple-200">
                  <div className="flex items-center gap-2 mb-1">
                    <Activity className="w-6 h-6 text-purple-600" />
                    <span className="font-semibold text-lg text-purple-700">Analysis Complexity</span>
                  </div>
                  <p className="text-base text-gray-600">Simple → Correlation → Comprehensive</p>
                </div>
                
                <div className="bg-purple-50 rounded-lg p-3 border border-purple-200">
                  <div className="flex items-center gap-2 mb-1">
                    <Clock className="w-6 h-6 text-purple-600" />
                    <span className="font-semibold text-lg text-purple-700">Time Scope</span>
                  </div>
                  <p className="text-base text-gray-600">Latest → 3 Months → Multi-Year</p>
                </div>
                
                <div className="bg-purple-50 rounded-lg p-3 border border-purple-200">
                  <div className="flex items-center gap-2 mb-1">
                    <Stethoscope className="w-6 h-6 text-purple-600" />
                    <span className="font-semibold text-lg text-purple-700">Medical Specialty</span>
                  </div>
                  <p className="text-base text-gray-600">Cardiology, Endocrinology, Pharmacy...</p>
                </div>
                
                <div className="bg-purple-50 rounded-lg p-3 border border-purple-200">
                  <div className="flex items-center gap-2 mb-1">
                    <FileQuestion className="w-6 h-6 text-purple-600" />
                    <span className="font-semibold text-lg text-purple-700">Query Scenario</span>
                  </div>
                  <p className="text-base text-gray-600">Clear → Ambiguous → Complex Multi-Factor</p>
                </div>
              </div>
            </div>
          </div>

          {/* Arrow 1 */}
          <div className="flex flex-col items-center">
            <ArrowRight className="w-12 h-12 text-gray-400" />
            <p className="text-lg text-gray-600 mt-2 font-semibold">Combine</p>
          </div>

          {/* Step 2: Structured Tuples */}
          <div className="flex-1 max-w-md">
            <div className="bg-white rounded-xl p-6 shadow-lg border-2 border-blue-200">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-14 h-14 bg-blue-500 rounded-full flex items-center justify-center">
                  <FileText className="w-8 h-8 text-white" />
                </div>
                <h3 className="text-3xl font-bold text-blue-800">100 Structured Tuples</h3>
              </div>
              
              <div className="bg-blue-50 rounded-lg p-4 mb-4 border border-blue-200">
                <p className="text-base text-gray-700 mb-3">
                  <span className="font-semibold">25 Manual:</span> Ensure diverse coverage<br/>
                  <span className="font-semibold">75 LLM-Generated:</span> Maintain quality & variety
                </p>
                <div className="bg-blue-100 rounded-lg p-3 border border-blue-300">
                  <p className="text-base text-blue-800 font-semibold mb-1">Two-Step Process:</p>
                  <p className="text-base text-gray-700">
                    1. Generate tuples (avoid repetitive phrasing)<br/>
                    2. Convert each tuple → natural language query
                  </p>
                </div>
              </div>
              
              <div className="space-y-2">
                <div className="bg-gradient-to-r from-blue-100 to-purple-100 rounded-lg p-3 border border-blue-300">
                  <p className="text-base font-mono text-gray-700">
                    (Lab Results, <span className="text-blue-600">Correlation Analysis</span>, Multi-Year, Endocrinology, <span className="text-purple-600">Complex Multi-Factor</span>)
                  </p>
                </div>
                
                <div className="bg-gray-100 rounded-lg p-3 border border-gray-300">
                  <p className="text-base font-mono text-gray-600">
                    (Medications, Simple Lookup, Latest, Pharmacy, Clear)
                  </p>
                </div>
                
                <div className="bg-gray-100 rounded-lg p-3 border border-gray-300">
                  <p className="text-base font-mono text-gray-600">
                    (Vital Signs, Trend Analysis, 6 Months, Cardiology, Clear)
                  </p>
                </div>
                
                <div className="text-center text-gray-500 text-base">... 97 more tuples</div>
              </div>
            </div>
          </div>

          {/* Arrow 2 */}
          <div className="flex flex-col items-center">
            <ArrowRight className="w-12 h-12 text-gray-400" />
            <p className="text-lg text-gray-600 mt-2 font-semibold">Convert</p>
          </div>

          {/* Step 3: Natural Language Queries */}
          <div className="flex-1 max-w-md">
            <div className="bg-white rounded-xl p-6 shadow-lg border-2 border-pink-200">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-14 h-14 bg-pink-500 rounded-full flex items-center justify-center">
                  <Sparkles className="w-8 h-8 text-white" />
                </div>
                <h3 className="text-3xl font-bold text-pink-800">Natural Language Queries</h3>
              </div>
              
              <div className="space-y-3">
                <div className="bg-gradient-to-r from-pink-100 to-purple-100 rounded-lg p-4 border-2 border-pink-300">
                  <div className="flex items-center gap-2 mb-2">
                    <Heart className="w-6 h-6 text-pink-600" />
                    <span className="font-semibold text-lg text-pink-700">HbA1c Query (Complex)</span>
                  </div>
                  <p className="text-base text-gray-700 italic">
                    "How has my HbA1c level changed since I started taking metformin, has my dosage been adjusted over time based on my lab results, and is there a correlation between these changes and my weight measurements?"
                  </p>
                </div>
                
                <div className="bg-gray-100 rounded-lg p-3 border border-gray-300">
                  <p className="text-base text-gray-700">
                    "Am I taking metformin?"
                  </p>
                  <p className="text-sm text-gray-500 mt-1">Simple medication lookup</p>
                </div>
                
                <div className="bg-gray-100 rounded-lg p-3 border border-gray-300">
                  <p className="text-base text-gray-700">
                    "Show my blood pressure trends for the last 6 months"
                  </p>
                  <p className="text-sm text-gray-500 mt-1">Vital signs trend analysis</p>
                </div>
              </div>
              
              <div className="mt-4 bg-pink-50 rounded-lg p-3 text-center border border-pink-200">
                <p className="text-pink-700 font-semibold text-lg">100 Diverse Test Cases Ready</p>
              </div>
            </div>
          </div>
        </div>

        {/* Bottom Summary */}
        <div className="mt-10 bg-white rounded-xl p-6 shadow-lg border-2 border-gray-200">
          <div className="text-center">
            <h3 className="text-3xl font-bold text-gray-800 mb-3">Systematic Coverage, Not Random Guessing</h3>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              This dimensional approach ensures comprehensive test coverage across all complexity levels, 
              medical domains, and query patterns—revealing failure modes that random queries would miss.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DimensionGenerationFramework;