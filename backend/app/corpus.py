"""
Corpus loader for Bhumi Vikas Sahayak.
Loads data/bhumi_vikas_rules.jsonl at startup with integrity checking.
Implements FR-06, FR-09, FR-10, FR-11, FR-37.
"""
from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Running-header regex (FR-09)
# Matches lines like: "Rule 56   M.P. Bhumi Vikas Rules, 2012   78"
# and:  "Rule 29-31  M.P. Bhumi Vikas Rules, 2012   49"
# ---------------------------------------------------------------------------
_HEADER_RE = re.compile(
    r"^Rule\s+\d+[\w\-]*(?:\s*[-–]\s*\d+[\w\-]*)?\s+"
    r"M\.P\.\s+Bhumi\s+Vikas\s+Rules,\s+2012\s+\d+\s*$",
    re.IGNORECASE,
)

# Footnote block pattern (lines starting with lone digit + "Subs." / "Ins." / "Published")
_FOOTNOTE_RE = re.compile(r"^\d+\s*(Subs\.|Ins\.|Published)", re.IGNORECASE)


# ---------------------------------------------------------------------------
# Inserted-rule parent map (FR-10)
# ---------------------------------------------------------------------------
INSERTED_RULE_PARENTS: Dict[str, str] = {
    "12-A": "12",
    "12-a": "12",
    "17-a": "17",
    "17-A": "17",
    "25(A)": "25",
    "25(a)": "25",
    "26-A": "26",
    "26-a": "26",
    "42-A": "42",
    "42-a": "42",
    "93(a)": "93",
    "93(A)": "93",
}

# Rules known to contain sub-rule headings for inserted rules
INSERTED_RULE_HEADINGS: Dict[str, str] = {
    "12-A": "12-A",
    "17-a": "17-a",
    "25(A)": "25(A)",
    "26-A": None,   # 26-A has no heading in PDF; return parent with note
    "42-A": "42-A",
    "93(a)": "93(a)",
}


@dataclass
class RuleRecord:
    rule: str
    title: str
    part: str
    page_start: int
    page_end: int
    text: str
    text_stripped: str = field(default="", repr=False)
    footnotes: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.text_stripped:
            self.text_stripped = strip_headers(self.text)

    def sub_rule_text(self, sub_rule: str) -> Optional[str]:
        """Extract text of a sub-rule marker, e.g. '(1)(a)' from stripped text."""
        return extract_sub_rule(self.text_stripped, sub_rule)


def strip_headers(text: str) -> str:
    """Remove running-header lines from text (FR-09)."""
    lines = text.splitlines()
    cleaned = [line for line in lines if not _HEADER_RE.match(line.strip())]
    return "\n".join(cleaned)


def extract_footnotes(text: str) -> List[str]:
    """Extract footnote blocks (lines matching lone digit + Subs./Ins./Published)."""
    lines = text.splitlines()
    footnotes = []
    for line in lines:
        stripped = line.strip()
        if _FOOTNOTE_RE.match(stripped):
            footnotes.append(stripped)
    return footnotes


def extract_sub_rule(stripped_text: str, sub_rule: str) -> Optional[str]:
    """
    Given stripped text and a sub-rule marker like '(1)(a)' or '(1)', extract the
    text from that marker to the next sibling marker.
    """
    cleaned_marker = sub_rule.strip()

    # Direct regex match
    escaped = re.escape(cleaned_marker)
    pattern = re.compile(
        r"(?:^|\n)(" + escaped + r"[\.\s].+?)(?=\n\s*\(\d+\)|\n\s*\([a-z]\)|\Z)",
        re.DOTALL | re.IGNORECASE,
    )
    m = pattern.search(stripped_text)
    if m:
        return m.group(1).strip()

    # Compound sub-rule marker like '(1)(a)' where (1) and (a) are on separate lines
    compound_m = re.match(r"^\((\d+)\)\(([a-z]+)\)$", cleaned_marker, re.IGNORECASE)
    if compound_m:
        p_num, clause = compound_m.group(1), compound_m.group(2)
        # Find parent (1) block
        p_pattern = re.compile(rf"(?:^|\n)\s*\({p_num}\).*?(?=\n\s*\(\d+\)|\Z)", re.DOTALL)
        pm = p_pattern.search(stripped_text)
        if pm:
            sub_block = pm.group(0)
            c_pattern = re.compile(
                rf"(?:^|\n)\s*(\({clause}\)[\.\s].*?)(?=\n\s*\([a-z]\)|\n\s*\(\d+\)|\Z)",
                re.DOTALL | re.IGNORECASE,
            )
            cm = c_pattern.search(sub_block)
            if cm:
                return cm.group(1).strip()

    # Fallback: find the marker line and return lines until next marker
    lines = stripped_text.splitlines()
    start_idx = None
    marker = cleaned_marker
    for i, line in enumerate(lines):
        if line.strip().startswith(marker):
            start_idx = i
            break

    if start_idx is None:
        return None

    # Collect until next top-level marker
    result_lines = [lines[start_idx]]
    next_marker_re = re.compile(r"^\s*\(\d+\)|^\s*\([a-z]\)|^Table\s+\d+", re.IGNORECASE)
    for line in lines[start_idx + 1:]:
        if next_marker_re.match(line) and line.strip() != marker:
            break
        result_lines.append(line)

    return "\n".join(result_lines).strip() or None


