"""Offline tests for the OpenRouter switch: model names are rewritten only for OpenRouter."""
import asyncio
import json

import httpx
from openai import AsyncOpenAI, OpenAI

from softtime.openrouter import enable, openrouter_model_id

SEEN = []
PARAMS = []


def _handler(request: httpx.Request) -> httpx.Response:
    body = json.loads(request.content)
    SEEN.append((request.url.host, body["model"]))
    PARAMS.append({k: body.get(k) for k in ("temperature", "max_tokens")})
    if request.url.path.endswith("/embeddings"):
        return httpx.Response(200, json={"object": "list", "model": body["model"],
                                         "data": [{"object": "embedding", "index": 0, "embedding": [0.1, 0.2]}],
                                         "usage": {"prompt_tokens": 1, "total_tokens": 1}})
    return httpx.Response(200, json={"id": "x", "object": "chat.completion", "created": 0, "model": body["model"],
                                     "choices": [{"index": 0, "finish_reason": "stop",
                                                  "message": {"role": "assistant", "content": "ok"}}]})


def test_model_id_mapping():
    assert openrouter_model_id("text-embedding-3-small") == "openai/text-embedding-3-small"
    assert openrouter_model_id("gpt-4o-mini") == "openai/gpt-4o-mini"
    assert openrouter_model_id("gemini-2.5-flash-lite") == "google/gemini-2.5-flash-lite"
    assert openrouter_model_id("google/gemini-2.5-flash-lite") == "google/gemini-2.5-flash-lite"


def test_rewrites_only_for_openrouter():
    enable()
    enable()  # calling twice must not double-wrap
    SEEN.clear()
    PARAMS.clear()
    transport = httpx.MockTransport(_handler)
    orr = OpenAI(api_key="sk-or-test", base_url="https://openrouter.ai/api/v1",
                 http_client=httpx.Client(transport=transport))
    oai = OpenAI(api_key="sk-test", base_url="https://api.openai.com/v1",
                 http_client=httpx.Client(transport=transport))
    orr.embeddings.create(model="text-embedding-3-small", input=["a"])
    orr.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": "hi"}])
    orr.chat.completions.create(model="google/gemini-2.5-flash-lite", messages=[{"role": "user", "content": "hi"}])
    oai.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": "hi"}])

    async def run_async():
        aorr = AsyncOpenAI(api_key="sk-or-test", base_url="https://openrouter.ai/api/v1",
                           http_client=httpx.AsyncClient(transport=httpx.MockTransport(_handler)))
        await aorr.embeddings.create(model="text-embedding-3-small", input=["a"], encoding_format="float")
        await aorr.chat.completions.create(model="gemini-2.5-flash-lite", messages=[{"role": "user", "content": "x"}])

    asyncio.run(run_async())
    assert SEEN == [
        ("openrouter.ai", "openai/text-embedding-3-small"),
        ("openrouter.ai", "openai/gpt-4o-mini"),
        ("openrouter.ai", "google/gemini-2.5-flash-lite"),
        ("api.openai.com", "gpt-4o-mini"),
        ("openrouter.ai", "openai/text-embedding-3-small"),
        ("openrouter.ai", "google/gemini-2.5-flash-lite"),
    ]
    # Gemini via OpenRouter gets TG-RAG's Gemini defaults; OpenAI models are left as sent
    assert PARAMS[2] == {"temperature": 0.0, "max_tokens": 4096}
    assert PARAMS[1] == {"temperature": None, "max_tokens": None}
    assert PARAMS[5] == {"temperature": 0.0, "max_tokens": 4096}
