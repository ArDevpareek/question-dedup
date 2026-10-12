from store import create_table, get_missing_embeddings, save_embeddings
from embed import embed

def fill_missing_embeddings():
    rows = get_missing_embeddings()
    if not rows:
        return 0
    ids = [r[0] for r in rows]
    texts = [r[1] for r in rows]
    vectors = embed(texts)
    save_embeddings(ids, vectors)
    return len(ids)

if __name__ == "__main__":
    create_table()
    n = fill_missing_embeddings()
    print(f"Filled embeddings for {n} questions")