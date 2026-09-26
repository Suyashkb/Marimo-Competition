"""Shared scoring: every model and ablation is judged the same way on the test split."""

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from prep import ENDPOINTS

EPS = list(ENDPOINTS.values())


def score(truth: pd.DataFrame, pred: pd.DataFrame, split: str = "test") -> pd.DataFrame:
    """Per-endpoint MAE / Spearman / R² in model (log) space, joined on `name`."""
    t = truth[truth["split"] == split].set_index("name")
    p = pred.set_index("name").loc[t.index]
    rows = []
    for ep in EPS:
        m = t[ep].notna() & p[ep].notna()
        y, yh = t.loc[m, ep].to_numpy(), p.loc[m, ep].to_numpy()
        ss_res, ss_tot = ((y - yh) ** 2).sum(), ((y - y.mean()) ** 2).sum()
        rows.append(
            dict(
                endpoint=ep,
                n=int(m.sum()),
                mae=np.abs(y - yh).mean(),
                spearman=spearmanr(y, yh).statistic,
                r2=1 - ss_res / ss_tot,
            )
        )
    out = pd.DataFrame(rows).set_index("endpoint")
    out.loc["MEAN"] = out.mean(numeric_only=True)
    return out
