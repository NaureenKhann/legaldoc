"""
FastAPI application factory with all middleware, routes, and CORS.
"""
from __future__ import annotations

import time
import uuid

import structlog
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from structlog.contextvars import bind_contextvars, clear_contextvars

from app.core.config import get_settings
from app.core.logging import configure_logging

settings = get_settings()
configure_logging(settings.LOG_LEVEL)
from contextlib import asynccontextmanager
from app.db.session import init_db

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await init_db()
        logger.info("database_initialized")
    except Exception as e:
        logger.error("database_init_failed", error=str(e))
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=(
            "A traceable document-processing and evaluation pipeline for generating "
            "and validating Affidavits in Reply. "
            "AI interprets and drafts. Python validates and controls structure."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # ── CORS ──────────────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["Content-Disposition"],
    )

    # ── Request ID Middleware ─────────────────────────────────────────────────
    @app.middleware("http")
    async def request_id_middleware(request: Request, call_next):
        clear_contextvars()
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        bind_contextvars(request_id=request_id)

        start = time.perf_counter()
        response: Response = await call_next(request)
        duration = time.perf_counter() - start

        response.headers["X-Request-ID"] = request_id
        logger.info(
            "http_request",
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            duration_ms=round(duration * 1000, 2),
        )
        return response

    # ── Exception Handlers ────────────────────────────────────────────────────
    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        logger.error("unhandled_exception", error=str(exc), path=request.url.path)
        return JSONResponse(
            status_code=500,
            content={
                "error_code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred",
                "details": {},
            },
        )

    # ── Routes ────────────────────────────────────────────────────────────────
    from app.api.routes import (
        health,
        matters,
        documents,
        extraction,
        generation,
        validation,
        evaluation,
        synopsis,
        limitation,
    )

    prefix = settings.API_V1_PREFIX
    app.include_router(health.router, prefix=prefix, tags=["Health"])
    app.include_router(matters.router, prefix=prefix, tags=["Matters"])
    app.include_router(documents.router, prefix=prefix, tags=["Documents"])
    app.include_router(extraction.router, prefix=prefix, tags=["Extraction"])
    app.include_router(generation.router, prefix=prefix, tags=["Generation"])
    app.include_router(validation.router, prefix=prefix, tags=["Validation"])
    app.include_router(evaluation.router, prefix=prefix, tags=["Evaluation"])
    app.include_router(synopsis.router, prefix=prefix, tags=["Synopsis"])
    app.include_router(limitation.router, prefix=prefix, tags=["Limitation"])

    logger.info(
        "app_started",
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
        demo_mode=settings.DEMO_MODE,
        llm_provider=settings.LLM_PROVIDER,
    )

    return app


app = create_app()
