# Repo Handover — Evidence Persistence & Lead Docs (Airtable migration, repo half)
_Written 2026-07-25 by the Airtable-side session. Target repo: `haytham10/Funnel-Auditor`, branch `uae-track`. Commit this file to `docs/uae-track/` so it travels with the work._
---
## Why this exists, in one paragraph
The UAE CRM is migrating from Notion to Airtable. The Airtable schema is built and verified
(6 tables: Leads, Findings, Touches, Offers, Inboxes, Sources). The migration's real prize is the
**Touches** table — 213 sent emails currently trapped as prose inside Notion page bodies, which is
why "reply → call = 0/9" is currently undiagnosable. Two sessions are splitting the work:
| Session | Owns | Has |
|---|---|---|
| **Airtable session** (not you) | Airtable schema, Notion → Airtable record migration, all Airtable writes | Airtable MCP + Notion MCP |
| **You (Claude Code)** | The repo: tooling, lead docs, evidence promotion, re-walks | Repo write, Notion MCP, the CLI + tests |
**Do not write to Airtable. Do not write to the Notion CRM.** The other session is mid-migration
and holds the reconciliation counts; concurrent writes would corrupt them. You read Notion, you
write the repo.
---
## The problem you're solving
`.gitignore` has always contained `*.png`, `screenshots/`, and `evidence/`.
**No screenshot has ever been committed to this repo.** Every piece of visual evidence for all 368
leads existed only on the machine that ran the walk. Haytham works on cloud — those containers are
gone. Every `VISION PASS: COMPLETE — N of N required images confirmed read` line sitting in a Notion
page body refers to images that **no longer exist anywhere**.
That is an ongoing loss, not a historical one: it's still happening on every new walk. R1 and R2
stop it.
---
## R1 · Verify the groundwork actually works — **do this first**
Haytham has (as of 2026-07-25) committed a `.gitignore` change and `docs/leads/_TEMPLATE.md`.
The synced snapshot available to the other session was stale, so **verify against the live repo.**
Expected `.gitignore` shape:
```gitignore
*.png
evidence/
screenshots/
# promoted, permanent lead evidence — the ONLY images that get committed
!docs/leads/**/*.png
!docs/leads/**/*.jpg
!docs/leads/**/*.webp
```
**Smoke test it.** A gitignore negation that silently fails means every promoted screenshot is
silently dropped, and you'd find out months later with nothing recoverable:
```bash
mkdir -p docs/leads/_smoke/evidence && touch docs/leads/_smoke/evidence/x.png
git check-ignore -v docs/leads/_smoke/evidence/x.png   # expect exit 1 — NOT ignored
touch evidence/_smoke.png
git check-ignore -v evidence/_smoke.png                # expect exit 0 — ignored
rm -rf docs/leads/_smoke evidence/_smoke.png
```
(`git check-ignore` exits **0 when the path IS ignored**, 1 when it isn't.)
**Acceptance:** first command exits 1, second exits 0. If the negation doesn't hold, fix it before
anything else — note that a directory excluded by gitignore can never have its children
re-included, so `evidence/` must stay excluded and `docs/leads/` must never be excluded as a
directory.
---
## R2 · Build `promote-evidence`
**New command.** Everything else depends on this existing.
```bash
python main.py promote-evidence <slug> --kind finding --rank N --source <path>
python main.py promote-evidence <slug> --kind hook --source <path>
```
**Behavior:**
- `--source` resolves relative to `evidence/<slug>/` (e.g. `screenshots/foo_desktop.png`, `hook/1.png`)
- Resize so the longest edge is ≤ **1600px**, strip metadata, compress
- Write to `docs/leads/<slug>/evidence/finding-<rank>.png` or `.../hook.png`
- **Refuse to overwrite** an existing file unless `--force`. Evidence is append-only; a silent
  overwrite destroys the proof of an earlier finding.
- Print both the repo-relative path and the public GitHub URL (scheme in R5)
**Dependency:** needs Pillow. Follow the existing convention in `main.py` — `audit.crawler` is
lazily imported inside the commands that need it "so the gate commands keep working on machines
without the crawl dependencies installed." Do the same here; `crm-gate` and `send-cap` must keep
working without Pillow installed.
**Why 1600px + compression, not Git LFS:** full-page PNGs run 0.5–3 MB. ~313 promoted images
unoptimized is 150–900 MB, which is LFS territory. Optimized they're 150–400 KB → ~50–125 MB total,
which plain git handles fine, with no clone-time LFS dependency. Revisit only past ~500 MB.
**Acceptance:** produces a file under ~400 KB at the correct path; a second run without `--force`
refuses; `crm-gate` still runs on a machine without Pillow.
---
## R3 · Batch slug manifest — **this is the contract between the two sessions**
The Airtable session needs slugs to build `Walk Doc` and `Evidence Path` URLs. It cannot guess
them — `main.py slug` is the only authority, and promoted evidence must line up with the working
folder it came from.
Read the **122 non-Disqualified** leads from the Notion CRM
(`collection://5efbdd9b-1e19-468c-96db-f94a525846e0`, `Status != "Disqualified"`) and emit
`docs/leads/_manifest.json`:
```json
[
  {
    "name": "Avneet Kohli",
    "notion_page_id": "39f382c8-4585-81c6-a7b1-c4cf53682ea8",
    "slug": "avneet-kohli",
    "status": "Offer Sent",
    "walk_doc_url": "https://github.com/haytham10/Funnel-Auditor/blob/uae-track/docs/leads/avneet-kohli.md",
    "evidence_url": "https://github.com/haytham10/Funnel-Auditor/tree/uae-track/docs/leads/avneet-kohli/evidence"
  }
]
```
**Slugs must come from `audit.urls.slugify`** — the same function `walk` and `ingest` use. Don't
reimplement.
**Check for collisions explicitly.** Two coaches with the same name produce the same slug and would
silently overwrite each other's docs and evidence. If any collision exists, disambiguate (append a
short domain fragment) and **say so in the PR description** — the other session needs to know.
**Acceptance:** 122 entries, zero duplicate slugs, every slug reproducible via `python main.py slug "<name>"`.
**→ Hand this file back as soon as it exists.** It unblocks the Airtable side.
---
## R4 · Raw page-body archives — **before any parsing, no exceptions**
Haytham's explicit instruction was "don't lose any data." Parsing prose into structured Touch rows
is the one genuinely lossy step in this migration.
For each of the 122 leads: fetch the Notion page body via MCP and write it **verbatim** to
`docs/leads/<slug>.raw.md`, with a header:
```markdown
<!--
VERBATIM ARCHIVE — DO NOT EDIT
Source: Notion page <page-id>
Fetched: 2026-07-25T14:03:00Z
This is the unparsed original. The structured copy lives in Airtable
(Touches / Leads). If a parse is ever wrong, this is the source of truth.
-->
```
Body content below, **byte-for-byte unmodified**. No reformatting, no cleanup, no markdown
normalisation. If Notion's escaping looks ugly (`\$`, auto-linked domains), leave it ugly.
**Acceptance:** 122 `.raw.md` files; spot-check three against the live Notion page and confirm the
body is identical.
---
## R5 · Generate walk docs
From each archived page body, write `docs/leads/<slug>.md` following `docs/leads/_TEMPLATE.md`.
**Section mapping:**
| Notion page body | Walk doc |
|---|---|
| `## Overview` | → `## Overview` |
| `## Funnel Walk` | → `## Funnel Walk` |
| `## Evidence` | → `## Evidence` (keep the literal `VISION PASS:` line verbatim — never paraphrase) |
| Gate reasoning | → `## Gates` |
| `## Findings Bank` | → `## Findings — reasoning` |
| `## SMYKM Hook` | → `## SMYKM Hook` |
| `## Email Thread Log` | **DROPPED** → becomes Airtable `Touches` rows (preserved in `.raw.md`) |
| `## Price Discovery` | **DROPPED** → becomes Airtable Lead fields (preserved in `.raw.md`) |
**The Findings section holds reasoning, not fields.** Rank, status, depth, type and innocent
explanation are canonical in Airtable's `Findings` table. Duplicating them in prose guarantees
drift. Write *why* a finding is deep vs shallow, what it costs them, what was ruled out.
**Airtable record URL:** leave the placeholder line as
`<!-- airtable-record: TBD -->`. The Airtable session will hand back a name → recordId manifest
after Wave 1, and a later pass backfills these. Don't block on it.
**Acceptance:** 122 walk docs; none contains an email thread log or a verbatim price-discovery
answer; every `VISION PASS:` line is quoted literally.
---
## R6 · Re-walk the 7 live/warm leads
These are the only leads whose evidence is worth regenerating. The other 115 (and all 246
disqualified) are not worth the crawl budget.
| Lead | Status | Touch # |
|---|---|---|
| Avneet Kohli | Offer Sent | 6 |
| Rita Baki | Offer Sent | 5 |
| Ben Pringle | Reply Received | 5 |
| William Brown | Reply Received | 4 |
| Lisa Hugo | Reply Received | 4 |
| Lucia Csobonyei | Reply Received | 4 |
| Lee Harris | Price Discovery Sent | 3 |
For each: run the walk, complete the vision gate, then `promote-evidence` the screenshot proving
each banked finding.
### ⚠️ The honesty rule on re-walks
**A re-walk shows the funnel as it is TODAY, not as it was when the finding was made.**
If the coach has since fixed the leak, the screenshot will not show it. Do **not**:
- promote a screenshot that doesn't actually show the finding
- backdate the evidence
- describe today's capture as if it were the original
Instead, for each finding, record one of:
- **Still present** → promote the image, note the re-walk date in the walk doc
- **No longer present** → promote nothing, write
  `Finding no longer visible as of <date> — original evidence lost (pre-persistence)` in the walk
  doc's Findings section, and **list it in the PR description** so the Airtable session can set
  `Findings.Still Present = false`
