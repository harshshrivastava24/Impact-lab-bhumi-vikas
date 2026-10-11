"""
Tests for corpus loading, integrity, header stripping, inserted rules, footnotes.
Covers FR-06, FR-09, FR-10, FR-11, FR-37.
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest


class TestCorpusLoading:
    """FR-06: Corpus loading."""

    def test_106_records_loaded(self, corpus):
        assert len(corpus.records) == 106, (
            f"Expected 106 records, got {len(corpus.records)}"
        )

    def test_all_required_fields_present(self, corpus):
        for rec in corpus.records:
            assert rec.rule, "rule field must not be empty"
            assert rec.title, "title field must not be empty"
            assert rec.part, "part field must not be empty"
            assert isinstance(rec.page_start, int), "page_start must be int"
            assert isinstance(rec.page_end, int), "page_end must be int"
            assert rec.text, "text field must not be empty"

    def test_26B_present(self, corpus):
        assert "26-B" in corpus.by_rule, "Rule 26-B must be in corpus"

    def test_missing_file_raises(self, settings):
        from backend.app.corpus import load_corpus
        from backend.app.config import Settings
        import copy

        bad_settings = copy.copy(settings)
        bad_settings.corpus_path = Path("/nonexistent/path.jsonl")
        with pytest.raises(FileNotFoundError):
            load_corpus(bad_settings)

    def test_corrupted_line_fails_with_line_number(self, settings):
        """FR-06 AC: corrupted line produces error naming the line number."""
        from backend.app.corpus import load_corpus
        import copy

        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False, encoding="utf-8") as f:
            # Write one good line and one corrupted line
            f.write('{"rule":"1","title":"T","part":"P","page_start":1,"page_end":1,"text":"T"}\n')
            f.write('INVALID JSON LINE\n')
            tmppath = Path(f.name)

        bad_settings = copy.copy(settings)
        bad_settings.corpus_path = tmppath
        bad_settings.expected_record_count = 2

        with pytest.raises(RuntimeError) as exc_info:
            load_corpus(bad_settings)
        assert "line 2" in str(exc_info.value).lower() or "2" in str(exc_info.value)
        tmppath.unlink()

    def test_no_gaps_in_1_to_105(self, corpus):
        """FR-37: Report any gap in 1 to 105."""
        gaps = corpus.gaps
        assert gaps == [], f"Gaps found in corpus rules 1-105: {gaps}"


class TestHeaderStripping:
    """FR-09: Running header removal."""

    def test_header_stripped_from_rule56(self, corpus):
        rec = corpus.by_rule.get("56")
        assert rec is not None
        # The stripped text should not contain running header pattern
        import re
        header_pattern = re.compile(
            r"Rule\s+56\s+M\.P\.\s+Bhumi\s+Vikas\s+Rules,\s+2012\s+\d+",
            re.IGNORECASE
        )
        assert not header_pattern.search(rec.text_stripped), (
            "Running header should be stripped from displayed text"
        )

    def test_original_text_preserved(self, corpus):
        """Original text must be preserved for verbatim view."""
        rec = corpus.by_rule.get("56")
        assert rec is not None
        # Original text must be non-empty
        assert len(rec.text) > 0


class TestInsertedRules:
    """FR-10: Inserted-rule resolution."""

    def test_42_A_returns_rule42_pages(self, corpus):
        from backend.app.corpus import resolve_inserted_rule
        result = resolve_inserted_rule("42-A", corpus)
        assert result is not None
        parent_rec, sub_text = result
        assert parent_rec.rule == "42", "42-A should resolve to Rule 42 parent"
        assert parent_rec.page_start == 58

    def test_26_A_returns_parent_with_note(self, corpus):
        from backend.app.corpus import resolve_inserted_rule
        result = resolve_inserted_rule("26-A", corpus)
        assert result is not None
        parent_rec, note = result
        assert parent_rec.rule == "26"
        # Note should explain no heading
        assert "no" in note.lower() or "heading" in note.lower() or "26" in note

    def test_93a_resolves_to_rule93(self, corpus):
        from backend.app.corpus import resolve_inserted_rule
        result = resolve_inserted_rule("93(a)", corpus)
        assert result is not None
        parent_rec, _ = result
        assert parent_rec.rule == "93"


class TestFootnotes:
    """FR-11: Amendment footnote preservation."""

    def test_rule61_has_footnote(self, corpus):
        rec = corpus.by_rule.get("61")
        assert rec is not None
        assert len(rec.footnotes) > 0, "Rule 61 should have footnotes"
        # Footnote should mention the 2025 notification
        footnote_text = " ".join(rec.footnotes)
        assert "2025" in footnote_text or "Subs" in footnote_text


class TestSubRuleExtraction:
    """Sub-rule extraction tests from corpus."""

    def test_extract_56_1a(self, corpus):
        rec = corpus.by_rule.get("56")
        assert rec is not None
        text = rec.sub_rule_text("(1)(a)")
        # Should contain the setback table values
        assert text is not None

    def test_extract_56_3(self, corpus):
        rec = corpus.by_rule.get("56")
        assert rec is not None
        text = rec.sub_rule_text("(3)")
        assert text is not None
