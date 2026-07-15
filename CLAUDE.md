# Funnel Auditor — outreach automation system

This repo is the machine layer of Haytham's cold-outreach system, plus the
Claude skills that orchestrate it. Two tracks run in parallel:

- **UAE track (active — all new leads go here).** UAE-based solo coaches
  and course creators with real funnels. Sourced web-natively, worked
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

`source-leads` (Day 1: 5 web channels → CRM as Sourced, Site URL required
per row; Day 2: mechanical Gate 0/1 → Qualifying) → `/batch-audit` (one
lead-processor agent per lead, ~5 parallel, cap 20) → per lead: machine
walk (Firecrawl-primary fetch, parallel scrapes, Playwright fallback;
`cta-probe` for single-page JS-button resolution) → **mandatory vision
pass** → UAE Gate 0 floors → opener-finder (lane + finding + innocent
explanation + findings bank + 3-line Loom skeleton; `Finding Verified`
checked only on a visually-confirmed Lane 1 finding) → CRM write → email
address (checked by `main.py email-check`; FAIL never enters the CRM) →
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

Haytham's manual jobs: picking the sprint day, reviewing hook batches,
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
  is allowed for enrichment and SMYKM hook-finding, Instagram the same as
  LinkedIn, YouTube, and podcasts. (Sourcing is a separate question:
  Instagram is not a cold-sourcing channel for the UAE track, which stays
  web-native by design — see `docs/uae-track/03-targeting-and-sourcing.md`.)
- **Never send an email.** The system ends at Gmail drafts. Sending is
  human.
- **Never invent findings.** No verified finding → no opener. Lane 2/3
  exists. Machine check flags are candidates only — a flag that fails the
  vision pass is dead and stays dead. `Finding Verified` gets checked only
  on a visually-confirmed Lane 1 finding; it is the send gate, and
  checking it to make a lead sendable corrupts the track's data.
- **No send without `Finding Verified`, and never past the daily ceiling
  on TOTAL sends leaving the inbox** — openers, follow-ups, warm replies,
  both tracks; deliverability doesn't care what kind of email it was (one
  inbox, one domain, no backup). The ceiling lives in `send_cap.json` and
  ramps 20 → 25 → 30, one step per 7+ days, raised only by Haytham's
  explicit call and only if deliverability held (`python main.py send-cap
  status|set`; missing/invalid state fails closed to 20). **30 is the hard
  cap for one inbox — more volume means more inboxes, never a bigger
  number.** Follow-ups due today eat the budget first; new openers get
  what's left. Enforced per send: `python main.py crm-gate send <row.json>
  --sends-today N --touch T` (+ `--followups-due M` on touch 1, `--carries
  X` on touch 2/3). The bottleneck is findings, not sends — opener
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
  any priced offer; send = Finding Verified + address + follow-ups-first
  headroom under the inbox ceiling + a declared carrier on touch 2/3
  (checked against `Findings Bank` when it claims a second finding).
  Skills dump the fresh Notion row to JSON, run the gate, and quote its
  literal output line. Same trust model as the vision gate.
- `main.py send-cap status|set` — the inbox ceiling (see
  `audit/send_cap.py`): current cap + the built-in ramp reminder once a
  step has held 7 days. `set` moves one step (20/25/30) and is Haytham's
  command, never a skill's; state is `send_cap.json`, failing closed to 20.
  The ramp decision's evidence lives in `docs/deliverability-log.md`
  (uae-tick appends bounces/spam flags; Haytham appends test scores).
- `main.py email-check <address> [--name]` — pre-send address gate
  (`audit/email_check.py`): syntax + MX + typo/disposable/no-reply flags.
  FAIL = the address never enters the CRM or a queue; WARN inconclusive =
  verify via `main.py apify verify-email <addr>` first.
- `main.py apify <li-posts|li-profile|ig|ig-post|verify-email|search|actors>`
  — the no-login third-party fetch layer (`audit/apify.py`,
  `docs/uae-track/apify-actors.md`): read-only public LinkedIn/Instagram
  data for SMYKM hooks (the two platforms Firecrawl can't reach), email
  verification, and Google SERP, through vetted Apify actors that take a
  URL and need no account. Reads `APIFY_TOKEN` from the environment (an env
  secret, never in code); discovery works without it, runs need it, missing
  token fails closed. Posts-first on LinkedIn, cost-aware on IG. Podcasts /
  YouTube / About pages stay on Firecrawl.
- `main.py cta-probe <url> --type sales|course|booking` — single-page
  Playwright JS-button click-discovery, for resolving one Firecrawl-fetched
  page's unverified buttons without re-walking the whole funnel.
- `audit/` — checks, extraction, Gate 0 floors (`gates.py`, UAE:
  audience 1,500 / activity 30 days / funnel present / UAE-based), packet
  builder; all fetch-layer-agnostic. `crawler.py` still holds the
  Playwright fallback + the link/checkout classification logic both fetch
  paths share.
- `.claude/skills/source-leads` — the sourcing engine: the one-time Day 1
  volume sourcing / Day 2 mechanical qualifying sprint (bootstrap), plus
  top-up, the everyday on-demand tap that keeps the CRM filled for the
  life of the track (small runs, recency-biased to source the flow not the
  stock, rotating to the stalest channel).
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
  fetch path for LinkedIn/Instagram (which Firecrawl can't reach), email
  verification, and Google SERP. It needs `APIFY_TOKEN` set as an
  environment secret on the runner (never in code); without it, discovery
  still works but runs fail closed with a clear message. See
  `docs/uae-track/apify-actors.md`.
- Chromium/Playwright is only needed for the `main.py walk` fallback path.
  Managed cloud sessions: Chromium lives at `/opt/pw-browsers/chromium`
  (the crawler auto-detects it; override with `FUNNEL_AUDITOR_CHROMIUM`).
  The MITM egress proxy resets Chromium's post-quantum TLS handshake — the
  crawler writes a Chromium enterprise policy to disable PQ/ECH
  automatically.
- Local (WSL): `pip install -r requirements.txt && playwright install chromium`
  (only needed if you expect to exercise the Playwright fallback).
