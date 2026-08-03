"""The outbound machine's CLI. Python owns every check; the model owns the words.

The division of labour that survived the pivot from the funnel-auditor: a skill
fetches and reasons, and then calls one of these commands to decide. Anything a
machine can settle deterministically — a number that isn't in the fact table, a
duplicate name, a floor verdict with no source behind it — is settled here and
printed as a line the skill quotes verbatim rather than paraphrases.

Every gate fails closed. A check that cannot run is a failure, never a pass.

    intake      raw CSV -> profiled, junk-stripped Leads
    ig-intake   an Instagram profile dump -> Leads AND the observations it
                already carries, so the paid posts rung buys nothing new
    icf-intake  an ICF directory export (.xlsx) -> Leads AND the ICP fields the
                coach filled in themselves. The values are cell hyperlinks
    icf-export  the enrichment joined back onto that workbook, plus the
                committed CSV and leads.json
    chunk       an enriched list -> the chunks a batch runs, and the leads it
                holds out with a written reason. Cut by evidence, not row number
    triage      RUN / HOLD / DROP before anything is spent. `unclear` is HOLD
    corpus      attach a corpus somebody else retrieved to the list being run
    dedupe      the Contacted-Before wall, both passes
    wall-add    append a shipped batch to the wall, after it is uploaded
    qualify     the three floors, run over a research JSON
    research    validate one worker's returned research object
    observe     validate the observations a worker says it actually fetched
    hook        check a proposed hook BEFORE a verifier certifies its wording
    fetch       the free-first site read, plus one batched Apify plan
    resolve     which channels are plausibly this lead's own, and on what evidence
    plan        which hook rungs a lead has, and what each would cost
    select      which observation a hook would be made from, without fetching
    anchors     which hand-written lines a lead draws, and what it may cite
    deal        the same, for a whole batch, with the weights held exactly
    facts       the client-result table every number in an email traces to
    copy-usage  report a shipped batch's line usage back to Airtable
    copy-sync   pull the lines out of Airtable, rejecting any that fail the lint
    copy-check  assert Airtable is what a batch would draw from, and not a cache
    lint        the checks that make model-written copy safe
    export      leads.csv + preview.txt, refusing to write a failing email
    crm-rows    the Airtable Leads rows, joined explicitly and failing closed.
                Computes only — a human still performs the write
    email-check      address shape: syntax, MX, role and typo flags
    email-verify     deliverability confirm before a send
    email-verify-batch  the same, for a whole slice's addresses in one call
    email-enrich     the no-address fallback on the lead's own domain
    email-find       an address somebody else published, one batched search run
    channel-find     the LinkedIn / Instagram / website a list arrives without,
                     corroborated before anything is written
    ledger      what each retrieval cost and how long it took
    metrics     what the hook stage yielded, and what the leads that yielded
                nothing cost. `?` for a count nobody supplied, never 0
    verdict     validate a cold read before anything routes on it
    redraft     route a wave of cold reads: who goes back, who holds, and the
                one note that covers a beat several drafts failed on
    collect     assemble a stage's state file from the per-lead files, instead
                of out of the orchestrator's context
    usage       what the batch cost in Claude tokens, MEASURED from the session
                transcript — the half `ledger pass` cannot see, including the
                orchestrator, which reports no passes and is usually the largest
    replies     join a Smartlead replies export on email — reply rate by hook
                type and by the rung the hook came from
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
import re
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
    print(_reachability_note(shape))
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


def _reachability_note(shape: dict) -> str:
    """Whether this list can produce emails at all, said at intake.

    D32's number. A lead with no branded domain has nothing for `email-enrich`
    to guess against and usually nothing for `email-find` to find, so a list's
    own-domain rate predicts its yield before a cent is spent. The Instagram
    list where 13% of the ICP owned a domain shipped 2 emails from 237 rows, and
    every count printed above it looked fine.
    """
    total = shape.get("total") or 0
    if not total:
        return "  no rows to profile"
    rate = (shape.get("with_site") or 0) / total
    line = (f"  own domain        {shape.get('with_site', 0)}/{total} "
            f"({rate:.0%}) — the number that predicts whether this list can be "
            f"emailed")
    if rate < 0.20:
        line += ("\n                    LOW. Under about 20%, most leads will "
                 "end unreachable however good the research is (D32). Say so "
                 "before spending.")
    return line


def icf_intake_sheet() -> str:
    """The default sheet name, read from the module that owns it rather than
    typed into the parser — the same rule `docs/spec/00-index.md` states for
    docs, applied to argparse."""
    from outbound.icf_intake import SHEET

    return SHEET


def cmd_icf_intake(args) -> None:
    """An ICF directory export -> Leads, plus the ICP fields it already answers.

    Separate from `intake` because this source's real values are not in its
    cells. `ICF profile` reads "View profile" in all 311 rows and the URL that
    reaches the listing lives only in the cell's hyperlink target, so a CSV
    conversion produces a fully-populated column carrying nothing.

    The second output is a **hint file, never a verdict**. A directory listing
    is the coach's own words, which is what `sells_to` requires — and it is also
    stale by construction, so nothing in it settles a floor. It is written to
    its own path, every value carrying `icf_directory`, precisely so no later
    stage can mistake it for something a worker fetched.

    Exit 2 when the workbook, the sheet or openpyxl cannot be read — a list
    nobody could open is not a list of zero coaches. Exit 1 on an unmet
    `--expect`, which is `collect`'s rule: a count of what was found is not a
    count of what should exist.
    """
    from outbound import icf_intake

    try:
        leads, prefills = icf_intake.ingest(
            args.path, sheet=args.sheet, source=args.source or icf_intake.SOURCE)
        unmapped = icf_intake.unmapped_columns(args.path, sheet=args.sheet)
    except icf_intake.ICFIntakeError as exc:
        print(f"ICF INTAKE: FAIL — {exc}")
        sys.exit(2)

    print(icf_intake.report(leads, prefills))
    if unmapped:
        print(f"  columns the alias table does not map: {', '.join(unmapped)}")
        print("                    (they are carried in the prefill, not lost — "
              "add one to COLUMN_ALIASES only if it belongs on a Lead)")

    arriving = [l for l in leads if l.linkedin_url or l.instagram_url]
    if arriving:
        print(f"  {len(arriving)} lead(s) arrived with a social URL in the "
              f"website column, already routed — that is a channel nobody has "
              f"to search for")

    if args.out:
        Path(args.out).write_text(
            json.dumps([l.to_dict() for l in leads], indent=2, default=str),
            encoding="utf-8")
        print(f"  wrote {args.out}")
    if args.prefill:
        Path(args.prefill).write_text(
            json.dumps(prefills, indent=1, default=str), encoding="utf-8")
        print(f"  wrote {args.prefill}")

    if args.expect and len(leads) != args.expect:
        print(f"ICF INTAKE: FAIL — expected {args.expect} lead(s), got "
              f"{len(leads)}. A count of what was found is not a count of what "
              f"should exist.")
        sys.exit(1)


def cmd_chunk(args) -> None:
    """An enriched list -> the chunks a batch runs, and the leads it holds out.

    A 300-lead list is not a batch. q3 spent 182M tokens on 34 raw rows, so the
    size and the membership of a run are decisions worth writing down once and
    deterministically rather than re-deciding by hand at the top of every run.

    The cut is by evidence because the leads are not interchangeable: a dead
    address produces no row however good the hook is, and a lead with no channel
    has nowhere for research to look. Thirds of the file would pay for both
    groups three times over.

    **Nothing is dropped.** Every excluded lead lands in the held-out file
    carrying its reason, so a hundred missing rows read as a decision somebody
    made rather than as an oversight — `qualify`'s rule that a false kill is
    permanent and invisible, applied one stage earlier.

    Exit 2 when the enrichment cannot be read — an unreadable file is not a list
    of zero coaches. Exit 1 on a lead the enrichment does not carry, named:
    silently holding it out and deliberately holding it out look identical in
    the output and differ by whether anybody decided anything.
    """
    from outbound import chunk as chunk_mod

    leads = _load_leads(args.leads)
    try:
        enriched = chunk_mod.load_enriched(args.enriched)
    except chunk_mod.ChunkError as exc:
        print(f"CHUNK: FAIL — {exc}")
        sys.exit(2)

    groups, reasons, unjoined = chunk_mod.assign(
        leads, enriched, seed=args.seed)
    print(chunk_mod.report(groups, reasons, enriched))

    if unjoined:
        print(f"CHUNK: FAIL — {len(unjoined)} lead(s) are not in "
              f"{args.enriched}, so nothing decided where they go:")
        for lead in unjoined[:10]:
            print(f"    {getattr(lead, 'name', '?')} "
                  f"<{getattr(lead, 'email', '')}>")
        if len(unjoined) > 10:
            print(f"    ... and {len(unjoined) - 10} more")
        sys.exit(1)

    if args.dry_run:
        print("  --dry-run: wrote nothing")
        return
    for path in chunk_mod.write(groups, reasons, args.out_dir,
                                prefix=args.prefix):
        print(f"  wrote {path}")
    print("  commit all four — membership is the record, and a held-out lead "
          "with no file is a lead nobody can explain later")


def cmd_ig_intake(args) -> None:
    """An Instagram profile dump -> Leads AND the corpus it already carries.

    `intake` maps a CSV and maps nothing here: the last IG probe returned 0 rows
    on the dump's own shape and continued by hand. The second output is the
    reason this is a command rather than a converter — a profile record carries
    the account's recent posts with verbatim captions, real timestamps and their
    own URLs, which is what `plan`'s `ig_posts` rung pays to fetch. Ingesting
    them means the activity floor settles from a date and the hook stage quotes
    something already retrieved.

    **Both outputs are validated before either is written.** A malformed dump
    must not seed a corpus a later stage will quote; that is `observe`'s gate
    used at the moment the records are made rather than discovered by the stage
    that finally needs them.
    """
    from outbound import ig_intake, observe

    try:
        leads, observations = ig_intake.ingest(
            args.path, source=args.source or args.path,
            fetched_at=args.fetched_at or "")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"IG-INTAKE: FAIL — cannot read {args.path}: {exc}")
        sys.exit(2)

    problems = observe.validate_all(observations)
    if problems:
        print(f"IG-INTAKE: FAIL — {len(problems)} observation problem(s), "
              f"nothing written:")
        for problem in problems[:20]:
            print(f"  {problem}")
        sys.exit(1)

    shape = ig_intake.profile(leads, observations)
    print(f"IG-INTAKE {args.path}: {shape['total']} profiles")
    print(f"  live site            {shape['with_site']}")
    print(f"  social only          {shape['social_only']}")
    print(f"  nothing to work      {shape['no_research_target']}")
    print(f"  with a corpus        {shape['with_observations']} "
          f"({shape['posts']} posts, {shape['observations']} observations)")
    print(f"  no posts in the dump {shape['no_posts']}")
    print(_reachability_note(shape))
    print("  a dump is a CORPUS, not a source list (D32) — attach it to a list "
          "that arrives reachable with `corpus attach`")

    if args.out:
        Path(args.out).write_text(
            json.dumps([l.to_dict() for l in leads], indent=2, default=str),
            encoding="utf-8")
        print(f"  wrote {args.out}")
    if args.observations:
        Path(args.observations).write_text(
            json.dumps([o.to_dict() for o in observations], indent=2,
                       default=str),
            encoding="utf-8")
        print(f"  wrote {args.observations}")


def cmd_corpus(args) -> None:
    """Attach a corpus somebody else retrieved to the list actually being run.

    D32: an Instagram dump is evidence, not a source list — 237 profiles shipped
    2 emails because the ICP there does not own a domain and cannot be emailed.
    Its hooks were the best on record. So the dump belongs beside a list that
    arrives reachable, and until now it could not be: `ig-intake` keys every
    observation by the IG lead's own `fetch.lead_key`, and a queue CSV's row for
    the same human has a different site and therefore a different key.

    **Never exits 1 on a routing decision** — only on an unmet `--expect`, which
    is a claim the caller made about coverage, not a judgement this makes.
    """
    from outbound import corpus, observe
    from outbound.normalize import Lead

    data = _load_json(args.observations, "CORPUS")
    if isinstance(data, list) and any(
            isinstance(e, dict) and "observations" in e for e in data):
        data = [obs for entry in data for obs in (entry.get("observations") or [])]
    try:
        observations = observe.load(data)
    except (TypeError, ValueError, AttributeError) as exc:
        print(f"CORPUS: FAIL — {args.observations} is not a corpus "
              f"({type(exc).__name__}).")
        sys.exit(2)

    rows = _load_json(args.leads, "CORPUS")
    if not isinstance(rows, list):
        print("CORPUS: FAIL — expected a Leads array from `intake --out`.")
        sys.exit(2)
    leads = [Lead(**{k: v for k, v in row.items()
                     if k in Lead.__dataclass_fields__}) for row in rows]

    result = corpus.attach(leads, observations)
    print(corpus.report(result, total_leads=len(leads), expect=args.expect))

    problems = observe.validate_all(result.observations)
    if problems:
        print(f"CORPUS: FAIL — {len(problems)} re-keyed observation(s) no longer "
              f"pass the schema, nothing written:")
        for problem in problems[:10]:
            print(f"  {problem}")
        sys.exit(2)

    if args.out:
        Path(args.out).write_text(
            json.dumps([o.to_dict() for o in result.observations], indent=2,
                       default=str), encoding="utf-8")
        print(f"  wrote {args.out}")
    sys.exit(1 if corpus.short(result, args.expect) else 0)


def cmd_triage(args) -> None:
    """Sort a list into RUN / HOLD / DROP before anything is spent.

    The floors are `qualify`'s, called rather than re-implemented, and `unclear`
    is HOLD and never DROP — a false kill is permanent and invisible. The only
    `no` this stage can reach on evidence nobody fetched twice is a stale
    activity date, and only with `--complete-corpus`, which asserts that the
    observations are everything the channel has rather than a sample of it.

    **It never exits 1 on a routing decision.** A triage is a description, the
    same as a plan is, and the operator reading the DROP list is the gate.
    """
    from outbound import observe, triage as triage_mod
    from outbound.normalize import Lead

    leads_data = _load_json(args.leads, "TRIAGE")
    if not isinstance(leads_data, list):
        print("TRIAGE: FAIL — expected a Leads array from `ig-intake --out`.")
        sys.exit(2)
    leads = [Lead(**{k: v for k, v in row.items()
                     if k in Lead.__dataclass_fields__}) for row in leads_data]

    observations = []
    if args.observations:
        observations = observe.load(_load_json(args.observations, "TRIAGE"))

    results = triage_mod.triage_all(leads, observations,
                                    complete_corpus=args.complete_corpus)
    print(triage_mod.report(results))
    note = triage_mod.reachability(leads, results)
    if note:
        print(note)

    if args.out:
        Path(args.out).write_text(
            json.dumps([r.to_dict() for r in results], indent=2, default=str),
            encoding="utf-8")
        print(f"  wrote {args.out}")
    if args.run_out:
        keep = triage_mod.selected(results, triage_mod.RUN)
        from outbound.fetch import lead_key as key_of
        kept = [row for lead, row in zip(leads, leads_data)
                if key_of(lead) in keep]
        Path(args.run_out).write_text(
            json.dumps(kept, indent=2, default=str), encoding="utf-8")
        print(f"  wrote {args.run_out} ({len(kept)} RUN leads)")


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


def _read_text(path: str, label: str) -> str:
    """Raw text from a file or stdin, or a clean exit 2.

    The CSV sibling of `_load_json`. A Smartlead export is not JSON, and an
    unreadable one must produce a gate line rather than a traceback for exactly
    the same reason: "that file is not there" and "the run crashed" are
    different answers and only one of them is true.
    """
    try:
        return sys.stdin.read() if path == "-" else \
            Path(path).read_text(encoding="utf-8-sig")
    except OSError as exc:
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
    activity_source = ""
    if last:
        try:
            last_activity = date.fromisoformat(str(last))
        except ValueError:
            print(f"QUALIFY: FAIL — last_activity {last!r} is not an ISO date "
                  f"(YYYY-MM-DD).")
            sys.exit(2)
        activity_source = "worker"
    else:
        # The observations the worker already retrieved come first: they carry
        # real publication dates, which is the evidence this floor has never
        # had. They can only ever settle it as a `yes` — see
        # `activity_from_observations`, which returns None for a stale set
        # rather than handing `check_active` a date it would answer `no` to.
        last_activity, why = q.activity_from_observations(
            data.get("observations") or [])
        # Then the page text the worker fetched, rather than leaving the floor
        # to a judgement call. Without this the mechanical bridge existed only
        # as a library function and the CLI never reached it — all twelve leads
        # on the first real batch came back `unclear` on activity, and that is
        # the floor doing nothing.
        if last_activity is None:
            page_why = why
            last_activity, why = q.latest_activity_date(
                "\n".join([site_text, data.get("linkedin_text", "")]),
                page_url=data.get("site_url", "") or data.get("domain", ""))
            if data.get("observations"):
                why = f"{page_why}; {why}"
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
        print(f"  activity settled from: {activity_source}")
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

    # One lead is somebody debugging one lead; print everything. A slice is the
    # orchestrator checking a worker, and there the full block for a lead that
    # passed is four lines nobody acts on that stay in its context for the rest
    # of the run. `--verbose` restores the old output.
    full = args.verbose or len(data) == 1
    failed = quiet = 0
    for entry in data:
        if not isinstance(entry, dict):
            print(f"RESEARCH: FAIL — array holds a {type(entry).__name__}, "
                  f"expected an object per lead.")
            sys.exit(2)
        obj = r.Research.from_dict(entry)
        if full or r.needs_a_look(obj):
            print(r.report(obj))
        else:
            print(r.headline(obj))
            quiet += 1
        failed += 1 if r.validate(obj) else 0
    if len(data) > 1:
        print(f"RESEARCH: {len(data) - failed}/{len(data)} valid"
              + (f", {quiet} clean lead(s) shown as one line each — "
                 f"--verbose for the evidence" if quiet else ""))
    sys.exit(1 if failed else 0)


def cmd_observe(args) -> None:
    """Validate what a worker says it actually fetched.

    The research contract answers floors and throws the evidence away — it keeps
    a `_source` string per verdict, so the post that settled `active_recent`,
    which is the exact material a hook is made of, is read once, reduced to a
    boolean, and paid for again one stage later. An observation is that post,
    kept.

    Additive today: nothing reads observations yet, and the hook stage still
    does its own fetching. What this gate buys now is that the records being
    accumulated were schema-checked when they were written, rather than
    discovered to be unusable by the stage that finally needs them.

    Accepts ONE observation or an array, the same as `lint` — a worker handling
    a slice returns many.

    **It also accepts a research file and unwraps it.** The batch skill has
    always said to run this on `work/research-<slice>.json`, and until the first
    batch actually did, nobody noticed that a research object is not an
    observation: every one of them validated as a malformed observation with no
    platform, no kind and no url, producing fifty violations about ten objects
    that were in fact fine. `research` was checking the nested list correctly
    the whole time, so the gate was never the thing broken — the documented way
    to look at it was. Unwrapping here is the fix that keeps the documented
    command working rather than deleting it from the skill.
    """
    from outbound import observe

    data = _load_json(args.input, "OBSERVE")
    if isinstance(data, dict):
        data = [data]
    if not isinstance(data, list):
        print(f"OBSERVE: FAIL — expected an object or an array of them, got "
              f"{type(data).__name__}.")
        sys.exit(2)

    # A research object carries its observations under a key; an observation is
    # one itself. Detected rather than flagged, because the two files are both
    # legitimate inputs and asking a caller to say which is a question the shape
    # already answers.
    if any(isinstance(e, dict) and "observations" in e for e in data):
        unwrapped, carriers = [], 0
        for entry in data:
            if isinstance(entry, dict) and "observations" in entry:
                carriers += 1
                unwrapped.extend(entry.get("observations") or [])
            else:
                unwrapped.append(entry)
        print(f"OBSERVE: unwrapped {len(unwrapped)} observation(s) from "
              f"{carriers} research object(s)")
        data = unwrapped
    for entry in data:
        if not isinstance(entry, dict):
            print(f"OBSERVE: FAIL — array holds a {type(entry).__name__}, "
                  f"expected one object per observation.")
            sys.exit(2)

    observations = observe.load(data)
    print(observe.report(observations))
    sys.exit(1 if observe.validate_all(observations) else 0)


# ----------------------------------------------------------------------- hook


def cmd_hook(args) -> None:
    """Check a proposed hook before an independent verifier is spent on it.

    F4: the hook was the only consequential artifact with no mechanical gate.
    Research has a schema, observations have a schema, and the one sentence a
    stranger reads first arrived as prose and went straight to certification.

    **The ordering is the whole point.** Six of twelve drafts on
    `2026-08-01-q1` had to alter text a verifier had confirmed word for word —
    an em-dash, spaced hyphens, "touchpoints" — because every one of those rules
    ran three stages later. When a quote breaks a voice rule the honest repair is
    to pick a different quote, and only the worker can do that: it has the page
    open and the verifier has not run. The drafter, one stage on, has neither the
    alternatives nor the authority, so it edits the citation instead.

    **Exit 1 means fix the proposal, never edit their words.** Nothing here
    rewrites a quote, and nothing here has looked at the page: this is not
    verification and a PASS is not permission to skip the verifier.
    """
    from outbound import hook

    data = _load_json(args.input, "HOOK")
    if isinstance(data, dict):
        data = [data]
    if not isinstance(data, list):
        print(f"HOOK: FAIL — expected an object or an array of them, got "
              f"{type(data).__name__}.")
        sys.exit(2)
    for entry in data:
        if not isinstance(entry, dict):
            print(f"HOOK: FAIL — array holds a {type(entry).__name__}, "
                  f"expected one object per proposal.")
            sys.exit(2)

    shortlists = None
    if args.against:
        selections = _load_json(args.against, "HOOK")
        shortlists = hook.shortlists_from(selections)
        if not shortlists:
            print(f"HOOK: FAIL — {args.against} carries no lead with a "
                  f"shortlist; it should be `select --out`'s file.")
            sys.exit(2)

    proposals = hook.load(data)
    print(hook.report(proposals, shortlists=shortlists))
    sys.exit(1 if hook.validate_all(proposals, shortlists=shortlists) else 0)


# ------------------------------------------------------------------ crm-rows


def cmd_crm_rows(args) -> None:
    """Build the Airtable Leads rows, joined explicitly and failing closed.

    Twenty rows went in on `2026-08-01-q1` with no First Name, Last Name,
    Website, LinkedIn or City on any of them, because they were built from
    `work/researched.json` — which has never carried the intake identity fields.
    Those live on the normalized Lead. A `if v not in (None, "")` filter dropped
    every empty key before the request, so there was no error and no warning.

    Then the check that "verified" it counted four fields somebody expected to
    be populated and reported 20/20. A verification that only looks where you
    expect to find something is the writer certifying its own work with extra
    steps, and Haytham caught it rather than the machine.

    So: the join is explicit and a research object with no lead behind it is a
    failure rather than a row with blanks in it, and **coverage is printed for
    every field** — a field empty on every row is named whether or not it is
    required, because "nobody has a City" and "the City never got read" print
    identically otherwise.

    **It writes nothing to the CRM.** `audit/airtable.py`'s boundary is that a
    Lead row lands where a human sees it, and that stays. This computes the
    rows; a person still performs the write. What was wrong was never that a
    model did the typing — it was that a model did the join, from memory, in a
    script nothing tested.
    """
    from outbound import crm

    leads = _load_json(args.leads, "CRM")
    researches = _load_json(args.research, "CRM")
    drafts = _load_json(args.drafts, "CRM") if args.drafts else []
    for name, data in (("leads", leads), ("research", researches),
                       ("drafts", drafts)):
        if not isinstance(data, list):
            print(f"CRM: FAIL — {name} must be a JSON array, got "
                  f"{type(data).__name__}.")
            sys.exit(2)

    built = crm.build(leads, researches, drafts, batch=args.batch)
    print(built.report())
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(
            json.dumps(built.rows, indent=2, default=str), encoding="utf-8")
        print(f"  wrote {args.out} — write these by hand or through the MCP; "
              f"nothing here touches the CRM")
    sys.exit(1 if built.problems else 0)


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
            # Same pair as `deal --out`. A drafter reading either file needs
            # the floor and the pool, not one of them.
            "hook_room": anchor.hook_room(),
            "authored_budget": anchor.authored_budget(),
            "identity_budget": list(anchor.identity_budget()),
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
            # BOTH figures, because publishing only the floor made four
            # drafters on 2026-08-02-q3 independently "discover" that the
            # number was wrong. It was not wrong. `hook_room` is the floor that
            # survives an identity beat written to the top of its range, and
            # `authored_budget` is the pool the two beats share; the difference
            # is exactly the identity range, and every one of them reverse-
            # engineered it and reported the gap as a stale field. The prompt
            # block has always said this in prose. This file is what a drafter
            # actually reads, and it was handing over one of the two numbers a
            # drafter needs to allocate between its own beats.
            "authored_budget": a.authored_budget(),
            "identity_budget": list(a.identity_budget()),
        }
        for email, a in dealt.items()
    }
    if args.out:
        Path(args.out).write_text(json.dumps(out, indent=2), encoding="utf-8")

    from outbound.lint import FIXED_LINE_SHARE_CAP, MIN_BATCH_FOR_SHARES

    shares = anchors.batch_shares(list(dealt.values()))
    print(f"DEAL: {len(dealt)} leads")
    # Under the enforcement floor every share is a function of the batch size:
    # at 2 leads a line is 50% by arithmetic, and `check_batch` reports it as a
    # warning rather than a failure for exactly that reason. Saying so here too
    # keeps the two halves telling the same story — a bare `OVER CAP` on every
    # beat reads as a batch to fix, and the fixes on offer are re-dealing, which
    # the skill forbids once drafts exist, or writing copy nothing needs.
    enforced = len(dealt) >= MIN_BATCH_FOR_SHARES
    if not enforced:
        print(f"  NOTE  under {MIN_BATCH_FOR_SHARES} leads any line is a large "
              f"share by arithmetic. Shares below are reported, and `export` "
              f"warns rather than blocks on them — OVER CAP here is not a "
              f"batch to fix")

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
        budgets = [a.authored_budget() for a in dealt.values()]
        # Both, and labelled, because the printed line was the other half of
        # the confusion: an orchestrator reading "hook room 13 to 32" relays a
        # tight number, a drafter computes the pool and reports the field is
        # stale, and neither is wrong. The floor and the pool are different
        # quantities and the line now says which is which.
        print(f"  hook room  {min(rooms.values())} to {max(rooms.values())} "
              f"words, guaranteed floor per lead")
        print(f"  authored   {min(budgets)} to {max(budgets)} words shared by "
              f"the hook and the identity beat — hand BOTH to a drafter, it "
              f"allocates between its own two beats")
    for beat, per_line in shares.items():
        top = ", ".join(f"{k} {v:.0%}" for k, v in list(per_line.items())[:4])
        top_share = next(iter(per_line.values()), 0)
        over = top_share > FIXED_LINE_SHARE_CAP
        flag = ("  OVER CAP" if enforced else "  over cap, not enforced") \
            if over else ""
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
            # Named on the draft record by `hook-worker`, carried through
            # verification. A figure in the hook beat that is also in here is
            # the recipient's own, quoted; without it the drafter's only way to
            # keep it is the subject line, which nothing digit-checks.
            hook_quote=draft.get("hook_quote", ""),
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
            # Drop any body the drafter pre-assembled. Below, a present `body`
            # wins over `assemble_body`, so a swap written into `beats` would
            # never reach the shipped text: the email keeps the old ps while
            # `anchor_ids`, `line-usage.csv` and the CRM row all name the new
            # one. `--anchors` cannot see it either, because it compares
            # `beats` against the deal and `beats` is the half that moved.
            # That is the "CRM row describing an email nobody received" failure
            # arriving from the allocator instead of from a drafter.
            row.pop("body", None)
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
            hook_quote=row.get("hook_quote", ""),
        )
        allowed = row.get("allowed_numbers")
        if allowed is None:
            allowed = anchors.all_numbers(facts)
        results[draft.email] = lint.check_email(
            name=draft.name, subject=draft.subject, body=draft.body,
            beats=beats, allowed_numbers=set(allowed), facts=facts,
            hook_quote=draft.hook_quote)
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

    addresses = list(args.addresses)
    if getattr(args, "leads", ""):
        # A whole list's addresses do not fit on a command line, and typing 311
        # of them by hand is a transcription error waiting to happen.
        try:
            rows_in = json.loads(Path(args.leads).read_text(encoding="utf-8"))
            addresses += [r["email"] for r in rows_in
                          if isinstance(r, dict) and r.get("email")
                          and r["email"] not in addresses]
        except (OSError, ValueError, TypeError) as exc:
            print(f"EMAIL VERIFY: FAIL — cannot read {args.leads} "
                  f"({type(exc).__name__}: {exc})")
            sys.exit(2)
    if not addresses:
        print("EMAIL VERIFY: nothing to verify — no addresses given")
        sys.exit(2)
    args.addresses = addresses

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

    if getattr(args, "out", ""):
        # Keyed by address, carrying the verifier's own row plus the PASS /
        # WARN / FAIL the classifier settled on, so a later stage reads the
        # verdict rather than re-deriving it from `result`.
        payload = {}
        for addr in args.addresses:
            row = by_email.get(addr.strip().lower()) or {}
            status, detail = email_check.classify_verification(row or None)
            payload[addr] = dict(row, status=status, detail=detail)
        Path(args.out).write_text(json.dumps(payload, indent=1, default=str),
                                  encoding="utf-8")
        counts: dict[str, int] = {}
        for entry in payload.values():
            counts[entry["status"]] = counts.get(entry["status"], 0) + 1
        print(f"  wrote {args.out} — " + ", ".join(
            f"{n} {s}" for s, n in sorted(counts.items())))

    suspect = email_check.batch_health(list(rows) if rows else [])
    if suspect:
        print(suspect)
        sys.exit(2)
    sys.exit(worst)


def _lead_key_of(row: dict) -> str:
    """`fetch.lead_key` for a raw Leads row, or "" when the row is not one."""
    from outbound.fetch import lead_key
    from outbound.normalize import Lead

    try:
        return lead_key(Lead(**{k: v for k, v in row.items()
                                if k in Lead.__dataclass_fields__}))
    except (TypeError, ValueError):
        return ""


def _find_targets(args) -> list[dict]:
    """The leads to search for, from a file or from the command line.

    A file may be `intake --out` Leads or a research corpus; both carry `name`,
    and the headline/site fields are optional everywhere. Anything without a
    name is skipped and named, because a query built from an empty name
    searches for the words "email address" and charges for the page."""
    if args.leads:
        with open(args.leads, encoding="utf-8") as handle:
            blob = json.load(handle)
        rows = blob if isinstance(blob, list) else (
            blob.get("leads") or blob.get("research") or [])
        out = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            name = (row.get("name") or "").strip()
            if not name:
                print(f"  SKIP  a row with no name ({row.get('lead_key') or '?'}) "
                      f"— a nameless query costs a page and finds nobody")
                continue
            domains = [d for d in (row.get("site_url"), row.get("website"),
                                   row.get("domain")) if d]
            out.append({"name": name,
                        # A normalized Lead carries no `lead_key` field — it is
                        # computed. Leaving it blank keyed the whole verdict
                        # file by name, which `plan` tolerates because it reads
                        # both, and which nothing else can join a corpus on.
                        "lead_key": row.get("lead_key") or _lead_key_of(row),
                        "known_email": (row.get("email") or "").strip(),
                        "headline": row.get("headline") or row.get("title") or "",
                        "location": row.get("city") or row.get("location") or "",
                        "domains": domains})
        return out
    return [{"name": args.name, "lead_key": "", "known_email": "",
             "headline": args.headline or "",
             "location": args.location or "", "domains": list(args.domain or [])}]


def cmd_email_find(args) -> None:
    """Find an address somebody ELSE published, in one batched search run.

    The third address path, after `extract`'s harvest of the lead's own pages
    and `email_enrich`'s nominative guess at their own domain. It exists
    because both of those only ever look at the lead, and a coach's address is
    routinely printed by an accreditation body, a directory or a company page
    and nowhere else. On the 2026-08-03 probe that is exactly where four of
    five addresses were, two on domains the machine had never seen.

    **Every query goes in one run.** Correlation back to leads is on the
    query text, never on position — the actor returns records in an order
    matching nothing in particular.

    Exit 0 when every lead reached FOUND or ABSENT, 1 when any is still open
    (CLAIMED or NONE), 2 when the search layer itself could not run — which is
    the batch-health rule `email-verify-batch` learned: a dead fetch layer must
    not read as "these leads have no address"."""
    from audit import apify, email_find

    targets = _find_targets(args)
    if not targets:
        print("EMAIL FIND: nothing to search for — no named leads")
        sys.exit(2)

    # The free half, and it runs first. An address the lead printed in their own
    # bio is better corroborated than any citation this stage can buy — it
    # cannot be a different person of the same name — and searching for a lead
    # who already has one is a page charged for an answer already in hand.
    harvested = _harvest_addresses(targets, args.observations) \
        if getattr(args, "observations", None) else {}
    for target in targets:
        best = harvested.get(target["name"])
        if best:
            print(f"EMAIL FIND: SELF-PUBLISHED — {target['name']}: "
                  f"{best['email']} on their own channel "
                  f"({best['source_url'] or 'bio'}) — no search bought, and "
                  f"still a candidate a human confirms")

    searchable = [t for t in targets if not harvested.get(t["name"])]
    queries = [email_find.build_query(t["name"], t["headline"], t["location"],
                                      tuple(t["domains"]))
               for t in searchable]
    if not queries:
        _write_find_verdicts(args, targets, {}, harvested)
        sys.exit(0)
    try:
        items = apify.google_search(queries, country_code=args.country,
                                    max_pages=args.pages,
                                    ai_overview=args.ai_overview,
                                    approved=args.approve_cost)
    except apify.ApifyCostApprovalRequired as exc:
        print(f"EMAIL FIND: APPROVAL REQUIRED — {exc}")
        sys.exit(3)
    except apify.ApifyError as exc:
        print(f"EMAIL FIND: could not search ({exc}) — this says nothing about "
              f"these {len(targets)} lead(s), who have not been looked up")
        sys.exit(2)

    by_term = {}
    for item in items:
        term = ((item.get("searchQuery") or {}).get("term") or "").strip()
        if term:
            by_term[term] = item

    worst = 0
    results: dict[str, dict] = {}
    for target, query in zip(searchable, queries):
        item = by_term.get(query.strip())
        if item is None:
            print(f"EMAIL FIND: NONE — {target['name']}: the run returned no "
                  f"record for this query, so nothing was looked at")
            worst = max(worst, 1)
            result = {"verdict": "NONE", "candidates": []}
        else:
            result = email_find.find_addresses(
                target["name"], item, lead_domains=tuple(target["domains"]))
            worst = max(worst, email_find.print_find(
                target["name"], item, lead_domains=tuple(target["domains"])))
        results[target["name"]] = dict(result, query=query)

    _write_find_verdicts(args, targets, results, harvested)
    sys.exit(worst)


def _harvest_addresses(targets: list, path: str) -> dict:
    """Addresses the leads published on their own channel, keyed by name.

    Free, offline, and it runs before a single query is bought. `email-find`'s
    own failure mode is a stranger's mailbox that verifies clean; an address in
    the lead's own bio is the one kind this stage cannot get wrong about WHICH
    person of that name it belongs to.
    """
    from audit import email_find
    from outbound import observe

    try:
        with open(path, encoding="utf-8") as handle:
            data = json.load(handle)
        observations = observe.load(data)
    except (OSError, ValueError, TypeError) as exc:
        print(f"  OBSERVATIONS: could not read {path} ({type(exc).__name__}) — "
              f"harvesting nothing, and every lead still gets searched")
        return {}

    by_name = {t["name"]: t for t in targets}
    pools: dict[str, list] = {}
    for obs in observations:
        pools.setdefault(obs.lead_key, []).append(obs)

    out = {}
    for name, target in by_name.items():
        pool = pools.get(target.get("lead_key") or "", [])
        if not pool:
            # The verdict file is keyed by name because a Lead carries no
            # lead_key of its own; the corpus is keyed by `fetch.lead_key`. Fall
            # back to matching on the lead's own URLs rather than guessing a key.
            urls = {u for u in target.get("domains", []) if u}
            pool = [o for o in observations
                    if urls and any(o.url.startswith(u) for u in urls)]
        found = email_find.from_observations(
            name, pool, lead_domains=tuple(target.get("domains") or ()))
        if found:
            out[name] = found[0]
    return out


def _write_find_verdicts(args, targets: list, results: dict,
                         harvested: dict) -> None:
    """One verdict per lead, searched or harvested, for `plan --addresses`."""
    verdicts = {}
    for target in targets:
        name = target["name"]
        hit = harvested.get(name)
        result = results.get(name, {"verdict": "NONE", "candidates": []})
        if hit:
            best, verdict = hit["email"], "FOUND"
        else:
            best = next((c["email"] for c in result["candidates"]
                         if c["provenance"] == "organic"), "")
            verdict = result["verdict"]
        verdicts[target["lead_key"] or name] = {
            "name": name,
            "verdict": verdict,
            "found_email": best,
            # The whole point of the file. `plan` declines paid retrieval for a
            # lead nothing can be sent to, and "nothing can be sent to" is a
            # measurement over every cheap path, never the AI Overview's guess.
            "reachable": bool(best or target["known_email"]),
            "known_email": target["known_email"],
            "provenance": hit["provenance"] if hit else "search",
            "source_url": hit["source_url"] if hit else "",
            "query": result.get("query", ""),
        }

    if not args.out:
        return
    with open(args.out, "w", encoding="utf-8") as handle:
        json.dump(verdicts, handle, indent=1)
    unreachable = [v["name"] for v in verdicts.values() if not v["reachable"]]
    self_published = sum(1 for v in verdicts.values()
                         if v["provenance"] == "self_published")
    print(f"  wrote {args.out} — {len(verdicts) - len(unreachable)}/"
          f"{len(verdicts)} reachable"
          + (f", {self_published} of them self-published and free"
             if self_published else ""))
    if unreachable:
        print(f"  no address anywhere: {', '.join(unreachable[:12])}"
              f"{' ...' if len(unreachable) > 12 else ''}")
        print(f"  pass it to `plan --addresses {args.out}` — it declines "
              f"PAID retrieval for these and never drops them")


def cmd_channel_find(args) -> None:
    """The channels a directory list arrives without, in batched search runs.

    A row with an email and no LinkedIn is a lead the machine can contact and
    cannot hook. q1-q3's hooks came off `li_posts` and `li_profile`, so finding
    the URL is what turns a directory row into a lead with a rung.

    **Three properties, each with a precedent.**

    `--execute` is `fetch --escalate`'s rule: without it the plan is printed and
    nothing is spent, including the exact query strings, so the shape can be
    read before it is bought 300 times.

    `--leads` is the CLEAR list from `dedupe --stage early`, and its absence is
    exit 2 rather than exit 1. This is the first command here that spends on a
    whole list at once and the hard rule is dedupe before any paid call; a gate
    that could not establish its precondition could not run.

    **Chunking is for resume and blast radius, never for evading the gate.**
    45 leads is $0.11 and trips `ApifyCostApprovalRequired` every time. That is
    correct and it stays — sizing a chunk at 39 to slide under the threshold
    would be routing around an approval a human should give once.

    The state file keeps the raw organic rows beside each verdict, which is
    `select --batch`'s rule: a later change to the corroboration rule is then
    re-scorable against the corpus that produced the first answer, rather than
    a reason to pay for the same search twice.

    Exit 0 when every searched lead reached FOUND, 1 when any is still open,
    2 when the search layer could not run — a dead SERP must never read as
    "these coaches have no LinkedIn" — and 3 for cost approval.
    """
    from audit import apify, channel_find
    from outbound import ledger

    try:
        leads = json.loads(Path(args.leads).read_text(encoding="utf-8"))
        if not isinstance(leads, list):
            raise ValueError("not an array")
    except (OSError, ValueError) as exc:
        print(f"CHANNEL FIND: FAIL — cannot read {args.leads} "
              f"({type(exc).__name__}: {exc}). It must be the CLEAR list from "
              f"`dedupe --stage early` — nothing here spends on a list that has "
              f"not been checked against the wall.")
        sys.exit(2)

    batch = ledger.batch_label(getattr(args, "batch", "") or None)
    state_path = Path(args.state or f"data/runs/{batch}-channels.json")
    state = _channel_state(state_path, batch, args.shape)

    targets = _channel_targets(leads, state, args)
    if not targets:
        print(f"CHANNEL FIND: nothing to search — "
              f"{len(state['leads'])}/{len(leads)} lead(s) already have a "
              f"verdict in {state_path}. Use --refresh to re-query them.")
        _write_channel_out(args, state)
        sys.exit(0)

    plan = []
    for target in targets:
        queries = channel_find.build_queries(
            target["name"], city=target["city"], domains=tuple(target["domains"]),
            shape=args.shape)
        if queries:
            plan.append(dict(target, queries=queries))

    pages = sum(len(p["queries"]) for p in plan) * max(1, args.pages)
    estimate = pages * 0.0025
    print(f"CHANNEL FIND: {len(plan)} lead(s), {pages} search page(s), "
          f"~${estimate:.3f} — shape {args.shape!r}, batch {batch}")
    print(f"  state {state_path} ({len(state['leads'])} lead(s) already done)")

    if not args.execute:
        for entry in plan[:args.show]:
            print(f"    {entry['name']}: {' | '.join(entry['queries'])}")
        if len(plan) > args.show:
            print(f"    ... and {len(plan) - args.show} more")
        print("  PLAN ONLY — nothing spent. Add --execute to run it.")
        sys.exit(0)

    ledger.set_context(stage="channel-find", batch=batch)
    queries = [q for entry in plan for q in entry["queries"]]
    try:
        items = apify.google_search(queries, country_code=args.country,
                                    max_pages=args.pages,
                                    approved=args.approve_cost)
    except apify.ApifyCostApprovalRequired as exc:
        print(f"CHANNEL FIND: APPROVAL REQUIRED — {exc}")
        print("  Chunking below the threshold would be routing around an "
              "approval, not earning one. Re-run with --approve-cost.")
        sys.exit(3)
    except apify.ApifyError as exc:
        print(f"CHANNEL FIND: could not search ({exc}) — this says nothing "
              f"about these {len(plan)} lead(s), who have not been looked up. "
              f"Nothing was written.")
        sys.exit(2)

    by_term = {}
    for item in items:
        term = ((item.get("searchQuery") or {}).get("term") or "").strip()
        if term:
            by_term.setdefault(term, []).append(item)

    worst, found = 0, 0
    for entry in plan:
        records = [i for q in entry["queries"] for i in by_term.get(q.strip(), [])]
        if not records:
            # A query the run did not answer is not a coach with no LinkedIn.
            state["leads"][entry["lead_key"]] = {
                "name": entry["name"], "verdict": "NONE", "queries": entry["queries"],
                "accepted": {"linkedin_url": "", "instagram_url": "", "site_url": ""},
                "candidates": [], "unrelated": [],
                "reason": "the run returned no record for this query",
                "organic": [],
            }
            print(f"CHANNEL FIND: NONE — {entry['name']}: the run returned no "
                  f"record for this query, so nothing was looked at")
            worst = max(worst, 1)
            continue

        result = channel_find.find_channels(
            entry["name"], records, lead_domains=tuple(entry["domains"]),
            city=entry["city"], known=entry["known"])
        print(channel_find.report(entry["name"], result))
        worst = max(worst, 0 if result["verdict"] == "FOUND" else 1)
        found += 1 if result["verdict"] == "FOUND" else 0
        state["leads"][entry["lead_key"]] = {
            "name": entry["name"],
            "verdict": result["verdict"],
            "queries": entry["queries"],
            "accepted": result["accepted"],
            "ambiguous": result["ambiguous"],
            "from_row": result["from_row"],
            "candidates": result["candidates"],
            "unrelated": result["unrelated"],
            "reason": result["reason"],
            # The corpus beside the verdict, `select --batch`'s rule: a later
            # rule change is re-scorable rather than re-payable.
            "organic": [r for i in records for r in (i.get("organicResults") or [])],
        }

    state["chunks"].append({
        "leads": len(plan), "pages": pages, "shape": args.shape,
        "cost_usd_estimate": round(estimate, 4),
    })
    _write_channel_state(state_path, state)
    print(f"  {found}/{len(plan)} FOUND, wrote {state_path} "
          f"({len(state['leads'])} lead(s) total)")
    _write_channel_out(args, state)
    sys.exit(worst)


def cmd_icf_export(args) -> None:
    """Everything the enrichment learned, joined back onto the source workbook.

    Three artifacts from one join: the workbook with its original 31 columns
    untouched, a committed CSV, and a `leads.json` carrying the found channels
    merged in, so `intake` never has to run on this list again.

    **It prints coverage for every added column, not the ones anybody expects.**
    That is `crm-rows`' lesson: twenty rows went into the CRM with no First Name
    on any of them, and the check that passed them looked at four populated
    fields and reported 20/20.

    **Exit 1 on an unmet `--expect` or a row that does not join.** A silent
    partial join is the failure that produces a file which looks complete.
    """
    from outbound import icf_intake
    from outbound.fetch import lead_key
    from outbound.normalize import Lead

    def read(path, what):
        if not path:
            return {}
        try:
            return json.loads(Path(path).read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            print(f"ICF EXPORT: FAIL — cannot read {what} at {path} "
                  f"({type(exc).__name__}: {exc})")
            sys.exit(2)

    try:
        raw = json.loads(Path(args.leads).read_text(encoding="utf-8"))
        leads = [Lead(**{k: v for k, v in r.items()
                         if k in Lead.__dataclass_fields__}) for r in raw]
    except (OSError, ValueError, TypeError) as exc:
        print(f"ICF EXPORT: FAIL — cannot read {args.leads} "
              f"({type(exc).__name__}: {exc})")
        sys.exit(2)

    prefills = read(args.prefill, "the prefill")
    channels = read(args.channels, "the channel verdicts")
    verify = read(args.addresses, "the address verdicts")
    contacted = set(read(args.contacted, "the contacted list") or [])
    batch = ledger_batch_label(getattr(args, "batch", ""))
    at = args.at or _today()

    by_key, rows, enriched_leads = {}, {}, []
    missing = []
    for lead in leads:
        key = lead_key(lead)
        prefill = prefills.get(key) or {}
        icf_key = prefill.get("icf_key") or ""
        if not icf_key:
            missing.append(lead.name)
            continue
        channel = channels.get(key) or {}
        row = icf_intake.enriched_row(
            lead, prefill=prefill, channels=channel,
            verify=verify.get(lead.email) or {},
            contacted=key in contacted or lead.name in contacted,
            batch=batch, at=at)
        rows[icf_key] = row
        by_key[key] = row
        found = (channel.get("accepted") or {})
        merged = lead.to_dict()
        merged["linkedin_url"] = found.get("linkedin_url") or lead.linkedin_url
        merged["instagram_url"] = found.get("instagram_url") or lead.instagram_url
        merged["site_url"] = lead.site_url or found.get("site_url", "")
        enriched_leads.append(merged)

    if missing:
        print(f"ICF EXPORT: FAIL — {len(missing)} lead(s) carry no ICF key, so "
              f"they cannot be joined back to the workbook: "
              f"{', '.join(missing[:8])}")
        sys.exit(1)

    print(f"ICF EXPORT: {len(rows)} row(s), batch {batch}")
    for column in icf_intake.ENRICHED_COLUMNS:
        filled = sum(1 for r in rows.values() if str(r.get(column, "")).strip())
        print(f"  {column:26s} {filled:4d}/{len(rows)}")

    if args.out_xlsx:
        try:
            icf_intake.write_enriched(args.workbook, rows, args.out_xlsx)
        except icf_intake.ICFIntakeError as exc:
            print(f"ICF EXPORT: FAIL — {exc}")
            sys.exit(1)
        print(f"  wrote {args.out_xlsx}")

    if args.out_csv:
        import csv

        source_columns = ["Name", "Email", "Phone", "City", "Emirate",
                          "Credential", "Website (listed)"]
        with open(args.out_csv, "w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(
                handle, fieldnames=source_columns + list(icf_intake.ENRICHED_COLUMNS))
            writer.writeheader()
            for lead in leads:
                key = lead_key(lead)
                row = by_key.get(key)
                if not row:
                    continue
                prefill = prefills.get(key) or {}
                writer.writerow({
                    "Name": lead.name, "Email": lead.email, "Phone": lead.phone,
                    "City": lead.city, "Emirate": prefill.get("emirate", ""),
                    "Credential": prefill.get("credential", ""),
                    "Website (listed)": lead.site_url, **row})
        print(f"  wrote {args.out_csv}")

    if args.out_leads:
        Path(args.out_leads).write_text(
            json.dumps(enriched_leads, indent=2, default=str), encoding="utf-8")
        print(f"  wrote {args.out_leads}")

    if args.expect and len(rows) != args.expect:
        print(f"ICF EXPORT: FAIL — expected {args.expect} row(s), joined "
              f"{len(rows)}. A count of what joined is not a count of what "
              f"should have.")
        sys.exit(1)


def ledger_batch_label(label: str) -> str:
    from outbound import ledger

    return ledger.batch_label(label or None)


def _today() -> str:
    from datetime import date

    return date.today().isoformat()


def _channel_state(path: Path, batch: str, shape: str) -> dict:
    """The resume file. A lead present in `leads` is never re-queried.

    Membership, not a chunk counter: a chunk that died halfway leaves the leads
    it did answer for, and the next invocation picks up exactly the remainder.
    """
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(state, dict) and isinstance(state.get("leads"), dict):
            state.setdefault("chunks", [])
            return state
    except (OSError, ValueError):
        pass
    return {"batch": batch, "shape": shape, "leads": {}, "chunks": []}


def _write_channel_state(path: Path, state: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=1, default=str), encoding="utf-8")


def _channel_targets(leads: list, state: dict, args) -> list:
    """Which leads this invocation owes a search, in list order."""
    from outbound.fetch import lead_key
    from outbound.normalize import Lead

    wanted = None
    if getattr(args, "keys", ""):
        try:
            wanted = set(json.loads(Path(args.keys).read_text(encoding="utf-8")))
        except (OSError, ValueError):
            wanted = None

    out = []
    for raw in leads:
        lead = Lead(**{k: v for k, v in raw.items()
                       if k in Lead.__dataclass_fields__})
        key = lead_key(lead)
        if wanted is not None and key not in wanted:
            continue
        if key in state["leads"] and not args.refresh:
            continue
        out.append({
            "lead_key": key,
            "name": lead.name,
            "city": lead.city,
            "domains": [lead.site_url] if lead.site_url else [],
            "known": {"linkedin_url": lead.linkedin_url,
                      "instagram_url": lead.instagram_url,
                      "site_url": lead.site_url},
        })
        if args.chunk and len(out) >= args.chunk:
            break
    if args.limit:
        out = out[:args.limit]
    return out


def _write_channel_out(args, state: dict) -> None:
    if not getattr(args, "out", ""):
        return
    flat = {key: {k: v for k, v in entry.items() if k != "organic"}
            for key, entry in state["leads"].items()}
    Path(args.out).write_text(json.dumps(flat, indent=1, default=str),
                              encoding="utf-8")
    verdicts = {}
    for entry in flat.values():
        verdicts[entry["verdict"]] = verdicts.get(entry["verdict"], 0) + 1
    print(f"  wrote {args.out} — " + ", ".join(
        f"{count} {name}" for name, count in sorted(verdicts.items())))


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


def _run_escalations(plans: list, *, approved: bool) -> tuple[dict, list]:
    """Execute the batched Apify plans. Shared by the full run and the retry.

    Exits 3 on the cost gate, because a refused purchase means nothing was
    bought and there is nothing to keep.

    **An actor error does not exit here, and that is the whole point.** It used
    to, from inside the loop, which threw away every plan that had already
    succeeded — including the paid ones. On `2026-08-02-q3` the static crawl
    returned 12 pages and the render crawl then died of an OOM the caller could
    not have predicted; the successful half was discarded, the retry ran static
    a second time, and it was discarded again. Two paid runs, nothing kept.
    A failing plan must cost its own results and no others, so the failures come
    back to the caller, which writes what did land before it exits.
    """
    from audit.apify import ApifyCostApprovalRequired, ApifyError
    from outbound import fetch

    escalated: dict = {}
    failures: list = []
    for plan in plans:
        try:
            escalated[plan["actor_key"]] = fetch.run_plan(plan, approved=approved)
        except ApifyCostApprovalRequired as exc:
            print(f"FETCH: APPROVAL REQUIRED — {exc}")
            sys.exit(3)
        except ApifyError as exc:
            failures.append((plan.get("actor_key"), str(exc)))
            print(f"FETCH: escalation failed for {plan.get('actor_key')} ({exc})")
    for key, items in escalated.items():
        print(f"  ESCALATED {key}: {len(items)} page(s) back")
    if failures and escalated:
        print(f"  KEPT {len(escalated)} plan(s) that succeeded; "
              f"{len(failures)} failed. Re-run `fetch --escalate-only` and it "
              f"will re-plan only what is still unread.")
    return escalated, failures


def cmd_escalate_only(args) -> None:
    """Run a saved escalation plan and read nothing at tier 0.

    The retry path, and it exists because there was not one. A batched
    escalation failed on a 403 mid-run; the obvious repair — re-run `fetch
    --escalate` — re-reads every site before it escalates, so twenty free reads
    happened again and **52 duplicate `(lead, url)` pairs** went into the
    ledger. The batch existed to produce a duplicate count. D22 records the
    risk in advance, in those words, and it happened anyway, because avoiding it
    meant calling `fetch.run_plan` by hand and nothing in the CLI offered it.

    A retry must not be able to pollute the measurement it is retrying.
    """
    payload = _load_json(args.leads, "FETCH")
    if not isinstance(payload, dict) or "escalate_plans" not in payload:
        print(f"FETCH: FAIL — {args.leads} is not a sites.json from "
              f"`fetch --out`; it carries no escalate_plans.")
        sys.exit(2)

    plans = payload.get("escalate_plans") or []
    if not plans:
        print("FETCH: nothing to escalate — this run's tier 0 read every site.")
        return

    # A retry is for the half that failed. A plan whose pages are already in
    # this file has been bought; running it again buys the same pages a second
    # time, which is the duplicate this command exists to prevent — the free
    # tier-0 re-read was only the version of it that got caught first.
    done = payload.get("escalated") or {}
    pending = [p for p in plans if not done.get(p.get("actor_key"))]
    for plan in plans:
        if plan in pending:
            print(f"  ESCALATE  {plan['why']}")
        else:
            print(f"  SKIP      {plan['actor_key']}: "
                  f"{len(done[plan['actor_key']])} page(s) already in "
                  f"{args.leads}, not buying them twice")
    if not pending:
        print("FETCH: every plan in this file has already run.")
        return
    plans = pending
    if not args.approve_cost:
        print("  (pass --approve-cost to run these; they are paid)")
        return

    escalated, failures = _run_escalations(plans, approved=args.approve_cost)
    # Merge rather than replace: a retry runs only the plans that failed last
    # time, and overwriting would drop the half that already landed.
    merged = dict(payload.get("escalated") or {})
    merged.update(escalated)
    payload["escalated"] = merged
    print("  no tier-0 read happened, so no page in this run can be a "
          "duplicate of one already in the ledger.")
    if args.out:
        Path(args.out).write_text(json.dumps(payload, indent=2, default=str),
                                  encoding="utf-8")
        print(f"  wrote {args.out}")
    if failures:
        sys.exit(1)


def cmd_fetch(args) -> None:
    """Tier 0: read sites with free local HTTP, and plan one batched Apify run
    for whatever that couldn't read.

    Container boot dominates an Apify bill, not pages, so the escalation is
    always one run for the whole batch — never one per lead.
    """
    if args.escalate_only:
        return cmd_escalate_only(args)

    from outbound import fetch

    leads = _load_leads(args.leads)
    result = fetch.batch_fetch(leads, max_pages=args.max_pages,
                               workers=args.workers)
    print(result["report"])

    payload = {
        "tier0_rate": result["tier0_rate"],
        "escalate_plans": result["escalate_plans"],
        # Keyed by `fetch.lead_key` — an email, else `slug|site_url`. The
        # variable was called `slug` for months and it never was one; `resolve`
        # joins on this key, and a join on the actual slug would have missed
        # every lead that has an address, quietly.
        "sites": {
            key: {
                "ok": read.ok,
                "pages": [{"url": p.url, "status": p.status, "chars": len(p.text)}
                          for p in read.pages],
                "emails": read.emails,
                "social": read.social,
                "prices": read.prices[:10],
                "headings": read.headings[:20],
                "notes": read.notes,
                # Until now this existed only inside the printed OWNER-CHECK
                # line, so the one ownership fact the machine had computed died
                # with the terminal it was printed to.
                "owner_match": read.owner_match,
                "text": read.text if args.with_text else "",
            }
            for key, read in result["reads"].items()
        },
    }
    if args.out:
        Path(args.out).write_text(json.dumps(payload, indent=2, default=str),
                                  encoding="utf-8")
        print(f"  wrote {args.out}")
    for plan in result["escalate_plans"]:
        print(f"  ESCALATE  {plan['why']}")

    # Named work rather than a blind spot. These leads produce no tier-0 read
    # at all, so before this they simply were not in the output and each worker
    # rediscovered the gap on its own.
    for lead in result["unowned"]:
        print(f"  OWNER?    {lead['name'] or '(no name)'} — {lead['url']} "
              f"never mentions them")
    for lead in result["ig_only"]:
        print(f"  IG        {lead['name'] or '(no name)'} — {lead['url']} "
              f"(batch these: `apify ig <url> <url> --mode details`)")
    for lead in result["needs_search"]:
        hint = " ".join(x for x in (lead["name"], lead["company"], lead["city"]) if x)
        print(f"  SEARCH    {hint or '(nothing to search on)'} "
              f"— no site and no social, free WebSearch first")

    if not args.escalate:
        if result["escalate_plans"]:
            print("  (pass --escalate --approve-cost to run these; they are paid)")
        return

    # Off by default and gated exactly like every other paid call. Before this
    # the plan named an actor that was in no ACTORS map, so it could only be run
    # by hand, outside the approval path — and the first real batch skipped it.
    #
    # **If this fails, retry with `--escalate-only <sites.json>`, not with this
    # command again.** Re-running it re-reads every site first, which is 52
    # duplicate pairs in the ledger of a batch whose whole purpose was a
    # duplicate count.
    escalated, failures = _run_escalations(result["escalate_plans"],
                                           approved=args.approve_cost)
    if args.out:
        payload["escalated"] = escalated
        Path(args.out).write_text(json.dumps(payload, indent=2, default=str),
                                  encoding="utf-8")
        print(f"  wrote {args.out}")
    if failures:
        sys.exit(1)


# -------------------------------------------------------------------- resolve


def cmd_resolve(args) -> None:
    """Which channels are plausibly this lead's own, and on what evidence.

    ~40 of 151 rows on the first real batch pointed at somebody else, and the
    two free checks that could have said so were a note and a printed line that
    nothing carried forward. This is those two checks with a type on them.

    **An `absent` verdict is never a non-zero exit.** Exit 1 here means this
    command's own output failed its own schema, which can only be a bug in it.
    Ownership gates spend, never inclusion — a lead whose every channel names
    somebody else still gets researched, still gets drafted, and still gets a
    row. Exit 1 on a bad verdict is the natural mistake, and it would be R3 of
    the proposal violated in code.
    """
    from outbound import fetch as fetch_mod, ledger, resolve

    leads = _load_leads(args.leads)
    reads = {}
    if args.sites:
        data = _load_object(args.sites, "RESOLVE")
        sites = data.get("sites") or {}
        if not isinstance(sites, dict):
            print("RESOLVE: FAIL — --sites must carry a 'sites' object, as "
                  "`fetch --out` writes it.")
            sys.exit(2)
        for key, site in sites.items():
            if not isinstance(site, dict):
                continue
            read = fetch_mod.SiteRead(domain=key)
            read.social = site.get("social") or {}
            read.owner_match = site.get("owner_match") or "unknown"
            reads[key] = read

    # The only thing this stage fetches is the link-in-bio page, which no stage
    # has ever read even though intake has been discovering them since it was
    # written. `--no-fetch` makes that skippable without making it invisible.
    ledger.set_context(stage="resolve")
    result = resolve.resolve_all(
        leads, reads, workers=args.workers,
        fetch_page=None if args.no_fetch else resolve.page_reader())
    identities = result["identities"]
    print(result["report"])

    if args.out:
        Path(args.out).write_text(
            json.dumps({"identities": [i.to_dict() for i in identities]},
                       indent=2, default=str), encoding="utf-8")
        print(f"  wrote {args.out}")
    if args.json:
        print(json.dumps([i.to_dict() for i in identities], indent=2, default=str))

    sys.exit(1 if resolve.validate_all(identities) else 0)


# ----------------------------------------------------------------------- plan


def cmd_plan(args) -> None:
    """Which rungs this lead has, what each would cost, and what we would decline.

    **It declines nothing, and a decline is never a non-zero exit.** Exit 1 here
    means this command's own output failed its own schema, which can only be a
    bug in it. D21 says ownership gates spend and never inclusion; this batch
    does not gate spend either, because D21's reversal condition — whether
    declining costs more verified hooks than it saves scrapes — has never been
    measured, and the gate that produced the data judging it would not be a
    measurement.

    **Pricing is opt-in.** `estimate_cost_usd` needs a token and the network,
    and `tests/test_cli_failures.py` shells out with the real environment, so a
    default-on lookup would reach Apify on a developer machine and not in CI —
    the whoever-runs-it failure `offline_env` exists to prevent. Without
    `--price` every paid step reports `None`, which says "not priced" and never
    "$0.0000".
    """
    from outbound import plan as plan_mod, resolve

    identities = resolve.load(_load_json(args.identities, "PLAN"))

    # The one thing an Identity does not carry: their own site. It is not a
    # channel — nothing harvests a lead's homepage into its own channel list.
    sites = {}
    if args.leads:
        for lead in _load_leads(args.leads):
            from outbound.fetch import lead_key as _lead_key

            if getattr(lead, "site_url", ""):
                sites[_lead_key(lead)] = lead.site_url

    budget = None
    if args.budget:
        budget, why = plan_mod.budget_note()
        if why:
            print(f"  {why} — planning without it")

    # Leads every cheap address path already failed on. Paid retrieval for one
    # of them buys a hook for an email nobody can receive, and the agent passes
    # behind that hook are the batch's real bill.
    unreachable = set()
    if args.addresses:
        rows = _load_json(args.addresses, "PLAN") or {}
        no_address = 0
        for key, row in rows.items():
            if row.get("reachable"):
                continue
            no_address += 1
            unreachable.add(key)
            if row.get("name"):
                unreachable.add(row["name"])
        print(f"  ADDRESSES: {no_address}/{len(rows)} lead(s) have no address on "
              f"the row, on their site, or anywhere searched — their PAID rungs "
              f"are declined. They keep every free rung and still get a row.")

    result = plan_mod.plan_all(
        identities, sites=sites, budget=budget, unreachable=unreachable,
        price=plan_mod.apify_price if args.price else None)
    plans = result["plans"]
    print(result["report"])

    if args.out:
        Path(args.out).write_text(
            json.dumps({"plans": [p.to_dict() for p in plans]},
                       indent=2, default=str), encoding="utf-8")
        print(f"  wrote {args.out}")
    if args.json:
        print(json.dumps([p.to_dict() for p in plans], indent=2, default=str))

    sys.exit(1 if plan_mod.validate_all(plans) else 0)


# --------------------------------------------------------------------- select


def cmd_select(args) -> None:
    """Which observation a hook would be made from, chosen without fetching.

    **Nothing consumes this and a disagreement is never a non-zero exit.** It
    runs alongside the hook stage rather than in place of it: `hook-worker`
    still fetches, still proposes, and is not edited. Exit 1 means this
    command's own output failed its own schema.

    `--against` is the measurement the whole phase exists for. It asks whether
    the ranker would have picked the same evidence the hook stage paid to fetch,
    and it reports five verdicts rather than two because `missed` and
    `unobserved` say opposite things about whether that fetch is removable.

    `--batch` writes both halves of that measurement into `data/runs/`: the
    selections **and the corpus they were ranked from**. Only the first was kept
    for `2026-08-01-q1`, and the corpus lived in `work/`, which does not survive
    the container. So when the ban that caused all three MISSED turned out to be
    wrong, there was no way to re-score the batch that proved it — the fix had to
    ship on a diagnosis, and the next honest number needs a new paid run.

    A ranking change should be answerable against every batch already run. That
    is only true if the input is kept, and keeping it is not something to
    remember at the end of a long session.
    """
    from outbound import select

    data = _load_json(args.input, "SELECT")
    if isinstance(data, dict):
        data = [data]
    if not isinstance(data, list):
        print("SELECT: FAIL — expected a research object or a list of them.")
        sys.exit(2)
    if any(not isinstance(row, dict) for row in data):
        print("SELECT: FAIL — every entry must be a research object.")
        sys.exit(2)

    result = select.select_all(data, size=args.shortlist,
                               hook_room=args.hook_room, against=args.against)
    selections = result["selections"]
    print(result["report"])

    payload = json.dumps({"selections": [s.to_dict() for s in selections]},
                         indent=2, default=str)
    if args.out:
        Path(args.out).write_text(payload, encoding="utf-8")
        print(f"  wrote {args.out}")
    if args.batch:
        from outbound import ledger

        verdict = ledger.artifact("-select.json", batch=args.batch)
        corpus = ledger.artifact("-research.json", batch=args.batch)
        verdict.parent.mkdir(parents=True, exist_ok=True)
        verdict.write_text(payload, encoding="utf-8")
        # The input, not a summary of it. A re-score needs every observation's
        # text, date and kind — the selections carry only the shortlist, and the
        # rejections carry a ban name and a URL, which cannot be re-ranked.
        corpus.write_text(json.dumps(data, indent=2, default=str),
                          encoding="utf-8")
        print(f"  wrote {verdict} and {corpus}")
        print(f"  commit both. `select {corpus} --against` re-scores this batch "
              f"for free after any change to the bans or the ranking.")
    if args.json:
        print(json.dumps([s.to_dict() for s in selections], indent=2, default=str))

    sys.exit(1 if select.validate_all(selections) else 0)


# -------------------------------------------------------------------- fetching


def _apify_slug(args, cmd: str) -> str:
    """A deterministic file name for one (lead, target) fetch.

    Deterministic rather than timestamped on purpose: the retrieve-once
    invariant says the same page is fetched once, so the same fetch overwriting
    its own file is right, and two different targets for one lead must not
    collide. The hash is of the target, so both hold.
    """
    import hashlib

    target = ""
    for attr in ("url", "urls", "addresses"):
        value = getattr(args, attr, None)
        if value:
            target = "|".join(value) if isinstance(value, (list, tuple)) else str(value)
            break
    digest = hashlib.sha1(target.encode("utf-8", "replace")).hexdigest()[:8]
    lead = re.sub(r"[^A-Za-z0-9._-]", "-", getattr(args, "lead", "") or "").strip("-")
    return f"{lead}-{digest}" if lead else digest


def cmd_apify(args) -> None:
    """No-login third-party fetch layer. Writes JSON, prints a summary.

    Every run is cost-gated: a call whose estimate is unknown or over the
    approval threshold exits 3 rather than running.
    """
    from audit import apify
    from outbound import ledger

    cmd = args.apify_command
    approved = getattr(args, "approve_cost", False)
    # The run facts the wrappers cannot know. `run_actor` supplies the technical
    # half — which actor, which URL, how long, what it was priced at — and picks
    # these up from the ambient context rather than threading a lead key through
    # ten signatures that have nothing else to do with it.
    ledger.set_context(lead_key=getattr(args, "lead", "") or "",
                       stage=getattr(args, "stage", "") or "research",
                       purpose=getattr(args, "purpose", "") or "observe",
                       batch=getattr(args, "batch", "") or "")
    try:
        if cmd == "limits":
            out = apify.account_limits()
        elif cmd == "actors":
            out = apify.discover_actors(args.query, args.limit)
        elif cmd == "ig":
            # One url stays a string so the single-profile path keeps raising on
            # an actor error instead of returning a None the caller has to spot.
            target = args.url[0] if len(args.url) == 1 else args.url
            out = apify.instagram(target, mode=args.mode, newer_than=args.newer_than,
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
        elif cmd == "verify-email":
            out = apify.verify_emails(args.addresses, raw=args.raw, approved=approved)
        else:
            print(json.dumps({"error": f"apify: unknown subcommand {cmd!r}"}))
            sys.exit(2)
    except apify.ApifyCostApprovalRequired as exc:
        # A refusal never reaches run_actor, so it is recorded here. What the
        # gate turned down is as worth knowing as what it let through: a batch
        # that quietly stopped at the threshold looks identical, in every other
        # record this machine keeps, to a batch that found nothing.
        ledger.record(url="", cost_usd=exc.estimated_usd, secs=0.0,
                      outcome="blocked",
                      retrieved_by=f"apify:{apify._ACTOR_KEYS.get(exc.actor_id, exc.actor_id)}")
        print(json.dumps({"error": str(exc), "needs_approval": True,
                          "actor": exc.actor_id,
                          "estimated_usd": exc.estimated_usd}, indent=2))
        sys.exit(3)
    except apify.ApifyError as exc:
        print(json.dumps({"error": str(exc)}, indent=2))
        sys.exit(1)

    payload = json.dumps(out, indent=2, ensure_ascii=False, default=str)
    # `limits` and `actors` are the answer, not a payload — a budget check that
    # wrote its number to a file would be absurd. Everything else is a dataset.
    if cmd in ("limits", "actors") or getattr(args, "print_payload", False):
        print(payload)
        return

    target = Path(getattr(args, "out", "") or ledger.artifact(
        f"-apify-{cmd}-{_apify_slug(args, cmd)}.json",
        batch=getattr(args, "batch", "") or ""))
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(payload, encoding="utf-8")
    except OSError as exc:
        # Falling back to stdout is the expensive path, so it says so rather
        # than silently doing the thing this change exists to stop.
        print(f"APIFY: could not write {target} ({exc}) — printing instead, "
              f"which is the path that costs context.")
        print(payload)
        return
    summary = apify.summarise(out)
    print(f"APIFY {cmd}: {summary['items']} item(s), {summary['with_text']} "
          f"with text"
          + (f", {summary['oldest'][:10]} to {summary['newest'][:10]}"
             if summary["newest"] else "")
          + f", {len(payload):,} bytes")
    if summary["keys"]:
        print(f"  fields: {', '.join(summary['keys'])}")
    print(f"  wrote {target}")
    print(f"  Read it, or grep it. It is not printed here on purpose: this "
          f"command used to put its whole dataset in your context.")


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


# ---------------------------------------------------------------------- ledger


def cmd_ledger(args) -> None:
    """What each retrieval cost, and how long it took.

    Two subcommands, and the split matters. `add` is the only way a model-side
    retrieval gets recorded at all — an agent's own WebSearch and WebFetch happen
    outside Python, so those lines are reported on trust, and `retrieved_by`
    keeps them distinguishable from the ones the code wrote itself. `report`
    reads a batch back.

    `report` exits 2 on a missing ledger rather than printing a zero, on the same
    asymmetry as the dedupe wall: a missing wall must never read as "nobody has
    been contacted", and a missing ledger must never read as "this batch cost
    nothing". It never exits 1 — not even on a duplicate fetch. Reporting one is
    the job; failing on one belongs to the stage that removes it, and a gate that
    can halt a real send file over an accounting line is a gate people learn to
    route around.
    """
    from outbound import ledger

    if args.ledger_command == "batch":
        if args.label:
            target = ledger.set_batch(args.label)
            print(f"LEDGER: batch {args.label} — wrote {target}")
            print("  every later command and every subagent reads it from "
                  "there. Nothing else has to be told.")
            return
        label, where = ledger.batch_source()
        print(f"LEDGER: batch {label} (from {where})")
        if where.startswith("today"):
            print("  no batch has been named. Run `ledger batch <label>` "
                  "before anything paid, or this run's cost lands in a file "
                  "named after the date and not after the batch.")
        return

    if args.ledger_command == "pass":
        wrote = ledger.record_pass(
            batch=args.batch, stage=args.stage, agent=args.agent,
            model=args.model, count=args.count)
        if not wrote:
            print("LEDGER: FAIL — could not append to "
                  f"{ledger.path(args.batch)}.")
            sys.exit(2)
        print(f"LEDGER: {args.count} {args.agent or 'agent'} pass(es) on "
              f"{args.model or 'an unnamed model'} at stage {args.stage}, "
              f"REPORTED to {ledger.path(args.batch)}")
        return

    if args.ledger_command == "add":
        wrote = ledger.record(
            batch=args.batch, lead_key=args.lead, stage=args.stage,
            platform=args.platform, url=args.url, retrieved_by=args.by,
            cost_usd=args.cost, secs=args.secs, outcome=args.outcome,
            purpose=args.purpose)
        if not wrote:
            # The one place a failed append is visible. `ledger.append` swallows
            # everything so it can never kill a batch, which means the operator
            # asking for a line to be written is the only caller who can be told.
            print("LEDGER: FAIL — could not append to "
                  f"{ledger.path(args.batch)}.")
            sys.exit(2)
        print(f"LEDGER: added {args.by} {args.platform} {args.url} "
              f"to {ledger.path(args.batch)}")
        return

    try:
        records, malformed = ledger.read(args.batch)
    except ledger.LedgerUnreadable as exc:
        print(f"LEDGER: FAIL — {exc}. Refusing to report a batch it could "
              f"not read.")
        sys.exit(2)
    print(ledger.report(records, batch=args.batch, malformed=malformed,
                        leads=args.leads, verbose=args.verbose))


def cmd_metrics(args) -> None:
    """What the hook stage yielded, and what the leads that yielded nothing cost.

    `ledger report` covers what Python can see. Everything on the hook side
    happens inside an agent, so it was narrated into a batch brief and lost when
    the session ended — which is why every cost claim in the proposal had to be
    reconstructed from a hand-written journal entry.

    **A count this was not given prints `?`, never 0.** The wall's asymmetry and
    the ledger's, a third time: an unsupplied raw count must not read as "no
    leads came in". So the flags below are how a number gets in, and nothing
    here reaches back into a stage to guess one.

    **It never exits 1.** Reporting a bad number is the job. Exit 2 is for an
    input it could not read at all — a batch whose metrics could not be computed
    must not report as a batch with no findings.
    """
    from outbound import ledger, metrics

    rows = _load_json(args.input, "METRICS")
    if isinstance(rows, dict):
        rows = [rows]
    if not isinstance(rows, list) or any(not isinstance(r, dict) for r in rows):
        print("METRICS: FAIL — expected a research object or a list of them.")
        sys.exit(2)

    out = metrics.from_research(rows, batch=args.batch or "")

    # Supplied, never derived. Each of these belongs to a stage that already
    # printed it, and inventing one here would be the zero-fill this module
    # exists to refuse.
    for attr, value in (("raw", args.raw), ("after_dedupe", args.after_dedupe),
                        ("warm", args.warm), ("passed_floors", args.passed_floors),
                        ("written", args.written), ("rejected", args.rejected),
                        ("tier0_rate", args.tier0_rate),
                        ("source_list", args.source_list),
                        ("agent_passes", args.passes)):
        if value is not None:
            setattr(out, attr, value)

    if not args.no_ledger:
        try:
            records, _ = ledger.read(args.batch)
        except ledger.LedgerUnreadable as exc:
            print(f"METRICS: FAIL — {exc}. Refusing to report a batch's cost "
                  f"it could not read; pass --no-ledger to report the hook "
                  f"side alone.")
            sys.exit(2)
        verified = {(r.get("lead_key") or r.get("email") or "") for r in rows
                    if (r.get("hook_verified") or "").lower() == "verified"}
        metrics.add_ledger(out, records, verified_leads=verified)
        # The Claude bill. Same file, different authority — those records were
        # written by code at the moment of a fetch, these were typed by an
        # orchestrator, and the report says so on every line.
        metrics.add_passes(out, ledger.read_passes(args.batch))

    # The measured half of the same bill. Absent is `?`, never 0 — a batch whose
    # session ended before `usage` ran did not cost nothing, and the artifact is
    # the only part of a transcript that outlives its container.
    usage_path = Path(args.usage or ledger.artifact("-usage.json", batch=args.batch))
    if usage_path.is_file():
        try:
            metrics.add_usage(out, json.loads(usage_path.read_text(encoding="utf-8")))
        except ValueError:
            out.gaps.append(f"{usage_path} is not readable JSON — token counts "
                            f"are ?, and ? is not zero")
    else:
        out.gaps.append(f"no {usage_path.name} — run `usage --batch "
                        f"{args.batch or '<batch>'}` before this session ends, "
                        f"or the batch's largest cost dies with the container")

    # D21's reversal condition. The declines bind as of D27, so this is the
    # evidence the gate was held back for two batches waiting on.
    if args.plan:
        plans = _load_json(args.plan, "METRICS")
        if isinstance(plans, dict):
            plans = plans.get("plans") or []
        if not isinstance(plans, list):
            print("METRICS: FAIL — --plan wants `plan --out`'s file.")
            sys.exit(2)
        metrics.add_plan(out, plans, rows)

    print(metrics.report(out))
    print(metrics.batches_block(out))

    from outbound import ledger

    target = args.out or (ledger.artifact("-metrics.json", batch=args.batch)
                          if args.batch else "")
    if target:
        print(f"  wrote {metrics.write_artifact(out, target)}")
    sys.exit(0)


def cmd_collect(args) -> None:
    """Assemble a stage's state file from the per-lead files on disk.

    `work/researched.json`, `work/draftable.json` and `work/drafts.json` were
    written by no command — the orchestrator serialised each one out of its own
    context, which is the most expensive way to concatenate JSON and the reason
    no stage here could be resumed by anything that was not present when it ran.

    **Fails closed and prints coverage.** `crm-rows` is the precedent: twenty
    rows once went in with five empty columns on all of them, and the check that
    passed them reported 20/20 by looking only at fields that were populated.
    """
    from outbound import collect as co

    expect = []
    if args.expect:
        rows = _load_json(args.expect, "COLLECT")
        rows = rows if isinstance(rows, list) else [rows]
        expect = [str(r.get("slug") or "").strip() for r in rows
                  if isinstance(r, dict)]

    got = co.collect(args.where, args.stage, expect=expect)
    if args.stage == "drafts" and (args.leads or args.research):
        gaps = co.join_identity(
            got.members,
            leads=_load_json(args.leads, "COLLECT") if args.leads else None,
            research=_load_json(args.research, "COLLECT") if args.research else None)
        got.skipped.extend(gaps)
    print(co.report(got))
    if got.members:
        print(f"  wrote {co.write(got, args.out)}")
    sys.exit(1 if co.failed(got) else 0)


def cmd_verdict(args) -> None:
    """Validate what the cold read decided, before anything routes on it.

    The draft verdict had no artifact until now: `draft-verifier` returned SEND,
    REWRITE or REJECT as prose and had no `Write` tool, so the skill's own line
    was "the verdict lives in an agent, nothing in Python can reach it". A
    verdict only the orchestrator can read is a verdict only the orchestrator can
    route, which is why every one of them arrived on its own turn inside a
    600k-token context.

    The shape is `draft-verifier.md`'s own contract. The one change is that
    `beat` is an enum, because a wave's findings have to be counted by it and
    free text does not cluster.
    """
    from outbound import verdict as v

    data = _load_json(args.input, "VERDICT")
    items = v.load(data)
    if not items:
        print("VERDICT: FAIL — no verdicts to validate. An empty wave is a "
              "cold read that did not happen, not one where nothing was wrong.")
        sys.exit(2)
    print(v.report(items))
    sys.exit(1 if v.validate_all(items) else 0)


def cmd_redraft(args) -> None:
    """Route a wave of cold reads: who goes back, who holds, and what to say.

    Two things this replaces, both measured.

    **The cap.** `SKILL.md` has always said a REWRITE goes back to the drafter
    once and then the lead holds. Eight of nine leads exceeded it on
    `2026-08-02-q2` and eight on `2026-08-02-q3`; the repeats were 68% and 46%
    of those draft stages. It is a loop bound now.

    **The clustering.** Seventeen of seventeen drafts on q3 failed their first
    cold read on the same beat and were answered one at a time, because a reader
    going lead by lead cannot see the seventeenth until they have paid for
    sixteen. Counting makes the pattern visible on the first pass.

    **Never exits 1 on a routing decision** — a wave where everything holds is a
    real answer. Exit 1 is only its own output failing its own schema, the same
    rule as `plan` and `select`.
    """
    from outbound import redraft as rd, verdict as v

    if Path(args.input).is_dir():
        items = v.read_dir(args.input)
        source = f"{args.input} ({len(items)} verdict file(s))"
    else:
        items = v.load(_load_json(args.input, "REDRAFT"))
        source = args.input
    if not items:
        print(f"REDRAFT: FAIL — no verdicts in {source}. An empty wave is a "
              f"cold read that did not happen.")
        sys.exit(2)

    broken = [i for i in items if v.validate(i)]
    if broken:
        print(v.report(items))
        print(f"REDRAFT: FAIL — {len(broken)} verdict(s) do not validate. "
              f"Routing on a malformed verdict is how a lead gets redrafted "
              f"against no instruction.")
        sys.exit(2)

    out = rd.plan(items, max_rounds=args.max_rounds, cluster_min=args.cluster_min)
    print(rd.report(out, cluster_min=args.cluster_min))

    if args.out:
        Path(args.out).write_text(json.dumps(out.to_dict(), indent=2, default=str),
                                  encoding="utf-8")
        print(f"  wrote {args.out}")
    sys.exit(0)


def cmd_usage(args) -> None:
    """The Claude bill, measured from this session's transcript.

    `ledger pass` records that an agent ran and cannot record what it cost —
    neither an orchestrator nor a worker can see its own token usage. So the
    model side had a count and no magnitude, and `2026-08-02-q3` reported 185
    passes while 75% of the batch went to a thread that reports no passes at all.

    **Exit 2 when it cannot read a transcript**, naming where it looked. The
    layout belongs to the harness and can move; a zero here would read as "this
    batch used no agents", which is the wall's asymmetry again. **Never exit 1** —
    an accounting command that can halt a send file gets routed around.

    Transcripts live on the session's own container and die with it. Run this
    before the session ends, or the batch's largest cost is unrecoverable.
    """
    from outbound import ledger, usage

    try:
        sources = usage.discover(args.transcripts)
    except usage.TranscriptsUnreadable as exc:
        print(f"USAGE: FAIL — {exc}")
        sys.exit(2)

    turns = usage.read_turns(sources)
    if not turns:
        print(f"USAGE: FAIL — read {len(sources.main)} transcript(s) and "
              f"{len(sources.subagents)} subagent file(s) under {sources.root}, "
              f"and found no assistant record carrying `message.usage`. That is "
              f"a shape this does not recognise, not a batch that cost nothing.")
        sys.exit(2)

    out = usage.summarise(turns, batch=args.batch or "", sources=sources)
    print(usage.headline(out) if args.quiet else usage.report(out))

    target = args.out or (ledger.artifact("-usage.json", batch=args.batch)
                          if args.batch else "")
    if target:
        written = usage.write_artifact(out, target)
        print(f"  wrote {written}" if not args.quiet else f"  wrote {written.name}")
        if not args.quiet:
            print(f"  `metrics --written <n>` reads it for tokens_per_email, "
                  f"which is the control number for any change to the "
                  f"orchestration.")
    if args.json:
        print(json.dumps(out, indent=2, default=str))
    sys.exit(0)


def cmd_replies(args) -> None:
    """Join a Smartlead replies export to the batch, on email.

    The one gap no retrieval architecture closes. Smartlead owns replies and
    there is no API key here, so this is the manual bridge Part 8 describes:
    Haytham exports a CSV, this attributes each reply to the hook type and the
    rung that earned it. `Hook Type` has been a CRM select since the beginning,
    described in the base as a testable variable against reply rate. This is the
    first thing that can run the test.

    **Exit 2 when it cannot identify the columns**, naming the headers it saw.
    A zero reply rate from a column it failed to find would read as "the
    campaign did nothing" when the truth is "the question could not be asked".
    """
    from outbound import replies as rep

    text = _read_text(args.export, "REPLIES")
    leads = _load_json(args.leads, "REPLIES")
    if isinstance(leads, dict):
        leads = [leads]
    if not isinstance(leads, list) or any(not isinstance(r, dict) for r in leads):
        print("REPLIES: FAIL — --leads must be a research object or a list.")
        sys.exit(2)

    try:
        export = rep.load_export(text, email_column=args.email_column,
                                 replied_column=args.replied_column,
                                 all_replied=args.all_replied)
    except rep.RepliesUnreadable as exc:
        print(f"REPLIES: FAIL — {exc}")
        sys.exit(2)

    out = rep.join(leads, export, batch=args.batch or "")
    print(rep.report(out))

    from outbound import ledger

    target = args.out or (ledger.artifact("-replies.json", batch=args.batch)
                          if args.batch else "")
    if target:
        from outbound.metrics import write_artifact
        print(f"  wrote {write_artifact(out, target)}")
    sys.exit(0)


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
    from outbound import collect as collect_defaults
    from outbound import fetch as fetch_defaults
    from outbound import redraft as redraft_defaults
    from outbound import select as select_defaults

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

    p = sub.add_parser("ig-intake",
                       help="an Instagram profile dump -> Leads AND the "
                            "observations it already carries")
    p.add_argument("path", help="the Apify instagram-profile-scraper dataset (JSON)")
    p.add_argument("--source", help="label for where this list came from")
    p.add_argument("--out", help="write the Leads as JSON")
    p.add_argument("--observations",
                   help="write the posts and bios as observe.Observation records")
    p.add_argument("--fetched-at", default="",
                   help="when the dump was scraped, ISO (default: now)")
    p.set_defaults(func=cmd_ig_intake)

    p = sub.add_parser("icf-intake",
                       help="an ICF directory export (.xlsx) -> Leads AND the "
                            "ICP fields the coach filled in themselves")
    p.add_argument("path", help="the ICF Coach Finder export (.xlsx)")
    p.add_argument("--sheet", default=icf_intake_sheet(),
                   help="worksheet to read (default: Coaches)")
    p.add_argument("--source", default="", help="label for where this list came from")
    p.add_argument("--out", help="write the Leads as JSON")
    p.add_argument("--prefill", help="write the sourced ICP hints, keyed by lead_key")
    p.add_argument("--expect", type=int, default=0,
                   help="fail closed if this many leads do not arrive")
    p.set_defaults(func=cmd_icf_intake)

    p = sub.add_parser("chunk",
                       help="an enriched list -> the chunks a batch runs, cut "
                            "by evidence rather than by row number")
    p.add_argument("leads", help="Leads from `icf-intake --out` or `icf-export`")
    p.add_argument("--enriched", required=True,
                   help="the enriched CSV `icf-export --csv` wrote")
    p.add_argument("--out-dir", default="data/lists",
                   help="where the four files go (default: data/lists)")
    p.add_argument("--prefix", default="icf",
                   help="filename prefix (default: icf)")
    p.add_argument("--seed", type=int, default=20260803,
                   help="the halving seed. Same seed, same two halves")
    p.add_argument("--dry-run", action="store_true",
                   help="print the composition and write nothing")
    p.set_defaults(func=cmd_chunk)

    p = sub.add_parser("corpus",
                       help="attach a corpus somebody else retrieved to the "
                            "list you are actually running (D32)")
    p.add_argument("action", choices=["attach"])
    p.add_argument("observations",
                   help="observations from `ig-intake --observations`, or a "
                        "research file carrying them")
    p.add_argument("--leads", required=True,
                   help="the Leads this corpus should be re-keyed onto")
    p.add_argument("--out", help="write the re-keyed observations")
    p.add_argument("--expect", type=int,
                   help="the number of leads that SHOULD match. Exit 1 below it "
                        "— a corpus that joined 3 of 40 reads like one that "
                        "joined all 40 if only the total is printed")
    p.set_defaults(func=cmd_corpus)

    p = sub.add_parser("triage",
                       help="RUN / HOLD / DROP before anything is spent "
                            "(unclear is HOLD, never DROP)")
    p.add_argument("leads", help="Leads JSON from `intake --out` / `ig-intake --out`")
    p.add_argument("--observations", help="the corpus, for the activity floor")
    p.add_argument("--complete-corpus", action="store_true",
                   help="the observations are everything the channel has, not a "
                        "sample — the ONLY thing that lets a stale date drop a "
                        "lead. True of a profile scrape, false of a research pass")
    p.add_argument("--out", help="write every lead's tier and its verdicts")
    p.add_argument("--run-out", help="write just the RUN leads, as a Leads file")
    p.set_defaults(func=cmd_triage)

    p = sub.add_parser("dedupe", help="the Contacted-Before wall (exits 1 on a warm hit)")
    p.add_argument("leads", help="Leads JSON from `intake --out`")
    p.add_argument("--contacts", help="override the wall: a CSV, or a JSON array "
                                      "of CRM rows (default data/contacted-before.csv)")
    p.add_argument("--stage", choices=["early", "late"], default="early",
                   help="early = name/domain before any paid call; late = email after research")
    p.add_argument("--out", help="write the cleared Leads as JSON")
    p.set_defaults(func=cmd_dedupe)

    p = sub.add_parser("qualify", help="the three floors (unclear passes)")
    p.add_argument("input", help="JSON file, or '-' for stdin. Pass the lead's "
                                 "`observations` alongside its text and the "
                                 "activity floor settles from a real date")
    p.set_defaults(func=cmd_qualify)

    p = sub.add_parser("research", help="validate a worker's research object")
    p.add_argument("input", help="JSON file, or '-' for stdin")
    p.add_argument("--verbose", action="store_true",
                   help="the full block for every lead, not just the ones with "
                        "a problem or a blocker. One lead is always full")
    p.set_defaults(func=cmd_research)

    p = sub.add_parser("observe", help="validate what a worker actually fetched")
    p.add_argument("input", help="JSON file (one observation or a list), or '-' for stdin")
    p.set_defaults(func=cmd_observe)

    p = sub.add_parser("hook",
                       help="check a proposed hook BEFORE a verifier certifies it")
    p.add_argument("input", help="JSON file (one proposal or a list), or '-' for stdin")
    p.add_argument("--against", help="select --out's file. Checks the quote is "
                                     "really a contiguous piece of the "
                                     "observation it names — ban #3, which was "
                                     "unenforceable until there was something "
                                     "to check it against. A batch run passes "
                                     "it; the single-lead repair path need not")
    p.set_defaults(func=cmd_hook)

    p = sub.add_parser("crm-rows",
                       help="build the Airtable Leads rows, joined and failing closed")
    p.add_argument("leads", help="normalized Leads from `dedupe --out` (work/clear.json)")
    p.add_argument("--research", required=True,
                   help="the research objects (work/researched.json) — the "
                        "verdicts. They do NOT carry the identity fields, which "
                        "is the join this command exists to make explicit")
    p.add_argument("--drafts", help="what actually shipped, for Subject/Body/Hook")
    p.add_argument("--batch", default="", help="the batch label, for the row")
    p.add_argument("--out", help="write the rows as JSON (out/crm-leads.json)")
    p.set_defaults(func=cmd_crm_rows)

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
    p.add_argument("--escalate-only", dest="escalate_only", action="store_true",
                   help="run the escalation from a saved sites.json and read "
                        "NOTHING at tier 0. The retry path: `--escalate` after "
                        "a failed escalation re-reads every site first, which "
                        "put 52 duplicate pairs in one batch's ledger and "
                        "buried the one duplicate it existed to expose. With "
                        "this, the positional argument is the sites.json")
    p.add_argument("--approve-cost", action="store_true",
                   help="approve the escalation's cost (see exit 3)")
    p.set_defaults(func=cmd_fetch)

    p = sub.add_parser("resolve",
                       help="which channels are plausibly this lead's own")
    p.add_argument("leads", help="Leads JSON from `intake --out`")
    p.add_argument("--sites", help="sites.json from `fetch --out`, so a site "
                                   "that names the lead can vouch for the "
                                   "channels it links")
    p.add_argument("--out", help="write the identities as JSON")
    p.add_argument("--no-fetch", action="store_true",
                   help="skip the link-in-bio pages — every verdict then comes "
                        "from the row and the site read alone")
    p.add_argument("--workers", type=int, default=fetch_defaults.DEFAULT_WORKERS,
                   help="concurrent link-in-bio reads")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_resolve)

    p = sub.add_parser("plan",
                       help="which rungs a lead has, and what each would cost")
    p.add_argument("identities", help="identity JSON from `resolve --out`")
    p.add_argument("--leads", help="Leads JSON from `intake --out`, which is "
                                   "the only place the lead's own site URL is")
    p.add_argument("--price", action="store_true",
                   help="look up live Apify prices (needs a token and the "
                        "network; without it a paid step reports 'not priced')")
    p.add_argument("--budget", action="store_true",
                   help="read the monthly Apify cap once and print what is left")
    p.add_argument("--addresses",
                   help="verdicts from `email-find --out`: a lead nothing can be "
                        "sent to loses its PAID rungs and keeps every free one")
    p.add_argument("--out", help="write the plans as JSON")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_plan)

    p = sub.add_parser("select",
                       help="which observation a hook would be made from")
    p.add_argument("input", help="research JSON (one object or a list), or '-'")
    p.add_argument("--against", action="store_true",
                   help="compare the shortlist to the hooks the hook stage "
                        "actually verified — the measurement P3 is gated on")
    p.add_argument("--shortlist", type=int, default=select_defaults.SHORTLIST,
                   help="how many candidates to offer per lead")
    p.add_argument("--hook-room", type=int, default=0,
                   help="words the drafter will have — the low end of the range "
                        "`deal` prints. Advisory; 0 means not given")
    p.add_argument("--out", help="write the selections as JSON")
    p.add_argument("--batch", default="",
                   help="write data/runs/<batch>-select.json AND "
                        "-research.json, so a later change to the bans can be "
                        "re-scored against this batch without paying for it "
                        "again. Commit both")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_select)

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
    p.add_argument("addresses", nargs="*")
    p.add_argument("--leads", default="",
                   help="take the addresses off a Leads JSON as well — a whole "
                        "list does not fit on a command line")
    p.add_argument("--out", default="",
                   help="write the verdicts, keyed by address")
    p.add_argument("--approve-cost", action="store_true")
    p.set_defaults(func=cmd_email_verify_batch)

    p = sub.add_parser("email-enrich", help="no-address fallback on the lead's own domain")
    p.add_argument("name")
    p.add_argument("domain", help="domain or site URL")
    p.add_argument("--approve-cost", action="store_true")
    p.set_defaults(func=cmd_email_enrich)

    p = sub.add_parser("icf-export",
                       help="join the enrichment back onto the source workbook")
    p.add_argument("--workbook", required=True, help="the original .xlsx")
    p.add_argument("--leads", required=True, help="Leads from `icf-intake --out`")
    p.add_argument("--prefill", default="", help="from `icf-intake --prefill`")
    p.add_argument("--channels", default="", help="from `channel-find --out`")
    p.add_argument("--addresses", default="",
                   help="from `email-verify-batch --out`")
    p.add_argument("--contacted", default="",
                   help="JSON array of lead_keys or names already on the wall")
    p.add_argument("--out-xlsx", default="", help="the enriched workbook")
    p.add_argument("--out-csv", default="", help="the committed CSV")
    p.add_argument("--out-leads", default="",
                   help="Leads with the found channels merged in")
    p.add_argument("--expect", type=int, default=0,
                   help="fail closed if this many rows do not join")
    p.add_argument("--at", default="", help="the enrichment date (default today)")
    p.add_argument("--batch", default="", help="batch label")
    p.set_defaults(func=cmd_icf_export)

    p = sub.add_parser("channel-find",
                       help="the LinkedIn / Instagram / website a list arrives "
                            "without, in batched search runs")
    p.add_argument("--leads", required=True,
                   help="the CLEAR list from `dedupe --stage early`")
    p.add_argument("--shape", choices=["one", "two"], default="one",
                   help="one plain query per lead, or that plus a LinkedIn-"
                        "scoped one (default: one)")
    p.add_argument("--chunk", type=int, default=0,
                   help="stop after this many leads, for resume and blast radius")
    p.add_argument("--limit", type=int, default=0, help="cap the leads searched")
    p.add_argument("--keys", default="",
                   help="JSON array of lead_keys to search, for a chosen slice")
    p.add_argument("--state", default="",
                   help="resume file (default data/runs/<batch>-channels.json)")
    p.add_argument("--refresh", action="store_true",
                   help="re-query leads that already have a verdict")
    p.add_argument("--country", default="ae", help="SERP country code")
    p.add_argument("--pages", type=int, default=1, help="pages per query")
    p.add_argument("--show", type=int, default=12,
                   help="queries to print in the plan")
    p.add_argument("--execute", action="store_true",
                   help="actually run it. Without this the plan prints and "
                        "nothing is spent")
    p.add_argument("--approve-cost", action="store_true",
                   help="approve a run above the cost threshold")
    p.add_argument("--out", default="", help="write the merged verdicts")
    p.add_argument("--batch", default="", help="batch label (ledger)")
    p.set_defaults(func=cmd_channel_find)

    p = sub.add_parser("email-find",
                       help="an address somebody else published, one batched search run")
    p.add_argument("name", nargs="?", default="",
                   help="one lead's full name; omit when using --leads")
    p.add_argument("--leads", help="Leads or research JSON — every named row, one run")
    p.add_argument("--headline", default="", help="their positioning line, single-lead form")
    p.add_argument("--location", default="", help="city or country, single-lead form")
    p.add_argument("--domain", action="append",
                   help="a domain already known to be theirs; repeatable")
    p.add_argument("--country", default="ae",
                   help="Google country code (default ae — the free WebSearch is US-only)")
    p.add_argument("--pages", type=int, default=1, help="SERP pages per query")
    p.add_argument("--ai-overview", action="store_true",
                   help="add the AI Overview: +$0.002/query (nearly doubles the rung) "
                        "for an ABSENT verdict measured wrong on 2 of 5 leads")
    p.add_argument("--out", help="write the per-lead address verdicts for `plan --addresses`")
    p.add_argument("--observations",
                   help="a corpus from `ig-intake --observations`. Addresses the "
                        "lead published on their own channel are harvested free "
                        "FIRST, and those leads are not searched at all")
    p.add_argument("--approve-cost", action="store_true")
    p.set_defaults(func=cmd_email_find)

    p_ledger = sub.add_parser("ledger",
                              help="what each retrieval cost and how long it took")
    ledger_sub = p_ledger.add_subparsers(dest="ledger_command", required=True)

    a = ledger_sub.add_parser(
        "batch", help="name this batch, or ask which one you are in")
    a.add_argument("label", nargs="?", default="",
                   help="the batch label. Omitted, it prints the label that "
                        "resolves now and where it came from")

    a = ledger_sub.add_parser(
        "pass", help="record agent passes — the model cost Python cannot see")
    a.add_argument("--stage", required=True,
                   help="research | hook | verify | draft | cold-read | "
                        "orchestrator — which part of the run spent it")
    a.add_argument("--agent", default="",
                   help="the agent that ran, e.g. draft-worker")
    a.add_argument("--model", default="",
                   help="the tier it ran at, e.g. opus or sonnet. Counts, not "
                        "dollars: model prices are a value this repo does not "
                        "own and would go stale in it")
    a.add_argument("--count", type=int, default=1,
                   help="how many passes, for a fan-out reported in one line")
    a.add_argument("--batch", help="batch label (default: `ledger batch` resolves it)")

    a = ledger_sub.add_parser("add", help="record a retrieval Python did not make")
    a.add_argument("--lead", default="", help="the lead this was fetched for")
    a.add_argument("--platform", default="web",
                   help="site | linkedin | instagram | youtube | podcast | web | email")
    a.add_argument("--url", default="", help="the page actually fetched")
    a.add_argument("--by", default="websearch",
                   help="websearch | webfetch — the rungs that happen model-side")
    a.add_argument("--stage", default="research", help="fetch | research | hook | verify")
    a.add_argument("--purpose", default="observe", choices=["observe", "verify"],
                   help="a second fetch of the same page is only allowed to verify")
    a.add_argument("--secs", type=float, default=0.0)
    a.add_argument("--cost", type=float, default=0.0)
    a.add_argument("--outcome", default="ok", choices=["ok", "empty", "error", "blocked"])
    a.add_argument("--batch", help="batch label (default OUTBOUND_BATCH, then today)")

    a = ledger_sub.add_parser("report", help="a batch's retrievals, cost and duplicates")
    a.add_argument("--batch", help="batch label (default OUTBOUND_BATCH, then today)")
    a.add_argument("--leads", type=int, default=0,
                   help="the batch's real lead count, so cost/lead is not "
                        "computed over only the leads that needed a fetch")
    a.add_argument("--verbose", action="store_true",
                   help="every duplicate pair, not the shapes they fall into. "
                        "129 pairs in one batch were three shapes, and the "
                        "shape is what the fix reads")

    p_ledger.set_defaults(func=cmd_ledger)

    p = sub.add_parser("metrics",
                       help="what the hook stage yielded, and what the leads "
                            "that yielded nothing cost")
    p.add_argument("input", help="the batch's research/draft objects, or '-'")
    p.add_argument("--batch", help="batch label (default OUTBOUND_BATCH, then today)")
    p.add_argument("--no-ledger", action="store_true",
                   help="report the hook side alone, without reading a ledger")
    p.add_argument("--out", help="where to write the JSON artifact "
                                 "(default data/runs/<batch>-metrics.json)")
    # Supplied, never derived. Anything not passed prints `?` rather than 0 —
    # an unsupplied count is not a measurement of zero.
    p.add_argument("--raw", type=int, help="rows in the source list (intake)")
    p.add_argument("--after-dedupe", type=int, help="rows the early dedupe cleared")
    p.add_argument("--warm", type=int, help="warm-thread hits")
    p.add_argument("--passed-floors", type=int, help="leads through the three floors")
    p.add_argument("--written", type=int, help="rows in leads.csv (export)")
    p.add_argument("--rejected", type=int, help="rows in rejected.txt (export)")
    p.add_argument("--tier0-rate", type=float, help="tier 0 rate as a fraction, e.g. 0.59")
    p.add_argument("--source-list", help="what the raw list was called")
    p.add_argument("--passes", type=int,
                   help="agent passes for the batch. REPORTED on trust — Python "
                        "cannot see them, the same blind spot as `ledger add`")
    p.add_argument("--plan", help="plan --out's file. Reports, of the leads "
                                  "carrying a declined rung, how many produced "
                                  "a verified hook — D21's reversal condition, "
                                  "and the evidence the decline gate binds on")
    p.add_argument("--usage", help="usage --out's file (default "
                                   "data/runs/<batch>-usage.json). The MEASURED "
                                   "token bill, against the REPORTED pass counts")
    p.set_defaults(func=cmd_metrics)

    p = sub.add_parser("collect",
                       help="assemble a stage's state file from the per-lead "
                            "files, instead of out of the orchestrator's context")
    p.add_argument("stage", choices=sorted(collect_defaults.STAGES),
                   help="which state file to build")
    p.add_argument("--where", default="work",
                   help="the directory holding the per-lead files (default work/)")
    p.add_argument("--out", help="override the output path")
    p.add_argument("--expect", help="a JSON list carrying the slugs this stage "
                                    "should produce. 'found six' and 'found six "
                                    "of seventeen' are the whole check")
    p.add_argument("--leads", help="drafts only: the Leads file, to join each "
                                   "draft to its lead's own facts")
    p.add_argument("--research", help="drafts only: the research file, which is "
                                      "the authority on the address")
    p.set_defaults(func=cmd_collect)

    p = sub.add_parser("verdict",
                       help="validate a cold read before anything routes on it")
    p.add_argument("input", help="JSON file (one verdict, a list, or a "
                                 "{slug: verdict} map), or '-' for stdin")
    p.set_defaults(func=cmd_verdict)

    p = sub.add_parser("redraft",
                       help="route a wave of cold reads: who goes back, who "
                            "holds, and the one note that covers a shared beat")
    p.add_argument("input", help="a directory of verdict-<slug>.json, or one "
                                 "JSON file holding them")
    p.add_argument("--out", help="write the routing plan as JSON")
    p.add_argument("--max-rounds", type=int, default=redraft_defaults.MAX_ROUNDS,
                   help="rounds a lead may have before it holds. SKILL.md has "
                        "always said one repair; as a sentence it lost on both "
                        "measured batches")
    p.add_argument("--cluster-min", type=int, default=redraft_defaults.CLUSTER_MIN,
                   help="how many leads must share a beat before it is one "
                        "stage problem rather than N lead problems")
    p.set_defaults(func=cmd_redraft)

    p = sub.add_parser("usage",
                       help="what the batch cost in Claude tokens, measured "
                            "from the session transcript")
    p.add_argument("--batch", help="batch label (default OUTBOUND_BATCH, then today)")
    p.add_argument("--transcripts",
                   help="the session's project directory, when it is not where "
                        "this expects it (~/.claude/projects/<slug>)")
    p.add_argument("--out", help="where to write the JSON artifact "
                                 "(default data/runs/<batch>-usage.json)")
    p.add_argument("--quiet", action="store_true",
                   help="one line instead of the block. For the stage-boundary "
                        "checkpoint, where the artifact is the point and the "
                        "reading is not")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_usage)

    p = sub.add_parser("replies",
                       help="join a Smartlead replies export to the batch, "
                            "on email — reply rate by hook type and rung")
    p.add_argument("export", help="the Smartlead CSV, or '-' for stdin")
    p.add_argument("--leads", required=True,
                   help="the batch's research/draft objects, carrying hook_type")
    p.add_argument("--batch", help="batch label, for the artifact name")
    p.add_argument("--email-column", default="",
                   help="name the address column instead of sniffing it")
    p.add_argument("--replied-column", default="",
                   help="name the reply column instead of sniffing it")
    p.add_argument("--all-replied", action="store_true",
                   help="the export is already filtered to people who replied, "
                        "so it carries no reply column. Never inferred: a "
                        "pre-filtered file and an unrecognised column look the "
                        "same and differ by the whole answer")
    p.add_argument("--out", help="where to write the JSON artifact "
                                 "(default data/runs/<batch>-replies.json)")
    p.set_defaults(func=cmd_replies)

    p_apify = sub.add_parser("apify", help="no-login LinkedIn / Instagram / YouTube / SERP fetch")
    apify_sub = p_apify.add_subparsers(dest="apify_command", required=True)

    def paid(parser_) -> None:
        """The run facts a paid call carries into the ledger.

        Optional everywhere, because a ledger line with no lead on it is still
        worth more than no line, and a retrieval that refuses to happen without
        one is a gate this stage was explicitly not supposed to grow.
        """
        parser_.add_argument("--lead", default="",
                             help="the lead this retrieval is for (ledger)")
        # The payload goes to a file and a summary goes to stdout, like every
        # other bulk stage here. This was the one command that printed its whole
        # dataset into the caller's context.
        parser_.add_argument("--out", default="",
                             help="where to write the payload (default "
                                  "data/runs/<batch>-apify-<cmd>-<lead>.json)")
        parser_.add_argument("--print", dest="print_payload", action="store_true",
                             help="print the payload instead of writing it. For "
                                  "debugging by hand: in an agent this is the "
                                  "300 KB that made a batch expensive")
        parser_.add_argument("--stage", default="research",
                             help="fetch | research | hook | verify (ledger)")
        parser_.add_argument("--purpose", default="observe",
                             choices=["observe", "verify"],
                             help="a second fetch of the same page is only "
                                  "allowed to verify (ledger)")
        # Twelve workers were told to pass this and it did not exist. One
        # checked, used OUTBOUND_BATCH instead and said so; the other eleven
        # did as they were told, and 15 retrievals landed in the wrong file.
        # `ledger batch` is the answer to not having to pass it at all.
        parser_.add_argument("--batch", default="",
                             help="which batch to bill this to (ledger). "
                                  "Default: `ledger batch` resolves it")

    apify_sub.add_parser("limits", help="usage vs plan — check ONCE per batch")

    a = apify_sub.add_parser("actors", help="search the public Apify Store")
    a.add_argument("query")
    a.add_argument("--limit", type=int, default=6)

    a = apify_sub.add_parser("ig", help="Instagram posts or profile details")
    # Several profiles is one run for `--mode details`, whose input field is an
    # array. `--mode posts` refuses more than one, on purpose: see `instagram`.
    a.add_argument("url", nargs="+")
    a.add_argument("--mode", default="posts", choices=["posts", "details"])
    a.add_argument("--newer-than", dest="newer_than")
    a.add_argument("--limit", type=int, default=12)
    a.add_argument("--skip-pinned", dest="skip_pinned", action="store_true")
    a.add_argument("--include-about", dest="include_about", action="store_true")
    a.add_argument("--raw", action="store_true")
    a.add_argument("--approve-cost", action="store_true")
    paid(a)

    a = apify_sub.add_parser("ig-post", help="one Instagram post in full")
    a.add_argument("url")
    a.add_argument("--raw", action="store_true")
    a.add_argument("--approve-cost", action="store_true")
    paid(a)

    a = apify_sub.add_parser("li-posts", help="recent LinkedIn posts — primary hook source")
    a.add_argument("url")
    a.add_argument("--max", type=int, default=5)
    a.add_argument("--since", choices=["any", "1h", "24h", "week", "month",
                                       "3months", "6months", "year"])
    a.add_argument("--raw", action="store_true")
    a.add_argument("--approve-cost", action="store_true")
    paid(a)

    a = apify_sub.add_parser("li-profile", help="LinkedIn headline / about / experience")
    a.add_argument("urls", nargs="+",
                   help="one URL, or several to batch into one actor run")
    a.add_argument("--email", action="store_true", help="use the pricier email-search mode")
    a.add_argument("--raw", action="store_true")
    a.add_argument("--approve-cost", action="store_true")
    paid(a)

    a = apify_sub.add_parser("verify-email", help="verify addresses in one batched call")
    a.add_argument("addresses", nargs="+")
    a.add_argument("--raw", action="store_true")
    a.add_argument("--approve-cost", action="store_true")
    paid(a)

    # `youtube`, `search` and `footprint` were retired 2026-08-01 with the two
    # actors behind them. Sourcing keeps `classify-footprint` below, which never
    # fetched anything itself and is now fed by the agent's own WebSearch —
    # which `audit/footprint.py` already called the preferred path.
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
