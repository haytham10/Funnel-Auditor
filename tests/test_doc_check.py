"""The gate that keeps the defining docs true.

Run: python -m pytest tests/test_doc_check.py -q
 or: python tests/test_doc_check.py

Two halves, and the second matters more.

The red-team half builds a synthetic repo in a temp directory and violates
exactly one rule at a time, asserting the right kind, the right line, and that
nothing else fired. A doc checker that flags everything gets switched off in a
week, so the non-findings are pinned as hard as the findings.

The invariant half runs against the real repo. `test_the_repo_itself_passes` is
what turns doc-check from a command someone remembers into a gate that runs on
every test run, and `test_the_journal_is_skipped_on_purpose` makes sure the one
deliberate blind spot can never become an accident.
"""

import argparse
import re
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from outbound import doc_check

ROOT = Path(__file__).resolve().parent.parent

HEADER = ("**Owns:** the thing this file decides.\n"
          "**Defers to:** none.\n"
          "**Allows:** none.\n")


def fake_parser():
    """A stand-in for build_parser(), so these tests do not import main.py."""
    parser = argparse.ArgumentParser(prog="main.py")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("lint", "export", "deal", "dedupe", "doc-check"):
        sub.add_parser(name)
    apify = sub.add_parser("apify")
    apify_sub = apify.add_subparsers(dest="apify_command", required=True)
    for name in ("limits", "li-posts", "ig"):
        apify_sub.add_parser(name)
    return parser


def build(tmp, spec: dict, extra: dict | None = None) -> Path:
    """A minimal repo: copy CSVs, a main.py docstring, and the spec docs given.

    05-pipeline.md is written to mention every command in `fake_parser`, so the
    UNDOCUMENTED COMMAND check is satisfied by default and a test only sees the
    rule it is actually exercising.
    """
    root = Path(tmp)
    (root / "copy").mkdir(parents=True, exist_ok=True)
    for name, prefix in (("identity", "id-any"), ("offer", "b4"),
                         ("cta", "cta"), ("ps", "ps")):
        (root / "copy" / f"{name}.csv").write_text(
            f"id,line\n{prefix}-01,a line\n{prefix}-02,another line\n",
            encoding="utf-8")
    (root / "main.py").write_text(
        '"""A CLI.\n\n    lint\n    export\n    deal\n    dedupe\n'
        '    apify\n    doc-check\n"""\n', encoding="utf-8")
    (root / "CLAUDE.md").write_text(
        "Leads `tbl51dU7ojrxCVfxZ`\n", encoding="utf-8")

    specs = dict(spec)
    specs.setdefault("05-pipeline.md", HEADER + (
        "\n`lint` `export` `deal` `dedupe` `apify` `doc-check`\n"
        "`apify limits`, `apify li-posts` and `apify ig`\n"))
    (root / "docs" / "spec").mkdir(parents=True, exist_ok=True)
    for name, body in specs.items():
        (root / "docs" / "spec" / name).write_text(body, encoding="utf-8")
    for rel, body in (extra or {}).items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
    return root


# The whole suite runs the doc checks offline. The CRM schema check is the one
# that leaves the machine, and a suite that reaches the network starts failing
# on somebody's Airtable edit, which is not a code regression — the same reason
# conftest.py pins OUTBOUND_COPY_SOURCE=csv. Its logic is tested below against
# a stub schema, which is stricter than a live call anyway: a stub can be wrong
# on purpose.
OFFLINE = False


def check(tmp, spec: dict, extra: dict | None = None):
    return doc_check.check_docs(build(tmp, spec, extra), parser=fake_parser(),
                                airtable=OFFLINE)


def kinds(result) -> list:
    return sorted(f.kind for f in result.findings)


# ------------------------------------------------------------------ commands


def test_a_command_that_is_not_in_the_parser_is_caught():
    with tempfile.TemporaryDirectory() as tmp:
        result = check(tmp, {"01-a.md": HEADER + "\nRun `python main.py walk`.\n"})
        assert kinds(result) == ["UNKNOWN COMMAND"], result.report()
        assert result.findings[0].line == 5, result.findings[0]


