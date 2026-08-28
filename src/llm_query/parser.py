"""Answer parsing for Module 4 (LLM querying).

Model responses are supposed to be a bare letter (per the prompt's "只输出
选项字母" instruction), but in practice some models add explanation,
markdown emphasis, or answer in English. This module extracts a single
A/B/C/D choice from whatever text comes back, never raising -- a response
that can't be confidently parsed just yields None, which the runner logs
as a parse failure instead of crashing the batch.
"""

import re

_LEADING_LETTER = re.compile(r"^\s*\**\(?([A-D])\b\)?\**[.\)、]?", re.IGNORECASE)

_PATTERNS = [
    re.compile(r"(?:答案|answer)\s*(?:是|为|is)?\s*[:：\-]?\s*\**\(?([A-D])\)?\**", re.IGNORECASE),
    re.compile(r"选\s*(?:项)?\s*\**\(?([A-D])\)?\**", re.IGNORECASE),
    re.compile(r"\b([A-D])\b", re.IGNORECASE),
]


def parse_answer(raw_response: str) -> str | None:
    """Extract a single A/B/C/D choice from a model's raw text response.

    Priority order: a leading "A)"/"A."/"A、" marker at the very start of the
    response, then an explicit "答案：X" / "answer is X" marker, then a "选X"
    phrase, then (last resort) any standalone A-D letter token found anywhere.
    For the marker/phrase/fallback patterns the *last* match in the text is
    used, since verbose responses tend to state their conclusion last.
    Returns None if no confident match is found.
    """
    if not raw_response or not raw_response.strip():
        return None
    text = raw_response.strip()

    leading = _LEADING_LETTER.match(text)
    if leading:
        return leading.group(1).upper()

    for pattern in _PATTERNS:
        matches = pattern.findall(text)
        if matches:
            return matches[-1].upper()

    return None
