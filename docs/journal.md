## 2026-08-03 (the 70-lead measurement) — 37% found, 14% verified, and a warm thread

The FOUND rate the last two entries kept saying was unknown. Batch
`2026-08-03-ig73`, every actionable row of the Instagram list.

**A warm-thread hit, and it is the headline.** `dedupe` stopped on **Rita Baki
— matched on name, status Offer Sent**. She is on the wall at a live stage and
she is on this list. Nothing reached her: the wall runs before any paid call and
she is excluded from `clear73.json`. This run sent nothing and was a search, but
the wall did the one job it exists for, on the first list it was pointed at
since it was built.

### The funnel

| | n | of 70 |
|---|---|---|
| rows in the sheet (A+B+C) | 73 | |
| survived intake | 71 | two rows had neither a parseable name nor a site |
| clear of the wall | 70 | |
| **FOUND — an address with a citation** | **26** | **37%** |
| ABSENT | 22 | 31% |
| CLAIMED (AI Overview only) | 12 | 17% |
| NONE | 10 | 14% |
| **verified deliverable (PASS)** | **10** | **14%** |
| WARN — catch-all or inconclusive | 12 | 17% |
| FAIL — hard bounce | 4 | 6% |

Of the 26 found: 10 role accounts, 9 on free providers, 7 personal-on-branded.
**The free-provider share matters** — `email_enrich` refuses to guess against a
free provider, correctly, so those nine were reachable by no other path in this
machine.

**Cost: $0.2010 total.** $0.1750 of search over 70 leads ($0.0025 each) and
$0.0260 verifying 26 addresses ($0.0010 each). The whole measurement cost less
than a twentieth of what one shipped email costs in tokens.

### The failure mode the corroboration rule does not catch

`brandon.garcia@unlv.edu` for a Dubai coach named Brandon Garcia — the
University of Nevada. `jack.graham@avisonyoung.com` — a commercial real estate
firm. `matt.wright@gmail.com`, which **verified PASS**.

All three passed corroboration on `name_match`, which asks whether the local
part carries the lead's name and cannot ask whether it is *this* person of that
name. The previous entry's three revisions fixed "an address on a page that
merely mentions them"; none of them touch **a different human being with the
same name**. The verifier caught two of the three as hard bounces, by luck
rather than by design: a real stranger's real mailbox verifies clean, and
`matt.wright@gmail.com` is exactly that.

So **14% is the upper bound on usable, not the number**. Call it 12%, and treat
a FOUND address as a candidate a human confirms, never something to adopt. The
preview is the gate, as it has always been.

### What it is worth

The list arrived with zero addresses and the 5-lead probe called it
0% reachable. It is about 12-14% reachable for twenty cents.

The more valuable half is the other 44 of 70 — **63% have no address anywhere**.
`plan --addresses` declines their paid rungs, and the batch skill now names
`work/addresses.json` as the mechanical form of a condition it already carried
in prose: an unreachable lead does not enter the hook wave or stage 4. Four
agent passes each, on 44 leads, for emails that could never be sent. That is
where the token bill of q2 and q3 actually went.

Nothing here settles whether 37% is good. It is one list, mined one way, in one
market, and the previous entry's finding still stands: query wording swings the
yield and the SERP is not deterministic.

