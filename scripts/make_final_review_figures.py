"""Extra charts for the final review, drawn from the saved test-set CSVs (no API calls).

  answer_breakdown_test  how each method's answers split into correct / refused / incorrect (all 152 questions)
  reasoning_type_test    Correct by reasoning type (comparison, list, unanswerable) for the baseline and B1
  efficiency_test        retrieved context size and wall-clock seconds per question for each method

Each chart is saved as PNG (300 dpi) and PDF in paper/figures/, with the plotted numbers as CSV.

Run from the Temporal-GraphRAG folder:
    python scripts/make_final_review_figures.py
"""
import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # draw to files, no window
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
FIG = ROOT / "paper" / "figures"
BLUE, GREY, INK, MUTED = "#2a78d6", "#8a8984", "#0b0b0b", "#52514e"
LIGHT, ORANGE = "#d3d1cb", "#d9822b"
RUNS = ["tgrag", "naive", "B1_lam1", "B12_lam1", "B1QI_lam1_alpha1", "C", "BC_lam1"]
LABEL = {"tgrag": "TG-RAG (reproduced)", "naive": "Naive RAG", "B1_lam1": "B1 soft kernel (ours)",
         "B12_lam1": "B12 kernel + walk", "B1QI_lam1_alpha1": "B1QI question-indep.", "C": "C hybrid, hard filter",
         "BC_lam1": "BC B12 + hybrid"}


def overall() -> dict:
    """Read results_test/overall.csv into {run: row}."""
    with open(ROOT / "results" / "analysis" / "results_test" / "overall.csv", encoding="utf-8") as f:
        return {r["run"]: r for r in csv.DictReader(f)}


def style(ax) -> None:
    """Recessive axes: no top/right spines, light grid, muted ticks."""
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color("#c9c8c2")
    ax.set_axisbelow(True)
    ax.tick_params(colors=MUTED, labelsize=8)


def save(fig, name: str, header: list, rows: list) -> None:
    """Write the figure (PNG + PDF) and its data (CSV)."""
    FIG.mkdir(parents=True, exist_ok=True)
    for ext in ("png", "pdf"):
        fig.savefig(FIG / f"{name}.{ext}", dpi=300, facecolor="white", bbox_inches="tight")
    plt.close(fig)
    with open(FIG / f"{name}.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    print(f"wrote {FIG / (name + '.png')} (+ .pdf, .csv)")


def answer_breakdown() -> None:
    """Stacked bars: share of correct, refused and incorrect answer elements per method (all questions)."""
    ov = overall()
    runs = list(reversed(RUNS))  # baseline on top
    fig, ax = plt.subplots(figsize=(7.2, 3.3))
    rows = []
    for i, r in enumerate(runs):
        c, rf, inc = (float(ov[r][k]) for k in ("correct", "refusal", "incorrect"))
        rows.append([r, f"{c:.4f}", f"{rf:.4f}", f"{inc:.4f}"])
        left = 0
        for v, col in ((c, BLUE if r == "B1_lam1" else GREY), (rf, LIGHT), (inc, ORANGE)):
            ax.barh(i, v, left=left, height=0.62, color=col, edgecolor="white", linewidth=1.5)
            if v >= 0.06:  # label only segments wide enough to hold text
                ax.text(left + v / 2, i, f"{v:.2f}", ha="center", va="center", fontsize=7.5,
                        color="white" if col in (BLUE, GREY, ORANGE) else INK)
            left += v
    ax.set_yticks(range(len(runs)))
    ax.set_yticklabels([LABEL[r] for r in runs])
    ax.set_xlim(0, 1)
    ax.set_xlabel("Share of answer elements (LLM judge), all 152 test questions", fontsize=8, color=MUTED)
    style(ax)
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(color=BLUE, label="Correct (B1)"), Patch(color=GREY, label="Correct (others)"),
                       Patch(color=LIGHT, label="Refusal"), Patch(color=ORANGE, label="Incorrect")],
              frameon=False, fontsize=7.5, ncol=4, loc="lower left", bbox_to_anchor=(0, 1.0))
    save(fig, "answer_breakdown_test", ["run", "correct", "refusal", "incorrect"], rows)


