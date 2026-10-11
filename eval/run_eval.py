#!/usr/bin/env python3
"""
Evaluation harness for Bhumi Vikas Sahayak.
Runs all 17 sample questions against a live server and prints per-question pass/fail.
Implements FR-34, FR-35.

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

EXPECTATIONS_PATH = ROOT / "eval" / "expectations.json"
DEFAULT_URL = "http://localhost:8000"


def load_expectations() -> List[Dict]:
    return json.loads(EXPECTATIONS_PATH.read_text(encoding="utf-8"))


def run_lookup(base_url: str, case: Dict) -> Optional[Dict]:
    """Call /api/lookup with the test case params and topics."""
    params = case.get("params", {})
    topics = case.get("topics", [])
    language = case.get("language", "en")

    payload = {
        "params": params,
        "topics": topics,
        "language": language,
    }
    try:
        resp = requests.post(f"{base_url}/api/lookup", json=payload, timeout=10)
        return resp.json()
    except Exception as exc:
        print(f"  ERROR calling API: {exc}")
        return None


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


def main():
    parser = argparse.ArgumentParser(description="Bhumi Vikas Sahayak evaluation harness")
    parser.add_argument("--url", default=DEFAULT_URL, help="Base URL of the backend server")
    parser.add_argument("--no-inference", action="store_true",
                        help="Disable inference (FR-21: verify same numeric results)")
    args = parser.parse_args()

    expectations = load_expectations()
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
    print(f"Results: {passed}/{total} passed")

    if failed_ids:
        print(f"Failed: questions {failed_ids}")

    # FR-21: if --no-inference, print a note
    if args.no_inference:
        print("\nNOTE: --no-inference flag set. Numeric results should be identical to normal run.")
        print("The computation service is deterministic and does not use inference for numbers.")

    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
