"""Drop-in replacement for TG-RAG's local retrieval (querying._retrieve_chunks_with_ppr_algorithm).

One function covers every variant in the study:

    tgrag  : hard 0/1 time filter, embedding seeding, plain PPR (re-implementation of TG-RAG)
    B1     : soft time kernel in seeding and edge scoring
    B12    : B1 + time-weighted PPR transitions (Module B)
    C      : time-partitioned hybrid BM25 + dense seeding with RRF (Module C)
    BC     : Modules B and C together (full model)
    B1QI   : ablation: B1 + a query-INDEPENDENT temporal decay in the PPR walk (DyG-RAG-style).
             Identical to B12 except the walk weights ignore the question's dates.

Every variant can also run with injected timestamp noise (the robustness test).
TG-RAG's source code is never modified; run_ectqa.py swaps this function in at runtime.
"""
from __future__ import annotations

import hashlib
import math
import re
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

import networkx as nx
import numpy as np

from .soft_time import clean_ts, corrupt_timestamp, fiscal_aliases, kappa

LAST_RETRIEVAL: dict = {}  # filled after every call; the runner saves it with each answer


@dataclass
class RetrievalConfig:
    name: str = "tgrag"
    lam: Optional[float] = None        # None = TG-RAG's hard filter; a number = soft kernel
    kappa_min: float = 0.05            # facts with weight below this are ignored
    weighted_ppr: bool = False         # Module B2: walk weighted by kappa(fact time, question time)
    static_ppr: bool = False           # ablation: walk weighted by query-independent temporal coherence
    qi_alpha: float = 1.0              # decay rate of the query-independent weights
    untimed_edge_weight: float = 1.0   # PPR weight of edges that carry no timestamps
    hybrid_seeding: bool = False       # Module C
    rrf_k: int = 60
    noise_rate: float = 0.0            # share of stored timestamps shifted by one quarter
    noise_seed: int = 13
    fiscal_offsets: dict = field(default_factory=dict)


VARIANTS = {
    "tgrag": RetrievalConfig(name="tgrag"),
    "B1": RetrievalConfig(name="B1", lam=1.0),
    "B12": RetrievalConfig(name="B12", lam=1.0, weighted_ppr=True),
    "C": RetrievalConfig(name="C", hybrid_seeding=True),
    "BC": RetrievalConfig(name="BC", lam=1.0, weighted_ppr=True, hybrid_seeding=True),
    "B1QI": RetrievalConfig(name="B1QI", lam=1.0, static_ppr=True, qi_alpha=1.0),
}

_TOKEN = re.compile(r"[a-z0-9$%.]+")


def _content_hash(chunk: dict) -> str:
    return hashlib.md5(str(chunk.get("content", "")).encode("utf-8")).hexdigest()[:12]


def _tokens(text: str) -> list:
    return _TOKEN.findall(str(text).lower())


def _split_relation_name(name: str):
    """Relation keys are stored as SRC_TGT_TIMESTAMP (tgrag/src/core/building.py)."""
    parts = str(name).split("_")
    if len(parts) == 3:
        return parts[0], parts[1], parts[2]
    if len(parts) == 2:
        return parts[0], parts[1], None
    return None


class _RelationIndex:
    """BM25 + dense index over every stored relation; built once per graph and cached."""

    def __init__(self, relations_vdb):
        from rank_bm25 import BM25Okapi

        self.ids, self.src, self.tgt, self.ts = [], [], [], []
        docs, vecs = [], []
        for doc_id, meta in relations_vdb._data.items():
            parsed = _split_relation_name(meta.get("entity_name", ""))
            emb = relations_vdb._embeddings.get(doc_id)
            if parsed is None or emb is None:
                continue
            s, t, ts = parsed
            self.ids.append(doc_id)
            self.src.append(s)
            self.tgt.append(t)
            self.ts.append(ts)
            docs.append(_tokens(f"{s} {t} {meta.get('content', '')}") or ["_"])
            vecs.append(emb)
        if not docs:
            raise ValueError("relations index is empty: was the graph built in this working_dir?")
        self.bm25 = BM25Okapi(docs)
        mat = np.asarray(vecs, dtype=np.float32)
        self.mat = mat / np.maximum(np.linalg.norm(mat, axis=1, keepdims=True), 1e-12)


