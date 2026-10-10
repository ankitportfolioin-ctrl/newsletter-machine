"""Topic clustering: pure-Python TF-IDF + single-link agglomeration.

No sklearn/numpy dependency by design (dozens–hundreds of items/day cluster
in milliseconds with dict vectors). Single-link union-find merges doc pairs
with cosine similarity >= threshold; labels are the top-3 terms by summed
TF-IDF. Summaries/momentum notes belong to the Phase 5 LLM layer — clusters
store labels, terms and member keys only.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field

from newsletter_machine.pipeline.normalize import NormalizedDoc

_TOKEN_RE = re.compile(r"[a-z][a-z0-9-]*")

STOPWORDS = frozenset(
    """
    a an the and or but if then else for with from into over under about
    this that these those its their your our his her our my is are was were
    be been being has have had does did will would can could should shall may
    might must not no yes on in at to of as by it we you they he she them us
    him her who what when where why how which while after before between
    more most very just than also only such each other some any all new
    its via per day today daily top best here there out off own same
    """.split()
)

DEFAULT_THRESHOLD = 0.22


def tokenize(text: str) -> list[str]:
    return [t for t in _TOKEN_RE.findall((text or "").lower()) if t not in STOPWORDS and len(t) > 2]


def tfidf_vectors(docs: list[NormalizedDoc]) -> list[dict[str, float]]:
    tokenized = [tokenize(f"{d.title} {d.title} {d.text}") for d in docs]
    doc_count = len(docs)
    doc_freq: dict[str, int] = {}
    for tokens in tokenized:
        for term in set(tokens):
            doc_freq[term] = doc_freq.get(term, 0) + 1
    vectors: list[dict[str, float]] = []
    for tokens in tokenized:
        total = len(tokens) or 1
        counts: dict[str, int] = {}
        for token in tokens:
            counts[token] = counts.get(token, 0) + 1
        vectors.append(
            {
                term: (count / total) * math.log((doc_count + 1) / (doc_freq[term] + 1)) + 1.0
                for term, count in counts.items()
            }
        )
    return vectors


def cosine(a: dict[str, float], b: dict[str, float]) -> float:
    if not a or not b:
        return 0.0
    if len(a) > len(b):
        a, b = b, a
    dot = sum(weight * b.get(term, 0.0) for term, weight in a.items())
    if dot == 0.0:
        return 0.0
    norm_a = math.sqrt(sum(w * w for w in a.values()))
    norm_b = math.sqrt(sum(w * w for w in b.values()))
    return dot / (norm_a * norm_b) if norm_a and norm_b else 0.0


@dataclass
class TopicCluster:
    label: str
    terms: list[str] = field(default_factory=list)
    member_keys: list[str] = field(default_factory=list)

    @property
    def size(self) -> int:
        return len(self.member_keys)


def cluster_docs(
    docs: list[NormalizedDoc], threshold: float = DEFAULT_THRESHOLD
) -> list[TopicCluster]:
    """Group docs into topics. Deterministic; order-preserving labels. Largest first."""
    if not docs:
        return []
    vectors = tfidf_vectors(docs)
    parent = list(range(len(docs)))

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(i: int, j: int) -> None:
        ri, rj = find(i), find(j)
        if ri != rj:
            parent[max(ri, rj)] = min(ri, rj)

    for i in range(len(docs)):
        for j in range(i + 1, len(docs)):
            if cosine(vectors[i], vectors[j]) >= threshold:
                union(i, j)
    groups: dict[int, list[int]] = {}
    for i in range(len(docs)):
        groups.setdefault(find(i), []).append(i)
    clusters: list[TopicCluster] = []
    for members in groups.values():
        term_weights: dict[str, float] = {}
        for i in members:
            for term, weight in vectors[i].items():
                term_weights[term] = term_weights.get(term, 0.0) + weight
        top_terms = sorted(term_weights, key=lambda t: term_weights[t], reverse=True)[:3]
        label = " ".join(top_terms)[:60] if top_terms else "(untitled)"
        clusters.append(
            TopicCluster(
                label=label,
                terms=top_terms,
                member_keys=[docs[i].key for i in members],
            )
        )
    clusters.sort(key=lambda c: c.size, reverse=True)
    return clusters


def persist_clusters(
    session: object,
    niche_id: str,
    clusters: list[TopicCluster],
    key_to_db_id: dict[str, int],
    run_id: int | None = None,
) -> int:
    """Store clusters (members resolved to DB ids; id-less members skipped)."""
    from newsletter_machine.db.models import Cluster as ClusterRow

    written = 0
    for cluster in clusters:
        ids = [key_to_db_id[k] for k in cluster.member_keys if k in key_to_db_id]
        if not ids:
            continue
        session.add(  # type: ignore[union-attr]
            ClusterRow(
                niche_id=niche_id,
                run_id=run_id,
                label=cluster.label,
                summary="",
                item_ids_json=ids,
            )
        )
        written += 1
    session.flush()  # type: ignore[union-attr]
    return written
