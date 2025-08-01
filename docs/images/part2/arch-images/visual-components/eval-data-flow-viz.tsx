import React, { useState } from 'react';
import { 
  Heart, MessageSquare, Save, Wrench, Code, 
  ArrowRight, PlayCircle, Brain,
  Terminal, Bot, ArrowDown
} from 'lucide-react';

const EvalDataFlowVisualization = () => {
  const [hoveredStep, setHoveredStep] = useState(null);

  const steps = [
    {
      id: 1,
      title: "Health Query Execution",
      icon: Heart,
      color: "purple",
      bgGradient: "from-purple-100 to-violet-100",
      borderColor: "border-purple-300",
      iconBg: "bg-purple-500",
      content: {
        action: "Execute health query",
        tool: "Health Insight App",
        output: "CMO provides answer",
        trigger: "Click 'Create Test Case'"
      },
      details: [
        "User asks: 'How has my HbA1c changed since starting metformin?'",
        "CMO orchestrates 8 specialist agents",
        "21+ LLM calls, 15+ tool invocations",
        "Complete trace captured"
      ]
    },
    {
      id: 2,
      title: "Trace Analysis with EDA",
      icon: MessageSquare,
      color: "blue",
      bgGradient: "from-blue-100 to-cyan-100",
      borderColor: "border-blue-300",
      iconBg: "bg-blue-500",
      content: {
        action: "Review trace & identify issues",
        tool: "Eval Dev Studio",
        output: "Annotated observations",
        trigger: "Collaborate with EDA"
      },
      details: [
        "❌ Complexity: STANDARD → Should be COMPLEX",
        "❌ Missing specialists: Laboratory, Preventive Medicine",
        "❌ Correlation analysis incomplete",
        "💬 'EDA, the complexity should be COMPLEX'"
      ]
    },
    {
      id: 3,
      title: "Test Case Iteration",
      icon: Bot,
      color: "indigo",
      bgGradient: "from-indigo-100 to-purple-100",
      borderColor: "border-indigo-300",
      iconBg: "bg-indigo-500",
      content: {
        action: "Refine test expectations",
        tool: "EDA Assistant",
        output: "Updated test case",
        trigger: "Iterate until satisfied"
      },
      details: [
        "EDA updates expected_complexity: 'COMPLEX'",
        "Adds missing specialists to expected list",
        "Defines key_data_points to validate",
        "Real-time test case updates"
      ]
    },
    {
      id: 4,
      title: "Evaluation Execution",
      icon: PlayCircle,
      color: "green",
      bgGradient: "from-green-100 to-emerald-100",
      borderColor: "border-green-300",
      iconBg: "bg-green-500",
      content: {
        action: "Run evaluation",
        tool: "Eval Framework",
        output: "Dimension scores",
        trigger: "Click 'Run Evaluation'"
      },
      details: [
        "✅ Complexity Classification: 0.00 (Failed)",
        "⚠️ Specialty Selection: 0.81 (Partial)",
        "✅ Analysis Quality: 0.85",
        "Overall Score: 73.4%"
      ]
    },
    {
      id: 5,
      title: "Test Case Storage",
      icon: Save,
      color: "orange",
      bgGradient: "from-orange-100 to-amber-100",
      borderColor: "border-orange-300",
      iconBg: "bg-orange-500",
      content: {
        action: "Save to unified storage",
        tool: "File System",
        output: "Persisted test case",
        trigger: "Click 'Save Test Case'"
      },
      details: [
        "Path: evaluation/data/test-suites/",
        "         studio-generated/cmo/",
        "File: complex_002.json",
        "Schema-validated JSON format"
      ]
    },
    {
      id: 6,
      title: "LLM Judge Analysis",
      icon: Brain,
      color: "pink",
      bgGradient: "from-pink-100 to-rose-100",
      borderColor: "border-pink-300",
      iconBg: "bg-pink-500",
      content: {
        action: "Review recommendations",
        tool: "LLM Judge Diagnostics",
        output: "Targeted fixes",
        trigger: "Click failed dimensions"
      },
      details: [
        "📝 MODIFY: Complexity criteria in prompt",
        "➕ ADD: Correlation keywords to pharmacy",
        "🎯 TARGET: 1_gather_data_assess_complexity.txt",
        "Root cause analysis provided"
      ]
    },
    {
      id: 7,
      title: "Apply Fixes with Claude Code",
      icon: Code,
      color: "purple",
      bgGradient: "from-purple-100 to-violet-100",
      borderColor: "border-purple-300",
      iconBg: "bg-purple-500",
      content: {
        action: "Implement changes",
        tool: "Claude Code",
        output: "Updated prompts",
        trigger: "Apply recommendations"
      },
      details: [
        "Claude Code opens target files",
        "Applies LLM Judge recommendations",
        "Updates prompt templates",
        "Commits changes"
      ]
    },
    {
      id: 8,
      title: "Automated Test Suite Run",
      icon: Terminal,
      color: "teal",
      bgGradient: "from-teal-100 to-cyan-100",
      borderColor: "border-teal-300",
      iconBg: "bg-teal-500",
      content: {
        action: "Run test case in CI/CD pipeline",
        tool: "Test Suite / CI Pipeline",
        output: "Automated score validation",
        trigger: "Integrate into test suite"
      },
      details: [
        "Test case now part of regression suite",
        "Runs automatically on every PR/commit",
        "$ pytest tests/eval/test_complex_002.py",
        "✅ Validates fixes improved score: 73.4% → 91.2%",
        "✅ Prevents regression in future changes"
      ]
    }
  ];

  const StepCard = ({ step, idx }) => (
    <div 
      className="relative h-full"
      onMouseEnter={() => setHoveredStep(step.id)}
      onMouseLeave={() => setHoveredStep(null)}
    >
      <div className={`bg-gradient-to-br ${step.bgGradient} rounded-xl p-5 shadow-lg border-2 ${step.borderColor} transition-all duration-300 h-full flex flex-col ${
        hoveredStep === step.id ? 'scale-105 shadow-2xl' : ''
      }`} style={{ height: '320px' }}>
        {/* Step Number Badge */}
        <div className="absolute -top-3 -left-3 w-10 h-10 bg-white rounded-full shadow-md flex items-center justify-center border-2 border-gray-300">
          <span className="font-bold text-gray-700">{step.id}</span>
        </div>

        {/* Header */}
        <div className="flex items-center gap-3 mb-3">
          <div className={`w-14 h-14 ${step.iconBg} rounded-full flex items-center justify-center shadow-md`}>
            <step.icon className="w-8 h-8 text-white" />
          </div>
          <h3 className={`text-2xl font-bold text-${step.color}-800 leading-tight`}>{step.title}</h3>
        </div>

        {/* Content */}
        <div className="space-y-2 flex-1">
          <div className="bg-white/80 rounded-lg p-3">
            <p className="text-base text-gray-600 mb-1">
              <span className="font-semibold">Action:</span> {step.content.action}
            </p>
            <p className="text-base text-gray-600 mb-1">
              <span className="font-semibold">Tool:</span> {step.content.tool}
            </p>
            <p className="text-base text-gray-600">
              <span className="font-semibold">Output:</span> {step.content.output}
            </p>
          </div>

          <div className={`bg-${step.color}-200/50 rounded-lg p-2 text-center`}>
            <p className={`text-${step.color}-700 font-semibold text-base`}>
              {step.content.trigger}
            </p>
          </div>
        </div>

        {/* Hover Details */}
        {hoveredStep === step.id && (
          <div className="absolute top-full left-0 right-0 mt-2 bg-white rounded-lg shadow-xl p-3 border z-20" style={{ width: '300px' }}>
            <h4 className={`font-semibold text-${step.color}-700 mb-2 text-lg`}>Details:</h4>
            <ul className="space-y-1">
              {step.details.map((detail, i) => (
                <li key={i} className="text-base text-gray-600">{detail}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );

  return (
    <div className="w-full bg-gradient-to-br from-purple-50 via-blue-50 to-pink-50 p-8">
      {/* Title */}
      <div className="text-center mb-8">
        <h2 className="text-5xl font-bold mb-3">
          <span className="bg-gradient-to-r from-purple-600 via-blue-600 to-pink-600 bg-clip-text text-transparent">
            End-to-End Evaluation Development Flow
          </span>
        </h2>
        <p className="text-2xl text-gray-700 max-w-3xl mx-auto">
          From health query to improved agent performance through systematic evaluation
        </p>
      </div>

      {/* Main Flow Container */}
      <div className="max-w-6xl mx-auto">
        {/* First Row */}
        <div className="grid grid-cols-4 gap-4 mb-24 items-stretch relative">
          {steps.slice(0, 4).map((step, idx) => (
            <React.Fragment key={step.id}>
              <div className="relative">
                <StepCard step={step} idx={idx} />
                {idx < 3 && (
                  <div className="absolute" style={{ 
                    right: '-25px', 
                    top: '50%', 
                    transform: 'translateY(-50%)',
                    zIndex: 10 
                  }}>
                    <ArrowRight className="w-8 h-8 text-gray-400" />
                  </div>
                )}
              </div>
            </React.Fragment>
          ))}
        </div>

        {/* Connector Arrow Down */}
        <div className="flex justify-center mb-12">
          <div className="flex flex-col items-center">
            <ArrowDown className="w-10 h-10 text-gray-400" />
            <p className="text-base text-gray-600 font-semibold mt-1">Save & Analyze</p>
          </div>
        </div>

        {/* Second Row */}
        <div className="grid grid-cols-4 gap-4 mb-20 items-stretch relative">
          {steps.slice(4, 8).map((step, idx) => (
            <React.Fragment key={step.id}>
              <div className="relative">
                <StepCard step={step} idx={idx + 4} />
                {idx < 3 && (
                  <div className="absolute" style={{ 
                    right: '-25px', 
                    top: '50%', 
                    transform: 'translateY(-50%)',
                    zIndex: 10 
                  }}>
                    <ArrowRight className="w-8 h-8 text-gray-400" />
                  </div>
                )}
              </div>
            </React.Fragment>
          ))}
        </div>

        {/* Bottom Summary */}
        <div className="mt-8 bg-white rounded-xl p-6 shadow-lg border-2 border-gray-200">
          <div className="text-center">
            <h3 className="text-3xl font-bold text-gray-800 mb-2">Continuous Improvement Through Collaboration</h3>
            <p className="text-lg text-gray-600">
              This workflow combines human expertise, AI assistance, and systematic evaluation
              to transform agent failures into measurable improvements—turning every error into an opportunity for growth.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default EvalDataFlowVisualization;