def reasoning_type() -> None:
    """Grouped bars: Correct by reasoning type for the baseline and B1."""
    data = {}
    with open(ROOT / "results" / "analysis" / "results_test" / "by_type.csv", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["split"] == "reasoning_type" and r["run"] in ("tgrag", "B1_lam1"):
                data[(r["group"], r["run"])] = (float(r["correct"]), int(r["n"]))
    groups = ["comparison", "enumeration", "unanswerable|out-of-scope", "unanswerable|nonfact"]
    names = {"comparison": "Comparison", "enumeration": "List of values", "unanswerable|out-of-scope": "Unanswerable:\nout of scope",
             "unanswerable|nonfact": "Unanswerable:\nnot reported"}
    fig, ax = plt.subplots(figsize=(7.2, 3.0))
    rows, w = [], 0.36
    for i, g in enumerate(groups):
        t, b = data[(g, "tgrag")][0], data[(g, "B1_lam1")][0]
        n = data[(g, "tgrag")][1]
        rows.append([g, n, f"{t:.4f}", f"{b:.4f}"])
        for off, v, col in ((-w / 2 - 0.02, t, GREY), (w / 2 + 0.02, b, BLUE)):
            ax.bar(i + off, v, width=w, color=col)
            ax.text(i + off, v + 0.015, f"{v:.3f}", ha="center", fontsize=7.5, color=INK)
    ax.set_xticks(range(len(groups)))
    ax.set_xticklabels([f"{names[g]}\n(n = {data[(g, 'tgrag')][1]})" for g in groups], fontsize=8)
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Correct (LLM judge)", fontsize=8, color=MUTED)
    ax.grid(axis="y", color="#e6e5e0", linewidth=0.8)
    style(ax)
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(color=GREY, label="TG-RAG (reproduced)"), Patch(color=BLUE, label="B1 soft kernel (ours)")],
              frameon=False, fontsize=7.5, ncol=2, loc="lower left", bbox_to_anchor=(0, 1.0))
    save(fig, "reasoning_type_test", ["reasoning_type", "n", "tgrag_correct", "B1_correct"], rows)


def efficiency() -> None:
    """Two panels: mean retrieved context tokens and mean seconds per question, per method."""
    ov = overall()
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.0))
    rows = []
    for r in RUNS:
        ctx = ov[r]["ctx_tokens"]
        rows.append([r, ctx if ctx != "nan" else "", f"{float(ov[r]['sec_per_q']):.3f}"])
    # left: context tokens (naive RAG does not record it, so it is left out)
    ctx_runs = [r for r in RUNS if ov[r]["ctx_tokens"] != "nan"]
    ax = axes[0]
    for i, r in enumerate(ctx_runs):
        v = float(ov[r]["ctx_tokens"])
        ax.barh(i, v, height=0.6, color=BLUE if r == "B1_lam1" else GREY)
        # value inside the bar end, so it never crosses the budget line
        ax.text(v - 200, i, f"{v:,.0f}", va="center", ha="right", fontsize=7, color="white")
    ax.set_yticks(range(len(ctx_runs)))
    ax.set_yticklabels([LABEL[r] for r in ctx_runs], fontsize=7.5)
    ax.invert_yaxis()
    ax.set_xlim(0, 13000)
    ax.set_xticks([0, 4000, 8000, 12000])
    ax.set_xticklabels(["0", "4,000", "8,000", "12,000"])
    ax.axvline(12000, color=MUTED, linestyle="--", linewidth=1)
    ax.text(12000, -0.75, "budget", fontsize=6.5, color=MUTED, ha="center")
    ax.set_xlabel("Mean context tokens sent to the model", fontsize=8, color=MUTED)
    style(ax)
    # right: seconds per question
    ax = axes[1]
    for i, r in enumerate(RUNS):
        v = float(ov[r]["sec_per_q"])
        ax.barh(i, v, height=0.6, color=BLUE if r == "B1_lam1" else GREY)
        ax.text(v + 0.08, i, f"{v:.2f}", va="center", fontsize=7, color=INK)
    ax.set_yticks(range(len(RUNS)))
    ax.set_yticklabels([LABEL[r] for r in RUNS], fontsize=7.5)
    ax.invert_yaxis()
    ax.set_xlim(0, 7)
    ax.set_xlabel("Mean wall-clock seconds per question", fontsize=8, color=MUTED)
    style(ax)
    fig.tight_layout()
    save(fig, "efficiency_test", ["run", "ctx_tokens", "sec_per_q"], rows)


if __name__ == "__main__":
    answer_breakdown()
    reasoning_type()
    efficiency()
