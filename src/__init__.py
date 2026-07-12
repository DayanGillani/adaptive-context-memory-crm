"""
Adaptive Context Memory CRM — core package.

Public API surface. Import from here rather than reaching into individual
modules directly, so internal reorganization doesn't break callers.
"""

from .compressor import ContextCompressor
from .memory_store import MemoryStore
from .models import InteractionType, MemoryRecord, RankedMemory
from .prompt_assembler import AssembledPrompt, PromptAssembler
from .ranker import ContextRanker
from .retriever import ContextRetriever
from .validator import ResponseValidator, ValidationResult

__all__ = [
    "MemoryStore",
    "MemoryRecord",
    "InteractionType",
    "RankedMemory",
    "ContextRetriever",
    "ContextRanker",
    "ContextCompressor",
    "PromptAssembler",
    "AssembledPrompt",
    "ResponseValidator",
    "ValidationResult",
]
