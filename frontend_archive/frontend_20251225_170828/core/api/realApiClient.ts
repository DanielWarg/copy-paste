/**
 * Real API Client - NO MOCK DATA
 * 
 * This is the core API layer for real backend communication.
 * All requests go through proxy (https://localhost) with mTLS in prod_brutal.
 * 
 * Brutal-safe: No payloads in logs, only error codes + request_id
 */

import axios, { AxiosInstance, AxiosError } from 'axios';

// API Base URL
// In prod_brutal: https://localhost (proxy handles mTLS)
// In dev: http://localhost:8000 (direct backend)
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 
  (import.meta.env.PROD ? 'https://localhost' : 'http://localhost:8000');

// Generate request ID for correlation
function generateRequestId(): string {
  return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}

// Create axios instance with default config
const api: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor: Add X-Request-Id to all requests
api.interceptors.request.use((config) => {
  // Generate request ID if not already present
  if (!config.headers['X-Request-Id']) {
    config.headers['X-Request-Id'] = generateRequestId();
  }
  return config;
});

// Response interceptor: Extract X-Request-Id from response (for correlation)
api.interceptors.response.use(
  (response) => {
    // Response already contains X-Request-Id (backend echoes it)
    return response;
  },
  (error: AxiosError) => {
    // Brutal-safe error handling: no payloads in logs
    const errorCode = error.response?.status || 'network_error';
    const requestId = error.config?.headers['X-Request-Id'] || 'unknown';
    
    // Detect mTLS/TLS handshake failures
    const isTlsError = !error.response && (
      error.message?.includes('certificate') ||
      error.message?.includes('handshake') ||
      error.message?.includes('SSL') ||
      error.message?.includes('TLS') ||
      error.code === 'ECONNREFUSED' ||
      error.code === 'ERR_CERT_AUTHORITY_INVALID'
    );
    
    let errorMessage: string;
    if (isTlsError) {
      errorMessage = 'TLS handshake failed. Installera client certifikat för att fortsätta. Se: docs/MTLS_BROWSER_SETUP.md';
    } else {
      errorMessage = (error.response?.data as any)?.error?.message || 
                    (error.response?.data as any)?.detail || 
                    error.message || 
                    'Ett fel uppstod';
    }
    
    // Log only error code + request_id (brutal-safe)
    console.error('API Error:', errorCode, requestId);
    
    // Return structured error
    return Promise.reject({
      code: errorCode,
      message: errorMessage,
      request_id: requestId,
      isTlsError,
      originalError: error,
    });
  }
);

// Error type
export interface ApiError {
  code: string | number;
  message: string;
  request_id?: string;
  isTlsError?: boolean;
}

// Record Module API
export const recordApi = {
  /**
   * Create project and transcript shell
   */
  createRecord: async (title: string): Promise<{ project_id: number; transcript_id: number; title: string; created_at: string }> => {
    const response = await api.post('/api/v1/record/create', { title });
    return response.data;
  },

  /**
   * Upload audio file
   */
  uploadAudio: async (
    transcriptId: number,
    file: File,
    onProgress?: (progress: number) => void
  ): Promise<{ status: string; file_id: number; sha256: string; size_bytes: number; mime_type: string }> => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await api.post(
      `/api/v1/record/${transcriptId}/audio`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          if (progressEvent.total && onProgress) {
            const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            onProgress(percent);
          }
        },
      }
    );
    return response.data;
  },
};

// Transcript Module API
export const transcriptApi = {
  /**
   * Get transcript by ID
   */
  getTranscript: async (transcriptId: number, includeSegments: boolean = true): Promise<any> => {
    const response = await api.get(`/api/v1/transcripts/${transcriptId}`, {
      params: { include_segments: includeSegments },
    });
    return response.data;
  },

  /**
   * List transcripts
   */
  listTranscripts: async (limit: number = 200): Promise<{ items: any[]; total: number }> => {
    const response = await api.get('/api/v1/transcripts', {
      params: { limit },
    });
    return response.data;
  },
};

// Health check
export const healthApi = {
  checkHealth: async (): Promise<{ health: boolean; ready: boolean }> => {
    try {
      const healthRes = await api.get('/health');
      const readyRes = await api.get('/ready');
      return {
        health: healthRes.status === 200,
        ready: readyRes.status === 200,
      };
    } catch (error) {
      return { health: false, ready: false };
    }
  },
};

// Export API instance for direct use if needed
export { api };

// Export base URL for reference
export { API_BASE_URL };

