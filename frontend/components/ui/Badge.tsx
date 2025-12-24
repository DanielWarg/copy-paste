import React from 'react';
import { EventStatus } from '../../types';
import { Circle, Clock, Eye, CheckCircle2 } from 'lucide-react';

export const StatusBadge = ({ status }: { status: EventStatus | string }) => {
  
  // Mapping types to human editorial terms and visual configs
  const config = {
    [EventStatus.INCOMING]: {
      label: 'Ny',
      icon: Circle,
      style: 'bg-zinc-100 text-zinc-700 border-zinc-200 dark:bg-zinc-800 dark:text-zinc-300 dark:border-zinc-700',
      iconStyle: 'fill-zinc-400 text-zinc-400'
    },
    [EventStatus.TRIAGED]: {
      label: 'Pågår',
      icon: Clock,
      style: 'bg-zinc-100 text-zinc-900 border-zinc-300 dark:bg-zinc-800 dark:text-zinc-100 dark:border-zinc-600',
      iconStyle: 'text-zinc-600 dark:text-zinc-400'
    },
    [EventStatus.REVIEW]: {
      label: 'Kräver granskning',
      icon: Eye,
      style: 'bg-amber-50 text-amber-800 border-amber-200 dark:bg-amber-900/20 dark:text-amber-200 dark:border-amber-800',
      iconStyle: 'text-amber-600 dark:text-amber-400'
    },
    [EventStatus.PUBLISHED]: {
      label: 'Klar',
      icon: CheckCircle2,
      style: 'bg-emerald-50 text-emerald-800 border-emerald-200 dark:bg-emerald-900/20 dark:text-emerald-300 dark:border-emerald-800',
      iconStyle: 'text-emerald-600 dark:text-emerald-500'
    },
  };

  // Fallback configuration
  const currentConfig = config[status as EventStatus] || {
    label: status,
    icon: Circle,
    style: 'bg-zinc-50 text-zinc-500 border-zinc-200',
    iconStyle: 'text-zinc-400'
  };

  const Icon = currentConfig.icon;

  return (
    <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-sm text-[10px] font-bold uppercase tracking-wider border ${currentConfig.style}`}>
      <Icon size={10} className={currentConfig.iconStyle} />
      {currentConfig.label}
    </span>
  );
};

export const ScoreBadge = ({ score }: { score: number }) => {
  let colorClass = 'text-zinc-400 border-zinc-200 dark:border-zinc-700';
  if (score >= 80) colorClass = 'text-emerald-700 dark:text-emerald-400 border-emerald-200 dark:border-emerald-900 bg-emerald-50 dark:bg-emerald-900/10';
  else if (score >= 50) colorClass = 'text-amber-700 dark:text-amber-400 border-amber-200 dark:border-amber-900 bg-amber-50 dark:bg-amber-900/10';
  
  return (
    <div className={`flex items-center justify-center w-8 h-8 rounded-full border text-xs font-bold font-mono ${colorClass}`} title="Nyhetsvärde (0-100)">
      {score}
    </div>
  );
};