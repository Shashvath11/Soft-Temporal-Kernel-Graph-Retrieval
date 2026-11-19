"""Run one of TG-RAG's own scripts with OpenRouter model names switched on.

TG-RAG hard-codes the embedding model as "text-embedding-3-small"; OpenRouter needs
"openai/text-embedding-3-small". This wrapper fixes that at runtime, then runs the script unchanged.

Usage (from the Temporal-GraphRAG folder):
    python scripts/or_run.py build_graph.py --output_dir ./graph_subset --corpus_path ect-qa/subset/base_subset.jsonl.gz --num_docs 96
    python scripts/or_run.py query_graph.py --question "What was Crocs revenue in 2020 Q1?" --working_dir ./graph_smoke --mode local
"""
import runpy
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
import _paths  # noqa: F401,E402  (src/ and TG-RAG on sys.path)
load_dotenv(ROOT / ".env")

from softtime.openrouter import enable  # noqa: E402

if len(sys.argv) < 2:
    sys.exit(__doc__)
script = ROOT / sys.argv[1]
if not script.exists():
    sys.exit(f"Script not found: {script}")
enable()
sys.argv = [str(script)] + sys.argv[2:]
runpy.run_path(str(script), run_name="__main__")
