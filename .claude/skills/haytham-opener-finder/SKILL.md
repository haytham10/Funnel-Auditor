---
name: haytham-opener-finder
description: Walk a UAE coach or course-creator funnel (business, life, career, executive, mindset, fitness, health coaches), classify the lane, identify the strongest verified finding, and write the structured output directly to the lead's page in the UAE Lead CRM. Use this skill WHENEVER Haytham pastes a Notion lead page URL, a site link, screenshots, or notes from a funnel walk, or asks to audit/walk/qualify a coach lead, or says "walk this" or "what's the finding" or "what lane is this." This skill crawls the lead's Site URL and any linked pages (via Firecrawl) plus runs a search on the lead BEFORE looking at whatever Haytham pasted, then reconciles the two. It owns the full Gate 0 → Gate 1 → 5-stop walk → two filters → three lanes pipeline and writes the result to Notion in the exact page body format, including the Finding Verified checkbox that gates every send. It stops at the finding + innocent explanation — it does NOT find the SMYKM hook; that's a separate, manually-triggered step (`haytham-hook-finder`) that works from real public evidence (LinkedIn, podcasts, YouTube, About page). Do NOT fetch the framework docs from Notion — everything is baked in here and in docs/uae-track/.
---

# Haytham Opener Finder — UAE track

Walk a coach funnel, classify the lane, surface the strongest finding, and write the result to the lead's page in the **UAE Lead CRM**. The output feeds directly into the email skill — a clean lane verdict, opening angle, and innocent explanation is everything the email skill needs to draft a Lane 1 opener (SMYKM opening B). A hook is a separate, manually-triggered upgrade — see "What this skill does NOT do."

**CRM (all writes go here):** `collection://5efbdd9b-1e19-468c-96db-f94a525846e0`
**NEVER write to the old parenting DB** (`c6209e29-55ef-4781-b735-73b2a254e34f`). It runs live threads only.

The whole point of this skill is speed and depth in one pass, run in the right order: machine first, human second. A live crawl and a search build the raw skeleton of the funnel — what's technically there. Haytham's own observations (screenshots, notes, what a page actually felt like to click through) are placed on top of that skeleton, and they win where the two disagree, because they catch what a crawl cannot see: friction, tone, dead ends behind logins, manual-vs-automated delivery. Never treat the crawl as the finished picture. It's the first draft the human read corrects.

---

## Step A — Gather live signal first (always, before reading anything Haytham pasted)

Do this before opening any screenshots or notes in the prompt. (See
`.claude/skills/firecrawl` for the full MCP tool reference — which
Firecrawl tool to use when, and what this repo does and doesn't use it
for.)

1. **Get the Site URL and Profile URL.** If a Notion lead page URL or ID was given, fetch it first — Site URL and Profile URL live in its properties. If Haytham's prompt itself contains links (a sales page, a webinar registration, a booking page, a checkout), those count too.
2. **Crawl.** Use **Firecrawl** (`firecrawl_scrape` for the Site URL and any other linked pages; `firecrawl_crawl`/`firecrawl_map` if a page needs its linked sub-pages discovered first) instead of the generic web-fetch tool — it handles bot walls and JS-rendered pages that a plain fetch chokes on. Walk what's reachable stop by stop (see `references/walk.md`) and note, for each stop, what a crawl can actually see: entry link destination, freebie opt-in presence, sales/webinar page price/copy, checkout or booking flow if unauthenticated, footer/social links for audience ownership.
3. **Search.** Run one `firecrawl_search` on the lead's name plus niche or city. This serves the Activity floor (last 30 days — see Gate 0 below) and the UAE-residency check. It is **not** the place to build a SMYKM hook — that's `haytham-hook-finder`'s job, run separately after this walk lands the lead as Audit Ready, with its own sourcing discipline (LinkedIn posts, podcast appearances, YouTube, the About page — cited, never invented).
4. **Mark gaps.** Some stops a crawl cannot reach at all: login-walled checkouts, members-only content, anything requiring a real payment or booking attempt. Flag these explicitly as "not visible from crawl" rather than guessing or leaving them blank. This is exactly what Step B exists to fill.

