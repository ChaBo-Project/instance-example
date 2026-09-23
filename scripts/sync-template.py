#!/usr/bin/env python3

from __future__ import annotations

import argparse
import os
import re
import shutil
import sys
from pathlib import Path


DEPLOY_ENV = Path("deploy.env")
ENV_ASSIGNMENT_PATTERN = re.compile(
    r"^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*="
)


def path_exists(path: Path) -> bool:
    """Return true for normal paths and broken symbolic links."""
    return path.exists() or path.is_symlink()


def repository_paths(root: Path) -> dict[Path, Path]:
    """Return repository paths without entering the root .git directory."""
    paths: dict[Path, Path] = {}

    for current_root, directory_names, file_names in os.walk(
        root,
        topdown=True,
        followlinks=False,
    ):
        current_path = Path(current_root)
        relative_root = current_path.relative_to(root)

        if relative_root == Path("."):
            directory_names[:] = [
                name for name in directory_names if name != ".git"
            ]

        for directory_name in directory_names:
            path = current_path / directory_name
            paths[path.relative_to(root)] = path

        for file_name in file_names:
            path = current_path / file_name
            paths[path.relative_to(root)] = path

    return paths


def remove_path(path: Path) -> None:
    """Remove one file, symbolic link, or directory."""
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.is_dir():
        shutil.rmtree(path)
    elif path_exists(path):
        path.unlink()
    else:
        raise FileNotFoundError(f"Path does not exist: {path}")


def copy_path(source: Path, target: Path) -> None:
    """Copy one repository path while handling file-type changes."""
    target.parent.mkdir(parents=True, exist_ok=True)

    if source.is_symlink():
        if path_exists(target):
            remove_path(target)

        target.symlink_to(
            os.readlink(source),
            target_is_directory=source.is_dir(),
        )
        return

    if source.is_dir():
        if path_exists(target) and (
            target.is_symlink() or not target.is_dir()
        ):
            remove_path(target)

        target.mkdir(parents=True, exist_ok=True)
        return

    if source.is_file():
        if path_exists(target) and (
            target.is_symlink() or target.is_dir()
        ):
            remove_path(target)

        shutil.copy2(source, target)
        return

    raise ValueError(f"Unsupported source path type: {source}")


def deploy_env_variable_names(path: Path) -> set[str]:
    """Read variable names without returning or displaying their values."""
    names: set[str] = set()

    with path.open(
        "r",
        encoding="utf-8-sig",
        newline=None,
    ) as deploy_env:
        for line in deploy_env:
            match = ENV_ASSIGNMENT_PATTERN.match(line)

            if match is not None:
                names.add(match.group(1))

    return names


def render_deploy_env_report(
    missing_variables: list[str],
    target_only_variables: list[str],
) -> str:
    """Create a Markdown report containing variable names only."""
    lines = [
        "## deploy.env compatibility",
        "",
    ]

    if missing_variables:
        lines.extend(
            [
                "### Manual action required",
                "",
                (
                    "The target `deploy.env` is missing variables that exist "
                    "in the selected source template:"
                ),
                "",
            ]
        )
        lines.extend(
            f"- `{variable_name}`"
            for variable_name in missing_variables
        )
        lines.extend(
            [
                "",
                (
                    "Add and configure these variables manually in the "
                    "target repository. Their values were not copied or "
                    "displayed."
                ),
            ]
        )
    else:
        lines.append(
            "The target contains every variable name from the source "
            "`deploy.env`."
        )

    if target_only_variables:
        lines.extend(
            [
                "",
                "### Target-only variables",
                "",
                (
                    "These variables exist only in the target `deploy.env`. "
                    "They were not removed:"
                ),
                "",
            ]
        )
        lines.extend(
            f"- `{variable_name}`"
            for variable_name in target_only_variables
        )
        lines.extend(
            [
                "",
                (
                    "Review these names manually. They may be intentional "
                    "instance-specific settings or variables that are no "
                    "longer used by the template."
                ),
            ]
        )

    lines.extend(
        [
            "",
            (
                "Only variable names were compared. Variable values were "
                "not printed."
            ),
            "",
        ]
    )

    return "\n".join(lines)


