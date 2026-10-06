#!/usr/bin/env python3

"""Update an instance repository from instance-example.

Only the infrastructure files in MANAGED_PATHS are copied. Every other file
is instance-specific: it is never written, and the template's changes to it
are reported so the owner can port them by hand.
"""

from __future__ import annotations

import argparse
import difflib
import os
import re
import shutil
import sys
from pathlib import Path


DEPLOY_ENV = Path("deploy.env")
TEMPLATE_VERSION = Path(".template-version")

# Files that are identical in every instance and safe to overwrite.
MANAGED_PATHS = (
    Path(".gitattributes"),
    Path(".gitignore"),
    Path(".github/workflows/deploy.yml"),
    Path(".github/workflows/public-safety.yml"),
    Path(".github/workflows/update-from-template.yml"),
    Path("docs/template-synchronization.md"),
    Path("scripts/check-public-safety.py"),
    Path("scripts/render-config.py"),
    Path("scripts/sync-template.py"),
    Path("scripts/test-sync-template.py"),
    Path("scripts/validate-config.py"),
)

EXCLUDED_FROM_REPORT = {DEPLOY_ENV, TEMPLATE_VERSION, *MANAGED_PATHS}

ENV_ASSIGNMENT_PATTERN = re.compile(
    r"^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*="
)

MAX_DIFF_LINES_PER_FILE = 300


def repository_files(root: Path) -> set[Path]:
    """Return relative file paths, skipping the root .git entry.

    .git is a directory in a normal checkout and a file in a git worktree.
    """
    files: set[Path] = set()

    for current_root, directory_names, file_names in os.walk(root):
        current_path = Path(current_root)

        if current_path == root:
            directory_names[:] = [
                name for name in directory_names if name != ".git"
            ]
            file_names = [name for name in file_names if name != ".git"]

        for file_name in file_names:
            files.add((current_path / file_name).relative_to(root))

    return files


def read_bytes(path: Path) -> bytes | None:
    return path.read_bytes() if path.is_file() else None


def synchronize_managed_files(source: Path, target: Path) -> list[str]:
    """Copy managed files; remove those the source no longer has."""
    changes: list[str] = []

    for relative_path in MANAGED_PATHS:
        source_path = source / relative_path
        target_path = target / relative_path

        if source_path.is_file():
            if read_bytes(target_path) == source_path.read_bytes():
                continue

            action = "updated" if target_path.exists() else "added"
            target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_path, target_path)
            changes.append(f"{action} `{relative_path}`")
        elif target_path.is_file():
            target_path.unlink()
            changes.append(f"removed `{relative_path}`")

    return changes


def unified_diff(old: bytes | None, new: bytes | None, path: Path) -> str:
    try:
        old_lines = (old or b"").decode("utf-8").splitlines(keepends=True)
        new_lines = (new or b"").decode("utf-8").splitlines(keepends=True)
    except UnicodeDecodeError:
        return "(binary file, diff not shown)\n"

    lines = list(
        difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile=f"a/{path}",
            tofile=f"b/{path}",
        )
    )

    if len(lines) > MAX_DIFF_LINES_PER_FILE:
        omitted = len(lines) - MAX_DIFF_LINES_PER_FILE
        lines = lines[:MAX_DIFF_LINES_PER_FILE]
        lines.append(f"\n... {omitted} more diff lines not shown\n")

    return "".join(
        line if line.endswith("\n") else line + "\n" for line in lines
    )


def render_instance_file_report(
    source: Path,
    target: Path,
    base: Path | None,
) -> tuple[str, int]:
    """Report template changes to files that are never overwritten."""
    if base is not None:
        compared = base
        heading = (
            "Template changes since the last synchronized version "
            f"(`{(target / TEMPLATE_VERSION).read_text().strip()}`)."
        )
    else:
        compared = target
        heading = (
            "No previous synchronized version is recorded, so these are "
            "all differences between this instance and the template."
        )

    paths = sorted(
        path
        for path in repository_files(source) | repository_files(compared)
        if path not in EXCLUDED_FROM_REPORT
    )

    sections: list[str] = []

    for path in paths:
        old = read_bytes(compared / path)
        new = read_bytes(source / path)

        if old == new:
            continue

        if old is None:
            status = "added in template"
        elif new is None:
            status = (
                "removed from template"
                if base is not None
                else "only in this instance"
            )
        else:
            status = "changed"

        sections.append(
            f"### `{path}` — {status}\n\n"
            "```diff\n"
            f"{unified_diff(old, new, path)}"
            "```\n"
        )

    lines = ["## Instance files to review manually", "", heading, ""]

    if sections:
        lines.append(
            "These files were **not** changed. Port the parts you want "
            "in a separate commit."
        )
        lines.append("")
        lines.extend(sections)
    else:
        lines.append("No changes to review.")
        lines.append("")

    return "\n".join(lines), len(sections)


