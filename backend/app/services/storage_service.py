import hashlib
import os
from pathlib import Path
from typing import Tuple
import uuid
from fastapi import HTTPException, UploadFile, status

from app.core.config import settings

CHUNK_SIZE = 64 * 1024  # 64 KB chunks for memory efficiency


def get_base_upload_dir() -> Path:
    """Get absolute path to base upload directory."""
    return Path(os.path.abspath(settings.UPLOAD_DIR))


def get_safe_path(storage_path: str) -> Path:
    """Validate that the storage path does not escape the configured base upload directory."""
    base_dir = get_base_upload_dir()
    target_path = Path(os.path.abspath(storage_path))

    try:
        target_path.relative_to(base_dir)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid storage path: path traversal detected.",
        )

    return target_path


def file_exists(storage_path: str) -> bool:
    """Check if the physical file exists on disk."""
    try:
        target = get_safe_path(storage_path)
        return target.is_file()
    except Exception:
        return False


def delete_file(storage_path: str) -> bool:
    """Safely delete physical file from disk."""
    try:
        target = get_safe_path(storage_path)
        if target.is_file():
            target.unlink()
            return True
    except Exception:
        pass
    return False


def delete_tender_directory(tender_id: uuid.UUID) -> bool:
    """Safely delete all files and directory for a specific tender."""
    import shutil
    try:
        base_dir = get_base_upload_dir()
        tender_dir = base_dir / "tenders" / str(tender_id)
        if tender_dir.is_dir():
            shutil.rmtree(tender_dir, ignore_errors=True)
            return True
    except Exception:
        pass
    return False


async def save_tender_pdf(
    tender_id: uuid.UUID,
    upload_file: UploadFile,
) -> Tuple[str, str, int, str]:
    """Stream and validate uploaded tender PDF, saving to disk and calculating SHA-256.
    
    Returns:
        (storage_path, safe_filename, file_size, sha256_hash)
    """
    original_filename = upload_file.filename or "document.pdf"
    
    # 1. Extension validation
    if not original_filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files (.pdf) are allowed.",
        )

    # 2. Prepare target directory
    base_dir = get_base_upload_dir()
    tender_dir = base_dir / "tenders" / str(tender_id)
    tender_dir.mkdir(parents=True, exist_ok=True)

    document_uuid = uuid.uuid4()
    safe_filename = f"{document_uuid}.pdf"
    target_path = tender_dir / safe_filename
    storage_path = str(target_path)

    # 3. Stream write, compute SHA-256, validate magic bytes and max size
    max_size_bytes = settings.MAX_DOCUMENT_SIZE_MB * 1024 * 1024
    hasher = hashlib.sha256()
    bytes_written = 0
    first_chunk = True

    try:
        with open(target_path, "wb") as f_out:
            while True:
                chunk = await upload_file.read(CHUNK_SIZE)
                if not chunk:
                    break

                # Magic signature check on first bytes
                if first_chunk:
                    first_chunk = False
                    if not chunk.startswith(b"%PDF-"):
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Invalid PDF content: file header does not match PDF signature (%PDF-).",
                        )

                bytes_written += len(chunk)
                if bytes_written > max_size_bytes:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"File size exceeds maximum allowed limit of {settings.MAX_DOCUMENT_SIZE_MB}MB.",
                    )

                hasher.update(chunk)
                f_out.write(chunk)

        if bytes_written == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty (0 bytes).",
            )

    except Exception:
        # Cleanup file on any error
        if target_path.exists():
            try:
                target_path.unlink()
            except Exception:
                pass
        raise

    sha256_hash = hasher.hexdigest()
    return storage_path, safe_filename, bytes_written, sha256_hash
