# START HERE

_Written 2026-07-31, when the funnel auditor and the cold-email system merged.
If you are lost, read only this page._

## 1. What this is

A raw list of UAE coaches goes in. A Smartlead upload file comes out: one row
per lead, with an email written for that person and mechanically checked before
it was allowed into the file.

**It does not send.** Smartlead owns inboxes, warmup, sending and replies.

## 2. What the email offers

**Ten names.** Real people who fit her buyer profile, already pulled, handed
over on a fifteen-minute call along with why those ten and not the other forty.

No price appears in any email. The money conversation happens on the call.

## 3. The email, in five beats

Each beat answers the objection the reader raises at that exact moment. That is
why the order is fixed.

1. **Hook** — *is this a spammer?* One or two sentences about something specific
   and recent she did, cited, plus a clause saying what you took from it.
2. **Identity** — *who is this and why should I care?* A matched reference
   group, a real number, a timeframe. **It must turn to the reader before its
   first digit.**
3. **Offer** — *what can you do for me?* Ten names, already pulled.
4. **Close** — *what happens next?* Fifteen minutes, a clock on the deliverable,
   and why these ten and not the other forty.
5. **ps** — a costless no.

67 to 95 words. Plain text, no links, no price. Sign off "Haytham".

## 4. Why it changed

The funnel auditor ran 589 leads and made nothing. Its reply rate was good
(7-9% against a 1-5% benchmark). **Reply to call was 0 of 9.** Two causes: it
sold a finding, and a finding in an inbox is a free fix — 4 of 9 engaged leads
read it, fixed it themselves and left. And its CTA was a question, which selects
for replies that are *answers*, and an answer is a dead end that looks like
success.

The cold-email system that replaced the offer had the right ingredients and a
pipeline with no repo, no state, and beats stapled together so the hook never
connected to the paragraph after it.

**This machine keeps the auditor's chassis and the cold-email system's copy.**
The join is that the hand-written lines became the drafting model's anchor, and
a linter made that safe.

## 5. The machine, one line per stage

| Stage | What it does |
|---|---|
| `intake` | raw CSV to Leads, junk stripped, platform URLs routed to social |
| `dedupe` | name/domain **before any paid call**, email again after research |
| `fetch` | free local HTTP first, one batched Apify run for the rest |
| research | `research-worker` per slice, objects schema-validated |
| hook | `hook-worker` proposes, `hook-verifier` re-fetches the citation |
| draft | `draft-worker` writes against the anchors, `draft-verifier` reads cold |
| `lint` | everything mechanical, failing closed |
| `export` | `leads.csv` and `preview.txt` |

Fire `outbound-batch` for a whole list, `outbound-draft` for one email.

## 6. The things the code will not let you do

- **No email in the upload file that failed the lint.** Not flagged — absent.
- **No number that isn't true of a real client result**, and none attached to a
  segment it doesn't belong to. `copy/results.csv` is the authority.
- **No hook that a second agent couldn't re-fetch and confirm.** No hook found
  is a good answer; the lead just holds.
- **No paid call before the dedupe wall**, and a warm-thread hit stops the run.
- **No verdict without a source.** A hard yes/no naming nothing was reasoned,
  not fetched, and the schema rejects it.

And two only you can keep: **never log in as yourself anywhere**, and **never
send from the machine.**

## 7. The one instruction no code replaces

**Read `out/preview.txt` before you upload.** Ten emails, in full.

The linter catches invented numbers, lost claims, jargon and repetition. It
cannot catch a hook that lands wrong on a specific person, or a paragraph that
passes every rule and still reads like a robot. That has always been the gate
and it still is.

## 8. What is actually unknown

Be honest about the open bets, because they are what matter now:

- **Reply to call has never been above zero.** The ten-names offer is a real
  deliverable rather than a question, which is the fix — but it is a bet, not a
  result.
- **The tier-0 fetch rate is unmeasured.** Nobody has published what share of
  coach sites a plain HTTP fetch can read. The first real batch measures it;
  every cost estimate downstream depends on it.
- **The ten must actually exist on the call.** The close now carries a clock.
  Breaking that promise costs more than never making it — it is the first thing
  she can check, and it happens before anything is sold.
