# User Safety - Användarsäkerhet

Detta dokument beskriver hur Copy/Paste skyddar användare från misstag och säkerställer medvetna beslut.

## Översikt

Copy/Paste är designat för att skydda användare från oavsiktliga misstag genom explicit bekräftelse, dry-run som default, och tydliga receipts.

## Original Lock

### Princip

**Original transcript får aldrig redigeras direkt.**

**Beteende:**
- Original transcript är låst för redigering
- Endast ersättning via explicit endpoint
- Skyddar källmaterial från oavsiktlig förstörelse

**Dokumentation:**
- "Originalet är låst för att skydda källmaterial"
- Tydligt för användare varför detta finns

## Dry-Run som Default

### Princip

**Farliga operationer körs i dry-run-läge som standard.**

**Operationer med dry-run:**
- `destroy` (radera projekt)
- `export-and-destroy` (exportera och radera)

**Beteende:**
- Default: `dry_run=true`
- Kräver `{ confirm: true, reason: "..." }` för faktisk destruktion
- Returnerar vad som skulle hända utan att faktiskt göra det

**Exempel:**
```json
// Request (dry-run)
POST /api/v1/projects/123/destroy
{
  "dry_run": true  // Default
}

// Response
{
  "dry_run": true,
  "would_delete": {
    "transcripts": 3,
    "notes": 2,
    "files": 1
  },
  "message": "This would permanently delete 6 artifacts"
}

// Request (actual deletion)
POST /api/v1/projects/123/destroy
{
  "confirm": true,
  "reason": "Projektet är klart och materialet ska raderas enligt policy"
}

// Response
{
  "status": "deleted",
  "receipt_id": "uuid-here",
  "deleted_at": "2025-12-23T10:00:00",
  "counts": {
    "transcripts": 3,
    "notes": 2,
    "files": 1
  }
}
```

## Receipt System

### Princip

**Alla destruktiva handlingar returnerar receipt.**

**Receipt innehåller:**
- `receipt_id` (UUID för spårbarhet)
- `destroyed_at` (timestamp)
- `counts` (antal raderade artefakter)
- `reason` (användarens angivna anledning)

**Användning:**
- Spårbarhet för juridiska/etiska granskningar
- Verifiering att radering faktiskt skedde
- Audit trail för destruktiva operationer

## Human-in-the-Loop

### Princip

**Inga autonoma beslut - alltid mänsklig kontroll.**

**Regler:**
- **Inga autonoma content-förändringar:** Systemet ändrar aldrig innehåll automatiskt
- **Inga "auto-share":** Material delas aldrig automatiskt
- **All export/destroy kräver explicit confirm:** Användare måste bekräfta med `confirm: true` och ange `reason`

**Autonomy Guard:**
- Regelbaserade checks (NO AI)
- Flaggar potentiella problem
- Rekommenderar åtgärder
- Blockar ALDRIG handlingar
- Användaren har alltid sista ordet

## Error Prevention

### Validation

**Strikt validering:**
- Alla inputs valideras innan processing
- Tydliga felmeddelanden
- Inga "tysta fel"

**Exempel:**
```json
// Invalid request
POST /api/v1/transcripts/123/segments
{
  "segments": [
    {
      "start_ms": 5000,
      "end_ms": 0  // Invalid: start > end
    }
  ]
}

// Response
{
  "error": {
    "code": "validation_error",
    "message": "Invalid segment: start_ms (5000) must be < end_ms (0)",
    "request_id": "uuid-here"
  }
}
```

## Transparency

### Process-spårbarhet

**Audit trails visar:**
- Vad som hände (action)
- När det hände (timestamp)
- Vem som gjorde det (actor)
- Varför (reason, om destruktiv operation)

**Audit trails visar ALDRIG:**
- Vad som sades (content)
- Källidentifierare (IP, filnamn, etc.)

## Best Practices

### För Användare

**Före destruktiva operationer:**
- Använd dry-run först
- Verifiera vad som kommer raderas
- Ange tydlig reason
- Spara receipt för spårbarhet

**Vid misstag:**
- Kontrollera audit logs
- Verifiera med receipt_id
- Kontakta support om återställning behövs

### För Utvecklare

**När du implementerar destruktiva endpoints:**
- Default till dry-run
- Kräv explicit confirm
- Returnera receipt
- Logga audit event (utan content)

## Support

För frågor om användarsäkerhet:
- Se `docs/journalism-safety.md` för källskydd
- Se `docs/security.md` för tekniska säkerhetsdetaljer
- Kontakta support-teamet

