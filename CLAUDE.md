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

`source-leads` (fan out one worker per vein → workers RETURN candidates →
orchestrator dedups across veins + the live CRM → `sourcing-verifier` confirms
link/offer/audience → CRM as Sourced) → `qualify-leads` (fan out
qualifier-workers over slices of Sourced rows → `qualifier-verifier` re-checks
every promotion/kill → Qualifying) → `/batch-audit` (one lead-processor agent
per lead, ~5 parallel, cap 20) → per lead:
**pre-flight qualification first** (the cheap floors — UAE-base, gatekeeper,
paid-offer-exists, 30-day activity, 1,500 audience — settled from one search
+ at most one light profile scrape + one entry-page fetch, BEFORE the walk,
so a Gate 0 kill costs a lookup not a full crawl; audience is three-way:
hard number decides / inconclusive+strong stature proceeds /
inconclusive+weak holds at Qualifying) → machine walk on survivors only
(Firecrawl-primary fetch, parallel scrapes, Playwright fallback; `cta-probe`
for single-page JS-button resolution) → **mandatory vision pass** → Gate 0
confirm (funnel floor) → opener-finder (lane + finding + innocent
explanation + findings bank + 3-line Loom skeleton) — the walk **proposes** the
finding; an independent `finding-verifier` re-derives it from the screenshots and
is the ONLY thing that checks `Finding Verified` (verified → Audit Ready) → CRM
write → email
address (shape checked by `main.py email-check`; FAIL never enters the CRM;
then Lane 1 deliverability confirmed by `main.py email-verify` → `Email
Verified`; if the walk found NO address, `main.py email-enrich` derives
name-based candidates against the lead's own domain and verifies them in one
batched call, adopting at most one — a PASS there is a verify PASS that checks
`Email Verified`; both hard gates required for Audit Ready) →
**held** (no Gmail draft yet) → Haytham runs `haytham-hook-finder`
(single lead, or **batch mode = fan out `hook-worker` per Audit Ready lead →
`hook-verifier` re-fetches the cited source and confirms the quote before the
hook is trusted**; real public evidence: LinkedIn, podcasts, YouTube, About page)
→ he approves the hooks → Gmail
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
  dynamic and channel-agnostic through no-login read-only tools only — the
  ban is on logging in / acting as Haytham, not on the platform. See
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
  X` on touch 2/3; `--sends-today` = that inbox's own count). **Past noon
  Dubai a fresh touch-1 opener rolls to tomorrow's send-day** (it can't leave
  today — it's scheduled for the morning) and is gated against tomorrow's
  ceiling via `--sends-next-day M` (that inbox's already-scheduled count);
  follow-ups and warm replies never roll. The
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
  capitalization. **Sign off "Haytham" at the end** (the Gmail
  auto-signature is gone, so the body must carry the name). No weak closers
  ("no pressure / no rush / whenever timing's right") anywhere, including
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

Pointers, not manuals: every command and module below carries a full
docstring — open it for the mechanics, rationale, and history. This section
keeps only what each piece IS and how the pieces connect; the detail lives
in the code and is one file-open away.

**Fetch + walk**
- `main.py discover-links` / `discover-checkout` / `screenshot-name` /
  `ingest` — the Firecrawl-primary fetch path: Claude fetches via Firecrawl
  MCP, these classify links + build the evidence packet; Python owns all
  scope/analysis regardless of which layer fetched (`audit/`).
- `main.py walk <url>` — Playwright crawl fallback for leads Firecrawl can't
  handle (persistent bot walls, JS-button click-discovery).
- `main.py cta-probe <url> --type sales|course|booking` — single-page
  Playwright JS-button resolution without re-walking the whole funnel.
- `main.py vision …` — the vision-pass completeness gate ("read every
  screenshot" is a computed fact, not a claim).
- `audit/gates.py` — Gate 0 floors (UAE-based / funnel / 30-day activity /
  1,500 audience). `audit/crawler.py` — Playwright fallback + the
  link/checkout classification both fetch paths share.

**Gates + sending** — all fail closed. Skills dump the FRESH Notion row to
JSON, run the gate, and quote its literal output line (same trust model as
the vision gate).
- `main.py crm-gate offer|send` (`audit/crm_gate.py`) — offer = verbatim
  discovery answer + anchor before any priced offer; send = Finding Verified
  + Email Verified + follow-ups-first headroom under THAT inbox's ceiling
  (`--inbox`) + a declared carrier on touch 2/3 (checked against `Findings
  Bank` for a second finding).
- `main.py inbox list|route|counts|reconcile` (`audit/inboxes.py`) — the ONE
  seam between logical labels (`Inbox 1`/`Inbox 2`/…) and real addresses +
  transports (`gmail-mcp` / `gmail-gethaytham`). `route` picks a lead's inbox
  (sticky, else policy); `counts` reports each inbox's Dubai-day sends;
  `reconcile` corrects a row to where its thread physically lives. Scale to
  Inbox 3/N by adding one registry entry + cap + CRM option. Drafts on both
  transports linted by `audit/draft_lint.py` (bare links + em-dashes).
- `main.py send-cap status|set` (`audit/send_cap.py`) — the per-inbox ceiling
  + ramp (20→25→30, one step per 7+ days, Haytham's command only), state in
  `send_cap.json` (fails closed to 20), ramp evidence in
  `docs/deliverability-log.md` (`send-cap log`). More volume = more inboxes,
  never a bigger number.

**Email address gate** (`audit/email_check.py`, `email_enrich.py`,
`email_verifier.py`; provider selection under Environment notes)
- `main.py email-check <addr> [--name]` — free shape check (syntax + MX +
  typo/disposable/no-reply flags); FAIL never enters the CRM or a queue.
- `main.py email-verify <addr>` — deliverability confirm; PASS checks
  `Email Verified` and clears for Audit Ready, FAIL bounces so never send,
  WARN (catch_all/unknown) is Haytham's call.
- `main.py email-enrich "<name>" <domain-or-site-url>` — no-address fallback:
  derives ranked candidates on the lead's OWN branded domain, verifies them
  in one batched call, adopts AT MOST one PASS, and never on a catch-all or
  free-provider domain (else HOLD). A PASS here is a verify PASS.

**Sourcing**
- `main.py apify <li-posts|li-profile|ig|ig-post|verify-email|search|actors>`
  (`audit/apify.py`, `docs/uae-track/apify-actors.md`) — no-login read-only
  LinkedIn/IG fetch for SMYKM hooks (what Firecrawl can't reach); needs
  `APIFY_TOKEN`, every run cost-gated (see Environment notes).
- `main.py classify-footprint <platform> …` (`audit/footprint.py`) —
  Firecrawl-fed Google-footprint merge: dedupe by host, tag `foundVia`, drop
  own-site/social noise.

**Skills** (`.claude/skills/…` — when one applies, read its SKILL.md on disk)
- **All four stage skills share one orchestration chassis
  (`docs/agent-orchestration.md`): fan out least-privilege workers → an
  independent verifier re-checks the one claim the stage self-certifies → the
  orchestrator cross-checks Notion → the batch is sized to downstream demand.**
  The per-stage worker/verifier agents live in `.claude/agents/`; that split is
  the fix for low agent-output quality (no stage certifies its own work).
- `source-leads` — sourcing orchestrator: fan out `sourcing-worker` per vein
  (they RETURN candidates), the orchestrator owns cross-vein + live-CRM dedup,
  `sourcing-verifier` confirms link/offer/audience → `Sourced`. Collect-only, no
  gating; bootstrap fill + everyday top-up.
- `qualify-leads` — qualifying orchestrator: fan out `qualifier-worker` over
  slices of `Sourced` (~2 fetches/row), `qualifier-verifier` re-checks every
  promotion/kill (audience provenance — the soft pass that burned walks) →
  `Qualifying`. Sibling of batch-audit: this gates, that walks.
- `batch-audit` + `.claude/agents/lead-processor.md` + `finding-verifier.md` —
  walk orchestrator over the Walk Queue (~5 parallel, cap 20): the walker
  PROPOSES the finding + returns a structured JSON block, the `finding-verifier`
  re-derives it from the screenshots and is the only thing that checks
  `Finding Verified`.
- `process-lead` — per-lead flow of record + the canonical hard rules: walk →
  vision → floors → opener → **propose** → **held** at the Gmail draft until
  `haytham-hook-finder` resolves the hook.
- `haytham-opener-finder` — Gate 0/1 + the 5-stop walk → lane + finding +
  innocent explanation + CRM body format. PROPOSES the finding (the
  finding-verifier certifies), stops before the hook.
- `haytham-hook-finder` + `hook-worker.md` + `hook-verifier.md` — separate,
  manually triggered: real cited public evidence → the SMYKM hook line, never
  fabricated; batch mode fans out per Audit Ready lead and the `hook-verifier`
  re-fetches the cited source before the hook is trusted. Gates the draft.
- `haytham-email-draft` — voice, mechanics, gate, logging, both tracks (UAE
  AED + price-discovery layer in `references/uae-track.md`).
- `uae-tick` / `pipeline-tick` — the UAE / parenting daily loops.
- `dashboard` + `main.py dashboard skeleton|render` (`audit/dashboard.py`) —
  read-only command center fusing Notion state + both inboxes + ceilings into
  a stable-URL Artifact (same Python/skill split as `crm-gate`); never sends,
  drafts, or writes the CRM.
- `haytham-funnel-auditor` — deep audit (Loom/call prep). `firecrawl` —
  fetch-layer MCP tool reference.

## The CRMs

- **UAE Lead CRM (active):** data source
  `collection://5efbdd9b-1e19-468c-96db-f94a525846e0`, database ID (REST)
  `5a9fc583160046d1a64c4e65cc804229`. Views, schema, lifecycle, SQL:
  `docs/uae-track/01-crm-operating-spec.md`.
