"""Build TG-RAG's plain-RAG (naive) chunk index from an existing graph folder.

TG-RAG only embeds the text chunks for naive mode when the graph was built with
enable_naive_rag: true. Graphs built with the default settings have the chunks
(kv_store_text_chunks.json) but no vdb_chunks.json. This embeds those same chunks once
(about 330k tokens for the 6-company subset, well under one US cent with
text-embedding-3-small) and saves vdb_chunks.json next to the graph. The graph itself is
not changed, and later naive runs reuse the saved index.
"""
from __future__ import annotations


async def ensure_chunk_index(graph_rag) -> int:
    """Embed every stored text chunk into graph_rag.chunks_vdb if it is empty.

    Returns how many chunks were embedded (0 if the index already existed).
    """
    vdb = graph_rag.chunks_vdb
    if vdb is None:
        raise ValueError("chunks_vdb is None: create TG-RAG with enable_naive_rag=True")
    if getattr(vdb, "_data", None):
        return 0
    keys = await graph_rag.text_chunks.all_keys()
    chunks = await graph_rag.text_chunks.get_by_ids(keys)
    data = {k: {"content": c["content"]} for k, c in zip(keys, chunks) if c and c.get("content")}
    if not data:
        raise ValueError("No text chunks found in the graph folder; check --working_dir")
    await vdb.upsert(data)
    await vdb.index_done_callback()
    return len(data)
