"""Make a small ECT-QA subset (first N companies) plus a 20/80 dev/test question split.

Usage (from the Temporal-GraphRAG folder):
    python scripts/make_subset.py --companies 6

Writes:
    ect-qa/subset/base_subset.jsonl.gz   transcripts of the chosen companies (2020-2023)
    ect-qa/subset/dev.jsonl              20% of their questions, for tuning lambda
    ect-qa/subset/test.jsonl             80%, for the reported results
"""
import argparse
import gzip
import json
import random
import re
from collections import Counter, defaultdict
from pathlib import Path


def short_name(name: str) -> str:
    """'Crocs, Inc.' -> 'crocs'; 'Home Depot Inc' -> 'home depot'."""
    s = re.sub(r"[,.]|\b(inc|corp|corporation|company|plc|group|l\.?p|incorporated|holdings)\b", " ",
               name.lower())
    return " ".join(s.split())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", default="ect-qa/corpus/base.jsonl.gz")
    ap.add_argument("--questions", default="ect-qa/questions/local_base.jsonl")
    ap.add_argument("--companies", type=int, default=6, help="first N companies in corpus order")
    ap.add_argument("--out_dir", default="ect-qa/subset")
    ap.add_argument("--dev_share", type=float, default=0.2)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    docs = [json.loads(line) for line in gzip.open(args.corpus, "rt", encoding="utf-8")]
    order = list(dict.fromkeys(d["company_name"] for d in docs))
    chosen = set(order[: args.companies])
    sub_docs = [d for d in docs if d["company_name"] in chosen]

    questions = [json.loads(line) for line in open(args.questions, encoding="utf-8")]
    short = {short_name(c) for c in chosen}
    kept, unanswerable_other = [], []
    for i, q in enumerate(questions):
        q["qid"] = f"base-{i}"
        ev = q["evidence_list"] if isinstance(q["evidence_list"], list) else json.loads(q["evidence_list"] or "[]")
        if ev:
            if {e["company_name"] for e in ev} <= chosen:
                kept.append(q)
        elif any(s and s in q["question"].lower() for s in short):
            kept.append(q)
        else:
            unanswerable_other.append(q)

    # keep roughly the original share of unanswerable questions (about 24% in local_base)
    rng = random.Random(args.seed)
    share = sum(1 for q in questions if q["answer"] == "unanswerable") / len(questions)
    n_ans = sum(1 for q in kept if q["answer"] != "unanswerable")
    n_un_now = len(kept) - n_ans
    n_un_target = round(share * n_ans / (1 - share))
    extra = max(0, n_un_target - n_un_now)
    kept += rng.sample(unanswerable_other, min(extra, len(unanswerable_other)))

    # stratified dev/test split by question type
    by_type = defaultdict(list)
    for q in kept:
        by_type[q["question_type"]].append(q)
    dev, test = [], []
    for items in by_type.values():
        rng.shuffle(items)
        k = round(len(items) * args.dev_share)
        dev += items[:k]
        test += items[k:]

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    with gzip.open(out / "base_subset.jsonl.gz", "wt", encoding="utf-8") as f:
        for d in sub_docs:
            f.write(json.dumps(d) + "\n")
    for name, rows in [("dev", dev), ("test", test)]:
        with open(out / f"{name}.jsonl", "w", encoding="utf-8") as f:
            for q in rows:
                f.write(json.dumps(q) + "\n")

    print(f"Companies ({len(chosen)}): {', '.join(sorted(chosen))}")
    print(f"Transcripts: {len(sub_docs)}  (tokens: {sum(int(d['token_count']) for d in sub_docs):,})")
    print(f"Questions: {len(kept)}  -> dev {len(dev)}, test {len(test)}")
    print("By question type:", dict(Counter(q["question_type"] for q in kept)))
    print("By reasoning type:", dict(Counter(q["reasoning_type"] for q in kept)))


if __name__ == "__main__":
    main()
