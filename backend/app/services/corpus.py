"""Read-only access to data/bhumi_vikas_rules.jsonl for citations. Full loading and integrity checks
(FR-06, FR-37) belong to Phase 2; until the corpus file is present, citations are omitted."""
import json
from functools import lru_cache

from .. import config


@lru_cache
def records() -> dict:
    p = config.path("corpus")
    if not p.exists():
        return {}
    out = {}
    with open(p, encoding="utf-8") as f:
        for n, line in enumerate(f, start=1):
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError as e:
                raise RuntimeError(f"{p}: line {n} is not valid JSON: {e}") from e
            out[str(rec["rule"])] = rec
    return out


def citation(rule: str, sub_rule: str = "") -> dict | None:
    rec = records().get(rule)
    if rec is None:
        return None
    page = rec["page_start"]
    return {
        "rule": rule,
        "sub_rule": sub_rule or None,
        "title": rec.get("title", ""),
        "part": rec.get("part", ""),
        "page_start": rec["page_start"],
        "page_end": rec["page_end"],
        "text_en": rec["text"],
        "pdf_en_url": f"/pdf/en#page={page}",
        "pdf_hi_url": f"/pdf/hi#page={page}",
        "footnotes": rec.get("footnotes", []),
    }
