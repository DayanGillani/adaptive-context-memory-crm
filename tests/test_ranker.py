from src.models import InteractionType, MemoryRecord
from src.ranker import ContextRanker


def make_record(content):
    return MemoryRecord(
        customer_id="cust_1",
        interaction_type=InteractionType.CHAT_MESSAGE,
        content=content,
    )


def test_ranker_returns_empty_list_for_no_candidates():
    ranker = ContextRanker()
    results = ranker.rank("refund request", [])
    assert results == []


def test_ranker_scores_relevant_content_higher():
    ranker = ContextRanker()
    candidates = [
        make_record("Customer requested a refund for their order"),
        make_record("Customer asked about shipping times to Canada"),
    ]

    results = ranker.rank("I want a refund", candidates)

    assert len(results) == 2
    assert results[0].record.content.startswith("Customer requested a refund")
    assert results[0].score >= results[1].score


def test_ranker_respects_top_k():
    ranker = ContextRanker()
    candidates = [make_record(f"message about topic {i}") for i in range(10)]

    results = ranker.rank("topic 5", candidates, top_k=3)

    assert len(results) == 3


def test_ranker_handles_all_stopword_query_without_crashing():
    ranker = ContextRanker()
    candidates = [make_record("the of and a")]

    # Should not raise, even though vocabulary is empty after stopword removal.
    results = ranker.rank("the and", candidates)
    assert len(results) == 1


def test_ranker_output_is_sorted_descending():
    ranker = ContextRanker()
    candidates = [
        make_record("totally unrelated content about gardening"),
        make_record("billing invoice payment refund charge"),
        make_record("refund payment billing invoice charge dispute"),
    ]

    results = ranker.rank("billing refund dispute", candidates)

    scores = [r.score for r in results]
    assert scores == sorted(scores, reverse=True)