def test_an_argument_is_not_read_as_a_subcommand():
    """`main.py deal work/leads.json` — only apify has nested subparsers."""
    with tempfile.TemporaryDirectory() as tmp:
        result = check(tmp, {"01-a.md": HEADER
                             + "\n`python main.py deal work/leads.json`\n"})
        assert result.ok, result.report()


def test_an_option_is_not_read_as_a_subcommand():
    with tempfile.TemporaryDirectory() as tmp:
        result = check(tmp, {"01-a.md": HEADER + "\n`python main.py export --anchors`\n"})
        assert result.ok, result.report()


def test_alternatives_separated_by_pipes_are_each_checked():
    """CLAUDE.md really writes `python main.py email-check|email-verify`."""
    with tempfile.TemporaryDirectory() as tmp:
        good = check(tmp, {"01-a.md": HEADER + "\n`python main.py lint|export`\n"})
        assert good.ok, good.report()
        bad = check(tmp, {"01-a.md": HEADER + "\n`python main.py lint|exprot`\n"})
        assert kinds(bad) == ["UNKNOWN COMMAND"], bad.report()


def test_a_bad_apify_subcommand_is_caught_and_a_good_one_is_not():
    with tempfile.TemporaryDirectory() as tmp:
        good = check(tmp, {"01-a.md": HEADER + "\n`python main.py apify li-posts`\n"})
        assert good.ok, good.report()
        bad = check(tmp, {"01-a.md": HEADER + "\n`python main.py apify li-post`\n"})
        assert kinds(bad) == ["UNKNOWN COMMAND"], bad.report()


def test_prose_mentioning_main_py_is_not_a_command():
    with tempfile.TemporaryDirectory() as tmp:
        result = check(tmp, {"01-a.md": HEADER
                             + "\nSee main.py for the parser itself.\n"})
        assert result.ok, result.report()


def test_commands_are_read_from_fenced_blocks():
    """Every command in the skills lives in a fence, so fences must be read."""
    with tempfile.TemporaryDirectory() as tmp:
        result = check(tmp, {"01-a.md": HEADER
                             + "\n```\npython main.py walk\n```\n"})
        assert kinds(result) == ["UNKNOWN COMMAND"], result.report()


def test_a_column_aligned_file_listing_is_not_an_invocation():
    """README.md's layout block, which reads as `main.py the` otherwise.

    The fix is the single space before the subcommand, NOT requiring a `python`
    prefix — docs really do write bare `main.py lint`, and those must stay
    checked.
    """
    with tempfile.TemporaryDirectory() as tmp:
        result = check(tmp, {"01-a.md": HEADER
                             + "\n```\nmain.py            the CLI, one line each\n```\n"})
        assert result.ok, result.report()


def test_a_bare_invocation_is_still_checked():
    with tempfile.TemporaryDirectory() as tmp:
        good = check(tmp, {"01-a.md": HEADER + "\nRun `main.py lint` first.\n"})
        assert good.ok, good.report()
        bad = check(tmp, {"01-a.md": HEADER + "\nRun `main.py walk` first.\n"})
        assert kinds(bad) == ["UNKNOWN COMMAND"], bad.report()


# --------------------------------------------------------------------- paths


def test_a_path_that_is_not_on_disk_is_caught():
    with tempfile.TemporaryDirectory() as tmp:
        result = check(tmp, {"01-a.md": HEADER + "\nSee `outbound/nope.py`.\n"})
        assert kinds(result) == ["DEAD PATH"], result.report()


def test_a_real_path_is_not_flagged():
    with tempfile.TemporaryDirectory() as tmp:
        result = check(tmp, {"01-a.md": HEADER + "\nSee `copy/identity.csv`.\n"})
        assert result.ok, result.report()


def test_resolution_walks_up_to_the_repo_root():
    """The `references/voice.md` case, which both simpler rules get wrong.

    A skill reference file cites a sibling relative to the SKILL root, not to
    its own directory and not to the repo root. Without the ancestor walk this
    check cannot ship green on the real repo.
    """
    with tempfile.TemporaryDirectory() as tmp:
        result = check(tmp, {}, extra={
            ".claude/skills/s/references/voice.md": "See `references/craft.md`.\n",
            ".claude/skills/s/references/craft.md": "craft\n",
        })
        assert result.ok, result.report()


