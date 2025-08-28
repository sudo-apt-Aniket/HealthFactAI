from __future__ import annotations

from typing import List


def grade(answers: List[int], key: List[int]) -> dict:
    total = min(len(answers), len(key))
    score = 0
    explanations: List[str] = []
    for i in range(total):
        if answers[i] == key[i]:
            score += 1
            explanations.append(f"Q{i+1}: Correct.")
        else:
            explanations.append(f"Q{i+1}: Incorrect. Correct option: index {key[i]}.")
    return {"status": "ok", "score": score, "total": total, "explanations": explanations}


