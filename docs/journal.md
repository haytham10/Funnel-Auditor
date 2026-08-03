## 2026-08-03 (sourcing) — Instagram is a corpus, and the join that makes it one

Haytham, on the ig237 result: 2 emails for ~$53, so Instagram is not a good
source list, right?

**Right, and the numbers say something sharper than that.**

| batch | source | raw | shipped | per raw row |
|---|---|---|---|---|
| q1 | queue CSV | 20 | 5 | 25% |
| q2 | queue CSV | 20 | 9 | 45% |
| q3 | queue CSV | 34 | 13 | 38% |
| ig237 | IG dump | 237 | 2 | **0.8%** |

**But the machine's middle was the best it has been** — `hook_yield` 83% against
60-63%, `null_hook_rate` 17%, the cheapest cost per verified hook on record, and
every hook quoted from the ingested corpus held on a live re-fetch. D30 works.
The failure is sourcing, not retrieval, which is why D32 is about where lists
come from and changes nothing about `ig-intake`.

**The mechanism is reachability and it is structural:**

| | own a real domain |
|---|---|
| venues, gyms, clinics (not ICP) | 17 of 22 — 77% |
| solo coaches (the ICP) | 3 of 23 — **13%** |

On Instagram, owning a domain is **anti-correlated** with being our ICP. The
people we want use Instagram *instead of* having an email address, so
`email-find` has nothing to find and `email-enrich` no domain to guess at. A
machine that ends at a file of addresses cannot be fed from a channel whose
defining feature is not having one.

The `$53 / 2` figure is mostly not Instagram: fixed orchestrator cost over two
emails, in a session that also wrote eight commits of tooling.

### `corpus attach` — the join that was missing

`ig-intake` keys observations by the IG lead's `fetch.lead_key`, which is
`slug|site_url`, so the same coach on a queue CSV has a different key and the
corpus joins to nothing. `corpus attach` re-keys it: handle first, then name.

Verified on the real corpus re-keyed onto the same 23 coaches carrying different
sites — **23/23 matched by handle, 251 observations, all still schema-valid.**

**And its first live run had the bug it exists to prevent.** `handle_matches` is
any-token — right for the advisory note it was written for — so "fenton" in
"mariafenton" handed **Jack Fenton all of Maria Fenton's posts**. A stranger's
mailbox verified clean on this list last week; a stranger's *posts* are worse,
because they produce a hook that is verified, dated, quotable and about somebody
else, and every mechanical gate passes it. The join now requires **every** name
token, and two leads of the same name claiming one account attach nothing at
all.

### Reachability is knowable before spending, and only after the ICP filter

`intake` and `ig-intake` now print the own-domain rate, and `triage` prints it
**for the RUN tier with organisations excluded** — because the whole-dump rate
was 62% and the number that decided the batch was 13%. The two populations are
anti-correlated, so the raw-list rate does not merely have more noise, it points
the wrong way.

That needed a `person | organisation | unclear` label, which is the one
judgement I made by hand this batch. Instagram's own account category does it:
measured against a hand-labelled set, venue categories and role categories
separate 22 organisations from 16 people with one collision. `isBusinessAccount`
looks like the field for this and is worthless — true for 22 of 22 organisations
**and** 13 of 16 people. After tightening the personal-name fallback to exactly
two words with no brand noun, the label gets **16 of 16 people and 14 of 22
organisations with zero errors in either direction**; the rest are `unclear`,
which is the answer this module prefers everywhere else.

**It is a label and never a tier.** A gym clearing all three floors still runs.
Whether a marketing inbox is the wrong reader for "ten names for your buyer
profile" is Haytham's call at the preview.

`classify_site` also stopped calling `subscribepage.io` and `tejomaya.setmore.com`
a coach's own site. Hosted booking and landing pages are the same family as the
calendly entry that was already there, and they were inflating the one number
that predicts whether a list can be emailed.

### Still open

