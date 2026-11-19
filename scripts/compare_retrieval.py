"""Check that two runs retrieved the same chunks (e.g. TG-RAG's original code vs our "tgrag" re-implementation).

Usage:
    python scripts/compare_retrieval.py runs/dev_original.jsonl runs/dev_tgrag.jsonl

TG-RAG caches LLM calls (temperature 0), so the same question gets the same extracted time scope
in both runs; any difference here comes from the retrieval code itself.

Each question falls in one group:
    identical      same chunks in the same order (includes "both found nothing")
    same set       same chunks, different order (chunks with equal scores can swap places)
    different      some chunks differ; the overlap shows how many are shared
"""
import json
import sys


def load(path):
    return {r["qid"]: r for r in (json.loads(line) for line in open(path, encoding="utf-8") if line.strip())}


def hashes(rec):
    # Older runs did not save an empty list when nothing was found; treat missing as empty.
    return (rec.get("retrieval") or {}).get("chunk_hashes") or []


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    a, b = load(sys.argv[1]), load(sys.argv[2])
    shared = sorted(set(a) & set(b))
    identical, same_set, different = [], [], []
    for q in shared:
        ha, hb = hashes(a[q]), hashes(b[q])
        if ha == hb:
            identical.append(q)
        elif set(ha) == set(hb):
            same_set.append(q)
        else:
            different.append(q)
    n = max(len(shared), 1)
    print(f"Questions in both runs: {len(shared)}")
    print(f"Identical retrieved chunks: {len(identical)} ({len(identical) / n:.0%})"
          f"   [of these, both found nothing: {sum(1 for q in identical if not hashes(a[q]))}]")
    print(f"Same chunks, different order: {len(same_set)} ({len(same_set) / n:.0%})")
    print(f"Different chunks: {len(different)} ({len(different) / n:.0%})")
    print(f"=> Same evidence (identical + same set): {(len(identical) + len(same_set)) / n:.0%}")
    for q in different:
        ha, hb = hashes(a[q]), hashes(b[q])
        common = len(set(ha) & set(hb))
        print(f"  differs: {q} | chunks {len(ha)} vs {len(hb)}, shared {common} | {a[q]['question'][:70]}")


if __name__ == "__main__":
    main()
