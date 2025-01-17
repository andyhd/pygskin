"""Text utilities."""

import re

WORD_START = re.compile(r"(?<!^)(?=[A-Z])")


def to_snakecase(string: str):
    """Convert a string to snake_case."""
    return WORD_START.sub("_", string).lower()


def snakecase_to_capwords(snakecase: str) -> str:
    """Convert a snake_case string to CapWords."""
    return "".join(word.capitalize() for word in snakecase.split("_"))


def speech_duration(
    text: str, words_per_second: float = 3.3, min_duration: float = 1.0
) -> float:
    """Calculate the duration of a speech given the text."""
    return max(len(text.split()) / words_per_second, min_duration)
