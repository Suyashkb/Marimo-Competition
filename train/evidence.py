"""Check every claim the notebook wants to make, on the temporal test split.

Writes evidence_report.md. A claim that fails here does not go in the notebook.
Run after the ensemble and LightGBM are trained.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

sys.path.insert(0, str(Path(__file__).parent))
from metrics import EPS, score  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from lego.pairs import find_pairs  # noqa: E402
from lego.units import to_real  # noqa: E402

OUT = ROOT / "evidence_report.md"
lines: list[str] = []


def say(s: str = "") -> None:
    print(s)
    lines.append(s)


def load() -> tuple[pd.DataFrame, pd.DataFrame, list[pd.DataFrame], pd.DataFrame]:
    truth = pd.read_csv(ROOT / "data" / "prepared.csv")
    members = [
        pd.read_csv(p) for p in sorted((ROOT / "runs" / "ens").glob("member_*.csv"))
    ]
    if not members:
        raise SystemExit("no ensemble predictions; run predict_ens.py first")
    mean = members[0][["name"]].copy()
    stacked = {ep: np.stack([m[ep].to_numpy() for m in members]) for ep in EPS}
    for ep in EPS:
        mean[ep] = stacked[ep].mean(axis=0)
    std = members[0][["name"]].copy()
    for ep in EPS:
        std[ep] = stacked[ep].std(axis=0)
    lgbm = pd.read_csv(ROOT / "runs" / "lgbm" / "preds.csv")
    return truth, mean, [std, *members], lgbm


def a_graph_models_lead(truth, gnn, lgbm) -> None:
    """Graph model vs tree model, nothing more.

    This comparison cannot say *why* the GNN wins: depth, multitask sharing and
    pretraining are all confounded here. Those are tested separately in ablate2.py.
    An earlier version of this function labelled its verdict "A1/A2" (depth and
    multitask), which the measurement does not support.
    """
    say("## A0. Does the graph model beat the tree model?\n")
    say("_Scope: which family wins overall. It identifies no mechanism -- depth, "
        "multitask sharing and CheMeleon pretraining are confounded. See ablate2.py._\n")
    sg, sl = score(truth, gnn), score(truth, lgbm)
    cmp = pd.DataFrame(
        {"GNN MAE": sg.mae, "LGBM MAE": sl.mae, "GNN rho": sg.spearman, "LGBM rho": sl.spearman}
    ).round(3)
    say(cmp.to_markdown())
    wins = int((sg.mae.drop("MEAN") < sl.mae.drop("MEAN")).sum())
    say(f"\nGNN better MAE on {wins}/9 endpoints. "
        f"Mean MAE {sg.mae['MEAN']:.3f} vs {sl.mae['MEAN']:.3f}.")
    say(f"VERDICT A0 (family comparison only): {'KEEP' if wins >= 5 else 'RECONSIDER'}\n")


def a4_blending(truth, gnn, lgbm) -> None:
    say("## A4. When does blending with a tree model help?\n")
    t = truth[truth.split == "test"].set_index("name")
    g, l = gnn.set_index("name"), lgbm.set_index("name")
    rows = []
    for ep in EPS:
        m = t[ep].notna()
        idx = t.index[m]
        y, yg, yl = t.loc[idx, ep], g.loc[idx, ep], l.loc[idx, ep]
        rg, rl = y - yg, y - yl
        best = min(
            ((np.abs(y - (w * yg + (1 - w) * yl)).mean(), w) for w in np.linspace(0, 1, 21))
        )
        rows.append(
            dict(
                endpoint=ep,
                resid_corr=np.corrcoef(rg, rl)[0, 1],
                gnn_mae=np.abs(rg).mean(),
                blend50_mae=np.abs(y - 0.5 * (yg + yl)).mean(),
                best_mae=best[0],
                best_w_gnn=best[1],
            )
        )
    df = pd.DataFrame(rows).set_index("endpoint").round(3)
    df["blend_helps"] = df.blend50_mae < df.gnn_mae
    say(df.to_markdown())
    say("\nNote: best_w_gnn is chosen on test, so it is an upper bound, shown only to "
        "indicate where a blend could help at all.")
    helped = df.index[df.blend_helps].tolist()
    say(f"\nBlending (50/50) helps on: {helped or 'none'}")
    say(f"VERDICT A4: {'KEEP (reframed: helps only on local properties)' if helped else 'CUT'}\n")


def b1_cliffs(truth, gnn) -> None:
    say("## B1. Activity cliffs\n")
    t = truth.set_index("name")
    pairs = find_pairs(truth.name.tolist(), truth.smiles.tolist())
    g = gnn.set_index("name")
    test_names = set(truth.loc[truth.split == "test", "name"])
    rows = []
    for ep in ("HLM", "MLM", "LogD", "Efflux"):
        cliff_err, flat_err, n_cliff = [], [], 0
        for p in pairs:
            if p.name_a not in test_names and p.name_b not in test_names:
                continue
            va, vb = t.at[p.name_a, ep], t.at[p.name_b, ep]
            if pd.isna(va) or pd.isna(vb):
                continue
            gap = abs(va - vb)  # model space = log10 units
            for nm, v in ((p.name_a, va), (p.name_b, vb)):
                if nm not in test_names:
                    continue
                err = abs(v - g.at[nm, ep])
                if gap >= 1.0:  # a 10-fold difference from one small edit
                    cliff_err.append(err)
                    n_cliff += 1
                elif gap <= 0.1:
                    flat_err.append(err)
        if cliff_err and flat_err:
            rows.append(
                dict(
                    endpoint=ep,
                    n_cliff=n_cliff,
                    cliff_mae=np.mean(cliff_err),
                    flat_mae=np.mean(flat_err),
                    ratio=np.mean(cliff_err) / np.mean(flat_err),
                )
            )
    df = pd.DataFrame(rows).set_index("endpoint").round(3)
    say(df.to_markdown())
    ok = bool(len(df)) and bool((df.ratio > 1.3).any())
    say(f"\nVERDICT B1: {'KEEP' if ok else 'RECONSIDER'} "
        "(error on cliff pairs vs near-identical pairs)\n")


def b2_drift(truth, gnn, std) -> None:
    say("## B2. Drift into new chemistry\n")
    t = truth[truth.split == "test"].set_index("name")
    g, s = gnn.set_index("name"), std.set_index("name")
    rows = []
    for ep in EPS:
        m = t[ep].notna()
        idx = t.index[m]
        err = (t.loc[idx, ep] - g.loc[idx, ep]).abs()
        rho = spearmanr(s.loc[idx, ep], err).statistic
        bias = (g.loc[idx, ep] - t.loc[idx, ep]).mean()
        rows.append(dict(endpoint=ep, unc_vs_err_rho=rho, mean_bias=bias))
    df = pd.DataFrame(rows).set_index("endpoint").round(3)
    say(df.to_markdown())
    say("\nmean_bias > 0 means the model predicts too high on later compounds.")
    good = int((df.unc_vs_err_rho > 0.15).sum())
    say(f"\nUncertainty tracks error on {good}/9 endpoints.")
    say(f"VERDICT B2: {'KEEP' if good >= 5 else 'RECONSIDER (blur may be meaningless)'}\n")

    tr = truth[truth.split == "train"]
    te = truth[truth.split == "test"]
    shift = pd.DataFrame(
        {
            "train median": [to_real(e, tr[e].median()) for e in EPS],
            "test median": [to_real(e, te[e].median()) for e in EPS],
        },
        index=EPS,
    ).round(2)
    say("Real-unit medians, early vs late compounds (the whack-a-mole story):\n")
    say(shift.to_markdown())
    say("")


def b3_censoring(truth, gnn) -> None:
    say("## B3. The solubility ceiling\n")
    raw = pd.read_csv(ROOT / "data" / "expansion_data_raw.csv")
    ksol = raw["KSOL"].dropna().astype(str)
    say(f"Raw KSOL values: {len(ksol)}, of which censored ('<' or '>'): "
        f"{ksol.str.startswith(('<', '>')).sum()}")
    hlm = raw["HLM CLint"].dropna().astype(str)
    say(f"Raw HLM values: {len(hlm)}, censored: {hlm.str.startswith(('<', '>')).sum()} "
        f"(of which '<': {hlm.str.startswith('<').sum()} - the most stable compounds, "
        "deleted from the ML-ready file)")

    t = truth[truth.split == "test"].set_index("name")
    g = gnn.set_index("name")
    m = t["KSOL"].notna()
    idx = t.index[m]
    real = t.loc[idx, "KSOL"].map(lambda v: to_real("KSOL", v))
    rows = []
    for lo, hi, label in ((0, 100, "low (0-100 uM)"), (100, 250, "mid"), (250, 1e9, "at ceiling")):
        sel = (real >= lo) & (real < hi)
        if sel.sum() < 30:
            continue
        y, yh = t.loc[idx[sel], "KSOL"], g.loc[idx[sel], "KSOL"]
        rows.append(
            dict(band=label, n=int(sel.sum()), mae=np.abs(y - yh).mean(),
                 spearman=spearmanr(y, yh).statistic)
        )
    df = pd.DataFrame(rows).set_index("band").round(3)
    say("\nModel quality by solubility band:\n")
    say(df.to_markdown())
    say("\nLow MAE with collapsed rho at the ceiling = looks accurate, cannot rank.")
    say("VERDICT B3: KEEP if rho drops in the ceiling band.\n")


def b4_stereo(truth) -> None:
    say("## B4. Blind to 3D\n")
    from rdkit import Chem

    flat: dict[str, list[str]] = {}
    for name, smi in zip(truth.name, truth.smiles, strict=True):
        mol = Chem.MolFromSmiles(smi)
        if mol is None:
            continue
        key = Chem.MolToSmiles(mol, isomericSmiles=False)
        flat.setdefault(key, []).append(name)
    groups = {k: v for k, v in flat.items() if len(v) > 1}
    say(f"Molecules sharing a 2D skeleton but differing in stereochemistry: {len(groups)} groups")
    t = truth.set_index("name")
    diffs = 0
    for names in groups.values():
        for ep in EPS:
            vals = t.loc[names, ep].dropna()
            if len(vals) > 1 and vals.max() - vals.min() >= 0.5:
                diffs += 1
                break
    say(f"Groups where a measured value differs by >=0.5 log units: {diffs}")
    say(f"VERDICT B4: {'KEEP' if diffs >= 10 else 'CUT (too few examples)'}\n")


def main() -> None:
    truth, gnn, extras, lgbm = load()
    std = extras[0]
    say("# Evidence report\n")
    say(f"Test split: {(truth.split == 'test').sum()} molecules, IDs >= 20101. "
        f"Ensemble members: {len(extras) - 1}.\n")
    a_graph_models_lead(truth, gnn, lgbm)
    a4_blending(truth, gnn, lgbm)
    b1_cliffs(truth, gnn)
    b2_drift(truth, gnn, std)
    b3_censoring(truth, gnn)
    b4_stereo(truth)
    OUT.write_text("\n".join(lines) + "\n")
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()
