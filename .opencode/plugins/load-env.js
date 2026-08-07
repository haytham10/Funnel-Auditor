// Loads the repo's .env into every shell execution, so the machine's Python
// commands always see AIRTABLE_API_KEY / APIFY_TOKEN / etc. without the caller
// having to source the file. Runs via the `shell.env` hook, which fires for
// AI tool calls and user terminals alike.
//
// Fails open, exactly like session-memory.js: a missing or unreadable .env
// means an empty env injection, never a blocked session. The plugin never
// logs or echoes the values it reads.

import { readFile } from "node:fs/promises"
import { join } from "node:path"

function parseDotEnv(text) {
  const env = {}
  for (const raw of text.split("\n")) {
    const line = raw.trim()
    if (!line || line.startsWith("#")) continue
    const body = line.startsWith("export ") ? line.slice(7).trim() : line
    const eq = body.indexOf("=")
    if (eq <= 0) continue
    let key = body.slice(0, eq).trim()
    let value = body.slice(eq + 1).trim()
    if (!key) continue
    const quote = value[0]
    if ((quote === '"' || quote === "'") && value.endsWith(quote)) {
      value = value.slice(1, -1)
    }
    env[key] = value
  }
  return env
}

export const LoadEnv = async ({ worktree, directory }) => {
  const root = worktree ?? directory
  let cached = null
  return {
    "shell.env": async (input, output) => {
      if (cached === null) {
        try {
          const text = await readFile(join(root, ".env"), "utf8")
          cached = parseDotEnv(text)
        } catch {
          cached = {}
        }
      }
      Object.assign(output.env, cached)
    },
  }
}
