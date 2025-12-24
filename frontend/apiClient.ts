/**
 * API Client Adapter
 * 
 * Denna fil hanterar all kommunikation med backend (CORE).
 * Om VITE_API_BASE_URL är satt: gör connectivity-check mot /health och /ready.
 * Annars: kör i "mock mode" med statisk data.
 * 
 * INGA API-NYCKLAR SKA FINNAS HÄR.
 * INGA HEADERS/BODIES LOGGAS.
 */

import { MOCK_EVENTS, MOCK_TRANSCRIPTS, MOCK_SOURCES } from './mockData';
import { NewsEvent, Transcript, Source } from './types';

// API Base URL från environment (optional)
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

// Simulera nätverksfördröjning
const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

// Connectivity check mot CORE endpoints
// Fails softly: returns {health: false, ready: false} on any error
// UI should never crash if backend is unavailable
const checkCoreHealth = async (): Promise<{ health: boolean; ready: boolean }> => {
  if (!API_BASE_URL) {
    return { health: false, ready: false };
  }

  try {
    // Check /health (should always be 200)
    // Use AbortController for timeout (5s max)
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
  // Connectivity check (only if API_BASE_URL is set)
  checkCoreConnectivity: async (): Promise<{ health: boolean; ready: boolean }> => {
    if (!API_BASE_URL) {
      return { health: false, ready: false };
    }
    if (coreStatus === null) {
      coreStatus = await checkCoreHealth();
    }
    return coreStatus;
  },

  // Mock methods (continue to use mock data until real endpoints are built)
  getEvents: async (): Promise<NewsEvent[]> => {
    await delay(300);
    return MOCK_EVENTS;
  },

  getEventById: async (id: string): Promise<NewsEvent | undefined> => {
    await delay(200);
    return MOCK_EVENTS.find(e => e.id === id);
  },

  getTranscripts: async (): Promise<Transcript[]> => {
    await delay(300);
    return MOCK_TRANSCRIPTS;
  },

  getSources: async (): Promise<Source[]> => {
    await delay(200);
    return MOCK_SOURCES;
  },

  // Stub-metoder för framtida implementation
  createEvent: async (data: Partial<NewsEvent>) => {
    // Loggar endast händelsetyp, aldrig data
    console.log("API: Creating new event signal");
    return { success: true };
  },

  maskContent: async (text: string) => {
    console.log("API: Requesting Privacy Shield processing");
    return { masked: text.replace(/Jan/g, "[PERSON]"), logs: [] };
  },

  generateDraft: async (eventId: string) => {
    console.log("API: Requesting draft generation");
    return { draft: "Utkast genererat..." };
  }
};