"""Pack everything the notebook needs into one small compressed blob.

Constraint that drives this file: there is no hosting. The notebook must run on a
fresh molab session with nothing but PyPI and the public HuggingFace copy of the
dataset, so the trained models (23 MB of LightGBM + 36 MB per Chemprop member)
cannot travel with it.

What travels instead is what those models *said*: per-molecule ensemble mean and
spread, the LightGBM comparison, and the evidence tables. Float32 is pointless for
predictions whose own ensemble spread is ~0.1, so everything is float16, then
zlib, then base64 -- small enough to paste into the notebook as a literal.

The notebook rebuilds a fast surrogate from these teacher predictions at runtime,
which is what makes live prediction on an edited molecule possible at all.
"""

import base64
import glob
import io
import json
import sys
import zlib
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from metrics import EPS  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "artifacts"


def build() -> dict:
    truth = pd.read_csv(ROOT / "data" / "prepared.csv")
    members = [pd.read_csv(p) for p in sorted(glob.glob(str(ROOT / "runs/ens/member_*.csv")))]
    lgbm = pd.read_csv(ROOT / "runs" / "lgbm" / "preds.csv").set_index("name")

    order = members[0]["name"].tolist()
    truth = truth.set_index("name").loc[order]
    lgbm = lgbm.loc[order]

    stack = {e: np.stack([m[e].to_numpy() for m in members]) for e in EPS}
    return {
        "names": order,
        "smiles": truth["smiles"].tolist(),
        "id_num": truth["id_num"].to_numpy(np.int32),
        "split": truth["split"].tolist(),
        "y": np.stack([truth[e].to_numpy(np.float32) for e in EPS], 1),
        "gnn": np.stack([stack[e].mean(0) for e in EPS], 1).astype(np.float32),
        "sd": np.stack([stack[e].std(0) for e in EPS], 1).astype(np.float32),
        "lgbm": np.stack([lgbm[e].to_numpy(np.float32) for e in EPS], 1),
        "endpoints": list(EPS),
    }


def encode(d: dict) -> str:
    """float16 + zlib + base64. NaN survives float16; the values do not need more."""
    buf = io.BytesIO()
    np.savez(
        buf,
        gnn=d["gnn"].astype(np.float16),
        sd=d["sd"].astype(np.float16),
        lgbm=d["lgbm"].astype(np.float16),
        meta=np.frombuffer(
            zlib.compress(
                json.dumps(
                    {
                        # SMILES and split are recoverable from the public CSV
                        # by molecule name, so only the join key travels.
                        "names": d["names"], "endpoints": d["endpoints"],
                    }
                ).encode(),
                9,
            ),
            dtype=np.uint8,
        ),
    )
    return base64.b64encode(zlib.compress(buf.getvalue(), 9)).decode()


def decode(blob: str) -> dict:
    """Inverse of encode(); this same function is copied into the notebook."""
    raw = zlib.decompress(base64.b64decode(blob))
    z = np.load(io.BytesIO(raw), allow_pickle=False)
    meta = json.loads(zlib.decompress(z["meta"].tobytes()).decode())
    return {
        "gnn": z["gnn"].astype(np.float32),
        "sd": z["sd"].astype(np.float32),
        "lgbm": z["lgbm"].astype(np.float32),
        **meta,
    }


def main() -> None:
    ART.mkdir(exist_ok=True)
    d = build()
    blob = encode(d)
    (ART / "bundle.b64").write_text(blob)

    back = decode(blob)
    err = np.nanmax(np.abs(back["gnn"] - d["gnn"]))
    print(f"molecules      {len(d['names'])}")
    print(f"blob           {len(blob) / 1024:.0f} KiB base64")
    print(f"round-trip max abs error on predictions: {err:.5f}")
    assert back["names"] == d["names"] and back["endpoints"] == d["endpoints"]
    assert err < 0.01, "float16 lost too much precision"
    print("ok")


if __name__ == "__main__":
    main()
