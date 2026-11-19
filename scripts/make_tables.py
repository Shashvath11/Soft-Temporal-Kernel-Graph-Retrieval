"""Paper tables, built only from saved analyze.py outputs (no API calls).

Writes to results/ (each as Markdown for reading and CSV for the paper):
  main_table        tgrag, naive, B1, B1QI on the test set: Correct overall / answerable /
                    unanswerable, ROUGE-L, F1 (answerable only), and the paired bootstrap vs tgrag.
  ablation_table    B1, B12, B1QI, C, BC on the test set vs tgrag, plus the two pre-registered
                    secondary pairs (B12 vs B1QI, B12 vs B1).
  robustness_table  tgrag vs B1 at 0 / 10 / 20 / 30 % shifted timestamps.
  dev_table         all dev runs (37 questions), for the appendix.

Run from the Temporal-GraphRAG folder, after the analyze commands in scripts/run_test_suite.bat
and the MS4 commands recorded in results/SUMMARY.md:
    python scripts/make_tables.py
"""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results"

# Display names for run ids
NAMES = {"tgrag": "TG-RAG (reproduced, hard filter)", "naive": "Naive RAG (chunks only)",
         "B1_lam1": "B1: soft time kernel, λ = 1 (ours)", "B12_lam1": "B12: B1 + κ in PageRank walk",
         "B1QI_lam1_alpha1": "B1QI: question-independent decay", "C": "C: hard filter + hybrid BM25 + dense seeding",
         "BC_lam1": "BC: B12 + hybrid seeding", "original": "TG-RAG original code"}


def read_rows(path: Path) -> list:
    """Read a CSV file into a list of dicts."""
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def by_run(path: Path) -> dict:
    """Read a CSV keyed by its 'run' column."""
    return {r["run"]: r for r in read_rows(path)}


def f3(x) -> str:
    """Format a number with 3 decimals ('–' for missing / nan)."""
    try:
        v = float(x)
    except (TypeError, ValueError):
        return "–"
    return "–" if v != v else f"{v:.3f}"


def delta_cell(row) -> str:
    """'+0.004 [−0.049, 0.059], p = 0.445' from a significance row ('–' if none)."""
    if not row:
        return "–"
    d, lo, hi = (float(row[k]) for k in ("delta_correct", "ci_low", "ci_high"))
    star = " *" if lo > 0 else ""  # 95 % CI above 0 = one-sided p < 0.025
    return f"{d:+.3f} [{lo:+.3f}, {hi:+.3f}], p = {row['p']}{star}".replace("-", "−")


