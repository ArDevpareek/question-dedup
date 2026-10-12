import sys
from pathlib import Path
# The core modules live one folder up, in the project root, so add it to the import path.
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import json
from collections import defaultdict
import evaluate_pairs as ep

# Reads the judge verdicts that evaluate_pairs.py already saved. It never calls the LLM.
PAIRS_FILE = ep.find_file(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data" / "fresh_pairs.json"
FINAL = ep.FINAL

def main():
    with open(PAIRS_FILE, encoding="utf-8") as f:
        pairs = json.load(f)
    with open(ep.CACHE_FILE, encoding="utf-8") as f:
        cache = json.load(f)
    verdicts = cache["verdicts"]
    print(f"Pairs: {PAIRS_FILE.name} ({len(pairs)} pairs, "
          f"{sum(p['label'] == 'duplicate' for p in pairs)} duplicate, "
          f"{sum(p['label'] == 'different' for p in pairs)} different)")
    print(f"Judge verdicts from {ep.CACHE_FILE.name} (cache version {cache.get('version')}), no new LLM calls")

    ep.add_scores(pairs)
    for p in pairs:
        p["judge"] = "-" if p["exact"] else verdicts.get(p["id"], "error")
    missing = [p["id"] for p in pairs if p["judge"] == "error"]
    if missing:
        print(f"Warning: no saved verdict for {missing}; counted as review")

    print(f"\n=== 1. Final setting {FINAL}, numbers guard ON, all {len(pairs)} pairs (the whole file is a test set) ===")
    ep.show(f"final {FINAL}", ep.measure(pairs, *FINAL, True))
    ep.show("judge only (for comparison)", ep.measure(pairs, 9.0, -9.0, True))

    print(f"\n=== 2. Per category, final setting {FINAL}, guard ON ===")
    groups = defaultdict(list)
    for p in pairs:
        groups[p["category"]].append(p)
    for cat, group in groups.items():
        m = ep.measure(group, *FINAL, True)
        print(f"{cat:<30} ({group[0]['label']:<9}) pairs {len(group)} | correct {len(group) - len(m['mistakes'])} | "
              f"missed {m['fn']} | false alarms {m['fp']} | review {m['review']} | judge calls {m['judge']}")

    print(f"\n=== 3. Every pair, final setting {FINAL}, guard ON ===")
    for p in pairs:
        pred, used_judge = ep.decide(p, *FINAL, True)
        wrong = (pred != "different") != (p["label"] == "duplicate")
        layer = "exact" if p["exact"] else ("judge" if used_judge else "embedding")
        print(f"{p['id']:<4} {p['category']:<30} expected {p['label']:<9} got {pred:<9} "
              f"by {layer:<9} score {p['score']:.2f}  judge: {p['judge']:<9}{'  MISTAKE' if wrong else ''}")

    print(f"\n=== 4. Mistakes with the final setting {FINAL}, guard ON ===")
    mistakes = ep.measure(pairs, *FINAL, True)["mistakes"]
    if not mistakes:
        print("none")
    for p, pred in mistakes:
        print(f"{p['id']:<4} {p['category']:<30} expected {p['label']:<9} got {pred:<9} "
              f"score {p['score']:.2f}  judge: {p['judge']}")
        print(f"      A: {p['a']}")
        print(f"      B: {p['b']}")

if __name__ == "__main__":
    main()
