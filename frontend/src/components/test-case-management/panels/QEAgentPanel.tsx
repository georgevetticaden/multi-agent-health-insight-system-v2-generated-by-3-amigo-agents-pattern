import React, { useState, useEffect, useRef } from 'react';
import { Send, Loader2, Bot, User, Maximize2, Minimize2 } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { QEMessage, TestCase, EvaluationReport } from '../types';

interface QEAgentPanelProps {
  traceId: string;
  testCase: TestCase | null;
  onTestCaseUpdate: (updates: Partial<TestCase>) => void;
  onEvaluationStart: () => void;
  onEvaluationComplete: (report: EvaluationReport) => void;
}

const QEAgentPanel: React.FC<QEAgentPanelProps> = ({
  traceId,
  testCase,
  onTestCaseUpdate,
  onEvaluationStart,
  onEvaluationComplete
}) => {
  const [messages, setMessages] = useState<QEMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const eventSourceRef = useRef<EventSource | null>(null);
  const [isFullscreen, setIsFullscreen] = useState(false);

//   // Initial greeting
//   useEffect(() => {
//     setMessages([{
//       id: '1',
//       role: 'assistant',
//       content: `Hello! I'm the QE (Quality Engineering) Agent. I'm here to help you create and refine test cases for the health query you just executed.

// I've analyzed the trace and created an initial test case based on what actually happened. You can see it in the right panel.

// Here's how I can help:
// - Review the trace with you to identify areas for improvement
// - Update test case expectations based on your insights
// - Run evaluations to measure agent performance
// - Suggest improvements based on evaluation results

// Feel free to share your observations about the trace, and I'll help update the test case accordingly. When you're ready to evaluate, just type "run".`,
//       timestamp: new Date()
//     }]);
//   }, []);


  // Initial greeting
  useEffect(() => {
    setMessages([{
      id: '1',
      role: 'assistant',
      content: `**👋 Hi! I'm your Eval Development Assistant (EDA)**

I transform execution traces into powerful test cases and insightful evaluation reports that help you improve your agents.

**✨ What I've Done So Far:**
• 🔍 **Analyzed** your health query trace
• 📝 **Created** an initial test case (see right panel)
• ⚠️ **Note:** Expected values currently match actual results—let's fix that together!

**🚀 Let's Work Through the Analyze → Measure → Improve Workflow:**

**1. 🔍 Analyze** - Share what went wrong:
   • Misclassified complexity level?
   • Missing or incorrect specialists?
   • Wrong task assignments?
   • Other unexpected behaviors?

**2. 📏 Measure** - I'll update the test case:
   • Adjust expected values based on your insights
   • Define correct specialist requirements
   • Set proper complexity expectations

**3. 📊 Evaluate** - Run the evaluation:
   • Click the **⋯ menu** in Test Case panel
   • Select **"Run Evaluation"**
   • Get detailed scoring across 5 dimensions

**4. 💡 Improve** - Review results:
   • See exactly where your agent failed
   • Get LLM-as-Judge recommendations
   • Iterate and refine your approach

**💬 What issues do you see in this trace?**`,
    timestamp: new Date()
  }]);
}, []);


  // Scroll to bottom when messages change
  useEffect(() => {
    if (scrollContainerRef.current) {
      // Use scrollTop instead of scrollIntoView to avoid affecting parent containers
      const scrollContainer = scrollContainerRef.current;
      scrollContainer.scrollTop = scrollContainer.scrollHeight;
    }
  }, [messages]);

  const connectToQEAgent = async (message: string) => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    // Sync test case state before sending message
    if (testCase) {
      try {
        await fetch(`/api/qe/sync-test-case/${traceId}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(testCase)
        });
      } catch (error) {
        console.error('Failed to sync test case:', error);
      }
    }

    // Build URL with proper query parameters matching the backend API
    const url = `/api/qe/chat/stream?trace_id=${encodeURIComponent(traceId)}&message=${encodeURIComponent(message)}`;
    const eventSource = new EventSource(url);
    eventSourceRef.current = eventSource;

    let currentMessageId: string | null = null;
    let accumulatedContent = '';

    eventSource.onopen = () => {
      setIsConnected(true);
      console.log('Connected to QE Agent');
    };

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        switch (data.type) {
          case 'thinking':
            // Start a new message for thinking events
            currentMessageId = Date.now().toString();
            accumulatedContent = data.content || '';
            setMessages(prev => [...prev, {
              id: currentMessageId!,
              role: 'assistant',
              content: accumulatedContent,
              timestamp: new Date()
            }]);
            break;

          case 'text':
            // Handle streaming text
            if (!currentMessageId) {
              currentMessageId = Date.now().toString();
              accumulatedContent = '';
            }
            
            if (data.content) {
              accumulatedContent += data.content;
              setMessages(prev => {
                const existing = prev.find(m => m.id === currentMessageId);
                if (existing) {
                  return prev.map(m => 
                    m.id === currentMessageId 
                      ? { ...m, content: accumulatedContent }
                      : m
                  );
                } else {
                  return [...prev, {
                    id: currentMessageId!,
                    role: 'assistant',
                    content: accumulatedContent,
                    timestamp: new Date()
                  }];
                }
              });
            }
            break;

          case 'tool_result':
            // Handle test case code display
            if (data.content) {
              setMessages(prev => [...prev, {
                id: Date.now().toString(),
                role: 'assistant',
                content: `\`\`\`python\n${data.content}\n\`\`\``,
                timestamp: new Date()
              }]);
            }
            break;

          case 'test_case':
            // Handle legacy test case updates (Python format)
            if (data.content) {
              setMessages(prev => [...prev, {
                id: Date.now().toString(),
                role: 'assistant',
                content: `Test case created:\n\`\`\`python\n${data.content}\n\`\`\``,
                timestamp: new Date()
              }]);
            }
            break;

          case 'test_case_update':
            // Handle JSON test case updates
            if (data.content && onTestCaseUpdate) {
              // Update the test case in the parent component
              onTestCaseUpdate(data.content);
              // Don't show the JSON to the user
            }
            break;

          case 'action_menu':
            // Add action menu as a separate message
            if (data.content) {
              setMessages(prev => [...prev, {
                id: Date.now().toString(),
                role: 'assistant',
                content: data.content,
                timestamp: new Date()
              }]);
            }
            break;

          case 'start_evaluation':
            onEvaluationStart();
            break;

          case 'report_link':
            // Handle report links
            if (data.url && data.text) {
              setMessages(prev => [...prev, {
                id: Date.now().toString(),
                role: 'assistant',
                content: `[${data.text}](${data.url})`,
                timestamp: new Date()
              }]);
            }
            break;

          case 'error':
            console.error('QE Agent error:', data.content || data.error);
            setMessages(prev => [...prev, {
              id: Date.now().toString(),
              role: 'assistant',
              content: `Error: ${data.content || data.error}`,
              timestamp: new Date()
            }]);
            break;

          case 'done':
            setIsLoading(false);
            currentMessageId = null;
            accumulatedContent = '';
            break;

          default:
            console.log('Unknown event type:', data.type, data);
        }
      } catch (error) {
        console.error('Error parsing SSE data:', error);
      }
    };

    eventSource.onerror = (error) => {
      console.error('EventSource error:', error);
      setIsConnected(false);
      setIsLoading(false);
      eventSource.close();
    };
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputValue.trim() || isLoading) return;

    const userMessage: QEMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: inputValue,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    // Check if user wants to run evaluation
    if (inputValue.trim().toLowerCase() === 'run' && testCase) {
      // Show loading message
      setMessages(prev => [...prev, {
        id: Date.now().toString() + '-loading',
        role: 'assistant',
        content: 'Starting evaluation... This may take a moment.',
        timestamp: new Date()
      }]);

      try {
        onEvaluationStart();
        
        const response = await fetch(`/api/test-cases/${testCase.id}/evaluate`, {
          method: 'POST'
        });

        if (!response.ok) {
          throw new Error('Evaluation failed');
        }

        const result = await response.json();
        
        // Load the full evaluation report
        const reportResponse = await fetch(result.report_url);
        const reportData = await reportResponse.json();
        
        onEvaluationComplete({
          test_case_id: testCase.id,
          evaluation_id: result.evaluation_id,
          overall_score: result.overall_score,
          report_url: result.report_url,
          ...reportData
        });

        setMessages(prev => [...prev, {
          id: Date.now().toString(),
          role: 'assistant',
          content: `Evaluation complete! Overall score: ${(result.overall_score * 100).toFixed(1)}%\n\nCheck the right panel for detailed results.`,
          timestamp: new Date()
        }]);
      } catch (error) {
        console.error('Evaluation error:', error);
        setMessages(prev => [...prev, {
          id: Date.now().toString(),
          role: 'assistant',
          content: 'Error running evaluation. Please try again.',
          timestamp: new Date()
        }]);
      } finally {
        setIsLoading(false);
      }
    } else {
      // Regular conversation with QE Agent
      await connectToQEAgent(inputValue);
    }
  };

  const toggleFullscreen = () => {
    setIsFullscreen(!isFullscreen);
  };

  return (
    <div className={`h-full flex flex-col ${isFullscreen ? 'fixed inset-0 z-50 bg-white' : ''}`}>
      {/* Header */}
      <div className="px-4 py-3 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Bot className="w-5 h-5 text-blue-600" />
            <h2 className="font-semibold text-gray-900">Eval Development Assistant (EDA Agent)</h2>
            {isConnected && (
              <span className="ml-2 text-xs text-green-600 flex items-center gap-1">
                <span className="w-2 h-2 bg-green-600 rounded-full"></span>
                Connected
              </span>
            )}
          </div>
          <button
            onClick={toggleFullscreen}
            className="p-1.5 hover:bg-gray-100 rounded transition-colors"
            title={isFullscreen ? "Exit fullscreen" : "Enter fullscreen"}
          >
            {isFullscreen ? (
              <Minimize2 className="w-4 h-4 text-gray-600" />
            ) : (
              <Maximize2 className="w-4 h-4 text-gray-600" />
            )}
          </button>
        </div>
      </div>

      {/* Messages */}
      <div ref={scrollContainerRef} className="flex-1 overflow-y-scroll p-4 space-y-4" style={{ overscrollBehavior: 'contain' }}>
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex gap-3 ${message.role === 'user' ? 'justify-end' : ''}`}
          >
            {message.role === 'assistant' && (
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                  <Bot className="w-5 h-5 text-blue-600" />
                </div>
              </div>
            )}
            
            <div
              className={`max-w-[80%] rounded-lg px-4 py-2 ${
                message.role === 'user'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-900'
              }`}
            >
              {message.role === 'user' ? (
                <p className="whitespace-pre-wrap text-sm">{message.content}</p>
              ) : (
                <ReactMarkdown 
                  className="prose prose-sm max-w-none prose-headings:text-gray-900 prose-p:text-gray-700 prose-strong:text-gray-900 prose-ul:text-gray-700 prose-li:text-gray-700"
                  components={{
                    // Custom rendering for inline code
                    code: ({ node, inline, className, children, ...props }) => {
                      return inline ? (
                        <code className="px-1 py-0.5 bg-gray-200 rounded text-xs" {...props}>
                          {children}
                        </code>
                      ) : (
                        <pre className="bg-gray-200 p-3 rounded-lg overflow-x-auto my-2">
                          <code className="text-xs" {...props}>
                            {children}
                          </code>
                        </pre>
                      );
                    },
                    // Custom rendering for paragraphs to handle spacing
                    p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
                    // Custom rendering for lists
                    ul: ({ children }) => <ul className="list-disc pl-4 mb-2">{children}</ul>,
                    ol: ({ children }) => <ol className="list-decimal pl-4 mb-2">{children}</ol>,
                    li: ({ children }) => <li className="mb-1">{children}</li>,
                    // Custom rendering for headings
                    h1: ({ children }) => <h1 className="text-lg font-bold mb-2">{children}</h1>,
                    h2: ({ children }) => <h2 className="text-base font-bold mb-2">{children}</h2>,
                    h3: ({ children }) => <h3 className="text-sm font-bold mb-1">{children}</h3>,
                  }}
                >
                  {message.content}
                </ReactMarkdown>
              )}
              <div
                className={`text-xs mt-1 ${
                  message.role === 'user' ? 'text-blue-200' : 'text-gray-500'
                }`}
              >
                {message.timestamp.toLocaleTimeString()}
              </div>
            </div>

            {message.role === 'user' && (
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-gray-300 rounded-full flex items-center justify-center">
                  <User className="w-5 h-5 text-gray-700" />
                </div>
              </div>
            )}
          </div>
        ))}
        
        {isLoading && (
          <div className="flex gap-3">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                <Bot className="w-5 h-5 text-blue-600" />
              </div>
            </div>
            <div className="bg-gray-100 rounded-lg px-4 py-2">
              <Loader2 className="w-4 h-4 animate-spin text-gray-600" />
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="p-4 border-t border-gray-200">
        <div className="flex gap-2">
          <textarea
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onPaste={(e) => {
              // Preserve line breaks when pasting
              e.preventDefault();
              const text = e.clipboardData.getData('text');
              setInputValue(text);
            }}
            placeholder='Share observations or type "run" to evaluate... (Ctrl+Enter to send)'
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
            rows={3}
            disabled={isLoading}
            onKeyDown={(e) => {
              // Allow Ctrl/Cmd+Enter to submit
              if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
                e.preventDefault();
                handleSubmit(e);
              }
            }}
          />
          <button
            type="submit"
            disabled={isLoading || !inputValue.trim()}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isLoading ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <Send className="w-5 h-5" />
            )}
          </button>
        </div>
      </form>
    </div>
  );
};

export default QEAgentPanel;