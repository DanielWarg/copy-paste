# Config Best Practices - Förhindra Blocking Imports

## Vad var felet?

### Problem 1: `pydantic_settings` blockerade på flera `.env`-filer

**Vad hände:**
```python
class Config:
    env_file = [".env", "../.env", "../../.env"]  # ❌ PROBLEM
```

När `Settings()` instansierades, försökte `pydantic_settings` läsa från **alla tre filer** i sekvens. Om någon av dessa:
- Finns på långsamt nätverksfilsystem
- Har filsystem-locks
- Är på en mount som är långsam/nedstängd

→ Då **blockerar** `Settings()` och hela importen hänger sig.

**Fix:**
```python
class Config:
    env_file = ".env"  # ✅ Bara en fil, i aktuell katalog
```

### Problem 2: Shell-continuation med `python -c`

**Vad hände:**
```bash
python3 -c "from app.core.config import settings; print(...)"  # ❌ PROBLEM
```

Långa `python -c`-kommandon med komplexa strängar kan:
- Hamna i shell-continuation (`>>`) om citattecken är trasiga
- Vara svåra att debugga
- Ge inga felmeddelanden om importen blockerar

**Fix:**
```bash
python3 test_imports.py  # ✅ Testfil istället
```

### Problem 3: Debug-logging med hårdkodade sökvägar

**Vad hände:**
```python
with open('/Users/evil/Desktop/EVIL/PROJECT/COPY:PASTE/.cursor/debug.log', 'a') as f:  # ❌ PROBLEM
```

Hårdkodade absoluta sökvägar:
- Fungerar bara på en specifik maskin
- Bryter portabilitet
- Är svåra att underhålla

**Fix:**
- Använd relativ sökväg eller environment variable
- Eller ta bort debug-logging när den inte behövs

---

## Regler för Config-Moduler (FÖR ALLTID)

### ✅ GÖR DETTA

1. **Config ska vara "död" och deterministisk**
   ```python
   # ✅ OK: Bara läsa env vars och validera typer
   ollama_base_url: str = "http://localhost:11434"
   ```

2. **Använd singular `env_file`**
   ```python
   # ✅ OK
   env_file = ".env"
   ```

3. **Inga blocking operations vid import**
   ```python
   # ✅ OK: Bara instansiera Settings()
   settings = Settings()
   ```

### ❌ GÖR INTE DETTA

1. **Initiera klienter i config**
   ```python
   # ❌ FEL: Initierar klient vid import
   ollama_client = OllamaClient()  # I config.py
   ```

2. **Läs från flera filer**
   ```python
   # ❌ FEL: Kan blockera på långsamma filsystem
   env_file = [".env", "../.env", "../../.env"]
   ```

3. **Gör nätverksanrop vid import**
   ```python
   # ❌ FEL: Blocking network call
   response = httpx.get("http://...")  # I config.py
   ```

4. **Cirkulära imports**
   ```python
   # ❌ FEL: config -> service -> config
   # config.py
   from app.modules.service import something  # som importerar config
   ```

---

## Checklista för Nya Config-Moduler

När du skapar eller ändrar config:

- [ ] Använder `env_file = ".env"` (singular, inte lista)
- [ ] Inga `import` från service-moduler
- [ ] Inga klient-initialiseringar
- [ ] Inga nätverksanrop
- [ ] Inga fil-I/O utöver `.env`-läsning
- [ ] `Settings()` instansieras direkt (ingen lazy init om det inte behövs)
- [ ] Testbar med `python3 -c "from app.core.config import settings"` utan timeout

---

## Testning

### Snabb test (skulle fungera direkt):
```bash
cd backend
python3 -c "from app.core.config import settings; print('OK')"
```

### Om det hänger sig:
1. Använd `test_imports.py` för att se var det blockerar
2. Kolla om config importerar något som gör blocking I/O
3. Kolla om `env_file` är en lista istället för singular

---

## CI/CD Check (Framtida)

Lägg till i CI:
```bash
# Testa att config kan importeras snabbt
timeout 2 python3 -c "from app.core.config import settings" || exit 1
```

Om det tar >2 sekunder → config gör något fel.

---

## Exempel på Korrekt Config

```python
"""
Core configuration - FAST and NON-BLOCKING.
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Settings - only reads env vars, no I/O."""
    
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "ministral:3b"
    
    class Config:
        env_file = ".env"  # Single file only
        env_file_encoding = "utf-8"
        case_sensitive = False
        env_ignore_empty = True


# Fast instantiation - should be instant
settings = Settings()
```

---

## Sammanfattning

**Vad var felet:**
1. `env_file = [".env", "../.env", "../../.env"]` → blockerade på filsystem
2. Användning av `python -c` med långa strängar → shell-problem
3. Hårdkodade sökvägar i debug-logging

**Hur förhindra:**
1. ✅ Använd `env_file = ".env"` (singular)
2. ✅ Använd testfiler istället för `python -c` för längre kommandon
3. ✅ Se till att config är "ren" - inga blocking operations
4. ✅ Lägg till CI-check som timeoutar config-import
5. ✅ Dokumentera regler i denna fil

