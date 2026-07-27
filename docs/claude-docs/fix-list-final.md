# Fix List — Final
 
_Written 2026-07-26. **Supersedes `claude/fix-list-handover.md` (F1–F13) and `claude/fix-list-v2-post-phase10.md` (G1–G17).** Both are consumed; do not work from either. Built on `claude/phase10-wave1-truth.md` (v2, corrected), `claude/nine-threads-and-phase10-correction.md`, and `claude/saraev-translation-a-to-z.md`._
 
**Target:** `haytham10/Funnel-Auditor`, branch `uae-track` (repo default). Notion is the source of truth for live state; the repo is the source of truth for logic.
 
**This document is self-contained.** Claude Code should not need to read the strategy docs. Every fix carries its own evidence so nobody re-derives or reverts it.
 
---
 
# 1. The diagnosis, in one page
 
Nine leads have ever engaged. Every one of them carries `Finding Verified = YES`. Here is what each one actually proves:
 
| Lead | What happened | What it proves |
|---|---|---|
| **Lisa Hugo** | Thanked him, then five minutes later: *"I just checked and don't encounter any issues… All working perfectly."* 404 claim **retracted 07-17**, a www-only technicality. Page notes: *"Lisa pushed back correctly."* | **Finding was wrong at walk time** |
| **William Brown** | *"Where are you seeing and accessing the course content? All i see are the attached."* + screenshots. "Whole course exposed" walked back in Touch 2. | **Finding was overstated at walk time** |
| **Ben Pringle** | Rank-1 finding (vanished guide) **dead on re-walk 07-25** — it is back on the store. Touch 5 had already asserted it was gone. | **Finding went stale between walk and send** |
| **Rita Baki** | Rank-1 and Rank-2 findings **dead on re-walk 07-25** — she fixed the booking flow herself. A **3,200 AED offer scoped around fixing it is still outstanding.** | **Finding went stale between walk and quote** |
| **Lucia Csobonyei** | Long explanation of **her own** offer and pricing. Read him as a prospective coaching client. | **Frame miss — no identity beat** |
| **Lee Harris** | Long unsolicited explanation of his own methodology and tiers. No buying signal. | **Frame miss — no identity beat** |
| **Avneet Kohli** | Genuinely commercial. Asked for costing twice. Touch 4 answered with *"what were you expecting something like this to run?"* Logged `Refused to name`. | **Buying question answered with a question** |
| **Wafa Bassili** | Thanks, then blunt decline. Both sent bodies missing. | Declined |
| **Donna Brown** | Thanks, promised to fix, later declined: happy with her team. | Declined |
 
## The constraint
 
> **Four of nine engaged leads had their finding fail under scrutiny. Two more never understood who was writing to them. That is six of nine lost before the offer was ever the issue.**
 
Phase 10 v2 states it exactly: *"The failure isn't that people won't talk. It's that a meaningful share of the ones who do talk are correcting you. A finding that doesn't hold costs more than silence: it spends the trust the opener just earned, at the exact moment of engagement."*
 
**Reply→call is 0/9, but only 2 of the 9 were ever commercially live, and one of those has a quote priced on work she already did herself.**
 
## The corrected numbers
 
| | |
|---|---|
| Touch 1 | **7/95 · 7.4%** |
| Touch 2 | **2/85 · 2.4%** ← both of the two best threads opened here |
| Touch 3 | 0/22 · 0.0% |
| Positive intent | **9 of 18 messages (50%)**, not 71% |
| Inbox 2 cold openers | **6/35 · 17.1%** |
| Inbox 1 cold openers | **1/60 · 1.7%** |
| Findings that failed under scrutiny | **4 of 9 engaged leads (44%)** |
 
## Three things that are NOT the problem
 
Stated explicitly, because two prior versions of this list attacked them:
 
1. **Cold follow-ups.** 2.4% is weak, not dead, and Touch 2 produced both Avneet and Rita — the only two commercially live threads that have ever existed. **Do not cut them.** (v1 of Phase 10 said to. It was wrong.)
2. **The turn-two script.** It is imperfect and gets fixed below, but it is not the constraint. Only two leads ever reached it.
3. **The market, the channel, the price, and the leads.** All checked, all fine, all previously ruled out.
---
 
# 2. The fix list
 
Twenty fixes, five phases. Each phase gates the next.
 
| Phase | Theme | Fixes | Gate to next phase |
|---|---|---|---|
| **P0** | Stop the bleeding | H1–H4 | Rita and Ben resolved; staleness gate live |
| **P1** | Finding integrity | H5–H9 | Zero findings shipped without adversarial verification |
| **P2** | The message | H10–H14 | Identity beat and next-step close live in every draft |
| **P3** | Measurement | H15–H18 | Variant machinery gate-enforced; data repaired |
| **P4** | Run and read | H19–H20 | 25 replies on the new opener |
 
---
 
## P0 — Stop the bleeding — **STATUS 2026-07-26, verified against HEAD `d772391`**
 
