"""Two ablations for Part 2: does message-passing depth help, and does multitask help?

Each run is a fresh Chemprop model on the same temporal split, so the only thing
that changes is the knob under test. Single seed per setting: these support a
qualitative claim ("deeper helps", "sharing helps"), not a precise number, and the
notebook says so.

Writes runs/ablate/summary.csv
"""

import subprocess
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from metrics import EPS, score  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "runs" / "ablate"
CHEMPROP = ROOT / ".venv" / "bin" / "chemprop"
DATA = ROOT / "data" / "prepared.csv"
DEPTHS = (1, 2, 3, 4, 5)


def run(tag: str, targets: list[str], extra: list[str]) -> Path:
    out = OUT / tag
    if (out / "model_0" / "best.pt").exists():
        print(f"  {tag}: already trained")
        return out
    cmd = [
        str(CHEMPROP), "train", "-i", str(DATA), "-s", "smiles",
        "--target-columns", *targets,
        "--splits-column", "split",
        "--from-foundation", "CHEMELEON",
        "--epochs", "100", "--patience", "20",
        "-o", str(out), "--accelerator", "gpu", "--devices", "1",
        *extra,
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return out


def predict(run_dir: Path) -> pd.DataFrame:
    out = run_dir / "preds.csv"
    if not out.exists():
        subprocess.run(
            [
                str(CHEMPROP), "predict", "-i", str(DATA), "-s", "smiles",
                "--model-path", str(run_dir / "model_0" / "best.pt"),
                "-o", str(out), "--accelerator", "gpu", "--devices", "1",
            ],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
    return pd.read_csv(out)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    truth = pd.read_csv(DATA)
    rows = []

    print("depth ablation")
    for d in DEPTHS:
        tag = f"depth_{d}"
        print(f"  training {tag}")
        s = score(truth, predict(run(tag, EPS, ["--depth", str(d)])))
        rows.append(dict(setting=tag, kind="depth", depth=d, endpoint="MEAN",
                         mae=s.mae["MEAN"], spearman=s.spearman["MEAN"]))
        for ep in EPS:
            rows.append(dict(setting=tag, kind="depth", depth=d, endpoint=ep,
                             mae=s.mae[ep], spearman=s.spearman[ep]))

    print("single-task ablation")
    for ep in EPS:
        tag = f"single_{ep}"
        print(f"  training {tag}")
        s = score(truth, predict(run(tag, [ep], [])))
        rows.append(dict(setting=tag, kind="single", depth=None, endpoint=ep,
                         mae=s.mae[ep], spearman=s.spearman[ep]))

    pd.DataFrame(rows).to_csv(OUT / "summary.csv", index=False)
    print(f"wrote {OUT / 'summary.csv'}")


if __name__ == "__main__":
    main()
