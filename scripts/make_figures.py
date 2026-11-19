"""Paper figures, drawn only from saved results files (no API calls).

Makes:
  lambda_sweep_dev  - dev Correct (overall and answerable) of B1 for each lambda, with the
                      reproduced TG-RAG (tgrag) as a dashed reference line.
  robustness_test   - test Correct of tgrag and B1 (lambda 1) as the share of shifted stored
                      timestamps grows (0 = clean main runs; 0.1/0.2/0.3 = noise runs).
  per_type_test     - test Correct of tgrag and B1 for each of the four question types.

Each figure is saved as PNG (300 dpi) and PDF in paper/figures/, with the plotted numbers as CSV.

Run from the Temporal-GraphRAG folder:
    python scripts/analyze.py runs/dev_*.judged.jsonl --reference tgrag --out results_dev   # refresh the CSV
    python scripts/make_figures.py
The test figures read results_test/ and results_test_noise*/, written by the analyze commands at the
end of scripts/run_test_suite.bat.
"""
import csv
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # draw to files, no window
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
FIG = ROOT / "paper" / "figures"

# Colours: categorical slot 1 (blue) for our method, neutral grey for the baseline reference line
BLUE, GREY, INK, MUTED = "#2a78d6", "#8a8984", "#0b0b0b", "#52514e"
CHOSEN_LAMBDA = 1.0  # locked on dev (highest dev Correct); marked on the chart


def read_overall(path: Path) -> dict:
    """Read analyze.py's overall.csv into {run name: row dict with float metrics}."""
    rows = {}
    with open(path, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            rows[r["run"]] = {k: (float(v) if k != "run" else v) for k, v in r.items()}
    return rows


def style_axes(ax) -> None:
    """Recessive axes: no top/right spines, light horizontal grid, muted tick labels."""
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color("#c9c8c2")
    ax.grid(axis="y", color="#e6e5e0", linewidth=0.8)
    ax.set_axisbelow(True)
    ax.tick_params(colors=MUTED, labelsize=8)


def lambda_sweep_dev() -> None:
    """Dev-set lambda sweep: B1 Correct vs lambda, overall and answerable-only, against tgrag."""
    rows = read_overall(ROOT / "results" / "analysis" / "results_dev" / "overall.csv")
    # B1 runs are named B1_lam<value>; lambda = 1000 is the hard-filter limit
    sweep = sorted((float(name[len("B1_lam"):]), r) for name, r in rows.items() if name.startswith("B1_lam"))
    if "tgrag" not in rows or not sweep:
        sys.exit("results_dev/overall.csv lacks tgrag or B1_lam* rows; run analyze.py on the dev runs first")
    base = rows["tgrag"]

    # Save the exact numbers that are plotted
    FIG.mkdir(parents=True, exist_ok=True)
    with open(FIG / "lambda_sweep_dev.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["lambda", "correct", "correct_ans", "correct_unans", "n",
                    "tgrag_correct", "tgrag_correct_ans"])
        for lam, r in sweep:
            w.writerow([f"{lam:g}", f"{r['correct']:.4f}", f"{r['correct_ans']:.4f}", f"{r['correct_unans']:.4f}",
                        int(r["n"]), f"{base['correct']:.4f}", f"{base['correct_ans']:.4f}"])

    # Two small panels (one series each) instead of four lines on one chart.
    # The tried lambdas are discrete settings, so they sit at evenly spaced positions.
    lams = [lam for lam, _ in sweep]
    xs = list(range(len(lams)))
    labels = [f"{x:g}" if x < 1000 else "1000\n(≈ hard filter)" for x in lams]
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.9), sharey=True)
    for ax, key, title in [(axes[0], "correct", "All dev questions (n = 37)"),
                           (axes[1], "correct_ans", "Answerable only (n = 27)")]:
        vals = [r[key] for _, r in sweep]
        ax.plot(xs, vals, color=BLUE, linewidth=2, marker="o", markersize=5, zorder=3)
        ax.axhline(base[key], color=GREY, linewidth=1.2, linestyle="--", zorder=2)
        ax.text(xs[-1], base[key] - 0.012, f"TG-RAG reproduced {base[key]:.3f}", color=MUTED,
                fontsize=7.5, ha="right", va="top")
        # Mark the dev-chosen lambda with its value
        ci = lams.index(CHOSEN_LAMBDA)
        ax.scatter([ci], [vals[ci]], s=70, facecolor="white", edgecolor=BLUE, linewidth=2, zorder=4)
        ax.annotate(f"λ = 1: {vals[ci]:.3f}", (ci, vals[ci]), xytext=(0, 8),
                    textcoords="offset points", ha="center", fontsize=7.5, color=INK)
        ax.set_xticks(xs)
        ax.set_xticklabels(labels)
        ax.set_xlim(-0.4, xs[-1] + 0.4)
        ax.set_xlabel("λ (kernel strength)", fontsize=8, color=MUTED)
        ax.set_title(title, fontsize=9, color=INK, loc="left")
        style_axes(ax)
    axes[0].set_ylabel("Correct (LLM judge)", fontsize=8, color=MUTED)
    axes[0].set_ylim(0.30, 0.58)
    fig.suptitle("B1 soft time kernel: dev-set sweep of λ", fontsize=10, color=INK, x=0.01, ha="left")
    fig.tight_layout()
    for ext in ("png", "pdf"):
        fig.savefig(FIG / f"lambda_sweep_dev.{ext}", dpi=300, facecolor="white")
    plt.close(fig)
    print(f"wrote {FIG / 'lambda_sweep_dev.png'} (+ .pdf, .csv)")


