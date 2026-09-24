#!/usr/bin/env python3

from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SCRIPT_DIRECTORY = Path(__file__).resolve().parent
SYNC_SCRIPT = SCRIPT_DIRECTORY / "sync-template.py"


def load_sync_module():
    spec = importlib.util.spec_from_file_location(
        "sync_template",
        SYNC_SCRIPT,
    )

    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load sync-template.py")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SyncTemplateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        self.source = self.root / "source"
        self.target = self.root / "target"

        self.source.mkdir()
        self.target.mkdir()

        (self.source / "deploy.env").write_text(
            "SOURCE_DEPLOY_ENV\n",
            encoding="utf-8",
        )
        (self.target / "deploy.env").write_bytes(
            b"TARGET_DEPLOY_ENV\r\n"
        )

        (self.target / ".git").mkdir()
        (self.target / ".git" / "history-marker").write_text(
            "existing-history\n",
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def run_sync(
        self,
        github_summary: Path | None = None,
    ) -> subprocess.CompletedProcess[str]:
        command = [
            sys.executable,
            str(SYNC_SCRIPT),
        ]

        if github_summary is not None:
            command.extend(
                [
                    "--github-summary",
                    str(github_summary),
                ]
            )

        command.extend(
            [
                str(self.source),
                str(self.target),
            ]
        )

        return subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
        )

    def test_shared_files_are_synchronized(self) -> None:
        (self.source / "shared.txt").write_text(
            "new shared content\n",
            encoding="utf-8",
        )
        (self.target / "shared.txt").write_text(
            "old shared content\n",
            encoding="utf-8",
        )
        (self.target / "obsolete.txt").write_text(
            "remove me\n",
            encoding="utf-8",
        )

        workflow = (
            self.source
            / ".github"
            / "workflows"
            / "update-from-template.yml"
        )
        workflow.parent.mkdir(parents=True)
        workflow.write_text(
            "name: Synchronize instances\n",
            encoding="utf-8",
        )

        source_directory = self.source / "directory-change"
        source_directory.mkdir()
        (source_directory / "child.txt").write_text(
            "child\n",
            encoding="utf-8",
        )
        (self.target / "directory-change").write_text(
            "old file\n",
            encoding="utf-8",
        )

        source_file = self.source / "file-change"
        source_file.write_text(
            "new file\n",
            encoding="utf-8",
        )
        target_directory = self.target / "file-change"
        target_directory.mkdir()
        (target_directory / "old-child.txt").write_text(
            "old child\n",
            encoding="utf-8",
        )

        first_result = self.run_sync()

        self.assertEqual(
            first_result.returncode,
            0,
            msg=first_result.stderr,
        )
        self.assertEqual(
            (self.target / "shared.txt").read_text(encoding="utf-8"),
            "new shared content\n",
        )
        self.assertFalse((self.target / "obsolete.txt").exists())
        self.assertTrue(
            (
                self.target
                / "directory-change"
                / "child.txt"
            ).is_file()
        )
        self.assertTrue((self.target / "file-change").is_file())
        self.assertTrue(
            (
                self.target
                / ".github"
                / "workflows"
                / "update-from-template.yml"
            ).is_file()
        )
        self.assertEqual(
            (self.target / "deploy.env").read_bytes(),
            b"TARGET_DEPLOY_ENV\r\n",
        )
        self.assertEqual(
            (
                self.target
                / ".git"
                / "history-marker"
            ).read_text(encoding="utf-8"),
            "existing-history\n",
        )

        second_result = self.run_sync()

        self.assertEqual(
            second_result.returncode,
            0,
            msg=second_result.stderr,
        )
        self.assertEqual(
            (self.target / "deploy.env").read_bytes(),
            b"TARGET_DEPLOY_ENV\r\n",
        )
        self.assertTrue(
            (
                self.target
                / ".git"
                / "history-marker"
            ).is_file()
        )

    def test_deploy_env_differences_are_reported_safely(self) -> None:
        source_deploy_env = (
            "COMMON_VARIABLE=hidden-source-common-value\n"
            "NEW_VARIABLE=hidden-source-new-value\n"
            "export EXPORTED_VARIABLE=hidden-exported-value\n"
            "# COMMENTED_VARIABLE=hidden-commented-value\n"
        )
        target_deploy_env = (
            b"COMMON_VARIABLE=hidden-target-common-value\r\n"
            b"TARGET_ONLY_VARIABLE=hidden-target-only-value\r\n"
        )

        (self.source / "deploy.env").write_text(
            source_deploy_env,
            encoding="utf-8",
        )
        (self.target / "deploy.env").write_bytes(
            target_deploy_env
        )

        github_summary = self.root / "github-step-summary.md"

        result = self.run_sync(github_summary)

        self.assertEqual(
            result.returncode,
            0,
            msg=result.stderr,
        )
        self.assertEqual(
            (self.target / "deploy.env").read_bytes(),
            target_deploy_env,
        )
        self.assertTrue(github_summary.is_file())

        summary_text = github_summary.read_text(encoding="utf-8")
        combined_output = (
            result.stdout
            + result.stderr
            + summary_text
        )

        self.assertIn("NEW_VARIABLE", combined_output)
        self.assertIn("EXPORTED_VARIABLE", combined_output)
        self.assertIn("TARGET_ONLY_VARIABLE", combined_output)
        self.assertNotIn("COMMENTED_VARIABLE", combined_output)

        hidden_values = (
            "hidden-source-common-value",
            "hidden-source-new-value",
            "hidden-exported-value",
            "hidden-commented-value",
            "hidden-target-common-value",
            "hidden-target-only-value",
        )

        for hidden_value in hidden_values:
            with self.subTest(hidden_value=hidden_value):
                self.assertNotIn(
                    hidden_value,
                    combined_output,
                )

    def test_missing_target_deploy_env_is_rejected(self) -> None:
        (self.target / "deploy.env").unlink()

        result = self.run_sync()

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "Target deploy.env does not exist",
            result.stderr,
        )

    def test_same_directory_is_rejected(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(SYNC_SCRIPT),
                str(self.source),
                str(self.source),
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "must be different",
            result.stderr,
        )

    def test_permission_error_is_reported(self) -> None:
        (self.source / "shared.txt").write_text(
            "shared\n",
            encoding="utf-8",
        )

        sync_module = load_sync_module()

        with mock.patch.object(
            sync_module.shutil,
            "copy2",
            side_effect=PermissionError("permission denied"),
        ):
            with self.assertRaises(PermissionError):
                sync_module.synchronize(
                    self.source.resolve(),
                    self.target.resolve(),
                )


if __name__ == "__main__":
    unittest.main(verbosity=2)