"""Generate MSW fixtures from the real rule corpus.

Run from the frontend folder:  python scripts/make_fixtures.py

Verbatim rule text comes from ../data/bhumi_vikas_rules.jsonl. Every cited page
is located in ../data/bhumi_vikas_rules_fulltext_by_page.txt and asserted to
match the page stated in the shared context, so a fixture can never cite a
wrong page. Figures are the worked-example values from SRS Appendix A and A.5;
they are fixed test data, not computed here.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
OUT = Path(__file__).resolve().parents[1] / "src" / "mocks" / "fixtures"

RULES = {}
for line in (DATA / "bhumi_vikas_rules.jsonl").read_text(encoding="utf-8").splitlines():
    rec = json.loads(line)
    RULES[rec["rule"]] = rec

PAGES: dict[int, str] = {}
for chunk in re.split(r"^===== PDF page (\d+) =====\s*$", (DATA / "bhumi_vikas_rules_fulltext_by_page.txt").read_text(encoding="utf-8"), flags=re.M)[1:]:
    pass
_parts = re.split(r"^===== PDF page (\d+) =====\s*$", (DATA / "bhumi_vikas_rules_fulltext_by_page.txt").read_text(encoding="utf-8"), flags=re.M)
for i in range(1, len(_parts), 2):
    PAGES[int(_parts[i])] = _parts[i + 1]

HEADER = re.compile(r"^\s*Rule [0-9A-Za-z\-(), ]+?\s{2,}M\.P\. Bhumi Vikas Rules, 2012\s+\d+\s*$", re.M)
FOOTNOTE = re.compile(r"((?:Subs\.|Ins\.|Inserted|Substituted)[^\n]*\n[^\n]*Published[^\n]*)")


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def page_of(snippet: str) -> int:
    key = norm(snippet)
    hits = [p for p, t in PAGES.items() if key in norm(t)]
    if not hits:
        raise SystemExit(f"snippet not found in any page: {snippet!r}")
    return min(hits)


def slice_text(rule: str, start: str, end: str | None) -> str:
    text = RULES[rule]["text"]
    i = text.index(start)
    j = text.index(end, i) if end else len(text)
    return text[i:j].rstrip()


def strip_headers(text: str) -> str:
    return re.sub(r"\n{3,}", "\n\n", HEADER.sub("", text)).strip("\n")


def footnotes(text: str) -> list[str]:
    return [norm(m) for m in FOOTNOTE.findall(text)]


def citation(rule: str, sub_rule: str, start: str, end: str | None, expect_page: int, topics: list[str]) -> dict:
    rec = RULES[rule]
    sub = slice_text(rule, start, end)
    page = page_of(start)
    assert page == expect_page, f"{rule}{sub_rule}: found page {page}, expected {expect_page}"
    return {
        "_topics": topics,
        "rule": rule,
        "sub_rule": sub_rule,
        "title": rec["title"],
        "part": rec["part"],
        "page_start": rec["page_start"],
        "page_end": rec["page_end"],
        "text_en": rec["text"],
        "sub_rule_text_en": strip_headers(sub),
        "pdf_en_url": f"/pdf/en#page={page}",
        "pdf_hi_url": f"/pdf/hi#page={page}",
        "footnotes": footnotes(rec["text"]) if rule in ("61",) else footnotes(sub),
    }


C = {
    "56(1)(a)": citation("56", "(1)(a)", "(1) Front open spaces", "(b) In existing developed areas", 77, ["front_setback"]),
    "56(1)(b)": citation("56", "(1)(b)", "(b) In existing developed areas", "Rule 56                           M.P. Bhumi Vikas Rules, 2012                       78", 77, ["front_setback"]),
    "56(2)(a)": citation("56", "(2)(a)", "(2) Rear Open Space", "(b) Rear open space to extend", 78, ["rear_setback"]),
    "56(3)": citation("56", "(3)", "(3) Side open space", "(4) Notwithstanding", 78, ["side_setback"]),
    "53(1)(i)": citation("53", "(1)(i)", "53. Size of plots and other norms", "(ii) the norms of plot size", 70, ["side_setback"]),
    "42 Table 4": citation("42", " Table 4", "42. Additional provisions for buildings with height above 12.5 meters", "(2) For High Rise Buildings", 58, ["height_limit"]),
    "61 Table 8": citation("61", " Table 8", "61. Floor Area Ratio", "Note : (1)", 83, ["far"]),
    "21(2)": citation("21", "(2)", "(2) Application Fee", "(3) Permission Fee", 35, ["application_fee"]),
    "21(3)(b)": citation("21", "(3)(b)", "(b) In case of a building permission (other than high rise buildings)", "(c) In case of building permission of high rise", 36, ["permission_fee"]),
    "46": citation("46", "", "46. Building Line", None, 62, ["front_setback"]),
}
# Rule 46 is one sentence; keep only the rule itself, not the next rule's text.
C["46"]["sub_rule_text_en"] = C["46"]["sub_rule_text_en"].split("\n\n")[0]
C["46"].pop("sub_rule")

assert page_of('(20) "covered area or ground coverage"') == 5, "Rule 2(20) page"
assert page_of("(4) Notwithstanding anything contained in sub-rule (2) and (3) garage") == 78
assert page_of("58. Projections") == 81

VERSION_EN = {"consolidated_to": "2025-03-06", "label": "Derived from MP Bhumi Vikas Rules 2012, consolidated to 6 March 2025"}
VERSION_HI = {"consolidated_to": "2025-03-06", "label": "मध्यप्रदेश भूमि विकास नियम 2012 से, 6 मार्च 2025 तक समेकित प्रति के आधार पर"}
DISCLAIMER_EN = "This is a rule reference, not legal advice. The building-permission clerk decides."
DISCLAIMER_HI = "यह नियम का संदर्भ है, कानूनी सलाह नहीं। निर्णय भवन-अनुज्ञा लिपिक करते हैं।"
SOURCE = "https://teamleaseregtech.com/updates/article/59469/government-of-madhya-pradesh-amendment-to-land-development-rules"
AMEND_EN = {
    "date": "2026-08-28",
    "rule": "2(5)(c)",
    "concerns": "Whether separate development permission is needed for plots up to 500 sq m, subject to Development Plan conformity. It does not change the setback, height, FAR or fee figures shown.",
    "source_url": SOURCE,
    "source_kind": "secondary",
    "applied": False,
    "note": "Not applied in these figures. Gazette text is not in the corpus.",
}
AMEND_HI = dict(AMEND_EN, concerns="500 वर्ग मीटर तक के प्लॉट के लिए अलग विकास अनुज्ञा की आवश्यकता, विकास योजना के अनुरूप होने की शर्त पर। दिखाए गए सेटबैक, ऊँचाई, FAR या शुल्क के आंकड़े इससे नहीं बदलते।", note="इन आंकड़ों में लागू नहीं किया गया। राजपत्र का पाठ संग्रह में नहीं है।")


def fig(topic, label, value, unit, trace, rule, page, derived=False, conditional=False, cases=None, warning=None):
    f = {"topic": topic, "label": label, "value": value, "unit": unit, "derived": derived,
         "conditional": conditional, "trace": trace, "rule": rule, "page": page}
    if cases is not None:
        f["cases"] = cases
    if warning is not None:
        f["warning"] = warning
    return f


def base(lang="en"):
    return {
        "status": "answered",
        "figures": [],
        "citations": [],
        "version": VERSION_EN if lang == "en" else VERSION_HI,
        "amendment_flags": [AMEND_EN if lang == "en" else AMEND_HI],
        "disclaimer": DISCLAIMER_EN if lang == "en" else DISCLAIMER_HI,
        "language": lang,
        "used_inference": False,
    }


def write(name, obj):
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{name}.json").write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


# 1. Appendix A lookup, English
side_cases = [
    fig("side_setback", "Semi-detached: one side", 3.0, "m", "Rule 56(3)(ii): 3.0 m on one side for a semi-detached building", "56(3)(ii)", 78),
    fig("side_setback", "Semi-detached, height and frontage both up to 10 m: one side", 2.5, "m", "Rule 56(3)(ii) proviso: may be reduced to 2.5 m", "56(3)(ii)", 78),
    fig("side_setback", "Row type", 0.0, "m", "Rule 56(3)(iii): no side open space required", "56(3)(iii)", 78),
]
a = base("en")
a["figures"] = [
    fig("front_setback", "Front open space", 3.0, "m", "Road width 9.0 m; Rule 56(1)(a) table row 1, up to 9.0 m gives 3.0 m; p. 77", "56(1)(a)", 77),
    fig("rear_setback", "Rear open space", 2.5, "m", "Plot area 200 sq m; Rule 56(2)(a) table row 3, above 150 and up to 225.00 gives 2.50 m; p. 78", "56(2)(a)", 78),
    fig("side_setback", "Side open space", None, "m", "Development type not given. Rule 53(1)(i) permits semi-detached (125 to 225 sq m) and row type (50 to 225 sq m) for a 200 sq m plot.", "56(3)", 78, conditional=True, cases=side_cases),
    fig("height_limit", "Maximum height", 12.5, "m", "Road width 9.0 m is below the 12 m minimum of Rule 42 Table 4, so Rule 56 norms for buildings up to 12.5 m govern; p. 58", "42 Table 4", 58),
    fig("far", "Floor area ratio", 1.25, "", "Residential use; Rule 61 Table 8 row 1; p. 83", "61 Table 8", 83),
    fig("far", "Permitted floor area", 250.0, "sq m", "1.25 x 200 = 250 sq m, Rule 61 Table 8 row 1, p. 83", "61 Table 8", 83),
    fig("application_fee", "Application fee", 250.0, "Rs", "Rs 1.00 x 250 sq m built-up area = Rs 250, Rule 21(2)(ii), p. 35", "21(2)(ii)", 35),
    fig("permission_fee", "Permission fee", 3000.0, "Rs", "Built-up area 250 sq m falls in slab 201 to 300 sq m, Rule 21(3)(b) item 1, p. 36", "21(3)(b)", 36),
]
a["citations"] = [C[k] for k in ["56(1)(a)", "56(2)(a)", "56(3)", "53(1)(i)", "42 Table 4", "61 Table 8", "21(2)", "21(3)(b)"]]
write("lookup_appendix_a_en", a)

# 2. Appendix A lookup, Hindi (sample question 14: front open space only)
h = base("hi")
h["figures"] = [
    fig("front_setback", "सामने की न्यूनतम खुली जगह", 3.0, "m", "सड़क की चौड़ाई 9.0 मीटर; नियम 56(1)(a) तालिका पंक्ति 1, 9.0 मीटर तक पर 3.0 मीटर; पृष्ठ 77", "56(1)(a)", 77),
]
h["citations"] = [C["56(1)(a)"]]
write("lookup_appendix_a_hi", h)

# 5. Not found (sample question 16)
nf = base("en")
nf.update(status="not_found", message="Not found in MP Bhumi Vikas Rules 2012", amendment_flags=[])
write("lookup_not_found", nf)

# 8. Narrow street, existing developed area
ns = base("en")
ns["figures"] = [
    fig("front_setback", "Front open space", 3.5, "m", "Existing developed area, street 5.0 m wide: building line 6.0 m from the street centre line; 6.0 - 5.0 / 2 = 3.5 m from the plot boundary; Rule 56(1)(b) with Rule 46, p. 77", "56(1)(b)", 77),
]
ns["citations"] = [C["56(1)(b)"], C["46"]]
write("lookup_narrow_street", ns)

# 9. Development type out of Rule 53(1)(i) range
tw = base("en")
tw["figures"] = [
    fig("side_setback", "Side open space", 3.0, "m", "Semi-detached; frontage 14 m is above 10 m, so the Rule 56(3)(ii) reduction does not apply; 3.0 m on one side; p. 78", "56(3)(ii)", 78,
        warning="Rule 53(1)(i): a semi-detached building needs a plot of 125 to 225 sq m and frontage of 8 to 12 m. Frontage 14 m is outside that range."),
]
tw["citations"] = [C["56(3)"], C["53(1)(i)"]]
write("lookup_type_warning", tw)


# 3 and 4. Plan check, Appendix A.5 at height 10 and 10.5
def plan(height: float) -> dict:
    reduced = height <= 10
    left_req = 2.5 if reduced else 3.0
    front_req, rear_req, right_req = 3.0, 2.5, 0.0
    W, D = 10.0, 20.0
    fp = {"front": 2.4, "rear": 2.5, "left": 2.5, "right": 0.0}
    env_w = round(W - left_req - right_req, 2)
    env_d = round(D - front_req - rear_req, 2)
    fp_w = round(W - fp["left"] - fp["right"], 2)
    fp_d = round(D - fp["front"] - fp["rear"], 2)
    side_trace = (
        "Semi-detached, height 10.0 m and frontage 10 m are both up to 10 m: Rule 56(3)(ii) proviso reduces the side to 2.5 m; left side by convention; p. 78"
        if reduced else
        f"Semi-detached, height {height} m is above 10 m: Rule 56(3)(ii) proviso does not apply; 3.0 m on one side; left side by convention; p. 78"
    )
    req = {
        "front": {"value": front_req, "rule": "56(1)(a)", "sub_rule": "(1)(a)", "page": 77, "trace": "Road width 9.0 m, Rule 56(1)(a) row 1, up to 9.0 m gives 3.0 m, p. 77"},
        "rear": {"value": rear_req, "rule": "56(2)(a)", "sub_rule": "(2)(a)", "page": 78, "trace": "Plot area 200 sq m, Rule 56(2)(a) row 3, above 150 and up to 225.00 gives 2.50 m, p. 78"},
        "left": {"value": left_req, "rule": "56(3)(ii)", "sub_rule": "(3)(ii)", "page": 78, "trace": side_trace},
        "right": {"value": right_req, "rule": "56(3)(ii)", "sub_rule": "(3)(ii)", "page": 78, "trace": "Semi-detached: no open space on the shared side; right side by convention, p. 78"},
    }
    sides = []
    overlaps = []
    for s in ("front", "rear", "left", "right"):
        r = req[s]["value"]
        p = fp[s]
        short = round(max(0.0, r - p), 2)
        sides.append({"side": s, "required": r, "provided": p, "shortfall": short, "rule": req[s]["rule"], "page": req[s]["page"], "trace": req[s]["trace"]})
        if short > 0:
            if s == "front":
                overlaps.append({"side": s, "x": fp["left"], "y": fp["front"], "width": fp_w, "depth": short, "shortfall": short})
            elif s == "left":
                overlaps.append({"side": s, "x": fp["left"], "y": fp["front"], "width": short, "depth": fp_d, "shortfall": short})
    env_area = round(env_w * env_d, 2)
    conflict = bool(overlaps)
    out = base("en")
    out["figures"] = [
        fig("ground_coverage", "Ground coverage", round(env_area / 200 * 100, 1), "%", f"{env_area} / 200 = {round(env_area / 200 * 100, 1)} %, derived from setbacks, not a prescribed percentage; Rule 2(20), p. 5", "2(20)", 5, derived=True),
    ]
    out["citations"] = [C[k] for k in ["56(1)(a)", "56(2)(a)", "56(3)", "53(1)(i)"]]
    out["geometry"] = {
        "plot": {"width": W, "depth": D, "area": 200.0},
        "required": req,
        "envelope": {"x": left_req, "y": front_req, "width": env_w, "depth": env_d, "area": env_area},
        "footprint": {"x": fp["left"], "y": fp["front"], "width": fp_w, "depth": fp_d, "area": round(fp_w * fp_d, 2)},
        "sides": sides,
        "overlaps": overlaps,
        "result": "Setback conflict found" if conflict else "No setback conflict found against the checks listed",
        "result_kind": "conflict" if conflict else "clear",
        "checks_performed": [
            "Front open space, Rule 56(1)(a)",
            "Rear open space, Rule 56(2)(a)",
            "Side open space, left, Rule 56(3)(ii)",
            "Side open space, right, Rule 56(3)(ii)",
        ],
        "not_checked": "Parking, staircase, ventilation shaft, courtyard, fire and structural rules were not checked",
        "ground_coverage_derived": round(env_area / 200 * 100, 1),
        "exceptions_available": [
            {"id": "garage_side_rear", "label": "Garage at the rear end of the side open space", "rule": "56(4)", "page": 78},
            {"id": "projections", "label": "Projections governed by Rule 58", "rule": "58", "page": 81},
        ],
    }
    return out


write("plan_a5_h10", plan(10.0))
write("plan_a5_h10_5", plan(10.5))

# 6. Blocked: area mismatch
bl = base("en")
bl.update(status="blocked", message="Entered dimensions give 200.00 sq m; stated plot area is 230.00 sq m.", resolutions=["correct_inputs", "use_dimensions"], amendment_flags=[])
write("plan_blocked_area", bl)

# 7. Refused: corner plot
rf = base("en")
rf.update(status="refused", amendment_flags=[], message=(
    "Rule 56(1)(a) sets the front open space by \"the street facing the plot\", while Rule 65(2) says a plot on two or more streets is deemed to face the wider street for height.\n\n"
    "The Rules do not state which street sets the front open space on a corner plot. Reading one applies the wider street; reading two applies each street to its own frontage. The clerk decides; plan check is not drawn for this case."
))
write("plan_refused_corner", rf)

# Parse responses
write("parse_appendix_a_en", {"language": "en", "params": {"plot_area": 200, "road_width": 9, "use_type": "residential"}, "topics": ["front_setback", "height_limit", "permission_fee"], "used_inference": False})
write("parse_q14_hi", {"language": "hi", "params": {"plot_area": 200, "road_width": 9, "use_type": "residential"}, "topics": ["front_setback"], "used_inference": False})
write("parse_empty", {"language": "en", "params": {}, "topics": [], "used_inference": False})

print("fixtures written:", sorted(p.name for p in OUT.glob("*.json")))
