# The outbound machine

> **Lost? Read `docs/START-HERE.md`.** One page: what is sold, what the email
> is, the machine in one line per stage, and the checks that fail closed. This
> file is the full map.

A raw list of UAE coaches goes in. A Smartlead upload file comes out, one row
per lead, carrying an email written for that person and mechanically checked
before it was allowed into the file.

**The machine ends at a file.** It does not send. Smartlead owns the inboxes,
the warmup, the ramp, the sequence steps and the replies. Haytham uploads.

## What is sold

The email offers **ten names** — real people who fit her buyer profile, already
pulled, handed over on a fifteen-minute call along with why those ten and not
the other forty. That is the entire ask. No price appears in any email.

The paid offer lives on the call, not in the inbox. Nothing in the machine
quotes a number.

## Why it was rebuilt (so nobody re-litigates it)

Two systems merged on 2026-07-31.

**The funnel auditor** ran 589 leads and made zero. Its diagnosis: it sold a
finding, and a finding in an inbox is a free fix — 4 of 9 engaged leads read it,
fixed it themselves and left. Its reply rate was fine (7-9% against a 1-5%
benchmark); reply to call was 0 of 9. What survived is its chassis: fail-closed
Python gates, worker/verifier orchestration, and the email-verification layer.
The audit, the walk, the findings and the Gmail sending are gone.

**The cold-email system** had the right ingredients — a proof-based identity
beat, a concrete offer, a real CTA — and a pipeline with no repo, no state, and
beats stapled together mechanically so the hook never connected to the paragraph
after it. What survived is its copy and its offer. Its pipeline did not.

The merge point: **the hand-written lines became the drafting model's anchor,
and a deterministic linter made that safe.**

## The machine, one line per stage

```
intake      raw CSV -> Leads, junk stripped, platform URLs routed to social
dedupe      name/domain BEFORE any paid call; email again after research
fetch       free local HTTP first; ONE batched Apify run for what it can't read
research    research-worker per slice -> typed objects, schema-validated
hook        hook-worker proposes -> hook-verifier re-fetches the citation
draft       draft-worker writes against the anchors -> draft-verifier reads cold
lint        every check that can be mechanical, failing closed
export      leads.csv (assembled subject + body) + preview.txt
```

`outbound-batch` runs the whole thing. `outbound-draft` is the single-lead and
repair path.

## Hard rules

- **Never send an email.** The machine ends at a file. Sending is Smartlead,
  triggered by Haytham.
- **Never log in to, act as, or automate anything through Haytham's own
  accounts on any platform.** Read-only, no-login tools only. This is an
  identity rule, not a platform ban: public data through a no-login third party
  is fine, on LinkedIn and Instagram the same as anywhere.
- **Never invent a hook.** It is a citation or it is nothing. A hook that cannot
  be re-fetched and confirmed means the lead holds and gets no row. No hook
  found is a good answer.
- **Never invent a number, and never relabel one.** Every number in an email
  must be true of a real client result in `copy/results.csv`. A number sitting
  next to a named segment must belong to that segment: widening to "coaches
  here" is honest, calling a Business result a health coach's is not. Enforced
  by `python main.py lint`, which fails closed.
- **Dedupe runs before any paid call.** Name and domain first, email after
  research. The old pipeline deduped last and paid for eight Apify calls on an
  already-excluded lead. **A warm-thread hit stops the run.** A cold opener
  landing on a live conversation is the only failure here that destroys
  something rather than wasting something.
- **No agent certifies its own work.** Every stage that makes one consequential
  claim has an independent verifier that never saw how the claim was reached,
  and defaults to rejecting it. See `docs/agent-orchestration.md`.
- **The preview is the gate.** No automated check replaces reading ten emails in
  full before uploading. The linter catches invented numbers and lost claims; it
  cannot catch a hook that lands wrong on a specific person.
- **Copy rules, every email:** no em-dashes. No operator jargon (funnel,
  conversion, audit, sequence). No weak closers. Sign off "Haytham". Numbers with
  separators. No gendered pronoun in an identity line.

## The gates (all fail closed, all quotable)

Skills run these and quote the literal output line rather than paraphrasing it.

