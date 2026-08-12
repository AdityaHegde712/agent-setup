import { tool } from "@opencode-ai/plugin";
import { execFile } from "node:child_process";
import { promisify } from "node:util";

const execFileAsync = promisify(execFile);

/**
 * Fast, structured cross-file search across workspace directories.
 *
 * Implementation notes:
 *  - Uses `execFile` with an argument array (no shell) so the query, globs and
 *    paths are passed verbatim. This avoids `cmd.exe` quoting pitfalls on
 *    Windows and shell-injection issues on any platform.
 *  - Uses `rg --json` and parses the structured event stream instead of naively
 *    splitting each line on ":". Windows paths contain a drive-letter colon
 *    (e.g. `C:\Users\...`) which would otherwise be mis-parsed as the line
 *    number separator.
 */
export default tool({
  description:
    "Fast, structured cross-file string or regex search across workspace directories (similar to VS Code Ctrl+Shift+F).",
  args: {
    query: tool.schema.string().describe("Search string or regex pattern"),
    searchPath: tool.schema
      .string()
      .optional()
      .describe("Directory path to search (defaults to workspace root)"),
    includes: tool.schema
      .array(tool.schema.string())
      .optional()
      .describe("File globs to include (e.g. ['*.ts', '*.py'])"),
    excludes: tool.schema
      .array(tool.schema.string())
      .optional()
      .describe("File globs to exclude (e.g. ['node_modules', 'dist'])"),
    isRegex: tool.schema
      .boolean()
      .optional()
      .describe("Treat query as regex (default false)"),
    caseSensitive: tool.schema
      .boolean()
      .optional()
      .describe("Case-sensitive search (default false)"),
    wholeWord: tool.schema
      .boolean()
      .optional()
      .describe("Match whole word only (default false)"),
    maxResults: tool.schema
      .number()
      .optional()
      .describe("Maximum match lines to return (default 50)"),
  },
  async execute({
    query,
    searchPath,
    includes,
    excludes,
    isRegex,
    caseSensitive,
    wholeWord,
    maxResults,
  }) {
    const targetDir = searchPath || process.cwd();
    const limit = maxResults && maxResults > 0 ? maxResults : 50;

    const args: string[] = ["--json"];
    if (!isRegex) args.push("-F"); // fixed-string (literal) search
    if (!caseSensitive) args.push("-i");
    if (wholeWord) args.push("-w");

    if (includes) {
      for (const inc of includes) args.push("-g", inc);
    }
    if (excludes) {
      for (const exc of excludes) args.push("-g", `!${exc}`);
    }

    // Everything after "--" is treated as a positional (pattern, then path),
    // so a query that starts with "-" is not mistaken for a flag.
    args.push("--", query, targetDir);

    try {
      const { stdout } = await execFileAsync("rg", args, {
        maxBuffer: 32 * 1024 * 1024,
      });

      const matches: Array<{
        file: string;
        lineNumber: number;
        lineContent: string;
      }> = [];
      let totalMatches = 0;

      for (const raw of stdout.split("\n")) {
        const line = raw.trim();
        if (!line) continue;

        let event: any;
        try {
          event = JSON.parse(line);
        } catch {
          continue;
        }
        if (event.type !== "match") continue;

        totalMatches++;
        if (matches.length >= limit) continue; // keep counting, stop collecting

        const data = event.data;
        const file: string = data?.path?.text ?? "";
        const lineNumber: number = data?.line_number ?? 0;
        const lineContent: string = (data?.lines?.text ?? "").replace(
          /\r?\n$/,
          "",
        );

        matches.push({ file, lineNumber, lineContent: lineContent.trim() });
      }

      return JSON.stringify(
        {
          matchCount: matches.length,
          truncated: totalMatches > matches.length,
          matches,
        },
        null,
        2,
      );
    } catch (err: any) {
      // ripgrep exits with code 1 when there are simply no matches.
      if (err && err.code === 1) {
        return JSON.stringify({ matchCount: 0, truncated: false, matches: [] });
      }
      return JSON.stringify({
        error: `Search failed: ${err?.message ?? String(err)}`,
      });
    }
  },
});