Build a first-pass stop-by-stop skeleton from what steps 1-3 surfaced, with tier calls where confident and open flags where not. Do this whole step silently — don't narrate the crawl process to Haytham, just carry the result into Step B.

---

## Step B — Reconcile with the human-layer read

The human layer comes in two forms, and at least one is required:

1. **Haytham's own material** — screenshots, free-form notes, or both, pasted in chat or attached to the lead's Notion page. This outranks everything else in the walk.
2. **The vision pass** (automated runs, or whenever a machine walk produced screenshots) — read, as images, the desktop screenshot of every crawled page plus mobile for the entry and offer/checkout/booking pages, and the full text files of offer pages. This is Claude's own click-through, and it outranks the machine text checks.

**Machine flags are candidates, not findings.** Every reconciliation entry, leak candidate, stale-date and availability hit in the packet must be confirmed on the screenshot/text by eye before it can enter the filters. Known misfires: footer copyright years read as stale dates, "sold out" inside a testimonial, prices compared across unrelated products, bot walls read as dead pages. A flag that fails visual confirmation is dead — record it as rejected (one-word reason) and never resurrect it. While confirming, hunt the vision-only leaks the checks can't see: empty/stuck booking calendars, hero promises the links don't sell, placeholder content, stale cohort/webinar dates baked into images, mobile breakage, freebie buttons that go nowhere.

This layer is not a fallback for when the crawl comes up short — it's the correction layer that outranks the crawl every time the two disagree, because it reflects the real click-through experience a static fetch cannot capture (friction, tone, whether a wall is a permission gate or a hard 404, whether a "broken" freebie is actually a manual-delivery lag).

Reconciliation rules (Haytham's notes > vision pass > machine checks):
- **Where user observation and crawl agree:** confirmed, move on.
- **Where they conflict:** the user's observation wins (and the vision pass wins over the machine text checks). Note briefly why the lower layer missed it (logged-in view, geo-gated, JS-rendered content the fetch couldn't see, etc.) if it's discoverable, but don't block on figuring that out.
- **Where the crawl flagged a gap and the user's notes fill it:** merge — this is the expected, common case (login-walled flows, real payment/booking attempts).
- **Where the crawl found something the user's notes don't mention:** keep it if it's clearly evidenced (e.g. a stale date, a dead link) — the user may simply not have walked that particular stop.

If, after both passes, some stop still has no observation from either source, leave it unremarkable rather than inventing a finding.

If you have neither a Notion page/site URL to crawl NOR any user-provided observations (just a bare lead name), tell Haytham you need at least a link to crawl or one stop's worth of notes before you can walk. Don't invent findings.

**Vision-pass gate — check this before Step 1, every time.** "A crawl-only walk with no eyes on the screenshots is a draft, never a finished walk" used to rest entirely on self-report, and a real run said "4 screenshots read" in its final verdict when a transcript audit found only 1 Read call against those 4 images. That gap doesn't get caught by trying harder to remember to read things — it gets caught by a script that can't be talked past:

```bash
python main.py vision check evidence/<slug>
```

- **Invoked from process-lead:** it hands you the literal `VISION PASS: ...`
  line from its own Step 1.5. Do not proceed to Step 1 (Gate 1) without it.
- **Invoked standalone** (Haytham pasted a link or Notion page directly,
  no process-lead run before you): after your own crawl in Step A, run
  `python main.py vision init evidence/<slug>` then the `check` command
  yourself, mark every image you read as you read it
  (`python main.py vision mark evidence/<slug> <path>`), and do not begin
  Step 1 until it prints `VISION PASS: COMPLETE`.
