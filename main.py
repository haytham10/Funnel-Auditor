"""The outbound machine's CLI. Python owns every check; the model owns the words.

The division of labour that survived the pivot from the funnel-auditor: a skill
fetches and reasons, and then calls one of these commands to decide. Anything a
machine can settle deterministically — a number that isn't in the fact table, a
duplicate name, a floor verdict with no source behind it — is settled here and
printed as a line the skill quotes verbatim rather than paraphrases.

Every gate fails closed. A check that cannot run is a failure, never a pass.

    intake      raw CSV -> profiled, junk-stripped Leads
    dedupe      the Contacted-Before wall, both passes
    wall-add    append a shipped batch to the wall, after it is uploaded
    qualify     the three floors, run over a research JSON
    research    validate one worker's returned research object
    anchors     which hand-written lines a lead draws, and what it may cite
    deal        the same, for a whole batch, with the weights held exactly
    copy-usage  report a shipped batch's line usage back to Airtable
    copy-sync   pull the lines out of Airtable, rejecting any that fail the lint
    lint        the checks that make model-written copy safe
    export      leads.csv + preview.txt, refusing to write a failing email
    email-*     address shape, deliverability, and the no-address fallback
    apify       no-login LinkedIn / Instagram / YouTube / SERP fetch
    classify-footprint   merge pre-fetched search hits into sourcing candidates
"""

import argparse
import csv
import json
import sys
from pathlib import Path


# --------------------------------------------------------------------- intake


def cmd_intake(args) -> None:
    """Raw list -> Leads, with junk stripped and platform URLs routed.

    Prints the batch profile before anything is spent. A platform URL in the
    website column is not junk; it becomes a social research target, which is
    what the old pipeline got wrong when it discarded 24 rows for having a
    LinkedIn address where a domain was expected.
    """
    from outbound import normalize

    leads = normalize.load_csv(args.path, source=args.source or args.path)
    shape = normalize.profile(leads)

    if args.json:
        print(json.dumps({"profile": shape,
                          "leads": [l.to_dict() for l in leads]},
                         indent=2, default=str))
        return

    print(f"INTAKE {args.path}: {shape['total']} rows")
    print(f"  live site         {shape['with_site']}")
    print(f"  social only       {shape['social_only']}")
    print(f"  email on the row  {shape['with_email']}")
    print(f"  nothing to work   {shape['no_research_target']}")
    if shape["parked_names"]:
        print("  parked: " + ", ".join(shape["parked_names"]))
    # Silence here is expensive. The first real list used `companyWebsite`,
    # which the alias table did not know, so 13 of 13 sites mapped to nothing
    # and the whole free site-read tier was skipped without a word.
    unmapped = normalize.unmapped_headers(args.path)
    if unmapped:
        print(f"  ignored columns   {', '.join(unmapped)}")
        print("                    (if one of those is the website or the name, "
              "add it to COLUMN_ALIASES before running the batch)")
    if args.out:
        Path(args.out).write_text(
            json.dumps([l.to_dict() for l in leads], indent=2, default=str),
            encoding="utf-8")
        print(f"  wrote {args.out}")


# --------------------------------------------------------------------- dedupe


def _load_leads(path: str):
    from outbound.normalize import Lead
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    known = set(Lead.__dataclass_fields__)
    return [Lead(**{k: v for k, v in row.items() if k in known}) for row in data]


def cmd_dedupe(args) -> None:
    """The Contacted-Before wall. Pass 1 on name/domain, pass 2 on email.

    Pass 1 runs BEFORE any paid call. That ordering is the whole point: the old
    pipeline deduped last, so an already-excluded lead paid for all eight Apify
    calls before being thrown away. A warm-thread hit exits non-zero, because a
    cold opener landing on a live conversation is the one failure worth stopping
    the run for.
    """
    from outbound import dedupe

    leads = _load_leads(args.leads)
    if args.contacts:
        # An explicit file, for walling against a one-off CRM export. An
        # unreadable one must exit 2 with a message, exactly like a missing
        # default wall — a traceback here would read as "the run failed"
        # rather than "the wall could not be checked", and the hard rule is
        # that a missing wall never means "nobody has been contacted".
        try:
            raw = Path(args.contacts).read_text(encoding="utf-8")
            wall = (dedupe.ContactWall.from_records(json.loads(raw))
                    if args.contacts.endswith(".json")
                    else dedupe.ContactWall.from_csv(args.contacts))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"DEDUPE: FAIL — cannot read the wall at {args.contacts}: "
                  f"{type(exc).__name__}. Refusing to pass a batch it cannot "
                  f"check.")
            sys.exit(2)
    else:
        wall = dedupe.ContactWall.from_csv()

    if not len(wall):
        print("DEDUPE: FAIL — the wall is empty. Refusing to pass a batch it "
              "cannot check; a missing file must not read as 'nobody has been "
              "contacted'.")
        sys.exit(2)

    result = dedupe.partition(leads, wall, stage=args.stage)
    print(f"  wall: {len(wall)} contacts, "
          f"{sum(1 for c in wall.by_name.values() if c.warm)} warm")

    print("\n".join(dedupe.report(result, stage=args.stage)))
    if args.out:
        Path(args.out).write_text(
            json.dumps([l.to_dict() for l in result["clear"]], indent=2, default=str),
            encoding="utf-8")
        print(f"  wrote {args.out}")
    sys.exit(1 if result["warm_hits"] else 0)


