"""One-time: turns seed-jokes.txt into docs/jokes.json with stable ids. Later additions append via add_jokes.py."""
import json, re, sys
from pathlib import Path
from normalize import norm

DROP = {
    "How do you make a Kleenex dance?", "Why did the scarecrow get promoted?", "Why did the old man fall in the well?",
    "Why couldn't the bicycle stand up by itself?", "How do you throw a party in space?", "A cheeseburger walks into a bar.",
    "What did one hat say to the other?", "What did the hat say to the hat rack?", "Why did the old man install a knocker on his door?",
    "I bought shoes from a drug dealer.", "What do you call a nun in a wheelchair?", "Why did the grape stop in the middle of the road?",
    "What did the mustard say to the ketchup?", "Why did the scarecrow become a motivational speaker?", "What do you call a dog that's a great boxer?",
    "Why did the vampire get a job at the blood bank?", "Why do melons never get lost?", "Why did the crayon get promoted?",
}
root = Path(__file__).resolve().parent.parent
jokes, seen = [], set()
for line in (root / "tools" / "seed-jokes.txt").read_text(encoding="utf-8").splitlines():
    if not line.strip(): continue
    s, p = (x.strip() for x in line.split("|", 1))
    if s in DROP: continue
    k = norm(s + " " + p)
    if k in seen or norm(s) in {norm(j["s"]) for j in jokes}:
        print("dupe:", s); continue
    seen.add(k)
    jokes.append({"id": len(jokes) + 1, "s": s, "p": p})
out = {"version": 1, "updated": "2026-10-21", "jokes": jokes}
(root / "docs" / "jokes.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print(len(jokes), "jokes")
