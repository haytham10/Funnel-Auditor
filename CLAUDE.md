# Funnel Auditor — outreach automation system

This repo is the machine layer of Haytham's cold-outreach system, plus the
Claude skills that orchestrate it. Two tracks run in parallel:

- **UAE track (active — all new leads go here).** UAE-based solo coaches
  and course creators with real funnels. Sourced dynamically through
  no-login web tools, worked
  through the UAE Lead CRM, priced in AED, with one deliberately new step:
  **price discovery before any priced offer.**
- **Parenting track (live threads only).** The original
  parenting/faith-based pipeline: 125 cold-touched leads, ~9% reply rate
  by lead (above benchmark), zero closes. No new leads get sourced into
  it; existing warm threads get worked to a conclusion via
  `pipeline-tick`. Its IG sourcing channel is dead (account permanently
  banned Jun 22, 2026).

Why the UAE track exists, in one line: the parenting pipeline proved the
opener mechanic and nothing after it — only 2 of 11 repliers ever surfaced
a real priced objection, and nobody was ever asked what they would pay. So
this track holds the mechanic constant, swaps the market, and makes price
discovery a load-bearing, code-enforced step. The method files live in
`docs/uae-track/` (CRM spec, offer, targeting, outreach method) — the
files are the method; **Notion is the source of truth for live state.**
When you need to know what is actually happening, query the CRM, not the
docs.

## Branching (read before opening a PR)

**`uae-track` is the repo's git default branch** (changed 2026-07-14; it was
previously the parenting branch `claude/festive-heisenberg-6y2l94`).
UAE-track work is therefore the default path: cut new branches from
`uae-track`, and let UAE-track PRs take the default base.

**The hazard is now on the parenting side.** Parenting-track
(live-threads-only) work must set its PR base to
`claude/festive-heisenberg-6y2l94` **explicitly** — it will not be chosen
for you. Letting a parenting PR take the default base merges it into the
UAE track; letting a UAE PR target the parenting branch drags the whole UAE
track onto it (a squash replays the full diff between branches, not just
your change). Either direction crosses the two tracks, which is the thing
this repo is built to keep separate.

## The UAE pipeline in one line

`source-leads` (dynamic sourcing across whatever vein produces → CRM as
Sourced, a reachable link + audience size per row) → `qualify-leads`
(mechanical Gate 0/1 over Sourced → Qualifying) →
`/batch-audit` (one
lead-processor agent per lead, ~5 parallel, cap 20) → per lead:
**pre-flight qualification first** (the cheap floors — UAE-base, gatekeeper,
paid-offer-exists, 30-day activity, 1,500 audience — settled from one search
+ at most one light profile scrape + one entry-page fetch, BEFORE the walk,
so a Gate 0 kill costs a lookup not a full crawl; audience is three-way:
hard number decides / inconclusive+strong stature proceeds /
inconclusive+weak holds at Qualifying) → machine walk on survivors only
(Firecrawl-primary fetch, parallel scrapes, Playwright fallback; `cta-probe`
for single-page JS-button resolution) → **mandatory vision pass** → Gate 0
confirm (funnel floor) → opener-finder (lane + finding + innocent
explanation + findings bank + 3-line Loom skeleton; `Finding Verified`
checked only on a visually-confirmed Lane 1 finding) → CRM write → email
address (shape checked by `main.py email-check`; FAIL never enters the CRM;
then Lane 1 deliverability confirmed by `main.py email-verify` → `Email
Verified`; if the walk found NO address, `main.py email-enrich` derives
name-based candidates against the lead's own domain and verifies them in one
batched call, adopting at most one — a PASS there is a verify PASS that checks
`Email Verified`; both hard gates required for Audit Ready) →
**held** (no Gmail draft yet) → Haytham runs `haytham-hook-finder`
(single lead or batch mode over all Audit Ready; real public evidence:
LinkedIn, podcasts, YouTube, About page) → he approves the hooks → Gmail
DRAFTS created in the same session (SMYKM opening A or B), Status =
`Draft Ready` → Haytham sends by hand (or schedules — Status
`Scheduled`) → tick reconciles Gmail reality → `Outreach Sent` → reply →
turn-two artifact → **price discovery question** (answer logged VERBATIM
+ anchor set) → priced offer (735 AED Track A / 2,575 AED Track B, gated
by `crm-gate offer`) → close. `uae-tick` runs the daily loop; the send-day
is the Dubai calendar day everywhere.

Haytham's manual jobs: firing sourcing/qualifying runs, reviewing hook batches,
reviewing and sending (or scheduling) drafts from Gmail, recording the
turn-two artifact, confirming sends for logging, and appending test
scores to `docs/deliverability-log.md`.

