---
name: haytham-opener-finder
description: Walk a parenting/faith-based coach funnel, classify the lane, identify the strongest verified finding, and write the structured output directly to the lead's Notion page. Use this skill WHENEVER Haytham pastes a Notion lead page URL, a site link, screenshots, or notes from a funnel walk, or asks to audit/walk/qualify a coach lead, or says "walk this" or "what's the finding" or "what lane is this." This skill crawls the lead's Site URL and any linked pages plus runs a web search on the lead BEFORE looking at whatever Haytham pasted, then reconciles the two. It owns the full Gate 0 → Gate 1 → 5-stop walk → two filters → three lanes pipeline and writes the result to Notion in the exact page body format. Do NOT fetch the four framework docs from Notion — everything is baked in here.
---

# Haytham Opener Finder

Walk a coach funnel, classify the lane, surface the strongest finding, and write the result to the lead's Notion page. The output feeds directly into the email skill — a clean lane verdict and opening angle is everything the email skill needs as its input.

The whole point of this skill is speed and depth in one pass, run in the right order: machine first, human second. A live crawl and a search build the raw skeleton of the funnel — what's technically there. Haytham's own observations (screenshots, notes, what a page actually felt like to click through) are placed on top of that skeleton, and they win where the two disagree, because they catch what a crawl cannot see: friction, tone, dead ends behind logins, manual-vs-automated delivery. Never treat the crawl as the finished picture. It's the first draft the human read corrects.

---

## Step A — Gather live signal first (always, before reading anything Haytham pasted)

Do this before opening any screenshots or notes in the prompt.

1. **Get the Site URL and Profile URL.** If a Notion lead page URL or ID was given, fetch it first — Site URL and Profile URL live in its properties. If Haytham's prompt itself contains links (a sales page, a freebie link, a checkout), those count too.
2. **Crawl.** `web_fetch` the Site URL and any other linked pages. Walk what's reachable stop by stop (see `references/walk.md`) and note, for each stop, what a crawl can actually see: bio link destination, freebie opt-in presence, sales page price/copy, checkout flow if unauthenticated, footer/social links for audience ownership.
3. **Search.** Run one `web_search` on the lead's name plus niche or handle. This is for two things specifically: the Activity floor (see the floor, below — is she still active in the last ~3 weeks?) and any SMYKM hook material (recent posts, a launch, a framework she's named, a personal update).
4. **Mark gaps.** Some stops a crawl cannot reach at all: comment-for-freebie flows, DM-gated content, login-walled checkouts, anything requiring a real payment attempt. Flag these explicitly as "not visible from crawl" rather than guessing or leaving them blank. This is exactly what Step B exists to fill.

Build a first-pass stop-by-stop skeleton from what steps 1-3 surfaced, with tier calls where confident and open flags where not. Do this whole step silently — don't narrate the crawl process to Haytham, just carry the result into Step B.

---

## Step B — Reconcile with the human-layer read

The human layer comes in two forms, and at least one is required:

1. **Haytham's own material** — screenshots, free-form notes, or both, pasted in chat or attached to the lead's Notion page (his IG sourcing screenshots live there). This outranks everything else in the walk.
2. **The vision pass** (automated runs, or whenever a machine walk produced screenshots) — read, as images, the desktop screenshot of every crawled page plus mobile for the bio and offer/checkout pages, and the full text files of offer pages. This is Claude's own click-through, and it outranks the machine text checks.

**Machine flags are candidates, not findings.** Every reconciliation entry, leak candidate, stale-date and availability hit in the packet must be confirmed on the screenshot/text by eye before it can enter the filters. Known misfires: footer copyright years read as stale dates, "sold out" inside a testimonial, prices compared across unrelated products, bot walls read as dead pages. A flag that fails visual confirmation is dead — record it as rejected (one-word reason) and never resurrect it. While confirming, hunt the vision-only leaks the checks can't see: empty/stuck calendars, hero promises the links don't sell, placeholder content, stale dates baked into images, mobile breakage, freebie buttons that go nowhere.

This layer is not a fallback for when the crawl comes up short — it's the correction layer that outranks the crawl every time the two disagree, because it reflects the real click-through experience a static fetch cannot capture (friction, tone, whether a wall is a permission gate or a hard 404, whether a "broken" freebie is actually a manual-delivery lag).

