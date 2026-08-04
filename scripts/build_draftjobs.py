"""Build one draft job file per verified-hook lead for stage 4, so the
orchestrator hands a path rather than a payload. Prints the wave assignment only.
"""
import json

W = "work"

research = {r["slug"]: r for r in json.load(open(f"{W}/researched.json"))}
anchors = json.load(open(f"{W}/anchors.json"))
drops = ("observations", "notes")

jobs, skipped = [], []
for slug, r in sorted(research.items()):
    if r.get("hook_verified") != "verified":
        continue
    email = r.get("email") or ""
    anc = anchors.get(email)
    if not anc:
        skipped.append((slug, "no dealt anchors"))
        continue
    jobs.append(
        {
            "slug": slug,
            "name": r.get("name"),
            "hook": {
                "line": r.get("hook"),
                "quote": r.get("hook_quote"),
                "hook_type": r.get("hook_type"),
                "source_url": r.get("hook_source_url"),
                "published_at": r.get("hook_date"),
            },
            "research": {k: v for k, v in r.items() if k not in drops},
            "notes": (r.get("notes") or [])[:4],
            "anchors": anc,
        }
    )

for j in jobs:
    with open(f"{W}/draftjob-{j['slug']}.json", "w") as fh:
        json.dump(j, fh, indent=2, ensure_ascii=False)

print(f"DRAFT JOBS: {len(jobs)} lead(s), {len(skipped)} excluded")
for k, why in skipped:
    print(f"  excluded {k}: {why}")
for i in range(0, len(jobs), 6):
    print(f"wave {i//6+1}: " + " ".join(j["slug"] for j in jobs[i : i + 6]))
