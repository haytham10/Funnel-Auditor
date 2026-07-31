"""What the CLI does when it is handed something wrong.

Every gate in this machine is quoted verbatim by a skill rather than
paraphrased, which only works if a bad input produces a readable line and a
meaningful exit code. A traceback does neither: it reads as "the run crashed"
when the truth is "the wall could not be checked" or "a worker returned a list
where the schema says object", and an orchestrator that cannot tell those apart
either stops a good batch or, worse, waves a bad one through.

The contract these tests pin:

    exit 0   the check ran and passed
    exit 1   the check ran and something failed (a warm hit, a lint failure)
    exit 2   the check could NOT run

Exit 2 is the one that matters. A missing wall file must never read as "nobody
has been contacted".
"""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def offline_env() -> dict:
    """The CLI's environment with the Airtable key removed.

    `doc-check` runs its CRM schema check whenever a key is present, which is
    the right default for a person and the wrong one for a suite: the tests
    would reach the network on a developer machine and not in CI, so a failure
    would depend on who ran them. Same reason conftest.py pins
    OUTBOUND_COPY_SOURCE=csv. The schema check has its own tests, against a stub.
    """
    env = dict(os.environ)
    env.pop("AIRTABLE_API_KEY", None)
    return env


def run(*args, stdin: str = "") -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "main.py", *args],
        cwd=ROOT, input=stdin, capture_output=True, text=True, env=offline_env(),
    )


def write(tmp: str, name: str, payload) -> str:
    path = Path(tmp) / name
    path.write_text(payload if isinstance(payload, str) else json.dumps(payload),
                    encoding="utf-8")
    return str(path)


# --------------------------------------------------------------- the wall


def test_a_missing_wall_file_exits_2_not_a_traceback():
    """The most consequential failure in the machine. A wall that cannot be
    read must stop the batch, and must say so in a line a skill can quote."""
    with tempfile.TemporaryDirectory() as tmp:
        leads = write(tmp, "leads.json", [{"name": "Nobody New"}])
        result = run("dedupe", leads, "--contacts", f"{tmp}/does-not-exist.csv")
        assert result.returncode == 2, result.stdout + result.stderr
        assert "Traceback" not in result.stderr
        assert "cannot read the wall" in result.stdout


def test_a_corrupt_wall_file_exits_2():
    with tempfile.TemporaryDirectory() as tmp:
        leads = write(tmp, "leads.json", [{"name": "Nobody New"}])
        bad = write(tmp, "wall.json", "{not json at all")
        result = run("dedupe", leads, "--contacts", bad)
        assert result.returncode == 2, result.stdout + result.stderr
        assert "Traceback" not in result.stderr


def test_an_empty_wall_exits_2_rather_than_clearing_everyone():
    """"The file parsed and held nothing" and "nobody has ever been contacted"
    are the same bytes and opposite meanings."""
    with tempfile.TemporaryDirectory() as tmp:
        leads = write(tmp, "leads.json", [{"name": "Nobody New"}])
        empty = write(tmp, "wall.json", [])
        result = run("dedupe", leads, "--contacts", empty)
        assert result.returncode == 2, result.stdout + result.stderr
        assert "the wall is empty" in result.stdout


# ------------------------------------------------- one object, not a list


def test_qualify_on_a_json_array_exits_2_with_a_readable_line():
    """A worker returning a list where the schema says object used to raise
    AttributeError, which reads as a crash rather than the schema violation it
    is."""
    result = run("qualify", "-", stdin=json.dumps([{"name": "Sarah"}]))
    assert result.returncode == 2, result.stdout + result.stderr
    assert "Traceback" not in result.stderr
    assert "one JSON object" in result.stdout


