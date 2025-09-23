from src.utils import format_summary_prompt


def test_format_summary_prompt_short():
    transcript = "Hello world"
    prompt = format_summary_prompt(transcript, length="short")
    assert "short" in prompt
    assert "Hello world" in prompt


def test_format_summary_prompt_invalid():
    try:
        format_summary_prompt("x", length="tiny")
        assert False, "Expected ValueError for invalid length"
    except ValueError:
        assert True
