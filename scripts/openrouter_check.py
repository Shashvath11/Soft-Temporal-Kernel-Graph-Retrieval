"""Check that ONE OpenRouter key reaches every model the project uses (costs a fraction of a cent).

Usage (from the Temporal-GraphRAG folder, after filling in .env):
    python scripts/openrouter_check.py

The same key and base URL are used for all four calls; only the model name changes.
"""
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

key = os.getenv("OPENAI_API_KEY", "")
base = os.getenv("OPENAI_BASE_URL", "")
if not key.startswith("sk-or-") or "openrouter.ai" not in base:
    sys.exit("In .env set OPENAI_API_KEY to your OpenRouter key (starts with sk-or-) and "
             "OPENAI_BASE_URL to https://openrouter.ai/api/v1")

client = OpenAI(api_key=key, base_url=base)  # one key, one base URL, for everything below

# 1. Graph building (build_graph.py): Gemini extracts dated facts from a transcript sentence
r = client.chat.completions.create(
    model="google/gemini-2.5-flash-lite",
    messages=[{"role": "user", "content":
               "Extract one fact as (company | metric | value | quarter) from: "
               "'In the second quarter of 2023, Western Digital reported revenue of $3.1 billion.'"}],
    temperature=0,
)
print("1. Graph building  (google/gemini-2.5-flash-lite):", r.choices[0].message.content.strip())

# 2. Embeddings (graph store vectors + question search): same key, embedding model
e = client.embeddings.create(model="openai/text-embedding-3-small", input=["Crocs revenue 2020 Q1"])
print("2. Embeddings      (openai/text-embedding-3-small): vector length", len(e.data[0].embedding))

# 3. Answer generation (run_ectqa.py): GPT-4o-mini answers from retrieved text
r = client.chat.completions.create(
    model="openai/gpt-4o-mini",
    messages=[{"role": "user", "content":
               "Context: Western Digital revenue was $3.7B in 2023 Q1 and $3.1B in 2023 Q2.\n"
               "Question: What was Western Digital's revenue in 2023 Q2? Answer in one line."}],
    temperature=0,
)
print("3. Answering       (openai/gpt-4o-mini):", r.choices[0].message.content.strip())

# 4. Judging (judge.py): GPT-4o-mini returns JSON scores
r = client.chat.completions.create(
    model="openai/gpt-4o-mini",
    response_format={"type": "json_object"},
    messages=[{"role": "user", "content":
               'Gold answer: "$3.1 billion". Prediction: "$3.1B". '
               'Return JSON {"correct": int, "refusal": int, "incorrect": int}.'}],
    temperature=0,
)
print("4. Judging         (openai/gpt-4o-mini, JSON):", r.choices[0].message.content.strip())
print("\nAll four calls used the same OpenRouter key. You're ready.")
