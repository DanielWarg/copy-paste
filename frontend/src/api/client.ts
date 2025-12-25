/**
 * API Client - REAL WIRED (NO MOCK)
 * 
 * Centralized API client with:
 * - Request correlation (X-Request-Id)
 * - mTLS error detection
 * - Typed error mapping
 * - Form-data support
 */

import { generateRequestId } from '../utils/requestId';

// API Base URL
// Default: http://localhost:8000 (direct backend in dev)
// Prod: https://localhost (proxy for prod_brutal)
// Can be overridden with VITE_API_BASE_URL
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export interface ApiError {
  code: string | number;
  message: string;
  request_id?: string;
  isTlsError?: boolean;
  originalError?: Error;
}

export type ErrorCode = 
  | 'mtls_handshake_failed'
  | 'forbidden'
  | 'pii_blocked'
  | 'server_error'
  | 'network_error'
  | 'validation_error'
  | 'not_found'
  | 'db_uninitialized'
  | 'db_down'
  | 'unknown';

interface RequestOptions extends Omit<RequestInit, 'body'> {
  body?: BodyInit | Record<string, any>;
}

/**
 * Map HTTP status codes and network errors to error codes
 */
function mapErrorToCode(status: number | undefined, error: Error | null): ErrorCode {
  if (!status) {
    // Network error - likely mTLS handshake failure
    if (error?.message?.includes('certificate') || 
        error?.message?.includes('handshake') ||
        error?.message?.includes('SSL') ||
        error?.message?.includes('TLS')) {
      return 'mtls_handshake_failed';
    }
    return 'network_error';
  }

  switch (status) {
    case 401:
    case 403:
      return 'forbidden';
    case 422:
      return 'pii_blocked'; // Privacy Gate blocked
    case 404:
      return 'not_found';
    case 400:
      return 'validation_error';
    case 503:
      // Will be checked in response data for DB errors
      return 'server_error';
    case 500:
    case 502:
    case 504:
      return 'server_error';
    default:
      return 'unknown';
  }
}

/**
 * Get user-friendly error message based on error code
 */
function getErrorMessage(code: ErrorCode, responseData?: any): string {
  switch (code) {
    case 'mtls_handshake_failed':
      return 'Klientcertifikat krävs. Installera ditt mTLS-certifikat i webbläsaren. Se: docs/MTLS_BROWSER_SETUP.md';
    case 'forbidden':
      return 'Åtkomst nekad. Kontrollera dina behörigheter.';
    case 'pii_blocked':
      return 'Personuppgifter detekterades. Data måste anonymiseras innan bearbetning.';
    case 'db_uninitialized':
    case 'db_down':
      return 'Databas saknas. Projects kräver databas för persistens.';
    case 'server_error':
      return 'Serverfel. Försök igen senare.';
    case 'network_error':
      return 'Nätverksfel. Kontrollera anslutning.';
    case 'validation_error':
      return responseData?.detail || 'Valideringsfel. Kontrollera indata.';
    case 'not_found':
      return 'Resurs hittades inte.';
    default:
      return responseData?.detail || responseData?.error?.message || 'Ett okänt fel uppstod.';
  }
}

/**
 * Typed fetch wrapper with request correlation and error handling
 */
export async function apiRequest<T = any>(
  endpoint: string,
  options: RequestOptions = {}
): Promise<T> {
  const requestId = generateRequestId();
  const url = `${API_BASE_URL}${endpoint}`;

  // Prepare headers
  const headers = new Headers(options.headers);
  headers.set('X-Request-Id', requestId);

  // Handle body
  let body: BodyInit | undefined;
  if (options.body) {
    if (options.body instanceof FormData) {
      // FormData - don't set Content-Type, browser will set it with boundary
      body = options.body;
    } else if (options.body instanceof Blob || options.body instanceof ArrayBuffer) {
      body = options.body;
    } else if (typeof options.body === 'object') {
      // JSON
      headers.set('Content-Type', 'application/json');
      body = JSON.stringify(options.body);
    } else {
      body = options.body as BodyInit;
    }
  }

  try {
    const response = await fetch(url, {
      ...options,
      headers,
      body,
    });

    // Extract response request ID (backend echoes it)
    const responseRequestId = response.headers.get('X-Request-Id') || requestId;

    // Handle non-2xx responses
    if (!response.ok) {
      let responseData: any = {};
      try {
        const contentType = response.headers.get('content-type');
        if (contentType?.includes('application/json')) {
          responseData = await response.json();
        } else {
          responseData = { detail: await response.text() };
        }
      } catch (e) {
        // Ignore parse errors
      }

      // Check if it's a DB error (503 with specific detail)
      let errorCode = mapErrorToCode(response.status, null);
      if (response.status === 503 && (
        responseData?.detail?.includes('Database not available') ||
        responseData?.error?.detail?.includes('Database not available') ||
        responseData?.status === 'db_uninitialized' ||
        responseData?.status === 'db_down'
      )) {
        errorCode = 'db_down';
      }

      const errorMessage = getErrorMessage(errorCode, responseData);

      const error: ApiError = {
        code: errorCode,
        message: errorMessage,
        request_id: responseRequestId,
        originalError: new Error(`HTTP ${response.status}`),
      };

      // Brutal-safe logging: only error code + request_id
      console.error('[API Error]', errorCode, responseRequestId);

      throw error;
    }

    // Parse successful response
    const contentType = response.headers.get('content-type');
    if (contentType?.includes('application/json')) {
      return await response.json();
    } else {
      return await response.text() as any;
    }

  } catch (error) {
    // Network errors or fetch failures
    if (error instanceof TypeError || error instanceof Error) {
      const errorCode = mapErrorToCode(undefined, error);
      const errorMessage = getErrorMessage(errorCode);

      const apiError: ApiError = {
        code: errorCode,
        message: errorMessage,
        request_id: requestId,
        isTlsError: errorCode === 'mtls_handshake_failed',
        originalError: error,
      };

      // Brutal-safe logging
      console.error('[API Error]', errorCode, requestId);

      throw apiError;
    }

    // Re-throw if not an Error
    throw error;
  }
}

/**
 * Convenience methods
 */
export const api = {
  get: <T = any>(endpoint: string, options?: RequestOptions) =>
    apiRequest<T>(endpoint, { ...options, method: 'GET' }),

  post: <T = any>(endpoint: string, body?: any, options?: RequestOptions) =>
    apiRequest<T>(endpoint, { ...options, method: 'POST', body }),

  put: <T = any>(endpoint: string, body?: any, options?: RequestOptions) =>
    apiRequest<T>(endpoint, { ...options, method: 'PUT', body }),

  patch: <T = any>(endpoint: string, body?: any, options?: RequestOptions) =>
    apiRequest<T>(endpoint, { ...options, method: 'PATCH', body }),

  delete: <T = any>(endpoint: string, options?: RequestOptions) =>
    apiRequest<T>(endpoint, { ...options, method: 'DELETE' }),
};

// Export base URL for reference
export { API_BASE_URL };

