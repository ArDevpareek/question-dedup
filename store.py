import sqlite3
import json
import numpy as np
from normalize import normalize_text, make_hash

DB_PATH = "questions.db"

def get_connection():
    return sqlite3.connect(DB_PATH)

def create_table():
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS questions (
            id              TEXT PRIMARY KEY,
            text            TEXT NOT NULL,
            normalized_text TEXT NOT NULL,
            text_hash       TEXT NOT NULL,
            tags            TEXT,
            embedding       BLOB,
            cluster_id      INTEGER
        )
    """)
    columns = [row[1] for row in conn.execute("PRAGMA table_info(questions)")]
    if "embedding" not in columns:
        conn.execute("ALTER TABLE questions ADD COLUMN embedding BLOB")
    if "cluster_id" not in columns:
        conn.execute("ALTER TABLE questions ADD COLUMN cluster_id INTEGER")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS centroids (
            cluster_id INTEGER PRIMARY KEY,
            vector     BLOB NOT NULL
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_hash ON questions (text_hash)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_cluster ON questions (cluster_id)")
    conn.commit()
    conn.close()

def vec_to_blob(vec):
    return np.asarray(vec, dtype=np.float32).tobytes()

def blob_to_vec(blob):
    return np.frombuffer(blob, dtype=np.float32)

def add_question(qid, text, tags, embedding=None, cluster_id=None):
    blob = vec_to_blob(embedding) if embedding is not None else None
    conn = get_connection()
    conn.execute(
        "INSERT OR IGNORE INTO questions (id, text, normalized_text, text_hash, tags, embedding, cluster_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (qid, text, normalize_text(text), make_hash(text), json.dumps(tags), blob, cluster_id)
    )
    conn.commit()
    conn.close()

def find_by_hash(text_hash):
    conn = get_connection()
    rows = conn.execute(
        "SELECT id, text FROM questions WHERE text_hash = ?",
        (text_hash,)
    ).fetchall()
    conn.close()
    return rows

def get_all_questions():
    conn = get_connection()
    rows = conn.execute("SELECT id, text, tags FROM questions").fetchall()
    conn.close()
    return [{"id": r[0], "text": r[1], "tags": json.loads(r[2])} for r in rows]

def get_missing_embeddings():
    conn = get_connection()
    rows = conn.execute("SELECT id, text FROM questions WHERE embedding IS NULL").fetchall()
    conn.close()
    return rows

def save_embeddings(ids, vectors):
    conn = get_connection()
    conn.executemany(
        "UPDATE questions SET embedding = ? WHERE id = ?",
        [(vec_to_blob(v), qid) for qid, v in zip(ids, vectors)]
    )
    conn.commit()
    conn.close()

def load_all_with_embeddings():
    conn = get_connection()
    rows = conn.execute(
        "SELECT id, text, embedding, cluster_id FROM questions WHERE embedding IS NOT NULL"
    ).fetchall()
    conn.close()
    ids = [r[0] for r in rows]
    texts = [r[1] for r in rows]
    cluster_ids = [r[3] for r in rows]
    if not rows:
        return ids, texts, None, cluster_ids
    vectors = np.vstack([blob_to_vec(r[2]) for r in rows])
    return ids, texts, vectors, cluster_ids

def save_cluster_ids(ids, cluster_ids):
    conn = get_connection()
    conn.executemany(
        "UPDATE questions SET cluster_id = ? WHERE id = ?",
        [(int(c), qid) for qid, c in zip(ids, cluster_ids)]
    )
    conn.commit()
    conn.close()

def save_centroids(centroids):
    conn = get_connection()
    conn.execute("DELETE FROM centroids")
    conn.executemany(
        "INSERT INTO centroids (cluster_id, vector) VALUES (?, ?)",
        [(i, vec_to_blob(c)) for i, c in enumerate(centroids)]
    )
    conn.commit()
    conn.close()

def load_centroids():
    conn = get_connection()
    rows = conn.execute("SELECT vector FROM centroids ORDER BY cluster_id").fetchall()
    conn.close()
    if not rows:
        return None
    return np.vstack([blob_to_vec(r[0]) for r in rows])