## Hard rules (non-negotiable)

- **Never log in to, act as, or automate anything through Haytham's own
  accounts on ANY platform** (Instagram and LinkedIn included) — acting as
  him through his own Instagram is exactly what got the parenting account
  permanently banned, and the rule outlives that account. This is an
  identity / account-safety rule, NOT a blanket platform ban: read-only
  public data pulled through a no-login third-party tool — Firecrawl, or an
  Apify-style actor that takes a username or URL with no account required —
  is allowed for enrichment and SMYKM hook-finding AND for sourcing,
  Instagram the same as LinkedIn, YouTube, and podcasts. (Sourcing is
  dynamic and channel-agnostic — work whatever vein produces UAE solo
  coaches with an audience and a way to get paid, Instagram/link-in-bio
  included, through no-login read-only tools only; the ban is on logging in
  or acting as Haytham, not on the platform. See
  `docs/uae-track/03-targeting-and-sourcing.md`.)
- **Never send an email.** The system ends at Gmail drafts. Sending is
  human.
- **Never invent findings.** No verified finding → no opener. Lane 2/3
  exists. Machine check flags are candidates only — a flag that fails the
  vision pass is dead and stays dead. `Finding Verified` gets checked only
  on a visually-confirmed Lane 1 finding; it is the send gate, and
  checking it to make a lead sendable corrupts the track's data.
