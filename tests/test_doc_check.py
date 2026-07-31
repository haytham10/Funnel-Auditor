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
    for name in ("limits", "li-posts"):
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
        "`apify limits` and `apify li-posts`\n"))
    (root / "docs" / "spec").mkdir(parents=True, exist_ok=True)
    for name, body in specs.items():
        (root / "docs" / "spec" / name).write_text(body, encoding="utf-8")
    for rel, body in (extra or {}).items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
    return root


def check(tmp, spec: dict, extra: dict | None = None):
    return doc_check.check_docs(build(tmp, spec, extra), parser=fake_parser())


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
            doc_check.check_docs(root, parser=fake_parser())
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
            doc_check.check_docs(root, parser=argparse.ArgumentParser())
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


# ------------------------------------------------------- the real repo


def test_the_repo_itself_passes():
    """The one that makes this a standing gate rather than a command someone
    remembers to run."""
    sys.path.insert(0, str(ROOT))
    import main

    result = doc_check.check_docs(ROOT, parser=main.build_parser())
    assert result.ok, result.report()


def test_the_journal_is_skipped_on_purpose():
    """The one deliberate blind spot. It must be visible, so it can never
    become an accident: docs/journal.md legitimately names deleted files."""
    sys.path.insert(0, str(ROOT))
    import main

    result = doc_check.check_docs(ROOT, parser=main.build_parser())
    skipped = dict(result.skipped)
    assert "docs/journal.md" in skipped, result.skipped
    assert skipped["docs/journal.md"].strip(), "an exclusion must carry a reason"


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
            doc_check.check_docs(root, parser=fake_parser())
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
