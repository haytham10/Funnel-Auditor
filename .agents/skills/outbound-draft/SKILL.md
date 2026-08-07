---
name: outbound-draft
description: Write, review, or repair one cold email in Haytham's voice. Use whenever Haytham asks to draft one email, rewrite or tighten a draft, fix a beat, asks how a draft reads, or pastes a draft for review. Use outbound-batch for a whole list. Never sends email.
---

# Codex adapter for one email

The complete and authoritative workflow is
`.claude/skills/outbound-draft/SKILL.md`.

Before writing or reviewing:

1. Read that `SKILL.md` completely.
2. Read every reference it requires from
   `.claude/skills/outbound-draft/references/`.
3. Read the relevant hand-written lines from `copy/`.
4. Follow the shared workflow literally. Use the shell for its Python gates and
   quote the literal PASS line.

For a fresh draft, use the project `draft_worker` and an independent
`draft_verifier` when the workflow calls for a cold read. For a diagnosis-only
request, inspect and report without changing or sending anything.

Never invent a hook or number, never quote a price, and never send email.
