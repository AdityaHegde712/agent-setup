import fs from "fs";
import path from "path";

// How many recent episodes to stitch into working memory each LLM turn.
const EPISODES_TO_LOAD = 3;

// Pure INSTRUCTION for opencode's own compaction agent. opencode feeds the
// delta transcript (messages since the last compaction) as prior model
// messages, then appends this as the final user turn. Do NOT append the
// transcript here.
const COMPACTION_PROMPT_TEMPLATE = `Summarize the conversation so far into the exact Markdown structure inside <template>. Keep the section order unchanged. Do not include the <template> tags in your response.
<template>
## Goal
- [single-sentence task summary]

## Constraints & Preferences
- [user constraints, preferences, specs, or "(none)"]

## Progress
### Done
- [completed work or "(none)"]

### In Progress
- [current work or "(none)"]

### Blocked
- [blockers or "(none)"]

## Key Decisions
- [decision and why, or "(none)"]

## Next Steps
- [ordered next actions or "(none)"]

## Critical Context
- [important technical facts, errors, open questions, or "(none)"]

## Relevant Files
- [file or directory path: why it matters, or "(none)"]
</template>

Rules:
- Keep every section, even when empty.
- Use terse bullets, not prose paragraphs.
- Preserve exact file paths, commands, error strings, and identifiers when known.
- Do not mention the summary process or that context was compacted.`;

function compDirFor(baseDir, sessionID) {
  return path.join(baseDir, ".compactions", sessionID.slice(-8));
}

// Log to the workspace .compactions dir (editable), never the config dir.
function logError(baseDir, msg) {
  try {
    const dir = path.join(baseDir, ".compactions");
    fs.mkdirSync(dir, { recursive: true });
    fs.appendFileSync(
      path.join(dir, "plugin-error.log"),
      `[${new Date().toISOString()}] ${msg}\n`,
      "utf8",
    );
  } catch (e) {
    console.error("compaction-backup: failed to write log:", e);
  }
}

// Highest existing episode index in a compaction dir (0 if none).
function maxEpisode(compDir) {
  if (!fs.existsSync(compDir)) return 0;
  let maxN = 0;
  for (const file of fs.readdirSync(compDir)) {
    const match = file.match(/^episode_(\d+)\.md$/);
    if (match) {
      const num = parseInt(match[1], 10);
      if (num > maxN) maxN = num;
    }
  }
  return maxN;
}

// Concatenate text parts of a message the way opencode derives its summary.
function textOf(message) {
  return (message?.parts || [])
    .filter((p) => p.type === "text")
    .map((p) => (p.text || "").trim())
    .filter(Boolean)
    .join("\n\n")
    .trim();
}

export const CompactionBackupPlugin = async (input, _options) => {
  const runtime = input || {};
  const client = runtime.client;
  const baseDir = runtime.directory || process.cwd() || ".";

  if (!client) {
    logError(baseDir, "Plugin initialized without a client reference.");
    return {};
  }

  return {
    // Fires BEFORE opencode generates the summary. We only replace the prompt
    // so opencode's own compaction call emits our structured episode. opencode
    // already feeds the delta (messages since the last compaction) as context.
    "experimental.session.compacting": async (_input, output) => {
      try {
        if (output) output.prompt = COMPACTION_PROMPT_TEMPLATE;
      } catch (err) {
        logError(baseDir, `compacting hook error: ${err.stack || err.message}`);
      }
    },

    // Fires AFTER compaction persists. Capture opencode's generated summary
    // (the newest completed summary assistant message) and save it as the next
    // episode on disk.
    event: async (evt) => {
      try {
        const event = evt?.event;
        if (!event || event.type !== "session.compacted") return;
        const sessionID = event.properties?.sessionID;
        if (!sessionID) {
          logError(baseDir, "compacted event: missing sessionID");
          return;
        }

        const res = await client.session.messages({
          path: { id: sessionID },
          query: { directory: baseDir },
        });
        if (res?.error) {
          logError(baseDir, `messages error: ${JSON.stringify(res.error)}`);
          return;
        }
        const messages = res?.data || [];

        // Newest completed compaction summary (assistant, summary:true).
        let summaryMsg;
        for (let i = messages.length - 1; i >= 0; i--) {
          const info = messages[i]?.info;
          if (
            info?.role === "assistant" &&
            info?.summary === true &&
            info?.finish &&
            !info?.error
          ) {
            summaryMsg = messages[i];
            break;
          }
        }
        if (!summaryMsg) {
          logError(baseDir, "compacted event: no summary message found");
          return;
        }

        const summaryText = textOf(summaryMsg);
        if (!summaryText) {
          logError(baseDir, "compacted event: summary text empty");
          return;
        }

        const compDir = compDirFor(baseDir, sessionID);
        fs.mkdirSync(compDir, { recursive: true });

        // Idempotency: don't rewrite an identical episode if the event repeats.
        const maxN = maxEpisode(compDir);
        if (maxN > 0) {
          const latest = fs
            .readFileSync(path.join(compDir, `episode_${maxN}.md`), "utf8")
            .trim();
          if (latest === summaryText) return;
        }

        fs.writeFileSync(
          path.join(compDir, `episode_${maxN + 1}.md`),
          summaryText,
          "utf8",
        );
      } catch (err) {
        logError(baseDir, `event hook error: ${err.stack || err.message}`);
      }
    },

    // Fires each time messages are assembled for the LLM. Replace the stored
    // single summary the model sees with the last N episodes, so the model
    // gets rolling history (opencode's tail_turns already keeps recent turns
    // verbatim, and the current message is always included).
    "experimental.chat.messages.transform": async (_input, output) => {
      try {
        if (!output || !output.messages) return;

        for (const message of output.messages) {
          const info = message?.info;
          if (!info || info.role !== "assistant" || info.summary !== true)
            continue;

          const sessionID = info.sessionID;
          if (!sessionID) continue;

          const compDir = compDirFor(baseDir, sessionID);
          const maxN = maxEpisode(compDir);
          if (maxN === 0) continue;

          const from = Math.max(1, maxN - EPISODES_TO_LOAD + 1);
          const nums = [];
          for (let n = from; n <= maxN; n++) nums.push(n);

          let block = `# Episodic Memory (most recent ${nums.length} episode${nums.length === 1 ? "" : "s"})\n\n`;
          for (const n of nums) {
            const fp = path.join(compDir, `episode_${n}.md`);
            if (fs.existsSync(fp)) {
              block += `## Episode ${n}\n${fs.readFileSync(fp, "utf8")}\n\n`;
            }
          }

          // Non-mutative: preserve part order + metadata (signed reasoning must
          // stay adjacent). First text part carries the block; blank the rest.
          const parts = message.parts || [];
          const hasText = parts.some((p) => p.type === "text");
          if (hasText) {
            let injected = false;
            message.parts = parts.map((p) => {
              if (p.type !== "text") return p;
              if (!injected) {
                injected = true;
                return { ...p, text: block };
              }
              return { ...p, text: "" };
            });
          } else {
            message.parts = [...parts, { type: "text", text: block }];
          }
        }
      } catch (err) {
        logError(baseDir, `transform hook error: ${err.stack || err.message}`);
      }
    },
  };
};

export default CompactionBackupPlugin;
export const server = CompactionBackupPlugin;
