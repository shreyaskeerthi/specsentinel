"""File storage service for PDF uploads."""

import os
import uuid
from pathlib import Path

import aiofiles

from app.core.config import settings


class StorageService:
    """
    Local file storage service for uploaded PDFs.
    TODO: Replace with S3/GCS for production deployment.
    """

    def __init__(self, base_path: str | None = None):
        self.base_path = Path(base_path or settings.FILE_STORAGE_PATH)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _get_org_path(self, organization_id: uuid.UUID) -> Path:
        """Get organization-specific storage path."""
        org_path = self.base_path / str(organization_id)
        org_path.mkdir(parents=True, exist_ok=True)
        return org_path

    async def save_file(
        self,
        file_content: bytes,
        organization_id: uuid.UUID,
        original_filename: str,
    ) -> tuple[str, str]:
        """
        Save uploaded file to storage.
        Returns (unique_filename, full_file_path).
        """
        # Generate unique filename
        ext = Path(original_filename).suffix or ".pdf"
        unique_filename = f"{uuid.uuid4()}{ext}"

        # Build path
        org_path = self._get_org_path(organization_id)
        file_path = org_path / unique_filename

        # Write file
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(file_content)

        return unique_filename, str(file_path)

    async def get_file(self, file_path: str) -> bytes | None:
        """Read file from storage."""
        path = Path(file_path)
        if not path.exists():
            return None

        async with aiofiles.open(path, "rb") as f:
            return await f.read()

    async def delete_file(self, file_path: str) -> bool:
        """Delete file from storage."""
        path = Path(file_path)
        if path.exists():
            os.remove(path)
            return True
        return False

    def get_file_size(self, file_path: str) -> int:
        """Get file size in bytes."""
        path = Path(file_path)
        if path.exists():
            return path.stat().st_size
        return 0


# Singleton instance
storage_service = StorageService()
