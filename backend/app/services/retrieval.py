"""
Retrieval service: topic-to-rule mapping, keyword fallback, fabrication guard.
Implements FR-07, FR-08, FR-12, FR-23 to FR-27.
"""
from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from backend.app.corpus import Corpus, RuleRecord, resolve_inserted_rule, INSERTED_RULE_PARENTS
from backend.app.models import Citation, Params, Topic

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent.parent.parent


def _load_topic_map() -> Dict:
    path = ROOT / "config" / "topic_map.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _load_amendments() -> List[Dict]:
    path = ROOT / "config" / "amendments.json"
    return json.loads(path.read_text(encoding="utf-8"))


TOPIC_MAP: Dict = {}
AMENDMENTS: List[Dict] = []


def get_topic_map() -> Dict:
    global TOPIC_MAP
    if not TOPIC_MAP:
        TOPIC_MAP = _load_topic_map()
    return TOPIC_MAP


def get_amendments() -> List[Dict]:
    global AMENDMENTS
    if not AMENDMENTS:
        AMENDMENTS = _load_amendments()
    return AMENDMENTS


# ---------------------------------------------------------------------------
# Valid rule set (FR-27 fabrication guard)
# ---------------------------------------------------------------------------

def build_valid_rules(corpus: Corpus) -> Set[str]:
    """Build the set of all valid rule references."""
    valid: Set[str] = set(corpus.by_rule.keys())
    # Add inserted rules
    for k in INSERTED_RULE_PARENTS.keys():
        valid.add(k)
    return valid


def guard_rule(rule_str: str, valid_rules: Set[str], request_id: str = "") -> Optional[str]:
    """
    FR-27: Validate a rule reference. Return None and log if invalid.
    """
    if rule_str in valid_rules:
        return rule_str
    # Try numeric normalisation
    stripped = rule_str.replace("Rule ", "").replace("rule ", "").strip()
    if stripped in valid_rules:
        return stripped
    logger.error(
        "Fabrication guard: rule '%s' not in corpus; suppressed. request_id=%s",
        rule_str, request_id,
    )
    return None


# ---------------------------------------------------------------------------
# Citation builder
# ---------------------------------------------------------------------------

def build_citation(
    rule: str,
    sub_rule: Optional[str],
    corpus: Corpus,
    settings,
    candidate: bool = False,
    excerpt: Optional[str] = None,
) -> Optional[Citation]:
    """Build a Citation object for a validated rule reference."""
    # Check inserted rules first
    inserted = resolve_inserted_rule(rule, corpus)
    if inserted:
        rec, sub_text = inserted
        text_en = sub_text or rec.text_stripped
        if isinstance(sub_text, str) and "no separate heading" in sub_text:
            # 26-A note case
            text_en = rec.text_stripped + "\n\n" + sub_text
    else:
        rec = corpus.by_rule.get(rule)
        if rec is None:
            return None
        if sub_rule:
            extracted = rec.sub_rule_text(sub_rule)
            text_en = extracted if extracted else rec.text_stripped
        else:
            text_en = rec.text_stripped

    pdf_en_url = f"/pdf/en#page={rec.page_start}"
    pdf_hi_url = f"/pdf/hi#page={rec.page_start}"

    return Citation(
        rule=rule,
        sub_rule=sub_rule,
        title=rec.title,
        part=rec.part,
        page_start=rec.page_start,
        page_end=rec.page_end,
        text_en=text_en,
        pdf_en_url=pdf_en_url,
        pdf_hi_url=pdf_hi_url,
        footnotes=rec.footnotes,
        candidate=candidate,
        excerpt=excerpt,
    )


# ---------------------------------------------------------------------------
# Topic retrieval
# ---------------------------------------------------------------------------

def get_rules_for_topics(
    topics: List[Topic],
    params: Params,
    corpus: Corpus,
    settings,
) -> List[Citation]:
    """
    FR-07/FR-08: Return citations for each topic based on the topic map.
    """
    topic_map = get_topic_map()
    valid_rules = build_valid_rules(corpus)
    citations: List[Citation] = []
    seen: Set[str] = set()

    for topic in topics:
        topic_data = topic_map.get(topic)
        if topic_data is None:
            continue

        mappings = topic_data.get("mappings", [])
        for mapping in mappings:
            rule = mapping.get("rule")
            sub_rule = mapping.get("sub_rule")

            if not rule:
                continue

            # Guard against fabricated rules
            safe_rule = guard_rule(rule, valid_rules)
            if not safe_rule:
                continue

            key = f"{safe_rule}{sub_rule or ''}"
            if key in seen:
                continue
            seen.add(key)

            citation = build_citation(safe_rule, sub_rule, corpus, settings)
            if citation:
                citations.append(citation)

    return citations


