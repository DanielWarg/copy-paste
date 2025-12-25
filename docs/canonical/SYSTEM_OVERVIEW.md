# System Overview - Copy/Paste

**Version:** 1.0.0  
**Status:** Canonical Document (Single Source of Truth)  
**Senast uppdaterad:** 2025-12-25

---

## Vad är Copy/Paste?

Copy/Paste är ett **journalistiskt AI-assistanssystem** med fokus på källskydd, dataskydd och integritet. Systemet är designat för att hantera känsligt journalistiskt material (transkriptioner, källkontakter, artiklar) med maximal säkerhet.

### Huvudsyfte

- **Transkribering:** Ladda upp ljudfiler, transkribera automatiskt (faster-whisper), hantera transkriptioner
- **Projekthantering:** Organisera material i projekt med start/due dates, känslighetsnivåer
- **Källskydd:** Privacy Gate blockerar PII-leakage, zero egress förhindrar externa anrop
- **GDPR-compliance:** Krypterad lagring, retention policies, secure deletion

### Vad systemet INTE är

- ❌ **Inte en generell AI-assistent** - Fokuserar på journalistiskt arbetsflöde
- ❌ **Inte en cloud-tjänst** - Körs lokalt/on-premise med zero egress
- ❌ **Inte en live-recorder** - Fokus på uppladdning och transkribering (live recording planeras separat)
- ❌ **Inte en backup-lösning** - Material raderas permanent vid destruction (med receipt)

---

## Systemarkitektur

### Huvudkomponenter

```
┌─────────────────┐
│   Frontend      │  React + TypeScript (localhost:5174)
│   (UI)          │
└────────┬────────┘
         │ HTTP/REST (dev) eller HTTPS+mTLS (prod_brutal)
         │
┌────────▼────────┐
│   Proxy         │  Caddy (port 443/80)
│   (mTLS)        │
└────────┬────────┘
         │ HTTP (internal_net)
         │
┌────────▼────────┐
│   Backend       │  FastAPI (port 8000, internal only)
│   (CORE)        │
└────────┬────────┘
         │
    ┌────┴────┬─────────┬──────────┐
    │         │         │          │
┌───▼───┐ ┌──▼──┐ ┌────▼────┐ ┌──▼─────┐
│Postgres│ │Scout│ │Privacy  │ │Modules │
│  (DB)  │ │(RSS)│ │Shield   │ │        │
└────────┘ └─────┘ └─────────┘ └────────┘
```

### Kommunikationsflöde

**Frontend → Backend:**
- **Dev:** `http://localhost:8000` (direkt)
- **Prod (prod_brutal):** `https://localhost` via Caddy proxy med mTLS (klientcertifikat krävs)
- **Health/Ready:** `http://localhost:80` (utan mTLS, för driftmonitoring)

**Backend → Database:**
- PostgreSQL via SQLAlchemy
- DB är optional (backend startar utan DB)
- Auto-migrations vid startup

**Backend → Scout:**
- Inter-process via Docker network
- Scout läser RSS feeds → skapar events → lagras in-memory → Console module exponerar

**Backend → Privacy Shield:**
- Internal module calls
- Alla externa LLM-anrop måste passera Privacy Gate (maskerar PII)

---

## Huvudflöden

### 1. Transkribering (Record → Transcript)

```
1. Användare laddar upp ljudfil (WAV, MP3, etc.)
   ↓
2. POST /api/v1/record/create
   - Skapar Project (om project_id saknas)
   - Skapar Transcript (status: "uploading")
   ↓
3. POST /api/v1/record/{transcript_id}/audio
   - Validerar fil (magic bytes + extension)
   - Beräknar SHA256
   - Krypterar med Fernet
   - Lagrar som {sha256}.bin
   - Uppdaterar AudioAsset
   ↓
4. Asynkron transkribering (background thread)
   - faster-whisper transkriberar
   - Sparar segments till Transcript
   - Status: "transcribing" → "ready"
   ↓
5. UI visar transkript när status = "ready"
```

**Säkerhet:**
- Fil krypteras innan lagring (Fernet)
- Original filename lagras INTE på disk (endast SHA256)
- Inga filnamn/content i logs

### 2. Projekthantering

```
1. Skapa projekt
   POST /api/v1/projects
   - name, start_date, due_date, sensitivity
   ↓
2. Ladda upp filer till projekt
   POST /api/v1/projects/{id}/files
   - .txt, .docx, .pdf (max 25MB)
   - Validerar magic bytes + extension
   - Krypterar med Fernet
   - Lagrar som {sha256}.bin
   ↓
3. Lista projektfiler
   GET /api/v1/projects/{id}/files
   - Returnerar metadata (ingen content)
   ↓
4. Uppdatera projekt
   PATCH /api/v1/projects/{id}
   - name, start_date, due_date, sensitivity, status
```

