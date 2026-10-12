import json
import re
import sys
import time
import hashlib
from normalize import make_hash
from embed import embed
from judge import judge, JUDGE_PROMPT
from llm import MODEL

PAIRS_FILE = sys.argv[1] if len(sys.argv) > 1 else "test_pairs.json"
CACHE_FILE = "judge_cache.json"
SLEEP_BETWEEN_CALLS = 5


CURRENT = (0.92, 0.75)
DUP_OPTIONS = [0.92, 0.95, 0.98, 1.01]
NEW_OPTIONS = [0.30, 0.40, 0.50, 0.60, 0.70, 0.75]
MIN_PRECISION = 0.90
FINAL = (1.01, 0.50)
USE_NUMBERS_GUARD = True

def has_numbers(text):
    return bool(re.search(r"\d", text))

def add_scores(pairs):
    vec_a = embed([p["a"] for p in pairs])
    vec_b = embed([p["b"] for p in pairs])
    for p, va, vb in zip(pairs, vec_a, vec_b):
        p["exact"] = make_hash(p["a"]) == make_hash(p["b"])
        p["score"] = float(va @ vb)

def load_cache(version):
    try:
        with open(CACHE_FILE, encoding="utf-8") as f:
            cache = json.load(f)
    except FileNotFoundError:
        return {"version": version, "verdicts": {}}
    if cache.get("version") != version:
        print("The judge prompt or model changed, so the old saved verdicts are not used.")
        return {"version": version, "verdicts": {}}
    return cache

def save_cache(cache):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2)

def add_judge_verdicts(pairs):
    version = hashlib.sha256((JUDGE_PROMPT + MODEL).encode("utf-8")).hexdigest()[:12]
    cache = load_cache(version)
    todo = [p for p in pairs if not p["exact"] and p["id"] not in cache["verdicts"]]
    print(f"Judge: {len(todo)} pairs still need a verdict")
    for i, p in enumerate(todo, 1):
        try:
            v = judge(p["b"], [("A", p["a"], p["score"])])
            cache["verdicts"][p["id"]] = v.get("verdict", "review")
            save_cache(cache)
            print(f"   {i}/{len(todo)} {p['id']}: {cache['verdicts'][p['id']]}")
        except Exception as e:
            print(f"   {i}/{len(todo)} {p['id']}: judge failed, will retry next run ({e})")
        time.sleep(SLEEP_BETWEEN_CALLS)
    for p in pairs:
        p["judge"] = "-" if p["exact"] else cache["verdicts"].get(p["id"], "error")

def decide(p, dup_t, new_t, guard=None):
    if guard is None:
        guard = USE_NUMBERS_GUARD
    if p["exact"]:
        return "duplicate", False
    if p["score"] >= dup_t:
        return "duplicate", False
    if p["score"] < new_t:
        return "different", False
    v = p["judge"]
    if v == "duplicate" and guard and has_numbers(p["a"]) != has_numbers(p["b"]):
        return "review", True
    if v in ("duplicate", "different"):
        return v, True
    return "review", True

def measure(pairs, dup_t, new_t, guard=None):
    m = {"tp": 0, "fp": 0, "fn": 0, "tn": 0, "review": 0, "judge": 0, "mistakes": []}
    for p in pairs:
        pred, used_judge = decide(p, dup_t, new_t, guard)
        if used_judge:
            m["judge"] += 1
        if pred == "review":
            m["review"] += 1
        flagged = pred != "different"
        is_dup = p["label"] == "duplicate"
        if is_dup and flagged:
            m["tp"] += 1
        elif is_dup:
            m["fn"] += 1
            m["mistakes"].append((p, pred))
        elif flagged:
            m["fp"] += 1
            m["mistakes"].append((p, pred))
        else:
            m["tn"] += 1
    flagged_total = m["tp"] + m["fp"]
    dup_total = m["tp"] + m["fn"]
    m["precision"] = m["tp"] / flagged_total if flagged_total else 0.0
    m["recall"] = m["tp"] / dup_total if dup_total else 0.0
    return m

