/**
 * Recorder Hook - Real API Integration
 * 
 * Handles the complete recorder flow:
 * 1. Create record
 * 2. Upload audio
 * 3. Poll transcript status
 * 4. Return transcript when ready
 */

import { useState, useCallback } from 'react';
import { recordApi, transcriptApi, ApiError } from '../api/realApiClient';
import { RecorderStatus, RecorderState } from './RecorderState';

// Poll transcript status until ready or timeout
async function pollTranscriptStatus(
  transcriptId: number,
  onProgress?: (status: string) => void,
  maxAttempts: number = 60,
  intervalMs: number = 2000
): Promise<{ status: string; transcript?: any }> {
  for (let attempt = 0; attempt < maxAttempts; attempt++) {
    try {
      const transcript = await transcriptApi.getTranscript(transcriptId, false);
      const status = transcript.status || 'unknown';

      if (onProgress) {
        onProgress(status);
      }

      // Status values: uploaded|transcribing|ready|reviewed|archived|deleted
      if (status === 'ready' || status === 'reviewed') {
        return { status, transcript };
      }

      // If still transcribing, wait and retry
      if (status === 'transcribing' || status === 'uploaded') {
        await new Promise(resolve => setTimeout(resolve, intervalMs));
        continue;
      }

      // If error state, return immediately
      if (status === 'deleted' || status === 'error') {
        return { status, transcript };
      }

      // Unknown status, wait and retry
      await new Promise(resolve => setTimeout(resolve, intervalMs));
    } catch (error: any) {
      // If 404, transcript might not exist yet - wait and retry (first few attempts)
      if (error.code === 404 && attempt < 5) {
        await new Promise(resolve => setTimeout(resolve, intervalMs));
        continue;
      }
      throw error;
    }
  }

  // Timeout
  throw new Error('Transkribering tog för lång tid (timeout)');
}

export function useRecorder() {
  const [status, setStatus] = useState<RecorderStatus>({
    state: 'idle',
    progress: '',
  });

  const uploadAndTranscribe = useCallback(async (file: File) => {
    setStatus({ state: 'creating', progress: 'Skapar record...' });

    try {
      // Step 1: Create record
      const createResult = await recordApi.createRecord(file.name || 'Audio upload');
      const transcriptId = createResult.transcript_id;

      if (!transcriptId) {
        throw new Error('Kunde inte skapa record - saknar transcript_id');
      }

      setStatus({
        state: 'uploading',
        progress: `Laddar upp ${file.name}...`,
        transcriptId,
      });

      // Step 2: Upload audio
      await recordApi.uploadAudio(
        transcriptId,
        file,
        (percent) => {
          setStatus(prev => ({
            ...prev,
            progress: `Laddar upp... ${percent}%`,
          }));
        }
      );

      setStatus({
        state: 'transcribing',
        progress: 'Väntar på transkribering...',
        transcriptId,
      });

      // Step 3: Poll transcript status
      const result = await pollTranscriptStatus(
        transcriptId,
        (pollStatus) => {
          if (pollStatus === 'transcribing') {
            setStatus(prev => ({ ...prev, progress: 'Transkriberar...' }));
          } else if (pollStatus === 'uploaded') {
            setStatus(prev => ({ ...prev, progress: 'Väntar på transkribering...' }));
          }
        },
        60, // max 60 attempts
        2000 // 2 second interval = max 2 minutes
      );

      if (result.status === 'ready' || result.status === 'reviewed') {
        setStatus({
          state: 'done',
          progress: 'Klart!',
          transcriptId,
          transcript: result.transcript,
        });
        return { transcriptId, transcript: result.transcript };
      } else {
        throw new Error(`Transkribering misslyckades: status=${result.status}`);
      }
    } catch (error: any) {
      // Brutal-safe error handling
      const apiError = error as ApiError;
      setStatus({
        state: 'error',
        progress: '',
        error: apiError.message || 'Ett fel uppstod vid uppladdning',
        requestId: apiError.request_id,
      });
      throw error;
    }
  }, []);

  const reset = useCallback(() => {
    setStatus({ state: 'idle', progress: '' });
  }, []);

  return {
    status,
    uploadAndTranscribe,
    reset,
  };
}