@dataclass
class Corpus:
    records: List[RuleRecord]
    by_rule: Dict[str, RuleRecord]
    gaps: List[str]


def load_corpus(settings) -> Corpus:
    """
    Load JSONL corpus file.  Raises RuntimeError on missing file or bad line.
    Reports record count, rule numbers and gaps (FR-06, FR-37).
    """
    corpus_path: Path = settings.corpus_path
    if not corpus_path.exists():
        raise FileNotFoundError(
            f"Corpus file not found: {corpus_path}. "
            "Place data/bhumi_vikas_rules.jsonl in the repository root."
        )

    records: List[RuleRecord] = []
    by_rule: Dict[str, RuleRecord] = {}

    with corpus_path.open(encoding="utf-8") as fh:
        for line_no, raw_line in enumerate(fh, start=1):
            raw_line = raw_line.strip()
            if not raw_line:
                continue
            try:
                data = json.loads(raw_line)
            except json.JSONDecodeError as exc:
                raise RuntimeError(
                    f"Corpus parse error on line {line_no}: {exc}"
                ) from exc

            required = {"rule", "title", "part", "page_start", "page_end", "text"}
            missing = required - data.keys()
            if missing:
                raise RuntimeError(
                    f"Corpus line {line_no} missing fields: {missing}"
                )

            rec = RuleRecord(
                rule=str(data["rule"]),
                title=data["title"],
                part=data["part"],
                page_start=int(data["page_start"]),
                page_end=int(data["page_end"]),
                text=data["text"],
                footnotes=data.get("footnotes", []),
            )
            # Extract footnotes from text if not explicitly provided
            if not rec.footnotes:
                rec.footnotes = extract_footnotes(rec.text)

            records.append(rec)
            by_rule[rec.rule] = rec

    # Integrity check (FR-37)
    _check_integrity(records, by_rule, settings.expected_record_count)

    corpus = Corpus(records=records, by_rule=by_rule, gaps=[])
    corpus.gaps = _find_gaps(by_rule)

    logger.info(
        "Corpus loaded: %d records, rules: %s, gaps in 1-105: %s",
        len(records),
        sorted(by_rule.keys()),
        corpus.gaps if corpus.gaps else "none",
    )

    return corpus


def _check_integrity(records: List[RuleRecord], by_rule: Dict[str, RuleRecord], expected: int) -> None:
    """Report record count and gaps. Does not raise on gaps, only on parse errors."""
    count = len(records)
    logger.info("Corpus: %d records loaded (expected %d)", count, expected)
    if count != expected:
        logger.warning(
            "Expected %d corpus records, got %d. "
            "This may indicate a missing or duplicate record.",
            expected, count,
        )


def _find_gaps(by_rule: Dict[str, RuleRecord]) -> List[str]:
    """Return list of rule numbers 1-105 missing from corpus."""
    gaps = []
    for n in range(1, 106):
        if str(n) not in by_rule:
            gaps.append(str(n))
            logger.warning("Gap in corpus: Rule %d not found", n)
    return gaps


def resolve_inserted_rule(rule_str: str, corpus: Corpus) -> Optional[tuple[RuleRecord, Optional[str]]]:
    """
    Resolve an inserted rule (e.g. '42-A') to its parent record and sub-text.
    Returns (parent_record, sub_rule_text_or_None) or None if not an inserted rule.
    """
    normalised = rule_str.strip()
    # Check both the provided form and common alternates
    for variant in [normalised, normalised.upper(), normalised.lower()]:
        if variant in INSERTED_RULE_PARENTS:
            parent_rule = INSERTED_RULE_PARENTS[variant]
            parent_record = corpus.by_rule.get(parent_rule)
            if parent_record is None:
                return None

            heading = INSERTED_RULE_HEADINGS.get(variant)
            if heading is None:
                # 26-A: no heading in PDF, return parent with note
                note = f"Rule {normalised} is inserted within Rule {parent_rule}; no separate heading appears in the PDF."
                return parent_record, note

            # Find the sub-rule text by heading
            sub_text = None
            lines = parent_record.text_stripped.splitlines()
            found_start = None
            for i, line in enumerate(lines):
                if heading in line:
                    found_start = i
                    break

            if found_start is not None:
                # Collect until next rule-level heading
                chunk = []
                for line in lines[found_start:]:
                    chunk.append(line)
                sub_text = "\n".join(chunk).strip()

            return parent_record, sub_text

    return None
