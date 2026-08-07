// Mirror of .claude/hooks/session_memory.py for opencode.
//
// opencode has no SessionStart hook, so this plugin injects the same
// cross-session memory into every new session the same way: the newest journal
// entries plus the recent git history, capped so a long entry cannot flood
// context. It is the READ side only — it never writes, commits or pushes.
//
// Fails open, exactly like the Claude hook: any error here must never block a
// session from booting. Worst case is a session that starts cold.

import { readFile } from "node:fs/promises"
import { join } from "node:path"

const MAX_ENTRIES = 3
const MAX_JOURNAL_CHARS = 2000
const GIT_LOG_COUNT = 8

async function recentJournal(root) {
  try {
    const text = await readFile(join(root, "docs", "journal.md"), "utf8")
    const lines = text.split("\n")
    // Entries live below the `---` rule that closes the format preamble; the
    // preamble itself contains a fenced `## ` template that must NOT be read
    // as an entry. Anchor on the first standalone `---`, then take blocks.
    const sep = lines.findIndex((ln) => ln.trim() === "---")
    const body = sep >= 0 ? lines.slice(sep + 1) : lines
    const start = body.findIndex((ln) => ln.startsWith("## "))
    if (start < 0) return ""
    const kept = []
    let seen = 0
    for (const ln of body.slice(start)) {
      if (ln.startsWith("## ")) {
        seen += 1
        if (seen > MAX_ENTRIES) break
      }
      kept.push(ln)
    }
    let out = kept.join("\n").trim()
    if (out.length > MAX_JOURNAL_CHARS) {
      out = out.slice(0, MAX_JOURNAL_CHARS).trimEnd() +
        "\n… (truncated — see docs/journal.md)"
    }
    return out
  } catch {
    return ""
  }
}

async function recentCommits(root, $) {
  try {
    const { stdout } =
      await $`git -C ${root} log -${GIT_LOG_COUNT} --pretty=format:%h %ad %s --date=short`
    return String(stdout).trim()
  } catch {
    return ""
  }
}

export const SessionMemory = async ({ client, directory, worktree, $ }) => {
  const root = worktree ?? directory
  return {
    event: async ({ event }) => {
      if (event.type !== "session.created") return
      const sessionID = (event.properties || {}).sessionID
      if (!sessionID || !root) return

      const journal = await recentJournal(root)
      const commits = await recentCommits(root, $)
      if (!journal && !commits) return

      const text = [
        "PROJECT MEMORY (cross-session) — you start each session with no memory of prior ones; this is the recent narrative so you are not starting cold. Airtable holds live pipeline STATE (query the Outbound Machine base for where leads are); this is the story of what was done and decided. Full log: docs/journal.md. When you finish work worth remembering, add an entry at the top of that file and commit + push it.",
        journal && "Recent journal entries:\n" + journal,
        commits && "Recent commits:\n" + commits,
      ].filter(Boolean).join("\n\n")

      try {
        await client.session.prompt({
          path: { id: sessionID },
          body: {
            noReply: true,
            parts: [{ type: "text", text }],
          },
        })
      } catch (err) {
        try {
          await client.app.log({
            body: { service: "session-memory", level: "warn", message: String(err) },
          })
        } catch {
          // never throw — fail open
        }
      }
    },
  }
}
