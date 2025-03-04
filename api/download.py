import os

from fastapi.exceptions import HTTPException
from fastapi.responses import StreamingResponse
from fastapi.routing import APIRouter



download_router = APIRouter(prefix="/download", tags=["Download"])

@download_router.get("/kovaaks_tracker.exe")
async def download_binary():
    filename = "kovaaks_tracker.exe"
    file_path = os.path.join("api/bin", filename)

    if os.path.exists(file_path):
        file_like = open(file_path, mode="rb")
        return StreamingResponse(file_like, media_type="application/octet-stream")
    else:
        raise HTTPException(status_code=404)