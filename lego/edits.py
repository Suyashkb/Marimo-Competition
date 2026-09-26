"""The edits a medicinal chemist would actually try, as RDKit reaction SMARTS.

Each edit is one move in the puzzle: apply it, re-predict, watch the pegs move.
Transforms are declarative so the chemistry is readable and each one can be
checked against a known example in the tests.

Every result is re-parsed from canonical SMILES before being returned, so a
caller can never receive a molecule RDKit would refuse to read back.
"""

from dataclasses import dataclass

from rdkit import Chem, RDLogger
from rdkit.Chem import AllChem

RDLogger.DisableLog("rdApp.*")


@dataclass(frozen=True)
class Edit:
    key: str
    label: str
    smarts: str
    why: str  # what a chemist expects this to do


# Ordered as they appear in the UI.
EDITS: tuple[Edit, ...] = (
    Edit(
        key="ar_h_to_f",
        label="H to F on a ring",
        smarts="[cH:1]>>[c:1]F",
        why="Fluorine blocks the spot the liver would attack, and barely changes the shape.",
    ),
    Edit(
        key="ar_h_to_me",
        label="Add CH3 to a ring",
        smarts="[cH:1]>>[c:1]C",
        why="The 'magic methyl': fills a small pocket, often more potent, but greasier.",
    ),
    Edit(
        key="ar_h_to_cl",
        label="H to Cl on a ring",
        smarts="[cH:1]>>[c:1]Cl",
        why="Like fluorine but bigger and much greasier, so solubility usually suffers.",
    ),
    Edit(
        key="ar_h_to_oh",
        label="H to OH on a ring",
        smarts="[cH:1]>>[c:1]O",
        why="Adds a polar handle: more soluble, less permeable, and a new metabolism site.",
    ),
    Edit(
        key="benzene_to_pyridine",
        label="Ring CH to N (benzene to pyridine)",
        # Only carbons in a 6-membered aromatic ring, so 5-rings are left alone.
        smarts="[cH;r6:1]>>[n:1]",
        why="Swaps a CH for N: less greasy, more soluble, a classic bioisostere.",
    ),
    Edit(
        key="me_to_cf3",
        label="CH3 to CF3",
        smarts="[CH3:1][c:2]>>[C:1](F)(F)(F)[c:2]",
        why="Blocks metabolism hard, but pushes lipophilicity up.",
    ),
    Edit(
        key="alkyl_ch2_to_o",
        label="CH2 to O in a chain",
        smarts="[CX4H2:1]([CX4:2])[CX4:3]>>[O:1]([C:2])[C:3]",
        why="Breaks up a greasy chain and removes a soft spot.",
    ),
)

BY_KEY = {e.key: e for e in EDITS}


def _reaction(smarts: str) -> AllChem.ChemicalReaction:
    rxn = AllChem.ReactionFromSmarts(smarts)
    if rxn is None:
        raise ValueError(f"bad reaction SMARTS: {smarts}")
    return rxn


_RXN = {e.key: _reaction(e.smarts) for e in EDITS}


def products(smiles: str, key: str) -> list[str]:
    """Every distinct molecule this edit can produce, in a stable order.

    Symmetry-equivalent positions collapse to one entry, so the count here is
    what the UI should offer rather than the raw number of SMARTS matches.
    """
    if key not in BY_KEY:
        return []
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return []
    seen: list[str] = []
    for outcome in _RXN[key].RunReactants((mol,)):
        for product in outcome:
            smi = _sanitized_smiles(product)
            if smi is not None and smi != smiles and smi not in seen:
                seen.append(smi)
    return sorted(seen)


def options(smiles: str) -> list[dict]:
    """Which edits are available for this molecule, and how many results each gives."""
    return [
        {
            "key": e.key,
            "label": e.label,
            "why": e.why,
            "n_sites": len(products(smiles, e.key)),
        }
        for e in EDITS
    ]


def apply_edit(smiles: str, key: str, site: int = 0) -> tuple[str | None, str | None]:
    """Apply one edit. Returns (new_smiles, None) or (None, reason)."""
    if key not in BY_KEY:
        return None, f"Unknown edit '{key}'."
    if Chem.MolFromSmiles(smiles) is None:
        return None, "Could not read that molecule."
    choices = products(smiles, key)
    if not choices:
        return None, f"'{BY_KEY[key].label}' does not apply anywhere on this molecule."
    if not 0 <= site < len(choices):
        return None, f"Only {len(choices)} place(s) available for this edit."
    return choices[site], None


def _sanitized_smiles(mol: Chem.Mol) -> str | None:
    """Canonical SMILES, or None if the product is not a valid molecule.

    Reaction products carry no implicit-H information, so they are written out and
    parsed again: anything RDKit cannot read back is rejected here rather than
    surfacing later as a broken prediction.
    """
    try:
        mol.UpdatePropertyCache(strict=False)
        Chem.SanitizeMol(mol)
        smi = Chem.MolToSmiles(mol)
    except Exception:  # noqa: BLE001 - RDKit raises several unrelated types
        return None
    return smi if smi and Chem.MolFromSmiles(smi) is not None else None
