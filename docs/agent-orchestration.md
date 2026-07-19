# Agent orchestration — the shared chassis

This is the single, DRY description of how the pipeline's agent stages run.
Every stage orchestrator (`source-leads`, `qualify-leads`, `batch-audit`,
`haytham-hook-finder` batch mode) follows the pattern here and adds only its
own stage parameters. Read this once; the per-stage SKILL.md gives the specifics.

**Why this exists.** Agent output quality was low because at every stage a
**single context self-certified the one claim that mattered** — the walk's
finding, the hook's citation, the Gate 0/1 verdict, "this candidate is real" —
with nothing independent re-checking it. False Lane-1 findings shipped cold
emails; an unviewed post's numbers reached a real Gmail draft; a soft audience
pass sent three leads into full walks that all failed. The fix is the same at
every stage: **fan the work out, then have a second, independent context verify
the self-certified claim before anything downstream trusts it.** Keeping the
pattern in one file also kills the drift that produced bugs like batch-audit's
15-vs-20 cap (the same rule maintained in four places).

---

## The four stages

| Stage | Orchestrator (skill) | Worker agent | Verifier agent | Grain | The self-certified claim the verifier re-checks |
|---|---|---|---|---|---|
| 1 Source | `source-leads` | `sourcing-worker` | `sourcing-verifier` | one worker per **vein** | "this candidate is reachable / has a real offer / is unique / audience is a real number" |
| 2 Qualify | `qualify-leads` | `qualifier-worker` | `qualifier-verifier` | one worker per **slice of Sourced rows** | the Gate 0 / Gate 1 verdict (esp. audience provenance) on every promotion and kill |
| 3 Walk | `batch-audit` | `lead-processor` | `finding-verifier` | one worker per **lead** | the strongest finding (the thing that ships a cold email) |
| 4 Hook | `haytham-hook-finder` (batch) | `hook-worker` | `hook-verifier` | one worker per **Audit Ready lead** | the hook's citation (URL resolves, the quote/date actually appears) |

Drafting (`haytham-email-draft`) is deliberately **not** fanned out — its
catastrophic failures are already code-gated (`audit/draft_lint.py`, the
`gmail_draft_link_guard.py` PreToolUse hook, `crm-gate send`), so it stays an
in-context draft→gate→10/10 loop. An optional read-only `draft-critic` can add a
second pair of eyes on the subjective voice items only.

CRM: `collection://5efbdd9b-1e19-468c-96db-f94a525846e0` (REST DB
`5a9fc583160046d1a64c4e65cc804229`). **Never** the parenting DB
(`c6209e29-55ef-4781-b735-73b2a254e34f`).

---

## The six elements every stage shares

### 1. Orchestrator = a main-loop skill
Three moves: **fetch** a batch from the CRM by status → **fan out** workers →
**verify** → emit **one** structured brief. The orchestrator does not do the
per-unit work itself (except a stall takeover, below); it dispatches, collects,
cross-checks, and reports.

### 2. Workers = cold-start typed subagents
- **Least-privilege `tools:`** — enumerate exactly what the flow calls; exclude
  everything else. A worker that must not send email gets **no Gmail tools**, so
  "never send" is tool-enforced, not just prose. See the tool convention below.
- **Pinned `model:`** — pin the quality tier the stage needs; do not let it drift
  to a cheaper model on a whim. The judgment-heavy workers (walk, hook) stay on
  the top tier; a cheap worker feeding a verifier is "garbage in," which defeats
  the point.
- **Structured JSON return** (see the return contract).
- **Return vs. write:** a worker WRITES its own narrow result when rows are
  disjoint (qualify: each row is owned by one worker; walk/hook: one lead each).
  A worker RETURNS its result for the orchestrator to merge when results can
  collide (source: sibling veins surface the same coach — only the orchestrator
  can dedup across workers and against the live CRM).

### 3. Independent verification of the one self-certified claim
A separate context that **never saw the worker's reasoning**, handed only the
claim + its cited evidence, told to **disprove it**. This is the whole quality
fix — the worker believes its own summary, so the worker cannot honestly check
itself. The verifier:
- Runs the stage's mechanical checks (re-fetch the URL, re-match the quote,
  re-run `gates.py`, re-open the screenshot) — the checkable half.
- Returns a verdict ∈ **{VERIFIED, REFUTED, INCONCLUSIVE}**.
  - `VERIFIED` — and **only** the verifier, never the worker, then checks the
    gate box / confirms the promotion. The entity that certifies is the entity
    that independently confirmed.
  - `REFUTED` — the claim is killed; requires a **cited contradiction** (which
    path/check disproves it), never a vibe.
  - `INCONCLUSIVE` — holds at the current status with the reason; **never a
    false kill** (same shape as an `EMAIL VERIFY: WARN` hold).
- Runs only on the **consequential subset** (Lane 1 findings, gate
  promotions/kills, non-empty hooks) — the cheap majority skips it.

