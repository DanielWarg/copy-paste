/**
 * Main App Component
 * 
 * UI Shell with module routing.
 * Default page: 'recorder' (will be implemented in Record module)
 */

import { useState, useEffect } from 'react';
import { Layout } from './components/layout/Layout';
import { Recorder } from './views/Recorder';
import { ProjectsOverview } from './views/ProjectsOverview';
import { ProjectView } from './views/Project';

const App: React.FC = () => {
  // Default to transcripts page (Projects Overview)
  const [page, setPage] = useState('transcripts');
  const [selectedProjectId, setSelectedProjectId] = useState<number | null>(null);
  const [darkMode, setDarkMode] = useState(true);

  // Initialize Theme
  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [darkMode]);

  const toggleTheme = () => setDarkMode(!darkMode);

  const handleProjectSelect = (projectId: number) => {
    setSelectedProjectId(projectId);
    setPage('project');
  };

  const handleCreateRecord = (projectId: number) => {
    setSelectedProjectId(projectId);
    setPage('recorder');
  };

  const renderContent = () => {
    switch (page) {
      case 'transcripts':
        return <ProjectsOverview onProjectSelect={handleProjectSelect} />;
      case 'project':
        if (selectedProjectId) {
          return (
            <ProjectView 
              projectId={selectedProjectId} 
              onCreateRecord={() => handleCreateRecord(selectedProjectId)}
            />
          );
        }
        return <ProjectsOverview onProjectSelect={handleProjectSelect} />;
      case 'recorder':
        return <Recorder projectId={selectedProjectId || undefined} />;
      case 'overview':
        return (
          <div className="flex flex-col items-center justify-center h-full text-zinc-400">
            <p className="text-lg font-serif">Översikt</p>
            <p className="text-sm mt-2">Kommer snart</p>
          </div>
        );
      case 'monitoring':
        return (
          <div className="flex flex-col items-center justify-center h-full text-zinc-400">
            <p className="text-lg font-serif">Bevakning</p>
            <p className="text-sm mt-2">Kommer snart</p>
          </div>
        );
      case 'flow':
        return (
          <div className="flex flex-col items-center justify-center h-full text-zinc-400">
            <p className="text-lg font-serif">Arbetsflöde</p>
            <p className="text-sm mt-2">Kommer snart</p>
          </div>
        );
      case 'sources':
        return (
          <div className="flex flex-col items-center justify-center h-full text-zinc-400">
            <p className="text-lg font-serif">Källor</p>
            <p className="text-sm mt-2">Kommer snart</p>
          </div>
        );
      case 'settings':
        return (
          <div className="flex flex-col items-center justify-center h-full text-zinc-400">
            <p className="text-lg font-serif">Inställningar</p>
            <p className="text-sm mt-2">Här kan redaktionen konfigurera sina lokala vyer.</p>
          </div>
        );
      default:
        return (
          <div className="flex flex-col items-center justify-center h-full text-zinc-400">
            <p className="text-lg font-serif">Okänd sida</p>
            <p className="text-sm mt-2">Navigera via menyn</p>
          </div>
        );
    }
  };

  return (
    <Layout
      darkMode={darkMode}
      toggleTheme={toggleTheme}
      currentPage={page}
      navigate={setPage}
    >
      {renderContent()}
    </Layout>
  );
};

export default App;

