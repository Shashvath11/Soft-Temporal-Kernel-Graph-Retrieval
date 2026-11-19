# Changes to TG-RAG's `tgrag/configs/config.yaml`

The study used TG-RAG at commit `350f5163f2f6a56700fd20f20684d83aabbe44d7` with only the model lines changed,
so that all models are reached through one OpenRouter key:

| Section | Key | Upstream | Used in this study |
|---|---|---|---|
| `building` | `provider` | `gemini` | `openai` |
| `building` | `model` | `gemini-2.5-flash-lite` | `google/gemini-2.5-flash-lite` |
| `querying` | `provider` | `gemini` | `openai` |
| `querying` | `model` | `gemini-2.5-flash` | `openai/gpt-4o-mini` |

`src/softtime/openrouter.py` adds the provider prefix that OpenRouter needs to the embedding model name at run time.
No other TG-RAG file was changed.
