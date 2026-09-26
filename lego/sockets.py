"""Sockets: the property window a molecule has to fit, and whether a peg fits it.

A socket is one endpoint's acceptable range in *real units*, plus a direction so
the UI can say which way is better. Presets describe what different projects need:
an oral drug and a brain drug do not want the same molecule.

Thresholds are conventional medicinal-chemistry rules of thumb, not fitted values,
and the notebook says so wherever they appear.
"""

from dataclasses import dataclass
from typing import Literal

Direction = Literal["higher", "lower", "window"]

# Endpoint -> (unit, direction, plain-language meaning)
META: dict[str, tuple[str, Direction, str]] = {
    "LogD": ("", "window", "greasiness: too low can't cross membranes, too high won't dissolve"),
    "KSOL": ("uM", "higher", "how much dissolves in water"),
    "HLM": ("mL/min/kg", "lower", "how fast a human liver destroys it"),
    "MLM": ("mL/min/kg", "lower", "how fast a mouse liver destroys it"),
    "Papp": ("1e-6 cm/s", "higher", "how fast it crosses the gut wall"),
    "Efflux": ("ratio", "lower", "how hard cells pump it back out"),
    "MPPB": ("% unbound", "higher", "fraction free in blood, able to act"),
    "MBPB": ("% unbound", "higher", "fraction free in brain tissue"),
    "MGMB": ("% unbound", "higher", "fraction free in muscle tissue"),
}


@dataclass(frozen=True)
class Socket:
    """One endpoint's acceptable range. `lo`/`hi` are inclusive; None means open."""

    endpoint: str
    lo: float | None = None
    hi: float | None = None

    def accepts(self, value: float) -> bool:
        if self.lo is not None and value < self.lo:
            return False
        if self.hi is not None and value > self.hi:
            return False
        return True

    def verdict(self, value: float) -> Literal["fits", "too_low", "too_high"]:
        if self.lo is not None and value < self.lo:
            return "too_low"
        if self.hi is not None and value > self.hi:
            return "too_high"
        return "fits"


# Each preset names only the endpoints that project actually cares about.
# Endpoints left out are drawn as "not required" rather than as a pass.
PRESETS: dict[str, dict[str, Socket]] = {
    "Oral drug": {
        "LogD": Socket("LogD", 1.0, 3.0),
        "KSOL": Socket("KSOL", lo=50.0),
        "HLM": Socket("HLM", hi=20.0),
        "Papp": Socket("Papp", lo=5.0),
        "Efflux": Socket("Efflux", hi=2.5),
        "MPPB": Socket("MPPB", lo=1.0),
    },
    "Brain drug": {
        "LogD": Socket("LogD", 1.5, 3.5),
        "KSOL": Socket("KSOL", lo=50.0),
        "HLM": Socket("HLM", hi=20.0),
        "Papp": Socket("Papp", lo=5.0),
        # The blood-brain barrier is dense with efflux pumps, so this is strict.
        "Efflux": Socket("Efflux", hi=2.0),
        "MBPB": Socket("MBPB", lo=1.0),
    },
    "Muscle drug": {
        "LogD": Socket("LogD", 1.0, 3.0),
        "KSOL": Socket("KSOL", lo=50.0),
        "MLM": Socket("MLM", hi=100.0),
        "Papp": Socket("Papp", lo=5.0),
        "MGMB": Socket("MGMB", lo=1.0),
    },
    "Everything at once": {
        "LogD": Socket("LogD", 1.0, 3.0),
        "KSOL": Socket("KSOL", lo=50.0),
        "HLM": Socket("HLM", hi=20.0),
        "MLM": Socket("MLM", hi=100.0),
        "Papp": Socket("Papp", lo=5.0),
        "Efflux": Socket("Efflux", hi=2.0),
        "MPPB": Socket("MPPB", lo=1.0),
        "MBPB": Socket("MBPB", lo=1.0),
        "MGMB": Socket("MGMB", lo=1.0),
    },
}


def fit_report(
    sockets: dict[str, Socket], values: dict[str, float | None]
) -> dict[str, dict]:
    """Per-socket verdict. A value of None means 'no prediction', not a pass."""
    out = {}
    for ep, socket in sockets.items():
        v = values.get(ep)
        out[ep] = {
            "value": v,
            "verdict": "unknown" if v is None else socket.verdict(v),
            "lo": socket.lo,
            "hi": socket.hi,
            "unit": META[ep][0],
        }
    return out


def clicks(report: dict[str, dict]) -> bool:
    """True only if every required socket is satisfied by a known value."""
    return bool(report) and all(r["verdict"] == "fits" for r in report.values())
