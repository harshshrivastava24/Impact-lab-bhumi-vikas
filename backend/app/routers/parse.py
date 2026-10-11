"""Parse router: free-text → params and topics (FR-02, FR-03)."""
from __future__ import annotations

from fastapi import APIRouter, Request
from backend.app.models import ParseRequest, ParseResponse
from backend.app.services.parser import detect_language, parse_text_rule_based, parse_with_inference

router = APIRouter()


@router.post("/parse", response_model=ParseResponse, response_model_exclude_none=True)
async def parse_text(req: ParseRequest, request: Request) -> ParseResponse:
    settings = request.app.state.settings
    text = req.text.strip()
    language = detect_language(text, settings.devanagari_ratio_threshold)

    used_inference = False
    params = None
    topics = []

    # Try inference first if configured (Section 5.3)
    if settings.inference_configured:
        result = await parse_with_inference(text, settings)
        if result:
            params, topics, used_inference = result

    # Fall back to rule-based parser
    if params is None:
        params, topics = parse_text_rule_based(text)
        used_inference = False

    return ParseResponse(
        language=language,
        params=params,
        topics=topics,
        used_inference=used_inference,
    )
