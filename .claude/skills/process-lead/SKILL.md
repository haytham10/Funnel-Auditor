---
name: process-lead
description: Take a sourced Instagram lead from raw intake (name + bio link + follower count) through the machine walk, vision pass, floors, and opener-finder walk, logging everything to Notion. Use this skill WHENEVER Haytham pastes a new lead — a handle, a link-in-bio URL, a follower count, optionally notes or screenshots — or says "process this lead," "run this one," "new lead," or pastes several candidates from a sourcing session. It runs the machine funnel walk (Firecrawl-primary fetch, Python-owned scope/analysis, Playwright fallback), does the mandatory vision pass over the screenshots, enforces the Gate 0 floors, logs to the Notion pipeline, and hands the evidence to the opener-finder. The Gmail DRAFT step is held until `haytham-hook-finder` has resolved the SMYKM hook line for this lead — it never drafts on a fresh "not run yet" hook. It never sends anything and never touches Instagram.
---

# Process Lead — intake → walk → vision pass → Notion → opener → (hook-finder) → Gmail draft

One command per candidate. Haytham sources on Instagram by hand (that stays
manual — no IG automation, ever); this skill takes over the moment he has a
candidate's public info.

## Input

Minimum: a link-in-bio / site URL. Wanted: contact name, IG profile URL,
follower count. Optional: email if already known, niche hint, his own notes,
Source (how he found them).

**The sourcing contract (IG evidence).** At sourcing time Haytham attaches
his IG screenshots (profile header, recent posts grid, link-in-bio screen,
anything he clicked) directly to the lead's Notion page body. That is the
system's only window into Instagram — it must NEVER fetch instagram.com
itself. In chat he may paste screenshots instead; pasted evidence counts the
same and outranks everything.

If several leads are pasted at once, process them one at a time, start to
finish, and give a one-line verdict per lead at the end. (For batches already
logged in Notion, the batch-audit skill is the entry point — it parallelizes
with one lead-processor agent per lead.)

If only an IG profile URL is given with no bio-link URL: do NOT try to fetch
Instagram. Run a web search for the person instead; if that surfaces their
site/linktree, use it. Otherwise ask for the link in their bio — that's the
one thing only he can see.

## Step 0 — Pull the lead's Notion page + IG evidence

If the lead exists in the pipeline (batch runs always; chat runs when he
pastes a Notion URL), fetch the page first:

1. `notion-fetch` the lead page. Properties are the intake of record; the
   page body may already hold an old walk (you will overwrite it fresh).
2. **Compute the slug now, once, the same way the crawler will:**
   `python main.py slug "<Contact Name>"` (falls back to handle or URL if no
   name yet). Use this exact slug for every evidence path below — the
   Firecrawl fetch loop's screenshots/manifest, `discover-links`'s HTML
   files, `ingest --out evidence/<slug>`, and (if you fall back) `walk
   --out evidence/<slug>`. This is not optional — a hand-guessed slug is
   exactly what put a real lead's IG screenshots in
   `evidence/momhoodmentor/ig/` while the crawler wrote its packet to
   `evidence/lynsey-ward/`, two different folders the vision gate
   (Step 1.5) can't reconcile, silently dropping the IG images out of the
   completeness check entirely.
3. Collect every image in the page body — these are the sourcing
   screenshots. The fetch returns signed file URLs (file.notion.so /
   secure.notion-static.com). Download each one now (`curl -o
   evidence/<slug>/ig/<n>.png "<signed url>"`) — the URLs expire, so don't
   defer.
4. Run `python main.py vision init evidence/<slug>` — this registers every
   file just downloaded as a required, unread image. Then **Read every
   downloaded image, and immediately after each one, run
   `python main.py vision mark evidence/<slug> ig/<n>.png`.** Do not batch
   the marking to the end and do not read one image and assume the rest —
   each image gets its own Read call and its own mark call, in that order,
   before moving to the next.
5. What to pull from the IG screenshots: last-post recency (activity floor),
   follower count if the property is empty, the bio promise vs. where the
   bio link actually goes, and SMYKM hook material (a recent post topic, a
   named framework, a launch, a personal update). **Any SMYKM hook that
   names a specific post's content, date, or engagement numbers is only
   usable if that exact image is marked read** — see the hard rule at the
   bottom of this file.

No images attached and none pasted → proceed site-only, but carry the flag
"IG evidence: none attached — site-only walk" into the Notion body and the
final verdict so Haytham knows this call is weaker. Skip `vision init`/`mark`
for the ig/ portion in this case; the site portion in Step 1.5 still applies.

## Step 1 — Machine walk (Firecrawl-primary)

```bash
pip install -q -r requirements.txt   # first run only
```

Firecrawl (the MCP tools already connected this session) is the primary
fetcher — cheaper, faster, and better at bot walls/JS-rendered pages than
the local Playwright browser. Python still owns every decision about
scope, priority, and analysis; you're only driving the fetch. See
`.claude/skills/firecrawl` for the tool reference. Always use the exact
slug from Step 0.2 for every path below — same reason as before: IG
screenshots and the crawl's own screenshots must land in the same folder.

