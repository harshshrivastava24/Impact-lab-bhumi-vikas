"""Plan check orchestration behind POST /api/plan-check (FR-39 to FR-51).

Checks run in a fixed order, each returning early: mandatory fields (422), unsupported cases (refused),
area mismatch (blocked), footprint validity (422), then computation. The backend is stateless; the
frontend re-sends on every change (FR-44).
"""
from numbers import Real

from .. import plan_config as config
from ..models import Params
from . import audit, geometry, inference, retrieval
from . import setbacks as compute
from .setbacks import m, sqm

MANDATORY = ("plot_area", "road_width", "use_type", "frontage", "depth", "development_type", "height")
DEV_TYPES = ("detached", "semi_detached", "row")


class PlanCheckError(Exception):
    """Maps to HTTP 422 with the reason and the offending field."""

    def __init__(self, field: str, reason: str):
        super().__init__(reason)
        self.field = field
        self.reason = reason


def _number(v) -> bool:
    return isinstance(v, Real) and not isinstance(v, bool)


def _base(language: str, S: dict) -> dict:
    return {
        "figures": [],
        "citations": [],
        "version": config.version(),
        "amendment_flags": [],
        "disclaimer": S["disclaimer"],
        "language": language,
        "used_inference": False,
    }


def _amendment_flags(plot_area: float) -> list[dict]:
    """Same register and matching as /api/lookup (FR-25)."""
    keys = ("date", "rule", "concerns", "source_url", "source_kind", "applied", "note")
    return [{k: a[k] for k in keys} for a in retrieval.check_amendments(Params(plot_area=plot_area))]


def _citation(rule: str, sub_rule: str) -> dict | None:
    c = retrieval.build_citation(rule, sub_rule or None, config.corpus(), config.app_settings())
    return c.model_dump() if c else None


def _guard(figures: list[dict]) -> list[dict]:
    """FR-27: every rule number must exist in the corpus or the inserted-rule list."""
    valid = retrieval.build_valid_rules(config.corpus())
    return [f for f in figures if retrieval.guard_rule(f["rule"], valid, "plan-check")]


def _validate(req: dict) -> tuple[dict, dict]:
    params = req.get("params")
    if not isinstance(params, dict):
        raise PlanCheckError("params", "Missing field: params")
    for f in MANDATORY:
        if params.get(f) is None:
            raise PlanCheckError(f"params.{f}", f"Missing field for plan check: {f}")
    for f in ("plot_area", "road_width", "frontage", "depth", "height"):
        if not _number(params[f]) or params[f] <= 0:
            raise PlanCheckError(f"params.{f}", f"{f} must be a number above 0")
    fp = req.get("footprint") or params.get("footprint")
    if not isinstance(fp, dict):
        raise PlanCheckError("footprint", "Missing field for plan check: footprint")
    for s in geometry.SIDES:
        if not _number(fp.get(s)):
            raise PlanCheckError(f"footprint.{s}", f"Missing field for plan check: footprint.{s}")
    return params, {s: float(fp[s]) for s in geometry.SIDES}


