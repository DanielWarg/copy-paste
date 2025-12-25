/**
 * Request ID Generation Utility
 * 
 * Generates unique request IDs for request correlation.
 * Format: timestamp-randomString
 */

export function generateRequestId(): string {
  return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}
