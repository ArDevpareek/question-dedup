import json
from store import create_table, add_question, get_all_questions
from backfill import fill_missing_embeddings

create_table()

with open("seed_questions.json", encoding="utf-8") as f:
    seed = json.load(f)

for q in seed:
    add_question(q["id"], q["text"], q["tags"])
    fill_missing_embeddings()

for q in get_all_questions():
    print(q["id"], "|", q["text"], "|", q["tags"])