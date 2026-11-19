"""PoC demo: answer one question with TG-RAG (hard time filter) and with our B1 (soft time kernel).

It prints, side by side:
  * the question periods TG-RAG extracted from the question,
  * the candidate facts (relations) found by similarity, each with its stored date,
    TG-RAG's 0/1 weight and our kappa weight (dropped facts are marked),
  * both answers, the gold answer, and (for dev questions) the saved judge scores.

Cost: two TG-RAG queries, about 4 model calls (2 x timestamp extraction + 2 x answer) plus two
small embedding calls. For a dev question everything except the embeddings is already in
TG-RAG's response cache, so it costs about USD 0; a new question costs under USD 0.01.

Run from the Temporal-GraphRAG folder with the tgrag environment:
    python scripts/demo_compare.py                      # default: dev question base-6
    python scripts/demo_compare.py --qid base-542
    python scripts/demo_compare.py --question "What was Crocs' revenue in 2023 Q2?"
"""
import argparse
import dataclasses
import json
import logging
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
import _paths  # noqa: F401,E402  (src/ and TG-RAG on sys.path)
load_dotenv(ROOT / ".env")

from tgrag import create_temporal_graphrag_from_config  # noqa: E402
from tgrag.src.core.types import QueryParam  # noqa: E402
from softtime import LAST_RETRIEVAL, VARIANTS, install  # noqa: E402
from softtime.openrouter import enable as enable_openrouter  # noqa: E402

enable_openrouter()  # one OpenRouter key for every model (no effect without OPENAI_BASE_URL)

DEFAULT_QID = "base-6"  # TG-RAG found 0 seed facts here; B1 found 11 (dev runs)


def find_dev_question(qid: str) -> dict:
    """Return the dev or test record with this qid (question, gold answer, type), or exit if missing."""
    for split in ("dev", "test"):
        for line in open(ROOT / f"ect-qa/subset/{split}.jsonl", encoding="utf-8"):
            rec = json.loads(line)
            if rec["qid"] == qid:
                return {**rec, "split": split}
    sys.exit(f"qid {qid} not found in ect-qa/subset/dev.jsonl or test.jsonl")


def saved_judge_scores(qid: str) -> dict:
    """Judge Correct scores already saved for this qid in the dev runs (no API call), keyed by run name."""
    out = {}
    for name in ("tgrag", "B1_lam1"):
        path = ROOT / f"runs/dev_{name}.judged.jsonl"
        if path.exists():
            for line in open(path, encoding="utf-8"):
                rec = json.loads(line)
                if rec["qid"] == qid:
                    out[name] = rec["correct"]
    return out


def ask(graph_rag, question: str, cfg, param) -> dict:
    """Answer one question with one retrieval variant; return the answer and a copy of the retrieval record."""
    install(cfg)  # swap TG-RAG's retrieval function for this variant (TG-RAG's code itself is untouched)
    LAST_RETRIEVAL.clear()
    resp = graph_rag.query(question, param=param)
    answer = resp[0] if isinstance(resp, tuple) else resp
    return {"answer": str(answer), "retrieval": json.loads(json.dumps(LAST_RETRIEVAL, default=str))}


