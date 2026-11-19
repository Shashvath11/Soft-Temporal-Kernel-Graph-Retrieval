"""Score saved answers: LLM judge (Correct / Refusal / Incorrect) plus ROUGE-L and token F1.

Usage:
    python scripts/judge.py runs/dev_tgrag.jsonl runs/dev_B12.jsonl

For every input file X.jsonl it writes X.judged.jsonl (and reuses it, so re-running is free).

The judge follows the protocol described in the TG-RAG paper (Section V-C): GPT-4o-mini splits
the prediction into factual elements, compares each to the gold answer, and labels it correct,
refusal or incorrect; the three shares sum to 1 per question. The released repository ships no
evaluation code, so these prompts are our own wording of that protocol. For unanswerable
questions a correct refusal is counted as Correct (the paper's oracle row has Refusal 0.023 with
about a quarter of questions unanswerable, which implies this). Report this choice in your paper.
"""
import argparse
import glob
import json
import os
import re
import sys
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")
import _paths  # noqa: F401,E402  (src/ and TG-RAG on sys.path)
from softtime.openrouter import enable as enable_openrouter  # noqa: E402

enable_openrouter()  # "gpt-4o-mini" becomes "openai/gpt-4o-mini" when using OpenRouter

ANSWERABLE_PROMPT = """You are a strict fact-level grader for financial question answering.

Question: {question}
Gold answer: {gold}
Model prediction: {prediction}

Steps:
1. List the distinct factual elements the gold answer requires (each number, period, entity or
   comparison outcome is one element).
2. For each element, check the prediction and label it:
   - "correct": the prediction states it and it matches the gold answer (allow equivalent wording,
     rounding such as $2.0 billion vs $2 billion, and "Q4 2023" vs "2023 Q4");
   - "refusal": the prediction explicitly says it cannot answer or lacks evidence for it;
   - "incorrect": the prediction gives a wrong value or period, or states it without support.
   A required element the prediction never mentions counts as "refusal" if the prediction declined
   to answer and as "incorrect" otherwise.
3. Do not reward extra content; ignore formatting.

Return strict JSON: {{"correct": <int>, "refusal": <int>, "incorrect": <int>}}"""

UNANSWERABLE_PROMPT = """You are a strict grader. The gold answer to this question is UNANSWERABLE:
the documents do not contain the information.

Question: {question}
Model prediction: {prediction}

Identify the distinct factual claims in the prediction that try to answer the question.
Count as "refused" each part the model explicitly declines to answer (e.g. "no explicit evidence",
"not available"). Count as "incorrect" each part where the model gives a value or fact anyway.
If the whole prediction is a refusal, return refused = 1, incorrect = 0.

Return strict JSON: {{"refused": <int>, "incorrect": <int>}}"""


def normalize(text: str) -> list:
    text = text.lower().replace(",", "")
    text = re.sub(r"[^a-z0-9$%. ]", " ", text)
    return [t.strip(".") for t in text.split() if t.strip(".") and t not in {"a", "an", "the", "and", "of"}]


def token_f1(pred: str, gold: str) -> float:
    p, g = normalize(pred), normalize(gold)
    common = sum((Counter(p) & Counter(g)).values())
    if not p or not g or common == 0:
        return 0.0
    prec, rec = common / len(p), common / len(g)
    return 2 * prec * rec / (prec + rec)


def rouge_l(pred: str, gold: str) -> float:
    p, g = normalize(pred), normalize(gold)
    if not p or not g:
        return 0.0
    prev = [0] * (len(g) + 1)
    for x in p:
        cur = [0]
        for j, y in enumerate(g, 1):
            cur.append(prev[j - 1] + 1 if x == y else max(prev[j], cur[j - 1]))
        prev = cur
    lcs = prev[-1]
    if lcs == 0:
        return 0.0
    prec, rec = lcs / len(p), lcs / len(g)
    return 2 * prec * rec / (prec + rec)


