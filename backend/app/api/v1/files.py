from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.models.user import User
from backend.app.services.local_storage_service import LocalStorageService
from backend.app.api.deps import get_current_user

router = APIRouter(prefix="/files", tags=["Local File Storage"])

@router.get("/{file_id}")
@router.get("/{file_id}/download")
async def download_file(
    file_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    content, filename, mime, checksum = await LocalStorageService.get_file_bytes(db, file_id)

    return Response(
        content=content,
        media_type=mime,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-Checksum-SHA256": checksum
        }
    )
