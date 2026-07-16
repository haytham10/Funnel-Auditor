---
name: source-leads
description: Fill and keep filling the UAE Lead CRM's top of funnel, web-natively. One job — collect raw candidates into the CRM as Sourced (name + Site URL required), no judgment, no funnel walks, no gating. Two volume profiles — a bootstrap run (one-time, 60-70 raw names to fill an empty CRM) and top-up (the everyday tap: a small, lightweight, repeatable run you fire any day for the life of the track). Use WHENEVER Haytham says "source leads," "sourcing day," "fill the pipeline," "top up," "source me 20," "find more coaches," "grab some fresh leads," or names a sourcing channel to work (ICF directory, Google footprint, LinkedIn, podcasts, lateral). Works the five channels via Firecrawl search/scrape, with the Google footprint channel run harder via `apify footprint` (subdomain + "powered by" footer-signature queries across platforms and emirates, merged with Firecrawl) — it never sources from Instagram (not a cold-sourcing channel for this track), never logs in anywhere, and never acts as Haytham on any platform. It does NOT qualify or gate the rows it logs — that is the separate `qualify-leads` skill — and it does not walk funnels (that's batch-audit/process-lead after qualifying) and it never sends anything.
---

# Source Leads — the sourcing engine, as a skill

**One job: collect raw candidates into the CRM as `Sourced` rows.** No
judgment, no gating, no funnel walks. Speed and volume are the deliverable.
Gating those rows (Gate 0 + Gate 1 → `Qualifying`/`Disqualified`) is a
separate skill, `qualify-leads`; walking the survivors is a third
(`batch-audit`/`process-lead`). This skill stops at a logged `Sourced` row.

**Two volume profiles, same mechanics.** The work is identical either way —
same channels, same `Sourced` logging, same no-judgment discipline. Only
the size and cadence differ:

- **Bootstrap** — the one-time fill of an empty CRM. High volume: 60-70 raw
  names in a run, mining the back-catalog of every channel. Run once to get
  the track off the ground.
- **Top-up** — the everyday tap that keeps the pipeline alive after the
  bootstrap. Small and repeatable: ~15-20 raw names, fired on demand any
  day ("source me 20," "top up," "find more coaches"), biased to what's NEW
  since last time. This is the profile you run 99% of the time.

If Haytham names a number, use it. If he says "fill the pipeline" / "sourcing
day" on an empty or near-empty CRM, that's bootstrap volume. Otherwise
("top up," "source me N," "find more") it's top-up volume — see the
**Top-up discipline** section, which adds four rules on top of everything
below.

**CRM (all writes):** `collection://5efbdd9b-1e19-468c-96db-f94a525846e0`
(REST API database ID: `5a9fc583160046d1a64c4e65cc804229`).
**Never write to the parenting DB** (`c6209e29-55ef-4781-b735-73b2a254e34f`).

The ICP, one line: a UAE-based solo coach or course creator with a real
funnel or paid digital product, active in the last 30 days, operating in
English. Full targeting spec: `docs/uae-track/03-targeting-and-sourcing.md`.

---

## Before the run — two one-time checks

**Dedup first, once:** pull the CRM's existing Contact Names + Site URLs
in one SQL query at the start of the run. Skip anything already logged,
in any status. Never create a duplicate row.

**Check the Apify quota once, up front, if this run will touch channel 2:**
`python main.py apify limits`. `apify search`/`apify footprint` are cheap
(~$0.002 per search call; `footprint` is two search calls per platform,
one for markerless skool — confirmed 2026-07-16), but they still draw off
the same small monthly USD budget everything else on this layer shares. If
`near_cap` is `true`, skip the Apify side of channel 2 for the whole run
and work it on `firecrawl_search` alone (still run the footer-signature
queries there) — note it in the run report, don't silently degrade.

---

## The five channels (work them in this order)

1. **Coach directories (highest density, start here).** `firecrawl_scrape`
   / `firecrawl_crawl` the ICF UAE chapter directory and regional coach
   directories/marketplaces. Directory listings almost always carry name,
   city, specialty, and a site link — exactly the intake fields.