- **No send without `Finding Verified` AND `Email Verified`, and never past
  a sending inbox's daily ceiling — PER INBOX, never pooled.** The ceiling
  is TOTAL sends leaving THAT inbox (openers, follow-ups, warm replies, both
  tracks; deliverability doesn't care what kind of email it was, but it
  cares which domain it left). There are now **two inboxes** — `Inbox 1`
  (haytham@auto-mate.one, Gmail MCP) and `Inbox 2` (haytham@gethaytham.com,
  direct API) — each its own domain, each with its OWN independent ramp in
  `send_cap.json` (keyed by logical label, fails closed to 20 per inbox),
  moved 20 → 25 → 30 one step per 7+ days, only by Haytham's explicit call
  and only if THAT inbox's deliverability held (`python main.py send-cap
  status|set --inbox "<label>"`, `--all` for every inbox). **30 is the hard
  cap for ONE inbox — more volume means more inboxes, never a bigger
  number.** A lead's whole thread rides its assigned `Inbox` (sticky);
  `python main.py inbox route` picks one for a new lead. That inbox's
  follow-ups eat its budget first; its new openers get what's left. Enforced
  per send: `python main.py crm-gate send <row.json> --sends-today N
  --touch T --inbox "<label>"` (+ `--followups-due M` on touch 1, `--carries
  X` on touch 2/3; `--sends-today` = that inbox's own count). The
  registry that maps a label to its address + transport is
  `audit/inboxes.py`. The bottleneck is findings, not sends — opener
  headroom means that many funnel walks/day.
- **The cold sequence is three touches (day 0, 3, 9), then Dormant — and
  touches 2-3 must each carry something new:** the next unused banked
  finding, the Loom offer, or the disambiguating question. A bare bump is
  a wasted send and a spam signal. Enforced by the same gate (`--carries`;
  a `second-finding` claim is checked against the row's `Findings Bank`).
  The walk banks every verified finding, ranked, instead of discarding the
  ones it doesn't use — touch 1 takes #1, later touches draw the next.
- **Price discovery before any priced offer, never after a stall.** A
  lead cannot reach Offer Sent without a VERBATIM `Price Discovery
  Answer` and a `Discovery Anchor`. Enforced: `python main.py crm-gate
  offer <row.json>`. No PASS, no money email.
- **The price never moves.** $200 = 735 AED (Track A), $700 = 2,575 AED
  (Track B). The AED figures are the same price quoted natively, not a
  discount. A low anchor from a lead is market data, not permission to
  discount — objections get bonuses or restructured terms (GSO v2).
- **Copy rules, every generated email:** no em-dashes, ever. No operator
  jargon ("funnel", "conversion", "audit", "sequence"). Proper
  capitalization. **Sign off "Haytham" at the end** (changed Jul 14, 2026:
  the Gmail auto-signature was taken down, so the body must carry the name;
  the old rule here said no sign-off, which would now ship unsigned mail).
  No weak closers ("no
  pressure / no rush / whenever timing's right") anywhere, including
  silence-breakers.
- **Two CRMs, never crossed.** UAE leads live ONLY in the UAE Lead CRM;
  the parenting DB is live-threads-only. Never write a UAE lead into the
  parenting DB or vice versa.
- Notion is the source of truth for pipeline state, not chat memory.
- A Gmail draft is not a send. Status / Touch # / Last Contacted / Email
  Thread Log move only after Haytham confirms an email actually left.
- **No draft before a hook decision.** `haytham-email-draft` and
  `process-lead` hard-block on a `SMYKM hook:` line that still reads "not
  run yet" — no Gmail draft until `haytham-hook-finder` resolves the line
  (a real hook, or a confirmed "no hook found").
- **Before any Notion page update that uses search-and-replace
  (`update_content`), fetch the page first** to confirm the current
  literal content format — Notion's enhanced-markdown escaping (`\$`,
  auto-linked domains) breaks naive search-and-replace. Escaped or
  non-plain formatting → rewrite the full body (`replace_content`)
  instead.
- **A dispatched subagent gets one resume, not two.** A status-only reply
  with no new work product means take the task over directly — see
  `.claude/skills/batch-audit/SKILL.md` Step 2.

## Key pieces

- `main.py discover-links` / `discover-checkout` / `screenshot-name` /
  `ingest` — the Firecrawl-primary fetch path: Claude fetches via
  Firecrawl MCP tools, these commands classify links (scope/priority) and
  build the evidence packet. Python owns all scope/analysis logic
  regardless of which layer fetched the page.
- `main.py walk <url>` — the Playwright crawl fallback for leads Firecrawl
  can't handle (persistent bot walls, JS-button click-discovery).
- `main.py vision …` — the vision-pass completeness gate. "Read every
  screenshot" is a computed fact, not a claim.
- `main.py crm-gate offer|send` — the UAE transition gates (see
  `audit/crm_gate.py`): offer = verbatim discovery answer + anchor before
  any priced offer; send = Finding Verified + `Email Verified` (fails closed
  on either) + follow-ups-first headroom under THAT inbox's ceiling
  (`--inbox "<label>"`) + a declared carrier on touch 2/3 (checked against
  `Findings Bank` when it claims a second finding). Skills dump the fresh
  Notion row to JSON, run the gate, and quote its literal output line. Same
  trust model as the vision gate.
- `main.py inbox list|route|counts|reconcile` — the inbox registry (see
  `audit/inboxes.py`): the ONE seam between logical labels
  (`Inbox 1`/`Inbox 2`/…, used by the CRM `Inbox` property,
  `send_cap.json`, and `crm-gate send --inbox`) and real sending addresses
  + transports (`gmail-mcp` for Inbox 1, the `gmail-gethaytham` direct API
  for Inbox 2). `list` shows every inbox with its address, transport, and
  cap; `route` picks the inbox for a lead's next send — sticky if already
  assigned, else by policy (`headroom` default / `fill-primary`, with
  optional `--weight` warm-up bias); `counts` returns each inbox's sends
  today (epoch-exact Dubai day — direct-API inboxes counted, the Gmail MCP
  query emitted for the rest); `reconcile` corrects a row's `Inbox` to
  where its thread physically lives. `send-cap log --inbox … --kind …
  --detail …` appends the canonical per-inbox deliverability-log line.
  Scale to Inbox 3/N by adding one entry there, registering its cap, and
  adding the CRM select option — nothing else hardcodes a count. Drafts on
  BOTH transports are linted by the same shared rule (`audit/draft_lint.py`,
  bare links + em-dashes, subject and body).
- `main.py send-cap status|set` — the ceiling, one independent ramp PER
  inbox (see `audit/send_cap.py`): each inbox's cap + its ramp reminder once
  its step has held 7 days; `--all` prints every inbox + the additive total.
  `set --inbox "<label>"` moves one step (20/25/30) or registers a new inbox
  at 20 — Haytham's command, never a skill's; state is `send_cap.json` keyed
  by logical label, failing closed to 20 per inbox. The ramp decision's
  evidence lives in `docs/deliverability-log.md` (uae-tick appends
  bounces/spam flags naming the inbox; Haytham appends test scores).
- `main.py email-check <address> [--name]` / `main.py email-verify
  <address>` — the two-layer address gate (`audit/email_check.py`).
  `email-check` is the free shape check (syntax + MX + typo/disposable/
  no-reply flags): FAIL = the address never enters the CRM or a queue.
  `email-verify` is the deliverability confirm — **ZeroBounce**
  (`audit/email_verifier.py`, `ZEROBOUNCE_API_KEY`, free tier 100/month, no
  Apify cost) — run during the walk for Lane 1 leads: `EMAIL VERIFY: PASS`
  checks `Email Verified` and clears the lead for Audit Ready; FAIL = the
  mailbox bounces, never send; WARN (catch_all/unknown) = Haytham's call.
  It exists because `email-check` PASS is syntax+MX only and cleared two
  addresses that then hard-bounced at Touch 1, and a bounce burns the one
  shared domain. `apify verify-email` (MillionVerifier) remains a manual
  fallback.
- `main.py email-enrich "<name>" <domain-or-site-url>` — the no-email
  fallback stage (`audit/email_enrich.py`). When the walk harvests no
  address, it derives ranked name-based candidates against the lead's OWN
  branded domain (jane@, jane.doe@, jdoe@…), shape-gates the domain once for
  free, then verifies all candidates in ONE batched ZeroBounce call and
  converges on at most one deliverable address. Three baked-in safety
  properties: exactly ONE address is ever adopted (the top-ranked PASS; the
  rest are logged, never a second guessed spelling — the incident
  `email_check.py`'s header records); it never auto-adopts on a catch-all
  domain (every guess → `catch_all`/`catch-all`/WARN → `HOLD`, adopt
  nothing); and it refuses free-provider domains (`NONE`). `EMAIL ENRICH:
  PASS` is by construction an `EMAIL VERIFY: PASS` on the adopted mailbox,
  so it checks `Email Verified` exactly like a harvested-then-verified
  address. Reuses `email_verifier.verify_emails` + `classify_verification`
  + `check_email` — it adds only candidate generation. Fails closed
  (verifier error → `HOLD`, never a silent adoption).
- `main.py apify <li-posts|li-profile|ig|ig-post|verify-email|search|actors>`
  — the no-login third-party fetch layer (`audit/apify.py`,
  `docs/uae-track/apify-actors.md`): read-only public LinkedIn/Instagram
  data for SMYKM hooks (the two platforms Firecrawl can't reach), through
  vetted Apify actors that take a URL and need no account. Reads
  `APIFY_TOKEN` from the environment (an env secret, never in code);
  discovery works without it, runs need it, missing token fails closed.
  Posts-first on LinkedIn, cost-aware on IG. Podcasts / YouTube / About
  pages stay on Firecrawl. `verify-email`/`search`/`footprint` still work
  here but are a manual fallback only — email verification and
  Google-footprint sourcing default to `email-verify` (ZeroBounce) and
  `main.py classify-footprint` (Firecrawl-fed) instead, so Apify's small
  monthly cap stays free for LinkedIn/Instagram, the one thing with no
  substitute.
- `main.py classify-footprint <platform> --subdomain-hits <file>
  --marker-hits <file>` — the fetch-agnostic Google-footprint merge
  (`audit/footprint.py`): dedupes by host, tags `foundVia`
  (subdomain/footprint), and drops the platform's-own-site/social noise
  the wider footer-signature net drags in. Fed by `firecrawl_search` results
  saved to JSON (no Apify cost) rather than by `apify.google_search` — same
  output shape as the original `apify footprint`, which still exists as a
  fallback and now just calls into this module after fetching.
- `main.py cta-probe <url> --type sales|course|booking` — single-page
  Playwright JS-button click-discovery, for resolving one Firecrawl-fetched
  page's unverified buttons without re-walking the whole funnel.
- `audit/` — checks, extraction, Gate 0 floors (`gates.py`, UAE:
  audience 1,500 / activity 30 days / funnel present / UAE-based), packet
  builder; all fetch-layer-agnostic. `crawler.py` still holds the
  Playwright fallback + the link/checkout classification logic both fetch
  paths share.
- `.claude/skills/source-leads` — the sourcing engine, collect-only: works
  dynamically across whatever vein produces UAE solo coaches with an
  audience and a way to get paid (platform + link-in-bio footprints,
  directories, LinkedIn, podcasts/events, no-login IG actor, lateral),
  logging `Sourced` rows (a reachable link + audience size, no gating). The
  channel is not the point and there is no fixed rotation — follow what's
  producing, drop what's dry. Two volume profiles — a one-time bootstrap
  fill (60-70 names) and top-up, the everyday on-demand tap (small runs,
  recency-biased to source the flow not the stock).
- `.claude/skills/qualify-leads` — the mechanical gate, the step between
  sourcing and the walk: runs Gate 0 (UAE-based / funnel / 30-day activity
  / 1,500 audience) + Gate 1 (solo) over `Sourced` rows, ~2 fetches each,
  promoting passes to `Qualifying` and killing fails to `Disqualified`. No
  funnel walks (that's batch-audit). Sibling of batch-audit — both process
  existing rows at a status, this one gates, that one walks.
- `.claude/skills/process-lead` — the per-lead contract: walk → vision
  pass → floors → opener → **held** at the Gmail draft until
  `haytham-hook-finder` resolves the hook.
- `.claude/skills/batch-audit` + `.claude/agents/lead-processor.md` —
  batch orchestrator over the Walk Queue (~5 parallel, cap 20) and the
  per-lead subagent with its structured return block.
- `.claude/skills/haytham-opener-finder` — Gate 0/1, the 5-stop walk
  (widened for webinar funnels, call-booking flows, cohort launches),
  filters, lanes, CRM page body format. Stops at the finding + innocent
  explanation — does not find the SMYKM hook.
- `.claude/skills/haytham-hook-finder` — separate, manually-triggered:
  real public evidence (LinkedIn, podcasts, YouTube, About page) → the
  SMYKM hook line, cited, never fabricated. Gates the draft.
- `.claude/skills/haytham-email-draft` — voice, mechanics, gate, logging,
  both tracks. UAE layer (AED framing + the price discovery email type)
  in `references/uae-track.md`.
- `.claude/skills/uae-tick` — the UAE daily loop: replies, verbatim
  discovery-answer logging, due touches, gated send queue, weekly
  scoreboard.
- `.claude/skills/pipeline-tick` — the parenting track's daily loop, live
  threads only.
- `.claude/skills/dashboard` + `main.py dashboard skeleton|render`
  (`audit/dashboard.py`) — the read-only command center: fuses pipeline state
  (Notion) + sending reality (both Gmail inboxes) + the deliverability ceilings
  into one self-contained HTML page, published as a stable-URL Claude Artifact.
  Same Python/skill split as `crm-gate`: `skeleton` fills the Python-reachable
  slice (per-inbox ceilings + Inbox 2's real sent-today count) and seeds the
  Notion/Gmail-MCP panels null; the skill fills them via MCP and pipes the
  snapshot through `render`, which validates and draws every panel (null → an
  "awaiting data" empty state, never a crash). Never sends, drafts, or writes
  the CRM.
- `.claude/skills/haytham-funnel-auditor` — deep audit (Loom/call prep).
- `.claude/skills/firecrawl` — MCP tool reference for the fetch layer.

## The CRMs

- **UAE Lead CRM (active):** data source
  `collection://5efbdd9b-1e19-468c-96db-f94a525846e0`, database ID (REST)
  `5a9fc583160046d1a64c4e65cc804229`. Views, schema, lifecycle, SQL:
  `docs/uae-track/01-crm-operating-spec.md`.
