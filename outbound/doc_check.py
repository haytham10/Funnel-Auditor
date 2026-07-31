"""The docs, checked against the code they describe.

Every gate in this machine is quoted verbatim by a skill rather than
paraphrased, which only works while the quoted command still exists. And every
defining doc in `docs/spec/` promises something stronger: that it states a
decision and its reason and never holds a value something else owns.

Both promises rot the same way — quietly, one reasonable edit at a time, and
invisibly, because nothing reads a doc. The previous project's doc set died of
exactly this in about three weeks and cost a commit literally titled "Sweep the
last stale prices and rename the guarantee everywhere". That sweep is what a doc
layer costs when the only thing holding it together is somebody remembering.

So the mechanical half is mechanical. Eight drift classes:

    UNKNOWN COMMAND        a doc names a `main.py` subcommand the parser doesn't have
    DEAD PATH              a doc cites a repo path that isn't on disk
    STATE IN SPEC          a spec doc other than 03-offer.md carries a price
    UNKNOWN COPY ID        a doc cites a copy line that isn't in the CSV
    MISSING HEADER         a spec doc has no Owns:/Defers to: block
    UNOWNED AUTHORITY      a Defers to: names something that isn't there
    STALE ALLOW            an Allows: exception outlived the sentence it was for
    UNDOCUMENTED COMMAND   a real subcommand nothing writes down
    VALUE DRIFT            a value a doc owns, and code holds a stale copy of

**Fails closed.** A docs tree this cannot read is a failure, never a pass — the
same rule that makes an unreadable dedupe wall exit 2 rather than reading as
"nobody has been contacted". A gate that reports clean because it could not look
is worse than no gate, because it is believed.

Three scoping decisions, each made by running the check by hand over the real
corpus first rather than by reasoning about it:

**`docs/journal.md` is excluded.** It is an append-only log and it legitimately
names deleted files, retired commands and copy lines that no longer exist,
because it is recording that they were deleted. Four of its dead pointers are
live today and all four are correct. Checking a log against today's code is a
category error, and the noise would train people to ignore the gate. The
exclusion is printed in the report so it can never quietly become an accident.

**Paths are not read from fenced blocks, commands are.** Every command in the
skills lives in a fence, so commands must be read there. Fences are also full of
`work/leads.json` scratch paths and illustrative `some/authority.csv` filler, so
paths must not be. The asymmetry is deliberate and it is load-bearing.

**Path resolution walks from the file's directory up to the repo root.** This is
not an optimisation. `.claude/skills/outbound-draft/references/voice.md` cites
`references/critical-failures.md`, which resolves against the *skill* root — not
the citing file's directory and not the repo root. Both simpler rules flag it,
and a gate that fails on a clean checkout gets switched off inside a week.

One deliberate false negative: an id whose family is not in the copy CSVs is not
treated as a copy id at all. Flagging unknown families would catch a typo'd
prefix and would also flag `utf-8`, `sha-256` and `gpt-4`. The common failure is
a wrong digit on a real prefix (`ps-09`), and that is caught.
"""

from __future__ import annotations

import argparse
import csv
import re
from dataclasses import dataclass, field
from pathlib import Path

# The corpus. Everything else in the repo is code, and code has tests.
SCAN_GLOBS = ("docs/**/*.md", ".claude/skills/**/*.md")
SCAN_FILES = ("CLAUDE.md", "README.md")

SPEC_DIR = "docs/spec"
PRICE_OWNER = "docs/spec/03-offer.md"
PIPELINE_DOC = "docs/spec/05-pipeline.md"

# Excluded, with the reason, because a silent exclusion is indistinguishable
# from a bug. Both of these are reported on `skipped`.
EXCLUDED = {
    "docs/journal.md": "a log, not a spec — it names deleted things on purpose",
    "docs/claude-docs": "external market research, not a description of this machine",
}

# Gitignored (.gitignore: /out/, /work/) and so absent from a fresh clone, but
# legitimately named in docs. `test_runtime_prefixes_match_gitignore` pins these
# two against the file they came from.
RUNTIME_PREFIXES = ("out/", "work/")
RUNTIME_FILES = ("copy/_airtable.json",)

