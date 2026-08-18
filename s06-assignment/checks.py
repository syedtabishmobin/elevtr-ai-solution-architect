"""Transparent, deterministic checks for retrieval and evidence quality."""

import re


def contains_fact(text: str, fact: str) -> bool:
    """Match a fact as its own token, not inside a larger fused value."""
    return re.search(
        rf"(?<![\w.]){re.escape(fact)}(?!\w|\.\d)",
        text or "",
        flags=re.IGNORECASE,
    ) is not None


def expected_sources(source_file: str) -> set[str]:
    return {item.strip() for item in source_file.split("+") if item.strip()}


def source_recall(retrieved_sources: list[str], source_file: str) -> float:
    wanted = expected_sources(source_file)
    reached = {
        wanted_source
        for wanted_source in wanted
        if any(wanted_source in actual for actual in retrieved_sources)
    }
    return len(reached) / max(1, len(wanted))


def key_fact_check(response: str, key_facts: list[str], trap_facts: list[str]) -> dict:
    if not key_facts and not trap_facts:
        return {"value": "not_applicable", "missing": [], "traps": []}
    missing = [fact for fact in key_facts if not contains_fact(response, fact)]
    traps = [fact for fact in trap_facts if contains_fact(response, fact)]
    return {
        "value": "pass" if not missing and not traps else "fail",
        "missing": missing,
        "traps": traps,
    }


def quotability_check(response: str, contexts: list[str], key_facts: list[str]) -> dict:
    if not key_facts:
        return {"value": "not_applicable", "stated": [], "unquotable": []}
    stated = [fact for fact in key_facts if contains_fact(response, fact)]
    unquotable = [
        fact for fact in stated if not any(contains_fact(context, fact) for context in contexts)
    ]
    return {
        "value": "pass" if stated and not unquotable else "fail",
        "stated": stated,
        "unquotable": unquotable,
    }


def index_check(all_chunks: list[str], key_facts: list[str]) -> dict:
    if not key_facts:
        return {"value": "not_applicable", "absent": []}
    absent = [
        fact for fact in key_facts if not any(contains_fact(chunk, fact) for chunk in all_chunks)
    ]
    return {"value": "pass" if not absent else "fail", "absent": absent}
