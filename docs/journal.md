## 2026-08-02 (token forensics) — the orchestrator was 75% of the bill

Haytham: usage on the last two runs is not normal and I cannot track what is
going on. He was right, and nothing in this repo could have told him why.

`ledger pass` records that an agent ran. It cannot record what the agent cost —
neither an orchestrator nor a worker can see its own token usage — so the model
side had a count and no magnitude. q2 reported 99 passes and q3 reported 185.
Both numbers were accurate. Neither was the answer.

### What the transcripts said

Ran a forensics prompt in both sessions against their own transcript JSONL,
which carries `message.usage` per request and a separate file per subagent.

| | q2 | q3 | both |
|---|---|---|---|
| cost | $172.88 | $181.82 | **$354.70** |
| tokens | 227.9M | 182.4M | **410.3M** |
| shipped | 9 | 13 | 22 |
| per email | | | **$16.12 / 18.7M tokens** |
| orchestrator | 77.6% | 72.8% | **75.1%** |

**410 million tokens to ship 22 emails of about 120 words.** And three quarters
of it was the main thread, which reports no passes at all because nobody records
one for the loop they are typing in. Main-thread cache read plus write alone was
70% of everything — pure coordination.

The mechanism: one session runs the whole pipeline for 10+ hours, context reaches
578k-684k tokens, nothing compacts until after the work is done, every one of
~390 turns re-reads all of it. q2's report put it exactly: of its 577,797-token
final-quarter context, ~381k was **its own writing**. *"Two-thirds of what the
batch paid to re-read was my own writing."*

### Two hypotheses I had before the numbers, both wrong

I went in expecting whole-file reads to be the cost — `hook-worker` pointed at
`work/select.json` (73 KB), `research-worker` at `work/sites.json`. Measured:
`hook-worker` read select.json 4 times in q3 and 0 in q2 (it reaches the
shortlist through `hook --against` instead), and `research-worker` read
sites.json 0 times in both. Worth nothing. That is what the measurement was for,
and it is the reason the instrumentation shipped first.

The other tempting fix was the opus pin on the draft stage. Priced: the whole
draft stage is 14-18% of a batch and the sonnet swap saves $13-15. Model tier is
**not** where the money is, and trading the cold read — which caught 11 of 12
identity beats the linter passed — for 6% of a batch is a bad trade. Untouched.

### What was actually wrong, in the order it cost

**The verifiers could not write.** `draft-verifier` and `hook-verifier` had
`Read, Bash, Grep` and no `Write`, so a SEND/REWRITE/REJECT existed only in the
orchestrator's transcript. This file said so: *"the verdict lives in an agent,
nothing in Python can reach it."* `REWRITE` appeared in zero Python. A verdict
only one context can read is a verdict only that context can route — which is
why every one arrived on its own turn, and why `SKILL.md` telling us to *"pipeline
these, do not wait for all the workers"* was the single most expensive line in
the file. Twenty leads pipelined is eighty turns at full context.

**Three state files were assembled by hand.** `researched.json`,
`draftable.json`, `drafts.json` — no command produced any of them. Serialised out
of a 600k context and read back into it. Also why no stage here was resumable.

**The redraft cap was a sentence.** Eight of nine leads exceeded it on q2 (one at
five rounds), eight on q3 (three at three). Repeats were 68% and 46% of those
draft stages. A long session talks itself past a sentence one reasonable
exception at a time.

**Seventeen identical findings, answered seventeen times.** Every q3 draft failed
its first cold read on the same beat. The redraft prompts carried 1.6x the text
of all seventeen original briefs. This entry's predecessor already diagnosed it —
*"I answered the first finding per-lead, and the second, and the third, before
treating the repetition as the signal it was"* — and what it did not say is that
nobody could have done better: a reader going lead by lead cannot see the
seventeenth until they have paid for sixteen. **Counting is the fix, not
discipline.**

**`apify` printed its whole dataset to stdout.** The only command here that did;
every other bulk stage writes a file and prints a summary. q2 had three Instagram
runs producing 914,685 bytes of tool-result, ~305 KB each where a trimmed result
is 20-30 KB, and its forensics could not attribute them at all. Two causes:
`--raw` bypasses trimming, and `_lean` did not recurse, so `latestPosts` and
`author` came through carrying every blob `_NOISE_KEYS` exists to drop.

### What shipped

- **`usage`** — reads the session's transcripts, writes
  `data/runs/<batch>-usage.json`, `metrics` prints it as MEASURED beside the
  REPORTED passes. Deduped on `requestId` keeping the last record: counting
  records inflates requests 2-4x, keeping the first undercounts output ~4x, and
  one forensics run published a wrong total before catching that. **Tokens, not
  dollars** — `record_pass` refuses a rate table because prices go stale, which
  is right and is about prices; a token count is a measurement this repo owns.
  **Run it before the session ends**: transcripts die with the container.
- **`apify --out`** by default, `_lean` recurses, and `research` / `ledger
  report` stopped printing per-lead and per-duplicate dumps (14,202 → 2,316
  bytes; 15,905 → 1,474). `ledger report` groups duplicates by shape now, and q3's
  dominant shape is the first line rather than an inference.
- **`verdict`, `redraft`, `collect`**, and `Write` for the three agents that
  lacked it. The cap is a loop bound. A beat that two or more of a wave fail on
  produces **one** shared correction naming the leads.
- **`SKILL.md`**: waves fan out in one message, a wave is six leads (it was used
  as a tripwire boundary twice and never defined), and the cost section carries
  the measured number instead of an assertion.

### The number to beat

`tokens_per_email`. q3 measured 14.0M. If the next batch does not halve it the
model was wrong and this gets re-cut against the measurement rather than
defended. Quality control on the same batch is the cold-read REWRITE rate and
the count of leads held — if capping the loop or clustering the findings ships
worse emails, those two say so before the preview does.

None of this traded away a check. The money was never in the work.

## 2026-08-02 (batch q3) — 13 of 34, and the drafting stage failed 17 of 17 first reads

Haytham dropped two queue files (20 + 14) and said run it. Ran as one batch so
the copy weights had something to balance across.

**Shape: 34 raw, 28 draftable, 17 verified hooks, 13 shipped.**

Six leads never reached drafting and every one is list quality: three fail
`uae_based` on LinkedIn's own location field (Stevie Pages UK, Erika McDonnell
US, Rahat Shigri Islamabad), one fails `is_coach`, two have no deliverable
address. All six arrived carrying a company website that was not the lead's own,
true of about a third of this list.

**Retrieval was the strong half**: 61 observations over 34 leads, 24 dated,
against q2's 42 of which 26 were About pages. `hook_yield` 61%, `refute_rate`
0%, `escalation_rate` 0% — the D27 flip held completely, no hook worker had to
escalate off its shortlist.

### The finding: one missing section, repeated seventeen times

**Every draft failed its first cold read. 17 of 17.** The verifier findings
repeat almost word for word, which is what makes this a stage problem:

1. the hook's connecting clause **comments on the quote instead of taking
   something from it** — "That question lands.", "Full rebuild.", "an unusual
   combination.", "Same eye, new room."
2. the identity beat arrives as **the copy line with a `your` bolted on**, often
   verbless — "About AED 400k in signed business", "30 signed this year, across
   8 practices".

I made this far more expensive than it needed to be. I answered the first
finding per-lead, and the second, and the third, and wrote seventeen individual
rewrite notes before treating the repetition as the signal it was. **91 of the
first round's 137 agent passes were drafting.**

`.claude/agents/draft-worker.md` described the connecting clause as the
drafter's freedom and **never said what it must do**. The identity-beat section
already existed, written after 2026-08-01, and its failures recurred anyway —
so it now says so, and names the specific recurrence: buying hook room by
deleting "I worked with", the phrase that puts a person behind the number.

**The correction is measurable.** The 11 held leads were redrafted against the
corrected file with the same hooks and the same dealt lines. **Nine were
recovered**, most on the first attempt. Govind Abkari had failed two cold reads;
the third came back "I would put my name on this going to a stranger." Dalia
Hosny had failed twice on a clause that admired her without taking anything from
the fact; the replacement — "Nobody ahead of you to ask how, so I'll skip the
advice" — came back with an empty problems list.

### The four that held, and why each is different

- **Amjad Saijary** — withdrawn by his own drafter, and the best outcome here.
  The post his hook cites says he open-sourced the project "not to sell it", so
  any bridge naming buyers contradicts the source on the same screen. He also
  has no evidenced buyer profile: salaried at an academy that holds the
  enrolment relationship, `sells_to` empty, own domain unreachable.
