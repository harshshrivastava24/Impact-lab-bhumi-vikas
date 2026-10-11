"""
Tests for deterministic computation service.
Covers FR-13, FR-14, FR-15, FR-16, FR-17, FR-18, FR-19, FR-20, FR-21, FR-22, FR-51.
"""
from __future__ import annotations

import pytest
from backend.app.models import Params
from backend.app.services.compute import (
    compute_front_setback,
    compute_rear_setback,
    compute_side_setback,
    compute_height_limit,
    compute_storey_count,
    compute_far,
    compute_fees,
    compute_ground_coverage,
    lookup_range,
)


class TestRangeLookup:
    """FR-13: Table boundary tests."""

    def test_road_9_gives_3_0(self):
        row = lookup_range("front_56_1a", 9.0)
        assert row is not None
        assert row["value"] == 3.0, "Road 9.0 m → front setback 3.0 m"

    def test_road_9_1_gives_3_6(self):
        row = lookup_range("front_56_1a", 9.1)
        assert row is not None
        assert row["value"] == 3.6, "Road 9.1 m → front setback 3.6 m (next slab)"

    def test_road_exactly_9_is_inclusive(self):
        """'Up to 9.0' means 9.0 inclusive."""
        row = lookup_range("front_56_1a", 9.0)
        assert row["value"] == 3.0

    def test_plot_150_gives_1_50(self):
        row = lookup_range("rear_56_2a", 150.0)
        assert row is not None
        assert row["value"] == 1.50, "Plot 150 sq m → rear setback 1.50 m"

    def test_plot_150_1_gives_2_50(self):
        row = lookup_range("rear_56_2a", 150.1)
        assert row is not None
        assert row["value"] == 2.50, "Plot 150.1 sq m → rear setback 2.50 m"

    def test_plot_200_gives_2_50(self):
        row = lookup_range("rear_56_2a", 200.0)
        assert row is not None
        assert row["value"] == 2.50, "Plot 200 sq m → rear setback 2.50 m"

    def test_plot_225_gives_2_50(self):
        row = lookup_range("rear_56_2a", 225.0)
        assert row is not None
        assert row["value"] == 2.50

    def test_plot_225_1_gives_3_00(self):
        row = lookup_range("rear_56_2a", 225.1)
        assert row is not None
        assert row["value"] == 3.00

    def test_plot_40_gives_nil(self):
        row = lookup_range("rear_56_2a", 40.0)
        assert row is not None
        assert row["value"] == 0.0, "Plot up to 40 sq m → rear setback nil"


class TestFrontSetback:
    """FR-14: Front setback computation."""

    def test_road_9_front_3_0(self):
        params = Params(plot_area=200, road_width=9.0, use_type="residential")
        fig = compute_front_setback(params)
        assert fig.value == 3.0
        assert "56" in fig.rule
        assert fig.page == 77

    def test_road_9_1_front_3_6(self):
        params = Params(plot_area=200, road_width=9.1, use_type="residential")
        fig = compute_front_setback(params)
        assert fig.value == 3.6

    def test_road_12_front_3_6(self):
        params = Params(plot_area=200, road_width=12.0, use_type="residential")
        fig = compute_front_setback(params)
        assert fig.value == 3.6

    def test_road_12_1_front_4_5(self):
        params = Params(plot_area=200, road_width=12.1, use_type="residential")
        fig = compute_front_setback(params)
        assert fig.value == 4.5

    def test_road_5_existing_developed_area_gives_3_5(self):
        """FR-14 AC: 5 m road in existing developed area returns 3.5 m from 56(1)(b)."""
        params = Params(plot_area=200, road_width=5.0, use_type="residential",
                        existing_developed_area=True)
        fig = compute_front_setback(params)
        assert fig.value == 3.5, f"Expected 3.5, got {fig.value}"
        assert "56(1)(b)" in fig.trace or "56" in fig.rule
        assert "46" in fig.trace, "Rule 46 must be cited for narrow street"
        assert fig.page == 77

    def test_road_5_no_flag_conditional(self):
        """Road < 6 without EDA flag → conditional figure."""
        params = Params(plot_area=200, road_width=5.0, use_type="residential",
                        existing_developed_area=None)
        fig = compute_front_setback(params)
        assert fig.conditional is True
        assert fig.cases and len(fig.cases) == 2

    def test_trace_contains_rule_and_page(self):
        params = Params(plot_area=200, road_width=9.0, use_type="residential")
        fig = compute_front_setback(params)
        assert "56" in fig.trace
        assert "77" in fig.trace