# -------------------------------------------------------------------- qualify


def _load_object(path: str, label: str) -> dict:
    """One JSON object from a file or stdin, or a clean failure.

    A worker that returns a list instead of an object used to produce an
    `AttributeError` traceback, which reads as a crash rather than as the
    schema violation it actually is.
    """
    try:
        raw = sys.stdin.read() if path == "-" else \
            Path(path).read_text(encoding="utf-8")
        data = json.loads(raw)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"{label}: FAIL — cannot read {path}: {type(exc).__name__}: {exc}")
        sys.exit(2)
    if not isinstance(data, dict):
        print(f"{label}: FAIL — expected one JSON object, got "
              f"{type(data).__name__}. One lead per call.")
        sys.exit(2)
    return data


def cmd_qualify(args) -> None:
    """The three floors over one lead's gathered text. `unclear` passes.

    Only a clear `no` drops a row, because a false kill is permanent and
    invisible while a false pass costs one more research call. Audience size and
    program price are captured and printed, never gated on.
    """
    from datetime import date
    from outbound import qualify as q

    data = _load_object(args.input, "QUALIFY")

    last = data.get("last_activity")
    result = q.qualify(
        city=data.get("city", ""),
        domain=data.get("domain", ""),
        headline=data.get("headline", ""),
        site_text=data.get("site_text", ""),
        linkedin_text=data.get("linkedin_text", ""),
        last_activity=date.fromisoformat(last) if last else None,
        audience_size=data.get("audience_size"),
        top_program_price_aed=data.get("top_program_price_aed"),
        solo=data.get("solo", "unclear"),
    )
    print(result.report(data.get("name", "lead")))
    sys.exit(0 if result.passed else 1)


def cmd_research(args) -> None:
    """Validate one worker's returned research object against the schema.

    Catches the two failures a plausible-sounding worker produces: a verdict
    outside the enum, and a hard yes/no with nothing named as its source. A
    verdict that names nothing was reasoned, not fetched.
    """
    from outbound import research as r

    data = _load_object(args.input, "RESEARCH")
    obj = r.Research.from_dict(data)
    print(r.report(obj))
    sys.exit(0 if not r.validate(obj) else 1)


# -------------------------------------------------------------------- anchors


def cmd_anchors(args) -> None:
    """Which hand-written lines this lead draws, and every number it may cite.

    Deterministic on `sha256(email)`, so the same lead draws the same lines in
    every process on every machine. The builtin hash() is salted per process,
    which would make "reproducible" quietly false between runs.
    """
    from outbound import anchors

    anchor = anchors.draw(args.email, coach_type=args.coach_type,
                          sells_to=args.sells_to)
    if args.json:
        print(json.dumps({
            "identity": {"id": anchor.identity.id, "line": anchor.identity.line},
            "offer": {"id": anchor.offer.id, "line": anchor.offer.line},
            "cta": {"id": anchor.cta.id, "line": anchor.cta.line},
            "ps": {"id": anchor.ps.id, "line": anchor.ps.line},
            "segment": anchor.segment,
            "allowed_numbers": sorted(anchor.allowed_numbers),
        }, indent=2))
        return

    print(anchor.as_prompt_block())
    print(f"\nsegment: {anchor.segment or 'generic (no exact match drawn)'}")
    print("allowed numbers: " +
          ", ".join(str(n) for n in sorted(anchor.allowed_numbers)))
    print("\nAny number in the body outside that set is invented or relabelled.")


