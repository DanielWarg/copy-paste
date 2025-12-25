/**
 * Recorder State Management
 * 
 * Manages state for the recorder flow: idle → creating → uploading → transcribing → done/error
 */

export type RecorderState = 
  | 'idle'
  | 'creating'
  | 'uploading'
  | 'transcribing'
  | 'done'
  | 'error';

export interface RecorderStatus {
  state: RecorderState;
  progress: string;
  transcriptId?: number;
  transcript?: any;
  error?: string;
  requestId?: string;
}

export const createInitialStatus = (): RecorderStatus => ({
  state: 'idle',
  progress: '',
});

