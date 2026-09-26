"""Run every ensemble member over the whole dataset, one CSV per member.

Member spread is the notebook's uncertainty signal (the "blur" on a peg), so the
per-member predictions are kept rather than only their mean.
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENS = ROOT / "runs" / "ens"
PY = ROOT / ".venv" / "bin" / "chemprop"


def main() -> None:
    models = sorted(ENS.glob("model_*/best.pt"))
    if not models:
        raise SystemExit(f"no trained members under {ENS}")
    for i, model in enumerate(models):
        out = ENS / f"member_{i}.csv"
        cmd = [
            str(PY), "predict",
            "-i", str(ROOT / "data" / "prepared.csv"),
            "-s", "smiles",
            "--model-path", str(model),
            "-o", str(out),
            "--accelerator", "gpu", "--devices", "1",
        ]
        print(f"[{i + 1}/{len(models)}] {model.parent.name} -> {out.name}")
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"done: {len(models)} members")


if __name__ == "__main__":
    sys.exit(main())