- `python main.py qualify <lead.json>` — the three floors. **`unclear` passes;
  only a clear `no` drops a row.** A false kill is permanent and invisible; a
  false pass costs one research call.
- `python main.py research <obj.json>` — schema. Catches a verdict outside the
  enum, and a hard yes/no with no source, which means it was reasoned rather
  than fetched.
- `python main.py lint <drafts.json>` — traceability, claim preservation, the
  bridge, voice, and batch repetition.
- `python main.py email-check|email-verify|email-enrich` — address shape,
  deliverability, and the no-address fallback on her own branded domain.
- `python main.py dedupe` — exits 1 on a warm hit.

## The ICP

Three hard floors, and that is all: **UAE-based** (based here, not merely
serving here), **actually a coach**, **active in the last 30 days**.

Captured but never gated on: `coach_type`, `sells_to`, `audience_size`,
`top_program_price_aed`, `solo`. Two of these used to be floors and both were
wrong for different reasons — audience decoupled from the offer the moment we
started selling her clients rather than leverage on her list, and a price floor
reads `unclear` on ~94% of the market, which is a coin flip with extra fetches
attached.

`coach_type` picks the identity line, so it matters: **LinkedIn wins when the
site disagrees.** `sells_to` is collected from her own words, never inferred —
an empty answer draws a generic line, which is weaker than an exact match and
much stronger than a wrong one.

## Key pieces

Pointers, not manuals. Every module carries a full docstring.

**`outbound/`** — `normalize` (raw row to Lead, junk classification),
`dedupe` (the two passes and the Contacted-Before wall), `fetch` (the free-first
ladder and the batched Apify plan), `qualify` (the three floors, evidence-
carrying), `research` (the typed contract every worker returns), `anchors` (the
deterministic line draw and the fact table), `lint` (the checks), `export`
(leads.csv and preview.txt).

**`audit/`** — what survived the pivot: `email_check`, `email_verifier`,
`email_enrich`, `apify` (cost-gated), `extract`, `urls`, `draft_lint`,
`footprint`.

**`copy/`** — Haytham's hand-written lines. `identity.csv`, `offer.csv`,
`cta.csv`, `ps.csv`, and `results.csv`, which is the fact table every number in
every email traces back to. Edit these rather than the code.

**Skills** — `outbound-batch` (the whole run), `outbound-draft` (one email, and
the voice references). **Agents** — `research-worker`, `hook-worker`,
`hook-verifier`, `draft-worker`, `draft-verifier`.

## Environment

- **The repo's `.claude/skills/` is authoritative** — never a remembered or
  globally-installed copy. A SessionStart hook fingerprints every on-disk
  SKILL.md; if the `v=` differs from what you recall, the file on disk wins.
- **Cross-session memory is `docs/journal.md`.** The container is ephemeral.
  When a session does anything worth remembering, add a dated entry at the top
  and commit it.
- **Firecrawl is gone** (2026-07-31). The fetch ladder is: local
  `requests` + BeautifulSoup, then the agent's own WebSearch/WebFetch, then
  Apify for what is genuinely login-walled.
- **Apify** needs `APIFY_TOKEN`. Every run is cost-gated at $0.10 and blocks
  with `APPROVAL REQUIRED` / exit 3 above it. **Check the budget once per batch,
  not once per worker.** Container boot dominates the bill, not pages — batch
  every URL into one run.
- **Email verification** defaults to Apify/MillionVerifier, auto-falling back to
  ZeroBounce (`ZEROBOUNCE_API_KEY`) when Apify is near cap. Force with
  `EMAIL_VERIFY_PROVIDER=zerobounce`.
- **Airtable** is the CRM, via MCP. Base `appejF07kunksqt4D` ("Outbound
  Machine"): Leads `tbl9lyituyqG8dlnb`, Batches `tbl97PsqhdndK14hP`, Copy Assets
  `tblZnpXiuGy6V1mzl`, Contacted Before `tblXFiyyKeYwgSUTL`. The old
  funnel-audit base `appaBExqyEZykb1Qk` is archive only, never written to.
- **Smartlead** owns sending. No API key here yet; handover is a CSV Haytham
  uploads by hand.
- `pip install -r requirements.txt`. No browser needed — Playwright went with
  the crawler.
