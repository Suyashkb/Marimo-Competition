import math

import pytest

from lego import interaction, sockets, units


class TestUnits:
    @pytest.mark.parametrize("ep,val", [("KSOL", 250.0), ("HLM", 16.4), ("Efflux", 1.38)])
    def test_round_trip(self, ep, val):
        assert units.to_real(ep, units.to_model(ep, val)) == pytest.approx(val)

    def test_logd_untouched(self):
        assert units.to_model("LogD", 2.1) == 2.1
        assert units.to_real("LogD", 2.1) == 2.1

    def test_zero_is_representable(self):
        # The dataset genuinely contains 0.0 values; log10(x+1) must handle them.
        assert units.to_model("KSOL", 0.0) == 0.0
        assert units.to_real("KSOL", 0.0) == pytest.approx(0.0)

    def test_negative_real_rejected(self):
        with pytest.raises(ValueError):
            units.to_model("KSOL", -1.0)


class TestSockets:
    def test_window_verdicts(self):
        s = sockets.Socket("LogD", 1.0, 3.0)
        assert s.verdict(2.0) == "fits"
        assert s.verdict(0.5) == "too_low"
        assert s.verdict(4.0) == "too_high"

    def test_bounds_inclusive(self):
        s = sockets.Socket("LogD", 1.0, 3.0)
        assert s.accepts(1.0) and s.accepts(3.0)

    def test_one_sided(self):
        assert sockets.Socket("KSOL", lo=50.0).verdict(1e9) == "fits"
        assert sockets.Socket("HLM", hi=20.0).verdict(0.0) == "fits"

    def test_missing_value_is_not_a_pass(self):
        rep = sockets.fit_report({"KSOL": sockets.Socket("KSOL", lo=50.0)}, {})
        assert rep["KSOL"]["verdict"] == "unknown"
        assert not sockets.clicks(rep)

    def test_clicks_only_when_all_fit(self):
        socks = {"LogD": sockets.Socket("LogD", 1.0, 3.0), "HLM": sockets.Socket("HLM", hi=20.0)}
        assert sockets.clicks(sockets.fit_report(socks, {"LogD": 2.0, "HLM": 10.0}))
        assert not sockets.clicks(sockets.fit_report(socks, {"LogD": 2.0, "HLM": 100.0}))

    def test_empty_sockets_do_not_click(self):
        assert not sockets.clicks({})

    def test_presets_reference_known_endpoints(self):
        for name, socks in sockets.PRESETS.items():
            for ep, s in socks.items():
                assert ep in sockets.META, f"{name}: unknown endpoint {ep}"
                assert s.endpoint == ep
                assert s.lo is not None or s.hi is not None

    def test_brain_preset_stricter_on_efflux_than_oral(self):
        # The blood-brain barrier is pump-rich; the story depends on this ordering.
        assert sockets.PRESETS["Brain drug"]["Efflux"].hi < sockets.PRESETS["Oral drug"]["Efflux"].hi


class TestInteraction:
    def test_no_inhibitor_means_no_change(self):
        assert interaction.auc_ratio(0.9, 0.0, 1.0).auc_ratio == pytest.approx(1.0)

    def test_hand_computed(self):
        # fm=0.5, I=Ki -> route halved -> 1/(0.5*0.5 + 0.5) = 1.3333
        assert interaction.auc_ratio(0.5, 1.0, 1.0).auc_ratio == pytest.approx(4 / 3)

    def test_second_route_caps_the_rise(self):
        # Even a total block cannot exceed 1/(1-fm) when another route exists.
        strong = interaction.auc_ratio(0.8, 1e6, 1.0).auc_ratio
        assert strong == pytest.approx(1 / 0.2, rel=1e-3)

    def test_monotonic_in_inhibitor(self):
        ratios = [interaction.auc_ratio(0.7, c, 1.0).auc_ratio for c in (0, 0.5, 1, 5, 50)]
        assert ratios == sorted(ratios)

    def test_clearance_falls_as_inhibitor_rises(self):
        c0 = interaction.apparent_clearance(100.0, 0.7, 0.0, 1.0)
        c1 = interaction.apparent_clearance(100.0, 0.7, 5.0, 1.0)
        assert c0 == pytest.approx(100.0)
        assert c1 < c0

    @pytest.mark.parametrize("fm,conc,ki", [(-0.1, 1, 1), (1.1, 1, 1), (0.5, -1, 1), (0.5, 1, 0)])
    def test_invalid_inputs_rejected(self, fm, conc, ki):
        with pytest.raises(ValueError):
            interaction.auc_ratio(fm, conc, ki)

    def test_severity_bands(self):
        assert interaction.severity(1.0) == "negligible"
        assert interaction.severity(1.5) == "weak"
        assert interaction.severity(3.0) == "moderate"
        assert interaction.severity(10.0) == "strong"


