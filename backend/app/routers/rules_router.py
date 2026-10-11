"""
Rules router: GET /api/rules/{rule}
Returns a Citation for the given rule number. 404 if not in corpus.
Implements FR-08, FR-10.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from backend.app.corpus import resolve_inserted_rule
from backend.app.models import Citation
from backend.app.services.retrieval import build_citation, build_valid_rules, guard_rule

router = APIRouter()


@router.get("/rules/{rule}", response_model=Citation)
async def get_rule(rule: str, request: Request) -> Citation:
    corpus = request.app.state.corpus
    settings = request.app.state.settings
    valid_rules = build_valid_rules(corpus)

    # Fabrication guard (FR-27)
    safe_rule = guard_rule(rule, valid_rules)
    if not safe_rule:
        raise HTTPException(status_code=404, detail=f"Rule '{rule}' not found in corpus.")

    # Try inserted rule first (FR-10)
    inserted = resolve_inserted_rule(safe_rule, corpus)
    if inserted:
        rec, sub_text = inserted
        text_en = sub_text if isinstance(sub_text, str) else rec.text_stripped
        return Citation(
            rule=safe_rule,
            sub_rule=None,
            title=rec.title,
            part=rec.part,
            page_start=rec.page_start,
            page_end=rec.page_end,
            text_en=text_en,
            pdf_en_url=f"/pdf/en#page={rec.page_start}",
            pdf_hi_url=f"/pdf/hi#page={rec.page_start}",
            footnotes=rec.footnotes,
        )

    # Direct lookup
    rec = corpus.by_rule.get(safe_rule)
    if rec is None:
        raise HTTPException(status_code=404, detail=f"Rule '{rule}' not found in corpus.")

    citation = build_citation(safe_rule, None, corpus, settings)
    if citation is None:
        raise HTTPException(status_code=404, detail=f"Rule '{rule}' not found in corpus.")

    return citation
