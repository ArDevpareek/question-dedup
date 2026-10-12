from llm import ask_llm_json

JUDGE_PROMPT = """You are checking an exam question bank for duplicates.

A NEW question is a DUPLICATE of an existing question if a student would need the
same knowledge and would give the same kind of answer to both.

Treat these as DUPLICATES:
- the same question asked in different words
- the same calculation where only the numbers are changed
- the same question with a small extra part added, such as asking for an example,
  a reason, or a diagram

Treat these as DIFFERENT:
- the same topic but a different concept or a different kind of answer
  (for example a definition versus a calculation, or one law versus another)
- questions about two different things of the same kind, or about opposite cases.
  Changing a single key word can change the meaning completely.
- a question that asks what something is (a definition or explanation) versus a
  question that gives numbers and asks to calculate it. Adding numbers to a
  definition question turns it into a calculation; this is not a small extra part.
  For example "What is speed?" versus "A car travels 100 km in 2 hours. Find its speed."

Answer "review" if the new question is too vague to decide,
for example if a key word could have more than one meaning and the question gives no context.

Existing questions:
{existing}

New question:
{candidate}

Reply with JSON only, in this format:
{{"verdict": "duplicate" or "different" or "review", "duplicate_of": "<question id or null>", "reason": "<one short sentence>"}}
"""

def judge(candidate, neighbours):
    existing = "\n".join(f"- [{nid}] {ntext}" for nid, ntext, _ in neighbours)
    prompt = JUDGE_PROMPT.format(existing=existing, candidate=candidate)
    return ask_llm_json(prompt)