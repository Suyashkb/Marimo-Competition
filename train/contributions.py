"""Per-atom contributions: how much does each atom matter to each prediction?

Method: mask one atom at a time and re-predict. The shift in the prediction is
that atom's contribution. Masking is done by turning the atom into a dummy
("[*]") rather than deleting it, so the molecular graph stays connected and the
comparison is about that atom's identity, not about breaking the molecule in half.

This is what Part 3 needs: on a global property every atom shifts the prediction a
little; on a local property one atom shifts it a lot.

Writes artifacts/contributions.parquet with one row per (molecule, atom, endpoint).
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from rdkit import Chem, RDLogger

from chemprop import data, featurizers
from chemprop.models import MPNN

RDLogger.DisableLog("rdApp.*")
sys.path.insert(0, str(Path(__file__).parent))
from metrics import EPS  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "artifacts"
BATCH = 256


def masked_variants(smiles: str) -> tuple[list[str], list[int]]:
    """One variant per heavy atom, with that atom turned into a dummy."""
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return [], []
    out, idxs = [], []
    for atom in mol.GetAtoms():
        rw = Chem.RWMol(mol)
        a = rw.GetAtomWithIdx(atom.GetIdx())
        a.SetAtomicNum(0)
        a.SetFormalCharge(0)
        a.SetNoImplicit(True)
        a.SetNumExplicitHs(0)
        a.SetIsAromatic(False)
        for bond in a.GetBonds():
            bond.SetBondType(Chem.BondType.SINGLE)
            bond.SetIsAromatic(False)
        try:
            Chem.SanitizeMol(rw)
            smi = Chem.MolToSmiles(rw)
            if Chem.MolFromSmiles(smi) is None:
                continue
        except Exception:  # noqa: BLE001 - masking aromatics can fail sanitization
            continue
        out.append(smi)
        idxs.append(atom.GetIdx())
    return out, idxs


def predict(model: MPNN, smiles_list: list[str], device: str) -> np.ndarray:
    featurizer = featurizers.SimpleMoleculeMolGraphFeaturizer()
    rows = [data.MoleculeDatapoint.from_smi(s) for s in smiles_list]
    dset = data.MoleculeDataset(rows, featurizer)
    loader = data.build_dataloader(dset, batch_size=BATCH, shuffle=False)
    outs = []
    with torch.no_grad():
        for batch in loader:
            bmg, v_d, x_d, *_ = batch
            bmg.to(device)  # mutates in place and returns None, so do not reassign
            outs.append(model(bmg, v_d, x_d).cpu().numpy())
    return np.concatenate(outs)


def main(limit: int | None = None) -> None:
    ART.mkdir(exist_ok=True)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = MPNN.load_from_file(ROOT / "runs" / "ens" / "model_0" / "best.pt").to(device).eval()

    df = pd.read_csv(ROOT / "data" / "prepared.csv")
    if limit:
        df = df.head(limit)

    base = predict(model, df["smiles"].tolist(), device)

    records = []
    for row_i, (name, smi) in enumerate(zip(df["name"], df["smiles"], strict=True)):
        variants, atom_idxs = masked_variants(smi)
        if not variants:
            continue
        got = predict(model, variants, device)
        delta = base[row_i] - got  # positive = removing this atom lowers the prediction
        for k, atom_idx in enumerate(atom_idxs):
            rec = {"name": name, "atom": atom_idx}
            for j, ep in enumerate(EPS):
                rec[ep] = float(delta[k, j])
            records.append(rec)
        if row_i % 500 == 0:
            print(f"  {row_i}/{len(df)}", flush=True)

    out = pd.DataFrame.from_records(records)
    out.to_parquet(ART / "contributions.parquet", index=False)
    print(f"wrote {ART / 'contributions.parquet'}  rows={len(out)}")

    print(concentration(out).round(3).to_string())


def concentration(contrib: pd.DataFrame) -> pd.DataFrame:
    """Part 3's claim as one number per endpoint, comparable across endpoints.

    For each molecule, how much of the total atom contribution sits in the single
    biggest atom? Raw magnitudes are not comparable (LogD is untransformed while
    the rest are log10), so everything is a share of that molecule's own total.

    A *local* property should concentrate in few atoms; a *global* one should spread.
    """
    rows = {}
    for ep in EPS:
        absval = contrib[["name", ep]].copy()
        absval[ep] = absval[ep].abs()
        total = absval.groupby("name")[ep].sum()
        top1 = absval.groupby("name")[ep].max()
        top3 = absval.groupby("name")[ep].apply(lambda s: s.nlargest(3).sum())
        n_atoms = absval.groupby("name")[ep].size()
        ok = total > 0
        rows[ep] = dict(
            top1_share=float((top1[ok] / total[ok]).mean()),
            top3_share=float((top3[ok] / total[ok]).mean()),
            # What an even spread would give, for reference.
            even_top1=float((1 / n_atoms[ok]).mean()),
        )
    out = pd.DataFrame(rows).T
    out["concentration"] = out.top1_share / out.even_top1
    return out.sort_values("concentration")


if __name__ == "__main__":
    main(limit=int(sys.argv[1]) if len(sys.argv) > 1 else None)