Reconciliation rules (Haytham's notes > vision pass > machine checks):
- **Where user observation and crawl agree:** confirmed, move on.
- **Where they conflict:** the user's observation wins (and the vision pass wins over the machine text checks). Note briefly why the lower layer missed it (logged-in view, geo-gated, JS-rendered content the fetch couldn't see, etc.) if it's discoverable, but don't block on figuring that out.
- **Where the crawl flagged a gap and the user's notes fill it:** merge — this is the expected, common case (comment-gated freebies, DM flows, paid checkouts).
- **Where the crawl found something the user's notes don't mention:** keep it if it's clearly evidenced (e.g. a stale date, a dead link) — the user may simply not have walked that particular stop.

If, after both passes, some stop still has no observation from either source, leave it unremarkable rather than inventing a finding.

If you have neither a Notion page/site URL to crawl NOR any user-provided observations (just a bare lead name), tell Haytham you need at least a link to crawl or one stop's worth of notes before you can walk. Don't invent findings.

Read `references/walk.md` and `references/schema.md` now, before doing anything else past this point.

---

## Step 0.5 — The floor (added Jul 2, 2026, from pipeline evidence)

No automatic dedup query here — querying the pipeline on every single walk was burning tokens for a check that's rarely the actual failure point. If Haytham already has the lead's Notion page open or pasted, that page IS the dedup check; a walk on an existing row just overwrites it fresh, which is fine. Only query the pipeline for a name/URL match if something feels off — e.g. Haytham pastes a lead with no page link at all, or a name that rings a bell — and even then, one targeted query, not a routine step.

**The floor.** Gate 0 (sourcing) is supposed to happen upstream, but the rows prove it doesn't always, so the walk enforces a minimum before any touches get spent:

- **Audience floor:** roughly 1K followers or an equivalent real audience signal (podcast, list, active community). Receipt: Blanka Kellermayer, 115 followers, burned three touches on an account that cannot pay even the smallest price point.
- **Activity floor:** last post or visible activity within ~3 weeks. Check this against the Step A search results, not secondhand notes — the search is what actually tells you if she posted recently. Receipt: Lisa Chan, 7 weeks silent, correctly parked, but only because the user caught it by instinct. Now it's a rule, and now it's verifiable directly instead of trusted on faith.
- **Niche floor:** parenting or faith-based, genuinely. Adjacent wellness niches without the case-study fit get parked. Receipt: Gayu Lewis, menopause coach, her own row said "not parenting" and she got three touches anyway.

Failing the floor = Lane 3, reason noted, stop. The floor exists to protect touches, which are the scarcest resource in a crisis.

---

## Step 1 — Gate 1 check (2 seconds)

One question only: is there a team or gatekeeper between the user and the owner?

Signs: "our team", named co-creator running ops, verified mega-account (150K+) with a manager triaging DMs.

- YES → classify as Lane 3: Skip, note reason as "gatekeeper/team," write to Notion and stop.
- NO or unclear → proceed to Step 2.

---

## Step 2 — The 5-stop walk

Work through each stop in order using the observations provided. For each stop, apply the master principle:

> A leak is any point where attention the coach already earned fails to convert toward money she can see — AND she'd feel the cost if you named it.

Read `references/walk.md` for the full stop-by-stop diagnostic questions, tier classification, and the growing list of known leak patterns. The master principle catches leaks not in the list. If something fits it and isn't listed, it's still a leak.

For each stop: note what's there, flag anything that fails the master principle, tier it (A = critical, B = strong, C = soft).

---

## Step 3 — Two filters (run on everything the walk flagged)

**Sting test:** would she FEEL this as a cost, or shrug? If she'd shrug, it's not an opener even if technically suboptimal. Demote to Lane 2 or drop.

**Vitamin filter:** is this a FELT COST (attention or money leaking now) or a MECHANISM she lacks ("you need an email list")? Mechanisms are vitamins — low cold conversion. Reframe as felt loss if possible, or hold. If it can't be framed as felt cost without manufacturing it, it's not an opener.

A finding that fails either filter is not Lane 1.

---

## Step 4 — Lane classification

Sort into exactly one lane:

**Lane 1 — OPEN (felt leak + committed buyer).** At least one flagged finding survives both filters. Use the single strongest one as the opener. Don't stack multiple findings in one email.

**Lane 2 — WARM-UP (committed buyer, no felt leak).** No finding survives both filters, but the lead is clearly a committed operator (paid ladder, multiple offers, email capture, active engagement). Opener: not a leak. Either ask-the-number entry (enter as a genuine user/peer anchored to specific content) or pure warm-up (genuine engagement over days). Note the warm-up angle.

**Lane 3 — KILL (not a buyer).** Hobbyist floor (one freebie, "just for fun"), MLM/downline, no income signal, or gatekeeper. Park as Lost/Disqualified. No opener.

---

## Step 5 — The opening angle

