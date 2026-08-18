# Class 6 Assignment #3 - Findings

## 1. Dataset

I used ten questions that reflect how someone might test a portfolio research
assistant in practice. The dataset contains four direct policy lookups, two
numeric questions, a completeness question requiring several rules, a
comparison across two documents, a deliberately unanswerable support question,
and a financial-table question designed to expose PDF ingestion problems.

The questions do not reveal filenames or section headings. This makes the
assistant retrieve evidence from normal user wording rather than hints supplied
by the test. I checked the expected answers, source files, required facts, and
plausible traps against the source documents before running the experiments.

## 2. Baseline

The baseline supplied the four closest chunks to the answer model. Seven cases
passed all their applicable checks cleanly: `q01`, `q02`, `q03`, `q05`, `q08`,
`q09`, and `q10`.

For example, `q10` correctly returned Apple's product net sales of `$78,678`
million, services net sales of `$30,739` million, and total net sales of
`$109,417` million. Retrieval reached `apple_annual_report.pdf`, all three facts
were present in the answer, and the facts were directly quotable from the
retrieved table text.

## 3. Failure

`q07` exposed a completeness failure. The answer correctly said to cite the
latest annual report and distinguish reported facts from analyst interpretation,
but it omitted two other required parts: recording the evidence, source file,
and decision date for an escalation, and removing approved superseded notes
from active retrieval.

Source recall and index integrity both passed, which means the expected document
and required facts were available. Quotability also passed for the facts the
model chose to state. The failure therefore occurred during evidence selection
or generation rather than ingestion or document retrieval. The Ragas judge
correctly failed the response for not satisfying the complete rubric.

`q06` produced a smaller wording-sensitive failure. It stated that four chunks
are supplied but omitted that they are the *four closest* chunks. Both the
key-fact check and Ragas rubric therefore failed it.

## 4. Evidence quality

Yes. In the baseline, `q04` looked acceptable to the Ragas judge even though its
evidence failed. The judge gave it `correctness=pass`, but retrieval never
reached `portfolio_research_faq.md`, so source recall was `0.0`. The response
also missed the required phrases `retrieved context` and `source filename`, and
quotability failed.

This is the important difference between grading fluent wording and grading a
RAG system. The answer said it should use only supplied context and returned
"don't know," but cited `[no applicable source file]` rather than grounding the
policy in the expected FAQ. The judge accepted the behavior while the
transparent checks revealed that the answer could not be supported by the
retrieved evidence.

The PDF-layout case, `q10`, did not show an ingestion failure in this corpus.
All three table values passed both index-integrity and quotability checks, which
confirms that extraction preserved the required evidence for this question.

## 5. Ragas judge

The rubric judge added value on `q09`, the missing-information question. That
case has no required positive key facts, so string checks alone cannot reliably
decide whether a refusal is appropriate or whether the model invented a support
address. The judge examined the response and correctly passed it because it
said the requested email was unavailable and did not guess one.

I disagreed with the baseline judgment on `q04`. The judge reasonably recognized
some desired behavior in the wording, but its pass was too generous for a RAG
evaluation because the expected source was not retrieved and the response was
not quotable from the evidence. Keeping the deterministic checks beside the
judge made this disagreement visible.

## 6. Comparison

I changed only retrieval depth: `baseline` used `top_k=4`, while `top_k_6` used
`top_k=6`. The corpus, index, models, prompts, questions, and grading rules
remained unchanged.

- Improved cases: none
- Regressed cases: `q04`
- Unchanged cases: `q01`, `q02`, `q03`, `q05`, `q06`, `q07`, `q08`, `q09`, and
  `q10`

The comparison command reported:

```text
baseline -> top_k_6

q04: correctness: pass -> fail
```

Six retrieved chunks still did not reach the expected FAQ for `q04`. Instead,
the answer remained grounded in unrelated annual-report excerpts and the judge
now failed it for not clearly stating the actual policy. The added context did
not repair the two existing completeness failures or improve any other metric.

## 7. Shipping decision

I would not ship the six-chunk configuration. It produced no measured
improvements, left `q06` and `q07` unchanged, and caused `q04` to regress from a
judge pass to a fail. The four-chunk baseline is therefore the better of these
two tested configurations.

Before production use, I would improve retrieval for policy-behavior questions
like `q04` and retest the completeness prompt against `q07`. I would also keep
the transparent evidence checks in the release process so a favorable judge
score cannot hide missing or unquotable sources.

## Final checklist

- [x] Both CSV files contain all 10 rows.
- [x] Clean passes are identified.
- [x] Retrieval, completeness, and evidence failures are explained.
- [x] The table-ingestion evidence test is discussed.
- [x] A Ragas judgment is reviewed rather than accepted blindly.
- [x] Improved, regressed, and unchanged cases are named.
- [x] The shipping decision refers to specific qids.
- [x] All evidence placeholders have been replaced with observed results.
