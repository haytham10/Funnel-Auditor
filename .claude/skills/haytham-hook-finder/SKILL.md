---
name: haytham-hook-finder
description: Pull real Instagram evidence for an Audit Ready lead and find the SMYKM hook — the one line only this person would recognize (their own framework, a real recent post, a personal update) — then write just that line to their Notion page. Use this skill WHENEVER Haytham says "find the hook," "SMYKM this," "hook Jane," "add a hook," asks for a stronger opener on a lead that's already Audit Ready (Lane 1 or Lane 2), or process-lead/batch-audit reports a lead "held — needs haytham-hook-finder." This is a separate, manually-triggered step from haytham-opener-finder — the walk assigns the lane, finding, and innocent explanation; this skill's only job is the hook, and it must come from real IG screenshots/vision evidence, never from a web-search proxy. It is a required gate, not an optional upgrade: haytham-email-draft will not draft for a lead until this skill resolves the hook line. It does not touch the lane, the finding, the innocent explanation, or draft any email.
---

# Haytham Hook Finder — real IG evidence → SMYKM hook → one line in Notion

`haytham-opener-finder` classifies the lane and finds the felt-cost finding.
It stops there and writes `SMYKM hook: not run yet — see haytham-hook-finder`
as a placeholder. This skill's entire job is to fill that one line, and to
fill it from something Haytham's audience would actually recognize — a real
post, a real framework name, a real personal update — never from site copy
or a press mention a search happened to surface. That's what made the old
hooks read generic: they were built from whatever was easiest to find, not
from what was actually hers.

This is manual, not automatic — Haytham triggers it by name — but it is
**required** before `haytham-email-draft` will draft anything for this
lead. `process-lead` and `haytham-email-draft` both hard-block on a
`SMYKM hook:` line that still says "not run yet," so every Lane 1/2 lead
sits waiting for this skill to run before it can get a Gmail draft — this
isn't an optional upgrade Haytham reaches for on standout leads, it's a
gate every lead has to clear. Once this skill resolves the line (a real
hook, or a confirmed "no hook found"), the draft can go ahead.

---

## Input

A Notion lead page (URL or ID) or a name Haytham names. The lead must
already be Audit Ready (Lane 1 or Lane 2) with a funnel walk written by
`haytham-opener-finder` — if it isn't, say so and point Haytham to that
skill first; don't run a hook search on a lead with no lane verdict yet.

---

## Step 1 — Get real IG evidence (never a web search)

1. Fetch the lead's Notion page. Confirm Lane 1/2 + Status Audit Ready, and
   note the current `SMYKM hook:` line (should read "not run yet" on a
   fresh lead, or hold a stale search-based hook on an older row you're
   backfilling).
2. Compute the slug the same way the rest of the pipeline does:
   `python main.py slug "<Contact Name>"`.
3. **Reuse evidence, don't re-fetch it.** If `process-lead` already ran for
   this lead, `evidence/<slug>/ig/` holds the sourcing screenshots,
   already downloaded and vision-marked. Run
   `python main.py vision check evidence/<slug>` to see what's already
   confirmed read — start there.
