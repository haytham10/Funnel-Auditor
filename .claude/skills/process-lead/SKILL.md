---
name: process-lead
description: Take a sourced Instagram lead from raw intake (name + bio link + follower count) all the way to an approved cold-email draft. Use this skill WHENEVER Haytham pastes a new lead — a handle, a link-in-bio URL, a follower count, optionally notes or screenshots — or says "process this lead," "run this one," "new lead," or pastes several candidates from a sourcing session. It runs the machine funnel walk (Python), enforces the Gate 0 floors, logs to the Notion pipeline, hands the evidence to the opener-finder, then the email-draft skill, and finishes with a Gmail DRAFT awaiting his approval. It never sends anything and never touches Instagram.
---

# Process Lead — intake → walk → Notion → opener → draft

One command per candidate. Haytham sources on Instagram by hand (that stays
manual — no IG automation, ever); this skill takes over the moment he has a
candidate's public info.

## Input

Minimum: a link-in-bio / site URL. Wanted: contact name, IG profile URL,
follower count. Optional: email if already known, niche hint, his own notes or
screenshots from clicking around, Source (how he found them).

If several leads are pasted at once, process them one at a time, start to
finish, and give a one-line verdict per lead at the end.

If only an IG profile URL is given with no bio-link URL: do NOT try to fetch
Instagram. Run a web search for the person instead; if that surfaces their
site/linktree, use it. Otherwise ask for the link in their bio — that's the
one thing only he can see.

## Step 1 — Machine walk

```bash
pip install -q -r requirements.txt   # first run only
python main.py walk <bio-link-url> --name "<Name>" --handle "<@handle>" --followers <N>
```

Read the resulting `evidence/<slug>/packet.md` and `evidence.json`. Read the
bio page desktop screenshot, plus the screenshot of any page the packet
flagged. Read the page text files for the sales/freebie pages — the copy is
where non-mechanical leaks live.

If the crawl errored on the bio page, that is itself a possible Tier A finding
(verify: hard 404 vs permission wall) — don't abandon the lead.

## Step 2 — Floors (Gate 0, full version)

The packet gives the machine half. Complete the rest:

- **Activity floor**: one web search on the lead's name + niche/handle. Last
  visible activity within ~3 weeks? While there, collect SMYKM hook material
  (recent post, launch, named framework, personal update) — needed later.
- **Niche floor**: genuinely parenting or faith-based. Adjacent wellness
  without case-study fit = park.
- **Audience floor**: ~1K followers or an equivalent real audience signal.

Any floor failed → Lane 3. Create/update the Notion row (Lane 3 forces
Tier 4 + Status Disqualified, one-line reason in Notes, properties only, no
body) and stop. The floor exists to protect touches.

## Step 3 — Notion row

Pipeline data source: `collection://c6209e29-55ef-4781-b735-73b2a254e34f`.

Dedup per the opener-finder's rule: no routine pipeline query — only run one
targeted query if something feels off (name rings a bell, lead arrives with
no page link). If a row already exists, update it instead of creating one.

Create the row with what's known: Contact Name, Profile URL, Site URL,
Followers, Source, Email (if found — see Step 5), Status = Researching.

## Step 4 — The walk (judgment half)

Now invoke the **haytham-opener-finder** skill logic with:
- the evidence packet as Step A (the crawl + search layer, already done), and
- Haytham's notes/screenshots as Step B (the human read — it OUTRANKS the
  machine layer wherever they disagree).

Follow that skill exactly: Gate 1, 5-stop walk, sting test + vitamin filter,
lane classification, opening angle + innocent explanation + SMYKM hook with
WORK/LIFE/METRIC label. Machine-flagged candidates in the packet are
candidates only — they still have to survive both filters. Write the page
body and properties to Notion in the exact schema.md format.

## Step 5 — Email address

Work the Email OS decision tree with what the packet harvested:
1. Personal-looking address from the crawl → use it.
2. Generic (info@/contact@) → use only if nothing better.
3. Nothing harvested → web search (`"[name]" OR "[handle]" email contact`),
   podcast/YouTube show notes.
4. Still nothing → set Notes first line "email not found — freebie opt-in or
   pattern-guess+verify needed" and leave Status = Researching. The freebie
   opt-in and NeverBounce/Hunter verification are Haytham's manual steps.

If the email came from a source the walk flagged as broken/suspect, Status
stays Researching and that flag goes in Notes as the FIRST line.

## Step 6 — The draft

Lane 1 or Lane 2 with an email address → invoke the **haytham-email-draft**
skill for the Touch 1 opener. Full silent loop, voice rules, gate — as that
skill specifies. Deliver labeled variants.

Then STOP and wait:
- On approval of a variant → create a **Gmail draft** (never send) to the
  lead's address with the chosen subject and body.
- On "log this" → do the full Notion logging + property diff exactly as the
  email-draft skill specifies (Status Audit Ready → Outreach Sent only after
  he confirms it was actually sent).

## Hard rules

- Never send an email. Gmail drafts only. Sending is Haytham's hand.
- Never fetch, scrape, or automate anything on instagram.com.
- Never invent findings; a walk with nothing that survives the filters is
  Lane 2 or Lane 3, not a manufactured leak.
- One lead's full run ends with: lane verdict, strongest finding, innocent
  explanation, SMYKM hook + label, email address status, and (if applicable)
  the draft variants. That's the complete hand-off.
