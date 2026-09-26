"""A fast stand-in for the graph ensemble, fitted inside the notebook.

Why this exists: the trained models are 36 MB per ensemble member and there is no
hosting, so they cannot travel with a notebook that must run on a fresh molab
session. What travels is the ensemble's *predictions* for all 7,608 molecules --
and those are dense labels for every endpoint, with no missing values, which is
exactly what a small model needs to learn the teacher's behaviour.

So the notebook distils: fit gradient-boosted trees on fingerprints to reproduce
what the ensemble said. That takes about ten seconds and then answers instantly
for a molecule nobody has measured -- which is what the edit-a-molecule puzzle
needs.

It is a stand-in and the notebook says so: `fidelity()` reports agreement with
the teacher (R^2 ~ 0.87 held out) so a reader can see how much to trust it.
"""

from dataclasses import dataclass, field

import numpy as np
from rdkit import Chem, RDLogger
from rdkit.Chem import Descriptors, rdFingerprintGenerator

RDLogger.DisableLog("rdApp.*")

FP_BITS = 1024
DESCRIPTORS = (
    "MolWt", "MolLogP", "TPSA", "NumHDonors", "NumHAcceptors",
    "NumRotatableBonds", "RingCount", "FractionCSP3", "NumAromaticRings",
    "HeavyAtomCount",
)

_gen = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=FP_BITS)
_desc = {n: f for n, f in Descriptors.descList if n in DESCRIPTORS}


def featurize(smiles: str) -> np.ndarray | None:
    """Morgan counts + a few interpretable descriptors, or None if unreadable."""
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    fp = _gen.GetCountFingerprintAsNumPy(mol).astype(np.float32)
    desc = np.array([_desc[n](mol) for n in DESCRIPTORS], dtype=np.float32)
    out = np.concatenate([fp, desc])
    return np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)


def featurize_many(smiles: list[str]) -> tuple[np.ndarray, list[int]]:
    rows, keep = [], []
    for i, s in enumerate(smiles):
        f = featurize(s)
        if f is not None:
            rows.append(f)
            keep.append(i)
    return np.stack(rows), keep


@dataclass
class Surrogate:
    endpoints: list[str]
    models: list = field(default_factory=list)
    _fidelity: dict[str, float] = field(default_factory=dict)

    def fit(self, smiles: list[str], teacher: np.ndarray, seed: int = 0) -> "Surrogate":
        """teacher: (n_molecules, n_endpoints) predictions from the full ensemble."""
        from sklearn.ensemble import HistGradientBoostingRegressor

        X, keep = featurize_many(smiles)
        Y = teacher[keep]
        # Hold out a slice to report honest agreement with the teacher.
        rng = np.random.default_rng(seed)
        order = rng.permutation(len(X))
        cut = int(0.85 * len(X))
        tr, te = order[:cut], order[cut:]

        self.models = []
        for j, ep in enumerate(self.endpoints):
            m = HistGradientBoostingRegressor(
                max_iter=120, learning_rate=0.15, random_state=seed
            )
            m.fit(X[tr], Y[tr, j])
            pred = m.predict(X[te])
            ss_res = ((Y[te, j] - pred) ** 2).sum()
            ss_tot = ((Y[te, j] - Y[te, j].mean()) ** 2).sum()
            self._fidelity[ep] = float(1 - ss_res / ss_tot)
            # Refit on everything now that fidelity is measured.
            m.fit(X, Y[:, j])
            self.models.append(m)
        return self

    def predict(self, smiles: str) -> dict[str, float] | None:
        """Model-space predictions for one molecule, or None if unreadable."""
        f = featurize(smiles)
        if f is None or not self.models:
            return None
        x = f.reshape(1, -1)
        return {ep: float(m.predict(x)[0]) for ep, m in zip(self.endpoints, self.models, strict=True)}

    def fidelity(self) -> dict[str, float]:
        """Held-out R^2 against the teacher, per endpoint. Not accuracy vs experiment."""
        return dict(self._fidelity)
