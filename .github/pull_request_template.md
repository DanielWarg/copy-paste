### Mål & Scope

* [ ] Matchar PRD/ADR
* [ ] Scope tydligt definierat

### DoD & Kvalitet

* [ ] Tester gröna (backend + frontend)
* [ ] Coverage ≥ gates (70/60)
* [ ] Lint/type OK
* [ ] A11y OK (om UI-ändringar)
* [ ] Doc-audit OK
* [ ] Zero-hardcoding OK
* [ ] `.env.example` uppdaterad
* [ ] Inga secrets i git

### Säkerhet

* [ ] SSRF-skydd verifierat (om URL-fetching ändrats)
* [ ] Output sanitization verifierat (om LLM-output ändrats)
* [ ] Rate limiting verifierat (om endpoints ändrats)
* [ ] Audit trail verifierat (om operationer ändrats)

### Deployment

* [ ] Migration scripts testade
* [ ] Docker images byggs korrekt
* [ ] Environment variables dokumenterade

---

