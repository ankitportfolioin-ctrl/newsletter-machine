"""Phase 4: dedupe tests — canonical exact-match + SimHash calibration (no network)."""

from newsletter_machine.pipeline.dedupe import dedupe_docs, doc_fingerprint, hamming, simhash64
from newsletter_machine.pipeline.normalize import NormalizedDoc, canonicalize_url


def _doc(key: str, title: str, text: str, url: str = "") -> NormalizedDoc:
    platform, external = key.split(":", 1)
    raw = url or f"https://example.com/{external}"
    return NormalizedDoc(
        key=key,
        db_id=None,
        platform=platform,
        external_id=external,
        url=raw,
        canonical_url=canonicalize_url(raw),
        author="",
        title=title,
        text=text,
        published_at=None,
        fetched_at=None,
    )


def test_simhash_deterministic_and_separates_topics() -> None:
    text = "the quick brown fox jumps over the lazy dog near the river bank"
    assert simhash64(text) == simhash64(text)
    other = "quantum chromodynamics lattice gauge theory perturbative expansion"
    assert hamming(simhash64(text), simhash64(other)) > 5


def test_identical_and_near_identical_are_dupes() -> None:
    original = _doc("blogs:a", "AI tools roundup", "word " * 40 + "alpha")
    twin = _doc("blogs:b", "AI tools roundup", "word " * 40 + "beta")
    res = dedupe_docs([original, twin])
    assert [d.key for d in res.unique] == ["blogs:a"]  # first wins
    assert len(res.removed) == 1
    assert res.removed[0][2].startswith("simhash")


def test_same_topic_distinct_text_survives() -> None:
    a = _doc(
        "blogs:a",
        "Best AI marketing tools in 2026",
        "A roundup of the best AI marketing tools for modern teams, with ChatGPT workflows.",
    )
    b = _doc(
        "reddit:b",
        "AI marketing tools megathread — what actually works?",
        "Share the tools that moved numbers for you. Budgets, benchmarks and honest takes only.",
    )
    res = dedupe_docs([a, b])
    assert len(res.unique) == 2
    assert res.removed == []
    assert hamming(doc_fingerprint(a), doc_fingerprint(b)) > 5


def test_canonical_url_match_is_exact_dupe() -> None:
    a = _doc(
        "blogs:a",
        "Totally different title here",
        "unrelated body words",
        url="https://example.com/same",
    )
    b = _doc(
        "reddit:b", "Another title entirely", "another body", url="https://example.com/same?utm_x=1"
    )
    res = dedupe_docs([a, b])
    assert [d.key for d in res.unique] == ["blogs:a"]
    assert res.removed[0][2] == "canonical-url"


def test_empty_input() -> None:
    res = dedupe_docs([])
    assert res.unique == [] and res.removed == []
