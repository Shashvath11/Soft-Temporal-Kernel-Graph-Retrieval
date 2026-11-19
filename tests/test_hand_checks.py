"""Offline tests for scripts/make_hand_checks.py (no graph or API needed)."""
import importlib.util
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    "make_hand_checks", Path(__file__).resolve().parents[1] / "scripts" / "make_hand_checks.py")
mhc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mhc)


def test_excerpt_anchors_on_number_from_fact_text():
    # The company name appears first, but the window must be centred on the quoted number.
    chunk = "Crocs, Inc. call opening. " + "filler " * 200 + "We raised wages to $15 per hour. " + "more " * 50
    out = mhc.excerpt(chunk, "Crocs raised wages to $15 per hour.", ["WAGE", "CROCS, INC."], width=120)
    assert "$15 per hour" in out


def test_excerpt_falls_back_to_entity_then_start():
    chunk = "intro " * 100 + "Home Depot opened stores." + " end" * 10
    assert "Home Depot" in mhc.excerpt(chunk, "no numbers here", ["HOME DEPOT"], width=80)
    assert mhc.excerpt("abc def", "x", ["zzz"], width=80) == "abc def"