This isn't bookkeeping. If Avneet fixed her checkout, the opener built on that finding is now
factually wrong and must not be sent. The re-walk is also a live re-verification of seven warm
threads — treat a disappeared finding as a real signal, not an inconvenience.
**Acceptance:** 7 leads processed; every finding either has promoted evidence or an explicit
absence note; nothing backdated.
---
## Do NOT do (this sprint)
- **Don't touch `audit/crm_gate.py`, `audit/dashboard.py`, `audit/inboxes.py`, `audit/send_cap.py`,
  or any skill.** That's Phase 6, and it is gated on the Wave 1 data migration reconciling first.
  Changing storage and logic in the same sprint destroys the regression net.
- **Don't write to Airtable.** No connector needed here; the other session owns every Airtable write.
- **Don't write to the Notion CRM.** Read only. The other session is counting rows for
  reconciliation and a concurrent write corrupts the gate.
- **Don't delete anything under `evidence/`.** It's the source material for promotion, and for the
  historical leads it's the only copy that might still exist locally.
- **Don't commit unoptimized images.** Every promoted file goes through `promote-evidence`.
- **Don't migrate the 246 disqualified leads.** They're Wave 2, and they're blocked on a
  disqualification-reason extraction that hasn't run yet.
---
## Suggested PR plan
Cut from `uae-track`; let PRs take the default base.
| PR | Contents | Depends on |
|---|---|---|
| **1 — `repo/evidence-promotion`** | R1, R2 | — |
| **2 — `repo/lead-manifest`** | R3 | PR 1 |
| **3 — `repo/lead-archives`** | R4 | PR 2 |
| **4 — `repo/lead-docs`** | R5 | PR 3 |
| **5 — `repo/rewalk-warm`** | R6 | PRs 1–4 |
**Ship PR 2 as early as you can** — `_manifest.json` is what unblocks the Airtable session.
---
## Verification before you open anything
1. Confirm the gitignore negation holds (R1 smoke test) — everything downstream is worthless if it doesn't.
2. Confirm `python main.py crm-gate send --help` still works on a machine without Pillow.
3. Run the existing test suite; nothing here should touch it, so a failure means you strayed out of scope:
   `python -m pytest tests/ -q`
