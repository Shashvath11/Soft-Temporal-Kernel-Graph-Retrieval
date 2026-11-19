"""Unit tests for the soft time kernel. Run: python -m pytest src/softtime/tests -q"""
import math

from softtime.soft_time import (clean_ts, corrupt_timestamp, fiscal_aliases, hierarchy_distance,
                                 kappa, shift_quarters, ts_path)


def test_paths():
    assert ts_path("2023") == ("2023",)
    assert ts_path('"2023-q1"') == ("2023", "2023-Q1")
    assert ts_path("2023-05") == ("2023", "2023-Q2", "2023-05")
    assert ts_path("2023-05-17")[-1] == "2023-05-17"
    assert ts_path("FY23") is None
    assert clean_ts(" '2023-q4' ") == "2023-Q4"


def test_distances():
    assert hierarchy_distance("2023-Q1", "2023-Q1") == 0
    assert hierarchy_distance("2023-Q1", "2023") == 0          # descendant counts as in scope
    assert hierarchy_distance("2023-02", "2023-Q1") == 0
    assert hierarchy_distance("2023", "2023-Q1") == 1          # coarser fact
    assert hierarchy_distance("2023-Q2", "2023-Q1") == 2       # sibling quarters
    assert hierarchy_distance("2022-Q4", "2023-Q1") == 4       # across years, via root
    assert hierarchy_distance("2022", "2023") == 2
    assert hierarchy_distance("bad", "2023") is None


def test_kappa_limits():
    q = ["2023-Q1"]
    assert kappa("2023-Q1", q, lam=1.0) == 1.0
    assert math.isclose(kappa("2023-Q2", q, lam=1.0), math.exp(-2))
    # very large lambda reproduces TG-RAG's hard filter
    assert kappa("2023-Q2", q, lam=1e6) == 0.0
    assert kappa("2023-01-15", q, lam=1e6) == 1.0
    # lambda = 0 means no time restriction
    assert kappa("2019-Q3", q, lam=0.0) == 1.0
    assert kappa("unknown", q, lam=1.0) == 0.0
    # multi-period query: best matching period wins
    assert kappa("2023-Q3", ["2023-Q1", "2023-Q3"], lam=2.0) == 1.0


def test_shift_and_alias():
    assert shift_quarters("2023-Q4", 1) == "2024-Q1"
    assert shift_quarters("2023-Q1", -1) == "2022-Q4"
    assert shift_quarters("2023-02", 1) == "2023-05"
    assert shift_quarters("2023", -1) == "2022"
    assert fiscal_aliases("2023-Q2", "WESTERN DIGITAL CORPORATION", "REVENUE",
                          {"WESTERN DIGITAL": -2}) == ["2022-Q4"]
    assert kappa("2023-Q2", ["2022-Q4"], lam=5.0, aliases=["2022-Q4"]) == 1.0


def test_noise_is_deterministic_and_rate_correct():
    facts = [(f"2023-Q{q}", f"E{i}", "REVENUE") for i in range(2000) for q in (1, 2)]
    changed = [corrupt_timestamp(ts, s, t, 0.2, seed=13) != ts for ts, s, t in facts]
    assert abs(sum(changed) / len(changed) - 0.2) < 0.03
    # same fact, same result, regardless of entity order
    assert corrupt_timestamp("2023-Q1", "A", "B", 0.5, 1) == corrupt_timestamp("2023-Q1", "B", "A", 0.5, 1)
    assert corrupt_timestamp("2023-Q1", "A", "B", 0.0, 1) == "2023-Q1"