4. **If no evidence exists yet** (hook-finder invoked standalone on an
   older row, or the folder is missing): pull Haytham's IG screenshots the
   same way `process-lead` Step 0 does — they live attached to the lead's
   Notion page body (profile header, recent posts grid, link-in-bio
   screen, anything he clicked). Download each (`curl -o
   evidence/<slug>/ig/<n>.png "<signed url>"` — the fetch URLs expire, so
   don't defer), then `python main.py vision init evidence/<slug>` and
   `python main.py vision mark evidence/<slug> ig/<n>.png` as you read
   each one, exactly like process-lead does.
5. If Haytham pastes fresh screenshots or notes in chat instead of (or in
   addition to) what's on the Notion page, those count too and outrank
   anything stale already there.
6. **Never fetch instagram.com.** IG evidence is only what Haytham attached
   or pasted — this rule doesn't change just because this skill is IG-evidence-first.
7. No IG evidence anywhere (nothing on the page, nothing pasted, folder
   empty) → tell Haytham there's nothing to build a hook from and stop.
   Don't fall back to a web search — that's the exact failure mode this
   skill exists to avoid.

---

## Step 2 — Read for hook material

Read, as images, every `ig/` screenshot for this lead (and any freshly
pasted ones). Look specifically for:

- A framework, method, or program she's named and uses as her own language.
- A real recent post: its actual topic, a launch, a specific quote — not
  a vague "she posts a lot."
- A personal update: a birthday, a life event, something human and
  current.
- A stat she owns (a number from her own content) — but see the
  numeric-contrast warning below before using one.

Mark each image read via `python main.py vision mark evidence/<slug> <path>`
as you go, same discipline as the rest of the pipeline — don't batch it to
the end.

**Numeric-contrast warning:** if the only hook candidate pairs two metrics
she owns (e.g. a large podcast audience next to a small IG following),
never state both in the same line — the smaller number reads as the one
being pointed at, even when the intent is to praise the bigger one. Lead
with the strength alone, or find a different hook.

---

## Step 3 — The hard rule (unread images never produce a hook)

A hook that cites specific post content — a date, a quote, a topic, an
engagement number — is only usable if that exact image shows `read: true`
in `vision_manifest.json` (`python main.py vision check evidence/<slug>`
will list it as unread if it isn't).

If it isn't confirmed read:
- Read it now and mark it, or
- Substitute a hook grounded in something already confirmed read (a
  framework name that appears in her own site copy from the walk's
  evidence, an About-page bio line), or
- If neither works, say so plainly: "possible hook on an unread image
  (ig/N.png) — read it or confirm the post's content before using it," and
  leave the Notion line as "no hook found in IG evidence."

A hook built on an unread image must never reach Notion or an email draft.
This is the same failure that once put an unviewed IG post's like count
and comment-to-DM pricing into a real Gmail draft.

**Label the hook type** when one is found: WORK (her framework, content,
testimonial, point of view), LIFE (birthday, personal post), or METRIC
(numbers she owns). This is data collection, not a rule yet — keep
labeling every one so the pattern (currently: all confirmed warm-reply
hooks are WORK-anchored) stays checkable as more sends land.

---

## Step 4 — Write ONLY the hook line to Notion

Fetch the page fresh immediately before writing, even though you fetched
it in Step 1 — confirm the literal current body format (Notion's
enhanced-markdown escaping, e.g. `\$`, auto-linked domains, can break a
naive search-and-replace). If the fetch shows escaped or non-plain
formatting, rewrite the full body (`replace_content`) preserving every
other section exactly as it stood; otherwise a targeted
`update_content` replacing just the `SMYKM hook:` line is fine.

Replace the placeholder (or stale search-based hook) with one of:
- `SMYKM hook: <the hook, one line> — <WORK|LIFE|METRIC>`
- `SMYKM hook: no hook found in IG evidence — draft opens on the finding alone`

**Blast radius is exactly one line.** Do not touch Overview, Funnel Walk,
Evidence, Gate 1, the Lane verdict, the opening angle, the innocent
explanation, or the Email Thread Log. This skill has no opinion on any of
those and must not rewrite them.

---

## Step 5 — Hand off

Tell Haytham: the hook (or that none was found) and its type label, which
image(s) it came from, and the vision-check status. This resolves the
block on `haytham-email-draft` for this lead — say so explicitly ("hook
line resolved, ready to draft") so he knows the next natural step is to
ask for the Touch 1 draft. This skill still doesn't draft or touch Gmail
itself; that's a separate ask.

---

## What this skill does NOT do

- It does not classify the lane, run the 5-stop walk, or touch the finding
  or innocent explanation. That's `haytham-opener-finder`.
- It does not run automatically after opener-finder. Haytham triggers it by
  name, on the leads he wants a stronger opener for.
- It does not fetch or automate anything on instagram.com.
- It does not invent a hook. No confirmed IG evidence supporting one →
  say so and leave the line as "no hook found."
- It does not draft or send email, and it does not touch Gmail.
