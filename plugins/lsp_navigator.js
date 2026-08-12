import { tool } from "@opencode-ai/plugin";

/**
 * lsp_navigator — AST-exact code navigation for agents, backed by opencode's
 * OWN language servers.
 *
 * Design rationale (see build blueprint Item 2):
 *   opencode already runs and manages LSP servers itself — warm, per-project,
 *   and incrementally updated on its own lifecycle. Rather than spawn our own
 *   language-server processes (which would duplicate that work and its memory
 *   across parallel projects), this plugin simply QUERIES opencode's warm LSP
 *   through the SDK client handed to plugins via PluginInput. No daemon, no
 *   alias, no lifecycle coupling.
 *
 * Capabilities exposed (bounded by what opencode's API actually offers):
 *   - action "symbols":    LSP workspace-symbol search by name. Returns the
 *                          definition location(s) of functions/classes/vars —
 *                          the "where do I edit this?" trace agents need,
 *                          without reading whole files. (client.find.symbols)
 *   - action "status":     Which LSP servers opencode has running for this
 *                          project and their health. (client.lsp.status)
 *   - action "diagnostics": Best-effort. opencode's API only emits a change
 *                          NOTIFICATION ({serverID, path}) when a file's
 *                          diagnostics update — it does NOT expose the
 *                          diagnostic messages/severities. So this reports
 *                          which files the LSP has flagged recently, not their
 *                          contents. Documented honestly below.
 *
 * NOTE: cursor-position goto-definition / find-references are intentionally
 * NOT implemented — opencode's public API exposes no endpoint for them. Symbol
 * search (by name) is the available and, for name-aware agents, more directly
 * useful primitive.
 *
 * Prerequisite: language servers must be available to opencode via the `lsp`
 * block in opencode.jsonc, e.g.:
 *   "lsp": {
 *     "pyright": { "command": ["pyright-langserver", "--stdio"], "extensions": [".py"] },
 *     "typescript": { "command": ["typescript-language-server", "--stdio"], "extensions": [".ts", ".tsx", ".js"] }
 *   }
 * (opencode may also ship built-in defaults for common languages.)
 */

// LSP SymbolKind (1..26) -> human-readable name (LSP spec §Symbol Kinds).
const SYMBOL_KINDS = {
  1: "File",
  2: "Module",
  3: "Namespace",
  4: "Package",
  5: "Class",
  6: "Method",
  7: "Property",
  8: "Field",
  9: "Constructor",
  10: "Enum",
  11: "Interface",
  12: "Function",
  13: "Variable",
  14: "Constant",
  15: "String",
  16: "Number",
  17: "Boolean",
  18: "Array",
  19: "Object",
  20: "Key",
  21: "Null",
  22: "EnumMember",
  23: "Struct",
  24: "Event",
  25: "Operator",
  26: "TypeParameter",
};

export function _symbolKindName(kind) {
  return SYMBOL_KINDS[kind] || `Kind(${kind})`;
}

