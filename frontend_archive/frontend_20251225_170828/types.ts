export enum EventStatus {
  INCOMING = 'INKOMMANDE',
  TRIAGED = 'PÅGÅR', 
  PROCESSING = 'BEARBETAS',
  REVIEW = 'GRANSKNING',
  PUBLISHED = 'PUBLICERAD',
  ARCHIVED = 'ARKIVERAD'
}

export enum SourceType {
  RSS = 'RSS',
  MANUAL = 'MANUELL',
  UPLOAD = 'UPLOAD',
  TRANSCRIPT = 'TRANSKRIPTION'
}

export interface Citation {
  id: string;
  sourceText: string;
  startIndex: number;
  endIndex: number;
  confidence: number;
}

export interface PrivacyLog {
  timestamp: string;
  action: string;
  details: string;
}

export interface NewsEvent {
  id: string;
  title: string;
  summary: string;
  source: string;
  sourceType: SourceType;
  timestamp: string;
  status: EventStatus;
  score: number; // 0-100 Relevans
  content?: string; // Originaltext
  maskedContent?: string; // PII-maskad text
  draft?: string; // AI-genererat utkast
  citations?: Citation[];
  privacyLogs?: PrivacyLog[];
  isDuplicate?: boolean;
}

export interface Transcript {
  id: string;
  title: string;
  date: string;
  duration: string;
  speakers: number;
  snippet: string;
  status: 'KLAR' | 'BEARBETAS' | 'FEL';
}

export interface Source {
  id: string;
  name: string;
  type: 'RSS' | 'API' | 'MAIL';
  status: 'ACTIVE' | 'PAUSED' | 'ERROR';
  lastFetch: string;
  itemsPerDay: number;
}