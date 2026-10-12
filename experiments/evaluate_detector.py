import sys
from pathlib import Path
# The core modules live one folder up, in the project root, so add it to the import path.
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import json
from detector import DuplicateDetector

with open(ROOT / "data" / "seed_questions.json", encoding="utf-8") as f:
    questions = json.load(f)
with open(ROOT / "data" / "test_labels.json", encoding="utf-8") as f:
    expected = json.load(f)

detector = DuplicateDetector()
correct = wrong = judge_calls = 0

for q in questions:
    result = detector.check(q["text"])
    exp = expected[q["id"]]
    got = result["label"]

    if result["decided_by"] in ("judge", "judge failed", "numbers guard"):
        judge_calls += 1

    if got == exp:
        status = "OK"
        correct += 1
    else:
        status = "WRONG"
        wrong += 1

    score = f"{result['score']:.2f}" if result["score"] is not None else "  - "
    print(f"{q['id']:>4} | got: {got:<18} | expected: {exp:<18} | best: {score} {result['matches']} | by: {result['decided_by']:<11} | {status}")
    if result["reason"]:
        print(f"         reason: {result['reason']}")

    detector.add(q["id"], q["text"])

print(f"\nCorrect: {correct}/{len(questions)}   Wrong: {wrong}   LLM judge calls: {judge_calls}")