_INDEX_CACHE: dict = {}


def _relation_index(relations_vdb) -> _RelationIndex:
    key = id(relations_vdb)
    if key not in _INDEX_CACHE:
        _INDEX_CACHE[key] = _RelationIndex(relations_vdb)
    return _INDEX_CACHE[key]


async def _query_vector(relations_vdb, query: str) -> np.ndarray:
    enhance = getattr(relations_vdb, "_enhance_query_for_semantic_matching", None)
    text = enhance(query) if enhance else query
    vec = np.asarray((await relations_vdb.embedding_func([text]))[0], dtype=np.float32)
    return vec / max(float(np.linalg.norm(vec)), 1e-12)


def static_time_weights(G, cfg: RetrievalConfig) -> str:
    """Query-independent temporal edge weights for the PPR walk (DyG-RAG-style ablation).

    DyG-RAG (arXiv 2507.13396) links two events with weight exp(-alpha * |t_i - t_j|), so its walk
    favours paths through events close in time; the weights are fixed at build time and do not
    depend on the question. TG-RAG's graph is over entities, and each entity-entity edge holds
    several timestamped facts. First-order adaptation used here:

        coh(f)   = mean over facts f' sharing an entity with f of exp(-alpha * d_H(t_f, t_f'))
        w(u, v)  = max over facts f on edge (u, v) of coh(f)

    A fact that agrees in time with its neighbourhood gets a strong edge; an outlier date gets a
    weak one. Unlike B12's kappa, nothing here looks at the question. Weights are computed once per
    (alpha, noise) setting and cached on the graph. Returns the edge attribute name to use.
    """
    from collections import Counter

    from .soft_time import hierarchy_distance

    attr = "_qw"
    key = ("softtime_qi", cfg.qi_alpha, cfg.noise_rate, cfg.noise_seed, cfg.kappa_min, cfg.untimed_edge_weight)
    if G.graph.get("_softtime_qi_key") == key:
        return attr

    node_ts = defaultdict(Counter)   # entity -> multiset of (cleaned, noisy) timestamps of incident facts
    edge_ts = {}                     # (u, v) -> list of timestamps of facts on that edge
    for u, v, data in G.edges(data=True):
        sid = data.get("source_id")
        if isinstance(sid, dict):
            stamps = [clean_ts(corrupt_timestamp(ts, u, v, cfg.noise_rate, cfg.noise_seed)) for ts in sid]
            edge_ts[(u, v)] = stamps
            for t in stamps:
                node_ts[u][t] += 1
                if v != u:
                    node_ts[v][t] += 1

    decay_cache = {}

    def decay(a, b):
        k = (a, b)
        if k not in decay_cache:
            d = hierarchy_distance(a, b)
            decay_cache[k] = 0.0 if d is None else math.exp(-cfg.qi_alpha * d)
        return decay_cache[k]

    for u, v, data in G.edges(data=True):
        sid = data.get("source_id")
        if not isinstance(sid, dict):
            data[attr] = cfg.untimed_edge_weight
            continue
        stamps = edge_ts.get((u, v), [])
        if not stamps:
            data[attr] = 0.0
            continue
        on_edge = Counter(stamps)
        neigh = node_ts[u] + node_ts[v]
        neigh.subtract(on_edge)  # facts on this edge were counted at both endpoints; keep them once
        best = 0.0
        for t in set(stamps):
            others = neigh.copy()
            others[t] -= 1        # exclude the fact itself
            total = sum(c for c in others.values() if c > 0)
            if total <= 0:
                coh = 1.0 if hierarchy_distance(t, t) is not None else 0.0  # no neighbours: neutral
            else:
                coh = sum(c * decay(t, t2) for t2, c in others.items() if c > 0) / total
            best = max(best, coh)
        data[attr] = best if best >= cfg.kappa_min else 0.0
    G.graph["_softtime_qi_key"] = key
    return attr


