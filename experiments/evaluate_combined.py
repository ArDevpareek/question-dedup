import sys
from pathlib import Path
# The core modules live one folder up, in the project root, so add it to the import path.
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import json
from sentence_transformers import CrossEncoder
from normalize import make_hash
from embed import embed

PAIRS_FILE = ROOT / "data" / "test_pairs.json"
CACHE_FILE = Path(__file__).resolve().parent / "judge_caches" / "judge_cache.json"
CE_MODEL = "cross-encoder/quora-distilroberta-base"

D2_LINE = 0.5
HIGH_OPTIONS = [0.8, 0.9, 0.95]
LOW_OPTIONS = [0.05, 0.1, 0.2, 0.3]
MIN_PRECISION = 0.90

def add_scores(pairs, verdicts):
    vec_a = embed([p["a"] for p in pairs])
    vec_b = embed([p["b"] for p in pairs])
    model = CrossEncoder(CE_MODEL)
    ce = model.predict([(p["a"], p["b"]) for p in pairs])
    for p, va, vb, s in zip(pairs, vec_a, vec_b, ce):
        p["exact"] = make_hash(p["a"]) == make_hash(p["b"])
        p["score"] = float(va @ vb)
        p["ce"] = float(s)
        p["judge"] = "-" if p["exact"] else verdicts.get(p["id"], "error")

def judge_decision(p):
    v = p["judge"]
    if v in ("duplicate", "different"):
        return v, True
    return "review", True

def d1(p):
    if p["exact"]:
        return "duplicate", False
    return judge_decision(p)

def d2(p):
    if p["exact"]:
        return "duplicate", False
    return ("duplicate" if p["ce"] >= D2_LINE else "different"), False

def make_d3(high, low):
    def d3(p):
        if p["exact"]:
            return "duplicate", False
        if p["ce"] >= high:
            return "duplicate", False
        if p["ce"] < low:
            return "different", False
        return judge_decision(p)
    return d3

def measure(pairs, decide):
    m = {"tp": 0, "fp": 0, "fn": 0, "tn": 0, "review": 0, "judge": 0, "mistakes": []}
    for p in pairs:
        pred, used_judge = decide(p)
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
    with open(CACHE_FILE, encoding="utf-8") as f:
        cache = json.load(f)
    verdicts = cache["verdicts"]
    print(f"Judge verdicts from {CACHE_FILE.name} (cache version {cache.get('version')}, {len(verdicts)} verdicts)")

    add_scores(pairs, verdicts)
    missing = [p["id"] for p in pairs if p["judge"] == "error"]
    if missing:
        print(f"Warning: no judge verdict for {missing}; counted as review")
    tune = pairs[0::2]
    test = pairs[1::2]
    halves = [("all 60", pairs), ("TUNE half", tune), ("TEST half", test)]

    print("\n=== 1. D1 (exact, then judge) and D2 (exact, then cross-encoder line 0.5) ===")
    for half_name, group in halves:
        print(f"-- {half_name} ({len(group)} pairs)")
        show("D1 exact + judge", measure(group, d1))
        show(f"D2 exact + cross-encoder {D2_LINE}", measure(group, d2))

    print("\n=== 2. D3 tuning on the TUNE half (30 pairs) ===")
    results = []
    for high in HIGH_OPTIONS:
        for low in LOW_OPTIONS:
            m = measure(tune, make_d3(high, low))
            results.append((high, low, m))
            show(f"D3 (HIGH {high:.2f}, LOW {low:.2f})", m)
    good = [r for r in results if r[2]["precision"] >= MIN_PRECISION]
    pool = good if good else results
    best = sorted(pool, key=lambda r: (-r[2]["recall"], r[2]["judge"], -r[2]["precision"]))[0]
    chosen = (best[0], best[1])
    print(f"\nChosen D3: HIGH {chosen[0]}, LOW {chosen[1]} "
          f"(precision >= 0.90, then highest recall, then fewest judge calls)")

    print("\n=== 3. D3 settings on the TEST half and all 60 (for reference, not used for choosing) ===")
    for high in HIGH_OPTIONS:
        for low in LOW_OPTIONS:
            show(f"TEST D3 (HIGH {high:.2f}, LOW {low:.2f})", measure(test, make_d3(high, low)))
    for high in HIGH_OPTIONS:
        for low in LOW_OPTIONS:
            show(f"ALL  D3 (HIGH {high:.2f}, LOW {low:.2f})", measure(pairs, make_d3(high, low)))

    print("\n=== 4. Fair check on the TEST half (30 pairs, not used for tuning) ===")
    show("D1 exact + judge", measure(test, d1))
    show(f"D2 exact + cross-encoder {D2_LINE}", measure(test, d2))
    show(f"D3 chosen {chosen}", measure(test, make_d3(*chosen)))

    print("\n=== 5. Chosen D3 on all 60 pairs ===")
    show(f"D3 chosen {chosen}", measure(pairs, make_d3(*chosen)))

    print(f"\n=== 6. Mistakes with the chosen D3 setting {chosen} (all 60 pairs) ===")
    for p, pred in measure(pairs, make_d3(*chosen))["mistakes"]:
        print(f"{p['id']:<4} {p['category']:<30} expected {p['label']:<9} got {pred:<9} "
              f"cosine {p['score']:.2f}  ce {p['ce']:.2f}  judge: {p['judge']}")
        print(f"      A: {p['a']}")
        print(f"      B: {p['b']}")

if __name__ == "__main__":
    main()
