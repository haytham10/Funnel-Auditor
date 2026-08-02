# Hook rules

The hook is the first line of every email and the only beat written from
scratch per lead. It answers the reader's first objection — *"is this a
spammer?"* — and nothing else in the email gets read if it fails.

Written fresh 2026-07-31. The previous outbound repo had its own version of this
file; it was deliberately not carried over, so nothing here is inherited.

## What a hook is

One or two sentences about something specific and recent this person did, that
only this person would recognise, **plus a clause that says what you took from
it.**

That last part is the whole difference between a hook and a quote. Compare:

> You wrote that you couldn't contain the excitement of uncovering a solution
> for yourself.

> You wrote that you couldn't contain the excitement of uncovering a solution
> for yourself. That is a strange thing to read from someone who sells the
> solving.

The first hands them back their own sentence and stops. The second has a writer in
it, and the paragraph after it now has somewhere to start from.

## The four requirements

- **Specific to them.** If it could go to another coach in the same segment
  unedited, it is not a hook.
- **Recent.** Inside ~90 days, for everything. There is no longer an
  at-any-age exemption for an evergreen framework or an About-page line: the
  hook gate requires a real `published_at` from every proposal, so an exempt
  candidate is one the next gate is obliged to reject. **An About page is not a
  hook source at all** — see the note under ban #1.
- **Cited.** A URL actually fetched, the quote verbatim, and a date.
- **Theirs.** Something they wrote, said, built or named — not something
  written about them, and not their website's marketing copy.

## The twelve bans

The first eight make a hook read as spam. The last four make the rest of the
email fail even when the hook is technically true.

1. **No generic site copy.** "I saw you help women find their purpose" is the
   hero section of a thousand coach sites. **This is a ban on the writing, not
   on the page it sits on.** The mechanical half is the same text appearing for
   two different leads, which is this ban's own test — could it be sent unedited
   to another coach — settled on evidence.

   **Separately, and for a different reason, an About page cannot be a hook
   source.** This is not a judgement about genericness, which is why it is not
   really part of ban #1. It is arithmetic: requirement 3 wants a date, an About
   page has none and never will, and `outbound/hook.py` exempts no kind. The
   rule was relaxed once, on `2026-08-01-q1`, because three MISSED leads were
   About observations a verifier had VERIFIED — but a VERIFIED undated page can
   only have been dated by hand, and on `2026-08-02-q2` two workers were caught
   doing exactly that, one citing the other as precedent. Twenty-six of that
   batch's forty-two observations were About text and **none carried a date**.
   The ban is now on the `kind`, so a supplied date cannot rescue it.
2. **No compliment with no object.** "Love your content" names nothing.
3. **No invented specifics.** If it cannot be cited, it does not exist.
4. **No inferred emotion.** You do not know they were nervous, proud or
   relieved.
5. **No follower counts or growth observations.** They read as surveillance,
   and the offer has nothing to do with their audience.
6. **No stale news as fresh.** A 2023 podcast is not "your recent episode."
7. **No third-party coverage.** A directory listing is not their voice.
8. **No stacking.** One observation. Two makes it a dossier.
9. **The hook must have a writer in it.** See above. This is the most common
   failure and it cannot be repaired downstream — a hook with no writer produces
   an identity beat that reads as a non sequitur, whatever that beat says.
10. **No question as the hook.** A question invites an answer, and an answer is
    a dead end that looks like success. The close asks for the meeting.
11. **No flattery escalation.** "Brilliant", "incredible", "so inspiring."
    Peer to peer, not fan to celebrity.
12. **No restating their offer back to them.** They know what they sell.

