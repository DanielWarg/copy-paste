import React, { useEffect } from 'react';
import { ShieldCheck } from 'lucide-react';

interface ToastProps {
  message: string;
  isVisible: boolean;
  onClose: () => void;
}

export const Toast: React.FC<ToastProps> = ({ message, isVisible, onClose }) => {
  useEffect(() => {
    if (isVisible) {
      const timer = setTimeout(onClose, 4000);
      return () => clearTimeout(timer);
    }
  }, [isVisible, onClose]);

  if (!isVisible) return null;

  return (
    <div className="fixed bottom-6 right-6 z-50 flex items-center gap-3 px-4 py-3 bg-zinc-900 dark:bg-zinc-800 text-white rounded-sm shadow-lg border border-zinc-700 animate-in slide-in-from-bottom-5 duration-300">
      <ShieldCheck size={18} className="text-emerald-400" />
      <span className="text-sm font-medium">{message}</span>
    </div>
  );
};