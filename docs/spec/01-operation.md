# The operation

_Written 2026-07-31, at the merge of the funnel auditor and the cold-email
system. This file is what the business is; `docs/spec/03-offer.md` is what it
charges, and `docs/spec/05-pipeline.md` is how the machine runs._

**Owns:** what the operation is, who does which part, and the constraint that
decides everything else.
**Defers to:** `docs/spec/03-offer.md` — every price and the money model;
`docs/spec/02-icp.md` — who this is sold to; `audit/apify.py` — the Apify cost
ceiling and its approval gate; `docs/START-HERE.md` — the one-page orientation.
**Allows:** none.

## In one line

Haytham finds UAE coaches their next clients, and proves it by handing them ten
real names before asking for anything.

## The three roles, and the seams between them

The seams matter more than the roles. Every failure worth worrying about happens
at a handover, not inside a stage.

| Who | Owns | Ends at |
|---|---|---|
| **The machine** | sourcing, research, hooks, drafting, every mechanical check | a file. `out/leads.csv`, and nothing after it |
| **Haytham** | uploading that file, taking the call, delivering the ten | the relationship |
| **Smartlead** | inboxes, warmup, ramp, the sequence steps, replies | the reply landing in Haytham's inbox |

**The machine ends at a file, and this is not a limitation to be engineered
away.** It is the property that makes the whole thing safe to automate. A
pipeline that drafts and sends is one bad batch from an unrecoverable mistake
across a few hundred real people; a pipeline that drafts and stops is one bad
batch from a file nobody uploads. The gap between those two is a human reading
`out/preview.txt`, and that gap is the point.

## The two rules only a person can keep

Every other rule in this repo is enforced by code. These two cannot be, so they
are written where they will be read.

- **Never send an email from the machine.** Sending is Smartlead, triggered by
  Haytham.
- **Never log in to, act as, or automate anything through Haytham's own accounts
  on any platform.** Read-only, no-login tools only.

The second is an identity rule, not a platform ban. Public data through a
no-login third party is fine — on LinkedIn and Instagram exactly as anywhere
else. What is forbidden is the machine wearing Haytham's face.

## The constraint

**Capacity is hours. It has never been cash.**

Cash cost to acquire a customer on cold email is close to nothing: the data is
free or nearly, the domains amortise, and the fetch ladder spends its first two
rungs on free tools before it spends anything at all. What is scarce is
Haytham's time — delivery is hands-on, and concurrent clients are counted on one
hand.

Three consequences, and they are the reason this file exists:

1. **The money model is not solving a cash-flow problem.** It is solving a proof
   problem and a slot-filling problem. Standard advice about recouping
   acquisition cost fast is answering a question this business does not have.
2. **The answer to spare capacity is a higher price, not more volume.** More
   volume converts a scarce hour into a cheaper hour. `docs/spec/03-offer.md`
   holds the number and the argument.
3. **Spend on the machine is bounded and gated, not optimised.** The Apify cost
   ceiling and its approval exit live in `audit/apify.py`; the batch checks the
   budget once per run rather than once per worker, because container boot
   dominates that bill and rediscovering the quota fifty times is how a cheap
   run becomes an expensive one.

## Where the money is not

**No price appears in any email.** The inbox sells a fifteen-minute
conversation and a deliverable; the conversation sells everything else.

This is held mechanically, though indirectly, and it is worth knowing exactly
how — see `docs/spec/04-email.md`. The short version: the linter admits only
numbers that trace to a real client result, so a price fails as an untraceable
number rather than as a price. There is no rule in the code with the word
"price" in it.

## What is actually unknown

The honest list, because these are what matter now and none of them is a
detail:

- **Reply to call has never been above zero.** The previous system got replies at
  a healthy rate and converted none of them to a conversation. The ten-names
  offer is the fix — a deliverable instead of a question — and it is a bet, not a
  result.
- **Nothing behind the call has been sold yet.** The attraction offer has been
  shipping for months; the thing it attracts people toward is built on paper and
  has never been bought. `docs/spec/03-offer.md` marks which shelf each piece is
  on, and refuses to let the unbuilt read as live.
- **The ten must exist on the call.** The close now carries a clock. This is the
  first promise the coach can check and it comes due before anything is sold, so
  breaking it costs more than never having made it.
