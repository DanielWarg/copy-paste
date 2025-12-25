<!--
ARCHIVED DOCUMENT
This file is no longer authoritative.
Canonical source of truth: docs/canonical/
-->

# Frontend - Komplett Dokumentation

## Innehållsförteckning

1. [Arkitekturöversikt](#arkitekturöversikt)
2. [Startup Sequence](#startup-sequence)
3. [Request Flow](#request-flow)
4. [Core Modules](#core-modules)
5. [State Management](#state-management)
6. [Styling & Theming](#styling--theming)
7. [API Integration](#api-integration)
8. [Mock Mode](#mock-mode)
9. [Error Handling](#error-handling)
10. [Development & Build](#development--build)

---

## Arkitekturöversikt

Frontend är en React-applikation byggd med Vite, TypeScript och Tailwind CSS. Den fungerar som administrativt gränssnitt för Copy/Paste-systemet och kan köra i två lägen:

- **Mock Mode (default)**: Använder statisk mock-data, fungerar utan backend
- **CORE Connected**: Ansluter till CORE backend via `VITE_API_BASE_URL`

### Designprinciper

1. **Graceful Degradation**: UI kraschar aldrig om backend är offline
2. **Privacy-Safe**: Inga headers/bodies loggas i frontend
3. **Mock-First**: Fungerar fullt ut med mock-data för utveckling
4. **Type-Safe**: TypeScript för alla komponenter och API-anrop

### Filstruktur

```
frontend/
├── index.html              # HTML entry point
├── index.tsx               # React entry point
├── App.tsx                 # Main app component (routing, theme)
├── apiClient.ts            # API client (connectivity check, mock methods)
├── types.ts                # TypeScript type definitions
├── constants.ts            # App constants (MODULES, SYSTEM_STATUS)
├── mockData.ts             # Mock data for development
├── vite.config.ts          # Vite configuration
├── package.json            # Dependencies and scripts
├── tsconfig.json           # TypeScript configuration
├── components/
│   ├── Layout.tsx         # Main layout (sidebar, header)
│   └── ui/                # Reusable UI components
│       ├── Badge.tsx
│       ├── EmptyState.tsx
│       ├── Modal.tsx
│       └── Toast.tsx
└── views/                 # Page components
    ├── Dashboard.tsx      # Overview page
    ├── Console.tsx         # Monitoring/events list
    ├── Pipeline.tsx        # Workflow page
    ├── Transcripts.tsx     # Transcripts archive
    └── Sources.tsx         # RSS sources management
```

---

## Startup Sequence

Startup-ordningen är kritisk för att säkerställa att appen laddar korrekt:

### 1. HTML Loading (`index.html`)

**När:** Browser laddar HTML

**Vad som händer:**
```html
<!DOCTYPE html>
<html lang="sv" class="dark">
  <head>
    <!-- Tailwind CSS via CDN -->
    <script src="https://cdn.tailwindcss.com"></script>
    <!-- Tailwind config (dark mode, custom colors) -->
    <!-- Google Fonts (Inter, Merriweather, JetBrains Mono) -->
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/index.tsx"></script>
  </body>
</html>
```

**Viktigt:**
- `class="dark"` sätts på `<html>` för dark mode default
- Tailwind CSS laddas via CDN (kan bytas till build-time i produktion)
- Root-element (`#root`) är mount-point för React

### 2. React Entry (`index.tsx`)

**När:** Vite laddar `index.tsx` som ES module

**Vad som händer:**
```typescript
const rootElement = document.getElementById('root');
if (!rootElement) {
  throw new Error("Could not find root element to mount to");
}

const root = ReactDOM.createRoot(rootElement);
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
```

**Viktigt:**
- Fail-fast om root-element saknas
- `React.StrictMode` aktiverar extra checks i development
- React 19 `createRoot` API (modern)

### 3. App Component (`App.tsx`)

**När:** React renderar `<App />`

**Vad som händer:**
```typescript
const App: React.FC = () => {
  const [page, setPage] = useState('overview');
  const [darkMode, setDarkMode] = useState(true);

  // Initialize Theme
  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [darkMode]);

  // Render content based on page state
  const renderContent = () => {
    switch (page) {
      case 'overview': return <Dashboard navigate={setPage} />;
      case 'monitoring': return <Console navigate={setPage} />;
      // ... other pages
    }
  };

  return (
    <Layout darkMode={darkMode} toggleTheme={toggleTheme} currentPage={page} navigate={setPage}>
      {renderContent()}
    </Layout>
  );
};
```

**Process:**
1. Initialiserar state (`page`, `darkMode`)
2. Sätter dark mode class på `<html>` via `useEffect`
3. Renderar `Layout` med aktuell `page` som children
4. `Layout` hanterar sidebar navigation och header

**Viktigt:**
- Dark mode synkas med DOM via `useEffect`
- Page routing är client-side via state (inte React Router)
- `navigate` callback prop för att byta sida

### 4. Layout Component (`components/Layout.tsx`)

**När:** `App` renderar `<Layout>`

**Vad som händer:**
```typescript
export const Layout: React.FC<LayoutProps> = ({ children, darkMode, toggleTheme, currentPage, navigate }) => {
  return (
    <div className="flex h-screen w-full">
      {/* Sidebar */}
      <aside className="hidden md:flex flex-col w-64">
        {/* Logo */}
        {/* Navigation (MODULES) */}
        {/* User profile */}
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col">
        {/* Header (date, theme toggle) */}
        <div className="flex-1 overflow-auto">
          {children} {/* Page content */}
        </div>
      </main>
    </div>
  );
};
```

**Process:**
1. Renderar sidebar med navigation (MODULES från `constants.ts`)
2. Renderar header med datum och theme toggle
3. Renderar `children` (aktuell page) i main content area

**Viktigt:**
- Sidebar är dold på mobile (`hidden md:flex`)
- Navigation använder `MODULES` array från `constants.ts`
- Theme toggle anropar `toggleTheme` callback

### 5. Page Component (ex. `Dashboard.tsx`)

**När:** `Layout` renderar page component som `children`

**Vad som händer:**
```typescript
export const Dashboard: React.FC<DashboardProps> = ({ navigate }) => {
  const [events, setEvents] = useState<NewsEvent[]>([]);

  useEffect(() => {
    apiClient.getEvents().then(setEvents);
  }, []);

  // Render dashboard UI
  return (
    <div>
      {/* Stats cards */}
      {/* Recent events */}
      {/* Quick actions */}
    </div>
  );
};
```

**Process:**
1. Initialiserar state för page data
2. Hämtar data via `apiClient` i `useEffect`
3. Renderar UI med data

**Viktigt:**
- Data hämtas asynkront via `apiClient`
- `apiClient` kan vara mock eller riktig API (beroende på `VITE_API_BASE_URL`)

---

## Request Flow

När en page component behöver data går denna process:

### 1. Component Calls API Client

**Vad:** Page component anropar `apiClient` metod

**Exempel:**
```typescript
// Dashboard.tsx
useEffect(() => {
  apiClient.getEvents().then(setEvents);
}, []);
```

### 2. API Client Checks Mode

**Vad:** `apiClient.ts` kontrollerar om `VITE_API_BASE_URL` är satt

**Process:**
```typescript
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

export const apiClient = {
  getEvents: async (): Promise<NewsEvent[]> => {
    // Mock mode (default)
    await delay(300);
    return MOCK_EVENTS;
  },
  
  // Connectivity check (only if API_BASE_URL is set)
  checkCoreConnectivity: async () => {
    if (!API_BASE_URL) {
      return { health: false, ready: false };
    }
    // ... check /health and /ready
  }
};
```

**Viktigt:**
- Om `VITE_API_BASE_URL` saknas → mock mode
- Om `VITE_API_BASE_URL` är satt → connectivity check möjlig

### 3. Mock Mode (Default)

**Vad:** Returnerar mock-data med simulerad fördröjning

**Process:**
```typescript
const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

getEvents: async (): Promise<NewsEvent[]> => {
  await delay(300); // Simulate network delay
  return MOCK_EVENTS; // Return mock data
}
```

**Viktigt:**
- Mock-data från `mockData.ts`
- Simulerad fördröjning för realistisk UX
- Fungerar utan backend

### 4. CORE Connected Mode (Optional)

**Vad:** Om `VITE_API_BASE_URL` är satt, gör connectivity check

**Process:**
```typescript
const checkCoreHealth = async (): Promise<{ health: boolean; ready: boolean }> => {
  if (!API_BASE_URL) {
    return { health: false, ready: false };
  }

  try {
    // Timeout: 5s max
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 5000);

    // Check /health
    const healthRes = await fetch(`${API_BASE_URL}/health`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
      signal: controller.signal,
    });
    
    // Check /ready
    const readyRes = await fetch(`${API_BASE_URL}/ready`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
      signal: readyController.signal,
    });

    return { health: healthRes.ok, ready: readyRes.ok };
  } catch (error) {
    // Fail softly - don't crash UI
    console.warn('CORE connectivity check failed');
    return { health: false, ready: false };
  }
};
```

**Viktigt:**
- Timeout: 5 sekunder max (via `AbortController`)
- Fail softly: Returnerar `{health: false, ready: false}` vid fel
- UI kraschar inte om backend är offline

### 5. Component Updates State

**Vad:** Component uppdaterar state med data

**Process:**
```typescript
apiClient.getEvents().then(setEvents);
// events state uppdateras
// Component re-renderar med ny data
```

**Viktigt:**
- State uppdateras asynkront
- React re-renderar automatiskt när state ändras

---

## Core Modules

### 1. App Component (`App.tsx`)

**Syfte:** Main app component, hanterar routing och theme

**Implementation:**

```typescript
const App: React.FC = () => {
  const [page, setPage] = useState('overview');
  const [darkMode, setDarkMode] = useState(true);

  // Sync dark mode with DOM
  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [darkMode]);

  // Route to page component
  const renderContent = () => {
    switch (page) {
      case 'overview': return <Dashboard navigate={setPage} />;
      case 'monitoring': return <Console navigate={setPage} />;
      case 'flow': return <Pipeline navigate={setPage} />;
      case 'transcripts': return <Transcripts navigate={setPage} />;
      case 'sources': return <Sources navigate={setPage} />;
      default: return <Dashboard navigate={setPage} />;
    }
  };

  return (
    <Layout darkMode={darkMode} toggleTheme={() => setDarkMode(!darkMode)} currentPage={page} navigate={setPage}>
      {renderContent()}
    </Layout>
  );
};
```

**Viktiga detaljer:**

- **Client-side routing**: Via state (`page`), inte React Router
- **Theme management**: Dark mode synkas med DOM via `useEffect`
- **Navigation**: `navigate` callback prop för att byta sida
- **Default page**: `overview` (Dashboard)

### 2. API Client (`apiClient.ts`)

**Syfte:** Centraliserad API-kommunikation med graceful fallback

**Implementation:**

**Connectivity Check:**
```typescript
const checkCoreHealth = async (): Promise<{ health: boolean; ready: boolean }> => {
  if (!API_BASE_URL) {
    return { health: false, ready: false };
  }

  try {
    // Timeout: 5s
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 5000);

    const healthRes = await fetch(`${API_BASE_URL}/health`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
      signal: controller.signal,
    });
    
    const readyRes = await fetch(`${API_BASE_URL}/ready`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
      signal: readyController.signal,
    });

    return { health: healthRes.ok, ready: readyRes.ok };
  } catch (error) {
    // Fail softly
    console.warn('CORE connectivity check failed');
    return { health: false, ready: false };
  }
};
```

**Mock Methods:**
```typescript
export const apiClient = {
  checkCoreConnectivity: async () => {
    // Only if API_BASE_URL is set
    if (!API_BASE_URL) return { health: false, ready: false };
    if (coreStatus === null) {
      coreStatus = await checkCoreHealth();
    }
    return coreStatus;
  },

  getEvents: async (): Promise<NewsEvent[]> => {
    await delay(300);
    return MOCK_EVENTS;
  },

  getEventById: async (id: string): Promise<NewsEvent | undefined> => {
    await delay(200);
    return MOCK_EVENTS.find(e => e.id === id);
  },

  // ... other mock methods
};
```

**Viktiga detaljer:**

- **Mock-first**: Alla metoder returnerar mock-data som default
- **Connectivity check**: Valfri, endast om `VITE_API_BASE_URL` är satt
- **Timeout**: 5 sekunder max för connectivity check
- **Fail softly**: Returnerar `false` vid fel, kraschar inte UI
- **Privacy-safe**: Inga headers/bodies loggas

### 3. Layout Component (`components/Layout.tsx`)

**Syfte:** Main layout med sidebar navigation och header

**Implementation:**

```typescript
export const Layout: React.FC<LayoutProps> = ({ children, darkMode, toggleTheme, currentPage, navigate }) => {
  return (
    <div className="flex h-screen w-full">
      {/* Sidebar */}
      <aside className="hidden md:flex flex-col w-64">
        {/* Logo */}
        <div className="p-5 h-16 flex items-center">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-red-600 rounded-full animate-pulse"></div>
            <span>{APP_NAME}</span>
          </div>
        </div>
        
        {/* Navigation */}
        <div className="flex-1 overflow-y-auto py-6 px-4">
          {MODULES.map(m => (
            <NavItem key={m.id} module={m} active={currentPage === m.id} onClick={() => navigate(m.id)} />
          ))}
        </div>

        {/* User Profile */}
        <div className="p-4 border-t">
          {/* User info */}
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col">
        {/* Header */}
        <header className="h-14 flex items-center justify-between px-6 border-b">
          <div>{/* Date */}</div>
          <button onClick={toggleTheme}>
            {darkMode ? <Sun /> : <Moon />}
          </button>
        </header>

        {/* Page Content */}
        <div className="flex-1 overflow-auto p-6">
          {children}
        </div>
      </main>
    </div>
  );
};
```

**Viktiga detaljer:**

- **Responsive**: Sidebar dold på mobile (`hidden md:flex`)
- **Navigation**: Använder `MODULES` array från `constants.ts`
- **Theme toggle**: Anropar `toggleTheme` callback
- **Active state**: Highlightar aktiv page baserat på `currentPage`

### 4. Page Components (`views/*.tsx`)

**Syfte:** Individuella sidor för olika funktioner

**Struktur:**

```typescript
export const Dashboard: React.FC<DashboardProps> = ({ navigate }) => {
  const [events, setEvents] = useState<NewsEvent[]>([]);

  useEffect(() => {
    apiClient.getEvents().then(setEvents);
  }, []);

  return (
    <div className="space-y-8 max-w-5xl mx-auto">
      {/* Page content */}
    </div>
  );
};
```

**Pages:**

- **Dashboard** (`Dashboard.tsx`): Översikt med stats och senaste events
- **Console** (`Console.tsx`): Realtidslista över inkommande händelser
- **Pipeline** (`Pipeline.tsx`): Arbetsflöde från källmaterial till utkast
- **Transcripts** (`Transcripts.tsx`): Arkiv för intervjuer och ljudupptagningar
- **Sources** (`Sources.tsx`): Hantera RSS och inkommande strömmar

**Viktiga detaljer:**

- **Data fetching**: Via `apiClient` i `useEffect`
- **State management**: Lokal state per component
- **Navigation**: Använder `navigate` callback för att byta sida

### 5. Types (`types.ts`)

**Syfte:** TypeScript type definitions

**Implementation:**

```typescript
export enum EventStatus {
  INCOMING = 'INKOMMANDE',
  TRIAGED = 'PÅGÅR',
  PROCESSING = 'BEARBETAS',
  REVIEW = 'GRANSKNING',
  PUBLISHED = 'PUBLICERAD',
  ARCHIVED = 'ARKIVERAD'
}

export interface NewsEvent {
  id: string;
  title: string;
  summary: string;
  source: string;
  sourceType: SourceType;
  timestamp: string;
  status: EventStatus;
  score: number;
  content?: string;
  maskedContent?: string;
  draft?: string;
  citations?: Citation[];
  privacyLogs?: PrivacyLog[];
}

export interface Transcript {
  id: string;
  title: string;
  date: string;
  duration: string;
  speakers: number;
  snippet: string;
  status: 'KLAR' | 'BEARBETAS' | 'FEL';
}

export interface Source {
  id: string;
  name: string;
  type: 'RSS' | 'API' | 'MAIL';
  status: 'ACTIVE' | 'PAUSED' | 'ERROR';
  lastFetch: string;
  itemsPerDay: number;
}
```

**Viktiga detaljer:**

- **Type-safe**: Alla API-anrop och komponenter är typade
- **Enums**: För status-värden (EventStatus, SourceType)
- **Interfaces**: För data structures (NewsEvent, Transcript, Source)

### 6. Constants (`constants.ts`)

**Syfte:** App-wide constants

**Implementation:**

```typescript
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
  // ... other modules
];
```

**Viktiga detaljer:**

- **MODULES**: Definierar navigation items
- **SYSTEM_STATUS**: Mock status (kan uppdateras från API senare)
- **APP_NAME**: App-namn för branding

---

## State Management

### Local State (per Component)

**Användning:** Varje component hanterar sin egen state

**Exempel:**
```typescript
const Dashboard: React.FC<DashboardProps> = ({ navigate }) => {
  const [events, setEvents] = useState<NewsEvent[]>([]);

  useEffect(() => {
    apiClient.getEvents().then(setEvents);
  }, []);

  // Use events state
  return <div>{events.map(...)}</div>;
};
```

**Viktigt:**
- Ingen global state management (Redux, Zustand, etc.)
- State är lokal till varje component
- Data hämtas via `apiClient` i `useEffect`

### App-Level State (`App.tsx`)

**Användning:** `App` component hanterar routing och theme

**Exempel:**
```typescript
const App: React.FC = () => {
  const [page, setPage] = useState('overview');
  const [darkMode, setDarkMode] = useState(true);

  // page och darkMode är app-level state
  // Passed down via props
};
```

**Viktigt:**
- `page`: Aktuell sida (routing)
- `darkMode`: Theme state
- Passed down via props till `Layout` och page components

---

## Styling & Theming

### Tailwind CSS

**Konfiguration:** Via CDN i `index.html`

```html
<script src="https://cdn.tailwindcss.com"></script>
<script>
  tailwind.config = {
    darkMode: 'class',
    theme: {
      extend: {
        colors: {
          editorial: {
            bg: '#09090b',
            surface: '#18181b',
            // ... custom colors
          }
        }
      }
    }
  }
</script>
```

**Viktigt:**
- Dark mode: `class` strategy (toggle via `dark` class på `<html>`)
- Custom colors: `editorial` palette för redaktionell stil
- CDN: Kan bytas till build-time Tailwind i produktion

### Dark Mode

**Implementation:**

```typescript
// App.tsx
useEffect(() => {
  if (darkMode) {
    document.documentElement.classList.add('dark');
  } else {
    document.documentElement.classList.remove('dark');
  }
}, [darkMode]);
```

**Viktigt:**
- Synkas med DOM via `useEffect`
- Toggle via `toggleTheme` callback
- Default: Dark mode (`useState(true)`)

### Typography

**Fonts:**
- **Sans**: Inter (UI text)
- **Serif**: Merriweather (headings)
- **Mono**: JetBrains Mono (code, timestamps)

**Implementation:**
```html
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&family=Merriweather:wght@300;400;700&display=swap');
```

---

## API Integration

### Environment Configuration

**API Base URL:** `VITE_API_BASE_URL` från environment

**Lokal utveckling:**
```bash
# frontend/.env
VITE_API_BASE_URL=http://localhost:8000
```

**Docker:**
```yaml
# docker-compose.yml
environment:
  VITE_API_BASE_URL: http://backend:8000
```

**Viktigt:**
- Vite env vars måste prefixas med `VITE_`
- Om `VITE_API_BASE_URL` saknas → mock mode
- Om `VITE_API_BASE_URL` är satt → connectivity check möjlig

### Connectivity Check

**Syfte:** Verifiera att CORE backend är tillgänglig

**Implementation:**
```typescript
checkCoreConnectivity: async (): Promise<{ health: boolean; ready: boolean }> => {
  if (!API_BASE_URL) {
    return { health: false, ready: false };
  }
  
  // Check /health and /ready
  // Timeout: 5s
  // Fail softly on error
}
```

**Viktigt:**
- Endast om `VITE_API_BASE_URL` är satt
- Timeout: 5 sekunder max
- Fail softly: Returnerar `false` vid fel, kraschar inte UI

### Mock Methods

**Syfte:** Returnera mock-data för utveckling

**Implementation:**
```typescript
getEvents: async (): Promise<NewsEvent[]> => {
  await delay(300); // Simulate network delay
  return MOCK_EVENTS; // From mockData.ts
}
```

**Viktigt:**
- Alla metoder returnerar mock-data som default
- Simulerad fördröjning för realistisk UX
- Mock-data från `mockData.ts`

---

## Mock Mode

### Purpose

Mock mode låter frontend fungera fullt ut utan backend, vilket är användbart för:
- Utveckling utan backend dependency
- UI/UX testing
- Demo/presentation

### Implementation

**Mock Data:** `mockData.ts`

```typescript
export const MOCK_EVENTS: NewsEvent[] = [
  {
    id: '1',
    title: 'Example Event',
    status: EventStatus.INCOMING,
    // ... other fields
  },
  // ... more events
];
```

**API Client:** Returnerar mock-data

```typescript
getEvents: async (): Promise<NewsEvent[]> => {
  await delay(300);
  return MOCK_EVENTS;
}
```

**Viktigt:**
- Mock mode är default (om `VITE_API_BASE_URL` saknas)
- Alla API-metoder har mock-implementation
- Simulerad fördröjning för realistisk UX

### Switching to CORE Connected

**Steg:**
1. Skapa `frontend/.env` från `frontend/.env.example`
2. Sätt `VITE_API_BASE_URL=http://localhost:8000` (lokal) eller `http://backend:8000` (Docker)
3. Starta om Vite dev server
4. Frontend gör connectivity check mot CORE

**Viktigt:**
- Vite måste startas om för att läsa nya env vars
- Connectivity check är valfri (UI fungerar även om backend är offline)

---

## Error Handling

### Connectivity Check Errors

**Implementation:**
```typescript
try {
  // ... fetch /health and /ready
} catch (error) {
  // Fail softly
  if (error instanceof Error && error.name === 'AbortError') {
    console.warn('CORE connectivity check timed out');
  } else {
    console.warn('CORE connectivity check failed (backend may be offline)');
  }
  return { health: false, ready: false };
}
```

**Viktigt:**
- Timeout: 5 sekunder max (via `AbortController`)
- Network errors: Hanteras i catch-block
- CORS errors: Hanteras i catch-block
- UI kraschar inte: Returnerar `false`, fortsätter i mock mode

### API Call Errors

**Implementation:**
```typescript
// Mock methods don't throw errors
// Real API methods (future) should handle errors gracefully
getEvents: async (): Promise<NewsEvent[]> => {
  try {
    // ... API call
  } catch (error) {
    // Fallback to mock or show error state
    console.error('Failed to fetch events');
    return []; // Empty array or mock data
  }
}
```

**Viktigt:**
- Mock methods: Returnerar alltid data (ingen error)
- Real API methods (framtida): Ska hantera errors gracefully
- UI ska visa error state, inte krascha

### Component Errors

**Implementation:**
```typescript
// React Error Boundaries (future)
// For now, components handle errors internally
useEffect(() => {
  apiClient.getEvents()
    .then(setEvents)
    .catch(error => {
      console.error('Failed to load events:', error);
      // Set error state or use mock data
    });
}, []);
```

**Viktigt:**
- Components ska hantera errors internt
- Visa error state i UI, inte krascha
- Fallback till mock data om möjligt

---

## Development & Build

### Development Server

**Start:**
```bash
cd frontend
npm install
npm run dev
```

**Vite Dev Server:**
- Port: 5173 (default)
- Host: `0.0.0.0` (för Docker)
- HMR: Hot Module Replacement aktiverat
- TypeScript: Kompileras on-the-fly

**Viktigt:**
- Env vars läses vid start (måste starta om för nya vars)
- HMR uppdaterar komponenter automatiskt vid ändringar

### Build

**Production Build:**
```bash
npm run build
```

**Output:**
- `dist/` mapp med optimerade assets
- HTML, CSS, JS minifierade
- Tree-shaking: Oanvänd kod tas bort

**Viktigt:**
- Tailwind CSS ska bytas från CDN till build-time i produktion
- Env vars inbäddas i build (kan inte ändras efter build)

### Preview

**Preview Production Build:**
```bash
npm run preview
```

**Viktigt:**
- Testar production build lokalt
- Simulerar production environment

### Docker

**Docker Compose:**
```yaml
frontend:
  image: node:20-alpine
  working_dir: /app
  volumes:
    - ./frontend:/app
  environment:
    VITE_API_BASE_URL: http://backend:8000
  ports:
    - "5173:5173"
  command: sh -c "npm install && npm run dev -- --host 0.0.0.0 --port 5173"
```

**Viktigt:**
- Volume mount: `./frontend:/app` för live reload
- Environment: `VITE_API_BASE_URL` sätts automatiskt
- Port: 5173 exponeras

---

## Data Flow Diagrams

### Component Render Flow

```
index.html
    ↓
index.tsx (React entry)
    ↓
App.tsx
    ├─→ Initialize state (page, darkMode)
    ├─→ Sync dark mode with DOM
    └─→ Render Layout
        ↓
    Layout.tsx
        ├─→ Render Sidebar (MODULES navigation)
        ├─→ Render Header (date, theme toggle)
        └─→ Render Page Component (children)
            ↓
        Dashboard.tsx (or other page)
            ├─→ Initialize state (events)
            ├─→ Fetch data via apiClient
            └─→ Render UI
```

### API Call Flow

```
Component calls apiClient.getEvents()
    ↓
apiClient checks API_BASE_URL
    ├─→ Not set → Mock mode
    │   └─→ Return MOCK_EVENTS
    │
    └─→ Set → CORE connected (optional)
        └─→ Future: Real API call
            ├─→ Success → Return data
            └─→ Error → Fallback to mock or error state
```

### Connectivity Check Flow

```
Component calls apiClient.checkCoreConnectivity()
    ↓
Check if API_BASE_URL is set
    ├─→ No → Return {health: false, ready: false}
    │
    └─→ Yes → Check /health and /ready
        ├─→ Timeout (5s) → Return {health: false, ready: false}
        ├─→ Network error → Return {health: false, ready: false}
        ├─→ CORS error → Return {health: false, ready: false}
        └─→ Success → Return {health: true, ready: true}
```

---

## Verifiering

### Local Development

```bash
# Start backend
cd backend
uvicorn app.main:app --reload

# Start frontend
cd frontend
cp .env.example .env
# Edit .env: VITE_API_BASE_URL=http://localhost:8000
npm install
npm run dev
```

**Verifiera:**
- Frontend laddar på http://localhost:5173
- Connectivity check fungerar (om backend körs)
- UI fungerar även om backend är offline (mock mode)

### Docker Development

```bash
# Start all services
make up

# Or manually
docker-compose up
```

**Verifiera:**
- Frontend laddar på http://localhost:5173
- Frontend ansluter till backend via `http://backend:8000`
- Connectivity check fungerar

### Mock Mode

```bash
# Start frontend without VITE_API_BASE_URL
cd frontend
npm run dev
```

**Verifiera:**
- Frontend laddar utan backend
- Mock data visas i UI
- Inga connectivity errors i console

---

## Sammanfattning

Frontend är en React-applikation som:

1. **Fungerar standalone**: Mock mode låter UI fungera utan backend
2. **Ansluter till CORE**: Valfri connectivity check när `VITE_API_BASE_URL` är satt
3. **Kraschar inte**: Graceful fallback om backend är offline
4. **Är type-safe**: TypeScript för alla komponenter och API-anrop
5. **Har modern UX**: Dark mode, responsive design, Tailwind CSS
6. **Är utvecklingsvänlig**: HMR, mock data, enkel setup

Frontend är redo för utveckling och kan anslutas till CORE när backend-endpoints är klara.

