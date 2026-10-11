import pytest

from backend.app.services import geometry as g

A5_REQ = {"front": 3.0, "rear": 2.5, "left": 2.5, "right": 0.0}
A5_FP = {"front": 2.4, "rear": 2.5, "left": 2.5, "right": 0.0}


def test_a5_envelope():
    assert g.envelope(10, 20, A5_REQ) == {"x": 2.5, "y": 3.0, "width": 7.5, "depth": 14.5, "area": 108.75}


def test_a5_footprint():
    assert g.footprint(10, 20, A5_FP) == {"x": 2.5, "y": 2.4, "width": 7.5, "depth": 15.1, "area": 113.25}


def test_a5_shortfall_and_overlap():
    assert g.shortfalls(A5_REQ, A5_FP) == {"front": 0.6, "rear": 0.0, "left": 0.0, "right": 0.0}
    assert g.overlaps(10, 20, A5_REQ, A5_FP) == [
        {"side": "front", "x": 2.5, "y": 2.4, "width": 7.5, "depth": 0.6, "shortfall": 0.6}
    ]


def test_ground_coverage():
    assert g.ground_coverage(108.75, 200) == 54.4


@pytest.mark.parametrize(
    "fp, expected",
    [
        ({"front": 3.0, "rear": 2.0, "left": 2.5, "right": 0}, {"side": "rear", "x": 2.5, "y": 17.5, "width": 7.5, "depth": 0.5}),
        ({"front": 3.0, "rear": 2.5, "left": 2.0, "right": 0}, {"side": "left", "x": 2.0, "y": 3.0, "width": 0.5, "depth": 14.5}),
    ],
)
def test_single_side_overlaps(fp, expected):
    (lap,) = g.overlaps(10, 20, A5_REQ, fp)
    assert {k: lap[k] for k in expected} == expected


def test_right_overlap_detached():
    req = {"front": 3.0, "rear": 3.0, "left": 3.0, "right": 3.0}
    fp = {"front": 3.0, "rear": 3.0, "left": 3.0, "right": 2.0}
    (lap,) = g.overlaps(15, 20, req, fp)
    assert lap == {"side": "right", "x": 12.0, "y": 3.0, "width": 1.0, "depth": 14.0, "shortfall": 1.0}


def test_no_overlap_when_on_the_line():
    assert g.overlaps(10, 20, A5_REQ, {"front": 3.0, "rear": 2.5, "left": 2.5, "right": 0}) == []


def test_float_noise_is_not_a_shortfall():
    # 0.1 + 0.2 style noise must not create a 0.00 m overlap
    assert g.shortfalls({"front": 0.3, "rear": 0, "left": 0, "right": 0},
                        {"front": 0.1 + 0.2, "rear": 0, "left": 0, "right": 0})["front"] == 0.0


@pytest.mark.parametrize(
    "fp",
    [
        {"front": 10, "rear": 10, "left": 2.5, "right": 0},
        {"front": 3, "rear": 2.5, "left": 11, "right": 0},
        {"front": 3, "rear": 2.5, "left": 5, "right": 5},
        {"front": -1, "rear": 2.5, "left": 2.5, "right": 0},
    ],
)
def test_invalid_footprints(fp):
    assert g.footprint_error(10, 20, fp)


def test_valid_footprint():
    assert g.footprint_error(10, 20, A5_FP) is None