def test_a_leading_dot_directory_survives():
    """`strip('.')` turns `.claude/skills/` into `claude/skills/` and flags a
    directory that is really there. rstrip only."""
    with tempfile.TemporaryDirectory() as tmp:
        result = check(tmp, {"01-a.md": HEADER + "\nSkills live in `.claude/skills/`.\n"},
                       extra={".claude/skills/s/SKILL.md": "x\n"})
        assert result.ok, result.report()


def test_runtime_paths_are_never_flagged():
    """out/ and work/ are gitignored, so they are absent from a fresh clone."""
    with tempfile.TemporaryDirectory() as tmp:
        result = check(tmp, {"01-a.md": HEADER
                             + "\nRead `out/preview.txt`, then `work/leads.json`, "
                               "then `copy/_airtable.json`.\n"})
        assert result.ok, result.report()


def test_an_actor_id_is_not_a_path():
    """`harvestapi/linkedin-profile-scraper` reads as a path and is not one."""
    with tempfile.TemporaryDirectory() as tmp:
        result = check(tmp, {"01-a.md": HEADER
                             + "\nThe actor is `harvestapi/linkedin-profile-scraper`.\n"})
        assert result.ok, result.report()


def test_globs_and_placeholders_are_not_paths():
    with tempfile.TemporaryDirectory() as tmp:
        result = check(tmp, {"01-a.md": HEADER
                             + "\n`copy/*.csv` and `docs/spec/<name>.md`\n"})
        assert result.ok, result.report()


def test_paths_are_not_read_from_fenced_blocks():
    """Fences hold worked examples and scratch paths that were never real."""
    with tempfile.TemporaryDirectory() as tmp:
        result = check(tmp, {"01-a.md": HEADER
                             + "\n```markdown\n**Defers to:** `some/authority.csv`\n```\n"})
        assert result.ok, result.report()


def test_a_sibling_spec_reference_resolves_against_the_spec_dir():
    with tempfile.TemporaryDirectory() as tmp:
        good = check(tmp, {"01-a.md": HEADER + "\nSee `05-pipeline.md`.\n"})
        assert good.ok, good.report()
        bad = check(tmp, {"01-a.md": HEADER + "\nSee `09-ghost.md`.\n"})
        assert kinds(bad) == ["DEAD PATH"], bad.report()


def test_a_markdown_link_target_is_checked():
    with tempfile.TemporaryDirectory() as tmp:
        result = check(tmp, {"01-a.md": HEADER + "\n[gone](09-ghost.md)\n"})
        assert kinds(result) == ["DEAD PATH"], result.report()


# -------------------------------------------------------------------- prices


def test_a_price_outside_the_owner_is_caught():
    with tempfile.TemporaryDirectory() as tmp:
        result = check(tmp, {"01-a.md": HEADER + "\nIt costs AED 2,000.\n"})
        assert kinds(result) == ["STATE IN SPEC"], result.report()


def test_the_owner_may_carry_prices():
    with tempfile.TemporaryDirectory() as tmp:
        result = check(tmp, {"03-offer.md": HEADER + "\nIt costs AED 2,000, or $1,500.\n"})
        assert result.ok, result.report()


def test_a_field_name_containing_price_is_not_a_price():
    with tempfile.TemporaryDirectory() as tmp:
        result = check(tmp, {"01-a.md": HEADER
                             + "\n`top_program_price_aed` and the price conversation.\n"})
        assert result.ok, result.report()


def test_an_allow_suppresses_exactly_its_token():
    with tempfile.TemporaryDirectory() as tmp:
        body = ("**Owns:** a thing.\n**Defers to:** none.\n"
                "**Allows:** `AED 5,000` — the retired floor.\n"
                "\nThe old floor was AED 5,000.\n")
        assert check(tmp, {"01-a.md": body}).ok
        louder = body.replace("The old floor was AED 5,000.",
                              "The old floor was AED 5,000 and the new one AED 9,000.")
        result = check(tmp, {"01-a.md": louder})
        assert kinds(result) == ["STATE IN SPEC"], result.report()
        assert "AED 9,000" in result.findings[0].detail