# Non-file authorities a `Defers to:` may name. A literal set, so adding one is
# a code change with a comment rather than a free-text escape.
EXTERNAL_AUTHORITIES = ("Smartlead", "Airtable", "Apify")

HEADER_LINES = 15
HEADER_FIELDS = ("Owns", "Defers to", "Allows")
REQUIRED_FIELDS = ("Owns", "Defers to")
EMPTY_VALUES = ("none.", "none", "nothing.", "nothing")

_INLINE_CODE = re.compile(r"`([^`\n]+)`")
_FENCE = re.compile(r"^\s*(?:```|~~~)")
_LINK = re.compile(r"\]\(([^)\s]+)\)")
_FIELD = re.compile(r"^\*\*(" + "|".join(HEADER_FIELDS) + r"):\*\*\s*(.*)$")

# `$ python3 main.py apify li-posts` — the leading prompt, the interpreter and
# the second token are all optional. The second token is only consulted for
# `apify`, the one command with nested subparsers.
#
# Exactly ONE space before the subcommand, deliberately. A column-aligned file
# listing in a fenced block reads as an invocation otherwise:
#
#     main.py            the CLI — every command is a decision
#
# which yields the subcommand `the`. Requiring the `python` prefix instead
# would be the obvious fix and is wrong: docs really do write bare `main.py
# lint`, `main.py apify` and `main.py wall-add`, and those would stop being
# checked. A false negative on real content is worse than one on alignment.
_COMMAND = re.compile(
    r"(?:\$\s*)?(?:python3? )?main\.py ([a-z][a-z0-9|_-]*)(?: +([a-z][a-z0-9_-]*))?")

# A price is a currency marker with a digit against it. Requiring the digit is
# what saves `top_program_price_aed` and prose about "the price conversation".
_PRICE = re.compile(r"(?:\bAED\s*|\$)\d[\d,]*(?:\.\d+)?(?:\s*[kK]\b)?")

_PATH = re.compile(r"^[A-Za-z0-9._~@-]+(?:/[A-Za-z0-9._~@-]+)+/?$")
_SIBLING_SPEC = re.compile(r"^\d\d-[a-z0-9-]+\.md$")
_LINE_ID = re.compile(r"^([a-z][a-z0-9-]*)-(\d+)$")
_TBL_ID = re.compile(r"\btbl[A-Za-z0-9]{14}\b")

# Placeholders, globs and URLs, none of which are claims about the filesystem.
_NOT_A_PATH = ("*", "<", ">", "{", "}", "|", "://", "mailto:")


class DocCheckError(RuntimeError):
    """The check could not run. Always exit 2, never a pass."""


@dataclass(frozen=True)
class Finding:
    path: str
    line: int          # 1-based; 0 when the finding is about the whole file
    kind: str
    detail: str

    def as_line(self) -> str:
        return f"{self.path}:{self.line}  {self.kind}  {self.detail}"


@dataclass
class Header:
    owns: str = ""
    defers: str = ""
    allows: str = ""
    start: int = 0
    end: int = 0
    field_lines: dict = field(default_factory=dict)

    def allow_tokens(self) -> list[str]:
        """The literal tokens this file is permitted to carry, in backticks."""
        if self.allows.strip().lower().rstrip(".") in ("none", "nothing"):
            return []
        return _INLINE_CODE.findall(self.allows)


@dataclass
class DocCheckResult:
    findings: list = field(default_factory=list)
    scanned: list = field(default_factory=list)
    skipped: list = field(default_factory=list)   # (path, why)
    counts: dict = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return not self.findings

    @property
    def line(self) -> str:
        """The one line a skill quotes."""
        if self.ok:
            return (f"DOC-CHECK: PASS — {len(self.scanned)} file(s) scanned, "
                    f"0 findings")
        files = len({f.path for f in self.findings})
        return (f"DOC-CHECK: FAIL — {len(self.findings)} finding(s) in "
                f"{files} file(s), {len(self.scanned)} file(s) scanned")

    def report(self) -> str:
        out = []
        for f in sorted(self.findings, key=lambda f: (f.path, f.line, f.kind)):
            out.append(f.as_line())
        out.append(self.line)
        if self.ok:
            c = self.counts
            out.append(f"  {c.get('commands', 0)} command(s) + "
                       f"{c.get('apify', 0)} apify subcommand(s) known, "
                       f"{c.get('copy_ids', 0)} copy id(s), "
                       f"{c.get('specs', 0)} spec doc(s) with headers")
        for path, why in self.skipped:
            out.append(f"  skipped: {path} ({why})")
        return "\n".join(out)


