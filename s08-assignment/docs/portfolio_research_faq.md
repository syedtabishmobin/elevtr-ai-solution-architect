# Portfolio Research Assistant FAQ

This fictional FAQ describes how the local retrieval demonstration should be
used. It is shareable and provides a second editable text source for freshness
experiments.

## Which companies are in the demonstration corpus?

The corpus contains annual reports for Apple, Microsoft, and Tesla, together
with internal research-process notes created for the coursework.

## How many retrieved chunks should be supplied to the answer model?

The demonstration uses the four closest chunks for each question. A smaller or
larger value may be evaluated later, but changes must be measured against a set
of questions with known source documents.

## Which embedding model is the baseline?

The baseline embedding model is nomic-embed-text running locally through
Ollama. The read and write paths must use the same embedding contract.

## Can the assistant answer from general knowledge?

No. It must answer only from retrieved context, cite the source filename in
brackets, and say that it does not know when the retrieved context is
insufficient.

## Why are deleted documents important?

A deleted source must also disappear from the retrieval index. Otherwise the
assistant can confidently cite a document that no longer exists, which is more
dangerous than an obvious system error.
