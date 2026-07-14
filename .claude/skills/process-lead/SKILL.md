---
name: process-lead
description: Take a sourced UAE coach lead (name + site URL, usually from the UAE Lead CRM's Walk Queue) through the machine walk, vision pass, Gate 0 floors, and opener-finder walk, logging everything to the UAE Lead CRM. Use this skill WHENEVER Haytham pastes a new lead — a name, a site URL, a LinkedIn profile, optionally notes or screenshots — or says "process this lead," "run this one," "walk this one," "new lead," or pastes several candidates. It runs the machine funnel walk (Firecrawl-primary fetch, Python-owned scope/analysis, Playwright fallback), does the mandatory vision pass over the screenshots, enforces the UAE Gate 0 floors, logs to the UAE CRM, and hands the evidence to the opener-finder. The Gmail DRAFT step is held until `haytham-hook-finder` has resolved the SMYKM hook line for this lead — it never drafts on a fresh "not run yet" hook. It never sends anything, and never logs in to or automates anything through Haytham's own platform accounts.
---

# Process Lead — intake → walk → vision pass → Notion → opener → (hook-finder) → Gmail draft

One command per candidate. Sourcing is web-native now (`source-leads` skill,
five channels — directories, Google footprint, LinkedIn, podcasts/events,
lateral); this skill takes over the moment a candidate has a name and a
site URL.

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

## Step 1 — Machine walk (Firecrawl-primary)

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

**4. Loop.** Fetch each `funnel_links` entry the same way (steps 1-2),
capped at `MAX_PAGES` (16). Then the checkout-hop pass: for every page
fetched so far, `python main.py discover-checkout
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

**Known gap — CTA click-discovery.** The JS-button click-discovery and
booking-widget-interaction logic (clicking buttons on bio-link aggregators
and sales/course/booking pages to find hidden destinations) needs a live,
interactive browser session, which a stateless Firecrawl scrape can't
replicate. `cta_clicks` is always `[]` for Firecrawl-fetched pages —
`packet.md` will read "not run (Firecrawl-fetched)" rather than silently
claim a clean result. This is expected, not a bug.

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

## Step 2 — Gate 0 (the UAE floors)

The packet + vision pass give the machine half (`audit/gates.py`: entry
link, funnel floor, audience floor). Complete the rest by judgment:

- **UAE-based**: physically in Dubai, Abu Dhabi, Sharjah, or elsewhere in
  the UAE — About page, LinkedIn location, event appearances. "Serves the
  region" does not count. Set the City property while you're there.
- **Activity floor**: posted, emailed, or launched something in the last
  **30 days**. One web search on the lead's name + niche/city is required,
  not optional — the search is what actually tells you if she's active.
- **Funnel floor**: a live sales page, checkout, course, or paid digital
  offer exists (the crawl usually settles this). Call-only with nothing
  digital = fail.
- **Audience floor**: **1,500+** on their largest owned or social channel.

Any floor failed → set `Gate 0` = Fail, `Status` = Disqualified, one-line
reason in Notes (properties only, no body), and stop. The floor exists to
protect walks and touches — every opener under the send ceiling needs a verified finding, so walks are the bottleneck
by design.

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

Follow that skill exactly: Gate 1, 5-stop walk, sting test + vitamin
filter, lane classification, opening angle + innocent explanation. Only
visually-confirmed findings enter the filters. Bank every finding that
survives both filters, ranked strongest first — the body's Findings Bank
section plus the `Findings Bank` property (`N. UNUSED | finding` lines the
send gate parses); #1 is the opener, the rest is Touch 2/3 material that
must not be discarded. Write the page body and
properties to the UAE CRM in the exact schema.md format, including the
Evidence section with the literal vision-check line. `Finding Verified`
gets checked ONLY for a Lane 1 lead with a visually-confirmed finding —
it is the hard send gate. The `SMYKM hook:` line gets written as the
placeholder `not run yet — see haytham-hook-finder`. **This placeholder
blocks Step 6 below.** `haytham-hook-finder` is a separate, manual step
Haytham runs on this same lead to clear the block — its evidence sources
are LinkedIn, podcasts, YouTube, the About page, and read-only no-login
Instagram data (via a third-party actor, never logged in as Haytham).

## Step 5 — Email address

Work the Email OS decision tree with what the packet harvested:
1. Personal-looking address from the crawl → use it.
2. Generic (info@/contact@) → use only if nothing better.
3. Nothing harvested → web search (`"[name]" email contact`), LinkedIn
   contact info if publicly visible, podcast/YouTube show notes.
4. Still nothing → set Notes first line "email not found — freebie opt-in
   or pattern-guess+verify needed" and leave Status = Qualifying. The
   freebie opt-in and verification are Haytham's manual steps.

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
<row.json> --sends-today N --touch 1 --followups-due M` (N = today's TOTAL
sends out of the inbox, from Gmail's sent count; M = follow-ups still owed
today — they eat the budget before any opener; uae-tick owns both numbers
on a normal day) — a FAIL means the lead isn't actually sendable (finding
unverified, no address, or no opener headroom left under the ceiling) and
the draft holds with that reason.

Then, without waiting for approval:
- Pick the variant that came through the gate strongest and **create the
  Gmail DRAFT** (never send) to the lead's address with that subject and
  body. Haytham reviews, edits, and sends from Gmail by hand.
- Append one line to the lead's Notes: `Gmail draft ready (Touch 1) —
  "<subject>" — <date>`. Do NOT touch Status, Touch #, Last Contacted, or
  the Email Thread Log — those record sends, and nothing has been sent.
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
  finding.** It is the send gate. Checking it to make a lead sendable is
  the exact corruption this track's data cannot survive.
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
