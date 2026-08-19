#!/usr/bin/env python3

"""Render a configuration template using environment variables."""

import os
import re
import sys
from pathlib import Path
from string import Template


def main() -> int:
    if len(sys.argv) != 3:
        print(
            "Usage: render-config.py <template-file> <output-file>",
            file=sys.stderr,
        )
        return 1

    template_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])

    if not template_path.is_file():
        print(
            f"ERROR: Template file not found: {template_path}",
            file=sys.stderr,
        )
        return 1

    template_content = template_path.read_text(encoding="utf-8")

    variable_names = sorted(
        set(re.findall(r"\$\{([A-Z][A-Z0-9_]*)\}", template_content))
    )

    missing_variables = [
        name for name in variable_names if name not in os.environ
    ]

    if missing_variables:
        print(
            "ERROR: The following environment variables were not loaded:",
            file=sys.stderr,
        )

        for name in missing_variables:
            print(f"  - {name}", file=sys.stderr)

        return 1

    rendered_content = Template(template_content).substitute(os.environ)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(rendered_content, encoding="utf-8")

    print(f"PASS: Rendered configuration: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())