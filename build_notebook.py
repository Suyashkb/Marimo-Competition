"""Assemble the single-file marimo notebook that gets uploaded to molab.

molab runs one .py file with no repo beside it, so everything has to be inside
that file: the library modules from lego/, and the 460 KiB bundle of what the
trained ensemble predicted. This script inlines both into notebook_src.py's
placeholders and writes notebook.py.

Keeping the source split during development (lego/ + tests) and only joining at
build time means the library stays unit-tested rather than becoming an untestable
wall of text inside a notebook cell.
"""

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "notebook_src.py"
OUT = ROOT / "notebook.py"
BUNDLE = ROOT / "artifacts" / "bundle.b64"

# Inlined in dependency order; `lego.x` imports are rewritten to plain names.
MODULES = (
    "units", "sockets", "board", "edits", "pairs", "draw", "surrogate", "interaction",
)

# marimo requires exactly one defining cell per name, so every import and every
# library symbol is owned by the single library cell and handed to the rest.
PREAMBLE = """import base64
import io
import json
import zlib
from dataclasses import dataclass, field

import altair as alt
import marimo as mo
import numpy as np
import pandas as pd
"""

EXPORTS = (
    "mo", "np", "pd", "alt", "base64", "io", "json", "zlib",
    "Peg", "render", "AXIS", "clamp",
    "Socket", "PRESETS", "META", "fit_report", "clicks",
    "to_real", "to_model", "format_value",
    "EDITS", "BY_KEY", "apply_edit", "options", "products",
    "find_pairs", "fragment",
    "picture", "painted", "highlight", "changed_atoms",
    "Surrogate", "featurize", "neighborhood",
    "auc_ratio", "apparent_clearance", "severity",
)


def module_source(name: str) -> str:
    text = (ROOT / "lego" / f"{name}.py").read_text()
    # Flatten intra-package imports: everything lands in one namespace.
    text = re.sub(r"^from lego\.\w+ import .*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"^from lego import .*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s+from lego\.\w+ import .*$", "", text, flags=re.MULTILINE)
    # Drop the module docstring; the notebook introduces each section itself.
    text = re.sub(r'\A\s*"""(?:[^"]|"(?!""))*"""', "", text, count=1).strip()
    return f"# ---------- lego/{name}.py ----------\n{text}\n"


def deprivatize(text: str) -> str:
    """Rename module-level `_helper` to `lg_helper` throughout the library.

    marimo treats an underscore-prefixed top-level name as local to the cell that
    defines it. The library's private helpers are defined in the library cell but
    called from functions that run in other cells, where those names no longer
    exist -- so the leading underscore has to go at build time. The source keeps
    its normal Python conventions.
    """
    private = set(
        re.findall(r"^(?:def|class)\s+_(\w+)", text, flags=re.MULTILINE)
    ) | set(re.findall(r"^_(\w+)\s*(?::[^=\n]+)?=", text, flags=re.MULTILINE))
    for name in sorted(private, key=len, reverse=True):
        text = re.sub(rf"(?<![\w.])_{name}\b", f"lg_{name}", text)
    return text


def build() -> str:
    src = SRC.read_text()
    if "__BUNDLE__" not in src or "__LIBRARY__" not in src:
        raise SystemExit("notebook_src.py is missing a placeholder")

    body = deprivatize("\n\n".join(module_source(m) for m in MODULES))
    returns = ", ".join(EXPORTS)
    library = f"{PREAMBLE}\n\n{body}\n\nreturn ({returns})\n"
    blob = BUNDLE.read_text().strip()

    # Chunk the base64 so no single source line is absurdly long.
    width = 120
    chunks = "\n".join(
        f'        "{blob[i : i + width]}"' for i in range(0, len(blob), width)
    )
    src = src.replace('"__BUNDLE__"', f"(\n{chunks}\n    )")
    return src.replace("    __LIBRARY__", _indent(library, 4))


def _indent(text: str, n: int) -> str:
    pad = " " * n
    return "\n".join(pad + line if line.strip() else line for line in text.split("\n"))


def main() -> None:
    OUT.write_text(build())
    size = OUT.stat().st_size / 1024
    print(f"wrote {OUT.name}  {size:.0f} KiB")

    # A notebook that does not parse is a disqualified submission.
    subprocess.run([sys.executable, "-c", f"compile(open('{OUT}').read(), '{OUT}', 'exec')"],
                   check=True)
    print("parses cleanly")


if __name__ == "__main__":
    main()
