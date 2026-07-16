---
name: source-leads
description: Fill and keep filling the UAE Lead CRM's top of funnel. One job — collect raw candidates into the CRM as Sourced (name + a reachable link + audience size when findable), no judgment, no funnel walks, no gating. Sourcing is DYNAMIC — work whatever vein is producing UAE solo coaches with an audience and a way to get paid; the channel is not the point and there is no fixed rotation to follow. Two volume profiles — a bootstrap run (one-time, 60-70 raw names to fill an empty CRM) and top-up (the everyday tap: a small, repeatable run you fire any day). Use WHENEVER Haytham says "source leads," "sourcing day," "fill the pipeline," "top up," "source me 20," "find more coaches," "grab some fresh leads," or names a place to look. Works web search/scrape (Firecrawl), platform + link-in-bio footprints, and read-only no-login Apify actors (Google SERP, LinkedIn, Instagram) — it never logs in anywhere and never acts as Haytham on any platform. It does NOT qualify or gate the rows it logs — that is the separate `qualify-leads` skill — and it does not walk funnels (that's batch-audit/process-lead after qualifying) and it never sends anything.
---

# Source Leads — the sourcing engine, as a skill

**One job: collect raw candidates into the CRM as `Sourced` rows.** No
judgment, no gating, no funnel walks. Speed and volume are the deliverable.
Gating those rows (Gate 0 + Gate 1 → `Qualifying`/`Disqualified`) is a
separate skill, `qualify-leads`; walking the survivors is a third
(`batch-audit`/`process-lead`). This skill stops at a logged `Sourced` row.

**Two volume profiles, same mechanics.** The work is identical either way —
same dynamic sourcing, same `Sourced` logging, same no-judgment discipline.
Only the size and cadence differ:

- **Bootstrap** — the one-time fill of an empty CRM. High volume: 60-70 raw
  names in a run, mining hard across every vein. Run once to get the track
  off the ground.
- **Top-up** — the everyday tap that keeps the pipeline alive after the
  bootstrap. Small and repeatable: ~15-20 raw names, fired on demand any
  day ("source me 20," "top up," "find more coaches"), biased to what's NEW
  since last time. This is the profile you run 99% of the time.

If Haytham names a number, use it. If he says "fill the pipeline" / "sourcing
day" on an empty or near-empty CRM, that's bootstrap volume. Otherwise
("top up," "source me N," "find more") it's top-up volume — see the
**Dynamic sourcing discipline** section.

**CRM (all writes):** `collection://5efbdd9b-1e19-468c-96db-f94a525846e0`
(REST API database ID: `5a9fc583160046d1a64c4e65cc804229`).
**Never write to the parenting DB** (`c6209e29-55ef-4781-b735-73b2a254e34f`).

**The ICP, one line:** a UAE-based solo coach or course creator with an
**audience** and a **real way to get paid** — a funnel, a paid digital
product, OR a link-in-bio store (Stan / Beacons / Linktree) with a real
purchasable offer inside it. A big audience is a strong buy signal and
worth capturing every time, but it does NOT substitute for the offer: a
large following with no way to actually buy is not a lead for this track.
Full targeting spec: `docs/uae-track/03-targeting-and-sourcing.md`.

---

## Before the run — two one-time checks

**Dedup first, once:** pull the CRM's existing Contact Names + Site URLs
in one SQL query at the start of the run. Skip anything already logged,
in any status. Never create a duplicate row.

**Check the Apify quota once, up front, if this run will touch an Apify
actor** (`footprint`, `search`, `ig`, `li-posts`, `li-profile`):
`python main.py apify limits`. `search`/`footprint` are cheap
(~$0.002 per search call); **Instagram is the pricey actor** — use it
sparingly. All of them draw off the same small monthly USD budget. If
`near_cap` is `true`, skip the Apify actors for the whole run and work on
`firecrawl_search` alone — note it in the run report, don't silently
degrade.

---

## Where the leads are — work it dynamically, not by rotation

**The channel is not the point.** The point is UAE solo coaches with an
audience and a way to get paid. Below is a menu of veins that have produced
them, not an ordered checklist and not a rotation to march through. **Work
whatever is producing right now; when a vein dries (high dedup rate, mostly
noise), drop it and move to another.** Follow the leads, not the list. A
run that mechanically grinds one channel while it returns nothing new has
drifted — the discipline is to notice and switch.

