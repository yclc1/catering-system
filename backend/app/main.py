"""FastAPI application entry point."""
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.api.router import api_router
from app.core.exceptions import NotFoundError, DuplicateError, BusinessError, MonthClosedError

limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    from app.tasks.scheduler import start_scheduler, stop_scheduler
    start_scheduler()
    yield
    # Shutdown
    stop_scheduler()


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handlers
from fastapi.responses import JSONResponse
from fastapi import Request


@app.exception_handler(NotFoundError)
async def not_found_handler(request: Request, exc: NotFoundError):
    return JSONResponse(status_code=404, content={"detail": exc.detail})


@app.exception_handler(DuplicateError)
async def duplicate_handler(request: Request, exc: DuplicateError):
    return JSONResponse(status_code=409, content={"detail": exc.detail})


@app.exception_handler(BusinessError)
async def business_handler(request: Request, exc: BusinessError):
    return JSONResponse(status_code=400, content={"detail": exc.detail})


@app.exception_handler(MonthClosedError)
async def month_closed_handler(request: Request, exc: MonthClosedError):
    return JSONResponse(status_code=423, content={"detail": exc.detail})


# Routes
app.include_router(api_router)

# Protected static files for uploads
from app.dependencies import get_current_user
from app.models.user import User
from fastapi.responses import FileResponse
import pathlib

@app.get("/uploads/{file_path:path}")
async def serve_upload(file_path: str, current_user: User = Depends(get_current_user)):
    full_path = pathlib.Path(settings.UPLOAD_DIR) / file_path
    if not full_path.exists():
        raise NotFoundError("文件", file_path)
    return FileResponse(full_path)


@app.get("/health")
async def health_check():
    return {"status": "ok"}
