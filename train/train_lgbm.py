"""LightGBM per endpoint on Morgan count fingerprints + RDKit descriptors.

This is the "tree" half of the GNN + tree hybrid. Early stopping uses the
time-ordered validation split from prep.py; the test split is never touched
during training.

Output: runs/lgbm/preds.csv (name, split, <endpoint> predictions in model space)
        runs/lgbm/<endpoint>.txt (boosters, for live inference in the notebook)
"""

from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd
from rdkit import Chem, RDLogger
from rdkit.Chem import Descriptors, rdFingerprintGenerator

from prep import ENDPOINTS

RDLogger.DisableLog("rdApp.*")

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "runs" / "lgbm"

_morgan = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)
DESC_NAMES = [n for n, _ in Descriptors.descList]


def featurize(smiles: str) -> np.ndarray:
    mol = Chem.MolFromSmiles(smiles)
    fp = _morgan.GetCountFingerprintAsNumPy(mol).astype(np.float32)
    desc = np.array(list(Descriptors.CalcMolDescriptors(mol).values()), dtype=np.float32)
    return np.concatenate([fp, desc])


PARAMS = dict(
    objective="regression",
    learning_rate=0.03,
    num_leaves=31,
    min_data_in_leaf=10,
    feature_fraction=0.3,
    bagging_fraction=0.8,
    bagging_freq=1,
    lambda_l2=1.0,
    verbose=-1,
)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(ROOT / "data" / "prepared.csv")
    X = np.stack(df["smiles"].map(featurize))
    X[~np.isfinite(X)] = np.nan

    preds = df[["name", "split"]].copy()
    for ep in ENDPOINTS.values():
        y = df[ep].to_numpy()
        tr = (df["split"] == "train").to_numpy() & ~np.isnan(y)
        va = (df["split"] == "val").to_numpy() & ~np.isnan(y)
        booster = lgb.train(
            PARAMS,
            lgb.Dataset(X[tr], y[tr]),
            num_boost_round=3000,
            valid_sets=[lgb.Dataset(X[va], y[va])],
            callbacks=[lgb.early_stopping(100, verbose=False)],
        )
        booster.save_model(str(OUT / f"{ep}.txt"))
        preds[ep] = booster.predict(X, num_iteration=booster.best_iteration)
        print(f"{ep:7s} rounds={booster.best_iteration}")

    preds.to_csv(OUT / "preds.csv", index=False)


if __name__ == "__main__":
    main()
