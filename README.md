# Copy/Paste - Editorial AI Pipeline

Produktionsnära redaktionellt AI-system med lokal anonymisering, source-bound drafts, och fullständig GDPR-compliance.

## 🎯 Systemöversikt

Copy/Paste är ett internt redaktionellt AI-system som bevisar att "vibekodade" AI-ideer kan omvandlas till production-grade pipelines. Systemet är linjärt och spårbart: **Ingest → Scrub (Privacy Shield) → Source Extracts → Generate (Source-Bound Draft)**.

### Kärnprinciper

1. Journalister arbetar i **flows**, inte appar
2. All AI-output måste vara **source-bound eller refuserad**
3. Inga externa AI-modeller får **unscrubbed data**
4. Systemet måste vara förståeligt för utvecklare, infra, produkt och redaktörer
5. Om något inte kan verifieras → måste vara **synligt blockerat**

## 🚀 Quick Start

### Prerequisites

* Docker & Docker Compose
* Python 3.11+ (för lokal utveckling)
* Node.js 20+ (för lokal utveckling)
* Ollama (för lokal LLM - valfritt, regex fallback finns)

### Lokal Körning

```bash
# Klona repo
git clone https://github.com/DanielWarg/copy-paste.git
cd copy-paste

# Kopiera env-fil och sätt OpenAI API key
cp .env.example .env
# Redigera .env och lägg till din OPENAI_API_KEY

# Starta alla tjänster
docker compose up -d

# Verifiera att allt körs
curl http://localhost:8000/health
```

### Utveckling

```bash
# Backend (i separat terminal)
cd backend
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Frontend (i separat terminal)
cd frontend
npm install
npm run dev
```

## 🏗️ Arkitektur

### Backend
* **FastAPI** + **Pydantic** för data contracts
* **Ollama** + **Ministral 3B** för lokal PII-detection (med regex fallback)
* **OpenAI API** (abstracted) för draft generation
* **Privacy-safe logging**
* **Rate limiting** (100 req/min)

### Frontend
* **React** + **TypeScript** + **Vite**
* Komponenter: UniversalBox, ProductionModeToggle, DraftViewer, SourcePanel

### Infrastructure
* **Docker Compose** setup
* **PostgreSQL** (för framtida expansion)
* **.env** konfiguration

## 🔒 Säkerhet & GDPR

### Säkerhetsfunktioner

* ✅ **PII Anonymisering** - Lokal anonymisering innan externa API-anrop
* ✅ **Mapping Never in Response** - Mapping finns ALDRIG i API responses
* ✅ **External API Security** - Kräver `is_anonymized=true` ALLTID
* ✅ **Rate Limiting** - 100 requests/minut per IP
* ✅ **Privacy-Safe Logging** - Inga PII i logs
* ✅ **Prompt Injection Defense** - Injection-resistant prompts

### GDPR Compliance

* ✅ Data minimization
* ✅ Purpose limitation
* ✅ Security by design & default
* ✅ Right to be forgotten (session-based)

Se `REDTEAM_RAPPORT.md` för detaljerad säkerhetsverifiering.

## 📊 Testresultat

### Integrationstester
- ✅ **5/5 tester passerade**
- Health Check, Ingest, Scrub, Draft Generation, Security Check

### Red Team Attack
- ✅ **9 attackvektorer testade**
- ✅ **0 sårbarheter kvar**
- Alla attacker blockerade

Se `LIVETEST_FINAL_RAPPORT.md` för detaljerad testrapport.

## 📁 Projektstruktur

```
/copy-paste
├── backend/
│   ├── app/
│   │   ├── core/              # Config, logging, rate limiting
│   │   ├── modules/
│   │   │   ├── ingestion/     # Event creation
│   │   │   ├── privacy/       # Anonymization
│   │   │   └── drafting/      # Draft generation
│   │   ├── models.py          # Data contracts
│   │   └── main.py            # FastAPI app
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/        # React components
│   │   └── App.tsx
│   ├── package.json
│   └── Dockerfile
├── scripts/
│   ├── live_test.py           # Full pipeline test
│   ├── test_with_api.py       # Quick test med API
│   └── redteam_attack.py      # Security testing
├── docker-compose.yml
├── .env                        # API keys (ej i git)
└── README.md
```

## 📚 Dokumentation

* `SAMMANFATTNING.md` - Detaljerad systemöversikt
* `projektplan.md` - Projektplan med checkboxes
* `TEST_RAPPORT.md` - Integration test rapport
* `REDTEAM_RAPPORT.md` - Security test rapport
* `LIVETEST_FINAL_RAPPORT.md` - Live test rapport

## 🎬 Showreel

Systemet kan demonstreras på **under 2 minuter**:

1. Ingest source (URL/text)
2. Toggle Production Mode ON
3. Visa anonymisering (före/efter)
4. Generera draft
5. Bevisa citations (click sentence → highlight source)
6. Blockera unsupported claims (visa policy violations)

## ✅ Status

**PRODUCTION READY** 🚀

Alla komponenter:
- ✅ Implementerade
- ✅ Testade
- ✅ Säkerhetsverifierade
- ✅ GDPR-compliant

## 📝 License

MIT

## 🔗 Länkar

* [GitHub Repository](https://github.com/DanielWarg/copy-paste)
* [Security Report](REDTEAM_RAPPORT.md)
* [Live Test Report](LIVETEST_FINAL_RAPPORT.md)
