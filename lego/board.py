"""Render the socket-and-peg board as inline SVG.

Form: one horizontal track per endpoint, each showing an acceptable range (the
socket) and a predicted value (the peg) -- the bullet-chart family, dressed as
Lego. Nine labelled rows read better stacked horizontally than as vertical bars.

Colour: fit/fail is a *state*, so it uses the fixed status palette, never the
categorical one. Every verdict also carries a glyph and a word, so colour is never
the only channel -- required for the status palette and for colour-blind readers.

Scales: positions are computed in model space (log10(x+1) for every endpoint
except LogD), which is both the models' space and the right visual space for
quantities spanning orders of magnitude. Axis bounds come from the dataset's
0.5/99.5 percentiles, rounded outward.

Stage 1 of the widget: pure Python, no JS. Hover text ships as SVG <title>, which
browsers render as a native tooltip.
"""

from dataclasses import dataclass

from lego.sockets import META, Socket
from lego.units import format_value, to_model

# Axis bounds in REAL units, from data percentiles rounded outward.
AXIS: dict[str, tuple[float, float]] = {
    "LogD": (-1.5, 5.0),
    "KSOL": (0.0, 350.0),
    "HLM": (0.0, 1000.0),
    "MLM": (0.0, 7000.0),
    "Papp": (0.0, 50.0),
    "Efflux": (0.0, 200.0),
    "MPPB": (0.0, 100.0),
    "MBPB": (0.0, 100.0),
    "MGMB": (0.0, 100.0),
}

# Layout, in px.
W = 830
LABEL_W = 128
TRACK_X0 = 142
TRACK_X1 = 556
VALUE_X = 664  # right edge of the value column
VERDICT_X = 676
ROW_H = 36
BAR_H = 12
PAD_TOP = 22
PAD_BOTTOM = 54

# Five states, not three: an endpoint with no socket was still predicted, and
# saying "no data" there would be false.
WORD = {
    "fits": "fits", "too_low": "too low", "too_high": "too high",
    "not_required": "not required", "unknown": "not predicted",
}
# Marks are drawn, not typed: a glyph font may lack the character, and a missing
# check mark would leave colour carrying the verdict alone.
MARK = {
    "fits": '<polyline points="0,3 2.6,5.8 7,0.4" class="mk mk-fit"/>',
    "too_high": '<polyline points="0,5 3.4,0.6 6.8,5" class="mk mk-miss"/>',
    "too_low": '<polyline points="0,1 3.4,5.4 6.8,1" class="mk mk-miss"/>',
    "not_required": '<circle cx="3.4" cy="3.2" r="1.6" class="mk-dot"/>',
    "unknown": '<circle cx="3.4" cy="3.2" r="2.4" class="mk mk-dim"/>',
}

# Status palette (fixed, never themed) + ink/chrome tokens, light and dark.
TOKENS_LIGHT = {
    "surface": "#fcfcfb", "ink": "#0b0b0b", "ink2": "#52514e", "muted": "#898781",
    "grid": "#e1e0d9", "axis": "#c3c2b7", "good": "#0ca30c", "critical": "#d03b3b",
    "socket": "rgba(11,11,11,0.07)", "peg_unknown": "#898781",
}
TOKENS_DARK = {
    "surface": "#1a1a19", "ink": "#ffffff", "ink2": "#c3c2b7", "muted": "#898781",
    "grid": "#2c2c2a", "axis": "#383835", "good": "#0ca30c", "critical": "#d03b3b",
    "socket": "rgba(255,255,255,0.09)", "peg_unknown": "#898781",
}


@dataclass(frozen=True)
class Peg:
    """One endpoint's prediction. `sd` is ensemble spread; `measured` the ghost."""

    endpoint: str
    value: float | None  # real units, predicted
    sd: float | None = None  # model-space SD from the ensemble
    measured: float | None = None  # real units, experimental


def clamp(endpoint: str, real: float) -> float:
    """Hold a value inside its axis.

    A regression head can return log10(x+1) < 0, i.e. a negative concentration or
    permeability. That is physically meaningless and cannot be converted back, so
    it is clamped to the axis rather than allowed to raise or to print as "-0.3 uM".
    """
    lo, hi = AXIS[endpoint]
    return min(max(real, lo), hi)


def _pos(endpoint: str, real: float) -> float:
    """Real value -> x pixel, clamped to the track."""
    lo, hi = AXIS[endpoint]
    a, b = to_model(endpoint, lo), to_model(endpoint, hi)
    m = to_model(endpoint, clamp(endpoint, real))
    frac = 0.0 if b == a else (m - a) / (b - a)
    return TRACK_X0 + frac * (TRACK_X1 - TRACK_X0)


