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
