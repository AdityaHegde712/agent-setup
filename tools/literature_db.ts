import { tool } from "@opencode-ai/plugin";
import { execFile } from "node:child_process";
import { promisify } from "node:util";
import * as path from "node:path";

const execFileAsync = promisify(execFile);

/**
 * Query and manage the local LanceDB literature database.
 *
 * The heavy lifting lives in `scripts/literature_db.py`, which declares its
 * dependencies (lancedb, fastembed, flashrank, pyarrow) via PEP 723 inline
 * metadata. We therefore invoke it with `uv run --script`, which resolves those
 * dependencies into an isolated environment and ignores the surrounding
 * project's pyproject.toml. Arguments are passed as an array via `execFile`
 * (no shell) so queries and JSON metadata survive Windows `cmd.exe` quoting.
 */
export default tool({
  description:
    "Query and manage the local LanceDB literature database with FlashRank re-ranking for large (200+ paper) research sessions.",
  args: {
    action: tool.schema
      .enum(["search", "insert", "index_pdf", "init"])
      .describe("Database action"),
    query: tool.schema
      .string()
      .optional()
      .describe("Search query for literature research"),
    topK: tool.schema
      .number()
      .optional()
      .describe("Number of candidates to retrieve before re-ranking (default 20)"),
    filePath: tool.schema
      .string()
      .optional()
      .describe("Path to a paper Markdown/text file for indexing"),
    jsonFile: tool.schema
      .string()
      .optional()
      .describe("Path to a JSON file of paper(s) to insert"),
    metadataJson: tool.schema
      .string()
      .optional()
      .describe("JSON string of paper metadata (used with filePath)"),
  },
  async execute({ action, query, topK, filePath, jsonFile, metadataJson }) {
    const globalConfigDir = "c:/Users/hifia/.config/opencode";
    const scriptPath = path.join(globalConfigDir, "scripts", "literature_db.py");

    const args: string[] = ["run", "--script", scriptPath, action];

    if (query) args.push("--query", query);
    if (topK) {
      args.push("--top_k", String(topK));
      args.push("--rerank");
    } else if (action === "search") {
      // Default to re-ranking for search unless topK explicitly omitted intent.
      args.push("--rerank");
    }
    if (jsonFile) args.push("--json_file", jsonFile);
    if (filePath) args.push("--file_path", filePath);
    if (metadataJson) args.push("--metadata", metadataJson);

    try {
      const { stdout } = await execFileAsync("uv", args, {
        cwd: globalConfigDir,
        maxBuffer: 32 * 1024 * 1024,
      });
      return stdout.trim();
    } catch (err: any) {
      return JSON.stringify({
        error: `literature_db execution failed: ${err?.message ?? String(err)}`,
        stderr: err?.stderr ?? undefined,
      });
    }
  },
});
