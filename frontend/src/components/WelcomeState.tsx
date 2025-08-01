import React, { useState, useEffect } from 'react';
import { Brain, Sparkles, ChevronRight, Heart, FlaskConical, Activity, Users, BarChart3, FileText, Shield, Pill, Apple } from 'lucide-react';

interface WelcomeStateProps {
  onStartConversation: (question?: string) => void;
}

interface SpecialistPreview {
  id: string;
  name: string;
  specialty: string;
  icon: React.ComponentType<any>;
  gradient: string;
  description: string;
}

const WelcomeState: React.FC<WelcomeStateProps> = ({ onStartConversation }) => {
  const [inputValue, setInputValue] = useState('');
  const [hoveredQuestion, setHoveredQuestion] = useState<number | null>(null);
  const [animationPhase, setAnimationPhase] = useState(0);
  
  const exampleQuestions = [
    {
      text: "What's my cholesterol trend over the last 15 years? I want to see trends across the top 4 cholesterol metrics including Triglycerides across that time period (standard)",
      shortText: "What's my 15-year cholesterol trend?",
      icon: Heart,
      color: 'border-red-200 bg-red-50 hover:bg-red-100',
      complexity: 'standard'
    },
    {
      text: "Analyze cholesterol relevant medication adherence patterns over that time period and how do they correlate with these cholesterol lab results.",
      shortText: "Medication adherence vs cholesterol correlation",
      icon: Pill,
      color: 'border-orange-200 bg-orange-50 hover:bg-orange-100',
      complexity: 'complex'
    },
    {
      text: "Show my abnormal lab results from labs this year?",
      shortText: "Show my abnormal lab results this year",
      icon: FlaskConical,
      color: 'border-blue-200 bg-blue-50 hover:bg-blue-100',
      complexity: 'simple'
    },
    {
      text: "How has my HbA1c level changed since I started taking metformin, has my dosage been adjusted over time based on my lab results, and is there a correlation between these changes and my weight measurements during the same period?",
      shortText: "HbA1c, metformin & weight correlation",
      icon: Activity,
      color: 'border-purple-200 bg-purple-50 hover:bg-purple-100',
      complexity: 'complex'
    }
  ];

  const specialists: SpecialistPreview[] = [
    {
      id: 'cmo',
      name: 'Dr. Vitality',
      specialty: 'Chief Medical Officer',
      icon: Brain,
      gradient: 'from-blue-500 to-blue-600',
      description: 'Orchestrates your medical team'
    },
    {
      id: 'cardio',
      name: 'Dr. Heart',
      specialty: 'Cardiology',
      icon: Heart,
      gradient: 'from-red-400 to-red-500',
      description: 'Cardiovascular health expert'
    },
    {
      id: 'lab',
      name: 'Dr. Lab',
      specialty: 'Laboratory Medicine',
      icon: FlaskConical,
      gradient: 'from-green-400 to-green-500',
      description: 'Lab results interpretation'
    },
    {
      id: 'endo',
      name: 'Dr. Hormone',
      specialty: 'Endocrinology',
      icon: Activity,
      gradient: 'from-purple-400 to-purple-500',
      description: 'Hormonal and metabolic health'
    },
    {
      id: 'data',
      name: 'Dr. Analytics',
      specialty: 'Data Analysis',
      icon: BarChart3,
      gradient: 'from-yellow-400 to-yellow-500',
      description: 'Health data insights'
    },
    {
      id: 'prev',
      name: 'Dr. Prevention',
      specialty: 'Preventive Medicine',
      icon: Shield,
      gradient: 'from-indigo-400 to-indigo-500',
      description: 'Wellness and prevention'
    },
    {
      id: 'pharm',
      name: 'Dr. Pharma',
      specialty: 'Pharmacy',
      icon: Pill,
      gradient: 'from-orange-400 to-orange-500',
      description: 'Medication management'
    },
    {
      id: 'nutrition',
      name: 'Dr. Nutrition',
      specialty: 'Nutrition',
      icon: Apple,
      gradient: 'from-emerald-400 to-emerald-500',
      description: 'Diet and nutritional health'
    }
  ];

  useEffect(() => {
    const timer = setInterval(() => {
      setAnimationPhase((prev) => (prev + 1) % 7);
    }, 3000);
    return () => clearInterval(timer);
  }, []);

  const handleQuestionClick = (question: string) => {
    setInputValue(question);
    // Add a small delay for visual feedback
    setTimeout(() => onStartConversation(question), 300);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (inputValue.trim()) {
      onStartConversation(inputValue);
    }
  };

  return (
    <div className="h-[calc(100vh-73px)] flex">
      {/* Left Panel - Welcome & Quick Start */}
      <div className="w-80 bg-white/60 backdrop-blur-sm p-6 overflow-y-auto border-r border-gray-200">
        <div className="space-y-6">
          <div>
            <h2 className="text-xl font-bold text-gray-900 mb-2">Welcome to Your Health Command Center</h2>
            <div className="bg-green-50 border border-green-200 rounded-lg p-3 flex items-center gap-2">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
              <span className="text-sm font-medium text-gray-700">Medical Team Status: Ready</span>
            </div>
          </div>

          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-800">👋 Meet Your Medical Team</h3>
            <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-200">
              <div className="flex items-center gap-3 mb-3">
                <div className="w-12 h-12 bg-gradient-to-r from-blue-500 to-blue-600 rounded-full flex items-center justify-center">
                  <Brain className="w-6 h-6 text-white" />
                </div>
                <div>
                  <p className="font-semibold text-gray-900">Dr. Vitality, MD</p>
                  <p className="text-sm text-gray-600">Chief Medical Officer</p>
                </div>
              </div>
              <p className="text-sm text-gray-700 mb-3">
                "I coordinate your entire care team to ensure comprehensive health insights."
              </p>
              <div className="space-y-2">
                <p className="text-sm font-medium text-gray-700">🏥 Your Specialist Network:</p>
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div className="bg-gray-50 rounded px-2 py-1">• Cardiology</div>
                  <div className="bg-gray-50 rounded px-2 py-1">• Endocrinology</div>
                  <div className="bg-gray-50 rounded px-2 py-1">• Laboratory Medicine</div>
                  <div className="bg-gray-50 rounded px-2 py-1">• Preventive Medicine</div>
                  <div className="bg-gray-50 rounded px-2 py-1">• Data Analysis</div>
                  <div className="bg-gray-50 rounded px-2 py-1">• Pharmacy</div>
                  <div className="bg-gray-50 rounded px-2 py-1">• Nutrition</div>
                </div>
              </div>
            </div>
          </div>

          <div className="space-y-3">
            <h3 className="text-lg font-semibold text-gray-800">🚀 Try These Example Questions:</h3>
            {exampleQuestions.map((question, index) => (
              <button
                key={index}
                onClick={() => handleQuestionClick(question.text)}
                onMouseEnter={() => setHoveredQuestion(index)}
                onMouseLeave={() => setHoveredQuestion(null)}
                className={`w-full text-left p-4 rounded-lg border transition-all duration-200 ${question.color} ${
                  hoveredQuestion === index ? 'scale-102 shadow-md' : ''
                }`}
              >
                <div className="flex items-start gap-3">
                  <question.icon className="w-5 h-5 mt-0.5 flex-shrink-0" />
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-900">
                      {hoveredQuestion === index ? question.text : question.shortText}
                    </p>
                    {hoveredQuestion === index && (
                      <p className="text-xs text-gray-500 mt-1 capitalize">
                        Complexity: {question.complexity}
                      </p>
                    )}
                  </div>
                </div>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Center Panel - Interactive CMO Introduction */}
      <div className="flex-1 flex flex-col bg-gray-50/50">
        <div className="bg-white/70 backdrop-blur-sm border-b border-gray-200 p-4">
          <div className="flex items-center justify-center gap-2">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
            <span className="text-sm font-medium text-gray-700">Medical Team Status: Ready</span>
          </div>
        </div>

        <div className="flex-1 flex items-center justify-center p-8">
          <div className="max-w-2xl text-center space-y-6">
            {/* CMO Avatar */}
            <div className="w-32 h-32 mx-auto bg-gradient-to-r from-blue-500 to-blue-600 rounded-full flex items-center justify-center shadow-lg animate-pulse-soft">
              <Brain className="w-16 h-16 text-white" />
            </div>

            {/* Introduction Text */}
            <div className="space-y-4">
              <p className="text-lg text-gray-800">
                Hello, I'm <span className="font-semibold">Dr. Vitality</span>, your Chief Medical Officer. 
                I lead a team of 8 medical specialists ready to analyze your health data.
              </p>

              <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200 text-left">
                <p className="font-medium text-gray-900 mb-3">Here's how we work:</p>
                <div className="space-y-2 text-sm text-gray-700">
                  <div>1️⃣ You ask a health question</div>
                  <div>2️⃣ I analyze and assemble the right specialists</div>
                  <div>3️⃣ My team investigates in parallel</div>
                  <div>4️⃣ We deliver comprehensive insights</div>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4 text-sm">
                <div className="bg-blue-50 rounded-lg p-3 border border-blue-200">
                  <p className="text-gray-700">✓ Analyze years of health records</p>
                </div>
                <div className="bg-blue-50 rounded-lg p-3 border border-blue-200">
                  <p className="text-gray-700">✓ Identify patterns and trends</p>
                </div>
                <div className="bg-blue-50 rounded-lg p-3 border border-blue-200">
                  <p className="text-gray-700">✓ Evidence-based recommendations</p>
                </div>
                <div className="bg-blue-50 rounded-lg p-3 border border-blue-200">
                  <p className="text-gray-700">✓ Create visual health insights</p>
                </div>
              </div>

              <p className="text-lg font-medium text-gray-900 mt-6">
                What health question can we help you with today?
              </p>

              {/* Input Form */}
              <form onSubmit={handleSubmit} className="max-w-lg mx-auto">
                <div className="relative">
                  <input
                    type="text"
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    placeholder="Ask about labs, medications, correlations, or health trends..."
                    className="w-full px-6 py-6 pr-20 text-lg border-2 border-gray-300 rounded-xl focus:border-blue-500 focus:ring-2 focus:ring-blue-100 transition-all"
                  />
                  <button
                    type="submit"
                    className="absolute right-4 top-1/2 -translate-y-1/2 p-3.5 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
                  >
                    <ChevronRight className="w-6 h-6" />
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      </div>

      {/* Right Panel - Live Team Showcase */}
      <div className="w-96 bg-white/60 backdrop-blur-sm p-6 overflow-y-auto border-l border-gray-200">
        <div className="space-y-6">
          <div>
            <h3 className="text-lg font-semibold text-gray-800 mb-4">🏥 Your Medical Team Architecture</h3>
            
            {/* Architecture Diagram */}
            <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
              {/* Top 3 Specialists */}
              <div className="grid grid-cols-3 gap-2 mb-4">
                {specialists.slice(1, 4).map((specialist, index) => (
                  <div
                    key={specialist.id}
                    className={`bg-gray-50 rounded-lg p-3 text-center transition-all duration-500 ${
                      animationPhase === index ? 'ring-2 ring-blue-400 shadow-md' : ''
                    }`}
                  >
                    <div className={`w-10 h-10 mx-auto mb-2 bg-gradient-to-r ${specialist.gradient} rounded-full flex items-center justify-center`}>
                      <specialist.icon className="w-5 h-5 text-white" />
                    </div>
                    <p className="text-xs font-medium text-gray-900">{specialist.specialty}</p>
                    <p className="text-xs text-gray-600">{specialist.name}</p>
                    <div className="mt-2">
                      <span className="inline-block px-2 py-0.5 bg-green-100 text-green-700 text-xs rounded-full">
                        Ready
                      </span>
                    </div>
                  </div>
                ))}
              </div>

              {/* Connection Lines from Top */}
              <div className="flex justify-center mb-4">
                <div className="text-gray-400">
                  <svg width="150" height="30" className="mx-auto">
                    <line x1="25" y1="0" x2="75" y2="30" stroke="currentColor" strokeDasharray="2,2" />
                    <line x1="75" y1="0" x2="75" y2="30" stroke="currentColor" strokeDasharray="2,2" />
                    <line x1="125" y1="0" x2="75" y2="30" stroke="currentColor" strokeDasharray="2,2" />
                  </svg>
                </div>
              </div>
              
              {/* CMO in the Middle */}
              <div className="text-center mb-4">
                <div className="inline-flex items-center gap-2 bg-blue-50 rounded-full px-6 py-3 shadow-md">
                  <Brain className="w-6 h-6 text-blue-600" />
                  <span className="font-medium text-gray-900">Dr. Vitality (CMO)</span>
                </div>
                <p className="text-xs text-gray-600 mt-2">Orchestrates & Delegates</p>
              </div>

              {/* Connection Lines to Bottom */}
              <div className="flex justify-center mb-4">
                <div className="text-gray-400">
                  <svg width="150" height="30" className="mx-auto">
                    <line x1="75" y1="0" x2="25" y2="30" stroke="currentColor" strokeDasharray="2,2" />
                    <line x1="75" y1="0" x2="75" y2="30" stroke="currentColor" strokeDasharray="2,2" />
                    <line x1="75" y1="0" x2="125" y2="30" stroke="currentColor" strokeDasharray="2,2" />
                  </svg>
                </div>
              </div>

              {/* Bottom 4 Specialists */}
              <div className="grid grid-cols-4 gap-2">
                {specialists.slice(4, 8).map((specialist, index) => (
                  <div
                    key={specialist.id}
                    className={`bg-gray-50 rounded-lg p-3 text-center transition-all duration-500 ${
                      animationPhase === (index + 3) % 7 ? 'ring-2 ring-blue-400 shadow-md' : ''
                    }`}
                  >
                    <div className={`w-10 h-10 mx-auto mb-2 bg-gradient-to-r ${specialist.gradient} rounded-full flex items-center justify-center`}>
                      <specialist.icon className="w-5 h-5 text-white" />
                    </div>
                    <p className="text-xs font-medium text-gray-900">{specialist.specialty}</p>
                    <p className="text-xs text-gray-600">{specialist.name}</p>
                    <div className="mt-2">
                      <span className="inline-block px-2 py-0.5 bg-green-100 text-green-700 text-xs rounded-full">
                        Ready
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="space-y-4">
            <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-200">
              <h4 className="font-medium text-gray-900 mb-3">🔬 Powered by:</h4>
              <ul className="space-y-2 text-sm text-gray-700">
                <li>• Anthropic Claude Opus 4</li>
                <li>• Snowflake Cortex AI</li>
                <li>• Multi-Agent Orchestration</li>
              </ul>
            </div>

            <div className="bg-blue-50 rounded-xl p-4 border border-blue-200">
              <p className="text-sm text-gray-700">
                <span className="font-medium">💡 Demo Tip:</span> Try complex questions to see multiple specialists collaborate!
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default WelcomeState;