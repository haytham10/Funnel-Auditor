"""Render draft JSON as the recipient would read it, without running export.

`export` writes preview.txt but only for drafts that pass, and it is a stage
away. This renders any draft on disk so a wave can be read before it is
repaired or shipped.
"""
import json
import sys
import glob
import os

W = "work"
ORDER = ("hook", "identity", "offer", "cta", "ps")


def render(slug):
    with open(f"{W}/draft-{slug}.json") as fh:
        d = json.load(fh)
    beats = d["beats"]
    body = "\n\n".join(beats[b] for b in ORDER if beats.get(b))
    verdict = ""
    vpath = f"{W}/verdict-{slug}.json"
    if os.path.exists(vpath):
        with open(vpath) as fh:
            v = json.load(fh)
        problems = v.get("problems") or []
        beatsf = ",".join(sorted({p.get("beat", "?") for p in problems}))
        verdict = f"{v.get('verdict', '?')}" + (f" on {beatsf}" if beatsf else "")
    print("=" * 72)
    print(f"{slug}   [{verdict}]")
    print(f"subject: {d['subject']}")
    print("-" * 72)
    print(body)
    print()
    print("Haytham")
    print()


if __name__ == "__main__":
    args = sys.argv[1:]
    if args:
        slugs = args
    else:
        slugs = sorted(os.path.basename(p)[6:-5]
                       for p in glob.glob(f"{W}/draft-*.json"))
    for s in slugs:
        render(s)
