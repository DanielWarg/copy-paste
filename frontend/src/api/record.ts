/**
 * Record Module API
 * 
 * Typed wrappers for record endpoints:
 * - POST /api/v1/record/create
 * - POST /api/v1/record/{transcript_id}/audio
 */

import { apiRequest } from './client';

export interface CreateRecordRequest {
  title: string;
  project_id?: number;
  sensitivity?: 'standard' | 'sensitive';
  language?: string;
}

export interface CreateRecordResponse {
  project_id: number;
  transcript_id: number;
  title: string;
  created_at: string;
}

export interface UploadAudioResponse {
  status: string;
  file_id: number;
  sha256: string;
  size_bytes: number;
  mime_type: string;
}

/**
 * Create a new record (project + transcript shell)
 */
export async function createRecord(
  title: string,
  options?: { 
    project_id?: number;
    sensitivity?: 'standard' | 'sensitive'; 
    language?: string;
  }
): Promise<CreateRecordResponse> {
  const payload: CreateRecordRequest = {
    title,
    ...(options?.project_id && { project_id: options.project_id }),
    ...(options?.sensitivity && { sensitivity: options.sensitivity }),
    ...(options?.language && { language: options.language }),
  };

  return apiRequest<CreateRecordResponse>('/api/v1/record/create', {
    method: 'POST',
    body: payload,
  });
}

/**
 * Upload audio file for a transcript
 * 
 * @param transcriptId - Transcript ID from createRecord
 * @param file - File object from input[type=file]
 */
export async function uploadAudio(
  transcriptId: number,
  file: File
): Promise<UploadAudioResponse> {
  const formData = new FormData();
  formData.append('file', file);

  // Note: Native fetch doesn't support progress tracking directly
  // For now, we show "Uploading..." state
  // If progress is needed, we'd need XMLHttpRequest or a library
  return apiRequest<UploadAudioResponse>(
    `/api/v1/record/${transcriptId}/audio`,
    {
      method: 'POST',
      body: formData,
    }
  );
}