def deploy_env_variable_names(path: Path) -> set[str]:
    """Read variable names without returning or displaying their values."""
    names: set[str] = set()

    with path.open("r", encoding="utf-8-sig") as deploy_env:
        for line in deploy_env:
            match = ENV_ASSIGNMENT_PATTERN.match(line)

            if match is not None:
                names.add(match.group(1))

    return names


def render_deploy_env_report(source: Path, target: Path) -> str:
    """Compare variable names only; values are never printed."""
    source_variables = deploy_env_variable_names(source / DEPLOY_ENV)
    target_variables = deploy_env_variable_names(target / DEPLOY_ENV)

    missing = sorted(source_variables - target_variables)
    target_only = sorted(target_variables - source_variables)

    lines = ["## deploy.env variable names", ""]

    if missing:
        lines.append("Missing in this instance — add and configure manually:")
        lines.append("")
        lines.extend(f"- `{name}`" for name in missing)
        lines.append("")

    if target_only:
        lines.append(
            "Only in this instance — no longer used by the template, "
            "or intentional:"
        )
        lines.append("")
        lines.extend(f"- `{name}`" for name in target_only)
        lines.append("")

    if not missing and not target_only:
        lines.append("Same variable names as the template.")
        lines.append("")

    lines.append("Only variable names were compared; values were not printed.")
    lines.append("")

    return "\n".join(lines)


def validate_directories(
    source: Path,
    target: Path,
    base: Path | None,
) -> None:
    """Stop before changes when source or target is unsafe."""
    for name, path in (("Source", source), ("Target", target)):
        if not path.is_dir():
            raise ValueError(f"{name} directory does not exist: {path}")

    if source == target:
        raise ValueError("Source and target directories must be different.")

    if source in target.parents or target in source.parents:
        raise ValueError(
            "Source and target directories must not contain each other."
        )

    if not (source / DEPLOY_ENV).is_file():
        raise ValueError(
            "Source directory is not an instance-example repository: "
            "deploy.env is missing."
        )

    if not (target / ".git").exists():
        raise ValueError(
            "Target directory is not a Git checkout: .git is missing."
        )

    if not (target / DEPLOY_ENV).is_file():
        raise ValueError("Target deploy.env does not exist.")

    if base is not None and not base.is_dir():
        raise ValueError(f"Base directory does not exist: {base}")


def synchronize(
    source: Path,
    target: Path,
    source_sha: str,
    base: Path | None = None,
    github_summary: Path | None = None,
) -> None:
    validate_directories(source, target, base)

    deploy_env_before = (target / DEPLOY_ENV).read_bytes()

    report, review_count = render_instance_file_report(source, target, base)
    managed_changes = synchronize_managed_files(source, target)

    (target / TEMPLATE_VERSION).write_text(f"{source_sha}\n", encoding="utf-8")

    if (target / DEPLOY_ENV).read_bytes() != deploy_env_before:
        raise RuntimeError("Target deploy.env changed during synchronization.")

    summary_lines = ["## Infrastructure files updated", ""]

    if managed_changes:
        summary_lines.extend(f"- {change}" for change in managed_changes)
    else:
        summary_lines.append("Already up to date.")

    summary_lines.append("")
    summary = "\n".join(summary_lines)
    summary += "\n" + report + "\n" + render_deploy_env_report(source, target)

    print(
        f"PASS: {len(managed_changes)} infrastructure file change(s); "
        f"{review_count} instance file(s) to review manually."
    )
    print("PASS: Target deploy.env remained byte-for-byte unchanged.")

    if github_summary is not None:
        github_summary.parent.mkdir(parents=True, exist_ok=True)

        with github_summary.open("a", encoding="utf-8") as summary_file:
            summary_file.write(summary)
    else:
        print()
        print(summary)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Update an instance repository's infrastructure files from "
            "instance-example and report changes to instance-specific files."
        )
    )
    parser.add_argument(
        "--source-sha",
        required=True,
        help="Commit of the source template, recorded in .template-version.",
    )
    parser.add_argument(
        "--base-directory",
        type=Path,
        help=(
            "Checkout of the template version recorded in the target's "
            ".template-version, used to report template changes since then."
        ),
    )
    parser.add_argument(
        "--github-summary",
        type=Path,
        help="GitHub Actions step-summary file for the report.",
    )
    parser.add_argument("source_directory", type=Path)
    parser.add_argument("target_directory", type=Path)
    return parser.parse_args()


def main() -> int:
    arguments = parse_arguments()

    try:
        synchronize(
            arguments.source_directory.resolve(),
            arguments.target_directory.resolve(),
            arguments.source_sha,
            (
                arguments.base_directory.resolve()
                if arguments.base_directory is not None
                else None
            ),
            (
                arguments.github_summary.resolve()
                if arguments.github_summary is not None
                else None
            ),
        )
    except Exception as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
