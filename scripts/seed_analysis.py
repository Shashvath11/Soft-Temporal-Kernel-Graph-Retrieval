"""Where do TG-RAG and B1 differ? Seed counts and per-question outcomes on the test set (no API calls).

Exploratory analysis for the paper's discussion (not part of the pre-registered plan). For the
answerable test questions it reports:
  - how often each run found zero seed facts (TG-RAG's hard filter can leave nothing to start from),
  - how B1 scored on the questions where TG-RAG had zero seeds ("rescued" candidates),
  - how many questions B1 wins, loses or ties against TG-RAG, and the mean gain/loss,
  - the same counts per question type.
Output: printed and written to results/seed_analysis.md.

Run from the Temporal-GraphRAG folder:
    python scripts/seed_analysis.py
"""
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(run: str) -> dict:
    """Return {qid: judged record} for runs/test_<run>.judged.jsonl."""
    out = {}
    for line in open(ROOT / f"runs/test_{run}.judged.jsonl", encoding="utf-8"):
        r = json.loads(line)
        out[r["qid"]] = r
    return out


def seeds(r: dict) -> int:
    """Number of seed entities the retriever started from (0 = no evidence passed the time filter)."""
    return int((r.get("retrieval") or {}).get("n_seeds", 0) or 0)


def main():
    sys.stdout.reconfigure(encoding="utf-8")  # the Windows console default cannot print "λ"
    t, b = load("tgrag"), load("B1_lam1")
    # keep only answerable questions: there the retriever has to find evidence
    qids = sorted(q for q in t if t[q]["gold"].strip().lower() != "unanswerable")
    lines = [f"# TG-RAG vs B1 (λ = 1) on the {len(qids)} answerable test questions (exploratory)\n",
             "Command: `python scripts/seed_analysis.py` (reads runs/test_tgrag.judged.jsonl and runs/test_B1_lam1.judged.jsonl)\n"]

    zero_t = [q for q in qids if seeds(t[q]) == 0]
    zero_b = [q for q in qids if seeds(b[q]) == 0]
    lines.append(f"- Zero seed facts: TG-RAG {len(zero_t)}, B1 {len(zero_b)}")
    if zero_t:
        got = [q for q in zero_t if seeds(b[q]) > 0]
        mt = sum(t[q]["correct"] for q in zero_t) / len(zero_t)
        mb = sum(b[q]["correct"] for q in zero_t) / len(zero_t)
        lines.append(f"- On the {len(zero_t)} questions where TG-RAG had zero seeds, B1 found seeds for {len(got)}; "
                     f"mean Correct TG-RAG {mt:.3f} vs B1 {mb:.3f}")

    # Win / loss / tie per question (a difference under 0.01 counts as a tie)
    def tally(qs):
        d = [b[q]["correct"] - t[q]["correct"] for q in qs]
        win = [x for x in d if x > 0.01]
        loss = [x for x in d if x < -0.01]
        return len(win), len(loss), len(d) - len(win) - len(loss), sum(win), sum(loss)

    w, l, ti, sw, sl = tally(qids)
    lines.append(f"- Per question: B1 better on {w}, worse on {l}, tied on {ti} "
                 f"(sum of gains +{sw:.2f}, sum of losses {sl:.2f}, net {sw + sl:+.2f} of {len(qids)} questions)")
    same_ctx = sum(1 for q in qids if t[q]["retrieval"].get("chunk_hashes") == b[q]["retrieval"].get("chunk_hashes"))
    lines.append(f"- Identical retrieved context (same chunks, same order): {same_ctx} of {len(qids)} questions\n")

    lines.append("| Question type | n | TG-RAG zero seeds | B1 better | B1 worse | tied | net Δ (sum) |\n|---|---|---|---|---|---|---|")
    by_type = defaultdict(list)
    for q in qids:
        by_type[t[q]["question_type"]].append(q)
    for typ in sorted(by_type, key=lambda k: -len(by_type[k])):
        qs = by_type[typ]
        w, l, ti, sw, sl = tally(qs)
        z = sum(1 for q in qs if seeds(t[q]) == 0)
        lines.append(f"| {typ} | {len(qs)} | {z} | {w} | {l} | {ti} | {sw + sl:+.2f} |")

    text = "\n".join(lines) + "\n"
    print(text)
    (ROOT / "results").mkdir(exist_ok=True)
    (ROOT / "results" / "seed_analysis.md").write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
