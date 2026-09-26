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
    ## Part 2 -- Where a peg's length comes from

    A molecule is a graph: atoms are nodes, bonds are edges. The model works by
    letting every atom **send a message to its neighbours**, over and over. After one
    round an atom knows about the atoms next to it. After three, about everything
    within three bonds.

    Drag the slider to watch one atom's view spread.
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    rounds = mo.ui.slider(0, 5, value=2, label="Rounds of message passing", show_value=True)
    return (rounds,)


@app.cell(hide_code=True)
def _(highlight, mo, n_atoms, neighborhood, rounds):
    _smi = "Cc1ccc(C(=O)Nc2ccc(OC)cc2)cc1"
    _seen = neighborhood(_smi, 0, rounds.value)
    mo.vstack(
        [
            rounds,
            mo.hstack(
                [
                    mo.Html(highlight(_smi, _seen, 420, 250)),
                    mo.md(
                        f"""
    After **{rounds.value}** round{"" if rounds.value == 1 else "s"}, the highlighted
    atom has heard from **{len(_seen)} of {n_atoms(_smi)}** atoms.

    This is the model's receptive field. Nothing outside it can affect what this
    atom contributes. Pool every atom's final vector and you get one vector for the
    whole molecule -- and from that, nine numbers.
    """
                    ),
                ],
                widths=[1, 1],
                align="center",
            ),
        ]
    )
    return


@app.cell(hide_code=True)
def _(ABLATION, alt, mo, pd):
    _df = pd.DataFrame(ABLATION["depth"])
    _chart = (
        alt.Chart(_df)
        .mark_line(point=alt.OverlayMarkDef(size=90), strokeWidth=2, color="#2a78d6")
        .encode(
            x=alt.X("depth:O", title="rounds of message passing"),
            y=alt.Y("mae:Q", title="test error (MAE, lower is better)",
                    scale=alt.Scale(zero=False)),
            tooltip=["depth", alt.Tooltip("mae:Q", format=".3f")],
        )
        .properties(height=230, width="container")
    )
    _err = (
        alt.Chart(_df)
        .mark_errorbar(color="#2a78d6")
        .encode(
            x="depth:O",
            y=alt.Y("lo:Q", title=""),
            y2="hi:Q",
        )
    )
    mo.vstack(
        [
            mo.md(
                r"""
    ### Does seeing further actually help?

    We trained the same model at different depths, three random seeds each, and
    scored every one on molecules made *later* than anything it saw:
    """
            ),
            _chart + _err,
            mo.md(
                r"""
    Yes -- and it **flattens out**. Going from 2 rounds to 4 buys a lot; 4 to 6 buys
    almost nothing. Most of what predicts these properties lives within a few bonds.

    That is the one tuning knob in this notebook that reliably pays. The next two
    are the ones everybody recommends, and neither survived contact with our data.
    """
            ),
        ]
    )
    return


@app.cell(hide_code=True)
def _(ABLATION, mo):
    _p = ABLATION["pretrain"]
    _m = ABLATION["multitask"]
    mo.md(
        f"""
    ### Two things that did not work

    **Pretraining bought nothing.** CheMeleon is a foundation model pretrained on a
    million molecules, and every published write-up of this challenge names
    pretraining as a key ingredient. Starting from it, versus starting from random
    weights at the same depth:

    | | test error (MAE) |
    |---|---|
    | CheMeleon initialisation | {_p["chemeleon"]:.3f} ± {_p["chemeleon_sd"]:.3f} |
    | Random initialisation | **{_p["scratch"]:.3f} ± {_p["scratch_sd"]:.3f}** |

    No measurable benefit here. That is not a refutation of the method -- CheMeleon's
    own paper claims the advantage is largest on *small* datasets, and 7,608
    molecules is not small. It is a warning that "use a foundation model" is not
    free advice.

    **Sharing all nine properties hurt.** The appeal of one model with nine heads is
    that rare properties borrow strength from common ones. Measured, three seeds each:

    | endpoint | training values | own model | shared model | |
    |---|---|---|---|---|
    | LogD | 5,039 | {_m["LogD"][0]:.3f} | {_m["LogD"][1]:.3f} | no difference |
    | Papp | 2,157 | {_m["Papp"][0]:.3f} | {_m["Papp"][1]:.3f} | no difference |
    | **MBPB** | **975** | **{_m["MBPB"][0]:.3f}** | **{_m["MBPB"][1]:.3f}** | **16% worse shared** |
    | MGMB | 177 | {_m["MGMB"][0]:.3f} | {_m["MGMB"][1]:.3f} | no difference |

    Brain binding got *worse* by sharing, and the seed ranges do not overlap. This is
    **negative transfer**: nine properties pulling one set of weights in nine
    directions. It is exactly why the leading teams grouped related endpoints instead
    of lumping all of them together -- we failed where they took care.
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.accordion(
        {
            "A trap that nearly fooled us (worth two minutes)": mo.md(
                r"""
When we first trained one model per endpoint, every run on the rarest property
produced **NaN weights** and predicted nothing. Three seeds, same result. The
obvious story wrote itself: *177 training values is too few, the model cannot
learn at all.*

That story was wrong, and the giveaway was in the log: the loss was NaN at
**step 49 of the first epoch** -- instantly, not after drifting. Real divergence
creeps. This snapped.

The cause: the training file has one row per molecule and a column per property.
For muscle binding, **4,616 of 4,793 rows are empty**. With a batch size of 64,
most batches contained *zero* labelled molecules, so the loss averaged over an
empty set, produced NaN, and poisoned the weights forever.

Filter to labelled rows first and the same model trains fine (MAE 0.201 ± 0.004).

If you take one practical thing from this notebook: **a masked multitask loss on a
sparse label matrix can silently produce NaN**, and it looks exactly like a
scientific finding about small data.
"""
            )
        }
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ---
    ## Part 3 -- A big change is not a surprising change

    Here is the question that organises everything after it: **which properties are
    hard to predict, and why?**

    We had a hypothesis, and it was wrong. It is worth showing, because the way it
    failed points at the real answer.
    """
    )
    return


