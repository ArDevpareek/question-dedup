import sys
from pathlib import Path
# The core modules live one folder up, in the project root, so add it to the import path.
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import time
import numpy as np
from embed import embed

texts = [f"Sample physics question number {i} about light and mirrors?" for i in range(200)]
embed(texts[:5])

start = time.time()
embed(texts)
per_q = (time.time() - start) / len(texts)
print(f"Embedding: {per_q * 1000:.1f} ms per question")
for n in [10_000, 100_000]:
    print(f"   re-embedding {n:,} questions every run would take about {per_q * n:.0f} s")

dim = 384
query = np.random.randn(dim).astype(np.float32)
query /= np.linalg.norm(query)

for n in [1_000, 10_000, 100_000]:
    bank = np.random.randn(n, dim).astype(np.float32)
    bank /= np.linalg.norm(bank, axis=1, keepdims=True)
    for _ in range(3):
        scores = bank @ query
        np.argsort(-scores)[:3]
    start = time.perf_counter()
    for _ in range(50):
        scores = bank @ query
        top = np.argsort(-scores)[:3]
    ms = (time.perf_counter() - start) / 50 * 1000
    print(f"Search in {n:>7,} questions: {ms:.2f} ms")