"""Print statistics of a built TG-RAG graph (for your report and the review slides).

Usage:
    python scripts/graph_stats.py graph_subset
"""
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
import _paths  # noqa: F401,E402  (src/ and TG-RAG on sys.path)

from tgrag.src.storage.graph_networkx import NetworkXStorage  # noqa: E402
from softtime.soft_time import ts_path  # noqa: E402


def main():
    wd = Path(sys.argv[1] if len(sys.argv) > 1 else "graph_subset")
    G = NetworkXStorage.load_nx_graph(str(wd / "graph_chunk_entity_relation.graphml"))
    if G is None:
        sys.exit(f"No graph found in {wd}. Did build_graph.py finish?")
    rel_path = wd / "vdb_relations.json"
    rels = json.load(open(rel_path, encoding="utf-8")).get("data", {}) if rel_path.exists() else {}
    chunks_path = wd / "kv_store_text_chunks.json"
    n_chunks = len(json.load(open(chunks_path, encoding="utf-8"))) if chunks_path.exists() else 0

    levels = Counter()
    unparsed = 0
    for meta in rels.values():
        parts = str(meta.get("entity_name", "")).split("_")
        if len(parts) == 3:
            p = ts_path(parts[2])
            if p is None:
                unparsed += 1
            else:
                levels[["year", "quarter", "month", "date"][len(p) - 1]] += 1

    print(f"Working dir:            {wd}")
    print(f"Text chunks:            {n_chunks}")
    print(f"Graph nodes (entities): {G.number_of_nodes()}")
    print(f"Graph edges:            {G.number_of_edges()}")
    print(f"Timestamped relations:  {len(rels)}")
    print(f"  by granularity:       {dict(levels)}")
    print(f"  unparseable stamps:   {unparsed}")


if __name__ == "__main__":
    main()
