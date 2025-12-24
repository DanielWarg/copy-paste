import React, { useState, useEffect } from 'react';
import { Layout } from './components/Layout';
import { Dashboard } from './views/Dashboard';
import { Console } from './views/Console';
import { Pipeline } from './views/Pipeline';
import { Transcripts } from './views/Transcripts';
import { Sources } from './views/Sources';

const App: React.FC = () => {
  const [page, setPage] = useState('overview');
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

  const renderContent = () => {
    switch (page) {
      case 'overview':
        return <Dashboard navigate={setPage} />;
      case 'monitoring':
        return <Console navigate={setPage} />;
      case 'flow':
        return <Pipeline navigate={setPage} />;
      case 'transcripts':
        return <Transcripts navigate={setPage} />;
      case 'sources':
        return <Sources navigate={setPage} />;
      default:
        // Hantera fallback för inställningar eller okända rutter
        if (page === 'settings') {
            return (
                <div className="flex flex-col items-center justify-center h-full text-zinc-400">
                    <p className="text-lg font-serif">Inställningar</p>
                    <p className="text-sm mt-2">Här kan redaktionen konfigurera sina lokala vyer.</p>
                </div>
            )
        }
        return <Dashboard navigate={setPage} />;
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