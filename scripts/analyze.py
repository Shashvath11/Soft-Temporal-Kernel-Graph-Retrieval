"""Results tables, per-question-type breakdowns and paired bootstrap significance.

Usage:
    python scripts/analyze.py runs/test_*.judged.jsonl --reference tgrag --out results

Prints Markdown tables and writes results/overall.csv, results/by_type.csv, results/significance.csv.
Only questions answered by EVERY run are compared, so the runs are paired.
ROUGE-L and F1 are averaged over answerable questions only (unanswerable gold has no text).
correct_ans / correct_unans split Correct into answerable questions (finding the facts) and
unanswerable ones (refusing); report both, because refusing everything scores well on the second.
"""
import argparse
import glob
import csv
import json
import random
from collections import defaultdict
from pathlib import Path

METRICS = ["correct", "refusal", "incorrect", "rouge_l", "f1"]


def load(paths):
    runs = defaultdict(dict)
    for p in paths:
        for line in open(p, encoding="utf-8"):
            if line.strip():
                r = json.loads(line)
                runs[r["run"]][r["qid"]] = r
    return runs


def summarize(rows):
    n = len(rows)
    ans = [r for r in rows if r["gold"].strip().lower() != "unanswerable"]
    out = {"n": n}
    for k in ("correct", "refusal", "incorrect"):
        out[k] = sum(r[k] for r in rows) / n if n else 0.0
    for k in ("rouge_l", "f1"):
        out[k] = sum(r[k] for r in ans) / len(ans) if ans else 0.0
    una = [r for r in rows if r["gold"].strip().lower() == "unanswerable"]
    # Correct split: answerable questions test finding facts; unanswerable ones test refusing
    out["correct_ans"] = sum(r["correct"] for r in ans) / len(ans) if ans else float("nan")
    out["correct_unans"] = sum(r["correct"] for r in una) / len(una) if una else float("nan")
    out["sec_per_q"] = sum(r.get("seconds", 0) for r in rows) / n if n else 0.0
    toks = [r.get("retrieval", {}).get("context_tokens") for r in rows]
    toks = [t for t in toks if t is not None]
    out["ctx_tokens"] = sum(toks) / len(toks) if toks else float("nan")
    return out


def bootstrap(a, b, iters=1000, seed=0):
    """Paired bootstrap on per-question Correct: mean(b - a), 95% CI, one-sided p (b <= a)."""
    rng = random.Random(seed)
    diffs = [y - x for x, y in zip(a, b)]
    n = len(diffs)
    means = sorted(sum(diffs[rng.randrange(n)] for _ in range(n)) / n for _ in range(iters))
    obs = sum(diffs) / n
    p = sum(1 for m in means if m <= 0) / iters
    return obs, means[int(0.025 * iters)], means[int(0.975 * iters) - 1], p


def table(rows, cols):
    head = "| " + " | ".join(cols) + " |\n| " + " | ".join("---" for _ in cols) + " |\n"
    body = ""
    for r in rows:
        body += "| " + " | ".join(f"{r[c]:.3f}" if isinstance(r[c], float) else str(r[c]) for c in cols) + " |\n"
    return head + body


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--reference", default="tgrag", help="run name to test every other run against")
    ap.add_argument("--out", default="results")
    args = ap.parse_args()

    files = [f for pat in args.files for f in (sorted(glob.glob(pat)) or [pat])]  # Windows does not expand *
    runs = load(files)
    shared = set.intersection(*(set(v) for v in runs.values()))
    print(f"Runs: {', '.join(runs)} | questions answered by all runs: {len(shared)}\n")
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    overall = []
    for name, by_q in runs.items():
        overall.append({"run": name, **summarize([by_q[q] for q in shared])})
    cols = ["run", "n", "correct", "correct_ans", "correct_unans", "refusal", "incorrect", "rouge_l", "f1",
            "ctx_tokens", "sec_per_q"]
    print("## Overall\n\n" + table(overall, cols))

    by_type = []
    for field in ("question_type", "reasoning_type"):
        groups = defaultdict(list)
        for q in shared:
            groups[next(iter(runs.values()))[q][field]].append(q)
        for g, qs in sorted(groups.items()):
            for name, by_q in runs.items():
                s = summarize([by_q[q] for q in qs])
                by_type.append({"split": field, "group": g, "run": name, "n": s["n"],
                                "correct": s["correct"], "incorrect": s["incorrect"]})
    print("## By question type\n\n" + table(by_type, ["split", "group", "run", "n", "correct", "incorrect"]))

    sig, sig_a = [], []
    if args.reference in runs:
        qs = sorted(shared)
        ref = [runs[args.reference][q]["correct"] for q in qs]
        for name, by_q in runs.items():
            if name == args.reference:
                continue
            d, lo, hi, p = bootstrap(ref, [by_q[q]["correct"] for q in qs])
            sig.append({"run": name, "vs": args.reference, "delta_correct": d, "ci_low": lo, "ci_high": hi, "p": p})
        print("## Paired bootstrap on Correct (1,000 resamples)\n\n"
              + table(sig, ["run", "vs", "delta_correct", "ci_low", "ci_high", "p"]))
        qa = [q for q in qs if runs[args.reference][q]["gold"].strip().lower() != "unanswerable"]
        ref_a = [runs[args.reference][q]["correct"] for q in qa]
        sig_a = []
        for name, by_q in runs.items():
            if name == args.reference:
                continue
            d, lo, hi, p = bootstrap(ref_a, [by_q[q]["correct"] for q in qa])
            sig_a.append({"run": name, "vs": args.reference, "n": len(qa), "delta_correct": d,
                          "ci_low": lo, "ci_high": hi, "p": p})
        print("## Paired bootstrap on Correct, answerable questions only\n\n"
              + table(sig_a, ["run", "vs", "n", "delta_correct", "ci_low", "ci_high", "p"]))
        print("A gain is significant at 5% when ci_low > 0 (equivalently p < 0.025 one-sided).")

    for name, rows in [("overall", overall), ("by_type", by_type), ("significance", sig),
                       ("significance_answerable", sig_a)]:
        if rows:
            with open(out / f"{name}.csv", "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=list(rows[0]))
                w.writeheader()
                w.writerows(rows)
    print(f"\nCSV files written to {out}/")


if __name__ == "__main__":
    main()