def print_facts(hard: dict, soft: dict, top: int) -> None:
    """Print the candidate facts once, with TG-RAG's 0/1 weight and B1's kappa next to each other."""
    key = lambda f: (f["src"], f["tgt"], f["ts"])  # noqa: E731  (one fact = entity pair + date)
    h = {key(f): f for f in hard["retrieval"].get("candidate_facts", [])}
    s = {key(f): f for f in soft["retrieval"].get("candidate_facts", [])}
    # Order by similarity to the question, the order TG-RAG's vector search returns them in
    facts = sorted({**h, **s}.items(), key=lambda kv: -kv[1]["sim"])[:top]
    if not facts:
        print("  (no dated candidate facts: the question had no time period, or nothing was found)")
        return
    print(f"  {'#':>2}  {'stored date':<12} {'sim':>5}  {'TG-RAG':>8}  {'B1 kappa':>11}  fact")
    for i, (k, f) in enumerate(facts, 1):
        hw = h.get(k, {}).get("weight")
        sw = s.get(k, {}).get("weight")
        hs = "-" if hw is None else (f"{hw:.0f} keep" if h[k]["kept"] else "0 DROP")
        ss = "-" if sw is None else (f"{sw:.4f}" + ("" if s[k]["kept"] else " DROP"))
        text = (f.get("text") or f"{f['src']} -> {f['tgt']}").replace("\n", " ")
        print(f"  {i:>2}  {str(f['ts']):<12} {f['sim']:>5.3f}  {hs:>8}  {ss:>11}  {text[:90]}")
    n_h = sum(1 for f in h.values() if f["kept"])
    n_s = sum(1 for f in s.values() if f["kept"])
    print(f"\n  Facts kept as seeds: TG-RAG {n_h} of {len(h)} candidates, B1 {n_s} of {len(s)}.")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--qid", default=None, help=f"dev/test question id (default {DEFAULT_QID})")
    ap.add_argument("--question", default=None, help="any free-text question instead of --qid")
    ap.add_argument("--working_dir", default="graph_subset")
    ap.add_argument("--lam", type=float, default=1.0, help="B1 kernel strength (locked at 1 on dev)")
    ap.add_argument("--top", type=int, default=12, help="how many candidate facts to print")
    ap.add_argument("--verbose", action="store_true", help="show TG-RAG's own log messages")
    args = ap.parse_args()
    if not args.verbose:  # TG-RAG logs every step; keep the demo output readable
        logging.getLogger("temporal-graphrag").setLevel(logging.WARNING)
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # Windows consoles default to a narrow code page
    except Exception:
        pass

    # Pick the question: free text, a given qid, or the default dev example
    rec = None
    if args.question:
        question = args.question
    else:
        rec = find_dev_question(args.qid or DEFAULT_QID)
        question = rec["question"]

    # Same settings as the experiments: top_k 20, 12,000-token context, same answer style
    graph_rag = create_temporal_graphrag_from_config(
        config_path=str(Path(__import__("_paths").TGRAG_HOME) / "tgrag/configs/config.yaml"), config_type="querying",
        override_config={"working_dir": args.working_dir})
    param = QueryParam(mode="local", top_k=20, response_type="A concise, direct answer in one or two sentences",
                       local_max_token_for_text_unit=12000)

    hard = ask(graph_rag, question, VARIANTS["tgrag"], param)
    soft = ask(graph_rag, question, dataclasses.replace(VARIANTS["B1"], lam=args.lam), param)

    bar = "=" * 100
    print(f"\n{bar}\nQUESTION: {question}")
    if rec:
        print(f"  id {rec['qid']} ({rec['split']}), type: {rec['question_type']}\n  GOLD: {rec['answer']}")
    print(f"  Periods read from the question: {', '.join(hard['retrieval'].get('query_timestamps') or ['(none)'])}")
    print(f"\nCANDIDATE FACTS (TG-RAG keeps a fact only if its date is inside the asked period; "
          f"B1 weights it by kappa = exp(-{args.lam:g} x tree distance), drops it below 0.05)")
    print_facts(hard, soft, args.top)
    print(f"  Chunks sent to the answer model: TG-RAG {len(hard['retrieval'].get('chunk_ids', []))}, "
          f"B1 {len(soft['retrieval'].get('chunk_ids', []))}")
    print(f"\nANSWER, TG-RAG (hard filter):\n  {hard['answer'].strip()}")
    print(f"\nANSWER, B1 (soft kernel, lambda={args.lam:g}):\n  {soft['answer'].strip()}")
    if rec and rec["split"] == "dev":
        scores = saved_judge_scores(rec["qid"])
        if scores:
            print("\nSaved judge Correct from the dev runs: "
                  + ", ".join(f"{k} {v:.2f}" for k, v in scores.items()))
    print(bar)


if __name__ == "__main__":
    main()