Unchanged from the previous entry: `select` has no substance test, and `deal`
can hand a lead an identity line naming that lead's own segment and city. Both
bite any source list. The ig237 corpus and shortlist are committed under
`data/runs/` so a substance signal can be scored rather than guessed.

## 2026-08-03 (the IG dump) — 237 profiles, 2 emails, and the four gaps it found

Haytham dropped an Apify `instagram-profile-scraper` dump of 237 UAE coaches and
asked to work it IG-native, filtering to the ICP before spending anything.

### The funnel

| | n |
|---|---|
| profiles in the dump | 237 |
| triage RUN / HOLD / DROP | 45 / 141 / 51 |
| individuals after the venues and brands came out | 23 |
| reachable, address verified | 6 |
| hooks verified (0 refuted) | 5 |
| **shipped** | **2** |

**Apify $0.1415 for the whole batch. Claude 55.7M tokens, $40.12 equivalent, 78%
orchestrator.** `tokens_per_email` is 27.8M against q3's 18.6M — worse, and the
honest reason is that two emails carry the same fixed cost as twenty. The batch
also shipped five commits of machinery, which the number does not separate out.

### The dump is a retrieval, not input (D30)

205 of 237 leads arrived carrying up to 12 posts each with verbatim captions,
real dates and post URLs — the material `plan`'s `ig_posts` rung pays Apify to
fetch. `ig-intake` reads it into Leads **and** `observe.Observation` records, so
the activity floor settles from a date instead of `unclear` (F3), `select` ranks
a real corpus, and no stage re-fetched Instagram to write a hook.

**Every one of the 5 hooks was quoted from that stored corpus and every one held
on the verifier's live re-fetch.** That was D30's stated exposure — a caption
edited or deleted since the scrape — and it did not bite on this batch.

### `unclear` is HOLD, and only a complete corpus may drop (D31)

Triage sorts on `qualify`'s own floors, called rather than re-implemented. 141
leads are HOLD: no location word, no coach word, no dated posts. None of them is
a kill and all keep their verdicts.

48 of the 51 drops are a stale activity date, which is the one place absence may
read as a `no` — and only with `--complete-corpus`, because `latestPosts` is
what the account HAS, not a sample of what a worker happened to fetch.
`activity_from_observations` keeps its upward-only rule untouched for everybody
else.

### Four gaps, all found by running the thing

**1. The address they published themselves.** `email-find` searches for what
somebody else published and its failure mode is a stranger's mailbox that
verifies clean. Two of the four addresses that survived corroboration here were
in bio text the dump already carried — `misosuphtarot@gmail.com` and
`hadimazlom6@gmail.com`, both PASS, neither findable by the SERP. `extract`
harvests the lead's own *pages* and this list has almost no sites, so nothing
would have found them. `--observations` now harvests first and skips the query
for any lead it finds.

**2. The hook verdicts were never merged.** The skill has said "merge them in
one step" since `hook-verifier` got `Write`, and `collect.py` never read a
verdict file. Every lead in a verified wave still said `hook_verified:
proposed`, which `metrics` reads as `hook_yield 0%` — a measurement, not a `?`,
which defeats the `?`-not-`0` rule from underneath. Now merged in code, joined
fail-closed, because placing a certification on the wrong lead ships a verified
hook about somebody else.

**3. A draft carried none of the lead's facts.** `export` wants an address and
got `KeyError: 'email'`; the skill's stage 5 assumed `drafts.json` already
carried them, true only while a human assembled it. `collect drafts --leads
--research` joins them explicitly and names every field it could not fill, which
is `crm-rows`' lesson.

**4. A working file matched the glob.** `draft-observations.json` collected 67
observations as drafts, all with slug `None`, every one of which would have
reached `export` as a row with no lead. A member with no slug is not a member.

### The SERP is not deterministic, measured on one lead

