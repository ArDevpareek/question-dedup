import sys
from pathlib import Path
# The core modules live one folder up, in the project root, so add it to the import path.
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from store import get_all_questions
from embed import embed

questions = get_all_questions()
ids = [q["id"] for q in questions]
texts = [q["text"] for q in questions]

vectors = embed(texts)
print("Each question became", vectors.shape[1], "numbers\n")

scores = vectors @ vectors.T

print("      " + "".join(f"{i:>6}" for i in ids))
for i, row_id in enumerate(ids):
    row = "".join(f"{scores[i][j]:6.2f}" for j in range(len(ids)))
    print(f"{row_id:>5} {row}")

candidate = "Define reflection of light."
cand_vec = embed([candidate])[0]
cand_scores = vectors @ cand_vec

print("\nCandidate:", candidate)
for qid, text, s in sorted(zip(ids, texts, cand_scores), key=lambda x: -x[2]):
    print(f"   {s:.2f}  {qid}  {text}")