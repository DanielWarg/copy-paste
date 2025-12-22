# Agent Constitution Reference

Detta dokument är en referens för längre "constitution" eller systemprompts som kan användas för AI-assistenter i projektet.

## Syfte

Denna referens är tänkt som:
- Inspirationsbank för längre regler
- Referens för teamet
- Dokumentation av beslutsprocesser

## Relation till agent.md

- **agent.md** (`.cursor/rules/agent.md`): Kort, operativa regler för dagligt arbete
- **Denna fil**: Längre constitution för referens

## Exempel: Längre Constitution

### Principles

1. **Security First**: Alla beslut ska prioritera säkerhet
2. **Privacy by Design**: Data privacy från start
3. **Audit Everything**: Alla operationer ska vara spårbara
4. **Fail Safe**: Vid fel, returnera safe fallback

### Code Quality

1. **No Placeholders**: Inga TODOs eller placeholders i production code
2. **Full Files**: Vid ändring, ändra hela filen (inte delar)
3. **Tests First**: Tests före implementation
4. **Documentation**: Dokumentera beslut och arkitektur

### Security

1. **Input Validation**: Validera all input
2. **Output Sanitization**: Sanitize all output
3. **Rate Limiting**: Alla endpoints ska ha rate limiting
4. **Audit Trail**: Logga alla operationer

## Användning

Denna fil kan användas som:
- Referens när man behöver längre regler
- Inspirationsbank för nya regler
- Dokumentation av beslutsprocesser

## Relation till Implementation

Dessa principer är redan implementerade i:
- Backend security components
- Frontend safe rendering
- Audit trail service
- Rate limiting middleware

