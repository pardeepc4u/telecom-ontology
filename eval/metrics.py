"""Precision/recall/F1 of a ranked retrieval result against a ground-truth
relevant-ticket set. Order-agnostic (set-based) rather than a ranking metric
like NDCG — for this dataset's small ground-truth sets (a handful to ~20
tickets), "did you find the right tickets at all" is the more legible
number to put in front of an interviewer than a ranking metric would be.
"""


def precision_recall_f1(retrieved_ids: list[str], relevant_ids: set[str]) -> dict:
    retrieved_set = set(retrieved_ids)

    if not retrieved_set:
        precision = 0.0
    else:
        precision = len(retrieved_set & relevant_ids) / len(retrieved_set)

    if not relevant_ids:
        recall = 0.0
    else:
        recall = len(retrieved_set & relevant_ids) / len(relevant_ids)

    f1 = 0.0 if (precision + recall) == 0 else 2 * precision * recall / (precision + recall)

    return {"precision": precision, "recall": recall, "f1": f1}
