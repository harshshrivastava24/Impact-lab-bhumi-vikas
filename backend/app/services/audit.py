"""Append-only audit log (FR-38, FR-49). Structured fields only; free text is never logged."""
import json
from datetime import datetime, timezone

from .. import config

PARAM_FIELDS = (
    "plot_area", "road_width", "use_type", "built_up_area", "height", "development_type",
    "frontage", "depth", "floor_to_floor", "existing_developed_area", "streets_abutting",
)


def log(entry: dict) -> None:
    p = config.log_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    entry = {"timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"), **entry}
    with open(p, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def clean_params(params: dict) -> dict:
    return {k: params[k] for k in PARAM_FIELDS if k in params}
