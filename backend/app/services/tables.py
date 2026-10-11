"""Range-table lookup (FR-13). Boundaries follow the rule wording exactly."""


def in_range(x: float, lower, upper, lower_inclusive: bool, upper_inclusive: bool) -> bool:
    if lower is not None and (x < lower or (x == lower and not lower_inclusive)):
        return False
    if upper is not None and (x > upper or (x == upper and not upper_inclusive)):
        return False
    return True


def lookup(table: dict, x: float) -> tuple[int, dict]:
    """Return (1-based row number, row) for the row containing x."""
    for i, row in enumerate(table["rows"], start=1):
        if in_range(x, row["lower"], row["upper"], row["lower_inclusive"], row["upper_inclusive"]):
            return i, row
    raise ValueError(f"{x} outside every row of table {table['id']}")