**1. Fetch the bio-link URL.** `firecrawl_scrape` with `formats: ["html",
"screenshot"]`, `screenshotOptions: {fullPage: true}` (default desktop
viewport). Save the HTML to `evidence/<slug>/_firecrawl_raw/1.html`. Save
the screenshot to `evidence/<slug>/screenshots/<name>` using the exact
filename from `python main.py screenshot-name <url> desktop` — never
hand-guess the filename, the packet renderer and vision-gate matching
depend on it being exact.

**2. Mobile screenshot, only for required stop types.** If this stop's
link_type will be `bio_page`, `sales`, `course`, `checkout`, or `booking`
(`REQUIRED_MOBILE_TYPES` — same scope as the mobile-screenshot rule
below), run a second `firecrawl_scrape` with `mobile: true, formats:
["screenshot"]`, save it via `python main.py screenshot-name <url>
mobile`. Skip this call for stops outside that list. On booking/checkout
stops, pass `waitFor: 4000` or so — approximates the old iframe-attach
wait for Calendly-style embeds that load async.

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
python main.py ingest evidence/<slug>/manifest.json --name "<Name>" --handle "<@handle>" --followers <N> --out evidence/<slug>
```

This produces `evidence/<slug>/packet.md`, `evidence.json`, per-page text
files, and a refreshed `vision_manifest.json` — byte-identical contract to
the old `python main.py walk`, regardless of which layer fetched the
pages.

**Known gap — CTA click-discovery.** The JS-button click-discovery and
booking-widget-interaction logic (clicking buttons on Stan-style bio
aggregators and sales/course/booking pages to find hidden destinations)
needs a live, interactive browser session, which a stateless Firecrawl
scrape can't replicate. `cta_clicks` is always `[]` for Firecrawl-fetched
pages — `packet.md` will read "not run (Firecrawl-fetched)" rather than
silently claim a clean result. This is expected, not a bug.

**Fallback to Playwright.** If Firecrawl fails outright on a page after
retry (persistent block even with `proxy: stealth`), or the platform is a
bio-link aggregator with no anchor-discoverable products (exactly the
condition the click-discovery logic exists for), fall back to the
original path for this one lead instead of fighting it further:

```bash
python main.py walk <bio-link-url> --name "<Name>" --handle "<@handle>" --followers <N> --out evidence/<slug>
```

Say so plainly in NOTES when you fall back — this keeps click-discovery
reachable for the leads that actually need it, rather than losing it
silently.

If the crawl errored on the bio page, that is itself a possible Tier A
finding (verify: hard 404 vs bot wall vs permission wall — the screenshot
tells you which) — don't abandon the lead.

## Step 1.5 — The vision pass (mandatory, machine-checked, not self-reported)

The packet's machine checks are pattern-matchers; they misfire and they miss.
You have eyes — use them the way Haytham does when he clicks through by
hand. This step used to be enforced by instruction alone ("read every
image") and a real run reported "4 screenshots read" in its final verdict
when only 1 of 4 had actually been opened. It's enforced by a script now,
not by trusting your own summary.

**Read, as images, the desktop screenshot of EVERY crawled page**, plus the
mobile screenshot of the bio page and of every offer/checkout/booking page.
Read the full text files of the sales/freebie pages — copy is where
non-mechanical leaks live. Run `python main.py vision list evidence/<slug>`
first to see the exact list of paths this crawl requires.

**After each image Read, immediately run
`python main.py vision mark evidence/<slug> <path>`** (batch several paths
in one call if you just read several in a row — same rule, no deferring to
the end). Do this for every IG image from Step 0 too if you haven't already.

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
   an empty or stuck calendar, a hero promising a program the links don't
   sell, placeholder/lorem content, a checkout asking for trust the page
   hasn't earned, layout breakage on mobile, stale dates baked into images,
   a freebie button that goes nowhere. These are exactly the leaks Haytham
   catches manually — this pass is what replaces his click-through.

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

## Step 2 — Floors (Gate 0, full version)

The packet + vision pass give the machine half. Complete the rest:

- **Activity floor**: IG screenshots first (post dates are usually visible) —
  only images already marked read in `vision_manifest.json` count as having
  been checked; an unmarked image cannot be the basis for "last post N days
  ago." Then one web search on the lead's name + niche/handle to corroborate
  — this search is required, not optional, even when the screenshot looks
  clear. Last visible activity within ~3 weeks? While there, collect SMYKM
  hook material (recent post, launch, named framework, personal update) —
  needed later, subject to the same read-before-cited rule in Hard rules.
- **Niche floor**: genuinely parenting or faith-based. Adjacent wellness
  without case-study fit = park.
- **Audience floor**: ~1K followers or an equivalent real audience signal.

Any floor failed → Lane 3. Create/update the Notion row (Lane 3 forces
Tier 4 + Status Disqualified, one-line reason in Notes, properties only, no
body) and stop. The floor exists to protect touches.

## Step 3 — Notion row

Pipeline data source (MCP): `collection://c6209e29-55ef-4781-b735-73b2a254e34f`.
Database ID (REST API): `78b26ebe-5b4f-4ff2-884a-3ccf369d00e6`.