# --------------------------------------------------------------- introspection


def command_tree(parser) -> dict:
    """{'lint': frozenset(), 'apify': frozenset({'limits', ...}), ...}

    Read from the parser rather than a hand-kept list, because a hand-kept list
    is the exact class of copied value this whole layer exists to forbid. It
    is also, empirically, the thing that drifts: main.py's own docstring
    inventory had lost `fetch` and `facts` by the time this was written.
    """
    tree = {}
    for action in parser._actions:
        if not isinstance(action, argparse._SubParsersAction):
            continue
        for name, sub in action.choices.items():
            nested = set()
            for sub_action in sub._actions:
                if isinstance(sub_action, argparse._SubParsersAction):
                    nested.update(sub_action.choices)
            tree[name] = frozenset(nested)
    if not tree:
        # argparse._SubParsersAction is private API. If it ever changes shape,
        # this must fail closed: reporting every documented command as unknown
        # would be the single worst bug available in this command.
        raise DocCheckError("could not read any subcommand from the parser")
    return tree


# ---------------------------------------------------------------------- corpus


def scan_targets(root: Path) -> tuple[list, list]:
    """(files to scan, [(rel, why skipped)]). Raises if there is nothing to check."""
    spec = root / SPEC_DIR
    if not spec.is_dir():
        raise DocCheckError(f"{SPEC_DIR}/ is missing")
    if not any(spec.glob("*.md")):
        raise DocCheckError(f"{SPEC_DIR}/ holds no .md files")

    found, skipped = [], []
    for name in SCAN_FILES:
        if (root / name).is_file():
            found.append(root / name)
    for pattern in SCAN_GLOBS:
        found.extend(p for p in root.glob(pattern) if p.is_file())

    keep = []
    for path in sorted(set(found)):
        rel = path.relative_to(root).as_posix()
        why = next((w for pre, w in EXCLUDED.items()
                    if rel == pre or rel.startswith(pre + "/")), None)
        if why:
            skipped.append((rel, why))
        else:
            keep.append(path)
    return keep, sorted(set(skipped))


def read_doc(path: Path) -> list:
    try:
        return path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError) as exc:
        raise DocCheckError(f"cannot read {path}: {exc}") from exc


def _fence_mask(lines: list) -> list:
    """True for every line inside a fenced block (the fences themselves included)."""
    mask, inside = [], False
    for text in lines:
        if _FENCE.match(text):
            inside = not inside
            mask.append(True)
        else:
            mask.append(inside)
    return mask


def code_text(lines: list):
    """(lineno, text) for inline spans AND fenced blocks. Commands live in both."""
    mask = _fence_mask(lines)
    for i, text in enumerate(lines, start=1):
        if mask[i - 1]:
            yield i, text
        else:
            for span in _INLINE_CODE.findall(text):
                yield i, span


def path_tokens(lines: list):
    """(lineno, token) for inline spans and link targets — never fences.

    Fences are runtime invocations and worked examples; they cite scratch paths
    and illustrative filenames that were never meant to exist.
    """
    mask = _fence_mask(lines)
    for i, text in enumerate(lines, start=1):
        if mask[i - 1]:
            continue
        for span in _INLINE_CODE.findall(text):
            yield i, span
        for target in _LINK.findall(text):
            yield i, target