- **Parenting Lead Pipeline (live threads only, never new leads):** data
  source `collection://c6209e29-55ef-4781-b735-73b2a254e34f`, database ID
  (REST) `78b26ebe-5b4f-4ff2-884a-3ccf369d00e6`.

## Environment notes

- **The repo's `.claude/skills/` is the authoritative skill set — never a
  remembered or globally-installed copy.** A `SessionStart` hook
  (`.claude/hooks/skills_authoritative.py`, wired in `.claude/settings.json`)
  fingerprints every on-disk `SKILL.md` and injects that inventory at session
  start, so each skill's committed version is the one in force. When a skill
  applies, read its `SKILL.md` (and referenced files) FROM DISK and follow
  that; if the injected `v=` fingerprint differs from what you recall, the
  file on disk wins. Fails open — it can never block a session from starting.
- **Cross-session memory lives in `docs/journal.md`.** The container is
  ephemeral and each session starts cold; Notion holds live pipeline *state*
  and git holds *code changes*, but the narrative tying sessions together —
  ops events, decisions, gotchas, open follow-ups — lives only in this
  journal. A second `SessionStart` hook (`.claude/hooks/session_memory.py`)
  auto-loads its latest entries + recent commits at the top of every session,
  so you boot caught up (read side, fully automatic). **Write side is a
  habit:** when you finish a session with anything worth remembering (a tick,
  a send batch, a sourcing run, a decision, a code change), add a dated `## `
  entry at the TOP of `docs/journal.md` and commit + push it — a journal-only
  commit is fine on an ops-only session; the point is it survives the
  container. Newest first; keep entries short and scannable.
