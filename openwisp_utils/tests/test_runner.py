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

from openwisp_utils.test.runner import (
    TEST_CLASS_LABEL_PATTERN,
    InvalidTestArgument,
    compile_test_file_pattern,
    compile_test_label_pattern,
    parse_test_arguments,
    parse_test_files,
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
            def test_ok(self):
                pass

        matches, _ = parse_test_arguments(
            ["tests.test_one.TestExample.test_ok"], PATTERN, FLAGS
        )
        with patch("openwisp_utils.test.runner.import_module") as importer:
            module = ModuleType("tests.test_one")
            module.TestExample = TestExample
            importer.return_value = module
            parent = ModuleType("tests")
            parent.test_one = module
            with patch.dict(sys.modules, {"tests": parent, "tests.test_one": module}):
                validate_test_labels(matches)
                importer.assert_called_once_with("tests.test_one")
                module.TestExample = object
                class_only, _ = parse_test_arguments(
                    ["tests.test_one.TestExample"], PATTERN, FLAGS
                )
                with self.assertRaisesRegex(
                    InvalidTestArgument, "Unsupported test argument"
                ):
                    validate_test_labels(class_only)

    def test_missing_requested_module_is_an_invalid_label(self):
        matches, _ = parse_test_arguments(
            ["tests.test_missing.TestExample"], PATTERN, FLAGS
        )
        error = ModuleNotFoundError("not found", name="tests.test_missing")
        with patch("openwisp_utils.test.runner.import_module", side_effect=error):
            with self.assertRaisesRegex(
                InvalidTestArgument, "Unsupported test argument"
            ):
                validate_test_labels(matches)

    def test_missing_dependency_of_a_test_module_is_not_hidden(self):
        matches, _ = parse_test_arguments(
            ["tests.test_one.TestExample"], PATTERN, FLAGS
        )
        error = ModuleNotFoundError("missing dependency", name="some_dependency")
        with patch("openwisp_utils.test.runner.import_module", side_effect=error):
            with self.assertRaises(ModuleNotFoundError) as raised:
                validate_test_labels(matches)
        self.assertIs(raised.exception, error)

    def test_module_only_label_must_resolve_to_a_module(self):
        matches, _ = parse_test_arguments(["tests.test_one"], PATTERN, FLAGS)
        with patch("openwisp_utils.test.runner.import_module") as importer:
            module = ModuleType("tests.test_one")
            parent = ModuleType("tests")
            parent.test_one = module
            importer.return_value = module
            with patch.dict(sys.modules, {"tests": parent, "tests.test_one": module}):
                validate_test_labels(matches)
                importer.assert_called_once_with("tests.test_one")
                importer.return_value = lambda: None
                with self.assertRaisesRegex(
                    InvalidTestArgument, "Unsupported test argument"
                ):
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
                    InvalidTestArgument, "Unsupported test argument"
                ):
                    validate_test_labels(labels)

    def test_default_pattern_accepts_common_test_labels(self):
        for label in (
            "tests.test_example",
            "tests.test_example.TestExample.test_result",
        ):
            with self.subTest(label=label):
                matches, flags = parse_test_arguments([label], allowed_flags=())
                self.assertEqual(matches[0].group(0), label)
                self.assertEqual(flags, [])

    def test_default_pattern_rejects_unsafe_labels(self):
        for label in (
            "tests.test_example.test_action",
            "tests.test_example.Helper.run",
            "tests.test_example:TestExample",
            "os.system",
            "--plugin=unsafe",
        ):
            with self.subTest(label=label):
                with self.assertRaises(InvalidTestArgument):
                    parse_test_arguments([label], allowed_flags=())

    def test_configured_roots_cover_django_and_nested_test_packages(self):
        pattern = compile_test_label_pattern(
            module_roots=("django_x509.tests", "tests.test_snmp"),
            exact_modules=("openwisp2.sample_x509.tests",),
        )
        for label in (
            "django_x509.tests.test_ca.TestCa.test_new",
            "tests.test_snmp.test_base.TestSNMP.test_get_value_error_response",
            "openwisp2.sample_x509.tests.TestProbe.test_ok",
        ):
            with self.subTest(label=label):
                matches, _ = parse_test_arguments([label], pattern, ())
                self.assertEqual(matches[0].group(0), label)
        with self.assertRaises(InvalidTestArgument):
            parse_test_arguments(["django_x509.tests.test_ca.test_action"], pattern, ())

    def test_pattern_configuration_rejects_unsafe_or_empty_roots(self):
        for roots, modules in (
            (("tests.*",), ()),
            (("tests;other",), ()),
            ((), ()),
        ):
            with self.subTest(roots=roots, modules=modules):
                with self.assertRaises(ValueError):
                    compile_test_label_pattern(
                        module_roots=roots, exact_modules=modules
                    )

    def test_pattern_configuration_accepts_individual_module_names(self):
        pattern = compile_test_label_pattern(
            module_roots="example.tests", exact_modules="sample.tests"
        )
        for label in (
            "example.tests.test_widget",
            "sample.tests.TestWidget.test_render",
        ):
            with self.subTest(label=label):
                matches, _ = parse_test_arguments([label], pattern, ())
                self.assertEqual(matches[0].group(0), label)

    def test_nested_packages_require_explicit_opt_in(self):
        label = "tests.parsers.test_example.TestExample"
        with self.assertRaises(InvalidTestArgument):
            parse_test_arguments([label])
        pattern = compile_test_label_pattern(allow_subpackages=True)
        matches, _ = parse_test_arguments([label], pattern)
        self.assertEqual(matches[0].group(0), label)

    def test_pattern_configuration_accepts_iterable_module_names(self):
        pattern = compile_test_label_pattern(
            module_roots=iter(("example.tests",)), exact_modules=iter(("sample.tests",))
        )
        for label in (
            "example.tests.test_widget",
            "sample.tests.TestWidget.test_render",
        ):
            with self.subTest(label=label):
                matches, _ = parse_test_arguments([label], pattern)
                self.assertEqual(matches[0].group(0), label)

    def test_class_only_labels_use_the_shared_pattern(self):
        labels, flags = parse_test_arguments(
            ["TestExample.test_run", "-q"], TEST_CLASS_LABEL_PATTERN, ("-q",)
        )
        self.assertEqual(labels[0].group("class"), "TestExample")
        self.assertEqual(flags, ["-q"])
        for label in (
            "TestExample.setUpClass",
            "TestExample.test_run;id",
            "../test.py",
        ):
            with self.subTest(label=label):
                with self.assertRaises(InvalidTestArgument):
                    parse_test_arguments([label], TEST_CLASS_LABEL_PATTERN)

    def test_python_test_files_are_checked_before_running(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "tests").mkdir()
            (root / "tests" / "test_one.py").touch()
            (root / "tests" / "test_link.py").symlink_to(root / "tests" / "test_one.py")
            matches, flags = parse_test_files(
                ["-q", "tests/test_one.py"],
                allowed_flags=("-q",),
                root=root,
                max_files=1,
            )
            self.assertEqual(
                [match.group(0) for match in matches], ["tests/test_one.py"]
            )
            self.assertEqual(flags, ["-q"])
            for arguments in (
                ["tests/test_missing.py"],
                ["tests/test_link.py"],
                ["tests/test_one.py", "tests/test_one.py"],
                ["../test_one.py"],
                ["--config=other"],
            ):
                with self.subTest(arguments=arguments):
                    with self.assertRaises(InvalidTestArgument):
                        parse_test_files(
                            arguments, allowed_flags=("-q",), root=root, max_files=1
                        )

    def test_jest_and_lua_file_patterns(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "client" / "utils").mkdir(parents=True)
            (root / "client" / "utils" / "widget.test.js").touch()
            (root / "openwisp-config" / "tests").mkdir(parents=True)
            (root / "openwisp-config" / "tests" / "test_net.lua").touch()
            for kind, roots, label in (
                ("jest", "client", "client/utils/widget.test.js"),
                (
                    "lua",
                    ("openwisp-config/tests",),
                    "openwisp-config/tests/test_net.lua",
                ),
            ):
                with self.subTest(kind=kind):
                    pattern = compile_test_file_pattern(roots, kind=kind)
                    matches, _ = parse_test_files([label], pattern, root=root)
                    self.assertEqual(matches[0].group(0), label)
            for label in (
                "client/../utils/widget.test.js",
                "client/utils/missing.test.js",
            ):
                with self.subTest(label=label):
                    with self.assertRaises(InvalidTestArgument):
                        parse_test_files(
                            [label],
                            compile_test_file_pattern(("client",), kind="jest"),
                            root=root,
                        )

    def test_file_existence_can_be_left_to_the_runner(self):
        with tempfile.TemporaryDirectory() as directory:
            pattern = compile_test_file_pattern(("openwisp-config/tests",), kind="lua")
            label = "openwisp-config/tests/test_missing.lua"
            matches, _ = parse_test_files(
                [label], pattern, root=directory, require_exists=False
            )
            self.assertEqual(matches[0].group(0), label)

    def test_file_pattern_rejects_invalid_roots_and_kinds(self):
        for roots, kind in (
            ((), "python"),
            (("../tests",), "python"),
            (("/tests",), "python"),
            (("tests.*",), "python"),
            (("tests",), "unknown"),
        ):
            with self.subTest(roots=roots, kind=kind):
                with self.assertRaises(ValueError):
                    compile_test_file_pattern(roots, kind=kind)

    def test_rejects_a_test_file_inside_a_symlinked_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "client").mkdir()
            (root / "outside").mkdir()
            (root / "outside" / "widget.test.js").touch()
            (root / "client" / "link").symlink_to(
                root / "outside", target_is_directory=True
            )
            pattern = compile_test_file_pattern("client", kind="jest")
            with self.assertRaises(InvalidTestArgument):
                parse_test_files(["client/link/widget.test.js"], pattern, root=root)

    def test_test_file_pattern_accepts_a_hidden_root(self):
        pattern = compile_test_file_pattern(".github/actions/example/tests")
        self.assertIsNotNone(
            pattern.fullmatch(".github/actions/example/tests/test_example.py")
        )

    def test_rejects_class_and_static_methods_as_test_methods(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            package = root / "runner_probe"
            package.mkdir()
            (package / "__init__.py").touch()
            (package / "test_example.py").write_text(
                "import unittest\n"
                "class TestExample(unittest.TestCase):\n"
                "    @staticmethod\n"
                "    def test_static(): return unittest.TestSuite()\n"
                "    @classmethod\n"
                "    def test_class(cls): return unittest.TestSuite()\n"
                "    def test_normal(self): pass\n"
            )
            pattern = compile_test_label_pattern("runner_probe")
            with patch.object(sys, "path", [str(root), *sys.path]), patch.dict(
                sys.modules
            ):
                importlib.invalidate_caches()
                for method in ("test_static", "test_class"):
                    with self.subTest(method=method):
                        labels, _ = parse_test_arguments(
                            [f"runner_probe.test_example.TestExample.{method}"], pattern
                        )
                        with self.assertRaises(InvalidTestArgument):
                            validate_test_labels(labels)
                labels, _ = parse_test_arguments(
                    ["runner_probe.test_example.TestExample.test_normal"], pattern
                )
                validate_test_labels(labels)

    def test_rejects_a_module_shadowed_by_a_package_attribute(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            package = root / "runner_probe"
            package.mkdir()
            (package / "__init__.py").touch()
            (package / "test_example.py").touch()
            with patch.object(sys, "path", [str(root), *sys.path]), patch.dict(
                sys.modules
            ):
                importlib.invalidate_caches()
                module = importlib.import_module("runner_probe.test_example")
                sys.modules["runner_probe"].test_example = lambda: unittest.TestSuite()
                labels, _ = parse_test_arguments(
                    ["runner_probe.test_example"],
                    compile_test_label_pattern("runner_probe"),
                )
                self.assertIs(sys.modules["runner_probe.test_example"], module)
                with self.assertRaises(InvalidTestArgument):
                    validate_test_labels(labels)

    def test_later_import_cannot_shadow_an_earlier_selected_module(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            package = root / "runner_probe"
            package.mkdir()
            (package / "__init__.py").touch()
            (package / "test_first.py").touch()
            (package / "test_second.py").write_text(
                "import runner_probe\n" "runner_probe.test_first = lambda: None\n"
            )
            with patch.object(sys, "path", [str(root), *sys.path]), patch.dict(
                sys.modules
            ):
                importlib.invalidate_caches()
                labels, _ = parse_test_arguments(
                    ["runner_probe.test_first", "runner_probe.test_second"],
                    compile_test_label_pattern("runner_probe"),
                )
                with self.assertRaises(InvalidTestArgument):
                    validate_test_labels(labels)

    def test_rejects_traversal_even_when_target_exists(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "client").mkdir()
            (root / "outside").mkdir()
            (root / "outside" / "widget.test.js").touch()
            pattern = compile_test_file_pattern("client", kind="jest")
            with self.assertRaises(InvalidTestArgument):
                parse_test_files(
                    ["client/../outside/widget.test.js"], pattern, root=root
                )

    def test_single_allowed_flag_requires_an_exact_match(self):
        self.assertEqual(
            parse_test_arguments(["--failfast"], allowed_flags="--failfast"),
            ([], ["--failfast"]),
        )
        with self.assertRaises(InvalidTestArgument):
            parse_test_arguments(["ast"], allowed_flags="--failfast")

    def test_rejects_absolute_files_with_a_custom_pattern(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "tests").mkdir()
            outside = root / "test_outside.py"
            outside.touch()
            with self.assertRaises(InvalidTestArgument):
                parse_test_files(
                    [str(outside)], re.compile(r".*test_\w+\.py"), root=root / "tests"
                )

    def test_rejected_argument_cannot_add_a_log_line(self):
        with self.assertRaises(InvalidTestArgument) as raised:
            parse_test_arguments(["invalid\n::warning::forged##[warning]forged"])
        self.assertNotIn("\n", str(raised.exception))
        self.assertNotIn("forged", str(raised.exception))