def cmd_copy_sync(args) -> None:
    """Pull the hand-written lines out of Airtable, rejecting the bad ones.

    Airtable exists so a line can change without touching code. That is only
    safe because this is a gate: a line whose numbers do not trace to
    `copy/results.csv`, or that attaches one segment's result to another, is
    rejected here rather than reaching a stranger's inbox two stages later.

    Two ways in. With `AIRTABLE_API_KEY` set, `--live` fetches directly.
    Without one — which is the case today — a skill fetches the Copy Assets
    records through the Airtable MCP and pipes them here as JSON.
    """
    from outbound import copy_sync

    if args.live:
        from audit import airtable
        if not airtable.available():
            print("COPY-SYNC: FAIL — --live needs AIRTABLE_API_KEY in the "
                  "environment. Without it, fetch Copy Assets through the MCP "
                  "and pipe the records to this command instead.")
            sys.exit(2)
        try:
            records = airtable.copy_assets()
        except airtable.AirtableError as exc:
            print(f"COPY-SYNC: FAIL — {exc}")
            sys.exit(1)
        source = "airtable-api"
    else:
        raw = sys.stdin.read() if args.input == "-" else \
            Path(args.input).read_text(encoding="utf-8")
        payload = json.loads(raw)
        # Accept a bare list, or the MCP's {"records": [...]} envelope.
        records = payload.get("records", payload) if isinstance(payload, dict) else payload
        source = "mcp"

    result = copy_sync.sync(records, source=source, write=not args.dry_run)
    print(result.report())
    if result.ok and not args.dry_run:
        print(f"  wrote {copy_sync.SNAPSHOT}")
        print("  regenerated copy/*.csv — commit them so the fallback matches")
    sys.exit(0 if result.ok else 1)


