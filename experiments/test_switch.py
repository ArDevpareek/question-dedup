import sys
from pathlib import Path
# The core modules live one folder up, in the project root, so add it to the import path.
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from generator import load_detector

candidates = [
    "Define reflection of light.",
    "Why is the word AMBULANCE written in reverse on ambulances?",
    "How many images are formed by two plane mirrors kept at 90 degrees?",
    "What is the focal length of a plane mirror?",
]

brute = load_detector()
clustered = load_detector(switch_size=0, nprobe=1)

for text in candidates:
    a = brute.check(text)
    b = clustered.check(text)
    print(f"\n{text}")
    print(f"   {a['search']:<12}: {a['label']:<18} best {a['score']:.2f} {a['matches']}  (checked {a['checked']})")
    print(f"   {b['search']:<12}: {b['label']:<18} best {b['score']:.2f} {b['matches']}  (checked {b['checked']})")