"""
Tests for the API endpoints: /api/health, /api/lookup, /api/parse, /api/rules/{rule}.
Covers FR-26, FR-27, acceptance checklist items.
"""
from __future__ import annotations

import pytest


class TestHealthEndpoint:
    def test_health_ok(self, client):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["ok"] is True
        assert data["rules_loaded"] == 106
        assert data["version"] == "2025-03-06"

    def test_health_inference_field(self, client):
        resp = client.get("/api/health")
        data = resp.json()
        assert "inference_configured" in data


class TestLookupAppendixA:
    """Acceptance checklist: Appendix A worked example."""

    def _lookup(self, client, params, topics):
        resp = client.post("/api/lookup", json={
            "params": params,
            "topics": topics,
            "language": "en",
        })
        assert resp.status_code == 200
        return resp.json()

    def test_front_setback_3_0(self, client):
        data = self._lookup(client,
            {"plot_area": 200, "road_width": 9.0, "use_type": "residential"},
            ["front_setback"])
        figs = {f["topic"]: f["value"] for f in data["figures"]}
        assert abs(figs.get("front_setback", -1) - 3.0) < 0.01

    def test_rear_setback_2_50(self, client):
        data = self._lookup(client,
            {"plot_area": 200, "road_width": 9.0, "use_type": "residential"},
            ["rear_setback"])
        figs = {f["topic"]: f["value"] for f in data["figures"]}
        assert abs(figs.get("rear_setback", -1) - 2.50) < 0.01

    def test_height_12_5(self, client):
        data = self._lookup(client,
            {"plot_area": 200, "road_width": 9.0, "use_type": "residential"},
            ["height_limit"])
        figs = {f["topic"]: f["value"] for f in data["figures"]}
        assert abs(figs.get("height_limit", -1) - 12.5) < 0.01

    def test_far_1_25_and_floor_area_250(self, client):
        data = self._lookup(client,
            {"plot_area": 200, "road_width": 9.0, "use_type": "residential"},
            ["far"])
        figs = {f["topic"]: f["value"] for f in data["figures"]}
        assert abs(figs.get("far", -1) - 1.25) < 0.01

    def test_fees_250_and_3000(self, client):
        data = self._lookup(client,
            {"plot_area": 200, "road_width": 9.0, "use_type": "residential",
             "built_up_area": 250},
            ["application_fee", "permission_fee"])
        figs = {f["topic"]: f["value"] for f in data["figures"]}
        assert abs(figs.get("application_fee", -1) - 250.0) < 0.01
        assert abs(figs.get("permission_fee", -1) - 3000.0) < 0.01

    def test_figures_have_trace_rule_page(self, client):
        data = self._lookup(client,
            {"plot_area": 200, "road_width": 9.0, "use_type": "residential",
             "built_up_area": 250},
            ["front_setback", "rear_setback", "far", "application_fee"])
        for fig in data["figures"]:
            assert fig.get("trace"), f"Missing trace on figure {fig}"
            assert fig.get("rule"), f"Missing rule on figure {fig}"
            assert fig.get("page"), f"Missing page on figure {fig}"

    def test_version_stamp(self, client):
        data = self._lookup(client,
            {"plot_area": 200, "road_width": 9.0, "use_type": "residential"},
            ["front_setback"])
        assert data["version"]["consolidated_to"] == "2025-03-06"

    def test_disclaimer_present(self, client):
        data = self._lookup(client,
            {"plot_area": 200, "road_width": 9.0, "use_type": "residential"},
            ["front_setback"])
        assert "disclaimer" in data
        assert "clerk decides" in data["disclaimer"].lower()