`ig73` searched 18 of these names this morning. **Coach Zee came back ABSENT
then and FOUND now** — `hello@thecoachzee.com`, hours apart, same query shape.
Tony Barrak moved ABSENT to CLAIMED. Kristina Duffkova reproduced exactly,
including her hard bounce.

So **caching address verdicts across batches would have cost a lead rather than
saved a search.** A prior ABSENT is a measurement of one SERP draw. Re-searching
an already-searched lead is cheap; skipping one is not.

### And there is nothing off Instagram

Haytham, on the three held drafts: explore other ways to get hooks, you have
Google search. Fair, and it had not been tried — every hook came from one
channel because the dump made it free.

Swept four leads across WebSearch, WebFetch, their own sites, podcasts, press
and LinkedIn. **Two new observations, both undated profile text.** Kayleigh
Green has no blog, no podcast, no press, and the LinkedIn of her name is a hotel
employee. A search snippet put Tony Barrak in a weekly qigong class at SEVA and
the live pages do not carry it, so the worker refused to cite it — correctly.

**These coaches have essentially no public footprint outside Instagram.** That
is the strongest argument for the ingest and it also means "search harder" has a
floor in this niche.

### The repair moved the failure across the seam, and then the material ran out

3 of 5 drafts came back REWRITE on the hook, so `redraft` issued one shared
correction instead of three private ones — its whole reason for existing. All
three repairs passed the linter, and **all three then failed the cold read on
the identity beat.**

That is the correction's fault, not the leads'. It said the hook must hand
forward into the identity line; three drafters did exactly that and the seam
broke on the other side of the joint. The one-repair cap held them, which is
right as a loop bound and was not written for the case where one instruction
fails three times rather than three leads failing twice.

**The next correction about a seam has to name both beats.** A hook and an
identity line are one joint and repairing one side of it moves the break.

**Haytham overrode the cap for one round and it failed too**, which is the more
useful result: it means the note was not the whole fault. Round 3 sent a
corrected seam instruction naming both beats, all three passed the linter, and
all three came back REWRITE. The cold reads finally named the real cause, and it
is upstream of drafting:

- **Coach Zee's** certified quote is a Friday gym-photo dump — "3 or 4 are my
  fav". *"Hands her post straight back with nothing the writer took from it… a
  pun about photos being asked to carry a pitch about clients."*
- **Tony Barrak's** is a relationship-theory line about the balance of intimacy.
  *"Nothing in beat 1 is about rooms, audiences, or people not showing up, so
  beat 2 reads as a slot advancing rather than a thought continuing."*

### `select` ranks quotable and has no test for substance

That is the finding worth keeping. `select` ranks on recency, kind, length and a
ban list, and **nothing asks whether an observation carries a claim a stranger
can take something from.** A photo dump and a mood post rank exactly like a coach
explaining how they work.

Kayleigh Green hit this honestly: her shortlist was thin enough to force a null
hook, which is a good answer. Zee and Tony hit the dishonest version — thin
enough to produce a hook that is **verifiable and empty**, which is worse,
because it passes `hook --against`, passes the independent live re-fetch, passes
the linter, and only fails in front of a reader. Three of six leads in this batch
reached the drafter with material that could not support an email, and the
machine had no way to say so before four agent passes had been spent on each.

A substance signal belongs in `select`, not in a drafter's instructions. It is
not written yet and it should be measured against this batch's committed corpus,
which `select --batch` kept for exactly this.

### An identity line can name the recipient's own segment

Maria Fenton's failure is separate and also structural. Her dealt identity line
is `id-fit-1`: *"7 meetings in a month for the last fitness coach in Dubai."*
**Maria is a fitness coach in Dubai**, so the proof points back at her and the
client it is meant to name disappears. Two drafters could not re-voice out of it,
because an anchor's claim is fixed and the collision IS the claim.

The 70/30 exact-match ratio causes this on purpose: a Fitness lead is meant to
draw a Fitness identity line. It only bites when the line names the segment *and*
the city the recipient is in. The fix is a line that says "the last one I worked
with" without restating the reference class, which is an Airtable edit, or a
check in `deal` that refuses a same-segment line whose text names that segment.

