"""Appends new jokes to docs/jokes.json, skipping any the feed already has.

    python tools/add_jokes.py new-jokes.txt

One joke per line as `setup | punchline`. A joke counts as a duplicate when its setup, or its setup and punchline
together, match an existing one after normalize.norm (case, spacing and punctuation ignored). New jokes get the next ids,
so ids already on people's phones never change. Prints how many were added and lists the skipped ones.
"""
import json
import sys
from datetime import date
from pathlib import Path

from normalize import norm

root = Path(__file__).resolve().parent.parent
feed_path = root / "docs" / "jokes.json"


def main(src):
    feed = json.loads(feed_path.read_text(encoding="utf-8"))
    jokes = feed["jokes"]
    setups = {norm(j["s"]) for j in jokes}
    whole = {norm(j["s"] + " " + j["p"]) for j in jokes}
    next_id = max(j["id"] for j in jokes) + 1
    added, skipped = [], []
    for line in Path(src).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        if "|" not in line:
            skipped.append((line, "no | separator"))
            continue
        s, p = (x.strip() for x in line.split("|", 1))
        if not s or not p:
            skipped.append((line, "empty setup or punchline"))
            continue
        if norm(s) in setups or norm(s + " " + p) in whole:
            skipped.append((s, "duplicate"))
            continue
        jokes.append({"id": next_id, "s": s, "p": p})
        setups.add(norm(s))
        whole.add(norm(s + " " + p))
        added.append(next_id)
        next_id += 1
    if added:
        feed["version"] = feed.get("version", 1) + 1
        feed["updated"] = date.today().isoformat()
        feed_path.write_text(json.dumps(feed, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"added {len(added)} jokes (ids {added[0]}-{added[-1]})" if added else "added 0 jokes")
    print(f"feed now has {len(jokes)} jokes")
    for text, why in skipped:
        print(f"skipped ({why}): {text}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