### 4. Orchestrator cross-check against Notion
The worker's return block is a **report, never the source of truth.** For each
consequential result the orchestrator re-fetches the row and asserts the write
actually landed and matches the block (the fresh computed-fact line is present,
the gate box is in the expected state, the finding/hook text matches). A block
that claims success over a row that wasn't written → **Blocked**, not Done.

### 5. Demand-driven batch sizing (the "dynamic" part)
Each stage pulls only what the **next** stage can absorb, so the pipeline is
demand-driven instead of dumping:
- **Source** tops up to keep the Sourced/Qualifying buffer non-empty (fill to a
  target; don't flood).
- **Qualify** sizes to the walk's appetite (the run cap, 20).
- **Walk** sizes to send headroom — `python main.py inbox counts` +
  `send-cap status --all` across both inboxes; a walk with nowhere to send is
  wasted.
- **Hook** sizes to the same send headroom (Audit Ready → drafts → sends).

### 6. Governance (identical everywhere)
- **Concurrency:** at most **5 agents running at once, of any kind** — workers
  and verifiers share that budget. Dispatch in waves; as one finishes, launch
  the next.
- **One resume, not two:** a worker that returns a status-only stub with no new
  work product has stalled. Do **not** resume it a second time or nudge it —
  take the unit over directly from whatever it already produced on disk, and
  finish it yourself. (CLAUDE.md; batch-audit's stall guardrail is the
  reference.)
- **Apify cap checked once, up front** (`python main.py apify limits`), not once
  per worker — if `near_cap`, tell every worker in its prompt to skip Apify and
  proceed on Firecrawl/search signal.
- **Quality tripwire:** if the verifier **REFUTES ≥2 of the first wave**, pause
  the batch and surface to Haytham before spending the rest of the queue — a
  high refute rate is the machine noticing its own bad night.

---

## The structured return contract

Every worker ends its turn with a single fenced ```json object the orchestrator
parses programmatically (never by eye). Rules:
- **Computed facts are quoted literally, never paraphrased** — the exact
  `VISION PASS: …` line, the exact `EMAIL VERIFY: …` / `EMAIL ENRICH: …` line,
  the exact gate output. "N screenshots read" as a self-summary is banned; the
  tool's own line is the only acceptable claim.
- **Judgment fields are enums**, so an out-of-range value is a catchable schema
  violation (e.g. `lane ∈ {1,2,3}`, `status ∈` the real lifecycle values,
  `gate0/gate1 ∈ {Pass,Fail}`, verdicts ∈ {VERIFIED,REFUTED,INCONCLUSIVE}).
- **The certifying field is proposed, not asserted** — a walk worker returns
  `finding_verified: "proposed"` (it cannot say "checked"); the orchestrator
  fills a separate `verification` field with the verifier's literal verdict line
  after the verifier runs.
- On any hard-fail, still return the block with the failure in a `notes` field —
  never leave the orchestrator guessing.

Each stage's SKILL.md / agent file defines its own exact keys; these rules are
constant across all of them.

---

## Least-privilege tool convention

Give each agent the smallest tool set its flow actually invokes. Start from the
commands in the stage's flow-of-record and list only those:
- Local work: `Read`, `Write`, `Bash` (`python main.py …` + `curl`), `Glob`,
  `Grep` — as needed.
- Fetch: the specific `mcp__Firecrawl__firecrawl_*` tools the flow uses (usually
  `scrape` / `search` / `map` / `crawl`). Apify is `python main.py apify`, i.e.
  covered by `Bash` — there is no Apify MCP tool.
- CRM: the specific `mcp__Notion__notion-*` tools (usually `fetch`, and
  `update-page` and/or `query-data-sources`).
- **Exclude by default:** all Gmail tools (except the actual draft step in the
  draft flow), Slack, GoDaddy, Google Drive, Heggsfield, github, `WebFetch`,
  `WebSearch`, and `Task`/`Agent` (workers never spawn sub-workers —
  orchestration stays in the skill). Verifiers get read/fetch tools and no write
  to the thing they verify (independence).

---

## Hard rules every agent inherits

The full hard rules live in `CLAUDE.md` and `process-lead/SKILL.md` (the
canonical copy). Every worker and verifier is bound by them; the load-bearing
ones for agents:
- **Never send an email.** Gmail drafts only, and only in the draft flow.
- **Never log in to / act as Haytham on any platform.** Read-only public data
  through a no-login tool is fine; being him is not.
- **Never invent a finding or fabricate a hook.** No verified evidence → Lane 2
  / "no hook found". The verifier is the new enforcement of this.
- **Two CRMs, never crossed.** UAE leads only in the UAE CRM.

---

## Note: agent files are not fingerprinted

The `SessionStart` skills-authoritative hook fingerprints `skills/*/SKILL.md`,
**not** `.claude/agents/*.md`. So agent files are not under that
authority-injection mechanism — keep them thin and push authoritative logic into
the fingerprinted skills they point to (this is why `lead-processor` executes
`process-lead` rather than restating it). Extending the hook's glob to cover
`agents/*.md` is a worthwhile follow-up.