**Säkerhet:**
- Filer krypteras innan lagring
- Original filename lagras endast i DB (inte på disk)
- Inga filnamn/content i logs eller audit events

### 3. Privacy Gate (Extern LLM-egress)

```
1. Modul vill anropa extern LLM (t.ex. OpenAI)
   ↓
2. Måste först passera Privacy Gate
   mask_text(raw_text) → MaskedPayload
   ↓
3. Privacy Gate:
   - Pass 1: Regex masking (email, phone, PNR, etc.)
   - Pass 2: Re-mask on result (catches overlaps)
   - Pass 3 (strict): Ytterligare pass för max safety
   ↓
4. Leak check (fail-closed)
   - Om PII detekteras → BLOCK (422)
   - Ingen fallback, ingen kompromiss
   ↓
5. Om OK: Skicka MaskedPayload till extern provider
   - ensure_egress_allowed() (blockerar i prod_brutal)
   - Extern anrop (om tillåtet)
```

**Säkerhet:**
- Type-safe enforcement (MaskedPayload är enda tillåtna input)
- Fail-closed leak check (ANY PII = BLOCK)
- Zero egress i prod_brutal (ensure_egress_allowed() blockerar)

---

## Säkerhetsprofil: prod_brutal

Systemet kan köras i flera säkerhetsprofiler. **prod_brutal** är den strängaste:

### Zero Egress
- Backend kan **INTE** nå internet via Docker network (`internal_net: internal: true`)
- `ensure_egress_allowed()` blockerar alla externa providers i prod_brutal
- Boot fail om cloud API keys är satta i env

### mTLS Enforcement
- Alla HTTPS-requests på 443 kräver klientcertifikat
- Utan cert: TLS handshake failar
- Health/ready: Endast HTTP (80) för driftmonitoring

### Privacy Gate
- Extern egress får endast ske med `MaskedPayload`
- Ingen raw text med PII får nå externa providers
- Leak → 422 (fail-closed)

### Fail-Closed Design
- Osäker config i prod_brutal → boot fail
- Exempel: `SOURCE_SAFETY_MODE=false` i produktion → boot fail
- Exempel: Cloud API keys satta → boot fail

**Detaljerad säkerhetsdokumentation:** Se [SECURITY_MODEL.md](./SECURITY_MODEL.md)

---

## Data Lifecycle

### Skapande
- Filer krypteras innan lagring (Fernet)
- SHA256 beräknas för deduplicering
- Metadata sparas i DB (ingen content)

### Lagring
- Krypterade blobs: `{sha256}.bin`
- Original filename: Endast i DB (aldrig på disk)
- Encryption key: Från `PROJECT_FILES_KEY` (Docker secrets i prod_brutal)

### Raderas
- Atomic two-phase destroy (pending → destroyed)
- Best-effort secure delete (overwrite med zeros)
- Receipt för alla destruktiva handlingar
- **Varning:** På SSD kan fysiska bitar finnas kvar (kräver disk encryption för full garanti)

**Detaljerad datalifecycle:** Se [DATA_LIFECYCLE.md](./DATA_LIFECYCLE.md)

---

## Moduler

Systemet är modulärt. Alla features går i `/modules/*`, CORE är frozen.

**Aktiva moduler:**
- `record` - Audio upload, transkribering
- `transcripts` - Transcript management
- `projects` - Projekthantering
- `privacy_shield` - PII masking
- `console` - Events & Sources
- `autonomy_guard` - Guardrails för autonoma handlingar

**Module Contract:**
- Endast importera från `app.core.logging` och `app.core.config`
- Privacy-safe logging (inga payloads/headers/PII)
- Dokumentation i `README.md`

**Detaljerad modulmodell:** Se [MODULE_MODEL.md](./MODULE_MODEL.md)

---

## Referenser

- **Säkerhet:** [SECURITY_MODEL.md](./SECURITY_MODEL.md)
- **Moduler:** [MODULE_MODEL.md](./MODULE_MODEL.md)
- **Data Lifecycle:** [DATA_LIFECYCLE.md](./DATA_LIFECYCLE.md)
- **AI Governance:** [AI_GOVERNANCE.md](./AI_GOVERNANCE.md)
- **Operational:** [OPERATIONAL_PLAYBOOK.md](./OPERATIONAL_PLAYBOOK.md)

---

**Detta är en canonical document. Uppdatera endast om systemets grundläggande syfte eller arkitektur ändras.**

