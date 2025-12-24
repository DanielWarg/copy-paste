import React, { useEffect, useState } from 'react';
import { apiClient } from '../apiClient';
import { NewsEvent } from '../types';
import { ScoreBadge, StatusBadge } from '../components/ui/Badge';
import { EmptyState } from '../components/ui/EmptyState';
import { Search, Filter, RefreshCw, Inbox } from 'lucide-react';

interface ConsoleProps {
    navigate: (page: string) => void;
}

const ListItem = ({ event, onClick }: { event: NewsEvent, onClick: () => void }) => (
    <div onClick={onClick} className="grid grid-cols-12 gap-4 px-4 py-3 border-b border-zinc-100 dark:border-white/5 hover:bg-zinc-50 dark:hover:bg-white/5 cursor-pointer transition-colors items-center group">
        <div className="col-span-1 text-xs font-mono text-zinc-400">
            {new Date(event.timestamp).toLocaleTimeString('sv-SE', {hour: '2-digit', minute:'2-digit'})}
        </div>
        <div className="col-span-1">
            <ScoreBadge score={event.score} />
        </div>
        <div className="col-span-6">
            <h4 className="text-sm font-medium text-zinc-900 dark:text-zinc-200 group-hover:text-zinc-900 dark:group-hover:text-white truncate">
                {event.title}
            </h4>
            <div className="text-xs text-zinc-500 dark:text-zinc-500 truncate mt-0.5">
                {event.summary}
            </div>
        </div>
        <div className="col-span-2 text-xs text-zinc-500 font-medium">
            {event.source}
        </div>
        <div className="col-span-2 text-right">
            <StatusBadge status={event.status} />
        </div>
    </div>
)

export const Console: React.FC<ConsoleProps> = ({ navigate }) => {
    const [events, setEvents] = useState<NewsEvent[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    
    useEffect(() => {
        setIsLoading(true);
        apiClient.getEvents().then(data => {
            setEvents(data);
            setIsLoading(false);
        });
    }, []);

    return (
        <div className="flex flex-col h-full max-w-6xl mx-auto">
            <div className="flex items-center justify-between mb-6">
                 <div>
                    <h2 className="text-xl font-serif font-bold text-zinc-900 dark:text-white">Bevakning</h2>
                    <p className="text-sm text-zinc-500 dark:text-zinc-400">Inkommande signaler från aktiva källor.</p>
                 </div>
                 
                 <div className="flex gap-2">
                     <div className="relative">
                         <Search className="absolute left-2.5 top-2.5 text-zinc-400" size={16} />
                         <input type="text" placeholder="Filtrera händelser..." className="pl-9 pr-4 py-2 bg-white dark:bg-white/5 border border-zinc-200 dark:border-white/10 rounded-sm text-sm w-64 focus:ring-1 focus:ring-zinc-400 dark:focus:ring-zinc-600 outline-none transition-all placeholder:text-zinc-400" />
                     </div>
                     <button className="p-2 border border-zinc-200 dark:border-white/10 rounded-sm bg-white dark:bg-white/5 hover:bg-zinc-50 dark:hover:bg-white/10 text-zinc-600 dark:text-zinc-400 transition-colors" title="Filter">
                        <Filter size={18} />
                     </button>
                     <button className="p-2 border border-zinc-200 dark:border-white/10 rounded-sm bg-white dark:bg-white/5 hover:bg-zinc-50 dark:hover:bg-white/10 text-zinc-600 dark:text-zinc-400 transition-colors" title="Uppdatera">
                        <RefreshCw size={18} />
                     </button>
                 </div>
            </div>

            <div className="flex-1 bg-white dark:bg-[#18181b] border border-zinc-200 dark:border-white/5 rounded-sm shadow-sm overflow-hidden flex flex-col">
                <div className="grid grid-cols-12 gap-4 px-4 py-2 border-b border-zinc-200 dark:border-white/10 bg-zinc-50/50 dark:bg-black/20 text-[10px] font-bold text-zinc-500 dark:text-zinc-400 uppercase tracking-wider">
                    <div className="col-span-1">Tid</div>
                    <div className="col-span-1">Prio</div>
                    <div className="col-span-6">Händelse</div>
                    <div className="col-span-2">Källa</div>
                    <div className="col-span-2 text-right">Status</div>
                </div>
                
                <div className="flex-1 overflow-y-auto">
                    {isLoading ? (
                        <div className="p-8 text-center text-zinc-400 text-sm italic">Hämtar data från källor...</div>
                    ) : events.length === 0 ? (
                        <div className="h-full flex items-center justify-center p-8">
                            <EmptyState 
                                icon={Inbox}
                                title="Inga nya händelser"
                                description="Bevakningen är aktiv. Nya händelser visas här så fort de registreras av systemet."
                            />
                        </div>
                    ) : (
                        events.map(e => (
                            <ListItem key={e.id} event={e} onClick={() => navigate('flow')} />
                        ))
                    )}
                </div>
            </div>
        </div>
    );
};