import json
from detector import DuplicateDetector

with open("seed_questions.json", encoding="utf-8") as f:
    questions = json.load(f)
with open("test_labels.json", encoding="utf-8") as f:
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