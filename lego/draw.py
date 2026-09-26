"""Draw molecules as SVG, optionally painting atoms by how much they matter.

Two jobs:
  picture()    -- a plain structure, themed to sit on the notebook surface
  painted()    -- the same structure with atoms tinted by a per-atom weight

The tint uses a *diverging* scale, because a contribution has polarity: this atom
pushes the prediction up, that one pulls it down, and zero is a real midpoint.
Sequential colour here would hide the sign. Neutral grey sits at the midpoint, as
a diverging ramp requires, and the two poles are the documented warm/cool ends.
"""

from rdkit import Chem, RDLogger
from rdkit.Chem import rdDepictor
from rdkit.Chem.Draw import rdMolDraw2D

RDLogger.DisableLog("rdApp.*")

# Diverging pair: cool = pulls the prediction down, warm = pushes it up.
COOL = (0.17, 0.47, 0.84)
WARM = (0.92, 0.41, 0.20)
NEUTRAL = (0.85, 0.85, 0.83)


def _mol(smiles: str) -> Chem.Mol | None:
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    rdDepictor.Compute2DCoords(mol)
    rdDepictor.StraightenDepiction(mol)
    return mol


def _blend(a: tuple, b: tuple, t: float) -> tuple:
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


def _ramp(weight: float, scale: float) -> tuple:
    """Signed weight -> colour on the diverging ramp, saturating at `scale`."""
    if scale <= 0:
        return NEUTRAL
    t = max(-1.0, min(1.0, weight / scale))
    return _blend(NEUTRAL, WARM if t > 0 else COOL, abs(t))


def _style(drawer: rdMolDraw2D.MolDraw2DSVG, dark: bool) -> None:
    opts = drawer.drawOptions()
    opts.clearBackground = False
    opts.bondLineWidth = 2
    opts.padding = 0.08
    if dark:
        opts.setAtomPalette({-1: (0.95, 0.95, 0.95)})


def picture(smiles: str, width: int = 300, height: int = 200, dark: bool = False) -> str:
    mol = _mol(smiles)
    if mol is None:
        return '<svg xmlns="http://www.w3.org/2000/svg"></svg>'
    d = rdMolDraw2D.MolDraw2DSVG(width, height)
    _style(d, dark)
    rdMolDraw2D.PrepareAndDrawMolecule(d, mol)
    d.FinishDrawing()
    return d.GetDrawingText()


def painted(
    smiles: str,
    weights: dict[int, float],
    width: int = 340,
    height: int = 230,
    dark: bool = False,
    scale: float | None = None,
) -> str:
    """Structure with atoms tinted by `weights` (atom index -> signed value)."""
    mol = _mol(smiles)
    if mol is None:
        return '<svg xmlns="http://www.w3.org/2000/svg"></svg>'
    if scale is None:
        scale = max((abs(v) for v in weights.values()), default=0.0)

    colors = {i: _ramp(w, scale) for i, w in weights.items() if i < mol.GetNumAtoms()}
    d = rdMolDraw2D.MolDraw2DSVG(width, height)
    _style(d, dark)
    rdMolDraw2D.PrepareAndDrawMolecule(
        d,
        mol,
        highlightAtoms=list(colors),
        highlightAtomColors=colors,
        highlightBonds=[],
    )
    d.FinishDrawing()
    return d.GetDrawingText()


def highlight(
    smiles: str,
    atoms: list[int],
    width: int = 300,
    height: int = 200,
    dark: bool = False,
    color: tuple = (0.38, 0.78, 0.55),
) -> str:
    """Structure with a fixed set of atoms marked -- used for 'what changed'."""
    mol = _mol(smiles)
    if mol is None:
        return '<svg xmlns="http://www.w3.org/2000/svg"></svg>'
    keep = [i for i in atoms if i < mol.GetNumAtoms()]
    d = rdMolDraw2D.MolDraw2DSVG(width, height)
    _style(d, dark)
    rdMolDraw2D.PrepareAndDrawMolecule(
        d, mol, highlightAtoms=keep, highlightAtomColors={i: color for i in keep}
    )
    d.FinishDrawing()
    return d.GetDrawingText()


def changed_atoms(smiles_a: str, smiles_b: str) -> tuple[list[int], list[int]]:
    """Atoms of each molecule that the other does not account for.

    Used to point at the one edit in a matched pair. Falls back to an empty
    result when no common core is found, rather than guessing.
    """
    a, b = Chem.MolFromSmiles(smiles_a), Chem.MolFromSmiles(smiles_b)
    if a is None or b is None:
        return [], []
    from rdkit.Chem import rdFMCS

    res = rdFMCS.FindMCS(
        [a, b], timeout=5, matchValences=False, ringMatchesRingOnly=True
    )
    if res.canceled or not res.smartsString:
        return [], []
    patt = Chem.MolFromSmarts(res.smartsString)
    if patt is None:
        return [], []
    ma, mb = a.GetSubstructMatch(patt), b.GetSubstructMatch(patt)
    return (
        [i for i in range(a.GetNumAtoms()) if i not in ma],
        [i for i in range(b.GetNumAtoms()) if i not in mb],
    )


def neighborhood(smiles: str, center: int, radius: int) -> list[int]:
    """Atoms within `radius` bonds of `center`.

    This is exactly what one atom can "see" after `radius` rounds of message
    passing, so a slider over radius shows the model's receptive field growing --
    no trained model required to make the mechanism visible.
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None or not 0 <= center < mol.GetNumAtoms():
        return []
    seen = {center}
    frontier = {center}
    for _ in range(max(radius, 0)):
        nxt = set()
        for idx in frontier:
            for nb in mol.GetAtomWithIdx(idx).GetNeighbors():
                if nb.GetIdx() not in seen:
                    nxt.add(nb.GetIdx())
        seen |= nxt
        frontier = nxt
        if not frontier:
            break
    return sorted(seen)
