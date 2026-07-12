from src.prompt_assembler import PromptAssembler
from src.validator import ResponseValidator


def test_prompt_assembler_includes_context_and_query():
    assembler = PromptAssembler()
    result = assembler.assemble(
        context_block="[2026-01-01 | note] Customer prefers email contact.",
        query="How should I reach this customer?",
    )

    assert "Customer prefers email contact" in result.full_prompt
    assert "How should I reach this customer?" in result.full_prompt


def test_prompt_assembler_handles_empty_context():
    assembler = PromptAssembler()
    result = assembler.assemble(context_block="", query="What's my order status?")

    assert "no relevant history found" in result.full_prompt.lower()


def test_prompt_assembler_uses_custom_system_instructions():
    custom = "You are a sales assistant."
    assembler = PromptAssembler(system_instructions=custom)
    result = assembler.assemble(context_block="", query="test")

    assert result.system_instructions == custom
    assert custom in result.full_prompt


def test_validator_flags_empty_response():
    validator = ResponseValidator()
    result = validator.validate(response="", context_block="some context")

    assert result.is_valid is False
    assert len(result.warnings) == 1


def test_validator_passes_grounded_response():
    validator = ResponseValidator()
    result = validator.validate(
        response="Based on your order, it should arrive Tuesday.",
        context_block="[note] Order placed, estimated delivery Tuesday.",
    )

    assert result.is_valid is True
    assert result.warnings == []


def test_validator_flags_ungrounded_history_reference():
    validator = ResponseValidator()
    result = validator.validate(
        response="As you previously mentioned, your refund was processed.",
        context_block="",
    )

    assert result.is_valid is False
    assert any("history" in w.lower() for w in result.warnings)


def test_validator_allows_generic_response_with_no_context():
    validator = ResponseValidator()
    result = validator.validate(
        response="I don't have any history on file for this account yet.",
        context_block="",
    )

    assert result.is_valid is True
