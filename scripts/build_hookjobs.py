"""Build one hook job file per lead for stage 3b, so the orchestrator hands a
path rather than a payload. Prints the wave assignment only."""
import json
import os
import re
import sys

W = "work"


def slug(name):
    return re.sub(r"[^a-z0-9]+", "-", (name or "").lower()).strip("-")


sel = {s["lead_key"]: s for s in json.load(open(f"{W}/select.json"))["selections"]}
anchors = json.load(open(f"{W}/anchors.json"))
addresses = json.load(open(f"{W}/addresses.json"))
plans = json.load(open(f"{W}/plan.json"))["plans"]
draftable = json.load(open(f"{W}/draftable.json"))

plan_by = {}
for p in plans:
    for k in (p.get("lead_key"), slug(p.get("name", "")), p.get("email")):
        if k:
            plan_by[k] = p

jobs, skipped = [], []
for lead in draftable:
    email = lead.get("email") or lead.get("contact_email") or ""
    name = lead.get("name") or lead.get("full_name") or ""
    key = lead.get("lead_key") or slug(name)
    entry = sel.get(key) or sel.get(slug(name))
    addr = addresses.get(email, {})
    anc = anchors.get(email, {})
    reachable = bool(email) and addr.get("reachable", True) is not False
    if not entry or not entry.get("shortlist"):
        skipped.append((key, "no shortlist"))
        continue
    if not reachable:
        skipped.append((key, "unreachable"))
        continue
    jobs.append(
        {
            "lead_key": key,
            "slug": slug(name) or key,
            "name": name,
            "email": email,
            "hook_room": anc.get("hook_room"),
            "selection": entry,
            "plan": plan_by.get(key) or plan_by.get(slug(name)) or plan_by.get(email),
        }
    )

for j in jobs:
    with open(f"{W}/hookjob-{j['slug']}.json", "w") as fh:
        json.dump(j, fh, indent=2)

print(f"JOBS: {len(jobs)} lead(s), {len(skipped)} excluded")
for k, why in skipped:
    print(f"  excluded {k}: {why}")
for i in range(0, len(jobs), 6):
    wave = jobs[i : i + 6]
    print(f"wave {i//6+1}: " + " ".join(j["slug"] for j in wave))