@app.cell(hide_code=True)
def _(REFUTED, mo, pd):
    mo.accordion(
        {
            "Our first hypothesis, and how the data killed it": mo.vstack(
                [
                    mo.md(
                        r"""
We expected properties to split into two kinds. **Global** ones like greasiness
would be a sum over the whole molecule -- smooth, easy. **Local** ones like liver
clearance would hinge on a single site the enzyme attacks -- jumpy, hard.

Two tests, both of which should have shown that split:

**Test 1 -- ask the model.** Mask one atom at a time, re-predict, and measure how
concentrated the contributions are. Local properties should concentrate in a few
atoms.
"""
                    ),
                    mo.ui.table(
                        pd.DataFrame(REFUTED["concentration"]),
                        selection=None,
                        pagination=False,
                    ),
                    mo.md(
                        r"""
Solubility -- supposedly global -- is the *most* concentrated. Mouse clearance,
supposedly local, is near the bottom. The ordering is not there.

**Test 2 -- ask the data.** Take 20,048 pairs of molecules differing by a single
heavy atom, and ask how often that one change moves the value by 10x or more:

| LogD | KSOL | HLM | MLM | Efflux |
|---|---|---|---|---|
| **32.5%** | 19.7% | 10.3% | 9.7% | **4.6%** |

LogD -- the property we called smooth -- moves on a **third** of all one-atom
edits. Efflux, the one we called jumpy, moves on one in twenty. The hypothesis is
backwards.
"""
                    ),
                ]
            )
        }
    )
    return


