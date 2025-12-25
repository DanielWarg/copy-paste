/**
 * Request ID generation for correlation
 * 
 * Generates unique request IDs that can be traced from UI → Backend → Logs
 */

export function generateRequestId(): string {
  return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}

/**
 * Get axios config with X-Request-Id header
 */
export function getAxiosConfigWithRequestId(customHeaders: Record<string, string> = {}) {
  return {
    headers: {
      'X-Request-Id': generateRequestId(),
      ...customHeaders,
    },
  };
}