def _esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _row(y: int, socket: Socket | None, peg: Peg, verdict: str) -> list[str]:
    ep = peg.endpoint
    unit, _, meaning = META[ep]
    out: list[str] = []
    mid = y + ROW_H // 2
    bar_y = mid - BAR_H // 2

    # Name, and under it what this project asks for. Keeping the requirement in
    # the label column avoids colliding with a narrow band or the peg.
    out.append(
        f'<text x="{LABEL_W}" y="{mid - 1}" text-anchor="end" class="lbl">{_esc(ep)}</text>'
    )
    if socket is not None:
        out.append(
            f'<text x="{LABEL_W}" y="{mid + 11}" text-anchor="end" class="req">'
            f"{_esc(_range_label(ep, socket, unit))}</text>"
        )

    # The socket: the acceptable window. An open side runs to the track edge.
    if socket is not None:
        x0 = _pos(ep, socket.lo) if socket.lo is not None else TRACK_X0
        x1 = _pos(ep, socket.hi) if socket.hi is not None else TRACK_X1
        out.append(
            f'<rect x="{x0:.1f}" y="{y + 4}" width="{max(x1 - x0, 1):.1f}" '
            f'height="{ROW_H - 10}" rx="3" class="socket"/>'
        )
        for x in (x0, x1):
            out.append(
                f'<line x1="{x:.1f}" y1="{y + 4}" x2="{x:.1f}" y2="{y + ROW_H - 6}" '
                f'class="socket-edge"/>'
            )
    else:
        out.append(
            f'<rect x="{TRACK_X0}" y="{y + 4}" width="{TRACK_X1 - TRACK_X0}" '
            f'height="{ROW_H - 10}" rx="3" class="socket-off"/>'
        )

    # The peg: a bar from the axis start to the predicted value, rounded data-end.
    if peg.value is None:
        out.append(
            f'<text x="{TRACK_X0}" y="{mid + 4}" class="nodata">not predicted</text>'
        )
    else:
        x = _pos(ep, peg.value)
        # A "not required" endpoint was still predicted: it is neither pass nor
        # fail, so it must not wear a status colour.
        cls = {"fits": "peg-fit", "not_required": "peg-idle", "unknown": "peg-idle"}.get(
            verdict, "peg-miss"
        )
        out.append(
            f'<path d="{_bar_path(TRACK_X0, bar_y, x - TRACK_X0, BAR_H)}" class="{cls}"/>'
        )
        # Uncertainty: +/-1 ensemble SD in model space, drawn over the peg end so
        # it reads as a fuzzy tip rather than a second, detached mark.
        if peg.sd:
            m = to_model(ep, clamp(ep, peg.value))
            lo_x = _pos(ep, _inv(ep, m - peg.sd))
            hi_x = _pos(ep, _inv(ep, m + peg.sd))
            out.append(
                f'<rect x="{lo_x:.1f}" y="{bar_y}" width="{max(hi_x - lo_x, 2):.1f}" '
                f'height="{BAR_H}" rx="2" class="unc"/>'
            )
        tip = (
            f"{ep}: predicted {format_value(ep, clamp(ep, peg.value), unit)}"
            + (f", measured {format_value(ep, peg.measured, unit)}" if peg.measured is not None else "")
            + f" -- {meaning}"
        )
        out.append(f"<title>{_esc(tip)}</title>")

    # The ghost: the experimental value, so peg-to-ghost distance is the error.
    if peg.measured is not None:
        gx = _pos(ep, peg.measured)
        out.append(
            f'<line x1="{gx:.1f}" y1="{bar_y - 3}" x2="{gx:.1f}" y2="{bar_y + BAR_H + 3}" '
            f'class="ghost"/>'
        )

    # The number itself: a bullet track shows position, not magnitude.
    if peg.value is not None:
        out.append(
            f'<text x="{VALUE_X}" y="{mid + 4}" text-anchor="end" class="val">'
            f"{_esc(format_value(ep, clamp(ep, peg.value), unit))}</text>"
        )

    # Verdict: drawn mark + word, so colour never carries the meaning alone.
    vcls = {
        "fits": "v-fit", "unknown": "v-unknown", "not_required": "v-unknown",
    }.get(verdict, "v-miss")
    out.append(f'<g transform="translate({VERDICT_X},{mid - 3})">{MARK[verdict]}</g>')
    out.append(
        f'<text x="{VERDICT_X + 14}" y="{mid + 4}" class="{vcls}">{WORD[verdict]}</text>'
    )
    return out


def _range_label(endpoint: str, socket: Socket, unit: str) -> str:
    lo, hi = socket.lo, socket.hi
    if lo is not None and hi is not None:
        return f"{format_value(endpoint, lo, '')}-{format_value(endpoint, hi, unit)}"
    if lo is not None:
        return f"min {format_value(endpoint, lo, unit)}"
    if hi is not None:
        return f"max {format_value(endpoint, hi, unit)}"
    return ""


def _inv(endpoint: str, model_value: float) -> float:
    from lego.units import to_real

    return to_real(endpoint, model_value)


