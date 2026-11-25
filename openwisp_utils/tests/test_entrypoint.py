"""Exercise focused test selection through the repository entry point."""

import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class TestEntrypoint(unittest.TestCase):
    def run_entrypoint(self, *arguments):
        return subprocess.run(
            [str(ROOT / "runtests"), *arguments],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=60,
        )

    def test_focused_django_test_uses_timed_runner(self):
        result = self.run_entrypoint(
            "openwisp_utils.tests.test_runner.TestTestRunner."
            "test_default_pattern_accepts_common_test_labels"
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Ran 1 test", result.stderr)
        self.assertIn("Summary of slow tests", result.stdout)

    def test_focused_releaser_file(self):
        result = self.run_entrypoint(
            "openwisp_utils/releaser/tests/test_github.py", "-q"
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(" passed", result.stdout)

    def test_invalid_arguments_are_rejected(self):
        for argument in (
            "--settings=untrusted",
            "os.system",
            "--noinput",
            "openwisp_utils.tests.test_missing_entrypoint_probe",
            "openwisp_utils/releaser/tests/test_missing_entrypoint_probe.py",
        ):
            with self.subTest(argument=argument):
                result = self.run_entrypoint(argument)
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertIn("Unsupported test argument", result.stderr)
