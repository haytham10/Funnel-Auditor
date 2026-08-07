"""The agent bill, measured from Claude Code or Codex session transcripts.

`ledger pass` records that an agent ran. It cannot record what the agent cost,
because neither an orchestrator nor a worker can see its own token usage — so the
model side of this machine had a count and no magnitude. A pass can be 5k tokens
or 150k tokens and `passes_by_stage` reports both as `1`.

That gap is not academic. Forensics on `2026-08-02-q2` and `2026-08-02-q3` found
the two batches spent about 410M tokens producing 22 emails, and that **75% of it
was the orchestrator's own context** — a stage `ledger pass` has no record of at
all, because nobody thinks to report a pass for the thread they are typing in.
The batches reported 99 and 185 passes and both numbers were true and neither was
the answer.

The transcript can see all of it. Claude assistant records carry
`message.usage`; Codex rollouts carry cumulative and last-request token-count
events. Both hosts write subagent sessions separately, so the split between
coordination and work is measurable rather than arguable.

Three decisions worth not re-litigating.

**Deduplicate on `requestId`, keeping the last record.** A streaming response
emits several records per API call sharing one `requestId`, with `output_tokens`
growing across them. Counting records inflates the request count 2-4x; keeping
the *first* record per request undercounts output by about 4x. Both forensics
runs found this independently, and one of them found it only after reporting a
figure that was wrong by $4.

**Tokens, not dollars.** `ledger.record_pass` refuses a rate table on the grounds
that model prices are a value this repo does not own and would go stale in a file
nobody updates. That reasoning is right and it is about *prices*. A token count
is a measurement this repo does own, it never goes stale, and a reader who wants
dollars applies a rate the same way they do for any other input cost.

**A transcript this cannot parse is exit 2, naming what it saw.** The layout
belongs to the harness, not to this repo, and it can change under us. The
precedent is `replies`, which sniffs Smartlead's columns because nothing here has
ever seen a real export and refuses to report a zero rather than guess. A zero
here would read as "this batch used no agents", which is the wall's asymmetry in
a fourth costume. Like `ledger` and `metrics`, this never exits 1: an accounting
command that can halt a send file is one people learn to route around.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field, asdict
from datetime import date, datetime, timezone
from pathlib import Path

# Where the two supported hosts keep session transcripts. Neither layout is
# ours, which is why both are sniffed and overridable rather than assumed.
PROJECTS_DIR = Path("~/.claude/projects").expanduser()
CODEX_SESSIONS_DIR = Path(
    os.environ.get("CODEX_HOME", str(Path("~/.codex").expanduser()))
) / "sessions"

# The tools that spawn a subagent. Named so a third one cannot appear here
# without appearing in the map that gives an agent its type.
SPAWN_TOOLS = ("Task", "Agent")

# The result of a spawn names the agent it started. This is the only link
# between a `subagent_type` in the main transcript and an `agent-<id>.jsonl`
# beside it.
AGENT_ID = re.compile(r"agentId:\s*([0-9a-zA-Z_-]+)")

UNATTRIBUTED = "unattributed"

# --------------------------------------------------------------------- prices
#
# The one thing in this file that can go stale. `ledger.record_pass` refuses a
# rate table outright — "model prices are a value this repo does not own and
# would be a number going stale in a file nobody remembers to update". That is
# right about the failure mode and too strong about the remedy: the danger is
# not that a price is written down, it is that it goes wrong **silently**.
#
# It already did. The two 2026-08-02 forensics runs priced Sonnet 5
# differently — one used the introductory rate, one used list — so the combined
# figure quoted for days mixed two bases and was off by about 2%. Neither report
# was careless; nothing told either one which rate applied.
#
# So: every rate carries the date it was read, Sonnet 5's introductory rate
# carries the date it expires, and `price()` returns **None** once either has
# passed rather than a confident wrong number. The report then prints tokens and
# says why it could not price them. A figure that knows when to stop being
# trusted is the `?`-not-`0` rule applied to money.
RATES_AS_OF = date(2026, 6, 24)

# How long a rate card may go unrefreshed before it stops being quotable. Six
# months is longer than any intro window seen so far and short enough that a
# price change cannot sit unnoticed for a year.
RATES_STALE_AFTER_DAYS = 180

# Cache is priced off the base input rate: a write costs more than fresh input,
# a read costs a tenth. The 5m/1h split is not cosmetic — the orchestrator
# writes at the 1h tier and every subagent at 5m, and on the measured batches
# that split alone was ~30% of the bill.
CACHE_WRITE_5M = 1.25
CACHE_WRITE_1H = 2.0
CACHE_READ = 0.1

# USD per million tokens, base input and output. Everything else derives.
RATES = {
    "claude-opus-5": {"input": 5.00, "output": 25.00},
    "claude-sonnet-5": {
        "input": 3.00, "output": 15.00,
        # Introductory pricing, and the reason this whole mechanism exists.
        "intro": {"input": 2.00, "output": 10.00, "until": date(2026, 8, 31)},
    },
    "claude-opus-4-8": {"input": 5.00, "output": 25.00},
    "claude-haiku-4-5": {"input": 1.00, "output": 5.00},
}


def _today() -> date:
    return datetime.now(timezone.utc).date()


def _model_rate(model: str, on: date) -> dict | None:
    """Base input/output for one model on one date, or None if unknown."""
    card = RATES.get(model)
    if not card:
        return None
    intro = card.get("intro")
    if intro and on <= intro["until"]:
        return {"input": intro["input"], "output": intro["output"],
                "basis": f"{model} introductory rate, through {intro['until']}"}
    return {"input": card["input"], "output": card["output"],
            "basis": f"{model} list rate"}


def price(out: dict, *, on: date | None = None) -> dict:
    """Dollars for a summarised run, or the reason there are none.

    Returns `{"usd": float|None, "by_model": {...}, "basis": [...],
    "unpriceable": [...]}`. **`usd` is None whenever anything could not be
    priced** — a stale card, a model with no rate — rather than a total that
    quietly omits part of the run.
    """
    on = on or _today()
    result: dict = {"usd": None, "by_model": {}, "basis": [], "unpriceable": [],
                    "as_of": str(RATES_AS_OF), "priced_on": str(on)}

    stale_by = (on - RATES_AS_OF).days
    if stale_by > RATES_STALE_AFTER_DAYS:
        result["unpriceable"].append(
            f"the rate card was read {RATES_AS_OF} and is {stale_by} days old "
            f"(limit {RATES_STALE_AFTER_DAYS}) — refresh it from the "
            f"`claude-api` skill rather than quoting a price this may have "
            f"outlived. Tokens below are unaffected")
        return result

    total = 0.0
    for model, row in (out.get("by_model") or {}).items():
        rate = _model_rate(model, on)
        if not rate:
            result["unpriceable"].append(
                f"no rate on file for {model} — its tokens are counted and not "
                f"priced, so the total is withheld rather than made up")
            continue
        result["basis"].append(rate["basis"])
        result["by_model"][model] = {"tokens": row.get("tokens", 0)}

    if result["unpriceable"]:
        return result
    if not result["by_model"]:
        # Nothing to price is not a batch that cost nothing. Falling through
        # would sum an empty loop to $0.00 and print it beside exact token
        # counts, which is the wrong zero wearing the rate card's clothes.
        result["unpriceable"].append(
            "no model was named in the run, so there is nothing to price — "
            "tokens are still exact")
        return result

    # Bucket totals are run-wide, not per model. Attribute them by each model's
    # share of tokens — exact when one model dominates, which is every batch
    # measured so far, and honest about being a split when it is not.
    totals = out.get("totals") or {}
    grand = sum(r["tokens"] for r in result["by_model"].values()) or 1
    for model, row in result["by_model"].items():
        rate = _model_rate(model, on)
        share = row["tokens"] / grand
        cost = (
            totals.get("input_tokens", 0) * share * rate["input"]
            + totals.get("cache_write_5m", 0) * share * rate["input"] * CACHE_WRITE_5M
            + totals.get("cache_write_1h", 0) * share * rate["input"] * CACHE_WRITE_1H
            + totals.get("cache_read", 0) * share * rate["input"] * CACHE_READ
            + totals.get("output_tokens", 0) * share * rate["output"]
        ) / 1_000_000
        row["usd"] = round(cost, 2)
        total += cost

    result["usd"] = round(total, 2)
    return result


class TranscriptsUnreadable(Exception):
    """No transcript, or a shape this does not recognise. Always exit 2."""


def project_slug(cwd: str | Path | None = None) -> str:
    """The directory name Claude Code gives this project's transcripts.

    `/home/user/Outbound-Machine` becomes `-home-user-Outbound-Machine`: every
    character that is not alphanumeric or a hyphen becomes a hyphen, leading
    separator included.
    """
    raw = str(Path(cwd or Path.cwd()).resolve())
    return re.sub(r"[^A-Za-z0-9-]", "-", raw)


@dataclass
class Sources:
    """Which files were read, so a total can be argued with."""

    root: str = ""
    provider: str = "claude"
    main: list = field(default_factory=list)
    subagents: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return {"root": self.root,
                "provider": self.provider,
                "main": [str(p) for p in self.main],
                "subagents": [str(p) for p in self.subagents]}


def _session_meta(path: Path) -> dict:
    """The first Codex session metadata payload, or an empty dict."""
    try:
        for record in _lines(path):
            if record.get("type") == "session_meta":
                payload = record.get("payload")
                return payload if isinstance(payload, dict) else {}
            if record.get("type") in {"assistant", "user"}:
                return {}
    except OSError:
        return {}
    return {}


def _deep_named(value, names: set[str]):
    """First non-empty value under a named key in nested JSON."""
    if isinstance(value, dict):
        for key, item in value.items():
            if key in names and item not in (None, "", [], {}):
                return item
            found = _deep_named(item, names)
            if found not in (None, "", [], {}):
                return found
    elif isinstance(value, list):
        for item in value:
            found = _deep_named(item, names)
            if found not in (None, "", [], {}):
                return found
    return None


def _codex_agent(meta: dict) -> tuple[bool, str, str]:
    """Whether a Codex rollout is a subagent, plus its id and role."""
    source = meta.get("source")
    thread_source = meta.get("thread_source")
    joined = json.dumps({"source": source, "thread_source": thread_source},
                        default=str).lower()
    sidechain = "subagent" in joined
    agent_id = _deep_named(meta, {"agent_id", "agentId"})
    agent_type = _deep_named(meta, {"agent_type", "agentType", "subagent_type"})
    if sidechain and not agent_id:
        agent_id = meta.get("session_id") or meta.get("id") or ""
    return sidechain, str(agent_id or ""), str(agent_type or "")


def _codex_sources(base: Path, paths: list[Path]) -> Sources:
    main: list[Path] = []
    subagents: list[Path] = []
    for path in paths:
        sidechain, _, _ = _codex_agent(_session_meta(path))
        (subagents if sidechain else main).append(path)
    return Sources(root=str(base), provider="codex",
                   main=sorted(main), subagents=sorted(subagents))


def _discover_codex(cwd: str | Path | None = None) -> Sources:
    """Find Codex rollouts for this repo and current batch window."""
    base = CODEX_SESSIONS_DIR
    if not base.is_dir():
        raise TranscriptsUnreadable(f"no Codex session directory at {base}")

    resolved = str(Path(cwd or Path.cwd()).resolve())
    batch_marker = Path(resolved) / "work" / "BATCH"
    thread_id = os.environ.get("CODEX_THREAD_ID", "")
    since = batch_marker.stat().st_mtime if batch_marker.is_file() else None

    candidates: list[Path] = []
    for path in base.rglob("*.jsonl"):
        try:
            if since is not None and path.stat().st_mtime + 2 < since:
                continue
        except OSError:
            continue
        if since is None and thread_id and thread_id not in path.name:
            continue
        meta = _session_meta(path)
        meta_cwd = meta.get("cwd")
        try:
            same_cwd = str(Path(str(meta_cwd)).resolve()) == resolved
        except (OSError, TypeError, ValueError):
            same_cwd = False
        if same_cwd:
            candidates.append(path)

    if not candidates:
        window = (f"since {batch_marker}" if since is not None
                  else f"for thread {thread_id}" if thread_id
                  else "for the current repository")
        raise TranscriptsUnreadable(
            f"{base} holds no Codex rollout {window} with cwd {resolved}. "
            f"Pass --transcripts <file-or-directory> to name it explicitly")
    return _codex_sources(base, candidates)


def discover(root: str | Path | None = None,
             cwd: str | Path | None = None) -> Sources:
    """Find this session's transcripts. Raises `TranscriptsUnreadable`.

    `root` is the project directory itself when passed — a test points it at a
    fixture, and `--transcripts` points it at another session's directory when
    the layout moves.
    """
    if root:
        base = Path(root)
        paths = [base] if base.is_file() else sorted(base.rglob("*.jsonl"))
        codex_paths = [p for p in paths if _session_meta(p)]
        if codex_paths:
            return _codex_sources(base, codex_paths)
    elif os.environ.get("CODEX_THREAD_ID"):
        return _discover_codex(cwd)
    else:
        base = PROJECTS_DIR / project_slug(cwd)
    if not base.is_dir():
        raise TranscriptsUnreadable(
            f"no transcript directory at {base}. Transcripts live on the "
            f"agent host and may not survive its container — run `usage` "
            f"before the environment ends, or pass --transcripts <dir>")

    main = sorted(p for p in base.glob("*.jsonl") if p.is_file())
    subagents = sorted(base.glob("*/subagents/agent-*.jsonl"))
    if not main and not subagents:
        saw = sorted(p.name for p in base.iterdir())[:12]
        raise TranscriptsUnreadable(
            f"{base} holds no *.jsonl transcript and no */subagents/agent-*.jsonl. "
            f"Saw: {', '.join(saw) or '(empty)'}")
    return Sources(root=str(base), provider="claude",
                   main=main, subagents=subagents)


@dataclass
class Turn:
    """One billable API request. Not one record — see the module docstring."""

    request_id: str = ""
    model: str = ""
    at: str = ""
    sidechain: bool = False
    agent_id: str = ""
    agent_type: str = ""
    input_tokens: int = 0
    cache_write: int = 0
    cache_write_5m: int = 0
    cache_write_1h: int = 0
    cache_read: int = 0
    output_tokens: int = 0

    @property
    def total(self) -> int:
        return (self.input_tokens + self.cache_write + self.cache_read
                + self.output_tokens)


def _int(value) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _blocks(record: dict) -> list:
    content = (record.get("message") or {}).get("content")
    return [b for b in content if isinstance(b, dict)] if isinstance(content, list) else []


def _lines(path: Path):
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        try:
            data = json.loads(line)
        except ValueError:
            continue
        if isinstance(data, dict):
            yield data


def agent_types(main_paths: list) -> dict:
    """`agent-<id>.jsonl` -> the `subagent_type` it was spawned as.

    Recovered by pairing each spawn's `tool_use` with its `tool_result`, which
    is the only place the two identifiers meet. An agent whose spawn cannot be
    found is `unattributed` and says so — never folded into another type, and
    never dropped, because a missing attribution is a gap and not a zero.
    """
    spawned: dict = {}       # tool_use id -> subagent_type
    out: dict = {}           # agent id    -> subagent_type
    for path in main_paths:
        for record in _lines(path):
            for block in _blocks(record):
                kind = block.get("type")
                if kind == "tool_use" and block.get("name") in SPAWN_TOOLS:
                    label = (block.get("input") or {}).get("subagent_type")
                    if label:
                        spawned[block.get("id") or ""] = str(label)
                elif kind == "tool_result":
                    label = spawned.get(block.get("tool_use_id") or "")
                    if not label:
                        continue
                    body = block.get("content")
                    body = body if isinstance(body, str) else json.dumps(body)
                    found = AGENT_ID.search(body)
                    if found:
                        out[found.group(1)] = label
    return out


def read_turns(sources: Sources) -> list[Turn]:
    """Every billable request across every transcript, deduplicated.

    Records are deduplicated *within a file* on `requestId`, last one winning,
    because a streaming response repeats the id with a growing `output_tokens`.
    Across files the ids are already distinct.
    """
    if sources.provider == "codex":
        return _read_codex_turns(sources)

    types = agent_types(sources.main)
    turns: list[Turn] = []

    def harvest(path: Path, agent_id: str = "") -> None:
        seen: dict = {}
        order: list = []
        for record in _lines(path):
            if record.get("type") != "assistant":
                continue
            message = record.get("message") or {}
            usage = message.get("usage")
            if not isinstance(usage, dict):
                continue
            key = record.get("requestId") or f"{path.name}:{len(order)}"
            creation = usage.get("cache_creation")
            creation = creation if isinstance(creation, dict) else {}
            turn = Turn(
                request_id=str(key),
                model=str(message.get("model") or ""),
                at=str(record.get("timestamp") or ""),
                sidechain=bool(record.get("isSidechain") or agent_id),
                agent_id=agent_id or str(record.get("agentId") or ""),
                input_tokens=_int(usage.get("input_tokens")),
                cache_write=_int(usage.get("cache_creation_input_tokens")),
                cache_write_5m=_int(creation.get("ephemeral_5m_input_tokens")),
                cache_write_1h=_int(creation.get("ephemeral_1h_input_tokens")),
                cache_read=_int(usage.get("cache_read_input_tokens")),
                output_tokens=_int(usage.get("output_tokens")),
            )
            turn.agent_type = types.get(turn.agent_id, UNATTRIBUTED if turn.agent_id else "")
            if key not in seen:
                order.append(key)
            seen[key] = turn
        turns.extend(seen[k] for k in order)

    for path in sources.main:
        harvest(path)
    for path in sources.subagents:
        harvest(path, agent_id=path.stem[len("agent-"):])
    return turns


def _read_codex_turns(sources: Sources) -> list[Turn]:
    """Every Codex request from token-count events in selected rollouts."""
    turns: list[Turn] = []

    def harvest(path: Path, forced_sidechain: bool = False) -> None:
        meta = _session_meta(path)
        meta_sidechain, meta_agent_id, meta_agent_type = _codex_agent(meta)
        sidechain = forced_sidechain or meta_sidechain
        agent_id = meta_agent_id or (
            str(meta.get("session_id") or meta.get("id") or "") if sidechain else ""
        )
        agent_type = meta_agent_type or (UNATTRIBUTED if sidechain else "")
        model = ""
        index = 0
        for record in _lines(path):
            payload = record.get("payload")
            payload = payload if isinstance(payload, dict) else {}
            if record.get("type") == "turn_context":
                model = str(payload.get("model") or model)
                continue
            if payload.get("type") != "token_count":
                continue
            info = payload.get("info")
            info = info if isinstance(info, dict) else {}
            raw = info.get("last_token_usage")
            raw = raw if isinstance(raw, dict) else {}
            if not raw:
                continue
            index += 1
            input_total = _int(raw.get("input_tokens"))
            cache_read = _int(raw.get("cached_input_tokens"))
            cache_write = _int(raw.get("cache_write_input_tokens"))
            turns.append(Turn(
                request_id=f"{path.name}:{index}",
                model=model or str(meta.get("model") or ""),
                at=str(record.get("timestamp") or ""),
                sidechain=sidechain,
                agent_id=agent_id,
                agent_type=agent_type,
                input_tokens=max(0, input_total - cache_read - cache_write),
                cache_write=cache_write,
                cache_read=cache_read,
                output_tokens=_int(raw.get("output_tokens")),
            ))

    for path in sources.main:
        harvest(path)
    for path in sources.subagents:
        harvest(path, forced_sidechain=True)
    return turns


BUCKETS = ("input_tokens", "cache_write", "cache_read", "output_tokens")

# What a context is MADE OF, which is a different question from what it cost.
# `cache_read` is the sum of the context over every turn, so the way to shrink a
# bill is to shrink what sits in the context — and until this existed nothing
# here could say what that was.
#
# CLAUDE.md's rule was written from the true observation that ~two-thirds of the
# re-read is the orchestrator's own writing, and drew from it the fix "never
# narrate per lead". Measured on 2026-08-03: prose to the operator is **7%** of
# the context. Thinking blocks are 35% and the model's own tool CALLS are 28%.
# Cutting narration is cutting the smallest of the three.
BLOCK_KINDS = ("thinking", "tool_use", "text", "tool_result", "other")


def _block_kind(role: str, block: dict) -> str:
    kind = block.get("type") or "other"
    if kind in ("thinking", "redacted_thinking"):
        return "thinking"
    if kind in ("tool_use", "server_tool_use"):
        return "tool_use"
    if kind == "tool_result":
        return "tool_result"
    if kind == "text":
        # A user's own words are not something orchestration can economise on,
        # and folding them into `text` would make the operator look expensive.
        return "text" if role == "assistant" else "other"
    return "other"


def block_profile(sources: Sources, *, main_only: bool = True) -> dict:
    """What the context is made of, by block type, in characters.

    Characters rather than tokens on purpose: the transcript records no
    per-block token count, and a tokeniser here would be a second estimate
    dressed as a measurement. `chars_per_token` is stated once so the ratio is
    the reader's to adjust rather than something buried in a division.

    `main_only` because this is a question about the orchestrator. A subagent's
    context dies with the subagent and is already reported per agent.
    """
    paths = list(sources.main) if main_only else list(sources.main) + list(sources.subagents)
    counts = {k: 0 for k in BLOCK_KINDS}
    blocks = {k: 0 for k in BLOCK_KINDS}
    for path in paths:
        for record in _lines(path):
            if sources.provider == "codex":
                _profile_codex_record(record, counts, blocks)
                continue
            if record.get("isSidechain"):
                continue
            message = record.get("message") or {}
            role = message.get("role") or ""
            content = message.get("content")
            if isinstance(content, str):
                kind = _block_kind(role, {"type": "text"})
                counts[kind] += len(content)
                blocks[kind] += 1
            elif isinstance(content, list):
                for block in content:
                    if not isinstance(block, dict):
                        continue
                    kind = _block_kind(role, block)
                    counts[kind] += len(json.dumps(block, default=str))
                    blocks[kind] += 1
    total = sum(counts.values())
    return {"chars": counts, "blocks": blocks, "total_chars": total,
            "chars_per_token": 4,
            "share": {k: (counts[k] / total if total else 0.0) for k in BLOCK_KINDS}}


def _profile_codex_record(record: dict, counts: dict, blocks: dict) -> None:
    """Add one Codex response item to the approximate context composition."""
    if record.get("type") != "response_item":
        return
    payload = record.get("payload")
    if not isinstance(payload, dict):
        return
    kind = payload.get("type")
    if kind == "reasoning":
        bucket = "thinking"
    elif kind in {"function_call", "custom_tool_call", "local_shell_call",
                  "web_search_call"}:
        bucket = "tool_use"
    elif kind in {"function_call_output", "custom_tool_call_output",
                  "local_shell_call_output"}:
        bucket = "tool_result"
    elif kind == "message" and payload.get("role") == "assistant":
        bucket = "text"
    else:
        bucket = "other"
    counts[bucket] += len(json.dumps(payload, default=str))
    blocks[bucket] += 1


def _bucket_totals(turns: list) -> dict:
    out = {b: 0 for b in BUCKETS}
    out["cache_write_5m"] = 0
    out["cache_write_1h"] = 0
    out["requests"] = 0
    out["tokens"] = 0
    for turn in turns:
        for bucket in BUCKETS:
            out[bucket] += getattr(turn, bucket)
        out["cache_write_5m"] += turn.cache_write_5m
        out["cache_write_1h"] += turn.cache_write_1h
        out["requests"] += 1
        out["tokens"] += turn.total
    return out


def summarise(turns: list, *, batch: str = "", sources: Sources | None = None) -> dict:
    """Totals, and the three splits that answer where a batch went.

    `orchestrator` versus `subagents` is the split that matters most and the one
    `ledger pass` cannot express: it has no `kind` for the main thread, so the
    largest line item in a batch has never appeared in it.
    """
    main = [t for t in turns if not t.sidechain]
    subs = [t for t in turns if t.sidechain]

    by_model: dict = {}
    for turn in turns:
        name = turn.model or "unnamed"
        row = by_model.setdefault(name, {"requests": 0, "tokens": 0})
        row["requests"] += 1
        row["tokens"] += turn.total

    by_agent: dict = {}
    for turn in subs:
        name = turn.agent_type or UNATTRIBUTED
        row = by_agent.setdefault(name, {"agents": set(), "requests": 0, "tokens": 0})
        row["agents"].add(turn.agent_id)
        row["requests"] += 1
        row["tokens"] += turn.total
    by_agent = {k: {"agents": len(v["agents"]), "requests": v["requests"],
                    "tokens": v["tokens"]}
                for k, v in sorted(by_agent.items(),
                                   key=lambda kv: (-kv[1]["tokens"], kv[0]))}

    total = _bucket_totals(turns)
    out = {
        "batch": batch,
        "measured": True,
        "totals": total,
        "orchestrator": _bucket_totals(main),
        "subagents": _bucket_totals(subs),
        "by_model": dict(sorted(by_model.items(),
                                key=lambda kv: (-kv[1]["tokens"], kv[0]))),
        "by_agent": by_agent,
        "agents": len({t.agent_id for t in subs if t.agent_id}),
        "orchestrator_share": (round(_bucket_totals(main)["tokens"] / total["tokens"], 4)
                               if total["tokens"] else None),
        "sources": sources.to_dict() if sources else {},
        "gaps": [],
    }
    # What the context is made of, which is the only actionable half. The
    # totals say a batch was expensive; this says which kind of block to stop
    # putting in the loop. It re-reads the transcript rather than riding on
    # `turns` because a Turn is a billing record and carries no content.
    if sources is not None:
        try:
            out["blocks"] = block_profile(sources)
        except (OSError, ValueError) as exc:
            out["gaps"].append(f"could not profile the context blocks: {exc}")
    stray = by_agent.get(UNATTRIBUTED, {}).get("agents", 0)
    if stray:
        out["gaps"].append(
            f"{stray} subagent(s) could not be matched to a spawn, so their "
            f"tokens are counted but not attributed to an agent type")

    out["price"] = price(out)
    for reason in out["price"]["unpriceable"]:
        out["gaps"].append(reason)
    return out


def _n(value) -> str:
    return f"{int(value or 0):,}"


def headline(out: dict) -> str:
    """One line, for a checkpoint mid-run.

    A batch checkpoints this at every stage boundary so a container that dies
    mid-run still leaves its token accounting — the ledger's asymmetry applied
    to the model side. Eleven lines five times over is sixty lines of the
    orchestrator's own context spent watching itself, which would be a small
    version of the thing being measured.
    """
    total = out["totals"]
    share = out.get("orchestrator_share")
    return (f"USAGE {out.get('batch') or 'unlabelled'}: {_n(total['tokens'])} "
            f"token(s) over {_n(total['requests'])} request(s), "
            f"{'?' if share is None else f'{share * 100:.0f}%'} orchestrator "
            f"— MEASURED")


def report(out: dict) -> str:
    """The block a skill quotes. Every number here was measured, and says so."""
    total = out["totals"]
    main = out["orchestrator"]
    subs = out["subagents"]
    share = out.get("orchestrator_share")
    lines = [
        f"USAGE {out.get('batch') or 'unlabelled'}: {_n(total['requests'])} "
        f"request(s), {_n(total['tokens'])} token(s) — MEASURED",
        f"  orchestrator      {_n(main['tokens'])} "
        f"({'?' if share is None else f'{share * 100:.0f}%'}) over "
        f"{_n(main['requests'])} request(s)",
        f"  subagents         {_n(subs['tokens'])} over {_n(subs['requests'])} "
        f"request(s) across {out['agents']} agent(s)",
        f"  cache_read        {_n(total['cache_read'])}",
        f"  cache_write       {_n(total['cache_write'])} "
        f"({_n(total['cache_write_5m'])} at 5m, {_n(total['cache_write_1h'])} at 1h)",
        f"  input             {_n(total['input_tokens'])}",
        f"  output            {_n(total['output_tokens'])}",
    ]
    profile = out.get("blocks")
    if profile and profile.get("total_chars"):
        per = profile["chars_per_token"]
        lines.append(f"  context is made of (~{_n(profile['total_chars'] // per)} "
                     f"tokens of orchestrator transcript, ~{per} chars/token):")
        for kind in sorted(BLOCK_KINDS, key=lambda k: -profile["chars"][k]):
            chars = profile["chars"][kind]
            if not chars:
                continue
            lines.append(f"    {kind:<12} {_n(chars // per):>10} "
                         f"({profile['share'][kind] * 100:4.1f}%) over "
                         f"{_n(profile['blocks'][kind])} block(s)")
        lines.append("    cache_read is the SUM of this over every turn, so it "
                     "falls with BOTH a smaller context and fewer turns")
    if out["by_model"]:
        lines.append("  by_model          " + ", ".join(
            f"{k} {_n(v['tokens'])}" for k, v in out["by_model"].items()))
    if out["by_agent"]:
        lines.append("  by_agent          " + ", ".join(
            f"{k} {v['agents']}x {_n(v['tokens'])}"
            for k, v in out["by_agent"].items()))
    # Money last, and only when it can be stated with its basis. A dollar
    # figure whose rate card has expired is worse than none: it looks measured.
    money = out.get("price") or {}
    if money.get("usd") is not None:
        lines.append(f"  cost              ${money['usd']:,.2f} "
                     f"(rates as of {money['as_of']})")
        for basis in money.get("basis") or []:
            lines.append(f"                    {basis}")
        lines.append("                    equivalent list cost, not an "
                     "invoice — a subscription bills differently")
    elif money:
        lines.append("  cost              ? — tokens above are exact; see GAP")
    for gap in out.get("gaps") or []:
        lines.append(f"  GAP  {gap}")
    lines.append("  MEASURED from the session transcript, not reported by an "
                 "agent — the one number here that `ledger pass` cannot see is "
                 "the orchestrator, and it is usually the largest.")
    lines.append("  OBSERVER. This never fails a batch.")
    return "\n".join(lines)


def write_artifact(out: dict, path: str | Path) -> Path:
    """Persist it beside the ledger; this is the portable part of a transcript."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return target