# ---------------------------------------------------------------------------
# Keyword fallback (FR-12)
# ---------------------------------------------------------------------------

_STOP_WORDS = {
    "what", "is", "the", "for", "a", "an", "in", "on", "of", "and", "or",
    "to", "how", "can", "i", "does", "these", "if", "with", "this", "that",
    "are", "be", "do", "by", "from", "at", "as", "into"
}

_CONCEPT_TRIGGERS = [
    (["without permission", "unauthorised", "unauthorized", "without sanction"], "28", None),
    (["development plan", "prevail", "override"], "103", None),
    (["garage", "side open space"], "56", "(4)"),
]


_UNPRESCRIBED_CONCEPTS = [
    "window size", "window", "bedroom", "fire escape", "national building code", "nbc"
]


def keyword_fallback(
    query_text: str,
    corpus: Corpus,
    settings,
    max_results: int = 5,
) -> List[Citation]:
    """
    FR-12: Rank records by term overlap with query over stripped text.
    Returns up to max_results candidates with excerpts.
    """
    cleaned = query_text.strip().lower()
    if not cleaned:
        return []

    # FR-26: Say "not found" honestly for topics not prescribed in these rules
    if any(un in cleaned for un in _UNPRESCRIBED_CONCEPTS):
        return []

    results: List[Citation] = []
    seen_rules = set()

    # Check concept triggers first for procedural / legal questions
    for triggers, rule_no, sub_rule in _CONCEPT_TRIGGERS:
        if any(tr in cleaned for tr in triggers):
            if rule_no not in seen_rules:
                cit = build_citation(rule_no, sub_rule, corpus, settings, candidate=True)
                if cit:
                    results.append(cit)
                    seen_rules.add(rule_no)

    if results:
        return results[:max_results]

    tokens = set(re.findall(r"\b\w+\b", cleaned)) - _STOP_WORDS
    if len(tokens) < 2:
        return []

    scored: List[Tuple[float, RuleRecord, str]] = []

    for rec in corpus.records:
        text = rec.text_stripped.lower()
        title = rec.title.lower()
        text_tokens = set(re.findall(r"\b\w+\b", text)) - _STOP_WORDS
        title_tokens = set(re.findall(r"\b\w+\b", title)) - _STOP_WORDS
        overlap = tokens & text_tokens
        title_overlap = tokens & title_tokens

        if not overlap and not title_overlap:
            continue

        score = (len(overlap) + len(title_overlap) * 2.0) / max(len(tokens), 1)

        first_term = next(iter(overlap or title_overlap))
        idx = text.find(first_term)
        if idx >= 0:
            start = max(0, idx - 50)
            end = min(len(text), idx + 100)
            excerpt = rec.text_stripped[start:end].strip()
        else:
            excerpt = rec.title

        scored.append((score, rec, excerpt))

    scored.sort(key=lambda x: x[0], reverse=True)
    threshold = max(settings.relevance_threshold, 0.4)
    for score, rec, excerpt in scored[:max_results]:
        if score < threshold:
            break
        if rec.rule not in seen_rules:
            citation = build_citation(rec.rule, None, corpus, settings, candidate=True, excerpt=excerpt)
            if citation:
                results.append(citation)
                seen_rules.add(rec.rule)

    return results


# ---------------------------------------------------------------------------
# Amendment flagging (FR-24, FR-25)
# ---------------------------------------------------------------------------

def check_amendments(params: Params) -> List[Dict]:
    """
    FR-25: Return amendments that are potentially relevant to the params.
    """
    amendments = get_amendments()
    flags = []
    for am in amendments:
        condition = am.get("condition", "")
        triggered = False

        # Evaluate condition against params
        if "plot_area <= 500" in condition:
            if params.plot_area is not None and params.plot_area <= 500:
                triggered = True

        if triggered:
            flags.append(am)

    return flags