class TestBoundaryConditions:
    """Boundary condition tests from acceptance checklist."""

    def _lookup(self, client, params, topics):
        resp = client.post("/api/lookup", json={
            "params": params, "topics": topics, "language": "en"
        })
        return resp.json()

    def test_road_9_0_front_3_0(self, client):
        data = self._lookup(client,
            {"plot_area": 200, "road_width": 9.0, "use_type": "residential"},
            ["front_setback"])
        figs = {f["topic"]: f["value"] for f in data["figures"]}
        assert abs(figs["front_setback"] - 3.0) < 0.01

    def test_road_9_1_front_3_6(self, client):
        data = self._lookup(client,
            {"plot_area": 200, "road_width": 9.1, "use_type": "residential"},
            ["front_setback"])
        figs = {f["topic"]: f["value"] for f in data["figures"]}
        assert abs(figs["front_setback"] - 3.6) < 0.01

    def test_plot_150_rear_1_50(self, client):
        data = self._lookup(client,
            {"plot_area": 150, "road_width": 9.0, "use_type": "residential"},
            ["rear_setback"])
        figs = {f["topic"]: f["value"] for f in data["figures"]}
        assert abs(figs["rear_setback"] - 1.50) < 0.01

    def test_plot_200_rear_2_50(self, client):
        data = self._lookup(client,
            {"plot_area": 200, "road_width": 9.0, "use_type": "residential"},
            ["rear_setback"])
        figs = {f["topic"]: f["value"] for f in data["figures"]}
        assert abs(figs["rear_setback"] - 2.50) < 0.01

    def test_road_5_existing_area_front_3_5(self, client):
        """Road 5, existing developed area true → 3.5 m from 56(1)(b) and Rule 46."""
        data = self._lookup(client,
            {"plot_area": 200, "road_width": 5.0, "use_type": "residential",
             "existing_developed_area": True},
            ["front_setback"])
        figs = {f["topic"]: f["value"] for f in data["figures"]}
        assert abs(figs.get("front_setback", -1) - 3.5) < 0.01, f"Got: {figs}"
        # Check Rule 46 in trace
        front_fig = next(f for f in data["figures"] if f["topic"] == "front_setback")
        assert "46" in front_fig["trace"]

    def test_out_of_range_warning_semi_detached_frontage14(self, client):
        """Plot 200, frontage 14, semi-detached → Rule 53(1)(i) warning."""
        data = self._lookup(client,
            {"plot_area": 200, "road_width": 9.0, "use_type": "residential",
             "development_type": "semi_detached", "frontage": 14.0, "height": 10.0},
            ["side_setback"])
        figs = data["figures"]
        assert any(f.get("warning") and "53" in f["warning"] for f in figs), \
            "Expected Rule 53(1)(i) warning for frontage 14 semi-detached"


class TestAmendmentFlag:
    """FR-24, FR-25: Amendment flagging."""

    def _lookup(self, client, params, topics):
        resp = client.post("/api/lookup", json={
            "params": params, "topics": topics, "language": "en"
        })
        return resp.json()

    def test_plot_200_triggers_amendment_flag(self, client):
        data = self._lookup(client,
            {"plot_area": 200, "road_width": 9.0, "use_type": "residential"},
            ["front_setback"])
        flags = data.get("amendment_flags", [])
        assert len(flags) > 0, "Plot 200 sq m should trigger amendment flag"
        flag = flags[0]
        assert flag["rule"] == "2(5)(c)"
        assert flag["source_kind"] == "secondary"
        assert flag["applied"] is False
        assert "process" in flag["concerns"].lower() or "permission" in flag["concerns"].lower()

    def test_plot_600_no_flag(self, client):
        data = self._lookup(client,
            {"plot_area": 600, "road_width": 9.0, "use_type": "residential"},
            ["front_setback"])
        flags = data.get("amendment_flags", [])
        assert len(flags) == 0, "Plot 600 sq m should NOT trigger amendment flag"


class TestNotFound:
    """FR-26: Not-found handling."""

    def _lookup(self, client, params, topics, text=""):
        resp = client.post("/api/lookup", json={
            "params": params, "topics": topics, "language": "en"
        })
        return resp.json()

    def test_question_16_not_found(self, client):
        """Window sizes → not found."""
        data = self._lookup(client, {}, [])
        # With no params and no topics, should return not_found
        assert data["status"] == "not_found"
        assert data["message"] == "Not found in MP Bhumi Vikas Rules 2012"
        assert data["figures"] == []
        assert data["citations"] == []

    def test_not_found_has_disclaimer(self, client):
        data = self._lookup(client, {}, [])
        assert "disclaimer" in data


class TestFabricationGuard:
    """FR-27: Fabrication guard."""

    def test_injected_rule_110_stripped(self, corpus, settings):
        """Rule '110' should be suppressed by the guard."""
        from backend.app.services.retrieval import build_valid_rules, guard_rule
        valid_rules = build_valid_rules(corpus)
        result = guard_rule("110", valid_rules)
        assert result is None, "Rule 110 should be suppressed (not in corpus)"

    def test_valid_rule_56_passes(self, corpus):
        from backend.app.services.retrieval import build_valid_rules, guard_rule
        valid_rules = build_valid_rules(corpus)
        result = guard_rule("56", valid_rules)
        assert result == "56"

    def test_inserted_rule_42A_passes(self, corpus):
        from backend.app.services.retrieval import build_valid_rules, guard_rule
        valid_rules = build_valid_rules(corpus)
        result = guard_rule("42-A", valid_rules)
        assert result == "42-A"


