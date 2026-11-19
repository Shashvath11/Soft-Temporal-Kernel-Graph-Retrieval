"""pytest setup: make src/ and the TG-RAG checkout importable (see scripts/_paths.py)."""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TGRAG_HOME = Path(os.environ.get("TGRAG_HOME", ROOT / "third_party" / "TG-RAG"))
for p in (ROOT / "src", TGRAG_HOME, ROOT / "scripts"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
