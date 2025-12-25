/**
 * Project Detail View
 * 
 * Folder view showing project details and sections:
 * - Transkript (with CTA to create new record)
 * - Filer
 * - Export
 */

import { useState, useEffect } from 'react';
import { getProject, Project } from '../api/projects';
import { ApiError } from '../api/client';
import { Folder, FileText, File, Download, Loader2, AlertCircle, Plus } from 'lucide-react';

interface ProjectViewProps {
  projectId: number;
  onCreateRecord: () => void;
}

export function ProjectView({ projectId, onCreateRecord }: ProjectViewProps) {
  const [project, setProject] = useState<Project | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<ApiError | null>(null);

  useEffect(() => {
    loadProject();
  }, [projectId]);

  const loadProject = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const data = await getProject(projectId);
      setProject(data);
    } catch (err: any) {
      setError(err as ApiError);
    } finally {
      setLoading(false);
    }
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

  if (error) {
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

  return (
    <div className="max-w-5xl mx-auto">
      {/* Project Header */}
      <div className="bg-white dark:bg-zinc-800 p-6 rounded-sm shadow-sm border border-zinc-200 dark:border-zinc-700 mb-6">
        <div className="flex items-start gap-3 mb-4">
          <Folder size={24} className="text-zinc-500 dark:text-zinc-400 mt-1" />
          <div className="flex-1">
            <h2 className="text-xl font-serif font-bold text-zinc-900 dark:text-white mb-2">
              {project.name}
            </h2>
            <div className="flex items-center gap-4 text-sm text-zinc-500 dark:text-zinc-400">
              <span>ID: {project.id}</span>
              {project.started_working_at && (
                <span>
                  Start: {new Date(project.started_working_at).toLocaleDateString('sv-SE')}
                </span>
              )}
              {project.sensitivity === 'sensitive' && (
                <span className="px-2 py-0.5 bg-amber-100 dark:bg-amber-900/30 text-amber-800 dark:text-amber-400 rounded text-xs">
                  Känsligt projekt
                </span>
              )}
            </div>
          </div>
        </div>
      </div>

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
                <span>Skapa nytt transkript (record)</span>
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
          <div className="flex items-center gap-2 mb-4">
            <File size={20} className="text-zinc-500 dark:text-zinc-400" />
            <h3 className="text-lg font-semibold text-zinc-900 dark:text-white">
              Filer
            </h3>
            <span className="text-sm text-zinc-500 dark:text-zinc-400">
              ({project.files_count})
            </span>
          </div>
          
          {project.files_count === 0 ? (
            <div className="text-center py-8 text-zinc-500 dark:text-zinc-400">
              <File size={48} className="mx-auto mb-4 opacity-50" />
              <p className="text-sm">Inga filer än.</p>
            </div>
          ) : (
            <div className="text-sm text-zinc-600 dark:text-zinc-400">
              {project.files_count} fil{project.files_count !== 1 ? 'er' : ''} i projektet.
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

