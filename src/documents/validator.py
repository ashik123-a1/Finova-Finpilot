"""
Document Validation, File Integrity, and Storage Management.
Enforces size limits, mime-type verification, magic header checks, SHA-256 deduplication,
and safe filesystem storage.
"""

from __future__ import annotations

import hashlib
import io
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Tuple, Optional
from PIL import Image
from sqlalchemy.orm import Session
from sqlalchemy import select

from src.config import settings
from src.core.exceptions import DocumentProcessingError
from src.database.models import Document, Shop

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".pdf"}
ALLOWED_MIME_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "application/pdf",
}

# Magic bytes signature validation
IMAGE_SIGNATURES = {
    b"\xff\xd8\xff": "image/jpeg",
    b"\x89PNG\r\n\x1a\n": "image/png",
    b"RIFF": "image/webp",
    b"%PDF": "application/pdf",
}


def compute_file_hash(content: bytes) -> str:
    """Computes SHA-256 hash of file bytes for exact deduplication."""
    return hashlib.sha256(content).hexdigest()


def validate_file_content(content: bytes, filename: str) -> Tuple[str, str]:
    """
    Validates file size, extension, and content signatures.
    Returns (sanitized_extension, detected_mime_type).
    """
    if len(content) > settings.MAX_UPLOAD_SIZE_BYTES:
        raise DocumentProcessingError(
            f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_BYTES / (1024*1024):.1f} MB."
        )

    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise DocumentProcessingError(
            f"Unsupported file format '{ext}'. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )

    # Inspect magic bytes
    detected_mime: Optional[str] = None
    for sig, mime in IMAGE_SIGNATURES.items():
        if content.startswith(sig):
            detected_mime = mime
            break

    if not detected_mime:
        raise DocumentProcessingError("Invalid file content: Signature does not match permitted file types.")

    # Additional image corruption check for image formats
    if detected_mime.startswith("image/"):
        try:
            with Image.open(io.BytesIO(content)) as img:
                img.verify()
        except Exception as e:
            raise DocumentProcessingError(f"Corrupt or unreadable image file: {e}")

    return ext, detected_mime


def check_for_duplicate_document(
    session: Session, shop_id: int, file_hash: str
) -> Optional[Document]:
    """Checks if a document with this identical SHA-256 hash already exists in this shop."""
    stmt = select(Document).where(
        Document.shop_id == shop_id,
        Document.file_hash_sha256 == file_hash,
    )
    return session.scalars(stmt).first()


def save_uploaded_file(
    content: bytes,
    business_id: int,
    shop_id: int,
    original_filename: str,
    file_hash: str,
    extension: str,
) -> Path:
    """
    Persists uploaded document into structured local storage:
    storage/documents/{business_id}/{year}/{month}/{file_hash}{ext}
    Prevents path traversal and directory exposure.
    """
    now = datetime.now(timezone.utc)
    target_dir = settings.DOCUMENTS_STORAGE_PATH / str(business_id) / f"{now.year:04d}" / f"{now.month:02d}"
    target_dir.mkdir(parents=True, exist_ok=True)

    target_file = target_dir / f"{file_hash}{extension}"
    if not target_file.exists():
        target_file.write_bytes(content)

    return target_file
