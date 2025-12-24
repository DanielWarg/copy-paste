/**
 * API Client Adapter
 * 
 * Denna fil hanterar all kommunikation med backend (CORE).
 * Om VITE_USE_MOCK=false: använder riktiga API-anrop
 * Annars: kör i "mock mode" med statisk data.
 * 
 * INGA API-NYCKLAR SKA FINNAS HÄR.
 * INGA HEADERS/BODIES LOGGAS.
 */

import { MOCK_EVENTS, MOCK_TRANSCRIPTS, MOCK_SOURCES } from './mockData';
import { NewsEvent, Transcript, Source, EventStatus, SourceType } from './types';

// API Base URL från environment (optional)
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const USE_MOCK = import.meta.env.VITE_USE_MOCK === 'true' || (import.meta.env.VITE_USE_MOCK === undefined && import.meta.env.DEV);

// Simulera nätverksfördröjning (endast för mock)
const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

// Error response type
interface ApiError {
  code: string;
  message: string;
  request_id?: string;
}

// Fetch wrapper med error handling
async function apiFetch<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<{ data: T; error: null } | { data: null; error: ApiError }> {
  const url = `${API_BASE_URL}${endpoint}`;
  
  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    // Extract request_id from header
    const requestId = response.headers.get('X-Request-Id') || undefined;

    // Handle non-JSON responses (e.g., ZIP files)
    const contentType = response.headers.get('Content-Type') || '';
    if (contentType.includes('application/zip') || contentType.includes('application/octet-stream')) {
      if (!response.ok) {
        return {
          data: null,
          error: {
            code: `http_${response.status}`,
            message: `Request failed with status ${response.status}`,
            request_id: requestId,
          },
        };
      }
      // Return blob for binary responses
      const blob = await response.blob();
      return { data: blob as unknown as T, error: null };
    }

    const json = await response.json();

    if (!response.ok) {
      // Extract error from response body
      const errorData = json.error || json;
      return {
        data: null,
        error: {
          code: errorData.code || `http_${response.status}`,
          message: errorData.message || errorData.detail || `Request failed with status ${response.status}`,
          request_id: errorData.request_id || requestId,
        },
      };
    }

    return { data: json as T, error: null };
  } catch (error) {
    // Network error, CORS issue, etc.
    if (error instanceof Error && error.name === 'AbortError') {
      return {
        data: null,
        error: {
          code: 'timeout',
          message: 'Request timed out',
        },
      };
    }
    return {
      data: null,
      error: {
        code: 'network_error',
        message: error instanceof Error ? error.message : 'Network error',
      },
    };
  }
}

// Adapter: Mappa backend Transcript response till UI Transcript type
function adaptTranscript(backendTranscript: any): Transcript {
  // Backend format: { id, title, source, language, duration_seconds, status, created_at, preview, segments_count }
  // UI format: { id, title, date, duration, speakers, snippet, status }
  
  const durationSeconds = backendTranscript.duration_seconds || 0;
  const hours = Math.floor(durationSeconds / 3600);
  const minutes = Math.floor((durationSeconds % 3600) / 60);
  const seconds = durationSeconds % 60;
  const duration = hours > 0 
    ? `${hours}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`
    : `${minutes}:${seconds.toString().padStart(2, '0')}`;

  return {
    id: backendTranscript.id?.toString() || '',
    title: backendTranscript.title || 'Untitled',
    date: backendTranscript.created_at ? new Date(backendTranscript.created_at).toISOString().split('T')[0] : new Date().toISOString().split('T')[0],
    duration: duration,
    speakers: backendTranscript.segments_count ? Math.max(1, Math.floor(backendTranscript.segments_count / 10)) : 1, // Estimate speakers from segments
    snippet: backendTranscript.preview || backendTranscript.segments?.[0]?.text?.substring(0, 100) || '',
    status: backendTranscript.status === 'ready' ? 'KLAR' : backendTranscript.status === 'processing' ? 'BEARBETAS' : 'FEL',
  };
}

// Adapter: Mappa backend response till UI Transcript[] type
function adaptTranscripts(backendResponse: any): Transcript[] {
  if (backendResponse.items && Array.isArray(backendResponse.items)) {
    return backendResponse.items.map(adaptTranscript);
  }
  if (Array.isArray(backendResponse)) {
    return backendResponse.map(adaptTranscript);
  }
  return [];
}

