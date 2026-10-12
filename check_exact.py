from normalize import normalize_text, make_hash
from store import find_by_hash, get_connection

def check_exact(new_text):
    matches = find_by_hash(make_hash(new_text))
    return [m[0] for m in matches]

candidates = [
    "Define the reflection of light.",
    "DEFINE the reflection of light!!",
    "   define   the   reflection of light ",
    "What is the angle of reflection",
    "Define the refraction of light.",
    "The angle of incidence is 45°. What is the angle of reflection?",
    "Define reflection of light.",
]

for c in candidates:
    ids = check_exact(c)
    print(repr(c))
    print("   cleaned :", normalize_text(c))
    print("   matches :", ids if ids else "none")

print("\nDuplicates already inside the store:")
conn = get_connection()
rows = conn.execute("""
    SELECT GROUP_CONCAT(id), COUNT(*)
    FROM questions
    GROUP BY text_hash
    HAVING COUNT(*) > 1
""").fetchall()
conn.close()
for ids, count in rows:
    print(f"   {ids}  ({count} copies)")