def save(fig, name: str) -> None:
    """Save a figure as PNG (300 dpi) and PDF in paper/figures/ and close it."""
    for ext in ("png", "pdf"):
        fig.savefig(FIG / f"{name}.{ext}", dpi=300, facecolor="white")
    plt.close(fig)
    print(f"wrote {FIG / (name + '.png')} (+ .pdf, .csv)")


def read_b1_significance(folder: Path) -> dict:
    """Return {'all': row, 'ans': row} with the paired-bootstrap row of the B1 run in an analyze folder."""
    out = {}
    for key, name in (("all", "significance.csv"), ("ans", "significance_answerable.csv")):
        with open(folder / name, encoding="utf-8") as f:
            out[key] = next(r for r in csv.DictReader(f) if r["run"].startswith("B1_lam1"))
    return out


def robustness_test() -> None:
    """Test-set robustness: Correct vs share of shifted timestamps, tgrag vs B1, two panels."""
    rates = [0.0, 0.1, 0.2, 0.3]
    # Noise 0 = the clean main runs; the other rates come from the noise runs
    pts, sig = {"tgrag": [], "B1": []}, []
    for r in rates:
        folder = ROOT / "results" / "analysis" / ("results_test" if r == 0 else f"results_test_noise{r:g}")
        rows = read_overall(folder / "overall.csv")
        suffix = "" if r == 0 else f"_noise{r:g}"
        pts["tgrag"].append(rows["tgrag" + suffix])
        pts["B1"].append(rows["B1_lam1" + suffix])
        sig.append(read_b1_significance(folder))

    # Save the plotted numbers plus the paired-bootstrap result (B1 - tgrag) at each rate
    FIG.mkdir(parents=True, exist_ok=True)
    with open(FIG / "robustness_test.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["noise_rate", "tgrag_correct", "B1_correct", "delta", "ci_low", "ci_high", "p",
                    "tgrag_correct_ans", "B1_correct_ans", "delta_ans", "ci_low_ans", "ci_high_ans", "p_ans"])
        for i, r in enumerate(rates):
            row = [r]
            for key, metric in (("all", "correct"), ("ans", "correct_ans")):
                s = sig[i][key]
                row += [f"{pts['tgrag'][i][metric]:.4f}", f"{pts['B1'][i][metric]:.4f}",
                        f"{float(s['delta_correct']):.4f}", f"{float(s['ci_low']):.4f}",
                        f"{float(s['ci_high']):.4f}", s["p"]]
            w.writerow(row)

    xs = [100 * r for r in rates]
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.9), sharey=True)
    for ax, metric, key, title in [(axes[0], "correct", "all", "All test questions (n = 152)"),
                                   (axes[1], "correct_ans", "ans", "Answerable only (n = 116)")]:
        for run, color, label in [("tgrag", GREY, "TG-RAG (hard filter)"), ("B1", BLUE, "B1, λ = 1 (ours)")]:
            vals = [p[metric] for p in pts[run]]
            ax.plot(xs, vals, color=color, linewidth=2, marker="o", markersize=5, zorder=3, label=label)
            # Direct value label at the right end of each line (text in ink, not the series colour)
            ax.annotate(f"{vals[-1]:.3f}", (xs[-1], vals[-1]), xytext=(6, 0), textcoords="offset points",
                        va="center", fontsize=7.5, color=INK)
        # Star where the paired-bootstrap 95 % CI of B1 - tgrag lies above zero
        for i in range(len(rates)):
            if float(sig[i][key]["ci_low"]) > 0:
                ax.annotate("*", (xs[i], pts["B1"][i][metric]), xytext=(0, 4), textcoords="offset points",
                            ha="center", fontsize=12, color=INK)
        ax.set_xticks(xs)
        ax.set_xticklabels(["0\n(clean)", "10", "20", "30"])
        ax.set_xlim(-3, 37)
        ax.set_xlabel("Stored timestamps shifted by one quarter (%)", fontsize=8, color=MUTED)
        ax.set_title(title, fontsize=9, color=INK, loc="left")
        style_axes(ax)
    axes[0].set_ylabel("Correct (LLM judge)", fontsize=8, color=MUTED)
    axes[0].set_ylim(0.45, 0.68)
    axes[0].legend(frameon=False, fontsize=7.5, loc="lower left")
    fig.suptitle("Robustness to noisy timestamps (test set; * = B1 > TG-RAG, paired-bootstrap 95 % CI above 0)",
                 fontsize=10, color=INK, x=0.01, ha="left")
    fig.tight_layout()
    save(fig, "robustness_test")


