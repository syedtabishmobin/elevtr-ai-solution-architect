"""Print per-question metric changes between two saved experiments."""

import csv
import sys


def load(name):
    with open(f"experiments/{name}.csv", encoding="utf-8") as file:
        return {row["qid"]: row for row in csv.DictReader(file)}


if len(sys.argv) != 3:
    raise SystemExit("usage: uv run python compare.py BASELINE CHANGED")

before_name, after_name = sys.argv[1], sys.argv[2]
before = load(before_name)
after = load(after_name)
columns = ["correctness", "source_recall", "key_facts", "quotable", "index_ready"]

print(f"{before_name} -> {after_name}\n")
for qid in sorted(before.keys() | after.keys()):
    if qid not in before or qid not in after:
        print(f"{qid}: missing from one experiment")
        continue
    changes = [
        f"{column}: {before[qid][column]} -> {after[qid][column]}"
        for column in columns
        if before[qid][column] != after[qid][column]
    ]
    if changes:
        print(f"{qid}: " + "; ".join(changes))

