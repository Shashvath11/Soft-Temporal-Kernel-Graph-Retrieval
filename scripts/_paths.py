"""Make the package in src/ and the TG-RAG checkout importable when a script is run directly.

TG-RAG is not part of this repository (its release has no licence file). Clone it into
third_party/TG-RAG (see third_party/README.md) or point TGRAG_HOME at an existing checkout.
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TGRAG_HOME = Path(os.environ.get("TGRAG_HOME", ROOT / "third_party" / "TG-RAG"))
for p in (ROOT / "src", TGRAG_HOME):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
