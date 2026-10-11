"""
Lookup router: POST /api/lookup
Main computation and retrieval endpoint.
Implements FR-14 to FR-27, FR-36, FR-38, FR-51.
Also implements POST /api/plan-check returning 501 until Phase 3.
"""
from __future__ import annotations

import logging
from typing import List, Optional

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from backend.app.models import (
    AmendmentFlag, Citation, Figure, LookupRequest, LookupResponse,
    Params, Topic, Version,
)
from backend.app.services import compute, retrieval, audit
from backend.app.services.retrieval import (
    build_valid_rules, check_amendments, get_rules_for_topics,
    guard_rule, keyword_fallback, build_citation,
)
from backend.app.services.compute import (
    compute_front_setback, compute_rear_setback, compute_side_setback,
    compute_height_limit, compute_storey_count, compute_far, compute_fees,
    compute_ground_coverage,
)

logger = logging.getLogger(__name__)
router = APIRouter()

NOT_FOUND_MSG = "Not found in MP Bhumi Vikas Rules 2012"


# ---------------------------------------------------------------------------
# /api/plan-check → 501 until Phase 3
# ---------------------------------------------------------------------------

@router.post("/plan-check")
async def plan_check_stub():
    return JSONResponse(
        status_code=501,
        content={
            "detail": (
                "Plan check (plot envelope drawing and setback verification) is not yet implemented. "
                "It will be available in Phase 3 of this tool."
            )
        },
    )


# ---------------------------------------------------------------------------
# /api/lookup
# ---------------------------------------------------------------------------

