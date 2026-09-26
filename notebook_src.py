# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "marimo",
#     "numpy",
#     "pandas",
#     "rdkit",
#     "scikit-learn",
#     "altair",
# ]
# ///
"""Molecular Lego -- molab Notebook Competition #3 entry.

Built from https://github.com/Suyashkb/Marimo-Competition ; this single file is
assembled by build_notebook.py and is self-contained by design.
"""

import marimo

__generated_with = "0.25.0"
app = marimo.App(width="medium", app_title="Molecular Lego")


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    <div style="border-left:4px solid #2a78d6;padding:0.2rem 0 0.2rem 1rem">

    # Molecular Lego
    ### Nine properties, one model, nine different problems

    </div>

    A drug has to be many things at once. Soluble enough to dissolve. Greasy enough
    to cross a membrane, but not so greasy it falls apart. Slow enough to survive the
    liver. Free enough in the blood to actually reach anything.

    Miss **one** and the molecule is dead, however good the rest looks.

    So this notebook draws a molecule as a **Lego piece**: one peg per property, and
    a **socket** that a given project will accept. The piece clicks, or it doesn't.

    Then it asks the question it was really built for: *when the peg comes out the
    wrong length, whose fault is it -- the model's, or the data's?*

    The answer turns out to be different for every one of the nine properties. That
    is the whole notebook.
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.accordion(
        {
            "New to any of this? Start here (60 seconds)": mo.md(
                r"""
| Word | What it means |
|---|---|
| **ADMET** | What the body does to a drug: **A**bsorption, **D**istribution, **M**etabolism, **E**xcretion, **T**oxicity. A potent drug that fails any of these is not a drug. |
| **SMILES** | A molecule written as text. `CCO` is ethanol. The model reads these. |
| **LogD** | Greasiness. How the molecule splits between oil and water at blood pH. Roughly 1-3 is the sweet spot. |
| **Solubility (KSOL)** | How much dissolves in water, in micromolar. Undissolved drug cannot be absorbed. |
| **Clearance (HLM/MLM)** | How fast liver enzymes destroy it. **H**uman or **M**ouse **L**iver **M**icrosomes. Lower is better. |
| **Permeability (Papp)** | How fast it crosses a sheet of gut-like cells. Higher is better. |
| **Efflux** | How hard cells pump it back out. Above ~2 is trouble, especially for the brain. |
| **Protein binding (MPPB/MBPB/MGMB)** | The % left *unbound* in blood, brain or muscle. Only unbound drug can act. |
| **Endpoint** | One measured property. This dataset has nine. |
| **Temporal split** | Train on molecules the chemists made early, test on the ones they made later. Harder, and honest -- it is what real prediction has to do. |
"""
            )
        }
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## Where all of this comes from

    **The data** is real. Expansion Therapeutics ran drug-discovery campaigns against
    RNA-mediated diseases -- myotonic dystrophy, ALS, dementia -- and released
    **7,608 molecules** with up to nine ADMET measurements each, under CC-BY-4.0.
    Over 370 teams competed on it in the OpenADMET-ExpansionRx blind challenge.

    **The models** are ours, trained for this notebook on the challenge's own
    **temporal split**: every molecule in the test set was made *after* every
    molecule in the training set.

    > The challenge winner, Inductive Bio's *Beacon*, is proprietary -- no code, no
    > weights. Nothing here reproduces it. We rebuilt the *public* recipe that the
    > published write-ups describe: a Chemprop D-MPNN with CheMeleon initialisation,
    > five seeds, next to gradient-boosted trees on fingerprints.

    Every number in this notebook came out of those runs, on that split. Where a
    result contradicted what we expected, it is still here -- four of them do.
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""## Part 1 -- Nine sockets, one molecule""")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    Pick what kind of drug you are trying to make. Each project accepts a different
    set of property ranges: a brain drug cannot afford to be pumped out at the
    blood-brain barrier, a muscle drug cares about how much stays free in muscle.

    Then pick a molecule, and see whether its nine pegs fit.
    """
    )
    return


@app.cell(hide_code=True)
def _(PRESETS, mo):
    preset_choice = mo.ui.dropdown(
        options=list(PRESETS), value="Brain drug", label="This project is making a"
    )
    return (preset_choice,)


@app.cell(hide_code=True)
def _(EXAMPLES, mo):
    molecule_choice = mo.ui.dropdown(
        options=EXAMPLES, value=list(EXAMPLES)[0], label="Molecule"
    )
    return (molecule_choice,)


@app.cell(hide_code=True)
def _(mo, molecule_choice, preset_choice):
    mo.hstack([preset_choice, molecule_choice], justify="start", gap=2)
    return


@app.cell(hide_code=True)
def _(board_for, mo, molecule_choice, picture, preset_choice):
    _name = molecule_choice.value
    mo.hstack(
        [
            mo.Html(picture(SMILES_OF[_name], 300, 220)),
            mo.Html(board_for(_name, preset_choice.value)),
        ],
        widths=[1, 3],
        align="center",
        gap=1,
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    **How to read it.** The shaded band is what this project will accept. The bar is
    what our model predicts. The pale tip on the bar is how much the five models in
    the ensemble disagreed. The dashed line, where it appears, is the value someone
    actually measured in a lab.

    The gap between the bar and the dashed line is the model being wrong. Keep an
    eye on it -- the rest of this notebook is about when that gap opens up.
    """
    )
    return


