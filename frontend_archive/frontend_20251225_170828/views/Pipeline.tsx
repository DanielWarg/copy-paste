import React, { useState, useEffect, useCallback } from 'react';
import { apiClient } from '../apiClient';
import { NewsEvent, EventStatus } from '../types';
import { Shield, ArrowRight, Check, ArrowLeft, PenTool, Lock, Eye, EyeOff, FileText, Sparkles, Clock } from 'lucide-react';
import { StatusBadge } from '../components/ui/Badge';
import { EmptyState } from '../components/ui/EmptyState';
import { Modal } from '../components/ui/Modal';
import { Toast } from '../components/ui/Toast';

interface PipelineProps {
    navigate: (page: string) => void;
}

export const Pipeline: React.FC<PipelineProps> = ({ navigate }) => {
    // För demo: Hämta ett event som är i 'REVIEW' (MOCK_EVENTS[3])
    const [event, setEvent] = useState<NewsEvent | null>(null);
    const [showOriginal, setShowOriginal] = useState(false);
    
    // UI State for Security Features
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [showToast, setShowToast] = useState(false);
    const [auditLog, setAuditLog] = useState<string | null>(null);

    useEffect(() => {
        apiClient.getEvents().then(events => {
            const target = events.find(e => e.status === EventStatus.REVIEW);
            setEvent(target || null);
        });
    }, []);

    // Auto-revert timer logic (3 minutes inactivity)
    useEffect(() => {
        let timer: ReturnType<typeof setTimeout>;
        
        if (showOriginal) {
            // Reset timer on user interaction
            const resetTimer = () => {
                clearTimeout(timer);
                timer = setTimeout(() => {
                    setShowOriginal(false);
                    setShowToast(true);
                }, 180000); // 3 minutes
            };

            // Initial start
            resetTimer();

            // Listeners for activity
            window.addEventListener('mousemove', resetTimer);
            window.addEventListener('keydown', resetTimer);
            window.addEventListener('scroll', resetTimer);

            return () => {
                clearTimeout(timer);
                window.removeEventListener('mousemove', resetTimer);
                window.removeEventListener('keydown', resetTimer);
                window.removeEventListener('scroll', resetTimer);
            };
        }
    }, [showOriginal]);

    const handleToggleOriginal = () => {
        if (!showOriginal) {
            // If trying to show original, require confirmation
            setIsModalOpen(true);
        } else {
            // If hiding, just hide
            setShowOriginal(false);
        }
    };

    const confirmShowOriginal = () => {
        setShowOriginal(true);
        setIsModalOpen(false);
        // Set local audit log (UI only)
        setAuditLog(new Date().toLocaleTimeString('sv-SE', { hour: '2-digit', minute: '2-digit' }));
    };

    if (!event) return (
        <div className="max-w-4xl mx-auto mt-20">
            <EmptyState 
                icon={PenTool}
                title="Arbetsflödet är tomt"
                description="Det finns inga aktiva ärenden att granska just nu. Gå till Bevakningen för att påbörja ett nytt jobb."
                actionLabel="Gå till Bevakning"
                onAction={() => navigate('monitoring')}
            />
        </div>
    );

    return (
        <div className="flex flex-col h-[calc(100vh-6rem)] max-w-6xl mx-auto relative">
            
            {/* Security Components */}
            <Modal 
                isOpen={isModalOpen}
                onClose={() => setIsModalOpen(false)}
                onConfirm={confirmShowOriginal}
                title="Varning: Oskyddad data"
                confirmLabel="Visa rådata"
                description={
                    <div className="space-y-3">
                        <p>Du är på väg att visa omaskad källtext. Detta kan exponera personuppgifter (PII) som normalt skyddas av systemet.</p>
                        <p className="font-medium">Genom att fortsätta bekräftar du att du har redaktionellt skäl att granska originaldatat.</p>
                        <div className="bg-amber-50 dark:bg-amber-900/10 p-3 rounded-sm border border-amber-100 dark:border-amber-900/30 text-xs text-amber-800 dark:text-amber-200">
                            Denna handling loggas lokalt i sessionen. Vyn återställs automatiskt vid inaktivitet.
                        </div>
                    </div>
                }
            />

            <Toast 
                message="Säkerhetsåtgärd: Vyn återgick till skyddat läge på grund av inaktivitet."
                isVisible={showToast}
                onClose={() => setShowToast(false)}
            />

            <button onClick={() => navigate('monitoring')} className="flex items-center gap-2 text-zinc-500 hover:text-zinc-900 dark:hover:text-white mb-6 text-xs font-medium w-fit uppercase tracking-wider transition-colors">
                <ArrowLeft size={14} /> Tillbaka till listan
            </button>
            
            {/* Header & Stepper */}
            <div className="flex items-start justify-between mb-8 border-b border-zinc-200 dark:border-white/10 pb-6">
                <div>
                     <div className="flex items-center gap-2 mb-2">
                        <span className="text-[10px] font-bold px-2 py-0.5 bg-zinc-100 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300 rounded-sm uppercase tracking-wide border border-zinc-200 dark:border-zinc-700">
                            {event.source}
                        </span>
                        <span className="text-zinc-400 text-xs font-mono">{event.id}</span>
                     </div>
                     <h1 className="text-2xl font-serif font-bold text-zinc-900 dark:text-white leading-tight max-w-3xl">
                        {event.title}
                     </h1>
                </div>

                {/* Explicit Process Stepper */}
                <div className="flex items-start gap-3">
                    {/* Step 1 */}
                    <div className="flex flex-col items-center w-24 text-center">
                        <div className="w-8 h-8 rounded-full bg-emerald-50 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400 flex items-center justify-center mb-2 border border-emerald-100 dark:border-emerald-900">
                            <Check size={16} />
                        </div>
                        <span className="text-[10px] font-bold text-zinc-900 dark:text-white uppercase tracking-wide">Inkommet</span>
                        <span className="text-[10px] text-zinc-400 leading-tight mt-1">Data hämtad från källa</span>
                    </div>
                    
                    <div className="w-12 h-px bg-zinc-200 dark:bg-zinc-800 mt-4"></div>

                    {/* Step 2 */}
                    <div className="flex flex-col items-center w-24 text-center">
                        <div className="w-8 h-8 rounded-full bg-emerald-50 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400 flex items-center justify-center mb-2 border border-emerald-100 dark:border-emerald-900">
                            <Shield size={16} />
                        </div>
                        <span className="text-[10px] font-bold text-zinc-900 dark:text-white uppercase tracking-wide">Skyddat</span>
                        <span className="text-[10px] text-zinc-400 leading-tight mt-1">Personuppgifter dolda</span>
                    </div>

                    <div className="w-12 h-px bg-zinc-200 dark:bg-zinc-800 mt-4"></div>

                    {/* Step 3 (Active) */}
                    <div className="flex flex-col items-center w-24 text-center">
                        <div className="w-8 h-8 rounded-full bg-zinc-900 text-white dark:bg-white dark:text-black flex items-center justify-center mb-2 ring-4 ring-zinc-100 dark:ring-white/10">
                            <PenTool size={16} />
                        </div>
                        <span className="text-[10px] font-bold text-zinc-900 dark:text-white uppercase tracking-wide">Utkast</span>
                        <span className="text-[10px] text-zinc-400 leading-tight mt-1">Redo för granskning</span>
                    </div>
                </div>
            </div>

            {/* Content Area */}
            <div className="flex-1 grid grid-cols-1 lg:grid-cols-2 gap-8 min-h-0">
                
                {/* Left: Source Material (Normalized & Secure) */}
                <div className="flex flex-col h-full bg-zinc-50 dark:bg-[#121214] border border-zinc-200 dark:border-white/5 rounded-sm overflow-hidden relative transition-colors duration-500">
                    
                    {/* Header: Normalization Status */}
                    <div className={`px-5 py-3 border-b border-zinc-200 dark:border-white/5 flex items-center justify-between ${showOriginal ? 'bg-amber-50 dark:bg-amber-900/10' : 'bg-white dark:bg-white/5'}`}>
                        <div className="flex items-center gap-2">
                            <FileText size={16} className={showOriginal ? "text-amber-700 dark:text-amber-500" : "text-zinc-500"} />
                            <h3 className={`text-sm font-bold uppercase tracking-wider ${showOriginal ? "text-amber-900 dark:text-amber-100" : "text-zinc-900 dark:text-white"}`}>
                                {showOriginal ? 'Originaltext (Rådata)' : 'Normaliserad text'}
                            </h3>
                        </div>
                        {showOriginal && (
                            <span className="flex items-center gap-1.5 text-[10px] font-bold text-amber-700 dark:text-amber-400 bg-white/50 dark:bg-black/20 px-2 py-0.5 rounded-sm border border-amber-200 dark:border-amber-800 uppercase tracking-wide">
                                <Eye size={10} />
                                Oskyddad Vy
                            </span>
                        )}
                    </div>

                    {/* Integrity Indicator (Default View) */}
                    {!showOriginal && (
                        <div className="px-5 py-3 bg-emerald-50/50 dark:bg-emerald-900/10 border-b border-emerald-100 dark:border-emerald-900/30 flex items-start gap-3">
                            <Lock size={16} className="text-emerald-600 dark:text-emerald-500 mt-0.5 shrink-0" />
                            <div>
                                <div className="text-xs font-bold text-emerald-800 dark:text-emerald-400 uppercase tracking-wide mb-0.5">
                                    Integritet: Aktiv
                                </div>
                                <p className="text-xs text-emerald-700/80 dark:text-emerald-500/80 leading-snug">
                                    Personuppgifter identifieras och skyddas automatiskt innan bearbetning.
                                </p>
                            </div>
                        </div>
                    )}

                    {/* Content Body */}
                    <div className={`flex-1 p-6 overflow-y-auto font-serif text-sm leading-relaxed whitespace-pre-wrap transition-colors duration-300 ${showOriginal ? 'bg-amber-50/30 dark:bg-amber-900/5 text-zinc-900 dark:text-zinc-200' : 'text-zinc-800 dark:text-zinc-300'}`}>
                        {showOriginal ? event.content : (event.maskedContent || event.content)}
                    </div>

                    {/* Footer: Disclaimer & Responsibility Action */}
                    <div className="p-4 border-t border-zinc-200 dark:border-white/5 bg-zinc-50 dark:bg-white/5">
                        
                        {/* Audit Log Marker */}
                        {auditLog && !showOriginal && (
                            <div className="mb-3 flex items-center gap-1.5 text-[10px] text-zinc-400">
                                <Clock size={10} />
                                <span>Original granskat {auditLog}</span>
                            </div>
                        )}

                        {!showOriginal && !auditLog && (
                            <p className="text-[10px] text-zinc-400 mb-3 flex items-center gap-1.5">
                                <Sparkles size={12} />
                                Innehållet har rensats och strukturerats för vidare arbete.
                            </p>
                        )}
                        
                        <button 
                            onClick={handleToggleOriginal}
                            className={`flex items-center gap-2 text-xs font-medium transition-colors w-full justify-center py-2 rounded-sm border border-dashed ${
                                showOriginal 
                                ? 'text-zinc-600 border-zinc-300 hover:bg-white hover:text-zinc-900 dark:text-zinc-400 dark:border-zinc-700 dark:hover:bg-white/10 dark:hover:text-white' 
                                : 'text-zinc-500 border-zinc-300 hover:text-zinc-900 hover:border-zinc-400 dark:text-zinc-500 dark:border-zinc-800 dark:hover:text-zinc-300'
                            }`}
                        >
                            {showOriginal ? (
                                <>
                                    <EyeOff size={14} />
                                    Dölj originaltext (Återgå till skyddat läge)
                                </>
                            ) : (
                                <>
                                    <Eye size={14} />
                                    Visa originaltext för granskning
                                </>
                            )}
                        </button>
                    </div>
                </div>

                {/* Right: Draft Editor */}
                <div className="flex flex-col h-full">
                    <div className="flex items-center justify-between mb-2">
                        <h3 className="text-sm font-bold text-zinc-900 dark:text-white uppercase tracking-wider">Förslag till artikel</h3>
                        <StatusBadge status={EventStatus.REVIEW} />
                    </div>
                    <div className="flex-1 bg-white dark:bg-[#18181b] border border-zinc-200 dark:border-white/5 rounded-sm p-6 shadow-sm overflow-y-auto flex flex-col">
                        <textarea 
                            className="w-full h-full resize-none outline-none bg-transparent font-serif text-lg leading-relaxed text-zinc-900 dark:text-zinc-100"
                            defaultValue={event.draft}
                        />
                    </div>
                    <div className="mt-4 flex justify-end gap-3">
                        <button className="px-4 py-2 text-sm font-medium text-zinc-600 hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-white transition-colors border border-transparent hover:border-zinc-200 dark:hover:border-zinc-700 rounded-sm">
                            Förkasta
                        </button>
                        <button className="px-6 py-2 bg-zinc-900 hover:bg-zinc-800 dark:bg-zinc-100 dark:text-black dark:hover:bg-zinc-200 text-white text-sm font-medium rounded-sm shadow-sm flex items-center gap-2 transition-colors">
                            <span>Godkänn & Publicera</span>
                            <ArrowRight size={16} />
                        </button>
                    </div>
                </div>

            </div>
        </div>
    );
};