"""Per-side setback requirements for the plan check (FR-14, FR-15, FR-16, FR-40, FR-47).

Reads the same config/range_tables.json rows as compute.py, which serves /api/lookup. The plan check
needs left and right sides separately and the FR-47 trace format, so it has its own functions;
test_setbacks_match_lookup asserts both give the same values.

Each function returns a SideReq dict: value, rule, sub_rule, page, trace, plus related_rules where
another rule is read with it.
"""
from .. import plan_config as config
from .tables import in_range, lookup


class MissingInput(ValueError):
    def __init__(self, field: str, reason: str):
        super().__init__(reason)
        self.field = field


def m(x: float) -> str:
    """Format a distance: one decimal when exact, else two (NFR-23)."""
    return f"{x:.1f}" if round(x, 1) == round(x, 2) else f"{x:.2f}"


def sqm(x: float) -> str:
    """Format an area without trailing zeros: 200, 108.75."""
    return f"{round(x, 2):.2f}".rstrip("0").rstrip(".")


def row_wording(row: dict, fmt, unit: str) -> str:
    """Rule wording for a range row: 'up to 9.0 m', 'more than 9.0 m and up to 12.0 m', 'above 18.0 m'."""
    lo, hi = row["lower"], row["upper"]
    if lo is None:
        return f"up to {fmt(hi)} {unit}"
    if hi is None:
        return f"above {fmt(lo)} {unit}"
    return f"more than {fmt(lo)} {unit} and up to {fmt(hi)} {unit}"


def front(road_width: float, existing_developed_area: bool | None) -> dict:
    t = config.tables()
    narrow = t["narrow_street_56_1b"]
    if road_width < narrow["street_width_below"]:
        if existing_developed_area is None:
            raise MissingInput(
                "existing_developed_area",
                f"Road width is under {m(narrow['street_width_below'])} m; state whether the plot is in an "
                "existing developed area (Rule 56(1)(b)).",
            )
        if existing_developed_area:
            line = narrow["building_line_from_centre"]
            value = line - road_width / 2
            return {
                "value": round(value, 2),
                "rule": narrow["rule"],
                "sub_rule": narrow["sub_rule"],
                "page": narrow["page"],
                "related_rules": narrow["related_rules"],
                "trace": (
                    f"road width {m(road_width)} m, under {m(narrow['street_width_below'])} m in an existing developed area, "
                    f"Rule 56(1)(b) building line {m(line)} m from the street centre line: "
                    f"{m(line)} - {m(road_width)} / 2 = {m(value)} m from the plot boundary, read with Rule 46, p. {narrow['page']}"
                ),
            }
    table = t["front_56_1a"]
    i, row = lookup(table, road_width)
    trace = (
        f"road width {m(road_width)} m, Rule 56(1)(a) row {i}, {row_wording(row, m, 'm')} gives {m(row['value'])} m, "
        f"p. {table['page']}"
    )
    if road_width < narrow["street_width_below"]:
        trace += "; Rule 56(1)(b) considered and not applied (not an existing developed area)"
    return {"value": row["value"], "rule": table["rule"], "sub_rule": table["sub_rule"], "page": table["page"], "trace": trace}


def rear(plot_area: float, area_note: str = "") -> dict:
    table = config.tables()["rear_56_2a"]
    i, row = lookup(table, plot_area)
    trace = (
        f"plot area {sqm(plot_area)} sq m{area_note}, Rule 56(2)(a) row {i}, {row_wording(row, sqm, 'sq m')} gives "
        f"{m(row['value'])} m, p. {table['page']}"
    )
    return {"value": row["value"], "rule": table["rule"], "sub_rule": table["sub_rule"], "page": table["page"], "trace": trace}


def _proviso_applies(p: dict, height: float, frontage: float) -> bool:
    return in_range(height, None, p["height_max"], False, p["height_max_inclusive"]) and in_range(
        frontage, None, p["frontage_max"], False, p["frontage_max_inclusive"]
    )


def sides(development_type: str, frontage: float, height: float) -> tuple[dict, dict]:
    """Return (left, right). Convention: a reduced or single side open space is on the left."""
    table = config.tables()["side_56_3"]
    spec = next(c for c in table["cases"] if c["development_type"] == development_type)
    sub, page = spec["sub_rule"], table["page"]
    ref = f"Rule 56{sub}"
    name = development_type.replace("_", "-")

    def req(value, trace):
        return {"value": value, "rule": table["rule"], "sub_rule": sub, "page": page, "trace": trace}

    if development_type == "row":
        v = spec["value"]
        t = f"{name}, {ref}: {m(v)} m on both sides, p. {page}"
        return req(v, t), req(v, t)

    p = spec["proviso_values"]
    label = spec["proviso"]["label"]
    applies = _proviso_applies(p, height, frontage)
    cond = f"height {m(height)} m, frontage {m(frontage)} m"
    if development_type == "semi_detached":
        full = spec["base_value_open_side"]
        left_v = p["reduced_value"] if applies else full
        status = (
            f"proviso applied ({label}): {m(full)} m reduced to {m(left_v)} m"
            if applies
            else f"proviso not applied ({label}): {m(full)} m"
        )
        left = req(left_v, f"{name}, {cond}, {ref} {status}; open space on the left side by convention, p. {page}")
        right = req(spec["attached_side"],
                    f"{name}, {ref}: open space on one side only; right side nil by convention, p. {page}")
        return left, right

    # detached
    full = spec["base_value_each_side"]
    left_v = p["reduced_value"] if applies else full
    status = (
        f"proviso applied ({label}): one side {m(full)} m reduced to {m(left_v)} m"
        if applies
        else f"proviso not applied ({label}): {m(full)} m"
    )
    left = req(left_v, f"{name}, {cond}, {ref} {status}; reduced side on the left by convention, p. {page}")
    right = req(full, f"{name}, {ref}: {m(full)} m on both sides; right side {m(full)} m, p. {page}")
    return left, right


def plot_type_warning(development_type: str, plot_area: float, frontage: float, area_note: str = "") -> dict | None:
    """Validate the development type against Rule 53(1)(i) on area and frontage (FR-16)."""
    table = config.tables()["plot_type_53_1i"]
    row = next(r for r in table["rows"] if r["development_type"] == development_type)
    problems = []
    if not in_range(plot_area, row["area_lower"], row["area_upper"], row["area_lower_inclusive"], row["area_upper_inclusive"]):
        problems.append(f"plot area {sqm(plot_area)} sq m{area_note}")
    if not in_range(frontage, row["frontage_lower"], row["frontage_upper"], row["frontage_lower_inclusive"],
                    row["frontage_upper_inclusive"]):
        problems.append(f"frontage {m(frontage)} m")
    if not problems:
        return None
    return {
        "rule": table["rule"],
        "sub_rule": table["sub_rule"],
        "page": table["page"],
        "trace": f"{' and '.join(problems)} outside Rule 53(1)(i) row {row['label']}, p. {table['page']}; "
        "setbacks computed for the stated type",
    }
