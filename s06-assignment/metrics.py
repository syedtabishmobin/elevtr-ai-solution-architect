"""LLM-judged rubric metric for requirements that need interpretation."""

from ragas.metrics import DiscreteMetric


correctness = DiscreteMetric(
    name="correctness",
    prompt=(
        "You are grading an answer produced by a RAG application.\n"
        "Return 'pass' only if the response satisfies every grading note. "
        "A missing or contradicted requirement is a failure.\n\n"
        "Response: {response}\n"
        "Grading notes: {grading_notes}"
    ),
    allowed_values=["pass", "fail"],
)

