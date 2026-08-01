import { tool } from "@opencode-ai/plugin";
import { exec } from "node:child_process";
import { promisify } from "node:util";
import * as path from "node:path";

const execAsync = promisify(exec);

export default tool({
  description: "Scrape problem description, code stubs, difficulty, and example test cases from LeetCode.",
  args: {
    inputSlugOrUrl: tool.schema.string().describe("The LeetCode problem URL (e.g. https://leetcode.com/problems/two-sum/) or title slug (e.g. two-sum)."),
  },
  async execute({ inputSlugOrUrl }) {
    // 1. Extract the title slug from the input
    let titleSlug = inputSlugOrUrl.trim();
    
    // Normalize URL
    if (titleSlug.includes("leetcode.com/problems/")) {
      const match = titleSlug.match(/leetcode\.com\/problems\/([^/]+)/);
      if (match) {
        titleSlug = match[1];
      }
    }
    
    // Remove trailing slash or query parameters if any
    titleSlug = titleSlug.split("/")[0].split("?")[0].trim();

    if (!titleSlug) {
      return JSON.stringify({ error: "Invalid URL or title slug provided." });
    }

    // 2. Locate the python scraper script relative to this tool's global directory
    const globalConfigDir = "c:/Users/hifia/.config/opencode";
    const scriptPath = path.join(globalConfigDir, "scripts", "leetcode_scraper.py");

    // 3. Execute the python script inside the local uv environment
    const command = `uv run python "${scriptPath}" "${titleSlug}"`;

    try {
      const { stdout, stderr } = await execAsync(command, { cwd: globalConfigDir });
      
      if (stderr && stderr.trim().length > 0 && !stdout) {
        return JSON.stringify({ error: `Scraper error: ${stderr}` });
      }
      
      return stdout.trim();
    } catch (error: any) {
      return JSON.stringify({
        error: `Failed to execute scraper tool: ${error.message || error}`,
      });
    }
  },
});
