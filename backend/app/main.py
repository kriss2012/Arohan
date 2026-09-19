import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from backend.app.core.config import settings
from backend.app.core.database import init_db, AsyncSessionLocal
from backend.app.services.seed_service import seed_database
from backend.app.services.local_storage_service import LocalStorageService
from backend.app.api.v1 import (
    auth, curriculum, mcat, arohan, faculty, 
    exam_controller, placement, admin, assignments, files, progress, security
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure local directories, initialize tables, seed data
    LocalStorageService.ensure_directories()
    await init_db()
    async with AsyncSessionLocal() as session:
        await seed_database(session)
    yield
    # Shutdown

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Institute Student Development Platform (ISDP) - Local Institutional Engine",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Server-Time-UTC", "X-Request-ID"]
)

# Server-Authoritative Time & Distributed Tracing Middleware
@app.middleware("http")
async def add_server_time_and_request_id(request: Request, call_next):
    request_id = str(uuid.uuid4())
    server_time_utc = datetime.now(timezone.utc).isoformat()

    response: Response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Server-Time-UTC"] = server_time_utc
    return response

# Include Routers
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(admin.router, prefix=settings.API_V1_STR)
app.include_router(curriculum.router, prefix=settings.API_V1_STR)
app.include_router(assignments.router, prefix=settings.API_V1_STR)
app.include_router(files.router, prefix=settings.API_V1_STR)
app.include_router(progress.router, prefix=settings.API_V1_STR)
app.include_router(mcat.router, prefix=settings.API_V1_STR)
app.include_router(arohan.router, prefix=settings.API_V1_STR)
app.include_router(faculty.router, prefix=settings.API_V1_STR)
app.include_router(exam_controller.router, prefix=settings.API_V1_STR)
app.include_router(placement.router, prefix=settings.API_V1_STR)
app.include_router(security.router, prefix=settings.API_V1_STR)

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT,
        "server_time_utc": datetime.now(timezone.utc).isoformat()
    }

# Mount static frontend build if present (for unified production & desktop packaging)
import os
import sys
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

def get_frontend_dist():
    if hasattr(sys, "_MEIPASS"):
        bundle_dist = os.path.join(sys._MEIPASS, "frontend", "dist")
        if os.path.exists(bundle_dist):
            return bundle_dist
    local_dist = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist"))
    if os.path.exists(local_dist):
        return local_dist
    return None

dist_dir = get_frontend_dist()
if dist_dir:
    assets_dir = os.path.join(dist_dir, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/")
    async def serve_root():
        index_path = os.path.join(dist_dir, "index.html")
        if os.path.isfile(index_path):
            return FileResponse(index_path)
        return Response(content="Frontend build index.html not found", status_code=404)

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # Do not intercept API, health, or swagger docs
        if (
            full_path.startswith("api/") 
            or full_path == "api" 
            or full_path.startswith("docs") 
            or full_path.startswith("redoc")
            or full_path == "openapi.json"
        ):
            return Response(status_code=404)
        
        target_file = os.path.join(dist_dir, full_path)
        if os.path.isfile(target_file):
            return FileResponse(target_file)
        
        index_path = os.path.join(dist_dir, "index.html")
        if os.path.isfile(index_path):
            return FileResponse(index_path)
        return Response(status_code=404)