def per_type_test() -> None:
    """Test-set Correct per question type for tgrag and B1, as horizontal grouped bars."""
    from matplotlib.patches import Patch

    rows = {}
    with open(ROOT / "results" / "analysis" / "results_test" / "by_type.csv", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["split"] == "question_type" and r["run"] in ("tgrag", "B1_lam1"):
                rows[(r["group"], r["run"])] = (float(r["correct"]), int(r["n"]))
    # Largest question type on top
    types = sorted({g for g, _ in rows}, key=lambda g: -rows[(g, "tgrag")][1])
    pretty = {"multi-time query": "Multi-time", "relative-time query": "Relative-time",
              "single-time query|multi-companies": "Single-time, multi-company",
              "single-time query|multi-keywords": "Single-time, multi-keyword"}

    with open(FIG / "per_type_test.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["question_type", "n", "tgrag_correct", "B1_correct", "delta"])
        for g in types:
            t, b = rows[(g, "tgrag")][0], rows[(g, "B1_lam1")][0]
            w.writerow([g, rows[(g, "tgrag")][1], f"{t:.4f}", f"{b:.4f}", f"{b - t:+.4f}"])

    fig, ax = plt.subplots(figsize=(7.0, 3.0))
    h = 0.36  # bar thickness; a small gap is left between the two bars of a pair
    for i, g in enumerate(types):
        y = len(types) - 1 - i
        for run, color, off in [("tgrag", GREY, h / 2 + 0.02), ("B1_lam1", BLUE, -h / 2 - 0.02)]:
            v = rows[(g, run)][0]
            ax.barh(y + off, v, height=h, color=color, zorder=3)
            ax.text(v + 0.01, y + off, f"{v:.3f}", va="center", fontsize=7.5, color=INK)
    ax.set_yticks(range(len(types)))
    ax.set_yticklabels([f"{pretty.get(g, g)} (n = {rows[(g, 'tgrag')][1]})" for g in reversed(types)])
    ax.set_xlim(0, 0.85)
    ax.set_xlabel("Correct (LLM judge)", fontsize=8, color=MUTED)
    style_axes(ax)
    ax.grid(axis="y", visible=False)
    ax.grid(axis="x", color="#e6e5e0", linewidth=0.8)
    ax.legend(handles=[Patch(color=GREY, label="TG-RAG (hard filter)"), Patch(color=BLUE, label="B1, λ = 1 (ours)")],
              frameon=False, fontsize=7.5, loc="lower left", bbox_to_anchor=(0, 1.0), ncol=2,
              borderaxespad=0.2)  # one row above the bars, so it never covers a bar
    fig.suptitle("Correct by question type (test set; exploratory, not pre-registered)",
                 fontsize=10, color=INK, x=0.01, ha="left")
    fig.tight_layout()
    save(fig, "per_type_test")


if __name__ == "__main__":
    lambda_sweep_dev()
    robustness_test()
    per_type_test()