def cmd_wall_add(args) -> None:
    """Append a shipped batch to `data/contacted-before.csv`.

    Run this AFTER the upload has actually happened. Export deliberately does
    not do it: nothing has been sent at export time, and walling a lead who
    never received anything would silently exclude her from every future batch.

    Idempotent. Re-running it adds nothing, so running it twice after a
    half-remembered upload is safe.
    """
    from outbound import dedupe, export

    wall = dedupe.ContactWall.from_csv()
    before = len(wall)

    with open(args.additions, newline="", encoding="utf-8-sig") as handle:
        incoming = list(csv.DictReader(handle))

    added = []
    for row in incoming:
        contact = dedupe.KnownContact(
            name=(row.get("name") or "").strip(),
            email=(row.get("email") or "").strip(),
            domain=(row.get("domain") or "").strip(),
            status=(row.get("status") or "Outreach Sent").strip(),
            warm=dedupe._truthy(row.get("warm")),
            track=(row.get("track") or "Outbound").strip(),
        )
        # Checked against the wall's own keys rather than check_early/check_late:
        # those read a Lead's `site_url`, which a KnownContact does not have, so
        # the domain half would silently never match.
        already = (
            (contact.name and dedupe.name_key(contact.name) in wall.by_name)
            or (contact.email and dedupe.email_key(contact.email) in wall.by_email)
            or (contact.domain and dedupe.domain_key(contact.domain) in wall.by_domain)
        )
        if already:
            continue
        wall.add(contact)
        added.append(contact.name)

    if added and not args.dry_run:
        with open(dedupe.CONTACTED_BEFORE, "w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=export.WALL_COLUMNS)
            writer.writeheader()
            writer.writerows(wall.to_rows())

    print(f"WALL-ADD: {len(added)} added, "
          f"{len(incoming) - len(added)} already present "
          f"({before} -> {len(wall)})")
    for name in added[:10]:
        print(f"  + {name}")
    if added and not args.dry_run:
        print(f"  wrote {dedupe.CONTACTED_BEFORE} — commit it")


def cmd_deal(args) -> None:
    """Anchors for a whole batch, allocated so the declared weights hold.

    The batch path, as against `anchors`, which is one lead. Independent
    per-lead hashing is unbiased only in the limit: measured over the real offer
    lines, a 50-lead batch gave one line 8% against a declared 20% and pushed
    another to 38%, over the repetition cap. Dealing the batch hits the weights
    as closely as whole leads allow, so the cap holds by construction.
    """
    from outbound import anchors

    leads = json.loads(Path(args.leads).read_text(encoding="utf-8"))
    dealt = anchors.deal_batch(leads)

    out = {
        email: {
            "identity": {"id": a.identity.id, "line": a.identity.line},
            "offer": {"id": a.offer.id, "line": a.offer.line},
            "cta": {"id": a.cta.id, "line": a.cta.line},
            "ps": {"id": a.ps.id, "line": a.ps.line},
            "segment": a.segment,
            "allowed_numbers": sorted(a.allowed_numbers),
        }
        for email, a in dealt.items()
    }
    if args.out:
        Path(args.out).write_text(json.dumps(out, indent=2), encoding="utf-8")

    from outbound.lint import FIXED_LINE_SHARE_CAP

    shares = anchors.batch_shares(list(dealt.values()))
    print(f"DEAL: {len(dealt)} leads")
    for beat, per_line in shares.items():
        top = ", ".join(f"{k} {v:.0%}" for k, v in list(per_line.items())[:4])
        flag = "  OVER CAP" if next(iter(per_line.values())) > FIXED_LINE_SHARE_CAP else ""
        print(f"  {beat:<9} {top}{flag}")

    # Which segments cannot fill their 70% share without repeating a sentence.
    # The deal already spilled to generic to stay legal; this says what to write.
    thin = anchors.thin_segments(anchors.CopyBank.load(), cap=FIXED_LINE_SHARE_CAP)
    drawn = {l.meta.get("coach_type", "") for l in
             [a.identity for a in dealt.values()]}
    for segment, shortfall in sorted(thin.items()):
        if segment.split("/")[0] in drawn or not drawn:
            print(f"  THIN  {segment}: {shortfall} more identity line(s) would let it "
                  f"hold its share without repeating")
    if args.out:
        print(f"  wrote {args.out}")


def cmd_copy_usage(args) -> None:
    """Report a shipped batch's line usage back to Airtable.

    Run after `wall-add`, for the same reason: it records what actually went
    out. Without it the weights stay guesses forever, because nothing anywhere
    records which line was in front of which reader.

    Increments `Times Used` and stamps `Last Used`. Needs AIRTABLE_API_KEY; the
    counts are in `out/line-usage.csv` either way, so a missing key loses the
    write, not the data.

    **Additive, and deliberately not idempotent** — unlike `wall-add`, which
    can be re-run safely. `Times Used` is a running total of emails sent, and
    there is no way to tell a re-run from a genuine second batch that happened
    to use the same lines. Run it once per batch. `--dry-run` first if unsure.
    """
    from datetime import date
    from audit import airtable

    with open(args.usage, newline="", encoding="utf-8-sig") as handle:
        counts = {r["line_id"]: int(r["count"]) for r in csv.DictReader(handle)}

    if not airtable.available():
        print("COPY-USAGE: SKIPPED — no AIRTABLE_API_KEY. Counts are still in "
              f"{args.usage}; re-run this when a key is set.")
        for line_id, count in sorted(counts.items()):
            print(f"  {line_id}: +{count}")
        sys.exit(0)

    try:
        records = airtable.list_records(airtable.COPY_ASSETS_TABLE)
    except airtable.AirtableError as exc:
        print(f"COPY-USAGE: FAIL — {exc}")
        sys.exit(1)

    by_id = {r.get("fields", {}).get("Line ID"): r for r in records}
    today = args.date or date.today().isoformat()
    updates, missing = [], []
    for line_id, count in counts.items():
        record = by_id.get(line_id)
        if not record:
            missing.append(line_id)
            continue
        previous = record.get("fields", {}).get("Times Used") or 0
        updates.append({"id": record["id"], "fields": {
            "Times Used": int(previous) + count, "Last Used": today}})

    if args.dry_run:
        print(f"COPY-USAGE: dry run, {len(updates)} line(s) would be updated")
    else:
        written = airtable.update_records(airtable.COPY_ASSETS_TABLE, updates)
        print(f"COPY-USAGE: {written} line(s) updated, dated {today}")
        print("  NOTE  additive, unlike wall-add. Run once per batch — a second "
              "run adds the same counts again.")
    for line_id in sorted(missing):
        print(f"  WARN  {line_id} is not in Copy Assets — run copy-sync?")


def cmd_facts(args) -> None:
    """The fact table, and the aggregate it licenses."""
    from outbound import anchors

    facts = anchors.load_facts()
    print(f"FACTS: {len(facts.results)} segments, "
          f"{facts.total_meetings} meetings, {facts.total_clients} clients, "
          f"AED {facts.total_aed:,} closed, {facts.total_sent} sends")
    for name, result in facts.results.items():
        print(f"  {name:<11} {result.meetings} mtgs / {result.period:<8} "
              f"{result.clients} clients  AED {result.aed_closed:>7,}  "
              f"first mtg {result.first_meeting_days}d  "
              f"{'still working' if result.still_working else ''}")
    print("  aggregate numbers: " +
          ", ".join(str(n) for n in sorted(facts.aggregate_numbers())))


# ----------------------------------------------------------------------- lint


def cmd_lint(args) -> None:
    """The gate on model-written copy. Per email, then across the batch.

    Traceability is the load-bearing check: every number in a body must resolve
    to that lead's allowed fact set. The client results are real and they come
    up on a call, and these coaches compare emails, so an invented digit or a
    segment's number relabelled onto another segment is the tell that the whole
    email was fabricated.
    """
    from outbound import anchors, lint

    drafts = json.loads(Path(args.input).read_text(encoding="utf-8")) \
        if args.input != "-" else json.loads(sys.stdin.read())
    if isinstance(drafts, dict):
        drafts = [drafts]

    facts = anchors.load_facts()
    failed = 0
    for draft in drafts:
        allowed = draft.get("allowed_numbers")
        if allowed is None:
            allowed = anchors.all_numbers(facts)
        result = lint.check_email(
            name=draft.get("name", draft.get("slug", "lead")),
            subject=draft.get("subject", ""),
            body=draft.get("body", ""),
            beats=draft.get("beats", {}),
            allowed_numbers=set(allowed),
            facts=facts,
        )
        print(result.report())
        failed += 0 if result.passed else 1

    if len(drafts) > 1:
        batch = lint.check_batch(drafts)
        print(batch.report())
        failed += 0 if batch.passed else 1

    sys.exit(1 if failed else 0)


# --------------------------------------------------------------------- export


def cmd_export(args) -> None:
    """Write leads.csv and preview.txt for the drafts that passed the lint.

    A failing email never reaches the CSV — not flagged in a column, absent.
    A failing email in an upload file is an email that gets sent by accident.
    """
    from outbound import anchors, export, lint

    drafts_raw = json.loads(Path(args.input).read_text(encoding="utf-8"))
    facts = anchors.load_facts()

    drafts, results, for_batch = [], {}, []
    for row in drafts_raw:
        beats = row.get("beats", {})
        body = row.get("body") or export.assemble_body(
            beats, greeting_name=row.get("first_name", ""))
        draft = export.Draft(
            slug=row.get("slug", ""), name=row.get("name", ""),
            first_name=row.get("first_name", ""), last_name=row.get("last_name", ""),
            email=row.get("email", ""), subject=row.get("subject", ""),
            body=body, beats=beats, anchor_ids=row.get("anchor_ids", {}),
            coach_type=row.get("coach_type", ""), sells_to=row.get("sells_to", ""),
            city=row.get("city", ""), company=row.get("company", ""),
            website=row.get("website", ""), linkedin_url=row.get("linkedin_url", ""),
            hook_type=row.get("hook_type", ""),
            hook_source_url=row.get("hook_source_url", ""),
        )
        allowed = row.get("allowed_numbers")
        if allowed is None:
            allowed = anchors.all_numbers(facts)
        results[draft.email] = lint.check_email(
            name=draft.name, subject=draft.subject, body=draft.body,
            beats=beats, allowed_numbers=set(allowed), facts=facts)
        drafts.append(draft)
        for_batch.append({"subject": draft.subject, "body": draft.body,
                          "beats": beats})

    shares: dict = {}
    for beat in ("identity", "offer", "cta", "ps"):
        counts: dict[str, int] = {}
        for draft in drafts:
            line_id = draft.anchor_ids.get(beat, "")
            if line_id:
                counts[line_id] = counts.get(line_id, 0) + 1
        if counts:
            shares[beat] = {k: v / len(drafts) for k, v in
                            sorted(counts.items(), key=lambda kv: -kv[1])}

    dealt = None
    if args.anchors:
        dealt = json.loads(Path(args.anchors).read_text(encoding="utf-8"))

    batch_result = lint.check_batch(for_batch, shares)
    out = export.write_batch(drafts, results, out_dir=args.out,
                             batch=args.batch or "", anchor_shares=shares,
                             batch_result=batch_result, dealt=dealt,
                             bank=anchors.CopyBank.load() if dealt else None)
    print(batch_result.report())
    print(out["report"])
    sys.exit(1 if out["blocked"] or out["rejected"] else 0)


# ------------------------------------------------------------------ addresses


def cmd_email_check(args) -> None:
    """Free shape check: syntax, MX, role/typo/disposable flags. A FAIL here
    never enters a queue or the CRM."""
    from audit import email_check
    sys.exit(email_check.print_check(args.address, args.name or ""))


def _apify_quota_note() -> tuple[bool, str | None]:
    """Cheap pre-flight cap read — no token cost, no actor run. Fails OPEN: an
    unreadable quota should not block a call that might otherwise succeed."""
    from audit import apify
    try:
        limits = apify.account_limits()
    except apify.ApifyError:
        return False, None
    if limits.get("near_cap"):
        return True, f"Apify at {limits.get('pct_of_usd_cap')}% of its monthly cap"
    return False, None


def _email_verifier(approved: bool = False):
    """Which verifier to use. `EMAIL_VERIFY_PROVIDER` picks (default apify),
    and a capped Apify quota auto-falls back to ZeroBounce rather than spending
    an attempt that would just 402."""
    import os
    import functools
    from audit import email_verifier
    provider = os.environ.get("EMAIL_VERIFY_PROVIDER", "apify").strip().lower()
    if provider != "apify":
        return email_verifier.verify_emails, email_verifier.EmailVerifierError, None

    from audit import apify
    capped, note = _apify_quota_note()
    if capped:
        return (email_verifier.verify_emails, email_verifier.EmailVerifierError,
                f"{note} — auto-switched to ZeroBounce for this call")
    return functools.partial(apify.verify_emails, approved=approved), apify.ApifyError, None


def cmd_email_verify(args) -> None:
    """Deliverability confirm. Syntax and MX are not enough — one real bounce
    burns the domain. A verifier error is inconclusive (WARN), never a silent
    pass."""
    from audit import email_check
    from audit.apify import ApifyCostApprovalRequired
    verify_fn, error_cls, note = _email_verifier(approved=args.approve_cost)
    try:
        rows = verify_fn([args.address])
    except ApifyCostApprovalRequired as exc:
        print(f"EMAIL VERIFY: APPROVAL REQUIRED — {exc}")
        sys.exit(3)
    except error_cls as exc:
        print(f"EMAIL VERIFY: WARN — {args.address}: verifier unavailable "
              f"({exc}) — inconclusive, could not confirm deliverability")
        sys.exit(0)
    sys.exit(email_check.print_verify(args.address, rows[0] if rows else None,
                                      note=note or ""))


def cmd_email_enrich(args) -> None:
    """The no-address fallback: derive name-based candidates on the lead's OWN
    branded domain, verify them in one batched call, adopt at most one. Never
    two guessed spellings, never a catch-all guess, never a free provider."""
    from audit import email_enrich
    from audit.urls import registrable_domain
    from audit.apify import ApifyCostApprovalRequired
    verify_fn, error_cls, note = _email_verifier(approved=args.approve_cost)
    try:
        sys.exit(email_enrich.print_enrich(args.name, args.domain,
                                           verifier=verify_fn, note=note or ""))
    except ApifyCostApprovalRequired as exc:
        print(f"EMAIL ENRICH: APPROVAL REQUIRED — "
              f"{registrable_domain(args.domain) or args.domain}: {exc}")
        sys.exit(3)
    except error_cls as exc:
        print(f"EMAIL ENRICH: HOLD — {registrable_domain(args.domain) or args.domain}: "
              f"verifier unavailable ({exc}) — inconclusive, no candidate confirmed")
        sys.exit(0)


# ------------------------------------------------------------------ the fetch


def cmd_fetch(args) -> None:
    """Tier 0: read sites with free local HTTP, and plan one batched Apify run
    for whatever that couldn't read.

    Container boot dominates an Apify bill, not pages, so the escalation is
    always one run for the whole batch — never one per lead.
    """
    from outbound import fetch

    leads = _load_leads(args.leads)
    result = fetch.batch_fetch(leads, max_pages=args.max_pages)
    print(result["report"])

    payload = {
        "tier0_rate": result["tier0_rate"],
        "escalate_plans": result["escalate_plans"],
        "sites": {
            slug: {
                "ok": read.ok,
                "pages": [{"url": p.url, "status": p.status, "chars": len(p.text)}
                          for p in read.pages],
                "emails": read.emails,
                "social": read.social,
                "prices": read.prices[:10],
                "headings": read.headings[:20],
                "notes": read.notes,
                "text": read.text if args.with_text else "",
            }
            for slug, read in result["reads"].items()
        },
    }
    if args.out:
        Path(args.out).write_text(json.dumps(payload, indent=2, default=str),
                                  encoding="utf-8")
        print(f"  wrote {args.out}")
    for plan in result["escalate_plans"]:
        print(f"  ESCALATE  {plan['why']}")


# -------------------------------------------------------------------- fetching


def cmd_apify(args) -> None:
    """No-login third-party fetch layer. Prints JSON for the calling skill.

    Every run is cost-gated: a call whose estimate is unknown or over the
    approval threshold exits 3 rather than running.
    """
    from audit import apify

    cmd = args.apify_command
    approved = getattr(args, "approve_cost", False)
    try:
        if cmd == "limits":
            out = apify.account_limits()
        elif cmd == "actors":
            out = apify.discover_actors(args.query, args.limit)
        elif cmd == "ig":
            out = apify.instagram(args.url, mode=args.mode, newer_than=args.newer_than,
                                  limit=args.limit, skip_pinned=args.skip_pinned,
                                  include_about=args.include_about, raw=args.raw,
                                  approved=approved)
        elif cmd == "ig-post":
            out = apify.instagram_post(args.url, raw=args.raw, approved=approved)
        elif cmd == "li-posts":
            out = apify.linkedin_posts(args.url, max_posts=args.max, since=args.since,
                                       raw=args.raw, approved=approved)
        elif cmd == "li-profile":
            out = apify.linkedin_profile(args.url, with_email=args.email, raw=args.raw,
                                         approved=approved)
        elif cmd == "youtube":
            out = apify.youtube_channel(args.channel, raw=args.raw, approved=approved)
        elif cmd == "verify-email":
            out = apify.verify_emails(args.addresses, raw=args.raw, approved=approved)
        elif cmd == "search":
            out = apify.google_search(args.query, pages=args.pages, site=args.site,
                                      country=args.country, raw=args.raw,
                                      approved=approved,
                                      meta=getattr(args, "meta", False))
        elif cmd == "footprint":
            out = apify.footprint_search(args.platform, geo=args.geo, role=args.role,
                                         country=args.country, raw=args.raw,
                                         approved=approved)
        else:
            print(json.dumps({"error": f"apify: unknown subcommand {cmd!r}"}))
            sys.exit(2)
    except apify.ApifyCostApprovalRequired as exc:
        print(json.dumps({"error": str(exc), "needs_approval": True,
                          "actor": exc.actor_id,
                          "estimated_usd": exc.estimated_usd}, indent=2))
        sys.exit(3)
    except apify.ApifyError as exc:
        print(json.dumps({"error": str(exc)}, indent=2))
        sys.exit(1)
    print(json.dumps(out, indent=2, ensure_ascii=False, default=str))


def cmd_classify_footprint(args) -> None:
    """Merge pre-fetched search hits into deduped, tagged sourcing candidates.

    Fetch-agnostic by design: whatever fetched the hits (the agent's own web
    search, or `apify search`) hands them here as JSON.
    """
    from audit import footprint

    def _load_hits(path: str | None) -> list[dict]:
        if not path:
            return []
        text = sys.stdin.read() if path == "-" else Path(path).read_text()
        return json.loads(text) if text.strip() else []

    try:
        out = footprint.classify_footprint_hits(
            args.platform, _load_hits(args.subdomain_hits),
            _load_hits(args.marker_hits), geo=args.geo, role=args.role)
    except (footprint.FootprintError, OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"error": str(exc)}, indent=2))
        sys.exit(1)
    print(json.dumps(out, indent=2, ensure_ascii=False, default=str))


