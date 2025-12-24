import { NewsEvent, EventStatus, SourceType, Transcript, Source } from './types';
import { subMinutes, subHours } from 'date-fns';

export const MOCK_EVENTS: NewsEvent[] = [
  {
    id: 'evt-201',
    title: 'Riksbanken höjer styrräntan med 25 punkter',
    summary: 'Beskedet kom klockan 09:30. Riksbanken motiverar höjningen med fortsatt hög kärninflation.',
    source: 'TT Flash',
    sourceType: SourceType.RSS,
    timestamp: subMinutes(new Date(), 2).toISOString(),
    status: EventStatus.INCOMING,
    score: 95,
    isDuplicate: false,
    content: "Riksbanken har idag beslutat att höja styrräntan med 0,25 procentenheter till 4,00 procent. Prognosen för räntan ligger kvar..."
  },
  {
    id: 'evt-202',
    title: 'Trafikolycka på E4 norr om Uppsala',
    summary: 'Två personbilar inblandade. Stor påverkan på trafiken i södergående riktning.',
    source: 'Trafikverket API',
    sourceType: SourceType.RSS,
    timestamp: subMinutes(new Date(), 15).toISOString(),
    status: EventStatus.INCOMING,
    score: 65,
    isDuplicate: false,
    content: "Larm inkom 14:15. Räddningstjänst på plats. Vägen beräknas vara avstängd till 16:00."
  },
  {
    id: 'evt-203',
    title: 'Debattartikel: "AI måste regleras hårdare"',
    summary: 'Insändare från ledande forskare vid KTH.',
    source: 'Inkommande Mail',
    sourceType: SourceType.MANUAL,
    timestamp: subHours(new Date(), 1).toISOString(),
    status: EventStatus.TRIAGED,
    score: 40,
    content: "Vi ser en oroande utveckling där generativ AI används utan etisk hänsyn..."
  },
  {
    id: 'evt-204',
    title: 'PRESSMEDDELANDE: Volvo redovisar rekordvinst',
    summary: 'Kvartalsrapport Q3 slår förväntningarna.',
    source: 'Cision',
    sourceType: SourceType.RSS,
    timestamp: subHours(new Date(), 3).toISOString(),
    status: EventStatus.REVIEW, // Drafted -> Review
    score: 88,
    content: "Volvokoncernen rapporterar ett justerat rörelseresultat på 19,1 miljarder kronor...",
    maskedContent: "[FÖRETAG] rapporterar ett justerat rörelseresultat på [BELOPP] kronor...",
    draft: "Volvokoncernen levererar en oväntat stark kvartalsrapport för årets tredje kvartal. Det justerade rörelseresultatet landade på 19,1 miljarder kronor, vilket var betydligt högre än analytikernas förväntningar.",
    citations: [
        { id: 'c1', sourceText: "justerat rörelseresultat på 19,1 miljarder", startIndex: 85, endIndex: 120, confidence: 0.99 }
    ],
    privacyLogs: [
        { timestamp: subHours(new Date(), 3).toISOString(), action: 'SCAN_COMPLETE', details: 'Hittade 2 företagsnamn.' },
        { timestamp: subHours(new Date(), 3).toISOString(), action: 'MASKING_APPLIED', details: 'Maskerade finansiell data för extern analys.' }
    ]
  }
];

export const MOCK_TRANSCRIPTS: Transcript[] = [
    { id: 'tr-1', title: 'Intervju: Kommunalrådet om skolnedläggningen', date: '2023-11-01', duration: '14:20', speakers: 2, snippet: 'Det är ett tufft beslut, men vi måste se till ekonomin...', status: 'KLAR'},
    { id: 'tr-2', title: 'Presskonferens Polisen', date: '2023-11-02', duration: '08:45', speakers: 1, snippet: 'Vi kan bekräfta att en person är frihetsberövad...', status: 'KLAR'},
    { id: 'tr-3', title: 'Mötesanteckningar: Morgonmötet', date: '2023-11-03', duration: '22:10', speakers: 5, snippet: 'Dagens fokus ligger på uppföljningen av valet...', status: 'BEARBETAS'},
];

export const MOCK_SOURCES: Source[] = [
    { id: 'src-1', name: 'TT Flash', type: 'RSS', status: 'ACTIVE', lastFetch: '1 min sedan', itemsPerDay: 140 },
    { id: 'src-2', name: 'Polisen Händelser', type: 'API', status: 'ACTIVE', lastFetch: '5 min sedan', itemsPerDay: 45 },
    { id: 'src-3', name: 'Reuters World', type: 'RSS', status: 'ERROR', lastFetch: '2 timmar sedan', itemsPerDay: 300 },
];