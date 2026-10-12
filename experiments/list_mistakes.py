import sys
from pathlib import Path
# The core modules live one folder up, in the project root, so add it to the import path.
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import json
from collections import defaultdict
import evaluate_pairs as ep
from evaluate_combined import add_scores, measure, show, d1, d2, make_d3

CACHE_DIR = Path(__file__).resolve().parent / "judge_caches"
RULE_CACHES = {
    "old": CACHE_DIR / "judge_cache_v1.json",
    "new": CACHE_DIR / "judge_cache_v2.json",
    "calc": CACHE_DIR / "judge_cache.json",
}
RULE_NAMES = {"old": "old rules", "new": "new rules", "calc": "new + calc rule"}

def load_verdicts(path):
    with open(path, encoding="utf-8") as f:
        cache = json.load(f)
    print(f"{path.name}: cache version {cache['version']}, {len(cache['verdicts'])} verdicts")
    return cache["verdicts"]

def cascade(dup_t, new_t):
    return lambda p: ep.decide(p, dup_t, new_t)

def main():
    with open(ROOT / "data" / "test_pairs.json", encoding="utf-8") as f:
        pairs = json.load(f)
    verdicts = {rules: load_verdicts(path) for rules, path in RULE_CACHES.items()}
    add_scores(pairs, verdicts["old"])
    for p in pairs:
        for rules, v in verdicts.items():
            p[f"judge_{rules}"] = "-" if p["exact"] else v.get(p["id"], "error")

    approaches = [("embedding only, line 0.80", "old", cascade(0.80, 0.80))]
    for rules in RULE_CACHES:
        approaches.append((f"judge only ({RULE_NAMES[rules]})", rules, d1))
    approaches.append(("old cascade (0.92, 0.75), old rules", "old", cascade(0.92, 0.75)))
    approaches.append(("old cascade (0.92, 0.75), new rules", "new", cascade(0.92, 0.75)))
    approaches.append(("old cascade (0.92, 0.75), calc", "calc", cascade(0.92, 0.75)))
    approaches.append(("step-1 best (0.92, 0.50), old rules", "old", cascade(0.92, 0.50)))
    approaches.append(("step-4 best (0.98, 0.50), new rules", "new", cascade(0.98, 0.50)))
    approaches.append(("cascade (0.98, 0.50), calc", "calc", cascade(0.98, 0.50)))
    approaches.append(("cross-encoder alone, line 0.5", "old", d2))
    for rules in RULE_CACHES:
        approaches.append((f"D3 (0.8, 0.05), {RULE_NAMES[rules]}", rules, make_d3(0.8, 0.05)))
    halves = [("all 60", pairs), ("TEST half", pairs[1::2])]

    print("\n=== 1. Scores per approach ===")
    for half_name, group in halves:
        print(f"-- {half_name} ({len(group)} pairs)")
        for name, rules, decide in approaches:
            for p in pairs:
                p["judge"] = p[f"judge_{rules}"]
            show(name[:34], measure(group, decide))

    print("\n=== 2. Mistakes per approach on all 60 pairs, grouped by category ===")
    for name, rules, decide in approaches:
        for p in pairs:
            p["judge"] = p[f"judge_{rules}"]
        by_cat = defaultdict(list)
        for p, pred in measure(pairs, decide)["mistakes"]:
            by_cat[p["category"]].append(p["id"])
        total = sum(len(v) for v in by_cat.values())
        print(f"\n{name}: {total} mistakes")
        for cat, ids in by_cat.items():
            print(f"   {cat:<30} {', '.join(ids)}")

if __name__ == "__main__":
    main()
