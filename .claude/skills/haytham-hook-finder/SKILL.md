---
name: haytham-hook-finder
description: Pull real public evidence for an Audit Ready UAE lead — LinkedIn posts, podcast appearances, YouTube, their own About page — and find the SMYKM hook, the one line only this person would recognize (their own framework, a real recent post or episode, a personal update), then write just that line to their Notion page in the UAE Lead CRM. Use this skill WHENEVER Haytham says "find the hook," "SMYKM this," "hook Jane," "add a hook," asks for a stronger opener on a lead that's already Audit Ready, or process-lead/batch-audit reports a lead "held — needs haytham-hook-finder." This is a separate, manually-triggered step from haytham-opener-finder — the walk assigns the lane, finding, and innocent explanation; this skill's only job is the hook, and it must come from real, cited public evidence, never fabricated and never from generic site marketing copy. It is a required gate, not an optional upgrade: no lead gets a Gmail draft until this skill resolves the hook line. As of 2026-07-19 it is draft-first: after resolving (and independently verifying) each hook, it carries the lead through to a HELD Gmail draft for review, so Haytham reviews finished drafts, not bare hooks. It never touches the lane, the finding, or the innocent explanation, and it never sends — the system ends at Gmail drafts.
---

# Haytham Hook Finder — real public evidence → SMYKM hook → one line in Notion

`haytham-opener-finder` classifies the lane and finds the felt-cost finding.
It stops there and writes `SMYKM hook: not run yet — see haytham-hook-finder`
as a placeholder. This skill's entire job is to fill that one line, and to
fill it from something the lead would actually recognize as THEIRS — a real
post, a real episode, a framework name they coined, a personal update —
never from whatever was easiest to find. That's what made the old
search-based hooks read generic: they were built from site marketing copy
and press blurbs, not from what was actually hers.

**The evidence base changed (Jul 13, 2026).** Haytham's own IG account is
permanently gone (banned Jun 22, 2026), so there is no browsing Instagram
as him — but that was an account-safety loss, not a ban on Instagram as a
data source. Read-only public IG data pulled through a no-login third-party
tool (an Apify-style actor that takes a username or URL, no account
required) is fair game for hooks, exactly like LinkedIn, YouTube, and
podcasts. Hook evidence for UAE leads comes from, in rough order of
strength:

1. **LinkedIn posts** — the UAE-specific unlock; UAE professionals actually
   post here. A specific recent post (its real topic, a real line from it,
   a program announcement) is the strongest hook material available.
2. **Podcast appearances** — a specific episode: what she actually said, a
   story she told, a framework she named on air. Show notes and episode
   pages are fetchable; cite the episode.
3. **YouTube** — her own channel or guest appearances. Titles, descriptions,
   and what she says in them.
4. **Her own About page** — her story in her words: the career she left,
   the origin story, the framework name. Weakest of the site sources (it's
   still site copy), but her About-page STORY is hers in a way a headline
   isn't.
5. **Instagram (read-only, no-login pull only)** — a specific recent post,
   a caption, a Reel topic, a personal update she posted publicly. Pull it
   through a no-login third-party actor (username or URL in, public data
   out); never log in, never browse as Haytham, never use his account. Same
   citation discipline as every source above.

This is manual, not automatic — Haytham triggers it by name — but it is
**required** before any Gmail draft. `process-lead` and `haytham-email-draft`
both hard-block on a `SMYKM hook:` line that still says "not run yet," so every
Lane 1 lead sits waiting for this skill to run. As of 2026-07-19 the skill is
**draft-first**: once it resolves the line (a real hook, independently verified,
or a confirmed "no hook found"), it goes straight on to build the held Gmail
draft for that lead (batch mode; see the Input section) — Haytham reviews the
finished drafts, not bare hooks.

**CRM:** `collection://5efbdd9b-1e19-468c-96db-f94a525846e0`. Never the old parenting DB.

---

## Input — single lead, or the whole batch

A Notion lead page (URL or ID) or a name Haytham names. The lead must
already be Audit Ready with a funnel walk written by
`haytham-opener-finder` — if it isn't, say so and point Haytham to that
skill first; don't run a hook search on a lead with no lane verdict yet.

**Batch mode — a verified hook→draft stage (2026-07-14 orchestrator; 2026-07-19
draft-first).** When Haytham says "hook the queue," "draft the queue," "hook them
all," or names several Audit Ready leads, run this as ONE stage that takes each
lead all the way to a held Gmail draft — he reviews the finished drafts, not bare
hooks. Over the shared chassis (`docs/agent-orchestration.md`):