Productive veins (reach for `firecrawl_search`/`firecrawl_scrape` first;
the no-login Apify actors where noted):

- **Platform footprint.** A platform footprint IS a funnel, so a hit here
  is pre-passed on the funnel floor. `python main.py apify footprint
  <platform> --geo <Dubai|Abu Dhabi|Sharjah|UAE> [--role coach]` runs two
  shapes and merges them: **subdomain** (`site:mykajabi.com coach Dubai`,
  free-tier coaches) and **footer signature** (`"powered by kajabi" coach
  Dubai`, custom-domain coaches the subdomain query is blind to — how
  achievher.com surfaced). Platforms: kajabi/teachable/thinkific/podia/
  systeme/kartra/skool. Run `firecrawl_search` on the footer query
  alongside it (near-different result sets, merge both). Each Apify hit is
  tagged `foundVia`/`emphasizedKeywords` (the false-positive filter — a
  footer hit whose keywords actually contain "Powered by <platform>" is
  real). `--meta` on `apify search` pulls relatedQueries/peopleAlsoAsk when
  a query runs thin.
- **Link-in-bio footprint.** Where the IG/DM-native coaches keep their
  money page. `site:stan.store`, `site:beacons.ai`, `site:linktr.ee` +
  coach + emirate/niche via `firecrawl_search`. The link-in-bio page **is**
  the funnel and is Firecrawl-scrapable — scrape it to confirm UAE + solo +
  a paid offer and grab the real name. This is the vein that catches
  exactly the coaches a domain-only search misses.
- **Coach directories.** ICF UAE chapter + regional coach directories /
  marketplaces (MantraCoach, Noomii, etc.). Listings carry name, city,
  specialty, and often a site link. Watch for profile-only entries with no
  real funnel — those fail the floor later, so grab the personal site if
  the listing has one, else treat as a name to resolve.
- **LinkedIn (read-only, no-login).** UAE professionals live here.
  `firecrawl_search` for coaches announcing programs/cohorts; `apify
  li-posts <url>` for recent-post signal. Take what's public, log the
  profile URL, move on. Never log in, never use Haytham's account.
- **Podcasts and events.** Dubai/UAE business podcast guest lists and event
  speaker pages are pre-qualified for ambition. Follow the "where to find
  me" link to their funnel.
- **Instagram, via no-login actor.** IG is a place coaches live, so it is a
  place to source — through the read-only actor only, never by logging in
  or acting as Haytham (see Hard rules). Firecrawl surfaces UAE-coach IG
  handles for free (reels, posts); `python main.py apify ig <profile-url>
  --mode details --raw` turns a handle into the three things that matter:
  **followersCount** (audience), **biography** (UAE + solo check), and
  **externalUrls** (the link-in-bio funnel = the Site URL). Cost-aware:
  harvest and vet handles for free first, then spend IG-actor calls only on
  the vetted ones.
- **Lateral.** From every good candidate: who they collaborate with, get
  interviewed by, or are recommended alongside. Each good lead is the next
  anchor — often the highest-yield vein once a run is warm.

**The wider nets (footer signature, link-in-bio, IG) need tighter
confirmation** — they catch non-UAE and non-solo hits too. Confirm
UAE-based and solo before a row, same as any candidate.

---

## What gets logged per candidate (Status = Sourced)

Contact Name, Site URL, Profile URL, City if stated, Coach Type best guess,
Platform if obvious, **Audience Size whenever findable**, Source Channel,
Status = `Sourced`. Nothing else. No page body, no notes essays. Speed is
the deliverable.

**Audience Size is a first-class field now, not an afterthought.** Grab a
real follower/subscriber number every time it's cheaply visible — a
directory listing, an IG/LinkedIn profile, an `apify ig --mode details`
call on a handle you're already vetting. A large audience is a strong buy
signal, so make it visible in the row; never guess it (a guessed number
poisons Gate 0 downstream), but do spend the one cheap lookup to find it.

**A reachable link to a real offer is required to log the row.** "Reachable
link" is broader than a custom-domain funnel, but it must lead to something
purchasable:
- A funnel or paid-product site (custom domain or platform subdomain).
- A **link-in-bio store** (Stan / Beacons / Linktree) **only when it has a
  real purchasable offer inside** — a product, course, program, or paid
  booking with a price. Open the page and confirm the offer before logging;
  the store URL is the Site URL only once you've seen the offer in it.
