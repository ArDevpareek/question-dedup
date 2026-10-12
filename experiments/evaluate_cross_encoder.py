import sys
from pathlib import Path
# The core modules live one folder up, in the project root, so add it to the import path.
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import json
from sentence_transformers import CrossEncoder
from normalize import make_hash

def find_file(name):
    path = Path(name)
    return path if path.exists() else ROOT / name

PAIRS_FILE = find_file(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data" / "test_pairs.json"

with open(PAIRS_FILE, encoding="utf-8") as f:
    pairs = json.load(f)

model = CrossEncoder("cross-encoder/quora-distilroberta-base")
scores = model.predict([(p["a"], p["b"]) for p in pairs])
for p, s in zip(pairs, scores):
    p["ce"] = float(s)
    p["exact"] = make_hash(p["a"]) == make_hash(p["b"])

print("=== Cross-encoder scores by category ===")
for cat in dict.fromkeys(p["category"] for p in pairs):
    group = [p["ce"] for p in pairs if p["category"] == cat]
    label = next(p["label"] for p in pairs if p["category"] == cat)
    print(f"{cat:<30} ({label:<9}) scores {min(group):.2f} to {max(group):.2f}")

print("\n=== Cross-encoder alone, different lines ===")
for t in [0.3, 0.5, 0.7, 0.9]:
    tp = fp = fn = 0
    for p in pairs:
        flagged = p["exact"] or p["ce"] >= t
        is_dup = p["label"] == "duplicate"
        if is_dup and flagged:
            tp += 1
        elif is_dup:
            fn += 1
        elif flagged:
            fp += 1
    precision = tp / (tp + fp) if tp + fp else 0
    recall = tp / (tp + fn) if tp + fn else 0
    print(f"line {t:.1f}: precision {precision:.2f} | recall {recall:.2f} | missed {fn:>2} | false alarms {fp:>2}")

print("\n=== Mistakes at line 0.5 ===")
for p in pairs:
    flagged = p["exact"] or p["ce"] >= 0.5
    if flagged != (p["label"] == "duplicate"):
        print(f"{p['id']:<4} {p['category']:<30} expected {p['label']:<9} ce {p['ce']:.2f}")
        print(f"      A: {p['a']}")
        print(f"      B: {p['b']}")