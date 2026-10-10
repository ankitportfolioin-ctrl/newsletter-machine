"""Phase 2: canonical URL + text normalization (pure functions, no network)."""

from newsletter_machine.pipeline.normalize import canonicalize_url, normalize_text


def test_strips_tracking_params() -> None:
    assert (
        canonicalize_url("https://example.com/blog/post-1?utm_source=newsletter&fbclid=xyz")
        == "https://example.com/blog/post-1"
    )


def test_strips_fragment_and_trailing_slash() -> None:
    assert canonicalize_url("https://example.com/a/b/#section") == "https://example.com/a/b"


def test_sorts_query_and_lowercases_host() -> None:
    assert canonicalize_url("https://EXAMPLE.com/p?b=2&a=1") == "https://example.com/p?a=1&b=2"


def test_keeps_meaningful_params() -> None:
    assert (
        canonicalize_url("https://www.youtube.com/watch?v=abc123&si=tracking")
        == "https://www.youtube.com/watch?v=abc123"
    )


def test_empty_and_bare_host() -> None:
    assert canonicalize_url("") == ""
    assert canonicalize_url("example.com") == "https://example.com"


def test_normalize_text_collapses_whitespace() -> None:
    assert normalize_text("  a\n\n  b\t c  ") == "a b c"
    assert normalize_text("", max_chars=5) == ""
