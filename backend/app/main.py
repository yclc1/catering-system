"""FastAPI application entry point."""
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.api.router import api_router
from app.core.exceptions import NotFoundError, DuplicateError, BusinessError, MonthClosedError


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
)

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

# Static files for uploads
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")


@app.get("/health")
async def health_check():
    return {"status": "ok"}
