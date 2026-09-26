"""Corrected ablations, replacing the broken first attempt.

Two bugs in ablate.py made its results meaningless:

1. `--depth` was silently ignored when `--from-foundation CHEMELEON` was given:
   every "depth_N" checkpoint stored depth=6, so that sweep measured seed noise.
   Fixed by running the depth sweep *without* the foundation model, which also
   gives the scratch-vs-pretrained comparison for free.
2. Single seed per setting, while seed noise on this data is large (test-MAE
   spread across 5 seeds: MPPB 23%, MGMB 15%, KSOL 12%). Any effect smaller than
   that is unreadable. Fixed by running SEEDS seeds per setting.

Also: each run now tees chemprop's own output to <run>/train.log so training is
directly tailable.
"""

import subprocess
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from metrics import EPS, score  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "runs" / "ablate2"
CHEMPROP = ROOT / ".venv" / "bin" / "chemprop"
DATA = ROOT / "data" / "prepared.csv"

SEEDS = (0, 1, 2)
DEPTHS = (2, 4, 6)
# Endpoints worth the multi-seed single-task comparison: the two whose single-seed
# effect exceeded seed noise, the one that diverged, and its nearest neighbour.
SINGLE_EPS = ("LogD", "Papp", "MGMB", "MBPB")


def train(tag: str, targets: list[str], seed: int, extra: list[str]) -> Path | None:
    out = OUT / f"{tag}_s{seed}"
    ckpt = out / "model_0" / "best.pt"
    if ckpt.exists():
        print(f"  {out.name}: already trained", flush=True)
        return out
    out.mkdir(parents=True, exist_ok=True)
    cmd = [
        str(CHEMPROP), "train", "-i", str(DATA), "-s", "smiles",
        "--target-columns", *targets,
        "--splits-column", "split",
        "--epochs", "100", "--patience", "20",
        "--pytorch-seed", str(seed),
        "-o", str(out), "--accelerator", "gpu", "--devices", "1",
        *extra,
    ]
    print(f"  training {out.name}", flush=True)
    with (out / "train.log").open("w") as log:
        res = subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT)
    if res.returncode != 0 or not ckpt.exists():
        print(f"  !! {out.name} FAILED (see train.log)", flush=True)
        return None
    return out


def predict(run_dir: Path) -> pd.DataFrame | None:
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


def diverged(preds: pd.DataFrame, cols: list[str]) -> bool:
    """A model whose weights blew up predicts NaN everywhere."""
    return all(preds[c].isna().all() for c in cols)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    truth = pd.read_csv(DATA)
    rows = []

    # 1. Depth, with no foundation model, so --depth actually takes effect.
    print("depth sweep (scratch init, depth genuinely varied)")
    for d in DEPTHS:
        for seed in SEEDS:
            run = train(f"scratch_depth{d}", list(EPS), seed, ["--depth", str(d)])
            if run is None:
                continue
            p = predict(run)
            if diverged(p, list(EPS)):
                rows.append(dict(kind="depth", setting=f"scratch_d{d}", seed=seed,
                                 endpoint="ALL", mae=None, diverged=True))
                continue
            s = score(truth, p)
            for ep in [*EPS, "MEAN"]:
                rows.append(dict(kind="depth", setting=f"scratch_d{d}", seed=seed,
                                 endpoint=ep, mae=s.mae[ep], diverged=False))

    # 2. Pretrained reference at CheMeleon's own depth, same seeds.
    print("pretrained reference (CheMeleon)")
    for seed in SEEDS:
        run = train("chemeleon", list(EPS), seed, ["--from-foundation", "CHEMELEON"])
        if run is None:
            continue
        s = score(truth, predict(run))
        for ep in [*EPS, "MEAN"]:
            rows.append(dict(kind="pretrain", setting="chemeleon", seed=seed,
                             endpoint=ep, mae=s.mae[ep], diverged=False))

    # 3. Single-task vs multitask, multi-seed, on the endpoints that matter.
    print("single-task, multi-seed")
    for ep in SINGLE_EPS:
        for seed in SEEDS:
            run = train(f"single_{ep}", [ep], seed, ["--from-foundation", "CHEMELEON"])
            if run is None:
                rows.append(dict(kind="single", setting=f"single_{ep}", seed=seed,
                                 endpoint=ep, mae=None, diverged=True))
                continue
            p = predict(run)
            if diverged(p, [ep]):
                print(f"  {ep} seed {seed}: DIVERGED (all-NaN predictions)", flush=True)
                rows.append(dict(kind="single", setting=f"single_{ep}", seed=seed,
                                 endpoint=ep, mae=None, diverged=True))
                continue
            s = score(truth, p)
            rows.append(dict(kind="single", setting=f"single_{ep}", seed=seed,
                             endpoint=ep, mae=s.mae[ep], diverged=False))

    pd.DataFrame(rows).to_csv(OUT / "summary.csv", index=False)
    print(f"wrote {OUT / 'summary.csv'}")


if __name__ == "__main__":
    main()
