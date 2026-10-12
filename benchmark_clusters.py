import time
import numpy as np
from clusters import ClusteredIndex

N = 100_000
DIM = 384
N_QUERIES = 200

def make_fake_bank(n, dim, n_topics=500, noise=0.7, spread=0.6, seed=0):
    rng = np.random.default_rng(seed)
    common = rng.standard_normal(dim)
    common /= np.linalg.norm(common)
    topics = common + spread * rng.standard_normal((n_topics, dim)) / np.sqrt(dim)
    topics /= np.linalg.norm(topics, axis=1, keepdims=True)
    which = rng.integers(0, n_topics, size=n)
    bank = topics[which] + noise * rng.standard_normal((n, dim)) / np.sqrt(dim)
    bank /= np.linalg.norm(bank, axis=1, keepdims=True)
    return bank.astype(np.float32)

rng = np.random.default_rng(1)
bank = make_fake_bank(N, DIM)
pairs = rng.integers(0, N, size=(2000, 2))
avg_sim = np.mean(np.sum(bank[pairs[:, 0]] * bank[pairs[:, 1]], axis=1))
print(f"Average similarity between two random fake questions: {avg_sim:.2f}")

rows = rng.choice(N, size=N_QUERIES, replace=False)
queries = bank[rows] + 0.9 * rng.standard_normal((N_QUERIES, DIM)) / np.sqrt(DIM)
queries /= np.linalg.norm(queries, axis=1, keepdims=True)
queries = queries.astype(np.float32)

start = time.perf_counter()
true_best = [int(np.argmax(bank @ q)) for q in queries]
brute_ms = (time.perf_counter() - start) / N_QUERIES * 1000
print(f"Brute force: {brute_ms:.2f} ms per query (searches all {N:,})")

k = int(np.sqrt(N))
start = time.perf_counter()
index = ClusteredIndex(bank, k)
print(f"Built {k} clusters in {time.perf_counter() - start:.1f} s\n")

for nprobe in [1, 2, 5, 10, 20]:
    found = 0
    searched = 0
    start = time.perf_counter()
    for q, true_row in zip(queries, true_best):
        result_rows, _, n_searched = index.search(q, nprobe)
        searched += n_searched
        if result_rows[0] == true_row:
            found += 1
    ms = (time.perf_counter() - start) / N_QUERIES * 1000
    print(f"nprobe={nprobe:>2}: {ms:.2f} ms per query | "
          f"checked {searched / N_QUERIES:,.0f} questions on average | "
          f"found the true closest match {found}/{N_QUERIES} times")