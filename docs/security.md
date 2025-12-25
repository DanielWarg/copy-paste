# Security Overview

**Detta dokument är en sammanfattning. För fullständig säkerhetsdokumentation, se [security-complete.md](security-complete.md).**

## Executive Summary

Copy/Paste är ett journalistiskt AI-assistanssystem med fokus på källskydd, dataskydd och integritet. Systemet implementerar "Brutal Security Profile v3.1" som garanterar:

- **Zero egress**: Backend kan inte nå internet (infrastruktur + kod-nivå)
- **mTLS enforcement**: All extern åtkomst över HTTPS kräver klientcertifikat
- **Privacy Gate**: Ingen rå PII skickas till externa AI:er
- **Fail-closed design**: Systemet startar inte i osäkert läge

## Säkerhetsgarantier

Systemet skyddar:
- Källkontakter och råmaterial från källor
- Transkriptioner av känsliga samtal
- Artiklar under utveckling
- Personuppgifter som måste skyddas enligt GDPR

## Detaljerad information

Se [security-complete.md](security-complete.md) för komplett säkerhetsdokumentation inklusive:
- Säkerhetsarkitektur
- Threat Model
- Säkerhetsmoduler
- Operational Security
- Journalism Safety & Källskydd
- User Safety
- Privacy Gate
- Certificate Lifecycle
- Incident Response
- Verification & Testing
- Risk Assessment
- Compliance & Regulatory


