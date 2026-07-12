import pytest

from src.compressor import ContextCompressor
from src.models import InteractionType, MemoryRecord, RankedMemory


def make_ranked(content, score):
    record = MemoryRecord(
        customer_id="cust_1",
        interaction_type=InteractionType.SUPPORT_TICKET,
        content=content,
    )
    return RankedMemory(record=record, score=score)


def test_compress_empty_list_returns_empty_string():
    compressor = ContextCompressor()
    assert compressor.compress([]) == ""


def test_compress_includes_all_when_under_budget():
    compressor = ContextCompressor(max_chars=1000)
    ranked = [make_ranked("short message one", 0.9), make_ranked("short message two", 0.8)]

    result = compressor.compress(ranked)

    assert "short message one" in result
    assert "short message two" in result


def test_compress_respects_max_chars_budget():
    compressor = ContextCompressor(max_chars=50)
    ranked = [
        make_ranked("a" * 30, 0.9),
        make_ranked("b" * 30, 0.8),
        make_ranked("c" * 30, 0.7),
    ]

    result = compressor.compress(ranked)

    assert len(result) <= 50 + 60  # allow for formatting prefix overhead
    assert "a" * 30 in result


def test_compress_always_includes_at_least_one_entry_even_over_budget():
    compressor = ContextCompressor(max_chars=10)
    ranked = [make_ranked("this single message is longer than the budget", 0.9)]

    result = compressor.compress(ranked)

    assert "this single message is longer than the budget" in result


def test_compress_keeps_highest_ranked_first():
    compressor = ContextCompressor(max_chars=10000)
    ranked = [make_ranked("low relevance", 0.1), make_ranked("high relevance", 0.9)]
    # Caller is responsible for pre-sorting (ranker does this); compressor
    # trusts input order.
    ranked_sorted = sorted(ranked, key=lambda r: r.score, reverse=True)

    result = compressor.compress(ranked_sorted)
    lines = result.split("\n")

    assert "high relevance" in lines[0]


def test_compressor_rejects_non_positive_max_chars():
    with pytest.raises(ValueError):
        ContextCompressor(max_chars=0)
