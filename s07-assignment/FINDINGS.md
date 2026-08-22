# Class 7 Assignment #4 - Findings

## 1. Corpus

I indexed five documents in one OpenAI vector store: the Apple, Microsoft, and
Tesla company-report PDFs, the equity research review policy, and the portfolio
research assistant FAQ. I reused the same corpus from S06 instead of building
another chunker or retriever.

I wrote eight questions and checked every expected behavior against the source
documents before running the agent. The mix contains four direct lookups
(`q01`, `q02`, `q03`, and `q08`), two questions that require both process
documents (`q04` and `q05`), one missing-information case (`q06`), and one
financial-table distractor (`q07`). The distractor targets the June 27, 2026
Apple values while the adjacent June 28, 2025 column contains three plausible
but wrong values.

## 2. Baseline

`q01` was the cleanest baseline pass. The agent searched the hosted file store,
returned the correct threshold, cited the real policy file, and passed the
deterministic guardrail:

```text
An internal risk score of 70 out of 100 triggers an additional risk review for a holding.

Sources: equity_research_policy.md
```

All eight questions completed. Seven responses passed the `Sources:` check.
`q07` was the one guardrail failure, which was useful because the answer sounded
confident and contained the right numbers but still lacked source evidence in
the required output format.

## 3. Refusal

The final `q06` run behaved correctly. It searched for a support address, found
no relevant evidence, called `flag_for_human`, and did not reuse any unrelated
email address from the company reports. The saved refusal trace ends with:

```text
I couldn't find the support email address for the portfolio research assistant in the documents searched. I have flagged this for human review for further assistance.

Sources: none (flagged for human review)
```

The baseline row recorded `flagged=True` and `guardrail=pass`. I also checked
the message trace rather than trusting the wording alone: it contains both the
`flag_for_human` function call and its result.

## 4. Distractor

`q07` selected the correct June 27, 2026 values: product net sales of `$78,678`
million, services net sales of `$30,739` million, and total net sales of
`$109,417` million. It did not copy the nearby 2025 values of `$66,613`,
`$27,423`, and `$94,036` million.

The answer still failed overall because it ended without a `Sources:` line. It
therefore cited neither the right file nor a wrong file. The output guardrail
returned `fail`, which is exactly the kind of quiet grounding problem the
assignment was designed to expose.

## 5. The break and the safeguards

I passed `vs_does_not_exist` instead of deleting the valid store. Every question
received an OpenAI 404 wrapped as `ChatClientException`. All eight CSV rows were
still written with `flagged=error` and `guardrail=error`, so one broken hosted
tool did not end the experiment after `q01`. No answer was generated and there
was no silent hallucination.

Neither the action limit nor the citation guardrail caught this particular
failure. The request failed before the agent received a response to inspect or
entered a useful tool loop. The per-question `try/except` boundary in the
evaluation harness caught it.

I tested the safeguards separately so their behavior was not only assumed from
configuration. An intentionally looping local tool caused both
`max_iterations` and `max_function_calls` to disable tools after one execution
and return:

```text
Function invocation limit reached before a final answer could be produced.
```

The deterministic guardrail also returned `fail` for both an uncited answer and
an empty `Sources:` line. These observed checks are saved in
`experiments/safeguards.txt`.

## 6. Pattern

The clean `q01` trace behaved mainly like Tool Use: search once, observe the
result, and answer. The `q06` refusal also searched once and then selected the
local escalation tool. There is an ACT / OBSERVE / DECIDE loop, but the saved
traces do not show a longer ReAct cycle that repeatedly searches, reconsiders,
and searches again.

I would add a second agent only when a genuinely separate responsibility is
needed, such as independently checking high-risk answers against the retrieved
evidence or resolving conflicting rules before anything reaches the user. I
would not add one just to make this simple lookup workflow look more agentic.

## 7. Shipping decision

I would not ship this version behind a real user-facing chat yet. `q07` proves
that a factually correct answer can still ignore the citation contract, and the
bad-store run proves that a hosted dependency can make every request fail.

The first safeguard I would add is an evidence-to-citation verifier. It should
compare the filenames in the final `Sources:` line with the filenames actually
returned by file search and withhold any answer that has a missing, invented,
or unmatched citation. The current regex checks that a line exists, but it
cannot prove that the stated source supported the answer.

## Final checklist

- [x] Five real documents were uploaded to one hosted vector store.
- [x] Every evaluation case used the same `ask()` function.
- [x] Hosted search and `flag_for_human` were both exercised.
- [x] The eight-row dataset meets the required category mix.
- [x] Baseline and deliberate 404 runs both contain all eight rows.
- [x] The action limits and citation guardrail were exercised directly.
- [x] Clean success, handled refusal, and hosted-tool failure traces were saved.
- [x] Every finding above is based on an observed run; no evidence placeholders remain.