- **If it prints INCOMPLETE and stays that way** (an image is genuinely
  corrupted/unreadable, not just unread-yet): proceed only with an explicit
  `⚠️ vision pass incomplete: <path> — <reason>` line carried into the
  Evidence section below and into the final lane verdict. Never let a lane
  classification, a Notion write, or a chat report claim "screenshots read"
  as a paraphrase — quote the tool's exact line, complete or incomplete.

Read `references/walk.md` and `references/schema.md` now, before doing anything else past this point.

---

## Step 0.5 — Gate 0 (the UAE floors)

No automatic dedup query here — querying the pipeline on every single walk was burning tokens for a check that's rarely the actual failure point. If Haytham already has the lead's Notion page open or pasted, that page IS the dedup check; a walk on an existing row just overwrites it fresh, which is fine. Only query the pipeline for a name/URL match if something feels off — e.g. Haytham pastes a lead with no page link at all, or a name that rings a bell — and even then, one targeted query, not a routine step.

**Gate 0 (docs/uae-track/03).** Sourcing and Day-2 qualifying are supposed to settle this upstream, but the old pipeline's rows proved gates get skipped, so the walk re-enforces all four before any touches get spent. The machine-checkable half comes back in the evidence packet (`audit/gates.py`); complete the rest by judgment:

- **UAE-based:** physically in Dubai, Abu Dhabi, Sharjah, or elsewhere in the UAE. "Serves the region" does not count. Check the About page, LinkedIn location, event appearances from the Step A search.
- **Has a funnel or paid product:** a live sales page, checkout, course, or paid digital offer exists. A coach who only sells 1:1 by DM or call has nothing to fix — out of scope.
- **Activity floor:** posted, emailed, or launched something within the last **30 days**. Check this against the Step A search results, not secondhand notes.
- **Audience floor:** **1,500+** on their largest owned or social channel. UAE audiences run smaller; a 2K UAE-focused list is worth what 8K is in the US.

Any floor failed → set `Gate 0` = Fail, `Status` = Disqualified, one-line reason in Notes, and stop. Do not linger. The floor exists to protect walks and touches, which are the scarcest resources — every opener under the daily send ceiling needs a verified finding behind it.

---

## Step 1 — Gate 1 check (2 seconds)

One question only: is there a team or gatekeeper between Haytham and the owner?

Fail signals: "we" / "our team" language, an agency in the footer, a support@ inbox with a ticketing system, a named marketing lead, a verified mega-account with someone triaging the inbox.
Pass signals: own face, own story, replies to their own comments, single-person About page.

- YES (gatekept) → set `Gate 1` = Fail, `Status` = Disqualified, note reason as "gatekeeper/team," write to Notion and stop. File mentally as long-term inbound, not a bad person.
- NO or unclear → set `Gate 1` = Pass and proceed to Step 2.

The ONLY thing this gate filters is a human wall. A real funnel, a custom site, a Kajabi build, a verified badge — none of these are skip reasons. If a funnel is genuinely optimized with no leaks, the walk finds that in 90 seconds and routes to Lane 2.

---

## Step 2 — The 5-stop walk

Work through each stop in order using the observations provided. For each stop, apply the master principle:

> A leak is any point where attention the coach already earned fails to convert toward money she can see — AND she'd feel the cost if you named it.

Read `references/walk.md` for the full stop-by-stop diagnostic questions, tier classification, and the growing list of known leak patterns — including the funnel shapes this market runs on: webinar funnels, call-booking flows, and cohort launches. The master principle catches leaks not in the list. If something fits it and isn't listed, it's still a leak.

For each stop: note what's there, flag anything that fails the master principle, tier it (A = critical, B = strong, C = soft).

---

## Step 3 — Two filters (run on everything the walk flagged)

**Sting test:** would she FEEL this as a cost, or shrug? If she'd shrug, it's not an opener even if technically suboptimal. Demote to Lane 2 or drop.

**Vitamin filter:** is this a FELT COST (attention or money leaking now) or a MECHANISM she lacks ("you need an email list")? Mechanisms are vitamins — low cold conversion. Reframe as felt loss if possible, or hold. If it can't be framed as felt cost without manufacturing it, it's not an opener.

