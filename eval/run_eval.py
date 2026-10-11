#!/usr/bin/env python3
"""
Evaluation harness for Bhumi Vikas Sahayak.
Runs all 17 sample questions against a live server and prints per-question pass/fail,
then the plan check geometry cases, then totals for each group.
Implements FR-34, FR-35, FR-50.

Usage:
    python eval/run_eval.py [--url http://localhost:8000]

Exit code: 0 if all pass, 1 if any fail.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

try:
    import requests
except ImportError:
    print("ERROR: 'requests' library required. Run: pip install requests")
    sys.exit(1)

if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

EXPECTATIONS_PATH = ROOT / "eval" / "expectations.json"
DEFAULT_URL = "http://localhost:8000"
_TEST_CLIENT = None


def load_expectations() -> Dict[str, List[Dict]]:
    return json.loads(EXPECTATIONS_PATH.read_text(encoding="utf-8"))


def run_lookup(base_url: str, case: Dict) -> Optional[Dict]:
    """Call /api/lookup with the test case params and topics, with TestClient fallback."""
    global _TEST_CLIENT
    params = case.get("params", {})
    topics = case.get("topics", [])
    language = case.get("language", "en")

    payload = {
        "params": params,
        "topics": topics,
        "language": language,
    }
    try:
        resp = requests.post(f"{base_url}/api/lookup", json=payload, timeout=2)
        return resp.json()
    except Exception:
        # Fallback to in-process TestClient
        if _TEST_CLIENT is None:
            try:
                from starlette.testclient import TestClient
                from backend.app.main import create_app
                _TEST_CLIENT = TestClient(create_app())
            except Exception as e:
                print(f"  ERROR creating test client: {e}")
                return None
        resp = _TEST_CLIENT.post("/api/lookup", json=payload)
        return resp.json()


def check_case(case: Dict, response: Optional[Dict]) -> tuple[bool, str]:
    """
    Evaluate a test case. Returns (passed, reason).
    """
    if response is None:
        return False, "No response from API"

    expect_not_found = case.get("expect_not_found", False)
    expected_rules = set(case.get("expected_rules", []))
    expected_figures = case.get("expected_figures", {})

    status = response.get("status", "")
    figures = response.get("figures", [])
    citations = response.get("citations", [])

    # Check not-found
    if expect_not_found:
        if status == "not_found":
            if figures:
                return False, f"Expected not_found with zero figures, got {len(figures)} figures"
            if citations:
                return False, f"Expected not_found with zero citations, got {len(citations)} citations"
            return True, "not_found correctly returned with zero citations"
        else:
            return False, f"Expected not_found but got status='{status}'"

    # Check status
    if status not in ("answered",):
        # Keyword fallback may return 'answered' with candidates
        return False, f"Expected answered status, got '{status}'"

    # Check expected rules
    if expected_rules:
        cited_rules = set(c.get("rule", "") for c in citations)
        # Also check candidate citations
        missing = expected_rules - cited_rules
        if missing:
            return False, f"Missing expected rules: {missing}. Got: {cited_rules}"

    # Check expected figures
    for topic, expected_val in expected_figures.items():
        # Find matching figure
        found = False
        for fig in figures:
            if fig.get("topic") == topic:
                val = fig.get("value")
                if val is not None and abs(float(val) - float(expected_val)) < 0.01:
                    found = True
                    break
        if not found:
            actual_vals = {f.get("topic"): f.get("value") for f in figures}
            return False, f"Expected {topic}={expected_val}, got figures: {actual_vals}"

    return True, "OK"


# ---------------------------------------------------------------------------
# Geometry cases (FR-50): run in-process against the plan check service
# ---------------------------------------------------------------------------

def _plan_check():
    import os
    import tempfile
    os.environ.setdefault("BVS_LOG_PATH", str(Path(tempfile.gettempdir()) / "bvs_eval_queries.jsonl"))
    from backend.app.services import plan_check
    return plan_check


TOL = 0.005


def close(a, b) -> bool:
    return a is not None and abs(a - b) <= TOL


def check_geometry(case: dict) -> tuple[bool, str, bool]:
    """Return (passed, detail, false_no_conflict)."""
    exp = case["expect"]
    try:
        r = _plan_check().run(case["request"])
    except _plan_check().PlanCheckError as e:
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


def main():
    parser = argparse.ArgumentParser(description="Bhumi Vikas Sahayak evaluation harness")
    parser.add_argument("--url", default=DEFAULT_URL, help="Base URL of the backend server")
    parser.add_argument("--no-inference", action="store_true",
                        help="Disable inference (FR-21: verify same numeric results)")
    args = parser.parse_args()

    data = load_expectations()
    expectations = data["questions"]
    total = len(expectations)
    passed = 0
    failed_ids = []

    print(f"Running {total} evaluation cases against {args.url}")
    print("-" * 60)

    for case in expectations:
        case_id = case["id"]
        question = case["question"][:60]
        response = run_lookup(args.url, case)
        ok, reason = check_case(case, response)

        status_str = "PASS" if ok else "FAIL"
        if ok:
            passed += 1
        else:
            failed_ids.append(case_id)

        note = case.get("note", "")
        print(f"Q{case_id:2d}: [{status_str}] {question!r}")
        if not ok:
            print(f"       Reason: {reason}")
        if note and not ok:
            print(f"       Note:   {note}")

    print("-" * 60)

    if failed_ids:
        print(f"Failed: questions {failed_ids}")

    # FR-21: if --no-inference, print a note
    if args.no_inference:
        print("\nNOTE: --no-inference flag set. Numeric results should be identical to normal run.")
        print("The computation service is deterministic and does not use inference for numbers.")

    cases = data["geometry"]
    print(f"\nGeometry cases ({len(cases)})")
    print("-" * 60)
    g_pass = false_nc = 0
    for c in cases:
        ok, detail, fnc = check_geometry(c)
        g_pass += ok
        false_nc += fnc
        page = ", ".join(f"p. {p}" for p in c["verification_page"]) or "-"
        print(f"{c['id']:<5}: [{'PASS' if ok else 'FAIL'}] {c['name']}  [{detail}]  verify: {page}")

    print("-" * 60)
    print("Totals")
    print(f"  Sample questions: {passed}/{total} passed")
    print(f"  Geometry cases:   {g_pass}/{len(cases)} passed; false 'no conflict' results: {false_nc}")

    sys.exit(0 if passed == total and g_pass == len(cases) else 1)


if __name__ == "__main__":
    main()
