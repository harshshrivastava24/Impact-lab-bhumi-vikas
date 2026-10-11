"""
Bhumi Vikas Sahayak – Backend entry point.
Rule lookup and compliance decision-support tool.
NOT a chatbot, NOT an assistant.
"""
from __future__ import annotations

import json
import logging
import os
import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Ensure project root is on the path so relative imports work when running
# from the repository root:  uvicorn backend.app.main:app
ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.corpus import load_corpus          # noqa: E402
from backend.app.config import load_settings        # noqa: E402
from backend.app.routers import parse, lookup, rules_router, health, plan_check  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s – %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------

def create_app() -> FastAPI:
    settings = load_settings()

    # Fail fast if corpus missing or corrupt
    corpus = load_corpus(settings)

    app = FastAPI(
        title="Bhumi Vikas Sahayak",
        description=(
            "Rule lookup and compliance decision-support tool for the "
            "Bhopal Municipal Corporation building-permission counter."
        ),
        version="1.0.0",
        docs_url="/docs",
        redoc_url=None,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

    # Attach shared state
    app.state.corpus = corpus
    app.state.settings = settings

    # API routers
    app.include_router(health.router,        prefix="/api")
    app.include_router(parse.router,         prefix="/api")
    app.include_router(lookup.router,        prefix="/api")
    app.include_router(rules_router.router,  prefix="/api")
    app.include_router(plan_check.router,    prefix="/api")

    # Serve PDFs: /pdf/en and /pdf/hi per the API contract; the frontend opens /pdf/en#page=N
    @app.get("/pdf/{lang}", include_in_schema=False)
    async def pdf(lang: str):
        path = {"en": settings.pdf_en_path, "hi": settings.pdf_hi_path}.get(lang)
        if path is None or not path.exists():
            raise HTTPException(status_code=404, detail=f"PDF '{lang}' not found")
        return FileResponse(path, media_type="application/pdf")

    resources_dir = ROOT / "resources"
    if resources_dir.exists():
        app.mount("/pdf", StaticFiles(directory=str(resources_dir)), name="pdf")
    else:
        logger.warning("resources/ directory not found; /pdf routes will 404")

    # Serve Phase-1 frontend from frontend/dist at /
    frontend_dist = ROOT / "frontend" / "dist"
    if frontend_dist.exists():
        app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")
    else:
        logger.warning(
            "frontend/dist not found; run 'npm run build' in frontend/ to create it. "
            "API routes are still available."
        )

    return app


app = create_app()
