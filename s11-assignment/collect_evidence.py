"""Verify completed runs and copy only non-secret evidence into the repo."""
import json
import shutil
from pathlib import Path

BASE = Path(__file__).resolve().parent
SOURCE = BASE / "runtime/submission"
TARGET = BASE / "evidence"
TARGET.mkdir(exist_ok=True)
logs = []
metrics = []
for label in "ABC":
    result = json.loads((SOURCE / f"run-{label}.json").read_text())
    spans = [json.loads(line) for line in (SOURCE / f"run-{label}-spans.jsonl").read_text().splitlines()]
    payout = [row for row in result["ledger"] if row["tool"] == "issue_payout"]
    assert len(payout) == (0 if label == "B" else 1)
    assert {span["trace_id"] for span in spans} == {result["trace_id"]}
    roots = [s for s in spans if s["parent_id"] is None]
    assert len(roots) == 1
    ids = {s["span_id"] for s in spans}
    assert all(s["parent_id"] in ids for s in spans if s["parent_id"] is not None)
    models = [s for s in spans if s["name"] == "model.chat"]
    gates = [s for s in spans if s["name"] == "reliability.approval_gate"]
    assert len(models) == 3
    assert [g["attributes"]["decision"] for g in gates] == (["blocked", "allowed"] if label == "C" else ["blocked" if label == "B" else "allowed"])
    if label == "C":
        assert gates[-1]["attributes"]["approved_by"] == "Syed Tabish Mobin"
    for suffix in (".json", "-spans.jsonl"):
        shutil.copyfile(SOURCE / f"run-{label}{suffix}", TARGET / f"run-{label}{suffix}")
    logs.append((SOURCE / f"run-{label}-terminal.txt").read_text())
    metrics.append({"run": label, "trace_id": result["trace_id"], "spans": len(spans),
        "model_calls": len(models), "payouts": len(payout),
        "tokens": sum(s["attributes"]["llm.token_count.total"] for s in models),
        "estimated_usd": sum(s["attributes"]["llm.cost.total"] for s in models),
        "duration_ms": roots[0]["duration_ms"]})
(TARGET / "runs-ABC.txt").write_text("\n\n".join(logs))
(TARGET / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")
print(json.dumps(metrics, indent=2))
print("All three live-run contracts verified.")