2. **Google footprint (proof of a paid product baked in — one of the two
   best channels, treat it that way).** A platform footprint IS a funnel,
   so every hit here comes pre-passed on the Gate 0 funnel floor. Work it
   two ways at once, because they find two different, barely-overlapping
   segments (confirmed 2026-07-16):
   - **Subdomain** (`site:mykajabi.com coach Dubai`) catches coaches on
     the FREE default platform subdomain — often the less-established end.
   - **Footer signature** (`"powered by kajabi" coach Dubai`, NOT
     site-scoped) catches coaches on a CUSTOM domain still running the
     platform underneath — the more-invested, often BETTER end, which the
     subdomain query is 100% blind to. (This surfaced achievher.com, a
     real Dubai somatic coach with a named method, that `site:mykajabi.com`
     never sees.)

   **Run the Apify side with one command — it does both shapes, merges,
   dedupes by host, and drops noise:**
   ```
   python main.py apify footprint <platform> --geo <Dubai|Abu Dhabi|Sharjah|UAE> [--role coach]
   ```
   Platforms: `kajabi teachable thinkific podia systeme kartra skool`
   (skool has no footer marker, so it runs the subdomain shape only). Each
   hit is tagged `foundVia: subdomain|footprint` and carries
   `emphasizedKeywords` — a footprint hit whose emphasizedKeywords
   actually contains "Powered by <platform>" is a real match, not a Google
   guess; that's your false-positive filter. Set the Platform property from
   which command found it, while it's free.

   **Run `firecrawl_search` alongside it on the footer-signature query**
   (`"powered by kajabi" coach Dubai`) — the two engines return
   near-different result sets, so Firecrawl nets custom-domain coaches
   Apify's SERP missed and vice versa. Merge both into the Apify result and
   dedupe by host before triage.

   **Rotate the geo, don't anchor only on Dubai.** Run each platform across
   `Dubai`, `Abu Dhabi`, `Sharjah`, and a plain `UAE` pass — anchoring only
   on "Dubai" silently undercounts the other emirates. `--geo` takes any of
   these.

   **The wider net needs tighter confirmation.** Footer-signature catches
   more, including non-UAE and non-solo hits (a UK sports-coaching *group*
   came through a Kajabi footer once). Do not log a footprint hit on the
   marker alone: confirm UAE-based and solo the same way as any other
   candidate before it gets a row. The subdomain shape is safer on geo
   (the `--country ae` bias plus the platform host), the footer shape is
   the one to double-check.

   **Query expansion (optional, when a platform+geo runs thin):** add
   `--meta` to `apify search` to pull Google's `relatedQueries` and
   `peopleAlsoAsk` for the query — real adjacent search terms to feed the
   next pass, cheaper than guessing.
3. **LinkedIn (the UAE unlock).** `firecrawl_search` for UAE coaches
   announcing programs/cohorts, then fetch what's PUBLIC. LinkedIn walls
   most content — take what renders, log the profile URL, move on.
   **Never log in, never use Haytham's account, never automate anything
   through it.** If a candidate looks strong but everything is walled,
   log them anyway with what's known; qualifying can dig later.
4. **Podcasts and events (pre-qualified for ambition).** `firecrawl_search`
   Dubai/UAE business podcasts' guest lists, event speaker pages, then
   follow the "where to find me" links to their sites.
5. **Lateral discovery.** From every good candidate found above: who they
   collaborate with, get interviewed by, or are recommended alongside.
   Follow the thread — each good lead is the next anchor.

---

## What gets logged per candidate (Status = Sourced)

Contact Name, Site URL, Profile URL, City if stated, Coach Type best
guess, Platform if obvious, Audience Size if visible for free, Source
Channel, Status = `Sourced`. Nothing else. No page body, no notes
essays. Speed is the deliverable.

**Site URL is required to log the row (2026-07-14).** It is the one
field the rest of the machine cannot work without, and the first
bootstrap proved the failure mode: 78 rows landed as name-only shells (0
site URLs), which just moved the entire enrichment cost into qualifying
and left the Walk Queue empty. A candidate whose site you can't find in
one obvious hop (their directory entry's link, their LinkedIn contact
section as rendered, one `firecrawl_search` on the name) does NOT get a
CRM row — list them at the end of the run report under "seen, no site
found" so the name isn't lost, and move on. Grab the audience number
whenever it's visible at zero extra cost; never guess it.

Create rows in batches (notion-create-pages takes multiples), not one
call per lead.

Do NOT qualify, do NOT walk funnels, do NOT reject anyone except obvious
non-candidates (not a coach, not plausibly UAE, no site at all). The gates
are `qualify-leads`'s job, on the `Sourced` rows this skill leaves behind.

---

## Top-up discipline (the everyday profile)

Top-up is sourcing shrunk and made repeatable — everything above still
applies, at ~15-20 names instead of 60-70. Four extra rules keep it useful
for the life of the track in a finite market. (On a one-time bootstrap
run, skip this section and just mine volume.)

