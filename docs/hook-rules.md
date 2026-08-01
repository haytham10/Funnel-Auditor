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
- **Recent.** Inside ~90 days for a post. An evergreen framework or an
  About-page line they wrote themselves is fine at any age.
- **Cited.** A URL actually fetched, the quote verbatim, and a date.
- **Theirs.** Something they wrote, said, built or named — not something
  written about them, and not their website's marketing copy.

## The twelve bans

The first eight make a hook read as spam. The last four make the rest of the
email fail even when the hook is technically true.

1. **No generic site copy.** "I saw you help women find their purpose" is the
   hero section of a thousand coach sites.
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

## Where hooks come from, in cost order

Actual cost order. This list used to open with the paid rung under a heading
that said cost order, which is how a batch reaches for LinkedIn before reading
an About page it already has on disk.

1. **Their own About page** — free, already fetched by the research stage.
2. **Podcasts and YouTube** — web search for their name plus "podcast", then
   fetch the episode page for the description and date. Free, and it reaches
   the coaches who do not post.
3. **LinkedIn posts** — the richest source by a distance, and paid.
   `python main.py apify li-posts <url> --max 5 --since 3months`
4. **Instagram** — `python main.py apify ig <url> --mode posts --newer-than "90 days"`

**Instagram is a rung, not a fallback.** For a coach whose whole presence is
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
- **Hook recency, 90 days.** Owned by this file. It is an editorial judgement:
  would they recognise this as something they recently did? The flags above are
  set to match, and an evergreen line they wrote themselves is exempt from both.

They are different questions, so they get different answers. What they may not
be is different answers to the same question in four places.

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
