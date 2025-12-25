import React, { useState, useRef } from 'react';
import axios from 'axios';
import { Mic, Upload, X, Loader2, CheckCircle2 } from 'lucide-react';

// Request ID utility (inline to avoid path issues)
function generateRequestId(): string {
  return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}

function getAxiosConfigWithRequestId(customHeaders: Record<string, string> = {}) {
  return {
    headers: {
      'X-Request-Id': generateRequestId(),
      ...customHeaders,
    },
  };
}

interface AudioUploadProps {
  onUploadComplete?: (transcriptId: number) => void;
  onError?: (error: string) => void;
  onTranscriptReady?: (transcriptId: number, transcript: any) => void;
}

// API Base URL - use relative paths in production (via proxy)
// In dev: use VITE_API_BASE_URL or fallback to localhost:8000
// In prod_brutal: all API calls go through proxy (HTTPS with mTLS)
// For mTLS testing: use https://localhost (proxy handles mTLS)
const API_BASE = import.meta.env.VITE_API_BASE_URL || 
  (import.meta.env.PROD ? 'https://localhost' : 'http://localhost:8000');

// Poll transcript status until ready or timeout
async function pollTranscriptStatus(
  transcriptId: number,
  onProgress?: (status: string) => void,
  maxAttempts: number = 60,
  intervalMs: number = 2000
): Promise<{ status: string; transcript?: any }> {
  for (let attempt = 0; attempt < maxAttempts; attempt++) {
    try {
      const response = await axios.get(
        `${API_BASE}/api/v1/transcripts/${transcriptId}`,
        getAxiosConfigWithRequestId()
      );

      const transcript = response.data;
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
      // If 404, transcript might not exist yet - wait and retry
      if (error.response?.status === 404 && attempt < 5) {
        await new Promise(resolve => setTimeout(resolve, intervalMs));
        continue;
      }
      throw error;
    }
  }

  // Timeout
  throw new Error('Transkribering tog för lång tid (timeout)');
}

