/**
 * Project Detail View
 * 
 * Folder view showing project details and sections:
 * - Redigera projekt (penna-ikon)
 * - Transkript (with CTA to create new record)
 * - Filer (upload + lista med checkboxes)
 * - Export (sammanställning)
 */

import { useState, useEffect, useRef } from 'react';
import { getProject, Project, updateProject, listProjectFiles, uploadProjectFile, ProjectFile } from '../api/projects';
import { ApiError } from '../api/client';
import { Folder, FileText, File, Download, Loader2, AlertCircle, Plus, Upload, Edit, CheckSquare, Square } from 'lucide-react';

interface ProjectViewProps {
  projectId: number;
  onCreateRecord: () => void;
}

export function ProjectView({ projectId, onCreateRecord }: ProjectViewProps) {
  const [project, setProject] = useState<Project | null>(null);
  const [files, setFiles] = useState<ProjectFile[]>([]);
  const [loading, setLoading] = useState(true);
  const [filesLoading, setFilesLoading] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);
  const [uploading, setUploading] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState<Set<number>>(new Set());
  const [editing, setEditing] = useState(false);
  const [editForm, setEditForm] = useState({
    name: '',
    start_date: '',
    due_date: '',
    sensitivity: 'standard' as 'standard' | 'sensitive',
  });
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    loadProject();
    loadFiles();
  }, [projectId]);

  const loadProject = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const data = await getProject(projectId);
      setProject(data);
      setEditForm({
        name: data.name,
        start_date: data.start_date || new Date().toISOString().split('T')[0],
        due_date: data.due_date || '',
        sensitivity: data.sensitivity,
      });
    } catch (err: any) {
      setError(err as ApiError);
    } finally {
      setLoading(false);
    }
  };

  const loadFiles = async () => {
    setFilesLoading(true);
    try {
      const response = await listProjectFiles(projectId);
      setFiles(response.items);
    } catch (err: any) {
      // Silently fail - files might not be available
      console.error('[Project] Failed to load files:', err);
    } finally {
      setFilesLoading(false);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (!selectedFile) return;

    // Validate file type
    const allowedExtensions = ['.txt', '.docx', '.pdf'];
    const fileName = selectedFile.name.toLowerCase();
    const isValid = allowedExtensions.some(ext => fileName.endsWith(ext));

    if (!isValid) {
      setError({
        code: 'validation_error',
        message: 'Endast .txt, .docx och .pdf filer är tillåtna',
        request_id: '',
      });
      return;
    }

    // Validate file size (25MB max)
    const maxSize = 25 * 1024 * 1024; // 25MB
    if (selectedFile.size > maxSize) {
      setError({
        code: 'validation_error',
        message: `Filen är för stor (max ${Math.round(maxSize / 1024 / 1024)}MB)`,
        request_id: '',
      });
      return;
    }

    handleUpload(selectedFile);
  };

  const handleUpload = async (file: File) => {
    setUploading(true);
    setError(null);

    try {
      await uploadProjectFile(projectId, file);
      // Reload files and project
      await loadFiles();
      await loadProject();
    } catch (err: any) {
      const apiError = err as ApiError;
      setError(apiError);
      console.error('[Project] Upload failed:', apiError.code, apiError.request_id);
    } finally {
      setUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const handleSaveEdit = async () => {
    if (!project) return;

    setUploading(true);
    setError(null);

    try {
      const updated = await updateProject(projectId, {
        name: editForm.name,
        start_date: editForm.start_date || undefined,
        due_date: editForm.due_date || undefined,
        sensitivity: editForm.sensitivity,
      });
      setProject(updated);
      setEditing(false);
    } catch (err: any) {
      const apiError = err as ApiError;
      setError(apiError);
    } finally {
      setUploading(false);
    }
  };

  const toggleFileSelection = (fileId: number) => {
    const newSelected = new Set(selectedFiles);
    if (newSelected.has(fileId)) {
      newSelected.delete(fileId);
    } else {
      newSelected.add(fileId);
    }
    setSelectedFiles(newSelected);
  };

  const isDueSoon = (dueDateStr: string | undefined) => {
    if (!dueDateStr) return false;
    const due = new Date(dueDateStr);
    const today = new Date();
    const daysUntilDue = Math.ceil((due.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));
    return daysUntilDue >= 0 && daysUntilDue <= 7; // Red if due within 7 days
  };

  if (loading) {
    return (
      <div className="max-w-5xl mx-auto">
        <div className="bg-white dark:bg-zinc-800 p-6 rounded-sm shadow-sm border border-zinc-200 dark:border-zinc-700">
          <div className="flex items-center gap-2 text-zinc-600 dark:text-zinc-400">
            <Loader2 size={20} className="animate-spin" />
            <span>Laddar projekt...</span>
          </div>
        </div>
      </div>
    );
  }

  if (error && !project) {
    return (
      <div className="max-w-5xl mx-auto">
        <div className="bg-white dark:bg-zinc-800 p-6 rounded-sm shadow-sm border border-zinc-200 dark:border-zinc-700">
          <div className="flex items-center gap-2 text-red-600 dark:text-red-500 mb-4">
            <AlertCircle size={20} />
            <span className="font-semibold">Ett fel uppstod</span>
          </div>
          <p className="text-sm text-zinc-600 dark:text-zinc-400 mb-4">
            {error.message || 'Kunde inte ladda projekt'}
          </p>
          {error.request_id && (
            <p className="text-xs text-zinc-500 dark:text-zinc-500">
              Request ID: {error.request_id}
            </p>
          )}
        </div>
      </div>
    );
  }

  if (!project) {
    return null;
  }

  const dueSoon = isDueSoon(project.due_date);

  return (
    <div className="max-w-5xl mx-auto">
      {/* Project Header */}
      <div className="bg-white dark:bg-zinc-800 p-6 rounded-sm shadow-sm border border-zinc-200 dark:border-zinc-700 mb-6">
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-start gap-3 flex-1">
            <Folder size={24} className="text-zinc-500 dark:text-zinc-400 mt-1" />
            <div className="flex-1">
              {editing ? (
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-zinc-900 dark:text-white mb-2">
                      Projektnamn *
                    </label>
                    <input
                      type="text"
                      value={editForm.name}
                      onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
                      className="w-full px-3 py-2 text-sm bg-zinc-100 dark:bg-zinc-700 border border-zinc-200 dark:border-zinc-600 rounded-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 text-zinc-900 dark:text-white"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-zinc-900 dark:text-white mb-2">
                      Startdatum
                    </label>
                    <input
                      type="date"
                      value={editForm.start_date}
                      onChange={(e) => setEditForm({ ...editForm, start_date: e.target.value })}
                      className="w-full px-3 py-2 text-sm bg-zinc-100 dark:bg-zinc-700 border border-zinc-200 dark:border-zinc-600 rounded-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 text-zinc-900 dark:text-white"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-zinc-900 dark:text-white mb-2">
                      Deadline
                    </label>
                    <input
                      type="date"
                      value={editForm.due_date}
                      onChange={(e) => setEditForm({ ...editForm, due_date: e.target.value })}
                      className={`w-full px-3 py-2 text-sm bg-zinc-100 dark:bg-zinc-700 border rounded-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 text-zinc-900 dark:text-white ${
                        dueSoon ? 'border-red-500 dark:border-red-600' : 'border-zinc-200 dark:border-zinc-600'
                      }`}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-zinc-900 dark:text-white mb-2">
                      Känslighet
                    </label>
                    <select
                      value={editForm.sensitivity}
                      onChange={(e) => setEditForm({ ...editForm, sensitivity: e.target.value as 'standard' | 'sensitive' })}
                      className="w-full px-3 py-2 text-sm bg-zinc-100 dark:bg-zinc-700 border border-zinc-200 dark:border-zinc-600 rounded-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 text-zinc-900 dark:text-white"
                    >
                      <option value="standard">Offentligt</option>
                      <option value="sensitive">Klassificerat</option>
                    </select>
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={handleSaveEdit}
                      disabled={!editForm.name.trim() || uploading}
                      className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed text-white text-sm font-medium rounded-sm shadow-sm transition-colors"
                    >
                      {uploading ? 'Sparar...' : 'Spara'}
                    </button>
                    <button
                      onClick={() => {
                        setEditing(false);
                        setEditForm({
                          name: project.name,
                          start_date: project.start_date || new Date().toISOString().split('T')[0],
                          due_date: project.due_date || '',
                          sensitivity: project.sensitivity,
                        });
                      }}
                      className="px-4 py-2 bg-zinc-200 dark:bg-zinc-700 hover:bg-zinc-300 dark:hover:bg-zinc-600 text-zinc-900 dark:text-white text-sm font-medium rounded-sm transition-colors"
                    >
                      Avbryt
                    </button>
                  </div>
                </div>
              ) : (
                <>
                  <h2 className="text-xl font-serif font-bold text-zinc-900 dark:text-white mb-2">
                    {project.name}
                  </h2>
                  <div className="flex items-center gap-4 text-sm text-zinc-500 dark:text-zinc-400">
                    <span>ID: {project.id}</span>
                    {project.start_date && (
                      <span>
                        Start: {new Date(project.start_date).toLocaleDateString('sv-SE')}
                      </span>
                    )}
                    {project.due_date && (
                      <span className={dueSoon ? 'text-red-600 dark:text-red-400 font-semibold' : ''}>
                        Deadline: {new Date(project.due_date).toLocaleDateString('sv-SE')}
                        {dueSoon && ' ⚠️'}
                      </span>
                    )}
                    <span className={`px-2 py-0.5 rounded text-xs ${
                      project.sensitivity === 'sensitive' 
                        ? 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300' 
                        : 'bg-zinc-100 dark:bg-zinc-700 text-zinc-700 dark:text-zinc-300'
                    }`}>
                      {project.sensitivity === 'sensitive' ? 'Klassificerat' : 'Offentligt'}
                    </span>
                  </div>
                </>
              )}
            </div>
          </div>
          {!editing && (
            <button
              onClick={() => setEditing(true)}
              className="flex items-center gap-2 px-3 py-2 bg-zinc-100 dark:bg-zinc-700 hover:bg-zinc-200 dark:hover:bg-zinc-600 text-zinc-900 dark:text-white text-sm font-medium rounded-sm transition-colors"
            >
              <Edit size={16} />
              <span>Redigera</span>
            </button>
          )}
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-red-900/20 border border-red-800 text-red-300 p-4 rounded-sm mb-6 flex items-center gap-3">
          <AlertCircle size={20} />
          <div>
            <p className="font-semibold">Ett fel uppstod: {error.message}</p>
            {error.request_id && (
              <p className="text-sm">Request ID: {error.request_id}</p>
            )}
          </div>
        </div>
      )}

      {/* Sections */}
      <div className="space-y-6">
        {/* Transkript Section */}
        <div className="bg-white dark:bg-zinc-800 p-6 rounded-sm shadow-sm border border-zinc-200 dark:border-zinc-700">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <FileText size={20} className="text-zinc-500 dark:text-zinc-400" />
              <h3 className="text-lg font-semibold text-zinc-900 dark:text-white">
                Transkript
              </h3>
              <span className="text-sm text-zinc-500 dark:text-zinc-400">
                ({project.transcripts_count})
              </span>
            </div>
            <button
              onClick={onCreateRecord}
              className="flex items-center gap-2 px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-medium rounded-sm shadow-sm transition-colors"
            >
              <Plus size={16} />
              <span>Skapa nytt transkript</span>
            </button>
          </div>
          
          {project.transcripts_count === 0 ? (
            <div className="text-center py-8 text-zinc-500 dark:text-zinc-400">
              <FileText size={48} className="mx-auto mb-4 opacity-50" />
              <p className="text-sm mb-4">Inga transkriptioner än.</p>
              <button
                onClick={onCreateRecord}
                className="inline-flex items-center gap-2 px-4 py-2 bg-zinc-900 dark:bg-white dark:text-black text-white text-sm font-medium rounded-sm shadow-sm hover:opacity-90 transition-opacity"
              >
                <Plus size={16} />
                <span>Skapa nytt transkript</span>
              </button>
            </div>
          ) : (
            <div className="text-sm text-zinc-600 dark:text-zinc-400">
              {project.transcripts_count} transkription{project.transcripts_count !== 1 ? 'er' : ''} i projektet.
            </div>
          )}
        </div>

        {/* Filer Section */}
        <div className="bg-white dark:bg-zinc-800 p-6 rounded-sm shadow-sm border border-zinc-200 dark:border-zinc-700">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <File size={20} className="text-zinc-500 dark:text-zinc-400" />
              <h3 className="text-lg font-semibold text-zinc-900 dark:text-white">
                Filer
              </h3>
              <span className="text-sm text-zinc-500 dark:text-zinc-400">
                ({files.length})
              </span>
            </div>
            <div className="flex items-center gap-2">
              <input
                ref={fileInputRef}
                type="file"
                accept=".txt,.docx,.pdf"
                onChange={handleFileSelect}
                className="hidden"
                id="project-file-upload"
                disabled={uploading}
              />
              <label
                htmlFor="project-file-upload"
                className={`inline-flex items-center gap-2 px-4 py-2 bg-zinc-900 dark:bg-white dark:text-black text-white text-sm font-medium rounded-sm shadow-sm transition-opacity cursor-pointer ${
                  uploading ? 'opacity-50 cursor-not-allowed' : 'hover:opacity-90'
                }`}
              >
                {uploading ? (
                  <>
                    <Loader2 size={16} className="animate-spin" />
                    <span>Laddar upp...</span>
                  </>
                ) : (
                  <>
                    <Upload size={16} />
                    <span>Ladda upp fil</span>
                  </>
                )}
              </label>
            </div>
          </div>
          
          {filesLoading ? (
            <div className="flex items-center gap-2 text-zinc-600 dark:text-zinc-400 py-4">
              <Loader2 size={16} className="animate-spin" />
              <span className="text-sm">Laddar filer...</span>
            </div>
          ) : files.length === 0 ? (
            <div className="text-center py-8 text-zinc-500 dark:text-zinc-400">
              <File size={48} className="mx-auto mb-4 opacity-50" />
              <p className="text-sm">Inga filer än.</p>
              <p className="text-xs mt-2">Ladda upp .txt, .docx eller .pdf filer (max 25MB)</p>
            </div>
          ) : (
            <div className="space-y-2">
              {files.map((file) => (
                <div
                  key={file.id}
                  className="flex items-center gap-3 p-3 bg-zinc-50 dark:bg-zinc-900 rounded-sm border border-zinc-200 dark:border-zinc-700 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors"
                >
                  <button
                    onClick={() => toggleFileSelection(file.id)}
                    className="flex items-center justify-center w-5 h-5 text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-200"
                  >
                    {selectedFiles.has(file.id) ? (
                      <CheckSquare size={18} className="text-blue-600 dark:text-blue-400" />
                    ) : (
                      <Square size={18} />
                    )}
                  </button>
                  <File size={16} className="text-zinc-500 dark:text-zinc-400" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-zinc-900 dark:text-white truncate">
                      {file.original_filename}
                    </p>
                    <p className="text-xs text-zinc-500 dark:text-zinc-400">
                      {(file.size_bytes / 1024).toFixed(1)} KB • {file.mime_type} • {new Date(file.created_at).toLocaleDateString('sv-SE')}
                    </p>
                  </div>
                </div>
              ))}
              {selectedFiles.size > 0 && (
                <div className="mt-4 pt-4 border-t border-zinc-200 dark:border-zinc-700">
                  <button
                    disabled
                    className="px-4 py-2 bg-zinc-200 dark:bg-zinc-700 text-zinc-500 dark:text-zinc-400 text-sm font-medium rounded-sm cursor-not-allowed"
                  >
                    Sammanställ valda filer ({selectedFiles.size}) - Kommer snart
                  </button>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Export Section */}
        <div className="bg-white dark:bg-zinc-800 p-6 rounded-sm shadow-sm border border-zinc-200 dark:border-zinc-700">
          <div className="flex items-center gap-2 mb-4">
            <Download size={20} className="text-zinc-500 dark:text-zinc-400" />
            <h3 className="text-lg font-semibold text-zinc-900 dark:text-white">
              Export
            </h3>
          </div>
          
          <div className="text-center py-8 text-zinc-500 dark:text-zinc-400">
            <Download size={48} className="mx-auto mb-4 opacity-50" />
            <p className="text-sm">Export kommer snart.</p>
          </div>
        </div>

        {/* Data Protection Info */}
        <div className="mt-6 bg-zinc-50 dark:bg-zinc-900 p-4 rounded-sm border border-zinc-200 dark:border-zinc-700">
          <h4 className="text-sm font-semibold text-zinc-900 dark:text-white mb-2">Dataskydd</h4>
          <ul className="text-xs text-zinc-600 dark:text-zinc-400 space-y-1">
            <li>• Filer lagras krypterat (Fernet) och sparas utan originalfilnamn</li>
            <li>• Metadata (titel, datum) lagras i databasen</li>
            <li>• Innehåll loggas aldrig. Request ID används för felsökning</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