def test_research_accepts_a_slice_array():
    """`research-worker` handles a slice of about ten leads and returns an
    array. This used to exit 2 with "expected one JSON object, got list",
    printed beside a skill instruction that says a schema violation goes back
    to the worker once — so the documented validation step failed on the
    documented file, in a way that read like the worker returned garbage."""
    slice_of_two = [
        {"name": "A", "uae_based": "yes", "is_coach": "yes", "active_recent": "unclear"},
        {"name": "B", "uae_based": "yes", "is_coach": "yes", "active_recent": "unclear"},
    ]
    result = run("research", "-", stdin=json.dumps(slice_of_two))
    assert "Traceback" not in result.stderr
    assert "RESEARCH A" in result.stdout and "RESEARCH B" in result.stdout
    assert "2 valid" in result.stdout or "/2" in result.stdout


def test_research_still_takes_a_single_object():
    result = run("research", "-", stdin=json.dumps(
        {"name": "A", "uae_based": "yes", "is_coach": "yes", "active_recent": "unclear"}))
    assert "Traceback" not in result.stderr
    assert "RESEARCH A" in result.stdout


def test_an_empty_research_slice_exits_2():
    """A worker that returned nothing is not a slice that passed."""
    result = run("research", "-", stdin="[]")
    assert result.returncode == 2, result.stdout
    assert "returned nothing" in result.stdout


def test_a_missing_input_file_exits_2():
    result = run("qualify", "/nope/not/here.json")
    assert result.returncode == 2, result.stdout + result.stderr
    assert "Traceback" not in result.stderr
    assert "cannot read" in result.stdout


def test_malformed_json_exits_2():
    result = run("qualify", "-", stdin="{oh dear")
    assert result.returncode == 2, result.stdout + result.stderr
    assert "Traceback" not in result.stderr


# ------------------------------------------------------------ the warm stop


def test_a_warm_hit_exits_1():
    """Not 2. The check ran fine; what it found is the problem, and the two
    cases need different handling by the caller."""
    with tempfile.TemporaryDirectory() as tmp:
        leads = write(tmp, "leads.json", [{"name": "Rita Baki"}])
        wall = write(tmp, "wall.json", [
            {"Contact Name": "Rita Baki", "Status": "Reply Received"},
            {"Contact Name": "Someone Else", "Status": "Outreach Sent"},
        ])
        result = run("dedupe", leads, "--contacts", wall)
        assert result.returncode == 1, result.stdout + result.stderr
        assert "WARM THREAD" in result.stdout


def test_a_clean_batch_exits_0():
    with tempfile.TemporaryDirectory() as tmp:
        leads = write(tmp, "leads.json", [{"name": "Nobody New"}])
        wall = write(tmp, "wall.json", [
            {"Contact Name": "Rita Baki", "Status": "Reply Received"},
        ])
        result = run("dedupe", leads, "--contacts", wall)
        assert result.returncode == 0, result.stdout + result.stderr


# ------------------------------------------------ every command, every bad file


BAD_INPUT_CASES = [
    ("lint",       "bad.json"),
    ("deal",       "bad.json"),
    ("export",     "bad.json"),
    ("dedupe",     "bad.json"),
    ("qualify",    "bad.json"),
    ("research",   "bad.json"),
    ("copy-sync",  "bad.json"),
]


def test_no_command_tracebacks_on_malformed_json():
    """A JSONDecodeError traceback reads as "the run crashed" when the truth is
    "that file is not JSON", and a skill quoting a gate cannot tell them apart."""
    with tempfile.TemporaryDirectory() as tmp:
        bad = write(tmp, "bad.json", "{not json at all")
        for command, _ in BAD_INPUT_CASES:
            args = [command, bad]
            if command == "export":
                args += ["--out", str(Path(tmp) / "out")]
            result = run(*args)
            assert "Traceback" not in result.stderr, f"{command}: {result.stderr[-300:]}"
            assert result.returncode == 2, f"{command} exited {result.returncode}"


def test_no_command_tracebacks_on_a_missing_file():
    with tempfile.TemporaryDirectory() as tmp:
        for command in ("lint", "deal", "dedupe", "qualify", "research",
                        "copy-sync", "intake", "wall-add", "copy-usage"):
            args = [command, "/nope/does-not-exist.json"]
            result = run(*args)
            assert "Traceback" not in result.stderr, f"{command}: {result.stderr[-300:]}"
            assert result.returncode == 2, f"{command} exited {result.returncode}"


