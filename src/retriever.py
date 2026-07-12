"""
Context retrieval layer.

Design decision: retrieval is deliberately split from ranking (see
ranker.py). Retrieval answers "which memories are even eligible
candidates for this query" (cheap filters: customer match, recency
window, interaction type). Ranking then answers "of those candidates,
which are most relevant" (more expensive: semantic similarity scoring).

Keeping these as separate stages means the expensive ranking step never
runs over records that were never going to be relevant anyway (e.g. a
different customer, or something from three years ago when only a
30-day window matters) — this is a basic but real performance and cost
control as the memory store grows.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from .memory_store import MemoryStore
from .models import InteractionType, MemoryRecord


class ContextRetriever:
    """Filters candidate memory records before they are ranked."""

    def __init__(self, store: MemoryStore) -> None:
        self._store = store

    def get_candidates(
        self,
        customer_id: str,
        max_age_days: int | None = 365,
        interaction_types: list[InteractionType] | None = None,
    ) -> list[MemoryRecord]:
        """Return candidate memory records for a customer, pre-filtered.

        Args:
            customer_id: Which customer's memories to retrieve.
            max_age_days: Exclude records older than this many days.
                Pass None to disable the recency filter entirely.
            interaction_types: If provided, only include records whose
                interaction_type is in this list. Pass None to include
                all types.

        Returns:
            A list of MemoryRecord objects matching the filters, in no
            particular order (ordering/ranking happens in ContextRanker).
        """
        records = self._store.get_by_customer(customer_id)

        if max_age_days is not None:
            cutoff = datetime.now(timezone.utc) - timedelta(days=max_age_days)
            records = [r for r in records if r.timestamp >= cutoff]

        if interaction_types is not None:
            allowed = set(interaction_types)
            records = [r for r in records if r.interaction_type in allowed]

        return records