def show(name, m):
    print(f"{name:<34} precision {m['precision']:.2f} | recall {m['recall']:.2f} | "
          f"missed dups {m['fn']:>2} | false alarms {m['fp']:>2} | review {m['review']:>2} | judge calls {m['judge']:>2}")

def main():
    with open(PAIRS_FILE, encoding="utf-8") as f:
        pairs = json.load(f)
    tune = pairs[0::2]
    test = pairs[1::2]

    add_scores(pairs)
    add_judge_verdicts(pairs)
    print(f"Numbers guard: {'ON' if USE_NUMBERS_GUARD else 'OFF'}")

    print("\n=== 1. Embedding scores by category ===")
    for cat in dict.fromkeys(p["category"] for p in pairs):
        group = [p for p in pairs if p["category"] == cat]
        scores = [p["score"] for p in group]
        print(f"{cat:<30} ({group[0]['label']:<9}) scores {min(scores):.2f} to {max(scores):.2f}")

    print("\n=== 2. Each layer on its own (all 60 pairs) ===")
    for t in [0.60, 0.70, 0.80, 0.90]:
        show(f"embedding only, line at {t:.2f}", measure(pairs, t, t))
    show("judge only (no embedding lines)", measure(pairs, 9.0, -9.0))
    show(f"cascade now {CURRENT}", measure(pairs, *CURRENT))
    show(f"final {FINAL}", measure(pairs, *FINAL))

    print("\n=== 3. Tuning on the TUNE half (30 pairs) ===")
    results = []
    for dup_t in DUP_OPTIONS:
        for new_t in NEW_OPTIONS:
            m = measure(tune, dup_t, new_t)
            results.append((dup_t, new_t, m))
            show(f"cascade ({dup_t:.2f}, {new_t:.2f})", m)
    good = [r for r in results if r[2]["precision"] >= MIN_PRECISION]
    pool = good if good else results
    best = sorted(pool, key=lambda r: (-r[2]["recall"], r[2]["judge"], -r[2]["precision"]))[0]
    chosen = (best[0], best[1])
    print(f"\nChosen: {chosen} (precision >= 0.90, then highest recall, then fewest judge calls)")

    print("\n=== 4. Fair check on the TEST half (30 pairs, not used for tuning) ===")
    show(f"cascade now {CURRENT}", measure(test, *CURRENT))
    show(f"cascade chosen {chosen}", measure(test, *chosen))
    show(f"final {FINAL}", measure(test, *FINAL))

    print(f"\n=== 5. Mistakes with the chosen setting {chosen} (all 60 pairs) ===")
    for p, pred in measure(pairs, *chosen)["mistakes"]:
        print(f"{p['id']:<4} {p['category']:<30} expected {p['label']:<9} got {pred:<9} "
              f"score {p['score']:.2f}  judge: {p['judge']}")
        print(f"      A: {p['a']}")
        print(f"      B: {p['b']}")

    print(f"\n=== 6. Final setting {FINAL}, numbers guard on vs off ===")
    for half_name, group in [("all pairs", pairs), ("TEST half", test)]:
        for guard in (True, False):
            show(f"{half_name}, guard {'ON' if guard else 'OFF'}", measure(group, *FINAL, guard))

    print(f"\n=== 7. Mistakes and reviews with the final setting {FINAL} "
          f"(all pairs, guard {'ON' if USE_NUMBERS_GUARD else 'OFF'}) ===")
    for p in pairs:
        pred, _ = decide(p, *FINAL)
        wrong = (pred != "different") != (p["label"] == "duplicate")
        if wrong or pred == "review":
            print(f"{p['id']:<4} {p['category']:<30} expected {p['label']:<9} got {pred:<9} "
                  f"score {p['score']:.2f}  judge: {p['judge']}{'  (MISTAKE)' if wrong else ''}")

if __name__ == "__main__":
    main()