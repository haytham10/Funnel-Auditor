# 2026-08-02-q3 — final state, snapshotted because `work/` and `out/` are gitignored

`leads.csv` here is the finished, uploadable Smartlead file: **13 rows**, all
lint PASS, all through `export --anchors`, all independently cold read.
`preview.txt` is the gate and should be read before uploading.

## Outcome

- **13 shipped** of 34 raw, from 17 verified hooks.
- **4 held**, each with a certified hook and dealt lines, so each is cheap to
  finish later and needs no retrieval:
  - **Amjad Saijary** — withdrawn by his own drafter. The post the hook cites
    says he open-sourced the project "not to sell it", so no honest bridge to a
    prospecting offer exists, and he has no evidenced buyer profile. Do not
    re-attempt without evidence of something he sells and to whom.
  - **David Singleton** — two mechanical words away. "in this city" should name
    Dubai (the linter bans "here" against the offer line's "Real people here",
    not the city's name), and the subject restates the hook's first sentence.
  - **Amanda Slade** — an upstream mismatch, not a drafting failure. See below.
  - **Solene Anglaret** — the hardest seam in the batch. The current clause
    ("Improv is mostly about who else is there") was cleared by the last read;
    what failed was the identity beat opening on a slogan, "I pick who you
    should meet."

## The finding this batch exists to record

**Every one of 17 drafts failed its first cold read.** The findings repeated
almost word for word, which made it an instruction gap rather than 17 accidents:
the hook's connecting clause commented on the quote instead of taking something
from it, and the identity beat arrived as the copy line with a "your" bolted on.

`.claude/agents/draft-worker.md` was corrected for both (commit a5ddf4d) and the
11 held leads were redrafted against it. **Nine of the eleven were recovered**,
most on the first attempt. Same leads, same hooks, same dealt lines — the only
thing that changed was the agent file.

## Two things for the next batch

**`hook_room` is stale and reads roughly half the real budget.** Four drafters
independently recomputed it: David 20 vs 47, Stephan 16 vs 41, Anita 18 vs 41,
Chris 17 vs 37. Drafters were cutting "I worked with" and "here" out of identity
beats to buy room they already had, and some first-round failures trace to that.

**`id-life-2` cannot be honestly written for an established coach.** Its claim
is `Life:first_client_days` and its line is "landed their first client in week
1". For Amanda Slade — a master coach with high-net-worth clients — dropping
"first" makes the speed claim evaporate ("week 1 of what, a client out of how
many"), and keeping it reads as beginner advice. Two verifiers reached that
independently. `deal` balances declared weights and has no notion of career
stage, so this recurs until the Life segment has a line whose proof is not a
first client.

## One deliberate deviation, recorded

`cta-02` came out at 38% against the 35% cap because four leads held after the
deal was made. `--rebalance-ps` only moves the ps, by design. Rather than drop a
cold-read-passed email, **Sam Eid's cta was reallocated from `cta-02` to
`cta-03` by hand in `anchors.json`**, and he was re-read cold with the new close
(SEND, no problems). That is a single-beat edit to the deal, not a re-deal — no
identity line moved and no email was re-drafted — but it was done by hand and
should not become a habit. A `--rebalance-cta` would need to re-voice the beat,
which is why it does not exist.

## Not done

`wall-add` and `copy-usage` have NOT been run, because nothing has been
uploaded. Run them only after the upload actually happens.
