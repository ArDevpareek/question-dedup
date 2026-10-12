import numpy as np

def kmeans(vectors, k, iters=10, seed=0):
    rng = np.random.default_rng(seed)
    start = rng.choice(len(vectors), size=k, replace=False)
    centroids = vectors[start].copy()

    for _ in range(iters):
        assign = np.argmax(vectors @ centroids.T, axis=1)
        for c in range(k):
            members = vectors[assign == c]
            if len(members) > 0:
                centre = members.mean(axis=0)
                centroids[c] = centre / np.linalg.norm(centre)

    assign = np.argmax(vectors @ centroids.T, axis=1)
    return centroids, assign

class ClusteredIndex:
    def __init__(self, vectors, k, iters=10):
        self.vectors = vectors
        self.centroids, assign = kmeans(vectors, k, iters)
        self.members = [np.where(assign == c)[0] for c in range(k)]

    def search(self, query, nprobe, top_k=3):
        centre_scores = self.centroids @ query
        nearest = np.argsort(-centre_scores)[:nprobe]
        rows = np.concatenate([self.members[c] for c in nearest])
        scores = self.vectors[rows] @ query
        best = np.argsort(-scores)[:top_k]
        return rows[best], scores[best], len(rows)