def test_an_allow_that_matches_nothing_is_stale():
    """The property that keeps the escape hatch from becoming a second spec."""
    with tempfile.TemporaryDirectory() as tmp:
        result = check(tmp, {"01-a.md": "**Owns:** a thing.\n**Defers to:** none.\n"
                                        "**Allows:** `AED 4,000` — a reason.\n\nBody.\n"})
        assert kinds(result) == ["STALE ALLOW"], result.report()


def test_the_header_declaring_an_allow_does_not_trip_the_price_check():
    """The header is metadata about the contract, not spec prose."""
    with tempfile.TemporaryDirectory() as tmp:
        result = check(tmp, {"01-a.md": "**Owns:** a thing.\n**Defers to:** none.\n"
                                        "**Allows:** `AED 5,000` — why.\n"
                                        "\nAED 5,000 was the floor.\n"})
        assert result.ok, result.report()


# -------------------------------------------------------------------- copy ids


def test_an_unknown_copy_id_is_caught():
    with tempfile.TemporaryDirectory() as tmp:
        result = check(tmp, {"01-a.md": HEADER + "\nThe line `ps-09` ships most.\n"})
        assert kinds(result) == ["UNKNOWN COPY ID"], result.report()


def test_a_real_copy_id_is_not_flagged():
    with tempfile.TemporaryDirectory() as tmp:
        result = check(tmp, {"01-a.md": HEADER + "\nThe line `ps-01` ships most.\n"})
        assert result.ok, result.report()


def test_an_unknown_family_is_not_treated_as_a_copy_id():
    """Deliberate false negative: flagging unknown families would flag
    `utf-8`, `sha-256` and `gpt-4`. The common typo is a wrong digit."""
    with tempfile.TemporaryDirectory() as tmp:
        result = check(tmp, {"01-a.md": HEADER + "\nEncoded as `utf-8`, via `gpt-4`.\n"})
        assert result.ok, result.report()


def test_a_copy_csv_with_no_id_column_cannot_run():
    """An empty authority must never read as "nothing is valid" — the same
    failure the dedupe wall's emptiness check exists to prevent."""
    with tempfile.TemporaryDirectory() as tmp:
        root = build(tmp, {"01-a.md": HEADER + "\nbody\n"})
        (root / "copy" / "ps.csv").write_text("line\nno id column\n", encoding="utf-8")
        try:
            doc_check.check_docs(root, parser=fake_parser(), airtable=OFFLINE)
        except doc_check.DocCheckError as exc:
            assert "ps.csv" in str(exc)
        else:
            raise AssertionError("a headerless copy CSV must not report zero ids")


# --------------------------------------------------------- header / authority


def test_a_missing_header_is_caught():
    with tempfile.TemporaryDirectory() as tmp:
        result = check(tmp, {"01-a.md": "# A doc\n\nNo header at all.\n"})
        assert kinds(result) == ["MISSING HEADER"], result.report()


def test_a_header_missing_one_required_field_is_caught():
    with tempfile.TemporaryDirectory() as tmp:
        result = check(tmp, {"01-a.md": "# A doc\n\n**Owns:** a thing.\n\nBody.\n"})
        assert kinds(result) == ["MISSING HEADER"], result.report()
        assert "Defers to:" in result.findings[0].detail


def test_a_wrapped_field_parses_as_one_field():
    """Every doc here wraps at 80, so continuation lines are the normal case."""
    with tempfile.TemporaryDirectory() as tmp:
        result = check(tmp, {"01-a.md": "**Owns:** a thing that takes\n"
                                        "several lines to say, because it\n"
                                        "wraps at eighty columns.\n"
                                        "**Defers to:** `copy/identity.csv` — lines.\n"
                                        "**Allows:** none.\n\nBody.\n"})
        assert result.ok, result.report()


def test_an_authority_that_does_not_exist_is_caught_once():
    """One problem, one finding — not a DEAD PATH and an UNOWNED AUTHORITY."""
    with tempfile.TemporaryDirectory() as tmp:
        result = check(tmp, {"01-a.md": "**Owns:** a thing.\n"
                                        "**Defers to:** `outbound/ghost.py` — nothing.\n"
                                        "**Allows:** none.\n\nBody.\n"})
        assert kinds(result) == ["UNOWNED AUTHORITY"], result.report()


