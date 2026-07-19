---
name: process-lead
description: Take a sourced UAE coach lead (name + site URL, usually from the UAE Lead CRM's Walk Queue) through the machine walk, vision pass, Gate 0 floors, and opener-finder walk, logging everything to the UAE Lead CRM. Use this skill WHENEVER Haytham pastes a new lead — a name, a site URL, a LinkedIn profile, optionally notes or screenshots — or says "process this lead," "run this one," "walk this one," "new lead," or pastes several candidates. It runs the machine funnel walk (Firecrawl-primary fetch, Python-owned scope/analysis, Playwright fallback), does the mandatory vision pass over the screenshots, enforces the UAE Gate 0 floors, logs to the UAE CRM, and hands the evidence to the opener-finder. The Gmail DRAFT step is held until `haytham-hook-finder` has resolved the SMYKM hook line for this lead — it never drafts on a fresh "not run yet" hook. It never sends anything, and never logs in to or automates anything through Haytham's own platform accounts.
---

# Process Lead — intake → walk → vision pass → Notion → opener → (hook-finder) → Gmail draft

One command per candidate. Sourcing is dynamic and no-login now
(`source-leads` skill — platform + link-in-bio footprints, directories,
LinkedIn, podcasts/events, no-login IG actor, lateral); this skill takes
over the moment a candidate has a name and a reachable link.

**CRM (all reads/writes):** `collection://5efbdd9b-1e19-468c-96db-f94a525846e0`
(REST API database ID: `5a9fc583160046d1a64c4e65cc804229`).
**NEVER write to the old parenting DB** (`c6209e29-55ef-4781-b735-73b2a254e34f`).

## Input

Minimum: a site URL (the funnel entry point). Wanted: contact name,
Profile URL (usually LinkedIn), audience size, city, Source Channel.
Optional: email if already known, coach-type hint, his own notes or
screenshots.

If several leads are pasted at once, process them one at a time, start to
finish, and give a one-line verdict per lead at the end. (For batches
already logged in Notion, the batch-audit skill is the entry point — it
parallelizes with one lead-processor agent per lead.)

If only a LinkedIn profile URL is given with no site URL: fetch the public
profile via Firecrawl (read-only; never log in, never act as Haytham) and
run a web search for the person — if that surfaces their site, use it.
Otherwise ask for the site link. Never log in anywhere or act as Haytham to do it.

## Step 0 — Pull the lead's Notion page + any pasted evidence

If the lead exists in the CRM (batch runs always; chat runs when he pastes
a Notion URL), fetch the page first:

1. `notion-fetch` the lead page. Properties are the intake of record; the
   page body may already hold an old walk (you will overwrite it fresh).
2. **Compute the slug now, once, the same way the crawler will:**
   `python main.py slug "<Contact Name>"` (falls back to URL if no name
   yet). Use this exact slug for every evidence path below — the
   Firecrawl fetch loop's screenshots/manifest, `discover-links`'s HTML
   files, and `ingest --out evidence/<slug>`. A hand-guessed slug once
   split one lead's evidence across two folders the vision gate couldn't
   reconcile.
3. If Haytham pasted screenshots in chat or attached images to the page
   body (a LinkedIn post, a checkout he clicked through, anything), save
   each to `evidence/<slug>/hook/<n>.png` (attached images come back as
   signed URLs that expire — download now, `curl -o ...`). After the crawl
   in Step 1, `vision init` registers them and they get read + marked like
   every other required image. Pasted evidence outranks everything the
   crawl says.

No pasted evidence is the normal case on this track — the crawl + search
IS the intake. Carry on.

## Step 0.5 — Pre-flight qualification (cheap, BEFORE the walk)

The walk and vision pass exist to find the *leak*, and a leak only matters
on a lead who is already a real UAE buyer reachable directly. Most Gate 0
kills fail on things a full crawl never needs — audience, activity,
UAE-base, gatekeeper — so settle those FIRST, cheaply, and commit the
expensive walk only to survivors. (This step exists because a July 2026
batch let three of four kills each burn a full 185K-268K-token walk +
vision pass before the one cheap number that killed them: audience.)

Budget: **one web search + at most one light profile scrape + one light
fetch of the entry page.** No multi-page crawl, no screenshots, no vision
pass yet. Bail the instant one floor hard-fails. Resolve cheapest-first:

1. **UAE-based** — search + the entry page's About/footer. Not UAE-primary
   (a multi-hub coach who lists Dubai alongside other home bases, or serves
   the region from elsewhere) → `Gate 0` = Fail, `City` = Unconfirmed,
   `Status` = Disqualified, one-line reason, stop. Free, and it kills early.
2. **Gatekeeper (Gate 1)** — the same entry-page fetch shows own-face vs
   "we"/agency/support-desk/named marketing lead. Walled → `Gate 1` = Fail,
   `Status` = Disqualified, "gatekeeper/team", stop. (This is the full Gate
   1 check from `haytham-opener-finder` Step 1, just pulled forward — no
   reason it waited behind the walk.)
3. **Funnel exists (cheap read)** — the entry-page fetch confirms a paid
   offer is present at all (sales page, checkout, course, paid digital
   product). Genuinely nothing-digital / call-only / brochure-only → Fail.
   Full funnel-floor confirmation comes from the walk; this is only the
   "is there an offer to leak from at all" read.
4. **Activity floor** — most-recent post/publish/launch date from the
   search or the profile. Nothing in the last **30 days** → Fail.
5. **Audience floor** — 1,500+ on the largest owned or social channel. Try
   the cheapest signal first (a search snippet, a follower count visible on
   the entry page). Escalate to **one** Apify profile scrape (`apify ig
   --mode details` OR `apify li-profile`, largest channel only, never both)
   ONLY if the cheap signal is inconclusive AND the lead survived 1-4 — and
   only if `python main.py apify limits` isn't already `near_cap`. One
   attempt, no retry-storm.

   **The audience call is three-way, never a blind pass/fail** — a scraper
   hiccup must not kill a real lead (a July run had Apify return empty for
   an obvious-above-floor ICF board chair and error on the cap for another;
   both turned out to be real Audit-Ready leads):
   - **Hard number obtainable** → it decides. Under 1,500 with no bigger
     owned channel = Fail → Disqualified.
   - **Inconclusive + strong qualitative signal** (public stature, press,
     directory presence, a real paid ladder) → proceed to the walk; write
     "audience unconfirmed — proceeding on <signal>" in Notes.
   - **Inconclusive + weak/no signal** → **hold at Qualifying** (Notes:
     "audience unconfirmed — needs a hard number before a walk"). Do NOT
     spend the walk, do NOT hard-Disqualify.

6. **Email, free check only** — if the entry-page fetch surfaced a contact/
   footer address, run `python main.py email-check <addr> --name "<name>"`
   now (free, no Apify). At this stage it's a soft reachability signal, a
   flag not a kill: no visible address yet is normal (it may surface in the
   walk or via a freebie opt-in). Deliverability verification is Step 5,
   once the real address is settled — don't spend Apify on it here.

**Only a lead that clears 1-5 earns the walk.** Write the resolved floors
onto the row now (City, Audience Size, `Gate 0` = Pass, `Gate 1` = Pass) so
a kill later in the walk doesn't lose the pre-flight evidence, and **keep
the entry-page fetch you already pulled — it becomes Stop 1 of the machine
walk**, so the tax on a lead that passes is ~zero.

## Step 1 — Machine walk (Firecrawl-primary)

Only reached by a lead that cleared Step 0.5. Reuse the Step 0.5 entry-page
fetch as this walk's Stop 1 (seed page) rather than re-fetching it.

```bash
pip install -q -r requirements.txt   # first run only
```

Firecrawl (the MCP tools already connected this session) is the primary
fetcher — cheaper, faster, and better at bot walls/JS-rendered pages than
the local Playwright browser. Python still owns every decision about
scope, priority, and analysis; you're only driving the fetch. See
`.claude/skills/firecrawl` for the tool reference. Always use the exact
slug from Step 0.2 for every path below.

**1. Fetch the site URL.** `firecrawl_scrape` with `formats: ["html",
"screenshot"]`, `screenshotOptions: {fullPage: true}` (default desktop
viewport). Save the HTML to `evidence/<slug>/_firecrawl_raw/1.html`. Save
the screenshot to `evidence/<slug>/screenshots/<name>` using the exact
filename from `python main.py screenshot-name <url> desktop` — never
hand-guess the filename, the packet renderer and vision-gate matching
depend on it being exact.

**2. Mobile screenshot, only for required stop types.** If this stop's
link_type will be `bio_page`, `sales`, `course`, `checkout`, or `booking`
(`REQUIRED_MOBILE_TYPES`), run a second `firecrawl_scrape` with `mobile:
true, formats: ["screenshot"]`, save it via `python main.py
screenshot-name <url> mobile`. Skip this call for stops outside that
list. On booking/checkout stops, pass `waitFor: 4000` or so —
approximates the old iframe-attach wait for Calendly-style embeds that
load async.

**3. Discover what to fetch next.** `python main.py discover-links
evidence/<slug>/_firecrawl_raw/1.html <url>` — prints JSON
(`funnel_links`, already scope-classified and priority-sorted;
`noise_links`; `external_refs`; detected `platform`). This is the single
source of truth for scope/priority — don't reimplement or second-guess it.

**4. Loop — fetch in parallel.** Fetch each `funnel_links` entry the same
way (steps 1-2), capped at `MAX_PAGES` (16). The scrapes are independent:
**issue 3-4 `firecrawl_scrape` calls per round in parallel** instead of
one at a time — this roughly halves a walk's wall-clock and changes
nothing else (discovery stays sequential per round, since each round's
links come from the last round's HTML). Then the checkout-hop pass: for
every page fetched so far, `python main.py discover-checkout
evidence/<slug>/_firecrawl_raw/<n>.html <page-url>`, fetch what it
returns, capped at `MAX_CHECKOUT_HOPS` (6) total.

**5. Approximate load time.** Time each `firecrawl_scrape` call yourself
(wall clock around the tool call) and use that as `load_time_ms` in the
manifest — it's Firecrawl's round-trip time, not raw browser nav timing,
so `speed.py`'s fast/moderate/slow buckets may skew a little slow. Not
worth optimizing further; it's a soft signal, not a gate.

**6. Assemble the manifest and ingest.** Build
`evidence/<slug>/manifest.json` — one entry per fetched page (`url,
title, link_type, load_time_ms, screenshot_desktop, screenshot_mobile,
depth, source_url, error, http_status, external, html_file, cta_clicks:
[]`) plus the accumulated `seed_url, platform, funnel_links, noise_links,
external_refs`. Then:

```bash
python main.py ingest evidence/<slug>/manifest.json --name "<Name>" --followers <audience size> --out evidence/<slug>
```

This produces `evidence/<slug>/packet.md`, `evidence.json`, per-page text
files, and a refreshed `vision_manifest.json` — byte-identical contract to
the old `python main.py walk`, regardless of which layer fetched the
pages.

**Known gap — CTA click-discovery, and the single-page fix.** The
JS-button click-discovery logic needs a live browser session, which a
stateless Firecrawl scrape can't replicate — `cta_clicks` is always `[]`
for Firecrawl-fetched pages. When the packet's "unverified interactive
elements" section flags JS-only buttons on a sales/course/booking page
that matter to the lane call, don't re-walk the whole funnel: run
`python main.py cta-probe <that-page-url> --type sales|course|booking`
to click-resolve just that one page (Playwright, one page, prints the
cta_clicks JSON). Quote what it resolved in the Evidence section. Pages
where the buttons are obvious chrome don't need it.

**Fallback to Playwright.** If Firecrawl fails outright on a page after
retry (persistent block even with `proxy: stealth`), or the platform is a
bio-link aggregator with no anchor-discoverable products (exactly the
condition the click-discovery logic exists for), fall back to the
original path for this one lead instead of fighting it further:

```bash
python main.py walk <site-url> --name "<Name>" --followers <N> --out evidence/<slug>
```

Say so plainly in NOTES when you fall back — this keeps click-discovery
reachable for the leads that actually need it, rather than losing it
silently.

If the crawl errored on the entry page, that is itself a possible Tier A
finding (verify: hard 404 vs bot wall vs permission wall — the screenshot
tells you which) — don't abandon the lead.

## Step 1.5 — The vision pass (mandatory, machine-checked, not self-reported)

The packet's machine checks are pattern-matchers; they misfire and they
miss. You have eyes — use them the way Haytham does when he clicks through
by hand. This step used to be enforced by instruction alone ("read every
image") and a real run reported "4 screenshots read" in its final verdict
when only 1 of 4 had actually been opened. It's enforced by a script now,
not by trusting your own summary.

**Read, as images, the desktop screenshot of EVERY crawled page**, plus the
mobile screenshot of the entry page and of every offer/checkout/booking
page, plus every pasted-evidence image under `hook/`. Read the full text
files of the sales/freebie pages — copy is where non-mechanical leaks
live. Run `python main.py vision list evidence/<slug>` first to see the
exact list of paths this crawl requires.

**Firecrawl mobile-render caution (learned 2026-07-19):** Firecrawl's
MOBILE screenshots are NOT reliable for layout-shape findings on some sites
— they produce full-page stitching artifacts and false overlaps/cutoffs
(this is what generated two findings that Haytham refuted on his real phone,
Corrie Block + Roota Mittal, and burned two re-walks). So a
**cutoff / overflow / clipping / overlap / cropped-off-the-edge** finding
seen ONLY in a Firecrawl mobile capture does NOT count until it is
reconfirmed on a real render — the Playwright walk (`python main.py walk` /
`cta-probe`), a desktop capture, or the raw HTML. A layout finding that
survives only in the mobile screenshot is dead on arrival. Content/text/
headline mismatches read from the HTML (e.g. a wrong-city title tag) are
safe — this caution is about pixel-layout claims only.

**Read each screenshot with the Read tool directly — it downscales tall
fullPage captures for you. Do NOT shell out to Python/PIL to slice, crop,
or resize a screenshot.** (`pillow` is in requirements.txt if you ever
genuinely need it, but the Read tool is the path — reaching for PIL is what
wedged a whole batch for 2h when the import failed and the agent never fell
back.) If ANY preprocessing or Read of an image errors, fall back to
reading it directly / note it as the unreadable-image exception below and
move on — **never stall on an image**. A crawled sales page can be
15k–20k px tall; that is normal, Read it as-is.

**After each image Read, immediately run
`python main.py vision mark evidence/<slug> <path>`** (batch several paths
in one call if you just read several in a row — same rule, no deferring to
the end).

Two analytical jobs while you read, in this order:

1. **Confirm or kill every machine flag.** Each reconciliation entry, leak
   candidate, stale-date candidate, and availability hit in packet.md is a
   CANDIDATE, not a finding. Find it on the screenshot/text with your own
   eyes. Common misfires to kill: a footer copyright year read as a stale
   event date; "sold out" inside a testimonial or story; a price mismatch
   across two unrelated products; a "broken" link that the screenshot shows
   rendering fine; bot-wall pages read as dead pages. A flag you could not
   visually confirm is DEAD — it cannot become a finding or an opener, ever.
   Keep a rejected-flags list (one-word reason each); it goes in the verdict.
2. **Find what the machine can't.** While reading, hunt vision-only leaks:
   an empty or stuck booking calendar, a hero promising a program the links
   don't sell, a passed cohort/webinar date still showing, placeholder
   content, a checkout asking for trust the page hasn't earned, layout
   breakage on mobile, stale dates baked into images, a freebie button that
   goes nowhere. These are exactly the leaks Haytham catches manually —
   this pass is what replaces his click-through.

**The hard gate — run before doing anything else in Step 2 or Step 4:**

```bash
python main.py vision check evidence/<slug>
```

This exits 0 and prints `VISION PASS: COMPLETE — X of X required images
confirmed read` only when every required image has actually been marked.
Otherwise it exits 1, prints `VISION PASS: INCOMPLETE — N of M...`, and
lists exactly which paths are still unread.

- **INCOMPLETE → do not proceed to Step 2 or Step 4.** Go back, Read the
  listed images, mark them, and run the check again. Repeat until it passes.
- **The only exception** is a genuinely unreadable/corrupted image (the file
  won't open, or the screenshot is blank/broken past the point of being
  informative). In that specific case only, you may proceed, but the exact
  path and the reason must be written verbatim into the Evidence section as
  `⚠️ vision pass incomplete: <path> — <reason>` — never silently dropped,
  never smoothed into "vision pass complete."
- **Paste the literal `vision check` output** (the `VISION PASS: ...` line)
  into the Evidence section of the eventual Notion body and into the final
  chat verdict. Never write a paraphrase like "4 screenshots read" — if the
  check didn't print exactly that, the report can't claim it either.

## Step 2 — Gate 0 (confirm + lock)

UAE-base, activity, audience, and the gatekeeper (Gate 1) were already
settled cheaply in Step 0.5 — this step does NOT re-litigate them. Its job
is the one floor the walk actually adds evidence to, plus a lock:

- **Funnel floor (confirm)**: the full crawl + vision pass now confirm the
  paid offer Step 0.5 saw is real and reachable, not login-walled vapor or
  a dead offer page. If the walk *contradicts* a pre-flight pass — the
  "offer" turns out to be nothing behind a wall, or the site is genuinely
  call-only after all — flip `Gate 0` = Fail, `Status` = Disqualified,
  one-line reason (properties only, no body), and stop.
- **Lock the verdict**: with the funnel floor confirmed and Step 0.5's
  floors holding, `Gate 0` stays Pass. `audit/gates.py` still owns the
  machine half (entry link, funnel floor, audience-if-supplied); the
  judgment floors carry over from pre-flight.

Do not re-run the Apify audience lookup here — Step 0.5 owns the one
attempt. The floors protect walks and touches: every opener under the send
ceiling needs a verified finding, so walks are the bottleneck by design,
and Step 0.5 is what keeps a walk from being spent on a lead that can't
clear them.

## Step 3 — Notion row

Dedup per the opener-finder's rule: no routine pipeline query — only run
one targeted query if something feels off (name rings a bell, lead arrives
with no page link). If a row already exists, update it instead of creating
one.

Create/update the row with what's known: Contact Name, Profile URL, Site
URL, Audience Size, City, Coach Type, Source Channel, Email (if found —
see Step 5), Status = Qualifying.

## Step 4 — The walk (judgment half)

Do not start this step until Step 1.5's `vision check` printed `VISION
PASS: COMPLETE` (or you've logged the unreadable-image exception). Pass
that literal line into the opener-finder invocation — it will not run a
lane classification without it.

Now invoke the **haytham-opener-finder** skill logic with:
- the evidence packet as Step A (the crawl + search layer, already done), and
- the vision pass + any pasted evidence + any notes Haytham typed as Step
  B (the human-layer read — it OUTRANKS the machine text checks wherever
  they disagree, and Haytham's own typed notes outrank everything).

Follow that skill exactly: the 5-stop walk, sting test + vitamin filter,
lane classification, opening angle + innocent explanation. (Gate 1 was
already settled in Step 0.5 — do not redo it.) Only visually-confirmed
findings enter the filters. Bank every finding that survives both filters,
ranked strongest first — the body's Findings Bank section plus the
`Findings Bank` property (`N. UNUSED | finding` lines the send gate
parses); #1 is the opener, the rest is Touch 2/3 material that must not be
discarded. Write the page body and properties to the UAE CRM in the exact
schema.md format, including the Evidence section with the literal
vision-check line. `Finding Verified` gets checked ONLY for a Lane 1 lead
with a visually-confirmed finding — it is one of the two hard send gates
(the other is `Email Verified`, set in Step 5). **Do not promote Status to
Audit Ready here** — a Lane 1 lead stays Qualifying until Step 5 confirms
deliverability and checks `Email Verified`; Audit Ready must mean sendable
pending only the hook. The `SMYKM hook:` line gets written as the
placeholder `not run yet — see haytham-hook-finder`. **This placeholder
blocks Step 6 below.** `haytham-hook-finder` is a separate, manual step
Haytham runs on this same lead to clear the block — its evidence sources
are LinkedIn, podcasts, YouTube, the About page, and read-only no-login
Instagram data (via a third-party actor, never logged in as Haytham).

## Step 5 — Email address + deliverability verify (send-readiness gate)

Work the Email OS decision tree with what the walk harvested (Step 0.5's
free `email-check` may already have a candidate):
1. Personal-looking address from the crawl → use it.
2. Generic (info@/contact@) → use only if nothing better.
3. Nothing harvested → web search (`"[name]" email contact`), LinkedIn
   contact info if publicly visible, podcast/YouTube show notes.
4. Still nothing → **nominative enrichment** (the automated fallback, run it
   before giving up): derive name-based candidates against the lead's own
   branded domain and verify them in one batched call:
   ```bash
   python main.py email-enrich "<Contact Name>" <Site URL>
   ```
   Quote the literal `EMAIL ENRICH:` line and act on it:
   - **`EMAIL ENRICH: PASS`** → the printed address is the adopted, verified
     mailbox. It is by construction an `EMAIL VERIFY: PASS`, so write it to
     `Email` and check the `Email Verified` box (skip the separate
     `email-verify` in check (b) — it is already done). Note in the row body
     that the address was enrichment-derived (audit trail). The engine already
     converged to ONE address; never send two spellings.
   - **`EMAIL ENRICH: HOLD`** (catch-all/inconclusive domain, or the
     verifier unavailable) → no confirmable mailbox; fall through to the
     manual note.
   - **`EMAIL ENRICH: NONE`** (nothing verified, or a free-provider domain
     that can't be guessed) → fall through to the manual note.
   - **`EMAIL ENRICH: APPROVAL REQUIRED`** (Apify's estimated cost for this
     batch is unknown or over $0.10) → do NOT retry it yourself. Ask
     Haytham for the go-ahead, quoting the estimate; only re-run with
     `--approve-cost` once he says yes. Treat the lead as still needing
     enrichment in the meantime (same as HOLD) — never guess an address to
     route around the gate.
   Skip enrichment for a Lane 2/3 lead — it never gets a cold send, so don't
   spend a verify call.
5. Enrichment came up empty (HOLD/NONE) → set Notes first line "email not
   found — enrichment attempted, no verified candidate; freebie opt-in
   needed" and leave Status = Qualifying. The freebie opt-in is Haytham's
   manual step.

**Two checks, in order — the first is free, the second is the send gate:**

a. **Shape (free):** `python main.py email-check <address> --name "<Contact
   Name>"` — quote the line. FAIL (typo/dead domain, no-reply, disposable)
   = unusable, never enters the Email property: keep hunting or fall to
   step 4 (enrichment). PASS/WARN = well-formed enough to verify.

b. **Deliverability (Lane 1 only — this is the gate):** for a Lane 1 lead
   that will actually get a send, confirm the mailbox accepts mail BEFORE
   the lead is declared sendable. `email-check` is syntax+MX only and has
   PASSED for addresses that then hard-bounced at Touch 1 — one bounce
   burns the sending domain. Run:
   ```bash
   python main.py email-verify <address>
   ```
   (one address, one Apify/MillionVerifier call by default — cheap enough
   at this volume to clear the cost gate automatically; falls back to
   ZeroBounce on its own if Apify is near its monthly cap). Act on the
   literal line:
   - **`EMAIL VERIFY: PASS`** → check the `Email Verified` box on the row.
     This is the only thing that checks it automatically.
   - **`EMAIL VERIFY: FAIL`** (invalid/disposable) → the address bounces;
     do NOT log it as sendable. Keep hunting (step 3) or fall to step 4
     (enrichment).
   - **`EMAIL VERIFY: WARN`** (catch_all/unknown, or the verifier
     unavailable) → leave `Email Verified` unchecked; Notes first line
     "deliverability inconclusive (<reason>) — Haytham's call before
     send." Not auto-sendable; he finds a better address or checks the box
     by hand to accept the risk.
   - **`EMAIL VERIFY: APPROVAL REQUIRED`** (should not happen at
     single-address volume, but fails closed if it does) → do NOT retry
     yourself; ask Haytham for approval, quoting the estimate, then re-run
     with `--approve-cost` only once he says yes.

   Skip (b) for Lane 2/3 — they never get a cold send, so don't spend a
   verify call on them.

**Status promotion (Lane 1):** a lead reaches **Audit Ready** only when
BOTH `Finding Verified` and `Email Verified` are checked. If the address is
FAIL / WARN / not-found, `Finding Verified` stays checked but Status
**holds at Qualifying** with the reason above — Audit Ready must mean
"sendable pending only the hook." One verified address per lead — never the
same opener to two guessed spellings.

If the email came from a source the walk flagged as broken/suspect, Status
stays Qualifying and that flag goes in Notes as the FIRST line.

## Step 6 — The draft → Gmail, held until the hook is resolved

**Check the `SMYKM hook:` line just written in Step 4 before doing anything
else here.** If it still reads `not run yet — see haytham-hook-finder`,
**stop — do not invoke haytham-email-draft, do not create a Gmail draft.**
Append to Notes: `Hook not yet found — run haytham-hook-finder, then ask to
draft this lead's email.` Report this lead's DRAFT status as "held — needs
haytham-hook-finder" and move on. This applies to every fresh lead, since
opener-finder always writes that placeholder — a Gmail draft only gets
created once Haytham has explicitly run `haytham-hook-finder` on this lead
(producing either a real hook or a confirmed "no hook found") and then asks
for the draft.

Only once the hook line reads `no hook found in public evidence...` or
holds an actual hook, and there's a usable, non-suspect email address,
invoke the **haytham-email-draft** skill for the Touch 1 opener (it reads
`references/uae-track.md` for this track's rules). Full silent loop, voice
rules, gate — as that skill specifies. Additionally, before creating the
draft, dump the fresh row to JSON and run `python main.py crm-gate send
<row.json> --sends-today N --touch 1 --followups-due M --inbox "<the
lead's Inbox>"` (assign the inbox first if the row's `Inbox` is blank:
`python main.py inbox route`, write the label back; N = today's TOTAL
sends out of THAT inbox, from its own sent count — `python main.py inbox
counts` gives Inbox 2's number and the query for Inbox 1; M = follow-ups
still owed today on that inbox — they eat its budget before any opener;
uae-tick owns both numbers on a normal day) — a FAIL means the lead isn't
actually sendable (finding
unverified, address unverified/`Email Verified` unchecked, no address, or
no opener headroom left under the ceiling) and the draft holds with that
reason. On a lead worked through Step 5 the `Email Verified` box is already
set, so the gate's deliverability check passes here — it's the backstop for
a row that skipped or failed that step.

Then, without waiting for approval:
- Pick the variant that came through the gate strongest and **create the
  Gmail DRAFT** (never send) to the lead's address with that subject and
  body. Haytham reviews, edits, and sends from Gmail by hand.
- Set Status = `Draft Ready` (the status that means "hook resolved, draft
  sitting in Gmail") and append one line to the lead's Notes: `Gmail
  draft ready (Touch 1) — "<subject>" — <date>`. Do NOT touch Touch #,
  Last Contacted, or the Email Thread Log — those record sends, and
  nothing has been sent. (`Outreach Sent` is set only when the message
  actually departs; uae-tick reconciles Draft Ready/Scheduled rows
  against Gmail every morning.)
- In the verdict, show the drafted variant in full plus the runner-up
  variants labeled, so he can swap in Gmail if he prefers another.

Held instead of drafted (say which and why): hook not yet resolved,
suspect-source address, generic address when the finding is personal,
crm-gate send FAIL, or the email-draft gate never passed.

Logging ("log this" / tick reply detection) still happens ONLY when
Haytham confirms an email actually left. A Gmail draft is not a send.

## Hard rules

- Never send an email. Gmail drafts only. Sending is Haytham's hand.
- Never log in to, act as, or automate anything through Haytham's own
  accounts on any platform (Instagram and LinkedIn included) — that
  identity / account-safety rule is what the IG ban was about, and it
  outlives the banned account. It is NOT a blanket ban on Instagram as
  data: read-only public data through a no-login third-party tool is fine,
  Instagram the same as the rest. (This skill walks funnels and does not
  hook-find; IG enrichment lives in `haytham-hook-finder`.)
- Never invent findings; a walk with nothing that survives the vision pass
  and both filters is Lane 2 or Lane 3, not a manufactured leak.
- A machine flag that failed visual confirmation is dead. It does not get
  resurrected as a hedge ("might also be…") in the email.
- **The vision pass is a computed fact, not a claim.** `python main.py
  vision check evidence/<slug>` is the only source of truth for "read every
  image." A verdict, a Notion write, or a chat report that says "N
  screenshots read" without that exact command having printed `VISION
  PASS: COMPLETE` first is a false statement, full stop.
- **`Finding Verified` is checked only on a visually-confirmed Lane 1
  finding.** It is a send gate. Checking it to make a lead sendable is
  the exact corruption this track's data cannot survive.
- **`Email Verified` is checked only on an `EMAIL VERIFY: PASS`** (or by
  Haytham's hand to accept a catch_all/unknown risk). It is the other send
  gate — `email-check` PASS (syntax+MX) is NOT enough; it cleared two
  addresses that then hard-bounced. A bounce burns the sending domain,
  so checking this box on an unverified address is the same class of
  corruption as faking `Finding Verified`.
- This flow does not find a SMYKM hook — that's `haytham-hook-finder`,
  triggered manually by Haytham, from cited public evidence.
- **Never invoke haytham-email-draft or create a Gmail draft while the
  `SMYKM hook:` line still reads "not run yet."** That line means the hook
  hasn't been looked for, not that none exists.
- Never write a UAE lead into the parenting DB, or vice versa.
- One lead's full run ends with: gate verdicts, lane verdict, strongest
  finding, innocent explanation, Finding Verified state, SMYKM hook status
  ("not run yet" means the draft is held, not that it went out anyway),
  email address status, the literal `VISION PASS: ...` line,
  rejected-flags count, and the Gmail-draft status. That's the complete
  hand-off.
