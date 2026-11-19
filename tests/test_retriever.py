"""Offline check that the re-implemented retriever matches TG-RAG's original code.

Builds a tiny fake graph (no API calls), runs TG-RAG's own _retrieve_chunks_with_ppr_algorithm
and our "tgrag" variant on the same inputs, and asserts they return identical chunks.
Run from the Temporal-GraphRAG folder: python -m pytest src/softtime/tests -q
"""
import asyncio
import hashlib

import networkx as nx
import numpy as np
import pytest

from tgrag.src.core import querying
from tgrag.src.utils import helpers
from softtime import RetrievalConfig, build_retriever
from softtime.retriever import LAST_RETRIEVAL, _INDEX_CACHE


def _vec(text):
    v = np.zeros(64, dtype=np.float32)
    for w in text.lower().replace("_", " ").split():
        v[int(hashlib.md5(w.encode()).hexdigest(), 16) % 64] += 1.0
    return v


class FakeVDB:
    def __init__(self, rels):
        self._data, self._embeddings = {}, {}
        for i, (name, content) in enumerate(rels):
            self._data[f"rel-{i}"] = {"entity_name": name, "content": content}
            self._embeddings[f"rel-{i}"] = _vec(name + " " + content)

    async def embedding_func(self, texts):
        return np.stack([_vec(t) for t in texts])

    async def query(self, query, top_k=5):
        q = _vec(query)
        q = q / np.linalg.norm(q)
        sims = [(k, float(np.dot(q, e / np.linalg.norm(e)))) for k, e in self._embeddings.items()]
        sims.sort(key=lambda x: -x[1])
        return [{**self._data[k], "similarity": s} for k, s in sims[:top_k]]


class FakeGraph:
    def __init__(self, G):
        self._graph = G

    async def get_edge(self, a, b):
        return self._graph.edges.get((a, b))

    async def get_top_pagerank_nodes(self, personalization_nodes=None, personalization_weights=None,
                                     top_k=10, alpha=0.85):
        if personalization_weights:
            tot = sum(personalization_weights.values())
            pers = {k: v / tot for k, v in personalization_weights.items()}
        else:
            pers = {n: 1 / len(personalization_nodes) for n in personalization_nodes}
        s = nx.pagerank(self._graph, alpha=alpha, personalization=pers, weight="weight")
        return sorted(s.items(), key=lambda x: -x[1])[:top_k]


class FakeChunks:
    def __init__(self, chunks):
        self.chunks = chunks

    async def get_by_id(self, cid):
        return self.chunks.get(cid)


class Param:
    top_k = 20
    local_max_token_for_text_unit = 10_000


def _world():
    G = nx.Graph()
    edges = [
        ("ACME", "REVENUE", {"2023-Q1": "c1", "2023-Q2": "c2"}),
        ("ACME", "EPS", {"2023-Q1": "c3"}),
        ("BETA", "MARGIN", {"2023-Q2": "c4"}),
        ("ACME", "BETA", {"2022-Q4": "c5"}),
        ('"2023-Q1"', "ACME", {"2023-Q1": "c1"}),
        ('"2023-Q2"', "BETA", {"2023-Q2": "c4"}),
    ]
    for a, b, sid in edges:
        G.add_edge(a, b, source_id=sid, description={k: f"{a} {b} {k}" for k in sid})
    rels = [
        ("ACME_REVENUE_2023-Q1", "ACME revenue in 2023 Q1 was 10 million"),
        ("ACME_REVENUE_2023-Q2", "ACME revenue in 2023 Q2 was 12 million"),
        ("ACME_EPS_2023-Q1", "ACME earnings per share 2023 Q1 was 0.5"),
        ("BETA_MARGIN_2023-Q2", "BETA gross margin 2023 Q2 was 40 percent"),
        ("ACME_BETA_2022-Q4", "ACME acquired BETA in 2022 Q4"),
    ]
    chunks = {f"c{i}": {"content": f"chunk {i} text about the company"} for i in range(1, 6)}
    hierarchy = {"2023": {"sub_communities": ["2023-Q1", "2023-Q2"]},
                 "2023-Q1": {"sub_communities": []}, "2023-Q2": {"sub_communities": []},
                 "2022-Q4": {"sub_communities": []}}
    return FakeVDB(rels), FakeGraph(G), FakeChunks(chunks), hierarchy


@pytest.fixture(autouse=True)
def no_tiktoken_download(monkeypatch):
    monkeypatch.setattr(helpers, "encode_string_by_tiktoken", lambda s, model_name=None: s.split())
    _INDEX_CACHE.clear()


def _run(fn, query, ts):
    vdb, kg, chunks, hier = _world()
    out = asyncio.run(fn(query, vdb, kg, ts, chunks, Param(), {}, hier))
    return [c["content"] for c in out]


@pytest.mark.parametrize("query,ts", [
    ("What was ACME revenue in 2023 Q1?", ["2023-Q1"]),
    ("ACME revenue in each quarter of 2023", ["2023"]),
    ("BETA gross margin 2023 Q2", ["2023-Q2"]),
    ("Tell me about ACME", []),
])
def test_reimplementation_matches_original(query, ts):
    original = _run(querying._retrieve_chunks_with_ppr_algorithm, query, ts)
    ours = _run(build_retriever(RetrievalConfig(name="tgrag")), query, ts)
    assert ours == original