1. Query the CRM for every `Audit Ready` row whose `SMYKM Hook` property is empty
   (hook line still "not run yet"). Size the batch to send headroom
   (`python main.py inbox counts` + `python main.py send-cap status --all`) — a
   draft with nowhere to send this week can wait for the next.
2. Once up front: `pip install -q -r requirements.txt`, then `python main.py apify
   limits` — pass the `near_cap` note into every worker prompt (one check, not
   one per lead).
3. Fan out one **`hook-worker`** per lead, at most 5 running at once. Each runs
   Steps 1-3 (gather cited public evidence, find the hook, self-check the
   citation) and **RETURNS a proposed hook + its citation** (URL/image, the exact
   quote/date, the WORK|LIFE|METRIC label) or "no hook found". A worker does NOT
   write the hook line.
4. **Resolve each lead's `SMYKM hook:` line:**
   - Proposed hook → dispatch a **`hook-verifier`** (the anti-fabrication gate —
     "never fabricate a hook" is the #1 rule and a citation is mechanically
     checkable). In a context that never saw the worker's search it re-fetches
     the cited URL, confirms the quote/date/claim appears (and isn't generic
     marketing copy), then WRITES the line: VERIFIED → the hook; REFUTED or
     INCONCLUSIVE → `no hook found in public evidence — draft opens on the finding
     alone` (a valid resolution — SMYKM opening B, not a failure).
   - Worker returned "no hook found" → the orchestrator writes that same
     finding-only line directly (nothing to verify — no fabrication risk).
   **Quality tripwire:** if the verifier REFUTES ≥2 of the first wave, pause and
   surface to Haytham before drafting the rest of the queue.
5. **Draft each resolved lead — this is the merge; there is no separate
   bare-hook approval step.** As soon as a lead's line is resolved, run the draft
   step below for it. It ends in a held Gmail draft + `Status = Draft Ready`, or a
   named hold if a gate fails. Drafting stays **orchestrator-run** and **re-reads
   the Notion hook line the verifier wrote** — it never trusts the worker's
   proposal directly; that independence is the anti-fabrication gate and it must
   not collapse into one context.
6. Present ONE **brief** (a report, not an approval gate): drafted (lead ·
   hook-or-finding-only · inbox · subject) · held-with-reason (gate/email FAIL,
   no address) · verifier notes. Haytham reviews the finished `Draft Ready` drafts
   in Gmail and sends or schedules them by hand.

