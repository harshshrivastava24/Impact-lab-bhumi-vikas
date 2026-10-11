import copy
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services import compute

client = TestClient(app)

A5 = {
    "params": {"plot_area": 200, "road_width": 9.0, "use_type": "residential", "frontage": 10, "depth": 20,
               "development_type": "semi_detached", "height": 10.0},
    "footprint": {"front": 2.4, "rear": 2.5, "left": 2.5, "right": 0},
    "language": "en",
}
PROHIBITED = ("approved", "compliant", "sanctionable")


def post(params=None, footprint=None, **extra):
    body = copy.deepcopy(A5)
    body["params"].update(params or {})
    if footprint:
        body["footprint"] = footprint
    body.update(extra)
    return client.post("/api/plan-check", json=body)


def side(r, name):
    return next(s for s in r.json()["geometry"]["sides"] if s["side"] == name)


def strings_in(obj):
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for k, v in obj.items():
            if k != "text_en":  # verbatim rule text is reproduced unchanged (FR-29)
                yield from strings_in(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from strings_in(v)


def test_a5_acceptance():
    r = post()
    assert r.status_code == 200
    body = r.json()
    g = body["geometry"]
    assert body["status"] == "answered"
    assert g["envelope"]["area"] == 108.75
    assert g["footprint"]["area"] == 113.25
    assert g["ground_coverage_derived"] == 54.4
    assert g["result"] == "Setback conflict found"
    front = side(r, "front")
    assert (front["shortfall"], front["rule"], front["page"]) == (0.6, "56(1)(a)", 77)
    assert front["trace"] == "road width 9.0 m, Rule 56(1)(a) row 1, up to 9.0 m gives 3.0 m, p. 77"
    assert g["not_checked"] == "Parking, staircase, ventilation shaft, courtyard, fire and structural rules were not checked"
    assert len(g["checks_performed"]) == 4
    assert body["disclaimer"] == "This is a rule reference, not legal advice. The building-permission clerk decides."
    gc = next(f for f in body["figures"] if f["topic"] == "ground_coverage")
    assert gc["derived"] and "not a prescribed percentage" in gc["trace"] and "Rule 2(20)" in gc["trace"]


def test_amendment_flag_on_small_plot():
    (flag,) = post().json()["amendment_flags"]
    assert flag["source_kind"] == "secondary" and flag["applied"] is False


def test_no_conflict_wording():
    r = post(footprint={"front": 3.0, "rear": 2.5, "left": 2.5, "right": 0})
    assert r.json()["geometry"]["result"] == "No setback conflict found against the checks listed"
    assert r.json()["geometry"]["overlaps"] == []


@pytest.mark.parametrize("fp", [None, {"front": 3.0, "rear": 2.5, "left": 2.5, "right": 0}])
@pytest.mark.parametrize("language", ["en", "hi"])
def test_no_prohibited_words(fp, language):
    body = post(footprint=fp, language=language).json()
    for s in strings_in(body):
        assert not any(w in s.lower() for w in PROHIBITED), s


def test_prohibited_words_absent_from_refusals():
    for params in ({"streets_abutting": 2}, {"use_type": "commercial"}, {"height": 13}):
        for s in strings_in(post(params).json()):
            assert not any(w in s.lower() for w in PROHIBITED)


@pytest.mark.parametrize("road, expected", [(9.0, 3.0), (9.1, 3.6), (12.0, 3.6), (12.1, 4.5), (18.0, 4.5), (18.1, 6.0)])
def test_front_thresholds(road, expected):
    assert side(post({"road_width": road}), "front")["required"] == expected


@pytest.mark.parametrize("area, expected", [(40, 0.0), (41, 1.5), (150, 1.5), (151, 2.5), (225, 2.5), (226, 3.0)])
def test_rear_thresholds(area, expected):
    assert compute.rear(area)["value"] == expected


def test_semi_detached_height_coupling():
    low = post({"height": 10.0}).json()["geometry"]["required"]["left"]
    high = post({"height": 10.1}).json()["geometry"]["required"]["left"]
    assert (low["value"], high["value"]) == (2.5, 3.0)
    assert "proviso applied" in low["trace"] and "proviso not applied" in high["trace"]


def test_detached_height_coupling():
    left, right = compute.sides("detached", 11, 7.0)
    assert (left["value"], right["value"]) == (1.5, 3.0)
    left, right = compute.sides("detached", 11, 7.1)
    assert (left["value"], right["value"]) == (3.0, 3.0)
    left, _ = compute.sides("detached", 12, 7.0)  # frontage must be under 12
    assert left["value"] == 3.0


def test_row_has_no_side_space():
    left, right = compute.sides("row", 6, 9)
    assert left["value"] == right["value"] == 0.0


def test_narrow_street_existing_developed_area():
    r = post({"road_width": 5.0, "existing_developed_area": True})
    front = side(r, "front")
    assert front["required"] == 3.5 and front["rule"] == "56(1)(b)" and "Rule 46" in front["trace"]


def test_narrow_street_not_developed_area():
    front = side(post({"road_width": 5.0, "existing_developed_area": False}), "front")
    assert front["required"] == 3.0 and "56(1)(b) considered and not applied" in front["trace"]


def test_narrow_street_needs_the_flag():
    r = post({"road_width": 5.0})
    assert r.status_code == 422 and r.json()["field"] == "params.existing_developed_area"


def test_area_mismatch_blocked():
    body = post({"plot_area": 230}).json()
    assert body["status"] == "blocked"
    assert body["message"] == "Entered dimensions give 200 sq m; stated plot area is 230 sq m"
    assert body["resolutions"] == ["correct_inputs", "use_dimensions"]
    assert body["geometry"] is None


def test_area_within_tolerance_proceeds():
    assert post({"plot_area": 204}).json()["status"] == "answered"


def test_use_dimensions_resolution():
    body = post({"plot_area": 230}, resolution="use_dimensions").json()
    assert body["status"] == "answered"
    assert body["geometry"]["plot"]["area"] == 200
    assert "230" not in side_trace(body, "rear")
    assert "by clerk resolution" in side_trace(body, "rear")
    gc = next(f for f in body["figures"] if f["topic"] == "ground_coverage")
    assert gc["value"] == 54.4 and "by clerk resolution" in gc["trace"]


def side_trace(body, name):
    return next(s for s in body["geometry"]["sides"] if s["side"] == name)["trace"]


def test_corner_plot_refused():
    body = post({"streets_abutting": 2}).json()
    assert body["status"] == "refused" and body["geometry"] is None
    msg = body["message"]
    assert "the street facing the plot" in msg and "Rule 56(1)(a)" in msg and "Rule 65(2)" in msg
    assert len(msg.split("\n\n")) == 2


def test_non_residential_refused():
    body = post({"use_type": "commercial"}).json()
    assert body["message"] == "Plan check version 1 supports residential buildings only; see Rule 57 for other occupancies."


def test_height_above_limit_refused():
    body = post({"height": 12.6}).json()
    assert body["message"] == "Plan check version 1 supports buildings up to 12.5 m; Rule 42 Tables 4 and 5 govern above that."
    assert post({"height": 12.5}).json()["status"] == "answered"


@pytest.mark.parametrize(
    "fp",
    [{"front": 10, "rear": 10, "left": 2.5, "right": 0}, {"front": 2.4, "rear": 2.5, "left": 11, "right": 0},
     {"front": -0.5, "rear": 2.5, "left": 2.5, "right": 0}],
)
def test_impossible_footprint_422(fp):
    r = post(footprint=fp)
    assert r.status_code == 422 and r.json()["field"] == "footprint"


@pytest.mark.parametrize("field", ["frontage", "depth", "development_type", "height", "plot_area"])
def test_missing_mandatory_field(field):
    body = copy.deepcopy(A5)
    del body["params"][field]
    r = client.post("/api/plan-check", json=body)
    assert r.status_code == 422 and field in r.json()["detail"]


def test_missing_footprint_side():
    r = post(footprint={"front": 2.4, "rear": 2.5, "left": 2.5})
    assert r.status_code == 422 and r.json()["field"] == "footprint.right"


def test_dev_type_out_of_range_warns():
    body = post({"frontage": 14, "depth": 14.29}, footprint={"front": 3, "rear": 2.5, "left": 3, "right": 0}).json()
    (w,) = [f for f in body["figures"] if f.get("warning")]
    assert w["rule"] == "53" and w["page"] == 70 and "frontage 14.0 m" in w["trace"]
    assert body["status"] == "answered"


def test_a5_dev_type_has_no_warning():
    assert not [f for f in post().json()["figures"] if f.get("warning")]


def test_exceptions_available_and_overlap_kept():
    g = post().json()["geometry"]
    assert {e["id"] for e in g["exceptions_available"]} == {"garage_side_rear", "projections"}
    assert {e["rule"] for e in g["exceptions_available"]} == {"56(4)", "58"}
    assert g["overlaps"]


def test_hindi_labels_and_english_traces():
    body = post(language="hi").json()
    g = body["geometry"]
    assert body["language"] == "hi"
    assert g["result"] == "सेटबैक में विरोध पाया गया"
    assert g["not_checked"].startswith("पार्किंग")
    assert body["figures"][0]["label"] == "सामने का खुला स्थान"
    # rule references and traces stay English, numbers stay Western digits
    assert side(post(language="hi"), "front")["trace"] == "road width 9.0 m, Rule 56(1)(a) row 1, up to 9.0 m gives 3.0 m, p. 77"
    assert "trace_hi" not in body  # inference not configured


def test_audit_log_has_geometry_and_no_free_text(log_to_tmp):
    post(text="free text the clerk typed")
    (entry,) = [json.loads(line) for line in Path(log_to_tmp).read_text(encoding="utf-8").splitlines()]
    assert entry["geometry_inputs"]["footprint"] == {"front": 2.4, "rear": 2.5, "left": 2.5, "right": 0.0}
    assert [s["shortfall"] for s in entry["sides"]] == [0.6, 0.0, 0.0, 0.0]
    assert "free text" not in json.dumps(entry, ensure_ascii=False)


def test_health():
    body = client.get("/api/health").json()
    assert body["ok"] is True and body["version"] == "2025-03-06"
