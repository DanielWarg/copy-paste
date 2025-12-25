import { LayoutDashboard, Radio, List, FileText, Settings, Shield, Antenna, Mic } from 'lucide-react';

export const APP_NAME = "REDAKTIONELLT STÖD";

export const SYSTEM_STATUS = {
  CORE: 'online',
  DB: 'connected',
  VERSION: 'RC-2.4'
};

export const MODULES = [
  {
    id: 'overview',
    title: 'Översikt',
    icon: LayoutDashboard,
    description: 'Samlad lägesbild och systemstatus.',
    link: '/overview'
  },
  {
    id: 'monitoring',
    title: 'Bevakning',
    icon: List,
    description: 'Realtidslista över inkommande händelser.',
    link: '/monitoring'
  },
  {
    id: 'flow',
    title: 'Arbetsflöde',
    icon: Shield,
    description: 'Från källmaterial till färdigt utkast.',
    link: '/flow'
  },
  {
    id: 'recorder',
    title: 'Inspelning',
    icon: Mic,
    description: 'Spela in och ladda upp ljudfiler för transkribering. (REAL WIRED)',
    link: '/recorder'
  },
  {
    id: 'transcripts',
    title: 'Transkriptioner',
    icon: FileText,
    description: 'Arkiv för intervjuer och ljudupptagningar.',
    link: '/transcripts'
  },
  {
    id: 'sources',
    title: 'Källor',
    icon: Antenna,
    description: 'Hantera RSS och inkommande strömmar.',
    link: '/sources'
  },
  {
    id: 'settings',
    title: 'Inställningar',
    icon: Settings,
    description: 'Lokala visningsalternativ.',
    link: '/settings'
  }
];