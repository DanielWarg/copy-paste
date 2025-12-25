# Data Lifecycle - Copy/Paste

**Version:** 1.0.0  
**Status:** Canonical Document (Single Source of Truth)  
**Senast uppdaterad:** 2025-12-25

---

## Översikt

Detta dokument beskriver hur data skapas, krypteras, lagras och raderas i Copy/Paste-systemet. Alla steg är designade för GDPR-compliance och journalistiskt källskydd.

---

## Data Creation

### 1. Upload Flow

**Steg:**
1. Användare laddar upp fil (audio, text, dokument)
2. Backend validerar fil (magic bytes + extension)
3. Beräknar SHA256 hash
4. Krypterar fil med Fernet (encryption-at-rest)
5. Lagrar som `{sha256}.bin` (inte original filename)
6. Sparar metadata i DB (original_filename, sha256, size_bytes, mime_type)

**Säkerhet:**
- Original filename lagras **INTE** på disk (endast SHA256)
- Fil krypteras innan lagring (Fernet)
- Inga filnamn/content i logs

**Exempel (Audio Upload):**
```python
# backend/app/modules/record/service.py
def upload_audio(...):
    # 1. Validera fil
    validate_audio_file(file_content, filename)
    
    # 2. Beräkna hash
    sha256 = compute_file_hash(file_content)
    
    # 3. Kryptera och lagra
    storage_path = store_file(file_content, sha256)
    
    # 4. Spara metadata i DB
    audio_asset = AudioAsset(
        sha256=sha256,
        storage_path=storage_path,  # Internal path: {sha256}.bin
        # INGA filnamn/content i logs
    )
```

---

## Data Storage

### Encryption-at-Rest

**Princip:**
- Alla filer krypteras innan lagring (Fernet symmetric encryption)
- Encryption key: Från `PROJECT_FILES_KEY` (Docker secrets i prod_brutal)
- Lagras som `{sha256}.bin` (inte original filename)

**Implementation:**
- `backend/app/modules/projects/file_storage.py` (eller motsvarande)
- Fernet encryption (cryptography library)
- Base64 URL-safe encoded keys

**Storage Path:**
- `/app/data/files/{sha256}.bin` (read-only filesystem except /app/data)
- Original filename: Endast i DB (aldrig på disk)

### Database Metadata

**Princip:**
- Metadata sparas i DB (original_filename, sha256, size_bytes, mime_type)
- **INGEN content** i DB (endast metadata)
- Original filename: Endast i DB (aldrig på disk)

**Exempel (ProjectFile):**
```python
class ProjectFile(Base):
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey(...))
    original_filename = Column(String, nullable=False)  # Only in DB
    sha256 = Column(String, nullable=False, unique=True)
    mime_type = Column(String, nullable=False)
    size_bytes = Column(Integer, nullable=False)
    storage_path = Column(String, nullable=False)  # Internal: {sha256}.bin
    # INGEN content field
```

---

## Data Retrieval

### Reading Files

**Steg:**
1. Hämta metadata från DB (via sha256)
2. Läsa krypterad fil från disk (`{sha256}.bin`)
3. Dekryptera med Fernet
4. Returnera decrypted content

**Säkerhet:**
- Original filename exponeras endast via API (inte på disk)
- Content dekrypteras endast vid retrieval (inte i cache)
- Inga filnamn/content i logs

**Exempel:**
```python
# backend/app/modules/projects/file_storage.py
def retrieve_file(sha256: str) -> bytes:
    storage_path = storage_dir / f"{sha256}.bin"
    encrypted = storage_path.read_bytes()
    return decrypt_content(encrypted)
```

---

## Data Deletion

### Secure Delete Policy

**Princip:**
- Atomic two-phase destroy (pending → destroyed)
- Best-effort overwrite (overwrite med zeros innan radering)
- Receipt för alla destruktiva handlingar

**Vad vi garanterar:**
- ✅ Filer raderas från filsystemet
- ✅ Krypterade blobs tas bort
- ✅ Best-effort overwrite (kan inte garanteras på SSD)

**Vad vi INTE garanterar:**
- ❌ Fysisk overwrite på SSD (wear leveling, TRIM)
- ❌ Data recovery omöjlighet (kräver disk encryption)

