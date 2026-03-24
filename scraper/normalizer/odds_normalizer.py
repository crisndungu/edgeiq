"""Convert any odds format to decimal."""


def american_to_decimal(american: int) -> float:
    if american > 0:
        return round(american / 100 + 1, 4)
    return round(100 / abs(american) + 1, 4)


def fractional_to_decimal(numerator: int, denominator: int) -> float:
    return round(numerator / denominator + 1, 4)


def normalize(odds: float | int | str, fmt: str = "decimal") -> float:
    """
    fmt options: 'decimal', 'american', 'fractional'
    fractional string format: '5/2'
    """
    if fmt == "decimal":
        return round(float(odds), 4)
    if fmt == "american":
        return american_to_decimal(int(odds))
    if fmt == "fractional":
        num, den = str(odds).split("/")
        return fractional_to_decimal(int(num), int(den))
    raise ValueError(f"Unknown odds format: {fmt}")


def implied_probability(decimal_odds: float) -> float:
    """Raw implied probability (includes bookmaker margin)."""
    return round(1 / decimal_odds, 6)
