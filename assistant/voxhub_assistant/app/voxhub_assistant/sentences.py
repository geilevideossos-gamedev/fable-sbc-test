"""Incremental sentence splitting so TTS can start before Claude has finished."""

from __future__ import annotations

import re

# A sentence ends at . ! ? … (plus closing quotes/brackets) followed by whitespace, or at a newline.
# Requiring whitespace keeps "21.5 degrees" and "3.30pm" intact.
_BOUNDARY = re.compile(r"([.!?…]+[\"')\]]*)\s+|\n+")
_MARKDOWN = re.compile(r"[*_`#>|~]+|^\s*[-•]\s+", re.MULTILINE)
_LINK = re.compile(r"\[([^\]]+)\]\([^)]+\)")
_SPACES = re.compile(r"\s+")


def clean_for_speech(text: str) -> str:
    """Strip markdown and other symbols a TTS engine would read aloud or stumble on."""
    text = _LINK.sub(r"\1", text)
    text = _MARKDOWN.sub(" ", text)
    return _SPACES.sub(" ", text).strip()


class SentenceSplitter:
    """Feed text deltas, get back complete sentences.

    Fragments shorter than ``min_chars`` are merged with the following sentence, so
    "Sure. " or "1. " do not become tiny, choppy TTS requests.
    """

    def __init__(self, min_chars: int = 12) -> None:
        self.min_chars = min_chars
        self._buffer = ""

    def feed(self, delta: str) -> list[str]:
        self._buffer += delta
        sentences: list[str] = []
        start = 0
        for match in _BOUNDARY.finditer(self._buffer):
            candidate = clean_for_speech(self._buffer[start : match.end()])
            if len(candidate) >= self.min_chars:
                sentences.append(candidate)
                start = match.end()
        self._buffer = self._buffer[start:]
        return sentences

    def flush(self) -> list[str]:
        rest = clean_for_speech(self._buffer)
        self._buffer = ""
        return [rest] if rest else []