@app.cell(hide_code=True)
def _(bundle, mo, pd, survivors):
    _rows = survivors()
    mo.md(
        f"""
    ### How many real molecules actually click?

    Every molecule here was made by a chemist who wanted it to work. Applying each
    project's full requirement list to the model's predictions for all
    **{len(bundle["names"]):,}** of them:

    {mo.ui.table(pd.DataFrame(_rows), selection=None, pagination=False).text}

    Even on the loosest preset most molecules fail something. That is the job:
    not optimising a property, but satisfying all of them at once -- what chemists
    call **whack-a-mole**, because fixing one usually breaks another.

    And there is a second problem hiding in the data.
    """
    )
    return


@app.cell(hide_code=True)
def _(coverage_chart, mo):
    mo.vstack(
        [
            mo.md(
                r"""
    ### The measurements nobody made

    Assays cost money, so cheap ones run on everything and expensive ones run only on
    molecules that already look good. Here is how often each property was measured
    at all:
    """
            ),
            coverage_chart(),
            mo.md(
                r"""
    Muscle binding exists for **4%** of the training molecules. Only **264 of 7,608**
    molecules have all nine.

    This is not random missingness. The molecules that reached the expensive assays
    are the ones that had *already passed* the cheap ones -- so the rare endpoints
    describe a pre-filtered, unusually well-behaved slice of chemistry. Any model
    trained on them inherits that bias, and so does any score you use to judge it.
    """
            ),
        ]
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ---
    ### Appendix -- the code behind this notebook

    The library below is inlined so this file runs anywhere with no repo beside it.
    It is developed and unit-tested separately; see the repository.
    """
    )
    return


@app.cell
def _():
    __LIBRARY__


@app.cell
def _(base64, io, json, np, zlib):
    def _decode(blob: str) -> dict:
        """Unpack what the trained ensemble predicted, inlined at build time."""
        raw = zlib.decompress(base64.b64decode(blob))
        z = np.load(io.BytesIO(raw), allow_pickle=False)
        meta = json.loads(zlib.decompress(z["meta"].tobytes()).decode())
        return {
            "gnn": z["gnn"].astype(np.float32),
            "sd": z["sd"].astype(np.float32),
            "lgbm": z["lgbm"].astype(np.float32),
            **meta,
        }

    BUNDLE_B64 = "__BUNDLE__"
    bundle = _decode(BUNDLE_B64)
    return (bundle,)


@app.cell
def _(bundle, np, pd):
    # The molecules themselves come from the public CC-BY-4.0 release, so only the
    # model's own output has to travel inside this notebook.
    _HF = (
        "https://huggingface.co/datasets/openadmet/"
        "openadmet-expansionrx-challenge-data/resolve/main/"
    )
    _COLS = {
        "Molecule Name": "name", "SMILES": "smiles", "LogD": "LogD", "KSOL": "KSOL",
        "HLM CLint": "HLM", "MLM CLint": "MLM",
        "Caco-2 Permeability Papp A>B": "Papp", "Caco-2 Permeability Efflux": "Efflux",
        "MPPB": "MPPB", "MBPB": "MBPB", "MGMB": "MGMB",
    }

    def _load() -> pd.DataFrame:
        frames = []
        for part, split in (("train", "train"), ("test", "test")):
            df = pd.read_csv(f"{_HF}expansion_data_{part}.csv").rename(columns=_COLS)
            frames.append(df.assign(split=split))
        out = pd.concat(frames, ignore_index=True)
        out["id_num"] = out["name"].str.split("-").str[1].astype(int)
        for ep in bundle["endpoints"]:
            if ep != "LogD":
                out[ep] = np.log10(out[ep] + 1)
        return out.set_index("name").loc[bundle["names"]].reset_index()

    data = _load()
    SMILES_OF = dict(zip(data["name"], data["smiles"]))
    Y = data[bundle["endpoints"]].to_numpy(np.float32)
    return SMILES_OF, Y, data


@app.cell
def _(SMILES_OF, Y, bundle, data, np):
    EPS = bundle["endpoints"]
    IDX = {n: i for i, n in enumerate(bundle["names"])}
    TEST = (data["split"] == "test").to_numpy()

    def pegs_for(name: str):
        """One Peg per endpoint: prediction, ensemble spread, and measurement."""
        i = IDX[name]
        out = []
        for j, ep in enumerate(EPS):
            measured = Y[i, j]
            out.append(
                Peg(
                    endpoint=ep,
                    value=to_real(ep, float(bundle["gnn"][i, j])),
                    sd=float(bundle["sd"][i, j]),
                    measured=None if np.isnan(measured) else to_real(ep, float(measured)),
                )
            )
        return out

    def board_for(name: str, preset: str) -> str:
        return render(PRESETS[preset], pegs_for(name), caption=f'{name} -- "{preset}"')

    return EPS, IDX, TEST, board_for, pegs_for


@app.cell
def _(EPS, IDX, SMILES_OF, bundle, np):
    # A few molecules worth looking at, chosen because each makes a different point.
    EXAMPLES = {
        "E-0016335 -- clicks into almost everything": "E-0016335",
        "E-0002036 -- fails three brain requirements": "E-0002036",
    }

    def _pick_extremes():
        """Add a high-efflux and a low-solubility example, found in the data."""
        eff, ksol = EPS.index("Efflux"), EPS.index("KSOL")
        order = np.argsort(-bundle["gnn"][:, eff])
        for i in order[:40]:
            n = bundle["names"][i]
            if len(SMILES_OF.get(n, "")) < 90:
                EXAMPLES[f"{n} -- pumped straight back out"] = n
                break
        order = np.argsort(bundle["gnn"][:, ksol])
        for i in order[:40]:
            n = bundle["names"][i]
            if len(SMILES_OF.get(n, "")) < 90:
                EXAMPLES[f"{n} -- barely dissolves"] = n
                break

    _pick_extremes()
    EXAMPLES = {k: v for k, v in EXAMPLES.items() if v in IDX}
    return (EXAMPLES,)


@app.cell
def _(EPS, PRESETS, bundle, np):
    def survivors():
        """How many molecules satisfy every requirement of each preset."""
        rows = []
        n_total = len(bundle["names"])
        for preset, socks in PRESETS.items():
            ok = np.ones(n_total, dtype=bool)
            for ep, sock in socks.items():
                col = bundle["gnn"][:, EPS.index(ep)]
                real = np.array([to_real(ep, float(v)) for v in col])
                if sock.lo is not None:
                    ok &= real >= sock.lo
                if sock.hi is not None:
                    ok &= real <= sock.hi
            rows.append(
                {
                    "project": preset,
                    "requirements": len(socks),
                    "molecules that click": int(ok.sum()),
                    "share": f"{100 * ok.mean():.1f}%",
                }
            )
        return rows

    return (survivors,)


@app.cell
def _(EPS, alt, data, pd):
    def coverage_chart():
        rows = []
        for split in ("train", "test"):
            sub = data[data["split"] == split]
            for ep in EPS:
                rows.append(
                    {
                        "endpoint": ep,
                        "split": split,
                        "measured": 100 * sub[ep].notna().mean(),
                    }
                )
        df = pd.DataFrame(rows)
        return (
            alt.Chart(df)
            .mark_bar(cornerRadiusTopRight=4, cornerRadiusBottomRight=4, height=12)
            .encode(
                y=alt.Y("endpoint:N", sort=EPS, title=None),
                x=alt.X("measured:Q", title="% of molecules measured",
                        scale=alt.Scale(domain=[0, 100])),
                color=alt.Color(
                    "split:N",
                    scale=alt.Scale(domain=["train", "test"],
                                    range=["#2a78d6", "#eb6834"]),
                    legend=alt.Legend(title=None, orient="top"),
                ),
                yOffset="split:N",
                tooltip=["endpoint", "split", alt.Tooltip("measured:Q", format=".1f")],
            )
            .properties(height=320, width="container")
        )

    return (coverage_chart,)


if __name__ == "__main__":
    app.run()