- **DM-only is not a funnel.** "DM me to work together," a Linktree that is
  just social links or a free lead magnet, or an IG bio with no store — none
  of these count, no matter how large the audience. A big audience with no
  purchasable offer is not a lead for this track. Note the strongest of
  these under "seen, no offer found" in the report so the name isn't lost
  (a coach with reach may launch an offer later), and move on.
- A candidate whose link to a real offer you can't find in one obvious hop
  does NOT get a row — same "seen, no offer found" list.

Create rows in batches (notion-create-pages takes multiples), not one call
per lead.

Do NOT qualify, do NOT walk funnels, do NOT reject anyone except obvious
non-candidates (not a coach, not plausibly UAE, no reachable offer). The
gates are `qualify-leads`'s job, on the `Sourced` rows this skill leaves
behind.

---

## Dynamic sourcing discipline (the everyday profile)

Top-up is sourcing shrunk and made repeatable — everything above still
applies, at ~15-20 names instead of 60-70. Three principles keep it useful
for the life of the track in a finite market. (On a one-time bootstrap run,
just mine volume.)

**1. Volume: small by default.** ~15-20 raw names, or whatever N Haytham
names. The Walk Queue drains at up to ~20/day; a top-up refills a day or
two of that, not more.

**2. Source the flow, not the stock.** The anti-exhaustion rule. The UAE /
English / solo market has a FINITE stock of coaches — re-mining the same
back-catalog every week dries it up. Bias to what is NEW since last time:
recently-added directory entries, podcast episodes from the last few weeks,
"just launched / now enrolling / new cohort" posts, fresh footprints and
link-in-bio pages. Use recency in the searches. A run that re-scrapes the
same back-catalog and leans on dedup to discard it has drifted — you're
burning fetches to find nothing new.

**3. Follow what's producing; abandon what's dry.** This is the dynamic
rule that replaces the old fixed channel rotation. There is no channel you
"owe" a turn to. Start wherever you last had signal or wherever the ask
points, and let results steer: a vein returning fresh UAE coaches gets
worked harder; a vein returning mostly dedup hits or noise gets dropped for
the day. The rising dedup rate is the drying signal — read it and switch,
don't push through it. If Haytham names a place ("top up from podcasts,"
"work the link-in-bio pages"), work that and skip the rest.

**Dedup against EVERY status, Disqualified included.** Skip a name/site
already in the CRM in ANY status — Sourced, Qualifying, Disqualified,
anything. A coach you already killed must not come back as a fresh Sourced
row. (Recheck-later nuance: a lead that failed Gate 0 only on activity or
audience — not niche or geography — may relaunch and is a future
recheck candidate; a hard niche/geo Disqualified is dead for good.)

---

## The run report

One message: how many logged, total in CRM at `Sourced`, whether the volume
target was hit (60-70 bootstrap, named N or ~15-20 top-up), and — since a
large audience is now a headline signal — call out the standout audiences
in the batch. If the target wasn't hit, say what's left to try; don't
quietly stop short.

Report which **veins produced and which came up dry** (one line each) — not
as channel bookkeeping, but as the signal for where to point the next run.
Give the seen-but-skipped duplicate count: a high dedup rate is the early
warning a vein is drying, and the trigger to work a different one next
time. List "seen, no offer found" names so they aren't lost.

Every run ends the same way: these `Sourced` rows now need `qualify-leads`
(Gate 0 + Gate 1) before they reach the Walk Queue. Say so.

---

## Hard rules

- **Never log in to, act as, or automate anything through Haytham's
  accounts on ANY platform** (Instagram and LinkedIn included). Acting as
  him through his own Instagram is what got the parenting account
  permanently banned, and the rule outlives that account. This is an
  identity / account-safety rule, NOT a platform ban: **read-only public
  data through a no-login third-party tool** — Firecrawl, or an Apify actor
  that takes a username/URL and needs no account — **is allowed for
  sourcing**, Instagram the same as LinkedIn. What is forbidden is a login
  or any action taken as Haytham, anywhere.
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
  outside the UAE however adjacent. A solo coach who works IG-first but
  sells through a real link-in-bio offer is IN scope; a DM-only coach with
  no purchasable offer is NOT — there is no funnel to work, however large
  the audience. Do not dilute the geographic thesis.
