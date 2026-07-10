---
name: haytham-funnel-auditor
description: Full senior-level funnel audit for parenting/faith-based coaching funnels — goes beyond visible leaks into copy, offer architecture, and sequencing failures. Use this skill WHENEVER Haytham asks for a full audit, a deep read, "what's wrong with this funnel," "is the copy working," "why isn't this converting," or anything that requires diagnosing invisible failures across copy, offer, and structure. Also use when preparing for a Loom, a discovery call, or a paid audit deliverable. This is the master-builder read, not the opener-finder. The opener-finder is for sourcing leads. This skill is for diagnosing funnels in depth.
---

# Haytham Funnel Auditor

Full diagnostic read of a coaching funnel — the kind a senior funnel builder does before a call or a paid engagement. Not a checklist of broken links. A layered read across copy, offer, and structure that finds what's quietly losing people.

The opener-finder (separate skill) handles the outreach walk: Gate 1, 5 stops, lane classification, opening angle. This skill goes deeper on everything the opener-finder leaves on the table. Run the opener-finder first if you haven't already. Then run this.

---

## What you need before starting

Minimum viable input: the funnel observations (screenshots, page copy, notes from the walk, or any combination). The more stops covered, the more complete the audit. You do not need all stops to begin — diagnose what you have, flag what's missing.

Read all three reference files before writing a single diagnosis line:
- `references/copy-diagnosis.md`
- `references/offer-diagnosis.md`
- `references/structure-diagnosis.md`

They are short. Reading them is what stops the audit from coming out generic.

---

## The audit sequence

### Step 0 — Vision-pass gate (check this before Step 1, every time)

If the input includes screenshots that live under an evidence directory
(`evidence/<slug>/`, produced by `main.py walk` or carried over from a prior
process-lead / opener-finder run on this same lead), the same rule that
gates those two skills gates this one: a crawl or a screenshot set with no
confirmed eyes-on-it pass is a draft, not a finished audit.

```bash
python main.py vision check evidence/<slug>
```

- **INCOMPLETE → do not proceed to Step 1.** Run `python main.py vision list
  evidence/<slug>` to see exactly which images are still unread, Read each
  one, mark it immediately after (`python main.py vision mark
  evidence/<slug> <path>`), and run `check` again. Repeat until it prints
  `VISION PASS: COMPLETE`.
- **The only exception** is a genuinely unreadable/corrupted image. In that
  case only, proceed, but carry an explicit `⚠️ vision pass incomplete:
  <path> — <reason>` line into the audit output. Never silently drop it and
  never paraphrase it as "screenshots reviewed."
- **Quote the literal `VISION PASS: ...` line** in the audit's Step 1
  surface read, not a paraphrase like "screenshots reviewed."

**If there is no evidence directory at all** — Haytham pasted screenshots,
page copy, or notes directly in chat, which is common for this skill since
it's often invoked ad hoc for Loom or call prep rather than through the full
`/batch-audit` or `/process-lead` pipeline — this gate does not apply. Say
so explicitly in the audit output: "no evidence directory — vision gate not
applicable, working from directly-provided material." Don't silently skip
past this; state it so it's clear the gate was considered and correctly
doesn't apply, not missed.

### Step 1 — Surface read (2 minutes)

Before any deep diagnosis, do one fast pass through everything provided. You are looking for the single most expensive leak: the place where the most qualified, most motivated buyer exits. That is the lead finding. Everything else is supporting detail.

Note the traffic temperature the funnel appears built for (cold, warm, hot) and whether the pages match it.

### Step 2 — Copy diagnosis

Read `references/copy-diagnosis.md`. Then evaluate the copy across every page provided:

- What stage of awareness is the copy written for? Does the traffic match it?
- Is the value proposition clear above the fold within 5 seconds, or buried?
- Are claims falsifiable and specific, or adjective-driven and vague?
- Is there a single big idea and promise, or is the page trying to do multiple jobs?
- Does every line pull the reader to the next, or does the throughline break?
- Run the "So What" test on every benefit claim: does it land on a visceral outcome or on a mechanism?
- Is there a credibility deficit — unverified claims, no proof, no specificity?

Flag each failure with the invisible failure mode it maps to (from the diagnostic matrix in copy-diagnosis.md).

### Step 3 — Offer diagnosis

Read `references/offer-diagnosis.md`. Then evaluate the offer itself:

- Is this a painkiller (immediate, felt, acute) or a vitamin (nice to have, delayed value)?
- Run the four Hormozi levers: Dream Outcome, Perceived Likelihood, Time Delay, Effort and Sacrifice. Which lever is weakest?
- Is there a guarantee? Does it actually reverse risk or is it weak/absent?
- Is pricing anchored correctly — premium first, core second — or presented cheapest-first?
- Is the value ladder connected step-to-step, or are the rungs solving unrelated problems?
- Is there an order bump or OTO at the highest-intent moment?

Distinguish clearly: is this a copy problem (the offer is fine but poorly communicated) or an offer problem (the terms of the trade are being rejected)? The behavioral tells are different. Copy failure = low time on page, early bounce. Offer failure = high time on page, deep scroll, checkout abandonment.

### Step 4 — Structure and sequencing diagnosis

Read `references/structure-diagnosis.md`. Then evaluate the funnel's architecture:

- Does each page have one job, or is it trying to educate, compare, and close simultaneously?
- Where in the Customer Value Journey is the funnel breaking? Name the stage and the failure pattern.
- Is friction appropriate to the stage — minimal at cold/opt-in, progressive as intent increases?
- What happens after the opt-in? Is there an orphan lead situation (warm subscriber, no pathway to buy)?
- What does the thank-you page do? Dead end or tactical transition?
- Does the welcome sequence fight buyer's remorse or is it dry and informational?
- Is the funnel driving cold traffic to a hot-traffic page (premature pitch)?

### Step 5 — Priority stack

Once all three domains are diagnosed, order the findings by revenue impact:

1. The single most expensive leak (highest qualified traffic exiting, highest intent lost)
2. Secondary structural issues
3. Copy refinements
4. Nice-to-haves

Never present a flat list of 12 equal problems. The coach needs to know what to fix first.

### Step 6 — Output

Deliver the audit as a structured written output, not bullets. Each finding gets: what it is, where it lives (which page, which element), why it's costing her (the felt cost, not the mechanism), and what the fix is in one line.

Use the voice from the email skill: peer, not consultant. Direct but not clinical. "Here's what I'd fix first and why" energy, not "our diagnostic framework identified the following suboptimal conversion elements."

If this audit is for a Loom, structure the output as talking points in the order you'd walk the page on screen — not a written report. Flag this if that's the use case.

---

## What this skill does NOT do

It does not replace the opener-finder. Lane classification and opening angle are the opener-finder's job.

It does not write the email. That's the email skill's job.

It does not invent findings. If a domain has no observations to work from, say so and flag what would need to be checked.
