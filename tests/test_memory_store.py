from datetime import datetime, timedelta, timezone

import pytest

from src.memory_store import MemoryStore
from src.models import InteractionType, MemoryRecord


def make_record(customer_id="cust_1", content="hello", days_ago=0):
    return MemoryRecord(
        customer_id=customer_id,
        interaction_type=InteractionType.CHAT_MESSAGE,
        content=content,
        timestamp=datetime.now(timezone.utc) - timedelta(days=days_ago),
    )


def test_add_and_get_by_customer():
    store = MemoryStore()
    record = make_record()
    store.add(record)

    results = store.get_by_customer("cust_1")
    assert len(results) == 1
    assert results[0].record_id == record.record_id


def test_get_by_customer_returns_empty_list_for_unknown_customer():
    store = MemoryStore()
    results = store.get_by_customer("does_not_exist")
    assert results == []


def test_records_are_isolated_per_customer():
    store = MemoryStore()
    store.add(make_record(customer_id="cust_1"))
    store.add(make_record(customer_id="cust_2"))

    assert store.count_for_customer("cust_1") == 1
    assert store.count_for_customer("cust_2") == 1


def test_add_many():
    store = MemoryStore()
    records = [make_record(content=f"msg {i}") for i in range(5)]
    store.add_many(records)

    assert store.count_for_customer("cust_1") == 5


def test_delete_by_record_id():
    store = MemoryStore()
    record = make_record()
    store.add(record)

    deleted = store.delete_by_record_id("cust_1", record.record_id)
    assert deleted is True
    assert store.count_for_customer("cust_1") == 0


def test_delete_nonexistent_record_returns_false():
    store = MemoryStore()
    store.add(make_record())

    deleted = store.delete_by_record_id("cust_1", "nonexistent-id")
    assert deleted is False


def test_all_customer_ids():
    store = MemoryStore()
    store.add(make_record(customer_id="cust_1"))
    store.add(make_record(customer_id="cust_2"))

    ids = store.all_customer_ids()
    assert set(ids) == {"cust_1", "cust_2"}


def test_memory_record_rejects_empty_customer_id():
    with pytest.raises(ValueError):
        MemoryRecord(
            customer_id="",
            interaction_type=InteractionType.NOTE,
            content="something",
        )


def test_memory_record_rejects_empty_content():
    with pytest.raises(ValueError):
        MemoryRecord(
            customer_id="cust_1",
            interaction_type=InteractionType.NOTE,
            content="   ",
        )