def test_defers_to_none_is_legal():
    with tempfile.TemporaryDirectory() as tmp:
        assert check(tmp, {"01-a.md": HEADER + "\nBody.\n"}).ok


def test_an_airtable_authority_resolves_against_claude_md():
    """Even the non-file authorities are mechanically checkable."""
    with tempfile.TemporaryDirectory() as tmp:
        good = check(tmp, {"01-a.md": "**Owns:** a thing.\n"
                                      "**Defers to:** `Airtable: Leads tbl51dU7ojrxCVfxZ`.\n"
                                      "**Allows:** none.\n\nBody.\n"})
        assert good.ok, good.report()
        # A well-formed id that CLAUDE.md does not declare — the realistic
        # failure is a typo'd digit in a real one, not a malformed id.
        bad = check(tmp, {"01-a.md": "**Owns:** a thing.\n"
                                     "**Defers to:** `Airtable: Ghost tbl51dU7ojrxCVfxA`.\n"
                                     "**Allows:** none.\n\nBody.\n"})
        assert kinds(bad) == ["UNOWNED AUTHORITY"], bad.report()


# ------------------------------------------------------- undocumented commands


def test_a_command_nothing_writes_down_is_caught():
    with tempfile.TemporaryDirectory() as tmp:
        result = check(tmp, {"05-pipeline.md": HEADER
                             + "\n`lint` `export` `dedupe` `apify` `doc-check`\n"
                               "`apify limits` and `apify li-posts`\n"})
        assert "UNDOCUMENTED COMMAND" in kinds(result), result.report()
        assert any("deal" in f.detail for f in result.findings), result.report()


def test_a_parser_with_no_subcommands_cannot_run():
    """argparse._SubParsersAction is private API. If it ever changes shape this
    must exit 2 — reporting every documented command as unknown would be the
    worst bug available in this command."""
    with tempfile.TemporaryDirectory() as tmp:
        root = build(tmp, {"01-a.md": HEADER + "\nbody\n"})
        try:
            doc_check.check_docs(root, parser=argparse.ArgumentParser(),
                                 airtable=OFFLINE)
        except doc_check.DocCheckError:
            pass
        else:
            raise AssertionError("an empty parser must not report a clean docs tree")


# ---------------------------------------------------------------- value drift


def test_the_word_budget_must_match_the_linter():
    """The one value a spec doc owns that code also holds a copy of. The doc
    decides and the linter implements, which is the right way round — but the
    number exists twice, and twice is how it goes stale."""
    from outbound import lint

    with tempfile.TemporaryDirectory() as tmp:
        good = check(tmp, {"04-email.md": HEADER
                           + f"\n{lint.WORD_MIN} to {lint.WORD_MAX} words.\n"})
        assert good.ok, good.report()
        bad = check(tmp, {"04-email.md": HEADER
                          + f"\n{lint.WORD_MIN - 7} to {lint.WORD_MAX} words.\n"})
        assert kinds(bad) == ["VALUE DRIFT"], bad.report()


def test_dropping_the_word_budget_entirely_is_also_drift():
    """Deleting the sentence must not be a way to pass the check."""
    with tempfile.TemporaryDirectory() as tmp:
        result = check(tmp, {"04-email.md": HEADER + "\nEmails are short.\n"})
        assert kinds(result) == ["VALUE DRIFT"], result.report()


# ------------------------------------------------------------------ rung flags


def test_a_rung_invoked_without_its_flags_is_caught():
    """The drift that cost the measurement. `research-worker.md` ran `apify
    li-posts --max 5` with no window while `hook-worker.md` ran the same command
    `--since 3months`, so one profile was asked two different questions a stage
    apart — 4 of the 5 UNOBSERVED hooks in `2026-08-01-q1`."""
    with tempfile.TemporaryDirectory() as tmp:
        result = check(tmp, {"01-a.md": HEADER
                             + "\n`python main.py apify li-posts <url> --max 5`\n"})
        assert kinds(result) == ["RUNG FLAGS"], result.report()