def test_a_json_object_where_an_array_belongs_exits_2():
    with tempfile.TemporaryDirectory() as tmp:
        obj = write(tmp, "obj.json", {"a": 1})
        for command in ("deal", "dedupe"):
            result = run(command, obj)
            assert result.returncode == 2, f"{command} exited {result.returncode}"
            assert "Traceback" not in result.stderr


def test_an_empty_batch_does_not_crash_the_deal_report():
    """`next(iter(...))` on an empty share table raised StopIteration, which is
    a traceback on a command whose whole output is meant to be quotable."""
    with tempfile.TemporaryDirectory() as tmp:
        empty = write(tmp, "empty.json", [])
        result = run("deal", empty)
        assert result.returncode == 0, result.stdout + result.stderr
        assert "Traceback" not in result.stderr
        assert "0 leads" in result.stdout


def test_wall_add_refuses_a_file_with_the_wrong_columns():
    """It printed "0 added, 104 -> 104", which reads exactly like "this batch
    was already walled". Those leads would never enter the wall and would be
    contacted a second time — the failure the wall exists to prevent, reached
    through a mistyped path."""
    with tempfile.TemporaryDirectory() as tmp:
        wrong = write(tmp, "wrong.csv", "alpha,beta\n1,2\n")
        result = run("wall-add", wrong)
        assert result.returncode == 2, result.stdout
        assert "none of the expected columns" in result.stdout
        assert "0 added" not in result.stdout


def test_copy_usage_refuses_a_file_with_the_wrong_columns():
    with tempfile.TemporaryDirectory() as tmp:
        wrong = write(tmp, "wrong.csv", "alpha,beta\n1,2\n")
        result = run("copy-usage", wrong)
        assert result.returncode == 2, result.stdout
        assert "none of the expected columns" in result.stdout


def test_piping_a_gate_into_head_does_not_traceback():
    """Piping a gate's output into head or grep is ordinary, and the default
    BrokenPipeError handling prints a traceback on exit — which looks exactly
    like a crash in a command whose job is to be believed."""
    import subprocess
    proc = subprocess.run(
        f"{sys.executable} main.py facts 2>&1 | head -2",
        cwd=ROOT, shell=True, capture_output=True, text=True)
    assert "Traceback" not in proc.stdout + proc.stderr
    assert "BrokenPipe" not in proc.stdout + proc.stderr


def test_qualify_settles_activity_from_the_page_when_no_date_is_given():
    """The bridge existed only as a library function and the CLI never reached
    it, so all twelve leads on the first real batch came back `unclear` on
    activity — the floor doing nothing at all."""
    with tempfile.TemporaryDirectory() as tmp:
        lead = write(tmp, "lead.json", {
            "name": "Test Coach", "city": "Dubai", "domain": "x.ae",
            "headline": "Life Coach",
            "site_text": "Coaching in Dubai. Latest article 2026-07-20 on pricing.",
        })
        result = run("qualify", lead)
        assert "activity settled from the page" in result.stdout, result.stdout
        assert "2026-07-20" in result.stdout


def test_qualify_prefers_a_date_the_worker_supplied():
    with tempfile.TemporaryDirectory() as tmp:
        lead = write(tmp, "lead.json", {
            "name": "Test Coach", "city": "Dubai", "headline": "Life Coach",
            "last_activity": "2026-07-25",
            "site_text": "Latest article 2020-01-01.",
        })
        result = run("qualify", lead)
        assert "2026-07-25" in result.stdout
        assert "activity settled from the page" not in result.stdout


def test_a_malformed_last_activity_exits_2():
    with tempfile.TemporaryDirectory() as tmp:
        lead = write(tmp, "lead.json", {
            "name": "X", "last_activity": "not-a-date", "site_text": "coach in dubai"})
        result = run("qualify", lead)
        assert result.returncode == 2, result.stdout
        assert "Traceback" not in result.stderr
        assert "ISO date" in result.stdout


