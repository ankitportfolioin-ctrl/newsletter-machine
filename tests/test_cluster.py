"""Phase 4: clustering tests — TF-IDF single-link on crafted docs (no network)."""

from newsletter_machine.pipeline.cluster import cluster_docs, cosine, tfidf_vectors, tokenize
from newsletter_machine.pipeline.normalize import NormalizedDoc


def _doc(key: str, title: str, text: str = "") -> NormalizedDoc:
    platform, external = key.split(":", 1)
    return NormalizedDoc(
        key=key,
        db_id=None,
        platform=platform,
        external_id=external,
        url=f"https://example.com/{external}",
        canonical_url=f"https://example.com/{external}",
        author="",
        title=title,
        text=text or title,
        published_at=None,
        fetched_at=None,
    )


def test_tokenize_drops_stopwords_and_short_tokens() -> None:
    tokens = tokenize("The Best AI Marketing Tools of 2026!")
    assert "the" not in tokens and "of" not in tokens
    assert "marketing" in tokens and "tools" in tokens


def test_cosine_identical_is_one_and_empty_is_zero() -> None:
    docs = [_doc("a:x", "ai marketing tools"), _doc("b:y", "ai marketing tools")]
    vectors = tfidf_vectors(docs)
    assert abs(cosine(vectors[0], vectors[1]) - 1.0) < 1e-9
    assert cosine({}, vectors[0]) == 0.0


def test_topic_pairs_cluster_and_noise_stays_single() -> None:
    docs = [
        _doc(
            "a:1", "AI marketing tools roundup", "ChatGPT workflows and automation demos for teams"
        ),
        _doc(
            "a:2", "AI marketing automation guide", "workflows for ChatGPT marketing teams roundup"
        ),
        _doc("b:1", "Night trains slow travel guide", "sleeper rail routes and station hotels"),
        _doc("b:2", "Slow travel by sleeper train", "rail journeys hotels and night routes"),
        _doc("c:1", "Crypto giveaway event", "double your coins today only"),
        _doc("c:2", "Beach day diary", "sun sand and quiet shoreline waves"),
    ]
    clusters = cluster_docs(docs)
    sizes = sorted((c.size for c in clusters), reverse=True)
    assert sizes == [2, 2, 1, 1]
    groups = {frozenset(c.member_keys) for c in clusters}
    assert frozenset({"a:1", "a:2"}) in groups
    assert frozenset({"b:1", "b:2"}) in groups
    assert all(c.label for c in clusters)


def test_empty_and_single() -> None:
    assert cluster_docs([]) == []
    clusters = cluster_docs([_doc("a:1", "lonely post", "nothing else like it anywhere")])
    assert len(clusters) == 1 and clusters[0].size == 1