# ------------------------------------------------------------------------ CLI


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="main.py",
        description="The outbound machine. Every command is a decision, "
                    "printed as a line to quote verbatim.")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("intake", help="raw CSV -> profiled, junk-stripped Leads")
    p.add_argument("path")
    p.add_argument("--source", help="label for where this list came from")
    p.add_argument("--out", help="write the Leads as JSON")
    p.add_argument("--json", action="store_true", help="print JSON instead of a profile")
    p.set_defaults(func=cmd_intake)

    p = sub.add_parser("dedupe", help="the Contacted-Before wall (exits 1 on a warm hit)")
    p.add_argument("leads", help="Leads JSON from `intake --out`")
    p.add_argument("--contacts", help="override the wall: a CSV, or a JSON array "
                                      "of CRM rows (default data/contacted-before.csv)")
    p.add_argument("--stage", choices=["early", "late"], default="early",
                   help="early = name/domain before any paid call; late = email after research")
    p.add_argument("--out", help="write the cleared Leads as JSON")
    p.set_defaults(func=cmd_dedupe)

    p = sub.add_parser("qualify", help="the three floors (unclear passes)")
    p.add_argument("input", help="JSON file, or '-' for stdin")
    p.set_defaults(func=cmd_qualify)

    p = sub.add_parser("research", help="validate a worker's research object")
    p.add_argument("input", help="JSON file, or '-' for stdin")
    p.set_defaults(func=cmd_research)

    p = sub.add_parser("fetch", help="tier 0 site reads, plus one batched Apify plan")
    p.add_argument("leads", help="Leads JSON from `intake --out`")
    p.add_argument("--max-pages", type=int, default=5)
    p.add_argument("--with-text", action="store_true", help="include page text in the output")
    p.add_argument("--out", help="write the reads as JSON")
    p.set_defaults(func=cmd_fetch)

    p = sub.add_parser("anchors", help="which hand-written lines a lead draws")
    p.add_argument("email")
    p.add_argument("--coach-type", default="", help="Business | Leadership | Life | ...")
    p.add_argument("--sells-to", default="", help="corporates | individuals")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_anchors)

    p = sub.add_parser("deal", help="anchors for a whole batch, weights held exactly")
    p.add_argument("leads", help="JSON list of {email, coach_type, sells_to}")
    p.add_argument("--out", help="write the per-lead anchors as JSON")
    p.set_defaults(func=cmd_deal)

    p = sub.add_parser("facts", help="the client-result fact table every number traces to")
    p.set_defaults(func=cmd_facts)

    p = sub.add_parser("copy-usage",
                       help="report a shipped batch's line usage back to Airtable "
                            "(run AFTER uploading, alongside wall-add)")
    p.add_argument("usage", help="out/line-usage.csv from `export`")
    p.add_argument("--date", help="ISO date to stamp (default today)")
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(func=cmd_copy_usage)

    p = sub.add_parser("copy-sync",
                       help="pull the hand-written lines out of Airtable, "
                            "rejecting any that fail the lint")
    p.add_argument("input", nargs="?", default="-",
                   help="JSON file of Copy Assets records, or '-' for stdin")
    p.add_argument("--live", action="store_true",
                   help="fetch directly (needs AIRTABLE_API_KEY)")
    p.add_argument("--dry-run", action="store_true",
                   help="validate and report, write nothing")
    p.set_defaults(func=cmd_copy_sync)

    p = sub.add_parser("wall-add",
                       help="append a shipped batch to data/contacted-before.csv "
                            "(run AFTER uploading, never before)")
    p.add_argument("additions", help="out/wall-additions.csv from `export`")
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(func=cmd_wall_add)

    p = sub.add_parser("lint", help="the gate on model-written copy")
    p.add_argument("input", help="JSON file (one draft or a list), or '-' for stdin")
    p.set_defaults(func=cmd_lint)

    p = sub.add_parser("export", help="write leads.csv + preview.txt for what passed")
    p.add_argument("input", help="JSON array of drafts")
    p.add_argument("--out", default="out", help="output directory (default out/)")
    p.add_argument("--batch", help="batch label (default today)")
    p.add_argument("--anchors", help="the JSON from `deal --out`. When given, any "
                                     "draft whose lines disagree with what the "
                                     "deal assigned is rejected")
    p.set_defaults(func=cmd_export)

    p = sub.add_parser("email-check", help="free shape check: syntax, MX, role/typo flags")
    p.add_argument("address")
    p.add_argument("--name", help="lead's full name, for the name-match note")
    p.set_defaults(func=cmd_email_check)

    p = sub.add_parser("email-verify", help="deliverability confirm before a send")
    p.add_argument("address")
    p.add_argument("--approve-cost", action="store_true")
    p.set_defaults(func=cmd_email_verify)

    p = sub.add_parser("email-enrich", help="no-address fallback on the lead's own domain")
    p.add_argument("name")
    p.add_argument("domain", help="domain or site URL")
    p.add_argument("--approve-cost", action="store_true")
    p.set_defaults(func=cmd_email_enrich)

    p_apify = sub.add_parser("apify", help="no-login LinkedIn / Instagram / YouTube / SERP fetch")
    apify_sub = p_apify.add_subparsers(dest="apify_command", required=True)

    apify_sub.add_parser("limits", help="usage vs plan — check ONCE per batch")

    a = apify_sub.add_parser("actors", help="search the public Apify Store")
    a.add_argument("query")
    a.add_argument("--limit", type=int, default=6)

    a = apify_sub.add_parser("ig", help="Instagram posts or profile details")
    a.add_argument("url")
    a.add_argument("--mode", default="posts", choices=["posts", "details"])
    a.add_argument("--newer-than", dest="newer_than")
    a.add_argument("--limit", type=int, default=12)
    a.add_argument("--skip-pinned", dest="skip_pinned", action="store_true")
    a.add_argument("--include-about", dest="include_about", action="store_true")
    a.add_argument("--raw", action="store_true")
    a.add_argument("--approve-cost", action="store_true")

    a = apify_sub.add_parser("ig-post", help="one Instagram post in full")
    a.add_argument("url")
    a.add_argument("--raw", action="store_true")
    a.add_argument("--approve-cost", action="store_true")

    a = apify_sub.add_parser("li-posts", help="recent LinkedIn posts — primary hook source")
    a.add_argument("url")
    a.add_argument("--max", type=int, default=5)
    a.add_argument("--since", choices=["any", "1h", "24h", "week", "month",
                                       "3months", "6months", "year"])
    a.add_argument("--raw", action="store_true")
    a.add_argument("--approve-cost", action="store_true")

    a = apify_sub.add_parser("li-profile", help="LinkedIn headline / about / experience")
    a.add_argument("url")
    a.add_argument("--email", action="store_true", help="use the pricier email-search mode")
    a.add_argument("--raw", action="store_true")
    a.add_argument("--approve-cost", action="store_true")

    a = apify_sub.add_parser("youtube", help="channel stats and recent videos")
    a.add_argument("channel")
    a.add_argument("--raw", action="store_true")
    a.add_argument("--approve-cost", action="store_true")

    a = apify_sub.add_parser("verify-email", help="verify addresses in one batched call")
    a.add_argument("addresses", nargs="+")
    a.add_argument("--raw", action="store_true")
    a.add_argument("--approve-cost", action="store_true")

    a = apify_sub.add_parser("search", help="Google SERP for one query")
    a.add_argument("query")
    a.add_argument("--pages", type=int, default=1)
    a.add_argument("--site")
    a.add_argument("--country", default="ae")
    a.add_argument("--meta", action="store_true")
    a.add_argument("--raw", action="store_true")
    a.add_argument("--approve-cost", action="store_true")

    a = apify_sub.add_parser("footprint", help="platform footprint sourcing")
    a.add_argument("platform")
    a.add_argument("--geo", default="Dubai")
    a.add_argument("--role", default="coach")
    a.add_argument("--country", default="ae")
    a.add_argument("--raw", action="store_true")
    a.add_argument("--approve-cost", action="store_true")

    p_apify.set_defaults(func=cmd_apify)

    p = sub.add_parser("classify-footprint",
                       help="merge pre-fetched search hits into sourcing candidates")
    p.add_argument("platform")
    p.add_argument("--subdomain-hits", help="JSON file, or '-' for stdin")
    p.add_argument("--marker-hits", help="JSON file, or '-' for stdin")
    p.add_argument("--geo", default="Dubai")
    p.add_argument("--role", default="coach")
    p.set_defaults(func=cmd_classify_footprint)

    return parser


def main() -> None:
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
