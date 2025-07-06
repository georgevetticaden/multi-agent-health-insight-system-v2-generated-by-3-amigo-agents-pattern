import axios from 'axios';
import { ChatRequest, ImportRequest, ImportResponse, QueryRequest, QueryResponse } from '@/types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Chat service with SSE support
export const chatService = {
  sendMessage: (request: ChatRequest) => {
    const eventSource = new EventSource(
      `${API_BASE_URL}/api/chat/message?${new URLSearchParams({
        message: request.message,
        conversationId: request.conversationId || '',
        enableExtendedThinking: String(request.enableExtendedThinking || false),
      })}`
    );
    
    return eventSource;
  },
  
  getHistory: async (conversationId: string) => {
    const response = await api.get(`/api/chat/history/${conversationId}`);
    return response.data;
  },
  
  clearConversation: async (conversationId: string) => {
    const response = await api.post(`/api/chat/clear/${conversationId}`);
    return response.data;
  },
};

// Health data service
export const healthService = {
  importData: async (request: ImportRequest): Promise<ImportResponse> => {
    const response = await api.post('/api/health/import', request);
    return response.data;
  },
  
  queryData: async (request: QueryRequest): Promise<QueryResponse> => {
    const response = await api.post('/api/health/query', request);
    return response.data;
  },
  
  uploadFiles: async (files: File[]) => {
    const formData = new FormData();
    files.forEach(file => {
      formData.append('files', file);
    });
    
    const response = await api.post('/api/health/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },
};

// System service
export const systemService = {
  healthCheck: async () => {
    const response = await api.get('/health');
    return response.data;
  },
};

export default api;