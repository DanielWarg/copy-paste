import React from 'react';
import { LucideIcon } from 'lucide-react';

interface EmptyStateProps {
  icon: LucideIcon;
  title: string;
  description: string;
  actionLabel?: string;
  onAction?: () => void;
}

export const EmptyState: React.FC<EmptyStateProps> = ({ 
  icon: Icon, 
  title, 
  description, 
  actionLabel, 
  onAction 
}) => {
  return (
    <div className="flex flex-col items-center justify-center h-64 text-center p-8 border border-dashed border-zinc-200 dark:border-zinc-800 rounded-sm bg-zinc-50/50 dark:bg-zinc-900/50">
      <div className="p-3 bg-zinc-100 dark:bg-zinc-800 rounded-full mb-4 text-zinc-400">
        <Icon size={24} strokeWidth={1.5} />
      </div>
      <h3 className="text-sm font-bold text-zinc-900 dark:text-white uppercase tracking-wide mb-2">
        {title}
      </h3>
      <p className="text-sm text-zinc-500 dark:text-zinc-400 max-w-sm mb-6 leading-relaxed">
        {description}
      </p>
      {actionLabel && onAction && (
        <button 
          onClick={onAction}
          className="px-4 py-2 bg-white dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 text-zinc-900 dark:text-zinc-100 text-sm font-medium rounded-sm shadow-sm hover:bg-zinc-50 dark:hover:bg-zinc-700 transition-colors"
        >
          {actionLabel}
        </button>
      )}
    </div>
  );
};