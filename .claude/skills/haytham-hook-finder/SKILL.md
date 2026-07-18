---
name: haytham-hook-finder
description: Pull real public evidence for an Audit Ready UAE lead — LinkedIn posts, podcast appearances, YouTube, their own About page — and find the SMYKM hook, the one line only this person would recognize (their own framework, a real recent post or episode, a personal update), then write just that line to their Notion page in the UAE Lead CRM. Use this skill WHENEVER Haytham says "find the hook," "SMYKM this," "hook Jane," "add a hook," asks for a stronger opener on a lead that's already Audit Ready, or process-lead/batch-audit reports a lead "held — needs haytham-hook-finder." This is a separate, manually-triggered step from haytham-opener-finder — the walk assigns the lane, finding, and innocent explanation; this skill's only job is the hook, and it must come from real, cited public evidence, never fabricated and never from generic site marketing copy. It is a required gate, not an optional upgrade: haytham-email-draft will not draft for a lead until this skill resolves the hook line. It does not touch the lane, the finding, the innocent explanation, or draft any email.
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
**required** before `haytham-email-draft` will draft anything for this
lead. `process-lead` and `haytham-email-draft` both hard-block on a
`SMYKM hook:` line that still says "not run yet," so every Lane 1 lead
sits waiting for this skill to run before it can get a Gmail draft. Once
this skill resolves the line (a real hook, or a confirmed "no hook
found"), the draft can go ahead.

**CRM:** `collection://5efbdd9b-1e19-468c-96db-f94a525846e0`. Never the old parenting DB.

---

## Input — single lead, or the whole batch

A Notion lead page (URL or ID) or a name Haytham names. The lead must
already be Audit Ready with a funnel walk written by
`haytham-opener-finder` — if it isn't, say so and point Haytham to that
skill first; don't run a hook search on a lead with no lane verdict yet.

**Batch mode (2026-07-14).** When Haytham says "hook the queue," "hook
them all," "batch hooks," or names several leads: query the CRM for
every `Audit Ready` row whose `SMYKM Hook` property is empty (hook line
still "not run yet") and run Steps 1-4 on each, one lead at a time, same
evidence discipline per lead — batch mode changes the invocation
overhead, never the citation bar. Then present ONE review table: lead /
hook (or "no hook found") / type label / cited source. Every hook line
is written to Notion as it resolves (Step 4 per lead, as always); the
table is his single review pass instead of sixteen separate asks.

**Auto-draft on approval (the round-trip killer).** End the batch (or
single-lead) hand-off with: "hooks resolved — say the word and the
drafts get created in this same session." When Haytham approves ("draft
them," "go," or per-lead picks/edits — an edited hook gets written back
to Notion first), immediately run the full Touch 1 draft flow for each
approved lead in this same session: `haytham-email-draft` (full loop,
UAE rules), `python main.py email-check`, then **assign the sending inbox
if the row's `Inbox` is blank** (`python main.py inbox route --current
"<row's Inbox>" --count "Inbox 1=<n>" --count "Inbox 2=<n>"`, write the
chosen label back to Notion), then `python main.py crm-gate send … --touch
1 --followups-due M --inbox "<assigned Inbox>"` per lead (quote both
lines). Create the Gmail DRAFT for each PASS **in that inbox** (Inbox 1 →
Gmail MCP `create_draft`; Inbox 2 → `python main.py gmail-gethaytham
draft`), and set Status = `Draft Ready`. Held leads (gate FAIL, email-check
FAIL, no address) get named with reasons. Drafts only — sending stays his
hand, from Gmail.

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

## Step 5 — Hand off

Tell Haytham: the hook (or that none was found), its type label, and its
exact source (URL or image path) with the read/fetch status — in batch
mode, the one review table. This resolves the block on
`haytham-email-draft` — close with "say the word and the drafts get
created in this same session." On his approval, the auto-draft flow in
the Input section runs right here (email-check + crm-gate per lead,
Gmail DRAFTS, Status = Draft Ready); the hook search itself never
drafts without that approval.

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
- It does not send email, ever. It touches Gmail only in the
  auto-draft-on-approval flow (creating DRAFTS after Haytham explicitly
  approves the resolved hooks), never during the hook search itself.
