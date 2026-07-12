"""
Prompt assembly layer.

Design decision: system instructions, retrieved context, and the current
query are kept as three explicitly separate inputs to `assemble`, rather
than letting callers pass in one pre-formatted string. This is the
practical expression of the "context engineering strategy" described in
the project README: keeping these concerns separate means the system
instructions can be versioned and improved independently of whatever
context happens to be retrieved for a given call, and the final prompt
stays auditable — every section is traceable to its source.
"""

from __future__ import annotations

from dataclasses import dataclass

DEFAULT_SYSTEM_INSTRUCTIONS = (
    "You are a customer support assistant. Use the customer history "
    "provided below to inform your response. If the history does not "
    "contain relevant information, say so rather than guessing."
)


@dataclass
class AssembledPrompt:
    """The final prompt, plus its components, for auditability.

    Keeping the components alongside the final text (rather than just
    returning a single string) means the response validator downstream
    can check the model's output against `context_block` specifically,
    without needing to re-parse the full prompt.
    """

    system_instructions: str
    context_block: str
    query: str
    full_prompt: str


class PromptAssembler:
    """Combines system instructions, compressed context, and a query."""

    def __init__(self, system_instructions: str = DEFAULT_SYSTEM_INSTRUCTIONS) -> None:
        self._system_instructions = system_instructions

    def assemble(self, context_block: str, query: str) -> AssembledPrompt:
        """Build the final prompt from its component parts.

        Args:
            context_block: Compressed context string from ContextCompressor.
            query: The current user query.

        Returns:
            An AssembledPrompt containing both the full prompt text and
            its individual components.
        """
        if context_block:
            context_section = f"Customer history:\n{context_block}"
        else:
            context_section = "Customer history: (no relevant history found)"

        full_prompt = (
            f"{self._system_instructions}\n\n"
            f"{context_section}\n\n"
            f"Current query: {query}"
        )

        return AssembledPrompt(
            system_instructions=self._system_instructions,
            context_block=context_block,
            query=query,
            full_prompt=full_prompt,
        )