**Säkerhetsmodell:**
- Vi litar på **encryption-at-rest** + **deletion of encrypted blobs**
- Om filen är krypterad och blobben är raderad: innehållet är säkert även om fysiska bitar finns kvar
- För riktig garanti: Använd disk encryption (LUKS, BitLocker) + kontrollerad storage

### Destruction Flow

**Steg:**
1. Användare begär destruction (med `confirm=true` och `reason`)
2. Set `destroy_status=pending` + generera `receipt_id`
3. Perform deletions:
   - Radera fil från disk (best-effort overwrite)
   - Radera metadata från DB
   - Radera relaterade records (cascade)
4. Set `destroy_status=destroyed`
5. Returnera receipt (proof of destruction)

**Atomic Behavior:**
- Om crash inträffar: Nästa destroy-call återupptar från pending
- Inga partial states (antingen pending eller destroyed, aldrig halvfärdigt)

**Exempel:**
```python
# backend/app/modules/record/service.py
def destroy_record(transcript_id: int, confirm: bool, reason: str):
    if not confirm:
        return {"dry_run": True, "would_delete": [...]}
    
    # Phase 1: Set pending
    transcript.destroy_status = "pending"
    receipt_id = str(uuid4())
    transcript.receipt_id = receipt_id
    db.commit()
    
    # Phase 2: Perform deletions
    delete_file(sha256)  # Best-effort overwrite + unlink
    db.delete(transcript)
    db.commit()
    
    return {"receipt_id": receipt_id, "status": "destroyed"}
```

---

## GDPR Compliance

### Retention Policies

**Princip:**
- Konfigurerbart per projekt (t.ex. `RECORDER_RETENTION_DAYS=14`)
- Automatisk rensning efter X dagar (om konfigurerat)
- Hard delete: När material raderas, raderas det permanent (med receipt)

**För känsliga projekt:**
- Filer kan sparas som temp-only (dokumenteras per projekt)
- Överväg automatisk rensning efter X dagar (konfigurerbart)

### Right to Erasure

**Princip:**
- Användare kan begära radering av data (via destruction endpoint)
- Receipt returneras (proof of erasure)
- Data raderas permanent (best-effort secure delete)

**Implementation:**
- `DELETE /api/v1/record/{id}` eller `POST /api/v1/record/{id}/destroy`
- Kräver `confirm=true` och `reason` (audit trail)
- Returnerar receipt (proof of destruction)

---

## Privacy-Safe Logging

### No-Content Logging

**Princip:**
- Inga filnamn/content i logs
- Endast metadata (counts, ids, format)
- Privacy guard skyddar detta

**Exempel:**
```python
# ✅ RÄTT
logger.info(
    "file_uploaded",
    extra={
        "file_id": file_id,
        "size_bytes": size_bytes,
        "mime_type": mime_type,
        # INGA filnamn/content
    }
)

# ❌ FEL
logger.info(f"Uploaded: {filename}")  # Filnamn i log
logger.info(f"Content: {file_content}")  # Content i log
```

**Verification:** `make check-security-invariants` → `check_no_content_in_logs()`

---

## Audit Trail

### Metadata-Only Audit

**Princip:**
- Audit events innehåller endast metadata (counts, ids, format)
- **INGEN content** i audit events
- **INGA filnamn** i audit events (om SOURCE_SAFETY_MODE är aktivt)

**Exempel:**
```python
class ProjectAuditEvent(Base):
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey(...))
    event_type = Column(String, nullable=False)  # "created", "updated", "destroyed"
    metadata = Column(JSON, nullable=True)  # {counts, ids, format} - INGEN content
    created_at = Column(DateTime, nullable=False)
    # INGA filnamn/content fields
```

---

## Referenser

- **System Overview:** [SYSTEM_OVERVIEW.md](./SYSTEM_OVERVIEW.md)
- **Security Model:** [SECURITY_MODEL.md](./SECURITY_MODEL.md)
- **Module Model:** [MODULE_MODEL.md](./MODULE_MODEL.md)

---

**Detta är en canonical document. Uppdatera endast om datalifecycle eller GDPR-policy ändras.**