**The draft step (run per resolved lead, this same session):** `haytham-email-
draft` (full loop, UAE rules — opening A on a real hook, opening B on "no hook
found") → `python main.py email-check <addr>` → **assign the inbox if the row's
`Inbox` is blank** (`python main.py inbox route --current "<row's Inbox>" --count
"Inbox 1=<n>" --count "Inbox 2=<n>"`, write the label back to Notion) → `python
main.py crm-gate send <row.json> --touch 1 --followups-due M --opener-rank <N>
--inbox "<assigned Inbox>"` (quote the PASS line).

**`--opener-rank` is not optional bookkeeping — read the Findings Bank property
itself, not the page-body "strongest verified finding" narrative, to pick what
the email is actually built from.** The two can disagree: a walk's narrative
prose may describe the most compelling finding even when the bank correctly
tagged that exact finding `RESERVED | DEEP` (the call bait, held for the call).
Build the draft from the bank's lowest-ranked `UNUSED` entry (bank #1) and pass
its rank as `--opener-rank`. If the rank you intended turns out to be
`RESERVED`, or doesn't match the lowest `UNUSED` rank, the gate now hard-fails
— fix the draft to use the correct bank entry, don't argue with the gate. (Added
2026-07-24 after a real incident: a draft was built from the narrative instead
of the bank, and emailed the exact finding the bank was reserving as deep
call-bait. `crm-gate send` previously only *noted* that a deep finding was held
in reserve — it never checked that the drafted email wasn't the reserved one.)

On PASS, create the Gmail DRAFT **in that inbox**
(Inbox 1 → Gmail MCP `create_draft`; Inbox 2 → `python main.py gmail-gethaytham
draft`) and set `Status = Draft Ready` + a `Gmail draft ready (Touch 1) —
"<subject>"` Notes line. Set **nothing else** — Touch #, Last Contacted, Email
Thread Log, and the Findings Bank flip move only on a confirmed send (uae-tick's
job). Any gate/email FAIL or no address → skip the draft, name the reason in the
brief. Drafts only; sending stays his hand, from Gmail.

Single-lead mode (Haytham names one lead) runs the inline Steps 1-5 below, then
the same draft step — carrying through to a held draft by default. If he only
wants the hook resolved, he says "just the hook" and it stops at the line. The
independent re-fetch + quote-match still applies (via `hook-verifier` in a batch;
by hand in a single-lead session).

---

## Step 1 — Gather real evidence (fetch it, cite it, never invent it)

0. **Batch mode only:** before running Step 1-4 on the first lead, run
   `python main.py apify limits` once (no cost). If `near_cap` is true,
   say so up front and fall back to Step 4 (Haytham pastes screenshots)
   for every lead in the batch instead of letting each one discover the
   same exhausted quota individually. Separately, each `apify` call is
   also cost-gated per-run (`audit/apify.py`, $0.10 threshold) — a normal
   single-lead LinkedIn/IG pull clears it automatically; if one instead
   prints `needs_approval`/exits 3, don't retry it — tell Haytham the
   estimate and only re-run with `--approve-cost` once he says yes.
1. Fetch the lead's Notion page. Confirm the lane + Status, and note the
   current `SMYKM hook:` line (should read "not run yet" on a fresh lead).
   The Profile URL property is usually the LinkedIn profile — start there.
2. Compute the slug the same way the rest of the pipeline does:
   `python main.py slug "<Contact Name>"`.
3. **Fetch public sources — the right tool per source:**
   - **LinkedIn (the strongest UAE source), via the Apify actor layer.**
     Firecrawl hard-refuses LinkedIn, so this is how LinkedIn evidence gets
     fetched at all: `python main.py apify li-posts "<Profile URL>" --max 5`
     for her recent posts (text + date, no cookies), and
     `python main.py apify li-profile "<Profile URL>"` when you need the
     About/career story. **Posts first** — a recent post is the strongest
     hook; only pull the profile when the posts are thin and you need the
     story (it also costs more).
   - **Instagram, read-only, via the same layer:**
     `python main.py apify ig "<IG URL>" --newer-than "60 days"` for recent
     posts with captions (`--mode details` for follower/bio metadata;
     `python main.py apify ig-post "<post URL>"` to dig into one post).
   - **Podcasts / YouTube / About page — Firecrawl:** `firecrawl_search` on
     her name + "podcast" / "interview" / her program name, then
     `firecrawl_scrape` the episode, speaker, YouTube, and About pages that
     come back. These are open web, so Firecrawl is the cheaper, connected
     path (and the About-page STORY is still hers).
   - Every one of these is read-only public data through no-login
     infrastructure. **Never log in, never use Haytham's account or
     credentials, never act AS him on any platform** — that's the exact
     account-safety rule the IG ban came from. An Apify actor that takes a
     URL and returns public data is allowed, the same as Firecrawl; acting
     as Haytham is not.
   - The actor layer is `audit/apify.py` (see `docs/uae-track/apify-actors.md`).
     If a command prints `{"error": "APIFY_TOKEN is not set"}`, the token
     isn't on this runner — fall back to Step 4 (ask Haytham for
     screenshots) rather than skipping the source silently.
4. **If the actor layer can't run (no token) or LinkedIn/IG comes up thin**,
   ask Haytham to paste screenshots of her recent LinkedIn posts (he can browse by hand —
   sourcing was always the manual half). Save each pasted/attached image to
   `evidence/<slug>/hook/<n>.png`, then
   `python main.py vision init evidence/<slug>` and
   `python main.py vision mark evidence/<slug> hook/<n>.png` as you read
   each one — same read-before-cite discipline the pipeline has always run.
5. Anything Haytham pastes in chat (screenshots or notes) counts as
   evidence and outranks anything stale already on the page.
6. Nothing anywhere — no public posts, no episodes, no About story, nothing
   pasted → tell Haytham there's nothing to build a hook from, write the
   "no hook found" resolution (Step 4), and stop. **Never pad the gap with
   site marketing copy or a manufactured observation.**

---

## Step 2 — Read for hook material

Across everything fetched and pasted, look specifically for:

- A framework, method, or program she's named and uses as her own language.
- A real recent post or episode: its actual topic, a launch, a specific
  quote — not a vague "she posts a lot."
- A personal update: a milestone, a move, a life event, something human and
  current.
- A stat she owns (a number from her own content) — but see the
  numeric-contrast warning below before using one.