// Connectivity check mot CORE endpoints
// Fails softly: returns {health: false, ready: false} on any error
// UI should never crash if backend is unavailable
const checkCoreHealth = async (): Promise<{ health: boolean; ready: boolean }> => {
  if (USE_MOCK || !API_BASE_URL) {
    return { health: false, ready: false };
  }

  try {
    // Check /health (should always be 200)
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 5000);

    const healthRes = await fetch(`${API_BASE_URL}/health`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
      signal: controller.signal,
    });
    clearTimeout(timeoutId);
    const healthOk = healthRes.ok;

    // Check /ready (200 if ready, 503 if not)
    const readyController = new AbortController();
    const readyTimeoutId = setTimeout(() => readyController.abort(), 5000);

    const readyRes = await fetch(`${API_BASE_URL}/ready`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
      signal: readyController.signal,
    });
    clearTimeout(readyTimeoutId);
    const readyOk = readyRes.ok;

    return { health: healthOk, ready: readyOk };
  } catch (error) {
    // Network error, CORS issue, or timeout - fail softly
    // Don't log full error details (privacy-safe)
    if (error instanceof Error && error.name === 'AbortError') {
      console.warn('CORE connectivity check timed out');
    } else {
      console.warn('CORE connectivity check failed (backend may be offline)');
    }
    return { health: false, ready: false };
  }
};

// Cache connectivity status (check once on module load)
let coreStatus: { health: boolean; ready: boolean } | null = null;

export const apiClient = {
  // Connectivity check (only if not using mock)
  checkCoreConnectivity: async (): Promise<{ health: boolean; ready: boolean }> => {
    if (USE_MOCK || !API_BASE_URL) {
      return { health: false, ready: false };
    }
    if (coreStatus === null) {
      coreStatus = await checkCoreHealth();
    }
    return coreStatus;
  },

  // Get Transcripts
  getTranscripts: async (): Promise<Transcript[]> => {
    if (USE_MOCK) {
      await delay(300);
      return MOCK_TRANSCRIPTS;
    }

    const result = await apiFetch<{ items: any[]; total: number }>('/api/v1/transcripts?limit=200');
    if (result.error) {
      console.warn('Failed to fetch transcripts, falling back to mock:', result.error.message);
      return MOCK_TRANSCRIPTS;
    }

    return adaptTranscripts(result.data);
  },

  // Get Events
  getEvents: async (): Promise<NewsEvent[]> => {
    if (USE_MOCK) {
      await delay(300);
      return MOCK_EVENTS;
    }

    const result = await apiFetch<{ items: any[]; total: number }>('/api/v1/events?limit=200');
    if (result.error) {
      console.warn('Failed to fetch events, falling back to mock:', result.error.message);
      return MOCK_EVENTS;
    }

    // Adapt backend events to frontend format
    return result.data.items.map((item: any) => ({
      id: item.id || '',
      title: item.title || 'Untitled',
      summary: item.summary || '',
      source: item.source || 'Unknown',
      sourceType: item.sourceType === 'RSS' ? SourceType.RSS : SourceType.MANUAL,
      timestamp: item.timestamp || new Date().toISOString(),
      status: item.status === 'INKOMMANDE' ? EventStatus.INCOMING :
              item.status === 'PÅGÅR' ? EventStatus.TRIAGED :
              item.status === 'BEARBETAS' ? EventStatus.PROCESSING :
              item.status === 'GRANSKNING' ? EventStatus.REVIEW :
              item.status === 'PUBLICERAD' ? EventStatus.PUBLISHED :
              EventStatus.ARCHIVED,
      score: item.score || 50,
      content: item.content,
      maskedContent: item.maskedContent,
      draft: item.draft,
      citations: item.citations,
      privacyLogs: item.privacyLogs,
      isDuplicate: item.isDuplicate || false,
    }));
  },

  getEventById: async (id: string): Promise<NewsEvent | undefined> => {
    if (USE_MOCK) {
      await delay(200);
      return MOCK_EVENTS.find(e => e.id === id);
    }

    const result = await apiFetch<any>(`/api/v1/events/${id}`);
    if (result.error) {
      console.warn('Failed to fetch event, falling back to mock:', result.error.message);
      return MOCK_EVENTS.find(e => e.id === id);
    }

    // Adapt backend event to frontend format
    const item = result.data;
    return {
      id: item.id || id,
      title: item.title || 'Untitled',
      summary: item.summary || '',
      source: item.source || 'Unknown',
      sourceType: item.sourceType === 'RSS' ? SourceType.RSS : SourceType.MANUAL,
      timestamp: item.timestamp || new Date().toISOString(),
      status: item.status === 'INKOMMANDE' ? EventStatus.INCOMING :
              item.status === 'PÅGÅR' ? EventStatus.TRIAGED :
              item.status === 'BEARBETAS' ? EventStatus.PROCESSING :
              item.status === 'GRANSKNING' ? EventStatus.REVIEW :
              item.status === 'PUBLICERAD' ? EventStatus.PUBLISHED :
              EventStatus.ARCHIVED,
      score: item.score || 50,
      content: item.content,
      maskedContent: item.maskedContent,
      draft: item.draft,
      citations: item.citations,
      privacyLogs: item.privacyLogs,
      isDuplicate: item.isDuplicate || false,
    };
  },

  // Get Sources
  getSources: async (): Promise<Source[]> => {
    if (USE_MOCK) {
      await delay(200);
      return MOCK_SOURCES;
    }

    const result = await apiFetch<{ items: any[]; total: number }>('/api/v1/sources');
    if (result.error) {
      console.warn('Failed to fetch sources, falling back to mock:', result.error.message);
      return MOCK_SOURCES;
    }

    // Adapt backend sources to frontend format
    return result.data.items.map((item: any) => ({
      id: item.id || '',
      name: item.name || 'Unknown',
      type: (item.type === 'RSS' || item.type === 'API' || item.type === 'MAIL') ? item.type : 'RSS',
      status: (item.status === 'ACTIVE' || item.status === 'PAUSED' || item.status === 'ERROR') ? item.status : 'ACTIVE',
      lastFetch: item.lastFetch || 'Aldrig',
      itemsPerDay: item.itemsPerDay || 0,
    }));
  },

  // Export download: Hämta ZIP från backend
  downloadExport: async (zipPath: string): Promise<Blob | null> => {
    if (USE_MOCK) {
      // Mock: returnera tom blob
      return new Blob([''], { type: 'application/zip' });
    }

    // TODO: Backend saknar download endpoint
    // Förslag: GET /api/v1/record/export/{package_id}/download
    // eller GET /api/v1/record/export/download?zip_path=...
    // Alternativt: Använd zip_path direkt om backend exponerar /app/data som statisk fil
    console.warn('Export download endpoint saknas i backend');
    
    // Fallback: Försök hämta direkt från zip_path (fungerar om backend exponerar statiska filer)
    try {
      const result = await apiFetch<Blob>(zipPath, { method: 'GET' });
      if (result.error) {
        console.error('Failed to download export:', result.error.message);
        return null;
      }
      return result.data;
    } catch (error) {
      console.error('Failed to download export:', error);
      return null;
    }
  },

  // Stub-metoder för framtida implementation
  createEvent: async (data: Partial<NewsEvent>) => {
    // Loggar endast händelsetyp, aldrig data
    console.log("API: Creating new event signal");
    if (USE_MOCK) {
      return { success: true };
    }
    // TODO: Implementera när events endpoint finns
    return { success: false, error: 'Events endpoint not implemented' };
  },

  maskContent: async (text: string) => {
    console.log("API: Requesting Privacy Shield processing");
    if (USE_MOCK) {
      return { masked: text.replace(/Jan/g, "[PERSON]"), logs: [] };
    }
    // TODO: Implementera när privacy shield endpoint finns
    return { masked: text, logs: [] };
  },

  generateDraft: async (eventId: string) => {
    console.log("API: Requesting draft generation");
    if (USE_MOCK) {
      return { draft: "Utkast genererat..." };
    }
    // TODO: Implementera när draft generation endpoint finns
    return { draft: "", error: 'Draft generation not implemented' };
  }
};