- **Amanda Slade** — not a drafting failure. `id-life-2` claims
  `Life:first_client_days` and she is a master coach with high-net-worth
  clients. Drop "first" and the speed claim evaporates ("week 1 of what, a
  client out of how many"); keep it and it reads as beginner advice. Two
  verifiers reached that independently. **`deal` balances declared weights and
  has no notion of career stage**, so this recurs until the Life segment has a
  line whose proof is not a first client.
- **David Singleton** — two mechanical words. Three attempts failed on the same
  collision: the certified fragment contains his own "I call", so every
  placement made the reader resolve two speakers. Quoting only "Leadership
  Architecture", a contiguous sub-span, dissolved it. What remains is "in this
  city" where Dubai belongs.
- **Solene Anglaret** — the hardest seam, flagged as such before drafting began.
  Also the one I got wrong: I relayed one verifier's suggested turn ("still
  paying to be the student") as settled guidance, and a different cold reader
  called it a dig at her status and money. That read is right. **A verifier's
  aside is not a spec, and passing one on as though it were is how a suggestion
  becomes a defect nobody owns.**

### hook_room is stale, and four drafters said so independently

David 20 vs 47, Stephan 16 vs 41, Anita 18 vs 41, Chris 17 vs 37 — roughly half
the real authored budget in every case. Drafters were cutting "I worked with"
and "here" out of identity beats to buy room they already had, and several
first-round failures trace directly to it. The previous commit before this
session was `deal: hook_room is a floor, not a projection`, so either that fix
does not reach the field the batch skill hands to workers, or it needs to reach
the drafters differently. **Not fixed here; it needs its own change and its own
test.**

### Three code faults, all found by running

**`crawl_render` has never worked.** Chromium at 1024 MB was SIGKILLed (exit
137) before its first page on every run. Every browser render this machine has
ever planned bought a container boot and returned nothing. Now 4096. Behind it:
the sync timeout was sized for cheerio, so a 10-URL browser batch rendered 5
pages and TIMED-OUT, discarding them; and a failed run returned nothing at all,
so those paid pages were thrown away and the retry bought them again.

**`_run_escalations` exited from inside its loop**, discarding every plan that
had already succeeded. The static crawl returned 12 pages three times and was
discarded three times.

**`crm-rows` joined email-first on both sides.** A research object's email is
not the Lead's — research re-checks it. Two of 34 failed to join and reported as
the missing-identity defect. `FAIL (2) — 32 rows` became `PASS — 34 rows`.

I also caused the duplicate I had just fixed the code to prevent: the first
escalation failure was retried with `fetch --escalate` instead of
`--escalate-only`. 110 of this batch's 129 duplicate pairs are that. Left in the
ledger; a batch is not entitled to a flattering measurement of itself.

### One deviation that touched the deal

`cta-02` hit 38% against the 35% cap once four leads held. `--rebalance-ps` only
moves the ps, by design — the ps sits alone at the end, the close is part of the
seam. Rather than drop a cold-read-passed email I reallocated **Sam Eid's cta to
`cta-03` by hand in `anchors.json`** and had him re-read cold with the new close
(SEND, no problems). A single-beat edit, not a re-deal: no identity line moved,
no email was re-drafted. Recorded because it was done by hand and should not
become a habit.

### Cost

$0.698 real Apify ($11.87 to $12.57), $0.0224/lead over 34. 377 retrievals, 129
duplicates. **185 agent passes** (draft 139, hook 41, research 5), opus 139 /
sonnet 46 — and the drafting share is the number to attack next time.

Not yet uploaded, so `wall-add` and `copy-usage` have NOT been run.

## 2026-08-02 (fixes) — the three things `2026-08-02-q2` found, and the one I did not fix

Haytham: fix the hook_room calculation in deal, make sure everything is fixed
based on this run.

### 1. `hook_room` was a projection sold as a budget

`Deal.hook_room()` measured the room against the **reference** identity line.
The drafter authors that sentence, so the figure was only true if the beat came
out exactly reference length — and drafters write to the top of a range.

Measured on the batch: every lead wrote at or above the reference. Sabine was
told 18 and had 16. John was told 32 and had 22. **Three different drafters
independently recomputed it and told me the instruction was wrong**, and they
were right every time; I then relayed the correction wrong twice more, once by
costing a 6-word quote as 7 and once by forgetting the 3-word citation frame is
not part of the quote.

What shipped:

- **`Deal.authored_budget()`** — the words hook and identity share. The only
  length figure true at deal time, because it depends on nothing the drafter has
  written.
- **`Deal.hook_room()`** now returns the **floor**: the budget less the top of
  `identity_budget()`. It holds however the beat is written, and a drafter who
  writes short finds room it did not expect, which is the harmless direction.
- **`_resolve_length` repairs against the same floor.** A promise the allocator
  does not honour is not a promise. This tightened the guard by `IDENTITY_SLACK`
  and the live bank still satisfies it — the extreme combination now escalates
  from a ps swap to ps-plus-cta, which is the documented order, not a defect.
- The prompt block hands over **both** numbers and says which is exact.

One thing recorded so nobody irons it out: **subtracting a separately-counted
identity from the budget is close, not exact.** `word_count` runs on the
assembled body — which is why `lint.hook_room` measures the body rather than
summing lines — and the joins are worth a word or two. One shipped email came
in a word over its derived budget and still landed at 94 of 95. The budget is a
guide; `WORD_MAX` is the enforcement, and the floor absorbs the difference.

### 2. The `b4-01` + `ps-05` echo, and the guard that was hiding it

A cold read named the pair rather than the wording: *"b4-01 and ps-05 should not
be dealt to the same lead."* `_ECHO_PHRASES` had no pattern for it, so
`echo_pairs()` reported none and the deal could pair them freely.

I tried this once mid-batch and reverted it, because adding the phrase made a
test fail that asserts the live bank has **no** colliding pair — and that test's
history shows the repo's answer to a collision is to rewrite the copy, which
lives in Airtable and is not mine to edit.

The resolution is an allowlist. `KNOWN_ECHO_PAIRS` records the one real
collision with its evidence; anything else still fails the build. The value of
the original assertion was that a new collision cannot arrive unnoticed, and
that survives. `deal` now prints the pair on every run, and a second test proves
the two are never dealt together, so **the emails stay clean while the copy is
wrong**. The fix is still three cells in Copy Assets.

### 3. The one I did not fix, and why

`qualify` returned `yes` on `uae_based` for Trudy Rowe off an incidental
**"Dubai Evening News"** mention — on a page that was not even hers.
`check_uae`'s bare marker scan matches any word-bounded city name anywhere in
the text, and the module already carries scars from exactly this family
(`aeon.co`, `Marina Bay`, `michae.com`).

I left it, on the repo's own asymmetry: **a false pass costs one research call
and a false kill is permanent and invisible.** Every fix I could construct —
capitalised-compound detection, a publications list, downgrading the bare scan
to `unclear` — trades a cheap error for the expensive one or needs an unbounded
list. "Dubai Knowledge Park" is a real place and "Dubai Evening News" is not,
and no rule I can write separates them reliably.

The sharper version of the finding is not about substrings at all: **the text
came from a page `resolve` had already flagged as not the lead's.** Feeding
owner-check-failed pages to the floors is the real defect, and it is a
qualify/resolve integration decision rather than a quiet patch. Left for a
decision, not smuggled in as a fix.

### Checked and not a bug

Jodie drew `id-lead-2` (`coach_type: Leadership, sells_to: any`) while selling
to corporates, with `id-lead-4` (Leadership + corporates) available. `any` means
fits either audience by design, and the 70/30 ratio draws a non-exact line by
design. Working as intended.

`crm-rows` printing `Body 0/19` was my process error, not a code defect — I had
stripped `body` so `export` would reassemble it after the ps rebalance. The
coverage block is the only reason it was visible, which is what it is for.

969 tests, `doc-check` clean.

## 2026-08-02 (final) — 9 of 20, and two rules that cost more than they protected

Haytham, after the 7-lead file: **fix john and fatima too, i want all 9.** Both
had verified hooks and were held at the draft stage on known, small faults. I
had held them on the skill's one-rewrite rule. He overrode it; that is his call,
and both shipped after a fresh cold read found nothing wrong.

Recording it because the rule is not wrong, but **it is a drafting-quality rule
being applied to leads whose defect was a single sentence.** John needed three
words cut. Fatima needed "the ones who taught you" opened to "among your
teachers", because her page says "name few but not limited to" and the closed
set wrote out the teacher she foregrounds. Worth considering whether the rule
should count *rounds where the finding was new* rather than rounds.

Fatima is also the case against my own reasoning earlier in the day. I let her
have one repair because the damage was mine — my re-deal cost her seven words of
hook room. That repair then surfaced a third, deeper fault. So "the damage was
mine" was a fair reason to allow the round and **not** evidence the email was
one round from done.

### Adding two leads cost two re-deals, and both were cheap

Seven holds left `b4-02` at 38% and `cta-03` at 50% against a 35% cap, and
`export` blocked the file. Correctly. Re-dealt for 8; then adding John and
Fatima meant re-dealing for 9.

**The skill's warning that re-dealing forces a re-draft of everything is
overstated.** Both times only ONE identity line moved — identity is the beat
woven into the seam and the only one that forces a rebuild. Everything else was
library copy needing a re-voice. The 9-lead deal touched 3 of 9 drafts.

### The hook_room defect, caught three times by three different drafters

`deal` prints `hook_room` computed against the **19-word reference identity
line**. A drafter who writes a longer identity beat eats the difference, and
nothing tells them. Measured this batch:

    Sabine   printed 18   real 16   (identity 27)
    John     printed 32   real 22   (identity 25)
    Fatima   printed 24   real 21   (identity 22)

Three drafters independently computed the real number and told me my instruction
was wrong. They were right every time. **The honest number is what is left of
the 95-word ceiling once the greeting, sign-off and the four dealt lines are
assembled with an empty hook.** That is a `deal` fix, not something orchestrators
should keep rediscovering — and I got it wrong twice more even after being told,
once by costing a 6-word quote as 7 and once by forgetting the 3-word citation
frame is not part of the quote.

### What the drafters got right that I did not ask for

Sabine's worker refused both cuts I offered and showed the arithmetic instead.
Jodie's worker reversed its own earlier decision on a repeated word and said so
plainly: *"I was wrong about it then rather than that the instruction changed."*
John's worker removed an aside with nothing in its place rather than replacing
it. None of that was instructed.

### Final

9 written of 20 raw. hook_yield 60%, refute 7%, null 33%, escalation 0%.
$0.3637 over 171 retrievals. Every beat inside the 35% cap at 9 leads.

Still open, both for Airtable rather than code: **`b4-01` + `ps-05` collide** and
should never be dealt together, and **Jodie drew a `sells_to: any` identity line
while selling to corporates** when corporate-specific lines exist.

## 2026-08-02 (re-run) — the same 20 leads, 3 emails to 7, on one gate change

Haytham: re-run the batch with the fixed gate. Same research corpus, no fresh
crawl — the change was `hook` accepting an empty `published_at` from a source
that genuinely has none (D29).

**hook_yield 20% -> 60%.** Nine verified hooks of fifteen attempted, against
three. Six leads that had produced nothing now had a hook, and **not one of them
needed new retrieval** — the material was already on disk and the gate had been
refusing it.

**The five nulls that stayed null are the better evidence.** Danyal, Sofie,
Ahmed, Sharon and Yaser all came back empty again, every one of them on ban #1
or on authorship, never on the date. Sofie's worker quoted her entire About
section to show it was mission-statement copy end to end. Yaser's applied the
test it was given — *does this sentence have Yaser in it, or the club in it* —
and found both candidates were the gym describing itself, the same voice that
refuted him the first time. Ahmed's is a profile card with no About paragraph
behind it, researched twice and empty twice. The fix removed the date as a
reason to reject and left every quality ban standing, which is exactly what it
was supposed to do.

**`escalation_rate` stayed 0%.** No verified hook needed a paid escalation.

### The drafting stage is where this batch actually got expensive

**Nine first drafts, nine linter passes, nine REWRITEs from the cold read.** Not
one survived a human-equivalent read on the first attempt. Recurring shapes,
worth naming because they will recur:

- **Flattery routed through unnamed peers.** Three drafters independently wrote
  "Most coaches can't/never…". A verifier drew the line precisely: John's
  survived because it points at *an observable decision he made*; Geeta's and
  Fatima's failed because they point at *other coaches' ignorance*. Fatima's was
  also false — her own page names Tony Robbins' teams two paragraphs above.
- **Telling the recipient what their own work is for.** Toleen's first draft said
  her lecture hall was full of people who cannot pay her. "The seam works and
  what it delivers is a verdict on her teaching."
- **Discovery frames** — "Your profile says", "Noticed you also teach". Three.
- **The sharpest catch, and unlintable:** John's identity beat read "Finding you
  more of them is my job", where the nearest antecedent to "them" was
  **Filipinos** — read by a man who very likely belongs to that group. Plus a
  lowercased demonym in his subject, where the batch's house style of
  lowercasing proper nouns collides with a word that is not a brand name.

### Two leads held with verified hooks, and I let them

**John** came back REWRITE a second time over a three-word aside ("capitals and
all", which concedes a blemish before the compliment). The skill says back to
the drafter **once**, then it passes or it holds. I had told the verifier in
advance that it was the final pass. Inventing an exception after seeing the
verdict is how a rule stops meaning anything, so he held.

**Fatima** is the more interesting one. She passed, then my re-deal cost her
seven words of hook room, the compression left a pronoun with no antecedent, and
the repair surfaced a *third* fault: "the ones who taught you" closes a set her
own page leaves open ("name few but not limited to"). I allowed one repair
because the damage was mine, not hers — but four rounds each finding something
new says the material is thin, not the wording unlucky. Both are small known
fixes and should lead the next batch at near-zero cost.

### The re-deal, and why `--rebalance-ps` was not enough

Seven of fifteen held, so the deal made for fifteen left `b4-02` at 38% and
`cta-03` at 50% against a 35% cap, and `export` **blocked the whole file**.
Correctly. `--rebalance-ps` only moves the ps, which is the one beat with no part
in the seam.

Re-dealing across the shipping set lands every beat at 25%. The cost was smaller
than the skill's warning implies: **only one lead's identity line moved**, and
identity is the beat woven into the seam. The rest were library copy, so five
leads needed a targeted re-voice and one needed a genuine rebuild.

Worth recording for next time: `deal`'s `hook_room` is a projection off the
**reference** identity length. A drafter who writes a longer identity beat eats
the difference, so the real room can be several words tighter than the anchors
file says. Fatima's drafter caught this and was right; my number was stale.

### Two findings I could not act on inside the rules

- **`b4-01` and `ps-05` collide** — "…before writing this" and "I read your work
  before I wrote this one", same construction two sentences apart. A cold read
  named it as an anchor-pairing fault. I added the phrase to `_ECHO_PHRASES`, it
  worked, and it made `echo_pairs()` report a live pair — which fails a test
  asserting the live bank has none. That test's history shows the repo's answer
  to a collision is to **rewrite the copy in Airtable**, which is not mine to
  edit. Reverted. **It is a three-cell fix in Copy Assets.**
- **Jodie drew a `sells_to: any` identity line while selling to corporates**,
  with corporate-specific lines available. An allocation question for the 70/30
  exact-match ratio, not a draft defect.

### Numbers

7 written of 20 raw. hook_yield 60%, refute_rate 7%, null 33%, escalation 0%,
declined_and_dry 1 of 2. $0.3637 over 171 retrievals, $0.0404 per verified hook.
**91 agent passes: draft 49, hook 38, research 4** — the draft stage cost more
than everything else combined, which is what nine unanimous REWRITEs buy.

`crm-rows` caught me shipping `Body 0/19` — I had stripped `body` so `export`
would reassemble it after the rebalance, and the CRM would have recorded seven
emails with no text. The coverage block is the only reason that was visible.

## 2026-08-02 (D29) — the date comes from the source, and I fixed the wrong end first

Haytham, after the `2026-08-02-q2` brief: fix the gate so About pages are not
shortlisted. Then, on seeing what I did: *About pages are a valid hook, but only
if we can't find any recent or good posts on social media.*

He was right and my first attempt was wrong, so both are recorded.

**What I did first, and why it was wrong.** I banned `kind == "about"` in
`select` outright and emptied `EVERGREEN_KINDS`. It looked well-evidenced —
re-scoring the corpus dropped candidate-carrying leads 14 → 4 with `0 missed`
against the verified hooks, so the shipped file would have been identical. But
"costs nothing measurable" is not the same as "is right". It deleted a real
fallback to remove a symptom, and the ranker was never the thing misbehaving:
`KIND_RANK` already put `about` last, so a lead only ever saw one when nothing
recent survived. That is exactly the behaviour Haytham described wanting.

**The actual defect was one stage later.** `outbound/hook.py` required a
non-empty `published_at` from *every* proposal. `select` legitimately offers
undated evergreen sources. So a worker handed a legitimate About page had two
moves: abandon the hook, or invent the date. **Two workers invented it** — same
batch, different leads, one citing the other's file as precedent — and since the
only date rule was "not in the future", a stand-in of today passed everything.

An impossible instruction gets resolved dishonestly. That is a gate defect, not
a worker defect, and the fix is to stop asking for the impossible.

**What shipped instead.** `hook.check_date` now takes the date from the cited
observation:

- source has a date → the proposal must carry the same one (a disagreement is
  now caught too, which it was not before)
- source has none → `published_at` must be **empty**, and a non-empty one is
  rejected as fabricated, because there was nowhere to read it from
- nothing joinable (no `--against`, or an escalation) → the old rule stands,
  since an unjoinable "the page had no date" cannot be told apart from not
  having looked

Replayed against the batch's own corpus, both withdrawn proposals are rejected
with `carries no date at all`, and both are accepted the moment their date is
empty. **The fabrication became mechanically detectable in the same change that
made it unnecessary.**

One subtlety worth keeping: a **missing** `published_at` key is unknown, not
undated. `resolve.py`'s rule — "`unknown` never means the tell said no" — one
stage over. A thin record must never convict a worker of inventing a date.
`select` always writes the field, so real batches take the strict branch; a
minimal test fixture caught this and it would have been a nasty false positive.

**Everything in `select` is back where it was**: `EVERGREEN_KINDS = ("framework",
"about")`, `about` ranked last, no `about_page` ban. The tests that briefly
encoded the ban were reverted rather than left as dead history, and the module
docstring now carries the half-day round trip so the next person does not
re-derive the same wrong fix from the same real evidence.

**The retrieval half stands on its own merits.** `research-worker` gained a
section saying an About page is the *fallback* and naming where dated material
actually is — LinkedIn posts, Instagram `--mode posts` (real timestamps),
podcast and interview pages, their own `/blog` and `/press`, and a plain
WebSearch on name plus "interview", "panel", "launched", "award". Free,
unlimited, least used. `outbound-batch` now says to look at what the shortlists
are *made of*, not just how many exist, and to push a slice back to research
before spending ten hook-worker passes on leads whose only material is an About
page. On this batch that was 26 of 42 observations and 10 of 14 leads.

966 tests, `doc-check` clean. D29 rewritten to describe the gate change.

## 2026-08-02 (batch 2026-08-02-q2) — the hook gate cannot accept the evidence the machine collects

20 raw UAE coaches in, 3 emails out. The yield is the story, and it is not a
drafting problem or a hook-worker problem. **It is a contradiction between three
modules that nobody had hit hard enough to see.**

- `plan` offers an `about` rung and describes it as potentially strong: "the
  hero section is generic, the founding story is not."
- `select` ranks `about` observations into shortlists. This batch: **26 of 42
  observations were `about` kind.**
- `hook` hard-requires `published_at` ("a post with no date cannot be shown to
  be recent"), and **no About page ever carries one.** Measured here: of 42
  observations, the only dated ones were the 12 `post`-kind. `about` scored
  0/26.

So research retrieves About-page material, the ranker shortlists it, and the
gate structurally cannot accept it. **10 of the 14 leads with a shortlist had no
dated candidate at all** and were unreachable the moment research finished.

### The part that matters most: the gate was producing the fabrication it exists to stop

Two hook workers, independently, on different leads, invented a stand-in
`published_at` of today for an undated page. **One of them cited the other's
file as precedent.** The gate only rejects dates in the *future*, so today
sails through.

Both were withdrawn before export and both leads re-picked or nulled. But the
pressure is structural, not a worker defect: faced with an undated source, a
worker's only options are to invent a date or abandon the hook, and nothing in
the gate's wording says which. **Assume this pattern exists in earlier batches
and check `Hook Date` against the cited page before trusting it.**

Suggested fix, not made here because it is a design call: either `select` stops
shortlisting undated kinds, or `hook` states plainly that an undated page is not
an eligible source. Right now the rule is enforced by a check whose message
sounds like a field-formatting complaint.

### What was NOT wrong

**`refute_rate` on quote accuracy was 0.** Every quote a research worker stored
was really on the page when a verifier re-fetched it live. Retrieval quality was
not the constraint; availability was.

The single refute was **authorship, not text**: Yaser Jeish's quote was verbatim
and correctly dated, but published by the gym's account in organisational "we"
voice signed "Abu Dhabi Muay Thai Team / ADMT", and the club's own page lists
seven coaches. The verifier traced the account through `identity.json` and the
coaches page rather than taking `author: self` on trust. That is the check
earning its cost.

**The cold reads earned theirs too.** All three drafts passed the mechanical
linter and all three came back REWRITE:

- a clause that flattered a non-distinction (telling a Hogan practitioner that
  naming Hogan is "rarer" — it is table stakes and she knows it)
- a semicolon, in the second sentence, in a register built on periods
- "**Another** leadership coach in Dubai" — quietly enrolling the recipient in a
  client list she was never in
- a clause that graded an ICF PCC / ORSCC on whether she spoke from experience
- a retained `@berlinmarathon` handle inside a quoted Instagram caption, which
  the reader called the exact detail that tips an email from noticing to being
  watched

None of those are lintable. All three passed on the second pass.

### A real bug, found and fixed: `--rebalance-ps` never reached the body

`export` prefers a `body` the drafter pre-assembled over rebuilding from
`beats`. `--rebalance-ps` writes the new ps into `beats` only. So a rebalanced
lead shipped the **old** ps sentence while `anchor_ids`, `line-usage.csv` and
the CRM row all named the **new** one.

`--anchors` cannot catch it: that check compares `beats` against the deal, and
`beats` is the half the allocator moved. Every gate passed and the file was
still wrong — the "CRM row describing an email nobody received" failure the
anchors check exists to stop, arriving from the allocator instead of a drafter.

Caught here because 12 of 15 held, so the rebalance moved 2 of 3 ps lines and
the mismatch was visible in a 3-line preview. On a 40-lead batch moving 2 lines
it would have been invisible. Fixed in `main.py`; regression test in
`tests/test_export.py` fails without the fix.

### The list itself

**Three of twenty rows carried a `companyWebsite` belonging to somebody else** —
Max Mears's domain serves an unrelated tutor in New Jersey, Trudy Rowe's is a
Vancouver company she merely licenses a program from, John Allego's is a
templated AU agency site with Lorem ipsum still in it. `intake` profiled all 20
as "live site". A 200 is not evidence the site is theirs; `resolve`'s owner-check
is the thing that knows, and it flagged 4.

All three UAE kills were sound and all three rested on a first-person current-role
statement: Kuala Lumpur, Panama, and a dated French post saying "je rentre en
France". No kill rested on a site.

**One gate weakness worth naming:** `qualify` returned `yes` on UAE for Trudy
Rowe off an incidental "Dubai Evening News" mention on a third party's page. A
substring match on a news-outlet name drove a floor verdict. The worker
overrode it correctly, but the mechanism is a false-pass generator.

**Sharon Holmes is the near-miss to learn from.** A worker set `is_coach: no`
because her LinkedIn is a cruise-tourism consultancy with no mention of
coaching. Her actual site returned **zero text** — not thin, empty. Killing a
lead on "her other business is X" when her coaching site never loaded is exactly
the false kill the asymmetry exists to prevent. Corrected to `unclear`, which
passes. The LinkedIn-wins rule is scoped to `coach_type`; it was never a rule
for settling a floor against an unread primary source.

### Numbers

hook_yield 20%, null_hook_rate 73%, refute_rate 7%, **escalation_rate 0%** (no
verified hook needed an escalation), declined_and_dry 1 of 2. $0.3437 over 160
retrievals, $0.0181/lead. 37 agent passes: hook 21, draft 12, research 4.

**16 duplicate (lead, url) pairs, and 10 of them are one structural pattern:**
`li_profile` then `li_posts` against the same profile URL. Two different actors
legitimately hitting one URL — the ledger keys on (lead, url) and cannot tell
that apart from a wasteful re-fetch. Worth either keying on (lead, url, actor)
or naming the pair as expected, before somebody "optimises" it away.

### Toleen is the counter-example to the whole yield story

She has genuinely quotable dated material — a Bloomberg Asharq TV interview and
a dated LinkedIn post — and **the ranker excluded both**, one as `stale` and one
as `too_short`, leaving her shortlist entirely undated About text. Her null is a
ban artefact, not an evidence problem. If the undated-source contradiction gets
fixed, check the bans next.

## 2026-08-02 (pre-flight) — the write-back nobody was told to do

Haytham, before running the first real batch since the flip: walk the whole
codebase, find the orphans, confirm the safeguards, **we produce a list of 2
today**. Nothing had been put to work all week.

`doc-check` and 951 tests were green on arrival and stayed green. The gates that
had tests were fine. What was not fine was a join between two stages that no
test and no gate looked at, because it runs through a human.

**`crm-rows` and `metrics` read the hook verdict off the research object and
nowhere else.** Not off the drafts, which carry `hook_type`, `hook_source_url`
and `hook_quote` on every row. Those fields reach the research object only when
the orchestrator writes them back at stage 3b, by hand, because the verdict
lives in an agent and Python cannot see it. The skill told you to write back two
things: the hook's **date** and its **observation_id**. It never mentioned
`hook_verified`, `hook_type` or `hook_source_url`.

Skip that step and nothing errors, which is the whole problem. A research worker
returns `hook_verified: "proposed"` — a legal value that reads like an answer —
so the numbers get **computed** rather than skipped. Reproduced end to end on a
2-lead run that shipped 2 verified hooks and 2 emails:

    hook_yield        0%    (0 verified of 2 attempted)
    null_hook_rate    100%  (2 found nothing)
    Hooks Verified    0
    escalation_rate   0%    ← D27's number, on the batch run to produce it

Every one of those is a measurement, not a `?`. **This is the `?`-not-`0` rule
defeated from underneath**: the rule protects a count nobody supplied, and this
count *was* supplied, from a field nobody was told to update. `Hooks Verified 0`
goes into Airtable and gets believed, and `Hook Type` lands empty — the field
`replies` exists to join on, per the skill's own line about it.

Three fixes, in the order they catch it:

1. **The skill.** Stage 3b now names all six fields in a table with who reads
   each one, and says the step is a step. That is the actual fix; the other two
   are for when somebody misses it anyway.
2. **`crm-rows` exits 1** on any row that is `Exported` with `Hook Verified`
   not `verified`. An exported email has a verified hook by construction — a
   refuted one is not drafted — so this is mechanical, and it is the same join
   this module was written for, one field over and quieter.
3. **`metrics` prints `SUSPECT`** when `--written` is above zero and no hook
   reads as verified, naming the fields to put back. Fail-open, never exit 1,
   same rule as the ledger: an observer that can halt a send file gets routed
   around.

Both land *after* the upload file exists and neither can block one.

**Three smaller things, all found by running the machine rather than reading
it.**

`deal` printed `OVER CAP` on all four beats for a batch of 2, where a line is
50% by arithmetic. `check_batch` already knew this and warns rather than fails
below 8 leads (`MIN_BATCH_FOR_SHARES`); `deal` did not consult it, so the two
halves told different stories and the fixes on offer were re-dealing, which the
skill forbids once drafts exist, or writing copy nothing needs. It now says
`under 8 leads ... not a batch to fix`. **This mattered today specifically** —
today's batch is 2.

`outbound/hook.py`'s schema help still said *"observation_id may be blank — the
hook stage still fetches"*. Pre-flip language, and it is printed to a
`hook-worker` at the moment its proposal was rejected for exactly that: a blank
`observation_id` is legal only with `escalated` and a rung. The recovery
instruction contradicted the rule that had just fired.

`audit/airtable.py` carried a **`create_records`** that nothing had ever called
and no test covered, added the same day as `update_records`. Generic POST, so
`create_records(LEADS_TABLE, rows)` would have written Lead rows from Python —
the one thing the module docstring says it does not do — sitting two screens
below the constant naming that table. Deleted, with the reason in its place. The
boundary was a sentence while the capacity to cross it was right there. Same
rule as `audit/apify.py`'s: **surface area, not capability.**

**What was checked and was genuinely fine**, so nobody re-audits it: every
module has a live importer; every documented flag parses against the real parser
(a flag checker `doc-check` does not have — three hits, all prose); the warm-hit
stop exits 1 and a missing wall exits 2; `export --anchors` caught a drafter
reproducing a different line under the assigned id; `hook --against` caught a
one-word edit to a quote and a blank provenance; `qualify` fails closed on a
list and settles activity from an observation date, upward only; the missing
ledger exits 2; `wall-add`/`copy-usage` `--dry-run` write nothing;
`copy-check` read 46 live lines from Airtable and matched the cache.
`data/runs/2026-08-01-q1-research.json` is absent because that batch predates
`select --batch` writing the corpus, which is what its docstring says.

`audit/draft_lint.py`'s **`scan()` is dead** — `bare_links` and `EM_DASH` are
imported individually by `lint.py` and `copy_sync.py`, so both rules are
enforced and the wrapper is redundant. Left alone: it is the documented entry
point of a module whose whole purpose is defining each rule once, and deleting
it is a coin flip nobody needed today.

Three test files have no standalone runner because their tests take a pytest
fixture; `requirements-dev.txt` claimed every file has one. The claim is now the
rule it actually is. `test_replies.py` took no fixture and got its runner.

958 tests, `doc-check` clean, nothing in `data/` or `copy/` touched.

## 2026-08-01 (the flip) — P3 on, one batch before its own gate

Haytham, immediately after the previous session recorded D26 (*the flip stays
off, and the batch that would decide it is not this one*): **turn the flip on,
apply everything.**

So it is on, and the honest framing is in **D27**: the corrected `unobserved`
number still does not exist and could not be produced — the corpus that would be
re-scored lived in `work/` and did not survive the container. This is acting on
the diagnosis, not on the measurement the diagnosis predicts. That is his call
and it is recorded as one rather than folded into D26 as a change of mind.

All three switches. `hook-worker` stops fetching and chooses from `select`'s
shortlist; `select` runs before the hook stage and is consumed; a `plan` decline
binds (**D28**).

## The contradiction in the proposal, and how it resolves

Part 5 says `select` writes the authored clause. Part 7 says do not make
`select` a model call — rank mechanically and hand a model three candidates.
Both cannot hold.

Part 7 wins, and the result is cleaner than either: **`select` stays pure Python
and `hook-worker` becomes an author instead of a searcher.** What it loses is
the search. What it keeps is the only genuinely authorial part of the beat —
deciding which piece of evidence is worth a stranger's first three seconds, and
writing the sentence that proves a person read it. The shortlist was always
justified as making a rejected first pick free, and now that is literally what
it does.

## The consequence nobody wrote down

Removing `WebSearch` from `hook-worker` **deletes the podcast rung**, which is
the free "their name plus podcast" search and the one that reaches coaches who
do not post. Nothing in the proposal mentions it.

It moved to `research-worker`, which is the proposal's own logic applied
honestly — retrieval belongs to the stage that already fetches — and it is a
real cost increase at stage 2, against a batch Haytham had already called
expensive. It is also R1's mitigation in practice: the retrieval pass now
carries the hook criteria and not only the floor questions.

`research-worker` says so at the top now. **An observation it does not return is
a hook that cannot be found**, and it will present as the lead's fault rather
than the retrieval's. Three things follow that it is told explicitly: return the
whole text rather than the part that settled the floor, because the hook stage
cannot go back for the rest; label `kind` honestly rather than upward, because it
decides how the observation ranks; and a summarised observation is worse than
none, because it reaches the reader as a quote and the verifier refutes it.

## Ban #3 stopped being a sentence

*"No invented specifics — if it cannot be cited, it does not exist."* That has
been something an agent was asked to remember for as long as there was nothing
to check it against. `select` hands the worker the observation's stored text, so
now there is: **`hook --against work/select.json`** requires the quote to be a
contiguous piece of the observation it names.

Whitespace is normalised and nothing else. A scraped post carries line breaks a
quote will not, but a changed word is precisely the drift this exists to catch,
so forgiving case or punctuation would forgive the failure. It also catches two
sentences welded into one quote, which is a real refusal from `2026-08-01-q1`
that cost a verifier pass to find.

Exercised against the real committed batch rather than a fixture: a verbatim
quote from Mirella's stored LinkedIn post passes; the same quote with `stay
consistent` changed to `stay focused` fails naming the drift.

**A blank `observation_id` now means one of two opposite things** — an
escalation the worker walked, or a hook composed from nothing — so it has to be
declared. `escalated` plus `escalation_rung`, or it is a failure.

## What the flip makes riskier, and the one thing that did not move

`hook-verifier` is untouched. That is not conservatism: the worker no longer
reads the page it cites, so **nothing confirms the stored record was ever real
except the live re-fetch**. If a research worker summarised a post instead of
copying it, every mechanical check downstream passes. That paragraph is in the
agent file now.

`refute_rate` changes meaning accordingly. It used to mean a worker misread a
page it had open; now it means the stored text did not match the page, which is
a research-stage failure reaching the reader. The skill says to name it as one.

## The declines, and why they could turn on now

`plan` shipped advisory for two batches on an explicit argument: a gate shipped
alongside its own measurement generates the data that judges it. That objection
was **paid off rather than dropped**. `metrics --plan` reports, of the leads
carrying a declined rung, how many produced a verified hook and how many
produced none — D21's reversal condition in D21's own words.

The half that does not change is stated three times because it is the one that
would do real damage if it drifted: a decline gates **spend**, never inclusion.
A declined lead still gets researched, still gets a row and a Blocker, and gets
a null hook rather than a purchase. `plan` still exits 0 when every rung on a
batch is declined.

## The numbers that judge all of this

`escalation_rate` — hooks the shortlist did not hold. It counts every attempt,
not only the verified ones: an escalation that produced a refuted hook still
cost the fetch the flip was meant to remove, and counting only the useful ones
would report the rate of *successful* escalations under the name of the
escalation rate. A null hook is not an escalation either — it is the cheaper,
honest outcome and must not be made to look like the expensive one.

`declined_and_dry` — `?` and never `0` without a plan file, because a zero there
would read as "declining cost nothing", which is the claim being tested. The
wall's asymmetry, a fifth time.

The skill gained a second tripwire to match: a third of the first wave
escalating is the flip failing, not those leads being hard.

**Where this can go wrong, and the three different answers**: a high
`escalation_rate` means research must fetch deeper, not that the ranker is
wrong; a high `refute_rate` means observations are being summarised rather than
kept verbatim; a high `null_hook_rate` with neither means selection genuinely
cannot replace the search and P3 was wrong. D27 carries all three.

951 tests (+20), `doc-check` clean at 30 commands.

## 2026-08-01 (post-mortem, acted on) — both blocking numbers were artefacts

Haytham dropped the post-mortem back in: fix this, make sure the proposal is
applied and wired, and the Claude usage was a lot for 20 leads.

**The useful thing that fell out of reading it against the stored artifact is
that the flip's verdict rests on two artefacts, not two findings.**
`data/runs/2026-08-01-q1-select.json`, read directly:

```
19 leads   agreed 4   missed 3   unobserved 5   (7 not compared)
bans: site_prose 21, not_content 5, stale 3, too_short 2, third_party 1
MISSED: Sanaa Diab, Bindu Joseph, Rory Buck — all three "excluded by site_prose"
```

**All three MISSED are one ban**, and it is also the largest ban in the corpus
at 21 of 32 rejections. **Four of the five UNOBSERVED are a flag**:
`research-worker.md:37` ran `apify li-posts --max 5` with no window while
`hook-worker.md:88` ran `--since 3months`, so one profile was asked two
different questions a stage apart and the hook stage kept "discovering" posts
research had never requested. `docs/hook-rules.md` has declared one owner for
that window since it was written; the agent files drifted from it and nothing
could see that, because `.claude/agents/` was outside `doc-check`'s corpus.

So the flip stays off (D26), and the condition to reopen it is one clean batch
after both fixes with `unobserved` and `missed` read apart.

## The ban fix needed a fourth line, and that is the interesting part

Removing the location ban alone changes nothing. A page somebody wrote about
themselves has no publication date, so all three would have moved from
`site_prose` to `no_date`. `docs/hook-rules.md` already granted the exemption in
prose — *"an evergreen framework **or an About-page line they wrote themselves**
is fine at any age"* — and the code carried only the first half.

What replaces the location ban is **ban #1's honest mechanical form: the same
text observed for two different leads.** That is the ban's own test — could this
be sent unedited to another coach in the segment — settled against the only
evidence that can settle it. It abstains on an observation nobody could
attribute, because a ban costs a lead its only observation.

## The re-measurement that could not be run

`work/` does not survive the container, and only the *verdict* was committed.
So the batch that disproved the ban cannot be re-scored against the correction:
selections carry a shortlist, and a rejection carries a ban name and a URL,
neither of which can be ranked again. **`select --batch` now writes the corpus
beside the verdict.** The expected 3 MISSED → 0 is a derivation from the stored
bans, not a measurement, and it is stated that way everywhere it appears.

## The Claude bill, which nothing here could see

Haytham is right and the proposal half-knew it: Part 11 says *"the larger waste
is agent passes, and it is invisible"* and then measures everything except that.
`2026-08-01-q1` cost ~64 agent passes for 20 leads and 5 rows, and the only
record was one number typed into `metrics --passes` at the end of a long
session. No stage, no model. "The drafting loop is most of it" was a guess.

`ledger pass --stage <s> --agent <a> --model <m> --count <n>` writes to the same
JSONL with `kind: pass`, and `metrics` prints `passes_by_stage` and
`passes_by_model`, REPORTED and never measured. Nothing reported prints `?` —
a zero would read as "this batch used no agents", which is the wall's asymmetry
a fourth time. **Counts, not dollars**: model prices are a value this repo does
not own and would go stale in it.

**The tiers were already right and are not the lever.** research, hook and
hook-verifier on sonnet; draft-worker and draft-verifier on opus. Downgrading
the cold read is the one saving this repo refuses twice in writing — it caught
11 of 12 identity beats that had passed the linter. The lever is D25: **a check
that can be mechanical must not cost an agent pass**, and every fix in this
session is one — `hook` before a verifier is spent, `check_batch` seeing a
template no per-email reader can, `crm-rows` replacing a script and the audit of
it, `--escalate-only` replacing a whole stage re-run, `ledger batch` replacing
telling twelve workers a label.

## Everything else, in the order the post-mortem ranked it

- **`--batch` on every paid subcommand, and `ledger batch` writes `work/BATCH`.**
  The env var was never going to work: a subagent is a different process. The
  label is discoverable now, and `ledger batch` with no argument says which one
  resolves and where it came from.
- **`fetch --escalate-only <sites.json>`.** The retry that put 52 of the batch's
  83 duplicate pairs in the ledger re-read every site first. D22 names that risk
  in advance and it happened anyway, because avoiding it meant calling
  `fetch.run_plan` by hand.
- **`main.py hook` closes F4.** Six of twelve drafts had to alter text a
  verifier had certified word for word. Every finding says *pick a different
  quote*, never edit theirs — one stage later the drafter has neither the
  alternatives nor the authority. It also catches the empty-slug LinkedIn URL
  Maurice's hook died on.
- **Quoting is not claiming.** A figure in the hook beat that is also in the
  certified quote is exempt. The first cut spared it by *value*, which spared it
  in the identity beat too; its own test caught that, and the substitution now
  happens inside the hook beat's text.
- **LinkedIn is two rungs.** Different actors, different prices, one batchable
  and one provably not. `yield_by_rung` reported `li_posts 10` where three came
  off profiles, in the number that settles F5.
- **`crm-rows`.** The join is explicit and fails closed, and coverage prints for
  every field rather than the four somebody expected to be populated.
- **Two checks a single email cannot see**: a four-word phrase two hooks share,
  and a close that opens on a question. Both warnings — the second is bank copy
  and `copy-check` now names `cta-04` at the source, on a passing run.
- **One `split_sentences`.** It was in `outbound/lint.py` rather than
  `draft_lint`, in two copies, both with the same bug.

Adding `.claude/agents/` to `doc-check` found a third thing on its first run:
`draft-worker.md` had been telling every drafter for months to read four
reference files at paths that resolve from nowhere.

**Not done, and named rather than dropped**: re-hooking Sehar McDermott is
operational and costs a paid rung; the `cta-04`/`ps-04` re-deal is Haytham's
edit in Airtable; and `hook-worker` optimising for the most quotable line is a
judgement, which D25 is explicit about not mechanising.

931 tests (+69), `doc-check` clean at 30 commands.

## 2026-08-01 (CRM write) — two defects in the Leads push, both mine

Haytham asked for the batch in Airtable. The Batches row was fine. The 20 Leads
rows went in **missing First Name, Last Name, Website, LinkedIn and City on
every single row**, and he caught it, not me.

**Cause: I built the rows from `work/researched.json`.** That is the research
workers' typed output — floors, sources, coach_type, email, hook. It has never
carried the intake identity fields, which live on the normalized Lead in
`work/clear.json`. I read `first_name` off the wrong object, got nothing, and a
`if v not in (None, "")` filter dropped every empty key before the request was
built. **No error, no warning, just absent columns.** Fixed by joining
`clear.json` on email and patching all 20.

**The worse half is that I said I had verified it.** I ran a check over Name,
Status, Hook Verified and Blockers, saw 20/20, and reported the push as
cross-checked against the store. Those are the four fields I expected to be
populated. A verification that only looks where you expect to find something is
not a verification — it is the writer certifying its own work with extra steps,
which is the one thing this machine's whole chassis exists to prevent. The
second pass counted every field on every row and is what actually found it.

**A second defect fell out of doing that properly.** Three of the five exported
rows had a `Hook` field naming a sentence the reader never saw:

  CRM Hook   "Your LinkedIn experience lists a complete business analysis..."
  Body       "You went through a fitness studio's finances, then took over..."

The `Hook` field was carrying the hook-worker's certified proposal while `Body`
carried the drafter's rewritten version. That is exactly the failure
`export --anchors` was built to catch one field over — a CRM row describing an
email nobody received. On an exported lead the `Hook` field now holds what
actually shipped, and the certified wording plus its source and date moved into
Notes as provenance, so nothing is lost and nothing is misdescribed.

**What is genuinely absent and correct**, checked against the source CSV rather
than assumed: City 11/20 (the CSV carries 11), Instagram 0/20 (no such column),
Sells To 15/20 (collected, never inferred — an empty answer draws a generic
line), Failed Floors 1/20, Subject/Body/Anchor Lines 5/20 (only what shipped).

**Worth building rather than remembering.** Nothing in the repo writes a Leads
row — `audit/airtable.py` says so deliberately, and this push was done on
Haytham's explicit instruction with a hand-written script. A hand-written script
is exactly where a wrong-source join like this hides. If CRM writes become
routine, the row builder belongs in code next to `export`, where the field
mapping can be tested and where a required column arriving empty can fail
closed instead of silently vanishing.

## 2026-08-01 (batch 2026-08-01-q1) — the flip is a no, and the reason is specific

Twenty UAE coaches, run end to end as the measurement batch three sessions had
been waiting for. **`data/runs/2026-08-01-q1.jsonl`**, `-select.json` and
`-metrics.json` are committed beside this entry.

```
AGAINST: 12 verified hook(s) — 4 agreed, 0 shortlisted, 3 missed, 5 unobserved
hook_yield 63%  refute_rate 26%  null_hook_rate 10%
cost_per_hook $0.0364   wasted_retrieval 47 paid fetch(es), $0.2086
```

**Five of twelve verified hooks (42%) cited a page no observation carried.**
That is the fetch selection could not have replaced, and it is too large to flip
on. Four were LinkedIn posts the hook stage pulled that research's own
`li_posts` call had not returned — different `--since` windows over one profile
give different posts — and one (Dana Barto) came off a site nobody had found
until the hook worker searched for it. **So P3 does not flip.** The fix that
number actually points at is research fetching deeper, not selection replacing
the fetch.

**All three MISSED share one cause and it is three lines.** Rory Buck's race
result, Sanaa Diab's named client project and Bindu Joseph's career pivot were
each observed, each independently VERIFIED, and each excluded by `select`'s
`site_prose` ban for being `kind: about`. That ban came from F5's narrowing —
"no generic site copy" became `kind != about` — and it is too blunt. What the
verifier refuses is the **generic**, not the location. Fix the ban and reachable
goes 4/12 to 7/12.

## The correction that cost five leads

I concluded that a hook cited to a `linkedin.com/in/` URL is structurally
unverifiable, because five verifiers hit the authwall with WebFetch and curl.
Haytham: *"of course linkedin urls are not fetchable through normal fetchers,
thats why we use linkedin apify actors."*

Correct, and the evidence was in the same run — research had pulled those exact
profiles with `apify li-profile` an hour earlier. The verifiers have Bash. The
rung was theirs the whole time and neither their agent file nor my prompts said
so. Re-run through the actor, all five produced real verdicts immediately:
three VERIFIED, two REFUTED on substance (an unsourced "rare adoption curve"
gloss, and a hook that fused two separate sentences).

`.claude/agents/hook-verifier.md` now says the paid rung is a LIVE fetch that
satisfies independence completely, that the rule which must never break is
reading the *stored observation*, and that **an INCONCLUSIVE reached by only
trying WebFetch is a rung not walked.** Three verifiers had independently found
that raw curl plus LinkedIn's embedded `application/ld+json` beats the WebFetch
summariser on post URLs; that is written down now too.

## Four findings the run turned up that nobody was looking for

**The scraper builds LinkedIn URLs that 404.** Maurice Hellemons' hook was
refuted on a dead citation. The content is real and paid for; the URL harvestapi
constructed has an empty slug (`/posts/mauricehellemons_-activity-...` against a
working `/posts/lucycrussell_i-put-my-phone-on-airplane-mode-10-days-ago-...`).
**This is the sharpest case for R2 yet**: the string was copied correctly, the
content is genuine, and the citation is still unusable, because an email cannot
cite a URL the reader cannot open. Only a live fetch finds that.

**The hook is certified before it is linted, and they disagree.** Six of twelve
drafts had to alter a hook the verifier had certified word-for-word: an em-dash
and spaced hyphens (`check_voice` refuses absolutely), "touchpoints" (JARGON
list), and — worse — "70.3", "2023", "11 years", "27 years". `check_numbers` has
no exemption for a figure that came from the recipient's own cited words, so the
rule meant to stop us relabelling a client result is instead deleting the
recipient's own facts from the one beat whose job is to prove we read their
page. Both drafters moved the figure into the subject line, which is not
digit-checked. That works and it is backwards. The fix is a scope, not a
loosening: a figure inside the hook beat that also appears in the certified
`hook_quote` is quoting, not claiming.

**Re-voicing the identity line is where every draft breaks.** Eight cold reads,
eight REWRITEs, the same beat every time. Four of five beats are dealt bank
lines and every reader cleared them explicitly. The identity beat is the one
written per lead and it is the only one that failed, always the same way — a
hand-written line that sounds spoken re-voiced into something a database would
say:

```
id-any-6  Deciding who is worth your time is most of my job. 30 of the ones
          I picked turned into signed clients this year.
drafted   Mine is on people, deciding who is worth your time. 30 of them
          became clients this year.
```

Gone: "is most of my job", the only place a stranger learns what Haytham does,
and "the ones I picked", which is what makes the 30 proof of judgment rather
than a floating statistic. Elsewhere: colons standing in for verbs, three
numbers stacked in a sentence, "the last business coach I worked with in Dubai"
compressed to the noun-stack "a Dubai business coach". One reader checked and
reported **zero of the 33 lines in `copy/identity.csv` use a colon.**

**The linter cannot see any of it.** Claim preservation survives every one —
right figures, right segment, nothing invented. What dies is voice, which is
what D10's chassis exists to protect and what the linter admits it cannot catch.
The cold read caught it eight times out of eight. Candidate fix: narrow what
re-voicing may change to what the seam actually needs, keeping the line's verb
and first-person framing.

## Two dealt lines drew fire, and that is Haytham's call

`cta-04` "Worth 15 minutes?" — two readers independently: the ask is a question
that invites "no", and *"the ask itself has become optional, which is the one
thing it is not allowed to be."* `ps-04` "if it's not for you, say so and I'll
leave it there" — a soft exit handing a one-word out immediately after the ask.
Both were reproduced faithfully from Copy Assets. Both readers said so. The copy
lives in Airtable and this is a bank-level question, not a drafting one.

## Smaller, recorded so they are not rediscovered

- **`apify` has no `--batch` flag.** Telling workers to pass one was impossible
  to follow, which is why 15 retrievals landed in `data/runs/2026-08-01.jsonl`
  and the batch under-reported its cost by 30%. Folded back, each line carrying
  `batch_relabelled_from`. The label should be discoverable, not remembered.
- **cheerio-scraper needed a console permission approval** nobody had clicked —
  a 403 `full-permission-actor-not-approved`, not the actor-id problem the
  proposal blamed. Approved mid-run; it then read 2 of 11 URLs.
- **`observe` graded research objects as observations.** The batch skill has
  always said to run it on a research file; doing it for real produced fifty
  violations about ten fine objects. It unwraps now.
- **The activity floor counted third-party coverage.** A company post naming
  Lorna King, two days old, made her "active". Fixed: `third_party` is skipped,
  `unknown` still counts, and dropping an observation can only move a lead
  toward `unclear`.
- **`HOMEPAGE-FIRST: 0/20 leads, 0 of 57 page fetches deferrable.** The
  proposal's −30% would have bought exactly nothing on this list.
- **`metrics.rung_of` conflates li_profile with li_posts** — LADDER has one
  LinkedIn rung. The `about 2` figure is right; `li_posts 10` includes three
  profile-sourced hooks.
- **83 duplicates, mostly mine.** A `fetch --escalate` retry re-read all 20
  sites before its 403. D22 pollution, self-inflicted, and an escalate-only CLI
  path would have avoided it.
- **Mihaela Nica's blog is serving gambling spam.** Her domain is compromised.

## Where the batch stopped

12 verified hooks drafted, all linted PASS. Cold reads: **1 SEND (Kira Jean),
8 REWRITE**, rewrites in flight. Nothing exported — no `leads.csv` yet, and
none of this has been sent. The three leads with no verified hook and the five
refuted ones hold, which is the machine working.

## 2026-08-01 (Part 8) — the batch stops being unjudgeable

Haytham: get everything unblocked, wire it up. Three decisions taken first —
metrics live in the repo not the CRM, Python computes the Batches row but does
not write it, and the Smartlead bridge gets built tolerant rather than waiting
on a real export.

**The gap this closes is not the flip.** That is still gated on a batch. What
was missing is everything needed to *judge* that batch when it runs: Part 8
names seven per-batch numbers and this repo computed zero of them. `ledger
report` covers what Python can see, because those retrievals pass through code.
Everything on the hook side happens inside an agent, got narrated into a brief
from memory, and died with the session. That is why every cost claim in the
proposal had to be reconstructed from a hand-written journal entry.

`python main.py metrics` now computes `hook_yield`, `refute_rate`,
`null_hook_rate`, `yield_by_rung`, `wasted_retrieval` and
`cost_per_verified_hook`, and writes `data/runs/<batch>-metrics.json`.

**The rule that shaped every field: a count nobody supplied prints `?`, never
`0`.** This is the dedupe wall's asymmetry and the ledger's, a third time. A
missing wall must never read as "nobody has been contacted"; a missing ledger
must never read as "this batch cost nothing"; an unsupplied raw count must never
read as "no leads came in". **A zero is a measurement.** A metrics block that
quietly zero-fills is worse than no block, because it looks like evidence and
gets quoted into a brief as though somebody counted.

The cost field needed its own flag to hold that line. A zero cost from an
unopened ledger and a zero cost from a genuinely free batch are the same number
and opposite facts, and only one of them belongs in a CRM currency field where
it will be believed for months. `ledger_read` separates them; without it the
first cut printed a confident zero into the Batches block and I nearly shipped
it.

**`yield_by_rung` derives the rung from the hook's source URL rather than
trusting a worker to report it.** A worker naming its own rung is a worker that
can mislabel the number judging its rung — the same reasoning that makes
`select` derive the `obs_id` join instead of trusting a citation. `plan.LADDER`
and `normalize.classify_site` stay the authorities; nothing is restated (D23).

**`wasted_retrieval` excludes free rungs and verification fetches**, and that is
not tidiness. Its only use is deciding whether a *purchase* was worth making, so
counting tier 0 would inflate it with things that cost nothing, and counting a
verify fetch would count the one duplicate this machine actually wants.

**The Batches row is computed here and written by a human-visible step.**
`audit/airtable.py` says writes stay narrow and a row lands where somebody sees
it, and a metrics command is not the place to widen that. The thing that was
actually wrong was never that a model did the typing — it was that a model did
the *arithmetic*, from memory, at the end of a long run. Every value in the
block is measured or `?`, so transcription is all that is left to get wrong.

**`python main.py replies` is Part 8's manual Smartlead bridge**, and the first
thing in this repo that touches reply data at all. Export a CSV, join on
`email`, get reply rate by `hook_type` and by rung. `Hook Type` has been a CRM
select since the beginning, described in the base as *"a testable variable
against reply rate rather than a detail buried in prose"*. The variable existed.
Nothing could run the test. Now something can.

Columns are sniffed because nothing here has ever seen a real Smartlead export,
and a hard-coded name would fail on first contact and fail *silently* if it
happened to match something else. A column it cannot identify **exits 2 naming
the headers it saw** rather than reporting a zero reply rate — a zero would read
as "the campaign did nothing" when the truth is "the question could not be
asked". Same shape as everything else here.

**`--all-replied` is never inferred, and that is the sharpest edge in the
module.** Smartlead can export a file already filtered to people who replied,
with no status column at all. That is *indistinguishable* from a full export
whose reply column went unrecognised, and the two differ by the whole answer —
6% against 100%. So it is a flag, and without it the second case is an error.

**A test caught the one real bug.** The first cut read any value in the reply
column as a reply, reasoning that the column had already been identified. That
is right for a timestamp column and wrong for a status column, where the
ordinary contents are `SENT`, `OPENED` and `BOUNCED` — so `SENT` counted, and
the rate was inflated for whichever hook type happened to sit behind it. My own
manual run reported 3 of 4 and I read past it; the test asserting 2 of 4 is what
noticed. The column's **kind** decides now. An unrecognised status counts as
not-a-reply and is named, because under-counting understates a campaign while
over-counting makes a hook type look good and drives a real decision on a word
nobody checked. Ordinary statuses pass silently, so the note only fires on
something genuinely new — a note that cries wolf every run is a note nobody
reads by the third one.

**Neither command can fail a batch.** Both are observers, and the ledger's rule
applies: reporting a bad number is the job, and a gate that can halt a real send
file over an accounting line is a gate people learn to route around.

**Neither draws a conclusion either.** `replies` prints `NOT A VERDICT` and says
why: one batch is a handful of samples per bucket, and the difference between
1 of 1 and 0 of 1 is noise wearing a percentage. It is worth running because it
accumulates.

**What is left is now exactly the flip, and nothing else.** `hook-worker` stops
fetching, `plan` starts declining, `select` gets consumed, and F4's
`HookProposal` arrives with the authored clause. The trigger is unchanged — one
batch reaching stage 3b, producing `ledger report`'s `DUPLICATE li_posts` count
and `select --against`'s `AGAINST:` line, with `missed` and `unobserved` read
apart. What changed is that everything needed to judge that batch now exists.

857 tests (+39), `doc-check` clean at 28 commands.

## 2026-08-01 (P4 and the rest) — everything the measurement does not gate

Haytham: read the proposal and the journal, then plan the remaining parts. The
useful thing that fell out of reading them together is that **the remainder is
two piles, not one**, and only one of them is blocked.

P3 landed switched off because it is gated on numbers that do not exist:
`data/runs/` has never recorded a `li_posts` fetch, so the duplicate the whole
proposal exists to remove has never been measured. Three sessions have held that
gate. **This one did not touch it.** What it did was finish everything that was
never waiting on it — which turned out to be most of what was left.

Shipped, in five commits, each its own argument:

- **The `run_plan` fallthrough**, recorded as found-and-not-fixed when P3
  landed. It dispatched on `actor_key`, returned the render crawler for
  `site_render`, and **defaulted to cheerio for everything else** — so a caller
  handing it an `li_profile` batch would have run a static HTML scraper against
  LinkedIn URLs, paid, silently, returning empty items that read as a lead with
  nothing on their profile. The defect was the defaulting, not a caller. It
  raises now.
- **P4a: `yt_channel` and `search` retired.** Nine actors, two of which bought
  nothing. `yt_channel` returned a subscriber count whose only consumer is
  `audience_size` — captured, never gated on, since the audience floor died with
  the shift to selling their clients rather than leverage on their list. A paid
  call wired to a field that by design changes no decision. `search` duplicated
  the agent's free WebSearch, which `audit/footprint.py` already called the
  preferred path and which is what every skill actually used. **Neither needed a
  measurement, because neither rests on one**: both are arguments about what a
  call *changes*, not what it costs. `classify-footprint` was untouched, and
  being fetch-agnostic is exactly why that was a deletion and not a rewrite.
- **P4b: homepage-first, counted rather than switched on.** And here the
  proposal was wrong, which is worth writing down. It estimates -30% of tier-0
  page fetches from the first batch's 106-of-151 floor pass rate. But those 45
  failures were settled with everything a research worker gathered across
  WebSearch, LinkedIn and several pages — and the floors pass on `unclear`. To
  skip anything, a homepage-only pre-pass needs a **clear `no` on one page**, and
  `check_uae` and `check_coach` only reach `no` on positive contrary evidence: a
  named non-UAE location, a named non-coach occupation. That will fire far less
  often than 45 in 151. Nobody knows how much less, so `fetch` now prints
  `HOMEPAGE-FIRST: <n> lead(s) already a clear no on page 1, <n> of <n> page
  fetch(es) deferrable` and skips nothing. One batch settles it. An unreadable
  homepage is `unknown`, never `no` — a counter that implied otherwise would be
  arguing for a saving it had not found.
- **F3 closed, and it needed no new evidence, only a wire.** The activity floor
  found zero usable dates across nine sites and ~220,000 characters, so
  `active_recent` was `unclear` for effectively every lead and the floor did
  nothing; the repair was a write-back from stage 3 that an orchestrator had to
  remember. **The dates had existed since P1 and nothing read them.**
  `research-worker` returns schema-checked observations carrying `published_at`,
  and it returns them *before* it calls `qualify`. The date was in its hand one
  line earlier.
- **F11 closed, recorded as D24.** `copy-check` and `deal` move to a new stage
  2b, before the hooks.

**The one real decision this session made: an observation may only ever move the
activity floor upward.** `check_active` already answers `NO` to a stale date. So
handing it the newest of an old observation set would have opened a brand-new
kill surface at the one floor built not to have one — and opened it on the
weakest evidence available, which is that the pages *we happened to retrieve*
were old. D4 says a false kill is permanent and invisible while a false pass
costs one research call. **Better evidence is a reason to settle a floor, not a
reason to weaken `unclear` passes.** So a stale set returns exactly what an
empty set returns, the restriction lives inside `activity_from_observations`
rather than in a caller's discipline, and the CLI test asserts the stale run is
line-for-line identical to the bare run. That identity is the property; anything
weaker is an implementation detail somebody will optimise away.

It still says what it saw: `newest of 1 observation(s) is 2026-01-13 (200d ago)
— too old to settle the floor, and never a kill`. Worth reading in a report even
though it changes no verdict.

**D24, the deal moving, is the change with a cost attached, and the cost is
stated rather than discovered.** The bank leaves between 12 and 36 words for a
hook. Dealing after the hook stage meant a hook could be found, cited, certified
by an independent verifier against a verbatim quote — and then handed to a
drafter with 12 words of room. `draft-worker` is forbidden from trimming the
offer, close or ps lines, because `hook_room` is computed on the assumption
those hand-written sentences survive intact. **So the only thing left to
compress was the one sentence the machine had just gone to the most trouble to
certify, and nothing re-checks it: the verifier has already run.** A hook chosen
to fit is a citation. A hook squeezed after certification is a citation drifting
from its source.

The price: lines are now allocated to leads that later hold on a refuted hook,
so the shipped batch drifts from the declared weights. That is R4, it needs no
new machinery — `export --rebalance-ps` exists for exactly this — and what
changes is frequency. It fires on most batches now rather than some, so the
brief template carries the drift it reports. Re-dealing after the hooks is not
the fix: the drafts and the CRM rows are written against the file `deal`
produced, and a second allocation makes them disagree.

`hook-worker` gets its lead's `hook_room` from `work/anchors.json` and writes to
it. **`hook-verifier` deliberately does not** — its question is whether the words
are on the page, and a length note is a reason to be lenient about a quote that
nearly fits.

**What is left is exactly what the measurement gates**, and nothing else: the P3
flip (hook-worker stops fetching, `plan` starts declining, `select` gets
consumed) and F4's `HookProposal`, which needs the authored clause the flip
brings. The trigger, so nobody re-derives it: one batch reaching stage 3b,
producing `ledger report`'s `DUPLICATE li_posts` count and `select --against`'s
`AGAINST:` line, with `missed` and `unobserved` read apart rather than summed.

818 tests (+12), `doc-check` clean at 26 commands and 7 apify subcommands, down
from 10.

## 2026-08-01 (P3) — the machine can say which fetch it could have skipped

Built P3 of `docs/proposals/2026-08-01-hook-retrieval.md`: `outbound/plan.py` and
`outbound/select.py`. **Switched off, exactly as the previous entry asked** —
`hook-worker` still fetches, still proposes, and is not edited. Neither module is
read by anything.

The last entry's brief was that P3 could not be judged, because `data/runs/` had
never recorded a `li_posts` fetch. So the deliverable here is not a saving. It is
**one line on the next batch**:

```
AGAINST: <n> verified hook(s) — <n> agreed, <n> shortlisted, <n> missed,
         <n> unobserved, <n> no_pool
```

**`missed` and `unobserved` are the whole design, and they mean opposite
things.** `missed` says the hook's page *was* observed and the ranker passed it
over, and it names the ban that dropped it — a wrong ban is a three-line fix.
`unobserved` says the hook cited a page no observation carries, which is
precisely the fetch that selection could not have replaced. Collapsing them
yields a percentage nobody can act on. That distinction also caught a real bug
in the first cut: an observation that survived every ban and merely ranked fourth
was being reported as `unobserved` — the same word used for a page nothing ever
fetched — which inflates the number arguing *for* keeping the fetch. Pinned by a
test now.

Read that line next to the ledger's `DUPLICATE li_posts` count. One says what the
second fetch cost, the other says whether it bought anything. Flipping the hook
stage over is then a change against evidence.

**`plan` declines nothing, and that needed no new decision.** D21 already says
ownership gates a purchase and never a kill, and already carries the reversal
condition: *"a batch where declining to spend on low-confidence channels costs
more verified hooks than it saves scrapes."* Nobody has measured it. So a step
whose channel is `absent` is labelled `decline` and taken anyway, and the label
is there to be correlated against the leads that produced no hook. Shipping the
gate beside its own measurement would have the gate generate the data judging it.
`unknown` is never declined — that is `resolve`'s rule one stage over, and
declining it would be the false-negative surface R3 names.

**D23: the ladder is code now.** The four rungs lived in `docs/hook-rules.md` and
`.claude/agents/hook-worker.md`, kept in agreement by hand, and the agreement had
already failed twice — the paid rung once sat at #1 under a heading that said
"cost order", and the recency window existed as four numbers in four files.
`plan.LADDER` is the authority; `hook-rules.md` names it and keeps what it
actually owns. **The agent file still carries its own copy, deliberately**: the
hook stage keeps fetching this phase, and rewriting its routing would be the
behaviour change this phase avoids. So there are two copies today, not one, and
the second is implementation-layer prose. It goes when the fetch does.

**Four of the twelve bans are mechanical**, not three as the proposal counted —
it missed that the `observation_id` join it proposed one paragraph later *is*
ban #3. A candidate names the observation it came from, so a hook citing a page
nothing retrieved cannot be built here at all.

Three corrections to the proposal, each because the code had moved under it:

- **`author == "self"` was the wrong filter.** `AUTHORS` is three-valued and
  `unknown` is the default, so filtering on `self` rejects most of a real pool
  for a field nobody was required to fill. `third_party` is excluded, `unknown`
  ranks second, and authorship stays the live verifier's call.
- **`kind != "about"` was incomplete.** `KINDS` grew `bio` and `result` when
  `resolve` shipped, and `resolve` writes a `bio` per linktree — without the
  wider rule, every link-in-bio lead's top pick is its own wall of buttons.
- **`MIN_HOOK_WORDS` is not the hook room.** It is a *floor on the hook*, used
  that way in three places; reusing 12 as a ceiling would be one number wearing
  two meanings in two stages, which is the drift that gave this stage four
  recency windows. `deal` still runs after the hook stage, so `select` says
  "hook room unknown" rather than assuming it, and length is a floor on the
  observation and nothing else.

**No score.** `resolve` states the rule — *"nothing in this repo carries a
numeric confidence, and one batch of 151 leads cannot calibrate a scale"* — so
the ranking is a lexicographic sort key of enum positions, printable in words.
Platform order is borrowed from `observe.PLATFORMS` rather than restated.

**Pricing is opt-in, and that is not fussiness.** `tests/test_cli_failures.py`
shells out with the real environment and only strips `AIRTABLE_API_KEY`, so a
default-on price lookup would reach Apify on a developer machine and not in CI —
the exact whoever-runs-it failure `offline_env` exists to prevent. Without
`--price` a paid step reports "not priced", which is a different answer from an
estimate of zero and different again from the cost gate's own "cannot be priced".
A first cut sniffed those apart out of the decision string, and a decline
overwrote it; `cost_note` is now its own field.

**Found and not fixed:** `fetch.run_plan` dispatches on `actor_key` and falls
through to `crawl_static` for anything that is not `site_render`. Nothing reaches
it with a non-site actor today — `plan` emits no run dicts — but a future caller
handing it a `li_profile` batch would run cheerio against LinkedIn URLs, paid,
silently, with plausible-looking empty results. Worth two lines and a test in its
own commit.

806 tests (77 new), `doc-check` clean at 26 commands.

## 2026-08-01 (P2, run against real leads) — the headline number was measuring the vendor

Ran `resolve` on 20 real UAE coaches, free, stopping before research. No spend,
nothing sent, nothing escalated. It works, and the run changed one thing.

```
TIER 0:  10/20 sites read free in 35s
OWNER-CHECK: 4/20 sites never mention the lead
RESOLVE: VALID, 20 identity(s), 49 channel(s)
LEDGER:  no duplicate fetch: every (lead, url) retrieved once
```

**D22 holds on real data rather than by assertion.** `resolve` added zero
retrievals to this batch — the list carried no link-in-bio pages — and the
ledger says so itself rather than it being a claim in a docstring.

**The finding: `20/20 lead(s) have at least one confirmed channel` was true and
said nothing.** Every row arrived from an enrichment vendor carrying a LinkedIn
URL whose slug IS the person's name, so rule 2 fired on all twenty. That
statistic measures the vendor, not the lead, and it will read 20/20 on every
Apollo-shaped list this machine is ever given. As the headline it would have
been quoted into a batch brief as evidence of something.

The number that discriminates is what a lead's **own pages** link, because that
is the part nobody chose in advance:

```
channels linked from their own site:  12 confirmed · 9 absent · 8 unknown
9 of 29 belong to somebody else (31%), or 9 of 21 among the ones we can judge
```

`report()` now leads with that and keeps the confirmed-lead count one line down,
labelled with why it flatters. The lesson generalises past this stage: a metric
computed over data somebody else assembled is measuring their pipeline.

**What the absent verdicts actually caught**, and this is the F7 case exactly:

- **Rory Buck.** Company website `harrisonassessments.eu` — an assessment
  vendor, not his. Email `rory@icanswimfast.com`, a third domain. Every social
  the site links is Harrison's corporate account, so his YouTube, Facebook and
  Twitter all came back `absent` and `/company/harrison-assessments-international`
  came back `unknown`. Under P3 that is three scrapes not bought.
- **Lucy Russell.** Same shape against Cancer Support UK, a charity she
  facilitates for. Instagram, Facebook and Twitter all the charity's.
- **All six `/company/` pages** were genuinely different entities from the
  person — mumkincoaching, changeosity, seed-special-education-center,
  harrison-assessments, iicm, cancer-support-uk. Rule 0 earned its place.

The two ownership signals agree without being wired to each other: 3 of the 4
leads `OWNER-CHECK` flagged also produced `absent` channels.

**Tier 0 read 10 of 20 (50%)**, against 59% on the first batch. 18 of 58
retrievals errored. Two lists is not a trend, but this is the first time the
number has been recorded by the machine rather than by hand.

**Still missing, and it is what P3 is gated on.** This run stopped before
research, so `data/runs/` has *still* never recorded a `li_posts` fetch. The
duplicate P3 exists to remove has never been measured, `hook_yield` and
`null_hook_rate` have no number, and D21's reversal condition is untested —
nobody knows whether the leads with no confirmed channel are the same leads that
produce no hook. If they are, declining to spend on them is free. If they are
not, `plan` should not gate on ownership at all, and that is much better learned
before it is built.

**What to do next:** build `plan` and `select` additive and switched off, the
way P0, P1 and P2 all arrived — `hook-worker` keeps fetching, `select` runs
alongside and its choice is recorded rather than used. Then one real batch
produces both numbers at once: the current `DUPLICATE li_posts` line, and
whether `select` would have picked the same hook without fetching. Flipping it
after that is a one-line change against evidence instead of an argument.

## 2026-08-01 (P2) — the machine says who a row is actually about

Built P2 of `docs/proposals/2026-08-01-hook-retrieval.md`: `resolve`, plus the
two bugs found sitting underneath it. Additive like P0 and P1 — nothing consumes
an Identity yet, the batch skill runs it and quotes it and hands it to nobody.

**The number this is for: ~40 of 151 rows on the first real batch pointed at the
wrong person.** Parked domains, name collisions, a coach's training school, an
Ohio retreat house, a Dutch tech-news site. Three separate things noticed — a
note at intake, an OWNER-CHECK line after the site read, and each agent
improvising — and all three were advisory prose that no data structure carried
forward. So every bad row was found by a worker, one at a time, after the money
had been spent. `outbound/resolve.py` is those same two free checks with a type
on them: one `Identity` per lead, one `Channel` per place they might be
reachable, each carrying `confirmed | absent | unknown` and the evidence that
settled it.

**Advisory is right for a kill and wrong for a purchase.** That distinction is
the whole stage. A false kill is permanent and invisible, which is why `unclear`
passes the floors and why nothing here drops a lead. A false *purchase* costs
one call and is recoverable, so that is what a verdict may gate — in P3, when
`plan` exists. Recorded as D21, and there is a CLI test asserting exit 0 when
every channel is `absent`, because exit 1 there is the natural mistake.

**`unknown` never means the tell said no.** A handle mismatch is the only path
to `absent`. `handle_of` returns `""` for an id that cannot carry a name, so
`youtube.com/channel/UC1a2b3c` is `unknown` rather than a false negative — it
folds to `ucabc`, and a naive port of the intake note would have called that a
name mismatch and filled the report with them. `_profile_name_notes` now
delegates to it and inherited the guard it never had.

**Two bugs found on the way in, both fixed first, in their own commits.**

- **`_SOCIAL_RE` was harvesting the Meta pixel.** The facebook and instagram
  patterns were bare `[\w\-.]+` after the host and `_harvest` takes the
  leftmost match on raw HTML. A pixel snippet and an embed sit in the `<head>`;
  the social bar sits in the footer. Measured on real markup:

  ```
  facebook   -> https://facebook.com/tr     the pixel
  instagram  -> https://instagram.com/p     an embedded post's permalink
  ```

  Wrong in `sites.json` and wrong in every worker prompt built from it, on any
  lead running ads. Building a typed ownership verdict on that input would have
  scored `facebook.com/tr` as `absent` and read it as a name collision.

- **`dedupe` was indexing podcast hosts on the wall.** `spotify.com` was not in
  `_NON_IDENTIFYING_HOSTS`, so two coaches with Spotify shows collided — the
  exact linktr.ee incident documented three lines above that frozenset, latent
  on a second host list. The two lists are now one.

**And `tests/test_fetch.py` was running seven of its thirty tests.** The
`if __name__ == "__main__"` block sat at line 108 of a 396-line file, so a
standalone run defined and ran the first seven, exited, and printed
`0 failure(s)`. Every `check_owner`, ledger and escalation-plan test below it
was never reached. Moved to the bottom; eleven tests take a pytest fixture the
runner cannot supply and are now named as SKIP rather than silently absent.

**Podcast hosts are a platform now (F9).** A Spotify show in the website column
used to be treated as an own site — a JS app that returns 200 with no text,
which routes it into the *render* escalation, the most expensive rung there is,
on a page that can never yield anything. `classify_site` matches host or
registrable domain, because `registrable_domain("podcasts.apple.com")` is
`apple.com` and keying on the domain alone would have labelled every Apple URL a
podcast. Deliberately excluded: `carrd.co`, `about.me`, `solo.to`, `linkin.bio`,
`many.link`. A real coach's website can be `sarah.carrd.co`, and calling it a
platform would take its text out of `sites.json`, which every research worker
reads. A podcast host is never somebody's own site; those are.

**Link-in-bio pages are read at last (F8).** `normalize` has been routing
linktr.ee into `other_urls` since intake was written, with a comment recording
that dropping them was a real bug — and `batch_fetch` targets `site_url` and
nothing else, so no stage ever read one. A linktree that names the coach vouches
for every channel it lists, which is the cheapest attribution in the machine.
The page is kept verbatim as an `Observation`, because once retrieve-once holds
nothing reads it again and reducing it to a list of links would be F2 committed
fresh by the stage written to end it.

**`resolve` runs after `fetch`, and that is D22.** The proposal's Part 5 diagram
puts it first. That diagram has no `fetch` stage at all — tier 0 is absorbed
into a later phase there — so resolving first in the machine as it stands means
reading each homepage and then reading it again seconds later: 89 duplicate
`(lead, url)` pairs on the first batch. `ledger.duplicates` would name every one
and bury the single `DUPLICATE li_posts` line P0 exists to expose. A signal
people are trained to scroll past is worse than no signal. Written as a pure
function with an injected fetcher, so when tier 0 moves into `observe` the
caller changes and none of the logic does.

Also promoted `fetch._read_key` to public `fetch.lead_key`, and put
`owner_match` into `sites.json` — it existed only inside a printed line, so the
one ownership fact the machine computed died with the terminal. The sites.json
loop variable was called `slug` and never was one; a `resolve` joining on the
actual slug would have missed every lead with an email address, quietly.

**What to do on the next real batch:** run `resolve` after `fetch` and read the
`RESOLVE:` line against `OWNER-CHECK`. The question P3 needs answered is whether
the leads with no confirmed channel are the same leads that produce no hook. If
they are, declining to spend on them is free. If they are not, D21's reversal
condition has already fired and `plan` should not gate on this at all.

## 2026-08-01 (P0 + P1) — the machine can finally say what a fetch cost

Built the first two phases of `docs/proposals/2026-08-01-hook-retrieval.md`. Both
are additive, neither changes how a hook is found, and that is on purpose — the
proposal's own Part 9 argues P3 cannot be judged without a baseline, and there
was none.

**The two numbers that already existed and were thrown away.**
`_require_cost_approval` computed the only dollar figure in this repo, compared it
against the $0.10 threshold, and returned `None`. So the estimate survived *only
inside the exception raised when the gate refused* — every run cheap enough to be
allowed went unpriced, which is every ordinary run. And `batch_fetch` computed an
`elapsed_secs` for a whole batch, printed it in the report line, and dropped it;
that was the only clock in 18,000 lines.

Both now land in `data/runs/<batch>.jsonl`, one JSON line per fetch, written as
the run proceeds so a batch that dies in stage 3 still leaves its accounting.
`run_actor` is where the Apify half goes, being the one chokepoint all ten
wrappers pass through and the only place a duration can be measured. Failed and
empty runs are recorded too: a paid run that came back with nothing still paid
for its container boot, and it is the most interesting line in a batch that
produced no hooks.

**Three defaults here are the opposite of the rest of this repo.**

- `ledger.append` **never raises.** Everything else fails closed. An observer
  that can halt the run it observes is worse than no observer.
- `ledger report` **never exits 1**, not even on a duplicate fetch. Reporting one
  is the job; blocking belongs to the stage that removes it. A gate that can halt
  a real send file over an accounting line is a gate people learn to route around
  — the same reason `doc-check` runs with the tests and not with a batch.
- A **missing** ledger is exit 2. The wall's asymmetry one stage over: a missing
  wall must never read as "nobody has been contacted", and a missing ledger must
  never read as "this batch cost nothing".

**F1 shows up on the very first report.** `research-worker` and `hook-worker`
both run `li-posts` on the same profile, on the one actor that provably cannot be
batched, and `purpose` is what makes that checkable — a second fetch of the same
`(lead, url)` is a DUPLICATE unless it is a verification. The verifier's fetch is
exempt rather than merely tolerated, because a verifier reading a cache would be
certifying that we copied a string correctly rather than that the words are on
the page.

**The duplicate is left in place.** Removing it before there is a number showing
what it costs removes the proof. That is what P3 is for.

**P1 is the `Observation`.** Research keeps a `_source` *string* per verdict, so
the post that settled `active_recent` — the exact material a hook is made of — is
read once, reduced to a boolean, discarded, and paid for again a stage later. An
observation is that post, kept, verbatim. `python main.py observe` gates it, and
a `Research` object now carries them through the same call.

The check that turned out to matter most is `retrieved_by`: it is validated
against the live `ACTORS` map, so an observation cannot claim a rung this machine
does not have. A record of a fetch that did not happen reads exactly like a real
one to everything downstream.

**Nothing consumes observations yet**, and `hook-worker` is untouched. What
exists is the contract and its gate, so the records being accumulated were
schema-checked when they were written rather than found unusable by the stage
that finally needs them.

**Two existing tests changed rather than being worked around.** Both pinned that
`approved=True` short-circuits before estimating — which is precisely the
property that left the signed-off, expensive runs unpriced. They now pin that it
still passes and still prices.

**`data/runs/` is committed**, unlike `out/` and `work/`. Those hold one batch's
artifacts; this is the record of what a run cost, and its whole value is
comparing one batch against the last. `OUTBOUND_LEDGER_ROOT` redirects it, which
is what the suite uses, so a test of the plumbing never lands inside the record
of what a real batch cost.

**And `doc-check` learned about `docs/proposals/`.** The proposal itself had to
drop the backticks off every command it named to get past the gate, and said so
in its own preamble. The directory now joins the journal and `docs/claude-docs`
in `EXCLUDED`, with its reason reported on `skipped`. The cost, stated rather
than discovered: a proposal citing a module is no longer told when that module
moves.

**What to do on the next real batch:** run `python main.py ledger report --leads
<n>` at the end, paste the first line into the journal, and commit the jsonl next
to the wall. That is the first honest per-batch cost figure this machine has ever
produced, and the number P3 gets judged against.

## 2026-08-01 (hook retrieval) — a proposal, and the number that reframes it

Haytham: the hook stage is the bottleneck — expensive, slow, and it searches
platforms where no good hook exists. Cut retrieval cost hard without losing
personalization. Reconstruct the current machine first, then propose. Treat
every idea in the brief as a hypothesis, not a requirement.

Deliverable is **`docs/proposals/2026-08-01-hook-retrieval.md`**, a proposal
only. Nothing implemented. Mid-session he added the rule the whole document now
turns on: *information is retrieved exactly once per lead, and every downstream
stage consumes structured observations rather than re-fetching — unless it is
explicitly verifying.*

**The number worth carrying forward: the first batch spent ~$1.36 of Apify
across 155 leads, about $0.009 a lead.** The hook stage is not expensive in
dollars and never was. It is expensive in *agent passes and wall-clock* — three
retrieving agents per lead, two of them searching for evidence, sharing nothing.
Anyone who reads "reduce retrieval cost" as a billing problem is optimising a
rounding error. The proposal says so in Part 11 rather than quietly delivering a
percentage nobody can feel.

### What the reconstruction turned up

- **The same LinkedIn posts are fetched twice per lead.** `research-worker` runs
  `apify li-posts <url> --max 5`; `hook-worker` runs the same actor on the same
  profile with `--since 3months`. Different flags, so even a command-keyed cache
  would miss — and `li_posts` is the one actor proven un-batchable, so it is the
  most expensive call in the machine, made up to twice.
- **Research keeps a `_source` string and throws the post away.** There is no
  observation type in this repo. The machine pays for a post, extracts one
  boolean, discards the text, and pays again.
- **The hook is the only consequential artifact with no mechanical gate.**
  Research has a schema command, copy has two, drafts have the linter and
  `export --anchors`. The hook has an agent and prose — against this machine's
  own stated rule to prefer a mechanical check to an agent, always.
- **The brief's premise that LinkedIn is searched first is already false.** Both
  hook files were reordered on 2026-07-31 to put the About page at rung 1, and
  both carry the comment explaining it. Credit where due.
- **But rung 1 is poisoned one file over.** `hook-verifier` refutes anything that
  could go unedited to another coach in the same segment, and generic About prose
  is exactly that — so the cheapest rung produces the observations most likely to
  be refuted, and the ladder gets walked to the paid rungs anyway. The fix is not
  reordering; it is narrowing rung 1 to a named framework or a founding story.
- **Link-in-bio pages are classified as research targets and never fetched.**
  `normalize` routes linktr.ee and five siblings into `other_urls`; `batch_fetch`
  only targets `site_url`. The cheapest identity artifact there is, discovered
  and discarded. There is also no podcast host pattern anywhere, and podcasts are
  rung 2.
- **`yt_channel` feeds `audience_size`, which the ICP captures and never gates
  on.** A paid actor wired to a field that by design changes no decision.

### The shape proposed

`resolve` (free identity resolution) → `plan` (mechanical routing with a cost
model, replacing search order as prose in two markdown files) → `observe` (the
one retrieval pass) → `select` (ranking, no fetching) → the verifier, unchanged
and still fetching live.

**Four of the brief's six abstractions accepted, two rejected.** "Observation
Extractors" as separate agents is rejected outright — an LLM pass per platform
per lead is exactly the cost being cut, and it would make the pipeline more
expensive while looking more principled. "Retriever" as a single stage is
rejected in favour of splitting the decision from the act.

### The thing that outranks the architecture

**Nothing is measured.** No per-lead cost, no hook source platform, no runtime
persisted. `Tier 0 Rate` and `Apify Cost USD` exist as Batches fields that only a
model filling them in by hand ever populates. Every cost claim in the proposal
had to be reconstructed from a hand-written journal entry.

So the migration puts instrumentation first and the behaviour change third, and
the metrics section admits the one gap no retrieval architecture closes:
**Smartlead owns replies, there is no API key, and this repo cannot compute any
part of cost per booked meeting past export.** `Hook Type` has been a CRM select
since the beginning, described in the base as a testable variable against reply
rate. The variable exists. The test has never been run.

**Not decided, not implemented.** `doc-check` passes with the proposal scanned —
which needed proposed commands kept out of backticks, since that gate assumes a
doc describes what exists and has no category for a proposal.

## 2026-08-01 (the fix list, worked) — the copy bank stops being sentences

Haytham: take another look at every problem the first batch produced, engineer
better fixes for the ones already patched, and finish the rest. Four things
named outright — one email verifier, a **permanent** copy-bank fix, cheerio as
a fallback, and actually use Instagram and search.

**The one that mattered.** The post-mortem's own verdict was that every line
the drafting model wrote passed on its second read, and what killed two of
three send-ready leads was defects in the hand-written bank and in how its
lines pair. A drafter cannot touch either, so the lead spent its one rewrite
pass on a problem it structurally could not fix. The previous fix was editing
the offending line in Airtable. Per lead. Forever.

So the identity beat is now **claim-scoped**: each line declares which row of
`results.csv` it draws from, which columns, and whether it may name the
segment, and the drafter writes the sentence. See `docs/spec/07-decisions.md`
D19 for the decision and what would reverse it. The thing to know here is that
this was already two-thirds true — `check_bridge` fails 21 of the 33 bank
lines, so the model was already composing that sentence on most leads and
nothing checked what it claimed.

**Filling in 33 claims found four defective lines, three more than the
post-mortem knew about.** `id-fit-2` had been shipping "closed AED 36k in 6
weeks" against a Fitness row whose close_period is 45 days — it passed every
check there was because 6 happens to sit in `OFFER_NUMBERS`. `id-any-4` counted
"the last 4 coaches", which is not a count of anything. `id-lead-1` kept its
flourish. And `id-lead-4` asserted a corporate decision-maker about the
Leadership row, whose buyer is an individual — the same defect as the flourish,
less obvious. The post-mortem had also named the wrong line: `id-life-1` was
fixed at `3981108` and the live flourish was `id-lead-1`.

**`results.csv` gained a column.** Two lines said a coach "landed their first
client in week 1" and the nearest column was `first_meeting_days`, a different
event. Haytham confirms a client really did sign in week 1, so the table was
short a column rather than the lines being wrong. `first_client_days` is blank
on six of eight rows, and blank means nobody measured it — a Claim naming a
blank cell is refused rather than resolved to zero.

**Open, for a new client result rather than for code:** Leadership has no
corporate result to point at, so after the `id-lead-4` fix its only
corporates-facing identity line is a plain matched-meetings one.

### The rest of the register

- **The seam check went in the linter, not the deal.** My first instinct was a
  deal-time rule and the measurement killed it: `_resolve_echoes` can only swap
  the ps, identity and offer are both pinned, so it would have been a rule with
  no legal repair on a fifth of pairs. Because identity is now authored, the
  drafter always has a repair — and it runs the linter on itself, so a
  collision costs one word in the first pass and never touches the budget.
- **The ps bank was monotone because the linter allowed one move.**
  `CLAIM_TOKENS["ps"]` named "a costless no" and `validate` rejected anything
  else, so a constraint nobody decided read as a choice somebody made. One
  candidate line did not survive: a ps promising no follow-up would be false
  the moment a batch is uploaded, because Smartlead owns the sequence steps.
- **A verifier outage is a property of the RUN.** `batch_health` exits 2 when a
  whole batch comes back inconclusive, which is never a real address pattern.
  That is what would have caught the 40 leads.
- **The escalation plan now names a vetted actor key**, so `fetch --escalate`
  runs it through the same gate and the same exit 3 as everything else. Both
  site actors are compute-billed with no `pricingInfos`, and the gate now says
  that rather than "pricing unavailable" — one of those is worth retrying.
- **Tier 0 is concurrent.** It was killed twice by timeouts on 151 sites.
- **Two floors could not reject anything** and the ICP table did not say so.
  `is_coach` can now say no, narrowly. `uae_based` reads two haystacks, so a
  sentence about a past employer stops killing a real lead.
- **~40 of 151 rows pointed at the wrong person.** `OWNER-CHECK` names them
  before the money. Advisory, never a kill.

### What is still open

- **The joint hook+identity word budget.** `hook_room` is still measured
  against the reference line, so the prompt hands the drafter a length range to
  keep that honest. The clean answer moves `MIN_HOOK_WORDS`,
  `copy_sync._check_hook_room` and `_resolve_length`, and is a change of its
  own.
- **None of this has been run against a real batch yet.** Every check is
  verified against the lines and rows that actually failed, which is not the
  same as a batch reaching SEND.

## 2026-08-01 (first real batch) — 155 leads in, 1 email out, and why that is the honest number

Haytham dropped a 155-row UAE coach list and asked for a clean Smartlead file.
The machine ran end to end for the first time. **One email reached SEND.** That
number is not a bug report, it is the gate working, but the run surfaced enough
that the fix list below matters more than the file.

### The funnel, measured

```
155 raw -> 151 clear (2 already contacted, 2 in-batch dupes; no WARM hits)
151 -> 106 pass the three floors (18 uae_based, 11 is_coach, 14 active, 2 both)
slice 1 of 16 taken to the end: 8 draftable -> 3 hooks VERIFIED -> 1 SEND
```

**Tier 0 read 89 of 151 sites free (59%).** That is the number the batch skill
says nobody has published for this niche. Record it. The other 62 were settled
by the workers' own WebSearch/WebFetch, not by Apify — the generic
site-crawler escalation plan was deliberately not run, because that actor is
not in the vetted set and the free tier-1 fallback covered it. Whole-batch
research cost about **$1.36 of Apify** (26.4% -> 31.1% of the monthly cap).

### Two email-verifier outages, one of them silent

`account56/email-verifier` returned `{"status":"error"}` for **every** address,
valid or not — an actor fault that `classify_verification` correctly reads as
WARN. Correct, and useless: the first 40 leads all came back WARN, which is
indistinguishable from a batch of genuine catch-alls. Added `email_alt`
(`michael.g/email-verifier-validator`, Haytham-named) as a fallback, then, on
his instruction, stopped calling the primary at all —
`_PRIMARY_EMAIL_ACTOR_DOWN` in `audit/apify.py`. **Flip it back when account56
recovers.**

The documented ZeroBounce fallback **was not actually available**:
`getcredits` returns `{"Credits":"0"}`. So during the outage window the machine
had no working verifier at all and said so only as WARN. Post-fix the same
addresses resolved to 69 pass / 68 warn / 4 fail across 151.

### Batching: two of three, and the third is a trap

Haytham: stop calling actors one lead at a time. `linkedin_profile()` and
`verify_emails()` now take a list and run once for a whole slice (new
`email-verify-batch`; `apify li-profile` takes many URLs). `linkedin_profile`
correlates results back per URL so one dead profile does not blank the rest.

**`linkedin_posts` must stay one call per profile.** Tested directly: two
`targetUrls`, `maxPosts: 10`, and all ten posts came back from ONE profile and
zero from the other. `maxPosts` is a budget shared across the run, not a
per-profile cap. Batching it would silently starve most leads of post data,
which reads downstream as "no recent activity" — a false `active_recent` kill
and a hook search that never sees what is there. Worth more than the container
boots it would save.

### The list lied, constantly

Roughly **40 of 151** leads carried an identity or site mismatch: the given
`site_url` or LinkedIn URL belonged to an unrelated person or company (parked
domains, name collisions, a coach's training-school site mistaken for their own
practice), or the current LinkedIn placed them in Saudi, Albania, Panama,
Egypt, India, Malaysia, Romania, the Netherlands or the US while the row said
UAE. Every override was independently re-sourced. **Treat any single field on a
purchased list as a hypothesis.**

### `qualify`'s `is_coach` check can never say no

It keyword-matches "coach" and structurally only returns yes/unclear. Workers
in at least five slices had to override it by hand with sourced evidence — a
Bacardi retail supervisor, a flydubai cabin crew member, a Middlesex lecturer,
an airline CEO whose goalie coaching is a stated hobby. The floor is doing
nothing on its own. Either it gets real logic or the docs should stop calling
it a floor.

### What actually blocked the drafts

This is the finding worth the session. Across three leads and six draft/verify
cycles: **every drafter-written line passed on its second read.** The recurring
blockers were the hand-written bank lines and, worse, their *pairings*.

- `id-biz-3` garden-pathed: "the last business coach in Dubai" read as *the
  only one left*. Fixed in Airtable (added "I worked with", matching
  `id-health-3`). The re-draft then reached **SEND** — the fix demonstrably
  worked.
- `id-life-1` ended on "all with prospects ready to say yes": an unfalsifiable
  flourish, and sales-desk register against a psychology-based coach's own
  voice. Replaced with "and 3 of them signed". **The replacement may have
  traded one flaw for another** — a later cold read called the result a
  three-number proof stack (8 / 5 weeks / 3). Unresolved; `id-life-4` (Abu
  Dhabi, two numbers, person-turn built in) was independently recommended twice
  as the better line for that segment.
- **Seam collisions are systemic and unchecked.** `id-career-3` ends "...worked
  with here." and `b4-02` opens "Real people here," — four seconds apart, each
  line fine alone. Measured across the bank: **14 of 132 identity->offer
  pairings (11%) repeat a distinctive word across the seam** (here, people,
  this, actually, meeting). Nothing catches this: the linter is per-line, and
  `deal` does not look at what a line sits next to. Roughly 1 lead in 9 will
  draw one and burn its rewrite pass on it.
- `cta-01` ships verbatim as the "good example" in
  `references/critical-failures.md`. Fine once; a tell if a reader sees two.

### The rewrite budget is spent on things the drafter cannot fix

A lead gets one rewrite. When the defect is in a bank line or a bank *pairing*,
the drafter cannot touch it, so the lead burns its pass and holds anyway. That
is how two of three send-ready leads died. The one-rewrite rule is right for
drafter error and wrong for copy error; they are not the same failure and
should not share a budget.

### Also worth knowing

A hook-worker overstated a lead's role ("ran the workshop" when his own post
said he was an invited participant) and the hook-verifier caught it on the
re-fetch. Another claimed "this month" for a 30-day-old comment; also caught.
Both refutations were correct. The independence is earning its cost.

Three leads produced **no hook at all** after a second pass that searched
Instagram and the open web as well as LinkedIn: one has a private Instagram,
one has no discoverable IG and a dead site, one is unfindable behind same-name
collisions. Null is the right answer and the workers gave it without stretching.

### Shipped this session

- `audit/apify.py`: `email_alt` fallback + `_PRIMARY_EMAIL_ACTOR_DOWN`;
  batched `linkedin_profile`; `linkedin_posts` documented as un-batchable.
- `main.py`: `email-verify-batch`; `apify li-profile` takes many URLs.
- Airtable Copy Assets: `id-biz-3` and `id-life-1` rewritten (both carry their
  reason in the Notes field).
- `out/leads.csv` — one lead, Chris Lake. Read `out/preview.txt` before upload.
  `wall-add` and `copy-usage` are NOT run; they wait on an actual upload.

The remaining 105 qualified leads are researched and un-drafted. Their research
lives in `work/research-all-151.json` (gitignored, container is ephemeral — it
was handed to Haytham directly).

## 2026-07-31 (email length) — the hook pays, so stop charging the copy

Haytham asked who pays for a long email. The answer was the hook: four of five
beats are drawn, so the only elastic text is beat 1. Then two bugs and a bad
rule fell out of measuring it.

**`_check_hook_room` was undercounting by three words.** It summed the four
drawn lines. `assemble_body` also puts a greeting and a sign-off into the body
`check_voice` counts, and it did not know about either. So it read the live bank
as leaving **13** words for a hook when the real figure was **10** — under its
own 12-word floor. The one combination it existed to catch was going through,
and would have surfaced downstream as a too-long draft, blaming the hook instead
of the lines that squeezed it. Today's earlier entry saying "hook room is back to
14" was really 11.

**Two word counters that disagreed.** `lint.check_voice` counts
`\b[\w'-]+\b`; the allocator's guards used `str.split()`. A separated figure is
two words to the first and one to the second, and `_UNSEPARATED` *requires* the
comma form on any four-digit currency amount. Latent — every live line writes
"AED 77k" — but armed. Now one `lint.word_count`, used everywhere.

**The rule itself was wrong, and that is the part worth keeping.** Requiring the
longest line in every beat to coexist made length a *copy* problem: the only
available fix was to trim a hand-written sentence until it read like a machine
wrote it. Haytham's objection, and he was right — measured it after: **6 of the
2,112 combinations** were ever too tight. The bank was being held hostage by
0.28% of draws.

So the constraint moved to where the combination is chosen. **`_resolve_length`
refuses to deal a set with no room for a hook** — swaps the ps, or the ps and
the cta, exactly the way `_resolve_echoes` already handles two beats repeating a
phrase. That function's own docstring had named `_check_hook_room` as the same
principle; it just had not been applied. Identity never moves: it is matched to
the lead's segment, which is what the 70/30 ratio exists to buy. Lines are never
edited.

Runs on **both** paths. `draw()` needed it more than `deal_batch` did — a
per-lead hash has no batch to spread against, and `outbound-draft` is the last
place anyone would look for the cause. Over 4,000 single-lead draws: 10 repaired,
0 short.

`_check_hook_room` now asks the only length question a swap cannot answer: **can
this line be dealt at all**, paired with the shortest line in every other beat.
A line that fails that is dead copy — it draws a weight and never reaches a
reader, which is what `ps-01` was doing under the echo rule.

**The drafter is handed `hook_room` per lead** instead of discovering it by
rejection. A drafter that knows it has 14 words writes 14; one that does not
writes 20 and gets refused. `deal` prints the range across the batch, a `LENGTH`
line when it had to move a beat (the weight drift is real, so it is said rather
than absorbed), and a `WARN` when no legal swap existed.

Live bank after all of it: hook room **12 to 36** words, nothing trimmed, no line
rewritten. 486 tests green, doc-check clean.

## 2026-07-31 (explainers) — two pages for people who have not read any of this

Haytham: "I need to visualize where everything is, and how the machine works
end-to-end", then "a one pager for the offer, something anyone can understand,
someone who isn't me can understand". Both now live in **`content/html/`**, a
new directory whose whole purpose is pages meant to be handed to a stranger.

**`content/html/system-map.html`** — the repo map, the eleven-step run from
intake to `wall-add`, every fail-closed gate with its exit code, the five beats,
the three worker/verifier pairs, and the authority table. Everything on it is
read out of the code or the CSVs rather than restated from a doc, which is the
only way it stays true: the counts (20 commands, 45 copy lines, 104 wall rows,
17 test files) came from the parser and the files, not from `CLAUDE.md`.

**`content/html/offer.html`** — the money model with the vocabulary removed.
No attraction offer, no decoy, no client-financed acquisition, no ICP, no
BAMFAM. It opens with six questions answered in a box, and it ends with the
four things that are honestly unsold or untested, because a page that hid
those would read as a pitch.

**Both are first person.** They describe what Haytham does, so they say "I".

### The thing worth knowing next time

**`content/html/` is outside `doc-check`.** `SCAN_GLOBS` is `docs/**/*.md` and
`.claude/skills/**/*.md`, plus `CLAUDE.md` and `README.md` by name — so nothing
under `content/` is scanned at all. That is why `offer.html` may carry prices
without breaking the rule that `docs/spec/03-offer.md` owns them.

Read the consequence rather than just the fact: **these pages are not gated.**
A price that moves in `docs/spec/03-offer.md` will not fail anything here, and
the drift is invisible until somebody hands the page to a person. The page
names `03-offer.md` as its authority in the footer, which is the doc-layer rule
applied by hand where the checker cannot reach. If these pages get more numbers
in them, that is the moment to add `content/**/*.html` to a checker rather than
to keep trusting the footer.

### A rendering bug worth naming, because the class of it recurs

The first draft of the offer page put one word on every line under "The order
it gets built". `ol.steps li` was a CSS grid with two declared columns, and its
children were an inline `<b>` and loose text — so the browser made **every word
its own grid item**. Grid and flex containers silently wrap bare text in
anonymous boxes; a container with `grid-template-columns` therefore needs all
of its children to be real elements. Both pages now do, and a sweep over every
`grid-template-columns` rule confirmed there is no second instance.

---

## 2026-07-31 (copy provenance) — Airtable owns the lines, and the fallback says so

Haytham: make Copy Assets the source of truth for copy, not some outdated CSV in
the repo. The ladder already preferred Airtable, and the key is set, so the live
path was working — `CopyBank.load()` returned `source: airtable`, 45 lines, and
the committed CSVs happened to match it exactly. The problem was that none of
that was **guaranteed or visible**.

`load()` fell through on three different failures and swallowed all of them into
the same `except Exception: pass`:

1. **No key.** Ordinary, and the CSVs are the right answer.
2. **Unreachable base.** Also ordinary. Also the right answer.
3. **A live edit that fails the linter.** Not ordinary at all. Airtable is
   reachable, somebody's edit is live there, `validate` refuses it, and the bank
   silently returns the previous copy — so the edit **looks applied** and the
   whole batch ships on the old lines. This one is drift, not an outage.

All three printed nothing. A batch could be drafted entirely from month-old copy
while the operator believed the table was in charge, and the only way to find out
was to read the emails and notice a sentence they thought they had changed.

**`CopyBank` now carries `reason` and `rejected`.** Every rung below the first
records why it was taken; `rejected` is non-empty only for case 3, which is what
makes the two defaults separable. `status_line()` is one quotable line naming the
source, printed by `deal`, by `anchors` when it isn't live, and by `export
--rebalance-ps`.

**`python main.py copy-check`** is the gate: live lines pass the linter, and
`copy/*.csv` still matches them. Exit 1 on either, exit 2 when it could not look.
It is the reader to `copy-sync`'s writer and writes nothing itself, so it is safe
at the top of a batch and again after a fix — which is where the batch skill now
runs it.

**`deal` blocks, with one override and not two.** A rejected live edit exits 1
with no flag: the fix is one line in Airtable and nothing here can do it. An
unreadable table exits 1 too, but `--allow-cached-copy` accepts the cache
deliberately. The cache is not unsafe — nothing reaches it without passing
`copy_sync.validate` — it is merely possibly stale, so the rule is that using it
must be a decision somebody made rather than a thing that happened. That is the
same split `.claude/hooks/schema_drift.py` makes, arrived at from the same place:
real drift is cheap to fix, an outage must not be able to halt work on its own.

Three things worth not re-deriving:

**A missing `copy/_airtable.json` is not drift.** It is gitignored, so a fresh
clone never has one, and a keyless run falls to the CSVs — which the file
comparison just proved match the table. Failing there would fail on every clone
for nothing.

**The comparison is byte-for-byte, and the first version reported all four beats
as drifted with zero rows edited.** `write_csvs` emits CRLF, and reading a
committed file back through Python's universal newlines turns it into LF. Hence
`render_csv`, which is what the writer now writes, and a read with `newline=""`.
There is a test pinning the two together, because a check that always says drift
is a check people learn to ignore.

**No test asserts the committed CSVs against the LIVE table**, deliberately. The
suite does not reach the network — conftest pins `OUTBOUND_COPY_SOURCE=csv` and
the reason on record is that a suite going live fails on somebody else's Airtable
edit, which is not a code regression. `copy-check` is where that assertion
belongs: a person can act on drift, a red build cannot. For the same reason the
push hook was left alone — copy drift endangers a batch, not a merge.

`copy/results.csv` stays repo-only and is untouched by any of this. The lines are
voice and get tweaked; the results are audited evidence and should not be
casually editable.

## 2026-07-31 (the push hook) — running the live check where the key actually is

The schema check shipped an hour earlier had a hole Haytham spotted immediately:
it needs a key, CI has none, so the only path that runs automatically is the one
path that cannot look. His observation was that ~99% of his PRs are opened from a
Claude Code session — and a session has a key.

So `.claude/hooks/schema_drift.py` is a **PreToolUse hook on Bash** that binds the
check to `git push`, which is what opens or updates the PR and is the last point
before the mirror leaves the machine.

**It matches by substring, not by the hook's `if:` filter, and that is the whole
design.** `if:` uses permission-rule syntax, which is prefix-matched:
`Bash(git push*)` does not match `git add -A && git commit -m ... && git push -u
origin ...`, which is how a commit-and-push is actually written — it is how the
push that shipped the schema check was written, three hours earlier in this same
session. The filter would have been a gate that looked installed and never fired.
So it matches every Bash call and returns after one `in` test; nothing beyond the
interpreter is imported until a push is confirmed. Measured at 58ms on the fast
path.

**It blocks on drift and allows on could-not-run**, which is the opposite of the
fail-closed rule everywhere else here, and the exception is deliberate. Real
drift is one line to fix and nothing else catches it. But "Airtable is
unreachable" would hold every unrelated push in the repo hostage to somebody
else's outage, and a stale mirror endangers a *batch*, not a merge. That case
warns where a person sees it — loudly, never silently, or "it would have run if
it could" is back, which is the thing `--live` exists to kill.

Proved it fires rather than assuming: sentinel prefix on the hook command, a
harmless Bash call, read the sentinel, strip it. Also pipe-tested all six paths
(non-push, plain push, compound push, malformed stdin, no key, injected drift)
before wiring it into settings at all.

**Note for a future session:** writing this file was blocked by the auto-mode
classifier the first time — a new executable the harness runs automatically is
exactly the kind of thing that should need a human. Haytham switched auto mode
off. Do not try to route around that denial; explain and ask, which is what
worked.

## 2026-07-31 (schema drift) — the one authority that is not in this repo

Haytham asked where schemas are stored. The answer is that there is no
`schemas/` directory and there should not be: every schema here is Python,
co-located with the stage that owns it, and `research.schema_help()` generates
its field list *from* the dataclass rather than restating it. Smartlead's eight
columns are `outbound/export.py`'s `COLUMNS`; the CRM's option lists are tuples
in `audit/airtable.py`; the Copy Assets field mapping is `copy_sync.FIELD_MAP`.

**Two real cracks, and neither was fixed by moving files.**

**The Airtable tuples are a mirror of a schema this repo does not own.** Their
only freshness signal was a comment reading "Verified against the base schema
2026-07-31". Somebody adds a select option in the UI and nothing notices — which
inverts the reason those tuples exist, since they are there to catch a bad value
*before* the write fails at the CRM step, which happens after the email is
already in the upload file. So `doc-check` grew a tenth drift class, `SCHEMA
DRIFT`, fetching the live field config through the metadata API and comparing
both directions. It found nothing: all eleven select fields matched on the day
it was written. That is the point — it is a gate, not a repair.

Three scoping calls worth not re-litigating. It **runs when a key is set and
reports itself as skipped when there is not**, next to the journal exclusion and
for the same reason; CI has no key and must not fail every build on a missing
secret. **`--live` is an assertion, not a switch** — same shape as `copy-sync
--live`, because "it would have run if it could" is not a thing to rely on. And
**the test suite passes `airtable=False` explicitly**, for the reason conftest
pins `OUTBOUND_COPY_SOURCE=csv`: a suite that reaches the network fails on
somebody else's Airtable edit, which is not a code regression. `tests/
test_cli_failures.py` strips the key from the subprocess environment for the
same reason — before that, the suite behaved differently on a machine with a key
than in CI.

The mapping points each select at **the module that already owns its list**
rather than adding tuples. `Leads.Coach Type` had no mirror at all, so it is
pointed at `outbound/research.py` — adding one next to the others would have
made a fourth copy of a list that already existed three times.

**Which was the second crack.** `COACH_TYPES` is in `research.py`, `qualify.py`
and `copy_sync.py`, and nothing read them together. The first two are the same
list (research adds `""` for not-yet-known); the third is deliberately different,
swapping `Other` for `Any`, the generic pool — a lead *has* a coach type, a line
*targets* one. `SELLS_TO` is the same story across three modules. Now pinned in
`tests/test_qualify.py`, including the deliberate difference, so dropping `Any`
cannot read as a tidy-up and silently empty the pool unknown-segment leads fall
back to.

`docs/spec/06-state.md` gained the row and a section on why that one row needs a
check when the rest only need the rule: every other authority is in this repo, so
following the pointer lands somewhere that cannot lie to you. A browser-edited
field config has no diff, and a pointer cannot tell you it moved.

## 2026-07-31 (the spec layer) — defining docs, and a gate that keeps them true

Haytham wanted defining docs for the operation the way uae-track had them, "but
better and more robust this time, something that can't be affected by daily
changes", and supplied his Hormozi-built offer doc as the input.

**Went and read the old set first.** It is in git at `89bf58b^`: five numbered
files under docs/uae-track/. Four of the five rotted and one did not, and the
split is diagnosable rather than a matter of care. 01-crm-operating-spec held
Notion record ids and per-inbox send counts, so every CRM change was also a doc
edit. The offer existed as *two* files, 02-the-offer-first-five and
02-the-offer-gso-v2, so it forked instead of changing. 03-targeting had price
floors in prose, which is why commit `4fcc9d3` in this history is called "Sweep
the last stale prices and rename the guarantee everywhere". 04-the-outreach-method
grew RETIRED-dated sections inside a live doc. 05-the-named-fifty aged fine, and
the reason is that it stated a decision and its reason and held no value anything
else owned.

**So that is the rule the new set is built on**, and it is enforced rather than
requested: *a defining doc states a decision and its reason; it never holds a
value that something else owns.* Where a value lives in code, a CSV or Airtable,
the doc names the authority. `docs/spec/03-offer.md` is the one exception and is
declared the sole price authority, because a price is a decision and has nowhere
better to live.

**Eight files in `docs/spec/`** — 00-index (the contract and the post-mortem
above), 01-operation, 02-icp, 03-offer, 04-email, 05-pipeline, 06-state,
07-decisions. hook-rules.md and agent-orchestration.md stayed where they are and
are named as companion specs; they were already right.

**`python main.py doc-check` is the enforcement.** Nine drift classes: unknown
command, dead path, state in spec, unknown copy id, missing header, unowned
authority, stale allow, undocumented command, value drift. Exit 1 on drift, exit
2 if it cannot read the docs.

The ninth came out of the final read-through and is worth the note. 04-email
declares that it owns the word budget and states "67 to 95 words", and
`outbound/lint.py` holds the same two numbers. That is the right way round — the
doc decides, the code implements — but it means the number exists twice, which
is the exact situation the rest of the layer forbids. `check_word_budget` pins
them together, and deleting the sentence counts as drift too, so that is not a
way out. Deliberately one hardcoded pairing rather than a mechanism: a framework
for a single case is not honest until there is a second one.

### What the design got from running it by hand before writing it

Swept the real corpus first instead of reasoning about false positives, and it
changed four decisions:

- **Path resolution has to walk from the citing file up to the repo root.**
  `.claude/skills/outbound-draft/references/voice.md` cites
  `references/critical-failures.md`, which resolves against the *skill* root.
  Both simpler rules flag it, and a gate that fails on a clean checkout gets
  switched off in a week.
- **`rstrip`, never `strip`.** `strip(".")` turns `.claude/skills/` into
  `claude/skills/` and guarantees a false positive on a directory that is there.
- **`docs/journal.md` is excluded, and the exclusion is printed.** It names four
  deleted files today and is right to — its own convention says "a record, not a
  pointer, and it stays". Checking a log against today's code is a category
  error and the noise would train people to ignore the gate.
- **Commands are read from fenced blocks, paths are not.** Every command in the
  skills lives in a fence; fences are also full of `work/*.json` scratch paths
  and worked-example filler.

### Two bits of live drift it found immediately

- **`main.py`'s own docstring inventory had lost `fetch` and `facts`** — a
  hand-kept list three feet above the parser that has always had them. Fixed,
  and the check now covers that list too.
- **`outbound/__init__.py` said "Nine stages" over a list of eight.** Fixed.

And one on its very first run: 00-index cited the deleted uae-track filenames in
backticks, which is a claim that they exist. That produced a convention worth
keeping — **a backticked path is a claim the file exists; a dead file's name goes
in plain text**, because naming it is a record rather than a pointer.

### Where it is wired, and where it deliberately is not

- **The test suite, yes.** `test_the_repo_itself_passes` is what makes it a
  standing gate rather than a command someone remembers.
- **`outbound-batch`, no.** A doc typo must never be able to halt a real 50-lead
  run, because a gate that can do that is one people learn to route around.
- **The SessionStart hook, no.** Both hooks fail *open* by design; a fail-closed
  gate on a fail-open surface is either noise or a lie about its own contract.

46 new tests. Full suite **452 passed**. Two container notes for whoever hits
them next: `pytest`, `beautifulsoup4` and the rest of requirements.txt are not
preinstalled, and before `pip install -r requirements.txt`
`test_qualify_settles_activity_from_the_page` fails on a missing `bs4` with
nothing to do with any change. And editing a module and reverting it inside the
same second leaves a stale `__pycache__` that mtime invalidation misses, which
looks exactly like a check ignoring a fix.

### Then a README, and two things it exposed

Haytham asked for a repo README. The care needed was in giving it a job that
does not overlap START-HERE or the specs — a fourth "what is this" file is the
rot this whole branch fights. So it is the *repo* front page: quickstart, the
exit-code table, layout, environment, and where to read next. Everything about
what the operation IS points at `docs/spec/`.

Added `README.md` to the checked corpus, and it failed immediately on its own
layout block:

    main.py            the CLI — every command is a decision

which parses as the subcommand `the`, because commands are read from fenced
blocks. **The obvious fix — requiring a `python` prefix — is wrong**: the docs
really do write bare `main.py lint`, `main.py apify` and `main.py wall-add`, and
those would silently stop being checked. A false negative on real content is
worse than one on alignment. The fix is a single literal space before the
subcommand: an invocation has one, a column-aligned listing has many.

And the README's first draft stated "452 tests" in two places, which is a value
the suite owns and which was stale within ten minutes of writing it (454 now).
Cut, along with "lists all 19" for the command count. The rule catches its
author as readily as anyone else, which is the point of having it in code.

### And then CI, which was the hole under all of it

Flagged that there was no `.github/workflows/`, so nothing ran the suite on a
push — meaning `doc-check` only guarded a change if someone remembered pytest.
Haytham: add it. `.github/workflows/checks.yml` now runs on every push to
`outbound` and every PR.

Two choices worth the note:

- **`doc-check` is its own step**, even though `test_the_repo_itself_passes`
  already covers it. A docs drift should report as a named failing step printing
  the line it was built to print, not as a pytest traceback somebody has to read
  to discover the docs are stale.
- **`requirements-dev.txt` rather than a `pip install pytest` line in the YAML.**
  "What it takes to run the suite" is a fact about this repo, and a fact with one
  home does not drift. Putting it in CI config would have made the workflow the
  authority on a dependency, which is the thing this whole branch argues against.

Single Python version, 3.11, matching what the repo is developed on. A matrix
would invent a support policy nobody has decided; when one is decided it belongs
in `docs/spec/` first.

### Open follow-ups
- [ ] The offer's build order is a set of gates, and none of them is met yet:
      The First Five has never been sold. Everything on the NOT BUILT shelf in
      `docs/spec/03-offer.md` stays there until it is.
- [ ] `docs/spec/07-decisions.md` has 18 entries and each carries a reversal
      condition. None has ever been tested, so they are guesses about what would
      matter.

## 2026-07-31 (the journal) — cut back to the pivot

Haytham: the journal still carries junk from the old track going back to 07-16,
and this is a new system. Cut. **`docs/journal.md` went from 2,621 lines to
766** — every entry from 2026-07-30 back to 2026-07-18 deleted — and
`docs/journal-archive.md`, 574 more lines of the same, deleted outright. What
remains is the thirteen 2026-07-31 entries, starting at the rebuild.

What went was the funnel auditor's log: Gmail-state reconciliations, Loom
offers, finding-staleness gates, Notion migrations, `uae-tick` runs, a Sunday
send pause, price-discovery experiments. All of it about machinery that no
longer exists. Loading three of those at every session start was actively
misleading — the hook does not know a pipeline was deleted, it just serves the
newest blocks.

**Checked before cutting rather than after.** Of 1,868 deleted lines, exactly
one current file was named: `audit/apify.py`, twice, both on the 2026-07-20 bug
where an unresolvable Instagram handle came back as an `error` field inside a
200 response and `_lean()`'s allow-list swallowed it. That story is already
told in full inside `_raise_on_actor_error`'s docstring, dated, which is where
someone reading the code will actually find it. Nothing else in the deleted
span referenced a file that still exists. Git has the rest.

Two things in the standing guidance block were stale and are fixed: it said
**Notion** holds live state (it is Airtable), and it instructed future sessions
to move old detail into `docs/journal-archive.md`, which would have recreated
the file I just deleted. The rule is now condense in place. A hand-maintained
overflow file nobody loads is where detail goes to rot, which is most of what
the archive turned out to be.

The journal now states its own floor: it starts at the pivot and nothing before
it is coming back.

Also ran the pronoun sweep over what survived — the earlier pass deliberately
skipped the journal, and with it down to thirteen entries there was no reason
to leave ten leads called "she" in it. What is left quotes the word rather than
using it.

## 2026-07-31 (pronouns) — the docs called every lead "she"

Haytham, with a screenshot of `hook-rules.md`: it still says "her" and "she" in
some docs. It did, roughly 180 times across 30 files, and the sharpest version
of the problem is that **`mechanics.md` carried the rule against it.** "No
gendered pronouns in an identity line. It fires across a whole segment and
'her' is wrong about half the time. Use 'them'." That paragraph sat in the
middle of a file that addressed the reader as "she" in eleven other places. The
linter enforces the rule on the identity beat; nothing enforced it on the
instructions, and the instructions are what the drafter reads first. A doc that
models the default it bans is how the default gets written back into an email.

Swept every live surface: `hook-rules.md`, all five agents, both skills and the
four voice references, `CLAUDE.md`, `START-HERE.md`, and the docstrings and
comments in `main.py`, `outbound/` and `audit/`, plus the test fixtures. Not a
sed — "her" splits between possessive and object ("hands her back her own
sentence" needs *them* then *their*), and "she sells" has to become "they
sell", so it was per-instance.

What deliberately still says it:

- `lint.py`'s `GENDERED` regex, which has to name the tokens to ban them, and
  the `copy_sync` comment recording that 31 live identity lines once carried
  one.
- `test_lint.py`'s fixture, which must contain "her" or it stops testing that a
  gendered identity line fails. Verified both directions still behave.
- The rule itself, quoting the word.
- **`voice.md`'s "he/him", which refers to Haytham rather than a lead.** Left
  alone deliberately: that is his own self-reference in his own voice doc, not a
  default applied to strangers, and changing it was not what he asked for.
  Flagged for him to call.

Also renamed the `her-site.com` fixture domain to `coach-site.com` in
`audit/urls.py` and its test.

408 tests green. The four shipped copy banks were already clean — no gendered
pronoun in any of the 45 lines.

## 2026-07-31 (audit residue) — swept the repo for what the pivot left behind

Haytham: find any sign of the old audit track and get rid of it. Swept every
tracked file. Most of what the vocabulary grep turns up is legitimate and
staying: `audit/` is the surviving chassis and its module name is everywhere,
`lint.py`'s jargon regexes have to name "funnel" and "audit" in order to ban
them, `copy/identity.csv` says "my job is finding your next client", and the
`track` column in the dedupe wall reads "UAE audit" on all 104 rows because
that is true of those people. None of that is residue. Four things were.

(`docs/journal-archive.md` was spared here as a labelled archive, and deleted
later the same day when Haytham asked for the journal itself to be cleaned —
see the entry above.)

**`drafting-craft.md` was still teaching the dead offer.** `draft-worker` reads
it on every email, and every worked example in it sharpened a funnel-audit
finding: "49K people go through your flow and you keep none of them", "the flow
ends on a Google Drive link", and, flatly, *"Don't open with 'your funnel's
good.'"* Meanwhile `mechanics.md` bans the word funnel outright. A live
reference file was modelling language a live rule forbids. The rules are Harry
Dry's and transfer fine, so they are unchanged; the examples are now the hook,
the identity beat, the ten names and the close, and the conflict section says
what it must no longer mean. It used to mean showing them a problem; that is the
dead offer and `critical-failures.md` bans it.

**`extract.py` carried a `stale_candidate` flag nothing read.** Its own
docstring said so. It was the Pam pattern — a passed kickoff date still showing
on a page — which is a finding. `blog_byline` existed only to stop a publish
date being mistaken for one, and nothing read that either. Both gone, with the
launch-keyword, byline and copyright regexes behind them. Checked the one live
caller (`qualify.latest_activity_date`) against the old implementation on six
pages: **byte-identical on every shared field**, only the two dead keys
missing. The sort keeps the ordering fix that mattered (closest to today
first, so a thirty-cohort events archive can't push the newest date past the
truncation) and loses only the stale tiebreaker.

**Two pre-pivot analysis docs deleted.**
`nine-threads-and-phase10-correction.md` and
`outreach-system-vs-saraev-comparison.md` were not history, they were **open
fix-lists** — "G16 · Re-verify the finding before any offer *(new, P1)*",
"crm-gate offer fails if the finding has not been re-verified", "the five
changes, ranked by expected impact" — prescribing work on a pipeline that no
longer exists, against a `haytham10/Funnel-Auditor` repo and a Notion CRM,
pointing at a Part II and a `claude/fix-list-v2-post-phase10.md` that aren't
here. Read cold, they look like a backlog. Their load-bearing conclusion is
already distilled in `CLAUDE.md` and `START-HERE.md` (589 leads, zero; 4 of 9
read the finding and left; 0 of 9 replies reached a call), and git keeps the
full text.

**`uae-market-study-2026-07.md` kept**, with a note saying why. Its subject is
the market, not the dead offer, and the ICP rests on it directly: audience
decoupled from price, and a price floor that reads `unclear` on most of the
market. The 122 funnel walks that fed it are gone; the note says to read it as
a snapshot of the buyers, not of any process that still runs.

Plus stale pointers: `outbound/__init__.py` pointed at a `docs/the-machine.md`
that does not exist (it is `START-HERE.md`), `apify.py` credited a lesson to
`batch-audit` and `lead-processor` agents that are deleted,
`test_footprint_sourcing.py` still named Firecrawl as the live feeder, and
`test_email_verify_gate.py` ended on an empty `crm_gate send` section header.

What is left that names the old track is deliberate: dated notes in
`CLAUDE.md`, `START-HERE.md`, `agent-orchestration.md`, `draft_lint.py` and
`extract.py` saying what went and why. `audit/gmail_gethaytham.py` still
appears in one sentence, which says it was deleted. That is a record, not a
pointer, and it stays.

408 tests green.

## 2026-07-31 (li_profile) — back to harvestapi, and the gate it would have jammed

Haytham: use `harvestapi/linkedin-profile-scraper` for LinkedIn profiles, and
the two `apify/instagram-*` actors for Instagram. Instagram was already on
those two (split there 2026-07-18), so this was the LinkedIn half only.

`li_profile` now matches `li_posts` — both LinkedIn calls run through one
vendor. **The reason it left harvestapi on 2026-07-16 has not gone away:** that
actor enforces its own ~20-runs/month quota, independent of Apify billing, and
a batch hit it mid-run. Nothing here can see that quota. `account_limits()`
reads Apify's USD cap and knows nothing about a vendor's own counter, and the
cost gate won't catch it either, because a quota-exhausted run is cheap rather
than expensive. So it will surface the same way it did before: an actor error
on run 21. The profile call is optional by design (posts-first), so the answer
mid-batch is to drop it for the rest of the run, not to swap actors under a
half-finished batch.

**The swap would have silently jammed the cost gate.** harvestapi prices two
events, `profile` at $4/1k and `profile_with_email` at $10/1k, and flags
neither `isPrimaryEvent`. `_actor_primary_event_price_usd` infers a primary
event by that flag, falling back to the sole recurring event when exactly one
exists — two recurring events and no flag is precisely its give-up case. It
returns None, the gate reads None as "can't estimate", and **every**
`li-profile` call raises `APPROVAL REQUIRED` forever. Not a wrong price: no
price. Wrappers can now name their charge event outright (`event_key`), so the
estimate prices the mode actually being run rather than assuming the cheap one,
and `_pricing_cache` is keyed on (actor, event) — keyed on the actor alone, the
email mode would have been billed at the no-email rate. A named event that
isn't in the actor's pricing returns None rather than falling back to some
other event's price: a stale hint has to fail closed.

The two actors return different shapes, so `linkedin_profile` normalizes.
apimaestro nested everything under `basic_info` with an `email` string;
harvestapi is flat, splits `firstName`/`lastName`, puts addresses under
`emails` (each with its own deliverability verdict, so the picker prefers a
valid one and falls back to the first rather than to nothing) and the location
string under `location.linkedinText`. It has no `is_current` flag — a running
position reads `endDate.text == "Present"`, same fact. Callers see the same
keys they did before. `_raise_on_actor_error` now guards this path too; it
didn't before, so an unresolvable profile came back as an empty-but-valid one.

Verified live against the real actor, not just the stub: one profile pull
through `main.py apify li-profile` cleared the gate automatically and returned
the normalized record. 408 tests green (8 new).

## 2026-07-31 (last copy gap) — Executive/individuals filled

`id-exec-3`: *"The executives worth your time are already paying for help
somewhere. AED 44,000 of that went to an executive coach I found the meetings
for."*

An Executive coach selling to individuals had exactly one usable line
(`id-exec-2`), so the deal had to spill them to generic to stay under the
repetition cap. `id-exec-1` is corporate-framed — budget holders — and unusable
for a buyer paying for their own coaching. The new line frames the buyer as a
senior person already spending on help, which is what individuals-facing means
for this segment, and cites AED 44,000: a number neither other Executive line
uses, so two Executive coaches comparing emails see different proof.

**`thin_segments` is now empty.** Every segment/audience pool can hold its share
without repeating a sentence, for the first time since the bank was written.

400 tests green. The bank is 45 lines: 33 identity, 4 offer, 4 cta, 4 ps.

## 2026-07-31 (the corporate generic) — and the mirror bug it uncovered

Haytham: "write the corporate-facing generic identity line." Writing it was the
small half. Looking at why Rohit needed it found a worse bug pointing the other
way.

**The generic identity pool ignored `sells_to` entirely.** `_identity_pools`
took every `coach_type = Any` line regardless of audience, so an
individuals-facing coach could be handed "I get coaches in front of the people
who actually hold the budget" — corporate proof to a health coach whose buyer is
one person paying for themselves. That is the majority of this market, so it was
the more common direction of the same fault a reader caught on Rohit. The
identity beat's whole job is a matching reference group; a mismatched one is
worse than a generic one, which is the argument the ICP notes already make about
`sells_to` being collected rather than inferred.

Fixed: a line tagged for an audience is generic only WITHIN that audience.
Neutral (`any`) lines stay available to everyone, and a lead whose own
`sells_to` is unknown draws only from those — guessing the reference group is
exactly what an empty `sells_to` exists to avoid, so it must not be guessed here
either. Verified end to end on mixed batches of 11, 30, 90 and 200: no lead
receives the other audience's proof, no line over cap, no echo.

**`id-corp-3`**, the new line: *"Your work lands in the room. The budget for it
sits somewhere else. AED 120,000 signed from meetings I set up with the people
holding it."* Both existing corporate generics are the same shape
(decision-maker) citing the same Business figures, and nothing corporate-facing
cited money. The opening two sentences are the corporate seller's actual problem
stated plainly: the person you impress is not the person who releases the
budget. Three corporate lines is also the minimum that can hold a pool under a
35% cap.

**One operational trap, now in the skill.** Re-dealing after drafting made the
drift check reject two verified emails with "the drafter drew its own instead of
using the batch's" — which is the opposite of what happened. The deal moved
under them, because the pool changed. Export against the same deal file the
drafts were written from; if you must re-deal, re-draft.

399 tests green.

## 2026-07-31 (the copy rewrite, second pass) — what a third cold read found

Redrafted Rohit against the rewritten `id-any-6`, since his two holds had the
same cause and that cause no longer existed. The reader refused him a third time
— but for **different** reasons, and two of them were structural, which is the
useful part.

**My own rewrite of `id-any-6` was individuals-flavoured.** It ended "30 of the
people I picked signed with a coach here this year", which describes people
hiring a coach. That line lives in the GENERIC pool, so a corporate-facing lead
draws it — and Rohit sells leadership and sales training to organisations. The
reader: *"the number lands on a market he does not sell into."* Fixed to "turned
into signed clients", which is neutral about whether the client is a person or an
organisation. A generic line has to be.

**`ps-04` has now been convicted by three separate readers.** "if this isn't your
thing, no hard feelings at all" dodged every banned weak-closer phrasing while
keeping their exact shape: *"hands him a pre-written way out one line after a
firm fifteen-minute ask, and presumes a relationship where feelings could be
hurt."* Rewritten to ask them to take the out rather than offer it. All four ps
lines now ask for a decision instead of apologising for the ask, which is the
pattern the readers kept circling.

**Rohit holds after three attempts.** That is the right answer and it is worth
recording why: corporate-facing, spilled to the generic pool, and an abstract
hook about a drawing. Three different faults on three attempts is not a drafter
problem, it is a lead the current copy cannot serve well. The `THIN` report has
been saying the adjacent thing all along.

394 tests green; the 8-lead file exports clean with a 2/2/2/2 ps spread.

## 2026-07-31 (the copy rewrite) — three lines the cold reads convicted

Haytham: "rewrite id-any-6, rewrite ps-01 and ps-03, fix all issues you found."
All three had been named by independent cold readers, and all three were copy
faults rather than drafting faults — which is why no amount of redrafting had
fixed them.

**`id-any-6` had no client result in it.** "I went through about a hundred coach
sites here before writing to anyone. 6 published a price." It was tagged
`shape=research`, and that was the problem: every other identity line carries an
outcome, and this one carried an anecdote. A drafter had nothing to bridge from,
and it produced BOTH stapled-beat failures in the batch — the only two. Two
readers said the same thing independently: "the proof beat contains no proof: he
learns Haytham browsed a hundred websites, not that Haytham produced anything for
any coach." It also read as a poke at the reader's own unpriced site, and
"finding who's worth your time is the job" left whose job unclear. The rewrite
keeps the selection idea, which was the good part, and attaches the real
aggregate: *"Deciding who is worth your time is most of my job. 30 of the people
I picked signed with a coach here this year."* Shape is now `selection`.

**`ps-01` denied something two of four offers never raise.** "not a list" only
makes sense after an offer that mentions one. `b4-01` does — and collided with it
under `check_echo`, so that pair could never be dealt at all — while `b4-03` and
`b4-04` never mention a list, leaving the ps answering an objection the reader
was never given. Now: *"ps: a straight no is a fine answer, and costs you
nothing."* **All sixteen offer/ps pairs are dealable for the first time**, so
`deal` no longer prints an ECHO line and `rebalance_ps` has nothing to work
around. The machinery stays as a net for the next one.

**`ps-03` cancelled the offer's own premise.** "a no here costs you nothing and
costs me nothing" — a reader put it exactly: *if a no costs him nothing, the ten
names he pulled by hand were not work.* Dropping that half keeps the costless
exit for them and stops the email undercutting its own ask.

Both new ps lines are also **firmer**, which was a third thing the readers kept
flagging: they ask for a decision rather than offering an escape. One called
`ps-04` "the soft exit the close is supposed to avoid."

**Two drafts of these were too long before one fit.** The firmer phrasings ran
15–16 words against the old 11–12, and `_check_hook_room` correctly refused the
set: the longest line in each beat totalled 85, leaving 10 words for a hook
against a 12-word minimum. Tightened to 12 and 10 words, hook room is back to 14.
That check earned its place — the failure is invisible on any single row.

**Also fixed: the machine was about to guess at someone's name.** A non-Latin
surname reaches Smartlead's `last_name` column verbatim — a real lead on this
batch shipped as Arabic script while his own LinkedIn slug carried the Latin
spelling. `check_merge_fields` surfaces it rather than transliterating, because
guessing someone's preferred spelling is the same class of error as inventing
their address. The first version flagged "José Álvarez", which would have trained
the reader to ignore the warning; it now decomposes accents and only fires on a
genuinely different script.

394 tests green. All three copy sources identical; every dealt combination legal
at n = 8, 11, 25, 60 and 200.

## 2026-07-31 (the diagnostic pass) — 16 findings, worst-first

Haytham: "full diagnose end-to-end, no more loose ends, we need to ship." Two
adversarial audits plus a systematic sweep of every command against every bad
input. Everything below was reproduced before it was fixed.

**The four that would have destroyed something.**

*A blank `Warm` column beat the status.* `warm is not None` meant an empty
checkbox overrode "Reply Received" and marked a live thread cold. A loose name
match on a cold contact returns a `NameEcho`, which by design proceeds — so the
one send this machine calls destructive rather than wasteful was reachable
through an empty cell.

*Shared link-in-bio hosts collapsed distinct people into one wall entry.* The
live wall already had six rows keyed on `stan.store`, `linktr.ee` and
`beacons.ai`, two of them warm. It broke both ways: a new coach on
`linktr.ee/x` matched Lee Harris and was reported "already present", so they were
emailed and then never walled; and any lead carrying `stan.store` hit a warm row
and halted the batch. `domain_key` now returns "" for a host that identifies
nobody — the path is the identity, and the registrable domain throws it away.

*A blank email merged two leads in the deal.* Keyed by address, and
`Research.email` defaults to "". Three leads in, two anchors out, with a Health
coach holding a Business identity line and `deal` reporting "2 leads". Blank and
duplicate addresses are now refused outright.

*`.ae` was substring-matched over the whole page, and the marker scan ran before
the stated-residence check.* "I am a coach based in Toronto. Read my essay at
nowhere.aeon.co" returned YES on ".ae"; "Our client Marina came to us from
Manchester" returned YES on "marina". A non-UAE coach passed the floor and got
an identity line whose entire premise is the UAE reference group. A written
statement of residence now outranks an incidental word, markers are word-bounded,
and the TLD is checked on the domain only.

**Two of the false-rejection bugs were mine, from this same session.** The
jargon list and my new `_ECHO_PHRASES` both used raw substring tests: "optimism"
tripped "optimi", "auditorium" and "auditioning" tripped "audit", "Detroit"
tripped "ROI", and "realistic" tripped "list". Each dropped a whole email and
named a word that was not in it — unfixable by the drafter, because the
complaint was false. Both are word-bounded now, with explicit stems.

**A lead lost to a date format.** dateutil parses month-first by default, so a
UAE/UK "03/07/2026" silently became 7 March, and `check_active` is a floor where
`no` is the only thing that kills. Separately, `extract_dates` sorted stale
candidates first and truncated at 30 — and a stale candidate requires
`days_past > 7`, so a genuinely recent date always sorted after them and fell
off the end of a long events archive.

**Three gates that could not fire.** The real reply rate (3.2%) was computed and
then discarded by an `isinstance(n, int)` filter, while `lint._licensed` carried
rounding logic that existed only to accept it — a true number was unwritable. A
segment's own `sent` and `sourced` counts were documented as citable and left
out of the set. And half of `check_subject`'s last check tested `text !=
text.strip()` on an already-stripped string.

**And the quieter ones.** An unchecked Airtable checkbox arrives ABSENT, not
`False`, so `is False` never fired and retiring a line did nothing. A blocked
batch left the previous run's `leads.csv` in the same default `out/` — reporting
"nothing written" over a file that was still there and still uploadable. `null`
from a worker crashed the schema gate rather than failing it. `batch_fetch` keyed
on slug, so two directory rows sharing a company site got one read and the
survivor's page text was the other person's. Repeated-subject failures printed in
string-hash order, randomised per process, against a design that says a skill
quotes the line verbatim.

**Also this pass:** every command now exits 2 rather than tracebacking on a
missing file, malformed JSON, the wrong JSON shape or an unrecognisable CSV —
`wall-add` on a mistyped path used to print "0 added, 104 -> 104", which reads
exactly like "already walled". The echo collision moved from the export gate to
the deal, where it belongs: one email in sixteen was being rejected for a
combination no drafter caused. `main.py lint` assembles the body from beats, so
the PASS line a drafting worker is required to quote is obtainable at all.
`research` accepts the slice array its own skill tells workers to produce. And
the test suite was order-dependent — a stub over `audit.airtable` was restored
only when a previous module existed, so twenty-four export tests failed in the
full run and passed alone.

385 tests green, order-independent forward and reverse. `tests/test_audit_regressions.py`
pins all sixteen findings by failure mode.

## 2026-07-31 (the first real batch) — 13 leads, end to end

Haytham dropped a real list and said run all 12. Every number below is measured,
not estimated, and every bug below was found by running the machine rather than
reading it.

**The funnel, stage by stage.** 13 rows in. Dedupe caught 1 (Salma El-Shurafa,
already contacted, cold). Tier 0 read **9 of 12 sites free (75%)**, 5k to 86k
characters each, and planned 2 batched Apify escalations rather than 12 separate
ones. All 12 passed the three floors. **11 of 12 hooks found and independently
verified (92%), zero refuted**, one clean no-hook (Nicola Tate: site is an
unconnected Wix domain with no Wayback snapshot, newest LinkedIn post 137 days
old, nothing on podcast or Instagram). 11 drafted, all 11 passed the linter.

**Then the draft-verifier refuted 7 of 11.** That is the headline. The linter
passed every one of them, and a cold reader who never saw them written sent back
4 SEND and 7 REWRITE. It caught: three numbers stacked into one proof sentence
so it reads as a pitch deck; "I got an executive coach here 6 meetings", which
parses wrong on first read and does it on the credibility line; "on the last
run", which tells the reader they are in a batch one line before the email
claims the names were picked for them; a subject promising "the action step in your
framework" over a body that opens on a different quote entirely; and one genuine
stapled-beats failure where the drafter pasted the identity anchor in with no
bridge sentence in front of it. The worker/verifier split is the whole reason
this machine exists and this is the run that earned it.

**Four bugs, three of which would have shipped.**

1. *The website column never mapped.* The list used `companyWebsite`; the alias
   table did not know that spelling, so 13 of 13 sites mapped to nothing and the
   entire free site-read tier was skipped in silence. Added the sales-export
   spellings, and `intake` now prints the columns it ignored.

2. *Tier 0 crashed on the first page of the first site.* `extract_emails`
   returns two buckets in a dict and `_harvest` called `list.extend()` on it,
   which iterates the keys — so `read.emails` filled with the strings "personal"
   and "generic" and died on `.get`. Unreachable with an empty page list, which
   is what every existing test had. `tests/test_fetch.py` now feeds real HTML
   through the real harvest, and the buckets stay apart until the end so a jane@
   on page four still outranks an info@ on page one.

3. *`coach_type` came back empty for 3 of 12 real headlines* — "Career and
   Work-Life Balance Coach", "Chief Executive Officer Coach" — because the
   patterns wanted the segment word adjacent to "coach". Added a loose pass
   allowing words between them, restricted to the headline and tried only after
   every strict pattern fails.

4. *Eight of the thirty-one identity lines carried "her" or "him"*, which
   `check_identity_pronouns` blocks — a quarter of the identity bank could not
   ship as written, and every drafter dealt one had to notice and silently
   rewrite it. Same class as yesterday's cta-02: `copy-sync` validated numbers,
   attribution and claims but never ran the pronoun check. It does now, and the
   eight lines are fixed in Airtable.

**Two findings that only a reader could produce, one now mechanical.** The cold
reader caught `b4-01` ("Not a scraped list") dealt alongside `ps-01` ("not a
list") — the same denial twice in ninety words. Neither line is at fault, so the
check belongs on the pair: `check_echo` now rejects any email whose offer, cta
and ps repeat a distinctive phrase. It fires on exactly 1 of the 16 offer/ps
combinations, and both test fixtures were using that pair, which is how common it
is. The second finding has no mechanical fix yet: `id-any-6` is a research
anecdote rather than a client result, and it was the one draft with no bridge —
it may only be safe on a lead whose hook is already about market opacity.

**A hazard worth naming.** Three draft-workers returned invented email addresses
in their JSON (`andy@theteamspace.ae` for a `.com` lead, and two others). Nothing
asked them for an address. The export takes the address from the lead record, so
nothing shipped wrong, but an orchestrator that trusted the worker's field would
mail the wrong person. Drafters should not be emitting addresses at all.

Final: 10 of 13 in the upload file, Cheryl held on the echo check, Nicola held on
no hook, Salma held on the wall. 337 tests green. Apify spend for the whole
batch stayed inside the $29 cap at 25.6% before the run.

## 2026-07-31 (last pass) — the hardening run, and the gate that was rejecting its own copy

Haytham: "do a final run over every part... make sure the system is ready,
bulletproof, and each part is synced." Two audit agents plus a full end-to-end
run on a synthetic five-lead list. The end-to-end run is what found the worst
one, which no static read would have.

**The machine was dealing lines its own linter rejected.** `cta-02` promised the
10 names and a same-day clock but never said *why those ten* — so `check_claims`
rejected every email it was dealt to, and `b4-04` never used the word "names",
failing the same check. Between them they silently condemned a share of every
batch, and the rejection line pointed at the draft rather than at the line that
caused it. `copy-sync` validated numbers, attribution, em-dashes, weights and
segments, but never asked whether a line carried its own beat's claim tokens.
It does now, and it fails closed. Identity is exempt on purpose: 22 of its 31
lines open on a bare stat, and turning that toward the reader is the drafting
model's job by design.

Repaired both lines in Airtable (the runtime source of truth — editing the CSVs
alone would have been overwritten by the next sync, and the live ladder was
still dealing the broken text), then ran `copy-sync --live` so Airtable, the
snapshot and the committed CSVs agree again.

Fixing `cta-02` made it 7 words longer, which exposed the next thing: the hook is
the only beat nobody writes in advance, so it absorbs every other beat's growth.
Added `_check_hook_room` — the longest line in each beat must still leave 12
words under the 95-word ceiling. Checked on the worst case, because the draw
picks the combination and nobody gets to avoid it. The live bank passes with 12
to spare, which is tight enough to be worth knowing.

**The false-kill surface in `check_uae` was much bigger than the DXB case.** The
rule was "X is not in UAE_CITIES", which is a statement about our list, not about
the lead. Measured it against 29 real UAE localities: eleven returned a hard NO,
including Al Barsha, Deira, Mirdif, Motor City and Emirates Hills. Every one of
those is a Dubai coach telling us exactly where they are. The burden now sits on
the kill: a NO needs a match in `FOREIGN_PLACES`, and an unrecognised place is
`unclear`, which costs one research call. Added the districts to `UAE_MARKERS`
too, so they pass rather than merely survive.

**`name_key` sorted its tokens**, so "Ahmed Mohammed Ali", "Ali Mohammed Ahmed"
and "Mohammed Ahmed Ali" were one key — three different men in a market where
given names double as surnames, and a permanent invisible kill for two of them.
The only case sorting bought was the inverted export, which is now handled by
un-inverting the comma. The sorted key survives as `loose_name_key` with
asymmetric consequences: it stops the run against a **warm** contact, and merely
reports a `NameEcho` against a cold one. That asymmetry is the whole design in
one function — a cold opener on a live thread destroys a conversation, a second
cold email months later wastes a send.

**Dead code that turned out not to be dead.** `extract_dates` had no caller;
rather than delete it, wired it into `qualify.latest_activity_date`, which
settles the active-in-30-days floor from page text instead of asking a worker
whether a page feels current. Two bugs found while doing it: the copyright filter
read the ±80-char context window, so a footer `©` discarded every date on the
page (which is every page — `extract_dates` now also returns the tight `near`
window it actually tested), and a year-less date would read a three-year-old
"March 14" as this March. `extract_availability` really was dead and went with
the audit — it made an un-buyable offer machine-visible, which was a *finding*,
and findings are not what this machine sells.

**`_rejoin_particles` was defined and never called.** Rewrote it as
`_joined_surname`, which ADDS candidates rather than replacing the surname: an
Al Fahim may use `alfahim@` or `fahim@`, and picking one silently loses the
other. Single-letter particles only rejoin when an apostrophe follows them in
the raw name, so "Jane L Smith" keeps `jane.smith@` instead of guessing
`lsmith@`.

Also: `write_batch`'s lint dict is keyed by email everywhere now (the test helper
was still on slug, which is the collision the fix was about); `draft_lint` and
`urls` had docstrings naming deleted modules as their consumers; and
`tests/test_cli_failures.py` is new — nothing pinned the exit codes the skills
quote, and exit 2 ("the check could not run") is the one that must never be
mistaken for exit 0.

326 tests green. End-to-end run writes 3 of 3 with the anchors held.

## 2026-07-31 (later still) — Copy Assets stopped being an inert table

Haytham: "the copy assets just sit there as a table, it shouldn't be a
bottleneck." Three things were true, and measuring first is what found the
second and third.

**1. Editing it had arithmetic homework attached.** Adding a fifth offer line
meant renumbering the other four roll ranges by hand so the spans stayed
contiguous, with a validator that failed the whole sync on a slip. Replaced with
a plain `Weight` on any scale, blank meaning equal share. Ranges are derived at
load, so the gap-and-overlap failure class is gone rather than checked. `Line ID`
now generates from the text when blank and `Word Count` is computed, so adding a
line is three cells: Beat, Line, Weight.

**2. The declared weights were fiction at real batch sizes.** Measured before
touching anything: independent per-lead hashing over the live offer lines gave
`b4-04` 8% against a declared 20% at n=50, pushed `b4-03` to 38% over the 35%
cap, and only converged near n=200. Added `deal` — largest-remainder allocation
over the whole batch. Worst miss at n=50 went 13 points to 1, and the cap is now
satisfied by construction instead of warned about afterwards. `anchors` keeps the
per-lead draw for single-lead work where there is no batch to balance.

**3. Nothing ever came back.** Added `copy-usage`, which reports which lines
actually shipped into `Times Used` / `Last Used` after an upload. The weights are
guesses today and usage plus reply data is the only thing that can replace a
guess with a measurement. Additive, deliberately not idempotent, unlike
`wall-add` — flagged in the output because the asymmetry could bite.

**Three bugs found while doing it, two of them pre-existing:**

- `exact_both + exact_type` put the same identity line in the pool twice
  whenever `sells_to` was `any`. That silently double-weighted those lines in
  the old per-lead draw, and made the batch deal issue more seats than there
  were leads. Deduped.
- **Alphabetical tie-breaking was systematically biased.** With 3 leads over 9
  equally-weighted identity lines every remainder ties, and sorting by id handed
  all three seats to `id-any-1/2/3` — so small segment groups never drew their
  matched line at all, which is the entire point of the pool. Ties now break on
  a hash of the id.
- **Dealing generics per segment clustered across the batch.** Six small segment
  groups each independently picked the same first generic line and put it in
  front of 42% of a 12-lead batch. The generic pool is shared, so it is now
  dealt once across the whole batch after each segment's matched share is taken.

**One content gap surfaced, not papered over.** Executive has exactly one
identity line usable for an individuals-facing lead, so a straight 70% match
rate put that sentence in front of 70% of the batch. The cap outranks the ratio,
so the excess spills to generic — but `deal` now prints a `THIN` line naming the
segment and the shortfall, because the spill is the workaround and writing
another line is the fix.

Copy Assets rebuilt (12 fields, seeded from Python rather than by hand) and
`audit/airtable.py` gained a narrow write path. 280 tests pass. Verified live:
deal → copy-sync → export → copy-usage → read back → reset.

### Open follow-ups
- [ ] Write a second Executive identity line for individuals-facing leads.
      `python main.py deal` prints the shortfall on any batch containing one.
- [ ] `Times Used` becomes useful only when reply data lands. Per-line reply
      rate is the number that turns the weights from guesses into measurements,
      and it needs Smartlead replies flowing back.

## 2026-07-31 (later) — Airtable read wired, wall moved to the repo, Smartlead columns pinned

Four asks, and two real bugs found while doing them.

**The Airtable read is a gate, not a copy.** `outbound/copy_sync.py` pulls Copy
Assets and validates every line before writing: numbers must trace to
`copy/results.csv`, no number may sit next to a segment it doesn't belong to,
and the weighted beats must cover 1-100 with no gap or overlap. Nothing is
written if anything fails. That last check was already needed and missing — a
gap in the roll ranges means some leads draw nothing and fall through to a
positional fallback nobody chose.

`anchors.CopyBank.load()` now tries live Airtable, then the last synced
snapshot, then the CSVs. `AIRTABLE_API_KEY` turned out to be live in the
environment after all, so the direct path is running today.

**Bug 1, found by the tests hanging: no cache.** `load()` fetched on every
call, so five draws made five HTTP requests. A 200-lead batch would have made
200 and tripped Airtable's 5-req/sec limit. Now cached per process, with
`OUTBOUND_COPY_SOURCE=csv` to force offline (the test suite sets it via
conftest, so the suite is network-free and doesn't depend on live data).

**Bug 2, found by round-tripping the real CSVs through a live fetch and
diffing: order changed the draw.** Airtable returns records in view order and
`draw_identity` indexes into the list, so the same lead drew a *different* line
depending on which source the bank loaded from. Deterministic within a source,
false across them. Fixed with a canonical sort by id everywhere; `copy/identity.csv`
is reordered in this commit as a result (content byte-identical, verified). A
test now asserts all three sources agree.

**Contacted Before moved to `data/contacted-before.csv`** — 104 rows, 9 warm —
and the Airtable table was deleted. Two walls that can disagree is worse than
either, and the dangerous direction is the repo one going stale while Airtable
looks current, since the repo one is what runs. It is read on every batch, never
needs a view, and appending is a commit, so the wall has a history for free.
`dedupe` now exits 2 on an unreadable wall rather than passing the batch.

**Export writes exactly eight Smartlead columns**: email, first_name, last_name,
website, linkedin_url, location, subject, body. Nothing analytical — that lives
in Airtable. It also writes `wall-additions.csv`, deliberately NOT applied:
nothing is sent at export time, and walling a lead who never received anything
would silently exclude them from every future batch. `main.py wall-add` closes
that loop after the upload, idempotently.

**Leads table rebuilt lean**, 34 fields to 28, grouped in the order the machine
fills them. Two real simplifications: the three floors collapsed into
`Qualified` (checkbox) + `Failed Floors` (multi-select), which is the query that
actually matters; and Status went 11 options to 7, with hold reasons living in
`Blockers` as text rather than as five near-identical statuses. New table ID
`tbl51dU7ojrxCVfxZ`. Copy Assets seeded with all 43 lines.

250 tests pass. The whole loop verified live end to end: live Airtable read →
copy-sync → intake → dedupe (stopped on a planted warm lead) → export →
wall-add → next batch blocks the walled lead.

### Open follow-ups
- [ ] `results.csv` is repo-only on purpose (lines are voice and get tweaked;
      results are audited evidence). Revisit if that friction bites.
- [ ] Move the Airtable base to its own workspace — the MCP can create a base
      but not a workspace, so it is in "My Workspace".
- [ ] Follow-ups (touch 2/3) still not built. Smartlead sequence steps; nobody
      has decided whether they should be per-lead personalised.
- [ ] First real batch still needs to measure the tier-0 fetch rate and
      reconcile Apify cost against the dashboard.

## 2026-07-31 — Rebuilt as an outbound machine: audit out, anchored AI drafting in

Merged the funnel auditor with the cold-email system Haytham had been running
separately. The auditor's offer is dead (589 leads, 0 AED, reply→call 0/9); its
chassis is not. The cold-email system's offer and copy are good; its pipeline
was not.

**What the merge actually is:** the hand-written copy lines became the drafting
model's ANCHOR rather than bricks it concatenates. The model authors the hook
and owns the seams between beats, and may re-voice an anchor for flow, but may
not change what the anchor claims. That is only safe because `outbound/lint.py`
makes every failure mechanical.

**Deleted** (~7,400 lines): crawler, evidence, vision gate, Gate 0 floors,
crm_gate, dashboard, send_cap, inboxes, touchlog, calendar_state, checks/,
config.py, the whole Gmail path, docs/leads (370 files), every funnel-audit
skill and agent. Firecrawl is gone from the environment, so the fetch ladder is
now local HTTP → WebSearch/WebFetch → one batched Apify run.

**Built:** `outbound/` (normalize, dedupe, fetch, qualify, research, anchors,
lint, export), `copy/` (the four line files + results.csv, the fact table),
skills `outbound-batch` and `outbound-draft`, agents research-worker,
hook-worker, hook-verifier, draft-worker, draft-verifier. 209 tests pass.

**Two things the linter caught that I had wrong**, both worth remembering:
- The first version rejected `id-corp-1` and `id-any-5` — real hand-written
  lines that *widen* a Business result to "coaches here". Widening is explicitly
  sanctioned; the failure is only relabelling (a number next to a segment it
  doesn't belong to). Split into `check_numbers` (invention) and
  `check_attribution` (relabelling).
- Periods needed exact unit equivalents: "60 days" and "2 months" are the same
  fact, and a checker that only knows one rejects an honest line. Approximations
  are deliberately NOT licensed — 45 days is not 6 weeks.

**Airtable:** new base `appejF07kunksqt4D` ("Outbound Machine") — Leads,
Batches, Copy Assets, Contacted Before. Seeded Contacted Before with all 103
previously-contacted leads from the old CRM, 9 flagged warm (Ben Pringle,
William Brown, Lucia Csobonyei, Lee Harris, Lisa Hugo, Avneet Kohli, Rita Baki,
Wafa Bassili, Donna Brown). Old base `appaBExqyEZykb1Qk` is archive only.

**ICP narrowed to three measurable floors:** UAE-based, is a coach, active in
30 days. Audience and program price are captured, never gated — audience
decoupled from the offer once we started selling their clients rather than
leverage on their list, and a price floor reads unclear on ~94% of coach sites.

### Open follow-ups
- [ ] Smartlead column names, so `export.py` writes them exactly. Currently
      `email, first_name, last_name, full_name, company, subject, body` + lead
      fields.
- [ ] Move the Airtable base to its own workspace (the MCP can create a base but
      not a workspace, so it landed in "My Workspace").
- [ ] Copy Assets table is created but empty and NOT yet read by `anchors.py` —
      `copy/*.csv` is authoritative. Wire the Airtable read, or drop the table.
- [ ] First real batch: measure the tier-0 fetch rate. Nobody has published what
      share of coach sites a plain HTTP fetch can read, and every cost estimate
      downstream depends on it.
- [ ] Reconcile that batch's real Apify cost against the usage dashboard. The
      last paper estimate was wrong by 6-7x.
- [ ] Follow-ups (touch 2/3) are not built. They are Smartlead sequence steps
      and nobody has decided whether they should be per-lead personalised.
- [ ] Sourcing is phase 2. Phase 1 is drop-a-list only.

# Project Journal — cross-session memory

What git history doesn't capture: **what happened each session** (pipeline ops
AND dev), the decisions behind it, gotchas learned, and open follow-ups.
Airtable holds live *state* (where each lead is); git holds *code changes*;
this file is the thread that ties sessions together so a fresh session isn't
starting cold.

**This journal starts at the pivot (2026-07-31) and nothing before it is
coming back.** The entries from 2026-07-16 to 2026-07-30 were the funnel
auditor's — walks, findings, Loom offers, Notion, Gmail sends, a fix list for a
pipeline that no longer exists — and `docs/journal-archive.md` was more of the
same. Deleted 2026-07-31 on Haytham's call: this is a new system and that log
described a different one. Where a pre-pivot session explains code that
survived, the reason lives in that module's docstring instead, which is where
someone reading the code will actually find it. Git history has the rest if it
is ever genuinely wanted.

**How it's used:** the `SessionStart` hook (`.claude/hooks/session_memory.py`)
injects the most recent entries here + the last few commits at the top of every
session, so context loads automatically — no fetch, no prompting.

**How to write it:** at the end of a session with anything worth remembering,
add a new `## ` block at the TOP (newest first), then commit + push. A
journal-only commit is fine on an ops-only session — the point is that it
survives the ephemeral container. Keep entries short and scannable: a few
bullets, then an `### Open follow-ups` list if any are outstanding. When an
entry's `### Open follow-ups` items are all resolved, cut the list rather than
leaving a stale all-checked block — the resolution belongs in whichever new
entry closed it out.

Entry template:

```
## YYYY-MM-DD — <one-line title>
- what happened (ops events, sends, sourcing, ticks, or code)
- decisions made and why
- gotchas / things that surprised us
### Open follow-ups
- [ ] the next thing someone should pick up
```

**Older entries get condensed, not archived elsewhere.** Once a day's entries
scroll past the "recent" window that is useful to load at session start, fold
them into one short dated summary in place. There is no second archive file any
more — the old one collected the pre-pivot log and went with it, and a
hand-maintained overflow file nobody loads is where detail goes to rot. If an
entry is worth keeping it is worth condensing; if it is not, git has it.
