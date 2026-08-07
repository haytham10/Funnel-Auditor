# Running the outbound machine with Codex

Codex and Claude Code share the same Python engine, copy bank, business rules,
worker specifications, drafting references, and fail-closed gates. The host
adapters are deliberately thin so the two agent setups cannot drift.

## What maps where

| Concern | Shared or Claude location | Codex location |
|---|---|---|
| Repository instructions | `CLAUDE.md` | `AGENTS.md`, which requires the shared map |
| Batch workflow | `.claude/skills/outbound-batch/` | `.agents/skills/outbound-batch/` adapter |
| Single-email workflow | `.claude/skills/outbound-draft/` | `.agents/skills/outbound-draft/` adapter |
| Worker role prompts | `.claude/agents/*.md` | `.codex/agents/*.toml` adapters |
| Lifecycle configuration | `.claude/settings.json` | `.codex/hooks.json` |
| Hook implementations | `.claude/hooks/*.py` | shared directly |
| Runtime settings | Claude permissions | `.codex/config.toml` plus the user's active permission mode |
| Token accounting | Claude and Codex transcripts | `python main.py usage` |

The `.claude` role and skill files remain canonical because they contain the
long, evidence-backed operating rules. Codex's native files load those exact
specifications and only translate host tool names.

## First use

1. Open the repository root in Codex.
2. Review and trust the project hooks with `/hooks`. Codex re-prompts when a
   hook definition changes.
3. Run `/skills` and confirm `outbound-batch` and `outbound-draft` appear.
4. Ask Codex to summarize the active project instructions and confirm it names
   `AGENTS.md`.
5. Run the offline checks:

   ```bash
   .venv/bin/python main.py doc-check
   .venv/bin/python -m pytest -q
   ```

The optional Codex `/import` flow can import broader user-level Claude setup and
recent chats, but this repository does not depend on it. Everything required by
the project is checked in.

## Running work

For a list, explicitly invoke `$outbound-batch` or ask Codex to process the lead
file. The skill authorizes the worker/verifier subagent waves and names the five
project agents.

For one email or a repair, invoke `$outbound-draft`.

At a stage boundary, the shared workflow still uses `/clear`, followed by
`python main.py brief`. Codex supports `/clear`; it starts a fresh task in the
same repository while the batch state remains on disk.

## Important host differences

- Claude's `permissions.allow` list does not translate into a repository-level
  Codex allowlist. Codex uses the active permission mode and sandbox selected by
  the user. The repository preserves least privilege through narrow custom-agent
  roles and explicit behavioral boundaries, without silently broadening the
  user's machine permissions.
- Codex project hooks must be trusted before they run. Until they are trusted,
  the instructions and tests still apply, but session memory and the pre-push
  Airtable drift check are not automatic.
- Under Codex, `usage` reads token-count events from Codex session rollouts. It
  scopes automatic discovery to this repository and to sessions created since
  `work/BATCH`. An explicit `--transcripts` file or directory overrides that.
- Codex model names are recorded as themselves in `ledger pass` and usage
  artifacts. Historical Claude labels remain unchanged.

## External systems

Airtable remains the owner of live copy and CRM state. The repo can read it when
`AIRTABLE_API_KEY` is available; writing rows is still an explicit human-visible
action. Apify remains cost-gated. Smartlead remains outside the machine and owns
sending and replies.

No Codex plugin is required for the offline pipeline. The installed Airtable
connector can be used for user-authorized CRM work; the Python fallback continues
to work from `AIRTABLE_API_KEY`.
