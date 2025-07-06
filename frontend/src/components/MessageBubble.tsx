import React from 'react';
import { Message } from '@/types';
import { format } from 'date-fns';
import ReactMarkdown from 'react-markdown';
import { User, Bot } from 'lucide-react';
import ToolCallSection from './ToolCallSection';

interface MessageBubbleProps {
  message: Message;
}

const MessageBubble: React.FC<MessageBubbleProps> = ({ message }) => {
  const isUser = message.role === 'user';
  
  return (
    <div className={`flex gap-3 ${isUser ? 'justify-end' : 'justify-start'}`}>
      {!isUser && (
        <div className="flex-shrink-0 w-8 h-8 bg-primary-100 rounded-full flex items-center justify-center">
          <Bot className="w-5 h-5 text-primary-600" />
        </div>
      )}
      
      <div className={`max-w-3xl ${isUser ? 'order-1' : 'order-2'}`}>
        <div
          className={`chat-message ${
            isUser ? 'chat-message-user' : 'chat-message-assistant'
          }`}
        >
          {isUser ? (
            <p className="whitespace-pre-wrap">{message.content}</p>
          ) : (
            // Check if message contains tool call
            message.content.includes('🔧') ? (
              <ToolCallSection content={message.content} />
            ) : (
              <ReactMarkdown
                className="prose prose-sm max-w-none"
                components={{
                // Custom rendering for code blocks
                code: ({ node, inline, className, children, ...props }) => {
                  return inline ? (
                    <code className="px-1 py-0.5 bg-gray-100 rounded text-sm" {...props}>
                      {children}
                    </code>
                  ) : (
                    <pre className="bg-gray-100 p-3 rounded-lg overflow-x-auto">
                      <code className="text-sm" {...props}>
                        {children}
                      </code>
                    </pre>
                  );
                },
                // Custom rendering for tables
                table: ({ children }) => (
                  <div className="overflow-x-auto my-4">
                    <table className="min-w-full divide-y divide-gray-200">
                      {children}
                    </table>
                  </div>
                ),
                th: ({ children }) => (
                  <th className="px-3 py-2 bg-gray-50 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    {children}
                  </th>
                ),
                td: ({ children }) => (
                  <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-900">
                    {children}
                  </td>
                ),
                }}
              >
                {message.content}
              </ReactMarkdown>
            )
          )}
        </div>
        
        <div className={`mt-1 text-xs text-gray-500 ${isUser ? 'text-right' : 'text-left'}`}>
          {format(new Date(message.timestamp), 'HH:mm')}
        </div>
      </div>
      
      {isUser && (
        <div className="flex-shrink-0 w-8 h-8 bg-gray-300 rounded-full flex items-center justify-center order-2">
          <User className="w-5 h-5 text-gray-600" />
        </div>
      )}
    </div>
  );
};

export default MessageBubble;