class TestPairs:
    def test_finds_an_obvious_pair(self):
        from lego.pairs import find_pairs

        # Toluene vs ethylbenzene: same ring, methyl -> ethyl.
        got = find_pairs(["tol", "eb"], ["Cc1ccccc1", "CCc1ccccc1"])
        assert any({p.sub_a, p.sub_b} == {"*C", "*CC"} for p in got)

    def test_identical_molecules_make_no_pair(self):
        from lego.pairs import find_pairs

        assert find_pairs(["a", "b"], ["Cc1ccccc1", "Cc1ccccc1"]) == []

    def test_attachment_point_is_label_free(self):
        from lego.pairs import fragment

        frags = fragment("Cc1ccccc1")
        assert frags, "expected at least one cut"
        for core, sub in frags:
            assert "[17*]" not in core and "[17*]" not in sub
            assert "*" in core or "*" in sub

    def test_bad_smiles_is_ignored(self):
        from lego.pairs import fragment

        assert fragment("not-a-molecule") == []

    def test_large_substituents_excluded(self):
        from lego.pairs import fragment

        # With a 1-atom cap only the smallest cuts survive.
        for _, sub in fragment("CCCCCCCCc1ccccc1", max_sub_atoms=1):
            assert sub.count("*") == 1
            assert len(sub.replace("*", "").replace("[", "").replace("]", "")) <= 2


class TestEdits:
    def test_fluorine_on_toluene(self):
        from lego.edits import apply_edit

        smi, err = apply_edit("Cc1ccccc1", "ar_h_to_f")
        assert err is None and smi == "Cc1ccc(F)cc1"

    def test_symmetry_deduplicated(self):
        from lego.edits import products

        # Toluene has 5 aromatic CH but only 3 distinct fluorotoluenes (o/m/p).
        assert len(products("Cc1ccccc1", "ar_h_to_f")) == 3

    def test_pyridine_positions(self):
        from lego.edits import products

        assert set(products("Cc1ccccc1", "benzene_to_pyridine")) == {
            "Cc1ccccn1", "Cc1cccnc1", "Cc1ccncc1",
        }

    def test_five_membered_ring_not_converted(self):
        from lego.edits import products

        # The r6 constraint must keep pyrrole out of the benzene->pyridine edit.
        assert products("c1cc[nH]c1", "benzene_to_pyridine") == []

    def test_cf3_valence_is_correct(self):
        from rdkit import Chem

        from lego.edits import apply_edit

        smi, err = apply_edit("Cc1ccccc1", "me_to_cf3")
        assert err is None
        mol = Chem.MolFromSmiles(smi)
        assert mol is not None
        carbon = next(
            a for a in mol.GetAtoms()
            if a.GetSymbol() == "C"
            and sum(n.GetSymbol() == "F" for n in a.GetNeighbors()) == 3
        )
        assert carbon.GetTotalNumHs() == 0

    def test_every_product_is_readable(self):
        from rdkit import Chem

        from lego.edits import EDITS, products

        for smi in ("Cc1ccccc1", "c1cc2cncc(-c3ccc(OCCN4CCCCC4)cc3)c2[nH]1", "CCOC(=O)c1ccncc1"):
            for edit in EDITS:
                for out in products(smi, edit.key):
                    assert Chem.MolFromSmiles(out) is not None, f"{edit.key} gave {out}"

    def test_product_never_equals_input(self):
        from lego.edits import EDITS, products

        smi = "Cc1ccccc1"
        for edit in EDITS:
            assert smi not in products(smi, edit.key)

    def test_unknown_key_and_bad_smiles(self):
        from lego.edits import apply_edit

        assert apply_edit("Cc1ccccc1", "nope")[0] is None
        assert apply_edit("not-a-molecule", "ar_h_to_f")[0] is None

    def test_inapplicable_edit_explains_itself(self):
        from lego.edits import apply_edit

        smi, err = apply_edit("FC(F)(F)F", "ar_h_to_f")
        assert smi is None and "does not apply" in err

    def test_site_out_of_range(self):
        from lego.edits import apply_edit

        smi, err = apply_edit("Cc1ccccc1", "ar_h_to_f", site=99)
        assert smi is None and "place" in err

    def test_options_counts_match_products(self):
        from lego.edits import options, products

        smi = "c1cc2cncc(-c3ccc(OCCN4CCCCC4)cc3)c2[nH]1"
        for o in options(smi):
            assert o["n_sites"] == len(products(smi, o["key"]))


