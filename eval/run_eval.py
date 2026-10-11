"""Evaluation harness (FR-34, FR-50). Prints one line per sample question, then one line per geometry
case, then totals for each group. Exits non-zero on any failure.

Run from the repository root: python eval/run_eval.py
"""
import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("BVS_LOG_PATH", str(Path(tempfile.gettempdir()) / "bvs_eval_queries.jsonl"))

from backend.app.services import plan_check  # noqa: E402

TOL = 0.005


def close(a, b) -> bool:
    return a is not None and abs(a - b) <= TOL


def check_geometry(case: dict) -> tuple[bool, str, bool]:
    """Return (passed, detail, false_no_conflict)."""
    exp = case["expect"]
    try:
        r = plan_check.run(case["request"])
    except plan_check.PlanCheckError as e:
        if exp.get("http") == 422:
            return True, f"422: {e.reason}", False
        return False, f"unexpected 422: {e.reason}", False
    if exp.get("http") == 422:
        return False, f"expected 422, got status {r['status']}", False

    errs = []
    if r["status"] != exp["status"]:
        errs.append(f"status {r['status']} != {exp['status']}")
    for s in exp.get("message_contains", []):
        if s not in (r.get("message") or ""):
            errs.append(f"message lacks {s!r}")
    g = r.get("geometry") or {}
    false_nc = False
    if "result" in exp:
        if g.get("result") != exp["result"]:
            errs.append(f"result {g.get('result')!r}")
            false_nc = exp["result"] == "Setback conflict found"
    sides = {s["side"]: s for s in g.get("sides", [])}
    for side, (req, short) in exp.get("sides", {}).items():
        s = sides.get(side, {})
        if not (close(s.get("required"), req) and close(s.get("shortfall"), short)):
            errs.append(f"{side} {s.get('required')}/{s.get('shortfall')} != {req}/{short}")
    for side, rule in exp.get("rule", {}).items():
        if sides.get(side, {}).get("rule") != rule:
            errs.append(f"{side} rule {sides.get(side, {}).get('rule')} != {rule}")
    for side, text in exp.get("trace_contains", {}).items():
        if text not in sides.get(side, {}).get("trace", ""):
            errs.append(f"{side} trace lacks {text!r}")
    for key, path in (("envelope_area", ("envelope", "area")), ("footprint_area", ("footprint", "area")),
                      ("plot_area", ("plot", "area"))):
        if key in exp and not close(g.get(path[0], {}).get(path[1]), exp[key]):
            errs.append(f"{key} {g.get(path[0], {}).get(path[1])} != {exp[key]}")
    if "ground_coverage" in exp and not close(g.get("ground_coverage_derived"), exp["ground_coverage"]):
        errs.append(f"ground coverage {g.get('ground_coverage_derived')}")
    for o in exp.get("overlaps", []):
        got = next((x for x in g.get("overlaps", []) if x["side"] == o["side"]), None)
        if not got or not all(close(got[k], o[k]) for k in ("x", "y", "width", "depth")):
            errs.append(f"{o['side']} overlap {got}")
    if "warning" in exp:
        has = any(f.get("warning") for f in r.get("figures", []))
        if has != exp["warning"]:
            errs.append(f"warning present={has}")
    detail = "; ".join(errs) if errs else (g.get("result") or r["status"])
    return not errs, detail, false_nc


def main() -> int:
    data = json.loads((ROOT / "eval" / "expectations.json").read_text(encoding="utf-8"))

    questions = data.get("questions", [])
    print(f"Sample questions ({len(questions)})")
    if not questions:
        print(f"  none defined: {data.get('questions_note', '')}")
    q_pass = 0  # question runner arrives with /api/lookup in Phase 2

    cases = data["geometry"]
    print(f"\nGeometry cases ({len(cases)})")
    g_pass = false_nc = 0
    for c in cases:
        ok, detail, fnc = check_geometry(c)
        g_pass += ok
        false_nc += fnc
        page = ", ".join(f"p. {p}" for p in c["verification_page"]) or "-"
        print(f"  {c['id']:<5} {'PASS' if ok else 'FAIL'}  {c['name']}  [{detail}]  verify: {page}")

    print("\nTotals")
    print(f"  Sample questions: {q_pass} / {len(questions)} passed")
    print(f"  Geometry cases:   {g_pass} / {len(cases)} passed; false 'no conflict' results: {false_nc}")
    return 0 if g_pass == len(cases) and q_pass == len(questions) else 1


if __name__ == "__main__":
    sys.exit(main())
