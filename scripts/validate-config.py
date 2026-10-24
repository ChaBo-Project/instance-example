#!/usr/bin/env python3

"""Validate a rendered params.override.cfg before deployment."""

import configparser
import os
import re
import sys
from pathlib import Path

# First releases with hybrid retrieval over the Qdrant Space (gradio mode).
HYBRID_MIN_DEPLOY_REF = (0, 3, 0)  # ChaBo-Deploy hf-spaces-vX.Y.Z
HYBRID_MIN_ORCHESTRATOR = (0, 9, 3)  # chabo-rag-orchestrator image tag
TESTED_SPARSE_MODELS = ("Qdrant/bm25",)
BOOLEAN_VALUES = {
    "1": True, "yes": True, "true": True, "on": True,
    "0": False, "no": False, "false": False, "off": False,
}


def parse_version(text: str, prefix: str = "") -> tuple[int, ...] | None:
    """(major, minor, patch) from e.g. "hf-spaces-v0.3.0" or "0.9.3"; None if not a release."""
    match = re.fullmatch(re.escape(prefix) + r"v?(\d+)\.(\d+)\.(\d+)", text.strip())
    return tuple(int(part) for part in match.groups()) if match else None


def check_hybrid(config, errors: list[str], warnings: list[str], notes: list[str]) -> None:
    """Hybrid needs hybrid_enabled and SPARSE_MODEL together, and new enough releases."""
    raw = config.get("retrieval", "hybrid_enabled", fallback="false").strip().lower()
    if raw not in BOOLEAN_VALUES:
        errors.append("[retrieval] hybrid_enabled must be true or false.")
        return
    hybrid_enabled = BOOLEAN_VALUES[raw]
    sparse_model = os.environ.get("SPARSE_MODEL", "").strip()

    if sparse_model and sparse_model not in TESTED_SPARSE_MODELS:
        warnings.append(
            f"SPARSE_MODEL={sparse_model} is untested; only "
            f"{', '.join(TESTED_SPARSE_MODELS)} is supported."
        )
    if not hybrid_enabled:
        if sparse_model:
            warnings.append(
                "SPARSE_MODEL is set in deploy.env but [retrieval] hybrid_enabled is not "
                "true: the Qdrant Space builds BM25 vectors that are never searched."
            )
        return

    if not sparse_model:
        errors.append(
            "[retrieval] hybrid_enabled = true needs SPARSE_MODEL in deploy.env "
            "(e.g. Qdrant/bm25), so the Qdrant Space builds the BM25 vectors."
        )

    deploy_ref = os.environ.get("CHABO_DEPLOY_REF", "").strip()
    deploy_version = parse_version(deploy_ref, "hf-spaces-")
    minimum = "hf-spaces-v" + ".".join(map(str, HYBRID_MIN_DEPLOY_REF))
    if deploy_version is None:
        notes.append(
            f"CHABO_DEPLOY_REF={deploy_ref or '(empty)'} is not a release tag; cannot check "
            f"it supports hybrid ({minimum} or later)."
        )
    elif deploy_version < HYBRID_MIN_DEPLOY_REF:
        errors.append(
            f"[retrieval] hybrid_enabled = true needs CHABO_DEPLOY_REF {minimum} or later "
            f"(Qdrant Space with hybrid support); deploy.env has {deploy_ref}."
        )

    tag = os.environ.get("CHABO_TAG", "").strip()
    tag_version = parse_version(tag)
    minimum_tag = ".".join(map(str, HYBRID_MIN_ORCHESTRATOR))
    if tag_version is not None and tag_version < HYBRID_MIN_ORCHESTRATOR:
        errors.append(
            f"[retrieval] hybrid_enabled = true with the Qdrant Space needs CHABO_TAG "
            f"{minimum_tag} or later; deploy.env has {tag}."
        )


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
    warnings: list[str] = []
    notes: list[str] = []

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

    check_hybrid(config, errors, warnings, notes)

    for note in notes:
        print(f"INFO: {note}")

    for warning in warnings:
        print(f"WARNING: {warning}")

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
