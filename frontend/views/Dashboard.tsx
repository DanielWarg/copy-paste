import React, { useEffect, useState } from 'react';
import { apiClient } from '../apiClient';
import { NewsEvent, EventStatus } from '../types';
import { ArrowRight } from 'lucide-react';
import { StatusBadge } from '../components/ui/Badge';

interface DashboardProps {
    navigate: (page: string) => void;
}

const StatCard = ({ label, value, subtext }: { label: string, value: string, subtext?: string }) => (
    <div className="bg-white dark:bg-[#18181b] border border-zinc-200 dark:border-white/5 p-5 rounded-sm">
        <div className="text-xs font-medium text-zinc-500 dark:text-zinc-400 uppercase tracking-wider mb-2">{label}</div>
        <div className="text-2xl font-bold text-zinc-900 dark:text-white font-mono tracking-tight">{value}</div>
        {subtext && <div className="text-xs text-zinc-400 mt-1">{subtext}</div>}
    </div>
)

export const Dashboard: React.FC<DashboardProps> = ({ navigate }) => {
    const [events, setEvents] = useState<NewsEvent[]>([]);

    useEffect(() => {
        apiClient.getEvents().then(setEvents);
    }, []);

    const incomingCount = events.filter(e => e.status === EventStatus.INCOMING).length;
    const activeCount = events.filter(e => [EventStatus.TRIAGED, EventStatus.REVIEW].includes(e.status)).length;

    return (
        <div className="space-y-8 max-w-5xl mx-auto">
            <div className="mb-8">
                <h1 className="text-2xl font-serif font-bold text-zinc-900 dark:text-white mb-2">Redaktionell Översikt</h1>
                <p className="text-zinc-500 dark:text-zinc-400">Systemstatus normal. Väntar på nya inkommande signaler.</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <StatCard label="Nytt i bevakning" value={incomingCount.toString()} subtext="Senaste timmen" />
                <StatCard label="Pågående arbeten" value={activeCount.toString()} subtext="I arbetsflödet" />
                <StatCard label="Publicerat idag" value="14" subtext="Godkända artiklar" />
            </div>

            {/* Quick Actions / Shortcuts */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="bg-white dark:bg-[#18181b] border border-zinc-200 dark:border-white/5 rounded-sm overflow-hidden">
                    <div className="px-5 py-4 border-b border-zinc-100 dark:border-white/5 flex justify-between items-center">
                        <h3 className="font-semibold text-zinc-900 dark:text-white">Senaste Händelser</h3>
                        <button onClick={() => navigate('monitoring')} className="text-xs font-medium text-zinc-500 hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-white flex items-center gap-1 transition-colors">
                            Gå till bevakning <ArrowRight size={12} />
                        </button>
                    </div>
                    <div className="divide-y divide-zinc-100 dark:divide-white/5">
                        {events.length === 0 ? (
                            <div className="p-6 text-center text-sm text-zinc-400">Inga händelser att visa.</div>
                        ) : events.slice(0, 3).map(e => (
                            <div key={e.id} onClick={() => navigate('flow')} className="px-5 py-3 hover:bg-zinc-50 dark:hover:bg-white/5 cursor-pointer group transition-colors">
                                <div className="flex justify-between items-start mb-1">
                                    <span className="text-[10px] font-mono text-zinc-400">{e.timestamp.substring(11, 16)}</span>
                                    <StatusBadge status={e.status} />
                                </div>
                                <div className="text-sm font-medium text-zinc-900 dark:text-zinc-200 group-hover:text-zinc-900 dark:group-hover:text-white truncate transition-colors">
                                    {e.title}
                                </div>
                                <div className="text-xs text-zinc-500 mt-1">{e.source}</div>
                            </div>
                        ))}
                    </div>
                </div>

                <div className="bg-zinc-100 dark:bg-white/5 border border-zinc-200 dark:border-white/5 rounded-sm p-6 flex flex-col justify-center items-start">
                    <h3 className="font-semibold text-zinc-900 dark:text-white mb-2">Skapa nytt utkast</h3>
                    <p className="text-sm text-zinc-500 dark:text-zinc-400 mb-6 max-w-xs leading-relaxed">
                        Starta ett nytt ärende manuellt genom att klistra in text eller ladda upp dokument.
                    </p>
                    <button onClick={() => navigate('flow')} className="px-4 py-2 bg-zinc-900 dark:bg-white text-white dark:text-black font-medium text-sm rounded-sm shadow-sm hover:opacity-90 transition-opacity w-full sm:w-auto">
                        + Skapa händelse
                    </button>
                </div>
            </div>
        </div>
    );
};