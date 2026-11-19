"""Answer ECT-QA questions with one retrieval variant and save every answer.

Usage (from the Temporal-GraphRAG folder):
    python scripts/run_ectqa.py --working_dir graph_subset --questions ect-qa/subset/dev.jsonl \
        --variant tgrag --out runs/dev_tgrag.jsonl --limit 5

Variants:
    original  TG-RAG's released retrieval code, untouched (baseline)
    naive     plain dense RAG over chunks (TG-RAG's "naive" mode)
    tgrag     our re-implementation of TG-RAG retrieval (must match "original")
    B1        + soft time kernel                    (--lam)
    B12       + soft kernel and time-weighted PPR   (Module B)
    C         + time-partitioned hybrid seeding     (Module C)
    BC        Modules B and C together (full model)
    B1QI      ablation: like B12, but the walk's time weights ignore the question (DyG-RAG-style; --alpha)
Add --noise 0.2 to shift 20% of stored timestamps by one quarter (robustness test).
The script resumes: questions already in --out are skipped, so you can stop and restart it.
"""
import argparse
import dataclasses
import json
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
import _paths  # noqa: F401,E402  (src/ and TG-RAG on sys.path)
load_dotenv(ROOT / ".env")

from tgrag import create_temporal_graphrag_from_config  # noqa: E402
from tgrag.src.core.types import QueryParam  # noqa: E402
from softtime import LAST_RETRIEVAL, VARIANTS, install  # noqa: E402
from softtime.openrouter import enable as enable_openrouter  # noqa: E402

enable_openrouter()  # no effect unless OPENAI_BASE_URL points to OpenRouter

try:  # TG-RAG returns this text (instead of raising) when a local query crashes internally
    from tgrag.src.core.querying import PROMPTS
    FAIL_TEXT = str(PROMPTS["fail_response"]).strip()
except Exception:
    FAIL_TEXT = "Sorry, I'm not able to provide an answer to that question."


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--working_dir", required=True, help="folder created by build_graph.py")
    ap.add_argument("--questions", required=True)
    ap.add_argument("--variant", required=True, choices=["original", "naive", *VARIANTS])
    ap.add_argument("--out", required=True)
    ap.add_argument("--config", default=str(Path(__import__("_paths").TGRAG_HOME) / "tgrag/configs/config.yaml"))
    ap.add_argument("--limit", type=int, default=None, help="only the first N questions")
    ap.add_argument("--lam", type=float, default=None, help="kernel strength (soft variants)")
    ap.add_argument("--kappa_min", type=float, default=None)
    ap.add_argument("--alpha", type=float, default=None, help="decay rate of the query-independent walk (B1QI)")
    ap.add_argument("--noise", type=float, default=0.0, help="share of timestamps to corrupt")
    ap.add_argument("--noise_seed", type=int, default=13)
    ap.add_argument("--top_k", type=int, default=20)
    ap.add_argument("--context_tokens", type=int, default=12000, help="paper: 12,000 for local retrieval")
    ap.add_argument("--response_type", default="A concise, direct answer in one or two sentences")
    args = ap.parse_args()

    if args.variant in ("original", "naive"):
        if args.noise:
            sys.exit("--noise needs one of: " + ", ".join(VARIANTS))
        install(None)
        mode = "naive" if args.variant == "naive" else "local"
        settings = {}
    else:
        cfg = dataclasses.replace(VARIANTS[args.variant], noise_rate=args.noise, noise_seed=args.noise_seed)
        if args.lam is not None:
            cfg.lam = args.lam
        if args.kappa_min is not None:
            cfg.kappa_min = args.kappa_min
        if args.alpha is not None:
            if not cfg.static_ppr:
                sys.exit("--alpha only applies to --variant B1QI")
            cfg.qi_alpha = args.alpha
        install(cfg)
        mode = "local"
        settings = dataclasses.asdict(cfg)

    overrides = {"working_dir": args.working_dir}
    if mode == "naive":
        overrides["enable_naive_rag"] = True  # plain RAG over the same chunks the graph was built from
    graph_rag = create_temporal_graphrag_from_config(
        config_path=args.config, config_type="querying", override_config=overrides)
    if mode == "naive":
        from tgrag.src.utils.async_utils import always_get_an_event_loop
        from softtime.naive_index import ensure_chunk_index
        print("Checking the plain-RAG chunk index (built once, saved as vdb_chunks.json)...")
        n_new = always_get_an_event_loop().run_until_complete(ensure_chunk_index(graph_rag))
        print(f"  embedded {n_new} chunks" if n_new else "  already there")
    param = QueryParam(mode=mode, top_k=args.top_k, response_type=args.response_type,
                       local_max_token_for_text_unit=args.context_tokens,
                       naive_max_token_for_text_unit=args.context_tokens)

    questions = [json.loads(line) for line in open(args.questions, encoding="utf-8")]
    if args.limit:
        questions = questions[: args.limit]
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    done = set()
    if out.exists():
        # Answers that hit a real error (timeout, 429, ...) are dropped so a re-run retries them.
        saved = [json.loads(line) for line in open(out, encoding="utf-8") if line.strip()]
        kept = [r for r in saved if not r.get("error")]
        if len(kept) < len(saved):
            print(f"Retrying {len(saved) - len(kept)} question(s) that hit an error last time")
            with open(out, "w", encoding="utf-8") as f:
                for r in kept:
                    f.write(json.dumps(r) + "\n")
        done = {r["qid"] for r in kept}

    run_name = args.variant
    if args.lam is not None:
        run_name += f"_lam{args.lam:g}"
    if args.kappa_min is not None:
        run_name += f"_kmin{args.kappa_min:g}"
    if args.alpha is not None:
        run_name += f"_alpha{args.alpha:g}"
    if args.noise:
        run_name += f"_noise{args.noise:g}"
    todo = [q for q in questions if q["qid"] not in done]
    print(f"{run_name}: {len(todo)} to answer ({len(done)} already done)")
    with open(out, "a", encoding="utf-8") as f:
        for n, q in enumerate(todo, 1):
            t0 = time.time()
            LAST_RETRIEVAL.clear()
            error = None
            try:
                resp = graph_rag.query(q["question"], param=param)
                answer = resp[0] if isinstance(resp, tuple) else resp
            except Exception as e:  # keep going; the error is saved with the question
                answer, error = "", repr(e)
            rec = {
                "qid": q["qid"], "run": run_name, "variant": args.variant,
                "question": q["question"], "gold": q["answer"],
                "question_type": q["question_type"], "reasoning_type": q["reasoning_type"],
                "prediction": str(answer), "error": error,
                "failed": bool(error) or str(answer).strip() == FAIL_TEXT, "seconds": round(time.time() - t0, 2),
                "retrieval": dict(LAST_RETRIEVAL), "settings": settings,
            }
            f.write(json.dumps(rec, default=str) + "\n")
            f.flush()
            flag = "ERROR " + error if error else ("FAILED (TG-RAG hid an internal error; rerun with TG_RAG_DEBUG=true)"
                                                 if rec["failed"] else "")
            print(f"[{n}/{len(todo)}] {rec['seconds']}s {flag}")

    try:  # close HTTP clients, as query_graph.py does (newer Python warns about get_event_loop; harmless)
        import asyncio
        import warnings
        from tgrag.src.llm.client import get_client_manager
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            asyncio.get_event_loop().run_until_complete(get_client_manager().close_clients())
    except Exception:
        pass


if __name__ == "__main__":
    main()
