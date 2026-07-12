"""
Storage layer for customer memory records.

Design decision: this implementation stores records in-process (a dict
keyed by customer_id). That is a deliberate scoping choice, not an
oversight — the goal of this module is to get the storage *interface*
right first (add / get_by_customer / delete / all), so that swapping the
backing store for SQLite or Postgres later is a matter of writing a new
class that satisfies the same interface, not a rewrite of everything that
calls it.

Trade-off: in-memory storage means data does not persist across process
restarts, and this will not scale past a single process. That is
acceptable for the current stage of the project (development /
demonstration) and explicitly called out here so it isn't mistaken for a
production-ready claim.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Iterable

from .models import MemoryRecord


class MemoryStore:
    """Stores and retrieves MemoryRecord objects, indexed by customer."""

    def __init__(self) -> None:
        self._records: dict[str, list[MemoryRecord]] = defaultdict(list)

    def add(self, record: MemoryRecord) -> None:
        """Store a new memory record.

        Args:
            record: The MemoryRecord to store.
        """
        self._records[record.customer_id].append(record)

    def add_many(self, records: Iterable[MemoryRecord]) -> None:
        """Store multiple memory records in one call."""
        for record in records:
            self.add(record)

    def get_by_customer(self, customer_id: str) -> list[MemoryRecord]:
        """Return all memory records for a given customer.

        Returns an empty list (not an error) if the customer has no
        records, so callers don't need a try/except for the common
        "new customer" case.
        """
        return list(self._records.get(customer_id, []))

    def delete_by_record_id(self, customer_id: str, record_id: str) -> bool:
        """Delete a single record by id. Returns True if a record was removed.

        Requires customer_id as well as record_id to keep lookups O(records
        for that customer) rather than O(all records ever stored) — this
        matters once the store holds many customers.
        """
        records = self._records.get(customer_id)
        if not records:
            return False
        for i, r in enumerate(records):
            if r.record_id == record_id:
                del records[i]
                return True
        return False

    def count_for_customer(self, customer_id: str) -> int:
        """Return how many memory records exist for a customer."""
        return len(self._records.get(customer_id, []))

    def all_customer_ids(self) -> list[str]:
        """Return the ids of every customer with at least one record."""
        return list(self._records.keys())