def report_deploy_env_compatibility(
    source_deploy_env: Path,
    target_deploy_env: Path,
    github_summary: Path | None,
) -> None:
    """Report source and target variable-name differences."""
    source_variables = deploy_env_variable_names(source_deploy_env)
    target_variables = deploy_env_variable_names(target_deploy_env)

    missing_variables = sorted(source_variables - target_variables)
    target_only_variables = sorted(target_variables - source_variables)

    if missing_variables:
        print(
            "WARNING: Target deploy.env is missing "
            f"{len(missing_variables)} source variable(s):"
        )

        for variable_name in missing_variables:
            print(f"WARNING: - {variable_name}")

        if github_summary is not None:
            joined_names = ", ".join(missing_variables)
            print(
                "::warning title=deploy.env action required::"
                "Target deploy.env is missing source variables: "
                f"{joined_names}"
            )
    else:
        print(
            "PASS: Target deploy.env contains every source variable name."
        )

    if target_only_variables:
        print(
            "INFO: Target deploy.env contains "
            f"{len(target_only_variables)} target-only variable(s):"
        )

        for variable_name in target_only_variables:
            print(f"INFO: - {variable_name}")

    if github_summary is not None:
        github_summary.parent.mkdir(parents=True, exist_ok=True)

        with github_summary.open(
            "a",
            encoding="utf-8",
            newline="\n",
        ) as summary:
            summary.write(
                render_deploy_env_report(
                    missing_variables,
                    target_only_variables,
                )
            )


def validate_directories(source: Path, target: Path) -> None:
    """Stop before changes when source or target is unsafe."""
    if not source.is_dir():
        raise ValueError(f"Source directory does not exist: {source}")

    if not target.is_dir():
        raise ValueError(f"Target directory does not exist: {target}")

    if source == target:
        raise ValueError(
            "Source and target directories must be different."
        )

    if source in target.parents or target in source.parents:
        raise ValueError(
            "Source and target directories must not contain each other."
        )

    if not (source / DEPLOY_ENV).is_file():
        raise ValueError(
            "Source directory is not an instance-example repository: "
            "deploy.env is missing."
        )

    if not path_exists(target / ".git"):
        raise ValueError(
            "Target directory is not a Git checkout: .git is missing."
        )

    if not (target / DEPLOY_ENV).is_file():
        raise ValueError("Target deploy.env does not exist.")


def synchronize(
    source: Path,
    target: Path,
    github_summary: Path | None = None,
) -> None:
    """Synchronize shared files and preserve target-specific state."""
    validate_directories(source, target)

    source_deploy_env = source / DEPLOY_ENV
    target_deploy_env = target / DEPLOY_ENV
    deploy_env_before = target_deploy_env.read_bytes()

    source_paths = repository_paths(source)
    target_paths = repository_paths(target)

    removed_count = 0
    copied_file_count = 0

    for relative_path, target_path in sorted(
        target_paths.items(),
        key=lambda item: len(item[0].parts),
        reverse=True,
    ):
        if relative_path == DEPLOY_ENV:
            continue

        if relative_path not in source_paths:
            remove_path(target_path)
            removed_count += 1

    for relative_path, source_path in sorted(
        source_paths.items(),
        key=lambda item: len(item[0].parts),
    ):
        if relative_path == DEPLOY_ENV:
            continue

        copy_path(source_path, target / relative_path)

        if source_path.is_file() or source_path.is_symlink():
            copied_file_count += 1

    if not target_deploy_env.is_file():
        raise RuntimeError(
            "Target deploy.env was removed during synchronization."
        )

    deploy_env_after = target_deploy_env.read_bytes()

    if deploy_env_before != deploy_env_after:
        raise RuntimeError(
            "Target deploy.env changed during synchronization."
        )

    print(
        "PASS: Shared template files synchronized "
        f"({copied_file_count} files copied, "
        f"{removed_count} obsolete paths removed)."
    )
    print("PASS: Target deploy.env remained byte-for-byte unchanged.")
    print("PASS: Target .git history remained outside synchronization.")

    report_deploy_env_compatibility(
        source_deploy_env,
        target_deploy_env,
        github_summary,
    )


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Synchronize instance-example files into an instance repository "
            "while preserving deploy.env and .git."
        )
    )
    parser.add_argument(
        "--github-summary",
        type=Path,
        help=(
            "Optional GitHub Actions step-summary file for the deploy.env "
            "compatibility report."
        ),
    )
    parser.add_argument(
        "source_directory",
        type=Path,
        help="Path to the checked-out instance-example source.",
    )
    parser.add_argument(
        "target_directory",
        type=Path,
        help="Path to the checked-out target instance repository.",
    )
    return parser.parse_args()


def main() -> int:
    arguments = parse_arguments()

    source = arguments.source_directory.resolve()
    target = arguments.target_directory.resolve()
    github_summary = (
        arguments.github_summary.resolve()
        if arguments.github_summary is not None
        else None
    )

    try:
        synchronize(
            source,
            target,
            github_summary,
        )
    except Exception as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())