4. Confirm the count: 122 non-disqualified leads in Notion. If it isn't 122, **stop and report** —
   the pipeline moved since 2026-07-25 and the Airtable session's reconciliation numbers need updating.
---
## Facts you'll need
- **Repo is public.** GitHub blob/tree URLs resolve without auth, safe to paste anywhere.
- **Branch:** `uae-track` (repo default).
- **URL scheme:** `blob` for files, `tree` for directories, pinned to the branch (not a commit SHA) —
  evidence is append-only by convention. Pin to a SHA only if a specific link ever needs to be immutable proof.
- **Notion CRM data source:** `collection://5efbdd9b-1e19-468c-96db-f94a525846e0`
- **Never touch the parenting DB:** `c6209e29-55ef-4781-b735-73b2a254e34f`
- **Current pipeline shape:** 368 leads total · 246 Disqualified · 122 in scope · 213 touches ·
  263 findings · 109 resolved hooks · 2 leads who asked for a price (Avneet, Rita)

---

## Repo-session execution notes (added 2026-07-25, same day)

All six items (R1–R6) shipped on `claude/evidence-persistence-lead-docs-wrenyt` rather than the
five separate PRs suggested above — the session's branch instructions designated one branch for
this whole handover, so everything landed there as a sequence of commits instead. See
`docs/journal.md`'s 2026-07-25 "Repo half of the Airtable migration" entry for the full rundown,
including the three findings (Rita Baki Rank 1 + Rank 2, Ben Pringle Rank 1) that R6's honesty rule
caught as dead. Manifest collision note: `docs/leads/_manifest.json` disambiguates the one real
slug collision (two "Dan Chadwick" CRM rows, identical Site URL) with a page-id suffix rather than
a domain fragment, since both rows share a domain.
