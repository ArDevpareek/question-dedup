import numpy as np
from normalize import make_hash
from embed import embed
from judge import judge

import re

def has_numbers(text):
    return bool(re.search(r"\d", text))

DUP_THRESHOLD = 1.01
NEW_THRESHOLD = 0.50
TOP_K = 3
CLUSTER_SWITCH_SIZE = 50_000
NPROBE = 5

def make_result(label, matches, score, decided_by, reason="", search="", checked=0):
    return {"label": label, "matches": matches, "score": score,
            "decided_by": decided_by, "reason": reason,
            "search": search, "checked": checked}

class DuplicateDetector:
    def __init__(self, switch_size=CLUSTER_SWITCH_SIZE, nprobe=NPROBE):
        self.ids = []
        self.texts = []
        self.hashes = {}
        self.vectors = None
        self.centroids = None
        self.cluster_ids = []
        self.members = {}
        self.switch_size = switch_size
        self.nprobe = nprobe

    def nearest_cluster(self, vec):
        if self.centroids is None:
            return None
        return int(np.argmax(self.centroids @ vec))

    def remember_cluster(self, row, cid):
        self.cluster_ids.append(cid)
        if cid is not None:
            self.members.setdefault(cid, []).append(row)

    def load(self, ids, texts, vectors, cluster_ids=None, centroids=None):
        self.ids = list(ids)
        self.texts = list(texts)
        self.vectors = vectors
        self.centroids = centroids
        self.hashes = {}
        for qid, text in zip(self.ids, self.texts):
            self.hashes.setdefault(make_hash(text), []).append(qid)
        self.cluster_ids = []
        self.members = {}
        if cluster_ids is None:
            cluster_ids = [None] * len(self.ids)
        for row, cid in enumerate(cluster_ids):
            if cid is None and centroids is not None:
                cid = self.nearest_cluster(vectors[row])
            self.remember_cluster(row, cid)

    def add(self, qid, text, vec=None):
        row = len(self.ids)
        self.ids.append(qid)
        self.texts.append(text)
        self.hashes.setdefault(make_hash(text), []).append(qid)
        if vec is None:
            vec = embed([text])[0]
        if self.vectors is None:
            self.vectors = vec.reshape(1, -1)
        else:
            self.vectors = np.vstack([self.vectors, vec.reshape(1, -1)])
        cid = self.nearest_cluster(vec)
        self.remember_cluster(row, cid)
        return vec, cid

    def search(self, vec, top_k=TOP_K):
        use_clusters = self.centroids is not None and len(self.ids) >= self.switch_size
        if use_clusters:
            nearest = np.argsort(-(self.centroids @ vec))[:self.nprobe]
            rows = np.array([r for c in nearest for r in self.members.get(int(c), [])], dtype=int)
            mode = "clustered"
            if len(rows) == 0:
                return [], mode, 0
            scores = self.vectors[rows] @ vec
        else:
            rows = np.arange(len(self.ids))
            mode = "brute force"
            scores = self.vectors @ vec
        best = np.argsort(-scores)[:top_k]
        neighbours = [(self.ids[rows[i]], self.texts[rows[i]], float(scores[i])) for i in best]
        return neighbours, mode, len(rows)

    def check(self, text):
        h = make_hash(text)
        if h in self.hashes:
            return make_result("exact_duplicate", self.hashes[h], 1.0, "exact")
        if self.vectors is None:
            return make_result("new", [], None, "empty store")

        vec = embed([text])[0]
        neighbours, mode, checked = self.search(vec)
        if not neighbours:
            return make_result("new", [], None, "embedding", search=mode, checked=checked)
        best_id, best_text, best_score = neighbours[0]

        if best_score >= DUP_THRESHOLD:
            return make_result("semantic_duplicate", [best_id], best_score, "embedding",
                               search=mode, checked=checked)
        if best_score < NEW_THRESHOLD:
            return make_result("new", [], best_score, "embedding",
                               search=mode, checked=checked)

        try:
            verdict = judge(text, neighbours)
        except Exception as e:
            return make_result("review", [best_id], best_score, "judge failed",
                               reason=str(e), search=mode, checked=checked)

        v = verdict.get("verdict")
        reason = verdict.get("reason", "")
        if v == "duplicate":
            dup_of = verdict.get("duplicate_of") or best_id
            dup_text = self.texts[self.ids.index(dup_of)] if dup_of in self.ids else best_text
            if has_numbers(text) != has_numbers(dup_text):
                return make_result("review", [dup_of], best_score, "numbers guard",
                                   reason="Only one question has numbers. " + reason,
                                   search=mode, checked=checked)
            return make_result("semantic_duplicate", [dup_of], best_score, "judge",
                               reason=reason, search=mode, checked=checked)
        if v == "different":
            return make_result("new", [], best_score, "judge",
                               reason=reason, search=mode, checked=checked)
        return make_result("review", [best_id], best_score, "judge",
                           reason=reason, search=mode, checked=checked)