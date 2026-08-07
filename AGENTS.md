# The outbound machine: Codex instructions

`CLAUDE.md` is the full operational map for this repository. Read it before
changing pipeline behavior or running a live batch. The name is historical:
its business rules, safety boundaries, gate semantics, and documentation rules
apply to every agent host, including Codex.

For orientation, read `docs/START-HERE.md`. For authoritative business and
pipeline contracts, start at `docs/spec/00-index.md`. Module docstrings explain
the reasoning behind individual commands.

## Non-negotiable boundaries

- The machine ends at files in `out/`. Never send email. Haytham uploads to
  Smartlead himself.
- Never log in to, act as, or automate through Haytham's accounts. Public,
  read-only, no-login retrieval is allowed.
- Never invent a hook, channel, source, number, or attribution. No evidence is
  a valid null result.
- Run dedupe before any paid call. A warm-thread hit stops the run.
- No agent certifies its own consequential claim. Use the worker/verifier
  chassis in `docs/agent-orchestration.md`.
- Read `out/preview.txt` in full before any upload.
- Do not commit, push, write to Airtable, approve paid retrieval, or perform an
  upload unless the current user request authorizes that action.

## Development workflow

- Use the repository virtual environment when it exists:
  `.venv/bin/python main.py ...` and `.venv/bin/python -m pytest ...`.
- Every CLI command is a decision and prints a literal line to quote. Exit 0 is
  pass, 1 is a checked failure, 2 means the check could not run, and 3 requests
  cost approval. Never turn exit 2 into a pass.
- After code changes, run:

  ```bash
  .venv/bin/python main.py doc-check
  .venv/bin/python -m pytest -q
  ```

- If pytest's capture layer is unavailable in the host, retry with
  `.venv/bin/python -m pytest -q -s` and report the environment issue.
- A command change requires a matching update to
  `docs/spec/05-pipeline.md`. `doc-check` enforces the code/document boundary.
- Preserve unrelated working-tree changes. Do not create commits or push unless
  asked.

## Codex-native workflows

Repository skills are exposed from `.agents/skills/`. Use `outbound-batch` for
a list and `outbound-draft` for one email or a repair. Those adapters point to
the full specifications in `.claude/skills/`, which remain shared with Claude
Code.

Project custom agents live in `.codex/agents/`:

- `research_worker`
- `hook_worker`
- `hook_verifier`
- `draft_worker`
- `draft_verifier`

The top-level `outbound-batch` skill explicitly authorizes subagent use for its
worker/verifier waves. Outside that workflow, do not delegate unless the user
or another applicable instruction requests it.

Codex lifecycle hooks are configured in `.codex/hooks.json` and reuse the
Python implementations in `.claude/hooks/`. On first use, review and trust the
project hooks with `/hooks`. The hooks load recent project memory, fingerprint
the shared skills, and check Airtable select-schema drift before a push.

`python main.py usage` supports both Claude Code and Codex transcripts. Under
Codex it discovers sessions for this repository since `work/BATCH` was written;
use `--transcripts <file-or-directory>` to override discovery.