| Fix | Status | Detail |
|---|---|---|
| **H3** staleness gate | ✅ **Shipped** (PR #83) | `STALE_SEND_DAYS = 3`, `STALE_OFFER_DAYS = 1`, exactly as specced. 25 tests green. Failure message cites Rita by name. **Three gaps → H3a/H3b/H3c below.** |
| **H1** Rita | ⚠️ **Half** | Re-walk landed 07-25, Rank 1 and Rank 2 marked dead. **The re-scoped quote was never sent** — still an unchecked TODO at `docs/journal.md:270`, and `raw.md:67` carries the original 3,200 AED copy verbatim. |
| **H2** Ben | ⚠️ **Half** | Same shape. Rank 1 marked DEAD 07-25, nothing after. |
| **H4** inbox split | ❌ **Not started** | No routing policy change (`ROUTING_POLICIES` is still `headroom, fill-primary`). No `deliverability-log.md` entry since 07-24. The only seed-test line is 07-14, marked *"Scores not yet recorded."* Caps unchanged at 25/25. |
| **H18** method note | ❌ **Not started** | Neither paragraph exists in any form. |
 
**Also found:** the branch has been **red since PR #80** (the Sunday pause). Three failures in `tests/test_send_gate_dubai.py` — fixtures use a 2026-07-18 afternoon `now` whose rolled send-day lands on a Sunday. 240 pass, 3 fail. PRs #82 and #83 merged over it.
 
### H0 · Green the branch *(new, do first)*
Fix the three Sunday-pause fixtures. Not the rule — the fixtures. Every subsequent PR merges over red until this lands.
 
### H3a · Backfill `verified:` dates *(new, BLOCKING)*
**`grep -rn "verified:20"` returns exactly one hit repo-wide, and it is the example in the spec doc.** No lead carries a `verified:` tag. A missing tag hard-fails the H3 gate exactly like an old date would, so **every existing live row fails on its next send or offer.** Backfill every Audit Ready and live row, and add a migration note explaining why they all appear at once.
 
### H3b · Extend the freshness check to warm touches *(new)*
**The gate currently misses its own motivating case.** `check_send` returns early on `touch > COLD_SEQUENCE_TOUCHES` (`crm_gate.py:663-668`), so touches 4, 5 and 6 never reach the freshness block at `crm_gate.py:689-700`. Rita is at Touch 5 and Avneet at Touch 6. The offer gate covers priced quotes, but a warm bump re-asserting a dead finding passes untouched — which is precisely the Rita incident.
 
### H3c · Close the `refresh-finding` loop *(new)*
`refresh-finding` takes `--page-file` (a page the caller already fetched) and `--baseline-file`, runs a `difflib` diff, and explicitly does **not** write a new `verified:` date. A human must fetch, read the diff, and hand-edit. Make it fetch the URL and stamp the date, or the staleness gate stays a manual process wearing a gate's clothes.
 
*(Minor, worth a line in the same PR: `check_send` evaluates freshness against `send_cap.today(now)` even for a touch-1 opener that has rolled to tomorrow's send-day, while the cap logic in the same function correctly uses `send_day`. A post-cutoff opener with a 3-day-old finding passes, then leaves at 4 days.)*
 
---
 
## P0 — original items
 
### H1 · Rita Baki — confirm scope before any further contact
**Owner: Haytham. Today. Not Claude Code.**
 
**Why:** she is at `Offer Sent` with a **3,200 AED quote scoped around fixing a booking flow she has already fixed herself.** Rank-1 and Rank-2 findings both confirmed dead on the 07-25 re-walk. Touch 5 went out the same day **still referencing the booking fix**. Only the shallow currency-fragmentation finding (Rank 3) is still standing.
 
If she replies "I already did that," the quote and the credibility both die at once. This is the single largest live commercial risk in the pipeline.
 
**Do:** re-walk her funnel today. Establish what is actually still broken. Then send one short message that concedes the fix, credits her for it, and re-scopes to what remains. Do not re-assert the booking finding. Do not re-send the 3,200 AED number against the old scope.
 
Shape (not a draft, the skill writes the draft):
> Concede she fixed it, in one line, with credit.
> Name what is actually still open now, specifically.
> One next step. No re-quote until scope is agreed.
 
**Acceptance:** Rita's Notion page shows a fresh re-walk dated today and a live findings bank reflecting reality. No outstanding quote references dead work.
 
### H2 · Ben Pringle — same problem, smaller
**Owner: Haytham. Today.**
 
**Why:** Touch 5 told him the Dubai Football Guide had dropped off the store. It is back. Per his page: *"no findings remain banked for this lead."* He is at Touch 5 awaiting a reply to a Loom offer built on a dead finding.
 
**Do:** if he replies disputing it, concede immediately per H9. If he does not reply, do not send Touch 6 on this thread. Park to Dormant with a revival date and a genuinely new angle.
 
**Acceptance:** no further send to Ben references the guide.
 
### H3 · Finding staleness gate
**Files:** `audit/crm_gate.py` (`check_send`, `check_offer`), `main.py`, Notion/Airtable schema
 
**Why:** Ben and Rita are the same bug. **The walk is a snapshot; threads run 5 to 10 days; Gate 0 selects for coaches who are active, which means coaches who fix things.** Your own qualification criteria guarantee this failure mode, and there is currently no re-check anywhere between the walk and the quote.
 
**Change:**
- New field `Finding Last Verified` (date) per finding, set at walk time and on every re-check.
- `crm-gate send` **hard-fails** if the drawn finding's `Finding Last Verified` is more than **3 days** old.
- `crm-gate offer` **hard-fails** if it is more than **1 day** old. A priced offer quotes work; the work must still need doing.
- New command `main.py refresh-finding <row.json> --rank N` — a single-URL re-fetch of the specific finding's page plus a diff against the stored evidence. **Not a full re-walk.** Cheap enough to run before every send.
**Acceptance:** `crm-gate send` fails on a 4-day-old finding. `crm-gate offer` fails on a 2-day-old one. Both name the Rita case in the failure message so nobody loosens the rule without reading why.
 
### H4 · Inbox split test (runs continuously from day one)
**Owner: Haytham + Claude Code.**
 
**Why:** Inbox 2 returns **17.1%** on cold openers against Inbox 1's **1.7%**. Same-channel control (Google Footprint, cold opener): Inbox 1 **0/28**, Inbox 2 **3/17**. Hook mix WORK-dominant in both, windows overlap. Inbox 1 carries 63% of all sends. Six replies behind it, so it is a hypothesis — but if it holds, **every other measurement in this document is taken through a pipe that loses 90% of its signal.**
 
**Do, part A:** route the next cold-opener batches evenly across both inboxes, same day, same source channel, same hook type. Minimum 20 per arm. This costs nothing; it is a routing decision on sends already happening.
 
**Do, part B, the diagnostic a split test cannot give you:**
 
| Cause | Signal | Fix |
|---|---|---|
| **Deliverability** — Inbox 1 lands in spam or a tab | Placement test shows spam/promotions | Warm it, or retire the domain |
| **Perception** — `auto-mate.one` reads like automation software to a marketing-aware coach, on an email whose entire premise is that a human did this by hand | Placement clean, replies still absent | New domain. Warming cannot fix a name. |
 
Run a seed-list placement test (Mail-Tester, GlockApps or equivalent) on both inboxes the same day. Ten minutes, and it separates the two.
 
**Acceptance:** placement scores logged via `python main.py send-cap log --inbox "<label>" --kind test-score`. Split-batch result recorded. **Do not raise either ramp until this reads out.**
 
---
 
## P1 — Finding integrity (the constraint)
 
### H5 · The verifier must try to refute, not confirm
**Files:** `.claude/agents/finding-verifier.md`, `.claude/skills/haytham-opener-finder/SKILL.md`
 
**Why:** `Finding Verified = YES` sat on all four findings that later failed. **The gate is checking that a finding was recorded, not that it is true.** Lisa's 404 was a www-only technicality — the evidence was real and the claim was false. William's "whole course exposed" was inferred from a listing page; the videos and docs were locked. In both cases the verifier confirmed *"did we see this?"* when the question was *"is what we are about to assert to a human true?"*
 
**Change — invert the verifier's job.** Its instruction becomes: *your task is to make this finding FALSE. Default to reject. Only pass if you tried and could not.*
 
Mandatory refutation attempts, each a hard reject on failure:
 
1. **URL-variant test.** Re-check with and without `www`, with and without a trailing slash, `http` and `https`, and the exact path a real visitor reaches by clicking rather than by direct URL. **Any finding that only reproduces on one variant is rejected.** (Lisa.)
2. **Access test.** Any claim of the form "X is exposed / broken / missing / unreachable" must be verified by **attempting the thing**, never by inferring from a listing, an index, or a sitemap. (William.)
3. **Charitable-path test.** Walk it the way the most competent visitor would, logged out, on mobile and desktop. If the defect requires an unusual path to reproduce, it is not a felt leak.
4. **Overstatement test.** Compare the claim's wording to the evidence's scope. "Some course files are listed" is not "the whole course is exposed." **Reject on scope inflation**, not just on falsity.
5. **Recency test.** Confirm the evidence is from the current walk, not a cached or prior capture.
**Acceptance:** the verifier's return block names which of the five tests it ran and what it found. A finding with a passed test it did not actually run is a failure of the agent, not of the finding.
 
### H6 · Ship a confidence level, not a boolean
**Files:** `audit/crm_gate.py`, `.claude/skills/haytham-opener-finder/references/schema.md`, schema
 
**Why:** `Finding Verified` is a checkbox, so a www-technicality and a screenshot-confirmed broken checkout are indistinguishable. Two of the four failures were *partly* true, which a boolean cannot express.
 
**Change:** add `Finding Confidence` — `Certain` / `Probable` / `Thin`.
- `Certain` — reproduced on every URL variant, on mobile and desktop, by attempting the action.
- `Probable` — reproduced, but with a caveat worth stating in the email.
- `Thin` — reproduced once, narrowly. **Never sendable.** Bank it, do not open on it.
`crm-gate send` fails on `Thin`. A `Probable` finding must be worded with its own hedge in the copy (see H11).
 
**Acceptance:** every banked finding carries a confidence. `Thin` cannot pass the send gate.
 
### H7 · Fill the `Depth` field, and gate on it
**Files:** `.claude/skills/haytham-opener-finder/SKILL.md`, `audit/crm_gate.py`
 
**Why:** `Depth` is empty on **239 of 256 findings.** It was specced, it was optional, it died, and it cost Phase 10 a question. Same story as `Sources` (H16). **A field that is not gate-required is a field that will be empty in three months.**
 
**Change:** the walker sets `Depth` (`Deep` / `Shallow`) on every banked finding at walk time. `crm-gate send --touch 1` fails if the drawn finding has no `Depth`.
 
**Acceptance:** a walk with an unlabelled finding cannot pass the send gate.
 
### H8 · Re-verify before any quote
**Files:** `audit/crm_gate.py` (`check_offer`)
 
**Why:** H3 covers sends. This covers money. **Rita's 3,200 AED quote is the reason.** A quote is a commitment to do work; if the work is done, the quote is worse than silence.
 
**Change:** `crm-gate offer` fails unless every finding named in the offer scope was re-verified **within 24 hours**. The failure message cites Rita.
 
**Acceptance:** an offer draft on a 2-day-old finding cannot pass the gate.
 
### H9 · The graceful concession play *(new copy play)*
**Files:** `.claude/skills/haytham-email-draft/references/mechanics.md`, `references/examples.md`, `references/gate.md`
 
**Why:** **three of nine engaged leads disputed the finding, and there is no rule for what to do about it.** Lisa got a second finding. William got an explanation. Ben got a new finding and then a Loom. None of those is the right move, and all three threads died.
 
Being correctly refuted is a trust *opportunity*, not a loss. Most cold outreach never admits anything. A fast, complete, unqualified concession, with the specific reason you got it wrong, is more credible than the original finding would have been if it had held.
 
**The play:**
1. **Concede in the first line, completely.** No "partly," no "in some cases," no defence.
2. **Say exactly what you saw and why you misread it.** Specific and technical. This is what converts the concession into competence.
3. **Do not serve a second finding in the same message.** (This is the failure in Lisa, Ben and Wafa.)
4. **One next step, and it must cost them nothing.**
Shape:
> You're right, I got that wrong.
> I was hitting the page without the www and it threw a 404 there, which is why I thought it was down. Loads fine the normal way. My mistake for not checking both.
> While I was in there I did notice something on the pricing page I'd want to look at properly rather than guess at again. Want me to check it and come back only if it's real?
> Haytham
 
Note what the close does: it asks permission to be *more* careful, which is the exact opposite of the reflex to recover with more volume.
 
**Acceptance:** `gate.md` gains a Disputed-finding section. A reply disputing a finding cannot be answered with a new finding. One worked example in `examples.md`.
 
---
 
## P2 — The message
 
### H10 · The identity beat
**Files:** `.claude/skills/haytham-email-draft/references/mechanics.md`, `references/voice.md`, `references/gate.md`, `references/examples.md`
 
**Why, now evidenced rather than theoretical:** **Lucia and Lee both read Haytham as a prospective coaching client.** Lucia sent a long explanation of her own offer and pricing. Lee sent his methodology and tiers. Neither was confused about the finding; both were confused about **who was writing.**
 
That is not an accident. A warm, specific, admiring email that asks a curious question about someone's business, with no statement of who you are, has one obvious default reading: *this person is interested in buying from me.* **Two of nine failures are caused by an absent sentence.**
 
The current cold opener structure is hook → finding → cost → close. It never says who is writing or why they can be believed.
 
**Change — five-beat structure:**
 
```
BEAT 1 — HOOK          elaborate the SMYKM hook (this is the admiration)
BEAT 2 — FINDING       stated flat, no discovery frame
BEAT 3 — IDENTITY      NEW. one sentence: who I am and why I spotted it
BEAT 4 — COST          what the gap costs, pictured
BEAT 5 — CLOSE         a next step (H12)
Haytham
```
 
Word budget 90 to 130.
 
**On the two rules this appears to contradict.** `mechanics.md:8` says *"lead with the result, not the credential"* and `04-the-outreach-method.md:19` says *"the finding is what earns the reply. Not the pitch, not the credentials."* Both are about what **leads** the email, and beat 3 does not lead. `04`'s line is specifically about earning the *reply* and it is correct. Beat 3 exists to prevent the reader misidentifying you, which is a different job, and one that has now failed twice. **Precedent already exists in the repo:** `examples.md:323` (Emily Ray) carries *"I work on the backend side for coaches, the pages, the setups, the parts that quietly lose people."* The move exists. It has never crossed to the UAE track.
 
**The line, available today with no new proof:**
> I go through coaching sites here for a living, about a hundred and twenty this year, and this one shows up more than you would think.
 
122 walked funnels is real, specific, honest, and answers "who is this" without a case study. **The moment one Leak Fix is delivered and paid, upgrade this to a named result.** That single event is worth more than every other fix in this document.
 
**Acceptance:** every drafted opener contains an identity sentence. `gate.md` gains: *"Could this email be read as someone wanting to buy from her? If yes, the identity beat is missing or too weak."*
 
### H11 · Hedge a `Probable` finding in the copy
**Files:** `references/drafting-craft.md`, `references/gate.md`
 
**Why:** two of the four failures were partly true. A finding stated flat when it is only probable is what produced Lisa's and William's pushbacks. `drafting-craft.md` currently says *"no adjectives for the leak, point at the exact thing"* — correct for a `Certain` finding, actively harmful for a `Probable` one.
 
**Change:** a `Probable` finding is written as an observation with its own limit visible, not as a fact.
 
- `Certain`: *"Two of the three order buttons open a test checkout at AED 9."*
- `Probable`: *"When I came in from the link on your bio rather than typing the address, the pricing page threw an error. Might just be how I got there, but worth a look."*
The hedge is not weakness. It is what makes you right either way, and it is what turns a pushback into a conversation instead of an ending.
 
**Acceptance:** `gate.md` checks confidence against wording.
 
### H12 · The close is a next step
**Files:** `references/mechanics.md`, `references/gate.md`, `SKILL.md`
 
**Why:** all four UAE cold openers in `examples.md` close on the same two-branch *"is it X, or Y?"* question. 4 of 4. Zero offers, zero time-proposals. A question-shaped close is optimised for replies that are *answers*, and an answer is a conversational dead end. Combined with H10's frame miss, it is why Lucia and Lee replied with essays about themselves: they were asked a question, so they answered it.
 
**Your rules already permit an offer close** (`mechanics.md:44`, `04:136`, `gate.md:33` all say "one question **or** one concrete offer"). Two other lines pull it back: `gate.md:38` (*"a real one-line-answerable question"*) and `SKILL.md:189` (*"one real question they can answer in one line"*). **Reword both, or the gate reverts this fix on the next draft.**
 
**Three legal closes, chosen by finding depth:**
 
1. **Offer-to-fix** (shallow finding, default)
   > I can have that saying the same thing by tomorrow evening. Want me to?
2. **Dated call** (a `RESERVED` deep finding exists)
   > There are two more and one of them costs you more than this does. Easier to show than write out. I can call Tuesday around 4, or Wednesday morning.
3. **Artifact with a time** (visual finding)
   > Faster to show than describe. I can record two minutes on your actual page and send it tonight. Want it?
**The test:** can she say yes in one word, and does that yes move her one rung? If the best possible reply leaves you with nothing to do next, the close is wrong.
 
**Acceptance:** no file defines the cold close as a question. Every opener closes on a next step.
 
### H13 · Turn-two rewrite
**Files:** `references/uae-track.md`, `references/mechanics.md`, `references/examples.md`, `references/gate.md`
 
**Why:** three defects, all identifiable from the threads.
 
1. **It is a menu.** *"Want me to just fix it? … If it's easier, here's my calendar"* is two CTAs. The no-menu rule is written four times (`04:151-156`, `uae-track.md:70-72`, `gate.md:57`, `gate.md:33`) and the canonical script violates all four. `examples.md:170` defends it as *"two doors, both concrete, both forward. No discovery question, no menu."* By `04`'s own definition ("call or video?"), price-or-calendar **is** a menu.
2. **Zero social proof, zero authority, zero scarcity.** A stranger is asked for money by someone who has still never said why he can be believed. Three honest scarcity lines are registered in GSO v2 and **not one has ever shipped in any email.**
3. **It answers buying questions with questions.** Avneet, Touch 4, verbatim: *"before I put a figure on it, I'd rather not guess: what were you expecting something like this to run?"* — sent to a woman who had asked for costs twice. Logged `Refused to name`. Your own docs identified this flip as the cause of two of three refusals.
**Change — two variants and a routing rule.**
 
*Variant A, fix-first. Default when banked findings are shallow.*
> Rather than talk about it, want me to just fix it?
> Access on your side, live within 48 hours, and you only pay once you have checked it and it works. 500 AED.
> I do these most weeks and they take an evening. The reason I offer it this way round is that it is the only version where you are not taking a risk on a stranger.
> I have one slot free this week. Say go and I will start tonight.
> Haytham
 
*Variant B, call-first. Default when a `RESERVED` deep finding exists.*
> Rather than write it out, easier to show you.
> The one I mentioned is the small one. There are two more and one of them matters more than this does.
> I go through coaching sites here for a living and I would rather walk you through what I would do than type it. Fifteen minutes, and if nothing in it is useful you can tell me to get lost.
> I can call Tuesday around 4, or Wednesday morning. Which is less annoying?
> Haytham
 
**Hard rules for every turn-two:**
- **One next step. Never a menu.**
- **Never a new finding.** It must convert the finding already given into an ask. (Lisa, Ben and Wafa all received a second finding and all three died.)
- **Never a question in answer to a buying question.** If she asks what it costs, the number goes in the reply.
- One credibility sentence, one true scarcity line, the friction sentence: *"All I need from you is access and about twenty minutes at the start. After that you do not hear from me until it is live and you are checking it."*
**Acceptance:** no turn-two contains two next steps or a finding the lead did not ask about. `gate.md`: *"A turn-two that introduces a new finding is a rewrite, not a send."*
 
### H14 · Fix the rules that would revert P2
**Files:** `references/gate.md`, `SKILL.md`, `audit/send_cap.py`, `audit/crm_gate.py`
 
1. **`gate.md:38` and `SKILL.md:189`** define the close as a question. Reword to: *"Close is an open door: one next step she can accept in one word, or one real question. Prefer the next step."* Without this, H12 is undone on the next draft.
2. **The Sunday pause has no stated rationale anywhere in the repo.** `is_pause_day` (`send_cap.py:119-126`) fails closed ahead of every other check in `check_send` (`crm_gate.py:480-485`) and costs roughly 14% of annual send capacity. The obvious justification is also ambiguous: the UAE moved to a Monday-to-Friday week in 2022, so Sunday is the second weekend day, not a workday. **Either write the reason in a comment next to the constant, or delete the rule.**
3. **`pipeline-tick/SKILL.md:60-63`** still prescribes "cold Touch 2/3/4 with a real carrier" while `mechanics.md:58` asserts the parenting track has no cold sequences left. `pipeline-tick` never calls `crm-gate send`, so its prose is the only enforcement there. Resolve.
---
 
## P3 — Measurement and data repair
 
> ### ✅ Airtable schema is DONE (2026-07-26)
>
> Ten fields created in base `appaBExqyEZykb1Qk`. Nothing left to design; the remaining work is code reading them.
>
> **Findings** (`tblE6IjJ0EvRinee4`) — `Last Verified` (date, what H3's gate reads, distinct from `Date Found`) · `Freshness (display)` (formula: 🟢 fresh / 🟡 stale for offer / 🔴 stale for send / ⚠ never re-checked, mirror only) · `Finding Confidence` (Certain / Probable / Thin) · `Refutation Tests` (the five H5 tests, multi-select) · `Disputed By Lead` (checkbox) · `_Is Disputed` (numeric helper)
>
> **Leads** (`tblWNogLfDoppYF1l`) — `Variant` (Control / V1 / V2 / V3, sticky per thread like `Inbox`) · `Disputed Findings` (rollup)
>
> **Touches** (`tblkgGqAVlFMyXqHt`) — `CTA Shape` (per-touch, not per-lead) · `Variant (from Lead)` (lookup, so per-variant reply rate is one group-by)
>
> **Two things already existed and do not need adding:** `Findings.Depth` (Shallow/Deep) is live, so H7 is a population problem not a schema one. And `Touches.Direction` already supports inbound rows — the schema was never the blocker on H17 item 7; the convention was.
>
> **One manual step:** add `Disputed finding` as an option on `Touches → Reply Type`. The Airtable API tool cannot add select options to an existing field. Ten seconds in the UI, and it is the option whose absence hid this constraint for a full analysis cycle.
>
> **Notion mirror:** only `Last Verified` matters before cutover, because the gate reads Notion today. Everything else can wait for Wave 2.
 
### H15 · Variant assignment, gate-required and fail-closed
**Files:** `audit/crm_gate.py`, `main.py`, `uae-tick/SKILL.md` *(schema done — see above)*
 
**Why:** without a variant field, changing the opener gives you a before/after across time, confounded by lead quality, inbox age, sourcing mix and every other fix in this document landing in the same window. That is not a test.
 
**⚠️ Design warning:** `Sources` holds **0 records**. `Depth` is empty on **239 of 256** findings. Both were specced, both were optional, both died. **Make it required or it will be empty.**
 
**Change:**
- `Variant` (single select), sticky for a lead's whole thread, exactly like `Inbox`.
- `CTA Shape` (single select): `question` / `offer-to-fix` / `dated-call` / `artifact`.
- `--variant` and `--cta-shape` become **required arguments** on `crm-gate send` for touch 1. Missing, blank, or mismatched against the row's stored value = hard fail, same class as a missing `Finding Verified`.
**Acceptance:** `crm-gate send --touch 1` without `--variant` fails. Tests for both.
 
### H16 · Resurrect `Sources`
**Files:** `.claude/skills/source-leads/SKILL.md`, schema
 
**Why:** the `Sources` table holds zero records and no lead carries a Source link, so source-yield-by-vein is not computable. It was ranked in the Phase 10 plan and simply could not be answered.
 
**Change:** `source-leads` writes one `Sources` record per vein-run and links every lead it creates to it. Not optional.
 
### H17 · Repair the reply data
**Owner: Claude Code + Haytham. Seven items from Phase 10 v2.**
 
| # | Repair |
|---|---|
| 1 | **Lisa Hugo's second inbound message is missing.** She replied twice to Touch 1, five minutes apart; the second disputes the finding. Notion has both, Airtable has one. |
| 2 | **`Reply Type` is wrong on at least 4 of 9 leads.** Lisa, William, Lucia and Lee are all labelled `Interested`. None are. **Add a `Disputed finding` option** — it is a distinct and important type, and its absence is what hid the constraint for a full analysis cycle. |
| 3 | **Lee Harris status drift** — `Price Discovery Sent` in Notion, `Reply Received` in Airtable. |
| 4 | **Donna Brown `Asked For Price`** — `NO` in Notion, `true` in Airtable. Airtable-only edit, never mirrored, and wrong on its merits: her answer is a decline, not a price ask. |
| 5 | **Ben Pringle's duplicated Touch 1 block** re-pasted between T3 and T4. Deduplicated at migration, still in the source. |
| 6 | **Wafa Bassili's two sent bodies are missing.** Both drew real replies ending in a decline and the send half is unreadable. |
| 7 | **The schema cannot represent two replies to one touch.** All 230 Touches are `Direction: Outbound`. **Fix before the go-forward logger is built or this recurs silently.** |
 
### H18 · Encode the method note as a rule
**Files:** `docs/uae-track/01-crm-operating-spec.md`, any future analysis skill
 
**Why:** Phase 10 v1 reached the wrong conclusion and nearly caused the deletion of the mechanism that produced the two best threads in the pipeline. The root cause is worth encoding permanently:
 
> **Never classify a touch by a field that can be rewritten after the fact.** `Sequence`, `Status` and `Reply Type` all describe the lead's *current* state, not its state at send time. Only touch ordering and the reply flags are safe.
>
> **And a guard that passes is not a guard that works.** The v1 reverse-causality guard compared same-day timestamps with a strict inequality and reported a clean zero on a base that was 14 of 17 same-day. **Test the test against a case you know is contaminated before you trust it.**
 
**Acceptance:** both paragraphs appear verbatim in the operating spec.
 
---
 
## P4 — Run and read
 
### H19 · The opener test
 
**Design, using the corrected numbers:**
 
- **Route through Inbox 2 only** until H4 reads out. At 17.1% you need ~150 sends for 25 replies. At Inbox 1's 1.7% you would need 1,470. **This one routing decision is the difference between a three-week test and a six-month one.**
- **Run the new opener on 100% of leads. Do not split 50/50.** The control already exists: 95 cold openers, 7 replies, 0 next-steps of logged history. Splitting halves the learning rate on the only arm that matters. This departs from the standard "always two arms" rule deliberately, because that rule assumes no baseline.
- **Count replies, not sends.**
| | |
|---|---|
| Stop rule | **25 replies** on the new opener |
| Sends needed | ~150 through Inbox 2 |
| **Adopt** | ≥2 next-steps (Call Booked or Leak Fix Sold) out of 25 replies |
| **Revert** | 0 next-steps AND reply rate below 4% |
| **Ambiguous** | 0–1 next-steps at healthy reply rate → the opener is not the problem, escalate downstream |
| **Secondary metric that matters as much** | **Disputed-finding rate.** Currently 3 of 9 leads. If P1 works this should approach zero. Track it separately. |
 
**Write the stop rule and the abort condition into the repo before the first send.** Deciding what counts as success while watching numbers arrive is how you talk yourself into what you already believed.
 
**A statistical note.** The 95% upper bound on a conversion rate given 0 successes in 9 replies is **28%**. Zero-for-nine is compatible with a turn-two converting at up to 28%. The reply→call constraint is real in direction, unknown in size, and **more replies genuinely buys information** — at 0/18 the bound falls to 15%, at 0/30 to 9.5%.
 
### H20 · `python main.py variant status`
**Files:** `main.py`, new `audit/variant.py`
 
Print per-arm sends, replies, reply rate, **disputed-finding rate**, next-steps, and the literal `DIRECTIONAL ONLY, n=<x>` line below the stop rule. Same trust model as `send-cap status`: the gate prints, the tick quotes.
 
---
 
# 3. The roadmap
 
Capacity: 2 inboxes at 25/day = **50/day ceiling**, currently running ~15/day, walk-bound at 12–15 walks/day, six sending days a week.
 
## Week 1 — ~~Stop the bleeding~~ · PARTLY DONE, remainder folded into week 2
- ~~H3 staleness gate~~ ✅ shipped
- Carried: **H0** green the branch · **H3a** backfill · **H3b** warm touches · **H3c** close the loop · **H1b** Rita re-scope · **H2b** Ben park · **H4** inbox split · **H18** method note
## Week 2 — Finding integrity *(now carries the P0 remainder)*
**Do in this order. The first three are blockers.**
1. **H0** green the branch
2. **H3a** backfill `verified:` dates — nothing sends until this is done
3. **H1b** Rita re-scope — the only item with money on it
4. **H3b** warm-touch freshness · **H3c** close the refresh loop · **H2b** Ben park
5. **H5** adversarial verifier · **H6** confidence in the gate · **H8** quote re-verify · **H9** concession play
6. **H4** inbox split · **H18** method note *(both small, both carried twice now)*
*H7 (`Depth`) drops out — the field already exists in Airtable and is live in the Findings Bank DSL. It is a population problem, folded into H5.*
 
**Gate:** run the new verifier against the four known failures — Lisa, William, Ben, Rita. **If it does not reject at least Lisa and William, it is not finished.** That is your regression test and you already have the labelled cases.
 
## Week 3 — The message
- **H10** identity beat · **H11** probable-finding hedging · **H12** next-step close · **H13** turn-two · **H14** rule fixes
**Gate:** draft five openers against real Audit Ready leads. Every one has five beats, an identity sentence, a next-step close, and could not be read as someone wanting to buy from her.
 
## Week 4 — Plumbing
- **H15** variant machinery · **H16** `Sources` · **H17** data repairs (items 1–6)
- **H20** `variant status`
**Gate:** `crm-gate send --touch 1` without `--variant` fails. Repairs 1–6 closed.
 
## Weeks 5 to 8 — Run
- **H19** starts. Route through the winning inbox.
- ~150 sends toward 25 replies. At 12–15 walks/day and Inbox 2 routing, roughly **3 to 4 weeks**.
- **Touch nothing else.** No copy changes, no new fixes, no peeking early. This is the hard part.
- Weekly Sunday read-out: quote `variant status`, log it, change nothing.
**Gate:** 25 replies.
 
## Weeks 9 to 10 — Read out and decide
- Apply the stop rule as written.
- Re-run Phase 10 on repaired data with the corrected classifier.
- **H17 item 7** (inbound rows in the schema) before the go-forward logger exists.
## Weeks 11 to 12 — Whichever door opened
- **Adopted** → scale: more inboxes, GCC geo expansion, casualization layer.
- **Ambiguous** → the opener is fine and the problem is downstream. Turn-two and offer become the next test.
- **Reverted** → back to the finding, with the disputed-rate number telling you whether P1 worked.
## The event that outranks the entire roadmap
 
**One delivered, paid Leak Fix.** It upgrades every identity line from *"I've walked 120 sites"* to *"here's what I did for a coach in Dubai last week."* It converts the turn-two from a promise into a receipt. It unlocks the Phase 1 gate in `offer-packaging-strategy.md`. **If a chance at one appears in week 2, drop the roadmap and take it.**
 
Avneet is at Touch 6 with `Asked For Price` checked, a written brief and a defined job on the table. Rita is at Touch 5 with the same flag. Neither needs a fix list.
 
---
 
# 4. What not to change
 
1. **The finding mechanic itself.** 7.4% on the opener against a 1–5% benchmark. Everything here exists to stop that being wasted.
2. **"Never invent findings."** H5 makes verification harder, never looser. `Finding Verified` stays sacred.
3. **Cold follow-ups.** 2.4% is weak, not dead, and Touch 2 produced both Avneet and Rita. Phase 10 v1 said to cut them and was wrong.
4. **The voice system.** `voice.md`, the kill list, no em-dashes, no operator vocabulary, the burrito test, the 10/10 bar.
5. **Harry Dry's three rules.** Visualize, falsify, bespoke.
6. **The soft-exit ban.** The most reliable negative finding in the whole dataset.
7. **Drafts only, sending is human.** Do not automate the send to hit volume. Add inboxes.
8. **The price.** 735 / 2,575 / 500 hold until two closes land. Every fix here is a message or a quality change; moving price at the same time destroys the read.
9. **Both guarantees, named, with the condition intact.**
10. **Gates in Python.** The whole safety model. Do not move enforcement into Airtable formulas.
11. **Warm-thread rules.** Match length and tone, one decision, stop.
---
 
# 5. Reversal guards
 
Rules a future session will revert on instinct unless the reason sits next to them. **Write the comment in the same commit as the code.**
 
| Rule | Comment to write |
|---|---|
| `Finding Last Verified` staleness gate | `# Rita 2026-07-25: 3,200 AED quoted for a booking fix she had already done herself. Ben: same class.` |
| Adversarial verifier | `# 4 of 9 engaged leads had their finding fail under scrutiny, all with Finding Verified=YES.` |
| Identity beat | `# Lucia and Lee both read this as an inbound coaching enquiry. Two of nine, caused by an absent sentence.` |
| Next-step close | `# 4 of 4 UAE openers closed on a question. 0 calls booked, ever.` |
| Cold sequence stays at 3 | `# Phase 10 v1 said cut to 1 on a broken classifier. Touch 2 = 2/85 and produced Avneet and Rita.` |
| `--variant` required | `# Sources: 0 records. Depth: empty on 239/256. Optional fields die.` |
 
---
 
# 6. Execution notes for Claude Code
 
- **One PR per fix.** `uae-track` is the default base.
- **The gate tests are the regression net.** Do not change the row-dict contract and the storage in the same commit.
- **H5 has a real regression suite already:** Lisa, William, Ben and Rita are four labelled failures. Use them.
- **H1 and H2 are not Claude Code work.** They are live threads with a person on the other end.
- **Do not run the Airtable Wave 2 / cutover in this window.** Large, confounding, not on the critical path.
- **Do not move the price.**
- **Do not batch phases.** Each one gates the next for a reason: P1 without P0 quotes dead work, P2 without P1 ships better copy about wrong findings, P3 without P2 measures the old message, and P4 without P3 is unattributable.