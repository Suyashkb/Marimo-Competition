"""Find matched molecular pairs: molecules that differ by one small change.

These are the pairs a chemist actually makes during a fluorine or methyl scan, and
they are where property prediction is hardest. A pair whose measured values differ
a lot despite an almost identical structure is an "activity cliff".

Method: cut one single, acyclic, non-ring bond in each molecule and index it by
(core, substituent). Two molecules sharing a core but differing in the substituent
form a pair. This is a compact version of the standard MMPA fragment-and-index
approach, kept dependency-free so it also runs inside the notebook.
"""

from collections import defaultdict
from dataclasses import dataclass
from itertools import combinations

from rdkit import Chem

# Bonds worth cutting: single, not in a ring, and not to a lone hydrogen.
_CUTTABLE = Chem.MolFromSmarts("[!#1]-!@[!#1]")
DUMMY = "[*]"


@dataclass(frozen=True)
class Pair:
    name_a: str
    name_b: str
    smiles_a: str
    smiles_b: str
    core: str
    sub_a: str
    sub_b: str

    @property
    def transform(self) -> str:
        return f"{self.sub_a} -> {self.sub_b}"


def fragment(smiles: str, max_sub_atoms: int = 8) -> list[tuple[str, str]]:
    """All (core, substituent) pairs from single-bond cuts.

    `max_sub_atoms` keeps the substituent small, so pairs describe a local edit
    rather than two halves of a molecule swapped.
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return []
    out = []
    for begin, end in mol.GetSubstructMatches(_CUTTABLE):
        bond = mol.GetBondBetweenAtoms(begin, end)
        if bond is None:
            continue
        frags = Chem.FragmentOnBonds(mol, [bond.GetIdx()], addDummies=True)
        pieces = Chem.GetMolFrags(frags, asMols=True, sanitizeFrags=False)
        if len(pieces) != 2:
            continue
        # Heavy-atom count excluding the dummy marks which piece is the substituent.
        sized = sorted(pieces, key=lambda m: m.GetNumHeavyAtoms())
        sub, core = sized[0], sized[1]
        if sub.GetNumHeavyAtoms() - 1 > max_sub_atoms:
            continue
        try:
            out.append((_canonical(core), _canonical(sub)))
        except Exception:  # noqa: BLE001 - unsanitized fragments can fail to write
            continue
    return out


def _canonical(frag: Chem.Mol) -> str:
    """SMILES with the attachment point written as a plain [*].

    FragmentOnBonds labels each dummy with the atom index it was cut from, which
    would make the same chemical transform look different at every position.
    """
    frag = Chem.Mol(frag)
    for atom in frag.GetAtoms():
        if atom.GetAtomicNum() == 0:
            atom.SetIsotope(0)
            atom.SetAtomMapNum(0)
    return Chem.MolToSmiles(frag)


def find_pairs(
    names: list[str], smiles: list[str], max_sub_atoms: int = 8, max_per_core: int = 60
) -> list[Pair]:
    """All matched pairs across a set of molecules, de-duplicated by molecule pair."""
    by_core: dict[str, list[tuple[str, str, str]]] = defaultdict(list)
    for name, smi in zip(names, smiles, strict=True):
        for core, sub in fragment(smi, max_sub_atoms):
            by_core[core].append((name, smi, sub))

    seen: set[tuple[str, str]] = set()
    pairs: list[Pair] = []
    for core, members in by_core.items():
        # A very common core would give a combinatorial blow-up with little value.
        if len(members) > max_per_core:
            continue
        for (na, sa, suba), (nb, sb, subb) in combinations(members, 2):
            if na == nb or suba == subb:
                continue
            key = (na, nb) if na < nb else (nb, na)
            if key in seen:
                continue
            seen.add(key)
            pairs.append(
                Pair(
                    name_a=na, name_b=nb, smiles_a=sa, smiles_b=sb,
                    core=core, sub_a=suba, sub_b=subb,
                )
            )
    return pairs