def test_lint_assembles_the_body_from_beats():
    """A drafting worker's whole contract is beats, and `lint` answered "body is
    empty" — so the PASS line the worker is required to quote was unobtainable.
    Telling workers to assemble their own is worse: the order is load-bearing,
    and a worker that joined it differently would quote a PASS about text that
    is not what ships, with word count the check most likely to differ."""
    draft = {
        "slug": "sarah-ahmed", "name": "Sarah Ahmed",
        "subject": "your hashimoto post",
        "beats": {
            "hook": ("You wrote that you couldn't contain the excitement of "
                     "uncovering a solution for yourself."),
            "identity": ("My job is finding your next client. A health coach in "
                         "Dubai closed AED 78,000 over 2 months from prospects "
                         "I put in front of them."),
            "offer": ("I pulled 10 names for you before writing this. Not a "
                      "scraped list, people I'd actually start with."),
            "cta": ("15 minutes and they're yours the same day. I'll tell you "
                    "why these 10 and not the other 40."),
            "ps": "ps: a no here costs you nothing and costs me nothing.",
        },
    }
    result = run("lint", "-", stdin=json.dumps([draft]))
    assert result.returncode == 0, result.stdout
    assert "PASS" in result.stdout
    assert "body is empty" not in result.stdout


def test_lint_uses_an_explicit_body_when_one_is_given():
    """The assembler is a fallback, not an override."""
    result = run("lint", "-", stdin=json.dumps([{
        "name": "X", "subject": "a subject", "body": "", "beats": {}}]))
    assert "body is empty" in result.stdout


def test_the_same_assembler_serves_lint_and_export():
    """One assembler, used by both commands, is the only version that cannot
    drift. If these ever diverge, a draft lints clean and ships different text."""
    import subprocess
    check = subprocess.run(
        [sys.executable, "-c",
         "import main, outbound.export as e, inspect;"
         "src = inspect.getsource(main.cmd_lint);"
         "print('assemble_body' in src and 'from outbound.export import' in src)"],
        cwd=ROOT, capture_output=True, text=True)
    assert check.stdout.strip() == "True", check.stdout + check.stderr


# ------------------------------------------------------------------ doc-check


def test_doc_check_passes_on_the_real_repo():
    result = run("doc-check")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "DOC-CHECK: PASS" in result.stdout


def test_doc_check_exits_2_when_it_cannot_read_the_docs():
    """A missing docs tree must never read as "no drift", for exactly the
    reason a missing wall must never read as "nobody has been contacted"."""
    import shutil
    with tempfile.TemporaryDirectory() as tmp:
        for name in ("main.py", "outbound", "audit", "copy", "CLAUDE.md",
                     ".gitignore"):
            src = ROOT / name
            dst = Path(tmp) / name
            (shutil.copytree if src.is_dir() else shutil.copy2)(src, dst)
        (Path(tmp) / "docs").mkdir()
        result = subprocess.run([sys.executable, "main.py", "doc-check"],
                                cwd=tmp, capture_output=True, text=True,
                                env=offline_env())
        assert result.returncode == 2, result.stdout + result.stderr
        assert "Traceback" not in result.stdout + result.stderr
        assert "could not run" in result.stdout
        assert "docs/spec" in result.stdout, "it must name what it could not read"


def test_piping_doc_check_into_head_does_not_traceback():
    """doc-check prints one line per finding plus a summary, so it is the
    command most likely to be piped into head or grep."""
    proc = subprocess.run(
        f"{sys.executable} main.py doc-check 2>&1 | head -1",
        cwd=ROOT, shell=True, capture_output=True, text=True, env=offline_env())
    assert "Traceback" not in proc.stdout + proc.stderr
    assert "BrokenPipe" not in proc.stdout + proc.stderr


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
