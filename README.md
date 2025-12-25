# Copy/Paste - Journalistisk AI-Assistans

Modulärt system för journalistisk AI-assistans med fokus på integritet, säkerhet och källskydd.

---

## 📚 Dokumentation

**Canonical Documentation (Single Source of Truth):**
- [SYSTEM_OVERVIEW.md](docs/canonical/SYSTEM_OVERVIEW.md) - Vad systemet är
- [SECURITY_MODEL.md](docs/canonical/SECURITY_MODEL.md) - Säkerhetsgarantier
- [MODULE_MODEL.md](docs/canonical/MODULE_MODEL.md) - Hur moduler byggs
- [DATA_LIFECYCLE.md](docs/canonical/DATA_LIFECYCLE.md) - Datahantering
- [AI_GOVERNANCE.md](docs/canonical/AI_GOVERNANCE.md) - AI-regler
- [OPERATIONAL_PLAYBOOK.md](docs/canonical/OPERATIONAL_PLAYBOOK.md) - Drift

**Versionshistorik:**
- [CHANGELOG.md](CHANGELOG.md)

---

## 🚀 Quick Start

```bash
# 1. Starta backend + database
make up

# 2. Starta frontend (i separat terminal)
make frontend-dev

# 3. Öppna webbläsaren
open http://localhost:5174
```

**Detaljerad guide:** Se [OPERATIONAL_PLAYBOOK.md](docs/canonical/OPERATIONAL_PLAYBOOK.md)

---

## Vanliga Kommandon

```bash
make up          # Starta backend + postgres
make down        # Stoppa alla services
make health      # Testa health/ready endpoints
make test        # Smoke tests
make verify      # GO/NO-GO verification
```

**Alla kommandon:** Se [OPERATIONAL_PLAYBOOK.md](docs/canonical/OPERATIONAL_PLAYBOOK.md)

---

## Säkerhet

**Hårda Invariants (Testbara, Maskinläsbara):**
1. Zero Egress (prod_brutal)
2. mTLS Enforcement
3. Privacy Gate
4. No-Content Logging
5. Fail-Closed Design

**Verifiering:** `make check-security-invariants` och `make verify-brutal`

**Detaljer:** Se [SECURITY_MODEL.md](docs/canonical/SECURITY_MODEL.md)

---

## AI-Assistenter

**Alla AI-sessioner börjar här:**
1. Läs [AI_GOVERNANCE.md](docs/canonical/AI_GOVERNANCE.md)
2. Läs canonical docs i `docs/canonical/`
3. Följ arbetsregler

**Tid:** < 10 minuter för att förstå systemet

---

**Version:** 1.0.0  
**Status:** Production-ready
