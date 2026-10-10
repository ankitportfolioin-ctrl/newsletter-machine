"""Dedupe: exact canonical-URL match + SimHash near-duplicate detection.

SimHash is vendored (~40 lines, hashlib-based, deterministic) so the pipeline
has zero new dependencies: shingle the text into word 3-grams, hash each with
blake2b-64, add/subtract per-bit weights, threshold the 64-bit fingerprint.
Hamming distance <= threshold (default 5, calibrated in tests) counts as a
near-duplicate. First occurrence in batch order wins; removals are reported
with reasons for transparency (stored on the Run diagnostics in Phase 5+).
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field

from newsletter_machine.pipeline.normalize import NormalizedDoc

_WORD_RE = re.compile(r"[a-z0-9]+")
SHINGLE_N = 3


def _shingles(text: str) -> list[str]:
    words = _WORD_RE.findall(text.lower())
    if len(words) < SHINGLE_N:
        return [" ".join(words)] if words else []
    return [" ".join(words[i : i + SHINGLE_N]) for i in range(len(words) - SHINGLE_N + 1)]


def simhash64(text: str) -> int:
    """64-bit SimHash fingerprint. Deterministic across runs (blake2b, not hash())."""
    vector = [0] * 64
    for shingle in _shingles(text or ""):
        digest = hashlib.blake2b(shingle.encode("utf-8"), digest_size=8).digest()
        value = int.from_bytes(digest, "big")
        for bit in range(64):
            vector[bit] += 1 if (value >> bit) & 1 else -1
    fingerprint = 0
    for bit in range(64):
        if vector[bit] > 0:
            fingerprint |= 1 << bit
    return fingerprint


def hamming(a: int, b: int) -> int:
    return bin(a ^ b).count("1")


def doc_fingerprint(doc: NormalizedDoc) -> int:
    # Title triple-weighted: same headline is a strong dupe signal, while
    # distinct headlines keep same-topic articles apart. Calibrated 2026-10-10
    # on tests/fixtures/pipeline_items.json: true repost twin = 6,
    # closest non-dupe pair = 21, so the default threshold 8 has margin both ways.
    return simhash64(f"{doc.title}\n{doc.title}\n{doc.title}\n{doc.text}")


@dataclass
class DedupeResult:
    unique: list[NormalizedDoc] = field(default_factory=list)
    removed: list[tuple[NormalizedDoc, NormalizedDoc, str]] = field(default_factory=list)
    # (removed_doc, kept_doc, reason)


def dedupe_docs(docs: list[NormalizedDoc], hamming_threshold: int = 8) -> DedupeResult:
    """Two passes, order-preserving. Never raises on empty/odd input."""
    result = DedupeResult()
    seen_canonical: dict[str, NormalizedDoc] = {}
    kept: list[tuple[NormalizedDoc, int]] = []  # (doc, fingerprint)
    for doc in docs:
        if doc.canonical_url:
            keeper = seen_canonical.get(doc.canonical_url)
            if keeper is not None:
                result.removed.append((doc, keeper, "canonical-url"))
                continue
            seen_canonical[doc.canonical_url] = doc
        fingerprint = doc_fingerprint(doc)
        match: NormalizedDoc | None = None
        for kept_doc, kept_fp in kept:
            if hamming(fingerprint, kept_fp) <= hamming_threshold:
                match = kept_doc
                break
        if match is not None:
            result.removed.append((doc, match, f"simhash<={hamming_threshold}"))
            continue
        kept.append((doc, fingerprint))
        result.unique.append(doc)
    return result