def prose_lines(lines: list, header: Header | None):
    """(lineno, text) for everything outside the header block.

    The header is metadata about the contract, not spec prose — so an `Allows:`
    entry quoting a price does not trip the price check on its own declaration.
    """
    lo, hi = (header.start, header.end) if header else (0, 0)
    for i, text in enumerate(lines, start=1):
        if lo <= i <= hi:
            continue
        yield i, text


# ---------------------------------------------------------------------- checks


def _clean(token: str) -> str:
    # rstrip only. strip(".") turns `.claude/skills/` into `claude/skills/`,
    # which is a guaranteed false positive on a path that is really there.
    return token.strip().rstrip(".,;:)]!?")


def _resolves(token: str, doc: Path, root: Path) -> bool:
    """Walk from the citing file's directory up to the repo root."""
    if (root / token).exists():
        return True
    here = doc.parent
    while True:
        if (here / token).exists():
            return True
        if here == root or root not in here.parents:
            return False
        here = here.parent


def check_commands(rel: str, lines: list, tree: dict) -> list:
    out = []
    for lineno, text in code_text(lines):
        for cmd, sub in _COMMAND.findall(text):
            for name in cmd.split("|"):
                if not name or any(c in name for c in _NOT_A_PATH):
                    continue
                if name not in tree:
                    out.append(Finding(rel, lineno, "UNKNOWN COMMAND",
                                       f"main.py {name} — not in build_parser()"))
                elif sub and tree[name] and sub not in tree[name]:
                    out.append(Finding(rel, lineno, "UNKNOWN COMMAND",
                                       f"main.py {name} {sub} — no such subcommand"))
    return out


def check_paths(rel: str, doc: Path, lines: list, root: Path,
                header: Header | None = None) -> list:
    """Paths outside the header block. The block is `check_authorities`' job.

    Without the split, a broken `Defers to:` target reports twice — once as a
    dead path and once as an unowned authority. One problem, one finding, or
    the count in the summary line stops meaning anything.
    """
    out = []
    in_spec = rel.startswith(SPEC_DIR + "/")
    skip = range(header.start, header.end + 1) if header else ()
    for lineno, raw in path_tokens(lines):
        if lineno in skip:
            continue
        token = _clean(raw)
        if not token or any(bad in token for bad in _NOT_A_PATH):
            continue
        if in_spec and _SIBLING_SPEC.match(token):
            if not (root / SPEC_DIR / token).exists():
                out.append(Finding(rel, lineno, "DEAD PATH",
                                   f"{token} — no such file in {SPEC_DIR}/"))
            continue
        if not _PATH.match(token):
            continue
        # An Apify actor id (`harvestapi/linkedin-profile-scraper`) reads as a
        # path and is not one. A real citation names a file or a directory.
        last = token.rstrip("/").rsplit("/", 1)[-1]
        if not token.endswith("/") and "." not in last:
            continue
        if token.startswith(RUNTIME_PREFIXES) or token in RUNTIME_FILES:
            continue
        if not _resolves(token, doc, root):
            out.append(Finding(rel, lineno, "DEAD PATH", token))
    return out


def check_prices(rel: str, lines: list, header: Header | None) -> list:
    if rel == PRICE_OWNER:
        return []
    allowed = header.allow_tokens() if header else []
    out, seen = [], set()
    for lineno, text in prose_lines(lines, header):
        for hit in _PRICE.findall(text):
            if any(hit in token for token in allowed):
                seen.add(hit)
                continue
            out.append(Finding(rel, lineno, "STATE IN SPEC",
                               f"{hit} — {PRICE_OWNER} owns prices"))
    if header:
        for token in allowed:
            if not any(t in token or token in t for t in seen):
                out.append(Finding(rel, header.field_lines.get("Allows", 0),
                                   "STALE ALLOW",
                                   f"{token} — allowed but appears nowhere in the file"))
    return out


def check_copy_ids(rel: str, lines: list, ids: dict) -> list:
    out = []
    for lineno, raw in path_tokens(lines):
        match = _LINE_ID.match(raw.strip())
        if not match:
            continue
        family = match.group(1)
        if family not in ids:
            continue          # not a copy id at all — see the module docstring
        if raw.strip() not in ids[family]:
            out.append(Finding(rel, lineno, "UNKNOWN COPY ID",
                               f"{raw.strip()} — not in the {family} lines"))
    return out