Lane 1 only: state the single strongest finding as the opening angle. One sentence, concrete, falsifiable, bespoke to this page. Frame as felt cost. This is what feeds into the email skill — the email skill takes this line and builds from it.

**The innocent explanation is a required second line (added Jul 2, 2026).** Alongside the finding, always output the plausible non-blame explanation for it: the calendar might just need a reset, the date might be stuck, the next round might not be set yet, the section might still be loading. The email skill turns this pair into the either/or closing question, and the pipeline evidence says that question is doing heavy lifting: all five cold openers that earned warm replies (Pam, Natavia, Louise, Helen, Amanda) closed with an either/or handing her a face-saving explanation, and the one opener that closed with a challenge and no exit (Darlynn) drew "Rude." This matches reactance research on feedback: delivery that questions competence triggers defensiveness, delivery that leaves the recipient autonomy keeps her receptive. If no innocent explanation exists for a finding, flag that to the user; it may mean the finding will read as an accusation no matter how it's phrased.

**Hook type label (data collection, added Jul 2, 2026).** When an SMYKM hook exists, label it: WORK (her framework, content, testimonial, point of view), LIFE (birthday, personal post), or METRIC (numbers she owns). All five warm-reply hooks so far were WORK-anchored; the METRIC hook went hostile and the LIFE hook is silent at touch 4. Sample is too small to make this a rule, so the label exists to let the answer accumulate — after ~30-40 more labeled sends the pattern will be checkable.

Also surface the SMYKM hook if one exists: something from their content, their story, their framework name — something only they would recognize. The Step A search is the primary source for this now — look there first for a recent post, a named framework, a launch, a personal update — rather than waiting for it to show up in the user's notes. Not required, but worth real effort before giving up on finding one.

Lane 2: note the warm-up angle or ask-the-number entry point. What specific piece of their content is the genuine entry?

Lane 3: one-line reason, nothing else.

---

## Step 6 — Write to Notion

Fetch the lead's Notion page first to get the current state. Then write the walk output to the page body in the exact format from `references/schema.md`. Update the Lane property and Finding Type property at the same time.

**Coherence rules (added Jul 2, 2026, from broken rows):**
- Lane 3 forces Tier 4 + Status Disqualified. Lane 1 or 2 can never carry Tier 4. Receipt: Arjuna O'Neal sat with Lane 1 + Tier 4 + Disqualified simultaneously, an unparseable state.
- If the lead's email was derived from a source the walk itself flagged as broken or suspect, the Status stays at Researching and the flag goes in Notes as the FIRST line, not buried. Receipt: Dr. Robyn Silverman's row noted her email came from her own broken footer address and needed verifying, and she was cold-emailed at that address anyway.
- Finding Type: prefer "Dead/stale element" for time-bound breakage (stale kickoff dates, empty calendars, dead links, expired events, placeholder content). This category, previously scattered into "Other," contains most of the warm repliers to date (Pam's stuck date, Helen's empty calendar, Louise's dead-end section). If the option doesn't exist in the select yet, add it once and use it from then on.

**Prioritization note for the user (tentative, revisit at more data):** all six warm replies to date came from accounts between 1.4K and 10.8K followers; ~25 sends to 20K+ accounts have produced zero warm replies so far. Confounded by send recency, so it's a sorting heuristic, not a gate: when the user asks which Audit Ready leads to send next, surface the sub-12K rows first.

The page body structure is strict — use it exactly. Don't improvise the format or the output won't be parseable later.

After writing, confirm to the user: lane verdict, the single strongest finding in one line, the innocent explanation, and the SMYKM hook with its type label if found. That's all they need to hand to the email skill.

---

## What this skill does NOT do

- It does not stop at crawling. Site URL, linked pages, and one lead-name search happen automatically before the walk (Step A), but the human layer — Haytham's screenshots and notes, and in automated runs the mandatory vision pass over the crawler's screenshots — is what confirms, corrects, or fills in what the crawl can't reach: logins, DM flows, comment-gated freebies, real checkout attempts. A crawl-only walk with no eyes on the screenshots is a draft, never a finished walk.
- It does not go exploring beyond what's linked. It fetches the Site URL, Profile URL, and any pages Haytham's prompt points to — it doesn't crawl arbitrary internal pages, attempt logins, or try to pay through a paid gate. Those stops rely on user observation.
- It does not invent findings. If neither the crawl nor the user's observations support a finding at a given stop, say so and move on.
- It does not draft the email. That's the email skill's job. This skill ends at the opening angle.
- It does not run Gate 0 (sourcing). The lead is already in the pipeline.
