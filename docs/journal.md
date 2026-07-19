# Project Journal — cross-session memory

The narrative git history and Notion don't capture: **what happened each
session** (pipeline ops AND dev), the decisions behind it, gotchas learned, and
open follow-ups. Notion holds live *state* (where each lead is); git holds *code
changes*; this file is the thread that ties sessions together so a fresh session
isn't starting cold.

**How it's used:** the `SessionStart` hook (`.claude/hooks/session_memory.py`)
injects the most recent entries here + the last few commits at the top of every
session, so context loads automatically — no fetch, no prompting.

**How to write it:** at the end of a session with anything worth remembering,
add a new `## ` block at the TOP (newest first), then commit + push. A
journal-only commit is fine on an ops-only session — the point is that it
survives the ephemeral container. Keep entries short and scannable: a few
bullets, then an `### Open follow-ups` list if any are outstanding.

Entry template:

```
## YYYY-MM-DD — <one-line title>
- what happened (ops events, sends, sourcing, ticks, or code)
- decisions made and why
- gotchas / things that surprised us
### Open follow-ups
- [ ] the next thing someone should pick up
```

---

## 2026-07-19 — Ops: 14 cold Touch-2 follow-ups drafted (held) for send-day 2026-07-20
Prepared tomorrow's due follow-ups so Haytham can schedule them in the morning. Query: Next Action ≤ 07-20, cold, Outreach Sent → 14 leads, all Touch 1 sent 07-17 (day-3 bump).

