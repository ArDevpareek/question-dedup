import argparse
import json
from pathlib import Path
import store
from store import set_db_path, create_table, add_question, get_all_questions, get_questions_by_tags
from backfill import fill_missing_embeddings
from build_clusters import build_clusters
from generator import load_detector, generate
from embed import embed

PROJECT_DIR = Path(__file__).resolve().parent
SEED_FILE = PROJECT_DIR / "data" / "seed_questions.json"
DEMO_DB = PROJECT_DIR / "demo.db"

Q1_TEXT = "What is reflection of light?"
CANDIDATES = [
    ("Exact duplicate", "exact_duplicate", "DEFINE THE REFLECTION OF LIGHT!!"),
    ("Exact duplicate", "exact_duplicate", "  what is   reflection of light "),
    ("Semantic duplicate", "semantic_duplicate", "Explain what is meant by the reflection of light."),
    ("Semantic duplicate", "semantic_duplicate", "What do we call the bouncing back of light from a surface?"),
    ("Semantic duplicate", "semantic_duplicate",
     "A ray of light strikes a plane mirror with an angle of incidence of 45°. Find the angle of reflection."),
    ("Different", "new", "Why does a plane mirror form a laterally inverted image?"),
    ("Different", "new", "Why are many images formed when two plane mirrors are placed parallel to each other?"),
    ("Different", "new", "What is the difference between a real image and a virtual image?"),
    ("Tricky: near-miss of Q6", "new", "What is the angle of incidence?"),
    ("Tricky: Q1 with other tags", "exact_duplicate", Q1_TEXT),
]
OTHER_TAGS = {"subject": "science", "chapter": "optics"}

def heading(title):
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)

def fresh_demo_db():
    # Never delete an old demo database: move it out of the way instead.
    if DEMO_DB.exists():
        old = PROJECT_DIR / "demo_old.db"
        n = 2
        while old.exists():
            old = PROJECT_DIR / f"demo_old_{n}.db"
            n += 1
        DEMO_DB.rename(old)
        print(f"Old demo.db renamed to {old.name}")
    set_db_path(DEMO_DB)
    print(f"Using database: {Path(store.DB_PATH).name} (questions.db is not touched)")

    create_table()
    with open(SEED_FILE, encoding="utf-8") as f:
        seed = json.load(f)
    for q in seed:
        add_question(q["id"], q["text"], q["tags"])
    print(f"Loaded {len(seed)} seed questions, embedded {fill_missing_embeddings()}")
    build_clusters()

def part_a():
    heading("Part A - Tags organise and filter questions")
    print("Tags of all questions:")
    for q in get_all_questions():
        print(f"   {q['id']:<4} {json.dumps(q['tags']):<62} {q['text']}")
    print("   (Q7 has an extra key 'type'. Q8 has no 'chapter'. No table change was needed for either.)")

    for filters in ({"chapter": "light"}, {"type": "numerical"}):
        found = get_questions_by_tags(filters)
        print(f"\nFilter {json.dumps(filters)}: {len(found)} questions -> {', '.join(q['id'] for q in found)}")
    print("   (Q8 is missing from the 'chapter' filter because it has no chapter tag.)")

    new_tags = {"subject": "physics", "chapter": "light", "difficulty": "easy"}
    add_question("Q11", "What is a plane mirror?", new_tags)
    print(f"\nAdded Q11 'What is a plane mirror?' with tags {json.dumps(new_tags)}")
    print("   'difficulty' is a brand-new key. Tags are stored as JSON, so the table did not change.")
    found = get_questions_by_tags({"difficulty": "easy"})
    print(f"Filter {json.dumps({'difficulty': 'easy'})}: {len(found)} question -> "
          + ", ".join(f"{q['id']} ({q['text']})" for q in found))

def part_b():
    heading("Part B - The independent detector (detector.check only, nothing is added)")
    detector = load_detector()
    rows = []
    for i, (kind, expected, text) in enumerate(CANDIDATES, 1):
        result = detector.check(text)
        print(f"\n{i}. {text!r}")
        print(f"   expected type : {kind} ({expected})")
        if i == len(CANDIDATES):
            print(f"   submitted with tags {json.dumps(OTHER_TAGS)}, but detector.check() receives only the text")
        print(f"   result        : {result['label']}")
        print(f"   decided by    : {result['decided_by']}")
        score = "-" if result["score"] is None else f"{result['score']:.2f}"
        print(f"   best score    : {score}")
        if result["matches"]:
            for qid in result["matches"]:
                print(f"   matched       : {qid} - {detector.texts[detector.ids.index(qid)]}")
        else:
            nearest, _, _ = detector.search(embed([text])[0], top_k=1)
            print(f"   matched       : none (closest was {nearest[0][0]} - {nearest[0][1]})")
        if result["reason"]:
            print(f"   judge reason  : {result['reason']}")
        rows.append((i, kind, expected, result["label"], result["decided_by"]))

    print("\nSummary")
    print(f"   {'#':<3} {'case':<28} {'expected':<20} {'got':<20} {'decided by':<14} match")
    for i, kind, expected, got, by in rows:
        print(f"   {i:<3} {kind:<28} {expected:<20} {got:<20} {by:<14} {'yes' if got == expected else 'NO'}")
    matched = sum(got == expected for _, _, expected, got, _ in rows)
    print(f"\nMatched: {matched}/{len(rows)}")

def part_c():
    heading("Part C - Generation with duplicate avoidance (topic 'reflection of light', 3 questions)")
    generate(topic="reflection of light", count=3,
             tags={"subject": "physics", "chapter": "light", "source": "llm"})

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-generate", action="store_true", help="skip Part C (no generation call)")
    args = parser.parse_args()

    heading("Setup - a throwaway demo database")
    fresh_demo_db()
    part_a()
    part_b()
    if args.no_generate:
        print("\nPart C skipped (--no-generate).")
    else:
        part_c()

if __name__ == "__main__":
    main()
