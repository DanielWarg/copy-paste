# Dokumentations-CI/CD

**Senast uppdaterad:** 2025-12-24

---

## Automatisk Dokumentationsvalidering

Projektet har automatisk validering av dokumentation som körs både lokalt och i CI/CD.

---

## Lokal Validering

### Kommando

```bash
make check-docs
# Eller direkt:
./scripts/check_docs.sh
```

### Vad den kontrollerar

1. **Modul README-konsistens**
   - Alla moduler registrerade i `main.py` måste ha `README.md`
   - Listar moduler som saknar README

2. **Obligatorisk dokumentation**
   - Verifierar att kärndokumentation finns:
     - `README.md`
     - `docs/core.md`
     - `docs/frontend.md`
     - `docs/architecture.md`
     - `docs/getting-started.md`

3. **Root .md filer**
   - Varnar om .md filer i root som inte ska vara där
   - Tillåtna filer: `README.md`, `CHANGELOG.md`, `agent.md`

---

## CI/CD Validering

### GitHub Actions

Workflow: `.github/workflows/docs-check.yml`

**Triggas på:**
- Pull requests som ändrar dokumentation
- Push till `main` branch med dokumentationsändringar

**Kontrollerar:**
1. Alla aktiva moduler har README.md
2. Obligatorisk dokumentation finns
3. Markdown-länkar är giltiga (basic check)
4. Modulkonsistens (moduler i main.py finns i filesystem)

**Status:** ✅ Konfigurerad och redo

---

## Integration i CI Pipeline

### Makefile

`make ci` kör nu automatiskt:
- `lint` - Code linting
- `typecheck` - Type checking
- `test` - Smoke tests
- `check-docs` - Dokumentationsvalidering ⬅️ **NYTT**

```bash
make ci  # Kör alla checks inkl. dokumentation
```

---

## Vad görs vid fel?

### Lokalt

- Script visar tydliga felmeddelanden
- Exit code 1 vid fel
- Warnings för mindre problem (failar inte)

### CI/CD

- GitHub Actions failar om validering misslyckas
- PR kan inte mergas om dokumentation är inkonsistent
- Status badge visas i PR

---

## Utöka Valideringen

### Lägg till nya kontroller

Redigera `scripts/check_docs.sh` för att lägga till:
- Länk-validering (external links)
- Markdown syntax check
- Dokumentationsstorlek
- Etc.

### Lägg till i CI

Redigera `.github/workflows/docs-check.yml` för att lägga till:
- Mer avancerade markdown-checks
- Länk-validering
- Dokumentationsgenerering
- Etc.

---

## Best Practices

1. **Kör `make check-docs` före commit**
2. **Fixa alla warnings innan PR**
3. **Uppdatera dokumentation när moduler ändras**
4. **Använd CI som safety net**

---

## Status

✅ **Lokal validering:** Fungerar  
✅ **CI/CD validering:** Konfigurerad  
✅ **Makefile integration:** Klar  
✅ **Dokumentation:** Uppdaterad