- **All 14 `crm-gate send --touch 2` PASS.** Carrier = `second-finding` (bank #2) for 13; **Jana Masri Vintrova** carried `loom-offer` (single-finding row, no #2). Each draft is a threaded reply in the existing thread, same subject, second finding as a felt cost + innocent explanation, fix left vague, one fresh question.
- **Inbox 1 (8, Gmail MCP drafts):** Kelly Allison, Aliya Rajah, Jana Masri Vintrova, Neha Nimje, Sarah Aboubi, Adam Ashcroft, Marie Graver, Ewa Ledeboer.
- **Inbox 2 (6, gmail-gethaytham drafts):** Jihane Labib, Sarah Boutros, Aman Merchant, Tanner Shuck, Chetna Chakravarthy, Avneet Kohli.
- **Send-day 07-20 ceiling holds (cap 20/inbox):** Inbox 1 = 8 scheduled openers + 8 follow-ups = 16 ≤ 20; Inbox 2 = 7 scheduled openers + 6 follow-ups = 13 ≤ 20. Room to spare on both.
- **Neha threading note:** Touch 1 to `neha@bizexconsultancy.com` bounced (550) on 07-17 and was resent to the verified `contact@bizexconsultancy.com` (thread 19f6f429dc3ffb9f) — follow-up threaded onto the live contact@ thread, not the bounced one.
- No CRM writes: a draft is not a send. Status stays Outreach Sent; Touch #/Last Contacted/Thread Log/bank #2 → USED-T2 move only on actual departure (uae-tick reconciles on the send-day).
- **Two warm rows due 07-20 left for Haytham's call, NOT batch-drafted:** **Christina Steinhoff** (Inbox 1) — replied twice with an identical canned "call/message my phone +971-562737368" autoresponder; low-signal, possibly an auto-reply. **Lisa Hugo** (Inbox 2) — turn-two (finding #2, podcast fix) already SENT 07-17 (the "held draft" note in her bank was stale; no Gmail draft exists); she engaged then went quiet after the finding-#1 correction. Both want individual warm handling, not a scheduled cold bump.

**Update (same day): Haytham SCHEDULED all 14 in Gmail for 07-20.** No "Scheduled" status exists for a mid-sequence Outreach Sent row, so instead each of the 14 rows got a `Notes` marker: `T2 scheduled 2026-07-20 (Inbox N), held draft threaded — log Touch 2 on departure, bank #2 → USED-T2`. This is the reality record that stops tomorrow's tick from re-drafting a duplicate Touch 2 (Chetna already ate one duplicate-send incident on 07-18) and reminds it to log on departure. Send-day 07-20 load is now: **Inbox 1 = 16 (8 openers + 8 follow-ups), Inbox 2 = 13 (7 openers + 6 follow-ups)**, both ≤ 20.

### Open follow-ups
- [ ] Decide Christina + Lisa warm moves (offered to draft either on request).
- [ ] uae-tick 07-20: rows carry the `T2 scheduled` Notes marker — do NOT re-draft; on each follow-up's departure, log Touch 2 (Last Contacted, Next Action +6 → Touch 3 day 9, Thread Log, bank #2 → USED-T2, clear the marker). Jana's Touch 2 spends no bank (loom-offer). Watch Neha's contact@ for a second bounce (two strikes = stop).

## 2026-07-19 — Ops: all Draft Ready scheduled for 2026-07-20 + Samira duplicate flagged
- Haytham scheduled EVERY Draft Ready lead in Gmail for send-day 2026-07-20 (~09:00 Dubai). **8 in Inbox 1:** Nabil, Caroline, Aleli (this session) + pre-existing Sadia Khan, Bonge Gumede, Monika Singh, Asma Ahmad, Dr. Jamila Al Hosani. **8 in Inbox 2:** Sabeen, Sanjukta, Trisha, Samira (this session) + Kalyani Seth Soni, Dr. Corrie Block, Nikki Evans + a Samira duplicate. **15 leads, 16 sends.**
- Flipped all 15 CRM rows `Draft Ready → Scheduled`. Nothing else moved — Touch #/Last Contacted/Thread Log/Findings Bank move only on actual departure; uae-tick reconciles → `Outreach Sent` on the send-day.
- ⚠ **Samira Alexander has TWO scheduled sends** for 2026-07-20: mine (subject "time to show up", body "Ten years mostly behind the scenes") and a stale prior-session draft (body "Ten years of doing the work quietly... into something calmer"). Couldn't read the stale one's recipient or cancel it via tooling (message/thread `message` lookups 404 once scheduled; `drafts` list empties). Flagged on her Notion page.
### Open follow-ups
- [x] Haytham CANCELLED the duplicate Samira scheduled send in Gmail (07-19) — only "time to show up" remains scheduled for 2026-07-20. CRM note updated.
- [ ] uae-tick 2026-07-20: reconcile the 16 scheduled sends → Outreach Sent (Touch 1, Last Contacted, Thread Log, Findings Bank #1 → USED-T1) as each departs; watch Caroline's heal@ for a bounce.

## 2026-07-19 — Ops: hook+draft stage → 6 Audit Ready leads drafted (Draft Ready)
Ran the merged draft-first `haytham-hook-finder` batch over the full Audit Ready view (6 leads). All 6 taken from empty-hook → held Gmail draft.

- **The 6:** Nabil El Fquir, Caroline Bakker, Aleli Carissa Gimena (→ Inbox 1); Sabeen Javed, Sanjukta Ghosh, Trisha Hazarika (→ Inbox 2). All Lane 1, both hard gates already set. 3/3 inbox split via `inbox route` (headroom policy) on tomorrow's fresh send-day.
- **Hooks:** 6 hook-workers fanned out → 6 hook-verifiers re-fetched each citation and wrote the line. **6/6 VERIFIED, all WORK-anchored, zero refutations** (quality tripwire not hit). Sources: Nabil Jul 15 LinkedIn networking-reframe post; Sabeen Jul 4 LinkedIn Founding-Cohort launch; Sanjukta Jul 18 World Listening Day post; Aleli Jul 18 IG "Desire Everything, Need Nothing" call theme; Trisha Jul 17 "Friday Things" discovery-call post; Caroline her book *The Healing Journey* origin story (Goodreads-verified, ~18mo old but genuinely hers — only thin IG in 60d).
- **Gate/draft:** email-check all pass (Aleli WARN role-account `hello@`, accepted; already Email Verified). `crm-gate send --touch 1` PASS on all 6, gated against tomorrow's ceiling (past-noon roll → send-day 2026-07-20). Drafts created (Inbox 1 = Gmail MCP, Inbox 2 = `gmail-gethaytham draft`), Status → Draft Ready, draft marker in Notes. Touch #/Last Contacted/Thread Log/Findings Bank left untouched (move on confirmed send).
- **Gotcha:** Notion MCP `query_data_sources` was hard-capped for the hour (free-tier entitlement), so no `WHERE Status='Audit Ready'` query. Fell back to semantic search (missed Caroline Bakker entirely) — Haytham's Audit Ready screenshot was the authoritative list that caught her. Worth remembering when the SQL cap hits mid-run.

### Open follow-ups
- [ ] Haytham: review the 6 Draft Ready drafts in Gmail and send/schedule by hand. On confirmed send, uae-tick logs Touch 1 + flips Findings Bank #1 → USED-T1 + clears the `run haytham-hook-finder` Notes lines.
- [ ] Caroline Bakker: `heal@sacredwarriormedia.com` is a bounce-risk accept (email-verify WARN) — watch for a bounce on her first send.
- [x] Samira Alexander: Haytham confirmed the hook pairs (Jul 17 "time to show up / come join me" IG post vs the sitewide dead Book-button Calendly — invitation live, door stuck). Drafted 07-19, Inbox 2, subject "time to show up" → held Draft Ready (7th draft this batch). crm-gate send PASS, email-check PASS (catch-all accepted, not re-verified).

## 2026-07-19 — Dev: Qualifying resolve-then-decide + merged draft-first hook+draft stage
Follow-on dev session to the 4-stage rebuild (#60), on `claude/email-draft-examples-skills-5cp2w0`, restarted from `uae-track`. Two changes.

**1. Qualifying overhaul — resolve-then-decide, cheapest tool per datum (commit b7fb96e).** The stage was Firecrawl-only, so leads whose audience lives on a login/JS-walled channel (LinkedIn, IG, **YouTube**) stalled at "Held for manual review / Not checked" even though a few-cent actor call settles it (journal #59: an `li-profile` re-run cleared 5 held rows instantly). It also never resolved the Profile↔Site URL swap. Fix, all wiring + discipline (no `gates.py` change — it's a correct scorer, just feed it resolved data):
- **New blessed actor (code):** `youtube_channel` → `apidojo~youtube-channel-information-scraper` in `audit/apify.py` ACTORS map + a gated `youtube_channel()` wrapper (cost-gate first, trims to name/handle/subs/videos/views/joinedAt/description), `apify youtube <channel|@handle>` subcommand in `main.py`, doc row in `apify-actors.md`. ~$0.0005/channel, single-item call auto-clears the $0.10 gate. Verified live: Aleli = 22,200 subs (passes the 1,500 floor); the `description` field also carries the funnel link + a +971 UAE phone (a second-floor signal). `youtubeHandles` input for @handles / `youtube.com/@` URLs (`startUrls` returned 0 items for those; reserved for `/channel/UC..`).
- **Datum→cheapest-tool map** encoded in `qualifier-worker.md`: audience via `li-profile.followerCount` / `ig followersCount` / `youtube subscriberCount`; activity via `li-posts --since month` / `ig posts` / Firecrawl `/videos`; UAE-base via `location.full` / +971 in a description; funnel floor stays Firecrawl-only. Plus the URL swap (write back the resolved Site/Profile URL), honest holds for directory-only leads (one search, then a real audience-floor Fail — not an indefinite hold), and cost discipline (~$0.05/lead Apify ceiling, `needs_approval` → surface don't retry, `near_cap` → skip actors).
- **Verifier parity:** `qualifier-verifier.md` was Firecrawl-only and **overturned correct actor-resolved promotions it couldn't re-see** — now it re-checks with the SAME actor the worker cited ("Firecrawl couldn't see a LinkedIn/YT count" is not grounds to overturn — re-run the actor first).
- **Up-front guard** in `qualify-leads/SKILL.md`: `pip install -q -r requirements.txt` + `apify limits` once per run (a missing dep once silently degraded the whole CLI to Firecrawl while `APIFY_TOKEN` was present), `near_cap` note passed to workers.

**2. Merged hook+draft stage — draft-first (this session, docs only, no code).** Hook-finding and drafting were two steps with a bare-hook approval gate between them. Haytham's steer: **"draft first, review drafts."** Now `haytham-hook-finder` batch mode is ONE stage: per Audit Ready lead → `hook-worker` proposes → `hook-verifier` (cold context, sole writer of the hook line) → the orchestrator **drafts each resolved lead** into a held Gmail draft (`Status = Draft Ready`), and Haytham reviews finished drafts in Gmail, not a hook table. No code needed — the gates (`crm-gate send`, `draft_lint`, the PreToolUse link guard) already enforce everything. **Anti-fabrication independence preserved:** the draft step re-reads the Notion hook line the verifier wrote, never the worker's proposal; worker/verifier/draft never collapse into one context. Propagated the walk-ends-held-at-Audit-Ready framing through `process-lead` (Step 6 is now a hand-off, not a duplicated draft), `batch-audit`, `agent-orchestration.md` (stage 4 = hook+draft), `01-crm-operating-spec.md` (Audit Ready → Draft Ready is one stage), `haytham-email-draft` (two invocation modes note), and `CLAUDE.md`.

### Open follow-ups
- [ ] First real draft-first run is the natural live smoke test of Change 2 (creates a real held draft on an Audit Ready lead) — not forced this session since it mutates production Notion/Gmail state.
- [ ] Optional cost-governance hole flagged, not done: the caprolok/vulnv email-finders still run via un-gated `run_actor`. Wrapping caprolok into `ACTORS` under the cost gate closes it (small, cost-positive, but enrichment not qualifying).

## 2026-07-19 — Dev: UAE-first email examples + full agent-layer rebuild into a verified 4-stage pipeline
Big dev session, no ops. Three workstreams, all on `claude/email-draft-examples-skills-5cp2w0` (3 commits).

**1. Email-draft examples, UAE-first.** `references/examples.md` was 100% parenting-track and pre-pivot. Reshaped UAE-first from REAL sent copy in the CRM Email Thread Logs: Aliya opener (WORK hook), Carol Glynn cold opener + cold Touch-2 carrying a NEW banked finding (the payload rule / anti-Heba contrast), Donna full warm arc incl. the real price-discovery email. Trimmed parenting to top anchors (Amanda / Helen priced-close / Emily Ray Lane 2 + the two anti-patterns); cut Louise (dup of Helen + the 550 AED error), Catherine, Pam, Lisa Smith, Ghadir. Reframed the Heba same-finding-bump section as parenting-era, superseded by the UAE carrier rule. **Baked-in note: no real UAE money-email example exists yet — every Price Discovery Answer/Anchor in the CRM is still null (nobody has answered the price question); Helen stays the priced-close shape anchor.**

**2. Skill staleness sweep (all flagged).** batch-audit 15-vs-20 cap; pipeline-tick "one domain"→Inbox 1; qualify-leads `send-cap status`→`--all` + per-inbox; process-lead + crm-operating-spec "one shared domain"→sending domain; opener-finder singular ceiling; funnel-auditor description.

**3. Agent-layer rebuild — the main event.** Root cause of low agent quality (this journal, Corrie/Roota): every stage let ONE context self-certify the claim that ships. Fix = one shared chassis (`docs/agent-orchestration.md`): fan out least-privilege workers → an INDEPENDENT verifier re-checks the self-certified claim → cross-check Notion → size the batch to downstream demand. Applied to all four stages:
- **Walk:** lead-processor now PROPOSES the finding (tools allowlist so "never send" is tool-enforced, pinned model, ~130 dup lines → pointer to process-lead, JSON return); new **finding-verifier** re-derives it from the screenshots and is the ONLY thing that checks `Finding Verified`. Propagated to process-lead / opener-finder / schema.
- **Hook (highest-value):** hook-finder batch mode → orchestrator; new **hook-worker** (proposes, writes nothing) + **hook-verifier** (re-fetches the cited URL, re-matches quote/date, rejects generic copy — enforces "never fabricate a hook").
- **Qualify:** qualify-leads → orchestrator (batch-of-rows grain); new **qualifier-worker** + **qualifier-verifier** (re-checks every promotion/kill, audience provenance).
- **Source:** source-leads → orchestrator (fan out by vein, workers RETURN, orchestrator owns cross-vein + live-CRM dedup); new **sourcing-worker** + **sourcing-verifier** (link/offer/audience-seen).
- batch-audit: cap fix, Step 2.5 verifier dispatch, quality tripwire (pause on ≥2 refutes), prompt checklists, demand-driven sizing. CLAUDE.md pipeline + Key-pieces reworked to point at the chassis.

Decisions: **opus pinned on every worker + verifier** — efficiency comes from least-privilege tools + de-dup + verifier-only-on-consequential-subset + demand-driven sizing, NOT model downgrade (cheap worker feeding a verifier = garbage-in); sourcing/qualifying workers are the tier-down candidates if cost ever bites. **crm_gate.py unchanged** — same checkboxes, trustworthy provenance now (no CRM migration). Drafting stays in-context (already code-gated by draft_lint + the PreToolUse guard + crm-gate send).

### Open follow-ups
- [x] **finding-verifier + hook-verifier smoke-tested (2026-07-19), both directions, on real leads — the two send-critical gates are proven.** finding-verifier on Aliya Rajah: a false "homepage 404s" claim → REFUTED (homepage is live 200, no write), the real Live-Workshops-subpage-404 → VERIFIED; the test also surfaced + fixed a latent status-regression bug (`8640d56`: promotion is now one-directional, only Qualifying→Audit Ready, never regress a sent lead). hook-verifier on Nikki Evans: her real origin-story hook cited to her own site → VERIFIED (quote reproduced, passed generic-copy + namesake tests), a fabricated "closing to launch Bali retreats" claim on that same real page → REFUTED (wrote the honest "no hook found" fallback). All report-only, zero CRM mutation.
- [ ] **Still unexercised:** qualifier-verifier + sourcing-verifier, and a full end-to-end batch-audit run wiring worker→verifier→brief (+ the hook orchestrator's fan-out). Run a small real batch before relying on the pipeline unattended.
- [ ] **Fingerprint gap:** `skills_authoritative.py` globs `skills/*/SKILL.md`, not `.claude/agents/*.md` — the 8 agent files sit outside SessionStart authority. Consider extending the glob to `agents/*.md`. Mitigated by keeping agent files thin (logic lives in the fingerprinted process-lead).
- [ ] Notion SQL (`query-data-sources`) hit its free-tier cap mid-session; `notion-fetch`/`notion-search` kept working. Use those or wait for reset if it recurs.

## 2026-07-19 — Qualified top-10 of Sourced pile via 3 agents; LinkedIn actor unblocked → 6 new Walk Queue leads
Ran `qualify-leads` over the 10 most promising `Sourced` rows, split across 3 general-purpose agents. First pass promoted only **1 (Aleli Gimena)** — nearly every other row was stuck on an unconfirmed audience floor because the agents used Firecrawl, which hard-refuses LinkedIn, and stopped there.
- **Gotcha (root cause):** the agents never fell back to the no-login `main.py apify li-profile` actor — and it wouldn't have run anyway: the fresh container was missing deps (`ModuleNotFoundError: rich`), so the whole `main.py` CLI was broken. `APIFY_TOKEN` was present. Fixed with `pip install -r requirements.txt`; the actor then pulled every LinkedIn follower count first try.
- **Lesson to bank:** in qualify-leads, when a lead's only blocker is a LinkedIn follower count, reach for `apify li-profile <url>` (and `li-posts` for the 30-day activity floor). Firecrawl will never crack LinkedIn.
- **Second-look results** (5 held rows, actor-confirmed follower counts): Sabeen Javed 17,583 ✅, Nabil El Fquir 8,008 ✅, Trisha Hazarika 5,512 ✅ (correct-spelling profile; the 112K "Trishna" was rightly rejected), Sanjukta Ghosh 3,164 ✅ (li-posts showed a post 23h ago → activity confirmed), **Agrim Gupta 2,812 → DQ** (audience passes but newest LinkedIn post Jan 2026, fails 30-day activity).
- **Caroline Bakker → Qualifying** on Haytham's explicit UAE-base call (audience 8.2K IG / 5.57K YT + funnel + activity already passed; only location was conflicting).
- **Top-10 final: 6 Qualifying** (Aleli, Sabeen, Nabil, Trisha, Sanjukta, Caroline) → Walk Queue; **4 DQ** (Simon Ree non-UAE+team, Prashant Welling activity, Aimee audience 307, Agrim Gupta activity).
### Open follow-ups
- [ ] `batch-audit` the 6 new Walk Queue leads.
- [ ] 5 `Sourced` rows remain unqualified on audience (Humaira, Hasina, Tahani, Dr. Shamma, Coach Mezyan, Nadine, etc. — directory listings with no scrapeable follower channel) plus Daria/Szilvia/Blair/Wafa/Ramy/Rajiv/Caroline-adjacent — most need a no-login IG/LinkedIn follower pull, same actor path.

## 2026-07-19 — Second wave: 4 fresh audits + hook→drafts → entire Qualifying bucket (12) resolved, 9 drafts held
Continued the sweep. The whole Qualifying bucket is now terminal: **9 Draft Ready, 1 Lane 2 (Roota), 2 DQ (Danish Gate 0, Sahar unreachable).**
- **4 never-walked fresh leads audited** (lead-processor agents), all landed verified Lane 1 findings — notably a run of dead-link/booking leaks:
  - **Monika Singh → Audit Ready → Draft Ready.** Finding: flagship group program is waitlist-only, no intake date/price. Email `monika.s@monikasphere.com` PASS. Hook: her Jul 14 IG "the ordinary days you almost skipped" POV. Draft "the days you almost skip" (Inbox 1).
  - **Sadia Khan → Audit Ready → Draft Ready.** Finding: "Book a 1:1 Session" buttons all load a dead Calendly. Her domain is catch-all (enrich HOLD) → Haytham supplied `Therapybysadia@gmail.com` from YouTube (verify PASS). Hook: her own "3M Method" (Master Yourself/Women/Relationships), namesake-locked to the Dubai Sadia via a YT episode transcript. Draft "master yourself first" (Inbox 1).
  - **Asma Ahmad → Audit Ready → Draft Ready.** Finding: sitewide "Free Clarity Webinar" CTA 404s to a dead Lovable app. Email `info@luminapathscoaching.com` catch-all, Haytham accepted. Hook: her "Soulful Serenity" masterclass. **Timing fix:** hook said "tonight" (Jul 19 event) but Touch-1 openers roll to the 07-20 send-day, so I reworded it to past tense ("last night"), trashed the stale draft, rebuilt it ("soulful serenity last night", Inbox 1).
  - **Sahar Huneidi Palmer → still Qualifying (email-blocked).** Finding: two e-courses show AED 0.00 on the paid storefront (vision 12/12). Email genuinely dead: `sahar@saharhuneidi.com` FAIL x2, and enrich proved the domain is NOT catch-all (MXroute infra), so it's a real dead mailbox, not an anti-harvest false-negative — even though her WordPress site aggressively ASN-bans (it blocked Haytham's own Maroc Telecom AS36903 from viewing the site). Her YouTube "About" lists the same dead address. Only unlocks via a manual test-send or the WhatsApp pivot (+971 55 635 1302). **DQ'd 2026-07-19 (Haytham's call)** — no reachable email, Lost Reason Other; gates + finding held, so revivable if a working address ever surfaces.
- **Corrie draft rebuilt by hand.** The agent's first version was missing the "Hey Corrie" greeting AND offered the Loom in Touch 1 (the other 5 openers end on a bare question; Loom is a later-touch carrier). Haytham trashed it; I hand-wrote a clean replacement ("the uncoachable ceo", greeting + bare question, no Loom).
- **Independently rechecked all drafts** (Haytham: "I don't trust the agents"): pulled the actual Gmail bodies on BOTH transports, ran each through `audit/draft_lint.py` + copy-rule checks (em-dash/jargon/weak-closer/Haytham-signoff), and cross-checked every draft's to-address, inbox, hook, and finding against the CRM. All matched; the only miss was Corrie's greeting/Loom (fixed).
- **9 drafts now Draft Ready (all held, send tomorrow 07-20):** Inbox 1 = Jamila, Bonge, Asma, Sadia, Monika; Inbox 2 = Kalyani, Samira, Nikki, Corrie. Send-day 07-20 load: ~10 follow-ups + 5 openers on Inbox 1, 4 openers on Inbox 2 — under the per-inbox 20 ceiling, but Inbox 1 is filling.
### Open follow-ups (manual, Haytham)
- [ ] Send the 9 held Touch-1 drafts tomorrow (07-20); run `crm-gate send` per inbox at send time (Inbox 1 is the tighter one).
- [x] Sahar DQ'd (unreachable by email) — revive only if a working address ever surfaces (manual YouTube read / she fixes the mailbox), then it's a fresh start from her verified finding.
- [ ] Delete any residual stale Inbox 2 draft (Roota "your khaleej times feature") by hand — no delete API on that transport.
- [ ] Run hook→draft nothing further needed on this bucket; next is sending + reply-handling.

## 2026-07-19 — Blocked Qualifying pile worked to conclusion (8 leads, ~9 agents): 4 drafts held, 2 re-walk→Audit Ready, 1 Lane 2, 1 DQ
Ran a wave of subagents over the stuck Qualifying leads after the email-finder pass. Every lead reached a real terminal-ish state. All drafts are HELD (nothing sent).
- **Bonge Gumede → Draft Ready (Inbox 1).** Email cracked: Haytham found `gumedebongebusiness@gmail.com` on her YouTube (the one surface crawlers can't reach — YT business email is captcha-gated); verify PASS → adopted, Email Verified YES. The Shopify `contact@` re-verified FAIL (matches its prior double-bounce). Hook = her "fitness is for being physically USEFUL, not physically expressive" framework (June 29 IG post, verified current). Touch-1 draft subject "building capable bodies" (stale-May-banner finding).
- **Danish Ali → DISQUALIFIED (Gate 0, not UAE).** Haytham added `danishali.help@gmail.com` (verify PASS) + `dan1ali@yahoo.com` (WARN). But a residency check found strong Pakistan signal (IG "reloading in Pakistan", "NIC Karachi hosted a coaching session with Danish Ali Malik", TikTok actor/comedian, "pioneered influencer marketing in South Asia") and ZERO UAE signal — the earlier-rejected "Karachi namesake" IS him; City=Dubai was a sourcing error. Set Status Disqualified, Gate 0 Fail, City Unconfirmed, Lost Reason "Wrong fit". A working email is moot when Gate 0 fails. (Haytham confirmed the DQ.)
- **Kalyani Seth Soni → Draft Ready (Inbox 2).** Drafted to the accepted `kalyani@sheinvests.me` (info@ was dead). Hook = her She Invests Show podcast (AI/Money ep w/ Abha Malpani Naismith); finding = checkout trust-stats shrink vs sales page. Subject "the ai and money episode".
- **Jamila Al Hosani → Draft Ready (Inbox 1).** Full hook→draft. Hook = her near-daily Arabic LinkedIn leadership posts (each closes with "رسالة التمكين" + a practical self-assessment tool). Subject "the best performer isn't the leader"; finding = "Price on request" sitewide vs live AED 550/750 booking.
- **Samira Alexander → Draft Ready (Inbox 2).** RE-WALKED her REAL funnel `rapidmindredesign.com` (not the peripheral Baxsan resell .store the old finding lived on). NEW vision-confirmed finding: every "Book" CTA sitewide lands on a dead Calendly ("This Calendly URL is not valid") — her only conversion action is broken. Baxsan finding archived, Site URL switched, Finding Verified YES. Hook REFRESHED to her Jul 17 IG "time to show up / anxiety to abundance" post (pairs tightly with the dead button). Subject "showing up after ten years".
- **Nikki Evans → Audit Ready (needs hook-finder).** RE-WALKED the REBUILT site. Old "4 unranked offers/no opt-in" finding RETIRED (homepage now has ranked CTAs). NEW verified finding: /contact page never migrated in the rebuild — title tag + Google meta still read "Best Life Coach in Sydney" while every other page says "Mindset Coach Dubai". Site URL fixed, Finding Verified YES, SMYKM hook reset to "not run yet" (old LIFEFREQ/shadow-work hook is dead; live brand is Mind Health School / Emotional Mastery).
- **Corrie Block → Audit Ready (needs hook-finder).** RE-WALKED via Playwright (Firecrawl mobile screenshots confirmed UNTRUSTWORTHY on this site — full-page stitching artifacts; this is why both prior findings got refuted). Both prior findings stay retired. NEW verified finding, and it CONFIRMS Haytham's own verbal lead: his flagship Spartan CEO masterclass page (/training-topics/spartan-ceo) opens with the WRONG program's headline ("Unlock the Full Potential of Your Team") + generic team/HR copy — "Spartan CEO" appears nowhere visible. Content/headline mismatch (raw HTML + Playwright verified), NOT a layout break, so it survives the mobile-render caution. Finding Verified YES, hook reset.
- **Roota Mittal → Lane 2 (no leak).** RE-WALKED; the refuted Skool /plans overlap confirmed a render artifact (matches Haytham's phone refute). No other real felt leak on her thin Skool surface; she's a well-run operator. Correct outcome is Lane 2, not a forced send. NOTE: the agent wrongly left her at Qualifying thinking "Lane 2" isn't a Status option — it IS (schema + the earlier migration). I corrected Status → "Lane 2".
### Lessons banked
- **Firecrawl mobile screenshots are unreliable for cutoff/overlap/clipping/layout claims on some sites** (Corrie + Roota both confirmed — stitching artifacts, false overlaps). Verify any layout-style finding on Playwright/desktop or raw HTML before trusting it. Content/headline mismatches (read from HTML) are safe.
- **`caprolok/website-email-phone-finder` + domain-hopping via IG external links + Taplink scrapes** is the email-FINDER combo that worked; but a captcha-gated YouTube business email needs Haytham's manual eyes (cracked both Bonge's real address and Danish's).
- **Lane 2 is a Status value** — no-leak leads go to Status "Lane 2", not Qualifying.
- **Notion single-source SQL has an hourly rate limit** that got exhausted mid-session — property writes (update_page) still work, but SQL queries stall; gate sends on send-pattern inference if needed (uae-tick owns the authoritative daily counts).
### Open follow-ups (manual, Haytham)
- [ ] Review + send the 4 held Touch-1 drafts: Jamila (Inbox 1), Kalyani (Inbox 2), Samira (Inbox 2), Bonge (Inbox 1). All roll to send-day 2026-07-20 (drafted past noon Dubai). Run `crm-gate send` per inbox at actual send time.
- [ ] DELETE 2 stale Inbox 2 Gmail drafts by hand (no delete API): Corrie "impossible to ignore" + Roota "your khaleej times feature" (both built on refuted findings).
- [ ] Run `haytham-hook-finder` on Nikki + Corrie (both Audit Ready, hooks reset to "not run yet"), then draft.

## 2026-07-19 — Email-blocked Qualifying leads: hygiene fix + creative Apify email-FINDER pass
- **Context:** 5 Qualifying leads had a verified finding but were stuck on a
  dead/missing email (Bonge, Jamila, Danish, Samira, Kalyani). Samira & Kalyani
  bounced today but still read `Email Verified` ✅ with the dead address in
  `Email` — corrupt send-gate state. Unchecked both + cleared the dead
  addresses (and Bonge's dead contact@).
- **`main.py email-enrich` only GUESSES name@domain and verifies — it never
  FINDS a published address.** So it re-derived Samira's already-dead
  `samira@samiraalexander.com` and the verifier falsely PASSed it. Ground-truth
  bounce beats verifier PASS — did not adopt.
- **New technique — no-login email FINDER via Apify (not in the vetted set):**
  used `caprolok/website-email-phone-finder` ($0.02/result, crawls a domain for
  published emails/phones) + `vulnv/linkedin-email-finder`, driven off each
  lead's IG external links (via the existing `apify ig --mode details --raw`)
  and Taplink/link-hub scrapes (Firecrawl). Whole run ~$0.13 of the $29 cap.
- **Results:**
  - **Jamila Al Hosani — FULLY UNBLOCKED → Audit Ready.** Her Taplink hub
    published `Jamila.Alhosany1@gmail.com` (verify PASS, deliverable). Adopted,
    `Email Verified` ✅. Finding already verified → both gates pass. Also banked
    hook intel (real site escape2happiness.com, LinkedIn, TikTok, WhatsApp).
  - **Samira → candidate found.** Her IG Calendly slug led to her REAL active
    brand `rapidmindredesign.com` (phone on the site matches her CRM phone).
    Adopted `samira@rapidmindredesign.com` into `Email`, `Email Verified` NO —
    WARN/catch-all, Haytham's call. Different domain than the dead one.
  - **Kalyani → candidate found.** Site crawl surfaced personal
    `kalyani@sheinvests.me` (vs dead info@). WARN/catch-all → Haytham's call,
    `Email Verified` NO.
  - **Bonge — still blocked.** 2nd domain apbybongegumede.com only yields her
    platform vendor's support@system2.fitness; runs a Flodesk community. No
    personal address anywhere.
  - **Danish — still blocked + GATE-0 FLAG.** No owned domain, YT email
    captcha-gated, no LinkedIn. His bio (20yr comedy / South-Asia influencer /
    3M followers) suggests the earlier-rejected "Karachi namesake" Gmail may be
    him — reconcile UAE-residency before more effort.
- **Actor note:** `caprolok/website-email-phone-finder` was the MVP and is worth
  considering as a proper `main.py apify find-email` command if this recurs —
  but it's cost per result and the catch-all problem still caps its value on
  domains like sheinvests.me / rapidmindredesign.com.
- **UPDATE (same day):** Haytham ACCEPTED both catch-all addresses. Samira
  (`samira@rapidmindredesign.com`) and Kalyani (`kalyani@sheinvests.me`) now
  `Email Verified` ✅ → both moved to **Audit Ready**. So 3 leads reached Audit
  Ready from this pass (Jamila + Samira + Kalyani), all ready for
  `haytham-hook-finder`.
### Open follow-ups
- [ ] Run `haytham-hook-finder` on the 3 new Audit Ready leads (Jamila, Samira,
  Kalyani) — hook intel for Jamila already in her Notes.
- [ ] Bonge / Danish: manual email find (Flodesk / IG DM) or park; reconcile
  Danish's UAE residency first.

## 2026-07-19 — Lucia Csobonyei turn-two SENT (Touch 2, Inbox 2), logged
- **Lucia's turn-two warm reply went out** (Inbox 2 / gethaytham.com, direct
  API path, threaded on "wake-up calls"). It reframes off the prospect read
  ("my first email sounded like I wanted coaching. I don't."), grants her
  fit-first / quiz logic, and offers the Loom walk. No price, no link, signed
  Haytham. Cleared draft_lint + the copy checks.
- **Logged on Haytham's confirmed send:** Touch # 1→2, Email Thread Log Touch 2
  block appended, Last Contacted 07-19, Next Action → 07-22 (warm nudge if
  quiet). Sequence stays Warm, Status stays Reply Received (Loom is offered,
  not yet an artifact — UAE has no "Loom Sent" status). Notes marker
  "turn-two must reframe" resolved. Findings Bank untouched (#2 USED-T1; #3/#4
  still UNUSED).
### Open follow-ups
- [ ] When she okays the walk: record the Loom same day, then send the **price
  discovery question** (still never asked) BEFORE any number of ours lands.
- [ ] If quiet by 07-22: warm nudge (do not ask price discovery into silence).

## 2026-07-19 — New "Lane 2" status + migration; Ben Pringle note fixed; Lucia replied (turn-two drafted, held)
- **New CRM Status option "Lane 2" added by Haytham; migrated all 12 `Lane 2: No
  leak`-tagged leads into it** — 6 from Dormant (Yasmina Nagnoug, Ola Gramovich,
  Nicolas Provencal, Dr. Mona AlHebsi, Alex Makarovski, Coach Islam) + 6 from
  Disqualified (Coach G, Jessica Morari, Dan Chadwick, Tina Ghazi, Anthony Walsh,
  Sheikh Nadir). The Disqualified 6 were a judgment call (moving them un-kills
  gate-failed leads) — Haytham confirmed move all. None had been touched, so
  nothing live was disturbed. This gives no-leak leads a proper home instead of
  being mixed into Dormant/Disqualified (resolves the earlier hygiene flag).
- **Ben Pringle Notes were wrong (stale mid-process snapshot) — rewrote them.**
  Old note said finding invalidated / Finding Verified NO / "re-walk queued,
  reset to Qualifying." Reality (per page body): the re-walk WAS completed
  2026-07-18, found a NEW verified Lane 1 finding (his GBP40 Dubai Football Guide
  vanished from the Stan store), Finding Verified is back to YES, and Touch 3
  already went out on it. **Correction to this session's own earlier hygiene read:
  Ben is NOT an open re-walk item** — that claim leaned on the truncated Notes;
  the body proved the walk was done. He's a live warm thread at Touch 3, awaiting
  reply, next check 07-21.
- **Lucia Csobonyei replied (Inbox 2) — logged verbatim, Warm.** Status
  Outreach Sent -> Reply Received, Sequence Cold -> Warm. She defended the
  no-visible-price finding as INTENTIONAL (fit-first / apply-to-work-with-me),
  volunteered her own selling prices (Rewire to Results 18,000 AED / Clear One
  Problem 980 AED — that's her price as a SELLER, NOT a Price Discovery Answer,
  so that field stays empty), and appears to have read the opener as me being a
  prospective client ("if you interested for yourself"). Turn-two drafted to
  reframe (not a prospect) + grant the fit-first logic + offer the Loom, no price.
  **Draft is HELD at Haytham's request — not pushed to Gmail, not logged as sent.**
- **Ops learning — reading Inbox 2 replies:** the Gmail MCP is bound to Inbox 1
  (auto-mate.one) ONLY. Inbox 2 (gethaytham.com) replies are NOT visible to the
  MCP `search_threads`; read them via `python main.py gmail-gethaytham
  search|thread|message` (direct Gmail API path, per audit/inboxes.py). Needs
  `pip install -r requirements.txt` first in a fresh container.
- Notion free-plan SQL query quota was exhausted again mid-session (during the
  Lane 2 work) — page-ID writes still work, but couldn't re-run a `GROUP BY
  Status` to visually confirm the Lane 2 column = 12. Eyeball it in Notion.
### Open follow-ups
- [ ] Lucia turn-two draft is written and HELD — push to Inbox 2 as a Gmail draft
      (via `gmail-gethaytham draft`, same thread) when Haytham approves, then log.
- [ ] Eyeball Notion: the new Lane 2 status column should read 12.

## 2026-07-19 — CRM hygiene sweep (clean) + Christina Steinhoff reclassified; WhatsApp cold-texting is an account-safety risk
- **Hygiene sweep** (the one the 07-19 tick couldn't finish on quota) re-run clean:
  ALL mechanical checks passed — 0 future-dated Last Contacted, 0 Touch#=0 on
  Outreach Sent, 0 missed Findings Bank UNUSED->USED flips (Shankar 1&2 USED,
  Marie 1 USED both verified correct), 0 stale pre-send markers (the two rows
  that matched carried the historical phrase "hook found VIA haytham-hook-finder",
  not a pending marker), 0 stale warm threads, 0 over-a-week un-walked Qualifying.
  Nothing auto-fixed because nothing needed it.
- **Attribution splits (Step 6, also skipped last tick):** over 67 cold-touched
  leads, all 5 warm replies (Ben, Donna, Christina, William, Lisa) came from
  **Google Footprint** sourcing (~13%, 5/39). Every other channel is 0 replies
  across 28 sends (LinkedIn 0/14, Coach Directory 0/6, Event Speaker 0/3,
  Podcast 0/2, IG 0/2, Lateral 0/1). Small n, but a clean directional case to
  concentrate sourcing on Google Footprint. Finding Type of repliers: Dead/stale
  x2, Other x3. Lane: every sent lead + every reply is Lane 1 (Lane 2/3 never
  sent), so no Lane comparison possible this round.
- **Judgment flags surfaced (not auto-fixed):** 4 Lane-2 "no leak" leads
  (Yasmina Nagnoug, Nicolas Provencal, Alex Makarovski, Coach Islam) sit at
  Dormant while their own notes say "holds at Qualifying" — status/note
  disagree, confirm intended parking status. Murielle Larriere went Dormant
  after only Touch 1 (cold seq is 3) — confirm early drop vs premature Dormant.
- **Christina Steinhoff reclassified Warm->Cold.** Her 07-19 "reply" was a
  CONFIRMED autoresponder (word-for-word the 07-16 auto-reply, same 1-min
  latency). Per its instruction, Haytham texted the +971562737368 number on
  WhatsApp — **his number got spam-flagged and feature-blocked for 6h after the
  first message.** The line is an automated WhatsApp Business gate; both her
  published channels (email + phone) are automated walls, no human reachable.
  Row set back to Status Outreach Sent / Sequence Cold / Touch 3 due 2026-07-25;
  if no human reply, Dormant. Email Thread Log + Notes updated to record all of it.
- **LESSON (account-safety, treat as a rule):** do NOT cold-text leads on
  WhatsApp from Haytham's personal number. One unsolicited message to a
  non-contact got reported/blocked within 6h. Same family of mistake as the IG
  ban — different platform, same "don't put Haytham's own account at risk" rule.
  A lead that only exposes an autoresponder email + a phone number is likely a
  bot moat, not a reachable person; don't chase it through personal channels.
### Open follow-ups
- [ ] Confirm the 4 Lane-2 Dormant rows' intended status (Dormant vs Qualifying-hold).
- [ ] Confirm Murielle Larriere's early Dormant (bounce/unreachable vs premature).
- [ ] Christina Touch 3 due 2026-07-25 (Inbox 1); park Dormant if no human reply.

## 2026-07-19 — uae-tick: reconciled 25 already-departed sends, 2 bounces, 1 probable autoresponder
- Ran the daily uae-tick. Unusual shape this run: 25 emails had already left both
  inboxes before the tick started (12 Inbox 1 Touch-2 follow-ups + Noona's
  scheduled Touch 1 + Christina's Touch 2, all auto-mate.one; 10 Inbox 2
  scheduled Touch-1 openers + 2 bounces, all gethaytham.com) — none logged to
  Notion yet. Fanned out ~25 parallel subagents (one per lead, worktree-isolated)
  to do full confirmed-send reconciliation against fetched Gmail thread content:
  Touch #, Sequence, Status, Last Contacted/Next Action, Findings Bank
  UNUSED->USED-TN flip, Notes, and the Email Thread Log entry — verified each
  against the actual Gmail message before writing, not just asserted.
- **2 new bounces**, both Inbox 2, both "Address not found": Samira Alexander
  (samira@samiraalexander.com, an Apify-enrich guess that had verified PASS
  the day before) and Kalyani Seth Soni (info@sheinvests.me, already flagged
  WARN/catch-all at verify time — the risk materialized). Both reverted to
  Qualifying, no touch counted, logged to docs/deliverability-log.md.
- **Christina Steinhoff's reply is very likely an autoresponder, not a person**
  — it landed 1 minute after Touch 2 sent and is near word-for-word identical
  to her Touch 1 auto-reply from 07-16 (same 1-minute latency, merge-tag
  artifacts on the first one). Logged as Reply Received/Warm per protocol
  since the rule is to record what came in, but flagged loudly in the brief —
  needs a human check (text the phone number in her signature) before treating
  it as a live warm thread.
- Ceilings held clean: Inbox 1 13/20, Inbox 2 13/20 (13 includes the 2
  bounces — a bounce still counts against ceiling, it departed the inbox).
  Neither inbox has held its ramp step 7 days yet, so no ramp reminder.
- Send queue was empty (no Audit Ready/Draft Ready rows) — bottleneck is walks,
  not sends, consistent with the standing note in CLAUDE.md.
- First scoreboard run (no prior one found in this journal) — ~66 unique leads
  cold-touched, 4 confirmed replies + 1 uncertain (Christina) ≈ 6-7.5% reply
  rate by lead, 0 discovery answers logged yet (Donna Brown's is pending), 0
  offers, 0 closes.
### Open follow-ups
- [ ] Donna Brown's price discovery answer — log VERBATIM the moment it lands,
      do not wait for the next tick.
- [ ] Confirm whether Christina Steinhoff's reply is a real person or fully
      automated before drafting anything further to her.
- [ ] Notion's SQL query quota (free plan) was exhausted mid-tick, so the
      hygiene sweep (future-dated Last Contacted, Touch#=0 on Outreach Sent)
      and the Finding Type/Source Channel/Lane attribution splits couldn't run
      this pass — re-run clean next tick.

## 2026-07-18 — Instagram fetch split into two dedicated Apify actors
- Swapped the single `apify/instagram-scraper` for `apify/instagram-profile-scraper`
  (`--mode details`, `usernames` input) + `apify/instagram-post-scraper` (posts +
  `ig-post` single-post detail, `username` input which also takes profile/post URLs).
  Branch `claude/apify-instagram-scraper-migration-vdnypk`, pushed (no PR yet).
- Why it's a clean swap: both are Apify's own sibling actors — **identical output
  field names** (trim/`_lean` keys unchanged) and both PAY_PER_EVENT with a flagged
  `isPrimaryEvent`, so the existing cost-approval estimator works untouched. Slightly
  cheaper too: $0.0023/profile + $0.0015/post at BRONZE.
- New flags: `--skip-pinned` (post actor's native `skipPinnedPosts`, **default off**
  by Haytham's call — a pinned post is often the coach's signature/framework content,
  i.e. the SMYKM hook) and `--include-about` (profile actor's paid about-account
  add-on). Dropped the unused reels/comments/mentions/stories modes; `--mode` is now
  `posts`/`details` only.
- CLI command names (`apify ig` / `ig-post`) unchanged on purpose, so
  `haytham-hook-finder` and every other consumer needed zero change. Only
  `audit/apify.py` + `main.py` + docs/tests touched. Tests: 23/23 (added
  actor-routing + username-normalize).
- Gotcha: the profile scraper's `usernames` field wants a **bare handle**, not a URL
  (the post scraper's `username` accepts either) — added `_ig_username()` to strip a
  handle out of a profile URL on the details path only.

## 2026-07-18 — Hooks + Touch-1 drafts for the 3 Audit Ready leads (Noona, Marie, Michele)
- Ran `haytham-hook-finder` (batch) over the 3 Audit Ready rows whose `SMYKM Hook`
  was empty. Apify cap fine (2% used). All 3 hooks from fresh, cited public evidence:
  - **Noona Nafousi** (Inbox 1, Track B) — WORK: her LinkedIn "factory workers packing
    medicine / 43% from one sentence / feel as good inside as success looks outside"
    post (8 Jul). Skipped her "choosing me" grief post (too intimate) and the 8M-view
    lisp reel (numeric-contrast/sensitive).
  - **Marie Hondekyn** (Inbox 2, Track A) — WORK: her coined "Selection Method" —
    "I don't teach you how to get chosen, I teach you how to choose" (IG @datingbymarie,
    9 Jul). Her 29K IG is @datingbymarie, NOT @infinityrelations (~1.3K).
  - **Michele Barouki** (Inbox 2, Track A) — LIFE: her 1 Jul IG post about building her
    home studio by hand. About page was too thin (generic, "cat mom of 3") so went to IG.
- Drafted all 3 Touch-1 openers (SMYKM opening A), Haytham approved copy.
- **Inbox split (his call):** Noona → Inbox 1, Marie + Michele → Inbox 2. Reasoning:
  split the two WARN-email leads (Noona catch-all, Marie inconclusive) across domains
  so a bounce doesn't hit one twice; Michele is the only clean PASS.
- Past noon Dubai → all 3 gate as next-day openers (send-day 07-19). `crm-gate send`
  PASS on all 3: Inbox 1 had 12 already scheduled for 07-19 (+Noona=13<20), Inbox 2 had
  10 (+Marie/Michele=12<20). Gmail drafts created (Noona via Gmail MCP; Marie+Michele via
  `gmail-gethaytham draft`), all linted clean. Rows set `Inbox` + Status = **Draft Ready**.
- Gotcha: `crm-gate send` requires BOTH `--sends-today` AND `--sends-next-day` even for a
  next-day opener — it won't count Gmail itself. Inbox 1 = gmail-mcp = haytham@auto-mate.one
  (confirmed). Inbox 1 already at 17 sends today (cap 20) but that doesn't constrain a
  next-day opener.
### Open follow-ups
- [ ] Haytham to schedule the 3 drafts in Gmail for 07-19, then confirm sends so the tick
  flips each to Outreach Sent (Touch #1, Last Contacted, Findings Bank #1 → USED-T1).

## 2026-07-18 — Donna Brown replied yes to the walkthrough (Inbox 2)
- Donna Brown (Leadership/Life coach, Dubai, Inbox 2, Track A) replied a second
  time on her thread (subj "your core blueprint bundle"), at 22:05 Dubai:
  "Thank you for your message... Sure happy to know what I can do better.. By the
  way, how did you come across my page?" — a **warm yes to the Loom walkthrough**
  plus a trust-check question.
- Thread state: Touch 1 = finding #1 (Core Blueprint checkout double-charge) →
  her reply #1 slightly **misread** it (thinks the worry is that the bundle
  duplicates the course; the real flag is the checkout add-on bump stacking the
  AED 1,997 bundle on top of the AED 597 course). Touch 2 = finding #2 (Save 35%
  badge is really ~29%) + loom-offer → her reply #2 above.
- Logged her reply verbatim to the Email Thread Log; Notes refreshed; Next Action
  pulled to today. Status stays `Reply Received`, Sequence `Warm`, Touch # 2 (no
  send yet). Findings Bank #3 (course-name mismatch) + #4 (Stripe branded
  "Coaching Business") still UNUSED — Loom material.
- **Drafted the turn-two Loom-delivery reply** and created the Gmail draft in
  Inbox 2 (threaded, subject unchanged), held on a `[Loom link]` placeholder.
  Answers her question honestly (Google-footprint sourcing), re-shows the
  double-charge she misread, carries the two remaining findings, closes steering
  her toward handing it over (she said "I'll revisit it myself" — gratitude-trap
  risk).
- **UPDATE (later 07-18/19):** Haytham recorded the Loom same night, rewrote the
  reply himself (better than mine), and folded the **price-discovery question**
  into the close: "if someone took the whole site top to bottom, everything
  sorted and off your plate, what would you expect that to run?" Scope widened
  from the fixes to the whole site on purpose (lifts her anchor; read it in that
  context). Loom link: loom.com/share/9333b35228e344c5b40900a5612b5ac4.
- **SENT** (accidental click, but a good email) 2026-07-19 ~04:18 Dubai, Inbox 2,
  Touch 3. Full confirmed-send logging done: Status `Reply Received` →
  `Price Discovery Sent`, Touch # → 3, Last Contacted 07-19, Next Action 07-22,
  Findings Bank #3 → USED-T3 (Loom spent it), #4 (Stripe branding) still UNUSED /
  held. Thread log + Price Discovery section updated. This is now a
  **Price Discovery Sent** lead — her next reply IS the study data.
- Loom itself covered findings #1 (double-charge, re-shown to fix her earlier
  misread), #2 (35% vs 29%), #3 (course-name mismatch). #4 held back.
### Open follow-ups
- [ ] Watch Inbox 2 for Donna's reply. The MOMENT a number (or refusal) lands:
      log it VERBATIM into `Price Discovery Answer`, set `Discovery Anchor` per
      the uae-track mapping. Do NOT wait for a tick — this is the track's whole
      point. Then `crm-gate offer` gates any priced email.
- [ ] If quiet by ~07-22: warm bump. #4 (Stripe 'Coaching Business' branding) is
      the unused held finding for it.

## 2026-07-18 — Luca & Larry "findings invalid" — over-retirement corrected
- Haytham flagged, while prepping tomorrow's follow-ups, that Luca Allam and Dr
  Larry Davies findings "don't hold anymore." Re-walked both funnels live.
- Reality: the earlier same-day session **over-retired**. The primary Touch-1
  findings (the ones gating `Finding Verified`) still HOLD; only the *secondary*
  banked findings died.
  - **Larry:** the note claiming `elmwoodevents.com/leadership-and-innovation`
    "now 404s" was WRONG — page is live (200), still dated 13 May 2026, $15/$25
    checkout live. Bank #1 holds. Bank #2 (no email capture) correctly retired:
    `elmwoodfields.com/contact-us` now has a newsletter opt-in.
  - **Luca:** "finding #1 likely stale" was WRONG — a paid checkout doesn't add a
    free opt-in. Homepage CTAs still dead-end at `#contact-us`, no freebie. Bank
    #1 (No opt-in capture) holds. Banks #2/#3 correctly retired: `/masterpitch/`
    is now a real 7-module course -> `/pricing` ($299/$399/$999).
- Corrected both Findings Banks + Notes in the UAE CRM. `Finding Verified` stays
  checked on both (send gate intact).
- Gotcha: a same-day "REFUTED/stale" aside is still a claim — verify the actual
  page before acting on it. A refuted *secondary* finding does not make the
  *primary* felt leak stale.
- Touch 2 carrier decided (Haytham): **Loom offer** for both (no banked 2nd
  finding left to carry). Drafted both Touch 2 replies (same thread/subject,
  Loom offer as the single payload, no link/price), created the Gmail drafts in
  Inbox 1, and left each row at Outreach Sent with a "Touch 2 held for 07-19
  send" marker in Notes. Status stays Outreach Sent (a follow-up draft on an
  already-sent lead does NOT flip back to Draft Ready — that status is the
  first-send pre-state only).
- Both Touch 2 drafts SCHEDULED in Gmail (Haytham) for 07-19 send, Inbox 1.
  Notes markers updated to "SCHEDULED". Status stays Outreach Sent (follow-up on
  an already-sent lead never flips to Scheduled/Draft Ready — those are
  first-send pre-states). The 2 scheduled sends count against Inbox 1's 07-19
  ceiling.
### Open follow-ups
- [ ] 07-19: on confirmed departure of each scheduled send, advance the rows
  (Touch #->2, Last Contacted->07-19, Next Action->07-25, append thread log).
  uae-tick reconciles Gmail reality; the crm-gate send carrier is loom-offer,
  Inbox 1 (its 07-19 budget must have room for these 2 plus anything else due).

## 2026-07-18 — Four bug fixes + cross-session memory setup
- Fixed and merged 4 bugs to `uae-track` (PR #48, squash `9cdc428`):
  mobile-screenshot re-settle, calendar events surviving Gmail/Notion date
  shapes, the noon-Dubai send-day cutoff for openers, and the
  authoritative-skills `SessionStart` hook.
- Added THIS journal + a second `SessionStart` hook that auto-loads recent
  memory (this file's latest entries + `git log`) so new sessions boot with
  context. Decision: keep session memory in git (auto-loads at start, diffable,
  lives with CLAUDE.md) rather than Notion, which stays the source of truth for
  live pipeline *state*, not narrative.
- Gotcha: past noon Dubai, a fresh touch-1 opener now needs
  `--sends-next-day <inbox's scheduled count>` on `crm-gate send`, or it fails
  closed asking for it. `inbox counts` prints `send_day` + an `opener_note`
  when this applies.
### Open follow-ups
- [ ] If phone-readable ops notes become useful, mirror journal entries to a
  Notion page (not needed yet).