Dedup per the opener-finder's rule: no routine pipeline query — only run one
targeted query if something feels off (name rings a bell, lead arrives with
no page link). If a row already exists, update it instead of creating one.

Create the row with what's known: Contact Name, Profile URL, Site URL,
Followers, Source, Email (if found — see Step 5), Status = Researching.

## Step 4 — The walk (judgment half)

Do not start this step until Step 1.5's `vision check` printed `VISION
PASS: COMPLETE` (or you've logged the unreadable-image exception). Pass
that literal line into the opener-finder invocation — it will not run a
lane classification without it.

Now invoke the **haytham-opener-finder** skill logic with:
- the evidence packet as Step A (the crawl + search layer, already done), and
- the vision pass + IG screenshots + any notes Haytham typed as Step B (the
  human-layer read — it OUTRANKS the machine text checks wherever they
  disagree, and Haytham's own typed notes outrank everything).

Follow that skill exactly: Gate 1, 5-stop walk, sting test + vitamin filter,
lane classification, opening angle + innocent explanation. Only
visually-confirmed findings enter the filters. Write the page body and
properties to Notion in the exact schema.md format, including the "IG
evidence" and rejected-flags lines. The `SMYKM hook:` line gets written as
the placeholder `not run yet — see haytham-hook-finder` — opener-finder no
longer finds a hook itself (split Jul 11, 2026). **This placeholder blocks
Step 6 below** — see that step for what happens next. `haytham-hook-finder`
is a separate, manual step Haytham runs on this same lead to clear the
block — it reuses the IG evidence already downloaded in Step 0, no
re-fetching needed.

## Step 5 — Email address

Work the Email OS decision tree with what the packet harvested:
1. Personal-looking address from the crawl → use it.
2. Generic (info@/contact@) → use only if nothing better.
3. Nothing harvested → web search (`"[name]" OR "[handle]" email contact`),
   podcast/YouTube show notes.
4. Still nothing → set Notes first line "email not found — freebie opt-in or
   pattern-guess+verify needed" and leave Status = Researching. The freebie
   opt-in and NeverBounce/Hunter verification are Haytham's manual steps.

If the email came from a source the walk flagged as broken/suspect, Status
stays Researching and that flag goes in Notes as the FIRST line.

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

Only once the hook line reads `no hook found in IG evidence...` or holds an
actual hook, and there's a usable, non-suspect email address, invoke the
**haytham-email-draft** skill for the Touch 1 opener. Full silent loop,
voice rules, gate — as that skill specifies.

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
suspect-source address, generic address when the finding is personal, or
the email-draft gate never passed.

Logging ("log this" / pipeline-tick reply detection) still happens ONLY when
Haytham confirms an email actually left. A Gmail draft is not a send.

## Hard rules

- Never send an email. Gmail drafts only. Sending is Haytham's hand.
- Never fetch, scrape, or automate anything on instagram.com. IG evidence
  comes only from screenshots he attached or pasted.
- Never invent findings; a walk with nothing that survives the vision pass
  and both filters is Lane 2 or Lane 3, not a manufactured leak.
- A machine flag that failed visual confirmation is dead. It does not get
  resurrected as a hedge ("might also be…") in the email.
- **The vision pass is a computed fact, not a claim.** `python main.py
  vision check evidence/<slug>` is the only source of truth for "read every
  image." A verdict, a Notion write, or a chat report that says "N
  screenshots read" without that exact command having printed `VISION
  PASS: COMPLETE` first is a false statement, full stop — this is what
  actually happened on Lynsey Ward (reported "4 screenshots read," 1 image
  had a Read call), and it is the one failure mode this file exists to
  close.
- This flow does not find a SMYKM hook — that's `haytham-hook-finder`,
  triggered manually by Haytham. If he runs it, that skill enforces its own
  rule: a hook citing specific IG post content (a quote, a date, an
  engagement number) is only usable if the image it came from shows
  `read: true` in `vision_manifest.json`. This flow never needs to
  construct or verify a hook itself.
- **Never invoke haytham-email-draft or create a Gmail draft while the
  `SMYKM hook:` line still reads "not run yet."** That line means the hook
  hasn't been looked for, not that none exists — a fresh lead always lands
  here after Step 4. Hold the lead at Step 6 and tell Haytham to run
  `haytham-hook-finder` first.
- One lead's full run ends with: lane verdict, strongest finding, innocent
  explanation, SMYKM hook status ("not run yet" means the draft is held,
  not that it went out anyway), email address status, IG-evidence status
  (**the literal `VISION PASS: ...` line**, not a paraphrase), rejected-flags
  count, and the Gmail-draft status. That's the complete hand-off.
