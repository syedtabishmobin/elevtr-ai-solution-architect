# Class 5 Assignment #2 - Findings

This document is the evidence log for the idempotency, freshness, cascade,
cost, and embedding-contract experiments. Replace every bracketed evidence
field only with output observed from an actual run.

##
## Experiment context

- Corpus: Apple, Microsoft, and Tesla annual reports plus two shareable equity
  research process notes
- Baseline embedding model: `ollama/nomic-embed-text`
- Comparison embedding model: `ollama/mxbai-embed-large`
- Generation model: `ollama/qwen3:8b`
- Chunking: 120 words with 20 words of overlap
- Retrieval depth: four chunks
- Date performed: `2026-08-13`
- Machine used: `Apple M1 Pro`

##
## 1. Idempotency

The first and second runs of `build.py` both produced `1,613` chunks, confirming 
that running the pipeline again did not create duplicates.

This works for two main reasons. First, each chunk receives a consistent ID based on 
its source filename and position in the document. If the source content has not changed, 
the same chunks receive the same IDs each time. Second, `build.py` uses `upsert`, which 
updates an existing record when its ID already exists instead of adding another copy.

In the S02 implementation, each chunk received a randomly generated `uuid4()` ID. This 
meant that the same chunk received a completely new ID every time the pipeline ran. 
S02 avoided keeping those duplicates by deleting and rebuilding its collections before indexing.

Evidence:

```text
indexed 1613 chunks from 5 docs -> 1613 in collection
indexed 1613 chunks from 5 docs -> 1613 in collection
```

##
## 2. The stale answer

Question used: `What risk score triggers an additional risk review?`

Original source fact: `70 out of 100`

Temporary edited fact: `85 out of 100`

After the source was edited but before re-indexing, `ask.py` returned:

```text
embedded 1/1
retrieved 4 chunks (lower distance = closer in meaning):
   0.563  equity_research_policy.md         threshold A holding is escalated for an additional risk review w...
   0.694  equity_research_policy.md         # Equity Research Review Policy This is a fictional but realisti...
   0.721  microsoft_annual_report.pdf       services are reviewed by our internal audit teams as well as ind...
   0.764  microsoft_annual_report.pdf       subject to price risk. SENSITIVITY ANALYSIS The following table ...

The risk score that triggers an additional risk review is **70 out of 100** [equity_research_policy.md].
```

For a non-engineer stakeholder: the source policy changed, but the assistant
silently continued answering from an old copy because its search index had not
been refreshed.

Full rebuild time after the one-fact edit: `47.620 seconds`.

##
## 3. The ghost document

Document temporarily moved out of `docs/`:
`docs/portfolio_research_faq.md`

The upsert-only rebuild reported:

```text
indexed 1610 chunks from 4 docs -> 1613 in collection
```

The two counts were different because `build.py` could only see the files currently 
in the `docs/` folder, while Chroma still held chunks from the document that had been 
removed. The `upsert` operation can add new records or update existing ones, but it does 
not automatically delete records when their source file disappears.

A deleted document is more serious than a stale one because the assistant can still answer 
from and cite a source that is no longer available or approved for use. The response may 
look trustworthy, so the user receives no warning that its source has been removed. 
An upsert-only pipeline cannot solve this problem by itself because it is never told which 
records are no longer needed. The pipeline must explicitly compare the index with the current 
source files and delete the missing records, or rebuild the entire index from scratch.

Ghost question: `How many chunks does the demonstration supply to the answer model?`

Answer before tombstoning:

```text
embedded 1/1
retrieved 4 chunks (lower distance = closer in meaning):
   0.778  portfolio_research_faq.md         # Portfolio Research Assistant FAQ This fictional FAQ describes ...
   0.966  microsoft_annual_report.pdf       of these three levels based on the lowest level input that is si...
   0.979  microsoft_annual_report.pdf       365 Commercial products and cloud services, Server products and ...
   0.982  microsoft_annual_report.pdf       that are allocated primarily include those relating to marketing...

The demonstration uses the four closest chunks for each question [portfolio_research_faq.md].
```

Deletion sync counts:

```text
unchanged: 1610
new      : 0
changed  : 0
removed  : 3

re-embedded 0 of 1610 chunks (0.0% of a full reindex)
collection now holds 1610 chunks
```

Answer after tombstoning:

```text
embedded 1/1
retrieved 4 chunks (lower distance = closer in meaning):
   0.966  microsoft_annual_report.pdf       of these three levels based on the lowest level input that is si...
   0.979  microsoft_annual_report.pdf       365 Commercial products and cloud services, Server products and ...
   0.982  microsoft_annual_report.pdf       that are allocated primarily include those relating to marketing...
   0.999  microsoft_annual_report.pdf       were as follows: (In millions, issuance by calendar year) Maturi...

The context provided does not mention anything about "chunks" or the number of chunks supplied to the answer model. Therefore, I don't know.
```

Restoration sync counts:

```text
unchanged: 1610
new      : 3
changed  : 0
removed  : 0
embedded 3/3
re-embedded 3 of 1613 chunks (0.2% of a full reindex)
collection now holds 1613 chunks
```