def test_the_full_call_passes():
    from outbound import plan

    rung = next(r for r in plan.LADDER if r.name == "li_posts")
    line = f"`python main.py apify li-posts <url> {' '.join(rung.flags)}`"
    with tempfile.TemporaryDirectory() as tmp:
        assert check(tmp, {"01-a.md": HEADER + f"\n{line}\n"}).ok


def test_prose_about_a_rung_is_not_an_invocation():
    """A doc may name `apify li-posts` to say what it is. An argument has to
    follow the subcommand before the line counts as a call — otherwise every
    mention of a command becomes a place flags have to be recited."""
    with tempfile.TemporaryDirectory() as tmp:
        result = check(tmp, {"01-a.md": HEADER
                             + "\nThe li_posts rung is the expensive one.\n"
                             + "\n`python main.py apify li-posts`\n"})
        assert result.ok, result.report()


def test_one_subcommand_serving_two_rungs_is_told_apart():
    """`apify ig --mode details` reads a bio for the floors; `--mode posts` is
    hook material. Checking the first against the second's window would demand a
    90-day filter on a profile read that has no posts in it."""
    with tempfile.TemporaryDirectory() as tmp:
        details = check(tmp, {"01-a.md": HEADER + "\n`python main.py apify "
                              "ig <url> --mode details`\n"})
        assert details.ok, details.report()
        posts = check(tmp, {"01-a.md": HEADER + "\n`python main.py apify "
                            "ig <url> --mode posts`\n"})
        assert kinds(posts) == ["RUNG FLAGS"], posts.report()


def test_a_verification_fetch_carries_no_window():
    """The verifier re-fetches one page to confirm one quote. Narrowing that to
    the hook window would make it refute a post for being older than the rule
    that chose it — the same reason it is never told the hook room."""
    with tempfile.TemporaryDirectory() as tmp:
        result = check(tmp, {"01-a.md": HEADER + "\n`python main.py apify "
                             "li-posts <url> --stage verify --purpose verify`\n"})
        assert result.ok, result.report()


def test_the_agent_files_are_in_the_scanned_corpus():
    """They were not, which is how two prompts disagreed about a retrieval
    window for months with every gate green. They name commands and paths
    exactly as the skills do."""
    assert any(".claude/agents" in glob for glob in doc_check.SCAN_GLOBS)


# --------------------------------------------------------------- schema drift


def stub_schema(overrides: dict | None = None) -> dict:
    """A base schema built from what the repo currently mirrors, so it passes.

    Built FROM `AIRTABLE_SELECTS` rather than hand-typed. A hand-typed copy of
    eleven option lists is a fourth copy of the thing this check exists to stop
    from existing twice, and it would go stale exactly as silently.
    """
    tables: dict = {}
    for table, field, module, attr in doc_check.AIRTABLE_SELECTS:
        options = sorted((overrides or {}).get(
            (table, field), doc_check.mirrored_options(module, attr)))
        tables.setdefault(table, []).append({
            "name": field,
            "type": "singleSelect",
            "options": {"choices": [{"name": v} for v in options]},
        })
    return {"tables": [{"name": name, "fields": fields}
                       for name, fields in tables.items()]}


def test_a_matching_schema_is_no_drift():
    assert doc_check.check_airtable_selects(stub_schema()) == []


def test_an_option_we_list_and_the_base_does_not_is_caught():
    """The failure the tuples exist to prevent: the write is rejected by
    Airtable at the CRM step, after the email is in the upload file."""
    from audit import airtable

    short = tuple(v for v in airtable.HOOK_TYPES if v != "METRIC")
    schema = stub_schema({("Leads", "Hook Type"): short})
    findings = doc_check.check_airtable_selects(schema)
    assert [f.kind for f in findings] == ["SCHEMA DRIFT"], findings
    assert "METRIC" in findings[0].detail
    assert findings[0].path == "audit/airtable.py", findings[0]


def test_an_option_added_in_the_ui_is_caught():
    """Drift the other way. Nothing breaks today; the guard now rejects a value
    the CRM accepts, which reads as a bug in the machine."""
    from audit import airtable

    grown = airtable.LEAD_STATUSES + ("Nurture",)
    schema = stub_schema({("Leads", "Status"): grown})
    findings = doc_check.check_airtable_selects(schema)
    assert [f.kind for f in findings] == ["SCHEMA DRIFT"], findings
    assert "Nurture" in findings[0].detail


