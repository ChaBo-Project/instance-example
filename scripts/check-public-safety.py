#!/usr/bin/env python3

"""Reject committed credentials and unsafe public-template configuration."""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path


PUBLIC_TEMPLATE_REPOSITORY = "ChaBo-Project/instance-example"

PUBLIC_TEMPLATE_MODE = (
    os.environ.get("PUBLIC_TEMPLATE_MODE", "").lower() == "true"
    or os.environ.get("GITHUB_REPOSITORY") == PUBLIC_TEMPLATE_REPOSITORY
)

PUBLIC_VALUES_THAT_MUST_BE_EMPTY = (
    "INSTANCE_NAME",
    "ORCHESTRATOR_HF_SPACE",
    "QDRANT_HF_SPACE",
    "CHATUI_HF_SPACE",
    "HF_COLLECTION_TITLE",
    "HF_RESOURCE_GROUP_ID",
    "INSTANCE_URL",
    "QDRANT_URL",
    "CHATUI_URL",
    "EMBEDDING_ENDPOINT_URL",
    "RERANKER_ENDPOINT_URL",
    "EMBEDDING_DATASET",
    "COLLECTION_NAME",
    "GENERATOR_ORGANIZATION",
    "AZURE_ENDPOINT",
    "QUERY_REWRITER_LLM_ORGANIZATION",
)

SECRET_PATTERNS = (
    (
        "Hugging Face token",
        re.compile(r"\bhf_[A-Za-z0-9]{20,}\b"),
    ),
    (
        "GitHub token",
        re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    ),
    (
        "AWS access key",
        re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    ),
    (
        "private key",
        re.compile(
            r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE "
            r"KEY-----"
        ),
    ),
    (
        "credential-bearing URL",
        re.compile(
            r"https?://[^/\s:@]+:[^@\s/]+@",
            re.IGNORECASE,
        ),
    ),
)

FORBIDDEN_FILENAMES = {
    ".env",
    ".env.local",
    ".env.production",
    "id_rsa",
    "id_ed25519",
    "params.override.cfg",
}

FORBIDDEN_SUFFIXES = {
    ".key",
    ".p12",
    ".pfx",
    ".pem",
}

errors: list[str] = []


def tracked_files() -> list[Path]:
    output = subprocess.check_output(
        ["git", "ls-files", "-z"],
    )

    return [
        Path(entry.decode("utf-8"))
        for entry in output.split(b"\0")
        if entry
    ]


def line_number(text: str, position: int) -> int:
    return text.count("\n", 0, position) + 1


def read_deploy_env() -> dict[str, str]:
    values: dict[str, str] = {}

    for raw_line in Path("deploy.env").read_text(
        encoding="utf-8"
    ).splitlines():
        line = raw_line.strip()

        if not line or line.startswith("#") or "=" not in line:
            continue

        name, value = line.split("=", 1)
        values[name.strip()] = value.strip().strip("\"'")

    return values


for path in tracked_files():
    if (
        path.name in FORBIDDEN_FILENAMES
        and path.as_posix() != "deploy.env"
    ):
        errors.append(f"{path}: forbidden sensitive filename")

    if path.suffix.lower() in FORBIDDEN_SUFFIXES:
        errors.append(f"{path}: forbidden credential file type")

    try:
        content = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        continue

    for description, pattern in SECRET_PATTERNS:
        for match in pattern.finditer(content):
            errors.append(
                f"{path}:{line_number(content, match.start())}: "
                f"possible {description}"
            )


if PUBLIC_TEMPLATE_MODE:
    deploy_values = read_deploy_env()

    for variable_name in PUBLIC_VALUES_THAT_MUST_BE_EMPTY:
        if variable_name not in deploy_values:
            errors.append(
                f"deploy.env: missing required template variable "
                f"{variable_name}"
            )
            continue

        if deploy_values[variable_name]:
            errors.append(
                f"deploy.env: {variable_name} must be empty in "
                f"the public template"
            )


if errors:
    print("ERROR: Public repository safety check failed:")

    for error in errors:
        print(f"  - {error}")

    print()
    print("No matched credential values were printed.")
    raise SystemExit(1)


mode = "public-template" if PUBLIC_TEMPLATE_MODE else "private-instance"
print(f"PASS: Repository safety check passed in {mode} mode.")