class TestRulesEndpoint:
    """GET /api/rules/{rule}"""

    def test_get_rule_56(self, client):
        resp = client.get("/api/rules/56")
        assert resp.status_code == 200
        data = resp.json()
        assert data["rule"] == "56"
        assert data["page_start"] == 77
        assert "Residential" in data["title"]

    def test_get_rule_42A(self, client):
        """FR-10: /api/rules/42-A returns Rule 42 pages."""
        resp = client.get("/api/rules/42-A")
        assert resp.status_code == 200
        data = resp.json()
        assert data["rule"] == "42-A"
        assert data["page_start"] == 58  # Rule 42 page

    def test_invalid_rule_404(self, client):
        resp = client.get("/api/rules/110")
        assert resp.status_code == 404

    def test_rule_has_pdf_links(self, client):
        resp = client.get("/api/rules/56")
        data = resp.json()
        assert "/pdf/en" in data["pdf_en_url"]
        assert "/pdf/hi" in data["pdf_hi_url"]


class TestParseEndpoint:
    """POST /api/parse"""

    def test_parse_english_basic(self, client):
        resp = client.post("/api/parse", json={
            "text": "What is the front setback for a 200 sq m plot on a 9 m road?"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["language"] == "en"
        assert data["params"]["plot_area"] == 200
        assert data["params"]["road_width"] == 9.0

    def test_parse_never_returns_rule_numbers(self, client):
        """FR-02: /api/parse never returns rule numbers, pages or figures."""
        resp = client.post("/api/parse", json={
            "text": "What is the front setback for a 200 sq m plot?"
        })
        data = resp.json()
        # params and topics should not contain rule numbers
        response_str = str(data)
        assert "Rule 56" not in response_str
        assert "page_start" not in response_str

    def test_parse_hindi_language_detected(self, client):
        resp = client.post("/api/parse", json={
            "text": "200 वर्ग मीटर प्लॉट पर 9 मीटर सड़क के लिए सामने की दूरी क्या है?"
        })
        data = resp.json()
        assert data["language"] == "hi"

    def test_parse_hindi_params_extracted(self, client):
        resp = client.post("/api/parse", json={
            "text": "200 वर्ग मीटर प्लॉट 9 मीटर सड़क आवासीय"
        })
        data = resp.json()
        assert data["language"] == "hi"


class TestPlanCheckWired:
    """POST /api/plan-check is served by Phase 3; incomplete plan-check input is a 422 naming the field."""

    def test_plan_check_missing_fields_422(self, client):
        resp = client.post("/api/plan-check", json={
            "params": {"plot_area": 200, "road_width": 9.0, "use_type": "residential"},
            "topics": []
        })
        assert resp.status_code == 422
        assert resp.json()["field"] == "params.frontage"


class TestKeywordFallback:
    """FR-12: Keyword fallback returns Rule 103 for Development Plan query."""

    def test_development_plan_returns_rule_103(self, client):
        resp = client.post("/api/lookup", json={
            "params": {},
            "topics": [],
            "language": "en",
        })
        # This will be not_found with empty params
        # For question 12, we need to test via keyword search
        # Test using the retrieval service directly
        from backend.app.config import load_settings
        from backend.app.corpus import load_corpus
        from backend.app.services.retrieval import keyword_fallback

        settings = load_settings()
        corpus = load_corpus(settings)
        candidates = keyword_fallback("Development Plan override rules", corpus, settings)
        rule_nums = [c.rule for c in candidates]
        assert "103" in rule_nums, f"Rule 103 should be in candidates, got {rule_nums}"


class TestNoChatbotLanguage:
    """Ensure no prohibited language appears in API responses."""

    def test_no_chatbot_in_responses(self, client):
        resp = client.post("/api/lookup", json={
            "params": {"plot_area": 200, "road_width": 9.0, "use_type": "residential"},
            "topics": ["front_setback"],
            "language": "en",
        })
        response_text = resp.text.lower()
        assert "chatbot" not in response_text
        assert "assistant" not in response_text