def test_the_not_set_sentinel_is_not_expected_in_the_base():
    """`""` is our not-yet-known marker. Airtable has no such option — a select
    is set or absent — so it must never be reported as missing from the base."""
    from outbound import research

    assert "" in research.COACH_TYPES, "the sentinel this test is about is gone"
    assert doc_check.check_airtable_selects(stub_schema()) == []


def test_every_mapped_option_list_resolves_and_is_not_empty():
    """A typo in the mapping must fail loudly. An unreadable option list read as
    an empty set would compare equal to nothing and report as no drift."""
    for table, field, module, attr in doc_check.AIRTABLE_SELECTS:
        assert doc_check.mirrored_options(module, attr), f"{module}.{attr}"


def test_an_unreachable_field_cannot_read_as_no_drift():
    """A renamed field in the base is exit 2, never a pass."""
    schema = stub_schema()
    schema["tables"][0]["fields"][0]["name"] = "Renamed In The UI"
    try:
        doc_check.check_airtable_selects(schema)
    except doc_check.DocCheckError:
        pass
    else:
        raise AssertionError("a field it could not read must never read as clean")


def test_live_without_a_key_is_exit_2_not_a_skip():
    """--live is an assertion. "It would have run if it could" is the thing it
    exists to stop being relied on."""
    import os

    from audit import airtable

    saved = os.environ.pop("AIRTABLE_API_KEY", None)
    try:
        assert not airtable.available()
        with tempfile.TemporaryDirectory() as tmp:
            root = build(tmp, {"01-a.md": HEADER + "\nbody\n"})
            try:
                doc_check.check_docs(root, parser=fake_parser(), airtable=True)
            except doc_check.DocCheckError as exc:
                assert "AIRTABLE_API_KEY" in str(exc), exc
            else:
                raise AssertionError("--live with no key must not report clean")
    finally:
        if saved is not None:
            os.environ["AIRTABLE_API_KEY"] = saved


def test_no_key_is_a_reported_skip_never_a_silent_pass():
    """Bare doc-check without a key still runs — CI has no key — but the check
    it could not do is printed, for the same reason the journal exclusion is."""
    import os

    saved = os.environ.pop("AIRTABLE_API_KEY", None)
    try:
        with tempfile.TemporaryDirectory() as tmp:
            root = build(tmp, {"01-a.md": HEADER + "\nbody\n"})
            result = doc_check.check_docs(root, parser=fake_parser())
        assert result.ok, result.report()
        reasons = [why for what, why in result.skipped if "select" in what]
        assert reasons, result.skipped
        assert "AIRTABLE_API_KEY" in reasons[0], reasons
        assert "select" in result.report()
    finally:
        if saved is not None:
            os.environ["AIRTABLE_API_KEY"] = saved


# ------------------------------------------------------- the real repo


def test_the_repo_itself_passes():
    """The one that makes this a standing gate rather than a command someone
    remembers to run."""
    sys.path.insert(0, str(ROOT))
    import main

    result = doc_check.check_docs(ROOT, parser=main.build_parser(), airtable=OFFLINE)
    assert result.ok, result.report()


def test_the_journal_is_skipped_on_purpose():
    """The one deliberate blind spot. It must be visible, so it can never
    become an accident: docs/journal.md legitimately names deleted files."""
    sys.path.insert(0, str(ROOT))
    import main

    result = doc_check.check_docs(ROOT, parser=main.build_parser(), airtable=OFFLINE)
    skipped = dict(result.skipped)
    assert "docs/journal.md" in skipped, result.skipped
    assert skipped["docs/journal.md"].strip(), "an exclusion must carry a reason"


def test_a_proposal_may_name_things_that_do_not_exist_yet():
    """A proposal argues for commands and modules that are not built. Checking
    one gates it on already being built, and the first proposal written under
    this check had to drop the backticks off every command it named to pass."""
    with tempfile.TemporaryDirectory() as tmp:
        root = build(tmp, {"01-a.md": HEADER + "\nbody\n"}, extra={
            "docs/proposals/a-proposal.md":
                "Run `python main.py observe <obs.json>`, defined in "
                "`outbound/observe.py`, writing `data/runs/<batch>.jsonl`.\n",
        })
        result = doc_check.check_docs(root, parser=fake_parser(), airtable=False)
        assert result.ok, result.report()
        skipped = dict(result.skipped)
        assert "docs/proposals/a-proposal.md" in skipped, result.skipped
        assert skipped["docs/proposals/a-proposal.md"].strip(), \
            "an exclusion must carry a reason"


