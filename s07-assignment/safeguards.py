"""Deterministic output safeguards for the document agent."""

from __future__ import annotations

import re


def has_source_citation(response_text: str) -> dict[str, str]:
    """Check that the agent cited sources or explicitly flagged the answer."""

    match = re.search(
        r"^Sources:[ \t]*(.*)$",
        response_text or "",
        flags=re.IGNORECASE | re.MULTILINE,
    )
    if not match:
        return {"value": "fail", "reason": "no Sources: line found"}
    cited = match.group(1).strip()
    if not cited:
        return {"value": "fail", "reason": "Sources: line was empty"}
    return {"value": "pass", "reason": cited}
