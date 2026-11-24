"""Test shared validation for focused test-runner arguments."""

import importlib
import io
import re
import sys
import tempfile
import unittest
from pathlib import Path
from types import ModuleType
from unittest.mock import patch

from openwisp_utils.test_runner import (
    InvalidTestArgument,
    parse_test_arguments,
    validate_test_labels,
)

PATTERN = re.compile(
    r"(?P<module>tests\.test_\w+)" r"(?:\.(?P<class>[A-Z]\w*)(?:\.test_\w+)?)?"
)
FLAGS = ("-q", "--failfast")


class TestTestRunner(unittest.TestCase):
    def test_parses_labels_and_reviewed_flags(self):
        labels, flags = parse_test_arguments(
            ["-q", "tests.test_one", "tests.test_two.TestThing.test_ok", "--failfast"],
            PATTERN,
            FLAGS,
        )
        self.assertEqual(
            [label.group(0) for label in labels],
            ["tests.test_one", "tests.test_two.TestThing.test_ok"],
        )
        self.assertEqual(flags, ["-q", "--failfast"])

    def test_rejects_unsupported_arguments(self):
        for argument in ("--plugin=x", "os.system", "tests.test_x:TestX"):
            with self.subTest(argument=argument):
                with self.assertRaisesRegex(
                    InvalidTestArgument, "Unsupported test argument"
                ):
                    parse_test_arguments([argument], PATTERN, FLAGS)

    def test_caller_controls_whether_a_label_is_required(self):
        self.assertEqual(parse_test_arguments(["-q"], PATTERN, FLAGS), ([], ["-q"]))
        with self.assertRaisesRegex(InvalidTestArgument, "a test label is required"):
            parse_test_arguments(["-q"], PATTERN, FLAGS, require_label=True)

    def test_only_accepts_unittest_testcase_classes(self):
        class TestExample(unittest.TestCase):
            pass

        matches, _ = parse_test_arguments(
            ["tests.test_one.TestExample.test_ok"], PATTERN, FLAGS
        )
        with patch("openwisp_utils.test_runner.import_module") as importer:
            module = ModuleType("tests.test_one")
            module.TestExample = TestExample
            importer.return_value = module
            validate_test_labels(matches)
            importer.assert_called_once_with("tests.test_one")
            module.TestExample = object
            with self.assertRaisesRegex(
                InvalidTestArgument, "tests.test_one.TestExample"
            ):
                validate_test_labels(matches)

    def test_missing_requested_module_is_an_invalid_label(self):
        matches, _ = parse_test_arguments(
            ["tests.test_missing.TestExample"], PATTERN, FLAGS
        )
        error = ModuleNotFoundError("not found", name="tests.test_missing")
        with patch("openwisp_utils.test_runner.import_module", side_effect=error):
            with self.assertRaisesRegex(
                InvalidTestArgument, "tests.test_missing.TestExample"
            ):
                validate_test_labels(matches)

    def test_missing_dependency_of_a_test_module_is_not_hidden(self):
        matches, _ = parse_test_arguments(
            ["tests.test_one.TestExample"], PATTERN, FLAGS
        )
        error = ModuleNotFoundError("missing dependency", name="some_dependency")
        with patch("openwisp_utils.test_runner.import_module", side_effect=error):
            with self.assertRaises(ModuleNotFoundError) as raised:
                validate_test_labels(matches)
        self.assertIs(raised.exception, error)

    def test_module_only_label_must_resolve_to_a_module(self):
        matches, _ = parse_test_arguments(["tests.test_one"], PATTERN, FLAGS)
        with patch("openwisp_utils.test_runner.import_module") as importer:
            importer.return_value = ModuleType("tests.test_one")
            validate_test_labels(matches)
            importer.assert_called_once_with("tests.test_one")
            importer.return_value = lambda: None
            with self.assertRaisesRegex(InvalidTestArgument, "tests.test_one"):
                validate_test_labels(matches)

    def test_parsing_can_be_used_with_a_non_module_selector(self):
        pattern = re.compile(r"(?P<class>Test[A-Za-z0-9_]+)(?:\.test_\w+)?")
        matches, flags = parse_test_arguments(
            ["TestExample.test_run", "-q"], pattern, FLAGS
        )
        self.assertEqual(matches[0].group("class"), "TestExample")
        self.assertEqual(flags, ["-q"])

    def test_validated_labels_work_with_the_real_unittest_runner(self):
        for should_pass in (True, False):
            with self.subTest(should_pass=should_pass):
                with tempfile.TemporaryDirectory() as directory:
                    root = Path(directory)
                    package = root / "runner_probe"
                    package.mkdir()
                    (package / "__init__.py").touch()
                    (package / "test_example.py").write_text(
                        "import unittest\n"
                        "class TestExample(unittest.TestCase):\n"
                        f"    def test_result(self): self.assertTrue({should_pass})\n"
                    )
                    pattern = re.compile(
                        r"(?P<module>runner_probe\.test_\w+)"
                        r"(?:\.(?P<class>[A-Z]\w*)(?:\.test_\w+)?)?"
                    )
                    label = "runner_probe.test_example.TestExample.test_result"
                    with patch.object(sys, "path", [str(root), *sys.path]), patch.dict(
                        sys.modules
                    ):
                        importlib.invalidate_caches()
                        labels, _ = parse_test_arguments([label], pattern, ())
                        validate_test_labels(labels)
                        suite = unittest.defaultTestLoader.loadTestsFromName(label)
                        result = unittest.TextTestRunner(stream=io.StringIO()).run(
                            suite
                        )
                    self.assertEqual(result.testsRun, 1)
                    self.assertEqual(result.wasSuccessful(), should_pass)

    def test_rejects_a_callable_disguised_as_a_module(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            package = root / "runner_probe"
            package.mkdir()
            (package / "__init__.py").write_text(
                "import unittest\n" "def test_action(): return unittest.TestSuite()\n"
            )
            pattern = re.compile(
                r"(?P<module>runner_probe\.test_\w+)"
                r"(?:\.(?P<class>[A-Z]\w*)(?:\.test_\w+)?)?"
            )
            labels, _ = parse_test_arguments(["runner_probe.test_action"], pattern, ())
            with patch.object(sys, "path", [str(root), *sys.path]), patch.dict(
                sys.modules
            ):
                importlib.invalidate_caches()
                with self.assertRaisesRegex(
                    InvalidTestArgument, "runner_probe.test_action"
                ):
                    validate_test_labels(labels)
