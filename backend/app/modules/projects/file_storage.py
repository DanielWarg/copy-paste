"""File storage with encryption - paranoid security."""
import base64
import hashlib
import os
from pathlib import Path
from typing import Optional

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from app.core.config import settings


# Storage directory (will be created if needed)
_STORAGE_DIR = Path("/app/data/files")  # Read-only filesystem except /app/data


def _get_encryption_key() -> bytes:
    """Get encryption key from environment (base64 encoded).
    
    Returns:
        Fernet encryption key
        
    Raises:
        ValueError: If PROJECT_FILES_KEY not set
    """
    key_b64 = os.getenv("PROJECT_FILES_KEY")
    if not key_b64:
        raise ValueError(
            "PROJECT_FILES_KEY environment variable not set. "
            "Required for file encryption. Set a base64-encoded Fernet key."
        )
    
    try:
        return base64.b64decode(key_b64)
    except Exception as e:
        raise ValueError(f"Invalid PROJECT_FILES_KEY format (must be base64): {e}")


def _ensure_storage_dir() -> Path:
    """Ensure storage directory exists.
    
    Returns:
        Storage directory path
    """
    _STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    return _STORAGE_DIR


def compute_file_hash(content: bytes) -> str:
    """Compute SHA256 hash of file content.
    
    Args:
        content: File content bytes
        
    Returns:
        SHA256 hex digest
    """
    return hashlib.sha256(content).hexdigest()


def encrypt_content(content: bytes) -> bytes:
    """Encrypt file content.
    
    Args:
        content: File content bytes
        
    Returns:
        Encrypted content bytes
    """
    key = _get_encryption_key()
    fernet = Fernet(key)
    return fernet.encrypt(content)


def decrypt_content(encrypted_content: bytes) -> bytes:
    """Decrypt file content.
    
    Args:
        encrypted_content: Encrypted content bytes
        
    Returns:
        Decrypted content bytes
    """
    key = _get_encryption_key()
    fernet = Fernet(key)
    return fernet.decrypt(encrypted_content)


def store_file(content: bytes, sha256: str) -> str:
    """Store encrypted file on disk.
    
    Files are stored as {sha256}.bin (no original filename on disk).
    Content is encrypted before storage.
    
    Args:
        content: File content bytes
        sha256: SHA256 hash of content (for verification)
        
    Returns:
        Storage path (relative to storage dir)
    """
    # Verify hash matches
    actual_hash = compute_file_hash(content)
    if actual_hash != sha256:
        raise ValueError(f"Hash mismatch: expected {sha256}, got {actual_hash}")
    
    # Encrypt content
    encrypted = encrypt_content(content)
    
    # Ensure storage directory exists
    storage_dir = _ensure_storage_dir()
    
    # Store as {sha256}.bin
    storage_path = storage_dir / f"{sha256}.bin"
    
    # Write encrypted content
    storage_path.write_bytes(encrypted)
    
    # Return relative path
    return f"{sha256}.bin"


def retrieve_file(sha256: str) -> bytes:
    """Retrieve and decrypt file from disk.
    
    Args:
        sha256: SHA256 hash (filename)
        
    Returns:
        Decrypted content bytes
        
    Raises:
        FileNotFoundError: If file doesn't exist
    """
    storage_dir = _ensure_storage_dir()
    storage_path = storage_dir / f"{sha256}.bin"
    
    if not storage_path.exists():
        raise FileNotFoundError(f"File not found: {sha256}")
    
    # Read encrypted content
    encrypted = storage_path.read_bytes()
    
    # Decrypt
    return decrypt_content(encrypted)


def delete_file(sha256: str) -> None:
    """Delete file from disk (best-effort secure deletion).
    
    **Secure Delete Policy:**
    - On SSD: Cannot guarantee overwrite (wear leveling, TRIM)
    - Real guarantee requires: disk encryption + controlled storage
    - We rely on: encryption-at-rest + deletion of encrypted blobs
    
    Args:
        sha256: SHA256 hash (filename)
    """
    storage_dir = _ensure_storage_dir()
    storage_path = storage_dir / f"{sha256}.bin"
    
    if storage_path.exists():
        # Best-effort overwrite (may not work on SSD)
        try:
            file_size = storage_path.stat().st_size
            # Overwrite with zeros
            storage_path.write_bytes(b"\x00" * file_size)
            # Sync to disk (if supported)
            try:
                os.fsync(storage_path.fileno())
            except Exception:
                pass  # Best effort
        except Exception:
            pass  # Best effort - continue with deletion
        
        # Delete file
        storage_path.unlink()


def generate_encryption_key() -> str:
    """Generate a new Fernet encryption key (base64 encoded).
    
    Returns:
        Base64-encoded Fernet key (for use in PROJECT_FILES_KEY)
    """
    key = Fernet.generate_key()
    return base64.b64encode(key).decode("utf-8")

