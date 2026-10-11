"""
Deterministic computation service for Bhumi Vikas Sahayak.
Implements FR-14 to FR-22, FR-51.
All arithmetic in code; no value originates from an inference service.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from backend.app.models import Figure, Params, Topic

ROOT = Path(__file__).resolve().parent.parent.parent.parent


def _load_tables() -> Dict[str, Any]:
    """Load range tables from config/range_tables.json."""
    path = ROOT / "config" / "range_tables.json"
    return {t["id"]: t for t in json.loads(path.read_text(encoding="utf-8"))}


TABLES: Dict[str, Any] = {}


def get_tables() -> Dict[str, Any]:
    global TABLES
    if not TABLES:
        TABLES = _load_tables()
    return TABLES


# ---------------------------------------------------------------------------
# Range lookup helper
# ---------------------------------------------------------------------------

def lookup_range(table_id: str, value: float) -> Optional[Dict[str, Any]]:
    """
    Find the matching row in a range table for the given scalar value.
    Boundaries follow rule wording exactly (FR-13).
    """
    tables = get_tables()
    table = tables.get(table_id)
    if table is None:
        return None
    for row in table.get("rows", []):
        lo = row.get("lower")
        hi = row.get("upper")
        lo_incl = row.get("lower_inclusive", False)
        hi_incl = row.get("upper_inclusive", False)

        lo_ok = True
        if lo is not None:
            lo_ok = (value >= lo) if lo_incl else (value > lo)

        hi_ok = True
        if hi is not None:
            hi_ok = (value <= hi) if hi_incl else (value < hi)

        if lo_ok and hi_ok:
            return row
    return None


# ---------------------------------------------------------------------------
# FR-14: Front setback
# ---------------------------------------------------------------------------

def compute_front_setback(params: Params) -> Figure:
    """
    FR-14: Front open space.
    - Road < 6.0 and existing_developed_area=True: Rule 56(1)(b), building line 6.0 m from centre
    - Road < 6.0 and flag absent: conditional figure with both cases
    - Otherwise: table front_56_1a for height <= 12.5; Rule 42 tables above
    """
    tables = get_tables()
    road = params.road_width or 0.0
    height = params.height or 0.0  # 0 means unspecified → default to <=12.5 branch
    eda = params.existing_developed_area

    if road < 6.0:
        if eda is True:
            # FR-14: building line 6.0 m from street centre
            # distance from plot boundary = 6.0 - road/2
            val = round(6.0 - road / 2.0, 2)
            return Figure(
                topic="front_setback",
                label="Front open space (narrow street, existing developed area)",
                value=val,
                unit="m",
                trace=(
                    f"Road {road} m < 6.0 m in existing developed area: "
                    f"building line 6.0 m from street centre line. "
                    f"Setback from plot boundary = 6.0 - {road}/2 = {val} m. "
                    f"Rule 56(1)(b), p. 77; Rule 46, p. 65."
                ),
                rule="56",
                page=77,
            )
        else:
            # eda is False or None → conditional
            val_56_1b = round(6.0 - road / 2.0, 2)
            row = lookup_range("front_56_1a", road)
            val_56_1a = row["value"] if row else None

            case_eda = Figure(
                topic="front_setback",
                label="If in existing developed area (Rule 56(1)(b))",
                value=val_56_1b,
                unit="m",
                trace=(
                    f"Existing developed area: building line 6.0 m from centre. "
                    f"6.0 - {road}/2 = {val_56_1b} m. Rule 56(1)(b), p. 77; Rule 46, p. 65."
                ),
                rule="56",
                page=77,
            )
            case_table = Figure(
                topic="front_setback",
                label="If not in existing developed area (Rule 56(1)(a))",
                value=val_56_1a,
                unit="m",
                trace=(
                    f"Not existing developed area: table row for road {road} m. "
                    f"Rule 56(1)(a), p. 77."
                ),
                rule="56",
                page=77,
            )
            return Figure(
                topic="front_setback",
                label="Front open space (conditional – clerk must confirm area type)",
                value=None,
                unit="m",
                conditional=True,
                trace=f"Road {road} m < 6.0 m: clerk must confirm whether plot is in existing developed area.",
                rule="56",
                page=77,
                cases=[case_eda, case_table],
            )

    # Normal case: table lookup
    if height <= 12.5 or height == 0.0:
        row = lookup_range("front_56_1a", road)
        if row:
            row_label = row["label"]
            lo_str = f"more than {row['lower']}" if row.get("lower") is not None else "up to"
            return Figure(
                topic="front_setback",
                label="Front open space",
                value=row["value"],
                unit="m",
                trace=(
                    f"Road width {road} m → Rule 56(1)(a) row: '{row_label}' gives {row['value']} m. "
                    f"Rule 56(1)(a), p. 77."
                ),
                rule="56",
                page=77,
            )

    # Height > 12.5: use Rule 42 Table 4 or 5
    return _front_setback_rule42(params)


def _front_setback_rule42(params: Params) -> Figure:
    """Front setback from Rule 42 Table 4 or 5 for tall buildings."""
    road = params.road_width or 0.0
    tables = get_tables()
    # Try Table 5 (high rise) first
    t5 = tables.get("high_rise_42_t5", {})
    for row in t5.get("rows", []):
        if road >= row["road_width_min"]:
            return Figure(
                topic="front_setback",
                label="Front MOS (high-rise, Rule 42 Table 5)",
                value=row["front_mos"],
                unit="m",
                trace=(
                    f"Road {road} m ≥ {row['road_width_min']} m: "
                    f"Rule 42 Table 5 gives front MOS {row['front_mos']} m. "
                    f"Rule 42 Table 5, p. 59."
                ),
                rule="42",
                page=59,
            )
    # Try Table 4
    t4 = tables.get("height_42_t4", {})
    for row in t4.get("rows", []):
        if road >= row["road_width_min"]:
            return Figure(
                topic="front_setback",
                label="Front MOS (above 12.5 m, Rule 42 Table 4)",
                value=row["front_mos"],
                unit="m",
                trace=(
                    f"Road {road} m ≥ {row['road_width_min']} m: "
                    f"Rule 42 Table 4 gives front MOS {row['front_mos']} m. "
                    f"Rule 42 Table 4, p. 58."
                ),
                rule="42",
                page=58,
            )
    return Figure(
        topic="front_setback",
        label="Front open space",
        value=None,
        unit="m",
        trace="Road width insufficient for Rule 42 Table 4 or Table 5; no match found.",
        rule="42",
        page=58,
    )


# ---------------------------------------------------------------------------
# FR-15: Rear setback
# ---------------------------------------------------------------------------

def compute_rear_setback(params: Params) -> Figure:
    """FR-15: Rear open space from Rule 56(2)(a) by plot area."""
    area = params.plot_area or 0.0
    row = lookup_range("rear_56_2a", area)
    if row:
        return Figure(
            topic="rear_setback",
            label="Rear open space",
            value=row["value"],
            unit="m",
            trace=(
                f"Plot area {area} sq m → Rule 56(2)(a) row: '{row['label']}' gives {row['value']} m. "
                f"Rule 56(2)(a), p. 78."
            ),
            rule="56",
            page=78,
        )
    return Figure(
        topic="rear_setback",
        label="Rear open space",
        value=None,
        unit="m",
        trace=f"Plot area {area} sq m: no matching row in Rule 56(2)(a).",
        rule="56",
        page=78,
    )


# ---------------------------------------------------------------------------
# FR-16: Side setback
# ---------------------------------------------------------------------------

def compute_side_setback(params: Params) -> Figure:
    """
    FR-16: Side open space from Rule 56(3) by development type.
    Validates against Rule 53(1)(i) on area and frontage.
    Without a type, returns conditional with permissible types from area/frontage.
    """
    tables = get_tables()
    dev_type = params.development_type
    height = params.height or 0.0
    frontage = params.frontage
    area = params.plot_area or 0.0

    # Validate development type against 53(1)(i)
    warning = None
    if dev_type and frontage is not None:
        warning = _validate_dev_type(dev_type, area, frontage, tables)

    if dev_type == "detached":
        return _side_detached(height, frontage, warning)
    elif dev_type == "semi_detached":
        return _side_semi_detached(height, frontage, warning)
    elif dev_type == "row":
        return Figure(
            topic="side_setback",
            label="Side open space (row type)",
            value=0.0,
            unit="m",
            trace="Row type: no side open space required. Rule 56(3)(iii), p. 78.",
            rule="56",
            page=78,
            warning=warning,
        )
    else:
        # No development type: conditional
        return _side_conditional(area, frontage, height, tables)


def _validate_dev_type(dev_type: str, area: float, frontage: float, tables: Dict) -> Optional[str]:
    """Return a warning string if the dev_type is out of Rule 53(1)(i) range."""
    t = tables.get("plot_type_53_1i", {})
    for row in t.get("rows", []):
        if row["development_type"] != dev_type:
            continue
        # Check area
        a_lo = row.get("area_lower")
        a_hi = row.get("area_upper")
        a_lo_incl = row.get("area_lower_inclusive", True)
        a_hi_incl = row.get("area_upper_inclusive", True)

        area_ok = True
        if a_lo is not None:
            area_ok = (area >= a_lo) if a_lo_incl else (area > a_lo)
        if a_hi is not None and area_ok:
            area_ok = (area <= a_hi) if a_hi_incl else (area < a_hi)

        f_lo = row.get("frontage_lower")
        f_hi = row.get("frontage_upper")
        f_lo_incl = row.get("frontage_lower_inclusive", True)
        f_hi_incl = row.get("frontage_upper_inclusive", True)

        frontage_ok = True
        if f_lo is not None:
            frontage_ok = (frontage >= f_lo) if f_lo_incl else (frontage > f_lo)
        if f_hi is not None and frontage_ok:
            frontage_ok = (frontage <= f_hi) if f_hi_incl else (frontage < f_hi)

        if not (area_ok and frontage_ok):
            return (
                f"Warning: plot area {area} sq m and frontage {frontage} m are "
                f"outside Rule 53(1)(i) range for {dev_type} type "
                f"({row['label']}). Setback computed but combination may not be permissible. "
                f"Rule 53(1)(i), p. 70."
            )
        return None  # in range, no warning

    return None


def _side_detached(height: float, frontage: Optional[float], warning: Optional[str]) -> Figure:
    if height <= 7.0 and frontage is not None and frontage < 12.0:
        val = 1.5
        label = "Side open space (detached, proviso: one side 1.5 m)"
        trace = (
            f"Detached, height {height} m ≤ 7.0 m and frontage {frontage} m < 12.0 m: "
            f"proviso applies, one side may be 1.5 m. Other side: 3.0 m. "
            f"Rule 56(3)(i) proviso, p. 78."
        )
    else:
        val = 3.0
        label = "Side open space (detached)"
        trace = (
            f"Detached: 3.0 m on both sides (proviso {'not applicable' if height > 7.0 or (frontage or 0) >= 12.0 else 'conditions unmet'}). "
            f"Rule 56(3)(i), p. 78."
        )
    return Figure(
        topic="side_setback",
        label=label,
        value=val,
        unit="m",
        trace=trace,
        rule="56",
        page=78,
        warning=warning,
    )


def _side_semi_detached(height: float, frontage: Optional[float], warning: Optional[str]) -> Figure:
    if height <= 10.0 and frontage is not None and frontage <= 10.0:
        val = 2.5
        label = "Side open space (semi-detached, open side, proviso: 2.5 m)"
        trace = (
            f"Semi-detached, height {height} m ≤ 10.0 m and frontage {frontage} m ≤ 10.0 m: "
            f"proviso applies, open side may be 2.5 m. Attached side: 0 m. "
            f"Rule 56(3)(ii) proviso, p. 78."
        )
    else:
        val = 3.0
        label = "Side open space (semi-detached, open side)"
        trace = (
            f"Semi-detached: 3.0 m on open side (proviso conditions not met). "
            f"Attached side: 0 m. Rule 56(3)(ii), p. 78."
        )
    return Figure(
        topic="side_setback",
        label=label,
        value=val,
        unit="m",
        trace=trace,
        rule="56",
        page=78,
        warning=warning,
    )


def _side_conditional(area: float, frontage: Optional[float], height: float, tables: Dict) -> Figure:
    """Without a dev type, derive permissible types from area/frontage and return conditional."""
    cases: List[Figure] = []
    t = tables.get("plot_type_53_1i", {})

    for row in t.get("rows", []):
        dev_type = row["development_type"]
        area_ok = _check_bound(area, row.get("area_lower"), row.get("area_upper"),
                               row.get("area_lower_inclusive", True), row.get("area_upper_inclusive", True))
        frontage_ok = True
        if frontage is not None:
            frontage_ok = _check_bound(frontage, row.get("frontage_lower"), row.get("frontage_upper"),
                                       row.get("frontage_lower_inclusive", True), row.get("frontage_upper_inclusive", True))
        if area_ok and frontage_ok:
            if dev_type == "detached":
                cases.append(_side_detached(height, frontage, None))
            elif dev_type == "semi_detached":
                cases.append(_side_semi_detached(height, frontage, None))
            elif dev_type == "row":
                cases.append(Figure(
                    topic="side_setback", label="Side open space (row type)",
                    value=0.0, unit="m",
                    trace="Row type: nil. Rule 56(3)(iii), p. 78.",
                    rule="56", page=78,
                ))

    if not cases:
        cases.append(Figure(
            topic="side_setback",
            label="Side open space",
            value=None, unit="m",
            trace="No permissible development type found for given area and frontage.",
            rule="53", page=70,
        ))

    return Figure(
        topic="side_setback",
        label="Side open space (conditional – clerk selects development type)",
        value=None,
        unit="m",
        conditional=True,
        trace=f"Development type not specified. Permissible types derived from Rule 53(1)(i) for area {area} sq m.",
        rule="53",
        page=70,
        cases=cases,
    )


def _check_bound(val: float, lo: Optional[float], hi: Optional[float], lo_incl: bool, hi_incl: bool) -> bool:
    lo_ok = True
    if lo is not None:
        lo_ok = (val >= lo) if lo_incl else (val > lo)
    hi_ok = True
    if hi is not None:
        hi_ok = (val <= hi) if hi_incl else (val < hi)
    return lo_ok and hi_ok


# ---------------------------------------------------------------------------
# FR-17: Height limit
# ---------------------------------------------------------------------------

def compute_height_limit(params: Params) -> Figure:
    """FR-17: Maximum height from Rule 42 Table 4 or 5 by road width."""
    road = params.road_width or 0.0
    tables = get_tables()

    if road < 12.0:
        return Figure(
            topic="height_limit",
            label="Height limit",
            value=12.5,
            unit="m",
            trace=(
                f"Road width {road} m is below 12.0 m: Rule 42 Table 4 requires a 12 m or wider road. "
                f"Rule 56 norms for buildings up to 12.5 m govern. "
                f"Rule 42 Table 4, p. 58; Rule 56, p. 77."
            ),
            rule="56",
            page=77,
        )

    # Check Table 5 (high-rise) first – match on road_width_min descending
    t5_rows = sorted(tables.get("high_rise_42_t5", {}).get("rows", []),
                     key=lambda r: r["road_width_min"], reverse=True)
    for row in t5_rows:
        if road >= row["road_width_min"]:
            height_max = row.get("height_max")
            label = f"Height limit (high-rise, Rule 42 Table 5)"
            trace = (
                f"Road {road} m ≥ {row['road_width_min']} m: "
                f"Rule 42 Table 5 gives height {'up to ' + str(height_max) + ' m' if height_max else 'above 90 m'}. "
                f"Minimum plot {row['plot_area_min']} sq m, frontage {row['frontage_min']} m. "
                f"Rule 42 Table 5, p. 59."
            )
            return Figure(topic="height_limit", label=label, value=height_max,
                          unit="m", trace=trace, rule="42", page=59)

    # Table 4
    t4_rows = sorted(tables.get("height_42_t4", {}).get("rows", []),
                     key=lambda r: r["road_width_min"], reverse=True)
    for row in t4_rows:
        if road >= row["road_width_min"]:
            return Figure(
                topic="height_limit",
                label="Height limit (Rule 42 Table 4)",
                value=row["height_max"],
                unit="m",
                trace=(
                    f"Road {road} m ≥ {row['road_width_min']} m: "
                    f"Rule 42 Table 4 gives height up to {row['height_max']} m. "
                    f"Minimum plot {row['plot_area_min']} sq m, frontage {row['frontage_min']} m. "
                    f"Rule 42 Table 4, p. 58."
                ),
                rule="42",
                page=58,
            )

    return Figure(
        topic="height_limit", label="Height limit", value=None, unit="m",
        trace=f"Road {road} m: no matching row in Rule 42 Table 4 or 5.",
        rule="42", page=58,
    )


# ---------------------------------------------------------------------------
# FR-18: Storey count (derived)
# ---------------------------------------------------------------------------

def compute_storey_count(params: Params, height_figure: Figure) -> Optional[Figure]:
    """FR-18: Only when floor_to_floor is supplied; labelled derived."""
    if not params.floor_to_floor or params.floor_to_floor <= 0:
        return None
    if height_figure.value is None:
        return None

    storeys = math.floor(height_figure.value / params.floor_to_floor)
    return Figure(
        topic="height_limit",
        label="Storey count (derived, not prescribed by the Rules)",
        value=float(storeys),
        unit="storeys",
        derived=True,
        trace=(
            f"floor(height limit {height_figure.value} m / floor-to-floor {params.floor_to_floor} m) = {storeys} storeys. "
            f"Derived figure; the Rules prescribe height, not storey count."
        ),
        rule=height_figure.rule,
        page=height_figure.page,
    )


# ---------------------------------------------------------------------------
# FR-19: FAR and floor area
# ---------------------------------------------------------------------------

def compute_far(params: Params) -> Tuple[Figure, Optional[Figure]]:
    """FR-19: FAR from Rule 61 Table 8; residential defaults 1.25."""
    area = params.plot_area or 0.0
    use = params.use_type or "residential"
    tables = get_tables()
    t = tables.get("far_61_t8", {})
    rows = t.get("rows", [])

    matched = None
    for row in rows:
        if row["use_type"] == use and row.get("category") is None:
            matched = row
            break
        if row["use_type"] == use:
            matched = row  # best match without category specified

    if matched is None:
        # Fallback: residential
        matched = next((r for r in rows if r["use_type"] == "residential"), None)

    if matched is None or matched.get("value") is None:
        far_fig = Figure(
            topic="far",
            label="FAR",
            value=None,
            unit="ratio",
            trace=f"FAR for use type '{use}' not found in Rule 61 Table 8. Rule 61 Table 8, p. 83.",
            rule="61",
            page=83,
        )
        return far_fig, None

    far_val = matched["value"]
    row_label = matched["label"]

    # Row index (1-based) for trace
    row_idx = rows.index(matched) + 1

    far_fig = Figure(
        topic="far",
        label="FAR",
        value=far_val,
        unit="ratio",
        trace=f"Use type '{use}': Rule 61 Table 8 row {row_idx}, '{row_label}'. Rule 61 Table 8, p. 83.",
        rule="61",
        page=83,
    )

    # Permitted floor area
    floor_area = round(far_val * area, 2)
    floor_fig = Figure(
        topic="far",
        label="Permitted floor area",
        value=floor_area,
        unit="sq m",
        derived=True,
        trace=(
            f"{far_val} x {area} = {floor_area} sq m, "
            f"Rule 61 Table 8 row {row_idx}, p. 83."
        ),
        rule="61",
        page=83,
    )
    return far_fig, floor_fig


# ---------------------------------------------------------------------------
# FR-20: Fees
# ---------------------------------------------------------------------------

def compute_fees(params: Params, settings) -> List[Figure]:
    """FR-20: Application fee (Rule 21(2)) and permission fee (Rule 21(3)(b) or (c))."""
    built_up = params.built_up_area
    use = params.use_type or "residential"
    height = params.height or 0.0
    high_rise_threshold = settings.high_rise_height_threshold_m

    if built_up is None:
        return []

    figures: List[Figure] = []

    # Application fee: Rs 1.00 per sq m built-up (Rule 21(2)(ii))
    app_fee = round(1.0 * built_up)
    figures.append(Figure(
        topic="application_fee",
        label="Application fee",
        value=float(app_fee),
        unit="Rs",
        trace=(
            f"Rule 21(2)(ii): Rs 1.00 x {built_up} sq m built-up = Rs {app_fee}. "
            f"Non-refundable. Rule 21(2), p. 35."
        ),
        rule="21",
        page=35,
    ))

    is_high_rise = height > high_rise_threshold

    if is_high_rise:
        # Rule 21(3)(c)
        perm_fee = round(10.0 * built_up)
        figures.append(Figure(
            topic="permission_fee",
            label="Permission fee (high-rise residential)",
            value=float(perm_fee),
            unit="Rs",
            trace=(
                f"High-rise residential (height {height} m > {high_rise_threshold} m): "
                f"Rs 10 x {built_up} sq m = Rs {perm_fee}. "
                f"Rule 21(3)(c), p. 37."
            ),
            rule="21",
            page=37,
        ))
    else:
        # Rule 21(3)(b) item 1 – residential slab
        row = lookup_range("perm_fee_21_3b_item1", built_up)
        if row:
            perm_fee = row["value"]
            surcharge = 0
            surcharge_pct = 0

            # Surcharges for non-residential
            if use in ("commercial",):
                surcharge_pct = 50
                surcharge = round(perm_fee * surcharge_pct / 100)

            total_perm = perm_fee + surcharge

            trace = (
                f"Rule 21(3)(b) item 1, slab '{row['label']}' → Rs {perm_fee}"
            )
            if surcharge:
                trace += f" + {surcharge_pct}% surcharge ({use}) = Rs {total_perm}"
            trace += f". Rule 21(3)(b), p. 36."

            figures.append(Figure(
                topic="permission_fee",
                label="Permission fee",
                value=float(total_perm),
                unit="Rs",
                trace=trace,
                rule="21",
                page=36,
            ))

    return figures


# ---------------------------------------------------------------------------
# FR-51: Ground coverage
# ---------------------------------------------------------------------------

def compute_ground_coverage(params: Params, settings) -> Figure:
    """
    FR-51: Prescribed percentage for high-rise (Table 5 30%);
    for residential up to 12.5 m, derived from setbacks requires plan check.
    """
    height = params.height or 0.0
    is_high_rise = height > settings.high_rise_height_threshold_m

    if is_high_rise:
        # Table 5 gives 30% for all high-rise rows
        return Figure(
            topic="ground_coverage",
            label="Ground coverage (high-rise, prescribed)",
            value=30.0,
            unit="%",
            trace="High-rise: Rule 42 Table 5 prescribes 30% ground coverage for all road-width rows. Rule 42 Table 5, p. 59.",
            rule="42",
            page=59,
        )

    # Not high-rise: prescribed percentage exists for Rules 53, 95, 96 cases
    # For residential up to 12.5 m, no prescribed percentage; requires plan check
    return Figure(
        topic="ground_coverage",
        label="Ground coverage",
        value=None,
        unit="%",
        trace=(
            "For residential buildings up to 12.5 m, the Rules set no ground coverage percentage. "
            "Derived ground coverage (envelope area / plot area) requires the plan check (Phase 3). "
            "Rule 2(20) definition: area covered by the plinth at ground floor level."
        ),
        rule="2",
        page=2,
    )