**Recency matters.** A post from this month beats an About page from 2023.
A hook anchored to something she did LAST WEEK reads like a person paying
attention; one anchored to her bio reads like research.

**Numeric-contrast warning:** if the only hook candidate pairs two metrics
she owns (e.g. a large podcast audience next to a small LinkedIn
following), never state both in the same line — the smaller number reads
as the one being pointed at, even when the intent is to praise the bigger
one. Lead with the strength alone, or find a different hook.

---

## Step 3 — The hard rule (uncited evidence never produces a hook)

Every hook must carry its source, and the source must have actually been
read:

- **Fetched web content:** the hook must trace to a specific URL you
  actually fetched this session, and the specific claim (the quote, the
  topic, the date) must appear in what the fetch returned. Note the URL —
  it goes in the hand-off. A hook "remembered" from training data or
  assembled from a search-result snippet you never opened is fabrication.
- **Pasted screenshots:** the exact image must show `read: true` in
  `vision_manifest.json` (`python main.py vision check evidence/<slug>`
  lists unread ones). A hook built on an unread image must never reach
  Notion or an email draft — this is the same failure that once put an
  unviewed post's engagement numbers into a real Gmail draft.

If a candidate hook can't be traced to a read source: read the source now,
substitute a hook grounded in something already confirmed, or say plainly
"possible hook on an unverified source — confirm before using it" and
leave the Notion line as "no hook found."

**Label the hook type** when one is found: WORK (her framework, content,
testimonial, point of view), LIFE (milestone, personal post), or METRIC
(numbers she owns). This is data collection, not a rule yet — keep
labeling every one so the pattern (in the old track: all confirmed
warm-reply hooks were WORK-anchored) stays checkable as sends land.

---

## Step 4 — Write ONLY the hook line to Notion

Fetch the page fresh immediately before writing, even though you fetched
it in Step 1 — confirm the literal current body format (Notion's
enhanced-markdown escaping, e.g. `\$`, auto-linked domains, can break a
naive search-and-replace). If the fetch shows escaped or non-plain
formatting, rewrite the full body (`replace_content`) preserving every
other section exactly as it stood; otherwise a targeted
`update_content` replacing just the `SMYKM hook:` line is fine.

Replace the placeholder with one of:
- `SMYKM hook: <the hook, one line> — <WORK|LIFE|METRIC> — source: <URL or hook/<n>.png>`
- `SMYKM hook: no hook found in public evidence — draft opens on the finding alone`

Also set the `SMYKM Hook` property to the same hook text (or leave it
empty on a "no hook found").

**Blast radius is exactly one line (plus that one property).** Do not
touch Overview, Funnel Walk, Evidence, Gates, the Lane verdict, the
opening angle, the innocent explanation, or the Email Thread Log. This
skill has no opinion on any of those and must not rewrite them.

---

## Step 5 — Hand off (the brief)

Draft-first: the drafts are already made. After the draft step (Input section)
has run per resolved lead, present ONE **brief** — drafted (lead · hook or
finding-only · inbox · subject) · held-with-reason (gate/email FAIL, no address)
· any verifier notes. That is the hand-off: Haytham reviews the finished
`Draft Ready` drafts in Gmail and sends or schedules them by hand. There is no
separate bare-hook approval step. (A single-lead "just the hook" run stops at the
resolved line and hands off the hook only.)

---

## What this skill does NOT do

- It does not classify the lane, run the 5-stop walk, or touch the finding
  or innocent explanation. That's `haytham-opener-finder`.
- It does not run automatically after opener-finder. Haytham triggers it by
  name, per lead.
- It does not log in to, act as, or automate anything through Haytham's
  accounts on any platform — that's the account-safety rule, and acting as
  him through his own IG is what got that account banned. Read-only public
  data is fine, Instagram included, as long as it comes through a no-login
  third-party tool (an Apify-style actor, or Firecrawl for the web sources);
  logging in as him anywhere is not.
- It does not invent a hook. No cited, confirmed evidence supporting one →
  say so and resolve the line as "no hook found."
- It does not build a hook from generic site marketing copy, a press blurb,
  or a directory listing. If that's all that exists, that's a "no hook
  found" — the finding-only opener (SMYKM opening B) is the honest draft.
- It does not send email, ever. It creates held Gmail DRAFTS (the draft-first
  step, after each hook is independently verified and the send gate passes) and
  stops there — sending is Haytham's hand, from Gmail.
