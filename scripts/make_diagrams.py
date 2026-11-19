"""Architecture and workflow diagrams for the paper, thesis and Review 3 (no API calls).

  architecture  The system: offline graph building, the online retrieval pipeline (TG-RAG's steps,
                with the steps we changed highlighted), and the evaluation stage.
  workflow      The research workflow from data subset to paper, with the pre-registration point.

Both are drawn with matplotlib (this script is the editable source) and saved as PNG (300 dpi) and
PDF in paper/figures/.

Run from the Temporal-GraphRAG folder:
    python scripts/make_diagrams.py
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # draw to files, no window
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
FIG = ROOT / "paper" / "figures"

# Colours: blue = our extension, grey = TG-RAG / unchanged, light fills keep text readable in print
OURS_FILL, OURS_EDGE = "#dbe9fa", "#2a78d6"
BASE_FILL, BASE_EDGE = "#f1f0ec", "#8a8984"
EVAL_FILL, EVAL_EDGE = "#ffffff", "#52514e"
INK, MUTED = "#0b0b0b", "#52514e"


def box(ax, x, y, w, h, title, body="", kind="base"):
    """Draw a rounded box with a bold title and an optional smaller body; (x, y) is the lower-left corner."""
    fill, edge = {"ours": (OURS_FILL, OURS_EDGE), "base": (BASE_FILL, BASE_EDGE),
                  "eval": (EVAL_FILL, EVAL_EDGE)}[kind]
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.08",
                                facecolor=fill, edgecolor=edge, linewidth=1.4))
    if body:
        # push the body below however many lines the title takes, so they never overlap
        n_title = title.count("\n") + 1
        ax.text(x + w / 2, y + h - 0.14, title, ha="center", va="top", fontsize=8.2, fontweight="bold", color=INK)
        ax.text(x + w / 2, y + h - 0.2 - 0.2 * n_title, body, ha="center", va="top", fontsize=6.9,
                color=MUTED, linespacing=1.3)
    else:
        ax.text(x + w / 2, y + h / 2, title, ha="center", va="center", fontsize=8.2, fontweight="bold", color=INK)


def arrow(ax, x1, y1, x2, y2, label="", style="-|>", color=MUTED, dashed=False):
    """Draw an arrow from (x1, y1) to (x2, y2), with an optional small label at its middle."""
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle=style, mutation_scale=10, color=color,
                                 linewidth=1.1, linestyle="--" if dashed else "-", shrinkA=2, shrinkB=2))
    if label:
        ax.text((x1 + x2) / 2 + 0.06, (y1 + y2) / 2, label, fontsize=6.5, color=MUTED, va="center")


def section(ax, x, y, text):
    """Section heading above a group of boxes."""
    ax.text(x, y, text, fontsize=9, fontweight="bold", color=INK, ha="left", va="bottom")


def save(fig, name):
    """Save a figure as PNG (300 dpi) and PDF in paper/figures/ and close it."""
    FIG.mkdir(parents=True, exist_ok=True)
    for ext in ("png", "pdf"):
        fig.savefig(FIG / f"{name}.{ext}", dpi=300, facecolor="white", bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {FIG / (name + '.png')} (+ .pdf)")


def architecture():
    """System architecture: offline build, online retrieval (changed steps in blue), evaluation."""
    fig, ax = plt.subplots(figsize=(10, 6.4))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6.6)
    ax.axis("off")

    # ---- offline: graph building (TG-RAG's pipeline, run once) ----
    section(ax, 0.1, 6.25, "Offline (once): temporal knowledge graph")
    box(ax, 0.1, 5.0, 1.9, 1.1, "96 earnings-call\ntranscripts", "6 companies, ECT-QA")
    box(ax, 2.4, 5.0, 2.2, 1.1, "Fact extraction", "gemini-2.5-flash-lite\nentities, dated relations")
    box(ax, 5.0, 5.0, 2.4, 1.1, "Temporal graph", "entities + relations, each fact\nwith timestamp & source chunk;\ntime tree year→quarter→month→day")
    box(ax, 7.8, 5.0, 2.1, 1.1, "Vector stores", "text-embedding-3-small\nrelations, chunks")
    arrow(ax, 2.0, 5.55, 2.4, 5.55)
    arrow(ax, 4.6, 5.55, 5.0, 5.55)
    arrow(ax, 7.4, 5.55, 7.8, 5.55)

    # ---- online: retrieval and answering ----
    section(ax, 0.1, 4.55, "Online (per question): retrieval and answer")
    y, h = 2.85, 1.55
    box(ax, 0.1, y, 1.55, h, "1 Question\ntime extraction", "gpt-4o-mini\n(TG-RAG, unchanged)")
    box(ax, 1.85, y, 1.9, h, "2 Seeding", "60 similar relations\nTG-RAG: keep if in period\nOurs: keep if κ ≥ 0.05,\nseed weight = κ\n(C/BC: BM25 + dense, RRF)", "ours")
    box(ax, 3.95, y, 1.9, h, "3 Personalized\nPageRank", "seeds weighted by κ\nB12: walk weights κ\nB1QI: question-independent\ndecay (ablation)", "ours")
    box(ax, 6.05, y, 1.85, h, "4 Evidence scoring", "edge score × κ\nper source chunk\n(TG-RAG: × 0/1)", "ours")
    box(ax, 8.1, y, 1.8, h, "5 Pack & answer", "top 20 chunks,\n≤ 12,000 tokens\ngpt-4o-mini")
    for x1, x2 in [(1.65, 1.85), (3.75, 3.95), (5.85, 6.05), (7.9, 8.1)]:
        arrow(ax, x1, y + h / 2, x2, y + h / 2)
    # the graph feeds steps 2-4 (one dashed arrow, labelled, keeps the picture uncluttered)
    arrow(ax, 6.2, 5.0, 4.9, y + h, dashed=True)
    ax.text(5.65, 4.62, "graph used in steps 2–4", fontsize=6.5, color=MUTED, ha="left")
    # kernel module under steps 2-4, feeding each of them
    box(ax, 1.85, 1.45, 6.05, 1.0, "Soft time kernel  (soft_time.py)",
        "κ(τ) = max over asked periods t of exp(−λ·d_H(τ, t)),  d_H = steps in the time tree\n"
        "λ = 1 (chosen on dev), drop if κ < 0.05;  λ → ∞ gives TG-RAG's 0/1 filter",
        "ours")
    for xa in (2.8, 4.9, 6.97):
        arrow(ax, xa, 2.45, xa, y, color=OURS_EDGE)
    # noise injection changes the stored dates the kernel reads
    box(ax, 0.1, 1.45, 1.55, 1.0, "N3 noise", "shift ρ of stored\ndates ±1 quarter", "ours")
    arrow(ax, 1.65, 1.95, 1.85, 1.95, color=OURS_EDGE, dashed=True)

    # ---- evaluation ----
    box(ax, 8.1, 0.75, 1.8, 1.7, "Evaluation", "LLM judge (gpt-4o-mini)\nCorrect / Refusal / Incorrect\nROUGE-L, token F1\nanswerable / unanswerable\npaired bootstrap", "eval")
    arrow(ax, 9.0, y, 9.0, 2.45)

    # legend
    ax.add_patch(FancyBboxPatch((0.1, 0.35), 0.3, 0.22, boxstyle="round,pad=0.01", facecolor=OURS_FILL, edgecolor=OURS_EDGE))
    ax.text(0.5, 0.46, "our extension, swapped in at run time", fontsize=7.2, va="center", color=INK)
    ax.add_patch(FancyBboxPatch((0.1, 0.0), 0.3, 0.22, boxstyle="round,pad=0.01", facecolor=BASE_FILL, edgecolor=BASE_EDGE))
    ax.text(0.5, 0.11, "TG-RAG's released code, unchanged", fontsize=7.2, va="center", color=INK)
    save(fig, "architecture")


def workflow():
    """Research workflow, left to right, with the pre-registration lock between dev and test."""
    fig, ax = plt.subplots(figsize=(10, 4.6))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 4.7)
    ax.axis("off")
    steps = [
        ("1 Subset & split", "6 companies\n37 dev / 152 test\n(seed 42)", "base"),
        ("2 Build graph", "96 transcripts\n378 chunks\n(once)", "base"),
        ("3 Reproduce\nTG-RAG", "same evidence on\n36/37 dev questions", "base"),
        ("4 Dev experiments", "λ sweep, B1, B12,\nB1QI, C, BC\n→ λ = 1 chosen", "ours"),
        ("5 Lock & pre-register", "settings fixed;\ncomparisons written\nbefore test runs", "ours"),
        ("6 Test runs", "7 main + 6 noise\n× 152 questions\n(run once)", "ours"),
        ("7 Judge & analyse", "LLM judge, ROUGE-L,\nF1, paired bootstrap", "eval"),
        ("8 Report", "tables, figures,\nmanuscript, thesis", "eval"),
    ]
    # Two rows of four wide boxes: row 1 = preparation and dev, row 2 = test and reporting
    w, h, gap = 2.2, 1.35, 0.33
    rows_y = [3.0, 1.15]
    pos = []
    for i, (t, b, k) in enumerate(steps):
        r, c = divmod(i, 4)
        x = 0.1 + c * (w + gap)
        pos.append((x, rows_y[r]))
        box(ax, x, rows_y[r], w, h, t.replace("\n", " "), b, k)
    for i in range(1, len(steps)):
        (x0, y0), (x1, y1) = pos[i - 1], pos[i]
        if y0 == y1:  # same row: arrow left to right
            arrow(ax, x0 + w, y0 + h / 2, x1, y1 + h / 2)
        else:  # row change: from the end of row 1 down to the start of row 2
            ax.plot([x0 + w / 2, x0 + w / 2, x1 + w / 2], [y0, y0 - 0.25, y0 - 0.25], color=MUTED, linewidth=1.1)
            arrow(ax, x1 + w / 2, y0 - 0.25, x1 + w / 2, y1 + h)
    # lock marker: the settings are fixed between step 5 and step 6
    xl = pos[5][0] - gap / 2
    ax.plot([xl, xl], [1.0, 2.65], color=OURS_EDGE, linewidth=1.4, linestyle=":")
    ax.text(xl, 0.82, "settings locked here", ha="center", fontsize=7, color=OURS_EDGE)
    # hand checks hang off the analysis step
    ax.text(pos[6][0] + w / 2, 0.55, "+ hand checks: 50 judged answers (blind), 100 stored dates",
            ha="center", fontsize=7, color=MUTED)
    arrow(ax, pos[6][0] + w / 2, rows_y[1], pos[6][0] + w / 2, 0.7)
    ax.text(0.1, 0.12, "Every result: command in results/SUMMARY.md; seeds 42 (split), 13 (noise), 0 (bootstrap)",
            fontsize=7.2, color=MUTED)
    save(fig, "workflow")


if __name__ == "__main__":
    architecture()
    workflow()