**Four of these are now mechanical**, in `outbound/select.py`: #1 is the
repeated-text test above (with the separate `about_page` ban beside it), #6 is a
date comparison that now applies to every kind, #7 is `author ==
"third_party"`, and #3 is the `obs_id` join —
a candidate names the observation it came from, so a hook citing a page nothing
retrieved cannot be built. The other eight are still judgement, and this file is
still the authority on all twelve.

## Where hooks come from, in cost order

**`outbound/plan.py` owns the ladder.** The rungs, their order, which are free,
which are paid and which actor each names live there as `LADDER`, and
`python main.py plan` prints the ones a particular lead actually has. This file
does not list them, because it used to and the list drifted: it once opened with
the **paid** rung under a heading that said cost order, so the sentence and the
list disagreed and the list won. That is D23 in `docs/spec/07-decisions.md`.

**The ladder is walked by the research stage now** (D27). `hook-worker` does not
search: it chooses from a shortlist `select` ranks over what research retrieved,
quotes it verbatim and writes the clause. The ladder still describes where hook
material comes from — it is just that one stage earlier gathers it and one
stage later uses it, instead of both fetching the same profile.

Three consequences worth stating rather than discovering:

- **The podcast rung is `research-worker`'s.** It was the free "their name plus
  podcast" search and it belonged to the agent that no longer has `WebSearch`.
  It reaches the coaches who do not post, so leaving it behind would have
  narrowed where a hook can come from without anybody deciding to.
- **An observation nobody returned is a hook nobody can find**, and it presents
  as the lead's fault rather than the retrieval's.
- **One bounded escalation** remains, against a URL the plan named and never a
  rung it declined. A null hook is the cheaper answer and is still a good one.

What stays here is the judgement the code cannot hold. **Free before paid,
always** — an About page already on disk is read before anything is bought.
**Instagram is a rung, not a fallback**: for a coach whose whole presence is
Instagram it is the only one there is, and `python main.py fetch` names those
leads in its report so they are handed out rather than discovered.

Social sources are worth the trouble: giving the research agents the social
links got hooks on 99 of 113 leads, against 21 of 40 when an earlier run ignored
that column.

### Two windows, and each has one owner

There were four, which is three too many for one stage: 30 days in the code,
"about 90 days" here, `--since month` in one agent file, `--newer-than "60
days"` in another.

- **Activity, 30 days.** Owned by `docs/spec/02-icp.md` and evaluated in
  `outbound/qualify.py`. It is a floor: is this person still working?
- **Hook recency, 90 days.** Owned by this file, enforced in
  `outbound/select.py` as `HOOK_RECENCY_DAYS` and matched by the `--since` and
  `--newer-than` flags the rungs pass. It is an editorial judgement: would they
  recognise this as something they recently did? An evergreen framework or a
  line they wrote themselves is exempt from both.

They are different questions, so they get different answers. What they may not
be is different answers to the same question in four places.

**It went back to two answers in one place, and it cost the measurement.**
`research-worker` ran `apify li-posts --max 5` with no window while
`hook-worker` ran the same command `--since 3months`, so one profile was asked
two different questions one stage apart and the hook stage kept finding posts
research had never requested. That was 4 of the 5 UNOBSERVED hooks in batch
`2026-08-01-q1` — the number the whole retrieve-once decision is gated on,
inflated by a flag nobody had written down anywhere.

So the flags are on the rung now. `outbound/plan.py`'s `LADDER` carries the
exact strings, `doc-check` fails any file that invokes a rung without them, and
`.claude/agents/` is inside the scanned corpus — it was not, which is why the
two files could disagree for months with every gate green.

**A verification fetch carries no window.** `hook-verifier` re-fetches one page
to confirm one quote; narrowing that to 90 days would make it refute a post for
being older than the rule that chose it.

## Types

- **WORK** — a framework, a launch, a client result they published.
- **LIFE** — a personal update they chose to make public.
- **METRIC** — a number *they* published about their own work. Never one you
  counted yourself.

Recorded per lead so hook type becomes a testable variable against reply rate
rather than a thing buried in a body of text.

## Verification, and why it is a separate agent

The agent that finds a hook may not certify it. A second agent re-fetches the
cited URL in a context that never saw the search, and defaults to refuted.

That split exists because a single context checking its own work is not
checking anything. Under the old machine, unread citations reached real drafts,
and a third of self-certified findings failed under scrutiny while carrying a
verified flag.

- **VERIFIED** — quote is on the page, they wrote it, date holds, it is
  specific.
- **REFUTED** — a citable contradiction, never a feeling.
- **INCONCLUSIVE** — page would not load or has changed. Holds, never kills.

**No hook found is a good answer.** The lead holds and gets no row in the upload
file. There is no volume target that justifies sending a hook nobody could
confirm: a fabricated hook is unrecoverable on the call, and it poisons every
beat behind it.
