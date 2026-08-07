---
name: outbound-batch
description: Run a raw coach list end to end into a checked Smartlead upload file. Use whenever Haytham provides a CSV or other supported lead list, asks to run or process a list, build a batch, or make an upload file. This workflow may delegate its independent worker and verifier waves to the project custom agents. It never sends email.
---

# Codex adapter for the outbound batch

This is the Codex-discoverable entry point. The complete workflow is archived
at `docs/archive/outbound-batch-SKILL.md` pending the pivot plan on the
`pivot` branch — batch work against the old target market is paused.

Before taking any batch action:

1. Read `docs/archive/outbound-batch-SKILL.md` completely.
2. Read `AGENTS.md` and `CLAUDE.md`.
3. Follow the shared skill literally, with these host mappings:
   - use Codex project custom agents `research_worker`, `hook_worker`,
     `hook_verifier`, `draft_worker`, and `draft_verifier`;
   - use Codex web search/open tools for `WebSearch` and `WebFetch`;
   - use the shell for `Bash`, `rg` for `Grep`, and normal file tools for
     `Read` and `Write`;
   - `/clear` is supported by Codex and starts the fresh stage chat required by
     the workflow;
   - record Codex model names in `ledger pass`; do not relabel them as Claude
     tiers.
4. Keep all stage boundaries, tripwires, fail-closed gates, worker/verifier
   separation, artifact writes, and operator stops unchanged.

The skill explicitly authorizes subagents for its independent, bounded waves.
Fan out whole waves, wait for all members of a worker wave, then start the
separate verifier wave. Never let a worker verify its own result.

The machine ends at files. Never send, upload, log in as Haytham, or approve a
paid retrieval without the authorization required by the shared workflow.