def _rrf(order_lists, k: int) -> dict:
    scores = defaultdict(float)
    for order in order_lists:
        for rank, i in enumerate(order, start=1):
            scores[i] += 1.0 / (k + rank)
    return scores


def build_retriever(cfg: RetrievalConfig):
    if cfg.weighted_ppr and cfg.static_ppr:
        raise ValueError("choose either weighted_ppr (query-relative) or static_ppr (query-independent), not both")
    from tgrag.src.core import querying  # imported lazily so tests can load this module

    async def retrieve(query, relations_vdb, knowledge_graph_inst, aligned_timestamp_in_query,
                       text_chunks_db, query_param, global_config, temporal_hierarchy=None):
        LAST_RETRIEVAL.clear()
        LAST_RETRIEVAL.update(variant=cfg.name, query_timestamps=list(aligned_timestamp_in_query or []),
                              chunk_ids=[], chunk_hashes=[], n_seeds=0)
        if not relations_vdb:
            return []

        k_rel = query_param.top_k * 3  # same candidate budget as the released TG-RAG code
        no_timestamp = not aligned_timestamp_in_query

        # Hard scope T_q, expanded to descendants exactly as TG-RAG does
        timestamps_set = set()
        if not no_timestamp and temporal_hierarchy:
            for q_ts in aligned_timestamp_in_query:
                timestamps_set.update(querying._get_all_descendant_timestamps(q_ts, temporal_hierarchy))
            timestamps_set = {clean_ts(ts) for ts in timestamps_set}
        elif not no_timestamp:
            timestamps_set = {clean_ts(ts) for ts in aligned_timestamp_in_query}
        query_ts = [clean_ts(t) for t in (aligned_timestamp_in_query or [])]

        def weight(ts, src, tgt, scope=None):
            """kappa for one stored fact (after optional noise); 1/0 in hard mode."""
            if no_timestamp:
                return 1.0
            ts2 = corrupt_timestamp(ts, src, tgt, cfg.noise_rate, cfg.noise_seed)
            if cfg.lam is None:
                if scope is None:
                    return 1.0 if clean_ts(ts2) in timestamps_set else 0.0
                return 1.0 if clean_ts(ts2) in scope else 0.0
            aliases = fiscal_aliases(ts2, src, tgt, cfg.fiscal_offsets)
            return kappa(ts2, scope if scope is not None else query_ts, cfg.lam, aliases)

        def keep(w):
            return w >= 1.0 if cfg.lam is None else w >= cfg.kappa_min

        # ---------- Step 1-2: seed relations and seed entities ----------
        seed_weights = defaultdict(float)
        relation_metadata = {}  # (src, tgt, ts) -> similarity gamma
        fact_text = {}  # (src, tgt, ts) -> stored relation description, only used for the record below

        if cfg.hybrid_seeding:
            idx = _relation_index(relations_vdb)
            qv = await _query_vector(relations_vdb, query)
            dense = idx.mat @ qv
            bm25 = idx.bm25.get_scores(_tokens(query) or ["_"])
            if no_timestamp:
                groups = [list(range(len(idx.ids)))]
            else:
                groups = []
                for q_ts in aligned_timestamp_in_query:
                    if cfg.lam is None:
                        scope = {clean_ts(x) for x in (querying._get_all_descendant_timestamps(q_ts, temporal_hierarchy)
                                                     if temporal_hierarchy else {q_ts})}
                    else:
                        scope = [clean_ts(q_ts)]
                    members = [i for i in range(len(idx.ids)) if idx.ts[i] is not None
                               and keep(weight(idx.ts[i], idx.src[i], idx.tgt[i], scope))]
                    groups.append(members)
            quota = math.ceil(k_rel / max(len(groups), 1))
            chosen = []
            for members in groups:
                if not members:
                    continue
                by_dense = sorted(members, key=lambda i: -dense[i])
                by_bm25 = sorted(members, key=lambda i: -bm25[i])
                fused = _rrf([by_dense, by_bm25], cfg.rrf_k)
                chosen += sorted(fused, key=lambda i: -fused[i])[:quota]
            candidates = [(idx.src[i], idx.tgt[i], idx.ts[i], float(dense[i])) for i in dict.fromkeys(chosen)]
        else:
            rels = await relations_vdb.query(query, top_k=k_rel)
            candidates = []
            for rel in rels or []:
                parsed = _split_relation_name(rel.get("entity_name", ""))
                if parsed:
                    candidates.append((*parsed, float(rel.get("similarity", 0.0))))
                    fact_text[parsed] = str(rel.get("content", ""))

        # Record every candidate fact with its time weight, so the demo and error analysis can show
        # which facts the time filter kept or dropped. This is bookkeeping only: it changes no score.
        facts_record = []
        LAST_RETRIEVAL["candidate_facts"] = facts_record

        for src, tgt, ts, sim in candidates:
            if no_timestamp:
                facts_record.append({"src": src, "tgt": tgt, "ts": ts, "sim": round(sim, 4),
                                     "weight": 1.0, "kept": True})
                seed_weights[src] = max(seed_weights[src], 1.0)
                seed_weights[tgt] = max(seed_weights[tgt], 1.0)
                continue
            if ts is None:
                continue
            w = weight(ts, src, tgt)
            facts_record.append({"src": src, "tgt": tgt, "ts": ts, "sim": round(sim, 4),
                                 "weight": round(w, 4), "kept": keep(w),
                                 "text": fact_text.get((src, tgt, ts), "")[:200]})
            if keep(w):
                seed_weights[src] = max(seed_weights[src], w)
                seed_weights[tgt] = max(seed_weights[tgt], w)
                relation_metadata[(src, tgt, clean_ts(ts))] = sim

        LAST_RETRIEVAL["n_seeds"] = len(seed_weights)
        if not seed_weights:
            return []

        # ---------- Step 3: (time-weighted) Personalized PageRank ----------
        n_top = query_param.top_k * 2
        if (cfg.weighted_ppr or cfg.static_ppr) and hasattr(knowledge_graph_inst, "_graph"):
            G = knowledge_graph_inst._graph
            if cfg.static_ppr:
                walk_attr = static_time_weights(G, cfg)
            else:
                walk_attr = "_tw"
                for u, v, data in G.edges(data=True):
                    sid = data.get("source_id")
                    if isinstance(sid, dict) and sid:
                        w = max(weight(ts, u, v) for ts in sid)
                    elif isinstance(sid, dict):
                        w = 0.0
                    else:
                        w = cfg.untimed_edge_weight
                    data["_tw"] = w if w >= cfg.kappa_min else 0.0
            pers = {n: w for n, w in seed_weights.items() if G.has_node(n)}
            total = sum(pers.values())
            pers = {n: w / total for n, w in pers.items()} if total > 0 else None
            try:
                scores = nx.pagerank(G, alpha=0.85, personalization=pers, max_iter=100, tol=1e-6, weight=walk_attr)
            except nx.PowerIterationFailedConvergence:
                scores = nx.pagerank(G, alpha=0.85, personalization=pers, max_iter=1000, tol=1e-6,
                                     weight=walk_attr)
            ppr_results = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:n_top]
        elif cfg.lam is None:
            ppr_results = await knowledge_graph_inst.get_top_pagerank_nodes(
                personalization_nodes=list(seed_weights), top_k=n_top, alpha=0.85)
        else:
            ppr_results = await knowledge_graph_inst.get_top_pagerank_nodes(
                personalization_nodes=list(seed_weights), personalization_weights=dict(seed_weights),
                top_k=n_top, alpha=0.85)
        ppr_scores = dict(ppr_results)

        # ---------- Step 4-5: edge scores s(e) = kappa * (s(v1)+s(v2)); chunk scores ----------
        chunk_edge_scores = defaultdict(float)
        chunk_edge_sims = defaultdict(list)
        for i in range(len(ppr_results)):
            for j in range(i + 1, len(ppr_results)):
                src_id, tgt_id = ppr_results[i][0], ppr_results[j][0]
                edge_data = await knowledge_graph_inst.get_edge(src_id, tgt_id)
                if not edge_data:
                    continue
                edge_score = ppr_scores.get(src_id, 0.0) + ppr_scores.get(tgt_id, 0.0)
                edge_sim = 0.0
                for (s, t, _), sim in relation_metadata.items():
                    if s == src_id and t == tgt_id:
                        edge_sim = sim
                        break
                sid = edge_data.get("source_id", {})
                if isinstance(sid, dict):
                    for ts, chunk_id in sid.items():
                        w = weight(ts, src_id, tgt_id)
                        if keep(w):
                            chunk_edge_scores[chunk_id] += w * edge_score
                            chunk_edge_sims[chunk_id].append(edge_sim)
                elif isinstance(sid, str):
                    for chunk_id in querying.split_string_by_multi_markers(sid, [querying.GRAPH_FIELD_SEP]):
                        chunk_edge_scores[chunk_id] += edge_score
                        chunk_edge_sims[chunk_id].append(edge_sim)

        doc_scores = {}
        for chunk_id, total in chunk_edge_scores.items():
            w_c = 1.0
            for g in chunk_edge_sims.get(chunk_id, []):
                w_c *= 1.0 + g
            doc_scores[chunk_id] = w_c * total
        ranked = sorted(doc_scores.items(), key=lambda x: x[1], reverse=True)[: query_param.top_k]

        # ---------- Step 6: greedy packing up to the context budget ----------
        from tgrag.src.utils import helpers
        model_name = global_config.get("tiktoken_model_name", "gpt-4o-mini")
        chunks, used = [], 0
        for chunk_id, _ in ranked:
            data = await text_chunks_db.get_by_id(chunk_id)
            if data is None:
                continue
            n_tok = len(helpers.encode_string_by_tiktoken(data.get("content", ""), model_name=model_name))
            if used + n_tok > query_param.local_max_token_for_text_unit:
                break
            chunks.append(data)
            used += n_tok
            LAST_RETRIEVAL["chunk_ids"].append(chunk_id)
            LAST_RETRIEVAL["chunk_hashes"].append(_content_hash(data))
        LAST_RETRIEVAL["context_tokens"] = used
        return chunks

    return retrieve


def install(cfg: Optional[RetrievalConfig]):
    """Swap TG-RAG's retrieval function. cfg=None keeps the original but still records chunk ids."""
    from tgrag.src.core import querying

    if not hasattr(querying, "_ORIGINAL_RETRIEVER"):
        querying._ORIGINAL_RETRIEVER = querying._retrieve_chunks_with_ppr_algorithm
    if cfg is None:
        original = querying._ORIGINAL_RETRIEVER

        async def recorded(*args, **kwargs):
            LAST_RETRIEVAL.clear()
            LAST_RETRIEVAL.update(variant="original", chunk_ids=[])
            chunks = await original(*args, **kwargs)
            LAST_RETRIEVAL["chunk_hashes"] = [_content_hash(c) for c in chunks]
            LAST_RETRIEVAL["n_chunks"] = len(chunks)
            return chunks

        querying._retrieve_chunks_with_ppr_algorithm = recorded
    else:
        querying._retrieve_chunks_with_ppr_algorithm = build_retriever(cfg)