### Still open

- **`hook.py` cannot represent a null hook with its reason.** `quote` and `line`
  are unconditionally required, so Kayleigh Green's honest "nothing here is
  quotable" had to be written as an empty list, and the reason lives nowhere a
  later stage can read. `collect` now records `hook_verified: none` from the
  empty file, which is the status but not the why.
- **The three held drafts.** Verified hooks, no email, after three rounds. They
  keep their rows and their Blockers. Nothing about them gets fixed by a fourth
  attempt: two need better material and one needs a different identity line.
- `cta-04` opens on a question ("Worth 15 minutes?") and both `copy-check` and
  the drafter flagged it. That is an Airtable edit, not a draft fix.

## 2026-08-03 (the orchestrator share) — narration was 7%, and the rule chased it

Haytham: now go after the orchestrator share. It is 75% of the bill and the
last three entries kept deferring it.

**The diagnosis in `CLAUDE.md` was right about the total and wrong about the
target.** It said two-thirds of what is re-read each turn is the orchestrator's
own writing, which is true, and drew from it: never narrate per lead. Measured
on this session's own transcript:

| block | ~tokens | share |
|---|---|---|
| thinking | 76,841 | **34.3%** |
| tool_result | 68,676 | 30.6% |
| tool_use (the model's OWN calls) | 63,002 | 28.1% |
| text (prose to the operator) | 15,214 | **6.8%** |

Narration is the smallest of the four. A rule aimed at it is aimed at 7% of the
context, and the two blocks nobody was looking at are 62%.

`tool_use` being that large is the surprise worth naming: **a heredoc, a `Write`
payload or a long `python3 -` script sits in the context for the rest of the
run**, exactly like a tool result does. Writing a file is not a free action.

### `cache_read` is a sum, and that is the whole cost model

`cache_read` is the sum of the context over every turn. So it falls with a
smaller context *and* with fewer turns, and it rises **quadratically** when a run
gets longer and chattier at once. Halving per-turn output and halving turn count
are the same size of win, and they multiply.

This session: 230 requests, ~224K context, **53.0M tokens, $37.36** — and it ran
**zero subagents**. That is a pure orchestrator specimen, and it cost more than
q1, q2 and q3's entire Apify bills multiplied by twenty.

### What shipped

**`usage` now prints the block profile.** Characters rather than tokens, and it
says so — the transcript carries no per-block token count and a tokeniser here
would be a second estimate dressed as a measurement. Main thread only: a
subagent's context dies with it and is already reported per agent. A profile of
nothing prints no section rather than a row of zeroes, which is `metrics`' rule
about a count nobody supplied.

**`research-worker` writes its own slice and replies with one line.** The skill
used to say workers write nothing and then validate `work/research-<slice>.json`
— so the array came back through the orchestrator's context and was copied to
disk by hand, paying for it twice and leaving the run unresumable. A research
object carries verbatim observation text at roughly a thousand tokens per lead;
a slice of ten is ten thousand tokens held for **every remaining turn**.
`collect research` has always built `researched.json` from those files.

`hook-worker` gets the same treatment. `draft-worker` already had it and its
reasoning is the one both now quote.

**`CLAUDE.md`'s rule is rewritten** around the measurement instead of the
inference, and keeps the narration advice with its real weight attached.

### What is not fixed

Thinking is 34% and nothing here can shorten it directly — it falls with fewer
turns, or with a lower reasoning effort on mechanical stages, and neither is a
change this repo can make on its own behalf. The honest position is that the
measurement now exists, two of the four blocks have a mechanical fix, and the
largest one is a judgement call the next batch will have to test.

**No batch has run since any of this.** `metrics --written` reads
`tokens_per_email` out of the usage artifact and that is the control number.
Nothing here is proven until a real batch produces one to compare.

