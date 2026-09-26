"""Model space <-> real units.

Models are trained on log10(x + 1) for everything except LogD, so pegs have to be
converted back before they are compared with a socket in real units.
"""

import math

LOG_ENDPOINTS = frozenset({"KSOL", "HLM", "MLM", "Papp", "Efflux", "MPPB", "MBPB", "MGMB"})


def to_real(endpoint: str, value: float) -> float:
    if endpoint not in LOG_ENDPOINTS:
        return value
    return 10.0**value - 1.0


def to_model(endpoint: str, value: float) -> float:
    if endpoint not in LOG_ENDPOINTS:
        return value
    if value < 0:
        raise ValueError(f"{endpoint} cannot be negative in real units")
    return math.log10(value + 1.0)


def format_value(endpoint: str, value: float, unit: str) -> str:
    """Short human-readable label for a peg."""
    if endpoint == "LogD":
        return f"{value:.1f}"
    if endpoint in {"KSOL", "HLM", "MLM"}:
        return f"{value:,.0f} {unit}".strip()
    return f"{value:.1f} {unit}".strip()
