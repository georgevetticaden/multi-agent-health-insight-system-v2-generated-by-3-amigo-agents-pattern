import React, { useState, useRef, useEffect } from 'react';
import { Send, Loader2, Upload, AlertCircle } from 'lucide-react';
import { v4 as uuidv4 } from 'uuid';
import { Message, StreamChunk, Visualization } from '@/types';
import { chatService } from '@/services/api';
import MessageBubble from './MessageBubble';
import VisualizationCard from './VisualizationCard';
import ToolCallEnvelope from './ToolCallEnvelope';
import { SSEEventParser } from '../services/sseEventParser';
import { AppState, TeamUpdate } from '../types/medical-team';

interface ChatInterfaceProps {
  conversationId?: string | null;
  onArtifact?: (artifact: any) => void;
  onCodeStreamStart?: () => void;
  onAppStateChange?: (state: AppState) => void;
  onTeamUpdate?: (update: TeamUpdate) => void;
  onStreamingContent?: (content: string) => void;
  onMessageSend?: (message: string) => void;
  appState?: AppState;
  scrollToQuery?: string;
}

const ChatInterface = React.forwardRef<any, ChatInterfaceProps>(({ 
  conversationId: initialConversationId, 
  onArtifact, 
  onCodeStreamStart,
  onAppStateChange,
  onTeamUpdate,
  onStreamingContent,
  onMessageSend,
  appState,
  scrollToQuery
}, ref) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [conversationId] = useState(initialConversationId || uuidv4());
  const [visualizations, setVisualizations] = useState<Map<string, Visualization>>(new Map());
  const [error, setError] = useState<string | null>(null);
  const [lastToolResult, setLastToolResult] = useState<any>(null);
  const [toolStatus, setToolStatus] = useState<string | null>(null);
  const [toolCalls, setToolCalls] = useState<Map<string, any>>(new Map());
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const eventSourceRef = useRef<EventSource | null>(null);
  const lastArtifactUpdateRef = useRef<number>(0);
  const sseParser = useRef(new SSEEventParser());
  const messageRefs = useRef<Map<string, HTMLDivElement>>(new Map());
  
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };
  
  useEffect(() => {
    scrollToBottom();
  }, [messages, visualizations]);
  
  // Scroll to specific query when scrollToQuery changes
  useEffect(() => {
    if (scrollToQuery) {
      // Find the message containing this query text
      const queryMessage = messages.find(msg => 
        msg.role === 'user' && msg.content === scrollToQuery
      );
      
      if (queryMessage && messageRefs.current.has(queryMessage.id)) {
        const element = messageRefs.current.get(queryMessage.id);
        element?.scrollIntoView({ behavior: 'smooth', block: 'center' });
        
        // Add a highlight effect
        element?.classList.add('highlight-message');
        setTimeout(() => {
          element?.classList.remove('highlight-message');
        }, 2000);
      }
    }
  }, [scrollToQuery, messages]);
  
  useEffect(() => {
    // Cleanup event source on unmount
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, []);
  
  const handleSendMessage = React.useCallback(async (messageOverride?: string) => {
    const messageToSend = messageOverride || input.trim();
    
    if (!messageToSend || isLoading) {
      console.log('Cannot send - no message or loading');
      return;
    }
    
    console.log('handleSendMessage called with:', messageToSend);
    
    const userMessage: Message = {
      id: uuidv4(),
      role: 'user',
      content: messageToSend,
      timestamp: new Date(),
    };
    
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);
    setError(null);
    setToolStatus(null);
    
    // Notify parent component
    if (onMessageSend) {
      onMessageSend(messageToSend);
    }
    
    // Reset SSE parser for new conversation
    sseParser.current.reset();
    
    // We'll create messages as they come in, not a placeholder
    let currentAssistantMessageId: string | null = null;
    
    try {
      // Close previous event source if exists
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
      
      // Create new event source
      const eventSource = chatService.sendMessage({
        message: userMessage.content,
        conversationId,
        enableExtendedThinking: true,
      });
      
      console.log('EventSource created:', eventSource);
      console.log('EventSource readyState:', eventSource.readyState);
      
      eventSourceRef.current = eventSource;
      let accumulatedContent = '';
      let isProcessingTool = false;
      let codeBlockBuffer = '';
      let isInCodeBlock = false;
      let codeBlockLanguage = '';
      let currentStreamingArtifactId: string | null = null;
      let hasCompletedCodeBlock = false; // Track if we've completed at least one code block
      
      let isDone = false;
      let currentData: any = null;
      let finalSynthesisMessageId: string | null = null; // Track the final synthesis message
      
      // Add open event listener
      eventSource.addEventListener('open', (event) => {
        console.log('EventSource opened:', event);
      });
      
      // Add a generic event listener to catch ALL events
      eventSource.onmessage = (event) => {
        console.log('Generic onmessage event:', event.type, event.data);
      };
      
      // Monitor connection state changes
      let connectionCheckInterval = setInterval(() => {
        console.log('EventSource readyState check:', eventSource.readyState);
        if (eventSource.readyState === EventSource.CLOSED) {
          console.log('EventSource connection closed unexpectedly');
          clearInterval(connectionCheckInterval);
        }
      }, 1000);
      
      // Function to extract code artifacts from content
      const extractCodeArtifact = (content: string) => {
        // Look for React component code blocks
        const codeBlockRegex = /```(?:jsx?|javascript|typescript|tsx?)\n([\s\S]*?)```/g;
        const matches = content.matchAll(codeBlockRegex);
        
        for (const match of matches) {
          const code = match[1].trim();
          // Check if it's a React component (contains JSX or return statement with JSX)
          if (code.includes('return (') || code.includes('<') || code.includes('LineChart') || code.includes('BarChart')) {
            if (onArtifact) {
              onArtifact({
                id: uuidv4(),
                code: code,
                language: 'javascript',
                data: lastToolResult || currentData,
                timestamp: new Date()
              });
            }
            // Remove the code block from the message content
            return content.replace(match[0], '\n*[Visualization rendered in side panel]*\n');
          }
        }
        return content;
      };
      
      eventSource.addEventListener('message', (event) => {
        console.log('Message event:', event.type, event.data);
        const chunk = JSON.parse(event.data) as StreamChunk;
        
        console.log('Parsed chunk:', chunk);
        
        // Parse SSE event for team updates
        const { appState: newState, teamUpdate, streamingContent } = sseParser.current.parseSSEEvent(chunk);
        
        if (newState && onAppStateChange) {
          console.log('[ChatInterface] App state change:', newState);
          onAppStateChange(newState as AppState);
        }
        
        if (teamUpdate && onTeamUpdate) {
          console.log('[ChatInterface] Team update:', teamUpdate);
          onTeamUpdate(teamUpdate);
        }
        
        if (streamingContent && onStreamingContent) {
          console.log('[ChatInterface] Streaming content:', streamingContent.substring(0, 50) + '...');
          onStreamingContent(streamingContent);
        }
        
        switch (chunk.type) {
          case 'text':
            console.log('Text chunk received:', chunk.content);
            if (chunk.content !== undefined) {  // Allow empty strings
              // For thinking messages, we've already created the message bubble
              // For the final synthesis text, we need to handle it differently
              // Check for code block markers
              const codeBlockStartRegex = /```(jsx?|javascript|typescript|tsx?)?/;
              const codeBlockEndRegex = /```/;
              
              let remainingContent = chunk.content;
              let processedContent = '';
              
              while (remainingContent.length > 0) {
                if (!isInCodeBlock) {
                  // Look for code block start
                  const startMatch = remainingContent.match(codeBlockStartRegex);
                  if (startMatch) {
                    const beforeCode = remainingContent.substring(0, startMatch.index);
                    processedContent += beforeCode;
                    
                    // Start code block
                    isInCodeBlock = true;
                    codeBlockLanguage = startMatch[1] || 'javascript';
                    codeBlockBuffer = '';
                    
                    // Create a new streaming artifact only if we don't have one for this message
                    if (!currentStreamingArtifactId || hasCompletedCodeBlock) {
                      currentStreamingArtifactId = uuidv4();
                      hasCompletedCodeBlock = false;
                    }
                    lastArtifactUpdateRef.current = Date.now(); // Reset throttle timer
                    if (onArtifact) {
                      onArtifact({
                        id: currentStreamingArtifactId,
                        code: '// Code streaming...\n',
                        language: codeBlockLanguage,
                        data: currentData || lastToolResult,
                        timestamp: new Date(),
                        isStreaming: true
                      });
                    }
                    
                    // Notify parent that code streaming started
                    if (onCodeStreamStart) {
                      onCodeStreamStart();
                    }
                    
                    // Skip the code block marker
                    remainingContent = remainingContent.substring(startMatch.index + startMatch[0].length);
                  } else {
                    // No code block start, add all content
                    processedContent += remainingContent;
                    remainingContent = '';
                  }
                } else {
                  // We're in a code block, look for the end
                  const endMatch = remainingContent.match(codeBlockEndRegex);
                  if (endMatch && endMatch.index !== undefined) {
                    // Found end of code block
                    const codeContent = remainingContent.substring(0, endMatch.index);
                    codeBlockBuffer += codeContent;
                    
                    // Send complete code block to artifact panel
                    if (codeBlockBuffer.includes('return (') || codeBlockBuffer.includes('<') || 
                        codeBlockBuffer.includes('LineChart') || codeBlockBuffer.includes('BarChart')) {
                      if (onArtifact && currentStreamingArtifactId) {
                        // Finalize the streaming artifact
                        onArtifact({
                          id: currentStreamingArtifactId,
                          code: codeBlockBuffer,
                          language: codeBlockLanguage,
                          data: currentData || lastToolResult,
                          timestamp: new Date(),
                          isStreaming: false // Mark as complete
                        });
                        hasCompletedCodeBlock = true; // Mark that we've completed a code block
                      }
                      // Add placeholder text instead of code
                      processedContent += '\n*[Visualization rendered in side panel]*\n';
                    } else {
                      // Not a React component, keep in main content
                      processedContent += '```' + codeBlockLanguage + '\n' + codeBlockBuffer + '```';
                    }
                    
                    // Reset code block state
                    isInCodeBlock = false;
                    codeBlockBuffer = '';
                    codeBlockLanguage = '';
                    // Don't reset currentStreamingArtifactId here - keep it for potential future blocks in same message
                    
                    // Skip the end marker
                    remainingContent = remainingContent.substring(endMatch.index + endMatch[0].length);
                  } else {
                    // Still in code block, buffer the content and update streaming artifact
                    codeBlockBuffer += remainingContent;
                    
                    // Update the streaming artifact in real-time with throttling
                    if (currentStreamingArtifactId && onArtifact) {
                      const now = Date.now();
                      const timeSinceLastUpdate = now - lastArtifactUpdateRef.current;
                      
                      // Throttle updates to max once per 100ms, or on newlines, or every 100 chars
                      if (timeSinceLastUpdate > 100 || 
                          remainingContent.endsWith('\n') || 
                          codeBlockBuffer.length % 100 === 0) {
                        lastArtifactUpdateRef.current = now;
                        onArtifact({
                          id: currentStreamingArtifactId,
                          code: codeBlockBuffer,
                          language: codeBlockLanguage,
                          data: currentData || lastToolResult,
                          timestamp: new Date(),
                          isStreaming: true
                        });
                      }
                    }
                    
                    remainingContent = '';
                  }
                }
              }
              
              // Update accumulated content with processed content
              accumulatedContent += processedContent;
              
              // Check if we need to create or update the final synthesis message
              if (!finalSynthesisMessageId && processedContent.trim()) {
                // This is the start of the final synthesis - create a new message
                finalSynthesisMessageId = uuidv4();
                const synthesisMessage: Message = {
                  id: finalSynthesisMessageId,
                  role: 'assistant',
                  content: processedContent,
                  timestamp: new Date(),
                };
                setMessages(prev => [...prev, synthesisMessage]);
              } else if (finalSynthesisMessageId) {
                // Update existing synthesis message
                setMessages(prev => {
                  const updated = prev.map(msg => 
                    msg.id === finalSynthesisMessageId 
                      ? { ...msg, content: accumulatedContent }
                      : msg
                  );
                  return updated;
                });
              }
            }
            break;
            
          case 'tool_result':
            // Store tool result data for visualization
            if (chunk.data) {
              currentData = chunk.data;
              setLastToolResult(chunk.data);
              console.log('Received tool result data:', currentData);
              
              // Update the last tool call with result
              const toolCallsForResult = Array.from(toolCalls.entries());
              const lastToolForResult = toolCallsForResult[toolCallsForResult.length - 1];
              if (lastToolForResult) {
                const [id, call] = lastToolForResult;
                setToolCalls(prev => {
                  const updated = new Map(prev);
                  updated.set(id, { ...call, status: 'completed', toolResult: chunk.data });
                  return updated;
                });
                
                // Update the tool message
                setMessages(prev => prev.map(msg => {
                  if (msg.role === 'tool' && JSON.parse(msg.content).id === id) {
                    return {
                      ...msg,
                      content: JSON.stringify({ ...call, status: 'completed', toolResult: chunk.data })
                    };
                  }
                  return msg;
                }));
              }
            }
            break;
            
          case 'thinking':
            // Create a new message bubble for each thinking update
            if (chunk.content) {
              const thinkingMessageId = uuidv4();
              const thinkingMessage: Message = {
                id: thinkingMessageId,
                role: 'assistant',
                content: chunk.content,
                timestamp: new Date(),
              };
              
              // Check if this is the first message or if we should create a new bubble
              setMessages(prev => {
                // Just add the thinking message
                return [...prev, thinkingMessage];
              });
            }
            break;
            
          case 'tool_call':
            // Tool calls are now handled within thinking messages in V3
            console.log('Tool call:', chunk.data);
            setToolStatus(null);
            break;
            
          case 'tool_executing':
            // Log tool execution with parameters
            console.log('Tool executing:', chunk.data);
            
            // Tool information is now in thinking messages from V3
            // We don't need separate tool envelopes
            setToolStatus(null);
            break;
            
          case 'visualization':
            // Skip visualization events - we're handling visualizations through code artifacts
            break;
            
          case 'done':
            console.log('🔍 [TRACE DEBUGGING] Done event in message handler:', chunk);
            console.log('🔍 [TRACE DEBUGGING] Final accumulated content in done:', accumulatedContent);
            console.log('🔍 [TRACE DEBUGGING] chunk.trace_id:', chunk.trace_id);
            console.log('🔍 [TRACE DEBUGGING] onTeamUpdate exists:', !!onTeamUpdate);
            
            // Handle done event with trace_id
            if (chunk.trace_id && onTeamUpdate) {
              console.log('🔍 [TRACE DEBUGGING] Passing trace_id to team update:', chunk.trace_id);
              const updatePayload = {
                teamStatus: 'complete',
                members: [],
                overallProgress: 100,
                traceId: chunk.trace_id
              };
              console.log('🔍 [TRACE DEBUGGING] Team update payload:', updatePayload);
              onTeamUpdate(updatePayload);
            } else {
              console.log('🔍 [TRACE DEBUGGING] NOT passing trace_id - chunk.trace_id:', chunk.trace_id, 'onTeamUpdate:', !!onTeamUpdate);
            }
            
            // Set done state and cleanup
            isDone = true;
            setIsLoading(false);
            setToolStatus(null);
            
            // Close event source
            clearInterval(connectionCheckInterval);
            eventSource.close();
            if (eventSourceRef.current) {
              eventSourceRef.current = null;
            }
            break;
            
          case 'error':
            setError(chunk.content || 'An error occurred');
            break;
            
          case 'viz_start':
            console.log('Visualization start event received');
            // Start a new code block for visualization
            isInCodeBlock = true;
            codeBlockLanguage = 'javascript';
            codeBlockBuffer = '';
            
            // Create a new streaming artifact
            currentStreamingArtifactId = uuidv4();
            hasCompletedCodeBlock = false;
            lastArtifactUpdateRef.current = Date.now();
            
            if (onArtifact) {
              onArtifact({
                id: currentStreamingArtifactId,
                code: '// Visualization loading...\n',
                language: 'javascript',
                data: currentData || lastToolResult,
                timestamp: new Date(),
                isStreaming: true
              });
            }
            
            // Notify parent that code streaming started
            if (onCodeStreamStart) {
              onCodeStreamStart();
            }
            break;
            
          case 'viz_code':
            console.log('Visualization code chunk received:', chunk.content?.substring(0, 50));
            if (chunk.content && isInCodeBlock) {
              codeBlockBuffer += chunk.content;
              
              // Throttle updates to avoid too many re-renders
              const now = Date.now();
              if (now - lastArtifactUpdateRef.current > 100) {
                if (onArtifact && currentStreamingArtifactId) {
                  onArtifact({
                    id: currentStreamingArtifactId,
                    code: codeBlockBuffer,
                    language: codeBlockLanguage,
                    data: currentData || lastToolResult,
                    timestamp: new Date(),
                    isStreaming: true
                  });
                }
                lastArtifactUpdateRef.current = now;
              }
            }
            break;
            
          case 'viz_complete':
            console.log('Visualization complete event received');
            if (isInCodeBlock && codeBlockBuffer && currentStreamingArtifactId) {
              // Finalize the visualization artifact
              if (onArtifact) {
                onArtifact({
                  id: currentStreamingArtifactId,
                  code: chunk.code || codeBlockBuffer,
                  language: 'javascript',
                  data: currentData || lastToolResult,
                  timestamp: new Date(),
                  isStreaming: false
                });
              }
              
              // Add placeholder text to the message
              accumulatedContent += '\n\n📊 [Visualization created - see the visualization tab]';
              
              // Update the current message
              setMessages(prev => {
                const lastIdx = prev.length - 1;
                if (lastIdx >= 0 && prev[lastIdx].role === 'assistant') {
                  const updated = [...prev];
                  updated[lastIdx] = {
                    ...updated[lastIdx],
                    content: accumulatedContent
                  };
                  return updated;
                }
                return prev;
              });
              
              // Reset code block state
              isInCodeBlock = false;
              codeBlockBuffer = '';
              hasCompletedCodeBlock = true;
            }
            break;
            
          // Removed duplicate 'done' case - handled above
        }
      });
      
      // Add listener for done event
      eventSource.addEventListener('done', (event) => {
        console.log('Done event received:', event);
        
        // Parse the done event data to extract trace_id
        try {
          const doneData = JSON.parse(event.data);
          if (doneData.trace_id) {
            console.log('Trace ID received:', doneData.trace_id);
            // Pass trace_id to parent through a new callback
            if (onTeamUpdate) {
              onTeamUpdate({
                teamStatus: 'complete',
                members: [],
                overallProgress: 100,
                traceId: doneData.trace_id
              });
            }
          }
        } catch (e) {
          console.error('Error parsing done event data:', e);
        }
        
        isDone = true;
        setIsLoading(false);
        setToolStatus(null);
        eventSource.close();
        if (eventSourceRef.current) {
          eventSourceRef.current = null;
        }
      });
      
      // Add listener for error event  
      eventSource.addEventListener('error', (event) => {
        console.log('Error event received:', event);
        const data = JSON.parse(event.data);
        setError(data.error || 'An error occurred');
      });
      
      eventSource.onerror = (error) => {
        console.log('SSE error, isDone:', isDone, 'readyState:', eventSource.readyState);
        console.log('Final accumulated content length:', accumulatedContent.length);
        console.log('Final accumulated content:', accumulatedContent);
        
        // Only show error if not done and connection wasn't closed intentionally
        if (!isDone && eventSource.readyState !== EventSource.CLOSED) {
          console.error('SSE error:', error);
          
          // Check if it's an overloaded error
          if (error.data && error.data.includes('overloaded')) {
            setError('The AI service is temporarily busy. Please wait a moment and try again.');
            // Add a message to the chat about the overload
            setMessages(prev => [...prev, {
              id: Date.now().toString(),
              role: 'assistant',
              content: 'I apologize, but the AI service is currently experiencing high demand. Please wait a moment and try your query again. The system automatically retries requests, but if the issue persists, please try again in a few seconds.',
              timestamp: new Date()
            }]);
          } else {
            setError('Connection error. Please try again.');
          }
        }
        setIsLoading(false);
        setToolStatus(null);
        clearInterval(connectionCheckInterval);
        if (eventSource.readyState !== EventSource.CLOSED) {
          eventSource.close();
        }
        if (eventSourceRef.current) {
          eventSourceRef.current = null;
        }
      };
      
    } catch (err) {
      setError('Failed to send message. Please try again.');
      setIsLoading(false);
      console.error('Chat error:', err);
    }
  }, [input, isLoading, conversationId, onMessageSend, onAppStateChange, onTeamUpdate, onArtifact, onCodeStreamStart]);
  
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };
  
  // Helper functions for input state
  const getInputPlaceholder = () => {
    switch (appState) {
      case 'cmo-analyzing':
        return 'CMO is analyzing your query...';
      case 'team-assembling':
        return 'Medical team is being assembled...';
      case 'team-working':
        return 'Specialists are analyzing your health data...';
      case 'synthesizing':
        return 'CMO is synthesizing findings...';
      case 'visualizing':
        return 'Creating visualizations...';
      default:
        return 'Ask about your health data...';
    }
  };

  const isInputDisabled = appState && [
    'cmo-analyzing',
    'team-assembling', 
    'team-working',
    'synthesizing',
    'visualizing'
  ].includes(appState);
  // This content has been moved to after the useImperativeHandle
  // See the previous edit

  // Expose methods via ref
  React.useImperativeHandle(ref, () => ({
    sendMessage: (message: string) => {
      console.log('sendMessage called with:', message);
      
      // Set the input value for visual feedback
      setInput(message);
      
      // Call handleSendMessage directly with the message
      // Use a small delay to ensure the UI updates
      setTimeout(() => {
        console.log('Calling handleSendMessage with override:', message);
        handleSendMessage(message);
      }, 100);
    }
  }), [handleSendMessage]);

  return (
    <div className="flex flex-col h-full">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center py-12">
            <p className="text-gray-500 mb-4">Welcome! I'm your Health Analyst Assistant.</p>
            <p className="text-gray-400 text-sm">
              I can help you analyze your health data and answer questions about your medical history.
            </p>
          </div>
        )}
        
        {messages.map((message) => (
          <div 
            key={message.id}
            ref={(el) => {
              if (el) messageRefs.current.set(message.id, el);
            }}
          >
            <MessageBubble message={message} />
          </div>
        ))}
        
        {error && (
          <div className="flex items-center gap-2 text-red-600 bg-red-50 p-3 rounded-lg">
            <AlertCircle className="w-5 h-5" />
            <span className="text-sm">{error}</span>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>
      
      {/* Input */}
      <div className="bg-white/80 backdrop-blur-sm border-t border-gray-200 px-6 py-4">
        <div className="flex items-center gap-3">
          <button
            className="p-2.5 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
            title="Upload health records"
          >
            <Upload className="w-5 h-5" />
          </button>
          
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder={getInputPlaceholder()}
            className="flex-1 px-4 py-2.5 bg-gray-50 border border-gray-300 rounded-lg placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            disabled={isLoading || isInputDisabled}
          />
          
          <button
            onClick={() => handleSendMessage()}
            disabled={!input.trim() || isLoading || isInputDisabled}
            className="px-4 py-2.5 bg-blue-500 hover:bg-blue-600 text-white rounded-lg font-medium disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
          >
            {isLoading ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <>
                <Send className="w-5 h-5" />
                <span>Send</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
});

ChatInterface.displayName = 'ChatInterface';

export default ChatInterface;