#!/usr/bin/env python3

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_DIRECTORY = Path(__file__).resolve().parent
SYNC_SCRIPT = SCRIPT_DIRECTORY / "sync-template.py"

SOURCE_SHA = "0123456789abcdef0123456789abcdef01234567"
BASE_SHA = "fedcba9876543210fedcba9876543210fedcba98"


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class SyncTemplateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        self.source = self.root / "source"
        self.target = self.root / "target"
        self.base = self.root / "base"
        self.summary = self.root / "summary.md"

        write(self.source / "deploy.env", "SOURCE_DEPLOY_ENV=1\n")
        (self.target / "deploy.env").parent.mkdir(parents=True)
        (self.target / "deploy.env").write_bytes(b"TARGET_DEPLOY_ENV=1\r\n")
        write(self.target / ".git" / "history-marker", "existing-history\n")

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def run_sync(
        self,
        base: Path | None = None,
        source: Path | None = None,
    ) -> subprocess.CompletedProcess[str]:
        command = [
            sys.executable,
            str(SYNC_SCRIPT),
            "--source-sha",
            SOURCE_SHA,
            "--github-summary",
            str(self.summary),
        ]

        if base is not None:
            command.extend(["--base-directory", str(base)])

        command.extend([str(source or self.source), str(self.target)])

        return subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
        )

    def summary_text(self) -> str:
        return self.summary.read_text(encoding="utf-8")

    def test_managed_files_are_copied_and_removed(self) -> None:
        write(self.source / "scripts/render-config.py", "new render\n")
        write(self.target / "scripts/render-config.py", "old render\n")
        write(self.source / ".github/workflows/deploy.yml", "name: deploy\n")
        write(self.target / "scripts/validate-config.py", "obsolete\n")

        result = self.run_sync()

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertEqual(
            (self.target / "scripts/render-config.py").read_text(),
            "new render\n",
        )
        self.assertTrue(
            (self.target / ".github/workflows/deploy.yml").is_file()
        )
        self.assertFalse(
            (self.target / "scripts/validate-config.py").exists()
        )
        self.assertIn("updated `scripts/render-config.py`", self.summary_text())
        self.assertIn("removed `scripts/validate-config.py`", self.summary_text())

    def test_instance_files_are_never_written(self) -> None:
        instance_files = {
            "orchestrator/instance_config/instance.yaml": "guidelines: ours\n",
            "chatui/PRIVACY.md": "our privacy text\n",
            "README.md": "our readme\n",
            "notes/only-in-instance.txt": "keep me\n",
        }

        for relative_path, content in instance_files.items():
            write(self.target / relative_path, content)

        write(
            self.source / "orchestrator/instance_config/instance.yaml",
            "guidelines: template\n",
        )
        write(self.source / "chatui/PRIVACY.md", "template privacy\n")
        write(self.source / "README.md", "template readme\n")
        write(self.source / "chatui/new-template-file.md", "new\n")

        result = self.run_sync()

        self.assertEqual(result.returncode, 0, msg=result.stderr)

        for relative_path, content in instance_files.items():
            with self.subTest(path=relative_path):
                self.assertEqual(
                    (self.target / relative_path).read_text(),
                    content,
                )

        self.assertFalse((self.target / "chatui/new-template-file.md").exists())

        summary = self.summary_text()
        self.assertIn("`chatui/PRIVACY.md` — changed", summary)
        self.assertIn("+template privacy", summary)
        self.assertIn("`chatui/new-template-file.md` — added in template", summary)
        self.assertIn(
            "`notes/only-in-instance.txt` — only in this instance",
            summary,
        )

    def test_report_with_base_shows_only_template_changes(self) -> None:
        write(self.target / ".template-version", f"{BASE_SHA}\n")

        # Customized by the instance, unchanged in the template.
        write(self.base / "chatui/PRIVACY.md", "template privacy\n")
        write(self.source / "chatui/PRIVACY.md", "template privacy\n")
        write(self.target / "chatui/PRIVACY.md", "our privacy text\n")

        # Changed in the template since the last synchronization.
        write(self.base / "README.md", "old template readme\n")
        write(self.source / "README.md", "new template readme\n")
        write(self.target / "README.md", "our readme\n")

        write(self.base / ".git", "gitdir: /somewhere\n")

        result = self.run_sync(base=self.base)

        self.assertEqual(result.returncode, 0, msg=result.stderr)

        summary = self.summary_text()
        self.assertIn(BASE_SHA, summary)
        self.assertIn("`README.md` — changed", summary)
        self.assertIn("-old template readme", summary)
        self.assertIn("+new template readme", summary)
        self.assertNotIn("PRIVACY.md", summary)
        self.assertNotIn("`.git`", summary)
        self.assertEqual((self.target / "README.md").read_text(), "our readme\n")

    def test_template_version_is_recorded(self) -> None:
        result = self.run_sync()

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertEqual(
            (self.target / ".template-version").read_text(),
            f"{SOURCE_SHA}\n",
        )

    def test_deploy_env_and_git_are_preserved(self) -> None:
        first = self.run_sync()
        second = self.run_sync()

        for result in (first, second):
            self.assertEqual(result.returncode, 0, msg=result.stderr)

        self.assertEqual(
            (self.target / "deploy.env").read_bytes(),
            b"TARGET_DEPLOY_ENV=1\r\n",
        )
        self.assertEqual(
            (self.target / ".git" / "history-marker").read_text(),
            "existing-history\n",
        )

    def test_deploy_env_differences_are_reported_safely(self) -> None:
        write(
            self.source / "deploy.env",
            "COMMON_VARIABLE=hidden-source-common-value\n"
            "NEW_VARIABLE=hidden-source-new-value\n"
            "export EXPORTED_VARIABLE=hidden-exported-value\n"
            "# COMMENTED_VARIABLE=hidden-commented-value\n",
        )
        (self.target / "deploy.env").write_bytes(
            b"COMMON_VARIABLE=hidden-target-common-value\r\n"
            b"TARGET_ONLY_VARIABLE=hidden-target-only-value\r\n"
        )

        result = self.run_sync()

        self.assertEqual(result.returncode, 0, msg=result.stderr)

        combined_output = result.stdout + result.stderr + self.summary_text()

        self.assertIn("NEW_VARIABLE", combined_output)
        self.assertIn("EXPORTED_VARIABLE", combined_output)
        self.assertIn("TARGET_ONLY_VARIABLE", combined_output)
        self.assertNotIn("COMMENTED_VARIABLE", combined_output)
        self.assertNotIn("hidden-", combined_output)

    def test_missing_target_deploy_env_is_rejected(self) -> None:
        (self.target / "deploy.env").unlink()

        result = self.run_sync()

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Target deploy.env does not exist", result.stderr)

    def test_same_directory_is_rejected(self) -> None:
        result = self.run_sync(source=self.target)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("must be different", result.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
