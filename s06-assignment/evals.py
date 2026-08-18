"""Run and persist one named evaluation experiment."""

import asyncio
import sys

from dotenv import load_dotenv
from openai import AsyncOpenAI
from ragas import Dataset, experiment
from ragas.backends import LocalCSVBackend
from ragas.llms import llm_factory

from checks import index_check, key_fact_check, quotability_check, source_recall
from metrics import correctness
from rag import all_indexed_chunks, answer


load_dotenv()

judge = llm_factory(
    "gpt-5-mini",
    client=AsyncOpenAI(),
    temperature=1,
    top_p=1,
    max_tokens=4096,
)
TOP_K = int(sys.argv[2]) if len(sys.argv) > 2 else 4
ALL_CHUNKS = all_indexed_chunks()


@experiment()
async def run_case(row):
    result = await asyncio.to_thread(answer, row["question"], TOP_K)
    response = result["response"]
    contexts = result["contexts"]
    sources = result["sources"]
    facts = key_fact_check(response, row.get("key_facts", []), row.get("trap_facts", []))
    quotable = quotability_check(response, contexts, row.get("key_facts", []))
    indexed = index_check(ALL_CHUNKS, row.get("key_facts", []))
    judged = await correctness.ascore(
        llm=judge,
        response=response,
        grading_notes=row["grading_notes"],
    )
    return {
        "qid": row["qid"],
        "category": row["category"],
        "question": row["question"],
        "response": response,
        "correctness": judged.value,
        "source_recall": source_recall(sources, row["source_file"]),
        "key_facts": facts["value"],
        "quotable": quotable["value"],
        "index_ready": indexed["value"],
        "missing_facts": ", ".join(facts["missing"]),
        "trap_facts_found": ", ".join(facts["traps"]),
        "unquotable_facts": ", ".join(quotable["unquotable"]),
        "facts_absent_from_index": ", ".join(indexed["absent"]),
        "retrieved_sources": ", ".join(sorted(set(sources))),
        "judge_reason": judged.reason,
    }


async def main():
    name = sys.argv[1] if len(sys.argv) > 1 else "baseline"
    dataset = Dataset.load("rag_eval", "local/jsonl", root_dir=".")
    result = await run_case.arun(
        dataset,
        name=name,
        backend=LocalCSVBackend(root_dir="."),
    )
    if len(result) != len(dataset):
        raise RuntimeError(
            f"Expected {len(dataset)} rows but received {len(result)}. "
            "A failed task may have been dropped."
        )
    print(f"Wrote experiments/{name}.csv with {len(result)} rows")


if __name__ == "__main__":
    asyncio.run(main())