- **Parenting Lead Pipeline (live threads only, never new leads):** data
  source `collection://c6209e29-55ef-4781-b735-73b2a254e34f`, database ID
  (REST) `78b26ebe-5b4f-4ff2-884a-3ccf369d00e6`.

## Environment notes

- Firecrawl MCP server is the primary fetcher — already connected in
  managed sessions, no setup needed.
- Apify actor layer (`main.py apify`, `audit/apify.py`) is the no-login
  fetch path for LinkedIn/Instagram (which Firecrawl can't reach). It needs
  `APIFY_TOKEN` set as an environment secret on the runner (never in code);
  without it, discovery still works but runs fail closed with a clear
  message. See `docs/uae-track/apify-actors.md`.
- Email verification (`main.py email-verify`, `email-enrich`) defaults to
  **ZeroBounce**, not Apify — `audit/email_verifier.py` reads
  `ZEROBOUNCE_API_KEY` from the environment (free tier: 100 verification
  credits/month, no card, never expire). Google-footprint sourcing
  defaults to **Firecrawl search** feeding `main.py classify-footprint`
  (`audit/footprint.py`), not Apify's google-search-scraper. Both moved
  off Apify 2026-07-17 so its small monthly cap stays free for LinkedIn/
  Instagram, the one thing Firecrawl can't reach; `apify verify-email` /
  `apify search` / `apify footprint` still work as a manual fallback.
- Chromium/Playwright is only needed for the `main.py walk` fallback path.
  Managed cloud sessions: Chromium lives at `/opt/pw-browsers/chromium`
  (the crawler auto-detects it; override with `FUNNEL_AUDITOR_CHROMIUM`).
  The MITM egress proxy resets Chromium's post-quantum TLS handshake — the
  crawler writes a Chromium enterprise policy to disable PQ/ECH
  automatically.
- Local (WSL): `pip install -r requirements.txt && playwright install chromium`
  (only needed if you expect to exercise the Playwright fallback).
