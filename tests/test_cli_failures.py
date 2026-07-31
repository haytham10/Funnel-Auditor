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
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def run(*args, stdin: str = "") -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "main.py", *args],
        cwd=ROOT, input=stdin, capture_output=True, text=True,
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


def test_research_on_a_json_array_exits_2():
    result = run("research", "-", stdin=json.dumps([{"lead": "Sarah"}]))
    assert result.returncode == 2, result.stdout + result.stderr
    assert "Traceback" not in result.stderr


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