def test_hard_filter_drops_neighbour_quarter_but_soft_kernel_keeps_it():
    # Only 2023-Q2 facts survive the hard filter; the soft kernel also admits the Q1 neighbour.
    hard = _run(build_retriever(RetrievalConfig(name="tgrag")), "ACME revenue 2023 Q2", ["2023-Q2"])
    soft = _run(build_retriever(RetrievalConfig(name="B1", lam=0.5, kappa_min=0.2)),
                "ACME revenue 2023 Q2", ["2023-Q2"])
    assert "chunk 2 text about the company" in hard
    assert "chunk 1 text about the company" not in hard
    assert "chunk 1 text about the company" in soft


def test_all_variants_run():
    for cfg in [RetrievalConfig(name="B12", lam=1.0, weighted_ppr=True),
                RetrievalConfig(name="C", hybrid_seeding=True),
                RetrievalConfig(name="BC", lam=1.0, weighted_ppr=True, hybrid_seeding=True),
                RetrievalConfig(name="noisy", noise_rate=0.3)]:
        out = _run(build_retriever(cfg), "ACME revenue in each quarter of 2023", ["2023-Q1", "2023-Q2"])
        assert out, cfg.name
        assert LAST_RETRIEVAL["variant"] == cfg.name


def test_b1_with_huge_lambda_reproduces_tgrag():
    # lambda -> infinity turns the soft kernel into TG-RAG's hard filter (the "special case" claim)
    for query, ts in [("What was ACME revenue in 2023 Q1?", ["2023-Q1"]),
                      ("ACME revenue in each quarter of 2023", ["2023"]),
                      ("BETA gross margin 2023 Q2", ["2023-Q2"]),
                      ("Tell me about ACME", [])]:
        hard = _run(build_retriever(RetrievalConfig(name="tgrag")), query, ts)
        soft = _run(build_retriever(RetrievalConfig(name="B1", lam=1000.0)), query, ts)
        assert soft == hard, query


def test_query_independent_weights_ignore_the_question():
    from softtime.retriever import static_time_weights

    cfg = RetrievalConfig(name="B1QI", lam=1.0, static_ppr=True, qi_alpha=1.0)
    _, kg, _, _ = _world()
    G = kg._graph
    static_time_weights(G, cfg)
    w1 = {(u, v): d["_qw"] for u, v, d in G.edges(data=True)}
    # run two queries with different dates; the walk weights must not change
    for query, ts in [("ACME revenue 2023 Q1", ["2023-Q1"]), ("ACME BETA deal 2022 Q4", ["2022-Q4"])]:
        asyncio.run(build_retriever(cfg)(query, FakeVDB([("ACME_REVENUE_2023-Q1", "ACME revenue")]), kg, ts,
                                         FakeChunks({"c1": {"content": "x"}}), Param(), {}, {}))
        assert {(u, v): d["_qw"] for u, v, d in G.edges(data=True)} == w1
    # all weights are in [0, 1]; the 2022-Q4 deal edge is a time outlier among ACME's 2023 facts
    assert all(0.0 <= w <= 1.0 for w in w1.values())
    deal = G.edges["ACME", "BETA"]["_qw"]
    revenue = G.edges["ACME", "REVENUE"]["_qw"]
    assert deal < revenue


def test_query_independent_variant_runs_and_differs_from_b12_weights():
    out = _run(build_retriever(RetrievalConfig(name="B1QI", lam=1.0, static_ppr=True)),
               "ACME revenue in each quarter of 2023", ["2023-Q1", "2023-Q2"])
    assert out
    assert LAST_RETRIEVAL["variant"] == "B1QI"
    with pytest.raises(ValueError):
        build_retriever(RetrievalConfig(name="bad", lam=1.0, weighted_ppr=True, static_ppr=True))


def test_query_independent_weights_change_with_noise():
    from softtime.retriever import static_time_weights

    _, kg, _, _ = _world()
    G = kg._graph
    static_time_weights(G, RetrievalConfig(name="q", static_ppr=True, noise_rate=0.0))
    clean = {(u, v): d["_qw"] for u, v, d in G.edges(data=True)}
    static_time_weights(G, RetrievalConfig(name="q", static_ppr=True, noise_rate=1.0, noise_seed=3))
    noisy = {(u, v): d["_qw"] for u, v, d in G.edges(data=True)}
    assert clean != noisy  # cache is keyed by the noise setting, so weights are recomputed


def test_candidate_facts_are_recorded_with_their_time_weight():
    # The record used by demo_compare.py: hard filter gives the Q1 fact weight 0 (dropped),
    # the soft kernel gives it exp(-1 * 2) because 2023-Q1 is two tree steps from 2023-Q2.
    import math
    _run(build_retriever(RetrievalConfig(name="tgrag")), "ACME revenue 2023 Q2", ["2023-Q2"])
    hard = {(f["src"], f["tgt"], f["ts"]): f for f in LAST_RETRIEVAL["candidate_facts"]}
    _run(build_retriever(RetrievalConfig(name="B1", lam=1.0)), "ACME revenue 2023 Q2", ["2023-Q2"])
    soft = {(f["src"], f["tgt"], f["ts"]): f for f in LAST_RETRIEVAL["candidate_facts"]}
    key = ("ACME", "REVENUE", "2023-Q1")
    assert hard[key]["weight"] == 0.0 and not hard[key]["kept"]
    assert soft[key]["weight"] == pytest.approx(math.exp(-2), abs=1e-4) and soft[key]["kept"]
    assert soft[key]["text"].startswith("ACME revenue in 2023 Q1")
