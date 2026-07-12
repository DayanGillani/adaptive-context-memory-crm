from datetime import datetime, timedelta, timezone

from src.memory_store import MemoryStore
from src.models import InteractionType, MemoryRecord
from src.retriever import ContextRetriever


def make_record(customer_id="cust_1", content="hello", days_ago=0, itype=InteractionType.CHAT_MESSAGE):
    return MemoryRecord(
        customer_id=customer_id,
        interaction_type=itype,
        content=content,
        timestamp=datetime.now(timezone.utc) - timedelta(days=days_ago),
    )


def test_retriever_returns_all_records_within_default_window():
    store = MemoryStore()
    store.add(make_record(days_ago=10))
    store.add(make_record(days_ago=20))

    retriever = ContextRetriever(store)
    candidates = retriever.get_candidates("cust_1")

    assert len(candidates) == 2


def test_retriever_filters_by_recency():
    store = MemoryStore()
    store.add(make_record(content="recent", days_ago=5))
    store.add(make_record(content="old", days_ago=500))

    retriever = ContextRetriever(store)
    candidates = retriever.get_candidates("cust_1", max_age_days=30)

    assert len(candidates) == 1
    assert candidates[0].content == "recent"


def test_retriever_recency_filter_disabled_with_none():
    store = MemoryStore()
    store.add(make_record(content="very old", days_ago=3650))

    retriever = ContextRetriever(store)
    candidates = retriever.get_candidates("cust_1", max_age_days=None)

    assert len(candidates) == 1


def test_retriever_filters_by_interaction_type():
    store = MemoryStore()
    store.add(make_record(content="ticket", itype=InteractionType.SUPPORT_TICKET))
    store.add(make_record(content="chat", itype=InteractionType.CHAT_MESSAGE))

    retriever = ContextRetriever(store)
    candidates = retriever.get_candidates(
        "cust_1", interaction_types=[InteractionType.SUPPORT_TICKET]
    )

    assert len(candidates) == 1
    assert candidates[0].content == "ticket"


def test_retriever_returns_empty_for_customer_with_no_records():
    store = MemoryStore()
    retriever = ContextRetriever(store)

    candidates = retriever.get_candidates("nobody")
    assert candidates == []


def test_retriever_does_not_leak_other_customers_records():
    store = MemoryStore()
    store.add(make_record(customer_id="cust_1", content="mine"))
    store.add(make_record(customer_id="cust_2", content="not mine"))

    retriever = ContextRetriever(store)
    candidates = retriever.get_candidates("cust_1")

    assert len(candidates) == 1
    assert candidates[0].content == "mine"
