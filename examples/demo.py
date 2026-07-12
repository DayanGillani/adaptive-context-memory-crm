"""
End-to-end demo of the Adaptive Context Memory CRM pipeline.

Run with:
    python examples/demo.py

This wires together every module in src/ exactly as described in the
architecture diagram in the README: store -> retrieve -> rank -> compress
-> assemble -> (simulated LLM call) -> validate.

The "LLM call" here is simulated with a canned response rather than a
real API call, since this demo is meant to prove the pipeline logic
works end-to-end without requiring an API key to run. Swapping in a real
LLM call is a matter of replacing `fake_llm_call` with an actual client.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import (
    ContextCompressor,
    ContextRanker,
    ContextRetriever,
    InteractionType,
    MemoryRecord,
    MemoryStore,
    PromptAssembler,
    ResponseValidator,
)
from datetime import datetime, timedelta, timezone


def seed_sample_data(store: MemoryStore, customer_id: str) -> None:
    """Populate the store with a realistic interaction history."""
    now = datetime.now(timezone.utc)
    sample_records = [
        MemoryRecord(
            customer_id=customer_id,
            interaction_type=InteractionType.PURCHASE,
            content="Purchased Pro plan subscription, annual billing.",
            timestamp=now - timedelta(days=90),
        ),
        MemoryRecord(
            customer_id=customer_id,
            interaction_type=InteractionType.SUPPORT_TICKET,
            content="Reported that billing was charged twice in one month. Refund issued.",
            timestamp=now - timedelta(days=45),
        ),
        MemoryRecord(
            customer_id=customer_id,
            interaction_type=InteractionType.CHAT_MESSAGE,
            content="Asked how to export account data to CSV.",
            timestamp=now - timedelta(days=20),
        ),
        MemoryRecord(
            customer_id=customer_id,
            interaction_type=InteractionType.EMAIL,
            content="Requested clarification on annual vs monthly billing cycles.",
            timestamp=now - timedelta(days=5),
        ),
        MemoryRecord(
            customer_id=customer_id,
            interaction_type=InteractionType.NOTE,
            content="Customer prefers async communication over phone calls.",
            timestamp=now - timedelta(days=2),
        ),
    ]
    store.add_many(sample_records)


def fake_llm_call(prompt: str) -> str:
    """Simulates an LLM response for demo purposes (no real API call)."""
    return (
        "Based on your account history, it looks like there was a double "
        "billing issue that was already refunded, and you asked about "
        "billing cycles recently. To clarify: your account is on annual "
        "billing, and the duplicate charge from 45 days ago was resolved."
    )


def run_demo() -> None:
    customer_id = "cust_42"
    query = "Can you explain my billing situation?"

    print("=" * 70)
    print("ADAPTIVE CONTEXT MEMORY CRM — END-TO-END DEMO")
    print("=" * 70)

    # 1. Storage
    store = MemoryStore()
    seed_sample_data(store, customer_id)
    print(f"\n[1] Seeded {store.count_for_customer(customer_id)} memory records for {customer_id}")

    # 2. Retrieval (cheap filtering)
    retriever = ContextRetriever(store)
    candidates = retriever.get_candidates(customer_id, max_age_days=365)
    print(f"[2] Retrieved {len(candidates)} candidate records (within 365-day window)")

    # 3. Ranking (relevance scoring)
    ranker = ContextRanker()
    ranked = ranker.rank(query, candidates, top_k=3)
    print(f"[3] Ranked top {len(ranked)} records by relevance to: \"{query}\"")
    for r in ranked:
        print(f"      score={r.score:.3f}  {r.record.content[:60]}")

    # 4. Compression (bound the context)
    compressor = ContextCompressor(max_chars=500)
    context_block = compressor.compress(ranked)
    print(f"\n[4] Compressed context block ({len(context_block)} chars):")
    print("      " + context_block.replace("\n", "\n      "))

    # 5. Prompt assembly
    assembler = PromptAssembler()
    assembled = assembler.assemble(context_block=context_block, query=query)
    print(f"\n[5] Assembled full prompt ({len(assembled.full_prompt)} chars)")

    # 6. Generation (simulated)
    response = fake_llm_call(assembled.full_prompt)
    print(f"\n[6] Generated response:\n      {response}")

    # 7. Validation
    validator = ResponseValidator()
    validation = validator.validate(response=response, context_block=context_block)
    print(f"\n[7] Validation result: is_valid={validation.is_valid}")
    if validation.warnings:
        for w in validation.warnings:
            print(f"      WARNING: {w}")

    print("\n" + "=" * 70)
    print("Pipeline complete.")
    print("=" * 70)


if __name__ == "__main__":
    run_demo()
