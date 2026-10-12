import json
import time
from google import genai

MODEL = "gemini-3.5-flash-lite"
RETRY_WAITS = [15, 30, 45, 60]
TEMPORARY_ERRORS = ("429", "RESOURCE_EXHAUSTED", "503", "UNAVAILABLE")
_client = None

def get_client():
    global _client
    if _client is None:
        _client = genai.Client()
    return _client

def is_temporary(message):
    if "PerDay" in message:
        return False
    return any(t in message for t in TEMPORARY_ERRORS)

def ask_llm_json(prompt, temperature=0):
    for attempt in range(len(RETRY_WAITS) + 1):
        try:
            response = get_client().models.generate_content(
                model=MODEL,
                contents=prompt,
                config={"response_mime_type": "application/json", "temperature": temperature},
            )
            break
        except Exception as e:
            message = str(e)
            if attempt == len(RETRY_WAITS) or not is_temporary(message):
                raise
            wait = RETRY_WAITS[attempt]
            print(f"   LLM busy ({message.split('.')[0][:60]}), retry {attempt + 1}/{len(RETRY_WAITS)} in {wait}s")
            time.sleep(wait)
    return json.loads(response.text)
