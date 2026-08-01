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
    fetch       the free-first site read, plus one batched Apify plan
    anchors     which hand-written lines a lead draws, and what it may cite
    deal        the same, for a whole batch, with the weights held exactly
    facts       the client-result table every number in an email traces to
    copy-usage  report a shipped batch's line usage back to Airtable
    copy-sync   pull the lines out of Airtable, rejecting any that fail the lint
    copy-check  assert Airtable is what a batch would draw from, and not a cache
    lint        the checks that make model-written copy safe
    export      leads.csv + preview.txt, refusing to write a failing email
    email-check      address shape: syntax, MX, role and typo flags
    email-verify     deliverability confirm before a send
    email-verify-batch  the same, for a whole slice's addresses in one call
    email-enrich     the no-address fallback on the lead's own domain
    apify       no-login LinkedIn / Instagram / YouTube / SERP fetch
    classify-footprint   merge pre-fetched search hits into sourcing candidates
    doc-check   the docs against the code they describe

This list is itself checked by `doc-check`. It had lost `fetch` and `facts` by
the time that check was written, three feet above the parser that has always
had them.
"""

import argparse
import csv
import json
import os
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

    try:
        leads = normalize.load_csv(args.path, source=args.source or args.path)
    except OSError as exc:
        print(f"INTAKE: FAIL — cannot read {args.path}: {type(exc).__name__}.")
        sys.exit(2)
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
    data = _load_json(path, "LEADS")
    if not isinstance(data, list):
        print(f"LEADS: FAIL — expected a JSON array of leads in {path}, got "
              f"{type(data).__name__}.")
        sys.exit(2)
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


def _load_csv(path: str, label: str, expect: tuple[str, ...]) -> list[dict]:
    """Rows from a CSV, or a clean exit 2 — never "0 rows" on the wrong file.

    Missing file, unreadable file, or a header carrying none of `expect` all
    exit 2. The last one matters most: `wall-add` on a mistyped path printed
    "0 added, 104 -> 104", which reads exactly like "this batch was already
    walled". It is not. Those leads would never enter the wall and would be
    contacted a second time, which is the failure this whole file exists to
    prevent, arrived at through a typo.
    """
    try:
        with open(path, newline="", encoding="utf-8-sig") as handle:
            reader = csv.DictReader(handle)
            rows = list(reader)
            headers = [h.strip().lower() for h in (reader.fieldnames or [])]
    except OSError as exc:
        print(f"{label}: FAIL — cannot read {path}: {type(exc).__name__}.")
        sys.exit(2)
    if not any(col in headers for col in expect):
        print(f"{label}: FAIL — {path} has none of the expected columns "
              f"({', '.join(expect)}); its header is {headers or 'empty'}. "
              f"Refusing to report 0 rows on what is probably the wrong file.")
        sys.exit(2)
    return rows


def _load_json(path: str, label: str):
    """Any JSON value from a file or stdin, or a clean exit 2.

    `_load_object` insists on an object; this one accepts either shape, for the
    commands that legitimately take an array. Both exist so that a malformed
    file is a readable gate line rather than a JSONDecodeError traceback, which
    reads as "the run crashed" when the truth is "that file is not JSON".
    """
    try:
        raw = sys.stdin.read() if path == "-" else \
            Path(path).read_text(encoding="utf-8")
        return json.loads(raw)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"{label}: FAIL — cannot read {path}: {type(exc).__name__}: {exc}")
        sys.exit(2)


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

    site_text = data.get("site_text", "")
    last = data.get("last_activity")
    if last:
        try:
            last_activity = date.fromisoformat(str(last))
        except ValueError:
            print(f"QUALIFY: FAIL — last_activity {last!r} is not an ISO date "
                  f"(YYYY-MM-DD).")
            sys.exit(2)
        activity_source = "worker"
    else:
        # No date supplied: derive one from the page text the worker already
        # fetched, rather than leaving the floor to a judgement call. Without
        # this the mechanical bridge existed only as a library function and the
        # CLI never reached it — all twelve leads on the first real batch came
        # back `unclear` on activity, and that is the floor doing nothing.
        last_activity, why = q.latest_activity_date(
            "\n".join([site_text, data.get("linkedin_text", "")]),
            page_url=data.get("site_url", "") or data.get("domain", ""))
        activity_source = why
    result = q.qualify(
        city=data.get("city", ""),
        domain=data.get("domain", ""),
        headline=data.get("headline", ""),
        site_text=site_text,
        linkedin_text=data.get("linkedin_text", ""),
        last_activity=last_activity,
        audience_size=data.get("audience_size"),
        top_program_price_aed=data.get("top_program_price_aed"),
        solo=data.get("solo", "unclear"),
    )
    print(result.report(data.get("name", "lead")))
    if not last:
        print(f"  activity settled from the page: {activity_source}")
    sys.exit(0 if result.passed else 1)


def cmd_research(args) -> None:
    """Validate a worker's returned research against the schema.

    Catches the two failures a plausible-sounding worker produces: a verdict
    outside the enum, and a hard yes/no with nothing named as its source. A
    verdict that names nothing was reasoned, not fetched.

    Accepts ONE object or an ARRAY of them. `research-worker` handles a slice of
    about ten leads and returns an array — which this used to reject outright
    with "expected one JSON object, got list", printed right beside a skill
    instruction that says a schema violation goes back to the worker once. The
    documented validation step failed on the documented file, and it failed in
    a way that reads like the worker returned garbage.
    """
    from outbound import research as r

    data = _load_json(args.input, "RESEARCH")
    if isinstance(data, dict):
        data = [data]
    if not isinstance(data, list):
        print(f"RESEARCH: FAIL — expected an object or an array of them, got "
              f"{type(data).__name__}.")
        sys.exit(2)
    if not data:
        print("RESEARCH: FAIL — no research objects to validate. An empty slice "
              "is a worker that returned nothing, not a slice that passed.")
        sys.exit(2)

    failed = 0
    for entry in data:
        if not isinstance(entry, dict):
            print(f"RESEARCH: FAIL — array holds a {type(entry).__name__}, "
                  f"expected an object per lead.")
            sys.exit(2)
        obj = r.Research.from_dict(entry)
        print(r.report(obj))
        failed += 1 if r.validate(obj) else 0
    if len(data) > 1:
        print(f"RESEARCH: {len(data) - failed}/{len(data)} valid")
    sys.exit(1 if failed else 0)


# -------------------------------------------------------------------- anchors


def cmd_anchors(args) -> None:
    """Which hand-written lines this lead draws, and every number it may cite.

    Deterministic on `sha256(email)`, so the same lead draws the same lines in
    every process on every machine. The builtin hash() is salted per process,
    which would make "reproducible" quietly false between runs.

    Says where the lines came from, and does not block on it. This is the
    single-lead and repair path: one email drafted from a day-old cached line is
    a small, visible cost, where a whole batch of them is the thing `deal`
    refuses.
    """
    from outbound import anchors

    bank = anchors.CopyBank.load()
    anchor = anchors.draw(args.email, coach_type=args.coach_type,
                          sells_to=args.sells_to, bank=bank)
    if not bank.is_live and not args.json:
        print(bank.status_line())
        if bank.rejected:
            print(f"  WARN  {len(bank.rejected)} live line(s) fail the lint, so "
                  f"Airtable's current copy is not what this draws from")
        print()
    if args.json:
        print(json.dumps({
            "identity": {"id": anchor.identity.id, "line": anchor.identity.line},
            "offer": {"id": anchor.offer.id, "line": anchor.offer.line},
            "cta": {"id": anchor.cta.id, "line": anchor.cta.line},
            "ps": {"id": anchor.ps.id, "line": anchor.ps.line},
            "segment": anchor.segment,
            "allowed_numbers": sorted(anchor.allowed_numbers),
            "hook_room": anchor.hook_room(),
        }, indent=2))
        return

    print(anchor.as_prompt_block())
    print(f"\nsegment: {anchor.segment or 'generic (no exact match drawn)'}")
    print("allowed numbers: " +
          ", ".join(str(n) for n in sorted(anchor.allowed_numbers)))
    print("\nAny number in the body outside that set is invented or relabelled.")


def cmd_copy_check(args) -> None:
    """Assert that Airtable is what this machine would actually draw from.

    The counterpart to `copy-sync`, and deliberately not the same command:
    `copy-sync` writes, this only looks. Run it at the top of a batch, where a
    wrong answer is still cheap, and again after a fix.

    It fails on the two ways stale copy ships silently — a live edit that fails
    the lint (so the bank falls back and the edit looks applied), and a cached
    file that no longer matches the table — and exits 2 when it could not read
    the table at all, because a check that cannot run is never a pass.
    """
    from outbound import copy_sync

    result = copy_sync.check()
    print(result.report())
    sys.exit(result.exit_code)


def cmd_copy_sync(args) -> None:
    """Pull the hand-written lines out of Airtable, rejecting the bad ones.

    Airtable exists so a line can change without touching code. That is only
    safe because this is a gate: a line whose numbers do not trace to
    `copy/results.csv`, or that attaches one segment's result to another, is
    rejected here rather than reaching a stranger's inbox two stages later.

    Two ways in. With `AIRTABLE_API_KEY` set, which is the normal case in a
    Claude Code session, a bare `copy-sync` fetches directly and `--live`
    asserts the key. Without one, a skill fetches the Copy Assets records
    through the Airtable MCP and pipes them here as JSON.

    This is the writer. `copy-check` is the reader that asserts the result is
    still true, and it is the one to run at the top of a batch.
    """
    from outbound import copy_sync

    from audit import airtable

    # Use the key when there is one. The skill and CLAUDE.md both say "run
    # `python main.py copy-sync`" after editing a line, and bare `copy-sync`
    # read stdin — so it blocked on a TTY, or exited 2 with a JSON error, at the
    # exact moment someone had just edited a line. The likely reading is
    # "Airtable is down" rather than "I was supposed to pipe records in".
    # `--live` is now an assertion (fail if no key) rather than the only way in.
    use_live = args.live or (args.input == "-" and airtable.available())
    if use_live:
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
        if args.input == "-" and (sys.stdin.isatty() or not (raw := sys.stdin.read()).strip()):
            print("COPY-SYNC: FAIL — no AIRTABLE_API_KEY and nothing piped in. "
                  "Either set the key and re-run, or fetch the Copy Assets "
                  "records through the Airtable MCP and pipe them to this "
                  "command.")
            sys.exit(2)
        if args.input == "-":
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError as exc:
                print(f"COPY-SYNC: FAIL — piped input is not JSON: {exc}")
                sys.exit(2)
        else:
            payload = _load_json(args.input, "COPY-SYNC")
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
    never received anything would silently exclude them from every future batch.

    Idempotent. Re-running it adds nothing, so running it twice after a
    half-remembered upload is safe.
    """
    from outbound import dedupe, export

    wall = dedupe.ContactWall.from_csv()
    before = len(wall)

    incoming = _load_csv(args.additions, "WALL-ADD",
                         ("name", "email", "domain"))

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

    This is the point where Airtable's lines become a specific batch's lines, so
    it is where the bank's provenance gets said out loud and enforced. Neither
    fallback is allowed to happen quietly:

    - **The live table answered and its lines fail the lint.** Somebody's edit
      is live in Airtable and unshippable, so the bank falls back and the batch
      would go out on the previous copy while the edit looks applied. Exit 1,
      and there is no override — the fix is one line in Airtable.
    - **The table could not be read at all.** Exit 1 too, but
      `--allow-cached-copy` accepts the committed lines deliberately. The cache
      is not unsafe (nothing reaches it without passing `copy_sync.validate`),
      it is merely possibly stale, and the point is that using it must be a
      decision somebody made rather than a thing that happened.
    """
    from outbound import anchors

    leads = _load_json(args.leads, "DEAL")
    if not isinstance(leads, list):
        print(f"DEAL: FAIL — expected a JSON array of leads, got "
              f"{type(leads).__name__}.")
        sys.exit(2)

    bank = anchors.CopyBank.load()
    print(bank.status_line())
    if bank.rejected:
        print("DEAL: FAIL — the live Copy Assets table is not shippable, and "
              "dealing would silently draft this batch from the cached copy "
              "instead:")
        for problem in bank.rejected[:10]:
            print(f"  LINT  {problem}")
        print("  Fix the line in Airtable and re-run. Nothing here can fix it: "
              "the table is the authority.")
        sys.exit(1)
    if not bank.is_live and not args.allow_cached_copy:
        print("DEAL: FAIL — the live Copy Assets table could not be read, so "
              "this batch would draw from a cache that nothing just checked.")
        print("  Set AIRTABLE_API_KEY and re-run, or pass --allow-cached-copy "
              "to accept the cached lines deliberately.")
        sys.exit(1)
    if not bank.is_live:
        print("  WARN  dealing from cached copy by request — anything edited in "
              "Airtable since that cache was written is not in this batch")

    dealt = anchors.deal_batch(leads, bank=bank)

    out = {
        email: {
            # The identity entry carries the CLAIM as well as the line, because
            # the line is the drafter's register and the claim is the actual
            # constraint. `export --anchors` re-checks the written sentence
            # against this, so the authority is the deal file rather than
            # whatever the drafter copied out of its prompt.
            "identity": {"id": a.identity.id, "line": a.identity.line,
                         "claim": a.claim.raw if a.claim else "",
                         "identity_words": list(a.identity_budget())},
            "offer": {"id": a.offer.id, "line": a.offer.line},
            "cta": {"id": a.cta.id, "line": a.cta.line},
            "ps": {"id": a.ps.id, "line": a.ps.line},
            "segment": a.segment,
            "allowed_numbers": sorted(a.allowed_numbers),
            # What the hook actually has to work with, given these four lines.
            # Handed over rather than left to be discovered by rejection: a
            # drafter that knows it has 14 words writes a 14-word hook, and one
            # that does not writes 20 and gets refused for length.
            "hook_room": a.hook_room(),
        }
        for email, a in dealt.items()
    }
    if args.out:
        Path(args.out).write_text(json.dumps(out, indent=2), encoding="utf-8")

    from outbound.lint import FIXED_LINE_SHARE_CAP

    shares = anchors.batch_shares(list(dealt.values()))
    print(f"DEAL: {len(dealt)} leads")

    # A ps that had to move because its offer already said the same thing. The
    # swap is correct and the drift it causes is real, so it is reported rather
    # than absorbed: `ps-01` cannot pair with `b4-01`, so it structurally cannot
    # reach its declared share whatever the weights say.
    from outbound.lint import check_echo
    swapped = sum(
        1 for a in dealt.values()
        if check_echo({"offer": a.offer.line, "cta": a.cta.line, "ps": a.ps.line})
    )
    collisions = anchors.echo_pairs(bank)
    if collisions:
        pairs = ", ".join(f"{o}+{p}" for o, p in collisions)
        print(f"  ECHO  {len(collisions)} offer/ps pair(s) cannot be dealt "
              f"together ({pairs}); ps reallocated, so its share runs under "
              f"its weight by design")
    if swapped:
        print(f"  WARN  {swapped} lead(s) still echo after reallocation — "
              f"the lint will reject them")

    # A beat that had to move so the hook had somewhere to live. Reported for
    # the same reason the echo swap is: the repair is correct and the weight
    # drift it causes is real, so it is said out loud rather than absorbed.
    from outbound.lint import MIN_HOOK_WORDS

    rooms = {email: a.hook_room() for email, a in dealt.items()}
    moved = sum(1 for a in dealt.values() if a.length_repaired)
    if moved:
        print(f"  LENGTH {moved} lead(s) drew a combination with no room for a "
              f"hook; ps/cta reallocated, so those shares drift by that much")
    short = sorted(e for e, r in rooms.items() if r < MIN_HOOK_WORDS)
    if short:
        print(f"  WARN  {len(short)} lead(s) still leave under {MIN_HOOK_WORDS} "
              f"words for a hook and no legal swap existed ({', '.join(short[:3])}) "
              f"— shorten a line in that beat or the lint will reject them")
    if rooms:
        print(f"  hook room  {min(rooms.values())} to {max(rooms.values())} words")
    for beat, per_line in shares.items():
        top = ", ".join(f"{k} {v:.0%}" for k, v in list(per_line.items())[:4])
        top_share = next(iter(per_line.values()), 0)
        flag = "  OVER CAP" if top_share > FIXED_LINE_SHARE_CAP else ""
        print(f"  {beat:<9} {top}{flag}")

    # Which segments cannot fill their 70% share without repeating a sentence.
    # The deal already spilled to generic to stay legal; this says what to write.
    thin = anchors.thin_segments(bank, cap=FIXED_LINE_SHARE_CAP)
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

    usage_rows = _load_csv(args.usage, "COPY-USAGE", ("line_id", "id", "beat"))
    counts = {r["line_id"]: int(r["count"]) for r in usage_rows
              if r.get("line_id") and str(r.get("count", "")).strip().isdigit()}

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


def _identity_claim_of(draft: dict, facts):
    """The claim spec behind one draft's identity beat, from whichever of the
    two things the draft carries.

    A drafting worker is handed the Claim inline in its prompt and reports back
    the anchor id it used, so the id is the reliable half — it is looked up in
    the live bank here rather than trusted from the draft, which is the same
    reason `export --anchors` re-checks the id against the deal. A draft with
    an explicit `identity_claim` string wins, for a caller linting a beat in
    isolation with no bank behind it.
    """
    from outbound import anchors

    raw = (draft.get("identity_claim") or "").strip()
    if raw:
        return anchors.claim_for(anchors.Line("draft", "", {"claim": raw}), facts)

    line_id = (draft.get("anchor_ids") or {}).get("identity", "")
    if not line_id:
        return None
    bank = anchors.CopyBank.load()
    for line in bank.identity:
        if line.id == line_id:
            return anchors.claim_for(line, facts)
    return None


def cmd_lint(args) -> None:
    """The gate on model-written copy. Per email, then across the batch.

    Traceability is the load-bearing check: every number in a body must resolve
    to that lead's allowed fact set. The client results are real and they come
    up on a call, and these coaches compare emails, so an invented digit or a
    segment's number relabelled onto another segment is the tell that the whole
    email was fabricated.
    """
    from outbound import anchors, lint

    drafts = _load_json(args.input, "LINT")
    if isinstance(drafts, dict):
        drafts = [drafts]
    if not isinstance(drafts, list):
        print(f"LINT: FAIL — expected a JSON array of drafts, got "
              f"{type(drafts).__name__}.")
        sys.exit(2)

    from outbound.export import assemble_body

    facts = anchors.load_facts()
    failed = 0
    for draft in drafts:
        allowed = draft.get("allowed_numbers")
        if allowed is None:
            allowed = anchors.all_numbers(facts)
        beats = draft.get("beats", {})
        # Assemble from the beats when no body is given, exactly as `export`
        # does. A drafting worker returns beats — its whole contract is beats —
        # and this used to answer "body is empty", so the PASS line it is
        # required to quote was unobtainable. The alternative, telling workers
        # to assemble their own, is worse: the order is load-bearing, and a
        # worker that joined it differently would quote a PASS about text that
        # is not what ships, with word count the check most likely to differ.
        # One assembler, used by both commands, is the only version that cannot
        # drift.
        body = draft.get("body") or ""
        if not body.strip() and beats:
            body = assemble_body(
                beats, greeting_name=draft.get("first_name", "")
                or (draft.get("name", "").split() or [""])[0])
        result = lint.check_email(
            name=draft.get("name", draft.get("slug", "lead")),
            subject=draft.get("subject", ""),
            body=body,
            beats=beats,
            allowed_numbers=set(allowed),
            facts=facts,
            identity_claim=_identity_claim_of(draft, facts),
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

    drafts_raw = _load_json(args.input, "EXPORT")
    if not isinstance(drafts_raw, list):
        print(f"EXPORT: FAIL — expected a JSON array of drafts, got "
              f"{type(drafts_raw).__name__}.")
        sys.exit(2)
    if args.rebalance_ps:
        # Holds are guaranteed by design — a refuted hook, a twice-refused draft
        # — and every hold unbalances a deal made for the larger batch. Dropping
        # 3 of 11 on the first real run put two ps lines at 38% against a 35%
        # cap and the batch check blocked the file, correctly. Re-dealing from
        # scratch is the wrong answer: it moves identity lines too, forcing a
        # re-draft of emails that already passed a cold read.
        #
        # The ps is the one beat that can move safely. It is library copy the
        # drafter reproduces near-verbatim, it sits alone at the end, and it
        # takes no part in the seam between the hook and the identity beat. So
        # this is an allocation decision, not a drafting one.
        # Export runs in its own process, so the bank is loaded again here and
        # can differ from the one `deal` used if Airtable went down in between.
        # Said out loud rather than blocked: `--anchors` already rejects any
        # draft whose lines disagree with the deal, so a divergence fails
        # closed on its own — it just reads as a mysterious anchor mismatch
        # without this line.
        bank = anchors.CopyBank.load()
        if not bank.is_live:
            print(bank.status_line())
        moves = anchors.rebalance_ps(drafts_raw, bank=bank)
        by_id = {l.id: l.line for l in bank.ps}
        moved = 0
        for row in drafts_raw:
            new_id = moves.get(row.get("email", ""))
            if not new_id:
                continue
            if row.get("anchor_ids", {}).get("ps") != new_id:
                moved += 1
            row.setdefault("anchor_ids", {})["ps"] = new_id
            row.setdefault("beats", {})["ps"] = by_id[new_id]
        print(f"REBALANCE: {moved} ps line(s) reallocated across "
              f"{len(drafts_raw)} shipped lead(s)")

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
        dealt = _load_json(args.anchors, "EXPORT")
        # A rebalance moved the ps, so the deal file must be told or the drift
        # check rejects every reallocated lead for using a line it was given.
        if args.rebalance_ps and isinstance(dealt, dict):
            for row in drafts_raw:
                email = row.get("email")
                new_id = row.get("anchor_ids", {}).get("ps")
                if email in dealt and new_id:
                    dealt[email]["ps"] = {"id": new_id,
                                          "line": row.get("beats", {}).get("ps", "")}

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


class _LocalVerifierError(Exception):
    """Never raised. `_email_verifier` returns an exception class alongside the
    verify function so its three callers can have one `except` shape; the local
    verifier has no failure mode that reaches them, and saying that with a class
    nothing throws is honester than naming a real one that never fires."""


def _email_verifier(approved: bool = False):
    """Which verifier to use. `EMAIL_VERIFY_PROVIDER` picks — `apify` (default)
    or `local` — and a capped Apify quota falls back to the local check rather
    than spending an attempt that would just 402.

    The fallback used to be ZeroBounce. When the Apify actor's outage finally
    called on it, `getcredits` returned `{"Credits":"0"}` and the machine had no
    working verifier at all while the docs said it did. It is gone. The local
    check cannot confirm a mailbox and never claims to, but it is always there,
    it costs nothing, and its FAILs are real.
    """
    import os
    import functools
    from audit import email_check
    # `verify_local` cannot raise — every DNS path inside `check_email` catches
    # its own failures and returns a verdict — so the local branch names an
    # exception class that will never fire rather than pretending otherwise.
    local_never_raises = _LocalVerifierError
    provider = os.environ.get("EMAIL_VERIFY_PROVIDER", "apify").strip().lower()
    if provider == "local":
        return email_check.verify_local, local_never_raises, "local MX check, no paid verifier"

    note_prefix = ""
    if provider not in ("apify", ""):
        note_prefix = f"EMAIL_VERIFY_PROVIDER={provider!r} is not a provider, using apify — "

    from audit import apify
    capped, note = _apify_quota_note()
    if capped:
        return (email_check.verify_local, local_never_raises,
                f"{note_prefix}{note} — auto-switched to the local MX check for this call")
    return (functools.partial(apify.verify_emails, approved=approved),
            apify.ApifyError, note_prefix.rstrip(" —") or None)


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


def cmd_email_verify_batch(args) -> None:
    """Same gate as `email-verify`, one call for the whole list. A verifier
    run is priced per address regardless of whether the addresses arrive in
    one call or ten — batching pays for the run once instead of once per
    lead, same lever as the tier-0 site fetch and `deal`. Prints one
    quotable line per address, same format as the single-address command,
    so nothing downstream has to tell them apart.

    This is also the only place that can see a verifier outage, because an
    outage is a property of the run and not of any address in it. Exit 2 when
    the batch looks dead: nothing is wrong with these addresses, so exit 1
    would be a lie about them, and exit 0 is how 40 leads went past a broken
    verifier looking like catch-alls."""
    from audit import email_check
    from audit.apify import ApifyCostApprovalRequired
    verify_fn, error_cls, note = _email_verifier(approved=args.approve_cost)
    try:
        rows = verify_fn(args.addresses)
    except ApifyCostApprovalRequired as exc:
        print(f"EMAIL VERIFY: APPROVAL REQUIRED — {exc}")
        sys.exit(3)
    except error_cls as exc:
        for addr in args.addresses:
            print(f"EMAIL VERIFY: WARN — {addr}: verifier unavailable "
                  f"({exc}) — inconclusive, could not confirm deliverability")
        sys.exit(0)
    by_email = {(r.get("email") or "").strip().lower(): r
                for r in rows if isinstance(r, dict)}
    worst = 0
    for addr in args.addresses:
        code = email_check.print_verify(
            addr, by_email.get(addr.strip().lower()), note=note or "")
        worst = max(worst, code)

    suspect = email_check.batch_health(list(rows) if rows else [])
    if suspect:
        print(suspect)
        sys.exit(2)
    sys.exit(worst)


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
    result = fetch.batch_fetch(leads, max_pages=args.max_pages,
                               workers=args.workers)
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

    if not args.escalate:
        if result["escalate_plans"]:
            print("  (pass --escalate --approve-cost to run these; they are paid)")
        return

    # Off by default and gated exactly like every other paid call. Before this
    # the plan named an actor that was in no ACTORS map, so it could only be run
    # by hand, outside the approval path — and the first real batch skipped it.
    from audit.apify import ApifyCostApprovalRequired, ApifyError

    escalated = {}
    for plan in result["escalate_plans"]:
        try:
            escalated[plan["actor_key"]] = fetch.run_plan(
                plan, approved=args.approve_cost)
        except ApifyCostApprovalRequired as exc:
            print(f"FETCH: APPROVAL REQUIRED — {exc}")
            sys.exit(3)
        except ApifyError as exc:
            print(f"FETCH: escalation failed ({exc}) — tier 0 results above stand")
            sys.exit(1)
    for key, items in escalated.items():
        print(f"  ESCALATED {key}: {len(items)} page(s) back")
    if args.out:
        payload["escalated"] = escalated
        Path(args.out).write_text(json.dumps(payload, indent=2, default=str),
                                  encoding="utf-8")


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
            target = args.urls[0] if len(args.urls) == 1 else args.urls
            out = apify.linkedin_profile(target, with_email=args.email, raw=args.raw,
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


# ------------------------------------------------------------------- doc-check


def cmd_doc_check(args) -> None:
    """The docs against the code they describe.

    Every gate here is quoted verbatim by a skill, which only works while the
    quoted command still exists. And every file in `docs/spec/` promises
    something stronger: that it states a decision and its reason and never
    holds a value something else owns.

    Both promises rot invisibly, because nothing reads a doc. The previous
    project's doc set died of exactly that and cost a commit titled "Sweep the
    last stale prices and rename the guarantee everywhere". This is that sweep,
    run by a machine, on every test run.

    `--live` is an assertion, not a switch: the CRM schema check already runs
    whenever `AIRTABLE_API_KEY` is set, and this makes a missing key exit 2
    instead of a reported skip. Same shape as `copy-sync --live`, and for the
    same reason — "it would have run if it could" is not a thing to rely on.
    """
    from outbound import doc_check

    try:
        result = doc_check.check_docs(parser=build_parser(),
                                      airtable=True if args.live else None)
    except doc_check.DocCheckError as exc:
        # Exit 2, never 0. Something it could not read must never report as
        # clean, for the same reason an unreadable wall must never read as
        # "nobody has been contacted". Says "could not run" rather than "cannot
        # read the docs" because the CRM schema check can fail here too, and a
        # network error reported as a docs problem sends the reader to the
        # wrong file.
        print(f"DOC-CHECK: FAIL — could not run: {exc}. "
              f"Refusing to report a check it could not complete.")
        sys.exit(2)
    print(result.report())
    sys.exit(0 if result.ok else 1)


# ------------------------------------------------------------------------ CLI


def build_parser() -> argparse.ArgumentParser:
    # Imported for one default. `doc-check` builds this parser, so anything
    # heavy at import time here is paid by the test suite too.
    from outbound import fetch as fetch_defaults

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
    p.add_argument("--workers", type=int, default=fetch_defaults.DEFAULT_WORKERS,
                   help="concurrent site reads (network-bound; 1 restores the "
                        "serial loop that could not finish 151 sites)")
    p.add_argument("--escalate", action="store_true",
                   help="actually RUN the batched Apify plan, not just print it")
    p.add_argument("--approve-cost", action="store_true",
                   help="approve the escalation's cost (see exit 3)")
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
    p.add_argument("--allow-cached-copy", action="store_true",
                   help="deal from copy/*.csv or the snapshot when the live "
                        "Copy Assets table cannot be read. Never silent: the "
                        "run says so. Does NOT override a live table whose "
                        "lines fail the lint — that one is fixed in Airtable")
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

    p = sub.add_parser("copy-check",
                       help="assert the live Copy Assets table is what a batch "
                            "would draw from, and that copy/ still matches it")
    p.set_defaults(func=cmd_copy_check)

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
    p.add_argument("--rebalance-ps", action="store_true",
                   help="reallocate the ps across the leads that actually ship. "
                        "Use after holds: a deal made for 11 leads puts two ps "
                        "lines over the 35%% cap once 3 of them hold, and "
                        "re-dealing would move identity lines and force a "
                        "re-draft of emails that already passed a cold read")
    p.set_defaults(func=cmd_export)

    p = sub.add_parser("email-check", help="free shape check: syntax, MX, role/typo flags")
    p.add_argument("address")
    p.add_argument("--name", help="lead's full name, for the name-match note")
    p.set_defaults(func=cmd_email_check)

    p = sub.add_parser("email-verify", help="deliverability confirm before a send")
    p.add_argument("address")
    p.add_argument("--approve-cost", action="store_true")
    p.set_defaults(func=cmd_email_verify)

    p = sub.add_parser("email-verify-batch",
                       help="deliverability confirm for a whole slice, one call")
    p.add_argument("addresses", nargs="+")
    p.add_argument("--approve-cost", action="store_true")
    p.set_defaults(func=cmd_email_verify_batch)

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
    a.add_argument("urls", nargs="+",
                   help="one URL, or several to batch into one actor run")
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

    p = sub.add_parser("doc-check",
                       help="the docs against the code they describe")
    p.add_argument("--live", action="store_true",
                   help="demand the CRM schema check ran (needs AIRTABLE_API_KEY)")
    p.set_defaults(func=cmd_doc_check)

    return parser


def main() -> None:
    args = build_parser().parse_args()
    try:
        args.func(args)
    except BrokenPipeError:
        # `python main.py deal ... | head` closes the pipe mid-print, and the
        # default handling is a traceback on exit — which looks exactly like a
        # crash in a gate whose whole job is to be believed. Piping a gate's
        # output into head or grep is ordinary, so it must be silent.
        try:
            sys.stdout.close()
        finally:
            os._exit(0)


if __name__ == "__main__":
    main()
