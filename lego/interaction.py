"""SIMULATION ONLY: what a co-administered enzyme inhibitor would do to exposure.

Nothing here is fitted to the ExpansionRx data, which contains no drug-drug
interaction measurements at all. This is the textbook "static" model regulators
use for a first-pass estimate, driven by our *predicted* clearance plus a
hypothetical inhibitor the user invents with sliders.

The notebook states this in the cell itself. It exists to show where real CYP
inhibition data (e.g. the OpenADMET CYP challenge) would plug in.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Interaction:
    auc_ratio: float  # fold-change in total exposure
    fm_blocked: float  # fraction of the metabolic route that is shut down


def auc_ratio(fm: float, inhibitor_conc: float, ki: float) -> Interaction:
    """Fold-rise in exposure when one metabolic route is partly blocked.

    fm              fraction of clearance going through the inhibited enzyme (0-1)
    inhibitor_conc  free concentration of the inhibitor, same units as ki
    ki              inhibition constant; smaller means a stronger inhibitor

    AUC ratio = 1 / (fm / (1 + I/Ki) + (1 - fm))

    With no inhibitor the ratio is 1. With a total block of a route that carried
    all the clearance it diverges, which is exactly why fm < 1 matters clinically:
    a second elimination route caps the damage.
    """
    if not 0.0 <= fm <= 1.0:
        raise ValueError("fm must be between 0 and 1")
    if inhibitor_conc < 0 or ki <= 0:
        raise ValueError("need inhibitor_conc >= 0 and ki > 0")

    remaining = 1.0 / (1.0 + inhibitor_conc / ki)  # surviving activity of that route
    denom = fm * remaining + (1.0 - fm)
    return Interaction(auc_ratio=1.0 / denom, fm_blocked=fm * (1.0 - remaining))


def apparent_clearance(clint: float, fm: float, inhibitor_conc: float, ki: float) -> float:
    """Predicted clearance scaled down by the same static model, for the peg display."""
    return clint / auc_ratio(fm, inhibitor_conc, ki).auc_ratio


# Rough severity bands used by regulators to describe an interaction.
def severity(ratio: float) -> str:
    if ratio < 1.25:
        return "negligible"
    if ratio < 2.0:
        return "weak"
    if ratio < 5.0:
        return "moderate"
    return "strong"