/**
 * SAKNADE BACKEND ENDPOINTS:
 * 
 * 1. Events endpoint (för NewsEvent/Pipeline-vyn)
 *    - GET /api/v1/events - Lista events
 *    - GET /api/v1/events/{id} - Hämta specifik event
 *    - POST /api/v1/events - Skapa event
 *    - Alternativt: Använd scout-modulen om den exponerar events
 * 
 * 2. Sources endpoint (för Sources-vyn)
 *    - GET /api/v1/sources eller GET /api/v1/scout/feeds - Lista sources
 *    - POST /api/v1/sources - Lägg till source
 *    - PATCH /api/v1/sources/{id} - Uppdatera source
 *    - DELETE /api/v1/sources/{id} - Ta bort source
 * 
 * 3. Export download endpoint (för ZIP-download)
 *    - GET /api/v1/record/export/{package_id}/download - Hämta ZIP
 *    - Alternativt: GET /api/v1/record/export/download?zip_path=... - Hämta via zip_path
 *    - Returnerar ZIP bytes med Content-Type: application/zip
 * 
 * 4. Privacy Shield endpoint (för maskContent)
 *    - POST /api/v1/privacy/mask - Maskera content
 * 
 * 5. Draft generation endpoint (för generateDraft)
 *    - POST /api/v1/events/{id}/draft - Generera draft
 */
