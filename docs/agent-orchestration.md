# The worker/verifier chassis

_Rewritten 2026-07-31. The previous version described the funnel-audit pipeline
— `source-leads`, `qualify-leads`, `batch-audit`, a Notion CRM, Gmail drafts,
and six agents that no longer exist. The **pattern** survived the pivot intact;
every instance of it changed. This file is the pattern, against the machine that
is actually here._

## Why it exists

Every stage used to have one context self-certify its own output. That shipped
false findings, unread citations into real drafts, and soft-passed audience
numbers into full walks. A third of self-certified findings failed under
scrutiny while carrying a verified flag.

The fix is structural, not motivational: **the agent that makes a consequential
claim never gets to certify it.** A second agent, which never saw how the claim
was reached, re-derives it from the evidence alone and defaults to rejecting it.

## The shape

```
orchestrator (a skill, in the main loop)
   |-- fan out workers over a slice     -> each returns a typed object
   |-- verify the ONE self-certified claim, independently
   |-- cross-check the store, not the worker's word
   +-- emit one brief
```

The orchestrator does three things and no per-lead work: fetch a batch, fan out,
write the result. The exception is a stalled worker, taken over directly rather
than nudged twice.

## The instances in this machine

| Stage | Worker | Verifier | The one claim re-checked |
|---|---|---|---|
| Research | `research-worker` | *(none — schema instead)* | see below |
| Hook | `hook-worker` | `hook-verifier` | the quote is really at the cited URL |
| Draft | `draft-worker` | `draft-verifier` | beat 1 connects to beat 2, and it still sounds like Haytham |

**Research has no verifier on purpose.** Its claims are settled by
`python main.py research`, which rejects a verdict outside the enum and any hard
yes/no with no source named. A schema check is cheaper than an agent and
strictly harder to talk around, so where a mechanical check can do the job it
does. Spend an agent only on claims no regex can settle: whether a quote is
really on a page, whether a paragraph reads like a person wrote it.

## The rules that make it work

**The verifier never sees the worker's reasoning.** Give it the claim and the
citation, nothing else. Summarising the worker's search into the verifier's
prompt destroys the entire mechanism while looking helpful.

**Three verdicts, not two.** VERIFIED, REFUTED, INCONCLUSIVE. A refutation needs
a citable contradiction, never a feeling. INCONCLUSIVE — page gone, login wall,
content changed — holds the lead where it is. It is not a kill, because a false
kill is permanent and invisible.

**Only the verifier promotes.** The worker proposes; the flag is written by the
thing that checked it.

**Cross-check the store, not the report.** A worker's return block is a report.
For every consequential result, re-read the actual record and confirm the write
landed. A claimed success over an unwritten row is Blocked, not Done.

**Prefer a mechanical check to an agent, always.** The linter, the research
schema, the dedupe wall, and `export --anchors` each replaced something a human
or an agent was supposed to remember. The drift check is the newest example: the
drafting worker is *told* to use the lines it was handed, and `check_dealt`
makes disobeying it impossible to ship rather than merely discouraged.

**Least privilege.** Each agent lists only the tools its flow calls. No worker
gets a send-capable tool. No worker spawns sub-workers — orchestration stays in
the top-level skill. Research and hook work get `WebSearch` and `WebFetch`,
because free fetching is the first rung of the ladder now that Firecrawl is gone.

**Check a shared budget once per batch.** Apify is cost-gated; the orchestrator
reads the limit once and passes the answer into every worker prompt. Once per
worker is how a quota gets rediscovered fifty times.

**Quality tripwire.** If the verifier refutes two or more of the first wave,
stop and surface it before spending the rest of the queue. Two refusals in a row
is a problem with the instructions, not with those two leads.

## The return contract

- Computed facts are **quoted literally**. A tool's own output line is the only
  acceptable claim of "I checked this."
- Judgement fields are **enums**, so an out-of-range value is a catchable schema
  violation rather than a plausible sentence.
- The certifying field is **proposed, never asserted**, by the worker.
- On a hard fail, still return the full block with the failure noted. An
  orchestrator guessing why a lead vanished is worse than a `no` it can read.