A finding that fails either filter is not Lane 1.

---

## Step 4 — Lane classification

Sort into exactly one lane:

**Lane 1 — OPEN (felt leak + committed buyer).** At least one flagged finding survives both filters. Use the single strongest one as the opener. Don't stack multiple findings in one email. This is the only lane that produces a cold send in this track — the send gate requires a verified finding.

**Bank everything that survived, not just the winner.** Every visually-confirmed finding that passes both filters goes into the lead's Findings Bank, ranked strongest first (tier first, then sting). #1 is the opener; #2 onward is what cold Touch 2/3 draws on (`crm-gate send --carries second-finding` checks the bank, so a discarded finding is a follow-up that can't happen). Unverified candidates and filter-fails never enter the bank — it holds openable findings only, just ranked.

**Lane 2 — WARM-UP (committed buyer, no felt leak).** No finding survives both filters, but the lead is clearly a committed operator (paid ladder, multiple offers, email capture, active engagement). Most Gate 1 survivors land here and that is NORMAL — a felt leak on a real buyer runs roughly 20-25%. Note the warm-up angle (a genuine peer entry anchored to something specific and real they're doing right now). **A Lane 2 lead does not get `Finding Verified` and does not reach Audit Ready** — it holds at Qualifying as a long-play/warm-up lead. The hard gate is deliberate: no send without a verified finding.

**Lane 3 — SKIP (not a buyer).** Hobbyist floor, no income signal, MLM, or gatekeeper. Set Status = Disqualified. No opener. A felt leak on a non-buyer is still a skip — leak does not equal buyer.

**Drift-guard:** the warm-up lane is easier, so it tends to crowd out leak-hunting. Lane 1 leads are the only sendable ones here. Run the finding scan honestly before defaulting to warm-up.

---

## Step 5 — The opening angle

Lane 1 only: state the single strongest finding (bank #1) as the opening angle. One sentence, concrete, falsifiable, bespoke to this page. Frame as felt cost. This is what feeds into the email skill — the email skill takes this line and builds from it. Every other banked finding gets the same treatment in miniature (one felt-cost line + its innocent explanation) in the page body's Findings Bank section — it's follow-up material and deserves to be usable when Touch 2 needs it.

**The innocent explanation is a required second line.** Alongside the finding, always output the plausible non-blame explanation for it: the calendar might just need a reset, the cohort date might be stuck from last round, the replay link might still be mid-migration, the section might still be loading. The email skill turns this pair into the either/or closing question, and the pipeline evidence says that question is doing heavy lifting: all five cold openers that earned warm replies in the old track closed with an either/or handing her a face-saving explanation, and the one opener that closed with a challenge and no exit drew "Rude." This matches reactance research on feedback: delivery that questions competence triggers defensiveness, delivery that leaves the recipient autonomy keeps her receptive. If no innocent explanation exists for a finding, flag that to Haytham; it may mean the finding will read as an accusation no matter how it's phrased.

**The Loom skeleton (Lane 1, required).** While the funnel is still fresh in
context, write the three-line artifact outline into the page body's Loom
Skeleton section (see schema.md): Show (the exact page/element + URL), Fix
(the one change, in her platform's terms), Done state (what working looks
like). It costs nothing now and turns a "yes, show me" reply into a
30-minute delivery instead of a re-research session — slow artifact delivery
was the old track's #1 controllable failure.

**No SMYKM hook here.** This skill stops at the finding + innocent explanation. Write `SMYKM hook: not run yet — see haytham-hook-finder` as the placeholder line in Step 6 below. Finding the actual hook is `haytham-hook-finder`'s job — a separate skill Haytham triggers manually on an Audit Ready lead, working from real public evidence (LinkedIn posts, podcast appearances, YouTube, the About page). The email skill can draft perfectly well without one (SMYKM opening B, direct finding opener); the hook is an upgrade, not a blocker — but the hook line must be RESOLVED (real hook or confirmed "no hook found") before any draft goes out.

Lane 2: note the warm-up angle. What specific piece of their content or current activity is the genuine entry?

Lane 3: one-line reason, nothing else.

---

## Step 6 — Write to Notion (the UAE CRM)

Fetch the lead's Notion page first to get the current state. Then write the walk output to the page body in the exact format from `references/schema.md`. Update the properties at the same time — see the property table there. In particular:

- **`Finding Verified` gets checked ONLY for a Lane 1 lead whose finding you visually confirmed** (vision pass or Haytham's own observation) from a clean state. This checkbox is the hard send gate (`python main.py crm-gate send` fails without it). Checking it on a thin or unconfirmed finding is the exact failure this track exists to avoid.
- **Status:** Lane 1 with gates passed + finding verified → `Audit Ready`. Lane 2 → stays `Qualifying` (warm-up hold, Notes carries the angle). Lane 3 or any gate fail → `Disqualified`.
- **Est. Value:** `Track A ($200)` by default; `Track B ($700)` only when real launch or sales volume is visible; `Unknown` if you can't tell.
- **`Findings Bank` (property):** the ranked verified findings in compact machine-parseable lines, `1. UNUSED | <finding>` (one per line, all UNUSED on a fresh walk — send-confirmation logging is what flips them to `USED-TN` later). The send gate parses this property, so the format matters. Lane 2/3: leave empty.

If the write uses search-and-replace (`update_content`) rather than a full
body rewrite, the fetch above is not optional — confirm the page's literal
current formatting (Notion's enhanced-markdown escaping, e.g. `\$`,
auto-linked domains) before assuming plain text. Escaped formatting →
use `replace_content` instead.

**Coherence rules (carried from the old pipeline's broken rows):**
- Lane 3 forces Status = Disqualified. Lane 1 can never carry Disqualified. A row must parse.
- If the lead's email was derived from a source the walk itself flagged as broken or suspect, the Status stays at Qualifying and the flag goes in Notes as the FIRST line, not buried.
- Finding Type: prefer `Dead/stale element` for time-bound breakage (stale cohort/webinar dates, empty calendars, dead links, expired events, placeholder content) — in the old track this category contained most of the warm repliers. `Broken booking flow` and `No visible pricing` exist as their own options now; use them when they're the finding.

After writing, confirm to Haytham: lane verdict, the single strongest finding in one line, the innocent explanation, how many findings were banked (e.g. "banked 3 — Touch 2/3 have material"), and whether `Finding Verified` was checked. That's enough for the email skill to draft a Lane 1 opener today. Mention that the SMYKM hook line was written as "not run yet" and that `haytham-hook-finder` must resolve it before the draft can be created.

---

## What this skill does NOT do

- It does not stop at crawling. Site URL, linked pages, and one lead-name search happen automatically before the walk (Step A), but the human layer — Haytham's screenshots and notes, and in automated runs the mandatory vision pass over the crawler's screenshots — is what confirms, corrects, or fills in what the crawl can't reach: logins, real checkout or booking attempts. A crawl-only walk with no eyes on the screenshots is a draft, never a finished walk.
- It does not go exploring beyond what's linked. It fetches the Site URL, Profile URL, and any pages Haytham's prompt points to — it doesn't crawl arbitrary internal pages, attempt logins, or try to pay through a paid gate. Those stops rely on user observation.
- It does not invent findings. If neither the crawl nor the user's observations support a finding at a given stop, say so and move on. `Finding Verified` stays unchecked and the lead is Lane 2 or Lane 3 — that is a fine outcome, not a failure.
- **It does not find the SMYKM hook.** That's `haytham-hook-finder`, a separate skill Haytham triggers by hand on an Audit Ready lead, working from real public evidence (LinkedIn, podcasts, YouTube, About page). This skill writes a placeholder line and stops.
- It does not draft the email. That's the email skill's job. This skill ends at the opening angle + innocent explanation.
- It does not touch the old parenting DB, ever.