- Firecrawl MCP server is the primary fetcher — already connected in
  managed sessions, no setup needed.
- **Apify** (`main.py apify`, `audit/apify.py`; needs `APIFY_TOKEN` as an env
  secret, never in code) — the no-login LinkedIn/IG fetch path AND the default
  email verifier again as of 2026-07-18 (the account is on a paid plan).
  Missing token → discovery works, runs fail closed. **Every actor run is
  cost-gated** (`COST_APPROVAL_THRESHOLD_USD` = $0.10): it prices the run from
  the actor's live per-unit rate and blocks anything unknown or over the
  threshold with `APPROVAL REQUIRED` / exit 3 — get Haytham's OK, then re-run
  with `--approve-cost`. Ordinary single-lead calls clear automatically. See
  `docs/uae-track/apify-actors.md`.
- **Email verification providers** — `email-verify` / `email-enrich` default
  to Apify/MillionVerifier (`EMAIL_VERIFY_PROVIDER` in `main.py`).
  **ZeroBounce** (`audit/email_verifier.py`, `ZEROBOUNCE_API_KEY`, free tier
  100/month) stays fully wired as both the automatic fallback when Apify's
  monthly cap is hit and a manual override
  (`EMAIL_VERIFY_PROVIDER=zerobounce`). Google-footprint sourcing stays on
  Firecrawl search feeding `classify-footprint` — never was about the cap.
- Chromium/Playwright is only needed for the `main.py walk` fallback.
  Managed cloud sessions: Chromium lives at `/opt/pw-browsers/chromium` (the
  crawler auto-detects it; override with `FUNNEL_AUDITOR_CHROMIUM`), and the
  crawler auto-writes a Chromium policy disabling the PQ/ECH TLS handshake the
  MITM egress proxy resets. Local (WSL): `pip install -r requirements.txt &&
  playwright install chromium` (only for the Playwright fallback).
