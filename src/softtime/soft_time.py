"""Module B1: soft hierarchical time kernel, plus timestamp noise and fiscal aliases.

TG-RAG timestamps use the formats YYYY, YYYY-QN, YYYY-MM and YYYY-MM-DD
(tgrag/configs/prompts.yaml). Each timestamp is a node in a time hierarchy:

    root -> year -> quarter -> month -> day

kappa(tau, Tq) = max over t in Tq of exp(-lam * d(tau, t))

where d(tau, t) = 0 if tau lies inside t's subtree (tau equals t or is a
descendant, which is exactly what TG-RAG's hard filter keeps), and otherwise the
shortest-path distance between tau and t in the hierarchy.
As lam -> infinity, kappa becomes TG-RAG's 0/1 filter.
"""
from __future__ import annotations

import hashlib
import math
import re
from functools import lru_cache
from typing import Iterable, Optional

_YEAR = re.compile(r"^(\d{4})$")
_QUARTER = re.compile(r"^(\d{4})-Q([1-4])$")
_MONTH = re.compile(r"^(\d{4})-(\d{2})$")
_DATE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})$")


def clean_ts(ts: str) -> str:
    """Strip quotes/whitespace and upper-case, so '"2023-q1"' -> '2023-Q1'."""
    return str(ts).replace('"', "").replace("'", "").strip().upper()


@lru_cache(maxsize=200_000)
def ts_path(ts: str) -> Optional[tuple]:
    """Path from the root of the time hierarchy to this timestamp, or None if unparseable."""
    s = clean_ts(ts)
    m = _YEAR.match(s)
    if m:
        return (m.group(1),)
    m = _QUARTER.match(s)
    if m:
        y, q = m.groups()
        return (y, f"{y}-Q{q}")
    m = _MONTH.match(s)
    if m:
        y, mo = m.group(1), int(m.group(2))
        if not 1 <= mo <= 12:
            return None
        q = (mo - 1) // 3 + 1
        return (y, f"{y}-Q{q}", f"{y}-{mo:02d}")
    m = _DATE.match(s)
    if m:
        y, mo, d = m.group(1), int(m.group(2)), m.group(3)
        if not 1 <= mo <= 12:
            return None
        q = (mo - 1) // 3 + 1
        return (y, f"{y}-Q{q}", f"{y}-{mo:02d}", f"{y}-{mo:02d}-{d}")
    return None


def hierarchy_distance(tau: str, t: str) -> Optional[int]:
    """0 if tau is t or inside t's subtree; else shortest-path distance; None if unparseable."""
    a, b = ts_path(tau), ts_path(t)
    if a is None or b is None:
        return None
    if a[: len(b)] == b:  # tau is t itself or one of its descendants
        return 0
    common = 0
    for x, y in zip(a, b):
        if x != y:
            break
        common += 1
    # two different years share only the (virtual) root
    return len(a) + len(b) - 2 * common


def shift_quarters(ts: str, k: int) -> str:
    """Move a timestamp by k quarters (a year-level timestamp moves by k years)."""
    s = clean_ts(ts)
    p = ts_path(s)
    if p is None or k == 0:
        return s
    if len(p) == 1:
        return str(int(p[0]) + k)
    if len(p) == 2:
        y, q = int(s[:4]), int(s[-1])
        idx = y * 4 + (q - 1) + k
        return f"{idx // 4}-Q{idx % 4 + 1}"
    y, mo = int(s[:4]), int(s[5:7])
    idx = y * 12 + (mo - 1) + 3 * k
    ny, nm = idx // 12, idx % 12 + 1
    if len(p) == 3:
        return f"{ny}-{nm:02d}"
    day = min(int(s[8:10]), 28)
    return f"{ny}-{nm:02d}-{day:02d}"


def corrupt_timestamp(ts: str, src: str, tgt: str, rate: float, seed: int) -> str:
    """Deterministically shift a stored timestamp by +/-1 quarter with probability `rate`.

    The same fact (same entity pair + timestamp) is always corrupted the same way, so the
    relation index and the graph edges stay consistent, and every method sees identical noise.
    """
    if rate <= 0:
        return ts
    a, b = sorted([str(src), str(tgt)])
    h = hashlib.sha256(f"{seed}|{a}|{b}|{clean_ts(ts)}".encode()).digest()
    u = int.from_bytes(h[:8], "big") / 2**64
    if u >= rate:
        return ts
    direction = 1 if h[8] % 2 == 0 else -1
    return shift_quarters(ts, direction)


def fiscal_aliases(ts: str, src: str, tgt: str, offsets: dict) -> list:
    """Extra calendar readings of a timestamp for companies whose fiscal year differs.

    offsets maps an upper-case substring of an entity name (e.g. "WESTERN DIGITAL") to the
    number of quarters to add to a fiscal label to get the calendar quarter (e.g. -2).
    Check each company's fiscal year-end before using this; leave it empty otherwise.
    """
    out = []
    names = f"{src} {tgt}".upper()
    for key, k in (offsets or {}).items():
        if key.upper() in names:
            out.append(shift_quarters(ts, int(k)))
    return out


def kappa(tau: str, query_ts: Iterable[str], lam: float, aliases: Iterable[str] = ()) -> float:
    """Soft time weight in [0, 1]; 0 when the stored timestamp cannot be parsed."""
    best = None
    for cand in [tau, *aliases]:
        for t in query_ts:
            d = hierarchy_distance(cand, t)
            if d is not None and (best is None or d < best):
                best = d
    if best is None:
        return 0.0
    return math.exp(-lam * best)