def _bar_path(x: float, y: float, w: float, h: float, r: float = 4.0) -> str:
    """Bar with only the data-end rounded, anchored to the baseline."""
    w = max(w, 1.0)
    r = min(r, w, h / 2)
    return (
        f"M{x:.1f},{y:.1f} H{x + w - r:.1f} Q{x + w:.1f},{y:.1f} {x + w:.1f},{y + r:.1f} "
        f"V{y + h - r:.1f} Q{x + w:.1f},{y + h:.1f} {x + w - r:.1f},{y + h:.1f} "
        f"H{x:.1f} Z"
    )


def _css() -> str:
    def block(t: dict[str, str]) -> str:
        return "".join(f"--{k}:{v};" for k, v in t.items())

    return f"""
.lego-board {{ color-scheme: light; {block(TOKENS_LIGHT)}
  background: var(--surface); font: 12px system-ui, -apple-system, "Segoe UI", sans-serif; }}
@media (prefers-color-scheme: dark) {{
  :root:where(:not([data-theme="light"])) .lego-board {{ color-scheme: dark; {block(TOKENS_DARK)} }}
}}
:root[data-theme="dark"] .lego-board {{ color-scheme: dark; {block(TOKENS_DARK)} }}
.lego-board text {{ font: 12px system-ui, -apple-system, "Segoe UI", sans-serif; }}
.lego-board .lbl {{ fill: var(--ink2); }}
.lego-board .socket {{ fill: var(--socket); }}
.lego-board .socket-off {{ fill: none; stroke: var(--grid); stroke-dasharray: 2 4; }}
.lego-board .socket-edge {{ stroke: var(--axis); stroke-width: 2; }}
.lego-board .peg-fit {{ fill: var(--good); stroke: var(--surface); stroke-width: 2; }}
.lego-board .peg-miss {{ fill: var(--critical); stroke: var(--surface); stroke-width: 2; }}
.lego-board .unc {{ fill: var(--ink2); opacity: 0.35; }}
.lego-board .ghost {{ stroke: var(--ink); stroke-width: 2.5; stroke-dasharray: 4 2; }}
.lego-board .nodata, .lego-board .v-unknown {{ fill: var(--muted); }}
.lego-board .req {{ fill: var(--muted); font-size: 10px; }}
.lego-board .peg-idle {{ fill: var(--peg_unknown); stroke: var(--surface); stroke-width: 2; opacity: .55; }}
.lego-board .cap-strong {{ fill: var(--ink2); font-weight: 600; }}
.lego-board .mk {{ fill: none; stroke-width: 2; stroke-linecap: round; stroke-linejoin: round; }}
.lego-board .mk-fit {{ stroke: var(--good); }}
.lego-board .mk-miss {{ stroke: var(--critical); }}
.lego-board .mk-dim {{ stroke: var(--muted); }}
.lego-board .mk-dot {{ fill: var(--muted); }}
.lego-board .val {{ fill: var(--ink); font-variant-numeric: tabular-nums; }}
.lego-board .v-fit {{ fill: var(--good); }}
.lego-board .v-miss {{ fill: var(--critical); }}
.lego-board .axis {{ stroke: var(--axis); stroke-width: 1; }}
.lego-board .cap {{ fill: var(--muted); }}
"""


def render(
    sockets: dict[str, Socket],
    pegs: list[Peg],
    caption: str | None = None,
) -> str:
    """SVG for one molecule against one project preset.

    Endpoints absent from `sockets` are drawn as not-required rather than as a pass.
    """
    from lego.sockets import fit_report

    values = {p.endpoint: p.value for p in pegs}
    report = fit_report(sockets, values)
    height = PAD_TOP + ROW_H * len(pegs) + PAD_BOTTOM

    def verdict_for(peg: Peg) -> str:
        if peg.endpoint not in sockets:
            # Predicted, but this project does not ask for it.
            return "unknown" if peg.value is None else "not_required"
        return report[peg.endpoint]["verdict"]

    parts = [
        f'<svg class="lego-board" viewBox="0 0 {W} {height}" width="100%" '
        f'role="img" aria-label="Predicted properties against required ranges" '
        f'xmlns="http://www.w3.org/2000/svg"><style>{_css()}</style>'
    ]
    if caption:
        parts.append(f'<text x="8" y="14" class="cap-strong">{_esc(caption)}</text>')

    for i, peg in enumerate(pegs):
        y = PAD_TOP + i * ROW_H
        parts.append(
            f'<g class="row">{"".join(_row(y, sockets.get(peg.endpoint), peg, verdict_for(peg)))}</g>'
        )

    base = PAD_TOP + ROW_H * len(pegs) + 6
    parts.append(f'<line x1="{TRACK_X0}" y1="{base}" x2="{TRACK_X1}" y2="{base}" class="axis"/>')
    for n, line in enumerate(
        (
            "band = required range  /  bar = prediction  /  "
            "pale tip = model uncertainty  /  dashed line = measured value",
            "every row has its own scale; the number on the right is the prediction",
        )
    ):
        parts.append(f'<text x="{TRACK_X0}" y="{base + 18 + n * 14}" class="cap">{_esc(line)}</text>')
    parts.append("</svg>")
    return "".join(parts)
