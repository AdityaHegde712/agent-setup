import { spawn } from "child_process";
import path from "path";

const ReloadOpencodePlugin = async (input, _options) => {
  return {
    "chat.messages.transform": async (_input, output) => {
      const messages = output?.messages || [];
      const lastMessage = messages[messages.length - 1];
      if (!lastMessage) return;

      const textParts = (lastMessage.parts || [])
        .filter((p) => p.type === "text")
        .map((p) => p.text || "")
        .join(" ");

      if (textParts.includes("/reload-opencode")) {
        const parentPid = process.pid;
        const workspacePath = process.cwd();
        const scriptPath = path.join(
          process.env.USERPROFILE || "C:\\Users\\hifia",
          ".config",
          "opencode",
          "scripts",
          "reload.ps1"
        );

        const child = spawn(
          "powershell.exe",
          [
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            scriptPath,
            "-ParentPid",
            String(parentPid),
            "-WorkspacePath",
            workspacePath,
          ],
          {
            detached: true,
            stdio: "ignore",
          }
        );

        child.unref();

        // Sleep for 20s to block LLM turn invocation while reload.ps1 kills the process
        await new Promise((resolve) => setTimeout(resolve, 20000));
      }
    },
  };
};

export default ReloadOpencodePlugin;
export const server = ReloadOpencodePlugin;