def test_a_doc_outside_proposals_still_cannot_name_a_missing_command():
    """The exclusion is a directory, not a loophole. Pinned because the obvious
    way to write it — a substring match on 'proposal' — would exempt any file
    whose path merely contains the word."""
    with tempfile.TemporaryDirectory() as tmp:
        root = build(tmp, {"01-a.md": HEADER + "\nRun `main.py observe`.\n"})
        result = doc_check.check_docs(root, parser=fake_parser(), airtable=False)
        kinds = {f.kind for f in result.findings}
        assert kinds == {"UNKNOWN COMMAND"}, result.report()


def test_runtime_prefixes_match_gitignore():
    """The constant is derived from .gitignore. Pin it so the two cannot
    silently diverge and start flagging paths a clean checkout never has."""
    ignored = (ROOT / ".gitignore").read_text(encoding="utf-8")
    for prefix in doc_check.RUNTIME_PREFIXES:
        assert re.search(rf"^/?{re.escape(prefix)}\s*$", ignored, re.M), prefix


def test_a_missing_spec_dir_cannot_run():
    with tempfile.TemporaryDirectory() as tmp:
        root = build(tmp, {"01-a.md": HEADER + "\nbody\n"})
        for path in (root / "docs" / "spec").glob("*.md"):
            path.unlink()
        (root / "docs" / "spec").rmdir()
        try:
            doc_check.check_docs(root, parser=fake_parser(), airtable=OFFLINE)
        except doc_check.DocCheckError:
            pass
        else:
            raise AssertionError("a missing docs tree must never read as no drift")


if __name__ == "__main__":
    failures = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"  ok    {name}")
            except AssertionError as exc:
                failures += 1
                print(f"  FAIL  {name}: {exc}")
    print(f"\n{failures} failure(s)")
    sys.exit(1 if failures else 0)


# ------------------------------------------------ a manual quoting its own copy


def test_a_reference_doc_may_not_use_a_live_bank_line_as_its_example():
    """`cta-01` WAS the drafting manual's good example, word for word. Fine on
    a first send and a tell the moment a reader sees two — and a model shown a
    line as the exemplar reproduces it, which is what the same page tells it
    not to do two paragraphs later."""
    bank = doc_check.load_copy_lines(ROOT)
    live = next(iter(bank))
    text = next(k for k, v in bank.items() if v == bank[live])
    line = f'- Good: "{_readable(ROOT, bank[live])}"'
    found = doc_check.check_quoted_copy(
        ".claude/skills/x/references/y.md", [line], bank)
    assert found and found[0].kind == "QUOTED LIVE COPY"
    assert bank[live] in found[0].detail or found[0].detail


def test_a_spec_may_quote_copy_it_is_reasoning_about():
    """Only reference docs are scanned. `docs/spec/04-email.md` naming a line it
    is explaining is a citation, not an example anybody is meant to copy."""
    bank = doc_check.load_copy_lines(ROOT)
    line = f'- Good: "{_readable(ROOT, next(iter(bank.values())))}"'
    assert doc_check.check_quoted_copy("docs/spec/04-email.md", [line], bank) == []


def test_an_invented_example_passes():
    bank = doc_check.load_copy_lines(ROOT)
    line = '- Good: "Find me 15 minutes and you have all 10 by the end of the day."'
    assert doc_check.check_quoted_copy(
        ".claude/skills/x/references/y.md", [line], bank) == []


def _readable(root, line_id):
    """The live text of one bank line, by id."""
    import csv as _csv
    for name in ("identity", "offer", "cta", "ps"):
        with (root / "copy" / f"{name}.csv").open(newline="", encoding="utf-8") as fh:
            for row in _csv.DictReader(fh):
                if (row.get("id") or "").strip() == line_id:
                    return row["line"]
    raise AssertionError(line_id)