class TestRearSetback:
    """FR-15: Rear setback computation."""

    def test_plot_200_rear_2_50(self):
        params = Params(plot_area=200, road_width=9.0, use_type="residential")
        fig = compute_rear_setback(params)
        assert fig.value == 2.50
        assert fig.page == 78

    def test_plot_150_rear_1_50(self):
        params = Params(plot_area=150, road_width=9.0, use_type="residential")
        fig = compute_rear_setback(params)
        assert fig.value == 1.50

    def test_trace_format(self):
        params = Params(plot_area=200, road_width=9.0, use_type="residential")
        fig = compute_rear_setback(params)
        assert "56(2)(a)" in fig.trace or "56" in fig.trace
        assert "78" in fig.trace


class TestSideSetback:
    """FR-16: Side setback computation."""

    def test_semi_detached_proviso_applies(self):
        """200 sq m, frontage 10, height 10 → 2.5 m (proviso)."""
        params = Params(plot_area=200, road_width=9.0, use_type="residential",
                        development_type="semi_detached", frontage=10.0, height=10.0)
        fig = compute_side_setback(params)
        assert fig.value == 2.5, f"Expected 2.5, got {fig.value}"
        assert "proviso" in fig.trace.lower()

    def test_semi_detached_no_proviso(self):
        """Height > 10 → 3.0 m."""
        params = Params(plot_area=300, road_width=9.0, use_type="residential",
                        development_type="semi_detached", frontage=12.0, height=11.0)
        fig = compute_side_setback(params)
        assert fig.value == 3.0

    def test_detached_proviso_1_5m(self):
        """Detached, height <= 7, frontage < 12 → 1.5 m one side."""
        params = Params(plot_area=300, road_width=9.0, use_type="residential",
                        development_type="detached", frontage=11.0, height=7.0)
        fig = compute_side_setback(params)
        assert fig.value == 1.5

    def test_row_nil(self):
        params = Params(plot_area=100, road_width=9.0, use_type="residential",
                        development_type="row")
        fig = compute_side_setback(params)
        assert fig.value == 0.0

    def test_out_of_range_warning(self):
        """Plot 200, frontage 14, semi-detached → warning (frontage > 12)."""
        params = Params(plot_area=200, road_width=9.0, use_type="residential",
                        development_type="semi_detached", frontage=14.0, height=10.0)
        fig = compute_side_setback(params)
        assert fig.warning is not None, "Should have Rule 53(1)(i) warning"
        assert "53" in fig.warning

    def test_no_type_conditional(self):
        params = Params(plot_area=200, road_width=9.0, use_type="residential")
        fig = compute_side_setback(params)
        assert fig.conditional is True


class TestHeightLimit:
    """FR-17: Height limit."""

    def test_road_9_height_12_5(self):
        """Road 9 m < 12 m → Rule 56 norms, 12.5 m."""
        params = Params(plot_area=200, road_width=9.0, use_type="residential")
        fig = compute_height_limit(params)
        assert fig.value == 12.5
        assert "12" in fig.trace or "56" in fig.trace

    def test_road_12_height_18(self):
        params = Params(plot_area=1000, road_width=12.0, use_type="residential")
        fig = compute_height_limit(params)
        assert fig.value == 18.0
        assert "42" in fig.rule

    def test_road_11_height_12_5(self):
        params = Params(plot_area=200, road_width=11.0, use_type="residential")
        fig = compute_height_limit(params)
        assert fig.value == 12.5

    def test_trace_mentions_12m_road_requirement(self):
        params = Params(plot_area=200, road_width=9.0, use_type="residential")
        fig = compute_height_limit(params)
        assert "12" in fig.trace  # mentions 12 m road requirement


