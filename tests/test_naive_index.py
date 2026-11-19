"""The naive-mode chunk index is built once from the stored chunks and then reused."""
import asyncio
import json
import os
from types import SimpleNamespace

import numpy as np

from tgrag.src.storage.kv_json import JsonKVStorage
from tgrag.src.storage.vector_nanovectordb import NanoVectorDBStorage
from softtime.naive_index import ensure_chunk_index

CALLS = []


async def fake_embed(texts):
    CALLS.append(len(texts))
    return np.array([[float(len(t)), 1.0, 0.5] for t in texts], dtype=np.float32)


fake_embed.embedding_dim = 3


def make(tmp_path):
    cfg = {"working_dir": str(tmp_path), "embedding_batch_num": 2}
    kv = JsonKVStorage(namespace="text_chunks", global_config=cfg)
    vdb = NanoVectorDBStorage(namespace="chunks", global_config=cfg, embedding_func=fake_embed)
    return SimpleNamespace(text_chunks=kv, chunks_vdb=vdb)


def test_builds_once_and_reuses(tmp_path):
    chunks = {f"chunk-{i}": {"content": f"Crocs revenue text {i}" * (i + 1), "tokens": 5} for i in range(3)}
    (tmp_path / "kv_store_text_chunks.json").write_text(json.dumps(chunks))
    CALLS.clear()
    assert asyncio.run(ensure_chunk_index(make(tmp_path))) == 3
    assert os.path.exists(tmp_path / "vdb_chunks.json")
    assert sum(CALLS) == 3
    # a second run loads the saved index and embeds nothing
    CALLS.clear()
    g = make(tmp_path)
    assert asyncio.run(ensure_chunk_index(g)) == 0
    assert CALLS == []
    assert set(g.chunks_vdb._data) == set(chunks)
