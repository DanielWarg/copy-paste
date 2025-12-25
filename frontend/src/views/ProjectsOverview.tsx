/**
 * Projects Overview View
 * 
 * First view when clicking "Transkriptioner" in navigation.
 * Shows project list and create project button.
 */

import { useState, useEffect } from 'react';
import { listProjects, createProject, Project } from '../api/projects';
import { ApiError } from '../api/client';
import { FolderPlus, Folder, Loader2, AlertCircle, Database } from 'lucide-react';

export function ProjectsOverview({ 
  onProjectSelect 
}: { 
  onProjectSelect?: (projectId: number) => void;
}) {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<ApiError | null>(null);
  const [dbError, setDbError] = useState(false);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [creating, setCreating] = useState(false);
  
  // Create form state
  const [projectName, setProjectName] = useState('');
  const [startDate, setStartDate] = useState(new Date().toISOString().split('T')[0]);
  const [dueDate, setDueDate] = useState('');
  const [sensitivity, setSensitivity] = useState<'standard' | 'sensitive'>('standard');

  useEffect(() => {
    loadProjects();
  }, []);

  const loadProjects = async () => {
    setLoading(true);
    setError(null);
    setDbError(false);
    
    try {
      const response = await listProjects();
      setProjects(response.items);
    } catch (err: any) {
      const apiError = err as ApiError;
      setError(apiError);
      
      // Check if it's a DB error
      if (apiError.code === 'db_uninitialized' || apiError.code === 'db_down' || apiError.code === 503) {
        setDbError(true);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleCreateProject = async () => {
    if (!projectName.trim()) return;

    setCreating(true);
    try {
      const newProject = await createProject({
        name: projectName.trim(),
        start_date: startDate,
        due_date: dueDate || undefined,
        sensitivity: sensitivity,
      });
      
      setShowCreateForm(false);
      setProjectName('');
      setStartDate(new Date().toISOString().split('T')[0]);
      setDueDate('');
      setSensitivity('standard');
      
      // Navigate to new project
      if (onProjectSelect) {
        onProjectSelect(newProject.id);
      }
    } catch (err: any) {
      setError(err as ApiError);
    } finally {
      setCreating(false);
    }
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
      <div className="p-6">
        <div className="flex items-center justify-center h-64 text-zinc-500 dark:text-zinc-400">
          <Loader2 size={24} className="animate-spin mr-2" />
          <span>Laddar projekt...</span>
        </div>
      </div>
    );
  }

  if (dbError) {
    return (
      <div className="p-6">
        <div className="bg-red-900/20 border border-red-800 text-red-300 p-4 rounded-sm flex items-center gap-3">
          <Database size={20} />
          <div>
            <p className="font-semibold">Databasfel: Projekt kräver databas</p>
            <p className="text-sm">
              Backend rapporterar att databasen inte är tillgänglig eller initierad.
              <br />
              Kontrollera backend-loggar. Request ID: {error?.request_id || 'N/A'}
            </p>
          </div>
        </div>
      </div>
    );
  }

  if (error && !dbError) {
    return (
      <div className="p-6">
        <div className="bg-red-900/20 border border-red-800 text-red-300 p-4 rounded-sm flex items-center gap-3">
          <AlertCircle size={20} />
          <div>
            <p className="font-semibold">Ett fel uppstod: {error.message}</p>
            <p className="text-sm">Request ID: {error.request_id || 'N/A'}</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="max-w-7xl mx-auto">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-serif font-bold text-zinc-900 dark:text-white">
            Dina Projekt
          </h2>
          <button
            onClick={() => setShowCreateForm(true)}
            className="flex items-center gap-2 px-4 py-2 bg-zinc-900 dark:bg-white dark:text-black text-white text-sm font-medium rounded-sm shadow-sm hover:opacity-90 transition-opacity"
          >
            <FolderPlus size={16} />
            <span>Nytt projekt</span>
          </button>
        </div>

        {projects.length === 0 ? (
          <div className="text-center py-12 text-zinc-500 dark:text-zinc-400">
            <Folder size={48} className="mx-auto mb-4 opacity-50" />
            <p className="text-lg font-semibold">Inga projekt hittades</p>
            <p className="text-sm mt-2">Skapa ditt första projekt för att organisera transkriptioner.</p>
            <button
              onClick={() => setShowCreateForm(true)}
              className="mt-6 flex items-center gap-2 px-4 py-2 bg-zinc-900 dark:bg-white dark:text-black text-white text-sm font-medium rounded-sm shadow-sm hover:opacity-90 transition-opacity mx-auto"
            >
              <FolderPlus size={16} />
              <span>Nytt projekt</span>
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {projects.map((project) => {
              const dueSoon = isDueSoon((project as any).due_date);
              return (
                <div
                  key={project.id}
                  onClick={() => onProjectSelect?.(project.id)}
                  className="bg-white dark:bg-zinc-800 p-4 rounded-sm shadow-sm border border-zinc-200 dark:border-zinc-700 cursor-pointer hover:border-blue-500 dark:hover:border-blue-400 transition-colors"
                >
                  <div className="flex items-center justify-between mb-2">
                    <Folder size={18} className="text-zinc-500" />
                    <span className={`text-xs px-2 py-1 rounded-sm ${
                      project.sensitivity === 'sensitive' 
                        ? 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300' 
                        : 'bg-zinc-100 dark:bg-zinc-700 text-zinc-700 dark:text-zinc-300'
                    }`}>
                      {project.sensitivity === 'sensitive' ? 'Klassificerat' : 'Offentligt'}
                    </span>
                  </div>
                  <h3 className="font-semibold text-zinc-900 dark:text-white mb-2">{project.name}</h3>
                  <div className="text-xs text-zinc-500 dark:text-zinc-400 space-y-1">
                    <p>Start: {project.started_working_at ? new Date(project.started_working_at).toLocaleDateString() : 'Ej startat'}</p>
                    {(project as any).due_date && (
                      <p className={dueSoon ? 'text-red-600 dark:text-red-400 font-semibold' : ''}>
                        Deadline: {new Date((project as any).due_date).toLocaleDateString()}
                        {dueSoon && ' ⚠️'}
                      </p>
                    )}
                    <p>Transkript: {project.transcripts_count} | Filer: {project.files_count}</p>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* Create Project Modal */}
        {showCreateForm && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <div className="bg-white dark:bg-zinc-800 p-6 rounded-sm shadow-lg w-full max-w-md">
              <h3 className="text-lg font-semibold text-zinc-900 dark:text-white mb-4">Skapa nytt projekt</h3>
              
              <div className="space-y-4">
                <div>
                  <label htmlFor="projectName" className="block text-sm font-medium text-zinc-900 dark:text-white mb-2">
                    Projektnamn *
                  </label>
                  <input
                    type="text"
                    id="projectName"
                    value={projectName}
                    onChange={(e) => setProjectName(e.target.value)}
                    className="w-full px-3 py-2 text-sm bg-zinc-100 dark:bg-zinc-700 border border-zinc-200 dark:border-zinc-600 rounded-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 text-zinc-900 dark:text-white"
                    placeholder="T.ex. Intervju med Anna Svensson"
                  />
                </div>

                <div>
                  <label htmlFor="startDate" className="block text-sm font-medium text-zinc-900 dark:text-white mb-2">
                    Startdatum
                  </label>
                  <input
                    type="date"
                    id="startDate"
                    value={startDate}
                    onChange={(e) => setStartDate(e.target.value)}
                    className="w-full px-3 py-2 text-sm bg-zinc-100 dark:bg-zinc-700 border border-zinc-200 dark:border-zinc-600 rounded-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 text-zinc-900 dark:text-white"
                  />
                </div>

                <div>
                  <label htmlFor="dueDate" className="block text-sm font-medium text-zinc-900 dark:text-white mb-2">
                    Deadline (valfritt)
                  </label>
                  <input
                    type="date"
                    id="dueDate"
                    value={dueDate}
                    onChange={(e) => setDueDate(e.target.value)}
                    className="w-full px-3 py-2 text-sm bg-zinc-100 dark:bg-zinc-700 border border-zinc-200 dark:border-zinc-600 rounded-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 text-zinc-900 dark:text-white"
                  />
                </div>

                <div>
                  <label htmlFor="sensitivity" className="block text-sm font-medium text-zinc-900 dark:text-white mb-2">
                    Känslighet
                  </label>
                  <select
                    id="sensitivity"
                    value={sensitivity}
                    onChange={(e) => setSensitivity(e.target.value as 'standard' | 'sensitive')}
                    className="w-full px-3 py-2 text-sm bg-zinc-100 dark:bg-zinc-700 border border-zinc-200 dark:border-zinc-600 rounded-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 text-zinc-900 dark:text-white"
                  >
                    <option value="standard">Offentligt</option>
                    <option value="sensitive">Klassificerat</option>
                  </select>
                  <p className="text-xs text-zinc-500 dark:text-zinc-400 mt-1">
                    Klassificerade projekt har kortare retentiontid och striktare åtkomstkontroll.
                  </p>
                </div>
              </div>

              <div className="flex justify-end gap-2 mt-6">
                <button
                  onClick={() => {
                    setShowCreateForm(false);
                    setProjectName('');
                    setStartDate(new Date().toISOString().split('T')[0]);
                    setDueDate('');
                    setSensitivity('standard');
                  }}
                  className="px-4 py-2 text-sm font-medium text-zinc-700 dark:text-zinc-300 rounded-sm hover:bg-zinc-100 dark:hover:bg-zinc-700 transition-colors"
                >
                  Avbryt
                </button>
                <button
                  onClick={handleCreateProject}
                  disabled={!projectName.trim() || creating}
                  className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed text-white text-sm font-medium rounded-sm shadow-sm transition-colors"
                >
                  {creating ? 'Skapar...' : 'Skapa projekt'}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