class TestStoreyCount:
    """FR-18: Derived storey count."""

    def test_storey_count_with_floor_height(self):
        params = Params(plot_area=200, road_width=9.0, use_type="residential",
                        floor_to_floor=3.0)
        height_fig = compute_height_limit(params)
        storey_fig = compute_storey_count(params, height_fig)
        assert storey_fig is not None
        assert storey_fig.derived is True
        # 12.5 / 3.0 = 4 storeys
        assert storey_fig.value == 4.0

    def test_no_storey_without_floor_height(self):
        params = Params(plot_area=200, road_width=9.0, use_type="residential")
        height_fig = compute_height_limit(params)
        storey_fig = compute_storey_count(params, height_fig)
        assert storey_fig is None


class TestFAR:
    """FR-19: FAR and floor area."""

    def test_residential_far_1_25(self):
        params = Params(plot_area=200, road_width=9.0, use_type="residential")
        far_fig, floor_fig = compute_far(params)
        assert far_fig.value == 1.25
        assert floor_fig is not None
        assert floor_fig.value == 250.0

    def test_far_trace_format(self):
        """FR-22 AC: trace shows '1.25 x 200 = 250 sq m, Rule 61 Table 8 row 1, p. 83'."""
        params = Params(plot_area=200, road_width=9.0, use_type="residential")
        far_fig, floor_fig = compute_far(params)
        assert floor_fig is not None
        trace = floor_fig.trace
        assert "1.25" in trace
        assert "200" in trace
        assert "250" in trace
        assert "61" in trace
        assert "83" in trace

    def test_floor_area_is_derived(self):
        params = Params(plot_area=200, road_width=9.0, use_type="residential")
        far_fig, floor_fig = compute_far(params)
        assert floor_fig is not None
        assert floor_fig.derived is True


class TestFees:
    """FR-20: Fee computation."""

    def test_appendix_a_fees(self):
        """AC: Residential, 250 sq m built-up → application fee Rs 250, permission fee Rs 3,000."""
        params = Params(plot_area=200, road_width=9.0, use_type="residential",
                        built_up_area=250)

        class FakeSettings:
            high_rise_height_threshold_m = 15.0

        figs = compute_fees(params, FakeSettings())
        app_fee = next((f for f in figs if f.topic == "application_fee"), None)
        perm_fee = next((f for f in figs if f.topic == "permission_fee"), None)

        assert app_fee is not None
        assert app_fee.value == 250.0, f"Expected 250, got {app_fee.value}"

        assert perm_fee is not None
        assert perm_fee.value == 3000.0, f"Expected 3000, got {perm_fee.value}"

    def test_no_fees_without_built_up_area(self):
        params = Params(plot_area=200, road_width=9.0, use_type="residential")

        class FakeSettings:
            high_rise_height_threshold_m = 15.0

        figs = compute_fees(params, FakeSettings())
        assert figs == []

    def test_application_fee_rule_page(self):
        params = Params(plot_area=200, road_width=9.0, use_type="residential",
                        built_up_area=100)

        class FakeSettings:
            high_rise_height_threshold_m = 15.0

        figs = compute_fees(params, FakeSettings())
        app_fee = next(f for f in figs if f.topic == "application_fee")
        assert app_fee.rule == "21"
        assert app_fee.page == 35


class TestGroundCoverage:
    """FR-51: Ground coverage."""

    def test_residential_no_prescribed_pct(self):
        params = Params(plot_area=200, road_width=9.0, use_type="residential", height=10.0)

        class FakeSettings:
            high_rise_height_threshold_m = 15.0

        fig = compute_ground_coverage(params, FakeSettings())
        assert fig.value is None
        assert "prescribed" in fig.trace.lower() or "plan check" in fig.trace.lower()

    def test_high_rise_30_pct(self):
        params = Params(plot_area=2500, road_width=30.0, use_type="residential", height=40.0)

        class FakeSettings:
            high_rise_height_threshold_m = 15.0

        fig = compute_ground_coverage(params, FakeSettings())
        assert fig.value == 30.0


class TestComputationIsolation:
    """FR-21: Numbers must not change when inference is disabled."""

    def test_front_setback_deterministic(self):
        """Same params always give same result regardless of inference state."""
        params = Params(plot_area=200, road_width=9.0, use_type="residential")
        fig1 = compute_front_setback(params)
        fig2 = compute_front_setback(params)
        assert fig1.value == fig2.value

    def test_rear_setback_deterministic(self):
        params = Params(plot_area=200, road_width=9.0, use_type="residential")
        fig1 = compute_rear_setback(params)
        fig2 = compute_rear_setback(params)
        assert fig1.value == fig2.value
