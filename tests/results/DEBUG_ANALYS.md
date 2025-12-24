# DEBUG ANALYS: Varför Tester Hänger Sig

## Hypoteser om varför testerna hänger sig:

### Hypotes A: Backend körs inte / endpoint saknas
- **Bevis:** Testet väntar på server som inte svarar
- **Instrumentering:** Log när scrub_v2 startar

### Hypotes B: Layer 0 preflight tar för lång tid
- **Bevis:** Preflight körs synkront men borde vara snabb
- **Instrumentering:** Log före/efter L0

### Hypotes C: Ollama-anrop blockerar (Layer 1 anonymization)
- **Bevis:** Ollama har 30s timeout, kan hänga om Ollama inte körs
- **Instrumentering:** Log före/efter anonymizer.anonymize() call

### Hypotes D: Layer 2 verification tar för lång tid
- **Bevis:** Regex-baserad, borde vara snabb men kan hänga på lång text
- **Instrumentering:** Log före/efter verify_anonymization()

### Hypotes E: Exception i Layer 1 hanteras fel
- **Bevis:** Om anonymizer kraschar kan clean_text vara i felaktigt tillstånd
- **Instrumentering:** Log när exception fångas

### Hypotes F: Layer 3 semantic audit blockerar på Ollama
- **Bevis:** Semantic audit anropar Ollama med 30s timeout, kan hänga
- **Instrumentering:** Log före/efter semantic_audit() call, mät elapsed time

## Förväntade Problem:

1. **Ollama inte igång:** Om Ollama inte körs kommer httpx.AsyncClient att vänta 30 sekunder PER anrop innan timeout. Med Layer 1 + Layer 3 = 60+ sekunder väntetid.

2. **Ingen timeout i testet:** Testet har timeout=30 för scrub_v2, men om Ollama tar längre tid kan det hänga.

3. **Blocking calls:** Om Ollama inte svarar alls, kommer async calls att vänta tills timeout.

## Lösningar:

1. **Kontrollera Ollama:** Se till att Ollama körs innan tester
2. **Kortare timeout:** Sätt kortare timeout för Ollama-anrop (t.ex. 10s)
3. **Timeout i tester:** Öka timeout i tester eller gör dem mer robusta
4. **Fallback:** Se till att regex fallback fungerar när Ollama inte svarar