@router.post("/lookup", response_model=LookupResponse)
async def lookup(req: LookupRequest, request: Request) -> LookupResponse:
    corpus = request.app.state.corpus
    settings = request.app.state.settings
    valid_rules = build_valid_rules(corpus)

    params = req.params
    topics = req.topics
    language = req.language

    version = Version(
        consolidated_to=settings.consolidated_to,
        label=settings.version_label,
    )
    disclaimer = settings.disclaimer

    # Fabrication guard on any inline rule references
    # (params don't contain rule numbers; guard is applied below on citations)

    # Amendment flags (FR-24, FR-25)
    raw_flags = check_amendments(params)
    amendment_flags: List[AmendmentFlag] = [
        AmendmentFlag(
            date=f["date"],
            rule=f["rule"],
            concerns=f["concerns"],
            source_url=f["source_url"],
            source_kind=f["source_kind"],
            applied=f["applied"],
            note=f["note"],
        )
        for f in raw_flags
    ]

    # -----------------------------------------------------------------------
    # Compute figures for requested topics
    # -----------------------------------------------------------------------
    figures: List[Figure] = []
    citations: List[Citation] = []

    query_text = req.query or req.raw_query or " ".join(topics)

    if not topics:
        # No topics → keyword fallback
        candidates = keyword_fallback(query_text, corpus, settings)
        if candidates:
            return LookupResponse(
                status="answered",
                figures=[],
                citations=candidates,
                version=version,
                amendment_flags=amendment_flags,
                disclaimer=disclaimer,
                language=language,
            )
        return LookupResponse(
            status="not_found",
            message=NOT_FOUND_MSG,
            figures=[],
            citations=[],
            version=version,
            amendment_flags=amendment_flags,
            disclaimer=disclaimer,
            language=language,
        )

    # Compute figures per topic
    for topic in topics:
        if topic == "front_setback":
            fig = compute_front_setback(params)
            fig = _guard_figure(fig, valid_rules)
            figures.append(fig)

        elif topic == "rear_setback":
            fig = compute_rear_setback(params)
            fig = _guard_figure(fig, valid_rules)
            figures.append(fig)

        elif topic == "side_setback":
            fig = compute_side_setback(params)
            fig = _guard_figure(fig, valid_rules)
            figures.append(fig)

        elif topic == "height_limit":
            fig = compute_height_limit(params)
            fig = _guard_figure(fig, valid_rules)
            figures.append(fig)
            # Storey count (derived, FR-18)
            storey = compute_storey_count(params, fig)
            if storey:
                storey = _guard_figure(storey, valid_rules)
                figures.append(storey)

        elif topic == "far":
            far_fig, floor_fig = compute_far(params)
            if floor_fig:
                floor_fig = _guard_figure(floor_fig, valid_rules)
                figures.append(floor_fig)
            far_fig = _guard_figure(far_fig, valid_rules)
            figures.append(far_fig)

        elif topic in ("application_fee", "permission_fee"):
            fee_figs = compute_fees(params, settings)
            for ff in fee_figs:
                ff = _guard_figure(ff, valid_rules)
                figures.append(ff)

        elif topic == "ground_coverage":
            gc_fig = compute_ground_coverage(params, settings)
            gc_fig = _guard_figure(gc_fig, valid_rules)
            figures.append(gc_fig)

        elif topic == "permission_validity":
            # Return Rule 23 citation and note
            cit = build_citation("23", None, corpus, settings)
            if cit and cit not in citations:
                citations.append(cit)

        elif topic == "documents_required":
            for rule_no in ("14", "16"):
                cit = build_citation(rule_no, None, corpus, settings)
                if cit:
                    citations.append(cit)

    # Build citations from figures
    seen_keys = {f"{c.rule}{c.sub_rule or ''}" for c in citations}
    for topic in topics:
        topic_citations = get_rules_for_topics([topic], params, corpus, settings)  # type: ignore
        for cit in topic_citations:
            key = f"{cit.rule}{cit.sub_rule or ''}"
            if key not in seen_keys:
                seen_keys.add(key)
                citations.append(cit)

    # Guard all citations (FR-27)
    guarded_citations: List[Citation] = []
    for cit in citations:
        safe = guard_rule(cit.rule, valid_rules)
        if safe:
            guarded_citations.append(cit)
        else:
            logger.error("Fabrication guard stripped citation for rule '%s'", cit.rule)
    citations = guarded_citations

    # -----------------------------------------------------------------------
    # Not-found handling (FR-26)
    # -----------------------------------------------------------------------
    if not figures and not citations:
        # Keyword fallback
        candidates = keyword_fallback(
            " ".join(topics),
            corpus, settings,
        )
        if candidates:
            return LookupResponse(
                status="answered",
                figures=[],
                citations=candidates,
                version=version,
                amendment_flags=amendment_flags,
                disclaimer=disclaimer,
                language=language,
            )
        return LookupResponse(
            status="not_found",
            message=NOT_FOUND_MSG,
            figures=[],
            citations=[],
            version=version,
            amendment_flags=amendment_flags,
            disclaimer=disclaimer,
            language=language,
        )

    # -----------------------------------------------------------------------
    # Audit log (FR-38)
    # -----------------------------------------------------------------------
    try:
        audit.append_log_entry(
            log_path=settings.log_path,
            params=params.model_dump(exclude_none=True),
            topics=list(topics),
            rules_cited=[c.rule for c in citations],
            figures_returned=[f.topic for f in figures],
            version=settings.consolidated_to,
            amendment_flags=[f.rule for f in amendment_flags],
            used_inference=False,
        )
    except Exception as exc:
        logger.error("Audit log error: %s", exc)

    return LookupResponse(
        status="answered",
        figures=figures,
        citations=citations,
        version=version,
        amendment_flags=amendment_flags,
        disclaimer=disclaimer,
        language=language,
        used_inference=False,
    )


def _guard_figure(fig: Figure, valid_rules: set) -> Figure:
    """FR-27: Validate rule field of a figure."""
    safe = guard_rule(fig.rule, valid_rules)
    if not safe:
        logger.error("Fabrication guard stripped figure rule '%s'", fig.rule)
        # Replace with placeholder rather than crashing
        fig = fig.model_copy(update={"rule": "unknown", "trace": fig.trace + " [rule reference suppressed by fabrication guard]"})
    return fig
