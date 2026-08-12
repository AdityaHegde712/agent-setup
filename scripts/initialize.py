import os
import sys
import shutil
import json
import time
import re
from urllib.request import Request, urlopen
from urllib.error import URLError

GLOBAL_CONFIG_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
GLOBAL_AGENTS_DIR = os.path.join(GLOBAL_CONFIG_DIR, "agents")
KB_FILE_PATH = os.path.join(GLOBAL_CONFIG_DIR, "free_models_kb.json")
CACHE_EXPIRATION_SECONDS = 24 * 60 * 60  # 24 hours


def copy_sub_agents(target_project_dir):
    """Copies global agent definitions flatly into the project's .opencode/agents/ directory,
    prepending 'local-' to avoid naming conflicts, and updates mentions to refer to the local names.
    """
    target_agents_dir = os.path.join(target_project_dir, ".opencode", "agents")
    print(
        f"[*] Copying sub-agents from '{GLOBAL_AGENTS_DIR}' flatly to '{target_agents_dir}'..."
    )

    if not os.path.exists(GLOBAL_AGENTS_DIR):
        print(
            f"[!] Error: Global agents directory '{GLOBAL_AGENTS_DIR}' does not exist."
        )
        return False

    copied_files = []
    try:
        os.makedirs(target_agents_dir, exist_ok=True)
        # Find all .md files in GLOBAL_AGENTS_DIR recursively and copy them flatly with 'local-' prefix
        for root, _, files in os.walk(GLOBAL_AGENTS_DIR):
            for file in files:
                if file.endswith(".md"):
                    src_file = os.path.join(root, file)
                    dest_file = os.path.join(target_agents_dir, f"local-{file}")
                    shutil.copy2(src_file, dest_file)
                    copied_files.append(dest_file)

        print(
            f"[+] Successfully copied {len(copied_files)} agents with 'local-' prefix."
        )

        # Update references in all copied markdown files to add 'local-' prefix
        # This replaces e.g., @util/clean-coder or @clean-coder with @local-clean-coder
        agent_names = [
            "architect",
            "orchestrator",
            "backend-dev",
            "frontend-dev",
            "ops-expert",
            "technical-writer",
            "tester",
            "data-engineer",
            "model-scientist",
            "clean-coder",
            "doc-analyzer",
            "general-builder",
            "research-analyst",
            "security-reviewer",
            "skill-creator",
            "skill-tester",
            "structure-expert",
            "sub-agent-creator",
            "theory-deep-dive",
            "doc-oracle",
            "codebase-analyst",
            "codebase-doc",
            "debugger",
            "leetcode-aide",
        ]
        # Regex matches @[optional folder/]agent_name but avoids prepending duplicate local-
        pattern = re.compile(
            r"@(?:util/|app/|ml/)?(?<!local-)("
            + "|".join(re.escape(name) for name in agent_names)
            + r")\b"
        )
        updated_count = 0
        for fpath in copied_files:
            try:
                with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()

                # Replace with @local-agentname
                new_content = pattern.sub(r"@local-\1", content)

                # Also replace generic dynamic references (e.g. @dynamic-name) with @local-dynamic-name
                new_content = re.sub(
                    r"@(?<!local-)dynamic-([a-zA-Z0-9_-]+)",
                    r"@local-dynamic-\1",
                    new_content,
                )

                if new_content != content:
                    with open(fpath, "w", encoding="utf-8") as f:
                        f.write(new_content)
                    updated_count += 1
            except Exception as e:
                print(f"[!] Warning: failed to update references in '{fpath}': {e}")

        print(
            f"[+] Updated subdirectory and local references in {updated_count} copied agent configs."
        )
        return True
    except Exception as e:
        print(f"[!] Error copying sub-agents: {e}")
        return False


def fetch_and_cache_free_models(force=False):
    """Caches OpenCode's native free tier models in a local knowledge base."""
    print("[*] Caching native OpenCode models...")
    free_models_kb = {
        "opencode/big-pickle": {
            "name": "Big Pickle",
            "description": "Large stealth reasoning model optimized for general planning and orchestration.",
            "context_length": 1000000,
            "keywords": ["thinking", "reasoning", "general"],
        },
        "opencode/deepseek-v4-flash-free": {
            "name": "DeepSeek V4 Flash Free",
            "description": "Highly capable developer/coding model optimized for code generation and testing.",
            "context_length": 1000000,
            "keywords": ["coding", "code"],
        },
        "opencode/mimo-v2.5-free": {
            "name": "MiMo-V2.5 Free",
            "description": "Curated context-oriented model optimized for structured documentation and long-context processing.",
            "context_length": 1000000,
            "keywords": ["general", "text"],
        },
        "opencode/nemotron-3-ultra-free": {
            "name": "Nemotron 3 Ultra Free",
            "description": "High-performance logic and analysis model optimized for scientific reasoning and data processing.",
            "context_length": 1000000,
            "keywords": ["thinking", "reasoning"],
        },
    }

    try:
        with open(KB_FILE_PATH, "w", encoding="utf-8") as f:
            json.dump(free_models_kb, f, indent=2, ensure_ascii=False)
        print(
            f"[+] Successfully cached {len(free_models_kb)} native OpenCode models in '{KB_FILE_PATH}'."
        )
        return True
    except Exception as e:
        print(f"[!] Error writing free models knowledge base: {e}")
        return False


def check_uv():
    """Checks if 'uv' is installed on the system path and warns if it's missing."""
    print("[*] Checking for 'uv' package manager...")
    uv_path = shutil.which("uv")
    if uv_path:
        print(f"[+] Found 'uv' at: {uv_path}")
        return True
    else:
        print("[!] WARNING: 'uv' package manager was not found on your system PATH.")
        print(
            "    'uv' is required by some skills to install Python dependencies efficiently."
        )
        print("    You can install it by running:")
        if sys.platform == "win32":
            print('    powershell -c "irm https://astral.sh/uv/install.ps1 | iex"')
        # else:
        #     print("    curl -LsSf https://astral.sh/uv/install.sh | sh")
        print("    Please install 'uv' and ensure it is in your PATH.\n")
        return False


def main():
    force_fetch = False
    if len(sys.argv) > 1 and sys.argv[1] in ["force", "--force", "-f"]:
        force_fetch = True

    # 0. Check for uv package manager
    check_uv()

    # 1. Agent flat-copying deprecated (using global definitions directly)
    copy_success = True

    # 2. Fetch and cache free models
    kb_success = fetch_and_cache_free_models(force=force_fetch)

    if copy_success and kb_success:
        print("[+] OpenCode initialization completed successfully.")
    else:
        print("[!] OpenCode initialization finished with some warnings/errors.")


if __name__ == "__main__":
    main()
