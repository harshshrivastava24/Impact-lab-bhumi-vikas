"""Plan check geometry (FR-40, FR-42, FR-43, FR-51). Pure functions, no I/O.

Coordinates: origin at the plot's front-left corner, x to the right along the road, y into the plot.
Arithmetic runs at full precision and is rounded to 0.01 only at the end (NFR-23).
"""

SIDES = ("front", "rear", "left", "right")


def r2(x: float) -> float:
    return round(x + 0.0, 2) + 0.0  # + 0.0 turns -0.0 into 0.0


def rect(x: float, y: float, width: float, depth: float) -> dict:
    return {"x": r2(x), "y": r2(y), "width": r2(width), "depth": r2(depth), "area": r2(width * depth)}


def footprint_error(frontage: float, depth: float, fp: dict) -> str | None:
    """Reason a footprint given as four boundary distances is invalid, or None (FR-42)."""
    for side in SIDES:
        if fp[side] < 0:
            return f"Footprint {side} distance {fp[side]} m is negative."
    width = frontage - fp["left"] - fp["right"]
    fdepth = depth - fp["front"] - fp["rear"]
    if r2(width) <= 0:
        return (
            f"Footprint width is {r2(width)} m (frontage {frontage} minus left {fp['left']} minus right "
            f"{fp['right']}); it must be above 0 and inside the plot."
        )
    if r2(fdepth) <= 0:
        return (
            f"Footprint depth is {r2(fdepth)} m (depth {depth} minus front {fp['front']} minus rear "
            f"{fp['rear']}); it must be above 0 and inside the plot."
        )
    return None


def envelope(frontage: float, depth: float, req: dict) -> dict:
    """Buildable envelope from the four required distances (values in metres)."""
    width = max(0.0, frontage - req["left"] - req["right"])
    edepth = max(0.0, depth - req["front"] - req["rear"])
    return rect(req["left"], req["front"], width, edepth)


def footprint(frontage: float, depth: float, fp: dict) -> dict:
    return rect(fp["left"], fp["front"], frontage - fp["left"] - fp["right"], depth - fp["front"] - fp["rear"])


def shortfalls(req: dict, fp: dict) -> dict:
    return {s: r2(max(0.0, req[s] - fp[s])) for s in SIDES}


def overlaps(frontage: float, depth: float, req: dict, fp: dict) -> list[dict]:
    """One rectangle per side with a shortfall above 0, inside the footprint (FR-43)."""
    f = footprint(frontage, depth, fp)
    short = shortfalls(req, fp)
    out = []
    for s in SIDES:
        sf = short[s]
        if sf <= 0:
            continue
        if s == "front":
            x, y, w, d = f["x"], f["y"], f["width"], sf
        elif s == "rear":
            x, y, w, d = f["x"], depth - req["rear"], f["width"], sf
        elif s == "left":
            x, y, w, d = f["x"], f["y"], sf, f["depth"]
        else:
            x, y, w, d = frontage - req["right"], f["y"], sf, f["depth"]
        out.append({"side": s, "x": r2(x), "y": r2(y), "width": r2(w), "depth": r2(d), "shortfall": sf})
    return out


def ground_coverage(envelope_area: float, plot_area: float) -> float:
    """Derived ground coverage, one decimal (FR-51)."""
    return round(envelope_area / plot_area * 100, 1)
