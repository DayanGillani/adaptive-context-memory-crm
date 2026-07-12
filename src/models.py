"""
Core data models for the Adaptive Context Memory CRM.

Design decision: MemoryRecord is a plain, immutable-by-convention dataclass
rather than an ORM model. This keeps the memory layer storage-agnostic —
the same record shape works whether the backing store is an in-memory dict
(current implementation), SQLite, or a vector database later on. Swapping
storage backends should never require touching this file.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4


class InteractionType(str, Enum):
    """Categorizes what kind of event a memory record represents.

    Kept as a closed enum (not a free string) so downstream filtering and
    ranking logic can reason about categories reliably instead of guessing
    at string values.
    """

    SUPPORT_TICKET = "support_ticket"
    SALES_CALL = "sales_call"
    EMAIL = "email"
    CHAT_MESSAGE = "chat_message"
    PURCHASE = "purchase"
    NOTE = "note"


@dataclass
class MemoryRecord:
    """A single stored interaction or fact about a customer.

    Attributes:
        customer_id: Identifier of the customer this memory belongs to.
        interaction_type: Category of the interaction (see InteractionType).
        content: The raw text content of the interaction (e.g. ticket body,
            call summary, chat message).
        timestamp: When the interaction occurred. Defaults to now if not
            provided, but callers should pass the real event time when
            backfilling historical data.
        metadata: Free-form key/value data for anything that doesn't need
            first-class treatment (e.g. channel, agent_id, sentiment).
        record_id: Unique identifier, auto-generated if not supplied.
    """

    customer_id: str
    interaction_type: InteractionType
    content: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict = field(default_factory=dict)
    record_id: str = field(default_factory=lambda: str(uuid4()))

    def __post_init__(self) -> None:
        if not self.customer_id:
            raise ValueError("MemoryRecord requires a non-empty customer_id")
        if not self.content or not self.content.strip():
            raise ValueError("MemoryRecord requires non-empty content")


@dataclass
class RankedMemory:
    """A MemoryRecord paired with its relevance score for a given query.

    Kept separate from MemoryRecord itself because relevance is always
    query-dependent — a record has no intrinsic "score" outside the context
    of a specific retrieval request, so bundling the two together at the
    storage layer would be misleading.
    """

    record: MemoryRecord
    score: float
