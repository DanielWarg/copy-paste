# 🧠 `agent.md` — Standardmall v2.2 (Cursor-Ready, 100/100)

## 0. Init-kontrakt (GÖR DETTA FÖRST)

**Mål:** Säkerställ 100/100 redan i första PR genom att skapa alla meta-filer innan funktionell kod.

**Cursor, skapa exakt dessa filer nu:**

1. `.github/workflows/backend.yml` (pytest + coverage gate)
2. `.github/workflows/frontend.yml` (vitest + coverage gate)
3. `scripts/verify_docs.sh` (kör README:s curl-exempel)
4. `scripts/audit_hardcoded.sh` (detektera URL/token i kod)
5. `scripts/a11y_ci.mjs` (Playwright + axe-core)
6. `.python-version` (3.11.9) och `.nvmrc` (20)
7. `LICENSE` (MIT)
8. `.gitignore` (python/node/build/coverage)
9. `.github/pull_request_template.md` (DoD + checklist)

**Godkännandekriterium:** Alla workflows gröna, skript körbara (`chmod +x scripts/*.sh`), PR-mall syns.

---

## 1. Syfte och Scope

– **Projekt:** {PROJECT_NAME}
– **Mål:** {PROJECT_GOAL}
– **Scope:** {SCOPE_DESCRIPTION}
– **Out of scope:** {OUT_OF_SCOPE}

## 2. Affärsregler

– Lista regler + hur de bevisas i test (länka till sektion 8).
**Verifieras genom:** {BUSINESS_RULE_VERIFICATION_METHOD}

## 3. Teknisk Arkitektur

Frontend: {FRONTEND_STACK} · Backend: {BACKEND_STACK} · Test: {TEST_STRATEGY} · CI: {CI_PIPELINE_DESCRIPTION} · Kodstil: {CODE_STYLE}

Repo:

```
/frontend/src  /frontend/tests
/backend/src   /backend/tests
/docs          /scripts
```

## 4. Lokal Körning (2-kommando-garanti)

Backend: `uvicorn src.main:app --reload --port {BACKEND_PORT}`
Frontend: `npm run dev` (port {FRONTEND_PORT})

## 5. CI “Local-First” Policy

Kör lokalt innan push: `npm run verify && pytest -q` (fail lokalt ⇒ ingen push).

## 6. API-Kontrakt

Endpoint: `{API_ENDPOINT}` · Request: `{ "input": "..." }` · Response: `{ "result": "...", "meta": {...} }`
Docs: `http://localhost:{BACKEND_PORT}/docs` · Fel: `{ code, message, trace_id }`

## 7. Definition of Done (DoD)

All funktionlighet enligt PRD, gröna tester, policyer uppfyllda, CI passerar, dokumentation komplett, noll hårdkodning.

## 8. Testningsmatris (Regel → Test)

| Regel    | Testfil                   | Metod               | Status |
| -------- | ------------------------- | ------------------- | ------ |
| {RULE_1} | backend/tests/test_api.py | test_rule1_behavior | ☐      |
| {RULE_2} | frontend/tests/ui.spec.ts | test_rule2_ui       | ☐      |

## 9. Kvalitetskrav (NFR)

Säkerhet, Prestanda, A11y, UX, Observability – se 9.5, 10, 11 och CI.

### 9.5 a11y-Checklist (CI-testbar)

* [ ] `aria-label` på interaktiva element
* [ ] `aria-live="polite"` för dynamik
* [ ] Kontrast ≥4.5:1
* [ ] Synlig focus-state, keyboard-nav
* [ ] `aria-hidden` för dold text
* [ ] Dark-mode kontrast
  **CI:** `node scripts/a11y_ci.mjs` (Playwright + axe-core)

## 10. Zero-Hardcoding Audit

* [ ] Inga hårdkodade URL:er/tokens
* [ ] Alla konstanter via `.env`
* [ ] Språksträngar via i18n
  **CI:** `scripts/audit_hardcoded.sh`

## 11. Mock-Fallback & Offline

Vid API-fel: deterministisk mock + toast “Offline-läge”. Testas i `test_mock_mode.py`.

## 12. Teststrategi

Backend: pytest + mocks + coverage · Frontend: vitest + RTL · Mål: ≥90 % core

## 13. Coverage Gates (CI-hårda)

Backend min **70 %**, Frontend min **60 %**. Fail gate ⇒ blockera PR.

## 14. CI/CD-Pipeline (ska redan finnas)

Backend-job: black/ruff/mypy + pytest-cov + gate
Frontend-job: eslint/prettier + vitest-coverage + gate

## 15. Dokumentations-Audit

**CI:** `scripts/verify_docs.sh` validerar README:s curl-exempel.

## 16. Troubleshooting & FAQ

Tabell med vanliga fel (venv, CORS, port, versionsmismatch) och lösning.

## 17. Miljövariabler

```
DEEPSEEK_API_KEY=
BACKEND_PORT={BACKEND_PORT}
FRONTEND_PORT={FRONTEND_PORT}
VITE_API_BASE_URL=http://localhost:{BACKEND_PORT}
CORS_ORIGINS=http://localhost:{FRONTEND_PORT}
DEBUG=true
```

