"""The Claude bill, measured from the session transcript rather than reported.

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

The transcript can see all of it. Every assistant record carries
`message.usage`, and every subagent gets its own file, so the split between
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
from pathlib import Path

# Where Claude Code keeps a session's transcripts. Not ours, which is why it is
# sniffed and overridable rather than assumed.
PROJECTS_DIR = Path("~/.claude/projects").expanduser()

# The tools that spawn a subagent. Named so a third one cannot appear here
# without appearing in the map that gives an agent its type.
SPAWN_TOOLS = ("Task", "Agent")

# The result of a spawn names the agent it started. This is the only link
# between a `subagent_type` in the main transcript and an `agent-<id>.jsonl`
# beside it.
AGENT_ID = re.compile(r"agentId:\s*([0-9a-zA-Z_-]+)")

UNATTRIBUTED = "unattributed"


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
    main: list = field(default_factory=list)
    subagents: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return {"root": self.root,
                "main": [str(p) for p in self.main],
                "subagents": [str(p) for p in self.subagents]}


def discover(root: str | Path | None = None,
             cwd: str | Path | None = None) -> Sources:
    """Find this session's transcripts. Raises `TranscriptsUnreadable`.

    `root` is the project directory itself when passed — a test points it at a
    fixture, and `--transcripts` points it at another session's directory when
    the layout moves.
    """
    base = Path(root) if root else PROJECTS_DIR / project_slug(cwd)
    if not base.is_dir():
        raise TranscriptsUnreadable(
            f"no transcript directory at {base}. Transcripts live on the "
            f"session's own container and do not survive it — run `usage` "
            f"before the session ends, or pass --transcripts <dir>")

    main = sorted(p for p in base.glob("*.jsonl") if p.is_file())
    subagents = sorted(base.glob("*/subagents/agent-*.jsonl"))
    if not main and not subagents:
        saw = sorted(p.name for p in base.iterdir())[:12]
        raise TranscriptsUnreadable(
            f"{base} holds no *.jsonl transcript and no */subagents/agent-*.jsonl. "
            f"Saw: {', '.join(saw) or '(empty)'}")
    return Sources(root=str(base), main=main, subagents=subagents)


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


BUCKETS = ("input_tokens", "cache_write", "cache_read", "output_tokens")


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
    stray = by_agent.get(UNATTRIBUTED, {}).get("agents", 0)
    if stray:
        out["gaps"].append(
            f"{stray} subagent(s) could not be matched to a spawn, so their "
            f"tokens are counted but not attributed to an agent type")
    return out


def _n(value) -> str:
    return f"{int(value or 0):,}"


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
    if out["by_model"]:
        lines.append("  by_model          " + ", ".join(
            f"{k} {_n(v['tokens'])}" for k, v in out["by_model"].items()))
    if out["by_agent"]:
        lines.append("  by_agent          " + ", ".join(
            f"{k} {v['agents']}x {_n(v['tokens'])}"
            for k, v in out["by_agent"].items()))
    for gap in out.get("gaps") or []:
        lines.append(f"  GAP  {gap}")
    lines.append("  MEASURED from the session transcript, not reported by an "
                 "agent — the one number here that `ledger pass` cannot see is "
                 "the orchestrator, and it is usually the largest.")
    lines.append("  OBSERVER. This never fails a batch.")
    return "\n".join(lines)


def write_artifact(out: dict, path: str | Path) -> Path:
    """Persist it beside the ledger. A transcript dies with its container; this
    is the only part of it that outlives the session."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return target
