import time
import numpy as np
from llm import ask_llm_json
from embed import embed
from detector import DuplicateDetector, CLUSTER_SWITCH_SIZE, NPROBE
from store import create_table, load_all_with_embeddings, load_centroids, add_question
from backfill import fill_missing_embeddings

CONTEXT_K = 15
OVERSAMPLE = 2
MAX_ROUNDS = 3
BATCH_SIZE = 10
MAX_REJECTED_IN_PROMPT = 10
SHOW_CONTEXT = True
CONTEXT_SKIP_SIM = 0.88

GEN_PROMPT = """You are writing exam questions on the topic: {topic}

These questions ALREADY EXIST in the question bank:
{existing}

These questions were ALREADY SUGGESTED earlier and REJECTED as duplicates. Do not suggest them again:
{rejected}

Write {n} NEW questions on this topic.

Rules:
- Do not repeat or reword any existing or rejected question.
- Each new question must test a concept or skill that the existing questions do NOT already test.
- Each new question must test something different from the other new questions in your list.
- Use a mix of question types: definition, explanation, numerical, application, comparison, reasoning.
- Each question must be clear and complete on its own, suitable for a school exam.
- Stay strictly within the topic. If the main concept of a question belongs to a different neighbouring topic, do not write it.

Reply with JSON only, in this format:
{{"questions": [{{"concept": "<short name of what it tests>", "type": "<question type>", "question": "<the question>"}}]}}
"""

def load_detector(switch_size=CLUSTER_SWITCH_SIZE, nprobe=NPROBE):
    start = time.time()
    create_table()
    filled = fill_missing_embeddings()
    ids, texts, vectors, cluster_ids = load_all_with_embeddings()
    centroids = load_centroids()
    detector = DuplicateDetector(switch_size=switch_size, nprobe=nprobe)
    detector.load(ids, texts, vectors, cluster_ids, centroids)
    n_clusters = 0 if centroids is None else len(centroids)
    print(f"Loaded {len(ids)} questions and {n_clusters} clusters in {time.time() - start:.2f}s (newly embedded: {filled})")
    return detector

def related_questions(detector, topic, k):
    if detector.vectors is None:
        return []
    topic_vec = embed([topic])[0]
    scores = detector.vectors @ topic_vec

    if detector.centroids is None:
        order = np.argsort(-scores)[:k]
        return [detector.texts[i] for i in order]

    cluster_order = np.argsort(-(detector.centroids @ topic_vec))
    queues = []
    for c in cluster_order:
        rows = sorted(detector.members.get(int(c), []), key=lambda r: -scores[r])
        if rows:
            queues.append(rows)

    picked = []
    while len(picked) < k and any(queues):
        for q in queues:
            if len(picked) >= k:
                break
            while q:
                r = q.pop(0)
                if picked and np.max(detector.vectors[picked] @ detector.vectors[r]) >= CONTEXT_SKIP_SIM:
                    continue
                picked.append(r)
                break
    return [detector.texts[i] for i in picked]

def generate(topic, count, tags):
    detector = load_detector()
    accepted, rejected, review = [], [], []
    checked = 0
    next_num = len(detector.ids) + 1

    for round_no in range(1, MAX_ROUNDS + 1):
        needed = count - len(accepted)
        if needed <= 0:
            break

        existing = related_questions(detector, topic, CONTEXT_K)
        existing_text = "\n".join(f"- {t}" for t in existing) or "(none yet)"
        recent_rejected = rejected[-MAX_REJECTED_IN_PROMPT:]
        rejected_text = "\n".join(f"- {t}" for t in recent_rejected) or "(none yet)"
        ask_for = min(needed * OVERSAMPLE, BATCH_SIZE)
        prompt = GEN_PROMPT.format(topic=topic, existing=existing_text,
                                   rejected=rejected_text, n=ask_for)

        try:
            data = ask_llm_json(prompt, temperature=0.8)
        except Exception as e:
            print(f"\n--- Round {round_no}: generation call failed, stopping ({str(e).split('.')[0][:80]}) ---")
            break
        candidates = data.get("questions", [])
        print(f"\n--- Round {round_no}: sent {len(existing)} existing + {len(recent_rejected)} rejected, asked for {ask_for}, got {len(candidates)} ---")
        if SHOW_CONTEXT and round_no == 1:
            print("  Context sent to the LLM:")
            for t in existing:
                print(f"     - {t}")

        for c in candidates:
            if len(accepted) >= count:
                break
            text = c.get("question", "").strip()
            if not text:
                continue

            checked += 1
            result = detector.check(text)

            if result["label"] == "new":
                qid = f"Q{next_num}"
                next_num += 1
                vec, cid = detector.add(qid, text)
                add_question(qid, text, tags, vec, cid)
                accepted.append(qid)
                print(f"  ACCEPT {qid} [{c.get('concept', '')}] (cluster {cid}, by {result['decided_by']}): {text}")
            elif result["label"] == "review":
                review.append(text)
                print(f"  REVIEW : {text}")
                print(f"           reason: {result['reason']}")
            else:
                rejected.append(text)
                print(f"  REJECT : {text}")
                print(f"           {result['label']} of {result['matches']} (by {result['decided_by']})")

    print(f"\nAccepted: {len(accepted)}   Rejected: {len(rejected)}   Review: {len(review)}   Checked: {checked}")
    return accepted, rejected, review