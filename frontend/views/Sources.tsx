import React, { useEffect, useState } from 'react';
import { apiClient } from '../apiClient';
import { Source } from '../types';
import { Antenna, AlertCircle, CheckCircle, RefreshCw } from 'lucide-react';
import { EmptyState } from '../components/ui/EmptyState';

interface SourcesProps {
    navigate: (page: string) => void;
}

export const Sources: React.FC<SourcesProps> = () => {
    const [sources, setSources] = useState<Source[]>([]);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        setIsLoading(true);
        apiClient.getSources().then(data => {
            setSources(data);
            setIsLoading(false);
        });
    }, []);

    return (
        <div className="space-y-6 max-w-5xl mx-auto">
             <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-xl font-serif font-bold text-zinc-900 dark:text-white">Källor & Flöden</h2>
                    <p className="text-sm text-zinc-500 dark:text-zinc-400">Konfigurera inkommande nyhetsströmmar.</p>
                </div>
                 <button className="px-4 py-2 border border-zinc-300 dark:border-zinc-700 text-zinc-700 dark:text-zinc-300 text-sm font-medium rounded-sm hover:bg-zinc-50 dark:hover:bg-white/5 transition-colors">
                    Hantera API-nycklar
                 </button>
            </div>

            {isLoading ? (
                <div className="p-8 text-center text-sm text-zinc-400">Läser in källor...</div>
            ) : sources.length === 0 ? (
                <EmptyState 
                    icon={Antenna}
                    title="Inga källor konfigurerade"
                    description="Lägg till RSS-flöden eller API-kopplingar för att starta bevakningen."
                    actionLabel="Lägg till källa"
                    onAction={() => console.log('Add source')}
                />
            ) : (
                <div className="grid grid-cols-1 gap-4">
                    {sources.map(source => (
                        <div key={source.id} className="bg-white dark:bg-[#18181b] border border-zinc-200 dark:border-white/5 p-4 rounded-sm flex items-center justify-between shadow-sm">
                            <div className="flex items-center gap-4">
                                <div className={`p-3 rounded-full ${source.status === 'ACTIVE' ? 'bg-zinc-100 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300' : 'bg-red-50 text-red-700 dark:bg-red-900/20 dark:text-red-400'}`}>
                                    <Antenna size={20} />
                                </div>
                                <div>
                                    <h3 className="text-sm font-bold text-zinc-900 dark:text-white">{source.name}</h3>
                                    <div className="text-xs text-zinc-500 flex items-center gap-2 mt-0.5">
                                        <span className="bg-zinc-100 dark:bg-white/10 px-1.5 rounded text-[10px] font-mono">{source.type}</span>
                                        <span>• Uppdaterad {source.lastFetch}</span>
                                    </div>
                                </div>
                            </div>

                            <div className="flex items-center gap-6">
                                <div className="text-right">
                                    <div className="text-xs text-zinc-400 uppercase tracking-wide">Volym</div>
                                    <div className="text-sm font-mono font-medium">{source.itemsPerDay} / dag</div>
                                </div>
                                
                                <div className="h-8 w-px bg-zinc-100 dark:bg-white/10"></div>

                                {source.status === 'ACTIVE' ? (
                                    <div className="flex items-center gap-1.5 text-emerald-700 dark:text-emerald-400 text-sm font-medium bg-emerald-50 dark:bg-emerald-900/10 px-3 py-1 rounded-full border border-emerald-100 dark:border-emerald-900">
                                        <CheckCircle size={14} />
                                        <span>Aktiv</span>
                                    </div>
                                ) : (
                                    <div className="flex items-center gap-1.5 text-red-700 dark:text-red-400 text-sm font-medium bg-red-50 dark:bg-red-900/10 px-3 py-1 rounded-full border border-red-100 dark:border-red-900">
                                        <AlertCircle size={14} />
                                        <span>Fel</span>
                                    </div>
                                )}

                                <button className="p-2 hover:bg-zinc-100 dark:hover:bg-white/10 rounded-full text-zinc-400 transition-colors">
                                    <RefreshCw size={16} />
                                </button>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};