**1. Volume: small by default.** ~15-20 raw names, or whatever N Haytham
names. The Walk Queue drains at up to ~20/day (the send ceiling's pace); a
top-up exists to refill a day or two of that, not to overflow it.

**2. Source the flow, not the stock.** This is the anti-exhaustion rule
and the reason top-up stays useful for a year. The UAE / English / solo
market has a FINITE stock of coaches — re-mine the same ICF directory
every week and it dries up in a month. So top-up biases to what is NEW
since last time: recently-added directory entries, podcast episodes from
the last few weeks, "just launched / now enrolling / new cohort" LinkedIn
posts, fresh platform footprints. Use recency in the searches (recent
posts, recent episodes, current launches). A bootstrap run mines the
back-catalog once; top-up skims the new arrivals. A top-up run that just
re-scrapes the same back-catalog and leans on dedup to discard it has
drifted — you are burning fetches to find nothing new.

**3. Default to the Google footprint channel; rotate WITHIN it.** Unless
Haytham names a channel, a top-up works **Google footprint (channel 2)**
by default — it's one of the two best channels, a hit here is pre-passed
on the funnel floor, and it has enough internal variety to be the everyday
default without drying up: 7 platforms (kajabi/teachable/thinkific/podia/
systeme/kartra/skool) × 4 geos (Dubai/Abu Dhabi/Sharjah/UAE) × both query
shapes (subdomain + footer signature) = a large rotation surface. So the
staleness logic moves DOWN a level: instead of picking the stalest
*channel*, pick the stalest **platform × geo combo** inside footprint —
the combos whose most-recent `Sourced` row (by Created time, or by the
Platform/City it produced) is oldest, or that have never been run. Lean to
the footer-signature shape and recency (rule 2) so each pass skims new
custom-domain arrivals, not the back-catalog.

**When to leave footprint for the day:** if footprint's dedup rate comes
back high (rule 4 — most hits already in the CRM), that combo set is
drying for now. Fall back to the old channel-level staleness rotation:
pick the stalest OTHER channel (directories, LinkedIn, podcasts/events,
lateral) by each channel's most-recent row Created time, and work that
instead. Footprint is the default, not a cage — a drying signal means
rotate out.

If Haytham names a channel ("top up from podcasts"), work that one and
skip all of this.

**4. Dedup against EVERY status, Disqualified included.** Same one-time
dedup pull as above, but be explicit: skip a name/site already in the CRM
in ANY status — Sourced, Qualifying, Disqualified, anything. A coach you
already killed must not come back as a fresh Sourced row. (Future hook,
not built yet: leads that failed Gate 0 only on activity or audience — not
niche or geography — are recheck-later candidates, since a dormant coach
may relaunch; a hard niche/geo Disqualified is dead for good.)

---

## The run report

One message: how many logged per channel, total in CRM at `Sourced`, any
channel that came up dry (and why, one line), and whether the volume target
was hit (60-70 for a bootstrap run, the named N or ~15-20 for a top-up). If
it wasn't, say what's left to try — don't quietly stop short.

**On a top-up run, also report:** which channel worked and why (footprint
by default — name the platform × geo combos run; or the stalest other
channel if footprint was drying or Haytham named one), and how many
candidates were seen-but-skipped as already-in-CRM duplicates. The dedup
rate is the early warning that a channel or combo is drying up — call it
out if it's high, since that's the trigger to rotate off footprint.

Every run ends the same way: these `Sourced` rows now need `qualify-leads`
(Gate 0 + Gate 1) before they reach the Walk Queue. Say so.

---

## Hard rules

- **Never source from Instagram.** Sourcing died there once — browsing as
  Haytham got the account banned — and this whole skill exists because of
  it. This is a *sourcing* exclusion only; it does not touch the separate
  enrichment rule, where read-only no-login IG data is a valid hook source
  (see `haytham-hook-finder`). What is banned is logging in or acting as
  Haytham, on IG or anywhere.
- **Never log in to, act as, or automate anything through Haytham's
  accounts on any platform.** Read-only public fetching via Firecrawl is
  the ceiling. LinkedIn especially: public pages only.
- **This skill sources; it never gates.** It logs `Sourced` rows and stops.
  Running Gate 0/Gate 1, promoting to `Qualifying`, or killing to
  `Disqualified` is `qualify-leads`'s job — do not drift into it. (Lateral
  discovery inside a sourcing run is still sourcing.)
- No funnel walks. The walk is batch-audit's job, on Qualifying rows, with
  the vision gate. A sourcing fetch that turns into a 10-page crawl has
  drifted — stop it.
- Never invent a candidate, a city, or an audience number. Unknown is a
  fine value; a guessed one poisons Gate 0 downstream.
- Never write to the parenting DB, and never source parenting/faith leads
  into this CRM — that niche is closed.
- Out of scope stays out: agencies/teams, non-English funnels, coaches
  outside the UAE however adjacent. Do not dilute the geographic thesis.