@app.cell(hide_code=True)
def _(alt, mo, pd, surprise_table):
    _df = pd.DataFrame(surprise_table())
    _pts = (
        alt.Chart(_df)
        .mark_circle(size=170, opacity=0.9, color="#2a78d6")
        .encode(
            x=alt.X("volatility:Q", title="how often one atom moves it 10x or more",
                    axis=alt.Axis(format="%")),
            y=alt.Y("surprise:Q", title="how much those moves surprise the model",
                    scale=alt.Scale(zero=False)),
            tooltip=[
                "endpoint",
                alt.Tooltip("volatility:Q", format=".1%"),
                alt.Tooltip("surprise:Q", format=".2f"),
                alt.Tooltip("n_cliff:Q", title="cases"),
            ],
        )
    )
    _labels = _pts.mark_text(dx=9, dy=-9, align="left", fontSize=12).encode(
        text="endpoint:N", color=alt.value("#52514e")
    )
    mo.vstack(
        [
            mo.md(
                r"""
    ### What is actually going on

    Two different things were tangled together:

    - **Volatility** -- how often a one-atom change moves the value at all.
    - **Surprise** -- how much *worse* the model does on the pairs that did move,
      compared with pairs that barely moved.

    They are not the same axis:
    """
            ),
            (_pts + _labels).properties(height=300, width="container"),
            mo.md(
                r"""
    **LogD, top left: moves constantly, surprises nobody.** Greasiness is close to
    additive -- each chemical group contributes a roughly fixed increment. That is
    precisely how hand-built LogP calculators have worked since the 1970s, and a
    model learns it easily. Big changes, all of them predictable.

    **Efflux, bottom right: moves rarely, blindsides the model.** Whether a cell's
    pump grabs a molecule is closer to a threshold than a sum: below the line
    nothing happens, above it the molecule is thrown out. The model, fitting a
    smooth function, has no way to see the edge coming.

    > **Honesty note.** With only nine endpoints this is suggestive, not
    > statistically significant (Pearson −0.47, Spearman −0.26 over the six with
    > enough cases). The claim rests on the two labelled examples, which are
    > well-powered -- 4,129 and 748 cases -- not on a fitted trend.

    **The takeaway:** *"sensitive to structure"* and *"hard to predict"* are
    different properties of a property. Everything in Part 5 follows from this.
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
    ## Part 4 -- Should you build a second model?

    Everyone ensembles. Average a graph network with gradient-boosted trees on
    fingerprints and you usually do a bit better. But *how much* better, and is it
    worth the second model at all?

    There is a clean answer, and you can work it out **before training anything**.

    Let the better model have error standard deviation σ₁, the worse one σ₂, and let
    their errors correlate at ρ. The best possible weighted blend puts weight

    $$w^* = \frac{\sigma_2^2 - \rho\,\sigma_1\sigma_2}{\sigma_1^2 + \sigma_2^2 - 2\rho\,\sigma_1\sigma_2}$$

    on the better model -- and blending helps **only when ρ < σ₁/σ₂**.

    The intuition is the Lego one: two slightly wrong pegs average into a better peg
    only if they are wrong in *different directions*. If both models make the same
    mistakes (ρ high), averaging just reproduces the mistake.

    Pick an endpoint and see whether it holds.
    """
    )
    return


@app.cell(hide_code=True)
def _(EPS, mo):
    blend_ep = mo.ui.dropdown(options=EPS, value="HLM", label="Endpoint")
    return (blend_ep,)


@app.cell(hide_code=True)
def _(alt, blend_curve, blend_ep, mo, pd):
    _c = blend_curve(blend_ep.value)
    _df = pd.DataFrame(_c["curve"])
    _line = (
        alt.Chart(_df)
        .mark_line(strokeWidth=2.5, color="#2a78d6")
        .encode(
            x=alt.X("w:Q", title="weight on the graph model  (0 = trees only, 1 = graph only)"),
            y=alt.Y("rmse:Q", title="test error (RMSE)", scale=alt.Scale(zero=False)),
            tooltip=[alt.Tooltip("w:Q", format=".2f"), alt.Tooltip("rmse:Q", format=".4f")],
        )
    )
    _pred = (
        alt.Chart(pd.DataFrame([{"w": _c["w_star"]}]))
        .mark_rule(strokeWidth=2, strokeDash=[5, 3], color="#eb6834")
        .encode(x="w:Q")
    )
    mo.vstack(
        [
            blend_ep,
            (_line + _pred).properties(height=260, width="container"),
            mo.md(
                f"""
    Solid line: what every blend weight actually scores. Dashed line: where the
    formula said the best weight would be, **using only the errors correlation and
    the two error sizes**.

    | | |
    |---|---|
    | error correlation ρ | **{_c["rho"]:.3f}** |
    | σ₁/σ₂ (graph vs trees) | **{_c["ratio"]:.3f}** |
    | formula predicts | blending {"**helps**" if _c["rho"] < _c["ratio"] else "**does not help**"} |
    | best weight, predicted | {_c["w_star"]:.2f} |
    | best weight, measured | {_c["w_emp"]:.2f} |
    | error reduction at best weight | {_c["gain"]:.1f}% |

    Try all nine. The dashed line lands on the bottom of the curve every time.
    """
            ),
        ]
    )
    return


@app.cell(hide_code=True)
def _(HONEST_BLEND, mo, pd):
    mo.vstack(
        [
            mo.md(
                r"""
    ### The catch

    That worked because we computed ρ and σ **on the test set** -- the answers we
    were trying to predict. Nobody gets to do that.

    So do it honestly: estimate ρ and σ on a validation set of earlier molecules,
    pick the weight from the formula, then apply it to the later molecules and see
    what you actually gained.
    """
            ),
            mo.ui.table(pd.DataFrame(HONEST_BLEND), selection=None, pagination=False),
            mo.md(
                r"""
    On the endpoints with plenty of validation data, the formula delivers: **+4.2%**
    on permeability, **+2.7%** on human clearance.

    On brain and muscle binding it **loses**. Not "helps less" -- actively makes the
    model worse. With 45 to 81 validation molecules you cannot estimate a correlation
    well enough to choose a weight, so you choose a bad one.

    Look back at Part 1 and you can see why those two are short of data: they are the
    expensive assays, the ones that only ran on molecules that had already passed
    everything else.

    > **The result:** the theory tells you exactly when a second model pays. Using it
    > requires estimating two numbers from held-out data. On the endpoints that most
    > need help, there is not enough held-out data to estimate them -- so the
    > technique fails precisely where you wanted it.

    That is this notebook's answer to *"is it the model's fault or the data's?"* It
    is the data's, one level up from where people usually look: not too little data
    to *fit* a model, too little to *decide how* to fit it.
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
    ## Part 5 -- Three ways the data lies

    Everything so far assumed the measurements mean what they say. They don't
    always. Three cases, each with a different culprit.
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ### 5a. Cliffs -- you versus the model

    Below are pairs of molecules differing by **one small change**, highlighted in
    green. For each pair, guess: does this one change move efflux by **10x or more**?

    Part 3 gives you an edge the model does not have. Efflux is a recognition
    threshold -- adding bulk, charge, or a hydrogen-bond donor can flip a pump from
    ignoring a molecule to grabbing it. Look for changes that alter *what the pump
    sees*, not just size.
    """
    )
    return


@app.cell(hide_code=True)
def _(mo, quiz_pairs):
    guesses = mo.ui.array(
        [mo.ui.switch(label="10x jump") for _ in quiz_pairs],
    )
    return (guesses,)


@app.cell(hide_code=True)
def _(changed_atoms, guesses, highlight, mo, quiz_pairs):
    def _card(i, p):
        _, changed_b = changed_atoms(p["smiles_a"], p["smiles_b"])
        return mo.vstack(
            [
                mo.md(f"**Pair {i + 1}**"),
                mo.Html(highlight(p["smiles_a"], [], 230, 140)),
                mo.Html(highlight(p["smiles_b"], changed_b, 230, 140)),
                guesses[i],
            ],
            align="center",
        )

    mo.hstack(
        [_card(i, p) for i, p in enumerate(quiz_pairs)],
        widths="equal",
        gap=1,
    )
    return


@app.cell(hide_code=True)
def _(guesses, mo, quiz_pairs):
    _you = sum(
        1
        for i, p in enumerate(quiz_pairs)
        if bool(guesses.value[i]) == p["is_cliff"]
    )
    _model = sum(1 for p in quiz_pairs if p["model_says_cliff"] == p["is_cliff"])
    _rows = "\n".join(
        f"| {i + 1} | {'10x jump' if p['is_cliff'] else 'barely moved'} "
        f"| {'yes' if guesses.value[i] else 'no'} "
        f"| {'yes' if p['model_says_cliff'] else 'no'} |"
        for i, p in enumerate(quiz_pairs)
    )
    mo.md(
        f"""
    #### Results

    | pair | what really happened | you said | the model said |
    |---|---|---|---|
    {_rows}

    **You: {_you}/{len(quiz_pairs)} — the model: {_model}/{len(quiz_pairs)}.**

    Flip the switches and the score updates. The point is not the score: it is that
    a person reasoning about *mechanism* can beat a model reasoning about
    *similarity*, on exactly the pairs where similarity is misleading.

    Across the whole test set, model error on 10x-jump pairs versus near-identical
    pairs: **efflux 2.8x worse, human clearance 2.4x, mouse clearance 1.7x — but
    LogD only 1.2x.** The model is not uniformly blind. It is blind in the places
    Part 3 predicted.
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ### 5b. The ceiling that lies

    A solubility assay cannot see past its top concentration. Anything more soluble
    than that comes back as the same number.

    Drag the ceiling down and watch two things move in **opposite** directions.
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    ceiling = mo.ui.slider(
        50, 350, value=350, step=25, label="Assay ceiling (uM)", show_value=True
    )
    return (ceiling,)


@app.cell(hide_code=True)
def _(alt, ceiling, ceiling_effect, mo, pd):
    _e = ceiling_effect(ceiling.value)
    _df = pd.DataFrame(_e["points"])
    _scatter = (
        alt.Chart(_df)
        .mark_circle(size=22, opacity=0.35, color="#2a78d6")
        .encode(
            x=alt.X("measured:Q", title="measured solubility (log scale)"),
            y=alt.Y("predicted:Q", title="predicted"),
            tooltip=[alt.Tooltip("measured:Q", format=".2f"),
                     alt.Tooltip("predicted:Q", format=".2f")],
        )
        .properties(height=280, width="container")
    )
    mo.vstack(
        [
            ceiling,
            _scatter,
            mo.md(
                f"""
    | | |
    |---|---|
    | average error (MAE) | **{_e["mae"]:.3f}** {"-- better" if _e["mae"] < _e["mae_full"] else ""} |
    | ranking ability (Spearman) | **{_e["rho"]:.3f}** {"-- worse" if _e["rho"] < _e["rho_full"] else ""} |
    | molecules stuck at the ceiling | {_e["at_ceiling"]:.0%} |

    Lower the ceiling and the **error improves while the ranking collapses**. The
    model looks more accurate and becomes less useful, because a chemist does not
    want a number -- they want to know which molecule to make next.

    In the real data, **51%** of molecules sit at or above 200 uM, and by the top
    band Spearman falls to **0.10** while MAE *improves* to 0.235. A model scoring
    well on this endpoint may have learned nothing but where the lid is.

    There is a second, quieter version of the same problem. The published
    "ML-ready" file drops every out-of-range measurement -- including **265
    compounds** recorded as `< 4.5` on human clearance. Those are the *most
    metabolically stable molecules in the set*, the ones a chemist most wants. The
    clean file is missing its best examples, and nothing in it says so.
    """
            ),
        ]
    )
    return


@app.cell(hide_code=True)
def _(mo, stereo_example):
    _s = stereo_example()
    mo.vstack(
        [
            mo.md(
                r"""
    ### 5c. Two molecules the model cannot tell apart

    The model reads a molecule as a 2D graph: which atoms, which bonds. Mirror-image
    molecules have identical graphs and different shapes in space -- and biology is
    made of shapes.
    """
            ),
            mo.hstack(_s["pictures"], widths="equal", align="center"),
            mo.md(_s["caption"]),
        ]
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ### 5d. And the model cannot tell you which of these you are in

    The obvious move is to ask the model where it is unsure, or which atoms it is
    using. We tried both.

    - **Atom attributions** (Part 3) do not line up with either volatility or
      surprise. Concentration of attribution is highest for solubility, which is
      neither the jumpiest nor the most surprising endpoint.
    - **Ensemble disagreement** tracks error on only **5 of 9** endpoints, and
      barely at all on LogD (ρ = 0.06) and permeability (ρ = 0.03).

    So the pale tip on the pegs at the top of this notebook is real information for
    solubility and efflux, and close to decoration for LogD.

    **Which is the whole thesis.** Nine properties, one model, nine different
    problems -- and the model cannot tell you which one it is facing. Only the
    measured data can, and only if you go looking.
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ---
    ## Part 6 -- Your turn

    ### Make this molecule fit

    Below is a real compound that **fails the brain-drug socket**. Your job: change it
    until every peg fits.

    The seven edits on offer are things a medicinal chemist actually does. Each one
    rewrites the molecule, and the model re-predicts all nine properties instantly.

    Watch the trade-offs bite. Adding fluorine blocks the spot the liver attacks, but
    also nudges greasiness. Adding a methyl helps permeability and hurts solubility.
    There is no edit that improves everything.
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    > **This cell fits a fast stand-in model, which takes about 20 seconds the first
    > time.** The real graph ensemble is 36 MB per member and cannot travel inside a
    > notebook, so instead this learns to imitate what the ensemble predicted for all
    > 7,608 molecules. It agrees with the real model at **R² 0.87** and answers in 8
    > milliseconds, which is what makes live editing possible. It is a stand-in, and
    > every number it produces below should be read as such.
    """
    )
    return


@app.cell
def _(Surrogate, SMILES_OF, bundle, mo):
    with mo.status.spinner("Fitting the stand-in model (about 20 seconds)..."):
        surrogate = Surrogate(bundle["endpoints"]).fit(
            [SMILES_OF[n] for n in bundle["names"]], bundle["gnn"]
        )
    return (surrogate,)


@app.cell
def _(mo):
    get_history, set_history = mo.state([])
    return get_history, set_history


@app.cell(hide_code=True)
def _(EDITS, PUZZLE_START, get_history, mo, options, set_history):
    _current = get_history()[-1][1] if get_history() else PUZZLE_START
    _avail = {o["label"]: o["key"] for o in options(_current) if o["n_sites"] > 0}

    edit_pick = mo.ui.dropdown(
        options=_avail,
        value=list(_avail)[0] if _avail else None,
        label="Edit",
    )
    site_pick = mo.ui.number(0, 9, value=0, step=1, label="Which position")
    return edit_pick, site_pick


@app.cell(hide_code=True)
def _(
    PUZZLE_START,
    apply_edit,
    edit_pick,
    get_history,
    mo,
    set_history,
    site_pick,
):
    def _apply(_):
        cur = get_history()[-1][1] if get_history() else PUZZLE_START
        if edit_pick.value is None:
            return
        new, err = apply_edit(cur, edit_pick.value, int(site_pick.value))
        if new is not None:
            set_history(get_history() + [(edit_pick.value, new)])

    apply_button = mo.ui.button(label="Apply edit", on_change=_apply)
    reset_button = mo.ui.button(label="Start over", on_change=lambda _: set_history([]))
    return apply_button, reset_button


@app.cell(hide_code=True)
def _(apply_button, edit_pick, mo, reset_button, site_pick):
    mo.hstack([edit_pick, site_pick, apply_button, reset_button],
              justify="start", gap=1, align="end")
    return


@app.cell(hide_code=True)
def _(
    PRESETS,
    PUZZLE_START,
    Peg,
    bundle,
    clicks,
    fit_report,
    get_history,
    mo,
    picture,
    render,
    surrogate,
    to_real,
):
    _hist = get_history()
    _current = _hist[-1][1] if _hist else PUZZLE_START
    _pred = surrogate.predict(_current)

    if _pred is None:
        _out = mo.md("That edit produced something the model cannot read. Start over.")
    else:
        _pegs = [
            Peg(endpoint=ep, value=to_real(ep, _pred[ep]))
            for ep in bundle["endpoints"]
        ]
        _socks = PRESETS["Brain drug"]
        _report = fit_report(_socks, {p.endpoint: p.value for p in _pegs})
        _done = clicks(_report)
        _fails = [ep for ep, r in _report.items() if r["verdict"] != "fits"]
        _steps = " -> ".join(k for k, _ in _hist) if _hist else "no edits yet"
        _msg = (
            "### It clicks. Every brain-drug requirement is met."
            if _done
            else f"**Still failing:** {', '.join(_fails)}"
        )
        _out = mo.vstack(
            [
                mo.hstack(
                    [
                        mo.Html(picture(_current, 330, 230)),
                        mo.Html(render(_socks, _pegs, caption="your molecule")),
                    ],
                    widths=[1, 3],
                    align="center",
                ),
                mo.md(f"{_msg}\n\n**Edits so far:** {_steps}\n\n`{_current}`"),
            ]
        )
    _out
    return


@app.cell(hide_code=True)
def _(mo, reality_check):
    mo.vstack(
        [
            mo.md(
                r"""
    ### Does the model actually know what that edit does?

    The model just told you what your edit would do. Here is what the *same edit*
    did to real molecules in this dataset -- pairs that differ by exactly that
    change, both measured in a lab.
    """
            ),
            reality_check(),
            mo.md(
                r"""
    Where the spread is wide, the model's confident single number is hiding a range
    of real outcomes. An edit is not a fixed effect: it depends on everything else in
    the molecule, which is what "context matters" means in practice -- and what a
    model trained on similarity finds hardest.
    """
            ),
        ]
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ### Watching the chemistry move

    The split in this notebook is by time: the model trained on molecules made early
    in these programs and was tested on ones made later. Chemists do not wander
    randomly -- they chase problems. Drag through the timeline and watch what they
    were fighting.
    """
    )
    return


@app.cell(hide_code=True)
def _(alt, drift_frame, mo, pd):
    _df = pd.DataFrame(drift_frame())
    _chart = (
        alt.Chart(_df)
        .mark_line(strokeWidth=2.5)
        .encode(
            x=alt.X("batch:Q", title="molecules, in the order they were made"),
            y=alt.Y("value:Q", title="median value (relative to the first batch)"),
            color=alt.Color(
                "endpoint:N",
                scale=alt.Scale(
                    domain=["KSOL", "Efflux", "Papp"],
                    range=["#2a78d6", "#eb6834", "#1baf7a"],
                ),
                legend=alt.Legend(title=None, orient="top"),
            ),
            tooltip=["endpoint", "batch", alt.Tooltip("value:Q", format=".2f")],
        )
        .properties(height=280, width="container")
    )
    mo.vstack(
        [
            _chart,
            mo.md(
                r"""
    Solubility climbs -- they fixed it. Then efflux takes off: median **1.34** early
    to **4.99** late, and permeability falls from **10.2** to **3.2**. They solved
    one problem and uncovered another. Chemists call this **whack-a-mole**.

    For the model this is the worst possible situation. High-efflux molecules were
    rare in training, so it under-predicts efflux on the later compounds by **0.22
    log units** on average -- always in the same direction. Not noise: a systematic
    blind spot, in exactly the region the project had moved into.
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
    ### One more thing, clearly marked

    <div style="border:2px solid #eb6834;border-radius:8px;padding:0.8rem 1rem">

    **⚠ SIMULATION — none of this is in the dataset.**

    Everything above used measured data. What follows does not, and is included to
    show where a real dataset would plug in.

    Patients take more than one drug. If a second drug blocks the liver enzyme that
    clears this one, this one builds up. That is a **drug-drug interaction**, and it
    is why grapefruit juice carries warnings.

    The dataset has **no interaction measurements at all**. So the slider below
    invents an inhibitor, and the standard regulatory equation turns our *predicted*
    clearance into a predicted rise in exposure. The clearance is a model output; the
    inhibitor is fiction.

    </div>
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    fm_slider = mo.ui.slider(
        0.0, 1.0, value=0.8, step=0.05,
        label="Share of clearance going through the blocked enzyme", show_value=True,
    )
    inhib_slider = mo.ui.slider(
        0.0, 20.0, value=2.0, step=0.5,
        label="Inhibitor strength (concentration / Ki)", show_value=True,
    )
    return fm_slider, inhib_slider


@app.cell(hide_code=True)
def _(auc_ratio, fm_slider, inhib_slider, mo, severity):
    _r = auc_ratio(fm_slider.value, inhib_slider.value, 1.0)
    _bar = int(min(_r.auc_ratio, 10) * 6)
    mo.vstack(
        [
            mo.hstack([fm_slider, inhib_slider], widths="equal", gap=2),
            mo.md(
                f"""
    ### Exposure would rise **{_r.auc_ratio:.1f}x** — a *{severity(_r.auc_ratio)}* interaction

    `{"#" * _bar}`

    A drug cleared by a single enzyme (share near 1.0) is at the mercy of anything
    that blocks it. A drug with a second route out (share near 0.5) is capped at
    **{1 / max(1 - fm_slider.value, 0.01):.1f}x** no matter how strong the inhibitor
    gets. That is why "how is this cleared?" is asked as early as "how fast?".

    **To make this real** you would need measured enzyme-inhibition data. It exists:
    OpenADMET's CYP Inhibition Challenge covers exactly this, for the four enzymes
    that handle most drugs. That is the natural next notebook.
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
    ## What this notebook found

    | | |
    |---|---|
    | **Depth pays** | 2 → 4 rounds of message passing cuts error; 4 → 6 barely moves it |
    | **Pretraining did not** | CheMeleon 0.315 vs random init 0.307 — no measurable gain at this data size |
    | **Sharing tasks did not** | Brain binding got 16% *worse* in a nine-headed model |
    | **A rule for ensembling** | Blend only when ρ < σ₁/σ₂ — and it predicted the right weight on all nine endpoints |
    | **…that you often cannot use** | Estimated honestly, it backfires on the endpoints with too little validation data |
    | **Volatility ≠ surprise** | LogD moves on 33% of one-atom edits and surprises nobody; efflux moves on 5% and blindsides the model |
    | **The label may not mean what it says** | Censored solubility, 265 deleted stable compounds, 129 stereo pairs the model cannot see |

    Four things we expected to find are not in this notebook, because the data said
    otherwise, and one thing we nearly reported was a NaN artefact wearing a lab coat.

    **The thesis, once more:** nine properties, one model, nine different problems —
    and the model cannot tell you which one it is facing. Only the data can.

    ### If you want to take this further

    - Swap the presets in Part 1 for your own project's requirements.
    - Run the Part 4 rule on your own two models before building the second one.
    - Check your own labels for a ceiling before trusting an R².
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.accordion(
        {
            "Sources, licence, and how this was made (including AI use)": mo.md(
                r"""
**Data.** OpenADMET–ExpansionRx Blind Challenge, full post-challenge release,
courtesy of Expansion Therapeutics, **CC-BY-4.0**. Loaded at run time from
[huggingface.co/datasets/openadmet/openadmet-expansionrx-challenge-data](https://huggingface.co/datasets/openadmet/openadmet-expansionrx-challenge-data).
7,608 molecules, nine endpoints, temporal train/test split.

**Models.** Chemprop 2.3 D-MPNN with CheMeleon initialisation, five seeds,
multitask over all nine endpoints; LightGBM on Morgan count fingerprints plus
RDKit descriptors. Trained locally on one RTX A5000. Ablations at three seeds.
All scores are on the challenge's temporal test split; nothing was tuned on it.

**The challenge winner is not reproduced here.** Inductive Bio's *Beacon* is
proprietary. This notebook rebuilds the public recipe described in the published
write-ups, and its purpose is not accuracy.

**Built with.** marimo, RDKit, Chemprop, LightGBM, scikit-learn, Altair.

**AI use — disclosed.** This notebook was built in collaboration with Claude
(Anthropic) used as a coding agent: it wrote most of the code, ran the training
and analysis, and drafted the prose. Direction, the choice of question, and every
decision about what to keep or cut were mine. Two things are worth saying plainly,
because they shaped the result:

1. **Four planned claims were abandoned** when the data contradicted them —
   including the notebook's original thesis. Those refutations are still in here
   (Part 3's accordion, Part 2's two negative results) rather than quietly deleted.
2. **One finding was nearly published and was wrong.** The single-task NaN looked
   like evidence about small data; it was an empty-batch artefact. It is in Part 2
   as a trap, not as a finding.

Every number in this notebook came from a run on this machine, on the temporal
split, and the code that produced it is in the repository.

**Code.** [github.com/Suyashkb/Marimo-Competition](https://github.com/Suyashkb/Marimo-Competition)
— training scripts, the unit-tested library that is inlined below, and the
evidence report.

**Author.** Suyash Bhagat ([@Suyashkb](https://github.com/Suyashkb)).
"""
            )
        }
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
def _():
    # Results from the offline training runs, which cannot be recomputed here:
    # every number is a test-split score, averaged over 3 seeds. See the repo's
    # train/ablate2.py for the runs that produced them.
    ABLATION = {
        "depth": [
            {"depth": 2, "mae": 0.3436, "lo": 0.3409, "hi": 0.3463},
            {"depth": 4, "mae": 0.3126, "lo": 0.3080, "hi": 0.3172},
            {"depth": 6, "mae": 0.3072, "lo": 0.3037, "hi": 0.3107},
        ],
        "pretrain": {
            "chemeleon": 0.3145, "chemeleon_sd": 0.0069,
            "scratch": 0.3072, "scratch_sd": 0.0035,
        },
        # endpoint -> (own model, shared model)
        "multitask": {
            "LogD": (0.413, 0.419), "Papp": (0.313, 0.303),
            "MBPB": (0.165, 0.192), "MGMB": (0.201, 0.207),
        },
    }

    # The hypothesis we abandoned, kept so the reader can check it themselves.
    REFUTED = {
        "concentration": [
            {"endpoint": "KSOL", "contribution concentrated in top atom": 3.92},
            {"endpoint": "HLM", "contribution concentrated in top atom": 3.23},
            {"endpoint": "LogD", "contribution concentrated in top atom": 3.02},
            {"endpoint": "Efflux", "contribution concentrated in top atom": 2.68},
            {"endpoint": "MLM", "contribution concentrated in top atom": 2.45},
            {"endpoint": "Papp", "contribution concentrated in top atom": 2.40},
        ]
    }
    return ABLATION, REFUTED


@app.cell
def _():
    def n_atoms(smiles: str) -> int:
        """Heavy-atom count. Counting letters in a SMILES string is not this."""
        from rdkit import Chem

        mol = Chem.MolFromSmiles(smiles)
        return mol.GetNumHeavyAtoms() if mol else 0

    return (n_atoms,)


@app.cell
def _(EPS, IDX, SMILES_OF, TEST, Y, bundle, find_pairs, np):
    def matched_pairs():
        """Molecule pairs differing by one small substituent.

        Recomputed here rather than shipped, so the reader can see exactly what
        counts as a pair. Takes a few seconds over 7,608 molecules.
        """
        names = bundle["names"]
        pairs = find_pairs(names, [SMILES_OF[n] for n in names])
        from rdkit import Chem

        heavy = {}

        def n_heavy(s):
            if s not in heavy:
                m = Chem.MolFromSmiles(s)
                heavy[s] = m.GetNumHeavyAtoms() if m else 0
            return heavy[s]

        return [
            p for p in pairs
            if abs(n_heavy(p.smiles_a) - n_heavy(p.smiles_b)) <= 1
        ]

    PAIRS = matched_pairs()
    return (PAIRS,)


@app.cell
def _(EPS, IDX, PAIRS, TEST, Y, bundle, np):
    def surprise_table():
        """Volatility and surprise per endpoint, from the matched pairs.

        volatility -- share of one-atom edits that move the value >= 1 log unit
        surprise   -- model error on those pairs, over error on pairs that hardly
                      moved. Above 1 means the model is caught out by the jumps.
        """
        rows = []
        for j, ep in enumerate(EPS):
            gaps, cliff_err, flat_err = [], [], []
            for p in PAIRS:
                ia, ib = IDX[p.name_a], IDX[p.name_b]
                va, vb = Y[ia, j], Y[ib, j]
                if np.isnan(va) or np.isnan(vb):
                    continue
                gap = abs(va - vb)
                gaps.append(gap)
                for i, v in ((ia, va), (ib, vb)):
                    if not TEST[i]:
                        continue
                    err = abs(v - bundle["gnn"][i, j])
                    if gap >= 1.0:
                        cliff_err.append(err)
                    elif gap <= 0.1:
                        flat_err.append(err)
            if len(gaps) < 200 or len(cliff_err) < 20 or len(flat_err) < 20:
                continue
            rows.append(
                {
                    "endpoint": ep,
                    "volatility": float(np.mean(np.array(gaps) >= 1.0)),
                    "surprise": float(np.mean(cliff_err) / np.mean(flat_err)),
                    "n_cliff": len(cliff_err),
                }
            )
        return rows

    return (surprise_table,)


@app.cell
def _(EPS, TEST, Y, bundle, np):
    def blend_curve(endpoint: str) -> dict:
        """Every blend weight's test error, next to what the formula predicts."""
        j = EPS.index(endpoint)
        m = TEST & ~np.isnan(Y[:, j])
        e1 = bundle["gnn"][m, j] - Y[m, j]
        e2 = bundle["lgbm"][m, j] - Y[m, j]
        # Order so model 1 is the better one; the rule is stated that way.
        flipped = e1.std(ddof=1) > e2.std(ddof=1)
        if flipped:
            e1, e2 = e2, e1
        s1, s2 = e1.std(ddof=1), e2.std(ddof=1)
        rho = float(np.corrcoef(e1, e2)[0, 1])
        w_star = (s2**2 - rho * s1 * s2) / (s1**2 + s2**2 - 2 * rho * s1 * s2)
        w_star = float(np.clip(w_star, 0.0, 1.0))

        ws = np.linspace(0, 1, 101)
        rmse = [float(np.sqrt((((w * e1 + (1 - w) * e2)) ** 2).mean())) for w in ws]
        best = int(np.argmin(rmse))
        base = float(np.sqrt((e1**2).mean()))
        # Report on the graph model's axis whichever way the sort went.
        to_graph = (lambda w: 1 - w) if flipped else (lambda w: w)
        return {
            "curve": [{"w": float(to_graph(w)), "rmse": r} for w, r in zip(ws, rmse)],
            "rho": rho,
            "ratio": float(s1 / s2),
            "w_star": float(to_graph(w_star)),
            "w_emp": float(to_graph(ws[best])),
            "gain": 100 * (1 - rmse[best] / base),
        }

    return (blend_curve,)


@app.cell
def _():
    # Weights chosen on validation molecules only, then applied to the later test
    # molecules -- the honest version. Computed offline; see train/evidence.py.
    HONEST_BLEND = [
        {"endpoint": "Papp", "validation molecules": 97, "error reduction": "+4.2%"},
        {"endpoint": "HLM", "validation molecules": 22, "error reduction": "+2.7%"},
        {"endpoint": "MLM", "validation molecules": 380, "error reduction": "+2.6%"},
        {"endpoint": "LogD", "validation molecules": 532, "error reduction": "+1.8%"},
        {"endpoint": "KSOL", "validation molecules": 531, "error reduction": "+0.5%"},
        {"endpoint": "Efflux", "validation molecules": 97, "error reduction": "+0.1%"},
        {"endpoint": "MPPB", "validation molecules": 81, "error reduction": "0.0%"},
        {"endpoint": "MBPB", "validation molecules": 81, "error reduction": "-1.7%"},
        {"endpoint": "MGMB", "validation molecules": 45, "error reduction": "-2.5%"},
    ]
    return (HONEST_BLEND,)


@app.cell
def _(EPS, IDX, PAIRS, SMILES_OF, TEST, Y, bundle, np):
    def build_quiz(endpoint: str = "Efflux", n: int = 4) -> list[dict]:
        """Matched pairs for the guessing game: half real cliffs, half flat.

        Chosen deterministically so everyone sees the same puzzle, and drawn only
        from pairs where both molecules were measured.
        """
        j = EPS.index(endpoint)
        cliffs, flats = [], []
        for p in PAIRS:
            ia, ib = IDX[p.name_a], IDX[p.name_b]
            va, vb = Y[ia, j], Y[ib, j]
            if np.isnan(va) or np.isnan(vb):
                continue
            if not (TEST[ia] or TEST[ib]):
                continue
            if max(len(p.smiles_a), len(p.smiles_b)) > 70:
                continue
            gap = abs(va - vb)
            model_gap = abs(bundle["gnn"][ia, j] - bundle["gnn"][ib, j])
            rec = {
                "name_a": p.name_a, "name_b": p.name_b,
                "smiles_a": p.smiles_a, "smiles_b": p.smiles_b,
                "is_cliff": bool(gap >= 1.0),
                "model_says_cliff": bool(model_gap >= 1.0),
                "gap": float(gap),
            }
            (cliffs if rec["is_cliff"] else flats).append(rec)

        cliffs.sort(key=lambda r: -r["gap"])
        flats.sort(key=lambda r: r["gap"])
        half = n // 2
        picked = cliffs[:half] + flats[:half]
        # Interleave so the answers are not all on one side.
        out = []
        for a, b in zip(picked[:half], picked[half:]):
            out.extend([a, b])
        return out[:n]

    quiz_pairs = build_quiz()
    return (quiz_pairs,)


@app.cell
def _(EPS, TEST, Y, bundle, np):
    def ceiling_effect(ceiling_um: float) -> dict:
        """Clip measured solubility at a ceiling and re-score, as an assay would."""
        j = EPS.index("KSOL")
        m = TEST & ~np.isnan(Y[:, j])
        y_real = 10 ** Y[m, j] - 1
        pred = bundle["gnn"][m, j]

        clipped = np.log10(np.minimum(y_real, ceiling_um) + 1)
        full = Y[m, j]

        def spearman(a, b):
            ra = np.argsort(np.argsort(a))
            rb = np.argsort(np.argsort(b))
            return float(np.corrcoef(ra, rb)[0, 1])

        idx = np.argsort(y_real)[:: max(1, len(y_real) // 900)]
        return {
            "mae": float(np.abs(clipped - pred).mean()),
            "rho": spearman(clipped, pred),
            "mae_full": float(np.abs(full - pred).mean()),
            "rho_full": spearman(full, pred),
            "at_ceiling": float((y_real >= ceiling_um).mean()),
            "points": [
                {"measured": float(clipped[i]), "predicted": float(pred[i])}
                for i in idx
            ],
        }

    return (ceiling_effect,)


@app.cell
def _(EPS, IDX, SMILES_OF, Y, bundle, np, picture):
    def stereo_example() -> dict:
        """Find two molecules with the same 2D skeleton but different measurements."""
        from rdkit import Chem

        flat = {}
        for name, smi in SMILES_OF.items():
            mol = Chem.MolFromSmiles(smi)
            if mol is None:
                continue
            flat.setdefault(Chem.MolToSmiles(mol, isomericSmiles=False), []).append(name)

        best = None
        for names in flat.values():
            if len(names) < 2:
                continue
            for j, ep in enumerate(EPS):
                vals = [(n, Y[IDX[n], j]) for n in names if not np.isnan(Y[IDX[n], j])]
                if len(vals) < 2:
                    continue
                vals.sort(key=lambda t: t[1])
                spread = vals[-1][1] - vals[0][1]
                if best is None or spread > best["spread"]:
                    best = {
                        "spread": float(spread), "endpoint": ep,
                        "a": vals[0][0], "b": vals[-1][0],
                        "va": float(vals[0][1]), "vb": float(vals[-1][1]),
                    }
        if best is None:
            return {"pictures": [], "caption": "No stereoisomer pair found."}

        ja = EPS.index(best["endpoint"])
        pa = float(bundle["gnn"][IDX[best["a"]], ja])
        pb = float(bundle["gnn"][IDX[best["b"]], ja])
        unit = META[best["endpoint"]][0]
        return {
            "pictures": [
                picture(SMILES_OF[best["a"]], 320, 210),
                picture(SMILES_OF[best["b"]], 320, 210),
            ],
            "caption": (
                f"**{best['a']}** and **{best['b']}** differ only in 3D arrangement.\n\n"
                f"Measured **{best['endpoint']}**: "
                f"{format_value(best['endpoint'], to_real(best['endpoint'], best['va']), unit)} "
                f"versus "
                f"{format_value(best['endpoint'], to_real(best['endpoint'], best['vb']), unit)} "
                f"-- a **{10 ** best['spread']:.0f}x** difference.\n\n"
                f"The model predicts "
                f"{format_value(best['endpoint'], to_real(best['endpoint'], pa), unit)} "
                f"and "
                f"{format_value(best['endpoint'], to_real(best['endpoint'], pb), unit)} "
                f"-- nearly the same, because to a 2D graph these *are* nearly the same.\n\n"
                f"Across the dataset, **548** groups share a 2D skeleton and **129** of "
                f"them disagree by at least 0.5 log units on something measured. Every "
                f"one is an error the model cannot avoid, because the information "
                f"needed is not in its input."
            ),
        }

    return (stereo_example,)


@app.cell
def _(EPS, IDX, PRESETS, SMILES_OF, bundle, fit_report, np, to_real):
    def _pick_puzzle() -> str:
        """A real molecule that fails the brain socket but is small enough to edit."""
        socks = PRESETS["Brain drug"]
        best = None
        for i, name in enumerate(bundle["names"]):
            smi = SMILES_OF.get(name, "")
            if not 25 <= len(smi) <= 55:
                continue
            vals = {
                ep: to_real(ep, float(bundle["gnn"][i, j])) for j, ep in enumerate(EPS)
            }
            fails = sum(
                1 for r in fit_report(socks, vals).values() if r["verdict"] != "fits"
            )
            # One or two failures: solvable in a few edits, not hopeless.
            if fails in (1, 2) and (best is None or fails < best[0]):
                best = (fails, smi)
                if fails == 1:
                    break
        return best[1] if best else "Cc1ccc(C(=O)Nc2ccccc2)cc1"

    PUZZLE_START = _pick_puzzle()
    return (PUZZLE_START,)


@app.cell
def _(EPS, IDX, PAIRS, Y, alt, edit_pick, np, pd):
    def reality_check():
        """What the chosen edit did to real measured pairs, per endpoint."""
        from rdkit import Chem

        key = edit_pick.value
        # Map an edit to the substituent change it makes, so real pairs can be found.
        wanted = {
            "ar_h_to_f": {"*F"}, "ar_h_to_me": {"*C"}, "ar_h_to_cl": {"*Cl"},
            "ar_h_to_oh": {"*O"}, "me_to_cf3": {"*C(F)(F)F"},
        }.get(key)

        rows = []
        for p in PAIRS:
            subs = {p.sub_a, p.sub_b}
            if wanted is None or not (subs & wanted):
                continue
            ia, ib = IDX[p.name_a], IDX[p.name_b]
            for j, ep in enumerate(EPS):
                va, vb = Y[ia, j], Y[ib, j]
                if np.isnan(va) or np.isnan(vb):
                    continue
                # Sign it so "added group" is always the second molecule.
                delta = (vb - va) if p.sub_b in (wanted or set()) else (va - vb)
                rows.append({"endpoint": ep, "change": float(delta)})

        if len(rows) < 12:
            import marimo as _mo

            return _mo.md(
                "_No measured pairs in this dataset made exactly that edit, so there "
                "is nothing to check the model against here. Try H to F or add CH3._"
            )

        df = pd.DataFrame(rows)
        return (
            alt.Chart(df)
            .mark_boxplot(size=16, color="#2a78d6", outliers={"size": 8, "opacity": 0.4})
            .encode(
                y=alt.Y("endpoint:N", sort=EPS, title=None),
                x=alt.X("change:Q", title="measured change, log units (0 = no effect)"),
                tooltip=[alt.Tooltip("count()", title="pairs")],
            )
            .properties(height=300, width="container")
        )

    return (reality_check,)


@app.cell
def _(EPS, Y, data, np):
    def drift_frame(n_batches: int = 12):
        """Median of three endpoints over time, indexed to the first batch.

        Three measures on one axis only works because each is expressed as a ratio
        to its own starting value; the raw units are not comparable.
        """
        order = np.argsort(data["id_num"].to_numpy())
        rows = []
        for ep in ("KSOL", "Efflux", "Papp"):
            j = EPS.index(ep)
            vals = Y[order, j]
            chunks = np.array_split(np.arange(len(order)), n_batches)
            base = None
            for b, chunk in enumerate(chunks):
                v = vals[chunk]
                v = v[~np.isnan(v)]
                if len(v) < 20:
                    continue
                med = float(np.median(v))
                if base is None:
                    base = med if abs(med) > 1e-6 else 1.0
                rows.append({"endpoint": ep, "batch": b, "value": med / base})
        return rows

    return (drift_frame,)


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
