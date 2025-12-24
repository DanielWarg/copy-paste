import React, { ReactNode } from 'react';
import { MODULES, APP_NAME } from '../constants';
import { Menu, Sun, Moon, Shield } from 'lucide-react';

interface LayoutProps {
  children: ReactNode;
  darkMode: boolean;
  toggleTheme: () => void;
  currentPage: string;
  navigate: (page: string) => void;
}

const NavItem = ({ module, active, onClick }: { module: any, active: boolean, onClick: () => void }) => {
  const Icon = module.icon;
  return (
    <button
      onClick={onClick}
      className={`w-full flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-all duration-150 mb-0.5
      ${active 
        ? 'bg-zinc-100 text-zinc-900 dark:bg-white/10 dark:text-white' 
        : 'text-zinc-500 dark:text-zinc-400 hover:bg-zinc-50 dark:hover:bg-white/5 hover:text-zinc-900 dark:hover:text-zinc-200'
      }`}
    >
      <Icon size={16} strokeWidth={2} className={active ? 'text-zinc-900 dark:text-white' : 'text-zinc-400 dark:text-zinc-500'} />
      <span className="tracking-tight">{module.title}</span>
    </button>
  );
};

export const Layout: React.FC<LayoutProps> = ({ children, darkMode, toggleTheme, currentPage, navigate }) => {
  return (
    <div className={`flex h-screen w-full overflow-hidden bg-zinc-50 dark:bg-[#09090b]`}>
      
      {/* Sidebar - Stramare redaktionell stil */}
      <aside className="hidden md:flex flex-col w-64 border-r border-zinc-200 dark:border-white/5 bg-white dark:bg-[#09090b]">
        <div className="p-5 h-16 flex items-center border-b border-zinc-100 dark:border-white/5">
            <div className="flex items-center gap-2 text-zinc-900 dark:text-white font-bold text-sm tracking-wider uppercase">
                <div className="w-2 h-2 bg-red-600 rounded-full animate-pulse"></div>
                <span>{APP_NAME}</span>
            </div>
        </div>
        
        <div className="flex-1 overflow-y-auto py-6 px-4">
          <div className="space-y-1">
            <div className="text-[10px] font-bold text-zinc-400 dark:text-zinc-600 uppercase tracking-widest mb-3 px-3">Produktion</div>
            {MODULES.slice(0, 3).map(m => (
                <NavItem key={m.id} module={m} active={currentPage.startsWith(m.id)} onClick={() => navigate(m.id)} />
            ))}
          </div>

          <div className="space-y-1 mt-8">
            <div className="text-[10px] font-bold text-zinc-400 dark:text-zinc-600 uppercase tracking-widest mb-3 px-3">Bibliotek & Data</div>
            {MODULES.slice(3, 5).map(m => (
                <NavItem key={m.id} module={m} active={currentPage === m.id} onClick={() => navigate(m.id)} />
            ))}
          </div>

          <div className="space-y-1 mt-8">
             <NavItem module={MODULES[5]} active={currentPage === 'settings'} onClick={() => navigate('settings')} />
          </div>
        </div>

        {/* User Profile - Minimal */}
        <div className="p-4 border-t border-zinc-100 dark:border-white/5">
            <div className="flex items-center gap-3 opacity-60 hover:opacity-100 transition-opacity cursor-pointer">
                <div className="w-6 h-6 rounded bg-zinc-200 dark:bg-zinc-800 flex items-center justify-center text-[10px] font-bold text-zinc-600 dark:text-zinc-400">
                    JD
                </div>
                <div className="text-xs font-medium text-zinc-600 dark:text-zinc-400">Redaktör</div>
            </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col min-w-0 bg-white dark:bg-[#09090b]">
        {/* Topbar - Minimal */}
        <header className="h-14 flex items-center justify-between px-6 border-b border-zinc-200 dark:border-white/5 bg-white dark:bg-[#09090b]">
          <div className="flex items-center gap-4">
            <button className="md:hidden text-zinc-500">
                <Menu size={20} />
            </button>
            <div className="text-sm font-medium text-zinc-400 dark:text-zinc-600 hidden sm:block">
                {new Date().toLocaleDateString('sv-SE', { weekday: 'long', day: 'numeric', month: 'long' })}
            </div>
          </div>

          <div className="flex items-center gap-4">
             <button 
                onClick={toggleTheme}
                className="text-zinc-400 hover:text-zinc-900 dark:hover:text-white transition-colors"
             >
                {darkMode ? <Sun size={18} /> : <Moon size={18} />}
             </button>
          </div>
        </header>

        <div className="flex-1 overflow-auto bg-zinc-50/50 dark:bg-black/20 p-6">
          {children}
        </div>
      </main>
    </div>
  );
};