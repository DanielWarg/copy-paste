/**
 * Real Recorder Page - REAL WIRED (NO MOCK)
 * 
 * This page implements the recorder flow end-to-end:
 * - Upload audio file
 * - Create record
 * - Upload audio
 * - Poll transcription status
 * - Display transcript when ready
 * 
 * Visual profile: Same as Transcripts view (preserves look & feel)
 */

import React, { useState, useRef, useEffect } from 'react';
import { useRecorder } from '../core/recorder/useRecorder';
import { transcriptApi } from '../core/api/realApiClient';
import { FileText, Search, Mic, Upload, X, Loader2, CheckCircle2, AlertCircle } from 'lucide-react';
import { EmptyState } from '../components/ui/EmptyState';

interface RealRecorderPageProps {
  navigate: (page: string) => void;
}

export const RealRecorderPage: React.FC<RealRecorderPageProps> = ({ navigate }) => {
  const [file, setFile] = useState<File | null>(null);
  const [transcripts, setTranscripts] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  const { status, uploadAndTranscribe, reset } = useRecorder();

  // Load transcripts on mount and after upload
  const loadTranscripts = async () => {
    setIsLoading(true);
    try {
      const result = await transcriptApi.listTranscripts(200);
      setTranscripts(result.items || []);
    } catch (error: any) {
      console.error('Failed to load transcripts:', error.code, error.request_id);
      setTranscripts([]);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadTranscripts();
  }, []);

  // Refresh transcripts when upload completes
  useEffect(() => {
    if (status.state === 'done' && status.transcriptId) {
      setTimeout(() => {
        loadTranscripts();
        // Reset after showing success
        setTimeout(() => {
          reset();
          setFile(null);
          if (fileInputRef.current) {
            fileInputRef.current.value = '';
          }
        }, 3000);
      }, 1000);
    }
  }, [status.state, status.transcriptId, reset]);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      // Validate file type
      if (!selectedFile.type.startsWith('audio/')) {
        alert('Välj en ljudfil (WAV, MP3, etc.)');
        return;
      }
      // Validate file size (max 100MB)
      if (selectedFile.size > 100 * 1024 * 1024) {
        alert('Filen är för stor (max 100MB)');
        return;
      }
      setFile(selectedFile);
      reset(); // Reset any previous error
    }
  };

  const handleUpload = async () => {
    if (!file) {
      alert('Välj en fil först');
      return;
    }

    try {
      await uploadAndTranscribe(file);
    } catch (error: any) {
      // Error is already handled in useRecorder hook
      console.error('Upload failed:', error.code, error.request_id);
    }
  };

  const handleRemove = () => {
    setFile(null);
    reset();
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  // Adapt transcript to display format
  const adaptTranscript = (t: any) => ({
    id: t.id,
    title: t.title || 'Untitled',
    date: t.created_at ? new Date(t.created_at).toLocaleDateString('sv-SE') : 'N/A',
    duration: t.duration_seconds ? `${Math.floor(t.duration_seconds / 60)}:${String(t.duration_seconds % 60).padStart(2, '0')}` : 'N/A',
    status: t.status === 'ready' || t.status === 'reviewed' ? 'KLAR' : 'BEARBETAS',
    snippet: t.preview || t.segments?.[0]?.text?.substring(0, 50) || '',
  });

  const displayTranscripts = transcripts.map(adaptTranscript);

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-serif font-bold text-zinc-900 dark:text-white">Inspelning & Transkribering</h2>
          <p className="text-sm text-zinc-500 dark:text-zinc-400">Ladda upp ljudfil för transkribering</p>
        </div>
        
        {/* Upload Controls */}
        <div className="flex items-center gap-3">
          <input
            ref={fileInputRef}
            type="file"
            accept="audio/*"
            onChange={handleFileSelect}
            disabled={status.state !== 'idle' && status.state !== 'error'}
            className="hidden"
            id="real-recorder-upload-input"
          />
          <label
            htmlFor="real-recorder-upload-input"
            className={`flex items-center gap-2 px-4 py-2 bg-zinc-900 dark:bg-white dark:text-black text-white text-sm font-medium rounded-sm shadow-sm hover:opacity-90 transition-opacity cursor-pointer ${
              (status.state !== 'idle' && status.state !== 'error') ? 'opacity-50 cursor-not-allowed' : ''
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
                {(status.state === 'idle' || status.state === 'error') && (
                  <button
                    onClick={handleRemove}
                    className="ml-2 text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-300"
                  >
                    <X size={14} />
                  </button>
                )}
              </div>

              {status.state === 'idle' && (
                <button
                  onClick={handleUpload}
                  className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-medium rounded-sm shadow-sm transition-colors"
                >
                  Upload & Transcribe
                </button>
              )}
            </>
          )}
        </div>
      </div>

      {/* Status Display */}
      {status.state !== 'idle' && (
        <div className="bg-white dark:bg-[#18181b] border border-zinc-200 dark:border-white/5 rounded-sm p-4">
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-sm">
              {status.state === 'done' ? (
                <CheckCircle2 size={16} className="text-emerald-600 dark:text-emerald-400" />
              ) : status.state === 'error' ? (
                <AlertCircle size={16} className="text-red-600 dark:text-red-400" />
              ) : (
                <Loader2 size={16} className="animate-spin text-zinc-600 dark:text-zinc-400" />
              )}
              <span className="text-zinc-900 dark:text-white font-medium">
                {status.state === 'creating' && 'Skapar record...'}
                {status.state === 'uploading' && status.progress}
                {status.state === 'transcribing' && status.progress}
                {status.state === 'done' && 'Transkribering klar!'}
                {status.state === 'error' && 'Fel uppstod'}
              </span>
            </div>
            {status.progress && status.state !== 'done' && status.state !== 'error' && (
              <div className="text-xs text-zinc-500 dark:text-zinc-400 ml-6">
                {status.progress}
              </div>
            )}
            {status.requestId && import.meta.env.DEV && (
              <div className="text-xs text-zinc-400 dark:text-zinc-500 ml-6 font-mono">
                Request ID: {status.requestId}
              </div>
            )}
            {status.error && (
              <div className="space-y-2">
                <div className="text-sm text-red-700 dark:text-red-400 ml-6">
                  {status.error}
                </div>
                {status.error.includes('TLS handshake') && (
                  <div className="text-xs text-zinc-600 dark:text-zinc-400 ml-6 bg-zinc-50 dark:bg-zinc-900/50 p-3 rounded-sm border border-zinc-200 dark:border-zinc-800">
                    <strong>mTLS Setup:</strong>
                    <ul className="list-disc list-inside mt-1 space-y-1">
                      <li>macOS: Importera <code className="text-xs">certs/client.crt</code> till Keychain</li>
                      <li>Chrome/Edge: Settings → Certificates → Import</li>
                      <li>Se: <code className="text-xs">docs/MTLS_BROWSER_SETUP.md</code></li>
                    </ul>
                  </div>
                )}
                {import.meta.env.DEV && status.requestId && (
                  <div className="text-xs mt-1 ml-6 font-mono opacity-75 text-zinc-500">
                    Request ID: {status.requestId}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Transcripts List */}
      <div className="bg-white dark:bg-[#18181b] border border-zinc-200 dark:border-white/5 rounded-sm shadow-sm overflow-hidden">
        {/* Toolbar */}
        <div className="p-3 border-b border-zinc-100 dark:border-white/5 flex gap-2">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-2.5 top-2 text-zinc-400" size={16} />
            <input 
              type="text" 
              placeholder="Sök i arkivet..." 
              className="pl-9 pr-4 py-1.5 bg-zinc-50 dark:bg-white/5 border border-zinc-200 dark:border-white/10 rounded-sm text-sm w-full outline-none focus:border-zinc-400 dark:focus:border-zinc-600 transition-colors placeholder:text-zinc-400" 
            />
          </div>
        </div>

        {isLoading ? (
          <div className="p-8 text-center text-sm text-zinc-400">Laddar arkiv...</div>
        ) : displayTranscripts.length === 0 ? (
          <div className="p-8">
            <EmptyState 
              icon={Mic}
              title="Arkivet är tomt"
              description="Inga transkriptioner har sparats än. Ladda upp en ljudfil för att starta bearbetning."
            />
          </div>
        ) : (
          <table className="w-full text-left">
            <thead>
              <tr className="bg-zinc-50 dark:bg-black/20 text-xs font-bold text-zinc-500 dark:text-zinc-400 uppercase tracking-wider border-b border-zinc-200 dark:border-white/5">
                <th className="px-6 py-3 font-medium">Titel / Innehåll</th>
                <th className="px-6 py-3 font-medium">Datum</th>
                <th className="px-6 py-3 font-medium">Längd</th>
                <th className="px-6 py-3 font-medium text-right">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-100 dark:divide-white/5">
              {displayTranscripts.map((t) => (
                <tr key={t.id} className="hover:bg-zinc-50 dark:hover:bg-white/5 transition-colors cursor-pointer group">
                  <td className="px-6 py-4">
                    <div className="flex items-start gap-3">
                      <div className="mt-1 p-1.5 bg-zinc-100 dark:bg-zinc-800 text-zinc-500 rounded-sm">
                        <FileText size={16} />
                      </div>
                      <div>
                        <div className="text-sm font-medium text-zinc-900 dark:text-zinc-200 group-hover:text-zinc-900 dark:group-hover:text-white transition-colors">{t.title}</div>
                        <div className="text-xs text-zinc-500 mt-1 line-clamp-1 italic">"{t.snippet}"</div>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-sm text-zinc-500 font-mono">
                    {t.date}
                  </td>
                  <td className="px-6 py-4 text-sm text-zinc-500 font-mono">
                    {t.duration}
                  </td>
                  <td className="px-6 py-4 text-right">
                    <span className={`inline-flex items-center px-2 py-0.5 rounded-sm text-[10px] font-bold uppercase tracking-wide border ${
                      t.status === 'KLAR' 
                        ? 'bg-emerald-50 text-emerald-700 border-emerald-100 dark:bg-emerald-900/20 dark:text-emerald-400 dark:border-emerald-900' 
                        : 'bg-amber-50 text-amber-700 border-amber-100 dark:bg-amber-900/20 dark:text-amber-400 dark:border-amber-900'
                    }`}>
                      {t.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};

