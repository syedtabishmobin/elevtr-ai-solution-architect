"""Exact-call approval middleware and a durable, simulated payout ledger."""
from __future__ import annotations

import hashlib
import json
import math
import sqlite3
from datetime import datetime, timezone


def canonical(name: str, args: dict) -> str:
    return json.dumps({"tool": name, "args": args}, sort_keys=True,
                      separators=(",", ":"), allow_nan=False)


def binding_of(name: str, args: dict) -> str:
    return hashlib.sha256(canonical(name, args).encode()).hexdigest()


def validate(args: dict) -> None:
    if set(args) != {"claim_id", "account", "amount"}:
        raise ValueError("All and only the three payout arguments are required")
    if not all(isinstance(args[k], str) and args[k].strip() for k in ("claim_id", "account")):
        raise ValueError("Claim and account must be non-empty strings")
    if type(args["amount"]) not in (int, float) or not math.isfinite(args["amount"]) or args["amount"] <= 0:
        raise ValueError("Amount must be a finite positive number")


class Store:
    def __init__(self, path):
        self.db = sqlite3.connect(path)
        self.db.executescript('''
          CREATE TABLE IF NOT EXISTS approvals (
            run TEXT, binding TEXT, actor TEXT, approved_at TEXT, payload TEXT,
            consumed INTEGER DEFAULT 0, PRIMARY KEY(run,binding));
          CREATE TABLE IF NOT EXISTS pending (
            run TEXT PRIMARY KEY, binding TEXT, payload TEXT);
          CREATE TABLE IF NOT EXISTS ledger (
            id INTEGER PRIMARY KEY, run TEXT, tool TEXT, args TEXT,
            operation_key TEXT UNIQUE);
        ''')

    def approve(self, run, name, args, actor):
        validate(args)
        if not actor.strip():
            raise ValueError("Approver identity is required")
        with self.db:
            self.db.execute("INSERT INTO approvals(run,binding,actor,approved_at,payload) VALUES (?,?,?,?,?)",
                            (run, binding_of(name, args), actor,
                             datetime.now(timezone.utc).isoformat(), canonical(name, args)))

    def read(self, run, claim_id):
        with self.db:
            self.db.execute("INSERT INTO ledger(run,tool,args) VALUES (?,?,?)",
                            (run, "read_claim_document", json.dumps({"claim_id": claim_id})))

    def ledger(self, run):
        return [{"tool": tool, **json.loads(args)} for tool, args in self.db.execute(
            "SELECT tool,args FROM ledger WHERE run=? ORDER BY id", (run,))]

    def attempt(self, run, args, tracer):
        """Revalidate and perform the local side effect in the SAME transaction."""
        validate(args)
        payload = canonical("issue_payout", args)
        binding = binding_of("issue_payout", args)
        # The claim's settlement business ID survives process/redeploy changes.
        key = f"settlement:v1:{args['claim_id']}"
        with tracer.start_as_current_span("reliability.approval_gate") as span:
            span.set_attributes({"openinference.span.kind": "CHAIN", "binding": binding,
                                 "tool.name": "issue_payout", "tool.parameters": json.dumps(args),
                                 "input.value": payload, "run.id": run,
                                 "llm.token_count.total": 0})
            try:
                self.db.execute("BEGIN IMMEDIATE")
                approval = self.db.execute(
                    "SELECT actor,approved_at,consumed FROM approvals WHERE run=? AND binding=? AND payload=?",
                    (run, binding, payload)).fetchone()
                previous = self.db.execute("SELECT args FROM ledger WHERE operation_key=?", (key,)).fetchone()
                if previous and previous[0] != json.dumps(args, sort_keys=True):
                    raise ValueError("Settlement already exists with different arguments")
                if not approval or (approval[2] and not previous):
                    self.db.execute("INSERT OR REPLACE INTO pending VALUES (?,?,?)", (run, binding, payload))
                    result = {"status": "blocked", "binding": binding, "arguments": args}
                    span.set_attributes({"decision": "blocked", "allowed": False,
                                         "output.value": json.dumps(result)})
                else:
                    if not previous:
                        self.db.execute("INSERT INTO ledger(run,tool,args,operation_key) VALUES (?,?,?,?)",
                                        (run, "issue_payout", json.dumps(args, sort_keys=True), key))
                        self.db.execute("UPDATE approvals SET consumed=1 WHERE run=? AND binding=?", (run, binding))
                    self.db.execute("DELETE FROM pending WHERE run=?", (run,))
                    result = {"status": "already_paid" if previous else "paid", "binding": binding,
                              "approved_by": approval[0], "arguments": args, "simulated": True}
                    span.set_attributes({"decision": "allowed", "allowed": True,
                                         "approved_by": approval[0], "approved_at": approval[1],
                                         "idempotency.key": key, "output.value": json.dumps(result)})
                self.db.commit()
                return result
            except BaseException:
                self.db.rollback()
                raise

    def approve_pending(self, run, expected_binding, actor):
        row = self.db.execute("SELECT binding,payload FROM pending WHERE run=?", (run,)).fetchone()
        if row is None or row[0] != expected_binding:
            raise ValueError("Pending call changed or does not exist; approval refused")
        call = json.loads(row[1])
        self.approve(run, call["tool"], call["args"], actor)
        return call["args"]
