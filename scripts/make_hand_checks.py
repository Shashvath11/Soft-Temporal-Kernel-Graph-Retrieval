"""Prepare the hand-check files that the owner fills in (no API calls).

Two jobs:
  facts    100 stored facts (relations) sampled from the graph, each with its stored date, the
           earnings call it came from, the fact text and an excerpt of the source chunk, plus an
           empty verdict column. It also counts automatically how many stored timestamps are not
           in one of TG-RAG's four forms (YYYY, YYYY-QN, YYYY-MM, YYYY-MM-DD).
  answers  50 judged test answers, sampled across the main runs and question types, with an
           empty verdict column. The sheet is blind: run names and judge scores go to a separate
           key file (needs the judged test runs). Score with scripts/score_hand_checks.py.

Both use seed 42. Output goes to docs/hand_checks/.

Run from the Temporal-GraphRAG folder:
    python scripts/make_hand_checks.py facts
    python scripts/make_hand_checks.py answers
"""
import argparse
import csv
import json
import random
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
import _paths  # noqa: F401,E402  (src/ and TG-RAG on sys.path)
from softtime.soft_time import clean_ts, ts_path  # noqa: E402

OUT = ROOT / "results" / "hand_checks"
SEED = 42
MAIN_RUNS = ["tgrag", "naive", "B1_lam1", "B12_lam1", "B1QI_lam1_alpha1", "C", "BC_lam1"]


def load_graph_facts(graph_dir: Path) -> list:
    """Return every stored fact as a dict: one entry per (entity pair, timestamp) that has a description.

    TG-RAG stores, on each entity-entity edge, a JSON dict timestamp -> description and a dict
    timestamp -> source chunk id. Edges to time nodes carry no description and are skipped.
    """
    import networkx as nx

    G = nx.read_graphml(str(graph_dir / "graph_chunk_entity_relation.graphml"))
    facts = []
    for u, v, data in G.edges(data=True):
        try:  # both attributes are JSON strings in the .graphml file
            desc = json.loads(data.get("description", "{}"))
            src = json.loads(data.get("source_id", "{}"))
        except (json.JSONDecodeError, TypeError):
            continue
        if not isinstance(desc, dict) or not isinstance(src, dict):
            continue
        for ts, text in desc.items():
            if str(text).strip():  # a fact = a timestamp with a written description
                facts.append({"src": u, "tgt": v, "ts": ts, "text": str(text), "chunk_id": src.get(ts, "")})
    # Deterministic order before sampling, so the sample does not depend on file order
    facts.sort(key=lambda f: (f["src"], f["tgt"], f["ts"]))
    return facts


