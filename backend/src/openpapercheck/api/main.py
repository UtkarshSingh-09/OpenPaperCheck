"""
FastAPI Application Factory for OpenPaperCheck REST API.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from openpapercheck import __version__
from openpapercheck.api.errors import register_error_handlers
from openpapercheck.api.routers import check, health, sources


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="OpenPaperCheck API",
        description=(
            "Fast, honest scholarly retraction and reference integrity checker.\n\n"
            "Paste a paper's DOI to receive sourced facts about whether it has been retracted "
            "or leans on retracted work. Provides deterministic signals (S-001, S-002, S-003, S-010, S-040) "
            "with zero personal profiling and verifiable external authority links."
        ),
        version=__version__,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        contact={
            "name": "OpenPaperCheck Contributors",
            "url": "https://github.com/UtkarshSingh-09/OpenPaperCheck",
        },
        license_info={
            "name": "Apache-2.0",
            "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
        },
    )

    # 1. Register RFC 9457 problem+json error handlers
    register_error_handlers(app)

    # 2. Configure CORS middleware (allowing local frontend dev)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:8000",
            "http://127.0.0.1:8000",
        ],
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )

    # 3. Mount v1 routers
    app.include_router(health.router, prefix="/v1")
    app.include_router(sources.router, prefix="/v1")
    app.include_router(check.router, prefix="/v1")

    # Root redirect / status
    @app.get("/", include_in_schema=False)
    async def root():
        return {
            "name": "OpenPaperCheck API",
            "version": __version__,
            "docs": "/docs",
            "health": "/v1/health",
        }

    return app


app = create_app()