##
## 4. The cascade

Use `docs/equity_research_policy.md` for both edits, restoring the file with Git
between experiments so they start from the same baseline.

| Experiment | Changed | New | Changed + new |
|---|---:|---:|---:|
| Edit A - one word near the end | `1` | `0` | `1` |
| Edit B - one sentence at the top | `2` | `0` | `2` |

Edit A should only affect the chunk containing the changed word. Edit B can have a 
much wider impact because adding a sentence at the beginning shifts the words that 
fall into every later 120-word chunk. Since the chunk IDs are based on the filename 
and chunk position, the IDs stay the same even though the content inside those chunks 
changes. Their hashes therefore change, and an additional chunk may also be created 
if the document crosses a new chunk boundary.

One possible improvement would be to create chunk IDs from a hash of the chunk’s content. 
This would allow unchanged chunks to keep the same identity even when new text is added 
earlier in the document. However, this approach also has trade-offs. Identical text could 
produce the same ID unless the source filename is included, an edited chunk would appear as 
one deletion and one addition, and extra metadata would still be needed to preserve the 
original order and support accurate citations.

##
## 5. The cost

### Observed measurements

- Total characters across `docs/`: `1,081,230`
- Approximate tokens (`characters / 4`): `270,307.5`
- Full re-embed time with the comparison model: `1:24.06`
- Edit A changed chunks: `1`
- Total chunks after the clean rebuild: `1,613`

At the assignment yardstick of `$0.02` per one million tokens:

- Full re-index price: `(270,307.5 / 1,000,000) x $0.02 = $0.00540615`
- Edit A delta price: `(270,307.5 x 1 / 1,613 / 1,000,000) x $0.02 = $0.00000335`
- Corpus multiplied by 1,000, full price: `$5.40615000`
- Corpus multiplied by 1,000, proportional delta price: `$0.00335161`

For this corpus, I would update the index whenever an approved source document changes 
and run a weekly check to make sure the index still matches the source files. I would 
reserve a full rebuild for major changes, such as switching embedding models, or for 
recovering from a damaged index. This approach keeps answers current without repeatedly 
processing documents that have not changed.


##
## 6. The embedding contract

After changing `EMBED` to `ollama/mxbai-embed-large`, `sync.py` reported:

```text
unchanged: 1613
new      : 0
changed  : 0
removed  : 0

re-embedded 0 of 1613 chunks (0.0% of a full reindex)
collection now holds 1613 chunks
```

The subsequent `ask.py` error was:

```text
Traceback (most recent call last):
  File "/Users/syedtabishmobin/Documents/ELEVTR/src/elevtr-ai-solution-architect/s05-assignment/ask.py", line 78, in <module>
    ask(user_question)
  File "/Users/syedtabishmobin/Documents/ELEVTR/src/elevtr-ai-solution-architect/s05-assignment/ask.py", line 25, in ask
    result = index.query(
             ^^^^^^^^^^^^
  File "/Users/syedtabishmobin/Documents/ELEVTR/src/elevtr-ai-solution-architect/s05-assignment/.venv/lib/python3.11/site-packages/chromadb/api/models/Collection.py", line 265, in query
    query_results = self._client._query(
                    ^^^^^^^^^^^^^^^^^^^^
  File "/Users/syedtabishmobin/Documents/ELEVTR/src/elevtr-ai-solution-architect/s05-assignment/.venv/lib/python3.11/site-packages/chromadb/api/rust.py", line 582, in _query
    rust_response = self.bindings.query(
                    ^^^^^^^^^^^^^^^^^^^^
chromadb.errors.InvalidArgumentError: Collection expecting embedding with dimension of 768, got 1024
```

The sync process did not detect the model change because it only checks whether the 
chunk content has changed. Since none of the source documents were edited, all the 
content hashes still matched and the system assumed the index was up to date. The 
problem only became visible when `ask.py` created a query embedding with the new model 
and Chroma found that its dimensions did not match the stored embeddings.

If the replacement model had also produced 768-dimensional embeddings, Chroma would 
not have raised an error. The system would still be comparing query and document 
embeddings created by different models, which could quietly make the retrieval results 
less accurate. I would catch this by recording the embedding model in each chunk’s 
metadata and testing retrieval with questions that have known-correct source documents. 
I would also include the model name, vector dimensions, prefixes, and preprocessing rules 
in an `embedding_contract` version. When that version changes, the sync process would 
treat every chunk as changed and rebuild its embedding.

##
## Final state checklist

## Final checks

- `[x]` I ran `build.py` twice and recorded both collection counts.
- `[x]` I recorded the stale answer and measured how long a full rebuild took.
- `[x]` I reproduced the ghost-document problem, removed its old chunks from the index, and restored the document.
- `[x]` I used the same starting point for both Edit A and Edit B so the results could be compared fairly.
- `[x]` I recorded the complete embedding-dimension error.
- `[x]` I rebuilt the index using my final embedding model.
- `[x]` I replaced all evidence placeholders with results from my own runs.
- `[x]` I confirmed that the generated index, virtual environment, environment file, and submission ZIP are not tracked by Git.
