#!/usr/bin/env python3

"""Validate a rendered params.override.cfg before deployment."""

import configparser
import os
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 2:
        print(
            "Usage: validate-config.py <rendered-params-file>",
            file=sys.stderr,
        )
        return 1

    config_path = Path(sys.argv[1])

    # strict=True rejects duplicate sections and keys.
    config = configparser.ConfigParser(interpolation=None, strict=True)

    try:
        config.read_string(
            config_path.read_text(encoding="utf-8"),
            source=str(config_path),
        )
    except (OSError, configparser.Error) as error:
        print(f"ERROR: Cannot parse {config_path}: {error}", file=sys.stderr)
        return 1

    missing: list[str] = []
    errors: list[str] = []

    def value(section: str, key: str) -> str:
        return config.get(section, key, fallback="").strip()

    def require(section: str, key: str) -> None:
        if not value(section, key):
            missing.append(f"[{section}] {key}")

    require("hf_endpoints", "embedding_endpoint_url")
    require("hf_endpoints", "reranker_endpoint_url")

    for key in ("PROVIDER", "MODEL", "MAX_TOKENS", "TEMPERATURE"):
        require("generator", key)

    generator_provider = value("generator", "PROVIDER")

    if generator_provider == "huggingface":
        require("generator", "INFERENCE_PROVIDER")
        require("generator", "ORGANIZATION")

    if generator_provider == "azure":
        require("generator", "AZURE_ENDPOINT")

        if not os.environ.get("AZURE_API_KEY"):
            errors.append(
                "GitHub Actions secret AZURE_API_KEY is missing; "
                "it is required when [generator] PROVIDER is azure."
            )

    rewriter_enabled = value("query_rewriter", "enabled")

    if rewriter_enabled not in ("true", "false"):
        errors.append("[query_rewriter] enabled must be either true or false.")

    if rewriter_enabled == "true":
        for key in (
            "llm_provider",
            "llm_model",
            "llm_max_tokens",
            "llm_temperature",
        ):
            require("query_rewriter", key)

        if value("query_rewriter", "llm_provider") == "huggingface":
            require("query_rewriter", "llm_inference_provider")
            require("query_rewriter", "llm_organization")

    if missing:
        print("ERROR: The following required settings are empty:")

        for name in missing:
            print(f"  - {name}")

    if errors:
        print("ERROR: Additional configuration problems:")

        for error_message in errors:
            print(f"  - {error_message}")

    if missing or errors:
        print()
        print(
            "Edit orchestrator/instance_config/params.override.cfg.template "
            "and run the workflow again."
        )
        return 1

    print(f"PASS: Validated orchestrator configuration: {config_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
