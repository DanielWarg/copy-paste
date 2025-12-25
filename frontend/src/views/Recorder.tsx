/**
 * Transkribering View
 * 
 * Full implementation of record creation and audio upload flow.
 * States: idle → creating → created → uploading → success/error
 */

import { useState, useRef, useEffect } from 'react';
import { createRecord, uploadAudio, CreateRecordResponse, UploadAudioResponse } from '../api/record';
import { getProject, Project } from '../api/projects';
import { ApiError, API_BASE_URL } from '../api/client';
import { Mic, Upload, Loader2, CheckCircle2, AlertCircle, X, Folder } from 'lucide-react';

type RecorderState = 
  | { status: 'idle' }
  | { status: 'creating'; title: string }
  | { status: 'created'; record: CreateRecordResponse }
  | { status: 'uploading'; record: CreateRecordResponse; progress: number }
  | { status: 'success'; record: CreateRecordResponse; upload: UploadAudioResponse }
  | { status: 'error'; error: ApiError };

interface RecorderProps {
  projectId?: number;
}

export function Recorder({ projectId }: RecorderProps) {
  const [state, setState] = useState<RecorderState>({ status: 'idle' });
  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState('');
  const [project, setProject] = useState<Project | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Load project if projectId provided
  useEffect(() => {
    if (projectId) {
      getProject(projectId)
        .then(setProject)
        .catch(() => {
          // Silently fail - project might not exist
        });
    }
  }, [projectId]);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (!selectedFile) return;

    // Validate file type
    if (!selectedFile.type.startsWith('audio/')) {
      setState({
        status: 'error',
        error: {
          code: 'validation_error',
          message: 'Välj en ljudfil (WAV, MP3, etc.)',
          request_id: '',
        },
      });
      return;
    }

    // Validate file size (200MB max per backend)
    const maxSize = 200 * 1024 * 1024; // 200MB
    if (selectedFile.size > maxSize) {
      setState({
        status: 'error',
        error: {
          code: 'validation_error',
          message: `Filen är för stor (max ${Math.round(maxSize / 1024 / 1024)}MB)`,
          request_id: '',
        },
      });
      return;
    }

    setFile(selectedFile);
    // Auto-fill title from filename (without extension)
    if (!title) {
      const nameWithoutExt = selectedFile.name.replace(/\.[^/.]+$/, '');
      setTitle(nameWithoutExt);
    }
    // Reset any previous error
    if (state.status === 'error') {
      setState({ status: 'idle' });
    }
  };

  const handleStart = async () => {
    if (!file) {
      setState({
        status: 'error',
        error: {
          code: 'validation_error',
          message: 'Välj en fil först',
          request_id: '',
        },
      });
      return;
    }

    const recordTitle = title.trim() || file.name.replace(/\.[^/.]+$/, '');

    try {
      // Step 1: Create record
      setState({ status: 'creating', title: recordTitle });

      const record = await createRecord(recordTitle, {
        project_id: projectId,
      });
      
      setState({ status: 'created', record });

      // Step 2: Upload audio
      setState({ status: 'uploading', record, progress: 0 });

      const upload = await uploadAudio(record.transcript_id, file);

      setState({ status: 'success', record, upload });

    } catch (error: any) {
      // Better error handling - check if it's already an ApiError
      let apiError: ApiError;
      if (error && typeof error === 'object' && 'code' in error) {
        apiError = error as ApiError;
      } else {
        // Wrap unknown errors
        apiError = {
          code: 'unknown',
          message: error?.message || String(error) || 'Ett okänt fel uppstod',
          request_id: '',
          originalError: error,
        };
      }
      
      setState({ status: 'error', error: apiError });
      
      // Brutal-safe logging: only error code + request_id
      console.error('[Transkribering Error]', {
        code: apiError.code,
        message: apiError.message,
        request_id: apiError.request_id,
        url: API_BASE_URL + '/api/v1/record/create',
      });
    }
  };

  const handleReset = () => {
    setState({ status: 'idle' });
    setFile(null);
    setTitle('');
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const renderContent = () => {
    switch (state.status) {
      case 'idle':
        return (
          <div className="p-6">
            <div className="max-w-5xl mx-auto">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-serif font-bold text-zinc-900 dark:text-white">
                  Transkribering
                </h2>
                {project && (
                  <div className="flex items-center gap-2 px-3 py-1.5 bg-zinc-100 dark:bg-zinc-700 rounded-sm text-sm">
                    <Folder size={14} className="text-zinc-500" />
                    <span className="text-zinc-900 dark:text-zinc-200">Projekt: {project.name}</span>
                  </div>
                )}
              </div>
              
              <div className="bg-white dark:bg-zinc-800 p-6 rounded-sm shadow-sm border border-zinc-200 dark:border-zinc-700">
                <h3 className="text-lg font-semibold text-zinc-900 dark:text-white mb-4">
                  Ladda upp ljudfil för transkribering
                </h3>
                <p className="text-sm text-zinc-500 dark:text-zinc-400 mb-4">
                  Välj en ljudfil (t.ex. WAV, MP3) för att automatiskt transkribera den. Max 200MB.
                </p>

                <div className="space-y-4">
                  {/* File input - Simple label approach */}
                  <div>
                    <input
                      ref={fileInputRef}
                      type="file"
                      accept="audio/*"
                      onChange={handleFileSelect}
                      className="hidden"
                      id="audio-upload-input"
                    />
                    <label
                      htmlFor="audio-upload-input"
                      className="inline-flex items-center gap-2 px-4 py-2 bg-zinc-900 dark:bg-white dark:text-black text-white text-sm font-medium rounded-sm shadow-sm hover:opacity-90 transition-opacity cursor-pointer"
                    >
                      <Upload size={16} />
                      <span>+ Välj ljudfil</span>
                    </label>
                  </div>

                  {/* Selected file */}
                  {file && (
                    <div className="flex items-center gap-2 px-3 py-1.5 bg-zinc-100 dark:bg-zinc-700 rounded-sm text-sm">
                      <Mic size={14} className="text-zinc-500" />
                      <span className="text-zinc-900 dark:text-zinc-200">{file.name}</span>
                      <span className="text-zinc-500 text-xs">
                        ({(file.size / (1024 * 1024)).toFixed(1)} MB)
                      </span>
                      <button
                        type="button"
                        onClick={() => {
                          setFile(null);
                          if (fileInputRef.current) {
                            fileInputRef.current.value = '';
                          }
                        }}
                        className="ml-auto text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-300"
                      >
                        <X size={14} />
                      </button>
                    </div>
                  )}

                  {/* Title input */}
                  {file && (
                    <div>
                      <label className="block text-sm font-medium text-zinc-900 dark:text-white mb-2">
                        Titel (valfritt)
                      </label>
                      <input
                        type="text"
                        value={title}
                        onChange={(e) => setTitle(e.target.value)}
                        placeholder={file.name.replace(/\.[^/.]+$/, '')}
                        className="w-full px-3 py-2 text-sm bg-zinc-100 dark:bg-zinc-700 border border-zinc-200 dark:border-zinc-600 rounded-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 text-zinc-900 dark:text-white"
                      />
                    </div>
                  )}

                  {/* Start button */}
                  {file && (
                    <button
                      type="button"
                      onClick={handleStart}
                      className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-medium rounded-sm shadow-sm transition-colors"
                    >
                      Starta transkribering
                    </button>
                  )}
                </div>
              </div>
            </div>
          </div>
        );

      case 'creating':
        return (
          <div className="p-6">
            <div className="max-w-5xl mx-auto">
              <div className="bg-white dark:bg-zinc-800 p-6 rounded-sm shadow-sm border border-zinc-200 dark:border-zinc-700">
                <div className="flex items-center gap-2 text-zinc-600 dark:text-zinc-400">
                  <Loader2 size={20} className="animate-spin" />
                  <span>Initierar transkribering...</span>
                </div>
              </div>
            </div>
          </div>
        );

      case 'created':
        return (
          <div className="p-6">
            <div className="max-w-5xl mx-auto">
              <div className="bg-white dark:bg-zinc-800 p-6 rounded-sm shadow-sm border border-zinc-200 dark:border-zinc-700">
                <div className="flex items-center gap-2 text-zinc-600 dark:text-zinc-400">
                  <Loader2 size={20} className="animate-spin" />
                  <span>Laddar upp ljudfil...</span>
                </div>
              </div>
            </div>
          </div>
        );

      case 'uploading':
        return (
          <div className="p-6">
            <div className="max-w-5xl mx-auto">
              <div className="bg-white dark:bg-zinc-800 p-6 rounded-sm shadow-sm border border-zinc-200 dark:border-zinc-700">
                <div className="flex items-center gap-2 text-zinc-600 dark:text-zinc-400">
                  <Loader2 size={20} className="animate-spin" />
                  <span>Laddar upp: {state.progress}%</span>
                </div>
              </div>
            </div>
          </div>
        );

      case 'success':
        return (
          <div className="p-6">
            <div className="max-w-5xl mx-auto">
              <div className="bg-white dark:bg-zinc-800 p-6 rounded-sm shadow-sm border border-zinc-200 dark:border-zinc-700">
                <div className="flex items-center gap-2 text-emerald-600 dark:text-emerald-500 mb-4">
                  <CheckCircle2 size={20} />
                  <span className="font-semibold">Uppladdning klar!</span>
                </div>
                
                <div className="space-y-2 text-sm">
                  <div>
                    <span className="text-zinc-500 dark:text-zinc-400">Record ID:</span>{' '}
                    <span className="text-zinc-900 dark:text-white font-mono">
                      {state.record.transcript_id}
                    </span>
                  </div>
                  <div>
                    <span className="text-zinc-500 dark:text-zinc-400">SHA256:</span>{' '}
                    <span className="text-zinc-900 dark:text-white font-mono text-xs">
                      {state.upload.sha256}
                    </span>
                  </div>
                  <div>
                    <span className="text-zinc-500 dark:text-zinc-400">Storlek:</span>{' '}
                    <span className="text-zinc-900 dark:text-white">
                      {(state.upload.size_bytes / (1024 * 1024)).toFixed(1)} MB
                    </span>
                  </div>
                  <div>
                    <span className="text-zinc-500 dark:text-zinc-400">Format:</span>{' '}
                    <span className="text-zinc-900 dark:text-white">{state.upload.mime_type}</span>
                  </div>
                </div>

                {/* Data Protection Info */}
                <div className="mt-6 pt-4 border-t border-zinc-200 dark:border-zinc-700">
                  <p className="text-xs text-zinc-500 dark:text-zinc-400">
                    <strong>Dataskydd:</strong> Filer lagras krypterat (Fernet) och sparas utan originalfilnamn. Metadata (titel, datum) lagras i databasen. Innehåll loggas aldrig. Request ID används för felsökning.
                  </p>
                </div>

                <button
                  type="button"
                  onClick={handleReset}
                  className="mt-4 px-4 py-2 bg-zinc-200 dark:bg-zinc-700 hover:bg-zinc-300 dark:hover:bg-zinc-600 text-zinc-900 dark:text-white text-sm font-medium rounded-sm transition-colors"
                >
                  Ladda upp ny fil
                </button>
              </div>
            </div>
          </div>
        );

      case 'error':
        const error = state.error;
        const errorTitle = 
          error.code === 'mtls_handshake_failed' ? 'mTLS-certifikat krävs' :
          error.code === 'forbidden' ? 'Åtkomst nekad' :
          error.code === 'pii_blocked' ? 'Personuppgifter detekterade' :
          error.code === 'server_error' ? 'Serverfel' :
          'Ett fel uppstod';

        const isMtlsError = error.code === 'mtls_handshake_failed';

        return (
          <div className="p-6">
            <div className="max-w-5xl mx-auto">
              <div className="bg-white dark:bg-zinc-800 p-6 rounded-sm shadow-sm border border-red-200 dark:border-red-800">
                <div className="flex items-center gap-2 text-red-600 dark:text-red-500 mb-4">
                  <AlertCircle size={20} />
                  <span className="font-semibold">{errorTitle}</span>
                </div>
                
                <div className="text-sm text-zinc-900 dark:text-white mb-4">
                  {isMtlsError ? (
                    <>
                      Kunde inte ansluta till backend. <br />
                      <strong>Klientcertifikat krävs.</strong> <br />
                      Vänligen installera ditt mTLS klientcertifikat i webbläsaren. <br />
                      Se instruktioner i{' '}
                      <a
                        href="/docs/MTLS_BROWSER_SETUP.md"
                        target="_blank"
                        rel="noopener noreferrer"
                        className="underline text-blue-500 hover:text-blue-600"
                      >
                        docs/MTLS_BROWSER_SETUP.md
                      </a>
                      .
                    </>
                  ) : (
                    error.message
                  )}
                </div>

                {error.request_id && (
                  <div className="text-xs text-zinc-500 dark:text-zinc-400 font-mono mb-4">
                    Request ID: {error.request_id}
                  </div>
                )}

                <button
                  type="button"
                  onClick={handleReset}
                  className="px-4 py-2 bg-zinc-200 dark:bg-zinc-700 hover:bg-zinc-300 dark:hover:bg-zinc-600 text-zinc-900 dark:text-white text-sm font-medium rounded-sm transition-colors"
                >
                  Försök igen
                </button>
              </div>
            </div>
          </div>
        );
    }
  };

  return <div className="h-full">{renderContent()}</div>;
}
