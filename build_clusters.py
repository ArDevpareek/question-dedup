import numpy as np
from store import create_table, load_all_with_embeddings, save_centroids, save_cluster_ids
from backfill import fill_missing_embeddings
from clusters import kmeans

def choose_k(n):
    return max(2, int(round(np.sqrt(n))))

def build_clusters():
    create_table()
    fill_missing_embeddings()
    ids, texts, vectors, _ = load_all_with_embeddings()
    if vectors is None or len(ids) < 4:
        print("Not enough questions to build clusters yet.")
        return

    k = choose_k(len(ids))
    centroids, assign = kmeans(vectors, k)
    save_centroids(centroids)
    save_cluster_ids(ids, assign)

    print(f"Built {k} clusters from {len(ids)} questions\n")
    for c in range(k):
        rows = np.where(assign == c)[0]
        print(f"Cluster {c} ({len(rows)} questions)")
        for r in rows[:5]:
            print(f"   {ids[r]}: {texts[r]}")
        if len(rows) > 5:
            print(f"   ... and {len(rows) - 5} more")
        print()

if __name__ == "__main__":
    build_clusters()