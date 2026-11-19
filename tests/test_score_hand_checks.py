"""Tests for scripts/score_hand_checks.py (agreement statistics and score parsing)."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from score_hand_checks import agreement_stats, parse_score  # noqa: E402


def test_perfect_agreement_gives_kappa_one():
    s = agreement_stats([1, 0, 1, 0.5], [1, 0, 1, 0.5])
    assert s["mad"] == 0 and s["agree"] == 1 and s["kappa"] == pytest.approx(1)
    assert s["pearson"] == pytest.approx(1)


def test_kappa_corrects_for_chance():
    # observed agreement 3/4; owner says correct 1/2, judge 1/4 -> chance 0.5 -> kappa 0.5
    s = agreement_stats([1, 1, 0, 0], [1, 0, 0, 0.0])
    assert s["agree"] == pytest.approx(0.75)
    assert s["kappa"] == pytest.approx((0.75 - 0.5) / 0.5)


def test_parse_score_accepts_common_forms():
    assert parse_score("") is None
    assert parse_score("0,5") == 0.5
    assert parse_score("50%") == 0.5
    with pytest.raises(ValueError):
        parse_score("2")
