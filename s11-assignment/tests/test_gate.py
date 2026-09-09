import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

import pytest
from opentelemetry.sdk.trace import TracerProvider

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from hitl import Store, binding_of

ARGS = {"claim_id": "C-2087", "account": "AC-10045", "amount": 1840.0}
TRACER = TracerProvider().get_tracer("test")


def test_binding_covers_tool_and_every_argument():
    original = binding_of("issue_payout", ARGS)
    assert original == binding_of("issue_payout", dict(reversed(list(ARGS.items()))))
    assert original != binding_of("other_tool", ARGS)
    for key, value in [("claim_id", "C-9999"), ("account", "AC-99999"), ("amount", 1841.0)]:
        assert original != binding_of("issue_payout", {**ARGS, key: value})


def test_drift_fails_closed_and_exact_human_approval_resumes(tmp_path):
    store = Store(tmp_path / "ledger.db")
    store.approve("C", "issue_payout", ARGS, "fixture")
    drift = {**ARGS, "account": "AC-99999"}
    blocked = store.attempt("C", drift, TRACER)
    assert blocked["status"] == "blocked"
    assert store.ledger("C") == []
    with pytest.raises(ValueError):
        store.approve_pending("C", binding_of("issue_payout", ARGS), "test human")
    store.db.close()
    # A new connection models process restart: pending call and approvals persist.
    restarted = Store(tmp_path / "ledger.db")
    exact = restarted.approve_pending("C", blocked["binding"], "test human")
    assert restarted.attempt("C", exact, TRACER)["status"] == "paid"
    assert len(restarted.ledger("C")) == 1
    assert restarted.attempt("C", exact, TRACER)["status"] == "already_paid"
    assert len(restarted.ledger("C")) == 1
    restarted.db.close()


def test_approval_is_scoped_and_revalidated(tmp_path):
    store = Store(tmp_path / "ledger.db")
    store.approve("A", "issue_payout", ARGS, "fixture")
    assert store.attempt("B", ARGS, TRACER)["status"] == "blocked"
    store.db.execute("DELETE FROM approvals")
    store.db.commit()
    assert store.attempt("A", ARGS, TRACER)["status"] == "blocked"
    assert store.ledger("A") == []
    store.db.close()


@pytest.mark.parametrize("amount", [float("nan"), float("inf"), -1, 0, True, "1840"])
def test_invalid_amount_never_pays(tmp_path, amount):
    store = Store(tmp_path / "ledger.db")
    with pytest.raises(ValueError):
        store.attempt("A", {**ARGS, "amount": amount}, TRACER)
    assert store.ledger("A") == []
    store.db.close()


def test_parallel_retry_pays_once(tmp_path):
    path = tmp_path / "ledger.db"
    store = Store(path)
    store.approve("A", "issue_payout", ARGS, "fixture")
    store.db.close()
    def execute(_):
        connection = Store(path)
        try:
            return connection.attempt("A", ARGS, TRACER)["status"]
        finally:
            connection.db.close()
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(execute, range(2)))
    assert sorted(results) == ["already_paid", "paid"]
    check = Store(path)
    assert len(check.ledger("A")) == 1
    check.db.close()


def test_same_settlement_cannot_be_paid_again_with_new_arguments(tmp_path):
    store = Store(tmp_path / "ledger.db")
    store.approve("A", "issue_payout", ARGS, "fixture")
    store.attempt("A", ARGS, TRACER)
    drift = {**ARGS, "account": "AC-99999"}
    store.approve("A", "issue_payout", drift, "test human")
    with pytest.raises(ValueError, match="already exists"):
        store.attempt("A", drift, TRACER)
    assert len(store.ledger("A")) == 1
    store.db.close()