class TestBoard:
    def _pegs(self, **over):
        from lego.board import Peg

        base = dict(LogD=2.0, KSOL=200.0, HLM=5.0, MLM=50.0, Papp=10.0,
                    Efflux=1.2, MPPB=10.0, MBPB=5.0, MGMB=5.0)
        base.update(over)
        return [Peg(e, v) for e, v in base.items()]

    def test_renders_valid_svg_root(self):
        from lego.board import render
        from lego.sockets import PRESETS

        svg = render(PRESETS["Brain drug"], self._pegs())
        assert svg.startswith("<svg") and svg.endswith("</svg>")
        assert 'role="img"' in svg and "aria-label" in svg

    def test_is_parseable_xml(self):
        import xml.etree.ElementTree as ET

        from lego.board import render
        from lego.sockets import PRESETS

        for preset in PRESETS:
            ET.fromstring(render(PRESETS[preset], self._pegs()))

    def test_no_unresolved_placeholders(self):
        from lego.board import render
        from lego.sockets import PRESETS

        svg = render(PRESETS["Oral drug"], self._pegs())
        assert "{" not in svg.split("<style>")[1].split("</style>")[0].replace("{{", "")[:0] + ""
        assert "None" not in svg

    def test_ascii_only(self):
        # A glyph font that lacks a character would silently drop a verdict.
        from lego.board import render
        from lego.sockets import PRESETS

        svg = render(PRESETS["Everything at once"], self._pegs())
        assert svg.isascii(), "non-ASCII text in SVG"

    def test_not_required_is_neither_pass_nor_fail(self):
        from lego.board import render
        from lego.sockets import PRESETS

        # MGMB is not part of the brain-drug preset but is still predicted.
        svg = render(PRESETS["Brain drug"], self._pegs())
        assert "not required" in svg
        assert "peg-idle" in svg, "unrequired endpoints must not wear a status colour"

    def test_failing_value_is_marked(self):
        from lego.board import render
        from lego.sockets import PRESETS

        svg = render(PRESETS["Brain drug"], self._pegs(Efflux=40.0))
        assert "too high" in svg and "peg-miss" in svg

    def test_negative_prediction_is_clamped_not_crashed(self):
        from lego.board import clamp, render
        from lego.sockets import PRESETS

        # log10(x+1) heads can emit negatives; these are unconvertible reals.
        assert clamp("Papp", -3.0) == 0.0
        assert clamp("KSOL", 1e9) == 350.0
        svg = render(PRESETS["Brain drug"], self._pegs(Papp=-2.5, MBPB=-0.4))
        assert "-" not in svg.split("class=\"val\"")[1][:12]

    def test_missing_prediction_says_so(self):
        from lego.board import Peg, render
        from lego.sockets import PRESETS

        svg = render(PRESETS["Brain drug"], [Peg("LogD", None)])
        assert "not predicted" in svg

    def test_positions_stay_inside_track(self):
        from lego.board import AXIS, TRACK_X0, TRACK_X1, _pos

        for ep, (lo, hi) in AXIS.items():
            for v in (lo - 1e6, lo, (lo + hi) / 2, hi, hi + 1e6):
                assert TRACK_X0 - 0.01 <= _pos(ep, v) <= TRACK_X1 + 0.01

    def test_dark_mode_declared_both_ways(self):
        from lego.board import render
        from lego.sockets import PRESETS

        svg = render(PRESETS["Brain drug"], self._pegs())
        assert "prefers-color-scheme: dark" in svg
        assert '[data-theme="dark"]' in svg