def excerpt(chunk_text: str, fact_text: str, names: list, width: int = 700) -> str:
    """Cut a window of the chunk around the evidence for the fact, so the owner can check the date.

    Anchors are tried from most to least distinctive: numbers quoted in the fact text (e.g. "$15",
    "2.3"), then the entity names in the given order. The first anchor found in the chunk wins.
    """
    low = chunk_text.lower()
    numbers = [x for x in re.findall(r"\$?\d[\d,.]*%?", fact_text) if len(x.strip(".,")) >= 2]
    pos = -1
    for anchor in [*numbers, *names]:
        if anchor:
            pos = low.find(anchor.lower().strip(".,"))
            if pos >= 0:
                break
    start = max(pos - width // 3, 0) if pos >= 0 else 0
    return re.sub(r"\s+", " ", chunk_text[start:start + width]).strip()


def make_facts(n: int) -> None:
    """Write fact_dates_100.csv and malformed_timestamps.md."""
    graph_dir = ROOT / "graph_subset"
    facts = load_graph_facts(graph_dir)
    chunks = json.load(open(graph_dir / "kv_store_text_chunks.json", encoding="utf-8"))
    docs = json.load(open(graph_dir / "kv_store_full_docs.json", encoding="utf-8"))
    OUT.mkdir(parents=True, exist_ok=True)

    # ---- automatic count: stored timestamps outside the four standard forms ----
    bad = Counter(clean_ts(f["ts"]) for f in facts if ts_path(f["ts"]) is None)
    levels = Counter(["year", "quarter", "month", "date"][len(ts_path(f["ts"])) - 1]
                     for f in facts if ts_path(f["ts"]) is not None)
    n_bad = sum(bad.values())
    with open(OUT / "malformed_timestamps.md", "w", encoding="utf-8") as fh:
        fh.write("# Stored timestamps outside TG-RAG's four forms (automatic count)\n\n")
        fh.write("Command: `python scripts/make_hand_checks.py facts` (reads graph_subset/, no API calls)\n\n")
        fh.write(f"- Stored facts (entity pair + timestamp with a description): **{len(facts):,}**\n")
        fh.write(f"- Timestamp not in YYYY, YYYY-QN, YYYY-MM or YYYY-MM-DD form: **{n_bad:,} "
                 f"({n_bad / len(facts):.1%})**, {len(bad)} distinct strings\n")
        fh.write(f"- Parseable facts by level: {dict(levels)}\n\n")
        fh.write("Such facts get weight 0 from both TG-RAG's filter and our kernel (they cannot be placed in time).\n\n")
        fh.write("| Most frequent non-standard timestamps | count |\n|---|---|\n")
        for ts, c in bad.most_common(25):
            fh.write(f"| `{ts}` | {c} |\n")

    # ---- 100 random facts for the owner to check ----
    sample = random.Random(SEED).sample(facts, n)
    fields = ["id", "earnings_call", "entity_1", "entity_2", "stored_date", "date_form_ok", "fact_text",
              "source_excerpt", "chunk_id", "my_verdict (correct / wrong date / no date in text / unclear)", "notes"]
    with open(OUT / "fact_dates_100.csv", "w", newline="", encoding="utf-8-sig") as fh:  # -sig: opens cleanly in Excel
        w = csv.writer(fh)
        w.writerow(fields)
        for i, f in enumerate(sample, 1):
            ch = chunks.get(f["chunk_id"], {})
            call = docs.get(ch.get("full_doc_id", ""), {}).get("title", "")
            w.writerow([i, call, f["src"], f["tgt"], f["ts"], "yes" if ts_path(f["ts"]) else "NO", f["text"],
                        excerpt(ch.get("content", ""), f["text"], [f["tgt"], f["src"]]), f["chunk_id"], "", ""])
    print(f"facts: {len(facts):,} stored facts, {n_bad:,} ({n_bad / len(facts):.1%}) non-standard timestamps")
    print(f"wrote {OUT / 'fact_dates_100.csv'} and {OUT / 'malformed_timestamps.md'}")


def make_answers(n: int) -> None:
    """Write judge_check_50.csv: n judged test answers spread over runs and question types."""
    pool = defaultdict(list)  # question_type -> list of judged records from the main runs
    n_q = Counter()
    for run in MAIN_RUNS:
        path = ROOT / f"runs/test_{run}.judged.jsonl"
        if not path.exists():
            sys.exit(f"missing {path}: run and judge the test set first")
        for line in open(path, encoding="utf-8"):
            r = json.loads(line)
            pool[r["question_type"]].append(r)
            if run == MAIN_RUNS[0]:
                n_q[r["question_type"]] += 1
    rng = random.Random(SEED)
    # Share of the sample per question type = its share of the test questions (largest remainder)
    total = sum(n_q.values())
    raw = {t: n * c / total for t, c in n_q.items()}
    quota = {t: int(x) for t, x in raw.items()}
    for t in sorted(raw, key=lambda t: raw[t] - quota[t], reverse=True)[: n - sum(quota.values())]:
        quota[t] += 1
    chosen = []
    for t in sorted(quota):
        recs = sorted(pool[t], key=lambda r: (r["qid"], r["run"]))
        rng.shuffle(recs)
        by_run = defaultdict(list)
        for r in recs:
            by_run[r["run"]].append(r)
        used_q, picked, k = set(), [], 0
        # Round-robin over runs so every run is represented; one answer per question at most
        runs = sorted(by_run)
        while len(picked) < quota[t] and any(by_run.values()):
            lst = by_run[runs[k % len(runs)]]
            while lst:
                r = lst.pop()
                if r["qid"] not in used_q:
                    picked.append(r)
                    used_q.add(r["qid"])
                    break
            k += 1
        chosen += picked
    rng.shuffle(chosen)  # hide the run order from the reader
    OUT.mkdir(parents=True, exist_ok=True)
    # Blind check: the owner's sheet hides the run name and the judge's scores, so neither can bias
    # the verdict; they go to a separate key file that score_hand_checks.py joins back on "id".
    fields = ["id", "qid", "question_type", "question", "gold", "prediction",
              "my_correct (0 / 0.5 / 1, or any value 0-1)", "notes"]
    with open(OUT / "judge_check_50.csv", "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.writer(fh)
        w.writerow(fields)
        for i, r in enumerate(chosen, 1):
            w.writerow([i, r["qid"], r["question_type"], r["question"], r["gold"], r["prediction"], "", ""])
    with open(OUT / "judge_check_50_KEY_do_not_open.csv", "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.writer(fh)
        w.writerow(["id", "qid", "run", "judge_correct", "judge_refusal", "judge_incorrect"])
        for i, r in enumerate(chosen, 1):
            w.writerow([i, r["qid"], r["run"], f"{r['correct']:.3f}", f"{r['refusal']:.3f}", f"{r['incorrect']:.3f}"])
    print(f"wrote {OUT / 'judge_check_50.csv'} (blind) and the judge key: {len(chosen)} answers, "
          f"by run {dict(Counter(r['run'] for r in chosen))}")


def main():
    ap = argparse.ArgumentParser(description="Prepare hand-check CSVs (seed 42).")
    ap.add_argument("job", choices=["facts", "answers"])
    ap.add_argument("-n", type=int, default=None, help="sample size (default 100 facts / 50 answers)")
    args = ap.parse_args()
    if args.job == "facts":
        make_facts(args.n or 100)
    else:
        make_answers(args.n or 50)


if __name__ == "__main__":
    main()
