import React, { useEffect, useState } from 'react';
import { apiClient } from '../apiClient';
import { Transcript } from '../types';
import { FileText, Search, Mic } from 'lucide-react';
import { EmptyState } from '../components/ui/EmptyState';

interface TranscriptsProps {
    navigate: (page: string) => void;
}

export const Transcripts: React.FC<TranscriptsProps> = () => {
    const [transcripts, setTranscripts] = useState<Transcript[]>([]);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        setIsLoading(true);
        apiClient.getTranscripts().then(data => {
            setTranscripts(data);
            setIsLoading(false);
        });
    }, []);

    return (
        <div className="space-y-6 max-w-5xl mx-auto">
             <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-xl font-serif font-bold text-zinc-900 dark:text-white">Transkriptioner</h2>
                    <p className="text-sm text-zinc-500 dark:text-zinc-400">Sökbart arkiv för ljudupptagningar.</p>
                </div>
                 <button className="flex items-center gap-2 px-4 py-2 bg-zinc-900 dark:bg-white dark:text-black text-white text-sm font-medium rounded-sm shadow-sm hover:opacity-90 transition-opacity">
                    <span>+ Ladda upp ljudfil</span>
                 </button>
            </div>

            <div className="bg-white dark:bg-[#18181b] border border-zinc-200 dark:border-white/5 rounded-sm shadow-sm overflow-hidden">
                {/* Toolbar */}
                <div className="p-3 border-b border-zinc-100 dark:border-white/5 flex gap-2">
                     <div className="relative flex-1 max-w-md">
                         <Search className="absolute left-2.5 top-2 text-zinc-400" size={16} />
                         <input type="text" placeholder="Sök i arkivet..." className="pl-9 pr-4 py-1.5 bg-zinc-50 dark:bg-white/5 border border-zinc-200 dark:border-white/10 rounded-sm text-sm w-full outline-none focus:border-zinc-400 dark:focus:border-zinc-600 transition-colors placeholder:text-zinc-400" />
                     </div>
                </div>

                {isLoading ? (
                    <div className="p-8 text-center text-sm text-zinc-400">Laddar arkiv...</div>
                ) : transcripts.length === 0 ? (
                    <div className="p-8">
                        <EmptyState 
                            icon={Mic}
                            title="Arkivet är tomt"
                            description="Inga transkriptioner har sparats än. Ladda upp en ljudfil för att starta bearbetning."
                        />
                    </div>
                ) : (
                    <table className="w-full text-left">
                        <thead>
                            <tr className="bg-zinc-50 dark:bg-black/20 text-xs font-bold text-zinc-500 dark:text-zinc-400 uppercase tracking-wider border-b border-zinc-200 dark:border-white/5">
                                <th className="px-6 py-3 font-medium">Titel / Innehåll</th>
                                <th className="px-6 py-3 font-medium">Datum</th>
                                <th className="px-6 py-3 font-medium">Längd</th>
                                <th className="px-6 py-3 font-medium text-right">Status</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-zinc-100 dark:divide-white/5">
                            {transcripts.map((t) => (
                                <tr key={t.id} className="hover:bg-zinc-50 dark:hover:bg-white/5 transition-colors cursor-pointer group">
                                    <td className="px-6 py-4">
                                        <div className="flex items-start gap-3">
                                            <div className="mt-1 p-1.5 bg-zinc-100 dark:bg-zinc-800 text-zinc-500 rounded-sm">
                                                <FileText size={16} />
                                            </div>
                                            <div>
                                                <div className="text-sm font-medium text-zinc-900 dark:text-zinc-200 group-hover:text-zinc-900 dark:group-hover:text-white transition-colors">{t.title}</div>
                                                <div className="text-xs text-zinc-500 mt-1 line-clamp-1 italic">"{t.snippet}"</div>
                                            </div>
                                        </div>
                                    </td>
                                    <td className="px-6 py-4 text-sm text-zinc-500 font-mono">
                                        {t.date}
                                    </td>
                                    <td className="px-6 py-4 text-sm text-zinc-500 font-mono">
                                        {t.duration}
                                    </td>
                                    <td className="px-6 py-4 text-right">
                                        <span className={`inline-flex items-center px-2 py-0.5 rounded-sm text-[10px] font-bold uppercase tracking-wide border ${
                                            t.status === 'KLAR' 
                                            ? 'bg-emerald-50 text-emerald-700 border-emerald-100 dark:bg-emerald-900/20 dark:text-emerald-400 dark:border-emerald-900' 
                                            : 'bg-amber-50 text-amber-700 border-amber-100 dark:bg-amber-900/20 dark:text-amber-400 dark:border-amber-900'
                                        }`}>
                                            {t.status}
                                        </span>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                )}
            </div>
        </div>
    );
};