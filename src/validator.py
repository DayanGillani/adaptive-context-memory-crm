"""
Response validation layer.

Design decision: validation here is a set of cheap, deterministic checks
run *after* the LLM generates a response — not a second LLM call. The
goal is to catch a specific, narrow failure mode: the model referencing
something that isn't actually in the context it was given (a basic
grounding check), not to fully fact-check or grade response quality,
which would require a much more involved (and expensive) evaluation
system — out of scope for this module by design.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class ValidationResult:
    """Outcome of validating a response against its source context."""

    is_valid: bool
    warnings: list[str] = field(default_factory=list)


class ResponseValidator:
    """Runs lightweight grounding checks on a generated response."""

    def __init__(self, min_context_overlap_ratio: float = 0.0) -> None:
        """
        Args:
            min_context_overlap_ratio: Currently unused placeholder for a
                future stricter check (minimum fraction of response
                claims that must be traceable to context). Kept at 0.0
                (i.e. disabled) because implementing genuine claim-level
                grounding requires NLI-style entailment checking, which
                is a separate, larger piece of work than this initial
                validator covers. Flagged here rather than silently
                implying full grounding verification exists.
        """
        self._min_context_overlap_ratio = min_context_overlap_ratio

    def validate(self, response: str, context_block: str) -> ValidationResult:
        """Run basic checks on a response before it's returned to the user.

        Checks performed:
            1. Response is non-empty.
            2. If context was empty, the response should not claim to be
               citing specific customer history (a simple heuristic check
               for phrases like "as you mentioned" or "your previous").

        Args:
            response: The LLM's generated response text.
            context_block: The context block that was given to the LLM.

        Returns:
            A ValidationResult with is_valid and any warnings raised.
        """
        warnings: list[str] = []

        if not response or not response.strip():
            return ValidationResult(is_valid=False, warnings=["Response is empty."])

        if not context_block.strip():
            suspicious_phrases = [
                r"\bas you (previously )?mentioned\b",
                r"\byour previous (order|ticket|call|purchase)\b",
                r"\blast time you\b",
            ]
            for pattern in suspicious_phrases:
                if re.search(pattern, response, flags=re.IGNORECASE):
                    warnings.append(
                        "Response appears to reference customer history, "
                        "but no context was retrieved for this query."
                    )
                    break

        is_valid = len(warnings) == 0
        return ValidationResult(is_valid=is_valid, warnings=warnings)
