"""Audit log service: append one JSON line per /api/lookup (FR-38, NFR-17)."""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


def append_log_entry(
    log_path: Path,
    params: Dict[str, Any],
    topics: List[str],
    rules_cited: List[str],
    figures_returned: List[str],
    version: str,
    amendment_flags: List[str],
    used_inference: bool,
) -> None:
    """
    FR-38: Append one log entry to logs/queries.jsonl.
    Never logs free text or personal data.
    """
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "params": params,
        "topics": topics,
        "rules_cited": rules_cited,
        "figures_returned": figures_returned,
        "version": version,
        "amendment_flags": amendment_flags,
        "used_inference": used_inference,
    }
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError as exc:
        logger.error("Failed to write audit log: %s", exc)


# ---------------------------------------------------------------------------
# Plan check entries (FR-38 extension, FR-49): geometry inputs and per-side results
# ---------------------------------------------------------------------------

PARAM_FIELDS = (
    "plot_area", "road_width", "use_type", "built_up_area", "height", "development_type",
    "frontage", "depth", "floor_to_floor", "existing_developed_area", "streets_abutting",
)


def clean_params(params: Dict[str, Any]) -> Dict[str, Any]:
    """Keep only the structured parameter fields; free text never reaches the log."""
    return {k: params[k] for k in PARAM_FIELDS if k in params}


def log_plan_check(entry: Dict[str, Any]) -> None:
    from backend.app.plan_config import log_path

    path = log_path()
    entry = {"timestamp": datetime.now(timezone.utc).isoformat(), **entry}
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError as exc:
        logger.error("Failed to write audit log: %s", exc)