## 18. Risker & Begränsningar

{RISK_ONE} → {MITIGATION_ONE} · {RISK_TWO} → {MITIGATION_TWO} · {LIMITATION_ONE}

## 19. Stretch Goals

Dark mode, kortkommandon, i18n, etc.

## 20. PR-Checklista (auto i PR-mall)

* [ ] Lint OK · [ ] Tester gröna · [ ] Coverage ≥ gate
* [ ] Doc-audit OK · [ ] A11y OK · [ ] Zero-hardcoding OK
* [ ] `.env.example` uppdaterad · [ ] Inga secrets i git

## 21. Status & Dokumentation

Status {…} · Datum {…} · Branch {…} · Ägare {…} · ADR/PRD-länkar {…}

## 22. Slutsats

Målet är **testbar, dokumenterad, skalbar MVP** med mätbara grindar.

---

## 🔩 Bilagor (kopiera in i repo oförändrat)

### `.github/workflows/backend.yml`

name: backend
on: [push, pull_request]
jobs:
test:
runs-on: ubuntu-latest
steps:
- uses: actions/checkout@v4
- uses: actions/setup-python@v5
with: { python-version: '3.11' }
- name: Install
run: |
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install pytest pytest-cov
- name: Lint & Type
run: |
cd backend
source .venv/bin/activate
black --check .
ruff check .
mypy .
- name: Tests with coverage
run: |
cd backend
source .venv/bin/activate
pytest -q --cov=src --cov-report=term --cov-report=xml
- name: Coverage gate (≥70%)
run: |
cd backend
python - << 'PY'
import xml.etree.ElementTree as ET
pct=float(ET.parse('coverage.xml').getroot().attrib['line-rate'])*100
print(f"backend coverage: {pct:.2f}%")
assert pct>=70, f"Coverage gate failed: {pct:.2f}% < 70%"
PY

### `.github/workflows/frontend.yml`

name: frontend
on: [push, pull_request]
jobs:
test:
runs-on: ubuntu-latest
steps:
- uses: actions/checkout@v4
- uses: actions/setup-node@v4
with: { node-version: '20' }
- name: Install
run: |
cd frontend
npm ci || npm install
- name: Lint & Format
run: |
cd frontend
npm run lint || npx eslint .
npm run format:check || npx prettier -c .
- name: Tests with coverage
run: |
cd frontend
npx vitest run --coverage --reporter=verbose
- name: Coverage gate (≥60%)
run: |
cd frontend
node -e "const fs=require('fs'); const r=JSON.parse(fs.readFileSync('coverage/coverage-summary.json','utf8')); const pct=r.total.statements.pct; console.log('frontend coverage:',pct+'%'); if(pct<60){process.exit(1)}"

### `scripts/verify_docs.sh`

#!/usr/bin/env bash
set -euo pipefail

# Anpassa endpoint/port efter README

API="[http://localhost:${BACKEND_PORT:-8000}/api/v1/analyze](http://localhost:${BACKEND_PORT:-8000}/api/v1/analyze)"
PAYLOAD='{"input":"Hello world"}'
RES=$(curl -s -X POST "$API" -H 'Content-Type: application/json' -d "$PAYLOAD")
echo "$RES" | grep -qi '"result"' || { echo "Doc-audit fail: saknar 'result' i svar"; exit 1; }
echo "Doc-audit OK"

### `scripts/audit_hardcoded.sh`

#!/usr/bin/env bash
set -euo pipefail
fail=0
grep -RIn --exclude-dir=node_modules --exclude-dir=.venv -E '(http://|https://).*(localhost|api.example|hardcoded)' . && { echo "Varning: Hårdkodad URL hittad"; fail=1; }
grep -RIn --exclude-dir=node_modules --exclude-dir=.venv -E '(SECRET|API_KEY|TOKEN)=[A-Za-z0-9]+' . && { echo "Varning: Möjlig secret i kod"; fail=1; }
exit $fail

### `scripts/a11y_ci.mjs`

import { chromium } from 'playwright';
import { AxeBuilder } from '@axe-core/playwright';
const url = process.env.A11Y_URL || '[http://localhost:3000](http://localhost:3000)';
const browser = await chromium.launch();
const page = await browser.newPage();
await page.goto(url);
const results = await new AxeBuilder({ page }).analyze();
console.log(`Violations: ${results.violations.length}`);
if (results.violations.length > 0) {
console.error(JSON.stringify(results.violations, null, 2));
process.exit(1);
}
await browser.close();

### `.python-version`

3.11.9

### `.nvmrc`

20

### `.github/pull_request_template.md`

### Mål & Scope

* [ ] Matchar PRD/ADR

### DoD & Kvalitet

* [ ] Tester gröna (backend + frontend)
* [ ] Coverage ≥ gates (70/60)
* [ ] Lint/type OK
* [ ] A11y CI OK
* [ ] Doc-audit OK
* [ ] Zero-hardcoding OK
* [ ] `.env.example` uppdaterad
* [ ] Inga secrets i git

---

