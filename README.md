# Molecular Lego

**Nine properties, one model, nine different problems — and the model cannot tell you which one it is facing.**

An interactive [marimo](https://marimo.io) notebook built on the
[OpenADMET–ExpansionRx](https://huggingface.co/datasets/openadmet/openadmet-expansionrx-challenge-data)
blind-challenge data, for molab Notebook Competition #3.

A drug has to satisfy many properties at once, so the notebook draws each molecule
as a **Lego piece**: one peg per property, and a **socket** holding the ranges a
given project will accept. The piece clicks, or it doesn't. From there it asks the
question it was built for: when a peg comes out the wrong length, is that the
model's fault or the data's?

The answer is different for all nine properties.

## What's in it

| Part | Question |
|---|---|
| 1 | Nine sockets, one molecule — why is this hard? |
| 2 | Where a peg's length comes from (message passing, and two things that didn't work) |
| 3 | A big change is not a surprising change |
| 4 | Should you build a second model? A rule, and a trap |
| 5 | Three ways the data lies (cliffs, censoring, stereochemistry) |
| 6 | Your turn — edit a molecule until it fits |

## Findings

- **Depth pays.** 2 → 4 rounds of message passing cuts test error (0.344 → 0.313);
  4 → 6 barely moves it (0.307). Three seeds each.
- **CheMeleon pretraining did not.** 0.315 ± 0.007 vs 0.307 ± 0.004 from random
  init at the same depth — no measurable gain at this dataset size.
- **Multitask sharing did not, and hurt one endpoint.** Brain protein binding was
  **16% worse** in a nine-headed model than in its own (0.192 vs 0.165,
  non-overlapping seed ranges): negative transfer.
- **A rule for when to ensemble.** For error SDs σ₁ ≤ σ₂ and error correlation ρ,
  blending helps iff **ρ < σ₁/σ₂**, with optimal weight
  `w* = (σ₂² − ρσ₁σ₂) / (σ₁² + σ₂² − 2ρσ₁σ₂)`. It predicted the right weight on
  **all nine** endpoints.
- **…that you often cannot use.** Estimating ρ and σ honestly on validation data,
  the rule gains +4.2% on permeability but **loses** 1.7–2.5% on brain and muscle
  binding, where only 45–81 validation molecules exist. Not too little data to fit
  a model — too little to decide *how* to fit it.
- **Volatility ≠ surprise.** One-atom edits move LogD ≥10× on **32.6%** of matched
  pairs yet the model is barely caught out (error ratio 1.19). Efflux moves on
  **4.6%** and blindsides it (2.79).
- **The labels lie in three ways.** A solubility ceiling that improves MAE while
  collapsing ranking; 265 of the *most metabolically stable* compounds silently
  dropped from the "ML-ready" file as `< 4.5`; 129 stereoisomer groups the 2D graph
  cannot distinguish.

Four claims we planned to make were abandoned when the data contradicted them,
including the original thesis. Those refutations are kept in the notebook.

## Repository

```
lego/          unit-tested library, inlined into the notebook at build time
  board.py       the socket-and-peg SVG
  sockets.py     property windows and project presets
  edits.py       seven medicinal-chemistry edits as reaction SMARTS
  pairs.py       matched-molecular-pair finder
  draw.py        molecule rendering, atom tinting, receptive fields
  surrogate.py   the fast stand-in fitted inside the notebook
  units.py       model space <-> real units
  interaction.py the clearly-labelled drug-interaction simulation
train/         data prep, training, ablations, evidence
tests/         56 unit tests
notebook_src.py   the notebook, with placeholders
build_notebook.py assembles the single self-contained notebook.py
check_notebook.sh builds it and executes every cell headlessly
```

## Build and verify

```bash
uv venv --python 3.12 .venv
uv pip install --python .venv marimo rdkit pandas numpy scikit-learn lightgbm \
  "chemprop>=2.2" torch altair pyarrow pytest scipy

.venv/bin/python -m pytest tests/ -q     # 56 tests
./check_notebook.sh                      # build + execute every cell
.venv/bin/python -m marimo edit notebook.py
```

Reproducing the models from scratch (about two hours on one RTX A5000):

```bash
.venv/bin/python train/prep.py            # standardize, temporal split
.venv/bin/python train/train_lgbm.py      # tree baseline
.venv/bin/chemprop train -i data/prepared.csv -s smiles \
  --target-columns LogD KSOL HLM MLM Papp Efflux MPPB MBPB MGMB \
  --splits-column split --from-foundation CHEMELEON \
  --epochs 100 --patience 20 --ensemble-size 5 -o runs/ens
.venv/bin/python train/predict_ens.py
.venv/bin/python train/ablate2.py         # depth / pretraining / multitask
.venv/bin/python train/evidence.py        # -> evidence_report.md
.venv/bin/python train/bundle.py          # -> artifacts/bundle.b64
```

## Why the notebook is one file

molab runs a single `.py` with no repository beside it, and the trained models are
36 MB per ensemble member. So `build_notebook.py` inlines the `lego/` library and a
460 KiB compressed record of **what the ensemble predicted** for all 7,608
molecules. The notebook refits a fast stand-in from those predictions in about 20
seconds (agreement with the teacher: R² 0.87), which is what makes live prediction
on an edited molecule possible. The molecules themselves are fetched at run time
from the public CC-BY-4.0 release.

Two marimo rules shaped the build: exactly one cell may define a given name, and
top-level names starting with `_` are cell-local — so every import and library
symbol lives in one cell, and private helpers are renamed `lg_*` at build time.

## Data and licence

Data: OpenADMET–ExpansionRx Blind Challenge full release, courtesy of Expansion
Therapeutics, **CC-BY-4.0**. Code in this repository: MIT.

The challenge winner (Inductive Bio's *Beacon*) is proprietary and is **not**
reproduced here; this rebuilds the public recipe described in the published
write-ups, and accuracy is not the point.

## AI use

Built in collaboration with Claude (Anthropic) as a coding agent: it wrote most of
the code, ran the training and analysis, and drafted the prose. Direction, the
choice of question, and every keep-or-cut decision were mine. The notebook's
disclosure section records the two things worth knowing — the four abandoned
claims, and the one finding that was nearly published before turning out to be an
empty-batch NaN artefact.

— Suyash Bhagat ([@Suyashkb](https://github.com/Suyashkb))
