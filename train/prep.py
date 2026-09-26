"""Standardize ExpansionRx molecules, log-transform targets, and assign the temporal split.

Output: data/prepared.csv with columns
    name, smiles, id_num, split (train/val/test), <9 endpoint columns in model space>

Split: the official challenge split (test = IDs >= 20101). The last 10% of the
training IDs become validation, so early stopping also respects time order.
"""

from pathlib import Path

import numpy as np
import pandas as pd
from rdkit import Chem, RDLogger
from rdkit.Chem.MolStandardize import rdMolStandardize

RDLogger.DisableLog("rdApp.*")

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

# Column in the CSV -> short name used everywhere else.
ENDPOINTS = {
    "LogD": "LogD",
    "KSOL": "KSOL",
    "HLM CLint": "HLM",
    "MLM CLint": "MLM",
    "Caco-2 Permeability Papp A>B": "Papp",
    "Caco-2 Permeability Efflux": "Efflux",
    "MPPB": "MPPB",
    "MBPB": "MBPB",
    "MGMB": "MGMB",
}
# LogD is already a log value; everything else is log10(x + 1) so zeros survive.
LOG_ENDPOINTS = [v for v in ENDPOINTS.values() if v != "LogD"]
VAL_FRACTION = 0.10

_chooser = rdMolStandardize.LargestFragmentChooser()


def standardize(smiles: str) -> str | None:
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    mol = _chooser.choose(mol)
    return Chem.MolToSmiles(mol)


def to_model_space(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for c in LOG_ENDPOINTS:
        out[c] = np.log10(out[c] + 1)
    return out


def to_real_units(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for c in LOG_ENDPOINTS:
        if c in out:
            out[c] = 10 ** out[c] - 1
    return out


def main() -> None:
    train = pd.read_csv(DATA / "expansion_data_train.csv").assign(split="train")
    test = pd.read_csv(DATA / "expansion_data_test.csv").assign(split="test")
    df = pd.concat([train, test], ignore_index=True).rename(
        columns={"Molecule Name": "name", "SMILES": "smiles_raw", **ENDPOINTS}
    )
    df["id_num"] = df["name"].str.split("-").str[1].astype(int)

    df["smiles"] = df["smiles_raw"].map(standardize)
    bad = df["smiles"].isna().sum()
    assert bad == 0, f"{bad} SMILES failed to parse"

    # Last VAL_FRACTION of training IDs -> validation (time-ordered early stopping).
    tr = df["split"] == "train"
    cutoff = df.loc[tr, "id_num"].quantile(1 - VAL_FRACTION)
    df.loc[tr & (df["id_num"] > cutoff), "split"] = "val"

    df = to_model_space(df)
    cols = ["name", "smiles", "id_num", "split", *ENDPOINTS.values()]
    df[cols].sort_values("id_num").to_csv(DATA / "prepared.csv", index=False)

    dup = df.duplicated("smiles").sum()
    print(df["split"].value_counts().to_string())
    print(f"duplicate standardized SMILES: {dup}")


if __name__ == "__main__":
    main()
