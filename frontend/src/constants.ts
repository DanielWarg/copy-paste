/**
 * Application Constants
 * 
 * Module definitions and app metadata.
 */

import { 
  LayoutDashboard, 
  List, 
  FileText, 
  Settings, 
  Shield, 
  Antenna
} from 'lucide-react';

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
    id: 'transcripts',
    title: 'Transkriptioner',
    icon: FileText,
    description: 'Projektöversikt och transkriptioner.',
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

