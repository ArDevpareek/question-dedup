import json
import random
from datasets import load_dataset

def sample(name, config, split, col_a, col_b, n, prefix):
    ds = load_dataset(name, config, split=split)
    rows = random.Random(0).sample(range(len(ds)), n)
    out = []
    for i, r in enumerate(rows, 1):
        x = ds[r]
        out.append({
            "id": f"{prefix}{i}",
            "category": prefix.lower(),
            "label": "duplicate" if x["label"] == 1 else "different",
            "a": x[col_a],
            "b": x[col_b],
        })
    return out

pairs = (sample("nyu-mll/glue", "qqp", "validation", "question1", "question2", 50, "QQP")
         + sample("google-research-datasets/paws", "labeled_final", "test", "sentence1", "sentence2", 50, "PAWS"))

with open("public_pairs.json", "w", encoding="utf-8") as f:
    json.dump(pairs, f, indent=1, ensure_ascii=False)
print(f"Saved {len(pairs)} pairs")