def write(name: str, header: list, rows: list, notes: list) -> None:
    """Write results/<name>.csv and results/<name>.md (Markdown table plus notes)."""
    OUT.mkdir(exist_ok=True)
    with open(OUT / f"{name}.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    with open(OUT / f"{name}.md", "w", encoding="utf-8") as f:
        f.write("| " + " | ".join(header) + " |\n|" + "---|" * len(header) + "\n")
        for r in rows:
            f.write("| " + " | ".join(str(c) for c in r) + " |\n")
        f.write("\n" + "\n".join(f"- {n}" for n in notes) + "\n")
    print(f"wrote {OUT / name}.md and .csv")


def metric_cells(r: dict) -> list:
    """The five score columns shared by every table."""
    return [f3(r["correct"]), f3(r["correct_ans"]), f3(r["correct_unans"]), f3(r["rouge_l"]), f3(r["f1"])]


METRIC_HEADER = ["Correct (all)", "Correct (answerable)", "Correct (unanswerable)", "ROUGE-L", "F1"]


def main_and_ablation() -> None:
    """Main table and ablation table from results_test/ and the MS4 pairwise folders."""
    ov = by_run(ROOT / "results" / "analysis" / "results_test" / "overall.csv")
    sig = by_run(ROOT / "results" / "analysis" / "results_test" / "significance.csv")
    sig_a = by_run(ROOT / "results" / "analysis" / "results_test" / "significance_answerable.csv")
    n = int(float(ov["tgrag"]["n"]))
    header = ["Method"] + METRIC_HEADER + ["Δ Correct vs TG-RAG (all) [95% CI]", "Δ Correct vs TG-RAG (answerable) [95% CI]"]
    notes_common = [
        f"Test set: {n} questions (116 answerable, 36 unanswerable), 6 companies of ECT-QA, run once with settings locked on dev "
        "(λ = 1, κ_min = 0.05, top_k = 20, 12,000 context tokens).",
        "Correct = LLM judge (gpt-4o-mini), 0–1 per question. ROUGE-L and F1 are on answerable questions only.",
        "Δ: paired bootstrap, 1,000 resamples, seed 0; p is one-sided (share of resamples with Δ ≤ 0); * = 95% CI above 0 (one-sided p < 0.025).",
    ]

    def rows_for(runs):
        return [[NAMES[r]] + metric_cells(ov[r]) + [delta_cell(sig.get(r)), delta_cell(sig_a.get(r))] for r in runs]

    write("main_table", header, rows_for(["tgrag", "naive", "B1_lam1", "B1QI_lam1_alpha1"]), notes_common + [
        "TG-RAG's paper reports Correct = 0.599 on the full ECT-QA benchmark with its own models and judge prompts. "
        "Our reproduced TG-RAG also scores 0.599 here, by coincidence; the numbers are not comparable (different "
        "subset, judge wording and models).",
        "Naive RAG scores high on unanswerable questions mainly because it refuses often; see the answerable column.",
    ])

    # Ablation: every variant vs tgrag, then the two secondary pre-registered pairs
    rows = rows_for(["B1_lam1", "B12_lam1", "B1QI_lam1_alpha1", "C", "BC_lam1"])
    pairs = []
    for folder, a, b in [("results_test_b12_vs_b1qi", "B12_lam1", "B1QI_lam1_alpha1"),
                         ("results_test_b12_vs_b1", "B12_lam1", "B1_lam1")]:
        s = read_rows(ROOT / "results" / "analysis" / folder / "significance.csv")[0]
        sa = read_rows(ROOT / "results" / "analysis" / folder / "significance_answerable.csv")[0]
        pairs.append([f"{a.split('_')[0]} vs {b.split('_')[0]}", delta_cell(s), delta_cell(sa)])
    write("ablation_table", header, rows, notes_common)
    with open(OUT / "ablation_table.md", "a", encoding="utf-8") as f:
        f.write("\nSecondary pre-registered pairs (paired bootstrap, same settings):\n\n"
                "| Pair | Δ Correct (all) [95% CI] | Δ Correct (answerable) [95% CI] |\n|---|---|---|\n")
        for p in pairs:
            f.write("| " + " | ".join(p) + " |\n")
    with open(OUT / "ablation_pairs.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["pair", "delta_all", "delta_answerable"])
        w.writerows(pairs)


def robustness() -> None:
    """tgrag vs B1 at each noise rate (0 = clean test runs)."""
    header = ["Shifted timestamps", "TG-RAG Correct (all)", "B1 Correct (all)", "Δ (all) [95% CI]",
              "TG-RAG Correct (answerable)", "B1 Correct (answerable)", "Δ (answerable) [95% CI]"]
    rows = []
    for rate in (0, 0.1, 0.2, 0.3):
        folder = ROOT / "results" / "analysis" / ("results_test" if rate == 0 else f"results_test_noise{rate:g}")
        sfx = "" if rate == 0 else f"_noise{rate:g}"
        ov = by_run(folder / "overall.csv")
        s = by_run(folder / "significance.csv")["B1_lam1" + sfx]
        sa = by_run(folder / "significance_answerable.csv")["B1_lam1" + sfx]
        t, b = ov["tgrag" + sfx], ov["B1_lam1" + sfx]
        rows.append([f"{rate:.0%}", f3(t["correct"]), f3(b["correct"]), delta_cell(s),
                     f3(t["correct_ans"]), f3(b["correct_ans"]), delta_cell(sa)])
    write("robustness_table", header, rows, [
        "Noise: each stored timestamp is shifted by ± one quarter with the given probability (deterministic hash, seed 13).",
        "Six tests (3 rates × 2 splits); with a Bonferroni correction the threshold would be p < 0.025/6 ≈ 0.004, which none meets.",
        "B1 at 30 % noise scores above clean B1, so part of the gap is run-to-run variation.",
    ])


def dev_table() -> None:
    """All dev runs with their bootstrap vs tgrag, for the appendix."""
    ov = by_run(ROOT / "results" / "analysis" / "results_dev" / "overall.csv")
    sig = by_run(ROOT / "results" / "analysis" / "results_dev" / "significance.csv")
    order = sorted(ov, key=lambda r: (r != "tgrag", r))
    header = ["Run"] + METRIC_HEADER + ["Δ Correct vs tgrag (all) [95% CI]"]
    rows = [[NAMES.get(r, r)] + metric_cells(ov[r]) + [delta_cell(sig.get(r))] for r in order]
    write("dev_table", header, rows, [
        "Dev set: 37 questions (27 answerable, 10 unanswerable). λ = 1 was chosen here and then locked.",
        "B1_lam<x> rows form the λ sweep; λ = 1000 approximates TG-RAG's hard filter.",
    ])


if __name__ == "__main__":
    main_and_ablation()
    robustness()
    dev_table()