def run(req: dict) -> dict:
    language = "hi" if req.get("language") == "hi" else "en"
    S = config.strings(language)
    pc = config.raw_settings()["plan_check"]

    # Step 1.1: mandatory fields
    params, fp = _validate(req)
    out = _base(language, S)

    # Step 1.2: unsupported cases (FR-48)
    refusal = None
    if (params.get("streets_abutting") or 1) >= 2:
        refusal = S["msg_refuse_corner"]
    elif params["use_type"] != "residential":
        refusal = S["msg_refuse_use"]
    elif params["height"] > pc["max_height"]:
        refusal = S["msg_refuse_height"]
    if refusal:
        out.update(status="refused", message=refusal, geometry=None)
        audit.log_plan_check({"endpoint": "plan-check", "status": "refused", "params": audit.clean_params(params),
                   "topics": ["plan_check"], "version": out["version"], "used_inference": False})
        return out

    frontage, depth = float(params["frontage"]), float(params["depth"])
    for f, v in (("frontage", frontage), ("depth", depth)):
        if not pc["dimension_min"] <= v <= pc["dimension_max"]:
            raise PlanCheckError(f"params.{f}", f"{f} must be between {pc['dimension_min']} and {pc['dimension_max']} m")
    if params["development_type"] not in DEV_TYPES:
        raise PlanCheckError("params.development_type", f"development_type must be one of {', '.join(DEV_TYPES)}")

    # Step 1.3: area mismatch gate (FR-39)
    stated = float(params["plot_area"])
    computed = frontage * depth
    use_dims = req.get("resolution") == "use_dimensions"
    if not use_dims and abs(computed - stated) / stated > pc["area_mismatch_tolerance"]:
        out.update(
            status="blocked",
            message=S["msg_area_mismatch"].format(computed=sqm(computed), stated=sqm(stated)),
            resolutions=["correct_inputs", "use_dimensions"],
            geometry=None,
        )
        audit.log_plan_check({"endpoint": "plan-check", "status": "blocked", "params": audit.clean_params(params),
                   "topics": ["plan_check"], "version": out["version"], "used_inference": False})
        return out
    plot_area = computed if use_dims else stated
    area_note = f" (taken as frontage x depth, {m(frontage)} x {m(depth)}, by clerk resolution)" if use_dims else ""

    # Step 1.4: footprint validity (FR-42)
    err = geometry.footprint_error(frontage, depth, fp)
    if err:
        raise PlanCheckError("footprint", err)

    # Step 2: required sides (FR-14, FR-15, FR-16)
    try:
        front = compute.front(float(params["road_width"]), params.get("existing_developed_area"))
    except compute.MissingInput as e:
        raise PlanCheckError(f"params.{e.field}", str(e)) from e
    rear = compute.rear(plot_area, area_note)
    left, right = compute.sides(params["development_type"], frontage, float(params["height"]))
    required = {"front": front, "rear": rear, "left": left, "right": right}
    req_v = {s: required[s]["value"] for s in geometry.SIDES}

    env = geometry.envelope(frontage, depth, req_v)
    foot = geometry.footprint(frontage, depth, fp)
    short = geometry.shortfalls(req_v, fp)
    laps = geometry.overlaps(frontage, depth, req_v, fp)
    gc = geometry.ground_coverage(env["area"], plot_area)

    # Step 3: per-side table and result wording (FR-43, FR-46, FR-47)
    sides = [
        {
            "side": s,
            "required": geometry.r2(req_v[s]),
            "provided": geometry.r2(fp[s]),
            "shortfall": short[s],
            "rule": required[s]["rule"] + required[s]["sub_rule"],
            "page": required[s]["page"],
            "trace": required[s]["trace"],
        }
        for s in geometry.SIDES
    ]
    conflict = any(v > 0 for v in short.values())

    gcd = config.raw_settings()["ground_coverage_definition"]
    gc_page = config.corpus().by_rule[gcd["rule"]].page_start
    gc_trace = (
        f"envelope {m(env['width'])} x {m(env['depth'])} = {sqm(env['area'])} sq m; {sqm(env['area'])} / {sqm(plot_area)} "
        f"x 100 = {gc:.1f} %, plot area {sqm(plot_area)} sq m{area_note}; derived from setbacks, not a prescribed "
        f"percentage; ground coverage as defined in Rule 2(20)"
    )

    figures = [
        {"topic": "front_setback" if s == "front" else "rear_setback" if s == "rear" else "side_setback",
         "label": S[f"label_{s}"], "value": req_v[s], "unit": "m", "derived": False, "conditional": False,
         "trace": required[s]["trace"], "rule": required[s]["rule"], "page": required[s]["page"]}
        for s in geometry.SIDES
    ]
    figures.append({"topic": "ground_coverage", "label": S["label_ground_coverage"], "value": gc, "unit": "%",
                    "derived": True, "conditional": False, "trace": gc_trace, "rule": gcd["rule"], "page": gc_page})

    # Step 1.5: development type validation; proceeds with a warning (FR-16)
    warning = compute.plot_type_warning(params["development_type"], plot_area, frontage, area_note)
    if warning:
        figures.append({"topic": "side_setback", "label": S["label_dev_type_warning"], "value": None, "unit": "",
                        "derived": False, "conditional": False, "warning": True, "trace": warning["trace"],
                        "rule": warning["rule"], "page": warning["page"]})

    cited = [("56", "")]
    if front.get("related_rules"):
        cited += [(r, "") for r in front["related_rules"]]
    if warning:
        cited.append((warning["rule"], warning["sub_rule"]))
    cited.append((gcd["rule"], gcd["sub_rule"]))
    citations = [c for c in (_citation(r, sr) for r, sr in cited) if c]
    figures = _guard(figures)

    out.update(
        status="answered",
        figures=figures,
        citations=citations,
        amendment_flags=_amendment_flags(plot_area),
        geometry={
            "plot": {"width": geometry.r2(frontage), "depth": geometry.r2(depth), "area": geometry.r2(plot_area)},
            "required": {s: {k: required[s][k] for k in ("value", "rule", "sub_rule", "page", "trace")}
                         for s in geometry.SIDES},
            "envelope": env,
            "footprint": foot,
            "sides": sides,
            "overlaps": laps,
            "result": S["result_conflict"] if conflict else S["result_no_conflict"],
            "checks_performed": [S[f"check_{s}"] for s in geometry.SIDES],
            "not_checked": S["not_checked"],
            "ground_coverage_derived": gc,
            "exceptions_available": [
                {"id": e["id"], "label": S.get(f"exception_{e['id']}", e["label"]), "rule": e["rule"], "page": e["page"]}
                for e in config.exceptions()
            ],
        },
    )

    # Step 5: optional Hindi rendering, kept apart from the official English trace (FR-30)
    if language == "hi":
        rendered = inference.render_hi([x["trace"] for x in sides])
        if rendered:
            out["trace_hi"] = {"rendering": True, "label": S["rendering_label"],
                               "sides": [{"side": s["side"], "text": t} for s, t in zip(sides, rendered)]}
            out["used_inference"] = True

    # Step 6: audit log (FR-38, FR-49)
    audit.log_plan_check({
        "endpoint": "plan-check",
        "status": "answered",
        "params": audit.clean_params(params),
        "topics": ["plan_check"],
        "rules_cited": sorted({f["rule"] for f in figures}),
        "figures": [{"topic": f["topic"], "value": f["value"], "rule": f["rule"], "page": f["page"]} for f in figures],
        "version": out["version"],
        "amendment_flags": [{"date": a["date"], "rule": a["rule"]} for a in out["amendment_flags"]],
        "used_inference": out["used_inference"],
        "geometry_inputs": {"frontage": frontage, "depth": depth, "footprint": fp,
                            "development_type": params["development_type"], "height": params["height"],
                            "resolution": "use_dimensions" if use_dims else None},
        "sides": [{k: s[k] for k in ("side", "required", "provided", "shortfall", "rule", "page")} for s in sides],
    })
    return out