export const AudioUpload: React.FC<AudioUploadProps> = ({ 
  onUploadComplete, 
  onError,
  onTranscriptReady 
}) => {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState<string>('');
  const [error, setError] = useState<string | null>(null);
  const [currentRequestId, setCurrentRequestId] = useState<string | null>(null);
  const [transcriptStatus, setTranscriptStatus] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      // Validate file type
      if (!selectedFile.type.startsWith('audio/')) {
        setError('Välj en ljudfil (WAV, MP3, etc.)');
        return;
      }
      // Validate file size (max 100MB)
      if (selectedFile.size > 100 * 1024 * 1024) {
        setError('Filen är för stor (max 100MB)');
        return;
      }
      setFile(selectedFile);
      setError(null);
      setTranscriptStatus(null);
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setError('Välj en fil först');
      return;
    }

    setUploading(true);
    setError(null);
    setProgress('Skapar record...');
    setTranscriptStatus(null);
    setCurrentRequestId(null);

    try {
      const requestId = generateRequestId();
      setCurrentRequestId(requestId);

      // Step 1: Create record
      const createRes = await axios.post(
        `${API_BASE}/api/v1/record/create`,
        {
          title: file.name || 'Audio upload'
        },
        {
          headers: {
            'X-Request-Id': requestId,
            'Content-Type': 'application/json',
          },
        }
      );

      const transcriptId = createRes.data.transcript_id;
      if (!transcriptId) {
        throw new Error('Kunde inte skapa record - saknar transcript_id');
      }

      setProgress(`Laddar upp ${file.name}...`);

      // Step 2: Upload audio file
      const formData = new FormData();
      formData.append('file', file);

      const uploadRequestId = generateRequestId();
      await axios.post(
        `${API_BASE}/api/v1/record/${transcriptId}/audio`,
        formData,
        {
          headers: {
            'X-Request-Id': uploadRequestId,
            'Content-Type': 'multipart/form-data',
          },
          onUploadProgress: (progressEvent) => {
            if (progressEvent.total) {
              const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total);
              setProgress(`Laddar upp... ${percent}%`);
            }
          },
        }
      );

      setProgress('Väntar på transkribering...');
      setTranscriptStatus('uploaded');

      // Step 3: Poll transcript status until ready
      const pollRequestId = generateRequestId();
      const result = await pollTranscriptStatus(
        transcriptId,
        (status) => {
          setTranscriptStatus(status);
          if (status === 'transcribing') {
            setProgress('Transkriberar...');
          } else if (status === 'uploaded') {
            setProgress('Väntar på transkribering...');
          }
        },
        60, // max 60 attempts
        2000 // 2 second interval = max 2 minutes
      );

      if (result.status === 'ready' || result.status === 'reviewed') {
        setProgress('Klart!');
        setTranscriptStatus('ready');
        
        // Callback with transcript data
        if (onTranscriptReady && result.transcript) {
          onTranscriptReady(transcriptId, result.transcript);
        }
        
        if (onUploadComplete) {
          onUploadComplete(transcriptId);
        }

        // Reset form after success
        setTimeout(() => {
          setFile(null);
          setProgress('');
          setTranscriptStatus(null);
          setCurrentRequestId(null);
          if (fileInputRef.current) {
            fileInputRef.current.value = '';
          }
        }, 3000);
      } else {
        throw new Error(`Transkribering misslyckades: status=${result.status}`);
      }

    } catch (err: any) {
      // Brutal-safe error handling: no payloads in UI logs
      const errorCode = err.response?.status || 'network_error';
      const errorRequestId = err.response?.data?.error?.request_id || currentRequestId || 'unknown';
      const errorMessage = err.response?.data?.detail || 
                          err.response?.data?.error?.message || 
                          err.message || 
                          'Ett fel uppstod vid uppladdning';
      
      // Log only error code + request_id (brutal-safe)
      console.error('Upload failed:', errorCode, errorRequestId);
      
      setError(`${errorMessage} (${errorCode})`);
      if (onError) {
        onError(errorMessage);
      }
    } finally {
      setUploading(false);
    }
  };

  const handleRemove = () => {
    setFile(null);
    setError(null);
    setTranscriptStatus(null);
    setCurrentRequestId(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-3">
        <input
          ref={fileInputRef}
          type="file"
          accept="audio/*"
          onChange={handleFileSelect}
          disabled={uploading}
          className="hidden"
          id="audio-upload-input"
        />
        <label
          htmlFor="audio-upload-input"
          className={`flex items-center gap-2 px-4 py-2 bg-zinc-900 dark:bg-white dark:text-black text-white text-sm font-medium rounded-sm shadow-sm hover:opacity-90 transition-opacity cursor-pointer ${
            uploading ? 'opacity-50 cursor-not-allowed' : ''
          }`}
        >
          <Upload size={16} />
          <span>{file ? 'Välj annan fil' : '+ Ladda upp ljudfil'}</span>
        </label>

        {file && (
          <>
            <div className="flex items-center gap-2 px-3 py-1.5 bg-zinc-100 dark:bg-zinc-800 rounded-sm text-sm">
              <Mic size={14} className="text-zinc-500" />
              <span className="text-zinc-900 dark:text-zinc-200">{file.name}</span>
              <span className="text-zinc-500 text-xs">
                ({(file.size / (1024 * 1024)).toFixed(1)} MB)
              </span>
              {!uploading && (
                <button
                  onClick={handleRemove}
                  className="ml-2 text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-300"
                >
                  <X size={14} />
                </button>
              )}
            </div>

            {!uploading && (
              <button
                onClick={handleUpload}
                className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-medium rounded-sm shadow-sm transition-colors"
              >
                Starta transkribering
              </button>
            )}
          </>
        )}
      </div>

      {uploading && (
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-sm text-zinc-600 dark:text-zinc-400">
            <Loader2 size={16} className="animate-spin" />
            <span>{progress}</span>
          </div>
          {transcriptStatus && (
            <div className="text-xs text-zinc-500 dark:text-zinc-400 ml-6">
              Status: {transcriptStatus === 'uploaded' ? 'Uppladdad' : 
                       transcriptStatus === 'transcribing' ? 'Transkriberar' :
                       transcriptStatus === 'ready' ? 'Klar' : transcriptStatus}
            </div>
          )}
          {currentRequestId && import.meta.env.DEV && (
            <div className="text-xs text-zinc-400 dark:text-zinc-500 ml-6 font-mono">
              Request ID: {currentRequestId.substring(0, 8)}...
            </div>
          )}
        </div>
      )}

      {transcriptStatus === 'ready' && !uploading && (
        <div className="flex items-center gap-2 text-sm text-emerald-600 dark:text-emerald-400">
          <CheckCircle2 size={16} />
          <span>Transkribering klar!</span>
        </div>
      )}

      {error && (
        <div className="px-3 py-2 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-900/50 rounded-sm text-sm text-red-700 dark:text-red-400">
          {error}
          {import.meta.env.DEV && currentRequestId && (
            <div className="text-xs mt-1 font-mono opacity-75">
              Request ID: {currentRequestId}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