def check_header(rel: str, lines: list) -> tuple:
    """Parse the block, and report what is missing. One finding per file."""
    header, current = Header(), None
    for i, text in enumerate(lines[:HEADER_LINES], start=1):
        match = _FIELD.match(text)
        if match:
            current = match.group(1)
            header.field_lines[current] = i
            header.start = header.start or i
            header.end = i
            setattr(header, _attr(current), match.group(2).strip())
        elif current and text.strip():
            # A wrapped field continues until the next field or a blank line.
            # Every doc here wraps at 80, so this is the normal case.
            setattr(header, _attr(current),
                    (getattr(header, _attr(current)) + " " + text.strip()).strip())
            header.end = i
        elif current:
            break

    missing = [f for f in REQUIRED_FIELDS
               if not getattr(header, _attr(f)).strip()]
    if missing:
        at = next((i for i, t in enumerate(lines, start=1)
                   if t.startswith("# ")), 1)
        return None, [Finding(rel, at, "MISSING HEADER",
                              "no " + " / ".join(f"{f}:" for f in missing)
                              + f" in the first {HEADER_LINES} lines")]
    return header, []


def _attr(field_name: str) -> str:
    return {"Owns": "owns", "Defers to": "defers", "Allows": "allows"}[field_name]


def check_authorities(rel: str, doc: Path, header: Header, root: Path,
                      table_ids: set) -> list:
    if header.defers.strip().lower().rstrip(".") in ("none", "nothing"):
        return []
    out = []
    at = header.field_lines.get("Defers to", 0)
    for token in _INLINE_CODE.findall(header.defers):
        token = _clean(token)
        if any(token.startswith(name) for name in EXTERNAL_AUTHORITIES):
            for tbl in _TBL_ID.findall(token):
                if tbl not in table_ids:
                    out.append(Finding(rel, at, "UNOWNED AUTHORITY",
                                       f"{tbl} — no such table id in CLAUDE.md"))
            continue
        if "/" in token and not _resolves(token, doc, root):
            out.append(Finding(rel, at, "UNOWNED AUTHORITY",
                               f"{token} — no such file"))
    return out


def check_word_budget(rel: str, lines: list) -> list:
    """The one value a spec doc owns that code also holds a copy of.

    `docs/spec/04-email.md` declares that it owns the word budget, and
    `outbound/lint.py` enforces it. That is the right way round — the doc
    decides, the code implements — but it means the number exists twice, which
    is the precise situation the rest of this layer forbids.

    There is no general mechanism for this and there should not be until there
    is a second instance. One hardcoded pairing with a reason attached is
    honest; a framework for one case is not.
    """
    if rel != "docs/spec/04-email.md":
        return []
    from outbound import lint

    want = f"{lint.WORD_MIN} to {lint.WORD_MAX} words"
    for lineno, text in enumerate(lines, start=1):
        if re.search(r"\b\d+ to \d+ words\b", text):
            if want in text:
                return []
            return [Finding(rel, lineno, "VALUE DRIFT",
                            f"the word budget here disagrees with "
                            f"outbound/lint.py, which says {want}")]
    return [Finding(rel, 0, "VALUE DRIFT",
                    f"this file owns the word budget and no longer states it; "
                    f"outbound/lint.py enforces {want}")]


def check_documented_commands(tree: dict, spec_text: str, corpus_text: str,
                              main_doc: str) -> list:
    """Drift the other way: a command that exists and nothing writes down.

    Only a mention is required, not a section. Demanding `python main.py <cmd>`
    for each would turn the pipeline spec into a command dump, which is the
    opposite of what it is for.
    """
    out = []
    for name, subs in sorted(tree.items()):
        if not re.search(r"`[^`\n]*\b" + re.escape(name) + r"\b[^`\n]*`", spec_text):
            out.append(Finding(PIPELINE_DOC, 0, "UNDOCUMENTED COMMAND",
                               f"{name} is in build_parser() and is written down nowhere"))
        if not re.search(r"^\s+" + re.escape(name) + r"\b", main_doc, re.M):
            out.append(Finding("main.py", 1, "UNDOCUMENTED COMMAND",
                               f"{name} is missing from main.py's own inventory"))
        for sub in sorted(subs):
            if not re.search(r"\b" + re.escape(name) + r"\s+"
                             + re.escape(sub) + r"\b", corpus_text):
                out.append(Finding(PIPELINE_DOC, 0, "UNDOCUMENTED COMMAND",
                                   f"{name} {sub} is written down nowhere"))
    return out


