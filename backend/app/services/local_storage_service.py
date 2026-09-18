import os
import hashlib
import uuid
import mimetypes
from datetime import datetime, timezone
from typing import Tuple, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, UploadFile

from backend.app.models.storage import FileRecord, FileVersion

STORAGE_ROOT = os.getenv("STORAGE_ROOT", os.path.abspath("./local_storage"))

ALLOWED_EXTENSIONS = {
    ".pdf", ".docx", ".pptx", ".xlsx", ".csv", ".txt", 
    ".png", ".jpg", ".jpeg", ".zip"
}

# Magic bytes signature header check
MAGIC_BYTES = {
    b"%PDF": "application/pdf",
    b"PK\x03\x04": "application/zip", # also docx, pptx, xlsx
    b"\x89PNG\r\n\x1a\n": "image/png",
    b"\xff\xd8\xff": "image/jpeg"
}

class LocalStorageService:
    @staticmethod
    def ensure_directories():
        for sub in ["assignments", "submissions", "resources", "backups", "temp"]:
            d = os.path.join(STORAGE_ROOT, sub)
            os.makedirs(d, exist_ok=True)

    @staticmethod
    def calculate_sha256(data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()

    @staticmethod
    def validate_file(filename: str, content: bytes) -> str:
        # Check path traversal
        clean_name = os.path.basename(filename)
        ext = os.path.splitext(clean_name)[1].lower()

        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=400, detail=f"File extension '{ext}' is not permitted.")

        # Check for executable signature evasion (e.g. exe header 'MZ')
        if content.startswith(b"MZ") or content.startswith(b"\x7fELF"):
            raise HTTPException(status_code=400, detail="Executable binaries are strictly prohibited.")

        mime = mimetypes.guess_type(clean_name)[0] or "application/octet-stream"
        return mime

    @classmethod
    async def save_file(
        cls,
        db: AsyncSession,
        file_bytes: bytes,
        original_filename: str,
        uploaded_by_user_id: str,
        category: str = "assignments", # assignments, submissions, resources, backups
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        existing_file_id: Optional[str] = None
    ) -> FileRecord:
        cls.ensure_directories()
        mime_type = cls.validate_file(original_filename, file_bytes)
        checksum = cls.calculate_sha256(file_bytes)
        file_size = len(file_bytes)

        clean_ext = os.path.splitext(original_filename)[1].lower()
        secure_filename = f"{uuid.uuid4().hex}{clean_ext}"
        rel_path = os.path.join(category, secure_filename)
        abs_path = os.path.join(STORAGE_ROOT, rel_path)

        # Write to local filesystem
        with open(abs_path, "wb") as f:
            f.write(file_bytes)

        # Handle versioning if replacing an existing file
        if existing_file_id:
            result = await db.execute(select(FileRecord).where(FileRecord.id == existing_file_id))
            file_rec = result.scalar_one_or_none()
            if file_rec:
                # Create historical version
                ver = FileVersion(
                    file_id=file_rec.id,
                    version_number=file_rec.version,
                    storage_path=file_rec.storage_path,
                    checksum_sha256=file_rec.checksum_sha256,
                    uploaded_by=file_rec.uploaded_by
                )
                db.add(ver)

                # Update current file record
                file_rec.original_filename = original_filename
                file_rec.stored_filename = secure_filename
                file_rec.storage_path = rel_path
                file_rec.mime_type = mime_type
                file_rec.file_size = file_size
                file_rec.checksum_sha256 = checksum
                file_rec.version += 1
                file_rec.uploaded_by = uploaded_by_user_id
                await db.commit()
                await db.refresh(file_rec)
                return file_rec

        # Create new FileRecord
        file_rec = FileRecord(
            original_filename=original_filename,
            stored_filename=secure_filename,
            storage_path=rel_path,
            mime_type=mime_type,
            file_size=file_size,
            checksum_sha256=checksum,
            uploaded_by=uploaded_by_user_id,
            entity_type=entity_type,
            entity_id=entity_id,
            version=1,
            status="ACTIVE"
        )
        db.add(file_rec)
        await db.commit()
        await db.refresh(file_rec)
        return file_rec

    @classmethod
    async def get_file_bytes(cls, db: AsyncSession, file_id: str) -> Tuple[bytes, str, str, str]:
        """Returns (content_bytes, original_filename, mime_type, checksum_sha256)"""
        result = await db.execute(select(FileRecord).where(FileRecord.id == file_id))
        file_rec = result.scalar_one_or_none()
        if not file_rec:
            raise HTTPException(status_code=404, detail="File metadata not found in database.")

        abs_path = os.path.join(STORAGE_ROOT, file_rec.storage_path)
        if not os.path.exists(abs_path):
            raise HTTPException(status_code=404, detail="Document unavailable on local storage. Please contact administrator.")

        with open(abs_path, "rb") as f:
            content = f.read()

        # Checksum integrity verification
        if cls.calculate_sha256(content) != file_rec.checksum_sha256:
            raise HTTPException(status_code=500, detail="File corruption detected: SHA-256 checksum mismatch.")

        return content, file_rec.original_filename, file_rec.mime_type, file_rec.checksum_sha256
