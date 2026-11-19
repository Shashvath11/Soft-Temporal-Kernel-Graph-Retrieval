"""Use ONE OpenRouter key for every model in the project.

When the OpenAI client's base URL points to OpenRouter (https://openrouter.ai/api/v1), model
names without a provider prefix are rewritten to OpenRouter's IDs before each request:

    text-embedding-3-small  -> openai/text-embedding-3-small   (hard-coded inside TG-RAG)
    gpt-4o-mini             -> openai/gpt-4o-mini
    gemini-2.5-flash-lite   -> google/gemini-2.5-flash-lite

Names that already contain "/" (e.g. "google/gemini-2.5-flash-lite") are left untouched.
With any other base URL (e.g. api.openai.com) nothing changes. TG-RAG's files are not edited.

Gemini calls through OpenRouter also get temperature 0.0 and max_tokens 4096 when the caller sets
neither, matching what TG-RAG's own Gemini client uses (tgrag/src/llm/client.py), so graph building
behaves the same as with a direct Google key.
"""
from __future__ import annotations

import functools

_PREFIXES = (("text-embedding-", "openai/"), ("gpt-", "openai/"), ("o1", "openai/"), ("o3", "openai/"),
             ("o4", "openai/"), ("gemini-", "google/"))


def openrouter_model_id(model: str) -> str:
    """Return the OpenRouter ID for a bare model name; IDs with a '/' pass through."""
    if not isinstance(model, str) or "/" in model:
        return model
    for start, prefix in _PREFIXES:
        if model.startswith(start):
            return prefix + model
    return model


def _is_openrouter(resource) -> bool:
    try:
        return "openrouter.ai" in str(resource._client.base_url)
    except Exception:
        return False


def _fix(kwargs: dict, chat: bool) -> dict:
    if "model" in kwargs:
        kwargs["model"] = openrouter_model_id(kwargs["model"])
        if chat and str(kwargs["model"]).startswith("google/"):
            kwargs.setdefault("temperature", 0.0)
            if "max_tokens" not in kwargs and "max_completion_tokens" not in kwargs:
                kwargs["max_tokens"] = 4096
    return kwargs


def _wrap(cls, is_async: bool, chat: bool):
    original = cls.create
    if getattr(original, "_openrouter_wrapped", False):
        return

    if is_async:
        @functools.wraps(original)
        async def create(self, *args, **kwargs):
            if _is_openrouter(self):
                kwargs = _fix(kwargs, chat)
            return await original(self, *args, **kwargs)
    else:
        @functools.wraps(original)
        def create(self, *args, **kwargs):
            if _is_openrouter(self):
                kwargs = _fix(kwargs, chat)
            return original(self, *args, **kwargs)

    create._openrouter_wrapped = True
    cls.create = create


def enable() -> None:
    """Patch the OpenAI SDK's chat and embedding calls (safe to call more than once)."""
    from openai.resources import AsyncEmbeddings, Embeddings
    from openai.resources.chat import AsyncCompletions, Completions

    _wrap(Embeddings, False, chat=False)
    _wrap(AsyncEmbeddings, True, chat=False)
    _wrap(Completions, False, chat=True)
    _wrap(AsyncCompletions, True, chat=True)
