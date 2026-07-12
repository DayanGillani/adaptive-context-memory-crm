"""
Context compression layer.

Design decision: compression here means "select and bound", not
"summarize with an LLM". Concretely: take the top-ranked memories, format
them into short lines, and stop once a character budget is reached. This
is a deliberately simple, fast, and free operation.

The alternative — running an LLM call to abstractively summarize context
before running a *second* LLM call to generate the actual response — adds
latency, cost, and a second point of possible information loss for every
single interaction. That trade-off may be worth it for very long
histories, but it should be an explicit upgrade path, not the default.
This module is written so that swapping in an LLM-based summarizer later
is a matter of implementing the same `compress` interface.
"""

from __future__ import annotations

from .models import RankedMemory


class ContextCompressor:
    """Condenses ranked memories into a single, bounded context block."""

    def __init__(self, max_chars: int = 2000) -> None:
        """
        Args:
            max_chars: Maximum total character length of the compressed
                context block. Chosen as a character budget rather than a
                token budget to keep this module dependency-free (no
                tokenizer required); callers integrating with a specific
                LLM should convert their token budget to an approximate
                character budget (roughly tokens * 4 for English text).
        """
        if max_chars <= 0:
            raise ValueError("max_chars must be positive")
        self._max_chars = max_chars

    def compress(self, ranked_memories: list[RankedMemory]) -> str:
        """Build a bounded context string from ranked memories.

        Records are included highest-score-first until adding the next
        one would exceed max_chars. This guarantees the output never
        exceeds budget, and that the most relevant memories are always
        the ones kept when something has to be dropped.

        Args:
            ranked_memories: Output of ContextRanker.rank, already sorted
                by descending score.

        Returns:
            A newline-separated string of formatted memory entries, or an
            empty string if no memories were provided.
        """
        if not ranked_memories:
            return ""

        lines: list[str] = []
        current_length = 0

        for ranked in ranked_memories:
            record = ranked.record
            date_str = record.timestamp.strftime("%Y-%m-%d")
            line = f"[{date_str} | {record.interaction_type.value}] {record.content}"

            # +1 accounts for the newline that will join this line to the rest.
            projected_length = current_length + len(line) + 1
            if projected_length > self._max_chars and lines:
                # Stop once budget is exceeded, but only after at least one
                # entry has been included — otherwise a single very long
                # top-ranked memory would silently produce empty context.
                break

            lines.append(line)
            current_length = projected_length

        return "\n".join(lines)
