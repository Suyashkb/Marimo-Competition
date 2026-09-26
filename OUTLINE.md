# Molecular Lego — locked chapter list and narrative

> **Subtitle:** One molecule has to click into nine sockets at once. Watch a graph model try.

**Thesis (the banner, one sentence):**
> Nine properties, one model, **nine different problems** — and the model cannot tell you which one it is facing.

Everything in the notebook is evidence for that one sentence. Nothing else goes in.

**Why this thesis:** it is ours, derived from our own runs on the temporal test split, and it explains results other write-ups reported as contradictory (does blending help? sometimes — here is exactly when, and why).

> ### Thesis revision (2026-09-26) — the first draft was wrong
> The locked v1 thesis was "every property is either **global** (whole-molecule average) or **local** (one site decides)". Two independent checks refuted it:
> 1. **Atom-masking attributions do not separate the endpoints.** Contribution concentration (top-1 atom's share of total, normalised): KSOL **3.92**, HLM 3.23, LogD 3.02, Efflux 2.68, MLM **2.45**, Papp 2.40. "Global" KSOL is the *most* concentrated and "local" MLM among the least. The predicted ordering simply is not there.
> 2. **One-atom edits move LogD the most, not least.** P(|Δ| ≥ 1 log unit) over 20,048 one-heavy-atom matched pairs: LogD **0.326**, KSOL 0.197, HLM 0.103, MLM 0.097, Efflux **0.046**.
>
> Both failures point somewhere better, so the distinction is kept but **redefined** (Part 3). The refutation is not buried: it is Part 3's opening move, and the abandoned hypothesis is shown as an abandoned hypothesis.

---

## The visual language (fixed, defined once, never changed)

| Element | Means |
|---|---|
| **Socket** | the acceptable range for one endpoint, in real units |
| **Peg height** | the model's predicted value |
| **Peg blur** | disagreement across the 5-model ensemble |
| **Ghost peg** | the *measured* value, where one exists. Gap peg↔ghost = error |
| **Click** | every required socket satisfied |
| **Grey socket** | not required by this project preset |

---

## Prologue — How to read a Lego piece
One worked molecule (`E-0016335`), every visual element labelled, nothing asked of the reader yet.
Plus: a **glossary** panel (SMILES, LogD, clearance, efflux, message passing…) and a **"you are here"** map of the six parts.

---

## Part 1 — The puzzle: nine sockets, one molecule
**Question:** Why is finding a drug hard when each individual property looks easy?

**Interaction:** pick a project preset (Oral / Brain / Muscle / Everything at once). Sliders per socket. A live counter: how many of the 7,608 real compounds click?

**Evidence:** only **264 of 7,608** molecules have all nine endpoints measured at all. The assay funnel: LogD ~95% measured, muscle binding **4%**.

**Takeaway:** **Chemists aren't optimizing a property. They're solving a simultaneous-fit problem — and they can't even afford to measure most of it.**

Panels: *For chemists* — the assay cascade and why cheap assays run first. *For ML engineers* — a sparse multitask label matrix, missing-not-at-random.

---

## Part 2 — The peg-maker: how a graph model builds a prediction
**Question:** Where does a peg's height actually come from?

**Interaction:**
1. **Message-passing slider (0→5 rounds).** Pick an atom; watch its highlighted "view" spread across the molecule, one bond per round. Pure RDKit, no model needed — the mechanism made visible.
2. Then the cost of getting it wrong: **test error vs depth** (needs ablation, see TODO).
3. **Single-task vs multitask toggle** → the muscle-binding peg sharpens.

**Evidence — and what it does and does not show:**
- ✅ **Family comparison:** the GNN ensemble beats LightGBM on **9/9** endpoints, mean MAE **0.288 vs 0.335**. This says the graph family wins. It says **nothing about why** — depth, multitask sharing and CheMeleon pretraining are all confounded in that one number. An earlier draft of this outline treated it as proof of the mechanism; it is not.
- ⏳ **Mechanism (pending `ablate2.py`):** depth sweep at scratch init, CheMeleon vs scratch, and single-task vs multitask at 3 seeds each. The first attempt was invalid (`--depth` is silently ignored under `--from-foundation`, so all five "depth" models were identical; and one seed cannot resolve effects when seed noise reaches 23%).
- 🔎 **Lead under test:** single-task MGMB (177 training values) **diverged to NaN weights** while the multitask model predicts it at MAE 0.179. If it reproduces across seeds, the claim becomes "single-task does not work at all here", which is far stronger than any percentage.

**Any mechanism claim in this part must cite `ablate2.py` with seed error bars, or be cut.** The free receptive-field visual stays regardless: it teaches the mechanism without asserting a performance claim.

**Takeaway (if the ablation supports it):** **A graph model invents its own features by letting atoms talk to their neighbours — and sharing one body across nine properties is what makes the rarest ones trainable at all.**

---

## Part 3 — The hinge: a big change is not the same as a surprising change
**Question:** Which properties are hard to predict, and can the model tell us?

**3a. A hypothesis, and its refutation (kept in the notebook).**
We expected "local" properties (one site decides) to behave differently from "global" ones (whole-molecule average). Two ways of testing it both came out wrong — shown as two small charts the reader can inspect (numbers in the revision box above). *This is a feature:* the reader watches a plausible idea die, which is how the work actually went.

**3b. What the data says instead.** Two axes that turn out to be different things:
- **Volatility** — how often one small edit moves the value at all.
- **Surprise** — how much bigger the model's error is on pairs that *did* move ≥1 log unit, versus pairs that barely moved.

| Endpoint | Volatility P(\|Δ\|≥1) | Surprise (cliff MAE / flat MAE) | n cliff cases |
|---|---|---|---|
| **LogD** | **0.326** | **1.19** | 4,129 |
| KSOL | 0.197 | 1.96 | 2,119 |
| HLM | 0.103 | 2.39 | 184 |
| MLM | 0.097 | 1.70 | 327 |
| Papp | 0.017 | 1.40 | 114 |
| **Efflux** | **0.046** | **2.79** | 748 |

**Interaction:** a 2-axis scatter (volatility vs surprise), each endpoint a dot, click one to see its matched pairs.

**The worked contrast** (both well-powered; presented as two examples, *not* as a law across all nine):
- **LogD** moves on a third of all one-atom edits, and the model sees it coming. Lipophilicity is close to additive: each group contributes a roughly fixed increment, which is learnable.
- **Efflux** moves on one edit in twenty, but when it does the model is blindsided. A pump either recognizes the molecule or it doesn't — a threshold, not a sum.

**Honesty note in the notebook:** across only 9 endpoints the volatility↔surprise relationship is suggestive, not significant (Pearson −0.47, Spearman −0.26, n=6 with enough cliff cases). The notebook states this and rests the chapter on the two named examples.

**Takeaway:** **The properties that move most are not the ones that catch a model out. "Hard to predict" and "sensitive to structure" are different things.**

Panels: *For chemists* — additive lipophilicity (Crippen fragments) vs P-gp recognition and CYP soft spots. *For ML engineers* — smooth vs threshold-like structure-property functions, and why error-on-cliffs is the diagnostic, not variance.

---

## Part 4 — Does a second model help? A rule, and a trap
**Question:** Everyone ensembles. When is it actually worth it?

**4a. The rule.** Blend the graph model with a gradient-boosted tree model. For error SDs σ₁ ≤ σ₂ and error correlation ρ:
> blending helps **iff ρ < σ₁/σ₂**, with optimal weight w\* = (σ₂² − ρσ₁σ₂)/(σ₁² + σ₂² − 2ρσ₁σ₂)

**Interaction:** a blend-weight slider with the error curve; the theoretical w\* marked. Verified against the empirical optimum on **all 9 endpoints**:

| | HLM | MLM | Papp | LogD | Efflux | MBPB | MGMB |
|---|---|---|---|---|---|---|---|
| w\* theory | 0.55 | 0.51 | 0.60 | 0.82 | 0.65 | 1.03 | 1.03 |
| w empirical | 0.59 | 0.53 | 0.51 | 0.73 | 0.68 | 1.00 | 1.00 |

And the gains land on the **local** properties: HLM +3.4%, MLM +4.8%, Papp +4.2%; protein binding **0%**.

**4b. The trap.** w\* needs ρ and σ estimated from held-out data. Fit them on **validation only**, apply to test:

| Papp (n=97) | HLM (22) | MLM (380) | LogD (532) | MPPB (81) | **MBPB (81)** | **MGMB (45)** |
|---|---|---|---|---|---|---|
| +4.2% | +2.7% | +2.6% | +1.8% | 0.0% | **−1.7%** | **−2.5%** |

**Takeaway:** **The theory tells you exactly when a second model pays. But using it means estimating two numbers — and on the endpoints that need help most, there isn't enough data to estimate them. Blending there makes things worse.**

This is the notebook's answer to *"is it the model's fault or the data's?"* — the data's, one level up from where people look.

---

## Part 5 — Three ways the data itself lies
Same illustration, now showing failure. One short chapter each.

**5a. Cliffs — you versus the model.**
*Interaction:* **Minesweeper.** A grid of matched pairs differing by one atom, the change highlighted. Click the pairs you think jump 10×. Then reveal — and compare your score with the model's.
*Evidence:* surprise ratios from Part 3 (Efflux 2.79, HLM 2.39, KSOL 1.96, MLM 1.70, LogD 1.19), from **37,210 matched pairs** found by our own fragment-and-index code (21,026 differing by ≤1 heavy atom).
*The point:* a reader who has internalised Part 3 should beat the model on Efflux pairs by using chemical reasoning the model has no access to.

**5b. The ceiling that lies.**
*Interaction:* **drag the assay ceiling line** down over the solubility data and watch MAE *improve* while ranking collapses.
*Evidence:* by solubility band, MAE 0.574 → 0.235 while Spearman **0.49 → 0.10**. Plus: **265 of the most metabolically stable compounds** were silently dropped from the "ML-ready" file as `< 4.5` values.

**5b-bis. The model can't tell you which regime it's in.**
*Evidence:* the refuted atom-masking probe from 3a, revisited. Attribution concentration does not correlate with either volatility or surprise, so a practitioner cannot read "is this endpoint cliffy?" off the model's own explanations — only off the measured data.
*Why it belongs here:* it is the sharpest form of the thesis. One short screen, no interaction.

**5c. Blind to 3D.**
*Evidence:* **548** groups share a 2D skeleton; **129** differ by ≥0.5 log units in a measured value. The graph model gives them identical pegs.
Kept short — one example pair, one sentence of theory.

**Takeaway:** **Three times over, the number on the page is not the number you think it is.**

---

## Part 6 — Your turn
**6a. The puzzle.** A compound that fails the Brain-drug socket. Seven real med-chem edits available (H→F, +CH₃, →Cl, →OH, ring CH→N, CH₃→CF₃, chain CH₂→O). Edit until it clicks.
**The reality check:** after each edit, show **real matched pairs from the dataset that made the same edit** and what actually happened. Sometimes the model is right; sometimes it walks into a cliff from 5a.

**6b. Drift.** A "today" slider over compound IDs: train on the past, colour the next batch by error. Watch the chemists move into new chemistry.
*Evidence:* efflux median **1.34 → 4.99** early to late, model under-predicts by −0.22 log units; solubility fixed (112 → 249 µM) while permeability broke (10.2 → 3.2). Whack-a-mole, visible.

**6c. ⚠ SIMULATION — a second drug in the room.** Clearly boxed. Invent an enzyme inhibitor with sliders; the textbook static model turns predicted clearance into a predicted exposure rise; the clearance peg lengthens out of its socket. States plainly: **clearance is ours, the inhibitor is invented, no interaction data exists in this dataset**, and names where real data (the OpenADMET CYP challenge) would plug in.

---

## Epilogue
What we would do next; **AI-use disclosure**; data licence and attribution (ExpansionRx, CC-BY-4.0); links to every source; the repo.

---

## Chapter budget
Six parts, twelve screens. If time runs short, cut in this order:
1. **5c (3D)** — one paragraph, easily dropped
2. **2's depth ablation** — keep the free receptive-field visual, drop the numbers
3. **6b (drift)** — fold its two numbers into Part 1

Never cut: Part 3 (the hinge), Part 4 (the original finding), 5a and 5b.

## TODO — evidence still to generate
- [ ] Depth ablation (depth 0–5), for Part 2. ~6 runs × 3 min.
- [ ] Single-task vs multitask, 9 models, for Part 2. ~30 min.
- [ ] Atom-contribution values (mask one atom, re-predict) for Parts 3 and 5a.
- [ ] Per-atom "view" highlighting for the message-passing slider (RDKit only).
- [ ] Curated puzzle molecule + its matched-pair partners for Part 6a.

## Non-goals
- Not beating a leaderboard. Accuracy is evidence, never the point.
- No reproduction of Inductive Bio's proprietary winner. The notebook says plainly that the top entry is closed, and that we rebuild the *public* recipe (Chemprop + CheMeleon + trees).
- No claim without a number from our own run on the temporal test split.