# --------------------------------------------------------------------- loaders


def load_copy_ids(root: Path) -> dict:
    """Ids by family. A missing or headerless CSV is exit 2, never zero ids.

    The same failure the dedupe wall's emptiness check exists to prevent: an
    empty authority must never read as "nothing is valid".
    """
    ids = {}
    for name in ("identity", "offer", "cta", "ps"):
        path = root / "copy" / f"{name}.csv"
        try:
            with path.open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
        except (OSError, UnicodeDecodeError) as exc:
            raise DocCheckError(f"cannot read copy/{name}.csv: {exc}") from exc
        if not rows or "id" not in (rows[0].keys() if rows else {}):
            raise DocCheckError(f"copy/{name}.csv has no id column")
        for row in rows:
            match = _LINE_ID.match((row.get("id") or "").strip())
            if match:
                ids.setdefault(match.group(1), set()).add(row["id"].strip())
    if not ids:
        raise DocCheckError("no copy line ids found in copy/*.csv")
    return ids


def airtable_table_ids(root: Path) -> set:
    """The table ids CLAUDE.md declares. It is the authority on them."""
    path = root / "CLAUDE.md"
    if not path.is_file():
        return set()
    return set(_TBL_ID.findall(path.read_text(encoding="utf-8")))


def main_docstring(root: Path) -> str:
    path = root / "main.py"
    if not path.is_file():
        raise DocCheckError("main.py is missing")
    text = path.read_text(encoding="utf-8")
    end = text.find('"""', 3)
    return text[3:end] if text.startswith('"""') and end > 0 else ""


# ----------------------------------------------------------------- entry point


def check_docs(root: Path | None = None, *, parser=None) -> DocCheckResult:
    """Every drift class, over the whole corpus. Raises DocCheckError on exit 2.

    `parser` is passed in rather than imported so this module never depends on
    main.py — the dependency runs one way, and a test can drive it with a
    synthetic parser.
    """
    root = Path(root) if root else Path(__file__).resolve().parent.parent
    if parser is None:
        raise DocCheckError("no parser given")

    tree = command_tree(parser)
    ids = load_copy_ids(root)
    table_ids = airtable_table_ids(root)
    targets, skipped = scan_targets(root)

    result = DocCheckResult(skipped=skipped)
    corpus, pipeline_text, specs = [], "", 0

    for doc in targets:
        rel = doc.relative_to(root).as_posix()
        lines = read_doc(doc)
        result.scanned.append(rel)
        corpus.append("\n".join(lines))

        header = None
        if rel == PIPELINE_DOC:
            pipeline_text = "\n".join(lines)
        if rel.startswith(SPEC_DIR + "/"):
            specs += 1
            header, problems = check_header(rel, lines)
            result.findings.extend(problems)
            if header:
                result.findings.extend(
                    check_authorities(rel, doc, header, root, table_ids))
            result.findings.extend(check_prices(rel, lines, header))
            result.findings.extend(check_word_budget(rel, lines))

        result.findings.extend(check_commands(rel, lines, tree))
        result.findings.extend(check_paths(rel, doc, lines, root, header))
        result.findings.extend(check_copy_ids(rel, lines, ids))

    result.findings.extend(check_documented_commands(
        tree, pipeline_text, "\n".join(corpus), main_docstring(root)))

    result.counts = {
        "commands": len(tree),
        "apify": len(tree.get("apify", ())),
        "copy_ids": sum(len(v) for v in ids.values()),
        "specs": specs,
    }
    return result
