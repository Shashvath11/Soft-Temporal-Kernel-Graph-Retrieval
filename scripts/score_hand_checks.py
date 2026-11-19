"""Score the hand checks after the owner has filled them in (no API calls).

Two jobs:
  answers  Joins docs/hand_checks/judge_check_50.csv (owner's blind verdicts) with the judge key
           and reports how far the LLM judge agrees with the owner: mean absolute difference,
           Pearson correlation, and agreement / Cohen's kappa on correct-vs-not (score >= 0.5).
  facts    Counts the owner's verdicts in docs/hand_checks/fact_dates_100.csv and reports the
           share of stored dates that are correct.

Rows with an empty verdict are skipped and counted, so a half-filled sheet can be scored too.
Results are printed and written to docs/hand_checks/agreement.md.

Run from the Temporal-GraphRAG folder:
    python scripts/score_hand_checks.py answers
    python scripts/score_hand_checks.py facts
"""
import argparse
import csv
import math
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HC = ROOT / "results" / "hand_checks"


def read_csv(path: Path) -> list:
    """Read a CSV written by make_hand_checks.py (utf-8 with BOM) into a list of dicts."""
    with open(path, encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def column(rows: list, prefix: str) -> str:
    """Return the name of the first column that starts with `prefix` (headers carry hints)."""
    for name in rows[0]:
        if name.startswith(prefix):
            return name
    raise KeyError(f"no column starting with {prefix!r}")


def agreement_stats(human: list, judge: list, threshold: float = 0.5) -> dict:
    """Compare two equal-length lists of 0-1 scores.

    In: the owner's scores and the judge's scores for the same answers.
    Out: dict with n, mean absolute difference, Pearson r (nan if a list is constant),
    binary agreement and Cohen's kappa where "correct" means score >= threshold.
    """
    n = len(human)
    mad = sum(abs(h - j) for h, j in zip(human, judge)) / n
    mh, mj = sum(human) / n, sum(judge) / n
    cov = sum((h - mh) * (j - mj) for h, j in zip(human, judge))
    vh, vj = sum((h - mh) ** 2 for h in human), sum((j - mj) ** 2 for j in judge)
    r = cov / math.sqrt(vh * vj) if vh > 0 and vj > 0 else float("nan")
    # Binary view: the judge and the owner agree if both call the answer correct, or both do not
    bh = [h >= threshold for h in human]
    bj = [j >= threshold for j in judge]
    p_obs = sum(a == b for a, b in zip(bh, bj)) / n
    ph, pj = sum(bh) / n, sum(bj) / n
    p_exp = ph * pj + (1 - ph) * (1 - pj)  # agreement expected by chance alone
    kappa = (p_obs - p_exp) / (1 - p_exp) if p_exp < 1 else float("nan")
    return {"n": n, "mad": mad, "pearson": r, "agree": p_obs, "kappa": kappa,
            "human_mean": mh, "judge_mean": mj}


def parse_score(text: str):
    """Turn the owner's entry into a float in [0, 1]; empty -> None. Accepts '1', '0.5', '50%'."""
    t = text.strip().replace(",", ".")
    if not t:
        return None
    v = float(t[:-1]) / 100 if t.endswith("%") else float(t)
    if not 0 <= v <= 1:
        raise ValueError(f"score {text!r} is outside 0-1")
    return v


def score_answers() -> str:
    """Join the owner's sheet with the judge key and return a markdown report."""
    sheet = read_csv(HC / "judge_check_50.csv")
    key = {r["id"]: r for r in read_csv(HC / "judge_check_50_KEY_do_not_open.csv")}
    col = column(sheet, "my_correct")
    human, judge, runs, skipped = [], [], Counter(), 0
    for r in sheet:
        v = parse_score(r[col])
        if v is None:  # not filled in yet
            skipped += 1
            continue
        human.append(v)
        judge.append(float(key[r["id"]]["judge_correct"]))
        runs[key[r["id"]]["run"]] += 1
    if not human:
        return "No verdicts filled in yet in judge_check_50.csv.\n"
    s = agreement_stats(human, judge)
    return (f"## LLM judge vs owner ({s['n']} answers scored, {skipped} still empty)\n\n"
            f"- Mean Correct: owner {s['human_mean']:.3f}, judge {s['judge_mean']:.3f}\n"
            f"- Mean absolute difference: {s['mad']:.3f}\n"
            f"- Pearson correlation: {s['pearson']:.3f}\n"
            f"- Agreement on correct (>= 0.5) vs not: {s['agree']:.1%}, Cohen's kappa {s['kappa']:.3f}\n"
            f"- Answers per run: {dict(runs)}\n")


def score_facts() -> str:
    """Count the owner's verdicts on the 100 stored facts and return a markdown report."""
    rows = read_csv(HC / "fact_dates_100.csv")
    col = column(rows, "my_verdict")
    verdicts = Counter(r[col].strip().lower() for r in rows if r[col].strip())
    filled = sum(verdicts.values())
    if not filled:
        return "No verdicts filled in yet in fact_dates_100.csv.\n"
    checkable = filled - verdicts.get("no date in text", 0) - verdicts.get("unclear", 0)
    lines = [f"## Stored fact dates ({filled} of {len(rows)} checked)\n"]
    lines += [f"- {v}: {c}" for v, c in verdicts.most_common()]
    if checkable:
        lines.append(f"- Correct dates among facts whose text gives a date: "
                     f"{verdicts.get('correct', 0)}/{checkable} = {verdicts.get('correct', 0) / checkable:.1%}")
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser(description="Score the filled-in hand-check sheets.")
    ap.add_argument("job", choices=["answers", "facts"])
    report = score_answers() if ap.parse_args().job == "answers" else score_facts()
    print(report)
    if report.startswith("No verdicts"):
        return
    # Append so that both jobs end up in the same file
    with open(HC / "agreement.md", "a", encoding="utf-8") as fh:
        fh.write(report + "\n")


if __name__ == "__main__":
    main()
