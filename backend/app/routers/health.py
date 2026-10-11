"""Health check router."""
from fastapi import APIRouter, Request
from backend.app.models import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health(request: Request) -> HealthResponse:
    corpus = request.app.state.corpus
    settings = request.app.state.settings
    return HealthResponse(
        ok=True,
        rules_loaded=len(corpus.records),
        version=settings.consolidated_to,
        inference_configured=settings.inference_configured,
    )
