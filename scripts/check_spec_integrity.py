# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Spec Integrity Guard.

Guards against silent weakening of the specification test-suite. It inspects the
working-tree diff of ``tests/spec/`` against ``HEAD`` and fails (exit code 1) if
any assertion line was **deleted or modified** (i.e. removed from the file).

Rationale: under a TDD workflow the spec tests encode the contract. Relaxing or
deleting their assertions to make a build "pass" defeats the purpose, so this
check is meant to run in a pre-commit hook or CI gate.

Behaviour:
  * Exit 0 — spec assertions untouched (or only comments / non-assertion lines
    changed), or the directory is not a git repository / has no spec dir.
  * Exit 1 — one or more assertion lines were removed or altered in tests/spec/.

Usage:
    python scripts/check_spec_integrity.py [--spec-dir tests/spec] [--base HEAD]
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys

# Lines that we treat as assertions. Matches common Python/JS test assertions:
#   assert x == y            (pytest / bare assert)
#   self.assertEqual(...)    (unittest)
#   self.assertTrue(...)     (unittest family)
#   expect(x).toBe(y)        (jest / vitest style)
#   expect(x)                (generic expectation)
_ASSERTION_RE = re.compile(
    r"""
    (^\s*assert\b)            # bare `assert ...`
    | (\bself\.assert\w*\s*\()  # unittest `self.assertEqual(` etc.
    | (\bexpect\s*\()          # `expect(`
    | (\bassert\w*\s*\()       # `assertEqual(`, `assertThat(`, ...
    """,
    re.VERBOSE,
)


def _run_git(args: list[str]) -> tuple[int, str, str]:
    """Run a git subcommand, returning (returncode, stdout, stderr)."""
    proc = subprocess.run(
        ["git", *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return proc.returncode, proc.stdout, proc.stderr


def _is_git_repo() -> bool:
    code, out, _ = _run_git(["rev-parse", "--is-inside-work-tree"])
    return code == 0 and out.strip() == "true"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Fail if assertions in the spec test suite were weakened."
    )
    parser.add_argument(
        "--spec-dir",
        default="tests/spec",
        help="Path (git pathspec) to the spec test directory (default: tests/spec).",
    )
    parser.add_argument(
        "--base",
        default="HEAD",
        help="Git ref to diff the working tree against (default: HEAD).",
    )
    args = parser.parse_args()

    if not _is_git_repo():
        print(
            "[spec-guard] Not inside a git work tree; skipping integrity check.",
            file=sys.stderr,
        )
        return 0

    # Compare the working tree (staged + unstaged) against the base ref, limited
    # to the spec directory.
    code, diff, err = _run_git(["diff", args.base, "--", args.spec_dir])
    if code != 0:
        # Most commonly: the base ref does not exist yet (fresh repo, no HEAD).
        print(
            f"[spec-guard] Unable to compute diff against '{args.base}' for "
            f"'{args.spec_dir}': {err.strip() or 'unknown error'}. Skipping.",
            file=sys.stderr,
        )
        return 0

    violations: list[str] = []
    current_file = "?"

    for line in diff.splitlines():
        # Track which file each hunk belongs to for a helpful report.
        if line.startswith("+++ b/"):
            current_file = line[len("+++ b/") :]
            continue
        if line.startswith("--- ") or line.startswith("+++ "):
            continue
        # A removed line (but not the file header "--- a/...").
        if line.startswith("-") and not line.startswith("--"):
            content = line[1:]
            if _ASSERTION_RE.search(content):
                violations.append(f"{current_file}: {content.strip()}")

    if violations:
        print(
            "[spec-guard] FAILED: assertion lines were deleted or modified in "
            f"'{args.spec_dir}'. Spec tests must not be weakened:",
            file=sys.stderr,
        )
        for v in violations:
            print(f"  - {v}", file=sys.stderr)
        print(
            f"\n[spec-guard] {len(violations)} assertion change(s) detected. "
            "Restore the assertions or justify the spec change explicitly.",
            file=sys.stderr,
        )
        return 1

    print(
        f"[spec-guard] OK: no assertions weakened in '{args.spec_dir}'.",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