def ask(client, model, prompt):
    for attempt in range(5):
        try:
            r = client.chat.completions.create(
                model=model, temperature=0, response_format={"type": "json_object"},
                messages=[{"role": "user", "content": prompt}])
            return json.loads(r.choices[0].message.content), r.usage.prompt_tokens, r.usage.completion_tokens
        except Exception as e:  # rate limits, bad JSON: wait and retry
            if attempt == 4:
                raise
            print(f"  retry after error: {e}")
            time.sleep(2 * (attempt + 1))


def judge_one(client, model, rec):
    pred = rec.get("prediction") or ""
    if rec["gold"].strip().lower() == "unanswerable":
        out, pt, ct = ask(client, model, UNANSWERABLE_PROMPT.format(question=rec["question"], prediction=pred))
        ref, inc = max(int(out.get("refused", 0)), 0), max(int(out.get("incorrect", 0)), 0)
        total = ref + inc or 1
        scores = {"correct": ref / total, "refusal": 0.0, "incorrect": inc / total}
    else:
        out, pt, ct = ask(client, model, ANSWERABLE_PROMPT.format(
            question=rec["question"], gold=rec["gold"], prediction=pred))
        c, r, i = (max(int(out.get(k, 0)), 0) for k in ("correct", "refusal", "incorrect"))
        total = c + r + i
        scores = ({"correct": c / total, "refusal": r / total, "incorrect": i / total}
                  if total else {"correct": 0.0, "refusal": 0.0, "incorrect": 1.0})
    gold_text = "" if rec["gold"].strip().lower() == "unanswerable" else rec["gold"]
    return {**rec, **scores, "judge_raw": out,
            "rouge_l": rouge_l(pred, gold_text), "f1": token_f1(pred, gold_text),
            "judge_tokens": [pt, ct]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--model", default="gpt-4o-mini")
    ap.add_argument("--workers", type=int, default=8)
    args = ap.parse_args()
    if not os.getenv("OPENAI_API_KEY"):
        sys.exit("OPENAI_API_KEY is not set (put it in .env)")
    client = OpenAI()

    files = [f for pat in args.files for f in (sorted(glob.glob(pat)) or [pat])]  # Windows does not expand *
    files = [f for f in files if not f.endswith(".judged.jsonl")]
    for path in files:
        src = Path(path)
        dst = src.with_suffix(".judged.jsonl")
        recs = [json.loads(line) for line in open(src, encoding="utf-8") if line.strip()]
        errored = [r for r in recs if r.get("error")]
        recs = [r for r in recs if not r.get("error")]
        if errored:
            print(f"{src.name}: skipping {len(errored)} answer(s) that hit an error - re-run run_ectqa.py first")
        current = {r["qid"]: r for r in recs}
        done = {}
        if dst.exists():
            for line in open(dst, encoding="utf-8"):
                if line.strip():
                    r = json.loads(line)
                    done[r["qid"]] = r
        # keep a cached score only if that exact answer is still in the run file
        stale = [q for q, r in done.items()
                 if q not in current or r.get("prediction") != current[q].get("prediction")]
        if stale:
            for q in stale:
                del done[q]
            with open(dst, "w", encoding="utf-8") as f:
                for r in done.values():
                    f.write(json.dumps(r) + "\n")
            print(f"{src.name}: {len(stale)} old score(s) dropped because the answer changed")
        todo = [r for r in recs if r["qid"] not in done]
        print(f"{src.name}: judging {len(todo)} ({len(done)} cached)")
        with ThreadPoolExecutor(args.workers) as pool, open(dst, "a", encoding="utf-8") as f:
            for res in pool.map(lambda r: judge_one(client, args.model, r), todo):
                f.write(json.dumps(res) + "\n")
                f.flush()
                done[res["qid"]] = res
        rows = list(done.values())
        n = len(rows)
        if not n:
            continue
        mean = lambda k: sum(r[k] for r in rows) / n  # noqa: E731
        print(f"  n={n}  Correct={mean('correct'):.3f}  Refusal={mean('refusal'):.3f}  "
              f"Incorrect={mean('incorrect'):.3f}  ROUGE-L={mean('rouge_l'):.3f}  F1={mean('f1'):.3f}")


if __name__ == "__main__":
    main()