/** Convert an LSP file URI (file:///c:/foo/bar.py) to a filesystem path. */
export function _uriToPath(uri) {
  if (typeof uri !== "string") return String(uri ?? "");
  if (!uri.startsWith("file:")) return uri;
  try {
    let p = decodeURIComponent(new URL(uri).pathname);
    // On Windows the pathname is "/C:/..."; strip the leading slash.
    if (/^\/[A-Za-z]:\//.test(p)) p = p.slice(1);
    return p;
  } catch {
    return uri;
  }
}

/** Shape one LSP Symbol into a compact, agent-friendly record (1-indexed). */
export function _formatSymbol(sym) {
  const loc = sym.location || {};
  const range = loc.range || {};
  const start = range.start || {};
  const end = range.end || {};
  return {
    name: sym.name,
    kind: _symbolKindName(sym.kind),
    file: _uriToPath(loc.uri),
    // LSP positions are 0-indexed; present them 1-indexed for humans/agents.
    line: typeof start.line === "number" ? start.line + 1 : null,
    character: typeof start.character === "number" ? start.character + 1 : null,
    endLine: typeof end.line === "number" ? end.line + 1 : null,
  };
}

/** Unwrap a HeyApi RequestResult ({ data, error }) or a raw array. */
function _unwrap(res) {
  if (res && typeof res === "object" && "data" in res) {
    if (res.error) {
      throw new Error(
        typeof res.error === "string" ? res.error : JSON.stringify(res.error),
      );
    }
    return res.data;
  }
  return res;
}

// Injected into the system prompt every turn via chat.system.transform. Unlike
// AGENTS.md (which can scroll out of context or be dropped on compaction), the
// system prompt is re-sent on every request, so this hint stays reliably in
// front of the agent for the whole task. Keep it terse — it costs tokens each
// turn.
const TOOLS_NOTE = [
  "[Additional workspace tools]",
  "Prefer these over ad-hoc grep or reading whole files:",
  '- lsp_navigator: AST-exact symbol tracing via opencode\'s own LSP. Use action "symbols" with a symbol name to get its definition file:line before editing shared code; "status" to list running LSP servers; "diagnostics" for recently-flagged files. (Read a source file once first so the language server is warm.)',
  "- codebase_search: fast, structured cross-file string/regex search (ripgrep-backed, result-capped). Use instead of shelling out to grep/rg to avoid context overflow.",
].join("\n");

const LspNavigatorPlugin = async (input) => {
  const { client } = input;

  // In-memory record of diagnostic-change notifications, keyed by file path.
  // opencode does not expose diagnostic contents, only that `path` changed.
  const diagnosticsByPath = new Map();
  let diagSeq = 0;

  async function doSymbols(args, context) {
    if (!args.query) {
      return JSON.stringify({
        error: "action 'symbols' requires a `query` (symbol name to search).",
      });
    }
    const res = await client.find.symbols({
      query: { query: args.query, directory: context?.directory },
    });
    const symbols = _unwrap(res) || [];
    const limit = args.limit && args.limit > 0 ? args.limit : 50;
    const formatted = symbols.slice(0, limit).map(_formatSymbol);
    return JSON.stringify(
      {
        action: "symbols",
        query: args.query,
        count: formatted.length,
        truncated: symbols.length > formatted.length,
        symbols: formatted,
      },
      null,
      2,
    );
  }

  async function doStatus() {
    const res = await client.lsp.status();
    const servers = _unwrap(res) || [];
    return JSON.stringify(
      {
        action: "status",
        servers: servers.map((s) => ({
          id: s.id,
          name: s.name,
          root: s.root,
          status: s.status,
        })),
      },
      null,
      2,
    );
  }

  function doDiagnostics(args) {
    let entries = [...diagnosticsByPath.values()];
    if (args.filePath) {
      const want = args.filePath.replace(/\\/g, "/").toLowerCase();
      entries = entries.filter((e) =>
        e.path.replace(/\\/g, "/").toLowerCase().includes(want),
      );
    }
    entries.sort((a, b) => b.lastSeq - a.lastSeq);
    return JSON.stringify(
      {
        action: "diagnostics",
        note:
          "opencode's API exposes diagnostic CHANGE NOTIFICATIONS only, not the " +
          "messages/severities. This lists files the LSP flagged recently; open " +
          "the file to see the actual diagnostics opencode surfaces inline.",
        count: entries.length,
        files: entries.map((e) => ({
          path: e.path,
          serverID: e.serverID,
          updates: e.count,
        })),
      },
      null,
      2,
    );
  }

  return {
    // Reliably surface the workspace tools to the agent every turn (survives
    // compaction / long tasks better than AGENTS.md).
    "experimental.chat.system.transform": async (_input, output) => {
      if (output && Array.isArray(output.system)) {
        output.system.push(TOOLS_NOTE);
      }
    },

    // Maintain the diagnostics activity map from opencode's LSP events.
    event: async ({ event }) => {
      if (event?.type === "lsp.client.diagnostics") {
        const { path, serverID } = event.properties || {};
        if (path) {
          const prev = diagnosticsByPath.get(path);
          diagnosticsByPath.set(path, {
            path,
            serverID,
            count: (prev?.count || 0) + 1,
            lastSeq: ++diagSeq,
          });
        }
      }
    },

    tool: {
      lsp_navigator: tool({
        description:
          "AST-exact code navigation backed by opencode's own LSP servers. " +
          "Use `symbols` to trace where a function/class/variable is defined " +
          "(returns file:line without reading whole files); `status` to list " +
          "running LSP servers; `diagnostics` to see which files the LSP " +
          "flagged recently.",
        args: {
          action: tool.schema
            .enum(["symbols", "status", "diagnostics"])
            .describe("Navigation action"),
          query: tool.schema
            .string()
            .optional()
            .describe("Symbol name to search (required for action 'symbols')"),
          filePath: tool.schema
            .string()
            .optional()
            .describe("Filter diagnostics to files matching this path"),
          limit: tool.schema
            .number()
            .optional()
            .describe("Max symbols to return (default 50)"),
        },
        async execute(args, context) {
          try {
            switch (args.action) {
              case "symbols":
                return await doSymbols(args, context);
              case "status":
                return await doStatus();
              case "diagnostics":
                return doDiagnostics(args);
              default:
                return JSON.stringify({
                  error: `Unknown action: ${args.action}`,
                });
            }
          } catch (err) {
            return JSON.stringify({
              error: `lsp_navigator failed: ${err?.message ?? String(err)}`,
            });
          }
        },
      }),
    },
  };
};

export default LspNavigatorPlugin;
export const server = LspNavigatorPlugin;
